import logging
import time
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, 
                             QLabel, QMessageBox, QSizePolicy, QPushButton)
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
        # Compact menu-item styling
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(30)
        self.setMaximumHeight(30)
        
        # Single line horizontal layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(8, 4, 8, 4)
        main_layout.setSpacing(8)
        
        # Script name only - compact
        self.name_label = QLabel(self.metadata.get('name', 'Unnamed Script'))
        self.name_label.setObjectName("scriptName")
        
        # Truncate long names to fit
        name = self.metadata.get('name', 'Unnamed Script')
        if len(name) > 18:
            name = name[:15] + "..."
        self.name_label.setText(name)
        
        main_layout.addWidget(self.name_label, 1)  # Take available space
        
        # Status indicator (visual only)
        button_type = self.metadata.get('button_type', ButtonType.RUN)
        self.status_indicator = self._create_status_indicator(button_type)
        main_layout.addWidget(self.status_indicator)
        
        # Set tooltip with full description
        description = self.metadata.get('description', 'No description')
        self.setToolTip(f"{self.metadata.get('name', 'Unknown')}\n{description}")
        
        if not self.script.is_available():
            logger.warning(f"Script '{self.metadata.get('name', 'Unknown')}' is not available on this system")
            self.setEnabled(False)
            self.setToolTip("Script not available on this system")
        else:
            logger.debug(f"Script '{self.metadata.get('name', 'Unknown')}' is available and ready")
    
    def _create_status_indicator(self, button_type):
        """Create visual-only status indicator"""
        indicator = QLabel()
        indicator.setObjectName("statusIndicator")
        indicator.setFixedSize(24, 24)
        indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        if button_type == ButtonType.RUN:
            indicator.setText("●")  # Ready indicator
        elif button_type == ButtonType.TOGGLE:
            indicator.setText("⚪")  # Off indicator (will update in update_status)
        elif button_type == ButtonType.CYCLE:
            indicator.setText("⟳")  # Cycle indicator (will update in update_status)
        else:
            indicator.setText("●")  # Default indicator
        
        return indicator
    
    def mousePressEvent(self, event):
        """Handle clicking anywhere on the script row"""
        if event.button() == Qt.MouseButton.LeftButton and self.isEnabled():
            # Determine what to execute based on script type
            button_type = self.metadata.get('button_type', ButtonType.RUN)
            
            if button_type == ButtonType.RUN:
                self.on_action_triggered()
            elif button_type == ButtonType.TOGGLE:
                # For toggle, we need to determine current state and flip it
                status = self.script.get_status()
                current_state = status and status.lower() in ['on', 'enabled', 'true', 'active']
                self.on_action_triggered(not current_state)
            elif button_type == ButtonType.CYCLE:
                # For cycle, advance to next option
                self._cycle_to_next_option()
            else:
                self.on_action_triggered()
        
        super().mousePressEvent(event)
    
    def _cycle_to_next_option(self):
        """Handle cycling to next option for cycle scripts"""
        button_options = self.metadata.get('button_options', None)
        if not button_options or not hasattr(button_options, 'options'):
            return
        
        options = button_options.options
        if not options:
            return
        
        # Get current status to determine current option
        current_status = self.script.get_status()
        current_index = 0
        
        # Find current option index
        for i, option in enumerate(options):
            if option.lower() in current_status.lower() or current_status.lower() in option.lower():
                current_index = i
                break
        
        # Move to next option
        next_index = (current_index + 1) % len(options)
        next_option = options[next_index]
        
        # Execute with the full option name
        self.on_action_triggered(next_option)
    
    def update_status(self):
        try:
            status = self.script.get_status_display()
            logger.debug(f"Status update for '{self.metadata.get('name', 'Unknown')}': {status}")
            
            button_type = self.metadata.get('button_type', ButtonType.RUN)
            
            # Update tooltip with current status
            description = self.metadata.get('description', 'No description')
            script_name = self.metadata.get('name', 'Unknown')
            self.setToolTip(f"{script_name}\n{description}\nStatus: {status}")
            
            # Update status indicator appearance based on status
            if button_type == ButtonType.TOGGLE and self.status_indicator:
                # Update toggle indicator appearance
                if status and status.lower() in ['on', 'enabled', 'true', 'active']:
                    self.status_indicator.setText("⚫")  # Filled circle for "on"
                else:
                    self.status_indicator.setText("⚪")  # Empty circle for "off"
                    
            elif button_type == ButtonType.CYCLE and self.status_indicator:
                # Update cycle indicator to show current state
                options = self.metadata.get('button_options', None)
                if options and hasattr(options, 'options'):
                    # Find matching option and show abbreviated version
                    for option in options.options:
                        if option.lower() in status.lower() or status.lower() in option.lower():
                            self.status_indicator.setText(option[:2])
                            break
                            
            elif button_type == ButtonType.RUN and self.status_indicator:
                # For run scripts, show ready/running state
                if hasattr(self, 'executor') and self.executor and self.executor.isRunning():
                    self.status_indicator.setText("◐")  # Running indicator
                else:
                    self.status_indicator.setText("●")  # Ready indicator
                
        except Exception as e:
            logger.error(f"Error updating status for '{self.metadata.get('name', 'Unknown')}': {e}")
            self.setToolTip(f"{self.metadata.get('name', 'Unknown')}\nStatus: Error")
    
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
            # Update tooltip to show running state
            self.setToolTip(f"{script_name}\nRunning...")
            # Update status indicator to show running
            if self.status_indicator:
                self.status_indicator.setText("◐")
            
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
        
        # Update tooltip with result
        script_name = self.metadata.get('name', 'Unknown')
        description = self.metadata.get('description', 'No description')
        
        if success:
            # Update tooltip to show success
            if message:
                self.setToolTip(f"{script_name}\n{description}\nSuccess: {message}")
            else:
                self.setToolTip(f"{script_name}\n{description}\nCompleted successfully")
            # No popup for success
        else:
            self.setToolTip(f"{script_name}\n{description}\nFailed")
            # Only show popup for failures (keep error notifications)
            if message:
                QMessageBox.warning(self, "Script Failed", message)
        
        self.update_status()
        self.script_executed.emit(self.metadata.get('name', ''), result)
    
    @pyqtSlot(str)
    def on_execution_error(self, error_msg):
        script_name = self.metadata.get('name', 'Unknown')
        description = self.metadata.get('description', 'No description')
        logger.error(f"Script '{script_name}' execution error: {error_msg}")
        self.setEnabled(True)
        
        # Update tooltip with error
        self.setToolTip(f"{script_name}\n{description}\nError: {error_msg}")
        
        QMessageBox.critical(self, "Execution Error", 
                           f"Script execution failed:\n{error_msg}")