# API Reference

## Core Module

### UtilityScript

Base class for all utility scripts.

```python
from core.base_script import UtilityScript
```

#### Methods

##### `get_metadata() -> Dict[str, Any]`
Returns script metadata for UI generation.

**Returns:**
- `name` (str): Display name of the script
- `description` (str): Brief description
- `button_type` (ButtonType): Type of UI control
- `button_options` (ButtonOptions, optional): Configuration for the button

**Example:**
```python
def get_metadata(self):
    return {
        'name': 'Network Toggle',
        'description': 'Enable/disable network adapter',
        'button_type': ButtonType.TOGGLE,
        'button_options': ToggleOptions(
            on_label="Connected",
            off_label="Disconnected"
        )
    }
```

##### `get_status() -> Any`
Returns current status without side effects.

**Returns:**
- Status value appropriate for the button type
  - Toggle: `bool`
  - Cycle: `str` (current option)
  - Slider: `float/int`
  - Select: `str` (selected option)

**Example:**
```python
def get_status(self):
    return self.is_network_enabled()
```

##### `execute(*args, **kwargs) -> Dict[str, Any]`
Executes the script action.

**Parameters:**
- `*args`: Positional arguments from UI control
- `**kwargs`: Keyword arguments from UI control

**Returns:**
- `success` (bool): Whether execution succeeded
- `message` (str, optional): User-friendly message
- `new_status` (Any, optional): Updated status value

**Example:**
```python
def execute(self, enabled):
    if self.set_network_state(enabled):
        return {
            'success': True,
            'message': f'Network {"enabled" if enabled else "disabled"}'
        }
    return {'success': False, 'message': 'Failed to change network state'}
```

##### `validate() -> bool`
Checks if script can run on current system.

**Returns:**
- `True` if script is compatible with system
- `False` otherwise

**Example:**
```python
def validate(self):
    return sys.platform == 'win32' and self.has_admin_rights()
```

### ButtonType

Enumeration of available button types.

```python
from core.button_types import ButtonType
```

| Value | Description |
|-------|-------------|
| `ButtonType.RUN` | Simple execution button |
| `ButtonType.TOGGLE` | Two-state toggle |
| `ButtonType.CYCLE` | Cycle through multiple options |
| `ButtonType.SELECT` | Dropdown selection |
| `ButtonType.NUMBER` | Numeric input |
| `ButtonType.SLIDER` | Range slider |
| `ButtonType.TEXT_INPUT` | Text input field |
| `ButtonType.CONFIRM` | Confirmation button |

### Button Options

Configuration classes for each button type.

#### ToggleOptions
```python
from core.button_types import ToggleOptions

options = ToggleOptions(
    on_label="On",        # Label when toggled on
    off_label="Off",      # Label when toggled off
    show_status=True      # Show status in button
)
```

#### CycleOptions
```python
from core.button_types import CycleOptions

options = CycleOptions(
    options=["Low", "Medium", "High"],  # List of options to cycle
    show_current=True                   # Show current option
)
```

#### SelectOptions
```python
from core.button_types import SelectOptions

options = SelectOptions(
    options=["Option1", "Option2"],  # Dropdown options
    placeholder="Select..."          # Placeholder text
)
```

#### NumberOptions
```python
from core.button_types import NumberOptions

options = NumberOptions(
    min_value=0,      # Minimum value (optional)
    max_value=100,    # Maximum value (optional)
    step=1.0,         # Step increment
    decimals=0,       # Decimal places
    suffix="%"        # Display suffix
)
```

#### SliderOptions
```python
from core.button_types import SliderOptions

options = SliderOptions(
    min_value=0,      # Minimum value
    max_value=100,    # Maximum value
    step=1,           # Step increment
    show_value=True,  # Show current value
    suffix="%"        # Display suffix
)
```

#### TextInputOptions
```python
from core.button_types import TextInputOptions

options = TextInputOptions(
    placeholder="Enter text...",  # Placeholder text
    max_length=100,               # Maximum length (optional)
    multiline=False               # Enable multiline
)
```

#### RunOptions
```python
from core.button_types import RunOptions

options = RunOptions(
    button_text="Execute",           # Button label
    confirm_before_run=False,        # Require confirmation
    confirm_message="Are you sure?"  # Confirmation message
)
```

### ScriptLoader

Handles dynamic script discovery and loading.

```python
from core.script_loader import ScriptLoader

loader = ScriptLoader(scripts_directory="scripts")
```

#### Methods

##### `discover_scripts() -> List[UtilityScript]`
Discovers and loads all valid scripts.

**Returns:**
- List of loaded UtilityScript instances

##### `reload_scripts() -> List[UtilityScript]`
Clears cache and reloads all scripts.

**Returns:**
- List of reloaded UtilityScript instances

##### `get_script(name: str) -> Optional[UtilityScript]`
Gets a loaded script by name.

**Parameters:**
- `name`: Script filename without extension

**Returns:**
- UtilityScript instance or None

##### `get_failed_scripts() -> Dict[str, str]`
Gets scripts that failed to load.

**Returns:**
- Dictionary mapping filename to error message

### Exceptions

Custom exceptions for error handling.

```python
from core.exceptions import (
    ScriptError,           # Base exception
    ScriptLoadError,       # Loading failed
    ScriptExecutionError,  # Execution failed
    ScriptValidationError, # Validation failed
    ScriptTimeoutError     # Operation timed out
)
```

## GUI Module

### MainWindow

Main application window.

```python
from gui.main_window import MainWindow

window = MainWindow(scripts_directory="scripts")
```

#### Signals
- `scripts_reloaded`: Emitted when scripts are reloaded

#### Methods

##### `load_scripts()`
Loads all scripts and creates widgets.

##### `reload_scripts()`
Reloads all scripts from disk.

##### `refresh_status()`
Updates status for all script widgets.

### ScriptWidget

Widget for individual script display and control.

```python
from gui.script_widget import ScriptWidget

widget = ScriptWidget(script_instance)
```

#### Signals
- `script_executed(str, dict)`: Emitted after execution with name and result

#### Methods

##### `update_status()`
Updates the status display.

##### `on_action_triggered(*args, **kwargs)`
Handles user interaction with the control.

### ButtonFactory

Factory for creating UI controls.

```python
from gui.button_factory import ButtonFactory

factory = ButtonFactory()
widget = factory.create_button(
    button_type=ButtonType.TOGGLE,
    options=ToggleOptions(),
    callback=my_callback
)
```

#### Methods

##### `create_button(button_type, options, callback) -> QWidget`
Creates appropriate Qt widget for button type.

**Parameters:**
- `button_type`: ButtonType enum value
- `options`: Corresponding options object
- `callback`: Function to call on interaction

**Returns:**
- Configured Qt widget

## Complete Script Example

```python
import sys
import subprocess
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.append('..')

from core.base_script import UtilityScript
from core.button_types import ButtonType, SliderOptions

class BrightnessControl(UtilityScript):
    """Adjust screen brightness on Windows."""
    
    def get_metadata(self) -> Dict[str, Any]:
        return {
            'name': 'Screen Brightness',
            'description': 'Adjust display brightness',
            'button_type': ButtonType.SLIDER,
            'button_options': SliderOptions(
                min_value=20,
                max_value=100,
                step=5,
                show_value=True,
                suffix="%"
            )
        }
    
    def get_status(self) -> int:
        """Get current brightness level."""
        try:
            # PowerShell command to get brightness
            cmd = '(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightness).CurrentBrightness'
            result = subprocess.run(
                ['powershell', '-Command', cmd],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            if result.returncode == 0:
                return int(result.stdout.strip())
        except Exception:
            pass
        return 50  # Default
    
    def execute(self, brightness: float) -> Dict[str, Any]:
        """Set brightness level."""
        try:
            brightness = int(brightness)
            
            # PowerShell command to set brightness
            cmd = f'(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,{brightness})'
            result = subprocess.run(
                ['powershell', '-Command', cmd],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'message': f'Brightness set to {brightness}%'
                }
        except Exception as e:
            return {
                'success': False,
                'message': f'Failed to set brightness: {str(e)}'
            }
    
    def validate(self) -> bool:
        """Check if brightness control is available."""
        if sys.platform != 'win32':
            return False
        
        try:
            # Check if WMI brightness control is available
            cmd = 'Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightness'
            result = subprocess.run(
                ['powershell', '-Command', cmd],
                capture_output=True,
                timeout=2,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return result.returncode == 0
        except Exception:
            return False
```

## Logging

Access loggers for debugging:

```python
import logging

# Get specific logger
logger = logging.getLogger('GUI.MainWindow')
logger.info("Custom log message")

# Available loggers:
# - 'MAIN'
# - 'GUI.MainWindow'
# - 'GUI.ScriptWidget'
# - 'GUI.ButtonFactory'
# - 'Core.ScriptLoader'
```