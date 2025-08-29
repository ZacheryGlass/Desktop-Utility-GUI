import logging
from typing import Optional, List, Dict, Any
from PyQt6.QtWidgets import (QSystemTrayIcon, QMenu, QApplication, 
                             QMessageBox, QWidget)
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
        refresh_interval = self.settings.get_status_refresh_seconds() * 1000  # Convert to milliseconds
        self.refresh_timer.start(refresh_interval)
        
        # Start hotkey manager
        self.hotkey_manager.start()
        
        logger.info("TrayManager initialized")
    
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
        # Title (clickable to open settings)
        title_action = QAction("Desktop Utilities", self)
        title_action.triggered.connect(self.settings_requested.emit)
        title_font = title_action.font()
        title_font.setBold(True)
        title_action.setFont(title_font)
        self.context_menu.addAction(title_action)
        
        self.context_menu.addSeparator()
        
        # Scripts will be added here by update_scripts()
        
        # Bottom separator and exit
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
        
        # Refresh external scripts to ensure we have the latest changes
        self.script_loader.refresh_external_scripts()
        
        # Discover all scripts
        all_scripts = self.script_loader.discover_scripts()
        
        # Filter out disabled native scripts and missing external scripts
        self.scripts = self._filter_available_scripts(all_scripts)
        
        self._rebuild_scripts_menu()
        self._register_hotkeys()
    
    def _filter_available_scripts(self, all_scripts):
        """Filter out disabled native scripts and handle missing external scripts"""
        filtered_scripts = []
        disabled_scripts = self.settings.get_disabled_scripts()
        external_scripts = self.settings.get_external_scripts()
        
        for script_info in all_scripts:
            script_name = script_info.display_name
            is_external = script_name in external_scripts
            
            # Skip disabled native scripts (external scripts are never "disabled", only removed)
            if not is_external and script_name in disabled_scripts:
                logger.debug(f"Filtering out disabled native script: {script_name}")
                continue
            
            # For external scripts, check if the file still exists
            if is_external:
                script_path = external_scripts.get(script_name)
                if not self.settings.validate_external_script_path(script_path):
                    logger.warning(f"Filtering out missing external script: {script_name} -> {script_path}")
                    continue
            
            filtered_scripts.append(script_info)
        
        logger.info(f"Filtered scripts: {len(filtered_scripts)} available out of {len(all_scripts)} total")
        return filtered_scripts
    
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
        
        # Keep bottom separator and exit
        if len(actions) >= 2:
            actions_to_keep.extend(actions[-2:])  # separator, exit
        
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
            bottom_actions = self.context_menu.actions()[-2:]
            if bottom_actions:
                self.context_menu.insertAction(bottom_actions[0], no_scripts_action)
        else:
            # Add scripts
            bottom_actions = self.context_menu.actions()[-2:]
            for script_info in self.scripts:
                try:
                    display_name = self.script_loader.get_script_display_name(script_info)
                    self.script_name_to_info[display_name] = script_info
                    
                    # Check if script needs configuration or has presets
                    script_name = script_info.file_path.stem
                    has_presets = self.settings.has_script_presets(script_name)
                    needs_config = script_info.needs_configuration and not has_presets
                    
                    if script_info.arguments and has_presets:
                        # Script has presets - create preset submenu
                        action = self._create_preset_submenu_action(script_info, display_name)
                    elif script_info.arguments or needs_config:
                        # Script needs configuration - show warning and config option
                        action = self._create_script_action_needing_config(script_info, display_name, needs_config)
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
        display_text = display_name
        
        # External scripts no longer get visual indicators
        
        # Get status for display
        status = self.script_loader.get_script_status(display_name)
        if status and status != "Ready":
            display_text += f" [{status}]"
        
        action = QAction(display_text, self)
        action.triggered.connect(lambda checked, s=script_info: self._execute_simple_script(s))
        return action
    
    def _create_script_action_with_arguments(self, script_info: ScriptInfo, display_name: str) -> QAction:
        """Create action for scripts that require arguments"""
        display_text = display_name
        
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
    
    def _create_script_action_needing_config(self, script_info: ScriptInfo, display_name: str, needs_config: bool) -> QAction:
        """Create action for scripts that need configuration"""
        if needs_config:
            display_text = f"⚠️ {display_name} (needs config)"
        else:
            display_text = display_name
        
        # External scripts no longer get visual indicators
        
        action = QAction(display_text, self)
        action.triggered.connect(lambda checked, s=script_info: self._handle_script_needing_config(s))
        return action
    
    def _create_preset_submenu_action(self, script_info: ScriptInfo, display_name: str) -> QAction:
        """Create submenu action for scripts with presets"""
        script_name = script_info.file_path.stem
        presets = self.settings.get_script_presets(script_name)
        
        if not presets:
            # Fallback to simple action if no presets
            return self._create_simple_script_action(script_info, display_name)
        
        # External scripts no longer get visual indicators
        menu_title = display_name
        
        submenu = QMenu(menu_title, self.context_menu)
        submenu.setFont(self.context_menu.font())
        
        # Add preset options
        for preset_name in presets.keys():
            preset_action = QAction(preset_name, submenu)
            preset_action.triggered.connect(
                lambda checked, s=script_info, preset=preset_name: self._execute_script_with_preset(s, preset)
            )
            submenu.addAction(preset_action)
        
        # Add separator and configure option
        submenu.addSeparator()
        config_action = QAction("Configure Presets...", submenu)
        config_action.triggered.connect(
            lambda checked, s=script_info: self._open_preset_configuration(s)
        )
        submenu.addAction(config_action)
        
        # Create main action
        main_action = QAction(menu_title, self)
        main_action.setMenu(submenu)
        self.script_menus[display_name] = submenu
        
        return main_action
    
    def _execute_simple_script(self, script_info: ScriptInfo):
        """Execute a simple script without arguments"""
        try:
            logger.info(f"Executing simple script: {script_info.display_name}")
            
            # For external scripts, use the display name; for default scripts, use file stem
            script_key = script_info.display_name if self.script_loader.is_external_script(script_info.display_name) else script_info.file_path.stem
            result = self.script_loader.execute_script(script_key)
            
            # Show notification if enabled for this script
            if self.settings.should_show_script_notifications(script_key):
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
            script_key = script_info.display_name if self.script_loader.is_external_script(script_info.display_name) else script_info.file_path.stem
            if self.settings.should_show_script_notifications(script_key):
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
            # For external scripts, use the display name; for default scripts, use file stem
            script_key = script_info.display_name if self.script_loader.is_external_script(script_info.display_name) else script_info.file_path.stem
            result = self.script_loader.execute_script(script_key, arguments)
            
            # Show notification if enabled for this script
            if self.settings.should_show_script_notifications(script_key):
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
            script_key = script_info.display_name if self.script_loader.is_external_script(script_info.display_name) else script_info.file_path.stem
            if self.settings.should_show_script_notifications(script_key):
                self.show_notification(
                    f"Script Error: {script_info.display_name}",
                    str(e),
                    QSystemTrayIcon.MessageIcon.Critical
                )
    
    def _execute_script_with_dialog(self, script_info: ScriptInfo):
        """Execute script by showing input dialog for arguments"""
        try:
            # For external scripts, use the display name; for default scripts, use file stem
            script_key = script_info.display_name if self.script_loader.is_external_script(script_info.display_name) else script_info.file_path.stem
            
            # Get currently configured arguments
            current_args = self.script_loader.get_script_arguments(script_key)
            
            # For now, execute with current settings
            # TODO: Implement argument configuration dialog for scripts that need user input
            #       This should show before execution if script has configurable arguments
            logger.info(f"Executing script {script_info.display_name} with current arguments")
            
            result = self.script_loader.execute_script(script_key, current_args)
            
            # Show notification if enabled for this script
            if self.settings.should_show_script_notifications(script_key):
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
            script_key = script_info.display_name if self.script_loader.is_external_script(script_info.display_name) else script_info.file_path.stem
            if self.settings.should_show_script_notifications(script_key):
                self.show_notification(
                    f"Script Error: {script_info.display_name}",
                    str(e),
                    QSystemTrayIcon.MessageIcon.Critical
                )
    
    def _execute_script_with_preset(self, script_info: ScriptInfo, preset_name: str):
        """Execute script with a specific preset configuration"""
        try:
            # For external scripts, use the display name; for default scripts, use file stem
            script_key = script_info.display_name if self.script_loader.is_external_script(script_info.display_name) else script_info.file_path.stem
            preset_args = self.settings.get_preset_arguments(script_key, preset_name)
            
            logger.info(f"Executing script {script_info.display_name} with preset '{preset_name}': {preset_args}")
            
            result = self.script_loader.execute_script(script_key, preset_args)
            
            # Show notification if enabled for this script
            if self.settings.should_show_script_notifications(script_key):
                if result.get('success'):
                    self.show_notification(
                        f"Script Executed: {script_info.display_name}",
                        f"Used preset: {preset_name}"
                    )
                else:
                    self.show_notification(
                        f"Script Failed: {script_info.display_name}",
                        result.get('message', 'Execution failed'),
                        QSystemTrayIcon.MessageIcon.Warning
                    )
            
            self.script_executed.emit(script_info.display_name, result)
            
        except Exception as e:
            error_msg = f"Error executing script {script_info.display_name} with preset {preset_name}: {str(e)}"
            logger.error(error_msg)
            script_key = script_info.display_name if self.script_loader.is_external_script(script_info.display_name) else script_info.file_path.stem
            if self.settings.should_show_script_notifications(script_key):
                self.show_notification(
                    f"Script Error: {script_info.display_name}",
                    str(e),
                    QSystemTrayIcon.MessageIcon.Critical
                )
    
    def _handle_script_needing_config(self, script_info: ScriptInfo):
        """Handle click on script that needs configuration"""
        # For external scripts, use the display name; for default scripts, use file stem
        script_key = script_info.display_name if self.script_loader.is_external_script(script_info.display_name) else script_info.file_path.stem
        
        # Check if script has any presets now (might have been configured since menu creation)
        if self.settings.has_script_presets(script_key):
            # Script has presets now, refresh menu
            self.update_scripts()
            return
        
        # Show message about needing configuration
        from PyQt6.QtWidgets import QMessageBox
        msg = QMessageBox(QMessageBox.Icon.Information, 
                         "Script Configuration Needed",
                         f"The script '{script_info.display_name}' requires configuration before it can be run.\n\n"
                         f"Please set up presets in the Settings dialog.",
                         QMessageBox.StandardButton.Ok)
        msg.exec()
        
        # Open settings dialog to preset tab
        self._open_preset_configuration(script_info)
    
    def _open_preset_configuration(self, script_info: ScriptInfo):
        """Open the preset configuration dialog for a script"""
        # This will be implemented when we create the settings dialog UI
        # For now, emit a signal to open settings
        self.settings_requested.emit()
    
    def _update_script_statuses(self):
        """Update script status displays in menu"""
        try:
            for display_name, action in self.script_actions.items():
                if display_name in self.script_name_to_info:
                    script_info = self.script_name_to_info[display_name]
                    # For external scripts, use the display name; for default scripts, use file stem
                    script_key = display_name if self.script_loader.is_external_script(display_name) else script_info.file_path.stem
                    status = self.script_loader.get_script_status(script_key)
                    
                    display_text = display_name
                    # External scripts no longer get visual indicators
                    
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
            self.hotkey_manager.stop()
        
        self.tray_icon.hide()
        logger.info("TrayManager cleaned up")
