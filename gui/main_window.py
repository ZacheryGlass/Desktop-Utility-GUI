import logging
from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtCore import QTimer, pyqtSignal

from core.script_loader import ScriptLoader
from core.settings import SettingsManager
from .settings_dialog import SettingsDialog

logger = logging.getLogger('GUI.MainWindow')

class MainWindow(QMainWindow):
    """Minimal main window class - only used as parent for settings dialog and script loading"""
    scripts_reloaded = pyqtSignal()
    hotkeys_changed = pyqtSignal()
    settings_changed = pyqtSignal()
    
    def __init__(self, scripts_directory: str = "scripts"):
        super().__init__()
        logger.info(f"Initializing minimal MainWindow (settings dialog parent only)")
        self.scripts_directory = scripts_directory
        self.script_loader = ScriptLoader(scripts_directory)  # Keep for reload functionality
        self.settings = SettingsManager()
        self.settings_dialog = None
        
        # Set window title and hide immediately
        self.setWindowTitle("Desktop Utilities")
        self.hide()
        
        logger.info("MainWindow initialized (hidden, for settings dialog parent only)")
    
    
    
    def reload_scripts(self):
        """Reload scripts and emit signal for tray menu update"""
        logger.info("User triggered script reload")
        self.script_loader.reload_scripts()
        self.scripts_reloaded.emit()
        logger.info("Script reload complete")
    
    def open_settings(self):
        """Open the settings dialog"""
        if not self.settings_dialog:
            self.settings_dialog = SettingsDialog(self.script_loader, self)
            self.settings_dialog.settings_changed.connect(self._on_settings_changed)
            self.settings_dialog.hotkeys_changed.connect(self._on_hotkeys_changed)
        
        self.settings_dialog.load_settings()  # Reload current settings
        self.settings_dialog.exec()
    
    def _on_settings_changed(self):
        """Handle settings changes"""
        logger.info("Settings changed, updating application behavior")
        # Emit the signal to notify other components (like font settings)
        self.settings_changed.emit()
    
    def _on_hotkeys_changed(self):
        """Handle hotkey changes"""
        logger.info("Hotkeys changed, refreshing registrations")
        self.hotkeys_changed.emit()