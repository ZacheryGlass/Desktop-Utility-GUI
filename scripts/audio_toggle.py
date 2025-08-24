import subprocess
from typing import Dict, Any, List
import sys
import os
from pathlib import Path
import json

sys.path.append('..')
from core.base_script import UtilityScript
from core.button_types import ButtonType

class AudioToggle(UtilityScript):
    
    def __init__(self):
        # State file for tracking current audio device
        self.state_file = Path.home() / '.desktop_utility_gui' / 'audio_device_state.json'
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Audio devices list will be populated on first execute
        self.audio_devices = []
        self.current_device_index = 0
        
        # Load saved state
        self._load_saved_state()
        
        # Call super().__init__() after setting attributes
        super().__init__()
    
    def _load_saved_state(self):
        """Load the saved audio device state from file."""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    self.audio_devices = data.get('devices', [])
                    self.current_device_index = data.get('current_index', 0)
        except Exception:
            pass
    
    def _save_state(self):
        """Save the current audio device state to file."""
        try:
            with open(self.state_file, 'w') as f:
                json.dump({
                    'devices': self.audio_devices,
                    'current_index': self.current_device_index
                }, f, indent=2)
        except Exception:
            pass
    
    def _get_audio_devices(self) -> List[str]:
        """Get list of available audio output devices using PowerShell."""
        try:
            # PowerShell script to get audio devices
            ps_script = """
            Add-Type @'
            using System;
            using System.Runtime.InteropServices;
            using System.Collections.Generic;
            
            public class AudioDevice {
                [DllImport("winmm.dll", CharSet = CharSet.Auto)]
                public static extern int waveOutGetNumDevs();
                
                [DllImport("winmm.dll", CharSet = CharSet.Auto)]
                public static extern int waveOutGetDevCaps(int uDeviceID, ref WAVEOUTCAPS pwoc, int cbwoc);
                
                [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Auto)]
                public struct WAVEOUTCAPS {
                    public short wMid;
                    public short wPid;
                    public int vDriverVersion;
                    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 32)]
                    public string szPname;
                    public uint dwFormats;
                    public short wChannels;
                    public short wReserved1;
                    public uint dwSupport;
                }
                
                public static List<string> GetDevices() {
                    var devices = new List<string>();
                    int numDevs = waveOutGetNumDevs();
                    for (int i = 0; i < numDevs; i++) {
                        WAVEOUTCAPS caps = new WAVEOUTCAPS();
                        if (waveOutGetDevCaps(i, ref caps, Marshal.SizeOf(caps)) == 0) {
                            devices.Add(caps.szPname);
                        }
                    }
                    return devices;
                }
            }
'@
            
            [AudioDevice]::GetDevices() | ConvertTo-Json
            """
            
            result = subprocess.run(
                ['powershell', '-Command', ps_script],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            
            if result.returncode == 0 and result.stdout:
                devices = json.loads(result.stdout)
                if isinstance(devices, list):
                    return devices
                elif isinstance(devices, str):
                    return [devices]
            
            # Fallback: use simpler PowerShell command
            ps_script_simple = """
            Get-CimInstance -ClassName Win32_SoundDevice | Where-Object {$_.Status -eq 'OK'} | Select-Object -ExpandProperty Name | ConvertTo-Json
            """
            
            result = subprocess.run(
                ['powershell', '-Command', ps_script_simple],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            
            if result.returncode == 0 and result.stdout:
                devices = json.loads(result.stdout)
                if isinstance(devices, list):
                    return devices
                elif isinstance(devices, str):
                    return [devices]
                    
        except Exception:
            pass
        
        return []
    
    def _set_default_audio_device(self, device_index: int) -> bool:
        """Set the default audio output device using nircmd."""
        try:
            # First, try using nircmd if available
            nircmd_path = Path('C:/Windows/nircmd.exe')
            if not nircmd_path.exists():
                nircmd_path = Path('nircmd.exe')
            
            if nircmd_path.exists():
                # nircmd setdefaultsounddevice <device_name>
                if device_index < len(self.audio_devices):
                    device_name = self.audio_devices[device_index]
                    result = subprocess.run(
                        [str(nircmd_path), 'setdefaultsounddevice', device_name],
                        capture_output=True,
                        timeout=5,
                        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
                    )
                    return result.returncode == 0
            
            # Fallback: Use PowerShell with AudioDeviceCmdlets module (if installed)
            ps_script = f"""
            # Try to import AudioDeviceCmdlets module
            try {{
                Import-Module AudioDeviceCmdlets -ErrorAction Stop
                $devices = Get-AudioDevice -List
                if ($devices.Count -gt {device_index}) {{
                    Set-AudioDevice -Index {device_index}
                    exit 0
                }}
            }} catch {{
                # Module not available
            }}
            
            # Alternative: Use Windows Audio Session API
            Add-Type @'
            using System;
            using System.Runtime.InteropServices;
            
            public class AudioSwitcher {{
                [DllImport("ole32.dll")]
                public static extern int CoInitialize(IntPtr pvReserved);
                
                public static void SetDevice(int index) {{
                    CoInitialize(IntPtr.Zero);
                    // This is a simplified version - full implementation would require COM interop
                }}
            }}
'@
            
            # For now, return error code to indicate we need nircmd or AudioDeviceCmdlets
            exit 1
            """
            
            result = subprocess.run(
                ['powershell', '-Command', ps_script],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            
            return result.returncode == 0
            
        except Exception:
            return False
    
    def get_metadata(self) -> Dict[str, Any]:
        return {
            'name': 'Audio Output',
            'description': 'Toggle between audio output devices',
            'button_type': ButtonType.TOGGLE
        }
    
    def get_status(self) -> str:
        """Return the current audio device name."""
        if self.audio_devices and self.current_device_index < len(self.audio_devices):
            device_name = self.audio_devices[self.current_device_index]
            # Truncate long device names for display
            if len(device_name) > 20:
                return device_name[:17] + '...'
            return device_name
        return 'No Device'
    
    def execute(self, *args, **kwargs) -> Dict[str, Any]:
        """Toggle to the next audio output device."""
        try:
            # Refresh device list
            devices = self._get_audio_devices()
            
            if not devices:
                return {
                    'success': False,
                    'message': 'No audio output devices found'
                }
            
            # Update device list if changed
            if devices != self.audio_devices:
                self.audio_devices = devices
                self.current_device_index = 0
            
            # Calculate next device index
            next_index = (self.current_device_index + 1) % len(self.audio_devices)
            
            # Try to set the audio device
            if self._set_default_audio_device(next_index):
                self.current_device_index = next_index
                self._save_state()
                
                return {
                    'success': True,
                    'message': f'Switched to: {self.audio_devices[next_index]}',
                    'new_status': self.get_status()
                }
            else:
                # If setting device failed, inform user about nircmd
                return {
                    'success': False,
                    'message': 'Audio switch requires nircmd.exe in C:\\Windows\\ or AudioDeviceCmdlets PowerShell module'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Error toggling audio device: {str(e)}'
            }
    
    def validate(self) -> bool:
        """Check if audio toggling is available on this system."""
        if sys.platform != 'win32':
            return False
        
        try:
            # Check if we can get audio devices
            devices = self._get_audio_devices()
            # Script is valid if we have at least 1 audio device
            return len(devices) >= 1
        except:
            return False


if __name__ == "__main__":
    import json as json_module
    
    script = AudioToggle()
    
    current_status = script.get_status()
    print(f"Current audio device: {current_status}")
    
    print("Toggling audio output device...")
    result = script.execute()
    
    print(json_module.dumps(result, indent=2))
    sys.exit(0 if result.get('success', False) else 1)