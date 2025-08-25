import logging
import re
import json
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
        'emoji_icons': {
            # Script emoji icons will be stored as 'emoji_icons/ScriptName': '🔊'
            # This is just a placeholder for the schema
        },
        'script_arguments': {
            # Script argument presets will be stored as nested structure:
            # 'script_arguments/ScriptName/PresetName': {'args': [...], 'enabled': True}
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
        if not re.match(r'^[a-zA-Z0-9\s\-_\(\)\[\]\.,:;!?\'"]+$', name):
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
    
    # Script emoji methods
    def get_script_emoji(self, script_name: str) -> Optional[str]:
        """Get custom emoji for a script, or None if no custom emoji is set."""
        return self.get(f'emoji_icons/{script_name}')
    
    def set_script_emoji(self, script_name: str, emoji: str) -> bool:
        """Set a custom emoji for a script. Returns True if successful, False if validation failed."""
        emoji = emoji.strip()
        
        if not emoji:
            self.remove_script_emoji(script_name)
            return True
        
        # Basic validation - ensure it's a single character (emoji)
        if not self._validate_emoji(emoji):
            logger.warning(f"Invalid emoji '{emoji}' for script '{script_name}'")
            return False
            
        self.set(f'emoji_icons/{script_name}', emoji)
        return True
    
    def _validate_emoji(self, emoji: str) -> bool:
        """Validate emoji meets requirements."""
        # Length validation (should be 1-4 characters for most emojis including compound ones)
        if len(emoji) < 1 or len(emoji) > 4:
            return False
        
        # Basic check - emoji should contain at least one character with Unicode category starting with 'S'
        # This catches most symbols and emojis
        import unicodedata
        for char in emoji:
            category = unicodedata.category(char)
            if category.startswith('S') or category == 'So':  # Symbol categories
                return True
        
        return False
    
    def remove_script_emoji(self, script_name: str) -> None:
        """Remove custom emoji for a script (revert to default or none)."""
        key = f'emoji_icons/{script_name}'
        if self.settings.contains(key):
            self.settings.remove(key)
            self.settings.sync()
            logger.debug(f"Removed custom emoji for: {script_name}")
    
    def get_all_script_emojis(self) -> Dict[str, str]:
        """Get all custom script emojis as a dict of {script_name: emoji}."""
        result = {}
        self.settings.beginGroup('emoji_icons')
        try:
            for key in self.settings.allKeys():
                result[key] = self.settings.value(key, '')
        finally:
            self.settings.endGroup()
        return result
    
    def get_effective_emoji(self, script_name: str) -> Optional[str]:
        """Get the effective emoji for a script (custom if set, otherwise None for default logic)."""
        return self.get_script_emoji(script_name)
    
    # Script arguments methods
    def get_script_argument_presets(self, script_name: str) -> Dict[str, Dict[str, Any]]:
        """Get all argument presets for a script as {preset_name: preset_data}"""
        result = {}
        self.settings.beginGroup(f'script_arguments/{script_name}')
        try:
            for preset_name in self.settings.allKeys():
                preset_data_str = self.settings.value(preset_name, '{}')
                try:
                    preset_data = json.loads(preset_data_str) if isinstance(preset_data_str, str) else preset_data_str
                    result[preset_name] = preset_data
                except (json.JSONDecodeError, TypeError):
                    logger.warning(f"Invalid preset data for {script_name}/{preset_name}")
                    continue
        finally:
            self.settings.endGroup()
        return result
    
    def set_script_argument_preset(self, script_name: str, preset_name: str, 
                                   arguments: List[Any], enabled: bool = True, 
                                   description: str = "") -> bool:
        """Set an argument preset for a script"""
        try:
            preset_data = {
                'args': arguments,
                'enabled': enabled,
                'description': description
            }
            
            key = f'script_arguments/{script_name}/{preset_name}'
            preset_data_str = json.dumps(preset_data)
            self.set(key, preset_data_str)
            
            logger.info(f"Set argument preset '{preset_name}' for script '{script_name}'")
            return True
        except Exception as e:
            logger.error(f"Failed to set argument preset: {e}")
            return False
    
    def remove_script_argument_preset(self, script_name: str, preset_name: str) -> bool:
        """Remove an argument preset for a script"""
        try:
            key = f'script_arguments/{script_name}/{preset_name}'
            if self.settings.contains(key):
                self.settings.remove(key)
                self.settings.sync()
                logger.info(f"Removed argument preset '{preset_name}' for script '{script_name}'")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to remove argument preset: {e}")
            return False
    
    def get_all_script_arguments(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """Get all script argument configurations as {script_name: {preset_name: preset_data}}"""
        result = {}
        self.settings.beginGroup('script_arguments')
        try:
            for script_name in self.settings.childGroups():
                result[script_name] = self.get_script_argument_presets(script_name)
        finally:
            self.settings.endGroup()
        return result
    
    def get_enabled_preset_for_script(self, script_name: str) -> Optional[Dict[str, Any]]:
        """Get the first enabled preset for a script, or None if no enabled presets"""
        presets = self.get_script_argument_presets(script_name)
        for preset_name, preset_data in presets.items():
            if preset_data.get('enabled', False):
                return {
                    'name': preset_name,
                    'args': preset_data.get('args', []),
                    'description': preset_data.get('description', '')
                }
        return None
    
    def get_script_preset_names(self, script_name: str) -> List[str]:
        """Get list of preset names for a script"""
        presets = self.get_script_argument_presets(script_name)
        return list(presets.keys())
    
    def enable_script_preset(self, script_name: str, preset_name: str, exclusive: bool = True) -> bool:
        """Enable a preset for a script. If exclusive=True, disables other presets."""
        try:
            presets = self.get_script_argument_presets(script_name)
            
            if preset_name not in presets:
                logger.warning(f"Preset '{preset_name}' not found for script '{script_name}'")
                return False
            
            # If exclusive, disable all other presets first
            if exclusive:
                for other_preset_name, preset_data in presets.items():
                    if other_preset_name != preset_name and preset_data.get('enabled', False):
                        preset_data['enabled'] = False
                        self.set_script_argument_preset(
                            script_name, other_preset_name, 
                            preset_data.get('args', []), 
                            False, 
                            preset_data.get('description', '')
                        )
            
            # Enable the target preset
            target_preset = presets[preset_name]
            return self.set_script_argument_preset(
                script_name, preset_name,
                target_preset.get('args', []),
                True,
                target_preset.get('description', '')
            )
            
        except Exception as e:
            logger.error(f"Failed to enable preset: {e}")
            return False
    
    def disable_script_preset(self, script_name: str, preset_name: str) -> bool:
        """Disable a preset for a script"""
        try:
            presets = self.get_script_argument_presets(script_name)
            
            if preset_name not in presets:
                return False
            
            preset_data = presets[preset_name]
            return self.set_script_argument_preset(
                script_name, preset_name,
                preset_data.get('args', []),
                False,
                preset_data.get('description', '')
            )
            
        except Exception as e:
            logger.error(f"Failed to disable preset: {e}")
            return False
    
    def clear_script_arguments(self, script_name: str) -> bool:
        """Remove all argument presets for a script"""
        try:
            self.settings.beginGroup(f'script_arguments')
            self.settings.remove(script_name)
            self.settings.endGroup()
            self.settings.sync()
            logger.info(f"Cleared all argument presets for script '{script_name}'")
            return True
        except Exception as e:
            logger.error(f"Failed to clear script arguments: {e}")
            return False