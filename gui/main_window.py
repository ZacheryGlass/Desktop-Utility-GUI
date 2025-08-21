import logging
from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtCore import QTimer, pyqtSignal

from core.script_loader import ScriptLoader
from core.settings import SettingsManager
from .theme_manager import ThemeManager
from .settings_dialog import SettingsDialog

logger = logging.getLogger('GUI.MainWindow')

class MainWindow(QMainWindow):
    """Minimal main window class - only used as parent for settings dialog and script loading"""
    scripts_reloaded = pyqtSignal()
    
    def __init__(self, scripts_directory: str = "scripts"):
        super().__init__()
        logger.info(f"Initializing minimal MainWindow with scripts directory: {scripts_directory}")
        self.scripts_directory = scripts_directory
        self.script_loader = ScriptLoader(scripts_directory)
        self.settings = SettingsManager()
        self.settings_dialog = None
        
        # Initialize theme manager (for settings dialog theming)
        self.theme_manager = ThemeManager()
        self.theme_manager.theme_changed.connect(self.on_theme_changed)
        
        # Set window title and hide immediately
        self.setWindowTitle("Desktop Utilities")
        self.hide()
        
        # Load scripts for tray menu use
        self.load_scripts()
        
        # Apply initial theme
        self.theme_manager.apply_theme()
        
        logger.info("MainWindow initialized (hidden, for settings dialog parent only)")
    
    
    def load_scripts(self):
        """Load scripts for tray menu use (no UI creation)"""
        logger.info("Loading scripts...")
        
        try:
            scripts = self.script_loader.discover_scripts()
            logger.info(f"Script loader discovered {len(scripts)} script(s)")
            
            if not scripts:
                logger.warning(f"No scripts found in '{self.scripts_directory}' directory")
            else:
                logger.info(f"Successfully loaded {len(scripts)} script(s)")
            
            failed_scripts = self.script_loader.get_failed_scripts()
            if failed_scripts:
                failed_count = len(failed_scripts)
                logger.warning(f"{failed_count} script(s) failed to load:")
                for script_name, error in failed_scripts.items():
                    logger.warning(f"  - {script_name}: {error}")
                
        except Exception as e:
            logger.error(f"Critical error loading scripts: {str(e)}", exc_info=True)
    
    def reload_scripts(self):
        """Reload scripts and emit signal for tray menu update"""
        logger.info("User triggered script reload")
        self.script_loader.reload_scripts()
        self.load_scripts()
        self.scripts_reloaded.emit()
        logger.info("Script reload complete")
    
    def on_theme_changed(self, theme_name):
        """Handle theme change event"""
        logger.debug(f"Theme changed to: {theme_name}")
    
    def open_settings(self):
        """Open the settings dialog"""
        if not self.settings_dialog:
            self.settings_dialog = SettingsDialog(self)
            self.settings_dialog.settings_changed.connect(self._on_settings_changed)
        
        self.settings_dialog.load_settings()  # Reload current settings
        self.settings_dialog.exec()
    
    def _on_settings_changed(self):
        """Handle settings changes"""
        logger.info("Settings changed, updating application behavior")
        # Theme changes are handled by the theme manager
        # Other settings will take effect on next action