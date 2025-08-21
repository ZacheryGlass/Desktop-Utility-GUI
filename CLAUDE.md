# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Commands

### Setup and Environment
- **Initial setup**: `setup.bat` (Windows) or `./setup.sh` (Linux/Mac)
- **Run application**: `run.bat` (Windows) or `./run.sh` (Linux/Mac)
- **Manual run**: Activate venv with `venv\Scripts\activate.bat` then `python main.py`
- **Install dependencies**: `pip install -r requirements.txt` (after activating venv)

### Development Commands
- **Run application**: `python main.py` (from activated virtual environment)
- **Run minimized to tray**: `python main.py --minimized`
- **Test script loading**: Scripts are auto-discovered from the `scripts/` directory

## Architecture Overview

This is a modular PyQt6 desktop application that dynamically loads and manages utility scripts with automatic UI generation.

### Core Components

**Core Infrastructure** (`core/`):
- `base_script.py`: Abstract base class `UtilityScript` that all utility scripts must inherit from
- `button_types.py`: Defines UI control types (RUN, TOGGLE, CYCLE, SLIDER, etc.) and their configuration options
- `script_loader.py`: Dynamically discovers and loads scripts from the `scripts/` directory
- `exceptions.py`: Custom exception hierarchy for script errors
- `settings.py`: Settings management using QSettings with persistent configuration
- `startup_manager.py`: Windows startup registration management

**GUI Layer** (`gui/`):
- `main_window.py`: Primary application window with script discovery and refresh functionality
- `script_widget.py`: Individual widget containers for each loaded script (legacy, now tray-only)
- `button_factory.py`: Creates appropriate UI controls based on script button types (legacy)
- `tray_manager.py`: System tray interface that manages script execution
- `theme_manager.py`: Theme and styling management
- `settings_dialog.py`: Configuration interface for application settings

**Script System** (`scripts/`):
- Auto-discovered Python files that inherit from `UtilityScript`
- Each script defines metadata (name, description, button type) and implements execute/status methods
- Supports multiple interaction types: run buttons, toggles, cycles, sliders, number inputs, etc.

### Key Patterns

**Script Contract**: All scripts must:
1. Inherit from `UtilityScript`
2. Implement `get_metadata()` returning name, description, and button_type
3. Implement `execute()` for script logic
4. Implement `get_status()` for current state display
5. Implement `validate()` for system compatibility checking

**Error Isolation**: Bad scripts don't crash the GUI - they're caught and reported individually

**Dynamic UI**: The GUI automatically generates appropriate controls based on each script's declared button type and options

**Hot Reload**: The application includes a refresh mechanism to reload scripts without restarting

**System Tray Architecture**: The application runs primarily as a system tray application with context menus for script interaction, supporting single-instance operation and minimized startup

## Dependencies

- PyQt6 >= 6.4.0 (GUI framework)
- pywin32 >= 305 (Windows-specific functionality)
- Python 3.8+ required

## Development Notes

- Virtual environment is automatically created by setup scripts
- Scripts directory is monitored for new .py files
- Application uses logging for debugging (logs to stdout)
- Cross-platform support with separate Windows (.bat) and Unix (.sh) scripts
- No formal testing framework configured - testing relies on manual script execution
- Settings are persisted using QSettings (Windows registry/cross-platform)
- Single instance enforcement prevents multiple app instances
- Main documentation files: `ARCHITECTURE.md` (detailed design), `docs/API_REFERENCE.md`, `docs/SCRIPT_TUTORIAL.md`

## Application Modes

**Current Architecture**: The application primarily runs as a system tray application:
- Main window exists but is hidden by default for settings dialog parent
- All script interaction occurs through system tray context menus  
- Scripts are dynamically loaded and presented as menu items
- Supports TOGGLE, CYCLE, RUN, and other button types through tray menus
- 5-second timer updates script status in background