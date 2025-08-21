import logging
from typing import List, Callable, Optional
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QPushButton, QLabel,
                             QSlider, QVBoxLayout, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

logger = logging.getLogger('GUI.ModernWidgets')

class SegmentedControl(QWidget):
    """Modern segmented control widget showing all options at once"""
    value_changed = pyqtSignal(str)
    
    def __init__(self, options: List[str], callback: Callable[[str], None]):
        super().__init__()
        self.options = options
        self.callback = callback
        self.current_index = 0
        self.buttons = []
        self.is_updating = False  # Prevent recursive updates
        
        self.init_ui()
    
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        for i, option in enumerate(self.options):
            button = QPushButton(option)
            button.setCheckable(True)
            button.setObjectName("segmentButton")
            button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            button.setMinimumHeight(60)
            button.clicked.connect(lambda checked, idx=i: self.on_segment_clicked(idx))
            
            # Style the first and last buttons with special border radius
            if len(self.options) == 1:
                button.setProperty("position", "single")
            elif i == 0:
                button.setProperty("position", "first")
            elif i == len(self.options) - 1:
                button.setProperty("position", "last")
            else:
                button.setProperty("position", "middle")
            
            self.buttons.append(button)
            layout.addWidget(button)
        
        # Don't set initial selection - let set_current() handle this
        # This prevents defaulting to first option when widget is recreated
    
    def on_segment_clicked(self, index):
        """Handle segment button click"""
        if self.is_updating or not (0 <= index < len(self.options)):
            return
            
        # Only proceed if this is actually a different selection
        if index == self.current_index:
            return
            
        self.is_updating = True
        self.current_index = index
        
        # Update button states
        for i, button in enumerate(self.buttons):
            button.setChecked(i == index)
        
        self.update_button_styles()
        
        # Call callback and emit signal
        selected_option = self.options[index]
        self.callback(selected_option)
        self.value_changed.emit(selected_option)
        
        self.is_updating = False
    
    def update_button_styles(self):
        """Update button styles based on selection"""
        for i, button in enumerate(self.buttons):
            if button.isChecked():
                button.setProperty("selected", True)
            else:
                button.setProperty("selected", False)
            
            # Force style update
            button.style().unpolish(button)
            button.style().polish(button)
    
    def set_current(self, value: str):
        """Set the current value programmatically"""
        if value in self.options:
            index = self.options.index(value)
            if index != self.current_index:
                self.is_updating = True
                self.current_index = index
                
                # Update button states without triggering callback
                for i, button in enumerate(self.buttons):
                    button.setChecked(i == index)
                
                self.update_button_styles()
                self.is_updating = False

class EnhancedSlider(QWidget):
    """Enhanced slider with integrated value display and icons"""
    value_changed = pyqtSignal(float)
    
    def __init__(self, min_val: float = 0, max_val: float = 100, 
                 step: float = 1, suffix: str = "", 
                 show_value: bool = True, callback: Callable[[float], None] = None):
        super().__init__()
        self.min_val = min_val
        self.max_val = max_val
        self.step = step
        self.suffix = suffix
        self.show_value = show_value
        self.callback = callback
        self.is_updating = False
        
        self.init_ui()
    
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # Volume icon (low)
        self.min_icon = QLabel("🔇")
        self.min_icon.setFixedSize(20, 20)
        self.min_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.min_icon)
        
        # Slider container
        slider_container = QWidget()
        slider_layout = QVBoxLayout(slider_container)
        slider_layout.setContentsMargins(0, 0, 0, 0)
        slider_layout.setSpacing(4)
        
        # Slider
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(int(self.min_val))
        self.slider.setMaximum(int(self.max_val))
        self.slider.setSingleStep(int(self.step))
        self.slider.valueChanged.connect(self.on_value_changed)
        
        slider_layout.addWidget(self.slider)
        
        # Value display (positioned below slider)
        if self.show_value:
            self.value_label = QLabel(f"{self.min_val}{self.suffix}")
            self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.value_label.setObjectName("sliderValue")
            slider_layout.addWidget(self.value_label)
        
        layout.addWidget(slider_container, 1)
        
        # Volume icon (high)
        self.max_icon = QLabel("🔊")
        self.max_icon.setFixedSize(20, 20)
        self.max_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.max_icon)
    
    def on_value_changed(self, value):
        """Handle slider value change"""
        float_value = float(value)
        
        if self.show_value:
            display_text = f"{int(float_value)}{self.suffix}"
            self.value_label.setText(display_text)
        
        if not self.is_updating:
            if self.callback:
                self.callback(float_value)
            self.value_changed.emit(float_value)
    
    def setValue(self, value):
        """Set slider value programmatically"""
        self.is_updating = True
        self.slider.setValue(int(value))
        if self.show_value:
            display_text = f"{int(value)}{self.suffix}"
            self.value_label.setText(display_text)
        self.is_updating = False

class ButtonGroup(QWidget):
    """Modern button group for power plans and similar multi-option controls"""
    value_changed = pyqtSignal(str)
    
    def __init__(self, options: List[str], callback: Callable[[str], None]):
        super().__init__()
        self.options = options
        self.callback = callback
        self.current_index = 0
        self.buttons = []
        self.is_updating = False  # Prevent recursive updates
        
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        for i, option in enumerate(self.options):
            button = QPushButton(option)
            button.setCheckable(True)
            button.setObjectName("groupButton")
            button.clicked.connect(lambda checked, idx=i: self.on_button_clicked(idx))
            
            self.buttons.append(button)
            layout.addWidget(button)
        
        # Don't set initial selection - let set_current() handle this
        # This prevents defaulting to first option when widget is recreated
    
    def on_button_clicked(self, index):
        """Handle button click"""
        if self.is_updating or not (0 <= index < len(self.options)):
            return
            
        # Only proceed if this is actually a different selection
        if index == self.current_index:
            return
            
        self.is_updating = True
        self.current_index = index
        
        # Update button states
        for i, button in enumerate(self.buttons):
            button.setChecked(i == index)
        
        # Call callback and emit signal
        selected_option = self.options[index]
        self.callback(selected_option)
        self.value_changed.emit(selected_option)
        
        self.is_updating = False
    
    def set_current(self, value: str):
        """Set the current value programmatically"""
        if value in self.options:
            index = self.options.index(value)
            if index != self.current_index:
                self.is_updating = True
                self.current_index = index
                
                # Update button states without triggering callback
                for i, button in enumerate(self.buttons):
                    button.setChecked(i == index)
                
                self.is_updating = False