"""
Schedule Controller - Manages schedule operations and coordination.

This controller handles schedule management, coordinates between
schedule models and views, and manages the scheduler lifecycle.
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QMessageBox

from models.schedule_models import ScheduleModel, ScheduleExecutionHistoryModel
from views.schedule_config_view import ScheduleConfigView
from core.scheduler_manager import SchedulerManager, ScheduleConfig

logger = logging.getLogger('Controllers.Schedule')


class ScheduleController(QObject):
    """
    Controller for managing script scheduling operations.
    
    This controller:
    - Handles schedule creation, modification, and deletion
    - Manages schedule configuration UI
    - Coordinates between scheduler and UI components
    - Provides schedule status and history
    """
    
    # Signals for schedule events
    schedule_created = pyqtSignal(str, dict)  # script_name, config
    schedule_updated = pyqtSignal(str, dict)  # script_name, config
    schedule_removed = pyqtSignal(str)  # script_name
    schedule_status_changed = pyqtSignal(str, bool)  # script_name, enabled
    
    def __init__(self, scheduler_manager: SchedulerManager, 
                 script_execution_model=None,
                 settings_manager=None):
        super().__init__()
        
        self._scheduler = scheduler_manager
        self._script_execution = script_execution_model
        self._settings = settings_manager
        
        # Initialize models
        self._schedule_model = ScheduleModel(scheduler_manager, settings_manager)
        self._history_model = ScheduleExecutionHistoryModel(scheduler_manager)
        
        # Connect model signals
        self._setup_model_connections()
        
        logger.info("ScheduleController initialized")
    
    def _setup_model_connections(self):
        """Set up connections between models and controller."""
        # Connect schedule model signals
        self._schedule_model.schedule_added.connect(self.schedule_created.emit)
        self._schedule_model.schedule_updated.connect(self.schedule_updated.emit)
        self._schedule_model.schedule_removed.connect(self.schedule_removed.emit)
        self._schedule_model.schedule_enabled.connect(
            lambda name: self.schedule_status_changed.emit(name, True))
        self._schedule_model.schedule_disabled.connect(
            lambda name: self.schedule_status_changed.emit(name, False))
    
    def show_schedule_dialog(self, script_name: str, script_info: Optional[Dict] = None,
                            parent=None) -> bool:
        """Show schedule configuration dialog for a script."""
        try:
            # Get existing schedule if any
            existing_schedule = self._schedule_model.get_schedule(script_name)
            
            # Create and show dialog
            dialog = ScheduleConfigView(
                script_name=script_name,
                script_info=script_info,
                existing_schedule=existing_schedule,
                parent=parent
            )
            
            # Connect dialog signals
            dialog.schedule_created.connect(self._handle_schedule_created)
            dialog.schedule_updated.connect(self._handle_schedule_updated)
            
            # Show dialog and return result
            return dialog.exec() == 1  # QDialog.DialogCode.Accepted
            
        except Exception as e:
            logger.error(f"Error showing schedule dialog: {e}")
            if parent:
                QMessageBox.critical(parent, "Error", 
                                    f"Failed to open schedule configuration:\n{str(e)}")
            return False
    
    def create_schedule(self, script_name: str, schedule_type: str,
                       **kwargs) -> bool:
        """Create a new schedule for a script."""
        try:
            success = self._schedule_model.add_schedule(
                script_name, schedule_type, **kwargs)
            
            if success:
                logger.info(f"Schedule created for {script_name}")
            else:
                logger.warning(f"Failed to create schedule for {script_name}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error creating schedule for {script_name}: {e}")
            return False
    
    def update_schedule(self, script_name: str, **kwargs) -> bool:
        """Update an existing schedule."""
        try:
            success = self._schedule_model.update_schedule(script_name, **kwargs)
            
            if success:
                logger.info(f"Schedule updated for {script_name}")
            else:
                logger.warning(f"Failed to update schedule for {script_name}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error updating schedule for {script_name}: {e}")
            return False
    
    def remove_schedule(self, script_name: str) -> bool:
        """Remove a schedule for a script."""
        try:
            success = self._schedule_model.remove_schedule(script_name)
            
            if success:
                logger.info(f"Schedule removed for {script_name}")
            else:
                logger.warning(f"Failed to remove schedule for {script_name}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error removing schedule for {script_name}: {e}")
            return False
    
    def enable_schedule(self, script_name: str) -> bool:
        """Enable a schedule."""
        try:
            return self._schedule_model.enable_schedule(script_name)
        except Exception as e:
            logger.error(f"Error enabling schedule for {script_name}: {e}")
            return False
    
    def disable_schedule(self, script_name: str) -> bool:
        """Disable a schedule."""
        try:
            return self._schedule_model.disable_schedule(script_name)
        except Exception as e:
            logger.error(f"Error disabling schedule for {script_name}: {e}")
            return False
    
    def toggle_schedule(self, script_name: str) -> bool:
        """Toggle schedule enabled state."""
        try:
            if self._schedule_model.is_schedule_enabled(script_name):
                return self.disable_schedule(script_name)
            else:
                return self.enable_schedule(script_name)
        except Exception as e:
            logger.error(f"Error toggling schedule for {script_name}: {e}")
            return False
    
    def has_schedule(self, script_name: str) -> bool:
        """Check if a script has a schedule."""
        return self._schedule_model.has_schedule(script_name)
    
    def is_schedule_enabled(self, script_name: str) -> bool:
        """Check if a schedule is enabled."""
        return self._schedule_model.is_schedule_enabled(script_name)
    
    def get_schedule(self, script_name: str) -> Optional[Dict[str, Any]]:
        """Get schedule configuration for a script."""
        return self._schedule_model.get_schedule(script_name)
    
    def get_all_schedules(self) -> List[Dict[str, Any]]:
        """Get all schedule configurations."""
        return self._schedule_model.get_all_schedules()
    
    def get_next_run_time(self, script_name: str) -> Optional[datetime]:
        """Get the next run time for a scheduled script."""
        return self._schedule_model.get_next_run_time(script_name)
    
    def get_next_runs(self, script_name: str, count: int = 5) -> List[datetime]:
        """Get the next N run times for a scheduled script."""
        return self._schedule_model.get_next_runs(script_name, count)
    
    def get_schedule_status_text(self, script_name: str) -> str:
        """Get human-readable schedule status text."""
        try:
            if not self.has_schedule(script_name):
                return "No schedule"
            
            if not self.is_schedule_enabled(script_name):
                return "Schedule disabled"
            
            next_run = self.get_next_run_time(script_name)
            if next_run:
                # Calculate time until next run
                now = datetime.now()
                delta = next_run - now
                
                if delta.days > 0:
                    return f"Next run in {delta.days} day(s)"
                elif delta.seconds > 3600:
                    hours = delta.seconds // 3600
                    return f"Next run in {hours} hour(s)"
                elif delta.seconds > 60:
                    minutes = delta.seconds // 60
                    return f"Next run in {minutes} minute(s)"
                else:
                    return f"Next run in {delta.seconds} second(s)"
            else:
                return "Schedule active"
                
        except Exception as e:
            logger.error(f"Error getting schedule status for {script_name}: {e}")
            return "Unknown"
    
    def get_execution_history(self, script_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get execution history for a scheduled script."""
        return self._history_model.get_execution_history(script_name, limit)
    
    def get_execution_stats(self, script_name: str) -> Dict[str, Any]:
        """Get execution statistics for a scheduled script."""
        return self._history_model.get_execution_stats(script_name)
    
    def clear_execution_history(self, script_name: str):
        """Clear execution history for a script."""
        self._history_model.clear_history(script_name)
    
    def start_scheduler(self):
        """Start the scheduler service."""
        try:
            self._scheduler.start()
            logger.info("Scheduler service started")
        except Exception as e:
            logger.error(f"Error starting scheduler service: {e}")
    
    def stop_scheduler(self):
        """Stop the scheduler service."""
        try:
            self._scheduler.stop()
            logger.info("Scheduler service stopped")
        except Exception as e:
            logger.error(f"Error stopping scheduler service: {e}")
    
    def create_quick_schedule(self, script_name: str, preset: str) -> bool:
        """Create a schedule using a preset configuration."""
        try:
            preset_configs = {
                'every_5_min': {'schedule_type': 'interval', 'interval_minutes': 5},
                'every_30_min': {'schedule_type': 'interval', 'interval_minutes': 30},
                'hourly': {'schedule_type': 'interval', 'interval_hours': 1},
                'daily_9am': {'schedule_type': 'daily', 'time_of_day': '09:00'},
                'daily_6pm': {'schedule_type': 'daily', 'time_of_day': '18:00'},
                'weekdays_9am': {
                    'schedule_type': 'weekly',
                    'days_of_week': [0, 1, 2, 3, 4],
                    'time_of_day': '09:00'
                }
            }
            
            if preset not in preset_configs:
                logger.warning(f"Unknown preset: {preset}")
                return False
            
            config = preset_configs[preset]
            return self.create_schedule(script_name, **config)
            
        except Exception as e:
            logger.error(f"Error creating quick schedule: {e}")
            return False
    
    def _handle_schedule_created(self, script_name: str, config: Dict[str, Any]):
        """Handle schedule creation from dialog."""
        try:
            # Extract schedule type and create schedule
            schedule_type = config.pop('schedule_type')
            success = self.create_schedule(script_name, schedule_type, **config)
            
            if not success:
                logger.error(f"Failed to create schedule for {script_name}")
                
        except Exception as e:
            logger.error(f"Error handling schedule creation: {e}")
    
    def _handle_schedule_updated(self, script_name: str, config: Dict[str, Any]):
        """Handle schedule update from dialog."""
        try:
            # Remove script_name from config as it's already a parameter
            config.pop('script_name', None)
            
            success = self.update_schedule(script_name, **config)
            
            if not success:
                logger.error(f"Failed to update schedule for {script_name}")
                
        except Exception as e:
            logger.error(f"Error handling schedule update: {e}")