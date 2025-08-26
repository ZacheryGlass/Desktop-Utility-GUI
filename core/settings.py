import logging
import re
from typing import Any, Optional, Dict
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
