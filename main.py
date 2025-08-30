"""
Main entry point for Desktop Utility GUI using MVC architecture.

This file sets up the MVC components and coordinates the application startup
while maintaining clear separation of concerns.
"""
import sys
import os
import logging
import argparse
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMessageBox
from PyQt6.QtCore import Qt, QSharedMemory

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import MVC components
from controllers.app_controller import AppController
from controllers.script_controller import ScriptController
from controllers.tray_controller import TrayController
from views.tray_view import TrayView
from views.main_view import MainView
from core.hotkey_manager import HotkeyManager


def setup_logging():
    """Set up application logging"""
    log_format = '%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s'
    logging.basicConfig(
        level=logging.DEBUG,
        format=log_format,
        datefmt='%H:%M:%S',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logging.getLogger('PyQt6').setLevel(logging.WARNING)
    
    logger = logging.getLogger('MAIN')
    return logger


class SingleApplication(QApplication):
    """Ensures only one instance of the application runs"""
    
    def __init__(self, argv, key):
        super().__init__(argv)
        self._key = key
        self._timeout = 1000
        
        # For fixing potential issues with shared memory
        self._shared_mem = QSharedMemory(self._key)
        if self._shared_mem.attach():
            self._running = True
        else:
            self._shared_mem.create(1)
            self._running = False
    
    def is_running(self):
        return self._running
    
    def __del__(self):
        if hasattr(self, '_shared_mem'):
            self._shared_mem.detach()


class MVCApplication:
    """
    Main application class that coordinates the MVC architecture.
    
    This class sets up the Model-View-Controller components and
    manages their lifecycle and interconnections.
    """
    
    def __init__(self, scripts_directory: str = "scripts"):
        self.scripts_directory = scripts_directory
        self.logger = logging.getLogger('MVC.App')
        
        # MVC Components
        self.app_controller = None
        self.script_controller = None
        self.tray_controller = None
        self.main_view = None
        self.tray_view = None
        self.hotkey_manager = None
        
    def initialize(self):
        """Initialize all MVC components and set up connections"""
        self.logger.info("Initializing MVC application...")
        
        try:
            # Create main application controller (creates all models)
            self.app_controller = AppController(self.scripts_directory)
            
            # Create specialized controllers
            self._create_controllers()
            
            # Create views
            self._create_views()
            
            # Set up MVC connections
            self._setup_mvc_connections()
            
            # Set up hotkey management
            self._setup_hotkey_management()
            
            # Initialize application
            self.app_controller.initialize_application()
            
            self.logger.info("MVC application initialization complete")
            
        except Exception as e:
            self.logger.error(f"Error during MVC initialization: {e}")
            raise
    
    def finalize_startup(self):
        """Complete application startup"""
        self.app_controller.finalize_startup()
    
    def shutdown(self):
        """Shutdown the application gracefully"""
        self.logger.info("Shutting down MVC application...")
        
        try:
            # Clean up hotkey manager
            if self.hotkey_manager:
                self.hotkey_manager.stop()
            
            # Clean up views
            if self.tray_view:
                self.tray_view.cleanup()
            
            # Shutdown application
            if self.app_controller:
                self.app_controller.shutdown_application()
                
            self.logger.info("MVC application shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
    
    def _create_controllers(self):
        """Create all controller instances"""
        self.logger.debug("Creating controllers...")
        
        # Get models from app controller
        script_collection = self.app_controller.get_script_collection_model()
        script_execution = self.app_controller.get_script_execution_model()
        hotkey_model = self.app_controller.get_hotkey_model()
        tray_model = self.app_controller.get_tray_model()
        notification_model = self.app_controller.get_notification_model()
        
        # Create script controller
        self.script_controller = ScriptController(
            script_collection, script_execution, hotkey_model
        )
        
        # Create tray controller
        self.tray_controller = TrayController(
            tray_model, notification_model, self.script_controller
        )
        
        # Register controllers with app controller
        self.app_controller.set_script_controller(self.script_controller)
        self.app_controller.set_tray_controller(self.tray_controller)
        
        self.logger.debug("Controllers created")
    
    def _create_views(self):
        """Create all view instances"""
        self.logger.debug("Creating views...")
        
        # Create main view (hidden parent window)
        self.main_view = MainView()
        
        # Create tray view
        self.tray_view = TrayView(self.main_view)
        
        self.logger.debug("Views created")
    
    def _setup_mvc_connections(self):
        """Set up the MVC signal/slot connections"""
        self.logger.debug("Setting up MVC connections...")
        
        # Tray Controller -> Tray View connections
        self.tray_controller.menu_structure_updated.connect(
            self.tray_view.update_menu_structure
        )
        self.tray_controller.notification_display_requested.connect(
            self.tray_view.show_notification
        )
        
        # Tray View -> Tray Controller connections
        self.tray_view.menu_action_triggered.connect(
            self.tray_controller.handle_menu_action
        )
        self.tray_view.title_clicked.connect(
            self.tray_controller.handle_title_clicked
        )
        self.tray_view.exit_requested.connect(
            self.tray_controller.handle_exit_requested
        )
        
        # Application-level connections
        self.tray_controller.application_exit_requested.connect(
            self._handle_exit_request
        )
        self.tray_controller.settings_dialog_requested.connect(
            self._handle_settings_request
        )
        
        # Initialize tray view based on models
        self._initialize_view_states()
        
        self.logger.debug("MVC connections setup complete")
    
    def _setup_hotkey_management(self):
        """Set up hotkey management system"""
        self.logger.debug("Setting up hotkey management...")
        
        try:
            # Create hotkey manager
            self.hotkey_manager = HotkeyManager()
            
            # Connect hotkey triggers to script execution
            self.hotkey_manager.hotkey_triggered.connect(
                self.script_controller.execute_script_from_hotkey
            )
            
            # Start hotkey manager
            if not self.hotkey_manager.start():
                self.logger.warning("Hotkey manager failed to start - hotkeys will not work")
                # Show notification about hotkey system failure
                tray_model = self.app_controller.get_tray_model()
                tray_model.show_notification(
                    "Hotkey System Warning",
                    "Failed to initialize hotkey system. Global hotkeys will not work.",
                    QSystemTrayIcon.MessageIcon.Warning
                )
            else:
                self.logger.info("Hotkey management system started")
                
                # Register current hotkeys
                self._register_hotkeys()
            
        except Exception as e:
            self.logger.error(f"Error setting up hotkey management: {e}")
    
    def _register_hotkeys(self):
        """Register all configured hotkeys"""
        try:
            hotkey_mappings = self.script_controller.get_all_hotkeys()
            
            for script_name, hotkey in hotkey_mappings.items():
                self.hotkey_manager.register_hotkey(script_name, hotkey)
                self.logger.debug(f"Registered hotkey {hotkey} for script {script_name}")
                
        except Exception as e:
            self.logger.error(f"Error registering hotkeys: {e}")
    
    def _initialize_view_states(self):
        """Initialize view states based on model data"""
        # Show tray icon
        self.tray_view.show_icon()
        
        # Update tray menu with current scripts
        self.tray_controller.update_menu()
    
    def _handle_exit_request(self):
        """Handle application exit request"""
        self.logger.info("Application exit requested")
        QApplication.instance().quit()
    
    def _handle_settings_request(self):
        """Handle settings dialog request"""
        self.logger.info("Settings dialog requested")
        
        # For now, show a simple message
        # In a full implementation, this would open the settings dialog
        QMessageBox.information(
            self.main_view,
            "Settings",
            "Settings dialog would open here.\n\n"
            "This is a placeholder during MVC refactoring."
        )


def main():
    """Main entry point"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Desktop Utility GUI')
    parser.add_argument('--minimized', action='store_true', 
                       help='Start minimized to system tray')
    args = parser.parse_args()
    
    # Change to script directory to ensure correct working directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    logger = setup_logging()
    
    logger.info("="*60)
    logger.info("DESKTOP UTILITY GUI STARTING (MVC Architecture)")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Working directory: {os.getcwd()}")
    logger.info(f"Command line args: {sys.argv}")
    logger.info("="*60)
    
    # Create QApplication
    app = None
    
    # For now, skip single instance check during MVC transition
    # TODO: Re-implement single instance check with MVC pattern
    app = QApplication(sys.argv)
    
    app.setApplicationName("Desktop Utility GUI")
    app.setOrganizationName("DesktopUtils")
    
    # Check if system tray is available
    if not QSystemTrayIcon.isSystemTrayAvailable():
        logger.error("System tray is not available on this system")
        QMessageBox.critical(None, "System Tray Not Available",
                           "System tray is required but not available on this system.")
        sys.exit(1)
    
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app.setStyle("Fusion")
    logger.info(f"Application style set to: Fusion")
    
    # Load and apply custom stylesheet
    try:
        style_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'style.qss')
        if os.path.exists(style_path):
            with open(style_path, 'r', encoding='utf-8') as f:
                app.setStyleSheet(f.read())
            logger.info(f"Applied custom stylesheet: {style_path}")
        else:
            logger.warning(f"Custom stylesheet not found: {style_path}")
    except Exception as e:
        logger.error(f"Failed to load custom stylesheet: {e}")
    
    # Don't quit when last window closes (we have tray icon)
    app.setQuitOnLastWindowClosed(False)
    
    # Create and initialize MVC application
    mvc_app = MVCApplication()
    
    try:
        # Initialize MVC components
        mvc_app.initialize()
        
        # Complete startup
        mvc_app.finalize_startup()
        
        logger.info("Starting application event loop...")
        logger.info("-"*60)
        
        # Run application
        exit_code = app.exec()
        
        # Clean shutdown
        mvc_app.shutdown()
        
        sys.exit(exit_code)
        
    except Exception as e:
        logger.error(f"Fatal error during application startup: {e}")
        QMessageBox.critical(
            None, 
            "Startup Error",
            f"Failed to start application: {str(e)}\n\nCheck the logs for details."
        )
        sys.exit(1)


if __name__ == "__main__":
    main()