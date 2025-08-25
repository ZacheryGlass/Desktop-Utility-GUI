import os
import sys
import ast
import re
import importlib.util
import traceback
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any, Set
from .base_script import UtilityScript, ScriptArgumentsSpec, ArgumentSpec, ArgumentType
from .exceptions import ScriptLoadError
from .settings import SettingsManager

logger = logging.getLogger('Core.ScriptLoader')

class ScriptLoader:
    
    def __init__(self, scripts_directory: str = "scripts"):
        self.scripts_directory = Path(scripts_directory)
        self.loaded_scripts: Dict[str, UtilityScript] = {}
        self.failed_scripts: Dict[str, str] = {}
        self.settings = SettingsManager()
        logger.info(f"ScriptLoader initialized with directory: {self.scripts_directory.absolute()}")
    
    def discover_scripts(self) -> List[UtilityScript]:
        logger.info(f"Discovering scripts in: {self.scripts_directory}")
        scripts = []
        self.failed_scripts.clear()
        
        if not self.scripts_directory.exists():
            logger.warning(f"Scripts directory does not exist, creating: {self.scripts_directory}")
            self.scripts_directory.mkdir(parents=True, exist_ok=True)
            return scripts
        
        script_files = list(self.scripts_directory.glob("*.py"))
        logger.info(f"Found {len(script_files)} Python files in scripts directory")
        
        # Sort files to ensure consistent ordering
        script_files.sort(key=lambda f: f.name.lower())
        
        for script_file in script_files:
            if script_file.name.startswith("__"):
                logger.debug(f"Skipping {script_file.name} (starts with __)")
                continue
            
            logger.debug(f"Attempting to load: {script_file.name}")
            try:
                script = self._load_script(script_file)
                if script:
                    scripts.append(script)
                    self.loaded_scripts[script_file.stem] = script
                    logger.info(f"Successfully loaded script: {script_file.name}")
            except Exception as e:
                error_msg = f"Failed to load {script_file.name}: {str(e)}"
                self.failed_scripts[script_file.name] = error_msg
                logger.error(f"Error loading script: {error_msg}")
        
        logger.info(f"Script discovery complete: {len(scripts)} loaded, {len(self.failed_scripts)} failed")
        return scripts
    
    def _load_script(self, script_path: Path) -> Optional[UtilityScript]:
        module_name = script_path.stem
        logger.debug(f"Loading module: {module_name} from {script_path}")
        
        try:
            spec = importlib.util.spec_from_file_location(module_name, script_path)
            if spec is None or spec.loader is None:
                raise ScriptLoadError(f"Could not load spec for {script_path}")
            
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            
            # Check for UtilityScript
            for item_name in dir(module):
                item = getattr(module, item_name)
                if (isinstance(item, type) and 
                    issubclass(item, UtilityScript) and 
                    item != UtilityScript):
                    
                    logger.debug(f"Found UtilityScript class: {item_name}")
                    try:
                        instance = item()
                        if instance.validate():
                            logger.debug(f"Script {item_name} passed validation")
                            return instance
                        else:
                            logger.warning(f"Script {module_name}.{item_name} failed validation")
                    except Exception as e:
                        logger.error(f"Failed to instantiate {item_name}: {str(e)}")
            
        except Exception as e:
            logger.error(f"Exception loading module {module_name}: {str(e)}")
            logger.debug(traceback.format_exc())
            raise ScriptLoadError(f"Error loading module {module_name}: {str(e)}")
        
        return None
    
    def reload_scripts(self) -> List[UtilityScript]:
        logger.info("Reloading all scripts")
        self.loaded_scripts.clear()
        
        modules_to_remove = []
        for module_name in list(sys.modules.keys()):
            if module_name.startswith(str(self.scripts_directory.name)):
                modules_to_remove.append(module_name)
        
        logger.debug(f"Removing {len(modules_to_remove)} cached modules")
        for module_name in modules_to_remove:
            del sys.modules[module_name]
        
        return self.discover_scripts()
    
    def get_script(self, name: str) -> Optional[UtilityScript]:
        return self.loaded_scripts.get(name)
    
    def get_failed_scripts(self) -> Dict[str, str]:
        return self.failed_scripts.copy()
    
    def get_script_display_name(self, script: UtilityScript) -> str:
        """Get the effective display name for a script (custom name if set, otherwise original)."""
        try:
            metadata = script.get_metadata()
            original_name = metadata.get('name', 'Unknown Script')
            return self.settings.get_effective_name(original_name)
        except Exception as e:
            logger.error(f"Error getting display name for script: {e}")
            return "Unknown Script"
    
    def get_script_argument_info(self, script: UtilityScript) -> Dict[str, Any]:
        """Get comprehensive argument information for a script"""
        try:
            metadata = script.get_metadata()
            original_name = metadata.get('name', 'Unknown Script')
            
            # Get explicit argument specification
            explicit_spec = script.get_arguments_spec()
            
            # Also try to detect arguments from the script file
            script_file_path = self._find_script_file(original_name)
            detected_patterns = self._detect_argument_patterns(script_file_path) if script_file_path else set()
            
            return {
                'name': original_name,
                'explicit_spec': explicit_spec,
                'detected_patterns': detected_patterns,
                'supports_arguments': explicit_spec.supports_arguments or len(detected_patterns) > 0,
                'needs_configuration': explicit_spec.supports_arguments and len(explicit_spec.arguments) > 0
            }
        except Exception as e:
            logger.error(f"Error getting argument info for script: {e}")
            return {
                'name': 'Unknown Script',
                'explicit_spec': ScriptArgumentsSpec(),
                'detected_patterns': set(),
                'supports_arguments': False,
                'needs_configuration': False
            }
    
    def _find_script_file(self, script_name: str) -> Optional[Path]:
        """Find the file path for a script by name"""
        for script_file in self.scripts_directory.glob("*.py"):
            if script_file.name.startswith("__"):
                continue
            
            # Try to match by reading the script and finding the class name
            try:
                with open(script_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Look for script metadata with matching name
                if f"'name': '{script_name}'" in content or f'"name": "{script_name}"' in content:
                    return script_file
                    
            except Exception:
                continue
        
        return None
    
    def _detect_argument_patterns(self, script_file: Path) -> Set[str]:
        """Detect common argument parsing patterns in script files"""
        patterns = set()
        
        if not script_file or not script_file.exists():
            return patterns
        
        try:
            with open(script_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Detect various argument patterns
            patterns.update(self._detect_patterns_by_text(content))
            patterns.update(self._detect_patterns_by_ast(content))
            
        except Exception as e:
            logger.debug(f"Error detecting patterns in {script_file}: {e}")
        
        return patterns
    
    def _detect_patterns_by_text(self, content: str) -> Set[str]:
        """Detect argument patterns using text matching"""
        patterns = set()
        
        # Common patterns to look for
        pattern_checks = [
            (r'import\s+argparse', 'argparse'),
            (r'ArgumentParser\s*\(', 'argparse'),
            (r'add_argument\s*\(', 'argparse'),
            (r'import\s+click', 'click'),
            (r'@click\.(command|option|argument)', 'click'),
            (r'sys\.argv\[', 'sys.argv'),
            (r'len\s*\(\s*sys\.argv\s*\)', 'sys.argv'),
            (r'getopt\.getopt', 'getopt'),
            (r'import\s+getopt', 'getopt'),
            (r'optparse\.OptionParser', 'optparse'),
            (r'import\s+optparse', 'optparse'),
        ]
        
        for pattern, name in pattern_checks:
            if re.search(pattern, content, re.IGNORECASE):
                patterns.add(name)
        
        return patterns
    
    def _detect_patterns_by_ast(self, content: str) -> Set[str]:
        """Detect argument patterns using AST analysis"""
        patterns = set()
        
        try:
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                # Check for argparse usage
                if isinstance(node, ast.Call):
                    if self._is_argparse_call(node):
                        patterns.add('argparse')
                
                # Check for sys.argv access
                if isinstance(node, ast.Subscript):
                    if self._is_sys_argv_access(node):
                        patterns.add('sys.argv')
                
                # Check for function definitions with arguments
                if isinstance(node, ast.FunctionDef):
                    if node.name == 'execute' and len(node.args.args) > 1:  # More than just 'self'
                        patterns.add('function_args')
        
        except SyntaxError:
            # If we can't parse the AST, that's OK
            pass
        except Exception as e:
            logger.debug(f"AST analysis error: {e}")
        
        return patterns
    
    def _is_argparse_call(self, node: ast.Call) -> bool:
        """Check if AST node is an argparse-related call"""
        try:
            if isinstance(node.func, ast.Attribute):
                if node.func.attr in ['ArgumentParser', 'add_argument', 'parse_args']:
                    return True
            elif isinstance(node.func, ast.Name):
                if node.func.id == 'ArgumentParser':
                    return True
        except Exception:
            pass
        return False
    
    def _is_sys_argv_access(self, node: ast.Subscript) -> bool:
        """Check if AST node accesses sys.argv"""
        try:
            if isinstance(node.value, ast.Attribute):
                if (isinstance(node.value.value, ast.Name) and 
                    node.value.value.id == 'sys' and 
                    node.value.attr == 'argv'):
                    return True
        except Exception:
            pass
        return False
    
    def get_scripts_needing_configuration(self) -> List[Dict[str, Any]]:
        """Get list of scripts that need argument configuration"""
        scripts_needing_config = []
        
        for script in self.loaded_scripts.values():
            arg_info = self.get_script_argument_info(script)
            if arg_info['needs_configuration']:
                scripts_needing_config.append(arg_info)
        
        return scripts_needing_config
    
    def get_scripts_supporting_arguments(self) -> List[Dict[str, Any]]:
        """Get list of scripts that support arguments (configured or not)"""
        scripts_supporting_args = []
        
        for script in self.loaded_scripts.values():
            arg_info = self.get_script_argument_info(script)
            if arg_info['supports_arguments']:
                scripts_supporting_args.append(arg_info)
        
        return scripts_supporting_args