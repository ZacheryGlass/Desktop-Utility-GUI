"""
Tray View - UI component for system tray interactions.

This view handles the visual representation and user interactions
for the system tray icon and menu, while remaining "dumb" about
business logic.
"""
import logging
from typing import Optional, Dict, Any, List
from PyQt6.QtWidgets import (QSystemTrayIcon, QMenu, QWidget)
from PyQt6.QtCore import QObject, pyqtSignal, QTimer, Qt
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QBrush, QPen, QCursor, QAction

logger = logging.getLogger('Views.Tray')


class TrayView(QObject):
    """
    View component for system tray interactions.
    
    This view:
    - Displays the system tray icon and menu
    - Handles user interactions with tray elements
    - Emits signals for user actions
    - Updates display based on controller requests
    """
    
    # Signals for user interactions
    menu_action_triggered = pyqtSignal(dict)  # action data
    title_clicked = pyqtSignal()
    exit_requested = pyqtSignal()
    settings_requested = pyqtSignal()
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__()
        self.parent = parent
        
        # Create tray icon
        self.tray_icon = QSystemTrayIcon(parent)
        self.tray_icon.setToolTip("Desktop Utilities")
        
        # Create context menu
        self.context_menu = QMenu(parent)
        
        # Create and set icon
        self._create_tray_icon()
        
        # Connect signals
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.setContextMenu(self.context_menu)
        
        logger.info("TrayView initialized")
    
    def show_icon(self):
        """Show the tray icon"""
        self.tray_icon.show()
        logger.debug("Tray icon shown")
    
    def hide_icon(self):
        """Hide the tray icon"""
        self.tray_icon.hide()
        logger.debug("Tray icon hidden")
    
    def set_tooltip(self, tooltip: str):
        """Set the tray icon tooltip"""
        self.tray_icon.setToolTip(tooltip)
        logger.debug(f"Tray tooltip set: {tooltip}")
    
    def show_notification(self, title: str, message: str, 
                         icon_type: QSystemTrayIcon.MessageIcon = QSystemTrayIcon.MessageIcon.Information):
        """Show a system tray notification"""
        if self.tray_icon.supportsMessages():
            self.tray_icon.showMessage(title, message, icon_type, 3000)
            logger.debug(f"Notification shown: {title}")
        else:
            logger.debug("Notification requested but not supported")
    
    def supports_notifications(self) -> bool:
        """Check if system supports tray notifications"""
        return self.tray_icon.supportsMessages()
    
    def update_menu_structure(self, menu_structure: Dict[str, Any]):
        """Update the menu structure based on provided data"""
        logger.debug("Updating menu structure...")
        
        try:
            # Clear existing menu
            self.context_menu.clear()
            
            # Add title (clickable)
            title_text = menu_structure.get('title', 'Desktop Utilities')
            title_action = QAction(title_text, self.context_menu)
            title_action.triggered.connect(self.title_clicked.emit)
            self.context_menu.addAction(title_action)
            
            # Add separator
            self.context_menu.addSeparator()
            
            # Add menu items
            menu_items = menu_structure.get('items', [])
            for item_data in menu_items:
                self._add_menu_item(self.context_menu, item_data)
            
            # Add bottom separator and exit
            self.context_menu.addSeparator()
            exit_action = QAction("Exit", self.context_menu)
            exit_action.triggered.connect(self.exit_requested.emit)
            self.context_menu.addAction(exit_action)
            
            logger.debug(f"Menu updated with {len(menu_items)} items")
            
        except Exception as e:
            logger.error(f"Error updating menu structure: {e}")
    
    def _add_menu_item(self, parent_menu: QMenu, item_data: Dict[str, Any]):
        """Add a menu item based on item data"""
        item_type = item_data.get('type', 'action')
        text = item_data.get('text', '')
        enabled = item_data.get('enabled', True)
        
        if item_type == 'action':
            action = QAction(text, parent_menu)
            action.setEnabled(enabled)
            
            # Connect action if data is provided
            action_data = item_data.get('data')
            if action_data and enabled:
                action.triggered.connect(
                    lambda checked, data=action_data: self.menu_action_triggered.emit(data)
                )
            
            parent_menu.addAction(action)
            
        elif item_type == 'submenu':
            submenu = QMenu(text, parent_menu)
            
            # Add submenu items
            submenu_items = item_data.get('items', [])
            for subitem_data in submenu_items:
                self._add_menu_item(submenu, subitem_data)
            
            # Add submenu to parent
            parent_menu.addMenu(submenu)
            
        elif item_type == 'separator':
            parent_menu.addSeparator()
    
    def _create_tray_icon(self):
        """Create the tray icon programmatically"""
        try:
            # Create a simple icon programmatically
            pixmap = QPixmap(64, 64)
            pixmap.fill(Qt.GlobalColor.transparent)
            
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Draw a rounded rectangle background
            painter.setBrush(QBrush(Qt.GlobalColor.lightGray))
            painter.setPen(QPen(Qt.GlobalColor.darkCyan, 2))
            painter.drawRoundedRect(4, 4, 56, 56, 10, 10)
            
            # Draw "DU" text
            painter.setPen(QPen(Qt.GlobalColor.black, 2))
            font = painter.font()
            font.setPointSize(20)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "DU")
            
            painter.end()
            
            icon = QIcon(pixmap)
            self.tray_icon.setIcon(icon)
            
        except Exception as e:
            logger.error(f"Error creating tray icon: {e}")
            # Fallback to system icon
            from PyQt6.QtWidgets import QApplication
            app = QApplication.instance()
            if app:
                self.tray_icon.setIcon(app.style().standardIcon(
                    app.style().StandardPixmap.SP_ComputerIcon))
    
    def _on_tray_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            # Left click - show context menu at cursor position
            cursor_pos = QCursor.pos()
            self.context_menu.popup(cursor_pos)
        elif reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            # Double click also shows the menu
            self.context_menu.popup(self.tray_icon.geometry().center())
    
    def cleanup(self):
        """Clean up resources"""
        self.tray_icon.hide()
        logger.info("TrayView cleaned up")