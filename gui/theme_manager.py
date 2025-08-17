import json
import logging
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QApplication
from .styles import get_theme_style, COLORS

logger = logging.getLogger('GUI.ThemeManager')

class ThemeManager(QObject):
    theme_changed = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.current_theme = 'light'
        self.settings_file = Path.home() / '.desktop_utility_gui' / 'settings.json'
        self.load_settings()
    
    def load_settings(self):
        """Load theme preference from settings file"""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                    self.current_theme = settings.get('theme', 'light')
                    logger.info(f"Loaded theme preference: {self.current_theme}")
            else:
                logger.info("No settings file found, using default light theme")
        except Exception as e:
            logger.error(f"Error loading settings: {e}")
            self.current_theme = 'light'
    
    def save_settings(self):
        """Save theme preference to settings file"""
        try:
            self.settings_file.parent.mkdir(parents=True, exist_ok=True)
            settings = {'theme': self.current_theme}
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
            logger.info(f"Saved theme preference: {self.current_theme}")
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
    
    def get_current_theme(self):
        """Get the current theme name"""
        return self.current_theme
    
    def set_theme(self, theme_name):
        """Set the current theme and apply it"""
        if theme_name not in COLORS:
            logger.warning(f"Unknown theme: {theme_name}")
            return
        
        if self.current_theme != theme_name:
            self.current_theme = theme_name
            self.apply_theme()
            self.save_settings()
            self.theme_changed.emit(theme_name)
            logger.info(f"Theme changed to: {theme_name}")
    
    def toggle_theme(self):
        """Toggle between light and dark themes"""
        new_theme = 'dark' if self.current_theme == 'light' else 'light'
        self.set_theme(new_theme)
    
    def apply_theme(self):
        """Apply the current theme to the application"""
        app = QApplication.instance()
        if app:
            style_sheet = get_theme_style(self.current_theme)
            app.setStyleSheet(style_sheet)
            logger.debug(f"Applied {self.current_theme} theme stylesheet")
    
    def get_theme_colors(self):
        """Get the current theme's color palette"""
        return COLORS[self.current_theme]
    
    def is_dark_theme(self):
        """Check if the current theme is dark"""
        return self.current_theme == 'dark'