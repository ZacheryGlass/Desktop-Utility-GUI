import logging
from typing import Optional, List, Dict, Any
from PyQt6.QtWidgets import (QSystemTrayIcon, QMenu, QApplication, 
                             QMessageBox, QWidget, QInputDialog)
from PyQt6.QtCore import QObject, pyqtSignal, QTimer, Qt, QRect
from PyQt6.QtGui import QIcon, QAction, QPixmap, QPainter, QBrush, QPen, QScreen, QCursor

from core.script_loader import ScriptLoader
from core.script_analyzer import ScriptInfo
from core.settings import SettingsManager
from core.hotkey_manager import HotkeyManager
from core.hotkey_registry import HotkeyRegistry

logger = logging.getLogger('GUI.TrayManager')

class TrayManager(QObject):
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
        self.script_menus = {}  # Track submenus for scripts with choices
        self.script_name_to_info = {}  # Map script names to ScriptInfo for hotkey execution
        
        # Initialize hotkey management
        self.hotkey_manager = HotkeyManager()
        self.hotkey_registry = HotkeyRegistry(self.settings)
        
        # Connect hotkey signals
        self.hotkey_manager.hotkey_triggered.connect(self._on_hotkey_triggered)
        self.hotkey_manager.registration_failed.connect(self._on_hotkey_registration_failed)
        
        # Create tray icon
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setToolTip("Desktop Utilities")
        
        # Create and set icon
        self._create_tray_icon()
        
        # Create context menu
        self.context_menu = QMenu(parent)
        # Apply initial menu styling (font will be updated via update_menu_font)
        self._update_menu_font()
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
        
        # Start hotkey manager
        self.hotkey_manager.start()
        
        logger.info("TrayManager initialized")
    
    def _get_effective_emoji_for_script(self, script_name: str) -> str:
        """Get effective emoji for script (custom or default)"""
        # First check for custom emoji
        custom_emoji = self.settings.get_script_emoji(script_name)
        if custom_emoji:
            return custom_emoji
        
        # Return default emoji based on script name/type
        return self._get_default_emoji(script_name)
    
    def _get_default_emoji(self, script_name: str) -> str:
        """Get default emoji based on script name"""
        name_lower = script_name.lower()
        
        # Audio related
        if any(word in name_lower for word in ['audio', 'sound', 'volume', 'speaker', 'microphone']):
            return '🔊'
        
        # Display related  
        if any(word in name_lower for word in ['display', 'monitor', 'screen', 'resolution']):
            return '🖥️'
        
        # Bluetooth related
        if any(word in name_lower for word in ['bluetooth', 'bt', 'wireless']):
            return '📶'
        
        # Power related
        if any(word in name_lower for word in ['power', 'battery', 'energy', 'plan']):
            return '⚡'
        
        # Network related
        if any(word in name_lower for word in ['network', 'wifi', 'internet', 'connection']):
            return '🌐'
        
        # System related
        if any(word in name_lower for word in ['system', 'registry', 'service']):
            return '⚙️'
        
        # File/folder related
        if any(word in name_lower for word in ['file', 'folder', 'directory', 'path']):
            return '📁'
        
        # Clipboard related
        if any(word in name_lower for word in ['clipboard', 'copy', 'paste']):
            return '📋'
        
        # Time/schedule related
        if any(word in name_lower for word in ['time', 'clock', 'schedule', 'timer']):
            return '⏰'
        
        # Process/task related
        if any(word in name_lower for word in ['process', 'task', 'kill', 'stop']):
            return '🔄'
        
        # Security related
        if any(word in name_lower for word in ['security', 'firewall', 'antivirus', 'scan']):
            return '🛡️'
        
        # Default fallback
        return '🔧'
    
    def _create_tray_icon(self):
        """Create the tray icon"""
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
            app = QApplication.instance()
            if app:
                self.tray_icon.setIcon(app.style().standardIcon(app.style().StandardPixmap.SP_ComputerIcon))
    
    def _update_menu_font(self):
        """Update menu font based on settings"""
        try:
            font_family = self.settings.get_font_family()
            font_size = self.settings.get_font_size()
            
            font = self.context_menu.font()
            if font_family and font_family != 'System Default':
                font.setFamily(font_family)
            font.setPointSize(font_size)
            
            self.context_menu.setFont(font)
            logger.debug(f"Updated menu font: {font_family}, {font_size}pt")
        except Exception as e:
            logger.error(f"Error updating menu font: {e}")
    
    def _setup_context_menu(self):
        """Setup the basic context menu structure"""
        # Title
        title_action = QAction("Desktop Utilities", self)
        title_action.setEnabled(False)
        title_font = title_action.font()
        title_font.setBold(True)
        title_action.setFont(title_font)
        self.context_menu.addAction(title_action)
        
        self.context_menu.addSeparator()
        
        # Scripts will be added here by update_scripts()
        
        # Bottom separator and settings
        self.context_menu.addSeparator()
        
        # Settings action
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.settings_requested.emit)
        self.context_menu.addAction(settings_action)
        
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
        self._register_hotkeys()
    
    def _rebuild_scripts_menu(self):
        # Clear everything except title and first separator
        self.script_actions.clear()
        self.script_menus.clear()
        self.script_name_to_info.clear()
        
        # Remove all actions except title and first separator
        actions = self.context_menu.actions()
        actions_to_keep = []
        
        # Keep title and first separator
        for i, action in enumerate(actions):
            if action.text() == "Desktop Utilities":
                actions_to_keep.append(action)
                # Also keep the separator right after title
                if i + 1 < len(actions) and actions[i + 1].isSeparator():
                    actions_to_keep.append(actions[i + 1])
                break
        
        # Keep bottom separator and settings/exit
        if len(actions) >= 3:
            actions_to_keep.extend(actions[-3:])  # separator, settings, exit
        
        # Remove all other actions
        for action in actions:
            if action not in actions_to_keep:
                self.context_menu.removeAction(action)
        
        # Clean up any orphaned submenus
        for menu in self.context_menu.findChildren(QMenu):
            if menu != self.context_menu:
                menu.deleteLater()
        
        # Add scripts
        if not self.scripts:
            no_scripts_action = QAction("No scripts available", self)
            no_scripts_action.setEnabled(False)
            # Insert before the bottom separator
            bottom_actions = self.context_menu.actions()[-3:]
            if bottom_actions:
                self.context_menu.insertAction(bottom_actions[0], no_scripts_action)
        else:
            # Add scripts
            bottom_actions = self.context_menu.actions()[-3:]
            for script_info in self.scripts:
                try:
                    display_name = self.script_loader.get_script_display_name(script_info)
                    self.script_name_to_info[display_name] = script_info
                    
                    # Determine if script needs arguments
                    if script_info.arguments:
                        # Script requires arguments - create submenu or input dialog
                        action = self._create_script_action_with_arguments(script_info, display_name)
                    else:
                        # Simple script - direct execution
                        action = self._create_simple_script_action(script_info, display_name)
                    
                    if action and bottom_actions:
                        self.context_menu.insertAction(bottom_actions[0], action)
                        self.script_actions[display_name] = action
                        
                except Exception as e:
                    logger.error(f"Error adding script {script_info.display_name}: {e}")
    
    def _create_simple_script_action(self, script_info: ScriptInfo, display_name: str) -> QAction:
        """Create action for simple scripts without arguments"""
        # Get emoji and create display text
        emoji = self._get_effective_emoji_for_script(display_name)
        # Use proper spacing instead of tabs for better alignment
        display_text = f"{emoji}  {display_name}" if emoji else display_name
        
        # Get status for display
        status = self.script_loader.get_script_status(script_info.file_path.stem)
        if status and status != "Ready":
            display_text += f" [{status}]"
        
        action = QAction(display_text, self)
        action.triggered.connect(lambda checked, s=script_info: self._execute_simple_script(s))
        return action
    
    def _create_script_action_with_arguments(self, script_info: ScriptInfo, display_name: str) -> QAction:
        """Create action for scripts that require arguments"""
        # Get emoji and create display text
        emoji = self._get_effective_emoji_for_script(display_name)
        # Use proper spacing instead of tabs for better alignment
        display_text = f"{emoji}  {display_name}" if emoji else display_name
        
        # Check if script has choice-based arguments (like cycle/select)
        has_choices = any(arg.choices for arg in script_info.arguments)
        
        if has_choices and len(script_info.arguments) == 1:
            # Single argument with choices - create submenu
            return self._create_choice_submenu(script_info, display_name, display_text)
        else:
            # Multiple arguments or complex input - use dialog
            action = QAction(display_text, self)
            action.triggered.connect(lambda checked, s=script_info: self._execute_script_with_dialog(s))
            return action
    
    def _create_choice_submenu(self, script_info: ScriptInfo, display_name: str, display_text: str) -> QAction:
        """Create submenu for scripts with choice arguments"""
        submenu = QMenu(display_text, self.context_menu)
        submenu.setFont(self.context_menu.font())
        
        arg_info = script_info.arguments[0]  # Single choice argument
        for choice in arg_info.choices:
            choice_action = QAction(choice, submenu)
            choice_action.triggered.connect(
                lambda checked, s=script_info, choice=choice: self._execute_script_with_choice(s, arg_info.name, choice)
            )
            submenu.addAction(choice_action)
        
        # Create the main action that shows the submenu
        main_action = QAction(display_text, self)
        main_action.setMenu(submenu)
        self.script_menus[display_name] = submenu
        
        return main_action
    
    def _execute_simple_script(self, script_info: ScriptInfo):
        """Execute a simple script without arguments"""
        try:
            logger.info(f"Executing simple script: {script_info.display_name}")
            
            result = self.script_loader.execute_script(script_info.file_path.stem)
            
            # Show notification if enabled
            if self.settings.should_show_notifications():
                if result.get('success'):
                    self.show_notification(
                        f"Script Executed: {script_info.display_name}",
                        result.get('message', 'Completed successfully')
                    )
                else:
                    self.show_notification(
                        f"Script Failed: {script_info.display_name}",
                        result.get('message', 'Execution failed'),
                        QSystemTrayIcon.MessageIcon.Warning
                    )
            
            self.script_executed.emit(script_info.display_name, result)
            
        except Exception as e:
            error_msg = f"Error executing script {script_info.display_name}: {str(e)}"
            logger.error(error_msg)
            if self.settings.should_show_notifications():
                self.show_notification(
                    f"Script Error: {script_info.display_name}",
                    str(e),
                    QSystemTrayIcon.MessageIcon.Critical
                )
    
    def _execute_script_with_choice(self, script_info: ScriptInfo, arg_name: str, choice: str):
        """Execute script with a specific choice value"""
        try:
            logger.info(f"Executing script {script_info.display_name} with {arg_name}={choice}")
            
            arguments = {arg_name: choice}
            result = self.script_loader.execute_script(script_info.file_path.stem, arguments)
            
            # Show notification if enabled
            if self.settings.should_show_notifications():
                if result.get('success'):
                    self.show_notification(
                        f"Script Executed: {script_info.display_name}",
                        result.get('message', f'Executed with {choice}')
                    )
                else:
                    self.show_notification(
                        f"Script Failed: {script_info.display_name}",
                        result.get('message', 'Execution failed'),
                        QSystemTrayIcon.MessageIcon.Warning
                    )
            
            self.script_executed.emit(script_info.display_name, result)
            
        except Exception as e:
            error_msg = f"Error executing script {script_info.display_name}: {str(e)}"
            logger.error(error_msg)
            if self.settings.should_show_notifications():
                self.show_notification(
                    f"Script Error: {script_info.display_name}",
                    str(e),
                    QSystemTrayIcon.MessageIcon.Critical
                )
    
    def _execute_script_with_dialog(self, script_info: ScriptInfo):
        """Execute script by showing input dialog for arguments"""
        try:
            # Get currently configured arguments
            current_args = self.script_loader.get_script_arguments(script_info.file_path.stem)
            
            # For now, execute with current settings
            # TODO: Add dialog for argument configuration
            logger.info(f"Executing script {script_info.display_name} with current arguments")
            
            result = self.script_loader.execute_script(script_info.file_path.stem, current_args)
            
            # Show notification if enabled
            if self.settings.should_show_notifications():
                if result.get('success'):
                    self.show_notification(
                        f"Script Executed: {script_info.display_name}",
                        result.get('message', 'Completed successfully')
                    )
                else:
                    self.show_notification(
                        f"Script Failed: {script_info.display_name}",
                        result.get('message', 'Execution failed'),
                        QSystemTrayIcon.MessageIcon.Warning
                    )
            
            self.script_executed.emit(script_info.display_name, result)
            
        except Exception as e:
            error_msg = f"Error executing script {script_info.display_name}: {str(e)}"
            logger.error(error_msg)
            if self.settings.should_show_notifications():
                self.show_notification(
                    f"Script Error: {script_info.display_name}",
                    str(e),
                    QSystemTrayIcon.MessageIcon.Critical
                )
    
    def _update_script_statuses(self):
        """Update script status displays in menu"""
        try:
            for display_name, action in self.script_actions.items():
                if display_name in self.script_name_to_info:
                    script_info = self.script_name_to_info[display_name]
                    status = self.script_loader.get_script_status(script_info.file_path.stem)
                    
                    # Update action text with current status
                    emoji = self._get_effective_emoji_for_script(display_name)
                    display_text = f"{emoji}  {display_name}" if emoji else display_name
                    if status and status != "Ready":
                        display_text += f" [{status}]"
                    
                    action.setText(display_text)
        except Exception as e:
            logger.debug(f"Error updating script statuses: {e}")
    
    def _register_hotkeys(self):
        """Register hotkeys for scripts"""
        try:
            # Clear existing hotkeys
            self.hotkey_manager.unregister_all()
            
            # Register hotkeys for each script
            for script_info in self.scripts:
                display_name = self.script_loader.get_script_display_name(script_info)
                hotkey = self.hotkey_registry.get_hotkey(display_name)
                if hotkey:
                    self.hotkey_manager.register_hotkey(display_name, hotkey)
                    logger.debug(f"Registered hotkey {hotkey} for script {display_name}")
            
        except Exception as e:
            logger.error(f"Error registering hotkeys: {e}")
    
    def _on_hotkey_triggered(self, script_name: str):
        """Handle hotkey triggered for a script"""
        try:
            logger.info(f"Hotkey triggered for script: {script_name}")
            if script_name in self.script_name_to_info:
                script_info = self.script_name_to_info[script_name]
                if script_info.arguments:
                    self._execute_script_with_dialog(script_info)
                else:
                    self._execute_simple_script(script_info)
        except Exception as e:
            logger.error(f"Error executing script from hotkey {script_name}: {e}")
    
    def _on_hotkey_registration_failed(self, script_name: str, hotkey: str, error: str):
        """Handle hotkey registration failure"""
        logger.warning(f"Failed to register hotkey {hotkey} for {script_name}: {error}")
    
    def _on_tray_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            # Left click - show context menu at cursor position
            cursor_pos = QCursor.pos()
            self.context_menu.popup(cursor_pos)
        elif reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            # Double click also shows the menu
            self.context_menu.popup(self.tray_icon.geometry().center())
    
    def show_notification(self, title: str, message: str, icon: QSystemTrayIcon.MessageIcon = QSystemTrayIcon.MessageIcon.Information):
        """Show system tray notification"""
        if self.tray_icon.supportsMessages():
            self.tray_icon.showMessage(title, message, icon, 3000)
    
    def update_font_settings(self):
        """Update font settings for tray menu"""
        self._update_menu_font()
        logger.debug("Font settings updated for tray menu")
    
    def refresh_hotkeys(self):
        """Refresh hotkey registrations (called when hotkeys change)"""
        logger.debug("Refreshing hotkeys...")
        self._register_hotkeys()
    
    def cleanup(self):
        """Cleanup resources"""
        if self.refresh_timer:
            self.refresh_timer.stop()
        
        if self.hotkey_manager:
            self.hotkey_manager.cleanup()
        
        self.tray_icon.hide()
        logger.info("TrayManager cleaned up")