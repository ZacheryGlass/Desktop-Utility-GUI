import logging
from typing import Optional, List, Dict, Any
from PyQt6.QtWidgets import (QSystemTrayIcon, QMenu, QApplication, 
                             QMessageBox, QWidget, QInputDialog)
from PyQt6.QtCore import QObject, pyqtSignal, QTimer, Qt, QRect
from PyQt6.QtGui import QIcon, QAction, QPixmap, QPainter, QBrush, QPen, QScreen

from core.base_script import UtilityScript
from core.script_loader import ScriptLoader
from core.settings import SettingsManager
from core.button_types import ButtonType
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
        self.script_menus = {}  # Track submenus for CYCLE/SELECT scripts
        self.script_name_to_instance = {}  # Map script names to instances for hotkey execution
        
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
    
    def _create_tray_icon(self):
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
    
    def _setup_context_menu(self):
        self.context_menu.clear()
        
        # Add title
        title_action = self.context_menu.addAction("Desktop Utilities")
        title_action.setEnabled(False)
        font = title_action.font()
        font.setBold(True)
        title_action.setFont(font)
        
        self.context_menu.addSeparator()
        
        # Scripts will be added dynamically here
        # (Scripts area - populated by _rebuild_scripts_menu)
        
        # Settings and Exit will be added at the end by _rebuild_scripts_menu
    
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
        self.script_name_to_instance.clear()
        
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
            self.context_menu.addAction(no_scripts_action)
        else:
            # Add scripts with tab-based alignment
            for script in self.scripts:
                try:
                    metadata = script.get_metadata()
                    original_name = metadata.get('name', 'Unknown Script')
                    button_type = metadata.get('button_type', ButtonType.RUN)
                    
                    # Get effective display name (custom or original)
                    display_name = self.script_loader.get_script_display_name(script)
                    
                    # Store script instance by original name for hotkey execution (hotkeys use original names)
                    self.script_name_to_instance[original_name] = script
                    
                    if button_type == ButtonType.RUN:
                        self._add_run_script(script, original_name, display_name, metadata)
                    elif button_type == ButtonType.TOGGLE:
                        self._add_toggle_script(script, original_name, display_name, metadata)
                    elif button_type == ButtonType.CYCLE:
                        self._add_cycle_script(script, original_name, display_name, metadata)
                    elif button_type == ButtonType.SELECT:
                        self._add_select_script(script, original_name, display_name, metadata)
                    elif button_type == ButtonType.NUMBER:
                        self._add_number_script(script, original_name, display_name, metadata)
                    elif button_type == ButtonType.TEXT_INPUT:
                        self._add_text_input_script(script, original_name, display_name, metadata)
                    elif button_type == ButtonType.SLIDER:
                        logger.info(f"Skipping deprecated SLIDER script: {display_name}")
                        continue
                    else:
                        self._add_run_script(script, original_name, display_name, metadata)
                        
                except Exception as e:
                    logger.error(f"Error adding script to tray menu: {e}")
        
        # Add final menu structure: Separator -> Settings -> Separator -> Exit
        self.context_menu.addSeparator()
        
        settings_action = QAction("Settings...", self)
        settings_action.triggered.connect(self.settings_requested.emit)
        self.context_menu.addAction(settings_action)
        
        self.context_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.exit_requested.emit)
        self.context_menu.addAction(exit_action)
    
    def _add_run_script(self, script: UtilityScript, original_name: str, display_name: str, metadata: dict):
        """Add a simple RUN script as a menu item"""
        # Get hotkey for this script (using original name)
        hotkey = self.hotkey_registry.get_hotkey(original_name)
        if hotkey:
            # Use tab character for alignment in monospace font, with visual formatting
            menu_text = f"{display_name}\t│ {hotkey}"
        else:
            menu_text = display_name
        
        action = QAction(menu_text, self)
        action.setToolTip(metadata.get('description', ''))
        action.triggered.connect(lambda checked, s=script: self._execute_script(s))
        
        self.script_actions[action] = script
        self.context_menu.addAction(action)
    
    def _add_toggle_script(self, script: UtilityScript, original_name: str, display_name: str, metadata: dict):
        """Add a TOGGLE script as a menu item showing current state"""
        # Get hotkey for this script (using original name)
        hotkey = self.hotkey_registry.get_hotkey(original_name)
        if hotkey:
            # Use tab character for alignment in monospace font, with visual formatting
            menu_text = f"{display_name}\t│ {hotkey}"
        else:
            menu_text = display_name
        
        action = QAction(menu_text, self)
        action.setToolTip(f"{metadata.get('description', '')} (Click to toggle)")
        action.triggered.connect(lambda checked, s=script: self._execute_toggle_script(s))
        
        self.script_actions[action] = script
        self.context_menu.addAction(action)
    
    def _add_cycle_script(self, script: UtilityScript, original_name: str, display_name: str, metadata: dict):
        """Add a CYCLE script as a submenu with all options"""
        button_options = metadata.get('button_options')
        if not button_options or not hasattr(button_options, 'options') or not button_options.options:
            # Fallback to simple execution if no options defined
            self._add_run_script(script, original_name, display_name, metadata)
            return
        
        # Create submenu for cycle options - include hotkey in submenu title
        hotkey = self.hotkey_registry.get_hotkey(original_name)
        if hotkey:
            # Use tab character for alignment in monospace font, with visual formatting
            submenu_title = f"{display_name}\t│ {hotkey}"
        else:
            submenu_title = display_name
        submenu = QMenu(submenu_title, self.context_menu)
        
        try:
            current_status = script.get_status()
        except:
            current_status = ""
        
        for option in button_options.options:
            option_action = QAction(option, self)
            option_action.setCheckable(True)
            
            # Check current option
            if current_status and (option.lower() in current_status.lower() or 
                                   current_status.lower() in option.lower()):
                option_action.setChecked(True)
            
            option_action.triggered.connect(
                lambda checked, s=script, opt=option: self._execute_script(s, opt)
            )
            
            self.script_actions[option_action] = script
            submenu.addAction(option_action)
        
        # Store the submenu for status updates
        self.script_menus[script] = submenu
        self.context_menu.addMenu(submenu)
    
    def _add_select_script(self, script: UtilityScript, original_name: str, display_name: str, metadata: dict):
        """Add a SELECT script as a submenu with all options"""
        button_options = metadata.get('button_options')
        if not button_options or not hasattr(button_options, 'options') or not button_options.options:
            # Fallback to simple execution if no options defined
            self._add_run_script(script, original_name, display_name, metadata)
            return
        
        # Create submenu for select options - include hotkey in submenu title
        hotkey = self.hotkey_registry.get_hotkey(original_name)
        if hotkey:
            # Use tab character for alignment in monospace font, with visual formatting
            submenu_title = f"{display_name}\t│ {hotkey}"
        else:
            submenu_title = display_name
        submenu = QMenu(submenu_title, self.context_menu)
        
        try:
            current_status = script.get_status()
        except:
            current_status = ""
        
        for option in button_options.options:
            option_action = QAction(option, self)
            option_action.setCheckable(True)
            
            # Check current option
            if current_status and (option.lower() in current_status.lower() or 
                                   current_status.lower() in option.lower()):
                option_action.setChecked(True)
            
            option_action.triggered.connect(
                lambda checked, s=script, opt=option: self._execute_script(s, opt)
            )
            
            self.script_actions[option_action] = script
            submenu.addAction(option_action)
        
        # Store the submenu for status updates
        self.script_menus[script] = submenu
        self.context_menu.addMenu(submenu)
    
    def _add_number_script(self, script: UtilityScript, original_name: str, display_name: str, metadata: dict):
        """Add a NUMBER script that shows input dialog when clicked"""
        # Get hotkey for this script (using original name)
        hotkey = self.hotkey_registry.get_hotkey(original_name)
        if hotkey:
            # Use tab character for alignment in monospace font, with visual formatting
            menu_text = f"{display_name}\t│ {hotkey}"
        else:
            menu_text = display_name
        
        action = QAction(menu_text, self)
        action.setToolTip(f"{metadata.get('description', '')} (Click to set value)")
        action.triggered.connect(lambda checked, s=script: self._execute_number_script(s, metadata))
        
        self.script_actions[action] = script
        self.context_menu.addAction(action)
    
    def _add_text_input_script(self, script: UtilityScript, original_name: str, display_name: str, metadata: dict):
        """Add a TEXT_INPUT script that shows input dialog when clicked"""
        # Get hotkey for this script (using original name)
        hotkey = self.hotkey_registry.get_hotkey(original_name)
        if hotkey:
            # Use tab character for alignment in monospace font, with visual formatting
            menu_text = f"{display_name}\t│ {hotkey}"
        else:
            menu_text = display_name
        
        action = QAction(menu_text, self)
        action.setToolTip(f"{metadata.get('description', '')} (Click to enter text)")
        action.triggered.connect(lambda checked, s=script: self._execute_text_input_script(s, metadata))
        
        self.script_actions[action] = script
        self.context_menu.addAction(action)
    
    def _execute_script(self, script: UtilityScript, *args, **kwargs):
        try:
            metadata = script.get_metadata()
            script_name = metadata.get('name', 'Unknown')
            
            logger.info(f"Executing script from tray: {script_name}")
            if args:
                logger.info(f"  Args: {args}")
            if kwargs:
                logger.info(f"  Kwargs: {kwargs}")
            
            # Execute script with provided parameters
            result = script.execute(*args, **kwargs)
            
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
    
    def _execute_toggle_script(self, script: UtilityScript):
        """Execute a toggle script by determining current state and flipping it"""
        try:
            status = script.get_status()
            current_state = status and status.lower() in ['on', 'enabled', 'true', 'active']
            # Toggle to opposite state
            self._execute_script(script, not current_state)
        except Exception as e:
            logger.error(f"Error toggling script: {e}")
            # Fallback to simple execution
            self._execute_script(script)
    
    def _execute_number_script(self, script: UtilityScript, metadata: dict):
        """Execute a number script by showing input dialog"""
        try:
            button_options = metadata.get('button_options')
            
            # Set up dialog parameters
            if button_options:
                min_val = getattr(button_options, 'min_value', None)
                max_val = getattr(button_options, 'max_value', None)
                decimals = getattr(button_options, 'decimals', 0)
                suffix = getattr(button_options, 'suffix', '')
            else:
                min_val = max_val = None
                decimals = 0
                suffix = ''
            
            # Get current value for default
            try:
                current_status = script.get_status()
                # Try to extract number from status
                import re
                numbers = re.findall(r'-?\d+\.?\d*', current_status)
                default_value = float(numbers[0]) if numbers else 0.0
            except:
                default_value = 0.0
            
            # Show input dialog
            if decimals > 0:
                value, ok = QInputDialog.getDouble(
                    None, 
                    f"Set {metadata.get('name', 'Value')}", 
                    f"Enter value{' (' + suffix + ')' if suffix else ''}:",
                    default_value,
                    min_val if min_val is not None else -2147483647,
                    max_val if max_val is not None else 2147483647,
                    decimals
                )
            else:
                value, ok = QInputDialog.getInt(
                    None,
                    f"Set {metadata.get('name', 'Value')}",
                    f"Enter value{' (' + suffix + ')' if suffix else ''}:",
                    int(default_value),
                    int(min_val) if min_val is not None else -2147483647,
                    int(max_val) if max_val is not None else 2147483647
                )
            
            if ok:
                self._execute_script(script, value)
                
        except Exception as e:
            logger.error(f"Error showing number input dialog: {e}")
            # Fallback to simple execution
            self._execute_script(script)
    
    def _execute_text_input_script(self, script: UtilityScript, metadata: dict):
        """Execute a text input script by showing input dialog"""
        try:
            button_options = metadata.get('button_options')
            
            if button_options:
                placeholder = getattr(button_options, 'placeholder', 'Enter text...')
                multiline = getattr(button_options, 'multiline', False)
            else:
                placeholder = 'Enter text...'
                multiline = False
            
            # Get current value for default
            try:
                current_status = script.get_status()
                default_text = current_status if current_status and current_status != 'Unknown' else ''
            except:
                default_text = ''
            
            # Show input dialog
            if multiline:
                text, ok = QInputDialog.getMultiLineText(
                    None,
                    f"Set {metadata.get('name', 'Text')}",
                    f"{placeholder}:",
                    default_text
                )
            else:
                text, ok = QInputDialog.getText(
                    None,
                    f"Set {metadata.get('name', 'Text')}",
                    f"{placeholder}:",
                    text=default_text
                )
            
            if ok and text:
                self._execute_script(script, text)
                
        except Exception as e:
            logger.error(f"Error showing text input dialog: {e}")
            # Fallback to simple execution
            self._execute_script(script)
    
    def _update_script_statuses(self):
        """Update script status display in menu items"""
        logger.debug(f"Updating status for {len(self.script_actions)} script actions and {len(self.script_menus)} script menus")
        
        # Track which scripts we've already processed to avoid duplicates
        processed_scripts = set()
        
        # Update CYCLE and SELECT scripts via their submenus
        for script, submenu in self.script_menus.items():
            if script in processed_scripts:
                continue
            processed_scripts.add(script)
            
            try:
                # Update submenu title to show hotkey with alignment
                metadata = script.get_metadata()
                original_name = metadata.get('name', 'Unknown Script')
                display_name = self.script_loader.get_script_display_name(script)
                hotkey = self.hotkey_registry.get_hotkey(original_name)
                if hotkey:
                    # Use tab character for alignment in monospace font
                    submenu_title = f"{display_name}\t| {hotkey}"
                else:
                    submenu_title = display_name
                submenu.setTitle(submenu_title)
                
                # Update option checkmarks based on current status
                current_status = script.get_status()
                for menu_action in submenu.actions():
                    option_text = menu_action.text()
                    if current_status and (option_text.lower() in current_status.lower() or 
                                         current_status.lower() in option_text.lower()):
                        menu_action.setChecked(True)
                    else:
                        menu_action.setChecked(False)
            except Exception as e:
                logger.error(f"Error updating submenu status for script: {e}")
        
        # Update other script types (RUN, TOGGLE, NUMBER, TEXT_INPUT)
        for action, script in self.script_actions.items():
            if script in processed_scripts:
                continue  # Skip CYCLE/SELECT scripts already processed above
                
            try:
                metadata = script.get_metadata()
                original_name = metadata.get('name', 'Unknown Script')
                display_name = self.script_loader.get_script_display_name(script)
                button_type = metadata.get('button_type', ButtonType.RUN)
                
                # Update action text to show hotkey with alignment
                hotkey = self.hotkey_registry.get_hotkey(original_name)
                if hotkey:
                    # Use tab character for alignment in monospace font, with visual formatting
                    action.setText(f"{display_name}\t│ {hotkey}")
                else:
                    action.setText(display_name)
                processed_scripts.add(script)
                        
            except Exception as e:
                logger.error(f"Error updating status for script action: {e}")
    
    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            # Left click - show context menu (same as right click)
            self._show_context_menu()
        elif reason == QSystemTrayIcon.ActivationReason.Context:
            # Right click - context menu (handled automatically)
            pass
        elif reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            # Double click - show context menu
            self._show_context_menu()
    
    def _show_context_menu(self):
        """Show the context menu at cursor position"""
        cursor_pos = self.parent.cursor().pos() if self.parent else None
        if cursor_pos:
            self.context_menu.popup(cursor_pos)
        else:
            # Fallback to showing at tray icon position
            self.context_menu.popup(self.tray_icon.geometry().center())
    
    
    def show_notification(self, title: str, message: str, 
                         icon: QSystemTrayIcon.MessageIcon = QSystemTrayIcon.MessageIcon.Information):
        if self.tray_icon.isSystemTrayAvailable():
            self.tray_icon.showMessage(title, message, icon, 3000)
    
    def _update_menu_font(self):
        """Update the menu font based on application settings"""
        font_family = self.settings.get_font_family()
        font_size = self.settings.get_font_size()
        
        # For menu alignment, we need monospace font for proper tab alignment
        # But we can use the user's selected font if it's monospace, or fallback to system monospace
        if font_family and font_family != 'System Default':
            # Check if the selected font is monospace-compatible
            from PyQt6.QtGui import QFontMetrics, QFont
            test_font = QFont(font_family, font_size)
            metrics = QFontMetrics(test_font)
            
            # Test if characters have similar widths (monospace check)
            w_width = metrics.horizontalAdvance('W')
            i_width = metrics.horizontalAdvance('i')
            
            if abs(w_width - i_width) < 2:  # Close enough to be monospace
                menu_font = f"'{font_family}'"
            else:
                # Use user font but add monospace fallback for alignment
                menu_font = f"'{font_family}', 'Courier New', 'Consolas', monospace"
        else:
            # System default - use monospace for alignment
            menu_font = "'Courier New', 'Consolas', 'Lucida Console', monospace"
        
        self.context_menu.setStyleSheet(f"""
            QMenu {{
                font-family: {menu_font};
                font-size: {font_size}pt;
                background-color: #ffffff;
                border: 1px solid #cccccc;
                padding: 2px;
            }}
            QMenu::item {{
                padding: 4px 12px;
                color: #000000;
                background-color: transparent;
                border: none;
            }}
            QMenu::item:selected {{
                background-color: #0078d4;
                color: #ffffff;
            }}
            QMenu::item:disabled {{
                color: #888888;
            }}
            QMenu::separator {{
                height: 1px;
                background: #e0e0e0;
                margin: 2px 0px;
            }}
        """)
        
        logger.info(f"Updated tray menu font: {menu_font}, {font_size}pt")
    
    def update_font_settings(self):
        """Public method to update font settings when they change"""
        self._update_menu_font()
    
    def cleanup(self):
        self.refresh_timer.stop()
        self.hotkey_manager.stop()
        self.tray_icon.hide()
    
    def _register_hotkeys(self):
        """Register all configured hotkeys for scripts"""
        if not self.script_loader:
            return
        
        # Validate mappings first (remove orphaned ones)
        self.hotkey_registry.validate_mappings(self.script_loader)
        
        # Clear existing hotkeys
        self.hotkey_manager.unregister_all()
        
        # Register each configured hotkey
        hotkey_mappings = self.hotkey_registry.get_all_mappings()
        
        for script_name, hotkey_string in hotkey_mappings.items():
            if script_name in self.script_name_to_instance:
                success = self.hotkey_manager.register_hotkey(script_name, hotkey_string)
                if success:
                    logger.info(f"Registered hotkey {hotkey_string} for {script_name}")
                else:
                    logger.warning(f"Failed to register hotkey {hotkey_string} for {script_name}")
            else:
                logger.warning(f"Script {script_name} has hotkey but is not loaded")
    
    def refresh_hotkeys(self):
        """Refresh hotkey registrations (called when settings change)"""
        self._register_hotkeys()
    
    def _on_hotkey_triggered(self, script_name: str, hotkey_string: str):
        """Handle hotkey trigger events"""
        logger.info(f"Hotkey {hotkey_string} triggered for script {script_name}")
        
        # Find the script instance
        script = self.script_name_to_instance.get(script_name)
        
        if script:
            # Execute the script
            self._execute_script(script)
        else:
            logger.error(f"Script {script_name} not found for hotkey execution")
            if self.settings.should_show_notifications():
                self.show_notification(
                    "Hotkey Error",
                    f"Script '{script_name}' not found",
                    QSystemTrayIcon.MessageIcon.Warning
                )
    
    def _on_hotkey_registration_failed(self, hotkey_string: str, error_message: str):
        """Handle hotkey registration failures"""
        logger.error(f"Hotkey registration failed: {hotkey_string} - {error_message}")
        
        # Always show registration failures as they're important feedback
        self.show_notification(
            "Hotkey Registration Failed",
            f"{hotkey_string}: {error_message}",
            QSystemTrayIcon.MessageIcon.Warning
        )