import json
from datetime import datetime
import tkinter as tk
from tkinter import messagebox


def main():
    """Show a popup window with current time"""
    try:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Create a temporary tkinter window for the popup
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        
        # Show the popup message
        messagebox.showinfo(
            "Hotkey Test Success!", 
            f"🎉 Hotkey triggered successfully!\n\n"
            f"Time: {current_time}\n\n"
            f"This popup confirms your hotkey is working correctly."
        )
        
        root.destroy()  # Clean up the tkinter window
        
        result = {
            'success': True,
            'message': f'Hotkey test popup shown at {current_time}'
        }
        
        print(json.dumps(result))
        return True
        
    except Exception as e:
        result = {
            'success': False,
            'message': f'Hotkey test popup failed: {str(e)}'
        }
        print(json.dumps(result))
        return False


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)