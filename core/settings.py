import logging
import re
from typing import Any, Optional, Dict, List
from PyQt6.QtCore import QSettings, QObject, pyqtSignal

logger = logging.getLogger('Core.Settings')

class SettingsManager(QObject):
    settings_changed = pyqtSignal(str, object)
    
    DEFAULTS = {
        'startup': {
            'run_on_startup': False,
            'start_minimized': True,
            'show_notification': True
        },
        'window': {
            'geometry': None,
            'last_position': None
        },
        'behavior': {
            'minimize_to_tray': True,
            'close_to_tray': True,
            'single_instance': True,
            'show_script_notifications': True
        },
        'execution': {
            'script_timeout_seconds': 30,
            'status_refresh_seconds': 5
        },
        'hotkeys': {
            # Hotkey mappings will be stored as 'hotkeys/ScriptName': 'Ctrl+Alt+X'
            # This is just a placeholder for the schema
        },
        'custom_names': {
            # Custom display names will be stored as 'custom_names/OriginalName': 'CustomName'
            # This is just a placeholder for the schema
        },
        'appearance': {
            'font_family': 'System Default',
            'font_size': 9
        },
        'script_arguments': {
            # Script arguments will be stored as 'script_arguments/ScriptName/ArgName': 'value'
            # This is just a placeholder for the schema
        },
        'script_presets': {
            # Script presets will be stored as 'script_presets/ScriptName/PresetName/ArgName': 'value'
            # Example: 'script_presets/audio_toggle/Headphones/device': 'headphones'
            # This is just a placeholder for the schema
        },
        'external_scripts': {
            # External scripts will be stored as 'external_scripts/ScriptName': '/absolute/path/to/script.py'
            # This is just a placeholder for the schema
        }
    }
    
    def __init__(self):
        super().__init__()
        self.settings = QSettings('DesktopUtils', 'DesktopUtilityGUI')
        logger.info(f"Settings initialized. Storage: {self.settings.fileName()}")
        self._ensure_defaults()
    
    def _ensure_defaults(self):
        for category, options in self.DEFAULTS.items():
            for key, default_value in options.items():
                full_key = f"{category}/{key}"
                if not self.settings.contains(full_key):
                    self.settings.setValue(full_key, default_value)
                    logger.debug(f"Set default: {full_key} = {default_value}")
    
    def get(self, key: str, default: Any = None) -> Any:
        parts = key.split('/')
        if len(parts) == 2 and parts[0] in self.DEFAULTS:
            if parts[1] in self.DEFAULTS[parts[0]]:
                default = self.DEFAULTS[parts[0]][parts[1]]
        
        value = self.settings.value(key, default)
        
        # Convert string booleans to actual booleans
        if isinstance(value, str):
            if value.lower() == 'true':
                return True
            elif value.lower() == 'false':
                return False
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        old_value = self.get(key)
        self.settings.setValue(key, value)
        self.settings.sync()
        
        if old_value != value:
            logger.debug(f"Setting changed: {key} = {value}")
            self.settings_changed.emit(key, value)
    
    def get_category(self, category: str) -> dict:
        if category not in self.DEFAULTS:
            return {}
        
        result = {}
        for key in self.DEFAULTS[category]:
            full_key = f"{category}/{key}"
            result[key] = self.get(full_key)
        return result
    
    def set_category(self, category: str, values: dict) -> None:
        for key, value in values.items():
            full_key = f"{category}/{key}"
            self.set(full_key, value)
    
    def reset_to_defaults(self) -> None:
        logger.info("Resetting all settings to defaults")
        self.settings.clear()
        self._ensure_defaults()
        self.settings.sync()
    
    def sync(self) -> None:
        self.settings.sync()
    
    # Convenience methods for common settings
    def is_run_on_startup(self) -> bool:
        return self.get('startup/run_on_startup', False)
    
    def set_run_on_startup(self, enabled: bool) -> None:
        self.set('startup/run_on_startup', enabled)
    
    def is_start_minimized(self) -> bool:
        return self.get('startup/start_minimized', True)
    
    def set_start_minimized(self, enabled: bool) -> None:
        self.set('startup/start_minimized', enabled)
    
    def is_minimize_to_tray(self) -> bool:
        return self.get('behavior/minimize_to_tray', True)
    
    def is_close_to_tray(self) -> bool:
        return self.get('behavior/close_to_tray', True)
    
    def should_show_notifications(self) -> bool:
        return self.get('behavior/show_script_notifications', True)
    
    # Font settings
    def get_font_family(self) -> str:
        return self.get('appearance/font_family', 'System Default')
    
    def set_font_family(self, font_family: str) -> None:
        self.set('appearance/font_family', font_family)
    
    def get_font_size(self) -> int:
        return self.get('appearance/font_size', 9)
    
    def set_font_size(self, font_size: int) -> None:
        self.set('appearance/font_size', font_size)
    
    # Custom display name methods
    def get_custom_name(self, original_name: str) -> Optional[str]:
        """Get custom display name for a script, or None if no custom name is set."""
        return self.get(f'custom_names/{original_name}')
    
    def set_custom_name(self, original_name: str, custom_name: str, existing_script_names: list = None) -> bool:
        """Set a custom display name for a script. Returns True if successful, False if validation failed."""
        custom_name = custom_name.strip()
        
        if not custom_name:
            self.remove_custom_name(original_name)
            return True
        
        # Validate input
        if not self._validate_custom_name(custom_name, original_name, existing_script_names):
            logger.warning(f"Invalid custom name '{custom_name}' for script '{original_name}'")
            return False
            
        self.set(f'custom_names/{original_name}', custom_name)
        return True
    
    def _validate_custom_name(self, name: str, original_name: str = None, existing_script_names: list = None) -> bool:
        """Validate custom name meets requirements."""
        # Length validation (1-50 characters)
        if len(name) < 1 or len(name) > 50:
            return False
        
        # Character validation - allow alphanumeric, spaces, and common punctuation
        if not re.match(r'^[a-zA-Z0-9\s\-_()[\]\.,:;!?\'"]+$', name):
            return False
        
        # Conflict validation - check if custom name matches any existing script names
        if existing_script_names:
            for script_name in existing_script_names:
                if script_name != original_name and name.lower() == script_name.lower():
                    logger.warning(f"Custom name '{name}' conflicts with existing script '{script_name}'")
                    return False
        
        # Check if custom name conflicts with other custom names
        existing_custom_names = self.get_all_custom_names()
        for orig_name, custom_name in existing_custom_names.items():
            if orig_name != original_name and custom_name.lower() == name.lower():
                logger.warning(f"Custom name '{name}' conflicts with existing custom name for '{orig_name}'")
                return False
            
        return True
    
    def remove_custom_name(self, original_name: str) -> None:
        """Remove custom display name for a script (revert to original)."""
        key = f'custom_names/{original_name}'
        if self.settings.contains(key):
            self.settings.remove(key)
            self.settings.sync()
            logger.debug(f"Removed custom name for: {original_name}")
    
    def get_all_custom_names(self) -> Dict[str, str]:
        """Get all custom display names as a dict of {original_name: custom_name}."""
        result = {}
        self.settings.beginGroup('custom_names')
        try:
            for key in self.settings.allKeys():
                result[key] = self.settings.value(key, '')
        finally:
            self.settings.endGroup()
        return result
    
    def get_effective_name(self, original_name: str) -> str:
        """Get the effective display name (custom if set, otherwise original)."""
        custom_name = self.get_custom_name(original_name)
        return custom_name if custom_name else original_name
    
    # Script arguments methods
    def get_script_arguments(self, script_name: str) -> Dict[str, Any]:
        """Get all configured arguments for a script."""
        result = {}
        self.settings.beginGroup(f'script_arguments/{script_name}')
        try:
            for key in self.settings.allKeys():
                value = self.settings.value(key)
                # Convert string booleans and numbers back to proper types
                if isinstance(value, str):
                    if value.lower() == 'true':
                        value = True
                    elif value.lower() == 'false':
                        value = False
                    else:
                        # Try to convert to number
                        try:
                            if '.' in value:
                                value = float(value)
                            else:
                                value = int(value)
                        except ValueError:
                            pass  # Keep as string
                result[key] = value
        finally:
            self.settings.endGroup()
        return result
    
    def set_script_arguments(self, script_name: str, arguments: Dict[str, Any]) -> None:
        """Set all arguments for a script, replacing existing ones."""
        # Remove existing arguments for this script
        self.settings.beginGroup(f'script_arguments/{script_name}')
        try:
            self.settings.remove('')  # Remove all keys in this group
        finally:
            self.settings.endGroup()
        
        # Set new arguments
        for arg_name, value in arguments.items():
            self.set_script_argument(script_name, arg_name, value)
    
    def set_script_argument(self, script_name: str, arg_name: str, value: Any) -> None:
        """Set a specific argument value for a script."""
        key = f'script_arguments/{script_name}/{arg_name}'
        self.set(key, value)
    
    def get_script_argument(self, script_name: str, arg_name: str, default: Any = None) -> Any:
        """Get a specific argument value for a script."""
        key = f'script_arguments/{script_name}/{arg_name}'
        return self.get(key, default)
    
    def remove_script_argument(self, script_name: str, arg_name: str) -> None:
        """Remove a specific argument for a script."""
        key = f'script_arguments/{script_name}/{arg_name}'
        if self.settings.contains(key):
            self.settings.remove(key)
            self.settings.sync()
            logger.debug(f"Removed argument {arg_name} for script: {script_name}")
    
    def remove_all_script_arguments(self, script_name: str) -> None:
        """Remove all arguments for a script."""
        self.settings.beginGroup(f'script_arguments/{script_name}')
        try:
            self.settings.remove('')  # Remove all keys in this group
            self.settings.sync()
            logger.debug(f"Removed all arguments for script: {script_name}")
        finally:
            self.settings.endGroup()
    
    def get_all_scripts_with_arguments(self) -> Dict[str, Dict[str, Any]]:
        """Get all scripts that have configured arguments."""
        result = {}
        self.settings.beginGroup('script_arguments')
        try:
            for script_name in self.settings.childGroups():
                result[script_name] = self.get_script_arguments(script_name)
        finally:
            self.settings.endGroup()
        return result
    
    # Execution timeout methods
    def get_script_timeout_seconds(self) -> int:
        """Get the timeout for script execution in seconds."""
        return self.get('execution/script_timeout_seconds', 30)
    
    def get_status_refresh_seconds(self) -> int:
        """Get the status refresh interval in seconds."""
        return self.get('execution/status_refresh_seconds', 5)
    
    def set_script_timeout_seconds(self, seconds: int) -> None:
        """Set the timeout for script execution in seconds."""
        self.set('execution/script_timeout_seconds', seconds)
    
    def set_status_refresh_seconds(self, seconds: int) -> None:
        """Set the status refresh interval in seconds."""
        self.set('execution/status_refresh_seconds', seconds)
    
    # Script preset methods
    def get_script_presets(self, script_name: str) -> Dict[str, Dict[str, Any]]:
        """Get all presets for a script as {preset_name: {arg_name: value}}."""
        result = {}
        self.settings.beginGroup(f'script_presets/{script_name}')
        try:
            for preset_name in self.settings.childGroups():
                preset_args = {}
                self.settings.beginGroup(preset_name)
                try:
                    for arg_name in self.settings.allKeys():
                        value = self.settings.value(arg_name)
                        # Convert string representations back to proper types
                        if isinstance(value, str):
                            if value.lower() == 'true':
                                value = True
                            elif value.lower() == 'false':
                                value = False
                            else:
                                try:
                                    if '.' in value:
                                        value = float(value)
                                    else:
                                        value = int(value)
                                except ValueError:
                                    pass  # Keep as string
                        preset_args[arg_name] = value
                finally:
                    self.settings.endGroup()
                result[preset_name] = preset_args
        finally:
            self.settings.endGroup()
        return result
    
    def save_script_preset(self, script_name: str, preset_name: str, arguments: Dict[str, Any]) -> None:
        """Save a preset configuration for a script."""
        # Remove existing preset
        self.delete_script_preset(script_name, preset_name)
        
        # Save new preset
        for arg_name, value in arguments.items():
            key = f'script_presets/{script_name}/{preset_name}/{arg_name}'
            self.set(key, value)
        
        logger.info(f"Saved preset '{preset_name}' for script '{script_name}' with {len(arguments)} arguments")
    
    def delete_script_preset(self, script_name: str, preset_name: str) -> None:
        """Delete a preset configuration for a script."""
        preset_key = f'script_presets/{script_name}/{preset_name}'
        self.settings.beginGroup(preset_key)
        try:
            self.settings.remove('')  # Remove all keys in this group
            self.settings.sync()
            logger.debug(f"Deleted preset '{preset_name}' for script '{script_name}'")
        finally:
            self.settings.endGroup()
    
    def get_script_preset_names(self, script_name: str) -> List[str]:
        """Get list of preset names for a script."""
        preset_names = []
        self.settings.beginGroup(f'script_presets/{script_name}')
        try:
            preset_names = list(self.settings.childGroups())
        finally:
            self.settings.endGroup()
        return preset_names
    
    def has_script_presets(self, script_name: str) -> bool:
        """Check if a script has any configured presets."""
        return len(self.get_script_preset_names(script_name)) > 0
    
    def get_all_scripts_with_presets(self) -> Dict[str, List[str]]:
        """Get all scripts that have presets as {script_name: [preset_names]}."""
        result = {}
        self.settings.beginGroup('script_presets')
        try:
            for script_name in self.settings.childGroups():
                result[script_name] = self.get_script_preset_names(script_name)
        finally:
            self.settings.endGroup()
        return result
    
    def get_preset_arguments(self, script_name: str, preset_name: str) -> Dict[str, Any]:
        """Get arguments for a specific preset."""
        presets = self.get_script_presets(script_name)
        return presets.get(preset_name, {})
    
    # External scripts management methods
    def get_external_scripts(self) -> Dict[str, str]:
        """Get all external scripts as a dict of {script_name: absolute_path}."""
        result = {}
        self.settings.beginGroup('external_scripts')
        try:
            for key in self.settings.allKeys():
                result[key] = self.settings.value(key, '')
        finally:
            self.settings.endGroup()
        return result
    
    def add_external_script(self, script_name: str, absolute_path: str) -> bool:
        """Add an external script. Returns True if successful, False if validation failed."""
        script_name = script_name.strip()
        absolute_path = absolute_path.strip()
        
        if not script_name or not absolute_path:
            logger.warning("External script name and path cannot be empty")
            return False
        
        # Validate the script path
        if not self.validate_external_script_path(absolute_path):
            logger.warning(f"Invalid external script path: {absolute_path}")
            return False
        
        # Check for naming conflicts with existing external scripts
        existing_externals = self.get_external_scripts()
        if script_name in existing_externals:
            logger.warning(f"External script name '{script_name}' already exists")
            return False
        
        # Validate script name (similar to custom name validation)
        if not self._validate_external_script_name(script_name):
            logger.warning(f"Invalid external script name: {script_name}")
            return False
        
        # Store the external script
        self.set(f'external_scripts/{script_name}', absolute_path)
        logger.info(f"Added external script: {script_name} -> {absolute_path}")
        return True
    
    def remove_external_script(self, script_name: str) -> None:
        """Remove an external script by name."""
        key = f'external_scripts/{script_name}'
        if self.settings.contains(key):
            self.settings.remove(key)
            self.settings.sync()
            logger.info(f"Removed external script: {script_name}")
    
    def update_external_script_path(self, script_name: str, new_absolute_path: str) -> bool:
        """Update the path for an existing external script."""
        if not self.validate_external_script_path(new_absolute_path):
            logger.warning(f"Invalid external script path: {new_absolute_path}")
            return False
        
        key = f'external_scripts/{script_name}'
        if self.settings.contains(key):
            self.set(key, new_absolute_path)
            logger.info(f"Updated external script path: {script_name} -> {new_absolute_path}")
            return True
        else:
            logger.warning(f"External script '{script_name}' not found")
            return False
    
    def validate_external_script_path(self, path: str) -> bool:
        """Validate that the external script path is valid."""
        if not path or not isinstance(path, str):
            return False
        
        try:
            from pathlib import Path
            script_path = Path(path)
            
            # Must be absolute path
            if not script_path.is_absolute():
                logger.debug(f"Path is not absolute: {path}")
                return False
            
            # Must exist and be a file
            if not script_path.exists() or not script_path.is_file():
                logger.debug(f"Path does not exist or is not a file: {path}")
                return False
            
            # Must be a Python file
            if script_path.suffix.lower() != '.py':
                logger.debug(f"Path is not a Python file: {path}")
                return False
            
            # Basic security check - prevent directory traversal attempts
            # This is mainly to catch obvious attempts, not comprehensive security
            normalized_path = str(script_path.resolve())
            if '..' in normalized_path or normalized_path != str(script_path.resolve()):
                logger.debug(f"Suspicious path detected: {path}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating external script path {path}: {e}")
            return False
    
    def _validate_external_script_name(self, name: str) -> bool:
        """Validate external script name meets requirements."""
        # Similar validation to custom names but for script names
        # Length validation (1-50 characters)
        if len(name) < 1 or len(name) > 50:
            return False
        
        # Character validation - allow alphanumeric, spaces, underscores, hyphens
        if not re.match(r'^[a-zA-Z0-9\s\-_]+$', name):
            return False
        
        return True
    
    def get_external_script_path(self, script_name: str) -> Optional[str]:
        """Get the absolute path for a specific external script."""
        return self.get(f'external_scripts/{script_name}')
    
    def has_external_scripts(self) -> bool:
        """Check if any external scripts are configured."""
        return len(self.get_external_scripts()) > 0
