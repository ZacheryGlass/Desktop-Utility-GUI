import sys
import logging
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                             QScrollArea, QLabel, QPushButton,
                             QHBoxLayout, QMessageBox)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon
from pathlib import Path

from core.script_loader import ScriptLoader
from core.divider_script import DividerScript
from .script_widget import ScriptWidget
from .divider_widget import DividerWidget
from .styles import MAIN_STYLE

logger = logging.getLogger('GUI.MainWindow')

class MainWindow(QMainWindow):
    scripts_reloaded = pyqtSignal()
    
    def __init__(self, scripts_directory: str = "scripts"):
        super().__init__()
        logger.info(f"Initializing MainWindow with scripts directory: {scripts_directory}")
        self.scripts_directory = scripts_directory
        self.script_loader = ScriptLoader(scripts_directory)
        self.script_widgets = []
        self.init_ui()
        self.load_scripts()
        
        logger.info("Setting up refresh timer (5 second interval)")
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_status)
        self.refresh_timer.start(5000)
    
    def init_ui(self):
        logger.debug("Initializing UI components")
        self.setWindowTitle("Desktop Utility GUI")
        self.setGeometry(100, 100, 600, 700)
        self.setStyleSheet(MAIN_STYLE)
        logger.debug("Main window configured: 600x700 at position (100,100)")
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(20, 20, 20, 10)
        
        title_label = QLabel("Desktop Utilities")
        title_label.setObjectName("titleLabel")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.reload_scripts)
        header_layout.addWidget(refresh_button)
        
        main_layout.addLayout(header_layout)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.script_list_widget = QWidget()
        self.script_list_widget.setObjectName("scriptListContainer")
        self.script_list_layout = QVBoxLayout(self.script_list_widget)
        self.script_list_layout.setContentsMargins(10, 10, 10, 10)
        self.script_list_layout.setSpacing(10)
        
        self.scroll_area.setWidget(self.script_list_widget)
        main_layout.addWidget(self.scroll_area)
        
        self.status_label = QLabel("Loading scripts...")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.status_label)
    
    def load_scripts(self):
        logger.info("Loading scripts...")
        self.clear_scripts()
        
        try:
            scripts = self.script_loader.discover_scripts()
            logger.info(f"Script loader discovered {len(scripts)} script(s)")
            
            if not scripts:
                logger.warning(f"No scripts found in '{self.scripts_directory}' directory")
                no_scripts_label = QLabel("No scripts found in the scripts directory")
                no_scripts_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                no_scripts_label.setStyleSheet("color: #999; padding: 40px; font-size: 14px;")
                self.script_list_layout.addWidget(no_scripts_label)
                self.status_label.setText(f"No scripts found in '{self.scripts_directory}' directory")
            else:
                for script in scripts:
                    try:
                        # Check if it's a divider
                        if isinstance(script, DividerScript):
                            metadata = script.get_metadata()
                            logger.debug(f"Creating divider widget: {metadata}")
                            divider = DividerWidget(
                                label=metadata.get('label'),
                                style=metadata.get('style', 'default')
                            )
                            self.script_list_layout.addWidget(divider)
                            logger.debug("Successfully added divider widget")
                        else:
                            # Regular script widget
                            metadata = script.get_metadata()
                            logger.debug(f"Creating widget for script: {metadata.get('name', 'Unknown')}")
                            widget = ScriptWidget(script)
                            self.script_widgets.append(widget)
                            self.script_list_layout.addWidget(widget)
                            logger.debug(f"Successfully added widget for: {metadata.get('name', 'Unknown')}")
                    except Exception as e:
                        logger.error(f"Error creating widget for script: {e}", exc_info=True)
                
                self.script_list_layout.addStretch()
                
                # Count actual scripts (not dividers)
                script_count = len([s for s in scripts if not isinstance(s, DividerScript)])
                divider_count = len([s for s in scripts if isinstance(s, DividerScript)])
                
                status_text = f"Loaded {script_count} script(s)"
                if divider_count > 0:
                    logger.info(f"Also loaded {divider_count} divider(s)")
                
                self.status_label.setText(status_text)
                logger.info(f"Successfully loaded {script_count} script widget(s) and {divider_count} divider(s)")
            
            failed_scripts = self.script_loader.get_failed_scripts()
            if failed_scripts:
                failed_count = len(failed_scripts)
                logger.warning(f"{failed_count} script(s) failed to load:")
                for script_name, error in failed_scripts.items():
                    logger.warning(f"  - {script_name}: {error}")
                current_text = self.status_label.text()
                self.status_label.setText(f"{current_text} | {failed_count} script(s) failed to load")
                
        except Exception as e:
            logger.error(f"Critical error loading scripts: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to load scripts: {str(e)}")
            self.status_label.setText("Error loading scripts")
    
    def clear_scripts(self):
        logger.debug(f"Clearing {len(self.script_widgets)} existing script widgets")
        while self.script_list_layout.count():
            item = self.script_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.script_widgets.clear()
    
    def reload_scripts(self):
        logger.info("User triggered script reload")
        self.status_label.setText("Reloading scripts...")
        self.script_loader.reload_scripts()
        self.load_scripts()
        self.scripts_reloaded.emit()
        logger.info("Script reload complete")
    
    def refresh_status(self):
        logger.debug(f"Refreshing status for {len(self.script_widgets)} script(s)")
        for widget in self.script_widgets:
            try:
                widget.update_status()
            except Exception as e:
                logger.error(f"Error updating status for widget: {e}")