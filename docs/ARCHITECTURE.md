# Desktop Utility GUI - Architecture Documentation

## Table of Contents
1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Core Components](#core-components)
4. [GUI Components](#gui-components)
5. [Script System](#script-system)
6. [Communication Flow](#communication-flow)
7. [Error Handling](#error-handling)
8. [Logging System](#logging-system)

## Overview

The Desktop Utility GUI is a modular PyQt6 application that automatically discovers and manages desktop utility scripts. It provides a dynamic, extensible interface where scripts can define their own UI controls and behaviors.

### Key Design Principles
- **Modularity**: Scripts are independent modules that can be added/removed without affecting the core system
- **Dynamic Discovery**: Scripts are automatically detected and loaded from the scripts directory
- **Error Isolation**: Individual script failures don't crash the application
- **Type Safety**: Strong typing through button types and options
- **Observable State**: Real-time status updates and logging

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Main Application                        │
│                        (main.py)                             │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────▼──────────────┐
        │      GUI Layer             │
        │   (PyQt6 Components)       │
        ├────────────────────────────┤
        │  • MainWindow              │
        │  • ScriptWidget            │
        │  • ButtonFactory           │
        │  • Styles                  │
        └─────────────┬──────────────┘
                      │
        ┌─────────────▼──────────────┐
        │      Core Layer            │
        │  (Business Logic)          │
        ├────────────────────────────┤
        │  • ScriptLoader            │
        │  • UtilityScript (Base)    │
        │  • ButtonTypes             │
        │  • Exceptions              │
        └─────────────┬──────────────┘
                      │
        ┌─────────────▼──────────────┐
        │     Scripts Layer          │
        │  (Utility Implementations) │
        ├────────────────────────────┤
        │  • DisplayToggle           │
        │  • VolumeControl           │
        │  • PowerPlan               │
        │  • [Custom Scripts...]      │
        └────────────────────────────┘
```

## Core Components

### 1. UtilityScript Base Class (`core/base_script.py`)

Abstract base class that all utility scripts must inherit from.

```python
class UtilityScript(ABC):
    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]
    # Returns: name, description, button_type, button_options
    
    @abstractmethod
    def get_status(self) -> Any
    # Returns current status without executing action
    
    @abstractmethod
    def execute(self, *args, **kwargs) -> Dict[str, Any]
    # Executes the script action
    # Returns: {'success': bool, 'message': str, 'new_status': Any}
    
    @abstractmethod
    def validate(self) -> bool
    # Checks if script can run on this system
```

### 2. ButtonTypes (`core/button_types.py`)

Defines all supported interaction types:

| ButtonType | Description | User Interaction |
|------------|-------------|------------------|
| `RUN` | One-time execution | Click button |
| `TOGGLE` | Boolean on/off state | Toggle between two states |
| `CYCLE` | Cycle through options | Click to advance to next option |
| `SELECT` | Dropdown selection | Choose from dropdown |
| `NUMBER` | Numeric input | Enter number in spinbox |
| `SLIDER` | Range selection | Drag slider |
| `TEXT_INPUT` | Text entry | Type text and submit |
| `CONFIRM` | Confirmation action | Click to execute with confirmation |

Each button type has corresponding options (e.g., `ToggleOptions`, `SliderOptions`) that configure its behavior.

### 3. ScriptLoader (`core/script_loader.py`)

Responsible for dynamic script discovery and management:

- **Discovery**: Scans scripts directory for Python files
- **Loading**: Imports modules and instantiates UtilityScript classes
- **Validation**: Ensures scripts pass validation before loading
- **Error Isolation**: Catches and logs individual script failures
- **Hot Reload**: Can reload scripts without restarting application

## GUI Components

### 1. MainWindow (`gui/main_window.py`)

The primary application window that:
- Manages the overall UI layout
- Coordinates script loading
- Handles refresh operations
- Manages the status bar
- Implements 5-second auto-refresh timer

### 2. ScriptWidget (`gui/script_widget.py`)

Individual widget for each script that:
- Displays script name and description
- Shows current status
- Creates appropriate control based on button type
- Handles script execution in separate thread
- Updates status display

### 3. ButtonFactory (`gui/button_factory.py`)

Factory pattern implementation that creates appropriate Qt widgets based on ButtonType:
- Maps ButtonType enum to Qt widget classes
- Configures widgets with provided options
- Connects callbacks for user interactions
- Prevents unwanted triggers during programmatic updates

### 4. ScriptExecutor (`gui/script_widget.py`)

QThread subclass that:
- Executes scripts in background thread
- Prevents UI freezing during long operations
- Emits signals for completion/error
- Enables cancellation (future enhancement)

## Script System

### Script Lifecycle

1. **Discovery Phase**
   ```
   ScriptLoader.discover_scripts()
   ├── Scan scripts/ directory
   ├── Filter *.py files
   └── Exclude __*.py files
   ```

2. **Loading Phase**
   ```
   ScriptLoader._load_script(path)
   ├── Import module
   ├── Find UtilityScript subclasses
   ├── Instantiate class
   └── Call validate()
   ```

3. **Widget Creation**
   ```
   ScriptWidget.__init__(script)
   ├── Get metadata
   ├── Create UI elements
   ├── Create button via ButtonFactory
   └── Initial status update
   ```

4. **Execution Phase**
   ```
   User Interaction
   ├── ScriptWidget.on_action_triggered()
   ├── Create ScriptExecutor thread
   ├── Execute script.execute()
   └── Handle result/error
   ```

### Script Implementation Example

```python
class CustomScript(UtilityScript):
    def get_metadata(self):
        return {
            'name': 'My Script',
            'description': 'Does something useful',
            'button_type': ButtonType.TOGGLE,
            'button_options': ToggleOptions(
                on_label="Enabled",
                off_label="Disabled"
            )
        }
    
    def get_status(self):
        # Return current state without side effects
        return self._check_current_state()
    
    def execute(self, enabled):
        # Perform the action
        if self._perform_action(enabled):
            return {
                'success': True,
                'message': f'State changed to {enabled}'
            }
        return {
            'success': False,
            'message': 'Failed to change state'
        }
    
    def validate(self):
        # Check system compatibility
        return sys.platform == 'win32'
```

## Communication Flow

### Status Update Flow
```
Every 5 seconds:
MainWindow.refresh_timer → refresh_status()
├── For each ScriptWidget:
│   ├── widget.update_status()
│   ├── script.get_status()
│   └── Update UI elements
```

### Action Execution Flow
```
User clicks button → ButtonWidget.callback()
├── ScriptWidget.on_action_triggered()
├── Validate script
├── Create ScriptExecutor thread
├── ScriptExecutor.run()
│   └── script.execute(*args)
├── Signal: finished(result) or error(msg)
└── Update UI with result
```

## Error Handling

### Three Levels of Error Isolation

1. **Script Loading Errors**
   - Caught by ScriptLoader
   - Script excluded from loaded list
   - Error logged to failed_scripts dict
   - Application continues with other scripts

2. **Script Execution Errors**
   - Caught by ScriptExecutor thread
   - Error signal emitted
   - Error displayed in UI
   - Widget re-enabled for retry

3. **Status Update Errors**
   - Caught in update_status()
   - Error displayed in status label
   - Next update attempted after 5 seconds

### Error Recovery Strategies

- **Graceful Degradation**: Show error in UI, don't crash
- **User Notification**: QMessageBox for critical errors
- **Logging**: All errors logged with context
- **Retry Logic**: User can retry failed operations
- **Hot Reload**: Refresh button to reload problematic scripts

## Logging System

### Logger Hierarchy
```
Root Logger
├── MAIN (Application lifecycle)
├── GUI.MainWindow (Window events)
├── GUI.ScriptWidget (Widget interactions)
├── GUI.ButtonFactory (Button creation)
└── Core.ScriptLoader (Script discovery)
```

### Log Levels and Usage

| Level | Usage | Example |
|-------|-------|---------|
| DEBUG | Detailed flow information | "Creating widget for script: Display Mode" |
| INFO | Important events | "Successfully loaded 3 script(s)" |
| WARNING | Non-critical issues | "Script not available on this system" |
| ERROR | Failures with recovery | "Error loading script: file.py" |

### Log Format
```
HH:MM:SS | LEVEL    | MODULE.Class         | Message
10:59:35 | INFO     | GUI.MainWindow       | Loading scripts...
```

## Performance Considerations

1. **Threading**: Script execution in separate threads prevents UI blocking
2. **Lazy Loading**: Scripts loaded on-demand during discovery
3. **Status Caching**: 5-second refresh interval balances responsiveness and performance
4. **Signal Debouncing**: Slider uses `is_updating` flag to prevent callback loops
5. **Process Flags**: `CREATE_NO_WINDOW` prevents console popup on Windows

## Security Considerations

1. **Script Validation**: Each script must pass validate() before loading
2. **Error Isolation**: Malicious/buggy scripts can't crash the application
3. **No Automatic Execution**: Scripts only run on user interaction
4. **Subprocess Safety**: Shell=False by default, CREATE_NO_WINDOW for stealth
5. **Type Safety**: Strong typing prevents type confusion attacks

## Future Enhancements

### Planned Features
- Script configuration persistence
- Script scheduling/automation
- Multi-script workflows
- Undo/redo functionality
- Script marketplace/sharing
- Remote script execution
- Script dependencies management

### Extension Points
- Custom button types via ButtonFactory
- Additional script metadata fields
- Plugin system for script loaders
- Theme customization
- Internationalization support