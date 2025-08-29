import subprocess
import sys
import json


def get_recycle_bin_status():
    """Get the current status of the recycle bin."""
    if sys.platform != 'win32':
        return 'Not available'
    
    try:
        # Use PowerShell to check recycle bin status
        ps_script = '''
        $recycleBin = (New-Object -ComObject Shell.Application).NameSpace(0xA)
        $items = $recycleBin.Items()
        if ($items.Count -eq 0) {
            Write-Output "Empty"
        } else {
            Write-Output "$($items.Count) items"
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
            return result.stdout.strip()
        else:
            return 'Error checking status'
            
    except Exception:
        return 'Status check failed'


def empty_recycle_bin():
    """Empty the recycle bin."""
    if sys.platform != 'win32':
        return {
            'success': False,
            'message': 'Recycle bin empty only supported on Windows'
        }
    
    try:
        # Use PowerShell to empty recycle bin
        ps_script = '''
        Add-Type -AssemblyName Microsoft.VisualBasic
        [Microsoft.VisualBasic.FileIO.FileSystem]::DeleteDirectory("C:\\$Recycle.Bin", "DeleteAllContents")
        Write-Output "Success"
        '''
        
        # Use Clear-RecycleBin cmdlet with -Force to avoid confirmations
        ps_script_alt = '''
        # First check if recycle bin has items
        $recycleBin = (New-Object -ComObject Shell.Application).NameSpace(0xA)
        $items = $recycleBin.Items()
        if ($items.Count -eq 0) {
            Write-Output "Already empty"
        } else {
            $itemCount = $items.Count
            # Use Clear-RecycleBin with -Force to avoid individual confirmations
            try {
                Clear-RecycleBin -Force -ErrorAction Stop
                Write-Output "Emptied $itemCount items"
            } catch {
                # Fallback to SHEmptyRecycleBin API
                Add-Type @'
                using System;
                using System.Runtime.InteropServices;
                public class RecycleBin {
                    [DllImport("shell32.dll")]
                    public static extern int SHEmptyRecycleBin(IntPtr hwnd, string pszRootPath, uint dwFlags);
                    public const uint SHERB_NOCONFIRMATION = 0x00000001;
                    public const uint SHERB_NOPROGRESSUI = 0x00000002;
                    public const uint SHERB_NOSOUND = 0x00000004;
                }
'@
                $result = [RecycleBin]::SHEmptyRecycleBin([IntPtr]::Zero, $null, 0x00000007)
                if ($result -eq 0) {
                    Write-Output "Emptied $itemCount items"
                } else {
                    throw "SHEmptyRecycleBin failed with code: $result"
                }
            }
        }
        '''
        
        result = subprocess.run(
            ['powershell', '-Command', ps_script_alt],
            capture_output=True,
            text=True,
            timeout=30,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
        
        if result.returncode == 0:
            output = result.stdout.strip()
            if "Already empty" in output:
                return {
                    'success': True,
                    'message': 'Recycle bin is already empty'
                }
            else:
                return {
                    'success': True,
                    'message': f'Recycle bin emptied successfully - {output}'
                }
        else:
            # Try alternative method using rd command
            result = subprocess.run(
                ['rd', '/s', '/q', 'C:\\$Recycle.Bin'],
                capture_output=True,
                text=True,
                timeout=30,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'message': 'Recycle bin emptied successfully'
                }
            else:
                error_msg = result.stderr if result.stderr else result.stdout
                return {
                    'success': False,
                    'message': f'Failed to empty recycle bin: {error_msg}'
                }
        
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'message': 'Recycle bin empty operation timed out'
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'Error emptying recycle bin: {str(e)}'
        }


def main():
    """Main function to empty recycle bin."""
    result = empty_recycle_bin()
    print(json.dumps(result))
    return result.get('success', False)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)