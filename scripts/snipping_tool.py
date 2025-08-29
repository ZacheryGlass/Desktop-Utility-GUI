#!/usr/bin/env python3
"""
Screenshot Capture Tool

Captures screenshots with region selection, automatically saves to Pictures folder
and copies to clipboard. Replaces Windows Snipping Tool functionality.
"""

import json
import sys
import os
import io
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import messagebox

try:
    import pyautogui
    from PIL import Image, ImageGrab
    import win32clipboard
    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False

# Global tkinter root instance to avoid multiple Tk() creation issues
_global_root = None


def get_global_root():
    """
    Get or create the global tkinter root instance
    """
    global _global_root
    if _global_root is None or not tk._default_root:
        # Create new root if none exists
        _global_root = tk.Tk()
        _global_root.withdraw()  # Hide it immediately
        _global_root.attributes('-topmost', False)
    return _global_root


class RegionSelector:
    """
    Creates a transparent overlay window for region selection using Toplevel
    """
    def __init__(self, parent):
        self.parent = parent
        self.start_x = None
        self.start_y = None
        self.end_x = None
        self.end_y = None
        self.region = None
        self.cancelled = False
        self.selection_complete = False
        
        # Create Toplevel window instead of using root directly
        self.window = tk.Toplevel(parent)
        self.window.attributes('-fullscreen', True)
        self.window.attributes('-alpha', 0.3)
        self.window.configure(bg='gray')
        self.window.attributes('-topmost', True)
        
        # Prevent window from being closed by window manager
        self.window.protocol("WM_DELETE_WINDOW", self.cancel_selection)
        
        # Create canvas for drawing
        self.canvas = tk.Canvas(self.window, cursor='crosshair', bg='gray', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Bind mouse events
        self.canvas.bind('<Button-1>', self.start_selection)
        self.canvas.bind('<B1-Motion>', self.update_selection)
        self.canvas.bind('<ButtonRelease-1>', self.end_selection)
        self.canvas.bind('<Escape>', self.cancel_selection)
        self.window.bind('<Escape>', self.cancel_selection)
        
        # Focus on canvas to receive key events
        self.canvas.focus_set()
        
        # Instruction label
        instruction = tk.Label(self.window, text="Click and drag to select area to capture (Press ESC to cancel)", 
                             fg='white', bg='gray', font=('Arial', 12))
        instruction.pack(side=tk.TOP, pady=10)
        
    def start_selection(self, event):
        self.start_x = event.x_root
        self.start_y = event.y_root
        
    def update_selection(self, event):
        self.canvas.delete('selection')
        if self.start_x and self.start_y:
            self.canvas.create_rectangle(
                self.start_x - self.window.winfo_rootx(), 
                self.start_y - self.window.winfo_rooty(),
                event.x, event.y, 
                outline='red', width=2, tags='selection'
            )
    
    def end_selection(self, event):
        self.end_x = event.x_root
        self.end_y = event.y_root
        
        # Calculate region bounds
        x1 = min(self.start_x, self.end_x)
        y1 = min(self.start_y, self.end_y)
        x2 = max(self.start_x, self.end_x)
        y2 = max(self.start_y, self.end_y)
        
        # Only proceed if we have a valid region
        if abs(x2 - x1) > 10 and abs(y2 - y1) > 10:
            self.region = (x1, y1, x2, y2)
        
        self.selection_complete = True
        self.window.destroy()
    
    def cancel_selection(self, event=None):
        self.cancelled = True
        self.selection_complete = True
        self.window.destroy()
        
    def wait_for_selection(self):
        """Wait for user to complete selection without using mainloop"""
        self.window.focus_force()
        while not self.selection_complete:
            try:
                self.parent.update()
                import time
                time.sleep(0.01)  # Small delay to prevent 100% CPU usage
            except tk.TclError:
                # Window was destroyed
                break


def copy_image_to_clipboard(image):
    """
    Copy PIL Image to Windows clipboard
    """
    try:
        # Convert image to bitmap format
        output = io.BytesIO()
        image.save(output, format='BMP')
        data = output.getvalue()[14:]  # Remove BMP header
        
        # Copy to clipboard
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
        win32clipboard.CloseClipboard()
        return True
    except Exception as e:
        print(f"Clipboard copy failed: {e}")
        return False


def get_screenshots_folder():
    """
    Get or create the Screenshots folder in Pictures
    """
    pictures_path = Path.home() / "Pictures"
    screenshots_path = pictures_path / "Screenshots"
    
    # Create Screenshots folder if it doesn't exist
    screenshots_path.mkdir(parents=True, exist_ok=True)
    
    return screenshots_path


def generate_filename():
    """
    Generate timestamp-based filename for screenshot
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return f"Screenshot_{timestamp}.png"


def capture_region_screenshot():
    """
    Capture screenshot of selected region using GUI selection with persistent root
    """
    try:
        # Get the persistent global root
        root = get_global_root()
        
        # Create region selector using Toplevel window
        selector = RegionSelector(root)
        
        # Wait for selection completion without mainloop
        selector.wait_for_selection()
        
        # Check if cancelled
        if selector.cancelled or not selector.region:
            return None, "Screenshot cancelled"
        
        # Capture the selected region
        region = selector.region
        
        # Small delay to allow overlay to disappear
        import time
        time.sleep(0.1)
        
        # Capture screenshot of the selected region
        screenshot = ImageGrab.grab(bbox=region)
        
        return screenshot, "Screenshot captured successfully"
        
    except Exception as e:
        return None, f"Screenshot capture failed: {str(e)}"


def launch_snipping_tool_keyboard():
    """
    Fallback: Launch Windows Snipping Tool using keyboard shortcut (Win + Shift + S)
    """
    try:
        import subprocess
        
        # Use PowerShell to send Win+Shift+S keyboard shortcut
        ps_script = """
        Add-Type -AssemblyName System.Windows.Forms
        [System.Windows.Forms.SendKeys]::SendWait("#{+}s")
        """
        
        result = subprocess.run(
            ['powershell', '-WindowStyle', 'Hidden', '-Command', ps_script],
            capture_output=True,
            text=True,
            timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
        
        if result.returncode == 0:
            return True, "Windows Snipping Tool launched via keyboard shortcut"
        else:
            return False, f"Keyboard shortcut failed: {result.stderr}"
            
    except Exception as e:
        return False, f"Keyboard shortcut method failed: {str(e)}"


def main():
    """
    Main function that captures screenshot with region selection,
    saves to Pictures/Screenshots and copies to clipboard.
    """
    # Check if dependencies are available
    if not DEPENDENCIES_AVAILABLE:
        # Fallback to Windows Snipping Tool
        success, message = launch_snipping_tool_keyboard()
        result = {
            'success': success,
            'message': f"⚠️ Dependencies missing. {message}" if success else f"❌ Failed: {message}",
            'method': 'Keyboard Shortcut Fallback'
        }
        print(json.dumps(result))
        return 0 if success else 1
    
    try:
        # Capture screenshot with region selection
        screenshot, capture_message = capture_region_screenshot()
        
        if screenshot is None:
            result = {
                'success': False,
                'message': f"❌ {capture_message}",
                'method': 'Region Selection'
            }
            print(json.dumps(result))
            return 1
        
        # Save to Pictures/Screenshots folder
        screenshots_folder = get_screenshots_folder()
        filename = generate_filename()
        filepath = screenshots_folder / filename
        screenshot.save(filepath, 'PNG')
        
        # Copy to clipboard
        clipboard_success = copy_image_to_clipboard(screenshot)
        
        # Prepare result message
        messages = [f"📸 Screenshot saved: {filepath}"]
        if clipboard_success:
            messages.append("📋 Copied to clipboard")
        else:
            messages.append("⚠️ Failed to copy to clipboard")
        
        result = {
            'success': True,
            'message': " | ".join(messages),
            'method': 'Direct Capture',
            'filepath': str(filepath),
            'clipboard': clipboard_success
        }
        print(json.dumps(result))
        return 0
        
    except Exception as e:
        # If direct capture fails, fallback to Windows Snipping Tool
        success, message = launch_snipping_tool_keyboard()
        result = {
            'success': success,
            'message': f"⚠️ Direct capture failed ({str(e)}). {message}" if success else f"❌ All methods failed: {str(e)}",
            'method': 'Keyboard Shortcut Fallback'
        }
        print(json.dumps(result))
        return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())