#!/usr/bin/env python3
"""
OCR Screen Capture Tool

Captures screenshots with region selection and extracts text using local OCR engines.
The extracted text is automatically copied to the clipboard for easy pasting.

Supported OCR Engines:
- EasyOCR (primary choice, deep learning based)
- Tesseract (fallback option, traditional OCR)

Usage:
1. Run the script (via GUI or command line)
2. Select screen area by clicking and dragging
3. Text is automatically extracted and copied to clipboard
4. Press Ctrl+V to paste the extracted text anywhere

Dependencies:
- easyocr OR pytesseract (for OCR processing)
- PIL/Pillow (for image processing) 
- pyautogui (for screen capture)
- win32clipboard (for clipboard operations)

Install dependencies: pip install easyocr pillow pyautogui pywin32
"""

import json
import sys
import os
import io
import time
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, scrolledtext
from typing import Dict, Any, List, Tuple, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from PIL import Image

# OCR Library import - using EasyOCR as primary choice
try:
    import easyocr
    OCR_AVAILABLE = True
    OCR_ENGINE = 'easyocr'
except ImportError:
    try:
        import pytesseract
        OCR_AVAILABLE = True
        OCR_ENGINE = 'tesseract'
    except ImportError:
        OCR_AVAILABLE = False
        OCR_ENGINE = None

# Required dependencies for screen capture
try:
    import pyautogui
    from PIL import Image, ImageGrab, ImageEnhance, ImageFilter
    import win32clipboard
    SCREEN_CAPTURE_AVAILABLE = True
except ImportError:
    SCREEN_CAPTURE_AVAILABLE = False

# Global tkinter root instance
_global_root = None


def get_global_root():
    """Get or create the global tkinter root instance"""
    global _global_root
    if _global_root is None or not tk._default_root:
        # Create root window in withdrawn state to prevent visible flash
        _global_root = tk.Tk()
        _global_root.withdraw()  # Hide immediately after creation
        _global_root.overrideredirect(True)  # Remove window decorations temporarily
        _global_root.attributes('-alpha', 0.0)  # Make completely transparent during setup
        _global_root.attributes('-topmost', False)
        # Reset properties after hiding
        _global_root.overrideredirect(False)
        _global_root.attributes('-alpha', 1.0)
    return _global_root


class RegionSelector:
    """Creates a transparent overlay window for region selection"""
    def __init__(self, parent):
        self.parent = parent
        self.start_x = None
        self.start_y = None
        self.end_x = None
        self.end_y = None
        self.region = None
        self.cancelled = False
        self.selection_complete = False
        
        # Create Toplevel window
        self.window = tk.Toplevel(parent)
        self.window.attributes('-fullscreen', True)
        self.window.attributes('-alpha', 0.3)
        self.window.configure(bg='gray')
        self.window.attributes('-topmost', True)
        
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
        
        self.canvas.focus_set()
        
        # Instruction label
        instruction = tk.Label(self.window, text="Click and drag to select area for OCR (Press ESC to cancel)", 
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
        """Wait for user to complete selection"""
        self.window.focus_force()
        while not self.selection_complete:
            try:
                self.parent.update()
                time.sleep(0.01)
            except tk.TclError:
                break


def copy_text_to_clipboard(text: str) -> bool:
    """Copy text to clipboard"""
    try:
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardText(text)
        win32clipboard.CloseClipboard()
        return True
    except Exception as e:
        print(f"Clipboard copy failed: {e}")
        return False


def preprocess_image(image):
    """Preprocess image for better OCR accuracy"""
    # Convert to grayscale if needed
    if image.mode != 'L':
        image = image.convert('L')
    
    # Enhance contrast
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2.0)
    
    # Apply slight gaussian blur to reduce noise
    image = image.filter(ImageFilter.GaussianBlur(radius=0.5))
    
    return image


def extract_text_with_ocr(image) -> Tuple[str, float]:
    """Extract text using the available OCR engine"""
    # Preprocess image
    processed_image = preprocess_image(image)
    
    try:
        if OCR_ENGINE == 'easyocr':
            # Initialize EasyOCR reader
            reader = easyocr.Reader(['en'])
            
            # Convert PIL image to numpy array
            import numpy as np
            img_array = np.array(processed_image)
            
            results = reader.readtext(img_array)
            
            if not results:
                return "", 0.0
            
            # Extract text and calculate average confidence
            texts = []
            confidences = []
            
            for (bbox, text, confidence) in results:
                if confidence > 0.3:  # Filter low confidence results
                    texts.append(text)
                    confidences.append(confidence)
            
            full_text = ' '.join(texts)
            avg_confidence = sum(confidences) / len(confidences) * 100 if confidences else 0
            
            return full_text, avg_confidence
            
        elif OCR_ENGINE == 'tesseract':
            # Get text with confidence data
            data = pytesseract.image_to_data(processed_image, output_type=pytesseract.Output.DICT)
            
            # Filter text by confidence
            texts = []
            confidences = []
            
            for i in range(len(data['text'])):
                if int(data['conf'][i]) > 30:  # Filter low confidence
                    text = data['text'][i].strip()
                    if text:
                        texts.append(text)
                        confidences.append(int(data['conf'][i]))
            
            full_text = ' '.join(texts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            return full_text, avg_confidence
            
    except Exception as e:
        print(f"OCR error: {e}")
        return "", 0.0
    
    return "", 0.0


def capture_and_extract_text():
    """Main function to capture screen region and extract text"""
    try:
        # Get the persistent global root
        root = get_global_root()
        
        # Create region selector
        selector = RegionSelector(root)
        
        # Wait for selection completion
        selector.wait_for_selection()
        
        # Check if cancelled
        if selector.cancelled or not selector.region:
            return None, "OCR capture cancelled"
        
        # Capture the selected region
        region = selector.region
        
        # Small delay to allow overlay to disappear
        time.sleep(0.1)
        
        # Capture screenshot of the selected region
        screenshot = ImageGrab.grab(bbox=region)
        
        # Extract text from screenshot
        text, confidence = extract_text_with_ocr(screenshot)
        
        if text.strip():
            # Copy text to clipboard
            clipboard_success = copy_text_to_clipboard(text)
            
            if clipboard_success:
                return {
                    'success': True,
                    'text': text,
                    'confidence': confidence,
                    'clipboard': True
                }, "Text extracted and copied to clipboard"
            else:
                return {
                    'success': True,
                    'text': text,
                    'confidence': confidence,
                    'clipboard': False
                }, "Text extracted but clipboard copy failed"
        else:
            return None, "No text detected in the selected region"
        
    except Exception as e:
        return None, f"OCR capture failed: {str(e)}"


def validate_system() -> bool:
    """Check if OCR is available on this system"""
    if not SCREEN_CAPTURE_AVAILABLE:
        return False
    return OCR_AVAILABLE


def main():
    """Main execution function"""
    # Check system compatibility
    if not SCREEN_CAPTURE_AVAILABLE:
        result = {
            'success': False,
            'message': 'Screen capture dependencies missing (PIL, pyautogui, win32clipboard)'
        }
        print(json.dumps(result))
        return 1
    
    if not OCR_AVAILABLE:
        result = {
            'success': False,
            'message': 'No OCR engine available. Install: pip install easyocr OR pip install pytesseract'
        }
        print(json.dumps(result))
        return 1
    
    print(f"Using OCR engine: {OCR_ENGINE}")
    print("Starting OCR screen capture...")
    
    # Capture and extract text
    ocr_result, message = capture_and_extract_text()
    
    if ocr_result:
        result = {
            'success': True,
            'message': message,
            'text': ocr_result['text'][:100] + ('...' if len(ocr_result['text']) > 100 else ''),  # Truncate for display
            'confidence': ocr_result['confidence'],
            'engine': OCR_ENGINE,
            'clipboard': ocr_result['clipboard']
        }
        print(json.dumps(result, indent=2))
        return 0
    else:
        result = {
            'success': False,
            'message': message,
            'engine': OCR_ENGINE
        }
        print(json.dumps(result))
        return 1


if __name__ == '__main__':
    sys.exit(main())