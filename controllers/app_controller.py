"""
Application Controller - Main controller that orchestrates the MVC architecture.

This controller manages the application lifecycle, coordinates between models,
and sets up the primary signal/slot connections for the MVC pattern.
"""
import logging
from typing import Optional
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QApplication

from models.application_model import ApplicationStateModel
from models.script_models import ScriptCollectionModel, ScriptExecutionModel, HotkeyModel
from models.system_models import TrayIconModel, NotificationModel, WindowStateModel
from core.scheduler_manager import SchedulerManager
from controllers.schedule_controller import ScheduleController

logger = logging.getLogger('Controllers.App')


class AppController(QObject):
    """
    Main application controller that orchestrates the MVC architecture.
    
    This controller:
    - Manages the lifecycle of all models
    - Coordinates high-level application operations
    - Sets up the foundational MVC connections
    - Handles application startup and shutdown
    """
    
    # High-level application signals
    application_initialized = pyqtSignal()
    application_ready = pyqtSignal()
    application_shutting_down = pyqtSignal()
    
    def __init__(self, scripts_directory: str = "scripts"):
        super().__init__()
        
        # Initialize all models
        self._app_model = ApplicationStateModel()
        self._script_collection = ScriptCollectionModel(scripts_directory)
        self._script_execution = ScriptExecutionModel(self._script_collection)
        self._hotkey_model = HotkeyModel()
        self._tray_model = TrayIconModel()
        self._notification_model = NotificationModel(self._app_model)
        self._window_model = WindowStateModel(self._app_model)
        
        # Initialize scheduler
        from core.settings import SettingsManager
        self._settings = SettingsManager()
        self._scheduler_manager = SchedulerManager(self._script_execution, self._settings)
        self._schedule_controller = ScheduleController(
            self._scheduler_manager, 
            self._script_execution,
            self._settings
        )
        
        # Store references for other controllers
        self._script_controller = None
        self._settings_controller = None
        self._tray_controller = None
        
        # Connect model signals for coordination
        self._setup_model_coordination()
        
        logger.info("AppController initialized")
    
    def initialize_application(self):
        """Initialize the application and all subsystems"""
        logger.info("Initializing application...")
        
        try:
            # Start application model
            self._app_model.start_application()
            
            # Initialize tray icon
            self._tray_model.show_icon()
            
            # Discover scripts
            self._script_collection.discover_scripts()
            
            # Set up tray system availability
            from PyQt6.QtWidgets import QSystemTrayIcon
            self._tray_model.set_supports_notifications(QSystemTrayIcon.supportsMessages())
            
            # Start the scheduler
            self._schedule_controller.start_scheduler()
            
            self.application_initialized.emit()
            logger.info("Application initialization complete")
            
        except Exception as e:
            logger.error(f"Error during application initialization: {e}")
            raise
    
    def finalize_startup(self):
        """Complete application startup and emit ready signal"""
        logger.info("Finalizing application startup...")
        
        try:
            # Show startup notification if appropriate
            if self._app_model.is_start_minimized():
                self._notification_model.show_startup_notification()
            
            self.application_ready.emit()
            logger.info("Application startup complete")
            
        except Exception as e:
            logger.error(f"Error during startup finalization: {e}")
    
    def shutdown_application(self):
        """Gracefully shut down the application"""
        logger.info("Shutting down application...")
        
        self.application_shutting_down.emit()
        
        # Stop the scheduler
        try:
            self._schedule_controller.stop_scheduler()
        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}")
        
        self._app_model.shutdown_application()
        
        # Clean up models
        try:
            self._tray_model.hide_icon()
            logger.info("Application shutdown complete")
        except Exception as e:
            logger.error(f"Error during application shutdown: {e}")
    
    def set_script_controller(self, controller):
        """Set the script controller reference"""
        self._script_controller = controller
    
    def set_settings_controller(self, controller):
        """Set the settings controller reference"""
        self._settings_controller = controller
    
    def set_tray_controller(self, controller):
        """Set the tray controller reference"""
        self._tray_controller = controller
    
    # Model accessors for other controllers
    def get_application_model(self) -> ApplicationStateModel:
        """Get the application state model"""
        return self._app_model
    
    def get_script_collection_model(self) -> ScriptCollectionModel:
        """Get the script collection model"""
        return self._script_collection
    
    def get_script_execution_model(self) -> ScriptExecutionModel:
        """Get the script execution model"""
        return self._script_execution
    
    def get_hotkey_model(self) -> HotkeyModel:
        """Get the hotkey model"""
        return self._hotkey_model
    
    def get_tray_model(self) -> TrayIconModel:
        """Get the tray icon model"""
        return self._tray_model
    
    def get_notification_model(self) -> NotificationModel:
        """Get the notification model"""
        return self._notification_model
    
    def get_window_model(self) -> WindowStateModel:
        """Get the window state model"""
        return self._window_model
    
    def get_schedule_controller(self) -> ScheduleController:
        """Get the schedule controller"""
        return self._schedule_controller
    
    def _setup_model_coordination(self):
        """Set up signal connections between models for coordination"""
        logger.debug("Setting up model coordination...")
        
        # Connect script execution to notifications
        self._script_execution.script_execution_completed.connect(
            self._on_script_execution_completed
        )
        self._script_execution.script_execution_failed.connect(
            self._on_script_execution_failed
        )
        
        # Connect notification model to tray model
        self._notification_model.notification_shown.connect(
            self._tray_model.show_notification
        )
        
        # Connect script collection changes to tray menu updates
        self._script_collection.scripts_filtered.connect(
            lambda scripts: self._tray_model.request_menu_update()
        )
        
        # Connect hotkey changes to tray menu updates
        self._hotkey_model.hotkeys_changed.connect(
            lambda: self._tray_model.request_menu_update()
        )
        
        # Connect application settings changes to relevant updates
        self._app_model.behavior_settings_changed.connect(
            self._on_behavior_settings_changed
        )
        
        logger.debug("Model coordination setup complete")
    
    def _on_script_execution_completed(self, script_name: str, result: dict):
        """Handle successful script execution"""
        if self._script_execution.should_show_notifications_for_script(script_name):
            message = result.get('message', 'Completed successfully')
            self._notification_model.show_script_notification(
                script_name, message, success=True
            )
    
    def _on_script_execution_failed(self, script_name: str, error: str):
        """Handle failed script execution"""
        if self._script_execution.should_show_notifications_for_script(script_name):
            self._notification_model.show_script_notification(
                script_name, error, success=False
            )
    
    def _on_behavior_settings_changed(self, settings: dict):
        """Handle behavior settings changes"""
        logger.debug(f"Behavior settings changed: {settings}")
        # This can trigger various UI updates through other controllers