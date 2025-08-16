import subprocess
import re
from typing import Dict, Any, List
import sys

sys.path.append('..')
from core.base_script import UtilityScript
from core.button_types import ButtonType, CycleOptions

class PowerPlanToggle(UtilityScript):
    
    def __init__(self):
        super().__init__()
        self.power_plans = {
            'Balanced': '381b4222-f694-41f0-9685-ff5bb260df2e',
            'High performance': '8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c',
            'Power saver': 'a1841308-3541-4fab-bc81-f71556f20b4a'
        }
    
    def get_metadata(self) -> Dict[str, Any]:
        return {
            'name': 'Power Plan',
            'description': 'Cycle through Windows power plans',
            'button_type': ButtonType.CYCLE,
            'button_options': CycleOptions(
                options=['Balanced', 'High performance', 'Power saver'],
                show_current=True
            )
        }
    
    def get_status(self) -> str:
        if sys.platform != 'win32':
            return 'Balanced'
        
        try:
            result = subprocess.run(
                ['powercfg', '/getactivescheme'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                match = re.search(r':\s+([a-f0-9-]+)\s+\(([^)]+)\)', result.stdout)
                if match:
                    plan_name = match.group(2)
                    for known_plan in self.power_plans.keys():
                        if known_plan.lower() in plan_name.lower():
                            return known_plan
                    return plan_name
            
            return 'Unknown'
            
        except Exception as e:
            print(f"Error getting power plan: {e}")
            return 'Unknown'
    
    def execute(self, plan_name: str) -> Dict[str, Any]:
        if sys.platform != 'win32':
            return {
                'success': False,
                'message': 'Power plan control only supported on Windows'
            }
        
        try:
            if plan_name not in self.power_plans:
                return {
                    'success': False,
                    'message': f'Unknown power plan: {plan_name}'
                }
            
            guid = self.power_plans[plan_name]
            
            result = subprocess.run(
                ['powercfg', '/setactive', guid],
                capture_output=True,
                text=True,
                timeout=5
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
    
    def validate(self) -> bool:
        if sys.platform != 'win32':
            return False
        
        try:
            result = subprocess.run(
                ['powercfg', '/?'],
                capture_output=True,
                timeout=2
            )
            return result.returncode == 0
        except:
            return False