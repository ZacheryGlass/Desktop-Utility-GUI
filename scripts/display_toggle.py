import subprocess
from typing import Dict, Any
import sys
import os
from pathlib import Path

sys.path.append('..')
from core.base_script import UtilityScript
from core.button_types import ButtonType, CycleOptions

class DisplayToggle(UtilityScript):
    
    def __init__(self):
        # Display modes with their DisplaySwitch.exe parameters
        self.display_modes = {
            'Extend': '/extend',
            'Duplicate': '/clone', 
            'PC Only': '/internal',
            'Second Only': '/external'
        }
        self.mode_order = ['Extend', 'Duplicate', 'PC Only', 'Second Only']
        self.current_mode_index = 0
        
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
                        
                    if saved_mode in self.mode_order:
                        self.current_mode_index = self.mode_order.index(saved_mode)
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
                        
                    if saved_mode in self.mode_order:
                        self.current_mode_index = self.mode_order.index(saved_mode)
                        # Save to our location for future use
                        self._save_state(saved_mode)
                        return
                        
        except Exception:
            pass
        
        # Default to Extend if no saved state or error
        self.current_mode_index = 0
    
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
            'description': 'Switch between display modes',
            'button_type': ButtonType.CYCLE,
            'button_options': CycleOptions(
                options=self.mode_order,
                show_current=True
            )
        }
    
    def get_status(self) -> str:
        """Return the current display mode from saved state."""
        # Simply return the saved state - no detection needed!
        return self.mode_order[self.current_mode_index]
    
    def execute(self, mode_name: str) -> Dict[str, Any]:
        """Execute display mode change."""
        try:
            if mode_name not in self.display_modes:
                return {
                    'success': False,
                    'message': f'Invalid display mode: {mode_name}'
                }
            
            # Build command
            display_switch_param = self.display_modes[mode_name]
            
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
                if mode_name in self.mode_order:
                    self.current_mode_index = self.mode_order.index(mode_name)
                    self._save_state(mode_name)
                
                return {
                    'success': True,
                    'message': f'Display mode changed to: {mode_name}',
                    'new_status': mode_name
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