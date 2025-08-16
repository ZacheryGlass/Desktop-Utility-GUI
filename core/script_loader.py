import os
import sys
import importlib.util
import traceback
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from .base_script import UtilityScript
from .exceptions import ScriptLoadError

logger = logging.getLogger('Core.ScriptLoader')

class ScriptLoader:
    
    def __init__(self, scripts_directory: str = "scripts"):
        self.scripts_directory = Path(scripts_directory)
        self.loaded_scripts: Dict[str, UtilityScript] = {}
        self.failed_scripts: Dict[str, str] = {}
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