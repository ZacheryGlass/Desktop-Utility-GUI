import subprocess
import re
from typing import Dict, Any
import sys

sys.path.append('..')
from core.base_script import UtilityScript
from core.button_types import ButtonType, SliderOptions

class VolumeControl(UtilityScript):
    
    def get_metadata(self) -> Dict[str, Any]:
        return {
            'name': 'Volume Control',
            'description': 'Adjust system volume',
            'button_type': ButtonType.SLIDER,
            'button_options': SliderOptions(
                min_value=0,
                max_value=100,
                step=5,
                show_value=True,
                suffix="%"
            )
        }
    
    def get_status(self) -> int:
        if sys.platform != 'win32':
            return 50
        
        try:
            script = '''
            Add-Type -TypeDefinition @"
            using System.Runtime.InteropServices;
            [Guid("5CDF2C82-841E-4546-9722-0CF74078229A"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
            interface IAudioEndpointVolume {
                int f(); int g(); int h(); int i();
                int SetMasterVolumeLevelScalar(float fLevel, System.Guid pguidEventContext);
                int j();
                int GetMasterVolumeLevelScalar(out float pfLevel);
                int k(); int l(); int m(); int n();
                int SetMute([MarshalAs(UnmanagedType.Bool)] bool bMute, System.Guid pguidEventContext);
                int GetMute(out bool pbMute);
            }
            [Guid("D666063F-1587-4E43-81F1-B948E807363F"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
            interface IMMDevice {
                int Activate(ref System.Guid id, int clsCtx, int activationParams, out IAudioEndpointVolume aev);
            }
            [Guid("A95664D2-9614-4F35-A746-DE8DB63617E6"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
            interface IMMDeviceEnumerator {
                int f();
                int GetDefaultAudioEndpoint(int dataFlow, int role, out IMMDevice endpoint);
            }
            [ComImport, Guid("BCDE0395-E52F-467C-8E3D-C4579291692E")] class MMDeviceEnumeratorComObject { }
            public class Audio {
                static IAudioEndpointVolume Vol() {
                    var enumerator = new MMDeviceEnumeratorComObject() as IMMDeviceEnumerator;
                    IMMDevice dev = null;
                    Marshal.ThrowExceptionForHR(enumerator.GetDefaultAudioEndpoint(0, 1, out dev));
                    IAudioEndpointVolume epv = null;
                    var epvid = typeof(IAudioEndpointVolume).GUID;
                    Marshal.ThrowExceptionForHR(dev.Activate(ref epvid, 23, 0, out epv));
                    return epv;
                }
                public static float Volume {
                    get {float v = -1; Marshal.ThrowExceptionForHR(Vol().GetMasterVolumeLevelScalar(out v)); return v;}
                }
            }
"@
            [Audio]::Volume * 100
            '''
            
            result = subprocess.run(
                ['powershell', '-Command', script],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            
            if result.returncode == 0:
                try:
                    volume = int(float(result.stdout.strip()))
                    return max(0, min(100, volume))
                except:
                    return 50
            return 50
            
        except Exception as e:
            print(f"Error getting volume: {e}")
            return 50
    
    def execute(self, volume: float) -> Dict[str, Any]:
        if sys.platform != 'win32':
            return {
                'success': False,
                'message': 'Volume control only supported on Windows'
            }
        
        try:
            volume = max(0, min(100, int(volume)))
            
            nircmd_commands = [
                ['nircmd.exe', 'setsysvolume', str(int(volume * 655.35))],
                ['nircmd.exe', 'changesysvolume', str(int((volume - self.get_status()) * 655.35))]
            ]
            
            for cmd in nircmd_commands:
                try:
                    result = subprocess.run(cmd, capture_output=True, timeout=2)
                    if result.returncode == 0:
                        return {
                            'success': True,
                            'message': f'Volume set to {volume}%',
                            'new_status': volume
                        }
                except:
                    continue
            
            powershell_script = f'''
            $volume = {volume / 100.0}
            Add-Type -TypeDefinition @"
            using System.Runtime.InteropServices;
            [Guid("5CDF2C82-841E-4546-9722-0CF74078229A"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
            interface IAudioEndpointVolume {{
                int f(); int g(); int h(); int i();
                int SetMasterVolumeLevelScalar(float fLevel, System.Guid pguidEventContext);
                int j();
                int GetMasterVolumeLevelScalar(out float pfLevel);
            }}
            [Guid("D666063F-1587-4E43-81F1-B948E807363F"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
            interface IMMDevice {{
                int Activate(ref System.Guid id, int clsCtx, int activationParams, out IAudioEndpointVolume aev);
            }}
            [Guid("A95664D2-9614-4F35-A746-DE8DB63617E6"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
            interface IMMDeviceEnumerator {{
                int f();
                int GetDefaultAudioEndpoint(int dataFlow, int role, out IMMDevice endpoint);
            }}
            [ComImport, Guid("BCDE0395-E52F-467C-8E3D-C4579291692E")] class MMDeviceEnumeratorComObject {{ }}
            public class Audio {{
                static IAudioEndpointVolume Vol() {{
                    var enumerator = new MMDeviceEnumeratorComObject() as IMMDeviceEnumerator;
                    IMMDevice dev = null;
                    Marshal.ThrowExceptionForHR(enumerator.GetDefaultAudioEndpoint(0, 1, out dev));
                    IAudioEndpointVolume epv = null;
                    var epvid = typeof(IAudioEndpointVolume).GUID;
                    Marshal.ThrowExceptionForHR(dev.Activate(ref epvid, 23, 0, out epv));
                    return epv;
                }}
                public static void SetVolume(float v) {{
                    Marshal.ThrowExceptionForHR(Vol().SetMasterVolumeLevelScalar(v, System.Guid.Empty));
                }}
            }}
"@
            [Audio]::SetVolume($volume)
            '''
            
            result = subprocess.run(
                ['powershell', '-Command', powershell_script],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'message': f'Volume set to {volume}%',
                    'new_status': volume
                }
            else:
                return {
                    'success': False,
                    'message': f'Failed to set volume: {result.stderr}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Error setting volume: {str(e)}'
            }
    
    def validate(self) -> bool:
        return sys.platform == 'win32'