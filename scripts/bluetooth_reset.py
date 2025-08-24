import subprocess
import time
import sys
from typing import Dict, Any

sys.path.append('..')
from core.base_script import UtilityScript
from core.button_types import ButtonType, RunOptions

class BluetoothToggle(UtilityScript):
    
    def __init__(self):
        super().__init__()
        self.service_name = "bthserv"
    
    def get_metadata(self) -> Dict[str, Any]:
        return {
            'name': 'Bluetooth Toggle',
            'description': 'Toggle Bluetooth off for 10 seconds then back on',
            'button_type': ButtonType.RUN,
            'button_options': RunOptions(
                button_text="Toggle Bluetooth",
                confirm_before_run=True,
                confirm_message="This will turn Bluetooth off for 10 seconds then back on. Continue?"
            )
        }
    
    def get_status(self) -> str:
        if sys.platform != 'win32':
            return 'Not available'
        
        try:
            # Use PowerShell with WinRT API to check actual Bluetooth radio state
            ps_script = '''
            Add-Type -AssemblyName System.Runtime.WindowsRuntime
            $asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
            Function Await($WinRtTask, $ResultType) {
                $asTask = $asTaskGeneric.MakeGenericMethod($ResultType)
                $netTask = $asTask.Invoke($null, @($WinRtTask))
                $netTask.Wait(-1) | Out-Null
                $netTask.Result
            }
            [Windows.Devices.Radios.Radio,Windows.System.Devices,ContentType=WindowsRuntime] | Out-Null
            [Windows.Devices.Radios.RadioAccessStatus,Windows.System.Devices,ContentType=WindowsRuntime] | Out-Null
            try {
                $accessLevel = Await ([Windows.Devices.Radios.Radio]::RequestAccessAsync()) ([Windows.Devices.Radios.RadioAccessStatus])
                if($accessLevel -eq "Allowed") {
                    $radios = Await ([Windows.Devices.Radios.Radio]::GetRadiosAsync()) ([System.Collections.Generic.IReadOnlyList[Windows.Devices.Radios.Radio]])
                    $bluetooth = $radios | Where-Object { $_.Kind -eq 'Bluetooth' }
                    if($bluetooth) {
                        if($bluetooth.State -eq 'On') { Write-Output "ON" } else { Write-Output "OFF" }
                    } else { Write-Output "Not available" }
                } else { Write-Output "Not available" }
            } catch { Write-Output "OFF" }
            '''
            
            result = subprocess.run(
                ['powershell', '-Command', ps_script],
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            
            if result.returncode == 0:
                status = result.stdout.strip()
                return status if status in ['ON', 'OFF', 'Not available'] else 'OFF'
            else:
                return 'OFF'
                
        except Exception:
            return 'OFF'
    
    def execute(self) -> Dict[str, Any]:
        if sys.platform != 'win32':
            return {
                'success': False,
                'message': 'Bluetooth toggle only supported on Windows'
            }
        
        try:
            # Ensure Bluetooth service is running first
            try:
                result = subprocess.run(
                    ['sc', 'query', self.service_name],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                if result.returncode == 0 and 'STOPPED' in result.stdout:
                    subprocess.run(
                        ['net', 'start', self.service_name],
                        capture_output=True,
                        timeout=10,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
            except:
                pass
            
            # PowerShell script to toggle Bluetooth off, wait, then on
            ps_script = '''
            Add-Type -AssemblyName System.Runtime.WindowsRuntime
            $asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
            Function Await($WinRtTask, $ResultType) {
                $asTask = $asTaskGeneric.MakeGenericMethod($ResultType)
                $netTask = $asTask.Invoke($null, @($WinRtTask))
                $netTask.Wait(-1) | Out-Null
                $netTask.Result
            }
            [Windows.Devices.Radios.Radio,Windows.System.Devices,ContentType=WindowsRuntime] | Out-Null
            [Windows.Devices.Radios.RadioAccessStatus,Windows.System.Devices,ContentType=WindowsRuntime] | Out-Null
            [Windows.Devices.Radios.RadioState,Windows.System.Devices,ContentType=WindowsRuntime] | Out-Null
            
            try {
                $accessLevel = Await ([Windows.Devices.Radios.Radio]::RequestAccessAsync()) ([Windows.Devices.Radios.RadioAccessStatus])
                if($accessLevel -eq "Allowed") {
                    $radios = Await ([Windows.Devices.Radios.Radio]::GetRadiosAsync()) ([System.Collections.Generic.IReadOnlyList[Windows.Devices.Radios.Radio]])
                    $bluetooth = $radios | Where-Object { $_.Kind -eq 'Bluetooth' }
                    if($bluetooth) {
                        Write-Output "Turning Bluetooth OFF..."
                        Await ($bluetooth.SetStateAsync("Off")) ([Windows.Devices.Radios.RadioAccessStatus]) | Out-Null
                        Start-Sleep -Seconds 10
                        Write-Output "Turning Bluetooth ON..."
                        Await ($bluetooth.SetStateAsync("On")) ([Windows.Devices.Radios.RadioAccessStatus]) | Out-Null
                        Write-Output "SUCCESS"
                    } else {
                        Write-Output "ERROR: No Bluetooth radio found"
                    }
                } else {
                    Write-Output "ERROR: Radio access not allowed"
                }
            } catch {
                Write-Output "ERROR: $($_.Exception.Message)"
            }
            '''
            
            # Run the PowerShell script in the background using Popen
            
            process = subprocess.Popen(
                ['powershell', '-Command', ps_script],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            
            # Return immediately while the process runs in background
            return {
                'success': True,
                'message': 'Bluetooth toggle started (runs for 10 seconds in background)'
            }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Error starting Bluetooth toggle: {str(e)}'
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


if __name__ == "__main__":
    import json
    
    script = BluetoothToggle()
    
    current_status = script.get_status()
    print(f"Current Bluetooth status: {current_status}")
    
    if current_status == 'Not available':
        print("Bluetooth is not available on this system")
        sys.exit(1)
    
    print("Starting Bluetooth toggle (will turn off for 10 seconds then back on)...")
    result = script.execute()
    
    print(json.dumps(result, indent=2))
    sys.exit(0 if result.get('success', False) else 1)