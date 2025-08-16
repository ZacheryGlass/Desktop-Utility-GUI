from enum import Enum
from dataclasses import dataclass
from typing import Any, List, Optional, Tuple

class ButtonType(Enum):
    RUN = "run"
    TOGGLE = "toggle"
    CYCLE = "cycle"
    SELECT = "select"
    NUMBER = "number"
    SLIDER = "slider"
    TEXT_INPUT = "text_input"
    CONFIRM = "confirm"

@dataclass
class ButtonOptions:
    pass

@dataclass
class ToggleOptions(ButtonOptions):
    on_label: str = "On"
    off_label: str = "Off"
    show_status: bool = True

@dataclass
class CycleOptions(ButtonOptions):
    options: List[str] = None
    show_current: bool = True
    
    def __post_init__(self):
        if self.options is None:
            self.options = []

@dataclass
class SelectOptions(ButtonOptions):
    options: List[str] = None
    placeholder: str = "Select..."
    
    def __post_init__(self):
        if self.options is None:
            self.options = []

@dataclass
class NumberOptions(ButtonOptions):
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    step: float = 1.0
    decimals: int = 0
    suffix: str = ""

@dataclass
class SliderOptions(ButtonOptions):
    min_value: float = 0
    max_value: float = 100
    step: float = 1
    show_value: bool = True
    suffix: str = ""

@dataclass
class TextInputOptions(ButtonOptions):
    placeholder: str = "Enter text..."
    max_length: Optional[int] = None
    multiline: bool = False

@dataclass
class RunOptions(ButtonOptions):
    button_text: str = "Run"
    confirm_before_run: bool = False
    confirm_message: str = "Are you sure you want to run this script?"