import subprocess
import re
import json
import sys
import argparse


def get_current_power_plan():
    """Get the currently active power plan."""
    power_plans = {
        'Balanced': '381b4222-f694-41f0-9685-ff5bb260df2e',
        'High performance': '8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c',
        'Power saver': 'a1841308-3541-4fab-bc81-f71556f20b4a'
    }
    
    if sys.platform != 'win32':
        return 'Balanced'
    
    try:
        result = subprocess.run(
            ['powercfg', '/getactivescheme'],
            capture_output=True,
            text=True,
            timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
        
        if result.returncode == 0:
            match = re.search(r':\s+([a-f0-9-]+)\s+\(([^)]+)\)', result.stdout)
            if match:
                plan_name = match.group(2)
                for known_plan in power_plans.keys():
                    if known_plan.lower() in plan_name.lower():
                        return known_plan
                return plan_name
        
        return 'Unknown'
        
    except Exception as e:
        print(f"Error getting power plan: {e}")
        return 'Unknown'


def set_power_plan(plan_name: str):
    """Set the Windows power plan."""
    power_plans = {
        'Balanced': '381b4222-f694-41f0-9685-ff5bb260df2e',
        'High performance': '8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c',
        'Power saver': 'a1841308-3541-4fab-bc81-f71556f20b4a'
    }
    
    if sys.platform != 'win32':
        return {
            'success': False,
            'message': 'Power plan control only supported on Windows'
        }
    
    try:
        if plan_name not in power_plans:
            return {
                'success': False,
                'message': f'Unknown power plan: {plan_name}'
            }
        
        guid = power_plans[plan_name]
        
        result = subprocess.run(
            ['powercfg', '/setactive', guid],
            capture_output=True,
            text=True,
            timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
        
        if result.returncode == 0:
            return {
                'success': True,
                'message': f'Power plan changed to: {plan_name}',
                'new_status': plan_name
            }
        else:
            error_msg = result.stderr if result.stderr else 'Unknown error'
            return {
                'success': False,
                'message': f'Failed to change power plan: {error_msg}'
            }
            
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'message': 'Power plan change operation timed out'
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'Error changing power plan: {str(e)}'
        }


def main():
    parser = argparse.ArgumentParser(description='Windows Power Plan Control')
    parser.add_argument('--plan', choices=['Balanced', 'High performance', 'Power saver'],
                       help='Power plan to set')
    
    args = parser.parse_args()
    
    if args.plan:
        result = set_power_plan(args.plan)
    else:
        # Cycle through available plans
        current_status = get_current_power_plan()
        options = ['Balanced', 'High performance', 'Power saver']
        
        current_index = options.index(current_status) if current_status in options else 0
        next_index = (current_index + 1) % len(options)
        next_plan = options[next_index]
        
        result = set_power_plan(next_plan)
    
    print(json.dumps(result))
    return result.get('success', False)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)