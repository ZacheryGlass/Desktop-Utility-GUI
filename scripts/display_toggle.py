import subprocess
from typing import Dict, Any
import sys
import os
from pathlib import Path

sys.path.append('..')
from core.base_script import UtilityScript
from core.button_types import ButtonType

class DisplayToggle(UtilityScript):
    
    def __init__(self):
        # Display modes with their DisplaySwitch.exe parameters
        self.display_modes = {
            'Extend': '/extend',
            'Duplicate': '/clone'
        }
        self.current_mode = 'Extend'
        
        # State file for tracking current display mode
        self.state_file = Path.home() / '.desktop_utility_gui' / 'display_mode_state.txt'
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize with saved state or default
        self._load_saved_state()
        
        # Call super().__init__() after setting attributes
        super().__init__()
    
    def _load_saved_state(self):
        """Load the saved display mode state from file."""
        try:
            # First check our own state file
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    saved_mode = f.read().strip()
                    # Handle both our format and the legacy format from toggle_display.py
                    if saved_mode.lower() == 'clone':
                        saved_mode = 'Duplicate'
                    elif saved_mode.lower() == 'extend':
                        saved_mode = 'Extend'
                        
                    if saved_mode in self.display_modes:
                        self.current_mode = saved_mode
                        return
            
            # Also check the legacy state file from toggle_display.py in current directory
            legacy_state = Path('display_mode_state.txt')
            if legacy_state.exists():
                with open(legacy_state, 'r') as f:
                    saved_mode = f.read().strip()
                    if saved_mode.lower() == 'clone':
                        saved_mode = 'Duplicate'
                    elif saved_mode.lower() == 'extend':
                        saved_mode = 'Extend'
                        
                    if saved_mode in self.display_modes:
                        self.current_mode = saved_mode
                        # Save to our location for future use
                        self._save_state(saved_mode)
                        return
                        
        except Exception:
            pass
        
        # Default to Extend if no saved state or error
        self.current_mode = 'Extend'
    
    def _save_state(self, mode: str):
        """Save the current display mode state to file."""
        try:
            with open(self.state_file, 'w') as f:
                f.write(mode)
        except Exception:
            pass
    
    def get_metadata(self) -> Dict[str, Any]:
        return {
            'name': 'Display Mode',
            'description': 'Toggle between Extend and Duplicate',
            'button_type': ButtonType.TOGGLE
        }
    
    def get_status(self) -> str:
        """Return the current display mode from saved state."""
        return self.current_mode
    
    def execute(self, *args, **kwargs) -> Dict[str, Any]:
        """Toggle between Extend and Duplicate modes."""
        try:
            # Toggle to the other mode
            new_mode = 'Duplicate' if self.current_mode == 'Extend' else 'Extend'
            
            # Build command
            display_switch_param = self.display_modes[new_mode]
            
            # Execute DisplaySwitch.exe with the appropriate parameter
            result = subprocess.run(
                ['DisplaySwitch.exe', display_switch_param],
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            
            if result.returncode == 0 or result.returncode is None:
                # DisplaySwitch.exe often returns None even on success
                # Update our saved state
                self.current_mode = new_mode
                self._save_state(new_mode)
                
                return {
                    'success': True,
                    'message': f'Display mode changed to: {new_mode}',
                    'new_status': new_mode
                }
            else:
                error_msg = result.stderr if result.stderr else "Unknown error"
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
                'message': f'Error executing display toggle: {str(e)}'
            }
    
    def validate(self) -> bool:
        """Check if DisplaySwitch.exe is available on this system."""
        if sys.platform != 'win32':
            return False
        
        try:
            # Check if DisplaySwitch.exe exists
            result = subprocess.run(
                ['where', 'DisplaySwitch.exe'],
                capture_output=True,
                timeout=2,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            
            if result.returncode == 0:
                # Also check if we have at least one monitor
                try:
                    # Use PowerShell to count monitors
                    ps_script = "@(Get-WmiObject -Namespace root\\wmi -ClassName WmiMonitorID -ErrorAction SilentlyContinue).Count"
                    result = subprocess.run(
                        ['powershell', '-Command', ps_script],
                        capture_output=True,
                        text=True,
                        timeout=5,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                    
                    if result.returncode == 0:
                        try:
                            monitor_count = int(result.stdout.strip())
                            # Script is valid if we have at least 1 monitor
                            return monitor_count >= 1
                        except:
                            pass
                except:
                    pass
                
                # If we can't count monitors, assume it's valid if DisplaySwitch exists
                return True
                
            return False
        except:
            return False


if __name__ == "__main__":
    import json
    
    script = DisplayToggle()
    
    current_status = script.get_status()
    print(f"Current display mode: {current_status}")
    
    print("Toggling display mode...")
    result = script.execute()
    
    print(json.dumps(result, indent=2))
    sys.exit(0 if result.get('success', False) else 1)