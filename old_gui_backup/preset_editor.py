"""
Preset Editor Dialog for Script Configuration

Provides a sophisticated interface for creating and editing script presets
with different input types based on argument specifications.
"""

import logging
from typing import Dict, Any, Optional
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox,
                             QCheckBox, QPushButton, QLabel, QTextEdit,
                             QDialogButtonBox, QMessageBox, QGroupBox)
from PyQt6.QtCore import Qt

from core.script_analyzer import ScriptInfo, ArgumentInfo

logger = logging.getLogger('GUI.PresetEditor')

class PresetEditorDialog(QDialog):
    """Dialog for editing script preset configurations"""
    
    def __init__(self, script_info: ScriptInfo, preset_name: str = "", 
                 current_args: Optional[Dict[str, Any]] = None, parent=None):
        super().__init__(parent)
        self.script_info = script_info
        self.preset_name = preset_name
        self.current_args = current_args or {}
        self.argument_widgets = {}
        self.is_editing = bool(preset_name)
        
        self.init_ui()
        self.load_current_values()
        
    def init_ui(self):
        """Initialize the user interface"""
        title = f"{'Edit' if self.is_editing else 'Create'} Preset: {self.script_info.display_name}"
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumSize(500, 400)
        
        layout = QVBoxLayout(self)
        
        # Preset name input
        name_group = QGroupBox("Preset Configuration")
        name_layout = QFormLayout(name_group)
        
        self.preset_name_edit = QLineEdit()
        self.preset_name_edit.setText(self.preset_name)
        self.preset_name_edit.setPlaceholderText("Enter a name for this preset...")
        name_layout.addRow("Preset Name:", self.preset_name_edit)
        
        layout.addWidget(name_group)
        
        # Arguments section
        if self.script_info.arguments:
            args_group = QGroupBox("Script Arguments")
            args_layout = QFormLayout(args_group)
            
            for arg_info in self.script_info.arguments:
                widget = self._create_argument_widget(arg_info)
                if widget:
                    label_text = arg_info.name
                    if arg_info.required:
                        label_text += " *"
                    if arg_info.help:
                        label_text += f" ({arg_info.help})"
                    
                    args_layout.addRow(label_text, widget)
                    self.argument_widgets[arg_info.name] = widget
            
            layout.addWidget(args_group)
        
        # Help text
        help_label = QLabel("* Required arguments must be filled")
        help_label.setStyleSheet("color: #888888; font-style: italic;")
        layout.addWidget(help_label)
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Set focus to preset name if creating new preset
        if not self.is_editing:
            self.preset_name_edit.setFocus()
    
    def _create_argument_widget(self, arg_info: ArgumentInfo):
        """Create appropriate input widget based on argument type"""
        
        if arg_info.choices:
            # Dropdown for choice arguments
            combo = QComboBox()
            combo.addItems(arg_info.choices)
            combo.setEditable(False)
            return combo
        
        elif arg_info.type == "bool":
            # Checkbox for boolean arguments
            checkbox = QCheckBox()
            return checkbox
        
        elif arg_info.type == "int":
            # Spin box for integer arguments
            spinbox = QSpinBox()
            spinbox.setRange(-2147483648, 2147483647)
            if arg_info.default is not None:
                try:
                    spinbox.setValue(int(arg_info.default))
                except (ValueError, TypeError):
                    pass
            return spinbox
        
        elif arg_info.type == "float":
            # Double spin box for float arguments
            spinbox = QDoubleSpinBox()
            spinbox.setRange(-1000000.0, 1000000.0)
            spinbox.setDecimals(6)
            if arg_info.default is not None:
                try:
                    spinbox.setValue(float(arg_info.default))
                except (ValueError, TypeError):
                    pass
            return spinbox
        
        else:
            # Text edit for string arguments
            if arg_info.help and any(word in arg_info.help.lower() 
                                   for word in ['multiline', 'text', 'description']):
                # Multi-line text for longer inputs
                text_edit = QTextEdit()
                text_edit.setMaximumHeight(100)
                return text_edit
            else:
                # Single-line text input
                line_edit = QLineEdit()
                if arg_info.default:
                    line_edit.setText(str(arg_info.default))
                return line_edit
    
    def load_current_values(self):
        """Load current argument values into widgets"""
        for arg_name, value in self.current_args.items():
            if arg_name in self.argument_widgets:
                widget = self.argument_widgets[arg_name]
                
                if isinstance(widget, QComboBox):
                    index = widget.findText(str(value))
                    if index >= 0:
                        widget.setCurrentIndex(index)
                
                elif isinstance(widget, QCheckBox):
                    widget.setChecked(bool(value))
                
                elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                    try:
                        widget.setValue(float(value) if isinstance(widget, QDoubleSpinBox) else int(value))
                    except (ValueError, TypeError):
                        pass
                
                elif isinstance(widget, QTextEdit):
                    widget.setPlainText(str(value))
                
                elif isinstance(widget, QLineEdit):
                    widget.setText(str(value))
    
    def get_preset_name(self) -> str:
        """Get the preset name"""
        return self.preset_name_edit.text().strip()
    
    def get_arguments(self) -> Dict[str, Any]:
        """Extract argument values from widgets"""
        arguments = {}
        
        for arg_info in self.script_info.arguments:
            if arg_info.name in self.argument_widgets:
                widget = self.argument_widgets[arg_info.name]
                value = self._extract_widget_value(widget, arg_info)
                
                if value is not None:
                    arguments[arg_info.name] = value
        
        return arguments
    
    def _extract_widget_value(self, widget, arg_info: ArgumentInfo):
        """Extract value from a widget based on its type"""
        
        if isinstance(widget, QComboBox):
            return widget.currentText()
        
        elif isinstance(widget, QCheckBox):
            return widget.isChecked()
        
        elif isinstance(widget, QSpinBox):
            return widget.value()
        
        elif isinstance(widget, QDoubleSpinBox):
            return widget.value()
        
        elif isinstance(widget, QTextEdit):
            text = widget.toPlainText().strip()
            return text if text else None
        
        elif isinstance(widget, QLineEdit):
            text = widget.text().strip()
            return text if text else None
        
        return None
    
    def validate_inputs(self) -> bool:
        """Validate all inputs before accepting"""
        
        # Check preset name
        preset_name = self.get_preset_name()
        if not preset_name:
            QMessageBox.warning(self, "Invalid Input", "Please enter a preset name.")
            self.preset_name_edit.setFocus()
            return False
        
        # Check required arguments
        arguments = self.get_arguments()
        for arg_info in self.script_info.arguments:
            if arg_info.required and arg_info.name not in arguments:
                QMessageBox.warning(
                    self, "Missing Required Argument",
                    f"The argument '{arg_info.name}' is required."
                )
                if arg_info.name in self.argument_widgets:
                    self.argument_widgets[arg_info.name].setFocus()
                return False
        
        return True
    
    def accept(self):
        """Override accept to validate inputs"""
        if self.validate_inputs():
            super().accept()