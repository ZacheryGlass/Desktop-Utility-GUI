"""
Schedule Models - Data models for script scheduling functionality.

These models manage schedule configurations, execution history,
and provide interfaces for schedule-related operations.
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from PyQt6.QtCore import QObject, pyqtSignal

from core.settings import SettingsManager
from core.scheduler_manager import SchedulerManager, ScheduleConfig

logger = logging.getLogger('Models.Schedule')


class ScheduleModel(QObject):
    """
    Model for managing script schedules.
    
    This model handles schedule configurations and provides
    an interface between the scheduler and the UI.
    """
    
    # Signals for schedule changes
    schedule_added = pyqtSignal(str, dict)  # script_name, config
    schedule_removed = pyqtSignal(str)  # script_name
    schedule_updated = pyqtSignal(str, dict)  # script_name, config
    schedule_enabled = pyqtSignal(str)  # script_name
    schedule_disabled = pyqtSignal(str)  # script_name
    schedules_loaded = pyqtSignal(list)  # List of schedule configs
    
    def __init__(self, scheduler_manager: SchedulerManager, settings: SettingsManager):
        super().__init__()
        self._scheduler = scheduler_manager
        self._settings = settings
        
        # Connect scheduler signals
        self._scheduler.schedule_added.connect(self.schedule_added.emit)
        self._scheduler.schedule_removed.connect(self.schedule_removed.emit)
        self._scheduler.schedule_updated.connect(self.schedule_updated.emit)
        
        logger.info("ScheduleModel initialized")
    
    def add_schedule(self, script_name: str, schedule_type: str, **kwargs) -> bool:
        """Add a new schedule for a script."""
        try:
            config = ScheduleConfig(
                script_name=script_name,
                schedule_type=schedule_type,
                **kwargs
            )
            
            success = self._scheduler.add_schedule(config)
            if success:
                logger.info(f"Schedule added for {script_name}: {schedule_type}")
            return success
            
        except Exception as e:
            logger.error(f"Error adding schedule for {script_name}: {e}")
            return False
    
    def remove_schedule(self, script_name: str) -> bool:
        """Remove a schedule for a script."""
        return self._scheduler.remove_schedule(script_name)
    
    def update_schedule(self, script_name: str, **kwargs) -> bool:
        """Update an existing schedule."""
        try:
            existing = self._scheduler.get_schedule(script_name)
            if not existing:
                logger.warning(f"No existing schedule found for {script_name}")
                return False
            
            # Update the configuration
            for key, value in kwargs.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            
            success = self._scheduler.update_schedule(existing)
            if success:
                self.schedule_updated.emit(script_name, existing.to_dict())
            return success
            
        except Exception as e:
            logger.error(f"Error updating schedule for {script_name}: {e}")
            return False
    
    def enable_schedule(self, script_name: str) -> bool:
        """Enable a schedule."""
        success = self._scheduler.enable_schedule(script_name)
        if success:
            self.schedule_enabled.emit(script_name)
        return success
    
    def disable_schedule(self, script_name: str) -> bool:
        """Disable a schedule."""
        success = self._scheduler.disable_schedule(script_name)
        if success:
            self.schedule_disabled.emit(script_name)
        return success
    
    def get_schedule(self, script_name: str) -> Optional[Dict[str, Any]]:
        """Get schedule configuration for a script."""
        config = self._scheduler.get_schedule(script_name)
        return config.to_dict() if config else None
    
    def get_all_schedules(self) -> List[Dict[str, Any]]:
        """Get all schedule configurations."""
        schedules = self._scheduler.get_all_schedules()
        return [config.to_dict() for config in schedules.values()]
    
    def has_schedule(self, script_name: str) -> bool:
        """Check if a script has a schedule."""
        return self._scheduler.get_schedule(script_name) is not None
    
    def is_schedule_enabled(self, script_name: str) -> bool:
        """Check if a schedule is enabled."""
        config = self._scheduler.get_schedule(script_name)
        return config.enabled if config else False
    
    def get_next_run_time(self, script_name: str) -> Optional[datetime]:
        """Get the next run time for a scheduled script."""
        return self._scheduler.get_next_run_time(script_name)
    
    def get_next_runs(self, script_name: str, count: int = 5) -> List[datetime]:
        """Get the next N run times for a scheduled script."""
        return self._scheduler.get_next_runs(script_name, count)
    
    def validate_cron_expression(self, expression: str) -> tuple[bool, str]:
        """Validate a cron expression."""
        try:
            from apscheduler.triggers.cron import CronTrigger
            CronTrigger.from_crontab(expression)
            return True, "Valid cron expression"
        except Exception as e:
            return False, str(e)
    
    def create_interval_schedule(self, script_name: str, seconds: int = 0, 
                                minutes: int = 0, hours: int = 0, 
                                days: int = 0, arguments: Dict[str, Any] = None) -> bool:
        """Create an interval-based schedule."""
        return self.add_schedule(
            script_name=script_name,
            schedule_type='interval',
            interval_seconds=seconds if seconds > 0 else None,
            interval_minutes=minutes if minutes > 0 else None,
            interval_hours=hours if hours > 0 else None,
            interval_days=days if days > 0 else None,
            arguments=arguments or {}
        )
    
    def create_daily_schedule(self, script_name: str, time_of_day: str,
                            arguments: Dict[str, Any] = None) -> bool:
        """Create a daily schedule at a specific time."""
        return self.add_schedule(
            script_name=script_name,
            schedule_type='daily',
            time_of_day=time_of_day,
            arguments=arguments or {}
        )
    
    def create_weekly_schedule(self, script_name: str, days_of_week: List[int],
                             time_of_day: str, arguments: Dict[str, Any] = None) -> bool:
        """Create a weekly schedule on specific days."""
        return self.add_schedule(
            script_name=script_name,
            schedule_type='weekly',
            days_of_week=days_of_week,
            time_of_day=time_of_day,
            arguments=arguments or {}
        )
    
    def create_monthly_schedule(self, script_name: str, day_of_month: int,
                              time_of_day: str, arguments: Dict[str, Any] = None) -> bool:
        """Create a monthly schedule on a specific day."""
        return self.add_schedule(
            script_name=script_name,
            schedule_type='monthly',
            day_of_month=day_of_month,
            time_of_day=time_of_day,
            arguments=arguments or {}
        )
    
    def create_cron_schedule(self, script_name: str, cron_expression: str,
                           arguments: Dict[str, Any] = None) -> bool:
        """Create a cron-based schedule."""
        # Validate expression first
        valid, error = self.validate_cron_expression(cron_expression)
        if not valid:
            logger.error(f"Invalid cron expression: {error}")
            return False
        
        return self.add_schedule(
            script_name=script_name,
            schedule_type='cron',
            cron_expression=cron_expression,
            arguments=arguments or {}
        )
    
    def create_one_time_schedule(self, script_name: str, run_date: datetime,
                                arguments: Dict[str, Any] = None) -> bool:
        """Create a one-time schedule."""
        return self.add_schedule(
            script_name=script_name,
            schedule_type='once',
            run_date=run_date,
            arguments=arguments or {}
        )


class ScheduleExecutionHistoryModel(QObject):
    """
    Model for tracking schedule execution history.
    
    This model maintains a history of scheduled script executions
    for monitoring and debugging purposes.
    """
    
    # Signals for history events
    execution_added = pyqtSignal(str, dict)  # script_name, execution_data
    history_cleared = pyqtSignal(str)  # script_name
    
    def __init__(self, scheduler_manager: SchedulerManager):
        super().__init__()
        self._scheduler = scheduler_manager
        
        # Connect to scheduler execution signals
        self._scheduler.schedule_executed.connect(self._on_schedule_executed)
        self._scheduler.schedule_error.connect(self._on_schedule_error)
        self._scheduler.schedule_missed.connect(self._on_schedule_missed)
        
        logger.info("ScheduleExecutionHistoryModel initialized")
    
    def get_execution_history(self, script_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get execution history for a script."""
        return self._scheduler.get_execution_history(script_name, limit)
    
    def get_last_execution(self, script_name: str) -> Optional[Dict[str, Any]]:
        """Get the last execution record for a script."""
        history = self.get_execution_history(script_name, 1)
        return history[0] if history else None
    
    def get_execution_stats(self, script_name: str) -> Dict[str, Any]:
        """Get execution statistics for a script."""
        history = self.get_execution_history(script_name, 100)
        
        if not history:
            return {
                'total_runs': 0,
                'successful_runs': 0,
                'failed_runs': 0,
                'missed_runs': 0,
                'success_rate': 0.0,
                'last_run': None,
                'last_success': None,
                'last_failure': None
            }
        
        total = len(history)
        successful = sum(1 for h in history if h.get('result') == 'success')
        failed = sum(1 for h in history if h.get('result') == 'error')
        missed = sum(1 for h in history if h.get('result') == 'missed')
        
        last_run = history[-1].get('timestamp') if history else None
        last_success = None
        last_failure = None
        
        for h in reversed(history):
            if not last_success and h.get('result') == 'success':
                last_success = h.get('timestamp')
            if not last_failure and h.get('result') == 'error':
                last_failure = h.get('timestamp')
            if last_success and last_failure:
                break
        
        return {
            'total_runs': total,
            'successful_runs': successful,
            'failed_runs': failed,
            'missed_runs': missed,
            'success_rate': (successful / total * 100) if total > 0 else 0.0,
            'last_run': last_run,
            'last_success': last_success,
            'last_failure': last_failure
        }
    
    def clear_history(self, script_name: str):
        """Clear execution history for a script."""
        # This would need to be implemented in scheduler_manager
        # For now, emit the signal
        self.history_cleared.emit(script_name)
        logger.info(f"Cleared execution history for {script_name}")
    
    def _on_schedule_executed(self, script_name: str, result: Dict[str, Any]):
        """Handle schedule execution event."""
        execution_data = {
            'timestamp': datetime.now(),
            'result': 'success',
            'details': result
        }
        self.execution_added.emit(script_name, execution_data)
    
    def _on_schedule_error(self, script_name: str, error: str):
        """Handle schedule error event."""
        execution_data = {
            'timestamp': datetime.now(),
            'result': 'error',
            'error': error
        }
        self.execution_added.emit(script_name, execution_data)
    
    def _on_schedule_missed(self, script_name: str):
        """Handle missed schedule event."""
        execution_data = {
            'timestamp': datetime.now(),
            'result': 'missed'
        }
        self.execution_added.emit(script_name, execution_data)


class SchedulePresetModel(QObject):
    """
    Model for managing schedule presets.
    
    This model provides pre-configured schedule templates
    for common scheduling patterns.
    """
    
    # Common schedule presets
    PRESETS = {
        'every_5_minutes': {
            'name': 'Every 5 Minutes',
            'schedule_type': 'interval',
            'interval_minutes': 5
        },
        'every_30_minutes': {
            'name': 'Every 30 Minutes',
            'schedule_type': 'interval',
            'interval_minutes': 30
        },
        'hourly': {
            'name': 'Every Hour',
            'schedule_type': 'interval',
            'interval_hours': 1
        },
        'daily_morning': {
            'name': 'Daily at 9 AM',
            'schedule_type': 'daily',
            'time_of_day': '09:00'
        },
        'daily_evening': {
            'name': 'Daily at 6 PM',
            'schedule_type': 'daily',
            'time_of_day': '18:00'
        },
        'weekdays_morning': {
            'name': 'Weekdays at 9 AM',
            'schedule_type': 'weekly',
            'days_of_week': [0, 1, 2, 3, 4],  # Monday to Friday
            'time_of_day': '09:00'
        },
        'weekends': {
            'name': 'Weekends at Noon',
            'schedule_type': 'weekly',
            'days_of_week': [5, 6],  # Saturday and Sunday
            'time_of_day': '12:00'
        },
        'monthly_start': {
            'name': 'Monthly on 1st at 9 AM',
            'schedule_type': 'monthly',
            'day_of_month': 1,
            'time_of_day': '09:00'
        },
        'monthly_end': {
            'name': 'Monthly on Last Day',
            'schedule_type': 'monthly',
            'day_of_month': -1,  # Last day of month
            'time_of_day': '17:00'
        }
    }
    
    def __init__(self):
        super().__init__()
        logger.info("SchedulePresetModel initialized")
    
    def get_preset(self, preset_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific preset configuration."""
        return self.PRESETS.get(preset_id)
    
    def get_all_presets(self) -> Dict[str, Dict[str, Any]]:
        """Get all available presets."""
        return self.PRESETS.copy()
    
    def get_preset_names(self) -> List[tuple[str, str]]:
        """Get list of preset IDs and names."""
        return [(pid, preset['name']) for pid, preset in self.PRESETS.items()]
    
    def apply_preset(self, preset_id: str) -> Optional[Dict[str, Any]]:
        """Get preset configuration ready to apply."""
        preset = self.get_preset(preset_id)
        if preset:
            # Remove the name field as it's not needed for configuration
            config = preset.copy()
            config.pop('name', None)
            return config
        return None