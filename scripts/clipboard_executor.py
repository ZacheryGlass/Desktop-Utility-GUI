"""Execute Python code from clipboard."""

import sys
import traceback
from io import StringIO
from core.base_script import UtilityScript
from core.button_types import ButtonType
from PyQt6.QtWidgets import QMessageBox, QApplication


class ClipboardExecutor(UtilityScript):
    """Execute Python code from clipboard with error handling."""
    
    def get_metadata(self):
        """Return script metadata."""
        return {
            "name": "Execute Clipboard",
            "description": "Execute Python code from clipboard",
            "button_type": ButtonType.RUN
        }
    
    def execute(self, *args, **kwargs):
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
                self._show_error("Clipboard is empty or contains no text")
                return "No code in clipboard"
            
            # Capture stdout
            old_stdout = sys.stdout
            sys.stdout = StringIO()
            
            try:
                # Execute the code
                exec(code, {"__name__": "__main__"})
                
                # Get output
                output = sys.stdout.getvalue()
                sys.stdout = old_stdout
                
                # Show success message if there's output
                if output:
                    self._show_info(f"Code executed successfully.\n\nOutput:\n{output}")
                    return f"Executed successfully with output"
                else:
                    return "Executed successfully"
                    
            except Exception as e:
                sys.stdout = old_stdout
                error_msg = f"Execution Error:\n{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
                self._show_error(error_msg)
                return f"Execution failed: {str(e)}"
                
        except Exception as e:
            error_msg = f"Failed to access clipboard:\n{str(e)}"
            self._show_error(error_msg)
            return f"Clipboard access failed: {str(e)}"
    
    def _show_error(self, message):
        """Show error popup."""
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
        except:
            # Fallback to console if GUI fails
            print(f"Error: {message}")
    
    def _show_info(self, message):
        """Show info popup."""
        try:
            app = QApplication.instance()
            if not app:
                app = QApplication(sys.argv)
            
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Icon.Information)
            msg_box.setWindowTitle("Clipboard Executor")
            msg_box.setText(message)
            msg_box.exec()
        except:
            # Fallback to console if GUI fails
            print(f"Info: {message}")
    
    def get_status(self):
        """Return current status."""
        return "Ready to execute clipboard content"
    
    def validate(self):
        """Validate that clipboard is accessible."""
        try:
            app = QApplication.instance()
            if not app:
                app = QApplication(sys.argv)
            clipboard = app.clipboard()
            _ = clipboard.text()
            return True, "Clipboard accessible"
        except Exception as e:
            return False, f"Cannot access clipboard: {str(e)}"


if __name__ == "__main__":
    import json
    
    script = ClipboardExecutor()
    
    status = script.get_status()
    print(f"Status: {status}")
    
    print("Executing code from clipboard...")
    result = script.execute()
    
    print(f"Result: {result}")
    
    # Exit with appropriate code based on result
    if "failed" in result.lower() or "error" in result.lower():
        sys.exit(1)
    else:
        sys.exit(0)