import sys
import os
from datetime import datetime
from pathlib import Path

sys.path.append('..')
from core.base_script import UtilityScript
from core.button_types import ButtonType


class TestHotkey(UtilityScript):
    
    def __init__(self):
        # Log file for tracking hotkey executions
        self.log_file = Path.home() / '.desktop_utility_gui' / 'hotkey_test.log'
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        super().__init__()
    
    def get_metadata(self):
        return {
            'name': 'Test Hotkey',
            'description': 'Test script for verifying hotkey functionality',
            'button_type': ButtonType.RUN
        }
    
    def get_status(self):
        """Show last execution time if available"""
        try:
            if self.log_file.exists():
                with open(self.log_file, 'r') as f:
                    lines = f.readlines()
                    if lines:
                        last_line = lines[-1].strip()
                        if 'Executed at' in last_line:
                            time_str = last_line.split('Executed at ')[-1]
                            return f"Last: {time_str}"
        except:
            pass
        return "Ready"
    
    def execute(self, *args, **kwargs):
        """Log the execution time and show a notification"""
        try:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Write to log file
            with open(self.log_file, 'a') as f:
                f.write(f"Executed at {current_time}\n")
            
            # Also create a visible indicator file on desktop
            desktop = Path.home() / 'Desktop'
            if desktop.exists():
                indicator_file = desktop / 'hotkey_test_executed.txt'
                with open(indicator_file, 'w') as f:
                    f.write(f"Hotkey test executed successfully at {current_time}\n")
                    f.write("You can delete this file.\n")
            
            return {
                'success': True,
                'message': f'Test hotkey executed at {current_time}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Test hotkey failed: {str(e)}'
            }
    
    def validate(self):
        """Always available for testing"""
        return True


if __name__ == "__main__":
    script = TestHotkey()
    print(f"Current status: {script.get_status()}")
    
    result = script.execute()
    print(f"Execution result: {result}")
    
    sys.exit(0 if result.get('success', False) else 1)