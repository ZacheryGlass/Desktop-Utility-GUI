import sys
import os
from datetime import datetime
import tkinter as tk
from tkinter import messagebox

sys.path.append('..')
from core.base_script import UtilityScript
from core.button_types import ButtonType


class HotkeyTestPopup(UtilityScript):
    
    def __init__(self):
        self.execution_count = 0
        super().__init__()
    
    def get_metadata(self):
        return {
            'name': 'Hotkey Test Popup',
            'description': 'Shows a popup window to test hotkey functionality',
            'button_type': ButtonType.RUN
        }
    
    def get_status(self):
        """Show execution count"""
        if self.execution_count == 0:
            return "Ready"
        else:
            return f"Executed {self.execution_count} times"
    
    def execute(self, *args, **kwargs):
        """Show a popup window with current time"""
        try:
            self.execution_count += 1
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Create a temporary tkinter window for the popup
            root = tk.Tk()
            root.withdraw()  # Hide the main window
            
            # Show the popup message
            messagebox.showinfo(
                "Hotkey Test Success!", 
                f"🎉 Hotkey triggered successfully!\n\n"
                f"Time: {current_time}\n"
                f"Execution count: {self.execution_count}\n\n"
                f"This popup confirms your hotkey is working correctly."
            )
            
            root.destroy()  # Clean up the tkinter window
            
            return {
                'success': True,
                'message': f'Hotkey test popup shown at {current_time} (execution #{self.execution_count})'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Hotkey test popup failed: {str(e)}'
            }
    
    def validate(self):
        """Always available for testing"""
        return True


if __name__ == "__main__":
    script = HotkeyTestPopup()
    print(f"Current status: {script.get_status()}")
    
    result = script.execute()
    print(f"Execution result: {result}")
    
    sys.exit(0 if result.get('success', False) else 1)