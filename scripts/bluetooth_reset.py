import subprocess
import time
import sys
from typing import Dict, Any

sys.path.append('..')
from core.base_script import UtilityScript
from core.button_types import ButtonType, RunOptions

class BluetoothReset(UtilityScript):
    
    def __init__(self):
        super().__init__()
        self.service_name = "bthserv"
        self.last_reset_time = None
    
    def get_metadata(self) -> Dict[str, Any]:
        return {
            'name': 'Bluetooth Reset',
            'description': 'Reset Bluetooth services and adapters to fix connectivity issues',
            'button_type': ButtonType.RUN,
            'button_options': RunOptions(
                button_text="Reset Bluetooth",
                confirm_before_run=True,
                confirm_message="This will temporarily disable Bluetooth and disconnect all devices. Continue?"
            )
        }
    
    def get_status(self) -> str:
        if sys.platform != 'win32':
            return 'Not available'
        
        try:
            result = subprocess.run(
                ['sc', 'query', self.service_name],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            
            if result.returncode == 0:
                if 'RUNNING' in result.stdout:
                    return 'Bluetooth service running'
                elif 'STOPPED' in result.stdout:
                    return 'Bluetooth service stopped'
                else:
                    return 'Bluetooth service status unknown'
            else:
                return 'Bluetooth service not found'
                
        except Exception as e:
            return f'Error: {str(e)}'
    
    def execute(self) -> Dict[str, Any]:
        if sys.platform != 'win32':
            return {
                'success': False,
                'message': 'Bluetooth reset only supported on Windows'
            }
        
        try:
            steps_completed = []
            
            # Step 1: Stop Bluetooth Support Service
            try:
                result = subprocess.run(
                    ['net', 'stop', self.service_name],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
                )
                if result.returncode == 0 or 'service is not started' in result.stdout.lower():
                    steps_completed.append("Bluetooth service stopped")
                else:
                    steps_completed.append(f"Warning: Could not stop service - {result.stderr[:100]}")
            except subprocess.TimeoutExpired:
                steps_completed.append("Warning: Service stop timed out")
            
            # Step 2: Disable and re-enable Bluetooth adapters using PowerShell
            try:
                # Disable all Bluetooth adapters
                disable_cmd = '''
                Get-PnpDevice -Class Bluetooth | Where-Object {$_.Status -eq 'OK'} | ForEach-Object {
                    Disable-PnpDevice -InstanceId $_.InstanceId -Confirm:$false
                }
                '''
                
                result = subprocess.run(
                    ['powershell', '-Command', disable_cmd],
                    capture_output=True,
                    text=True,
                    timeout=15,
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
                )
                
                if result.returncode == 0:
                    steps_completed.append("Bluetooth adapters disabled")
                else:
                    # Try alternative method using devcon if PowerShell fails
                    steps_completed.append("Note: Could not disable adapters via PowerShell")
                
                # Wait a moment for devices to fully disable
                time.sleep(2)
                
                # Re-enable all Bluetooth adapters
                enable_cmd = '''
                Get-PnpDevice -Class Bluetooth | Where-Object {$_.Status -ne 'OK'} | ForEach-Object {
                    Enable-PnpDevice -InstanceId $_.InstanceId -Confirm:$false
                }
                '''
                
                result = subprocess.run(
                    ['powershell', '-Command', enable_cmd],
                    capture_output=True,
                    text=True,
                    timeout=15,
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
                )
                
                if result.returncode == 0:
                    steps_completed.append("Bluetooth adapters re-enabled")
                else:
                    steps_completed.append("Note: Could not re-enable adapters via PowerShell")
                    
            except subprocess.TimeoutExpired:
                steps_completed.append("Warning: Adapter reset timed out")
            except Exception as e:
                steps_completed.append(f"Warning: Adapter reset failed - {str(e)[:50]}")
            
            # Step 3: Restart Bluetooth Support Service
            try:
                result = subprocess.run(
                    ['net', 'start', self.service_name],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
                )
                if result.returncode == 0 or 'service was started successfully' in result.stdout.lower():
                    steps_completed.append("Bluetooth service restarted")
                else:
                    steps_completed.append(f"Warning: Could not start service - {result.stderr[:100]}")
            except subprocess.TimeoutExpired:
                steps_completed.append("Warning: Service start timed out")
            
            # Step 4: Force Bluetooth discovery/scan
            try:
                # Use PowerShell to trigger Bluetooth discovery
                scan_cmd = '''
                Add-Type -AssemblyName System.Runtime.WindowsRuntime
                $asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | ? { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
                [Windows.Devices.Enumeration.DeviceInformation,Windows.Devices.Enumeration,ContentType=WindowsRuntime] > $null
                $deviceSelector = [Windows.Devices.Enumeration.DeviceInformation]::CreateWatcher()
                $deviceSelector.Start()
                Start-Sleep -Seconds 2
                $deviceSelector.Stop()
                '''
                
                result = subprocess.run(
                    ['powershell', '-Command', scan_cmd],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
                )
                
                if result.returncode == 0:
                    steps_completed.append("Bluetooth device scan triggered")
                else:
                    steps_completed.append("Note: Could not trigger device scan")
                    
            except:
                steps_completed.append("Note: Device scan step skipped")
            
            # Wait for services to stabilize
            time.sleep(2)
            
            self.last_reset_time = time.time()
            
            return {
                'success': True,
                'message': f'Bluetooth reset completed. Steps: {", ".join(steps_completed)}',
                'steps_completed': steps_completed
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Bluetooth reset failed: {str(e)}'
            }
    
    def validate(self) -> bool:
        if sys.platform != 'win32':
            return False
        
        try:
            # Check if we can query the Bluetooth service
            result = subprocess.run(
                ['sc', 'query', self.service_name],
                capture_output=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            
            # Also check if PowerShell is available
            ps_result = subprocess.run(
                ['powershell', '-Command', 'echo test'],
                capture_output=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            
            return result.returncode == 0 and ps_result.returncode == 0
        except:
            return False