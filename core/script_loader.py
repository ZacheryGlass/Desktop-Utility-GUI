import os
import sys
import importlib.util
import traceback
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from .script_analyzer import ScriptAnalyzer, ScriptInfo
from .script_executor import ScriptExecutor
from .exceptions import ScriptLoadError
from .settings import SettingsManager

logger = logging.getLogger('Core.ScriptLoader')

class ScriptLoader:
    
    def __init__(self, scripts_directory: str = "scripts"):
        self.scripts_directory = Path(scripts_directory)
        self.loaded_scripts: Dict[str, ScriptInfo] = {}
        self.failed_scripts: Dict[str, str] = {}
        self.settings = SettingsManager()
        self.analyzer = ScriptAnalyzer()
        self.executor = ScriptExecutor(self.settings)
        logger.info(f"ScriptLoader initialized with directory: {self.scripts_directory.absolute()}")
    
    def discover_scripts(self) -> List[ScriptInfo]:
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
            
            logger.debug(f"Attempting to analyze: {script_file.name}")
            try:
                script_info = self.analyzer.analyze_script(script_file)
                if script_info.is_executable:
                    scripts.append(script_info)
                    self.loaded_scripts[script_file.stem] = script_info
                    logger.info(f"Successfully analyzed script: {script_file.name}")
                else:
                    error_msg = f"Script not executable: {script_info.error}"
                    self.failed_scripts[script_file.name] = error_msg
                    logger.warning(f"Script {script_file.name} is not executable: {script_info.error}")
            except Exception as e:
                error_msg = f"Failed to analyze {script_file.name}: {str(e)}"
                self.failed_scripts[script_file.name] = error_msg
                logger.error(f"Error analyzing script: {error_msg}")
        
        logger.info(f"Script discovery complete: {len(scripts)} loaded, {len(self.failed_scripts)} failed")
        return scripts
    
    def execute_script(self, script_name: str, arguments: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a script by name with provided arguments."""
        if script_name not in self.loaded_scripts:
            return {
                'success': False,
                'message': f'Script "{script_name}" not found'
            }
        
        script_info = self.loaded_scripts[script_name]
        
        # Get arguments from settings if not provided
        if arguments is None:
            arguments = self.get_script_arguments(script_name)
        
        # Validate arguments
        validation_errors = self.executor.validate_arguments(script_info, arguments)
        if validation_errors:
            return {
                'success': False,
                'message': f'Argument validation failed: {"; ".join(validation_errors)}'
            }
        
        # Execute the script
        result = self.executor.execute_script(script_info, arguments)
        
        return {
            'success': result.success,
            'message': result.message,
            'output': result.output,
            'error': result.error,
            'data': result.data
        }
    
    def reload_scripts(self) -> List[ScriptInfo]:
        logger.info("Reloading all scripts")
        self.loaded_scripts.clear()
        
        # Clear executor's module cache
        self.executor.loaded_modules.clear()
        
        # Remove cached modules
        modules_to_remove = []
        for module_name in list(sys.modules.keys()):
            if module_name.startswith(str(self.scripts_directory.name)):
                modules_to_remove.append(module_name)
        
        logger.debug(f"Removing {len(modules_to_remove)} cached modules")
        for module_name in modules_to_remove:
            del sys.modules[module_name]
        
        return self.discover_scripts()
    
    def get_script(self, name: str) -> Optional[ScriptInfo]:
        return self.loaded_scripts.get(name)
    
    def get_failed_scripts(self) -> Dict[str, str]:
        return self.failed_scripts.copy()
    
    def get_script_display_name(self, script_info: ScriptInfo) -> str:
        """Get the effective display name for a script (custom name if set, otherwise original)."""
        try:
            original_name = script_info.display_name
            return self.settings.get_effective_name(original_name)
        except Exception as e:
            logger.error(f"Error getting display name for script: {e}")
            return "Unknown Script"
    
    def get_script_arguments(self, script_name: str) -> Dict[str, Any]:
        """Get configured arguments for a script from settings."""
        return self.settings.get_script_arguments(script_name)
    
    def set_script_arguments(self, script_name: str, arguments: Dict[str, Any]):
        """Save arguments configuration for a script to settings."""
        self.settings.set_script_arguments(script_name, arguments)
    
    def get_script_status(self, script_name: str) -> str:
        """Get current status of a script."""
        if script_name not in self.loaded_scripts:
            return "Not Found"
        
        script_info = self.loaded_scripts[script_name]
        return self.executor.get_script_status(script_info)
    
    def get_all_scripts(self) -> List[ScriptInfo]:
        """Get all loaded script info objects."""
        return list(self.loaded_scripts.values())