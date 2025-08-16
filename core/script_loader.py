import os
import sys
import importlib.util
import traceback
from pathlib import Path
from typing import List, Optional, Dict, Any
from .base_script import UtilityScript
from .exceptions import ScriptLoadError

class ScriptLoader:
    
    def __init__(self, scripts_directory: str = "scripts"):
        self.scripts_directory = Path(scripts_directory)
        self.loaded_scripts: Dict[str, UtilityScript] = {}
        self.failed_scripts: Dict[str, str] = {}
    
    def discover_scripts(self) -> List[UtilityScript]:
        scripts = []
        self.failed_scripts.clear()
        
        if not self.scripts_directory.exists():
            self.scripts_directory.mkdir(parents=True, exist_ok=True)
            return scripts
        
        script_files = self.scripts_directory.glob("*.py")
        
        for script_file in script_files:
            if script_file.name.startswith("__"):
                continue
            
            try:
                script = self._load_script(script_file)
                if script:
                    scripts.append(script)
                    self.loaded_scripts[script_file.stem] = script
            except Exception as e:
                error_msg = f"Failed to load {script_file.name}: {str(e)}"
                self.failed_scripts[script_file.name] = error_msg
                print(f"Error loading script: {error_msg}")
        
        return scripts
    
    def _load_script(self, script_path: Path) -> Optional[UtilityScript]:
        module_name = script_path.stem
        
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
                    
                    try:
                        instance = item()
                        if instance.validate():
                            return instance
                        else:
                            print(f"Script {module_name} failed validation")
                    except Exception as e:
                        print(f"Failed to instantiate {item_name}: {str(e)}")
            
        except Exception as e:
            traceback.print_exc()
            raise ScriptLoadError(f"Error loading module {module_name}: {str(e)}")
        
        return None
    
    def reload_scripts(self) -> List[UtilityScript]:
        self.loaded_scripts.clear()
        
        for module_name in list(sys.modules.keys()):
            if module_name.startswith(str(self.scripts_directory.name)):
                del sys.modules[module_name]
        
        return self.discover_scripts()
    
    def get_script(self, name: str) -> Optional[UtilityScript]:
        return self.loaded_scripts.get(name)
    
    def get_failed_scripts(self) -> Dict[str, str]:
        return self.failed_scripts.copy()