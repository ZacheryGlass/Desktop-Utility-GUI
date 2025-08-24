import logging
import ctypes
from ctypes import wintypes
import threading
from typing import Dict, Optional, Callable, Tuple, Set
from PyQt6.QtCore import QObject, pyqtSignal, QThread
from PyQt6.QtWidgets import QApplication
import win32con
import win32api
import win32gui

logger = logging.getLogger('Core.HotkeyManager')

# Windows modifier key constants
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000  # Prevents repeat when held down

# Virtual key code mappings
VK_CODES = {
    'F1': win32con.VK_F1, 'F2': win32con.VK_F2, 'F3': win32con.VK_F3,
    'F4': win32con.VK_F4, 'F5': win32con.VK_F5, 'F6': win32con.VK_F6,
    'F7': win32con.VK_F7, 'F8': win32con.VK_F8, 'F9': win32con.VK_F9,
    'F10': win32con.VK_F10, 'F11': win32con.VK_F11, 'F12': win32con.VK_F12,
    '0': ord('0'), '1': ord('1'), '2': ord('2'), '3': ord('3'), '4': ord('4'),
    '5': ord('5'), '6': ord('6'), '7': ord('7'), '8': ord('8'), '9': ord('9'),
    'A': ord('A'), 'B': ord('B'), 'C': ord('C'), 'D': ord('D'), 'E': ord('E'),
    'F': ord('F'), 'G': ord('G'), 'H': ord('H'), 'I': ord('I'), 'J': ord('J'),
    'K': ord('K'), 'L': ord('L'), 'M': ord('M'), 'N': ord('N'), 'O': ord('O'),
    'P': ord('P'), 'Q': ord('Q'), 'R': ord('R'), 'S': ord('S'), 'T': ord('T'),
    'U': ord('U'), 'V': ord('V'), 'W': ord('W'), 'X': ord('X'), 'Y': ord('Y'),
    'Z': ord('Z'),
    'SPACE': win32con.VK_SPACE, 'ENTER': win32con.VK_RETURN,
    'TAB': win32con.VK_TAB, 'ESCAPE': win32con.VK_ESCAPE, 'ESC': win32con.VK_ESCAPE,
    'BACKSPACE': win32con.VK_BACK, 'DELETE': win32con.VK_DELETE,
    'INSERT': win32con.VK_INSERT, 'HOME': win32con.VK_HOME,
    'END': win32con.VK_END, 'PAGEUP': win32con.VK_PRIOR,
    'PAGEDOWN': win32con.VK_NEXT, 'UP': win32con.VK_UP,
    'DOWN': win32con.VK_DOWN, 'LEFT': win32con.VK_LEFT,
    'RIGHT': win32con.VK_RIGHT,
    'NUMPAD0': win32con.VK_NUMPAD0, 'NUMPAD1': win32con.VK_NUMPAD1,
    'NUMPAD2': win32con.VK_NUMPAD2, 'NUMPAD3': win32con.VK_NUMPAD3,
    'NUMPAD4': win32con.VK_NUMPAD4, 'NUMPAD5': win32con.VK_NUMPAD5,
    'NUMPAD6': win32con.VK_NUMPAD6, 'NUMPAD7': win32con.VK_NUMPAD7,
    'NUMPAD8': win32con.VK_NUMPAD8, 'NUMPAD9': win32con.VK_NUMPAD9,
    'MULTIPLY': win32con.VK_MULTIPLY, 'ADD': win32con.VK_ADD,
    'SUBTRACT': win32con.VK_SUBTRACT, 'DIVIDE': win32con.VK_DIVIDE,
    'DECIMAL': win32con.VK_DECIMAL,
    'PAUSE': win32con.VK_PAUSE, 'CAPSLOCK': win32con.VK_CAPITAL,
    'NUMLOCK': win32con.VK_NUMLOCK, 'SCROLLLOCK': win32con.VK_SCROLL,
    'PRINTSCREEN': win32con.VK_SNAPSHOT,
    'PLUS': 0xBB, 'MINUS': 0xBD,  # OEM Plus and Minus keys
    'COMMA': 0xBC, 'PERIOD': 0xBE,  # OEM Comma and Period
    'SLASH': 0xBF, 'BACKSLASH': 0xDC,  # OEM 2 and 5
    'SEMICOLON': 0xBA, 'QUOTE': 0xDE,  # OEM 1 and 7
    'BRACKET_LEFT': 0xDB, 'BRACKET_RIGHT': 0xDD,  # OEM 4 and 6
    'GRAVE': 0xC0,  # OEM 3
}

# Reverse mapping for display
VK_NAMES = {v: k for k, v in VK_CODES.items()}

# System-reserved hotkey combinations to block
RESERVED_HOTKEYS = {
    ('CTRL', 'C'), ('CTRL', 'V'), ('CTRL', 'X'), ('CTRL', 'A'),
    ('CTRL', 'Z'), ('CTRL', 'Y'), ('CTRL', 'S'), ('CTRL', 'O'),
    ('CTRL', 'N'), ('CTRL', 'P'), ('CTRL', 'F'), ('CTRL', 'H'),
    ('ALT', 'TAB'), ('ALT', 'F4'), ('ALT', 'ESCAPE'),
    ('CTRL', 'ALT', 'DELETE'), ('CTRL', 'SHIFT', 'ESCAPE'),
    ('WIN', 'L'), ('WIN', 'D'), ('WIN', 'E'), ('WIN', 'R'),
    ('WIN', 'TAB'), ('WIN', 'X'),
}


class HotkeyListener(QThread):
    """Background thread that listens for Windows hotkey messages"""
    hotkey_triggered = pyqtSignal(int)  # Emits hotkey ID when triggered
    
    def __init__(self):
        super().__init__()
        self.hwnd = None
        self.running = False
        self._lock = threading.Lock()
        
    def run(self):
        """Main message loop for hotkey listening"""
        try:
            # Create a simple window using win32gui for receiving messages
            import win32gui
            
            # Register a window class
            wc = win32gui.WNDCLASS()
            wc.lpfnWndProc = lambda hwnd, msg, wparam, lparam: 0
            wc.lpszClassName = "HotkeyListener"
            wc.hInstance = win32api.GetModuleHandle(None)
            
            try:
                win32gui.RegisterClass(wc)
            except Exception:
                # Class might already be registered
                pass
            
            # Create a message-only window
            self.hwnd = win32gui.CreateWindow(
                "HotkeyListener",
                "Hotkey Listener Window",
                0,
                0, 0, 0, 0,
                win32con.HWND_MESSAGE,
                0,
                wc.hInstance,
                None
            )
            
            if not self.hwnd:
                logger.error("Failed to create message window")
                return
                
            logger.info(f"Hotkey listener started with hwnd: {self.hwnd}")
            self.running = True
            
            # Message loop using win32gui
            while self.running:
                try:
                    bRet, msg = win32gui.GetMessage(self.hwnd, 0, 0)
                    
                    if bRet == 0:  # WM_QUIT
                        break
                    elif bRet == -1:  # Error
                        logger.error("Error in message loop")
                        break
                    else:
                        if msg[1] == win32con.WM_HOTKEY:
                            hotkey_id = msg[2]  # wParam
                            logger.debug(f"Hotkey triggered: ID {hotkey_id}")
                            self.hotkey_triggered.emit(hotkey_id)
                        
                        win32gui.TranslateMessage(msg)
                        win32gui.DispatchMessage(msg)
                except Exception as e:
                    if self.running:
                        logger.error(f"Error in message loop: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"Error in hotkey listener thread: {e}")
        finally:
            self.cleanup()
    
    def stop(self):
        """Stop the message loop"""
        self.running = False
        if self.hwnd:
            # Post WM_QUIT to exit the message loop
            import win32gui
            try:
                win32gui.PostMessage(self.hwnd, win32con.WM_QUIT, 0, 0)
            except Exception as e:
                logger.error(f"Error posting quit message: {e}")
    
    def cleanup(self):
        """Clean up the message window"""
        if self.hwnd:
            import win32gui
            try:
                win32gui.DestroyWindow(self.hwnd)
            except Exception as e:
                logger.error(f"Error destroying window: {e}")
            self.hwnd = None
            logger.info("Hotkey listener cleaned up")


class HotkeyManager(QObject):
    """Manages global hotkey registration and handling"""
    
    hotkey_triggered = pyqtSignal(str, str)  # script_name, hotkey_string
    registration_failed = pyqtSignal(str, str)  # hotkey_string, error_message
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.listener = None
        self.hotkeys: Dict[int, Tuple[str, str]] = {}  # ID -> (script_name, hotkey_string)
        self.registered_combos: Set[str] = set()  # Track registered combinations
        self.next_id = 1
        self._lock = threading.Lock()
        
        logger.info("HotkeyManager initialized")
    
    def start(self):
        """Start the hotkey listener thread"""
        if self.listener is None or not self.listener.isRunning():
            self.listener = HotkeyListener()
            self.listener.hotkey_triggered.connect(self._on_hotkey_triggered)
            self.listener.start()
            
            # Wait for hwnd to be available
            import time
            for _ in range(10):
                if self.listener.hwnd:
                    break
                time.sleep(0.1)
            
            logger.info("HotkeyManager started")
    
    def stop(self):
        """Stop the hotkey listener and unregister all hotkeys"""
        logger.info("Stopping HotkeyManager...")
        
        # Unregister all hotkeys
        self.unregister_all()
        
        # Stop listener thread
        if self.listener:
            self.listener.stop()
            self.listener.wait(2000)  # Wait up to 2 seconds
            self.listener = None
        
        logger.info("HotkeyManager stopped")
    
    def parse_hotkey_string(self, hotkey_string: str) -> Tuple[int, int]:
        """
        Parse a hotkey string like 'Ctrl+Alt+X' into modifier flags and virtual key code
        
        Returns: (modifiers, vk_code) or (0, 0) if invalid
        """
        parts = [p.strip().upper() for p in hotkey_string.upper().split('+')]
        
        if not parts:
            return 0, 0
        
        modifiers = 0
        key = None
        
        for part in parts:
            if part in ('CTRL', 'CONTROL'):
                modifiers |= MOD_CONTROL
            elif part == 'ALT':
                modifiers |= MOD_ALT
            elif part == 'SHIFT':
                modifiers |= MOD_SHIFT
            elif part in ('WIN', 'WINDOWS', 'SUPER'):
                modifiers |= MOD_WIN
            else:
                # This should be the actual key
                if key is None:
                    key = part
                else:
                    # Multiple non-modifier keys - invalid
                    logger.warning(f"Invalid hotkey string: {hotkey_string}")
                    return 0, 0
        
        if key is None:
            logger.warning(f"No key specified in hotkey string: {hotkey_string}")
            return 0, 0
        
        # Get virtual key code
        vk_code = VK_CODES.get(key, 0)
        if vk_code == 0:
            # Try single character
            if len(key) == 1:
                vk_code = ord(key)
            else:
                logger.warning(f"Unknown key: {key}")
                return 0, 0
        
        # Add no-repeat flag to prevent key repeat
        modifiers |= MOD_NOREPEAT
        
        return modifiers, vk_code
    
    def is_hotkey_available(self, hotkey_string: str) -> bool:
        """Check if a hotkey combination is available for registration"""
        normalized = self.normalize_hotkey_string(hotkey_string)
        
        # Check if already registered
        if normalized in self.registered_combos:
            return False
        
        # Check if it's a reserved combination
        if self.is_reserved_hotkey(hotkey_string):
            return False
        
        return True
    
    def is_reserved_hotkey(self, hotkey_string: str) -> bool:
        """Check if a hotkey combination is system-reserved"""
        parts = set(p.strip().upper() for p in hotkey_string.upper().split('+'))
        
        # Remove modifier duplicates and normalize
        normalized_parts = set()
        for part in parts:
            if part in ('CTRL', 'CONTROL'):
                normalized_parts.add('CTRL')
            elif part in ('WIN', 'WINDOWS', 'SUPER'):
                normalized_parts.add('WIN')
            else:
                normalized_parts.add(part)
        
        # Check against reserved combinations
        for reserved in RESERVED_HOTKEYS:
            if set(reserved) == normalized_parts:
                return True
        
        return False
    
    def normalize_hotkey_string(self, hotkey_string: str) -> str:
        """Normalize a hotkey string for consistent comparison"""
        parts = []
        hotkey_upper = hotkey_string.upper()
        
        # Extract modifiers in consistent order
        if 'CTRL' in hotkey_upper or 'CONTROL' in hotkey_upper:
            parts.append('Ctrl')
        if 'ALT' in hotkey_upper:
            parts.append('Alt')
        if 'SHIFT' in hotkey_upper:
            parts.append('Shift')
        if 'WIN' in hotkey_upper or 'WINDOWS' in hotkey_upper or 'SUPER' in hotkey_upper:
            parts.append('Win')
        
        # Extract the main key
        for part in hotkey_string.split('+'):
            part = part.strip()
            part_upper = part.upper()
            if part_upper not in ('CTRL', 'CONTROL', 'ALT', 'SHIFT', 'WIN', 'WINDOWS', 'SUPER'):
                parts.append(part_upper)
                break
        
        return '+'.join(parts)
    
    def register_hotkey(self, script_name: str, hotkey_string: str) -> bool:
        """
        Register a global hotkey for a script
        
        Returns: True if successful, False otherwise
        """
        if not self.listener or not self.listener.hwnd:
            logger.error("Hotkey listener not started")
            return False
        
        # Normalize the hotkey string
        normalized = self.normalize_hotkey_string(hotkey_string)
        
        # Check if available
        if not self.is_hotkey_available(normalized):
            error_msg = f"Hotkey {normalized} is already registered or reserved"
            logger.warning(error_msg)
            self.registration_failed.emit(normalized, error_msg)
            return False
        
        # Parse the hotkey string
        modifiers, vk_code = self.parse_hotkey_string(hotkey_string)
        if modifiers == 0 and vk_code == 0:
            error_msg = f"Invalid hotkey format: {hotkey_string}"
            logger.error(error_msg)
            self.registration_failed.emit(hotkey_string, error_msg)
            return False
        
        with self._lock:
            hotkey_id = self.next_id
            self.next_id += 1
            
            # Attempt to register with Windows
            try:
                import win32gui
                win32gui.RegisterHotKey(
                    self.listener.hwnd, hotkey_id, modifiers, vk_code
                )
                
                # If we get here, registration was successful
                self.hotkeys[hotkey_id] = (script_name, normalized)
                self.registered_combos.add(normalized)
                logger.info(f"Registered hotkey {normalized} for script {script_name} (ID: {hotkey_id})")
                return True
                    
            except Exception as e:
                error_msg = str(e)
                
                # Check if it's because the hotkey is already registered
                if "already registered" in error_msg.lower() or "1409" in error_msg:
                    error_msg = f"Hotkey {normalized} is already registered by another application"
                else:
                    error_msg = f"Failed to register hotkey {normalized}: {error_msg}"
                
                logger.error(error_msg)
                self.registration_failed.emit(normalized, error_msg)
                return False
    
    def unregister_hotkey(self, script_name: str) -> bool:
        """Unregister a hotkey for a script"""
        if not self.listener or not self.listener.hwnd:
            return False
        
        with self._lock:
            # Find the hotkey ID for this script
            hotkey_id = None
            hotkey_string = None
            
            for hid, (sname, hstring) in self.hotkeys.items():
                if sname == script_name:
                    hotkey_id = hid
                    hotkey_string = hstring
                    break
            
            if hotkey_id is None:
                logger.warning(f"No hotkey registered for script {script_name}")
                return False
            
            # Unregister with Windows
            try:
                import win32gui
                win32gui.UnregisterHotKey(self.listener.hwnd, hotkey_id)
                
                # If we get here, unregistration was successful
                del self.hotkeys[hotkey_id]
                self.registered_combos.discard(hotkey_string)
                logger.info(f"Unregistered hotkey for script {script_name}")
                return True
                    
            except Exception as e:
                logger.error(f"Exception unregistering hotkey for {script_name}: {e}")
                return False
    
    def unregister_all(self):
        """Unregister all hotkeys"""
        if not self.listener or not self.listener.hwnd:
            return
        
        import win32gui
        with self._lock:
            for hotkey_id in list(self.hotkeys.keys()):
                try:
                    win32gui.UnregisterHotKey(self.listener.hwnd, hotkey_id)
                except Exception as e:
                    logger.error(f"Error unregistering hotkey {hotkey_id}: {e}")
            
            self.hotkeys.clear()
            self.registered_combos.clear()
            logger.info("All hotkeys unregistered")
    
    def get_registered_hotkeys(self) -> Dict[str, str]:
        """Get all registered hotkeys as script_name -> hotkey_string mapping"""
        with self._lock:
            return {script_name: hotkey_string 
                    for script_name, hotkey_string in self.hotkeys.values()}
    
    def _on_hotkey_triggered(self, hotkey_id: int):
        """Handle hotkey trigger from listener thread"""
        with self._lock:
            if hotkey_id in self.hotkeys:
                script_name, hotkey_string = self.hotkeys[hotkey_id]
                logger.info(f"Hotkey {hotkey_string} triggered for script {script_name}")
                self.hotkey_triggered.emit(script_name, hotkey_string)
            else:
                logger.warning(f"Unknown hotkey ID triggered: {hotkey_id}")
    
    def validate_hotkey_string(self, hotkey_string: str) -> Tuple[bool, str]:
        """
        Validate a hotkey string
        
        Returns: (is_valid, error_message)
        """
        if not hotkey_string or not hotkey_string.strip():
            return False, "Hotkey cannot be empty"
        
        # Check format
        modifiers, vk_code = self.parse_hotkey_string(hotkey_string)
        if modifiers == 0 and vk_code == 0:
            return False, "Invalid hotkey format"
        
        # Check if reserved
        if self.is_reserved_hotkey(hotkey_string):
            return False, "This hotkey combination is reserved by the system"
        
        # Check if already registered
        normalized = self.normalize_hotkey_string(hotkey_string)
        if normalized in self.registered_combos:
            return False, "This hotkey is already registered"
        
        return True, ""