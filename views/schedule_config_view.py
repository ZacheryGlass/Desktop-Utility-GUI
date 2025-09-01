"""
Schedule Configuration View - UI for configuring script schedules.

This view provides a user-friendly interface for creating and editing
script execution schedules with various scheduling options.
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, time, timedelta
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLabel, QComboBox, QSpinBox, QTimeEdit, QDateTimeEdit,
    QCheckBox, QPushButton, QDialogButtonBox, QListWidget,
    QLineEdit, QTextEdit, QTabWidget, QWidget, QGridLayout,
    QButtonGroup, QRadioButton, QMessageBox, QListWidgetItem
)
from PyQt6.QtCore import Qt, QTime, QDateTime, pyqtSignal
from PyQt6.QtGui import QFont

logger = logging.getLogger('Views.ScheduleConfig')


class ScheduleConfigView(QDialog):
    """
    Dialog for configuring script execution schedules.
    
    Provides intuitive UI for setting up various schedule types
    including intervals, daily, weekly, monthly, and cron schedules.
    """
    
    # Signals
    schedule_created = pyqtSignal(str, dict)  # script_name, schedule_config
    schedule_updated = pyqtSignal(str, dict)  # script_name, schedule_config
    
    def __init__(self, script_name: str, script_info: Optional[Dict] = None, 
                 existing_schedule: Optional[Dict] = None, parent=None):
        super().__init__(parent)
        self.script_name = script_name
        self.script_info = script_info or {}
        self.existing_schedule = existing_schedule
        
        self.setWindowTitle(f"Schedule Configuration - {script_name}")
        self.setModal(True)
        self.setMinimumWidth(600)
        
        self._setup_ui()
        self._load_existing_schedule()
        
    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Script info header
        self._add_script_header(layout)
        
        # Tab widget for different schedule types
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Add tabs for each schedule type
        self._add_interval_tab()
        self._add_daily_tab()
        self._add_weekly_tab()
        self._add_monthly_tab()
        self._add_cron_tab()
        self._add_once_tab()
        
        # Advanced options
        self._add_advanced_options(layout)
        
        # Preview section
        self._add_preview_section(layout)
        
        # Dialog buttons
        self._add_dialog_buttons(layout)
        
        # Connect signals
        self._connect_signals()
        
        # Set logical tab order
        self._set_tab_order()
    
    def _add_script_header(self, layout):
        """Add script information header."""
        header_group = QGroupBox("Script Information")
        header_layout = QFormLayout()
        
        # Script name
        name_label = QLabel(self.script_name)
        name_label.setFont(QFont("", 10, QFont.Weight.Bold))
        header_layout.addRow("Script:", name_label)
        
        # Script description if available
        if self.script_info.get('description'):
            desc_label = QLabel(self.script_info['description'])
            desc_label.setWordWrap(True)
            header_layout.addRow("Description:", desc_label)
        
        header_group.setLayout(header_layout)
        layout.addWidget(header_group)
    
    def _add_interval_tab(self):
        """Add interval schedule configuration tab."""
        widget = QWidget()
        layout = QFormLayout()
        
        # Interval inputs
        self.interval_days = QSpinBox()
        self.interval_days.setRange(0, 365)
        self.interval_days.setSuffix(" days")
        self.interval_days.setAccessibleName("Days interval")
        self.interval_days.setAccessibleDescription("Number of days between script executions")
        layout.addRow("&Days:", self.interval_days)
        
        self.interval_hours = QSpinBox()
        self.interval_hours.setRange(0, 23)
        self.interval_hours.setSuffix(" hours")
        self.interval_hours.setAccessibleName("Hours interval")
        self.interval_hours.setAccessibleDescription("Number of hours between script executions")
        layout.addRow("&Hours:", self.interval_hours)
        
        self.interval_minutes = QSpinBox()
        self.interval_minutes.setRange(0, 59)
        self.interval_minutes.setSuffix(" minutes")
        self.interval_minutes.setAccessibleName("Minutes interval")
        self.interval_minutes.setAccessibleDescription("Number of minutes between script executions")
        layout.addRow("&Minutes:", self.interval_minutes)
        
        self.interval_seconds = QSpinBox()
        self.interval_seconds.setRange(0, 59)
        self.interval_seconds.setSuffix(" seconds")
        self.interval_seconds.setAccessibleName("Seconds interval")
        self.interval_seconds.setAccessibleDescription("Number of seconds between script executions")
        layout.addRow("&Seconds:", self.interval_seconds)
        
        # Common presets
        preset_layout = QHBoxLayout()
        preset_label = QLabel("Presets:")
        preset_layout.addWidget(preset_label)
        
        for text, values in [
            ("&5 min", (0, 0, 5, 0)),
            ("&30 min", (0, 0, 30, 0)),
            ("&1 hour", (0, 1, 0, 0)),
            ("&6 hours", (0, 6, 0, 0)),
            ("&Daily", (1, 0, 0, 0))
        ]:
            btn = QPushButton(text)
            btn.clicked.connect(lambda checked, v=values: self._set_interval_preset(v))
            preset_layout.addWidget(btn)
        
        layout.addRow(preset_layout)
        
        widget.setLayout(layout)
        self.tab_widget.addTab(widget, "Interval")
    
    def _add_daily_tab(self):
        """Add daily schedule configuration tab."""
        widget = QWidget()
        layout = QFormLayout()
        
        # Time of day
        self.daily_time = QTimeEdit()
        self.daily_time.setDisplayFormat("h:mm AP")
        self.daily_time.setTime(QTime(9, 0))
        self.daily_time.setAccessibleName("Daily execution time")
        self.daily_time.setAccessibleDescription("Time of day when the script will run")
        layout.addRow("&Time:", self.daily_time)
        
        # Quick presets
        preset_layout = QHBoxLayout()
        for text, time_tuple in [
            ("&Morning (9 AM)", (9, 0)),
            ("&Noon", (12, 0)),
            ("&Evening (6 PM)", (18, 0)),
            ("Ni&ght (10 PM)", (22, 0))
        ]:
            btn = QPushButton(text)
            btn.clicked.connect(lambda checked, t=time_tuple: 
                              self.daily_time.setTime(QTime(*t)))
            preset_layout.addWidget(btn)
        
        layout.addRow("Presets:", preset_layout)
        
        widget.setLayout(layout)
        self.tab_widget.addTab(widget, "Daily")
    
    def _add_weekly_tab(self):
        """Add weekly schedule configuration tab."""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Days of week
        days_group = QGroupBox("Days of Week")
        days_layout = QGridLayout()
        
        self.weekday_checks = {}
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", 
                "Friday", "Saturday", "Sunday"]
        
        for i, day in enumerate(days):
            check = QCheckBox(day)
            self.weekday_checks[i] = check
            days_layout.addWidget(check, i // 4, i % 4)
        
        days_group.setLayout(days_layout)
        layout.addWidget(days_group)
        
        # Time of day
        time_layout = QFormLayout()
        self.weekly_time = QTimeEdit()
        self.weekly_time.setDisplayFormat("h:mm AP")
        self.weekly_time.setTime(QTime(9, 0))
        self.weekly_time.setAccessibleName("Weekly execution time")
        self.weekly_time.setAccessibleDescription("Time of day when the script will run on selected days")
        time_layout.addRow("&Time:", self.weekly_time)
        
        # Presets
        preset_layout = QHBoxLayout()
        
        weekdays_btn = QPushButton("&Weekdays")
        weekdays_btn.clicked.connect(self._select_weekdays)
        preset_layout.addWidget(weekdays_btn)
        
        weekends_btn = QPushButton("Weeken&ds")
        weekends_btn.clicked.connect(self._select_weekends)
        preset_layout.addWidget(weekends_btn)
        
        all_days_btn = QPushButton("&All Days")
        all_days_btn.clicked.connect(self._select_all_days)
        preset_layout.addWidget(all_days_btn)
        
        time_layout.addRow("Presets:", preset_layout)
        
        layout.addLayout(time_layout)
        
        widget.setLayout(layout)
        self.tab_widget.addTab(widget, "Weekly")
    
    def _add_monthly_tab(self):
        """Add monthly schedule configuration tab."""
        widget = QWidget()
        layout = QFormLayout()
        
        # Day of month
        self.monthly_day = QSpinBox()
        self.monthly_day.setRange(1, 31)
        self.monthly_day.setValue(1)
        self.monthly_day.setSpecialValueText("Last day")
        self.monthly_day.setAccessibleName("Day of month")
        self.monthly_day.setAccessibleDescription("Day of the month when the script will run")
        layout.addRow("&Day of Month:", self.monthly_day)
        
        # Time of day
        self.monthly_time = QTimeEdit()
        self.monthly_time.setDisplayFormat("h:mm AP")
        self.monthly_time.setTime(QTime(9, 0))
        self.monthly_time.setAccessibleName("Monthly execution time")
        self.monthly_time.setAccessibleDescription("Time of day when the script will run on the selected day")
        layout.addRow("T&ime:", self.monthly_time)
        
        # Note about month variations
        note = QLabel("Note: If the selected day doesn't exist in a month "
                     "(e.g., 31st in February), the schedule will run on the "
                     "last day of that month.")
        note.setWordWrap(True)
        note.setStyleSheet("color: #888888;")
        layout.addRow(note)
        
        widget.setLayout(layout)
        self.tab_widget.addTab(widget, "Monthly")
    
    def _add_cron_tab(self):
        """Add cron expression configuration tab."""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Common presets for beginners
        presets_group = QGroupBox("Common Patterns")
        presets_layout = QVBoxLayout()
        
        preset_info = QLabel("Select a common schedule pattern or create a custom one below:")
        preset_info.setWordWrap(True)
        presets_layout.addWidget(preset_info)
        
        # Preset buttons with their cron expressions
        preset_grid = QGridLayout()
        cron_presets = [
            ("Every hour at :00", "0 * * * *"),
            ("Every hour at :30", "30 * * * *"),
            ("Every 2 hours", "0 */2 * * *"),
            ("Every 4 hours", "0 */4 * * *"),
            ("Daily at midnight", "0 0 * * *"),
            ("Daily at noon", "0 12 * * *"),
            ("Monday at 9 AM", "0 9 * * 1"),
            ("Weekdays at 8 AM", "0 8 * * 1-5"),
            ("Weekends at 10 AM", "0 10 * * 0,6"),
            ("First of month", "0 0 1 * *"),
        ]
        
        for i, (label, cron) in enumerate(cron_presets):
            btn = QPushButton(label)
            btn.setToolTip(f"Cron: {cron}")
            btn.clicked.connect(lambda checked, expr=cron: self.cron_expression.setText(expr))
            preset_grid.addWidget(btn, i // 2, i % 2)
        
        presets_layout.addLayout(preset_grid)
        presets_group.setLayout(presets_layout)
        layout.addWidget(presets_group)
        
        # Advanced section with cron expression input
        advanced_group = QGroupBox("Custom Pattern")
        advanced_layout = QFormLayout()
        
        self.cron_expression = QLineEdit()
        self.cron_expression.setPlaceholderText("e.g., 0 */2 * * * (every 2 hours)")
        self.cron_expression.setAccessibleName("Cron expression")
        self.cron_expression.setAccessibleDescription("Enter a custom cron expression for advanced scheduling")
        advanced_layout.addRow("&Cron Expression:", self.cron_expression)
        
        # Validation button
        validate_btn = QPushButton("&Validate Expression")
        validate_btn.clicked.connect(self._validate_cron)
        advanced_layout.addRow("", validate_btn)
        
        advanced_group.setLayout(advanced_layout)
        layout.addWidget(advanced_group)
        
        # Cron help
        help_group = QGroupBox("Cron Expression Format")
        help_layout = QVBoxLayout()
        
        help_text = """
        Format: minute hour day_of_month month day_of_week
        
        Field values:
        - minute: 0-59
        - hour: 0-23
        - day_of_month: 1-31
        - month: 1-12
        - day_of_week: 0-6 (0 = Monday)
        
        Special characters:
        - * : any value
        - , : value list separator
        - - : range of values
        - / : step values
        
        Examples:
        - 0 9 * * * : Daily at 9:00 AM
        - 0 */2 * * * : Every 2 hours
        - 0 9 * * 1-5 : Weekdays at 9:00 AM
        - 0 0 1 * * : First day of month at midnight
        """
        
        help_label = QLabel(help_text)
        help_label.setFont(QFont("Courier", 9))
        help_layout.addWidget(help_label)
        
        help_group.setLayout(help_layout)
        layout.addWidget(help_group)
        
        widget.setLayout(layout)
        self.tab_widget.addTab(widget, "Cron")
    
    def _add_once_tab(self):
        """Add one-time schedule configuration tab."""
        widget = QWidget()
        layout = QFormLayout()
        
        # Date and time picker
        self.once_datetime = QDateTimeEdit()
        self.once_datetime.setDateTime(QDateTime.currentDateTime().addSecs(3600))
        self.once_datetime.setCalendarPopup(True)
        self.once_datetime.setDisplayFormat("yyyy-MM-dd h:mm AP")
        self.once_datetime.setAccessibleName("One-time execution date and time")
        self.once_datetime.setAccessibleDescription("Select the date and time for a one-time script execution")
        layout.addRow("&Run Date/Time:", self.once_datetime)
        
        # Quick presets
        preset_layout = QHBoxLayout()
        
        for text, hours in [
            ("In &1 hour", 1),
            ("In &6 hours", 6),
            ("&Tomorrow", 24),
            ("Next &week", 168)
        ]:
            btn = QPushButton(text)
            btn.clicked.connect(lambda checked, h=hours: 
                              self.once_datetime.setDateTime(
                                  QDateTime.currentDateTime().addSecs(h * 3600)))
            preset_layout.addWidget(btn)
        
        layout.addRow("Quick Set:", preset_layout)
        
        # Note about one-time schedules
        note = QLabel("Note: This schedule will be automatically removed after execution.")
        note.setWordWrap(True)
        note.setStyleSheet("color: #888888;")
        layout.addRow(note)
        
        widget.setLayout(layout)
        self.tab_widget.addTab(widget, "Once")
    
    def _add_advanced_options(self, layout):
        """Add advanced scheduling options."""
        advanced_group = QGroupBox("Advanced Options")
        advanced_layout = QFormLayout()
        
        # Enable/disable schedule
        self.enabled_check = QCheckBox("Enable schedule immediately")
        self.enabled_check.setChecked(True)
        advanced_layout.addRow(self.enabled_check)
        
        # Max instances
        self.max_instances = QSpinBox()
        self.max_instances.setRange(1, 10)
        self.max_instances.setValue(1)
        self.max_instances.setToolTip("Maximum number of concurrent executions")
        advanced_layout.addRow("Max Instances:", self.max_instances)
        
        # Misfire grace time
        self.misfire_grace = QSpinBox()
        self.misfire_grace.setRange(0, 3600)
        self.misfire_grace.setValue(60)
        self.misfire_grace.setSuffix(" seconds")
        self.misfire_grace.setToolTip("Grace period for missed executions")
        advanced_layout.addRow("Misfire Grace Time:", self.misfire_grace)
        
        # Start/end dates
        self.use_date_range = QCheckBox("Limit to date range")
        advanced_layout.addRow(self.use_date_range)
        
        date_range_widget = QWidget()
        date_range_layout = QHBoxLayout(date_range_widget)
        date_range_layout.setContentsMargins(0, 0, 0, 0)
        
        self.start_date = QDateTimeEdit()
        self.start_date.setDateTime(QDateTime.currentDateTime())
        self.start_date.setCalendarPopup(True)
        self.start_date.setEnabled(False)
        date_range_layout.addWidget(QLabel("From:"))
        date_range_layout.addWidget(self.start_date)
        
        self.end_date = QDateTimeEdit()
        self.end_date.setDateTime(QDateTime.currentDateTime().addDays(30))
        self.end_date.setCalendarPopup(True)
        self.end_date.setEnabled(False)
        date_range_layout.addWidget(QLabel("To:"))
        date_range_layout.addWidget(self.end_date)
        
        advanced_layout.addRow(date_range_widget)
        
        # Connect date range checkbox
        self.use_date_range.toggled.connect(self.start_date.setEnabled)
        self.use_date_range.toggled.connect(self.end_date.setEnabled)
        
        advanced_group.setLayout(advanced_layout)
        layout.addWidget(advanced_group)
    
    def _add_preview_section(self, layout):
        """Add schedule preview section."""
        preview_group = QGroupBox("Schedule Preview")
        preview_layout = QVBoxLayout()
        
        # Next run times
        self.preview_list = QListWidget()
        self.preview_list.setMaximumHeight(100)
        preview_layout.addWidget(QLabel("Next scheduled runs:"))
        preview_layout.addWidget(self.preview_list)
        
        # Preview button
        preview_btn = QPushButton("Preview Schedule")
        preview_btn.clicked.connect(self._preview_schedule)
        preview_layout.addWidget(preview_btn)
        
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
    
    def _add_dialog_buttons(self, layout):
        """Add dialog buttons."""
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._save_schedule)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def _connect_signals(self):
        """Connect widget signals."""
        # Update preview when settings change
        self.tab_widget.currentChanged.connect(self._preview_schedule)
        self.interval_days.valueChanged.connect(self._preview_schedule)
        self.interval_hours.valueChanged.connect(self._preview_schedule)
        self.interval_minutes.valueChanged.connect(self._preview_schedule)
        self.interval_seconds.valueChanged.connect(self._preview_schedule)
        self.daily_time.timeChanged.connect(self._preview_schedule)
        self.weekly_time.timeChanged.connect(self._preview_schedule)
        self.monthly_day.valueChanged.connect(self._preview_schedule)
        self.monthly_time.timeChanged.connect(self._preview_schedule)
        self.once_datetime.dateTimeChanged.connect(self._preview_schedule)
        
        for check in self.weekday_checks.values():
            check.toggled.connect(self._preview_schedule)
    
    def _set_tab_order(self):
        """Set logical tab order for keyboard navigation."""
        # Main tab widget should be first
        self.setTabOrder(self.tab_widget, self.interval_days)
        
        # Interval tab order
        self.setTabOrder(self.interval_days, self.interval_hours)
        self.setTabOrder(self.interval_hours, self.interval_minutes)
        self.setTabOrder(self.interval_minutes, self.interval_seconds)
        
        # Daily tab order
        self.setTabOrder(self.interval_seconds, self.daily_time)
        
        # Weekly tab order (weekday checkboxes)
        if hasattr(self, 'weekday_checks'):
            prev_widget = self.daily_time
            for i in range(7):
                if i in self.weekday_checks:
                    self.setTabOrder(prev_widget, self.weekday_checks[i])
                    prev_widget = self.weekday_checks[i]
            self.setTabOrder(prev_widget, self.weekly_time)
        
        # Monthly tab order
        self.setTabOrder(self.weekly_time, self.monthly_day)
        self.setTabOrder(self.monthly_day, self.monthly_time)
        
        # Cron tab order
        self.setTabOrder(self.monthly_time, self.cron_expression)
        
        # Once tab order
        self.setTabOrder(self.cron_expression, self.once_datetime)
        
        # Advanced options order
        self.setTabOrder(self.once_datetime, self.enabled_check)
        self.setTabOrder(self.enabled_check, self.max_instances)
        self.setTabOrder(self.max_instances, self.misfire_grace)
        self.setTabOrder(self.misfire_grace, self.use_date_range)
        self.setTabOrder(self.use_date_range, self.start_date)
        self.setTabOrder(self.start_date, self.end_date)
        
        # Preview section
        self.setTabOrder(self.end_date, self.preview_list)
    
    def _load_existing_schedule(self):
        """Load existing schedule configuration if available."""
        if not self.existing_schedule:
            return
        
        schedule_type = self.existing_schedule.get('schedule_type')
        
        if schedule_type == 'interval':
            self.tab_widget.setCurrentIndex(0)
            if 'interval_days' in self.existing_schedule:
                self.interval_days.setValue(self.existing_schedule['interval_days'])
            if 'interval_hours' in self.existing_schedule:
                self.interval_hours.setValue(self.existing_schedule['interval_hours'])
            if 'interval_minutes' in self.existing_schedule:
                self.interval_minutes.setValue(self.existing_schedule['interval_minutes'])
            if 'interval_seconds' in self.existing_schedule:
                self.interval_seconds.setValue(self.existing_schedule['interval_seconds'])
        
        elif schedule_type == 'daily':
            self.tab_widget.setCurrentIndex(1)
            if 'time_of_day' in self.existing_schedule:
                time_str = self.existing_schedule['time_of_day']
                hour, minute = map(int, time_str.split(':'))
                self.daily_time.setTime(QTime(hour, minute))
        
        elif schedule_type == 'weekly':
            self.tab_widget.setCurrentIndex(2)
            if 'days_of_week' in self.existing_schedule:
                for day in self.existing_schedule['days_of_week']:
                    if day in self.weekday_checks:
                        self.weekday_checks[day].setChecked(True)
            if 'time_of_day' in self.existing_schedule:
                time_str = self.existing_schedule['time_of_day']
                hour, minute = map(int, time_str.split(':'))
                self.weekly_time.setTime(QTime(hour, minute))
        
        elif schedule_type == 'monthly':
            self.tab_widget.setCurrentIndex(3)
            if 'day_of_month' in self.existing_schedule:
                self.monthly_day.setValue(self.existing_schedule['day_of_month'])
            if 'time_of_day' in self.existing_schedule:
                time_str = self.existing_schedule['time_of_day']
                hour, minute = map(int, time_str.split(':'))
                self.monthly_time.setTime(QTime(hour, minute))
        
        elif schedule_type == 'cron':
            self.tab_widget.setCurrentIndex(4)
            if 'cron_expression' in self.existing_schedule:
                self.cron_expression.setText(self.existing_schedule['cron_expression'])
        
        elif schedule_type == 'once':
            self.tab_widget.setCurrentIndex(5)
            if 'run_date' in self.existing_schedule:
                dt = QDateTime.fromString(self.existing_schedule['run_date'], Qt.DateFormat.ISODate)
                self.once_datetime.setDateTime(dt)
        
        # Load advanced options
        if 'enabled' in self.existing_schedule:
            self.enabled_check.setChecked(self.existing_schedule['enabled'])
        if 'max_instances' in self.existing_schedule:
            self.max_instances.setValue(self.existing_schedule['max_instances'])
        if 'misfire_grace_time' in self.existing_schedule:
            self.misfire_grace.setValue(self.existing_schedule['misfire_grace_time'])
    
    def _set_interval_preset(self, values):
        """Set interval values from preset."""
        days, hours, minutes, seconds = values
        self.interval_days.setValue(days)
        self.interval_hours.setValue(hours)
        self.interval_minutes.setValue(minutes)
        self.interval_seconds.setValue(seconds)
    
    def _select_weekdays(self):
        """Select weekdays (Monday-Friday)."""
        for i in range(5):
            self.weekday_checks[i].setChecked(True)
        for i in range(5, 7):
            self.weekday_checks[i].setChecked(False)
    
    def _select_weekends(self):
        """Select weekends (Saturday-Sunday)."""
        for i in range(5):
            self.weekday_checks[i].setChecked(False)
        for i in range(5, 7):
            self.weekday_checks[i].setChecked(True)
    
    def _select_all_days(self):
        """Select all days."""
        for check in self.weekday_checks.values():
            check.setChecked(True)
    
    def _validate_cron(self):
        """Validate cron expression."""
        expression = self.cron_expression.text()
        if not expression:
            QMessageBox.warning(self, "Validation", 
                              "Please enter a cron expression.\n\n"
                              "Example formats:\n"
                              "• 0 9 * * * - Daily at 9:00 AM\n"
                              "• 0 */2 * * * - Every 2 hours\n"
                              "• 0 9 * * 1-5 - Weekdays at 9:00 AM")
            return
        
        try:
            from apscheduler.triggers.cron import CronTrigger
            trigger = CronTrigger.from_crontab(expression)
            
            # Show the next 3 run times as confirmation
            from datetime import datetime, timedelta
            current_time = datetime.now()
            next_times = []
            
            for i in range(3):
                next_time = trigger.get_next_fire_time(None, current_time)
                if next_time:
                    next_times.append(next_time.strftime('%Y-%m-%d %I:%M %p'))
                    current_time = next_time + timedelta(seconds=1)
            
            if next_times:
                QMessageBox.information(self, "Valid Expression", 
                                      f"Valid cron expression!\n\n"
                                      f"Next runs:\n" + "\n".join(f"• {t}" for t in next_times))
            else:
                QMessageBox.information(self, "Valid Expression", 
                                      "Valid cron expression!\n\n"
                                      "Note: No upcoming runs scheduled with this expression.")
        except ValueError as e:
            error_msg = str(e)
            helpful_msg = "Invalid cron expression format.\n\n"
            
            # Provide specific help based on common errors
            if "Wrong number of fields" in error_msg:
                helpful_msg += ("Cron expressions need 5 fields:\n"
                               "minute hour day month weekday\n\n"
                               "Example: 0 9 * * * (daily at 9 AM)")
            elif "not in range" in error_msg:
                helpful_msg += ("Field values out of range:\n"
                               "• Minute: 0-59\n"
                               "• Hour: 0-23\n"
                               "• Day: 1-31\n"
                               "• Month: 1-12\n"
                               "• Weekday: 0-6 (0=Monday)")
            else:
                helpful_msg += f"Error: {error_msg}\n\n"
                helpful_msg += ("Format: minute hour day month weekday\n"
                               "Example: 0 9 * * * (daily at 9 AM)")
            
            QMessageBox.critical(self, "Validation Error", helpful_msg)
        except Exception as e:
            QMessageBox.critical(self, "Validation Error", 
                                f"Error validating expression:\n{str(e)}\n\n"
                                f"Please check the cron format and try again.")
    
    def _preview_schedule(self):
        """Preview the next scheduled run times."""
        self.preview_list.clear()
        
        try:
            config = self._get_schedule_config()
            if not config:
                return
            
            # Calculate next run times based on schedule type
            from datetime import datetime, timedelta
            from apscheduler.triggers.interval import IntervalTrigger
            from apscheduler.triggers.cron import CronTrigger
            from apscheduler.triggers.date import DateTrigger
            
            trigger = None
            schedule_type = config.get('schedule_type')
            
            try:
                if schedule_type == 'interval':
                    # Calculate total seconds
                    total_seconds = 0
                    if config.get('interval_days'):
                        total_seconds += config['interval_days'] * 86400
                    if config.get('interval_hours'):
                        total_seconds += config['interval_hours'] * 3600
                    if config.get('interval_minutes'):
                        total_seconds += config['interval_minutes'] * 60
                    if config.get('interval_seconds'):
                        total_seconds += config['interval_seconds']
                    
                    if total_seconds > 0:
                        trigger = IntervalTrigger(seconds=total_seconds)
                
                elif schedule_type == 'daily':
                    time_str = config.get('time_of_day', '09:00')
                    hour, minute = map(int, time_str.split(':'))
                    trigger = CronTrigger(hour=hour, minute=minute)
                
                elif schedule_type == 'weekly':
                    time_str = config.get('time_of_day', '09:00')
                    hour, minute = map(int, time_str.split(':'))
                    days = config.get('days_of_week', [])
                    if days:
                        days_str = ','.join(str(d) for d in days)
                        trigger = CronTrigger(day_of_week=days_str, hour=hour, minute=minute)
                
                elif schedule_type == 'monthly':
                    time_str = config.get('time_of_day', '09:00')
                    hour, minute = map(int, time_str.split(':'))
                    day = config.get('day_of_month', 1)
                    trigger = CronTrigger(day=day, hour=hour, minute=minute)
                
                elif schedule_type == 'cron':
                    expr = config.get('cron_expression')
                    if expr:
                        trigger = CronTrigger.from_crontab(expr)
                
                elif schedule_type == 'once':
                    run_date = config.get('run_date')
                    if run_date:
                        self.preview_list.addItem(f"Will run once at: {run_date.strftime('%Y-%m-%d %I:%M %p')}")
                        return
                
                # Calculate next 5 run times
                if trigger:
                    current_time = datetime.now()
                    next_times = []
                    
                    for i in range(5):
                        next_time = trigger.get_next_fire_time(None, current_time)
                        if next_time:
                            next_times.append(next_time)
                            current_time = next_time + timedelta(seconds=1)
                        else:
                            break
                    
                    if next_times:
                        self.preview_list.addItem("Next scheduled runs:")
                        for i, next_time in enumerate(next_times, 1):
                            time_str = next_time.strftime('%Y-%m-%d %I:%M %p')
                            self.preview_list.addItem(f"  {i}. {time_str}")
                    else:
                        self.preview_list.addItem("No upcoming runs scheduled")
                else:
                    self.preview_list.addItem("Configure schedule to see preview")
                    
            except Exception as e:
                self.preview_list.addItem(f"Preview error: {str(e)}")
                
        except Exception as e:
            self.preview_list.addItem(f"Error: {str(e)}")
    
    def _get_schedule_config(self) -> Optional[Dict[str, Any]]:
        """Get the current schedule configuration."""
        tab_index = self.tab_widget.currentIndex()
        config = {
            'script_name': self.script_name,
            'enabled': self.enabled_check.isChecked(),
            'max_instances': self.max_instances.value(),
            'misfire_grace_time': self.misfire_grace.value()
        }
        
        # Add date range if enabled
        if self.use_date_range.isChecked():
            config['start_date'] = self.start_date.dateTime().toPyDateTime()
            config['end_date'] = self.end_date.dateTime().toPyDateTime()
        
        if tab_index == 0:  # Interval
            total_seconds = (
                self.interval_days.value() * 86400 +
                self.interval_hours.value() * 3600 +
                self.interval_minutes.value() * 60 +
                self.interval_seconds.value()
            )
            
            if total_seconds <= 0:
                QMessageBox.warning(self, "Invalid Interval", 
                                   "Please specify a valid interval.\n\n"
                                   "At least one time unit (days, hours, minutes, or seconds) "
                                   "must be greater than zero.\n\n"
                                   "Examples:\n"
                                   "• 5 minutes for frequent checks\n"
                                   "• 1 hour for regular updates\n"
                                   "• 1 day for daily maintenance")
                return None
            
            config['schedule_type'] = 'interval'
            if self.interval_days.value() > 0:
                config['interval_days'] = self.interval_days.value()
            if self.interval_hours.value() > 0:
                config['interval_hours'] = self.interval_hours.value()
            if self.interval_minutes.value() > 0:
                config['interval_minutes'] = self.interval_minutes.value()
            if self.interval_seconds.value() > 0:
                config['interval_seconds'] = self.interval_seconds.value()
        
        elif tab_index == 1:  # Daily
            config['schedule_type'] = 'daily'
            config['time_of_day'] = self.daily_time.time().toString("HH:mm")
        
        elif tab_index == 2:  # Weekly
            days = [i for i, check in self.weekday_checks.items() if check.isChecked()]
            if not days:
                QMessageBox.warning(self, "Invalid Schedule", 
                                   "Please select at least one day of the week.\n\n"
                                   "You can use the preset buttons:\n"
                                   "• Weekdays: Monday through Friday\n"
                                   "• Weekends: Saturday and Sunday\n"
                                   "• All Days: Every day of the week")
                return None
            
            config['schedule_type'] = 'weekly'
            config['days_of_week'] = days
            config['time_of_day'] = self.weekly_time.time().toString("HH:mm")
        
        elif tab_index == 3:  # Monthly
            config['schedule_type'] = 'monthly'
            config['day_of_month'] = self.monthly_day.value()
            config['time_of_day'] = self.monthly_time.time().toString("HH:mm")
        
        elif tab_index == 4:  # Cron
            expression = self.cron_expression.text().strip()
            if not expression:
                QMessageBox.warning(self, "Invalid Schedule", 
                                   "Please enter a cron expression.\n\n"
                                   "You can use the Validate button to test your expression.\n\n"
                                   "Common patterns:\n"
                                   "• 0 9 * * * - Daily at 9:00 AM\n"
                                   "• 0 */2 * * * - Every 2 hours\n"
                                   "• 0 9 * * 1-5 - Weekdays at 9:00 AM")
                return None
            
            config['schedule_type'] = 'cron'
            config['cron_expression'] = expression
        
        elif tab_index == 5:  # Once
            config['schedule_type'] = 'once'
            config['run_date'] = self.once_datetime.dateTime().toPyDateTime()
        
        return config
    
    def _save_schedule(self):
        """Save the schedule configuration."""
        config = self._get_schedule_config()
        if not config:
            return
        
        if self.existing_schedule:
            self.schedule_updated.emit(self.script_name, config)
        else:
            self.schedule_created.emit(self.script_name, config)
        
        self.accept()