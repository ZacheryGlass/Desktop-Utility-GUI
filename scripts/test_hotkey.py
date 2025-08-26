import json
from datetime import datetime
from pathlib import Path


def main():
    """Log the execution time and show a notification"""
    try:
        # Log file for tracking hotkey executions
        log_file = Path.home() / '.desktop_utility_gui' / 'hotkey_test.log'
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Write to log file
        with open(log_file, 'a') as f:
            f.write(f"Executed at {current_time}\n")
        
        # Also create a visible indicator file on desktop
        desktop = Path.home() / 'Desktop'
        if desktop.exists():
            indicator_file = desktop / 'hotkey_test_executed.txt'
            with open(indicator_file, 'w') as f:
                f.write(f"Hotkey test executed successfully at {current_time}\n")
                f.write("You can delete this file.\n")
        
        result = {
            'success': True,
            'message': f'Test hotkey executed at {current_time}'
        }
        
        print(json.dumps(result))
        return True
        
    except Exception as e:
        result = {
            'success': False,
            'message': f'Test hotkey failed: {str(e)}'
        }
        print(json.dumps(result))
        return False


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)