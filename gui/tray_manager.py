import logging
from typing import Optional, List, Dict, Any
from PyQt6.QtWidgets import (QSystemTrayIcon, QMenu, QApplication, 
                             QMessageBox, QWidget)
from PyQt6.QtCore import QObject, pyqtSignal, QTimer, Qt, QRect
from PyQt6.QtGui import QIcon, QAction, QPixmap, QPainter, QBrush, QPen, QScreen

from core.base_script import UtilityScript
from core.script_loader import ScriptLoader
from core.settings import SettingsManager

logger = logging.getLogger('GUI.TrayManager')

class TrayManager(QObject):
    show_window_requested = pyqtSignal()
    show_window_bottom_right = pyqtSignal()
    hide_window_requested = pyqtSignal()
    exit_requested = pyqtSignal()
    settings_requested = pyqtSignal()
    script_executed = pyqtSignal(str, dict)
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.parent = parent
        self.settings = SettingsManager()
        self.script_loader = None
        self.scripts = []
        self.script_actions = {}
        
        # Create tray icon
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setToolTip("Desktop Utilities")
        
        # Create and set icon
        self._create_tray_icon()
        
        # Create context menu
        self.context_menu = QMenu(parent)
        self._setup_context_menu()
        
        # Connect signals
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.setContextMenu(self.context_menu)
        
        # Show tray icon
        self.tray_icon.show()
        
        # Setup refresh timer for script status
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._update_script_statuses)
        self.refresh_timer.start(5000)  # Update every 5 seconds
        
        logger.info("TrayManager initialized")
    
    def _create_tray_icon(self):
        # Create a simple icon programmatically
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw a rounded rectangle background
        theme = self.settings.get_theme()
        if theme == 'dark':
            painter.setBrush(QBrush(Qt.GlobalColor.darkGray))
        else:
            painter.setBrush(QBrush(Qt.GlobalColor.lightGray))
        
        painter.setPen(QPen(Qt.GlobalColor.darkCyan, 2))
        painter.drawRoundedRect(4, 4, 56, 56, 10, 10)
        
        # Draw "DU" text
        painter.setPen(QPen(Qt.GlobalColor.white if theme == 'dark' else Qt.GlobalColor.black, 2))
        font = painter.font()
        font.setPointSize(20)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "DU")
        
        painter.end()
        
        icon = QIcon(pixmap)
        self.tray_icon.setIcon(icon)
    
    def _setup_context_menu(self):
        self.context_menu.clear()
        
        # Add title
        title_action = self.context_menu.addAction("Desktop Utilities")
        title_action.setEnabled(False)
        font = title_action.font()
        font.setBold(True)
        title_action.setFont(font)
        
        self.context_menu.addSeparator()
        
        # Add show/hide action
        self.toggle_window_action = QAction("Show Window", self)
        self.toggle_window_action.triggered.connect(self._toggle_window_bottom_right)
        self.context_menu.addAction(self.toggle_window_action)
        
        self.context_menu.addSeparator()
        
        # Scripts section
        scripts_label = self.context_menu.addAction("Scripts")
        scripts_label.setEnabled(False)
        
        # Scripts will be added dynamically
        self.scripts_menu = QMenu("Quick Actions", self.context_menu)
        self.context_menu.addMenu(self.scripts_menu)
        
        self.context_menu.addSeparator()
        
        # Settings action
        settings_action = QAction("Settings...", self)
        settings_action.triggered.connect(self.settings_requested.emit)
        self.context_menu.addAction(settings_action)
        
        # Theme toggle
        self.theme_action = QAction("Switch to Light Theme", self)
        self.theme_action.triggered.connect(self._toggle_theme)
        self._update_theme_action()
        self.context_menu.addAction(self.theme_action)
        
        self.context_menu.addSeparator()
        
        # Exit action
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.exit_requested.emit)
        self.context_menu.addAction(exit_action)
    
    def set_script_loader(self, script_loader: ScriptLoader):
        self.script_loader = script_loader
        self.update_scripts()
    
    def update_scripts(self):
        if not self.script_loader:
            return
        
        self.scripts = self.script_loader.discover_scripts()
        self._rebuild_scripts_menu()
    
    def _rebuild_scripts_menu(self):
        self.scripts_menu.clear()
        self.script_actions.clear()
        
        if not self.scripts:
            no_scripts_action = self.scripts_menu.addAction("No scripts available")
            no_scripts_action.setEnabled(False)
            return
        
        for script in self.scripts:
            try:
                metadata = script.get_metadata()
                script_name = metadata.get('name', 'Unknown Script')
                
                # Create submenu for scripts with multiple actions
                script_action = QAction(script_name, self)
                script_action.setToolTip(metadata.get('description', ''))
                
                # Store script reference
                self.script_actions[script_action] = script
                
                # Connect to handler
                script_action.triggered.connect(lambda checked, s=script: self._execute_script(s))
                
                # Add status to the action text if available
                try:
                    status = script.get_status()
                    if status and status != 'Unknown':
                        script_action.setText(f"{script_name} [{status}]")
                except:
                    pass
                
                self.scripts_menu.addAction(script_action)
                
            except Exception as e:
                logger.error(f"Error adding script to tray menu: {e}")
    
    def _execute_script(self, script: UtilityScript):
        try:
            metadata = script.get_metadata()
            script_name = metadata.get('name', 'Unknown')
            
            logger.info(f"Executing script from tray: {script_name}")
            
            # For scripts that need parameters, we'll use default or last values
            # This is a simplified execution for tray menu
            result = script.execute()
            
            # Show notification if enabled
            if self.settings.should_show_notifications():
                if result.get('success'):
                    self.show_notification(
                        f"Script Executed: {script_name}",
                        result.get('message', 'Completed successfully')
                    )
                else:
                    self.show_notification(
                        f"Script Failed: {script_name}",
                        result.get('message', 'Execution failed'),
                        QSystemTrayIcon.MessageIcon.Warning
                    )
            
            self.script_executed.emit(script_name, result)
            
            # Update script status in menu
            self._update_script_statuses()
            
        except Exception as e:
            logger.error(f"Error executing script from tray: {e}")
            if self.settings.should_show_notifications():
                self.show_notification(
                    "Script Error",
                    str(e),
                    QSystemTrayIcon.MessageIcon.Critical
                )
    
    def _update_script_statuses(self):
        for action, script in self.script_actions.items():
            try:
                metadata = script.get_metadata()
                script_name = metadata.get('name', 'Unknown Script')
                status = script.get_status()
                
                if status and status != 'Unknown':
                    action.setText(f"{script_name} [{status}]")
                else:
                    action.setText(script_name)
            except:
                pass
    
    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            # Left click - toggle window in bottom right
            self._toggle_window_bottom_right()
        elif reason == QSystemTrayIcon.ActivationReason.Context:
            # Right click - context menu (handled automatically)
            pass
        elif reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            # Double click - show window in bottom right
            self.show_window_bottom_right.emit()
    
    def _toggle_window(self):
        if self.parent and self.parent.isVisible():
            self.hide_window_requested.emit()
            self.toggle_window_action.setText("Show Window")
        else:
            self.show_window_requested.emit()
            self.toggle_window_action.setText("Hide Window")
    
    def _toggle_window_bottom_right(self):
        if self.parent and self.parent.isVisible():
            self.hide_window_requested.emit()
            self.toggle_window_action.setText("Show Window")
        else:
            self.show_window_bottom_right.emit()
            self.toggle_window_action.setText("Hide Window")
    
    def _toggle_theme(self):
        current_theme = self.settings.get_theme()
        new_theme = 'light' if current_theme == 'dark' else 'dark'
        self.settings.set_theme(new_theme)
        self._update_theme_action()
        self._create_tray_icon()  # Recreate icon with new theme
    
    def _update_theme_action(self):
        current_theme = self.settings.get_theme()
        if current_theme == 'dark':
            self.theme_action.setText("Switch to Light Theme")
        else:
            self.theme_action.setText("Switch to Dark Theme")
    
    def show_notification(self, title: str, message: str, 
                         icon: QSystemTrayIcon.MessageIcon = QSystemTrayIcon.MessageIcon.Information):
        if self.tray_icon.isSystemTrayAvailable():
            self.tray_icon.showMessage(title, message, icon, 3000)
    
    def set_window_visible(self, visible: bool):
        if visible:
            self.toggle_window_action.setText("Hide Window")
        else:
            self.toggle_window_action.setText("Show Window")
    
    def get_bottom_right_position(self) -> QRect:
        """Calculate bottom right position for the compact window"""
        if not self.parent:
            return QRect(0, 0, 280, 200)
        
        # Get primary screen
        screen = QApplication.primaryScreen()
        if not screen:
            return QRect(0, 0, 280, 200)
        
        screen_geometry = screen.availableGeometry()
        window_size = self.parent.size()
        
        # Position compact window in bottom right with minimal padding
        padding = 10  # Reduced padding for popup feel
        x = screen_geometry.right() - window_size.width() - padding
        y = screen_geometry.bottom() - window_size.height() - padding
        
        return QRect(x, y, window_size.width(), window_size.height())
    
    def cleanup(self):
        self.refresh_timer.stop()
        self.tray_icon.hide()