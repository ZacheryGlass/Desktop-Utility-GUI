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
                 script_controller: ScriptController):
        super().__init__()
        
        self._tray_model = tray_model
        self._notification_model = notification_model
        self._script_controller = script_controller
        
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
            for script_info in scripts:
                script_name = script_info.display_name
                status = self._script_controller.get_script_status(script_name)
                hotkey = self._script_controller.get_script_hotkey(script_name)
                menu_items.append(self._build_script_menu_item(script_info, status, hotkey))
        return {
            'title': 'Desktop Utilities',
            'items': menu_items
        }
    
    def _build_script_menu_item(self, script_info, status: str, hotkey: str = None) -> Dict[str, Any]:
        """Build a menu item for a specific script"""
        script_name = script_info.display_name
        display_text = script_name
        if status and status != "Ready":
            display_text += f" [{status}]"
        if hotkey:
            display_text += f" ({hotkey})"
        
        if script_info.arguments:
            if self._has_choice_arguments(script_info):
                return self._build_choice_submenu_item(script_info, display_text)
            elif self._has_preset_configuration(script_name):
                return self._build_preset_submenu_item(script_info, display_text)
            else:
                return {
                    'type': 'action',
                    'text': f"{display_text} (needs config)",
                    'enabled': True,
                    'data': {
                        'action': 'configure_script',
                        'script_name': script_name,
                        'script_info': script_info
                    }
                }
        else:
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
        """Build submenu for script with presets"""
        # Placeholder: integrate with presets in settings when available
        return {
            'type': 'action',
            'text': display_text,
            'enabled': True,
            'data': {
                'action': 'execute_script',
                'script_name': script_info.display_name,
                'script_info': script_info
            }
        }
    
    def _has_choice_arguments(self, script_info) -> bool:
        """Check if script has choice-based arguments"""
        if not script_info.arguments:
            return False
        return any(getattr(arg, 'choices', None) for arg in script_info.arguments)
    
    def _has_preset_configuration(self, script_name: str) -> bool:
        """Check if script has preset configurations"""
        # TODO: Integrate with settings presets when available
        return False
    
    # User interaction handlers (called by views)
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
        elif action == 'configure_script':
            logger.info(f"Script configuration requested for: {script_name}")
            self.settings_dialog_requested.emit()
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
        self._script_controller.script_status_updated.connect(lambda name, status: self.update_menu())
        logger.debug("Tray controller model connections setup complete")

