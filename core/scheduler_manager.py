"""
Scheduler Manager - Handles time-based script execution scheduling.

This module manages scheduled script executions using APScheduler,
providing support for various schedule types including intervals,
cron expressions, and one-time executions.
"""
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_MISSED
from PyQt6.QtCore import QObject, pyqtSignal

logger = logging.getLogger('Core.Scheduler')


@dataclass
class ScheduleConfig:
    """Configuration for a scheduled script execution."""
    script_name: str
    schedule_type: str  # 'interval', 'daily', 'weekly', 'monthly', 'cron', 'once'
    enabled: bool = True
    arguments: Dict[str, Any] = field(default_factory=dict)
    
    # Schedule type specific configurations
    interval_seconds: Optional[int] = None
    interval_minutes: Optional[int] = None
    interval_hours: Optional[int] = None
    interval_days: Optional[int] = None
    
    # For daily/weekly/monthly schedules
    time_of_day: Optional[str] = None  # Format: "HH:MM"
    days_of_week: Optional[List[int]] = None  # 0=Monday, 6=Sunday
    day_of_month: Optional[int] = None
    
    # For cron schedules
    cron_expression: Optional[str] = None
    
    # For one-time schedules
    run_date: Optional[datetime] = None
    
    # Execution limits and windows
    max_instances: int = 1
    misfire_grace_time: int = 60  # seconds
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    
    # Tracking
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    last_result: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        data = {
            'script_name': self.script_name,
            'schedule_type': self.schedule_type,
            'enabled': self.enabled,
            'arguments': self.arguments,
            'max_instances': self.max_instances,
            'misfire_grace_time': self.misfire_grace_time,
            'run_count': self.run_count,
        }
        
        # Add type-specific fields
        if self.schedule_type == 'interval':
            if self.interval_seconds: data['interval_seconds'] = self.interval_seconds
            if self.interval_minutes: data['interval_minutes'] = self.interval_minutes
            if self.interval_hours: data['interval_hours'] = self.interval_hours
            if self.interval_days: data['interval_days'] = self.interval_days
        elif self.schedule_type in ['daily', 'weekly', 'monthly']:
            if self.time_of_day: data['time_of_day'] = self.time_of_day
            if self.days_of_week: data['days_of_week'] = self.days_of_week
            if self.day_of_month: data['day_of_month'] = self.day_of_month
        elif self.schedule_type == 'cron':
            if self.cron_expression: data['cron_expression'] = self.cron_expression
        elif self.schedule_type == 'once':
            if self.run_date: data['run_date'] = self.run_date.isoformat()
        
        # Add optional datetime fields
        if self.start_date: data['start_date'] = self.start_date.isoformat()
        if self.end_date: data['end_date'] = self.end_date.isoformat()
        if self.last_run: data['last_run'] = self.last_run.isoformat()
        if self.next_run: data['next_run'] = self.next_run.isoformat()
        if self.last_result: data['last_result'] = self.last_result
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScheduleConfig':
        """Create from dictionary."""
        # Parse datetime fields
        for field in ['run_date', 'start_date', 'end_date', 'last_run', 'next_run']:
            if field in data and data[field]:
                if isinstance(data[field], str):
                    data[field] = datetime.fromisoformat(data[field])
        
        return cls(**data)


class SchedulerManager(QObject):
    """
    Manages scheduled script executions using APScheduler.
    
    This class handles all scheduling operations including adding,
    removing, and monitoring scheduled tasks.
    """
    
    # Signals for schedule events
    schedule_added = pyqtSignal(str, dict)  # script_name, config
    schedule_removed = pyqtSignal(str)  # script_name
    schedule_updated = pyqtSignal(str, dict)  # script_name, config
    schedule_executed = pyqtSignal(str, dict)  # script_name, result
    schedule_error = pyqtSignal(str, str)  # script_name, error
    schedule_missed = pyqtSignal(str)  # script_name
    
    def __init__(self, script_executor=None, settings=None):
        super().__init__()
        self._script_executor = script_executor
        self._settings = settings
        self._scheduler = None
        self._schedules: Dict[str, ScheduleConfig] = {}
        self._execution_history: Dict[str, List[Dict[str, Any]]] = {}
        
        self._initialize_scheduler()
        
    def _initialize_scheduler(self):
        """Initialize the APScheduler instance."""
        try:
            self._scheduler = BackgroundScheduler(
                timezone='local',
                job_defaults={
                    'coalesce': True,
                    'max_instances': 1,
                    'misfire_grace_time': 60
                }
            )
            
            # Add event listeners
            self._scheduler.add_listener(
                self._on_job_executed,
                EVENT_JOB_EXECUTED
            )
            self._scheduler.add_listener(
                self._on_job_error,
                EVENT_JOB_ERROR
            )
            self._scheduler.add_listener(
                self._on_job_missed,
                EVENT_JOB_MISSED
            )
            
            logger.info("Scheduler initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize scheduler: {e}")
            raise
    
    def start(self):
        """Start the scheduler."""
        if self._scheduler and not self._scheduler.running:
            self._scheduler.start()
            self._load_schedules()
            logger.info("Scheduler started")
    
    def stop(self):
        """Stop the scheduler."""
        if self._scheduler and self._scheduler.running:
            self._save_schedules()
            self._scheduler.shutdown(wait=False)
            logger.info("Scheduler stopped")
    
    def add_schedule(self, config: ScheduleConfig) -> bool:
        """Add a new schedule."""
        try:
            if config.script_name in self._schedules:
                logger.warning(f"Schedule already exists for script: {config.script_name}")
                return False
            
            # Create the appropriate trigger
            trigger = self._create_trigger(config)
            if not trigger:
                logger.error(f"Failed to create trigger for schedule: {config.script_name}")
                return False
            
            # Add the job to scheduler
            job = self._scheduler.add_job(
                func=self._execute_scheduled_script,
                trigger=trigger,
                args=[config.script_name],
                id=f"script_{config.script_name}",
                name=f"Script: {config.script_name}",
                max_instances=config.max_instances,
                misfire_grace_time=config.misfire_grace_time,
                replace_existing=True
            )
            
            # Update next run time
            config.next_run = job.next_run_time
            
            # Store the schedule
            self._schedules[config.script_name] = config
            
            # Save to settings
            self._save_schedule_to_settings(config)
            
            # Emit signal
            self.schedule_added.emit(config.script_name, config.to_dict())
            
            logger.info(f"Schedule added for script: {config.script_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding schedule for {config.script_name}: {e}")
            return False
    
    def remove_schedule(self, script_name: str) -> bool:
        """Remove a schedule."""
        try:
            if script_name not in self._schedules:
                logger.warning(f"No schedule found for script: {script_name}")
                return False
            
            # Remove from scheduler
            job_id = f"script_{script_name}"
            self._scheduler.remove_job(job_id)
            
            # Remove from internal storage
            del self._schedules[script_name]
            
            # Remove from settings
            self._remove_schedule_from_settings(script_name)
            
            # Emit signal
            self.schedule_removed.emit(script_name)
            
            logger.info(f"Schedule removed for script: {script_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error removing schedule for {script_name}: {e}")
            return False
    
    def update_schedule(self, config: ScheduleConfig) -> bool:
        """Update an existing schedule."""
        try:
            # Remove old schedule if exists
            if config.script_name in self._schedules:
                self.remove_schedule(config.script_name)
            
            # Add new schedule
            return self.add_schedule(config)
            
        except Exception as e:
            logger.error(f"Error updating schedule for {config.script_name}: {e}")
            return False
    
    def enable_schedule(self, script_name: str) -> bool:
        """Enable a schedule."""
        try:
            if script_name not in self._schedules:
                return False
            
            job_id = f"script_{script_name}"
            self._scheduler.resume_job(job_id)
            
            self._schedules[script_name].enabled = True
            self._save_schedule_to_settings(self._schedules[script_name])
            
            logger.info(f"Schedule enabled for script: {script_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error enabling schedule for {script_name}: {e}")
            return False
    
    def disable_schedule(self, script_name: str) -> bool:
        """Disable a schedule."""
        try:
            if script_name not in self._schedules:
                return False
            
            job_id = f"script_{script_name}"
            self._scheduler.pause_job(job_id)
            
            self._schedules[script_name].enabled = False
            self._save_schedule_to_settings(self._schedules[script_name])
            
            logger.info(f"Schedule disabled for script: {script_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error disabling schedule for {script_name}: {e}")
            return False
    
    def get_schedule(self, script_name: str) -> Optional[ScheduleConfig]:
        """Get schedule configuration for a script."""
        return self._schedules.get(script_name)
    
    def get_all_schedules(self) -> Dict[str, ScheduleConfig]:
        """Get all schedule configurations."""
        return self._schedules.copy()
    
    def get_next_run_time(self, script_name: str) -> Optional[datetime]:
        """Get the next run time for a scheduled script."""
        try:
            job_id = f"script_{script_name}"
            job = self._scheduler.get_job(job_id)
            return job.next_run_time if job else None
        except Exception:
            return None
    
    def get_next_runs(self, script_name: str, count: int = 5) -> List[datetime]:
        """Get the next N run times for a scheduled script."""
        try:
            if script_name not in self._schedules:
                return []
            
            config = self._schedules[script_name]
            trigger = self._create_trigger(config)
            
            if not trigger:
                return []
            
            # Get next run times
            next_runs = []
            current_time = datetime.now()
            
            for _ in range(count):
                next_time = trigger.get_next_fire_time(None, current_time)
                if next_time:
                    next_runs.append(next_time)
                    current_time = next_time + timedelta(seconds=1)
                else:
                    break
            
            return next_runs
            
        except Exception as e:
            logger.error(f"Error getting next runs for {script_name}: {e}")
            return []
    
    def get_execution_history(self, script_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get execution history for a script."""
        history = self._execution_history.get(script_name, [])
        return history[-limit:] if limit else history
    
    def _create_trigger(self, config: ScheduleConfig):
        """Create the appropriate trigger based on schedule type."""
        try:
            if config.schedule_type == 'interval':
                # Calculate total seconds for interval
                total_seconds = 0
                if config.interval_seconds:
                    total_seconds += config.interval_seconds
                if config.interval_minutes:
                    total_seconds += config.interval_minutes * 60
                if config.interval_hours:
                    total_seconds += config.interval_hours * 3600
                if config.interval_days:
                    total_seconds += config.interval_days * 86400
                
                if total_seconds <= 0:
                    logger.error("Invalid interval configuration")
                    return None
                
                return IntervalTrigger(
                    seconds=total_seconds,
                    start_date=config.start_date,
                    end_date=config.end_date
                )
            
            elif config.schedule_type == 'daily':
                if not config.time_of_day:
                    logger.error("Daily schedule requires time_of_day")
                    return None
                
                hour, minute = map(int, config.time_of_day.split(':'))
                return CronTrigger(
                    hour=hour,
                    minute=minute,
                    start_date=config.start_date,
                    end_date=config.end_date
                )
            
            elif config.schedule_type == 'weekly':
                if not config.time_of_day or not config.days_of_week:
                    logger.error("Weekly schedule requires time_of_day and days_of_week")
                    return None
                
                hour, minute = map(int, config.time_of_day.split(':'))
                days = ','.join(str(d) for d in config.days_of_week)
                
                return CronTrigger(
                    day_of_week=days,
                    hour=hour,
                    minute=minute,
                    start_date=config.start_date,
                    end_date=config.end_date
                )
            
            elif config.schedule_type == 'monthly':
                if not config.time_of_day or not config.day_of_month:
                    logger.error("Monthly schedule requires time_of_day and day_of_month")
                    return None
                
                hour, minute = map(int, config.time_of_day.split(':'))
                
                return CronTrigger(
                    day=config.day_of_month,
                    hour=hour,
                    minute=minute,
                    start_date=config.start_date,
                    end_date=config.end_date
                )
            
            elif config.schedule_type == 'cron':
                if not config.cron_expression:
                    logger.error("Cron schedule requires cron_expression")
                    return None
                
                return CronTrigger.from_crontab(
                    config.cron_expression,
                    start_date=config.start_date,
                    end_date=config.end_date
                )
            
            elif config.schedule_type == 'once':
                if not config.run_date:
                    logger.error("One-time schedule requires run_date")
                    return None
                
                return DateTrigger(run_date=config.run_date)
            
            else:
                logger.error(f"Unknown schedule type: {config.schedule_type}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating trigger: {e}")
            return None
    
    def _execute_scheduled_script(self, script_name: str):
        """Execute a scheduled script."""
        try:
            config = self._schedules.get(script_name)
            if not config:
                logger.error(f"No schedule configuration found for {script_name}")
                return
            
            # Log execution start
            logger.info(f"Executing scheduled script: {script_name}")
            
            # Execute the script if executor is available
            if self._script_executor:
                from models.script_models import ScriptExecutionModel
                if isinstance(self._script_executor, ScriptExecutionModel):
                    # Use the execution model directly
                    result = self._script_executor.execute_script(
                        script_name, 
                        config.arguments,
                        async_execution=False  # Run synchronously in scheduler thread
                    )
                else:
                    # Use the script executor
                    script_info = self._script_executor._script_loader.get_script_by_name(script_name)
                    if script_info:
                        result = self._script_executor.execute_script(script_info, config.arguments)
                    else:
                        logger.error(f"Script not found: {script_name}")
                        return
            
            # Update schedule tracking
            config.last_run = datetime.now()
            config.run_count += 1
            config.last_result = "success"
            
            # Update next run time
            job_id = f"script_{script_name}"
            job = self._scheduler.get_job(job_id)
            if job:
                config.next_run = job.next_run_time
            
            # Save updated config
            self._save_schedule_to_settings(config)
            
            # Add to history
            self._add_to_history(script_name, {
                'timestamp': config.last_run,
                'result': 'success',
                'run_count': config.run_count
            })
            
            logger.info(f"Successfully executed scheduled script: {script_name}")
            
        except Exception as e:
            logger.error(f"Error executing scheduled script {script_name}: {e}")
            
            # Update schedule tracking for error
            if script_name in self._schedules:
                config = self._schedules[script_name]
                config.last_run = datetime.now()
                config.last_result = f"error: {str(e)}"
                self._save_schedule_to_settings(config)
            
            # Add error to history
            self._add_to_history(script_name, {
                'timestamp': datetime.now(),
                'result': 'error',
                'error': str(e)
            })
    
    def _on_job_executed(self, event):
        """Handle job execution event."""
        job_id = event.job_id
        if job_id.startswith('script_'):
            script_name = job_id[7:]  # Remove 'script_' prefix
            logger.debug(f"Scheduled job executed: {script_name}")
            self.schedule_executed.emit(script_name, {'status': 'executed'})
    
    def _on_job_error(self, event):
        """Handle job error event."""
        job_id = event.job_id
        if job_id.startswith('script_'):
            script_name = job_id[7:]  # Remove 'script_' prefix
            error_msg = str(event.exception) if event.exception else "Unknown error"
            logger.error(f"Scheduled job error for {script_name}: {error_msg}")
            self.schedule_error.emit(script_name, error_msg)
    
    def _on_job_missed(self, event):
        """Handle missed job event."""
        job_id = event.job_id
        if job_id.startswith('script_'):
            script_name = job_id[7:]  # Remove 'script_' prefix
            logger.warning(f"Scheduled job missed: {script_name}")
            self.schedule_missed.emit(script_name)
    
    def _add_to_history(self, script_name: str, entry: Dict[str, Any]):
        """Add an entry to execution history."""
        if script_name not in self._execution_history:
            self._execution_history[script_name] = []
        
        self._execution_history[script_name].append(entry)
        
        # Limit history size
        max_history = 100
        if len(self._execution_history[script_name]) > max_history:
            self._execution_history[script_name] = self._execution_history[script_name][-max_history:]
    
    def _load_schedules(self):
        """Load schedules from settings."""
        if not self._settings:
            return
        
        try:
            schedules_data = self._settings.get('schedules', {})
            
            for script_name, config_data in schedules_data.items():
                try:
                    config = ScheduleConfig.from_dict(config_data)
                    if config.enabled:
                        self.add_schedule(config)
                    else:
                        # Store disabled schedules without adding to scheduler
                        self._schedules[script_name] = config
                    
                except Exception as e:
                    logger.error(f"Error loading schedule for {script_name}: {e}")
            
            logger.info(f"Loaded {len(self._schedules)} schedules from settings")
            
        except Exception as e:
            logger.error(f"Error loading schedules: {e}")
    
    def _save_schedules(self):
        """Save all schedules to settings."""
        if not self._settings:
            return
        
        try:
            schedules_data = {}
            for script_name, config in self._schedules.items():
                schedules_data[script_name] = config.to_dict()
            
            self._settings.set('schedules', schedules_data)
            logger.info(f"Saved {len(schedules_data)} schedules to settings")
            
        except Exception as e:
            logger.error(f"Error saving schedules: {e}")
    
    def _save_schedule_to_settings(self, config: ScheduleConfig):
        """Save a single schedule to settings."""
        if not self._settings:
            return
        
        try:
            schedules_data = self._settings.get('schedules', {})
            schedules_data[config.script_name] = config.to_dict()
            self._settings.set('schedules', schedules_data)
            
        except Exception as e:
            logger.error(f"Error saving schedule for {config.script_name}: {e}")
    
    def _remove_schedule_from_settings(self, script_name: str):
        """Remove a schedule from settings."""
        if not self._settings:
            return
        
        try:
            schedules_data = self._settings.get('schedules', {})
            if script_name in schedules_data:
                del schedules_data[script_name]
                self._settings.set('schedules', schedules_data)
            
        except Exception as e:
            logger.error(f"Error removing schedule for {script_name}: {e}")