import logging
from typing import Optional, Callable, Any
from PyQt6.QtWidgets import (QPushButton, QComboBox, QSlider, QLineEdit,
                             QSpinBox, QDoubleSpinBox, QWidget, QHBoxLayout,
                             QLabel)
from PyQt6.QtCore import Qt, pyqtSignal

from core.button_types import (ButtonType, ButtonOptions, ToggleOptions, 
                               CycleOptions, SelectOptions, NumberOptions,
                               SliderOptions, TextInputOptions, RunOptions)

logger = logging.getLogger('GUI.ButtonFactory')

class ToggleButton(QPushButton):
    toggled_custom = pyqtSignal(bool)
    
    def __init__(self, options: ToggleOptions, callback: Callable):
        super().__init__()
        self.options = options
        self.callback = callback
        self.is_on = False
        self.setObjectName("toggleButton")
        self.update_state(False)
        self.clicked.connect(self.on_clicked)
    
    def on_clicked(self):
        self.is_on = not self.is_on
        self.update_state(self.is_on)
        self.callback(self.is_on)
        self.toggled_custom.emit(self.is_on)
    
    def update_state(self, is_on: bool):
        self.is_on = is_on
        text = self.options.on_label if is_on else self.options.off_label
        self.setText(text)
        self.setProperty("state", "on" if is_on else "off")
        self.style().unpolish(self)
        self.style().polish(self)

class CycleButton(QPushButton):
    cycled = pyqtSignal(str)
    
    def __init__(self, options: CycleOptions, callback: Callable):
        super().__init__()
        self.options = options
        self.callback = callback
        self.current_index = 0
        self.setObjectName("cycleButton")
        self.update_text()
        self.clicked.connect(self.on_clicked)
    
    def on_clicked(self):
        if self.options.options:
            self.current_index = (self.current_index + 1) % len(self.options.options)
            current_option = self.options.options[self.current_index]
            self.update_text()
            self.callback(current_option)
            self.cycled.emit(current_option)
    
    def update_text(self):
        if self.options.options and self.options.show_current:
            current = self.options.options[self.current_index]
            self.setText(f"Switch to: {self.options.options[(self.current_index + 1) % len(self.options.options)]}")
        else:
            self.setText("Cycle")
    
    def set_current(self, value: str):
        if value in self.options.options:
            self.current_index = self.options.options.index(value)
            self.update_text()

class SliderWidget(QWidget):
    value_changed = pyqtSignal(float)
    
    def __init__(self, options: SliderOptions, callback: Callable):
        super().__init__()
        self.options = options
        self.callback = callback
        self.is_updating = False
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(int(options.min_value))
        self.slider.setMaximum(int(options.max_value))
        self.slider.setSingleStep(int(options.step))
        
        layout.addWidget(self.slider)
        
        if options.show_value:
            self.value_label = QLabel(str(options.min_value))
            layout.addWidget(self.value_label)
        
        self.slider.valueChanged.connect(self.on_value_changed)
    
    def on_value_changed(self, value):
        float_value = float(value)
        if self.options.show_value:
            display_text = f"{float_value}{self.options.suffix}"
            self.value_label.setText(display_text)
        
        if not self.is_updating:
            self.callback(float_value)
            self.value_changed.emit(float_value)
    
    def setValue(self, value):
        self.is_updating = True
        self.slider.setValue(int(value))
        self.is_updating = False

class ButtonFactory:
    
    @staticmethod
    def create_button(button_type: ButtonType, 
                     options: Optional[ButtonOptions],
                     callback: Callable) -> Optional[QWidget]:
        
        if isinstance(button_type, str):
            try:
                button_type = ButtonType(button_type)
                logger.debug(f"Converted string '{button_type}' to ButtonType")
            except ValueError:
                logger.warning(f"Unknown button type string: '{button_type}', defaulting to RUN")
                button_type = ButtonType.RUN
        
        logger.debug(f"Creating button of type: {button_type.value}")
        
        if button_type == ButtonType.RUN:
            opts = options if isinstance(options, RunOptions) else RunOptions()
            button = QPushButton(opts.button_text)
            button.clicked.connect(lambda: callback())
            logger.debug(f"Created RUN button with text: '{opts.button_text}'")
            return button
        
        elif button_type == ButtonType.TOGGLE:
            opts = options if isinstance(options, ToggleOptions) else ToggleOptions()
            logger.debug(f"Created TOGGLE button: {opts.on_label}/{opts.off_label}")
            return ToggleButton(opts, callback)
        
        elif button_type == ButtonType.CYCLE:
            opts = options if isinstance(options, CycleOptions) else CycleOptions()
            logger.debug(f"Created CYCLE button with {len(opts.options)} options")
            return CycleButton(opts, callback)
        
        elif button_type == ButtonType.SELECT:
            opts = options if isinstance(options, SelectOptions) else SelectOptions()
            combo = QComboBox()
            if opts.options:
                combo.addItems(opts.options)
            combo.setPlaceholderText(opts.placeholder)
            combo.currentTextChanged.connect(callback)
            logger.debug(f"Created SELECT dropdown with {len(opts.options) if opts.options else 0} options")
            return combo
        
        elif button_type == ButtonType.NUMBER:
            opts = options if isinstance(options, NumberOptions) else NumberOptions()
            if opts.decimals > 0:
                spinbox = QDoubleSpinBox()
                spinbox.setDecimals(opts.decimals)
            else:
                spinbox = QSpinBox()
            
            if opts.min_value is not None:
                spinbox.setMinimum(opts.min_value)
            if opts.max_value is not None:
                spinbox.setMaximum(opts.max_value)
            spinbox.setSingleStep(opts.step)
            if opts.suffix:
                spinbox.setSuffix(opts.suffix)
            
            spinbox.valueChanged.connect(callback)
            return spinbox
        
        elif button_type == ButtonType.SLIDER:
            opts = options if isinstance(options, SliderOptions) else SliderOptions()
            logger.debug(f"Created SLIDER: range {opts.min_value}-{opts.max_value}")
            return SliderWidget(opts, callback)
        
        elif button_type == ButtonType.TEXT_INPUT:
            opts = options if isinstance(options, TextInputOptions) else TextInputOptions()
            line_edit = QLineEdit()
            line_edit.setPlaceholderText(opts.placeholder)
            if opts.max_length:
                line_edit.setMaxLength(opts.max_length)
            
            button = QPushButton("Submit")
            widget = QWidget()
            layout = QHBoxLayout(widget)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(line_edit)
            layout.addWidget(button)
            
            button.clicked.connect(lambda: callback(line_edit.text()))
            line_edit.returnPressed.connect(lambda: callback(line_edit.text()))
            
            return widget
        
        elif button_type == ButtonType.CONFIRM:
            button = QPushButton("Execute")
            button.clicked.connect(lambda: callback())
            return button
        
        else:
            logger.warning(f"Unhandled button type: {button_type}, creating default RUN button")
            button = QPushButton("Run")
            button.clicked.connect(lambda: callback())
            return button