"""
Preset Editor View - Pure UI component for script preset configuration.

This view provides a dialog for creating and editing script argument presets,
with no business logic - only UI display and user input handling.
"""
import logging
from typing import Dict, Any, List, Optional
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QLineEdit, QDialogButtonBox,
                             QComboBox, QCheckBox, QSpinBox, QDoubleSpinBox,
                             QFormLayout, QWidget, QScrollArea, QMessageBox,
                             QListWidget, QListWidgetItem, QSplitter,
                             QGroupBox, QTextEdit)
from PyQt6.QtCore import Qt, pyqtSignal

logger = logging.getLogger('Views.PresetEditor')


class ArgumentWidget(QWidget):
    """Widget for editing a single argument value"""
    
    value_changed = pyqtSignal(str, object)  # arg_name, value
    
    def __init__(self, arg_info: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.arg_name = arg_info['name']
        self.arg_type = arg_info.get('type', 'str')
        self.arg_info = arg_info
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI based on argument type"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Label
        label = QLabel(self.arg_info.get('help', self.arg_name) + ":")
        label.setMinimumWidth(150)
        layout.addWidget(label)
        
        # Create appropriate widget based on type and choices
        if self.arg_info.get('choices'):
            # Use combo box for choices
            self.value_widget = QComboBox()
            self.value_widget.addItems([str(c) for c in self.arg_info['choices']])
            self.value_widget.currentTextChanged.connect(
                lambda text: self.value_changed.emit(self.arg_name, text)
            )
        elif self.arg_type == 'bool':
            # Use checkbox for boolean
            self.value_widget = QCheckBox()
            self.value_widget.stateChanged.connect(
                lambda state: self.value_changed.emit(
                    self.arg_name, 
                    state == Qt.CheckState.Checked.value
                )
            )
        elif self.arg_type == 'int':
            # Use spinbox for integer
            self.value_widget = QSpinBox()
            self.value_widget.setMinimum(-999999)
            self.value_widget.setMaximum(999999)
            self.value_widget.valueChanged.connect(
                lambda value: self.value_changed.emit(self.arg_name, value)
            )
        elif self.arg_type == 'float':
            # Use double spinbox for float
            self.value_widget = QDoubleSpinBox()
            self.value_widget.setMinimum(-999999.0)
            self.value_widget.setMaximum(999999.0)
            self.value_widget.setDecimals(4)
            self.value_widget.valueChanged.connect(
                lambda value: self.value_changed.emit(self.arg_name, value)
            )
        else:
            # Use line edit for string and unknown types
            self.value_widget = QLineEdit()
            self.value_widget.textChanged.connect(
                lambda text: self.value_changed.emit(self.arg_name, text)
            )
        
        layout.addWidget(self.value_widget)
        layout.addStretch()
    
    def set_value(self, value: Any):
        """Set the widget value"""
        if isinstance(self.value_widget, QComboBox):
            index = self.value_widget.findText(str(value))
            if index >= 0:
                self.value_widget.setCurrentIndex(index)
        elif isinstance(self.value_widget, QCheckBox):
            self.value_widget.setChecked(bool(value))
        elif isinstance(self.value_widget, (QSpinBox, QDoubleSpinBox)):
            self.value_widget.setValue(value)
        elif isinstance(self.value_widget, QLineEdit):
            self.value_widget.setText(str(value) if value is not None else "")
    
    def get_value(self) -> Any:
        """Get the widget value"""
        if isinstance(self.value_widget, QComboBox):
            return self.value_widget.currentText()
        elif isinstance(self.value_widget, QCheckBox):
            return self.value_widget.isChecked()
        elif isinstance(self.value_widget, (QSpinBox, QDoubleSpinBox)):
            return self.value_widget.value()
        elif isinstance(self.value_widget, QLineEdit):
            text = self.value_widget.text()
            # Try to convert to appropriate type
            if self.arg_type == 'int':
                try:
                    return int(text) if text else None
                except ValueError:
                    return None
            elif self.arg_type == 'float':
                try:
                    return float(text) if text else None
                except ValueError:
                    return None
            return text if text else None


class PresetEditorView(QDialog):
    """
    View for editing script presets - pure UI component.
    
    This view provides the interface for creating and editing script
    argument presets with no business logic - only UI display and user input.
    """
    
    # Signals for controller
    preset_saved = pyqtSignal(str, dict)  # preset_name, arguments
    preset_deleted = pyqtSignal(str)  # preset_name
    preset_selected = pyqtSignal(str)  # preset_name
    auto_generate_requested = pyqtSignal()
    
    def __init__(self, script_name: str, script_args: List[Dict[str, Any]], 
                 existing_presets: Optional[Dict[str, Dict[str, Any]]] = None,
                 parent=None):
        super().__init__(parent)
        self.script_name = script_name
        self.script_args = script_args
        self.existing_presets = existing_presets or {}
        self.current_preset_name = None
        self.argument_widgets = {}
        
        self.setWindowTitle(f"Preset Editor - {script_name}")
        self.setModal(True)
        self.setMinimumSize(600, 400)
        
        self.init_ui()
        
        logger.info(f"PresetEditorView initialized for script: {script_name}")
    
    def init_ui(self):
        """Initialize the UI components"""
        layout = QVBoxLayout(self)
        
        # Header
        header_label = QLabel(f"<b>Configure presets for:</b> {self.script_name}")
        layout.addWidget(header_label)
        
        # Main content area with splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side - Preset list
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        left_layout.addWidget(QLabel("<b>Presets:</b>"))
        
        self.preset_list = QListWidget()
        self.preset_list.itemClicked.connect(self.on_preset_selected)
        left_layout.addWidget(self.preset_list)
        
        # Preset list buttons
        list_buttons = QHBoxLayout()
        
        new_btn = QPushButton("New")
        new_btn.clicked.connect(self.new_preset)
        list_buttons.addWidget(new_btn)
        
        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self.delete_current_preset)
        list_buttons.addWidget(delete_btn)
        
        auto_gen_btn = QPushButton("Auto Generate")
        auto_gen_btn.clicked.connect(self.auto_generate_requested.emit)
        auto_gen_btn.setToolTip("Generate presets based on argument choices")
        list_buttons.addWidget(auto_gen_btn)
        
        left_layout.addLayout(list_buttons)
        
        splitter.addWidget(left_widget)
        
        # Right side - Preset editor
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # Preset name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Preset Name:"))
        self.preset_name_edit = QLineEdit()
        self.preset_name_edit.setPlaceholderText("Enter preset name...")
        name_layout.addWidget(self.preset_name_edit)
        right_layout.addLayout(name_layout)
        
        # Arguments area
        right_layout.addWidget(QLabel("<b>Arguments:</b>"))
        
        # Scroll area for arguments
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        self.args_layout = QVBoxLayout(scroll_widget)
        
        # Create widgets for each argument
        if self.script_args:
            for arg_info in self.script_args:
                arg_widget = ArgumentWidget(arg_info)
                arg_widget.value_changed.connect(self.on_argument_changed)
                self.argument_widgets[arg_info['name']] = arg_widget
                self.args_layout.addWidget(arg_widget)
        else:
            no_args_label = QLabel("This script has no configurable arguments")
            no_args_label.setStyleSheet("color: #999;")
            self.args_layout.addWidget(no_args_label)
        
        self.args_layout.addStretch()
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        right_layout.addWidget(scroll_area)
        
        # Save button for current preset
        save_preset_btn = QPushButton("Save Current Preset")
        save_preset_btn.clicked.connect(self.save_current_preset)
        right_layout.addWidget(save_preset_btn)
        
        splitter.addWidget(right_widget)
        splitter.setSizes([200, 400])
        
        layout.addWidget(splitter)
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Load existing presets
        self.load_presets()
    
    def load_presets(self):
        """Load existing presets into the list"""
        self.preset_list.clear()
        for preset_name in sorted(self.existing_presets.keys()):
            self.preset_list.addItem(preset_name)
        
        # Select first preset if available
        if self.preset_list.count() > 0:
            self.preset_list.setCurrentRow(0)
            self.on_preset_selected(self.preset_list.item(0))
    
    def on_preset_selected(self, item: QListWidgetItem):
        """Handle preset selection"""
        if not item:
            return
        
        preset_name = item.text()
        self.current_preset_name = preset_name
        self.preset_name_edit.setText(preset_name)
        
        # Load preset values
        if preset_name in self.existing_presets:
            preset_data = self.existing_presets[preset_name]
            for arg_name, arg_widget in self.argument_widgets.items():
                if arg_name in preset_data:
                    arg_widget.set_value(preset_data[arg_name])
                else:
                    # Clear value if not in preset
                    arg_widget.set_value(None)
        
        self.preset_selected.emit(preset_name)
    
    def on_argument_changed(self, arg_name: str, value: Any):
        """Handle argument value changes"""
        # Could emit signal for real-time updates if needed
        pass
    
    def new_preset(self):
        """Create a new preset"""
        # Generate unique name
        base_name = "New Preset"
        name = base_name
        counter = 1
        while name in self.existing_presets:
            counter += 1
            name = f"{base_name} {counter}"
        
        # Add to list
        self.existing_presets[name] = {}
        self.preset_list.addItem(name)
        
        # Select the new preset
        items = self.preset_list.findItems(name, Qt.MatchFlag.MatchExactly)
        if items:
            self.preset_list.setCurrentItem(items[0])
            self.on_preset_selected(items[0])
    
    def save_current_preset(self):
        """Save the current preset"""
        preset_name = self.preset_name_edit.text().strip()
        
        if not preset_name:
            QMessageBox.warning(self, "Invalid Name", 
                              "Please enter a preset name")
            return
        
        # Collect argument values
        arguments = {}
        for arg_name, arg_widget in self.argument_widgets.items():
            value = arg_widget.get_value()
            if value is not None:  # Only save non-None values
                arguments[arg_name] = value
        
        # Check if renaming
        if self.current_preset_name and self.current_preset_name != preset_name:
            # Remove old name from list
            items = self.preset_list.findItems(
                self.current_preset_name, 
                Qt.MatchFlag.MatchExactly
            )
            if items:
                row = self.preset_list.row(items[0])
                self.preset_list.takeItem(row)
            
            # Remove from presets dict
            if self.current_preset_name in self.existing_presets:
                del self.existing_presets[self.current_preset_name]
        
        # Save preset
        self.existing_presets[preset_name] = arguments
        
        # Update list if new name
        if not self.preset_list.findItems(preset_name, Qt.MatchFlag.MatchExactly):
            self.preset_list.addItem(preset_name)
        
        # Select the saved preset
        items = self.preset_list.findItems(preset_name, Qt.MatchFlag.MatchExactly)
        if items:
            self.preset_list.setCurrentItem(items[0])
            self.current_preset_name = preset_name
        
        # Emit signal
        self.preset_saved.emit(preset_name, arguments)
        
        QMessageBox.information(self, "Preset Saved", 
                              f"Preset '{preset_name}' has been saved")
    
    def delete_current_preset(self):
        """Delete the currently selected preset"""
        current_item = self.preset_list.currentItem()
        if not current_item:
            return
        
        preset_name = current_item.text()
        
        reply = QMessageBox.question(
            self, "Delete Preset",
            f"Are you sure you want to delete preset '{preset_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Remove from list
            row = self.preset_list.row(current_item)
            self.preset_list.takeItem(row)
            
            # Remove from presets dict
            if preset_name in self.existing_presets:
                del self.existing_presets[preset_name]
            
            # Clear editor
            self.preset_name_edit.clear()
            for arg_widget in self.argument_widgets.values():
                arg_widget.set_value(None)
            
            self.current_preset_name = None
            
            # Emit signal
            self.preset_deleted.emit(preset_name)
    
    def add_preset(self, preset_name: str, arguments: Dict[str, Any]):
        """Add a new preset (called by controller after auto-generation)"""
        self.existing_presets[preset_name] = arguments
        if not self.preset_list.findItems(preset_name, Qt.MatchFlag.MatchExactly):
            self.preset_list.addItem(preset_name)
    
    def get_presets(self) -> Dict[str, Dict[str, Any]]:
        """Get all current presets"""
        return self.existing_presets.copy()