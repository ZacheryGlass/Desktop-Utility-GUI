"""
Settings View - UI component for application settings.

This view provides the settings dialog interface without business logic,
emitting signals for user interactions and updating display based on controller data.
"""
import logging
from typing import Dict, Any, List, Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QCheckBox,
    QLabel, QPushButton, QDialogButtonBox, QWidget, QTabWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QSpinBox, QComboBox, QListWidget, QListWidgetItem, QMessageBox,
    QFileDialog, QInputDialog, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QAction

logger = logging.getLogger('Views.Settings')


class SettingsView(QDialog):
    """
    View component for application settings dialog.
    
    This view:
    - Displays settings in a tabbed interface
    - Emits signals for user interactions
    - Updates display based on controller data
    - Contains no business logic
    """
    
    # Signals for user interactions
    # Startup settings
    run_on_startup_changed = pyqtSignal(bool)
    start_minimized_changed = pyqtSignal(bool)
    show_startup_notification_changed = pyqtSignal(bool)
    
    # Behavior settings
    minimize_to_tray_changed = pyqtSignal(bool)
    close_to_tray_changed = pyqtSignal(bool)
    single_instance_changed = pyqtSignal(bool)
    show_script_notifications_changed = pyqtSignal(bool)
    
    # Execution settings
    script_timeout_changed = pyqtSignal(int)
    status_refresh_changed = pyqtSignal(int)
    
    # Script management
    script_toggled = pyqtSignal(str, bool)  # script_name, enabled
    hotkey_configuration_requested = pyqtSignal(str)  # script_name
    custom_name_changed = pyqtSignal(str, str)  # script_name, custom_name
    external_script_add_requested = pyqtSignal(str)  # file_path
    external_script_remove_requested = pyqtSignal(str)  # script_name
    
    # Preset management
    preset_configuration_requested = pyqtSignal(str)  # script_name
    preset_deleted = pyqtSignal(str, str)  # script_name, preset_name
    auto_generate_presets_requested = pyqtSignal(str)  # script_name
    
    # Reset operations
    reset_requested = pyqtSignal(str)  # category
    
    # Dialog actions
    settings_accepted = pyqtSignal()
    settings_rejected = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # UI components
        self.tab_widget = None
        self.script_table = None
        self.preset_list = None
        
        # Checkboxes for settings
        self.run_on_startup_checkbox = None
        self.start_minimized_checkbox = None
        self.show_notification_checkbox = None
        self.minimize_to_tray_checkbox = None
        self.close_to_tray_checkbox = None
        self.single_instance_checkbox = None
        self.show_script_notifications_checkbox = None
        
        # Spinboxes for numeric settings
        self.timeout_spinbox = None
        self.refresh_spinbox = None
        
        # Track current data
        self._script_data = []
        self._preset_data = {}
        
        self._init_ui()
        
        logger.info("SettingsView initialized")
    
    def _init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.setMinimumSize(1100, 650)
        self.resize(1200, 700)  # Set a comfortable default size
        
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Create tabs
        self._create_general_tab()
        self._create_scripts_tab()
        self._create_presets_tab()
        self._create_reset_tab()
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self._on_reject)
        layout.addWidget(button_box)
    
    def _create_general_tab(self):
        """Create the General settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Startup Settings Group
        startup_group = QGroupBox("Startup")
        startup_layout = QVBoxLayout()
        
        self.run_on_startup_checkbox = QCheckBox("Run on system startup")
        self.run_on_startup_checkbox.toggled.connect(self.run_on_startup_changed.emit)
        startup_layout.addWidget(self.run_on_startup_checkbox)
        
        self.start_minimized_checkbox = QCheckBox("Start minimized to tray")
        self.start_minimized_checkbox.toggled.connect(self.start_minimized_changed.emit)
        startup_layout.addWidget(self.start_minimized_checkbox)
        
        self.show_notification_checkbox = QCheckBox("Show notification on startup")
        self.show_notification_checkbox.toggled.connect(self.show_startup_notification_changed.emit)
        startup_layout.addWidget(self.show_notification_checkbox)
        
        startup_group.setLayout(startup_layout)
        layout.addWidget(startup_group)
        
        # Behavior Settings Group
        behavior_group = QGroupBox("Behavior")
        behavior_layout = QVBoxLayout()
        
        self.minimize_to_tray_checkbox = QCheckBox("Minimize to system tray")
        self.minimize_to_tray_checkbox.toggled.connect(self.minimize_to_tray_changed.emit)
        behavior_layout.addWidget(self.minimize_to_tray_checkbox)
        
        self.close_to_tray_checkbox = QCheckBox("Close to system tray instead of exiting")
        self.close_to_tray_checkbox.toggled.connect(self.close_to_tray_changed.emit)
        behavior_layout.addWidget(self.close_to_tray_checkbox)
        
        self.single_instance_checkbox = QCheckBox("Allow only one instance")
        self.single_instance_checkbox.toggled.connect(self.single_instance_changed.emit)
        behavior_layout.addWidget(self.single_instance_checkbox)
        
        self.show_script_notifications_checkbox = QCheckBox("Show script execution notifications")
        self.show_script_notifications_checkbox.toggled.connect(self.show_script_notifications_changed.emit)
        behavior_layout.addWidget(self.show_script_notifications_checkbox)
        
        behavior_group.setLayout(behavior_layout)
        layout.addWidget(behavior_group)
        
        # Execution Settings Group
        execution_group = QGroupBox("Execution")
        execution_layout = QVBoxLayout()
        
        # Script timeout
        timeout_layout = QHBoxLayout()
        timeout_layout.addWidget(QLabel("Script timeout (seconds):"))
        self.timeout_spinbox = QSpinBox()
        self.timeout_spinbox.setMinimum(5)
        self.timeout_spinbox.setMaximum(300)
        self.timeout_spinbox.valueChanged.connect(self.script_timeout_changed.emit)
        timeout_layout.addWidget(self.timeout_spinbox)
        timeout_layout.addStretch()
        execution_layout.addLayout(timeout_layout)
        
        # Status refresh interval
        refresh_layout = QHBoxLayout()
        refresh_layout.addWidget(QLabel("Status refresh interval (seconds):"))
        self.refresh_spinbox = QSpinBox()
        self.refresh_spinbox.setMinimum(1)
        self.refresh_spinbox.setMaximum(60)
        self.refresh_spinbox.valueChanged.connect(self.status_refresh_changed.emit)
        refresh_layout.addWidget(self.refresh_spinbox)
        refresh_layout.addStretch()
        execution_layout.addLayout(refresh_layout)
        
        execution_group.setLayout(execution_layout)
        layout.addWidget(execution_group)
        
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "General")
    
    def _create_scripts_tab(self):
        """Create the Scripts management tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Instructions
        instructions = QLabel(
            "Manage scripts: Enable/disable, set hotkeys, customize names, and add external scripts."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Scripts table
        self.script_table = QTableWidget()
        self.script_table.setColumnCount(5)
        self.script_table.setHorizontalHeaderLabels([
            "SCRIPT", "STATUS", "HOTKEY", "CUSTOM NAME", "ACTIONS"
        ])
        
        # Configure table
        self.script_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.script_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.script_table.setAlternatingRowColors(True)
        self.script_table.verticalHeader().setVisible(False)  # Hide row numbers
        self.script_table.setShowGrid(True)  # Show grid lines for clarity
        
        # Set up proper column sizing
        header = self.script_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Script name stretches
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)  # Status checkbox - fixed width
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)  # Hotkey - fixed width
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)  # Custom Name
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)  # Actions - fixed width
        
        # Set proper column widths to prevent truncation and overlapping
        self.script_table.setColumnWidth(1, 80)   # STATUS - width for checkbox
        self.script_table.setColumnWidth(2, 200)  # HOTKEY - increased to show full hotkeys
        self.script_table.setColumnWidth(3, 150)  # CUSTOM NAME
        self.script_table.setColumnWidth(4, 120)  # ACTIONS - slightly wider
        
        layout.addWidget(self.script_table)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        add_external_btn = QPushButton("Add External Script...")
        add_external_btn.clicked.connect(self._on_add_external_script)
        button_layout.addWidget(add_external_btn)
        
        button_layout.addStretch()
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._refresh_script_table)
        button_layout.addWidget(refresh_btn)
        
        layout.addLayout(button_layout)
        
        self.tab_widget.addTab(tab, "Scripts")
    
    def _create_presets_tab(self):
        """Create the Script Presets/Arguments tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Instructions
        instructions = QLabel(
            "Configure preset arguments for scripts that accept parameters."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Script selection
        script_layout = QHBoxLayout()
        script_layout.addWidget(QLabel("Script:"))
        
        self.preset_script_combo = QComboBox()
        self.preset_script_combo.currentTextChanged.connect(self._on_preset_script_changed)
        script_layout.addWidget(self.preset_script_combo)
        
        script_layout.addStretch()
        layout.addLayout(script_layout)
        
        # Presets list
        self.preset_list = QListWidget()
        layout.addWidget(self.preset_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        add_preset_btn = QPushButton("Add Preset...")
        add_preset_btn.clicked.connect(self._on_add_preset)
        button_layout.addWidget(add_preset_btn)
        
        edit_preset_btn = QPushButton("Edit...")
        edit_preset_btn.clicked.connect(self._on_edit_preset)
        button_layout.addWidget(edit_preset_btn)
        
        delete_preset_btn = QPushButton("Delete")
        delete_preset_btn.clicked.connect(self._on_delete_preset)
        button_layout.addWidget(delete_preset_btn)
        
        button_layout.addStretch()
        
        auto_generate_btn = QPushButton("Auto-Generate")
        auto_generate_btn.clicked.connect(self._on_auto_generate_presets)
        auto_generate_btn.setToolTip("Automatically generate presets from script arguments")
        button_layout.addWidget(auto_generate_btn)
        
        layout.addLayout(button_layout)
        
        self.tab_widget.addTab(tab, "Script Args")
    
    def _create_reset_tab(self):
        """Create the Reset settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Warning
        warning = QLabel(
            "⚠️ Warning: Reset operations cannot be undone!\n\n"
            "Choose what you want to reset:"
        )
        warning.setStyleSheet("color: orange;")
        layout.addWidget(warning)
        
        # Reset buttons
        reset_all_btn = QPushButton("Reset All Settings to Defaults")
        reset_all_btn.clicked.connect(lambda: self._on_reset('all'))
        layout.addWidget(reset_all_btn)
        
        reset_hotkeys_btn = QPushButton("Clear All Hotkeys")
        reset_hotkeys_btn.clicked.connect(lambda: self._on_reset('hotkeys'))
        layout.addWidget(reset_hotkeys_btn)
        
        reset_presets_btn = QPushButton("Clear All Presets")
        reset_presets_btn.clicked.connect(lambda: self._on_reset('presets'))
        layout.addWidget(reset_presets_btn)
        
        reset_names_btn = QPushButton("Clear All Custom Names")
        reset_names_btn.clicked.connect(lambda: self._on_reset('custom_names'))
        layout.addWidget(reset_names_btn)
        
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "Reset")
    
    # Update slots (called by controller)
    def update_startup_settings(self, settings: Dict[str, Any]):
        """Update startup settings display"""
        self.run_on_startup_checkbox.setChecked(settings.get('run_on_startup', False))
        self.start_minimized_checkbox.setChecked(settings.get('start_minimized', True))
        self.show_notification_checkbox.setChecked(settings.get('show_notification', True))
    
    def update_behavior_settings(self, settings: Dict[str, Any]):
        """Update behavior settings display"""
        self.minimize_to_tray_checkbox.setChecked(settings.get('minimize_to_tray', True))
        self.close_to_tray_checkbox.setChecked(settings.get('close_to_tray', True))
        self.single_instance_checkbox.setChecked(settings.get('single_instance', True))
        self.show_script_notifications_checkbox.setChecked(
            settings.get('show_script_notifications', True)
        )
    
    def update_execution_settings(self, settings: Dict[str, Any]):
        """Update execution settings display"""
        self.timeout_spinbox.setValue(settings.get('script_timeout_seconds', 30))
        self.refresh_spinbox.setValue(settings.get('status_refresh_seconds', 5))
    
    def update_script_list(self, scripts: List[Dict[str, Any]]):
        """Update the scripts table"""
        self._script_data = scripts
        self._refresh_script_table()
        self._update_preset_script_combo()
    
    def update_preset_list(self, script_name: str, presets: Dict[str, Any]):
        """Update the preset list for a script"""
        self._preset_data[script_name] = presets
        
        # If this is the currently selected script, update the list
        if self.preset_script_combo.currentText() == script_name:
            self._refresh_preset_list(presets)
    
    def show_error(self, title: str, message: str):
        """Show an error message"""
        QMessageBox.critical(self, title, message)
    
    def show_info(self, title: str, message: str):
        """Show an information message"""
        QMessageBox.information(self, title, message)
    
    # Internal UI update methods
    def _refresh_script_table(self):
        """Refresh the scripts table display"""
        self.script_table.setRowCount(len(self._script_data))
        
        for row, script in enumerate(self._script_data):
            # Script name - use full display name
            name_item = QTableWidgetItem(script['display_name'])
            if script['is_external']:
                name_item.setToolTip(f"External script: {script.get('file_path', '')}")
            else:
                name_item.setToolTip(script['display_name'])
            self.script_table.setItem(row, 0, name_item)
            
            # Status (enabled/disabled) - center the checkbox
            status_container = QWidget()
            status_layout = QHBoxLayout(status_container)
            status_layout.setContentsMargins(2, 2, 2, 2)  # Small margins to prevent overflow
            status_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            status_checkbox = QCheckBox()
            status_checkbox.setChecked(not script['is_disabled'])
            status_checkbox.toggled.connect(
                lambda checked, s=script['name']: self.script_toggled.emit(s, checked)
            )
            status_layout.addWidget(status_checkbox)
            self.script_table.setCellWidget(row, 1, status_container)
            
            # Hotkey - show full hotkey text with proper sizing
            hotkey_text = script.get('hotkey', '')
            if not hotkey_text:
                hotkey_text = 'Click to set'
            hotkey_btn = QPushButton(hotkey_text)
            hotkey_btn.setMaximumHeight(28)  # Prevent button from being too tall
            hotkey_btn.setStyleSheet("QPushButton { text-align: center; padding: 2px 4px; }")
            hotkey_btn.setToolTip(f"Current hotkey: {hotkey_text}\nClick to change")
            hotkey_btn.clicked.connect(
                lambda checked, s=script['name']: self.hotkey_configuration_requested.emit(s)
            )
            self.script_table.setCellWidget(row, 2, hotkey_btn)
            
            # Custom name
            custom_name = script.get('custom_name', '')
            custom_btn_text = custom_name if custom_name else 'Set...'
            custom_name_btn = QPushButton(custom_btn_text)
            custom_name_btn.setMaximumHeight(28)  # Consistent height with hotkey button
            custom_name_btn.setStyleSheet("QPushButton { text-align: center; padding: 2px 4px; }")
            custom_name_btn.setToolTip(f"Custom name: {custom_name}" if custom_name else "Click to set a custom name")
            custom_name_btn.clicked.connect(
                lambda checked, s=script['name']: self._on_set_custom_name(s)
            )
            self.script_table.setCellWidget(row, 3, custom_name_btn)
            
            # Actions
            if script['is_external']:
                remove_btn = QPushButton("Remove")
                remove_btn.setMaximumHeight(28)  # Consistent height
                remove_btn.setStyleSheet("QPushButton { padding: 2px 4px; }")
                remove_btn.setToolTip(f"Remove external script: {script['display_name']}")
                remove_btn.clicked.connect(
                    lambda checked, s=script['name']: self.external_script_remove_requested.emit(s)
                )
                self.script_table.setCellWidget(row, 4, remove_btn)
            else:
                # For built-in scripts, show a disabled placeholder or leave empty
                placeholder = QLabel("Built-in")
                placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
                placeholder.setStyleSheet("color: #999;")
                self.script_table.setCellWidget(row, 4, placeholder)
        
        # Set consistent row height and ensure proper layout
        self.script_table.resizeRowsToContents()
        # Add a bit of padding to rows
        for row in range(self.script_table.rowCount()):
            self.script_table.setRowHeight(row, 32)  # Fixed height for consistency
    
    def _update_preset_script_combo(self):
        """Update the script combo box in presets tab"""
        current = self.preset_script_combo.currentText()
        self.preset_script_combo.clear()
        
        # Add scripts that have arguments
        for script in self._script_data:
            if script.get('has_arguments'):
                self.preset_script_combo.addItem(script['display_name'])
        
        # Try to restore selection
        if current:
            index = self.preset_script_combo.findText(current)
            if index >= 0:
                self.preset_script_combo.setCurrentIndex(index)
    
    def _refresh_preset_list(self, presets: Dict[str, Any]):
        """Refresh the preset list display"""
        self.preset_list.clear()
        
        for preset_name, args in presets.items():
            args_str = ', '.join(f"{k}={v}" for k, v in args.items())
            item_text = f"{preset_name}: {args_str}"
            self.preset_list.addItem(item_text)
    
    # UI event handlers
    def _on_accept(self):
        """Handle dialog accept"""
        self.settings_accepted.emit()
        self.accept()
    
    def _on_reject(self):
        """Handle dialog reject"""
        self.settings_rejected.emit()
        self.reject()
    
    def _on_add_external_script(self):
        """Handle add external script button"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Python Script",
            "",
            "Python Scripts (*.py)"
        )
        
        if file_path:
            # Emit signal with file path
            self.external_script_add_requested.emit(file_path)
    
    def _on_set_custom_name(self, script_name: str):
        """Handle set custom name button"""
        current_name = next(
            (s.get('custom_name') for s in self._script_data if s['name'] == script_name),
            script_name
        )
        
        new_name, ok = QInputDialog.getText(
            self,
            "Custom Name",
            f"Enter custom name for {script_name}:",
            text=current_name
        )
        
        if ok:
            self.custom_name_changed.emit(script_name, new_name)
    
    def _on_preset_script_changed(self, script_name: str):
        """Handle preset script selection change"""
        if script_name and script_name in self._preset_data:
            self._refresh_preset_list(self._preset_data[script_name])
        else:
            self.preset_list.clear()
    
    def _on_add_preset(self):
        """Handle add preset button"""
        script_name = self.preset_script_combo.currentText()
        if script_name:
            self.preset_configuration_requested.emit(script_name)
    
    def _on_edit_preset(self):
        """Handle edit preset button"""
        current_item = self.preset_list.currentItem()
        if current_item:
            # Extract preset name from the display text
            preset_text = current_item.text()
            preset_name = preset_text.split(':')[0]
            script_name = self.preset_script_combo.currentText()
            
            # Emit signal for editing
            self.preset_configuration_requested.emit(script_name)
    
    def _on_delete_preset(self):
        """Handle delete preset button"""
        current_item = self.preset_list.currentItem()
        if current_item:
            preset_text = current_item.text()
            preset_name = preset_text.split(':')[0]
            script_name = self.preset_script_combo.currentText()
            
            reply = QMessageBox.question(
                self,
                "Delete Preset",
                f"Delete preset '{preset_name}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.preset_deleted.emit(script_name, preset_name)
    
    def _on_auto_generate_presets(self):
        """Handle auto-generate presets button"""
        script_name = self.preset_script_combo.currentText()
        if script_name:
            self.auto_generate_presets_requested.emit(script_name)
    
    def _on_reset(self, category: str):
        """Handle reset button"""
        message = {
            'all': "This will reset ALL settings to defaults.",
            'hotkeys': "This will clear all hotkey assignments.",
            'presets': "This will delete all script presets.",
            'custom_names': "This will clear all custom script names."
        }.get(category, "This operation cannot be undone.")
        
        reply = QMessageBox.warning(
            self,
            "Confirm Reset",
            f"{message}\n\nAre you sure you want to continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.reset_requested.emit(category)