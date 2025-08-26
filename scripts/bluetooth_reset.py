import subprocess
import time
import sys
import json


def get_bluetooth_status():
    """Get the current Bluetooth status."""
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
                    if($bluetooth.State -eq "On") { 
                        Write-Output "On"
                    } else { 
                        Write-Output "Off" 
                    }
                } else { 
                    Write-Output "Not found" 
                }
            } else { 
                Write-Output "Access denied" 
            }
        } catch { 
            Write-Output "Error: $_" 
        }
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
            if status in ['On', 'Off']:
                return status
            else:
                # Fallback: Check Bluetooth service status
                service_result = subprocess.run(
                    ['sc', 'query', 'bthserv'],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
                )
                
                if 'RUNNING' in service_result.stdout:
                    return 'Service Running'
                elif 'STOPPED' in service_result.stdout:
                    return 'Service Stopped'
                else:
                    return 'Unknown'
        else:
            return 'Error checking status'
            
    except Exception:
        return 'Status check failed'


def toggle_bluetooth():
    """Toggle Bluetooth off for 10 seconds then back on."""
    if sys.platform != 'win32':
        return {
            'success': False,
            'message': 'Bluetooth toggle only supported on Windows'
        }
    
    try:
        service_name = "bthserv"
        
        # First, try to stop the Bluetooth service
        result = subprocess.run(
            ['net', 'stop', service_name],
            capture_output=True,
            text=True,
            timeout=30,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
        
        if result.returncode != 0 and "already stopped" not in result.stdout.lower():
            # Try with 'sc' command as fallback
            result = subprocess.run(
                ['sc', 'stop', service_name],
                capture_output=True,
                text=True,
                timeout=30,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            
            if result.returncode != 0:
                error_msg = result.stderr if result.stderr else result.stdout
                return {
                    'success': False,
                    'message': f'Failed to stop Bluetooth service: {error_msg}'
                }
        
        # Wait 10 seconds
        time.sleep(10)
        
        # Start the Bluetooth service again
        result = subprocess.run(
            ['net', 'start', service_name],
            capture_output=True,
            text=True,
            timeout=30,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
        
        if result.returncode != 0 and "already started" not in result.stdout.lower():
            # Try with 'sc' command as fallback
            result = subprocess.run(
                ['sc', 'start', service_name],
                capture_output=True,
                text=True,
                timeout=30,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            
            if result.returncode != 0:
                error_msg = result.stderr if result.stderr else result.stdout
                return {
                    'success': False,
                    'message': f'Failed to restart Bluetooth service: {error_msg}'
                }
        
        return {
            'success': True,
            'message': 'Bluetooth service restarted successfully'
        }
        
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'message': 'Bluetooth service operation timed out'
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'Error toggling Bluetooth: {str(e)}'
        }


def main():
    """Main function to toggle Bluetooth."""
    result = toggle_bluetooth()
    print(json.dumps(result))
    return result.get('success', False)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)