# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Conventional Commits

We use Conventional Commits for all commit messages to keep history clear and tooling-friendly.

- Format: `<type>(<scope>): <short summary>`
- Common types: `feat`, `fix`, `refactor`, `docs`, `chore`, `test`, `perf`, `build`.
- Optional scope: narrow area like `settings`, `executor`, `ui`.
- Body: explain the what/why; wrap at ~72 chars.
- Breaking changes: add a footer `BREAKING CHANGE: <description>`.

Examples:
- `feat(settings): hard-code status refresh interval and remove UI control`
- `fix(executor): show actual timeout value in timeout error`
- `docs(agents): note we use Conventional Commits`

When a change removes or renames a user-facing option or API, include a `BREAKING CHANGE` footer describing the migration path.

## Project Overview

Desktop Utility GUI is a PyQt6-based Windows system tray application that manages and executes utility scripts with global hotkey support and time-based scheduling. The application runs primarily from the system tray and provides a modular MVC architecture for script execution and scheduling.

## Development Commands

### Running the Application
```bash
# Run from project root
python main.py

# Run minimized to tray
python main.py --minimized

# With virtual environment
venv\Scripts\activate
python main.py
```

### Installing Dependencies
```bash
pip install -r requirements.txt
```

Required packages:
- PyQt6>=6.4.0 (GUI framework)
- pywin32>=305 (Windows API integration for hotkeys)
- APScheduler>=3.10.0 (Time-based script scheduling)
- easyocr>=1.6.0 (OCR functionality)
- Pillow>=9.0.0 (Image processing)
- pyautogui>=0.9.50 (Screen automation)
- psutil>=5.9.0 (System monitoring)

## Architecture

### Core Components

1. **System Tray Interface** (`views/tray_view.py`): Primary UI, all user interaction happens through the tray icon menu
2. **Hotkey System** (`core/hotkey_manager.py`): Uses Windows RegisterHotKey API for global hotkeys, stores mappings in Windows Registry
3. **Scheduler System** (`core/scheduler_manager.py`): APScheduler-based time-based script execution with various schedule types
4. **Script Loader** (`core/script_loader.py`): Auto-discovers scripts from `scripts/` directory at runtime
5. **Script Analyzer** (`core/script_analyzer.py`): Uses AST parsing to determine execution strategy (subprocess, function call, or module exec)
6. **Script Executor** (`core/script_executor.py`): Executes scripts based on analyzer's strategy
7. **Settings Manager** (`core/settings.py`): Manages application settings and script configurations
8. **MVC Controllers** (`controllers/`): Application logic coordination for tray, scripts, and scheduling

### Script Architecture

The application supports two script types:

1. **Legacy UtilityScript**: Class-based scripts inheriting from a base class
2. **Standalone Scripts**: Regular Python scripts with argparse support (preferred)

Scripts communicate results via JSON output:
```python
{"success": true, "message": "Operation completed"}
```

### Execution Strategies

Based on AST analysis, scripts are executed using:
- **SUBPROCESS**: For scripts with `if __name__ == '__main__'` blocks
- **FUNCTION_CALL**: For scripts with main() functions
- **MODULE_EXEC**: For simple scripts without main blocks

## Key Development Guidelines

### Adding New Scripts

1. Place Python scripts in the `scripts/` directory
2. Use argparse for command-line arguments
3. Return JSON results for GUI integration
4. Scripts are auto-discovered on application start
5. Scripts can be scheduled for automatic execution using various schedule types

### Working with Schedules

1. **Adding Schedules**: Use `schedule_controller.py` to create new scheduled executions
2. **Schedule Types**: Support for interval, daily, weekly, monthly, cron, and one-time schedules
3. **Schedule Storage**: Schedules persist in application settings and survive restarts
4. **Schedule UI**: Configure schedules through the Settings dialog Schedules tab
5. **Visual Indicators**: Scheduled scripts show clock icons (⏰) in tray menu

### Modifying Core Components

- **Hotkey Changes**: Update both `hotkey_manager.py` (runtime) and `hotkey_registry.py` (persistence)
- **Schedule Changes**: Modify `scheduler_manager.py` for scheduling logic, `schedule_controller.py` for business logic
- **Script Discovery**: Modify `script_loader.py` for loading logic changes
- **UI Updates**: Primary interface is in `views/tray_view.py`, settings dialog in `views/settings_dialog.py`
- **MVC Updates**: Controllers coordinate between models and views, modify appropriate controller for business logic changes

### Windows-Specific Considerations

- Application uses Windows Registry for hotkey persistence
- Requires Windows API calls via pywin32
- System tray integration is Windows-specific
- Global hotkeys use RegisterHotKey/UnregisterHotKey Windows APIs

## Common Tasks

### Debug Script Loading Issues
Check `script_loader.py` logs - it shows which scripts are discovered and any loading errors.

### Test Hotkey Registration
Use the included `scripts/power_plan.py` or create a simple test script that outputs to a file when triggered.

### Modify Tray Menu Structure
Edit `controllers/tray_controller.py` - the `_build_menu_structure()` method builds the context menu data, including schedule indicators.

### Debug Scheduling Issues
Check `scheduler_manager.py` logs - it shows scheduler events, job executions, and any scheduling errors. The scheduler runs in a background thread.

## Important Files

### Entry Points and Core
- `main.py`: Entry point, handles single instance check
- `controllers/app_controller.py`: Main application coordination and MVC integration
- `core/scheduler_manager.py`: APScheduler integration for time-based execution
- `core/script_loader.py`: Script discovery and loading
- `core/hotkey_manager.py`: Global hotkey registration and handling
- `core/settings.py`: Application and script settings management

### MVC Architecture
- `controllers/`: Business logic coordinators (tray, script, schedule, app)
- `models/`: Data models and core functionality (script, schedule, system models)
- `views/`: UI components and dialogs (tray, settings, schedule configuration)

### Scripts and Assets
- `scripts/`: Directory for all utility scripts (auto-discovered)
- `gui/`: Legacy GUI components (being refactored to MVC pattern)
