import sys
import logging
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                             QScrollArea, QLabel, QPushButton,
                             QHBoxLayout, QMessageBox)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon, QCloseEvent
from pathlib import Path

from core.script_loader import ScriptLoader
from core.settings import SettingsManager
from .script_widget import ScriptWidget
from .styles import MAIN_STYLE
from .theme_manager import ThemeManager
from .settings_dialog import SettingsDialog

logger = logging.getLogger('GUI.MainWindow')

class MainWindow(QMainWindow):
    scripts_reloaded = pyqtSignal()
    minimize_to_tray_requested = pyqtSignal()
    
    def __init__(self, scripts_directory: str = "scripts"):
        super().__init__()
        logger.info(f"Initializing MainWindow with scripts directory: {scripts_directory}")
        self.scripts_directory = scripts_directory
        self.script_loader = ScriptLoader(scripts_directory)
        self.script_widgets = []
        self.settings = SettingsManager()
        self.settings_dialog = None
        
        # Initialize theme manager
        self.theme_manager = ThemeManager()
        self.theme_manager.theme_changed.connect(self.on_theme_changed)
        
        self.init_ui()
        self.load_scripts()
        
        # Apply initial theme
        self.theme_manager.apply_theme()
        
        logger.info("Setting up refresh timer (5 second interval)")
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_status)
        self.refresh_timer.start(5000)
    
    def init_ui(self):
        logger.debug("Initializing UI components")
        self.setWindowTitle("Desktop Utilities")
        
        # Compact popup window size
        self.setGeometry(100, 100, 280, 200)
        
        # Remove window frame for popup look
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        
        # Add compact popup styling
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2d3142;
                border: 1px solid #4f5b66;
                border-radius: 6px;
            }
            
            /* Compact script widget styling */
            QWidget[objectName="scriptWidget"] {
                background-color: transparent;
                border: none;
                border-radius: 3px;
                padding: 2px;
            }
            
            QWidget[objectName="scriptWidget"]:hover {
                background-color: #3d4454;
                cursor: pointer;
            }
            
            /* Script name labels */
            QLabel[objectName="scriptName"] {
                color: #c5c8c6;
                font-size: 12px;
                font-weight: 500;
                padding: 0px;
                margin: 0px;
            }
            
            /* Status indicators */
            QLabel[objectName="statusIndicator"] {
                color: #888;
                font-size: 14px;
                background-color: transparent;
                border: none;
                padding: 0px;
                margin: 0px;
            }
        """)
        
        logger.debug("Main window configured: 280x200 compact popup")
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout with minimal margins - no header
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(0)
        
        # Script list widget - direct layout, no header
        self.script_list_widget = QWidget()
        self.script_list_widget.setObjectName("scriptListContainer")
        self.script_list_layout = QVBoxLayout(self.script_list_widget)
        self.script_list_layout.setContentsMargins(0, 0, 0, 0)
        self.script_list_layout.setSpacing(1)
        
        main_layout.addWidget(self.script_list_widget)
    
    def load_scripts(self):
        logger.info("Loading scripts...")
        self.clear_scripts()
        
        try:
            scripts = self.script_loader.discover_scripts()
            logger.info(f"Script loader discovered {len(scripts)} script(s)")
            
            if not scripts:
                logger.warning(f"No scripts found in '{self.scripts_directory}' directory")
                no_scripts_label = QLabel("No scripts found")
                no_scripts_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                no_scripts_label.setStyleSheet("color: #999; padding: 10px; font-size: 12px;")
                self.script_list_layout.addWidget(no_scripts_label)
            else:
                for script in scripts:
                    try:
                        # Create script widget
                        metadata = script.get_metadata()
                        logger.debug(f"Creating widget for script: {metadata.get('name', 'Unknown')}")
                        widget = ScriptWidget(script)
                        self.script_widgets.append(widget)
                        self.script_list_layout.addWidget(widget)
                        logger.debug(f"Successfully added widget for: {metadata.get('name', 'Unknown')}")
                    except Exception as e:
                        logger.error(f"Error creating widget for script: {e}", exc_info=True)
                
                # Auto-resize window height based on content
                self._resize_to_content()
                
                logger.info(f"Successfully loaded {len(scripts)} script widget(s)")
            
            failed_scripts = self.script_loader.get_failed_scripts()
            if failed_scripts:
                failed_count = len(failed_scripts)
                logger.warning(f"{failed_count} script(s) failed to load:")
                for script_name, error in failed_scripts.items():
                    logger.warning(f"  - {script_name}: {error}")
                
        except Exception as e:
            logger.error(f"Critical error loading scripts: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to load scripts: {str(e)}")
    
    def _resize_to_content(self):
        """Resize window to fit content"""
        # Calculate height based on number of scripts (no header now)
        script_count = len(self.script_widgets)
        if script_count == 0:
            height = 30
        else:
            # Each compact widget will be ~30px + spacing, no header
            height = (script_count * 32) + 8  # scripts + padding only
        
        # Set new size
        self.resize(280, min(height, 400))  # Max height 400px
    
    def clear_scripts(self):
        logger.debug(f"Clearing {len(self.script_widgets)} existing script widgets")
        while self.script_list_layout.count():
            item = self.script_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.script_widgets.clear()
    
    def reload_scripts(self):
        logger.info("User triggered script reload")
        self.status_label.setText("Reloading scripts...")
        self.script_loader.reload_scripts()
        self.load_scripts()
        self.scripts_reloaded.emit()
        logger.info("Script reload complete")
    
    def refresh_status(self):
        logger.debug(f"Refreshing status for {len(self.script_widgets)} script(s)")
        for widget in self.script_widgets:
            try:
                widget.update_status()
            except Exception as e:
                logger.error(f"Error updating status for widget: {e}")
    
    def on_theme_changed(self, theme_name):
        """Handle theme change event"""
        # Theme is now managed through settings dialog
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
    
    def closeEvent(self, event: QCloseEvent):
        """Handle window close event"""
        if self.settings.is_close_to_tray():
            logger.info("Closing to system tray")
            event.ignore()
            self.hide()
            self.minimize_to_tray_requested.emit()
        else:
            logger.info("Closing application")
            event.accept()
    
    def changeEvent(self, event):
        """Handle window state changes"""
        if event.type() == event.Type.WindowStateChange:
            if self.isMinimized() and self.settings.is_minimize_to_tray():
                logger.info("Minimizing to system tray")
                self.hide()
                self.minimize_to_tray_requested.emit()
                event.ignore()
        super().changeEvent(event)
    
    def show_from_tray(self):
        """Show and restore the window from tray"""
        self.show()
        self.raise_()
        self.activateWindow()
        self.setWindowState(self.windowState() & ~Qt.WindowState.WindowMinimized)
    
    def show_from_tray_bottom_right(self):
        """Show and restore the window from tray in bottom right corner"""
        # Get screen geometry
        screen = self.screen()
        if screen:
            screen_geometry = screen.availableGeometry()
            window_size = self.size()
            
            # Calculate bottom right position with padding
            padding = 10  # Reduced padding for compact popup
            x = screen_geometry.right() - window_size.width() - padding
            y = screen_geometry.bottom() - window_size.height() - padding
            
            # Set position and show
            self.move(x, y)
        
        self.show()
        self.raise_()
        self.activateWindow()
        self.setWindowState(self.windowState() & ~Qt.WindowState.WindowMinimized)
    
    def mousePressEvent(self, event):
        """Allow dragging the frameless window"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position = event.globalPosition().toPoint()
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle window dragging"""
        if (event.buttons() == Qt.MouseButton.LeftButton and 
            hasattr(self, 'drag_start_position')):
            self.move(self.pos() + event.globalPosition().toPoint() - self.drag_start_position)
            self.drag_start_position = event.globalPosition().toPoint()
        super().mouseMoveEvent(event)
    
    def focusOutEvent(self, event):
        """Hide window when it loses focus (popup behavior)"""
        if self.settings.get('behavior/close_to_tray', True):
            # Small delay to prevent closing when clicking buttons
            QTimer.singleShot(100, self._check_focus_and_hide)
        super().focusOutEvent(event)
    
    def _check_focus_and_hide(self):
        """Check if window should hide after losing focus"""
        if not self.isActiveWindow() and not self.settings_dialog:
            self.hide()
            self.minimize_to_tray_requested.emit()