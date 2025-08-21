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
    
    def _rebuild_scripts_menu(self):
        # Clear everything except title and first separator
        self.script_actions.clear()
        self.script_menus.clear()
        
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
            for script in self.scripts:
                try:
                    metadata = script.get_metadata()
                    script_name = metadata.get('name', 'Unknown Script')
                    button_type = metadata.get('button_type', ButtonType.RUN)
                    
                    if button_type == ButtonType.RUN:
                        self._add_run_script(script, script_name, metadata)
                    elif button_type == ButtonType.TOGGLE:
                        self._add_toggle_script(script, script_name, metadata)
                    elif button_type == ButtonType.CYCLE:
                        self._add_cycle_script(script, script_name, metadata)
                    elif button_type == ButtonType.SELECT:
                        self._add_select_script(script, script_name, metadata)
                    elif button_type == ButtonType.NUMBER:
                        self._add_number_script(script, script_name, metadata)
                    elif button_type == ButtonType.TEXT_INPUT:
                        self._add_text_input_script(script, script_name, metadata)
                    elif button_type == ButtonType.SLIDER:
                        logger.info(f"Skipping deprecated SLIDER script: {script_name}")
                        continue
                    else:
                        self._add_run_script(script, script_name, metadata)
                        
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
    
    def _add_run_script(self, script: UtilityScript, script_name: str, metadata: dict):
        """Add a simple RUN script as a menu item"""
        try:
            status = script.get_status_display()
            if status and status != 'Unknown':
                display_name = f"{script_name} [{status}]"
            else:
                display_name = script_name
        except:
            display_name = script_name
        
        action = QAction(display_name, self)
        action.setToolTip(metadata.get('description', ''))
        action.triggered.connect(lambda checked, s=script: self._execute_script(s))
        
        self.script_actions[action] = script
        self.context_menu.addAction(action)
    
    def _add_toggle_script(self, script: UtilityScript, script_name: str, metadata: dict):
        """Add a TOGGLE script as a menu item showing current state"""
        try:
            status = script.get_status()
            is_on = status and status.lower() in ['on', 'enabled', 'true', 'active']
            state_text = "ON" if is_on else "OFF"
            display_name = f"{script_name} [{state_text}]"
        except:
            display_name = f"{script_name} [Unknown]"
        
        action = QAction(display_name, self)
        action.setToolTip(f"{metadata.get('description', '')} (Click to toggle)")
        action.triggered.connect(lambda checked, s=script: self._execute_toggle_script(s))
        
        self.script_actions[action] = script
        self.context_menu.addAction(action)
    
    def _add_cycle_script(self, script: UtilityScript, script_name: str, metadata: dict):
        """Add a CYCLE script as a submenu with all options"""
        button_options = metadata.get('button_options')
        if not button_options or not hasattr(button_options, 'options') or not button_options.options:
            # Fallback to simple execution if no options defined
            self._add_run_script(script, script_name, metadata)
            return
        
        # Create submenu for cycle options
        submenu = QMenu(script_name, self.context_menu)
        
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
    
    def _add_select_script(self, script: UtilityScript, script_name: str, metadata: dict):
        """Add a SELECT script as a submenu with all options"""
        button_options = metadata.get('button_options')
        if not button_options or not hasattr(button_options, 'options') or not button_options.options:
            # Fallback to simple execution if no options defined
            self._add_run_script(script, script_name, metadata)
            return
        
        # Create submenu for select options
        submenu = QMenu(script_name, self.context_menu)
        
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
    
    def _add_number_script(self, script: UtilityScript, script_name: str, metadata: dict):
        """Add a NUMBER script that shows input dialog when clicked"""
        try:
            status = script.get_status_display()
            if status and status != 'Unknown':
                display_name = f"{script_name} [{status}]"
            else:
                display_name = script_name
        except:
            display_name = script_name
        
        action = QAction(display_name, self)
        action.setToolTip(f"{metadata.get('description', '')} (Click to set value)")
        action.triggered.connect(lambda checked, s=script: self._execute_number_script(s, metadata))
        
        self.script_actions[action] = script
        self.context_menu.addAction(action)
    
    def _add_text_input_script(self, script: UtilityScript, script_name: str, metadata: dict):
        """Add a TEXT_INPUT script that shows input dialog when clicked"""
        try:
            status = script.get_status_display()
            if status and status != 'Unknown':
                display_name = f"{script_name} [{status}]"
            else:
                display_name = script_name
        except:
            display_name = script_name
        
        action = QAction(display_name, self)
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
                script_name = metadata.get('name', 'Unknown Script')
                button_type = metadata.get('button_type', ButtonType.RUN)
                
                # Update action text based on script type
                if button_type == ButtonType.TOGGLE:
                    status = script.get_status()
                    is_on = status and status.lower() in ['on', 'enabled', 'true', 'active']
                    state_text = "ON" if is_on else "OFF"
                    action.setText(f"{script_name} [{state_text}]")
                    processed_scripts.add(script)
                    
                elif button_type in [ButtonType.RUN, ButtonType.NUMBER, ButtonType.TEXT_INPUT]:
                    # For these scripts, show current status if available
                    try:
                        status = script.get_status_display()
                        if status and status != 'Unknown':
                            action.setText(f"{script_name} [{status}]")
                        else:
                            action.setText(script_name)
                    except:
                        action.setText(script_name)
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
    
    def cleanup(self):
        self.refresh_timer.stop()
        self.tray_icon.hide()