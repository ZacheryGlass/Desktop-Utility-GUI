"""
View layer for Desktop Utility GUI following MVC pattern.

Views contain UI components and display logic only.
They emit signals for user interactions and have slots for updating display.
"""

from .main_view import MainView
from .tray_view import TrayView
from .settings_view import SettingsView
from .hotkey_config_view import HotkeyConfigView
from .preset_editor_view import PresetEditorView

__all__ = [
    'MainView',
    'TrayView',
    'SettingsView',
    'HotkeyConfigView',
    'PresetEditorView'
]