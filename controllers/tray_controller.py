"""
Tray Controller - Manages system tray interactions and menu coordination.

This controller handles tray icon behavior, menu updates, and coordinates
between tray-related models and the tray view.
"""
import logging
from typing import Dict, Any
from PyQt6.QtCore import QObject, pyqtSignal

from models.system_models import TrayIconModel, NotificationModel
from controllers.script_controller import ScriptController

logger = logging.getLogger('Controllers.Tray')


class TrayController(QObject):
    """
    Controller for managing system tray interactions.
    
    This controller:
    - Manages tray icon state and visibility
    - Coordinates menu updates based on script changes
    - Handles tray icon interactions
    - Manages tray notifications
    """
    
    # Signals for view updates
    menu_structure_updated = pyqtSignal(dict)  # Menu structure data
    notification_display_requested = pyqtSignal(str, str, object)  # title, message, icon
    settings_dialog_requested = pyqtSignal()
    application_exit_requested = pyqtSignal()
    
    def __init__(self, tray_model: TrayIconModel,
                 notification_model: NotificationModel,
                 script_controller: ScriptController,
                 schedule_controller=None):
        super().__init__()
        
        self._tray_model = tray_model
        self._notification_model = notification_model
        self._script_controller = script_controller
        self._schedule_controller = schedule_controller
        
        # Connect model signals
        self._setup_model_connections()
        
        logger.info("TrayController initialized")
    
    # Tray icon management
    def show_tray_icon(self):
        """Show the system tray icon"""
        self._tray_model.show_icon()
    
    def hide_tray_icon(self):
        """Hide the system tray icon"""
        self._tray_model.hide_icon()
    
    def set_tray_tooltip(self, tooltip: str):
        """Set the tray icon tooltip"""
        self._tray_model.set_tooltip(tooltip)
    
    def is_tray_visible(self) -> bool:
        """Check if tray icon is visible"""
        return self._tray_model.is_visible()
    
    # Menu management
    def update_menu(self):
        """Update the tray menu based on current script state"""
        logger.debug("Updating tray menu...")
        
        try:
            available_scripts = self._script_controller.get_available_scripts()
            menu_structure = self._build_menu_structure(available_scripts)
            self.menu_structure_updated.emit(menu_structure)
            logger.debug(f"Menu updated with {len(available_scripts)} scripts")
        except Exception as e:
            logger.error(f"Error updating menu: {e}")
    
    def _build_menu_structure(self, scripts) -> Dict[str, Any]:
        """Build the menu structure data for the view"""
        menu_items = []
        if not scripts:
            menu_items.append({
                'type': 'action',
                'text': 'No scripts available',
                'enabled': False,
                'data': None
            })
        else:
            # First pass: collect all script data and find max name length
            script_data = []
            max_name_length = 0
            
            for script_info in scripts:
                # Use effective display name (respects custom names) for UI text
                effective_name = self._script_controller._script_collection.get_script_display_name(script_info)
                # Use original analyzer display name for model lookups
                original_name = script_info.display_name
                # Status by original name
                status = self._script_controller.get_script_status(original_name)
                # Hotkey lookup by file stem identifier
                stem = script_info.file_path.stem if hasattr(script_info, 'file_path') else None
                hotkey = self._script_controller.get_script_hotkey(stem) if stem else None
                
                # Track max length for scripts with hotkeys
                if hotkey:
                    # Include status in the length calculation if present
                    name_with_status = effective_name
                    if status and status != "Ready":
                        name_with_status += f" [{status}]"
                    max_name_length = max(max_name_length, len(name_with_status))
                
                script_data.append((script_info, effective_name, status, hotkey))
            
            # Second pass: build menu items with aligned formatting
            for script_info, effective_name, status, hotkey in script_data:
                menu_items.append(self._build_script_menu_item(
                    script_info, effective_name, status, hotkey, max_name_length
                ))
        return {
            'title': 'Desktop Utilities',
            'items': menu_items
        }

    def _build_script_menu_item(self, script_info, display_text: str, status: str, hotkey: str = None, max_name_length: int = 0) -> Dict[str, Any]:
        """Build a menu item for a specific script with aligned hotkey display.

        display_text is the effective (customized) name, while script_info.display_name is the
        original identifier used by models.
        """
        script_name = script_info.display_name  # original name for actions
        
        # Check if script is currently running
        is_running = self._script_controller._script_execution.is_script_running(script_name)
        
        # Build the base display text with status
        if is_running:
            display_text += " [Running...]"
        elif status and status != "Ready":
            display_text += f" [{status}]"
        
        # Add schedule indicator if scheduled
        if self._schedule_controller and self._schedule_controller.has_schedule(script_name):
            if self._schedule_controller.is_schedule_enabled(script_name):
                display_text += " [Scheduled]"
            else:
                display_text += " [Schedule disabled]"
        
        # Format with aligned hotkey if present
        if hotkey and max_name_length > 0:
            # Pad the script name to align the pipe character
            display_text = f"{display_text:<{max_name_length}} | {hotkey}"
        elif hotkey:
            # Fallback if no alignment (shouldn't happen in normal flow)
            display_text += f" ({hotkey})"
        
        # If script is running, allow cancellation
        if is_running:
            return {
                'type': 'action',
                'text': display_text,
                'enabled': True,
                'is_running': True,
                'data': {
                    'action': 'cancel_script',
                    'script_name': script_name,
                    'script_info': script_info
                }
            }
        
        # Build submenu if script has arguments, presets, or schedule options
        if script_info.arguments or (self._schedule_controller and not is_running):
            submenu_items = []
            
            # Add execution options
            if script_info.arguments:
                if self._has_preset_configuration(script_name):
                    # Add preset options
                    preset_names = self._script_controller._settings_controller.get_script_preset_names(script_name)
                    for preset_name in preset_names:
                        submenu_items.append({
                            'type': 'action',
                            'text': f"Run: {preset_name}",
                            'enabled': True,
                            'data': {
                                'action': 'execute_preset',
                                'script_name': script_name,
                                'preset_name': preset_name,
                                'script_info': script_info
                            }
                        })
                else:
                    submenu_items.append({
                        'type': 'action',
                        'text': 'Configure Script',
                        'enabled': True,
                        'data': {
                            'action': 'configure_script',
                            'script_name': script_name,
                            'script_info': script_info
                        }
                    })
            else:
                # Simple execution for scripts without arguments
                submenu_items.append({
                    'type': 'action',
                    'text': 'Run Now',
                    'enabled': True,
                    'data': {
                        'action': 'execute_script',
                        'script_name': script_name,
                        'script_info': script_info
                    }
                })
            
            # Add separator before schedule options
            if self._schedule_controller and submenu_items:
                submenu_items.append({'type': 'separator'})
            
            # Add schedule options if controller is available
            if self._schedule_controller:
                submenu_items.extend(self._build_schedule_menu_items(script_name, script_info))
            
            # If we have submenu items, return as submenu
            if submenu_items:
                return {
                    'type': 'submenu',
                    'text': display_text,
                    'items': submenu_items
                }
        
        # Simple action for scripts without arguments or schedule support
        return {
            'type': 'action',
            'text': display_text,
            'enabled': True,
            'data': {
                'action': 'execute_script',
                'script_name': script_name,
                'script_info': script_info
            }
        }
    
    def _build_schedule_menu_items(self, script_name: str, script_info) -> list:
        """Build schedule-related menu items for a script."""
        items = []
        
        if self._schedule_controller.has_schedule(script_name):
            # Script has a schedule
            is_enabled = self._schedule_controller.is_schedule_enabled(script_name)
            
            # Toggle enable/disable
            items.append({
                'type': 'action',
                'text': 'Disable Schedule' if is_enabled else 'Enable Schedule',
                'enabled': True,
                'data': {
                    'action': 'toggle_schedule',
                    'script_name': script_name,
                    'script_info': script_info
                }
            })
            
            # Show next run time
            next_run = self._schedule_controller.get_next_run_time(script_name)
            if next_run and is_enabled:
                from datetime import datetime
                time_diff = next_run - datetime.now()
                if time_diff.days > 0:
                    time_text = f"Next run: in {time_diff.days} day(s)"
                elif time_diff.seconds > 3600:
                    hours = time_diff.seconds // 3600
                    time_text = f"Next run: in {hours} hour(s)"
                else:
                    minutes = time_diff.seconds // 60
                    time_text = f"Next run: in {minutes} minute(s)"
                
                items.append({
                    'type': 'action',
                    'text': time_text,
                    'enabled': False,
                    'data': None
                })
            
            # Edit schedule
            items.append({
                'type': 'action',
                'text': 'Edit Schedule...',
                'enabled': True,
                'data': {
                    'action': 'edit_schedule',
                    'script_name': script_name,
                    'script_info': script_info
                }
            })
            
            # Remove schedule
            items.append({
                'type': 'action',
                'text': 'Remove Schedule',
                'enabled': True,
                'data': {
                    'action': 'remove_schedule',
                    'script_name': script_name,
                    'script_info': script_info
                }
            })
        else:
            # No schedule yet
            items.append({
                'type': 'action',
                'text': 'Add Schedule...',
                'enabled': True,
                'data': {
                    'action': 'add_schedule',
                    'script_name': script_name,
                    'script_info': script_info
                }
            })
            
            # Quick schedule presets
            items.append({'type': 'separator'})
            items.append({
                'type': 'action',
                'text': 'Quick: Every 5 minutes',
                'enabled': True,
                'data': {
                    'action': 'quick_schedule',
                    'script_name': script_name,
                    'preset': 'every_5_min',
                    'script_info': script_info
                }
            })
            items.append({
                'type': 'action',
                'text': 'Quick: Every hour',
                'enabled': True,
                'data': {
                    'action': 'quick_schedule',
                    'script_name': script_name,
                    'preset': 'hourly',
                    'script_info': script_info
                }
            })
            items.append({
                'type': 'action',
                'text': 'Quick: Daily at 9 AM',
                'enabled': True,
                'data': {
                    'action': 'quick_schedule',
                    'script_name': script_name,
                    'preset': 'daily_9am',
                    'script_info': script_info
                }
            })
        
        return items
    
    def _build_choice_submenu_item(self, script_info, display_text: str) -> Dict[str, Any]:
        """Build submenu for script with choice arguments"""
        # Assume single choice argument for now
        arg_info = script_info.arguments[0]
        submenu_items = []
        for choice in getattr(arg_info, 'choices', []) or []:
            submenu_items.append({
                'type': 'action',
                'text': choice,
                'enabled': True,
                'data': {
                    'action': 'execute_script_with_choice',
                    'script_name': script_info.display_name,
                    'arg_name': arg_info.name,
                    'choice': choice,
                    'script_info': script_info
                }
            })
        return {
            'type': 'submenu',
            'text': display_text,
            'enabled': True,
            'items': submenu_items
        }
    
    def _build_preset_submenu_item(self, script_info, display_text: str) -> Dict[str, Any]:
        """Build submenu for script with saved presets from settings"""
        preset_names = []
        try:
            preset_names = self._script_controller.get_preset_names(script_info.display_name)
        except Exception:
            preset_names = []

        if not preset_names:
            # Fallback to configure action if somehow no presets are returned
            return {
                'type': 'action',
                'text': f"{display_text} (needs config)",
                'enabled': True,
                'data': {
                    'action': 'configure_script',
                    'script_name': script_info.display_name,
                    'script_info': script_info
                }
            }

        submenu_items = []
        for preset in preset_names:
            submenu_items.append({
                'type': 'action',
                'text': preset,
                'enabled': True,
                'data': {
                    'action': 'execute_script_with_preset',
                    'script_name': script_info.display_name,
                    'preset_name': preset,
                    'script_info': script_info
                }
            })

        # Add manage option at the bottom
        submenu_items.append({
            'type': 'separator'
        })
        submenu_items.append({
            'type': 'action',
            'text': 'Manage Presets…',
            'enabled': True,
            'data': {
                'action': 'configure_script',
                'script_name': script_info.display_name,
                'script_info': script_info
            }
        })

        return {
            'type': 'submenu',
            'text': display_text,
            'enabled': True,
            'items': submenu_items
        }
    
    def _has_preset_configuration(self, script_name: str) -> bool:
        """Check if script has preset configurations"""
        try:
            return self._script_controller.has_presets(script_name)
        except Exception:
            return False
    
    # User interaction handlers (called by views)
    def handle_schedule_action(self, action: str, script_name: str, script_info=None, **kwargs):
        """Handle schedule-related menu actions."""
        if not self._schedule_controller:
            logger.warning("Schedule controller not available")
            return
        
        try:
            if action == 'add_schedule' or action == 'edit_schedule':
                # Show schedule configuration dialog
                self._schedule_controller.show_schedule_dialog(script_name, script_info)
                # Update menu after configuration
                self.update_menu()
            
            elif action == 'toggle_schedule':
                # Toggle schedule enabled state
                self._schedule_controller.toggle_schedule(script_name)
                self.update_menu()
            
            elif action == 'remove_schedule':
                # Remove the schedule
                self._schedule_controller.remove_schedule(script_name)
                self.update_menu()
            
            elif action == 'quick_schedule':
                # Create a quick schedule with preset
                preset = kwargs.get('preset')
                if preset:
                    self._schedule_controller.create_quick_schedule(script_name, preset)
                    self.update_menu()
            
        except Exception as e:
            logger.error(f"Error handling schedule action {action}: {e}")
    
    def handle_menu_action(self, action_data: Dict[str, Any]):
        """Handle a menu action triggered by the user"""
        if not action_data:
            return
        action = action_data.get('action')
        script_name = action_data.get('script_name')
        logger.info(f"Handling menu action: {action} for script: {script_name}")
        if action == 'execute_script':
            self._script_controller.execute_script(script_name)
        elif action == 'execute_script_with_choice':
            arg_name = action_data.get('arg_name')
            choice = action_data.get('choice')
            self._script_controller.execute_script_with_choice(script_name, arg_name, choice)
        elif action == 'execute_script_with_preset':
            preset_name = action_data.get('preset_name')
            self._script_controller.execute_script_with_preset(script_name, preset_name)
        elif action == 'cancel_script':
            logger.info(f"Script cancellation requested for: {script_name}")
            self._script_controller.cancel_script_execution(script_name)
        elif action == 'configure_script':
            logger.info(f"Script configuration requested for: {script_name}")
            self.settings_dialog_requested.emit()
        elif action in ['add_schedule', 'edit_schedule', 'toggle_schedule', 
                       'remove_schedule', 'quick_schedule']:
            # Handle schedule-related actions
            script_info = action_data.get('script_info')
            self.handle_schedule_action(action, script_name, script_info, **action_data)
        else:
            logger.warning(f"Unknown menu action: {action}")
    
    def handle_title_clicked(self):
        """Handle click on menu title (open settings)"""
        logger.info("Tray menu title clicked - opening settings")
        self.settings_dialog_requested.emit()
    
    def handle_exit_requested(self):
        """Handle application exit request from tray"""
        logger.info("Application exit requested from tray")
        self.application_exit_requested.emit()
    
    # Notification handling
    def show_notification(self, title: str, message: str, icon_type=None):
        """Show a tray notification"""
        self._notification_model.show_notification(title, message, icon_type)
    
    def show_script_notification(self, script_name: str, message: str, success: bool = True):
        """Show a script execution notification"""
        self._notification_model.show_script_notification(script_name, message, success)
    
    # Model signal handlers
    def _setup_model_connections(self):
        """Set up connections to model signals"""
        logger.debug("Setting up tray controller model connections...")
        self._tray_model.menu_update_requested.connect(self.update_menu)
        self._tray_model.notification_requested.connect(self.notification_display_requested.emit)
        self._notification_model.notification_shown.connect(self.notification_display_requested.emit)
        self._script_controller.script_list_updated.connect(lambda scripts: self.update_menu())
        
        # Connect script execution signals to update menu for running state
        self._script_controller._script_execution.script_execution_started.connect(
            lambda name: self.update_menu())
        self._script_controller._script_execution.script_execution_completed.connect(
            lambda name, result: self.update_menu())
        self._script_controller._script_execution.script_execution_failed.connect(
            lambda name, error: self.update_menu())
        
        logger.debug("Tray controller model connections setup complete")
