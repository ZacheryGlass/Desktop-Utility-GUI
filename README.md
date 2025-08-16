# Desktop Utility GUI

A modular PyQt application that automatically detects and manages desktop utility scripts with a clean, intuitive interface.

## Features

- **Auto-detection**: Automatically discovers scripts in the `scripts` directory
- **Dynamic UI**: Generates appropriate UI controls based on script type
- **Multiple Button Types**: Run, Toggle, Cycle, Slider, Select, Number, Text Input
- **Error Isolation**: Bad scripts won't crash the GUI
- **Status Updates**: Real-time status display for each script
- **Hot Reload**: Refresh button to reload scripts without restarting

## Installation

1. Install Python 3.8 or higher
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the application:
```bash
python main.py
```

## Creating Custom Scripts

Create a Python file in the `scripts` directory that inherits from `UtilityScript`:

```python
from core.base_script import UtilityScript
from core.button_types import ButtonType

class MyScript(UtilityScript):
    def get_metadata(self):
        return {
            'name': 'My Script',
            'description': 'Description here',
            'button_type': ButtonType.RUN
        }
    
    def get_status(self):
        return "Ready"
    
    def execute(self, *args, **kwargs):
        # Your script logic here
        return {'success': True, 'message': 'Done!'}
    
    def validate(self):
        return True  # Check if script can run on this system
```

## Included Scripts

- **Display Toggle**: Switch between Duplicate and Extend display modes
- **Volume Control**: Adjust system volume with a slider
- **Power Plan**: Cycle through Windows power plans

## Architecture

- `core/`: Core infrastructure (base classes, types, exceptions)
- `gui/`: PyQt GUI components
- `scripts/`: Utility scripts directory
- `main.py`: Application entry point
