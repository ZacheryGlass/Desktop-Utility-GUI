import subprocess
import json
import sys
import os
from pathlib import Path


def get_display_modes():
    """Return available display modes."""
    return {
        'Extend': '/extend',
        'Duplicate': '/clone'
    }


def get_state_file():
    """Get the path to the state file."""
    state_file = Path.home() / '.desktop_utility_gui' / 'display_mode_state.txt'
    state_file.parent.mkdir(parents=True, exist_ok=True)
    return state_file


def load_saved_state():
    """Load the saved display mode state from file."""
    state_file = get_state_file()
    display_modes = get_display_modes()
    
    try:
        # First check our own state file
        if state_file.exists():
            with open(state_file, 'r') as f:
                saved_mode = f.read().strip()
                # Handle both our format and the legacy format from toggle_display.py
                if saved_mode.lower() == 'clone':
                    saved_mode = 'Duplicate'
                elif saved_mode.lower() == 'extend':
                    saved_mode = 'Extend'
                    
                if saved_mode in display_modes:
                    return saved_mode
        
        # Also check the legacy state file from toggle_display.py in current directory
        legacy_state = Path('display_mode_state.txt')
        if legacy_state.exists():
            with open(legacy_state, 'r') as f:
                saved_mode = f.read().strip()
                # Handle the legacy format from toggle_display.py
                if saved_mode.lower() == 'clone':
                    saved_mode = 'Duplicate'
                elif saved_mode.lower() == 'extend':
                    saved_mode = 'Extend'
                    
                if saved_mode in display_modes:
                    return saved_mode
    
    except Exception:
        pass
    
    return 'Extend'  # Default mode


def save_current_state(mode):
    """Save the current display mode to state file."""
    try:
        state_file = get_state_file()
        with open(state_file, 'w') as f:
            f.write(mode)
    except Exception:
        pass


def get_current_mode():
    """Get the current display mode."""
    return load_saved_state()


def toggle_display(target_mode=None):
    """Toggle the display mode or set to specific mode."""
    display_modes = get_display_modes()
    current_mode = get_current_mode()
    
    if target_mode:
        new_mode = target_mode
    else:
        # Toggle between modes
        modes_list = list(display_modes.keys())
        current_index = modes_list.index(current_mode) if current_mode in modes_list else 0
        next_index = (current_index + 1) % len(modes_list)
        new_mode = modes_list[next_index]
    
    if sys.platform != 'win32':
        return {
            'success': False,
            'message': 'Display toggle only supported on Windows'
        }
    
    try:
        switch_param = display_modes[new_mode]
        
        # Try to find DisplaySwitch.exe
        displayswitch_path = None
        possible_paths = [
            'DisplaySwitch.exe',  # Try system PATH first
            r'C:\Windows\System32\DisplaySwitch.exe',
            r'C:\Windows\DisplaySwitch.exe'
        ]
        
        for path in possible_paths:
            try:
                result = subprocess.run(
                    [path, '/?'],
                    capture_output=True,
                    timeout=2,
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
                )
                # DisplaySwitch.exe exists if command succeeded (returncode 0)
                displayswitch_path = path
                break
            except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
                continue
        
        if not displayswitch_path:
            return {
                'success': False,
                'message': 'DisplaySwitch.exe not found on system'
            }
        
        # Execute the display switch command
        result = subprocess.run(
            [displayswitch_path, switch_param],
            capture_output=True,
            text=True,
            timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
        
        if result.returncode == 0:
            save_current_state(new_mode)
            return {
                'success': True,
                'message': f'Display mode changed to: {new_mode}',
                'new_status': new_mode
            }
        else:
            error_msg = result.stderr if result.stderr else 'Unknown error'
            return {
                'success': False,
                'message': f'Failed to change display mode: {error_msg}'
            }
            
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'message': 'Display switch operation timed out'
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'Error changing display mode: {str(e)}'
        }


def main():
    # Simple toggle - no arguments needed
    result = toggle_display()
    print(json.dumps(result))
    return result.get('success', False)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)