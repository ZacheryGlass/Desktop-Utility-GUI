"""Execute Python code from clipboard."""

import sys
import json
import traceback
from io import StringIO
from PyQt6.QtWidgets import QMessageBox, QApplication


def show_error(message):
    """Show error message in popup."""
    try:
        app = QApplication.instance()
        if not app:
            app = QApplication(sys.argv)
        
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setWindowTitle("Clipboard Executor Error")
        msg_box.setText("An error occurred while executing clipboard content:")
        msg_box.setDetailedText(message)
        msg_box.exec()
    except Exception:
        # Fallback to console if GUI fails
        print(f"Error: {message}")


def show_success(message):
    """Show success message in popup."""
    try:
        app = QApplication.instance()
        if not app:
            app = QApplication(sys.argv)
        
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setWindowTitle("Clipboard Executor Success")
        msg_box.setText(message)
        msg_box.exec()
    except Exception:
        # Fallback to console if GUI fails
        print(f"Success: {message}")


def main():
    """Execute Python code from clipboard."""
    try:
        # Get QApplication instance (create if needed for clipboard access)
        app = QApplication.instance()
        if not app:
            app = QApplication(sys.argv)
        
        # Access clipboard
        clipboard = app.clipboard()
        code = clipboard.text()
        
        if not code or not code.strip():
            show_error("Clipboard is empty or contains no text")
            result = {
                'success': False,
                'message': 'No code in clipboard'
            }
            print(json.dumps(result))
            return False
        
        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        
        try:
            # Execute the code
            exec(code, {"__name__": "__main__"})
            
            # Get output
            output = sys.stdout.getvalue()
            sys.stdout = old_stdout
            
            # Show success message
            if output:
                show_success(f"Code executed successfully.\n\nOutput:\n{output}")
                message = "Executed successfully with output"
            else:
                show_success("Code executed successfully (no output)")
                message = "Executed successfully"
            
            result = {
                'success': True,
                'message': message
            }
            print(json.dumps(result))
            return True
                
        except Exception as e:
            sys.stdout = old_stdout
            error_msg = f"Execution Error:\n{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
            show_error(error_msg)
            
            result = {
                'success': False,
                'message': f'Execution failed: {str(e)}'
            }
            print(json.dumps(result))
            return False
            
    except Exception as e:
        error_msg = f"Failed to access clipboard:\n{str(e)}"
        show_error(error_msg)
        
        result = {
            'success': False,
            'message': f'Clipboard access failed: {str(e)}'
        }
        print(json.dumps(result))
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)