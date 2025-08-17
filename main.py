import sys
import os
import logging
from datetime import datetime
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.main_window import MainWindow

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

def main():
    # Change to script directory to ensure correct working directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    logger = setup_logging()
    
    logger.info("="*60)
    logger.info("DESKTOP UTILITY GUI STARTING")
    logger.info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Working directory: {os.getcwd()}")
    logger.info("="*60)
    
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    logger.info("Creating QApplication...")
    app = QApplication(sys.argv)
    app.setApplicationName("Desktop Utility GUI")
    app.setOrganizationName("DesktopUtils")
    
    app.setStyle("Fusion")
    logger.info(f"Application style set to: Fusion")
    
    logger.info("Creating main window...")
    window = MainWindow()
    
    logger.info(f"Window geometry: {window.geometry().width()}x{window.geometry().height()}")
    logger.info("Showing main window...")
    window.show()
    
    logger.info("Starting application event loop...")
    logger.info("-"*60)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()