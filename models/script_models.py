"""
Script Models - Manage script discovery, execution, and state.

These models handle all script-related business logic while remaining
UI-agnostic and providing signals for state changes.
"""
import logging
from typing import List, Dict, Any, Optional, Set
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal, QTimer

from core.script_loader import ScriptLoader
from core.script_analyzer import ScriptInfo
from core.settings import SettingsManager
from core.hotkey_registry import HotkeyRegistry

logger = logging.getLogger('Models.Scripts')


class ScriptCollectionModel(QObject):
    """
    Model for managing the collection of available scripts.
    
    Handles script discovery, filtering, and maintains the list
    of available scripts for execution.
    """
    
    # Signals emitted when script collection changes
    scripts_discovered = pyqtSignal(list)  # List[ScriptInfo]
    scripts_filtered = pyqtSignal(list)  # List[ScriptInfo] after filtering
    script_added = pyqtSignal(object)  # ScriptInfo
    script_removed = pyqtSignal(str)  # script name
    script_enabled = pyqtSignal(str)  # script name
    script_disabled = pyqtSignal(str)  # script name
    external_script_added = pyqtSignal(str, str)  # name, path
    external_script_removed = pyqtSignal(str)  # name
    
    def __init__(self, scripts_directory: str = "scripts"):
        super().__init__()
        self._script_loader = ScriptLoader(scripts_directory)
        self._settings = SettingsManager()
        
        self._all_scripts: List[ScriptInfo] = []
        self._available_scripts: List[ScriptInfo] = []
        self._disabled_scripts: Set[str] = set()
        self._external_scripts: Dict[str, str] = {}
        
        logger.info("ScriptCollectionModel initialized")
    
    def discover_scripts(self) -> List[ScriptInfo]:
        """Discover all available scripts"""
        logger.info("Discovering scripts...")
        
        try:
            self._all_scripts = self._script_loader.discover_scripts()
            self.scripts_discovered.emit(self._all_scripts)
            
            # Apply filtering
            self._update_available_scripts()
            
            logger.info(f"Discovered {len(self._all_scripts)} scripts, "
                       f"{len(self._available_scripts)} available after filtering")
            
            return self._available_scripts
        except Exception as e:
            logger.error(f"Error discovering scripts: {e}")
            return []
    
    def refresh_scripts(self) -> List[ScriptInfo]:
        """Refresh the script collection"""
        logger.info("Refreshing scripts...")
        return self.discover_scripts()
    
    def get_all_scripts(self) -> List[ScriptInfo]:
        """Get all discovered scripts (including disabled)"""
        return self._all_scripts.copy()
    
    def get_available_scripts(self) -> List[ScriptInfo]:
        """Get currently available (enabled) scripts"""
        return self._available_scripts.copy()
    
    def get_script_by_name(self, name: str) -> Optional[ScriptInfo]:
        """Get script info by name.

        Accepts either the display name (e.g., "Display Toggle") or the file stem
        identifier used for hotkeys and settings (e.g., "display_toggle").
        """
        # First, try exact display name match
        for script in self._all_scripts:
            if script.display_name == name:
                return script

        # Fallback: try file stem match (hotkey/settings use stems)
        lname = (name or "").strip().lower()
        for script in self._all_scripts:
            try:
                if script.file_path.stem.lower() == lname:
                    return script
            except Exception:
                pass
        return None
    
    def is_script_disabled(self, script_name: str) -> bool:
        """Check if a script is disabled"""
        return script_name in self._disabled_scripts
    
    def is_external_script(self, script_name: str) -> bool:
        """Check if a script is external"""
        return script_name in self._external_scripts
    
    def disable_script(self, script_name: str):
        """Disable a native script"""
        script = self.get_script_by_name(script_name)
        if script and not self.is_external_script(script_name):
            self._disabled_scripts.add(script_name)
            self._settings.add_disabled_script(script_name)
            self._update_available_scripts()
            self.script_disabled.emit(script_name)
            logger.info(f"Disabled script: {script_name}")
    
    def enable_script(self, script_name: str):
        """Enable a previously disabled script"""
        if script_name in self._disabled_scripts:
            self._disabled_scripts.remove(script_name)
            self._settings.remove_disabled_script(script_name)
            self._update_available_scripts()
            self.script_enabled.emit(script_name)
            logger.info(f"Enabled script: {script_name}")
    
    def add_external_script(self, script_name: str, script_path: str) -> bool:
        """Add an external script"""
        try:
            # Validate the script path
            if not self._settings.validate_external_script_path(script_path):
                logger.error(f"Invalid external script path: {script_path}")
                return False
            
            # Add to settings
            self._settings.add_external_script(script_name, script_path)
            self._external_scripts[script_name] = script_path
            
            # Refresh scripts to include the new one
            self.refresh_scripts()
            
            self.external_script_added.emit(script_name, script_path)
            logger.info(f"Added external script: {script_name} -> {script_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding external script {script_name}: {e}")
            return False
    
    def remove_external_script(self, script_name: str):
        """Remove an external script"""
        if script_name in self._external_scripts:
            script_path = self._external_scripts[script_name]
            
            # Remove from settings
            self._settings.remove_external_script(script_name)
            del self._external_scripts[script_name]
            
            # Refresh scripts to remove it from the collection
            self.refresh_scripts()
            
            self.external_script_removed.emit(script_name)
            logger.info(f"Removed external script: {script_name} -> {script_path}")
    
    def get_script_display_name(self, script_info: ScriptInfo) -> str:
        """Get display name for a script (may be customized)"""
        return self._script_loader.get_script_display_name(script_info)
    
    def _update_available_scripts(self):
        """Update the list of available scripts based on current filters"""
        # Load current settings
        self._disabled_scripts = set(self._settings.get_disabled_scripts())
        self._external_scripts = self._settings.get_external_scripts()
        
        # Filter scripts
        available = []
        for script_info in self._all_scripts:
            script_name = script_info.display_name
            is_external = script_name in self._external_scripts
            
            # Skip disabled native scripts (external scripts are never "disabled", only removed)
            if not is_external and script_name in self._disabled_scripts:
                continue
            
            # For external scripts, verify the path still exists
            if is_external:
                script_path = self._external_scripts.get(script_name)
                if not self._settings.validate_external_script_path(script_path):
                    continue
            
            available.append(script_info)
        
        self._available_scripts = available
        self.scripts_filtered.emit(self._available_scripts)


class ScriptExecutionModel(QObject):
    """
    Model for managing script execution and tracking execution state.
    
    Handles script execution, tracks results, and maintains execution history.
    """
    
    # Signals emitted during script execution
    script_execution_started = pyqtSignal(str)  # script name
    script_execution_completed = pyqtSignal(str, dict)  # script name, result
    script_execution_failed = pyqtSignal(str, str)  # script name, error
    script_status_changed = pyqtSignal(str, str)  # script name, status
    
    def __init__(self, script_collection: ScriptCollectionModel):
        super().__init__()
        self._script_collection = script_collection
        self._script_loader = script_collection._script_loader
        self._settings = SettingsManager()
        
        self._execution_results: Dict[str, Dict[str, Any]] = {}
        self._script_statuses: Dict[str, str] = {}
        
        # Setup status refresh timer
        self._status_timer = QTimer()
        self._status_timer.timeout.connect(self._refresh_script_statuses)
        refresh_interval = self._settings.get_status_refresh_seconds() * 1000
        self._status_timer.start(refresh_interval)
        
        logger.info("ScriptExecutionModel initialized")
    
    def execute_script(self, script_name: str, arguments: Optional[Dict[str, Any]] = None) -> bool:
        """Execute a script with optional arguments"""
        try:
            script_info = self._script_collection.get_script_by_name(script_name)
            if not script_info:
                self.script_execution_failed.emit(script_name, f"Script not found: {script_name}")
                return False
            
            logger.info(f"Executing script: {script_name}")
            self.script_execution_started.emit(script_name)
            
            # Determine script key for execution
            if self._script_collection.is_external_script(script_name):
                script_key = script_name  # Use display name for external scripts
            else:
                script_key = script_info.file_path.stem  # Use file stem for default scripts
            
            # Execute the script
            result = self._script_loader.execute_script(script_key, arguments or {})
            
            # Store result
            self._execution_results[script_name] = result
            
            if result.get('success', False):
                self.script_execution_completed.emit(script_name, result)
                logger.info(f"Script execution completed: {script_name}")
            else:
                error_msg = result.get('message', 'Unknown error')
                self.script_execution_failed.emit(script_name, error_msg)
                logger.error(f"Script execution failed: {script_name} - {error_msg}")
            
            return result.get('success', False)
            
        except Exception as e:
            error_msg = f"Error executing script {script_name}: {str(e)}"
            logger.error(error_msg)
            self.script_execution_failed.emit(script_name, str(e))
            return False
    
    def execute_script_with_preset(self, script_name: str, preset_name: str) -> bool:
        """Execute a script with a specific preset configuration"""
        try:
            script_info = self._script_collection.get_script_by_name(script_name)
            if not script_info:
                self.script_execution_failed.emit(script_name, f"Script not found: {script_name}")
                return False
            
            # Get script key for settings lookup
            script_key = script_info.file_path.stem
            preset_args = self._settings.get_preset_arguments(script_key, preset_name)
            
            logger.info(f"Executing script {script_name} with preset '{preset_name}': {preset_args}")
            return self.execute_script(script_name, preset_args)
            
        except Exception as e:
            error_msg = f"Error executing script {script_name} with preset {preset_name}: {str(e)}"
            logger.error(error_msg)
            self.script_execution_failed.emit(script_name, str(e))
            return False
    
    def get_script_status(self, script_name: str) -> str:
        """Get current status of a script"""
        if script_name not in self._script_statuses:
            # Determine script key for status lookup
            script_info = self._script_collection.get_script_by_name(script_name)
            if script_info:
                if self._script_collection.is_external_script(script_name):
                    script_key = script_name
                else:
                    script_key = script_info.file_path.stem
                
                status = self._script_loader.get_script_status(script_key)
                self._script_statuses[script_name] = status or "Ready"
        
        return self._script_statuses.get(script_name, "Unknown")
    
    def get_last_execution_result(self, script_name: str) -> Optional[Dict[str, Any]]:
        """Get the last execution result for a script"""
        return self._execution_results.get(script_name)
    
    def should_show_notifications_for_script(self, script_name: str) -> bool:
        """Check if notifications should be shown for a script"""
        script_info = self._script_collection.get_script_by_name(script_name)
        if script_info:
            script_key = script_info.file_path.stem
            return self._settings.should_show_script_notifications(script_key)
        return True
    
    def _refresh_script_statuses(self):
        """Refresh status for all scripts"""
        try:
            for script in self._script_collection.get_available_scripts():
                script_name = script.display_name
                old_status = self._script_statuses.get(script_name, "Unknown")
                new_status = self.get_script_status(script_name)
                
                if old_status != new_status:
                    self._script_statuses[script_name] = new_status
                    self.script_status_changed.emit(script_name, new_status)
                    
        except Exception as e:
            logger.debug(f"Error refreshing script statuses: {e}")


class HotkeyModel(QObject):
    """
    Model for managing hotkey assignments and registrations.
    
    Handles hotkey configuration and provides hotkey-to-script mappings.
    """
    
    # Signals for hotkey changes
    hotkey_registered = pyqtSignal(str, str)  # script name, hotkey
    hotkey_unregistered = pyqtSignal(str)  # script name
    hotkey_registration_failed = pyqtSignal(str, str, str)  # script name, hotkey, error
    hotkeys_changed = pyqtSignal()  # General hotkey configuration changed
    
    def __init__(self):
        super().__init__()
        self._settings = SettingsManager()
        self._hotkey_registry = HotkeyRegistry(self._settings)
        
        self._script_hotkeys: Dict[str, str] = {}
        self._load_hotkeys()
        
        logger.info("HotkeyModel initialized")
    
    def get_hotkey_for_script(self, script_name: str) -> Optional[str]:
        """Get the hotkey assigned to a script"""
        return self._script_hotkeys.get(script_name)
    
    def set_hotkey_for_script(self, script_name: str, hotkey: str):
        """Set hotkey for a script"""
        try:
            # Add the hotkey using the registry
            success, error_msg = self._hotkey_registry.add_hotkey(script_name, hotkey)
            
            if success:
                # Update local cache
                old_hotkey = self._script_hotkeys.get(script_name)
                self._script_hotkeys[script_name] = hotkey
                
                self.hotkey_registered.emit(script_name, hotkey)
                self.hotkeys_changed.emit()
                
                logger.info(f"Set hotkey for {script_name}: {hotkey}")
            else:
                self.hotkey_registration_failed.emit(script_name, hotkey, error_msg)
                logger.error(f"Failed to set hotkey for {script_name}: {error_msg}")
            
        except Exception as e:
            logger.error(f"Error setting hotkey for {script_name}: {e}")
            self.hotkey_registration_failed.emit(script_name, hotkey, str(e))
    
    def remove_hotkey_for_script(self, script_name: str):
        """Remove hotkey assignment for a script"""
        if script_name in self._script_hotkeys:
            # Remove using the registry
            if self._hotkey_registry.remove_hotkey(script_name):
                del self._script_hotkeys[script_name]
                
                self.hotkey_unregistered.emit(script_name)
                self.hotkeys_changed.emit()
                
                logger.info(f"Removed hotkey for {script_name}")
    
    def get_all_hotkeys(self) -> Dict[str, str]:
        """Get all script-to-hotkey mappings"""
        return self._script_hotkeys.copy()
    
    def is_hotkey_available(self, hotkey: str, exclude_script: Optional[str] = None) -> bool:
        """Check if a hotkey is available (not assigned to another script)"""
        existing_script = self._hotkey_registry.get_script_for_hotkey(hotkey)
        return existing_script is None or existing_script == exclude_script
    
    def _load_hotkeys(self):
        """Load hotkeys from settings"""
        try:
            # Get all hotkey settings
            all_hotkeys = self._hotkey_registry.get_all_mappings()
            self._script_hotkeys = all_hotkeys
            logger.info(f"Loaded {len(all_hotkeys)} hotkey assignments")
        except Exception as e:
            logger.error(f"Error loading hotkeys: {e}")
            self._script_hotkeys = {}
