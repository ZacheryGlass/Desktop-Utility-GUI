import subprocess
import re
from typing import Dict, Any
import sys

sys.path.append('..')
from core.base_script import UtilityScript
from core.button_types import ButtonType, ToggleOptions

class DisplayToggle(UtilityScript):
    
    def __init__(self):
        super().__init__()
        self.display_modes = {
            'extend': '/extend',
            'duplicate': '/clone',
            'internal': '/internal',
            'external': '/external'
        }
    
    def get_metadata(self) -> Dict[str, Any]:
        return {
            'name': 'Display Mode',
            'description': 'Toggle between Duplicate and Extend display modes',
            'button_type': ButtonType.TOGGLE,
            'button_options': ToggleOptions(
                on_label="Extended",
                off_label="Duplicate",
                show_status=True
            )
        }
    
    def get_status(self) -> bool:
        try:
            result = subprocess.run(
                ['wmic', 'path', 'Win32_DesktopMonitor', 'get', 'DeviceID'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            monitor_count = len([line for line in result.stdout.split('\n') 
                               if line.strip() and 'DeviceID' not in line])
            
            if monitor_count < 2:
                return None
            
            try:
                result = subprocess.run(
                    ['powershell', '-Command', 
                     '(Get-DisplayResolution).Count -gt 1'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                return 'true' in result.stdout.lower()
            except:
                return True
                
        except Exception as e:
            print(f"Error getting display status: {e}")
            return None
    
    def execute(self, is_extended: bool = None) -> Dict[str, Any]:
        try:
            current_status = self.get_status()
            
            if is_extended is None:
                target_mode = 'extend' if not current_status else 'duplicate'
            else:
                target_mode = 'extend' if is_extended else 'duplicate'
            
            cmd = f'DisplaySwitch.exe {self.display_modes[target_mode]}'
            
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                new_mode = "Extended" if target_mode == 'extend' else "Duplicate"
                return {
                    'success': True,
                    'message': f'Display mode changed to: {new_mode}',
                    'new_status': target_mode == 'extend'
                }
            else:
                return {
                    'success': False,
                    'message': f'Failed to change display mode. Error: {result.stderr}'
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
        if sys.platform != 'win32':
            return False
        
        try:
            result = subprocess.run(
                ['where', 'DisplaySwitch.exe'],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False