import sys
import os
import logging
import argparse
from datetime import datetime
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMessageBox
from PyQt6.QtCore import Qt, QSharedMemory, QSystemSemaphore

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.main_window import MainWindow
from gui.tray_manager import TrayManager
from core.settings import SettingsManager
from core.startup_manager import StartupManager

def setup_logging():
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

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Desktop Utility GUI')
    parser.add_argument('--minimized', action='store_true', 
                       help='Start minimized to system tray')
    args = parser.parse_args()
    
    # Change to script directory to ensure correct working directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    logger = setup_logging()
    
    logger.info("="*60)
    logger.info("DESKTOP UTILITY GUI STARTING")
    logger.info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Working directory: {os.getcwd()}")
    logger.info(f"Command line args: {sys.argv}")
    logger.info("="*60)
    
    # Initialize settings
    settings = SettingsManager()
    
    # Check for single instance if enabled
    app = None
    if settings.get('behavior/single_instance', True):
        app = SingleApplication(sys.argv, 'DesktopUtilityGUI-SingleInstance')
        if app.is_running():
            logger.warning("Another instance is already running. Exiting.")
            QMessageBox.information(
                None, 
                "Already Running",
                "Desktop Utility GUI is already running in the system tray."
            )
            sys.exit(0)
    else:
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
    
    # Don't quit when last window closes (we have tray icon)
    app.setQuitOnLastWindowClosed(False)
    
    logger.info("Creating main window (minimal, for settings dialog parent only)...")
    window = MainWindow()
    window.hide()  # Always keep it hidden since we only use tray menu now
    
    logger.info("Creating system tray manager...")
    tray_manager = TrayManager(window)
    
    # Set script loader for tray manager
    tray_manager.set_script_loader(window.script_loader)
    
    # Connect settings request to window
    tray_manager.settings_requested.connect(window.open_settings)
    
    # Handle exit request
    def handle_exit():
        logger.info("Exit requested from system tray")
        tray_manager.cleanup()
        app.quit()
    
    tray_manager.exit_requested.connect(handle_exit)
    
    # Always start in tray-only mode (no window UI)
    logger.info("Starting in system tray mode (no main window)")
    
    # Show notification if enabled and starting minimized
    if (args.minimized or settings.is_start_minimized()) and settings.get('startup/show_notification', True):
        tray_manager.show_notification(
            "Desktop Utilities",
            "Application started in system tray. Click the tray icon to access scripts."
        )
    
    # Update startup registration if needed
    startup_manager = StartupManager()
    startup_manager.update_path_if_needed()
    
    logger.info("Starting application event loop...")
    logger.info("-"*60)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()