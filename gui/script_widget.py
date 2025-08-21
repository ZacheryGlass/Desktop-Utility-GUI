import logging
import time
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, 
                             QLabel, QMessageBox, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, pyqtSlot
from PyQt6.QtGui import QFont

from core.base_script import UtilityScript
from core.button_types import ButtonType
from .button_factory import ButtonFactory

logger = logging.getLogger('GUI.ScriptWidget')

class ScriptExecutor(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, script, *args, **kwargs):
        super().__init__()
        self.script = script
        self.args = args
        self.kwargs = kwargs
    
    def run(self):
        try:
            result = self.script.execute(*self.args, **self.kwargs)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))

class ScriptWidget(QWidget):
    script_executed = pyqtSignal(str, dict)
    
    def __init__(self, script: UtilityScript):
        super().__init__()
        # CRITICAL FIX: Enable styled background painting for custom QWidget subclass
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.script = script
        self.metadata = script.get_metadata()
        logger.info(f"Creating widget for script: {self.metadata.get('name', 'Unknown')}")
        logger.debug(f"  Type: {self.metadata.get('button_type', 'Unknown')}")
        logger.debug(f"  Description: {self.metadata.get('description', 'None')}")
        self.executor = None
        self.button_factory = ButtonFactory()
        self.last_execution_time = 0
        self.min_execution_interval = 0.5  # Minimum 500ms between executions
        self.init_ui()
        self.update_status()
    
    def init_ui(self):
        self.setObjectName("scriptWidget")
        # Let theme manager handle styling - no hardcoded styles
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(110)
        self.setMaximumHeight(130)
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 12, 20, 12)
        main_layout.setSpacing(16)
        
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        
        self.name_label = QLabel(self.metadata.get('name', 'Unnamed Script'))
        self.name_label.setObjectName("scriptName")
        info_layout.addWidget(self.name_label)
        
        self.description_label = QLabel(self.metadata.get('description', 'No description'))
        self.description_label.setObjectName("scriptDescription")
        self.description_label.setWordWrap(True)
        info_layout.addWidget(self.description_label)
        
        # Removed extra spacing for tighter layout
        
        self.status_label = QLabel("")
        self.status_label.setObjectName("scriptStatus")
        info_layout.addWidget(self.status_label)
        
        info_layout.addStretch()
        
        main_layout.addLayout(info_layout, 1)
        
        button_type = self.metadata.get('button_type', ButtonType.RUN)
        button_options = self.metadata.get('button_options', None)
        
        self.action_widget = self.button_factory.create_button(
            button_type, 
            button_options,
            self.on_action_triggered
        )
        
        if self.action_widget:
            main_layout.addWidget(self.action_widget)
        
        if not self.script.is_available():
            logger.warning(f"Script '{self.metadata.get('name', 'Unknown')}' is not available on this system")
            self.setEnabled(False)
            self.status_label.setText("Script not available on this system")
        else:
            logger.debug(f"Script '{self.metadata.get('name', 'Unknown')}' is available and ready")
    
    def update_status(self):
        try:
            status = self.script.get_status_display()
            logger.debug(f"Status update for '{self.metadata.get('name', 'Unknown')}': {status}")
            
            button_type = self.metadata.get('button_type', ButtonType.RUN)
            
            if button_type == ButtonType.TOGGLE:
                status_text = f"Status: {status}"
                if hasattr(self.action_widget, 'update_state'):
                    is_on = str(self.script.get_status()).lower() in ['true', 'on', 'enabled', '1', 'yes']
                    self.action_widget.update_state(is_on)
            elif button_type == ButtonType.CYCLE:
                status_text = f"Current: {status}"
                if hasattr(self.action_widget, 'set_current'):
                    self.action_widget.set_current(status)
            elif button_type == ButtonType.SELECT:
                status_text = f"Selected: {status}"
                if hasattr(self.action_widget, 'setCurrentText'):
                    self.action_widget.setCurrentText(str(status))
            elif button_type in [ButtonType.NUMBER, ButtonType.SLIDER]:
                status_text = f"Value: {status}"
                if hasattr(self.action_widget, 'setValue'):
                    try:
                        self.action_widget.setValue(float(status))
                    except (ValueError, TypeError):
                        pass
            else:
                status_text = f"Ready" if status == "Unknown" else f"{status}"
            
            self.status_label.setText(status_text)
            # Reset status property for neutral styling
            self.status_label.setProperty("status", None)
            self.status_label.style().unpolish(self.status_label)
            self.status_label.style().polish(self.status_label)
            
        except Exception as e:
            logger.error(f"Error updating status for '{self.metadata.get('name', 'Unknown')}': {str(e)}")
            self.status_label.setText(f"Error: {str(e)}")
            self.status_label.setProperty("status", "error")
            self.status_label.style().unpolish(self.status_label)
            self.status_label.style().polish(self.status_label)
    
    @pyqtSlot()
    def on_action_triggered(self, *args, **kwargs):
        script_name = self.metadata.get('name', 'Unknown')
        logger.info(f"Action triggered for script: {script_name}")
        logger.debug(f"  Args: {args}, Kwargs: {kwargs}")
        
        # Check for rapid execution (throttling)
        current_time = time.time()
        if current_time - self.last_execution_time < self.min_execution_interval:
            logger.debug(f"Throttling execution for script '{script_name}' - too rapid")
            return
        
        if self.executor and self.executor.isRunning():
            logger.warning(f"Script '{script_name}' is already running")
            return
        
        try:
            if not self.script.validate():
                logger.error(f"Validation failed for script '{script_name}'")
                QMessageBox.warning(self, "Validation Failed", 
                                   "Script validation failed. Cannot execute.")
                return
            
            logger.info(f"Executing script '{script_name}'...")
            self.last_execution_time = current_time  # Update last execution time
            self.setEnabled(False)
            self.status_label.setText("Running...")
            self.status_label.setProperty("status", "running")
            self.status_label.style().unpolish(self.status_label)
            self.status_label.style().polish(self.status_label)
            
            self.executor = ScriptExecutor(self.script, *args, **kwargs)
            self.executor.finished.connect(self.on_execution_finished)
            self.executor.error.connect(self.on_execution_error)
            self.executor.start()
            
        except Exception as e:
            logger.error(f"Error starting script '{script_name}': {str(e)}", exc_info=True)
            self.on_execution_error(str(e))
    
    @pyqtSlot(dict)
    def on_execution_finished(self, result):
        script_name = self.metadata.get('name', 'Unknown')
        self.setEnabled(True)
        
        success = result.get('success', False)
        message = result.get('message', '')
        
        logger.info(f"Script '{script_name}' execution finished - Success: {success}")
        if message:
            logger.info(f"  Message: {message}")
        
        if success:
            # Show success in status label with message if available
            if message:
                self.status_label.setText(f"Success: {message}")
            else:
                self.status_label.setText("Success")
            self.status_label.setProperty("status", "success")
            # No popup for success
        else:
            self.status_label.setText("Failed")
            self.status_label.setProperty("status", "error")
            # Only show popup for failures (keep error notifications)
            if message:
                QMessageBox.warning(self, "Script Failed", message)
        
        # Apply the status styling
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)
        
        self.update_status()
        self.script_executed.emit(self.metadata.get('name', ''), result)
    
    @pyqtSlot(str)
    def on_execution_error(self, error_msg):
        script_name = self.metadata.get('name', 'Unknown')
        logger.error(f"Script '{script_name}' execution error: {error_msg}")
        self.setEnabled(True)
        self.status_label.setText(f"Error: {error_msg}")
        self.status_label.setProperty("status", "error")
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)
        QMessageBox.critical(self, "Execution Error", 
                           f"Script execution failed:\n{error_msg}")