import logging
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QCheckBox, QComboBox, QLabel, QPushButton,
                             QDialogButtonBox, QMessageBox, QWidget)
from PyQt6.QtCore import Qt, pyqtSignal

from core.settings import SettingsManager
from core.startup_manager import StartupManager

logger = logging.getLogger('GUI.SettingsDialog')

class SettingsDialog(QDialog):
    settings_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = SettingsManager()
        self.startup_manager = StartupManager()
        self.init_ui()
        self.load_settings()
        
    def init_ui(self):
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        # Startup Settings Group
        startup_group = QGroupBox("Startup")
        startup_layout = QVBoxLayout()
        
        self.run_on_startup_checkbox = QCheckBox("Run on Windows startup")
        self.run_on_startup_checkbox.setToolTip("Start Desktop Utilities when Windows starts")
        startup_layout.addWidget(self.run_on_startup_checkbox)
        
        self.start_minimized_checkbox = QCheckBox("Start minimized to system tray")
        self.start_minimized_checkbox.setToolTip("Hide the main window on startup")
        startup_layout.addWidget(self.start_minimized_checkbox)
        
        self.show_startup_notification = QCheckBox("Show notification when started")
        self.show_startup_notification.setToolTip("Display a system tray notification on startup")
        startup_layout.addWidget(self.show_startup_notification)
        
        startup_group.setLayout(startup_layout)
        layout.addWidget(startup_group)
        
        # Behavior Settings Group
        behavior_group = QGroupBox("Behavior")
        behavior_layout = QVBoxLayout()
        
        self.minimize_to_tray_checkbox = QCheckBox("Minimize to system tray")
        self.minimize_to_tray_checkbox.setToolTip("Hide to system tray when minimized")
        behavior_layout.addWidget(self.minimize_to_tray_checkbox)
        
        self.close_to_tray_checkbox = QCheckBox("Close to system tray")
        self.close_to_tray_checkbox.setToolTip("Hide to system tray instead of exiting when closed")
        behavior_layout.addWidget(self.close_to_tray_checkbox)
        
        self.single_instance_checkbox = QCheckBox("Allow only one instance")
        self.single_instance_checkbox.setToolTip("Prevent multiple instances of the application")
        behavior_layout.addWidget(self.single_instance_checkbox)
        
        self.show_notifications_checkbox = QCheckBox("Show script execution notifications")
        self.show_notifications_checkbox.setToolTip("Display notifications when scripts are executed")
        behavior_layout.addWidget(self.show_notifications_checkbox)
        
        behavior_group.setLayout(behavior_layout)
        layout.addWidget(behavior_group)
        
        # Appearance Settings Group
        appearance_group = QGroupBox("Appearance")
        appearance_layout = QVBoxLayout()
        
        theme_layout = QHBoxLayout()
        theme_label = QLabel("Theme:")
        theme_layout.addWidget(theme_label)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light"])
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()
        
        appearance_layout.addLayout(theme_layout)
        appearance_group.setLayout(appearance_layout)
        layout.addWidget(appearance_group)
        
        # Add stretch to push buttons to bottom
        layout.addStretch()
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel |
            QDialogButtonBox.StandardButton.Apply
        )
        
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self.apply_settings)
        
        layout.addWidget(button_box)
        
        # Connect change handlers
        self.run_on_startup_checkbox.stateChanged.connect(self._on_startup_changed)
    
    def load_settings(self):
        # Load startup settings
        self.run_on_startup_checkbox.setChecked(self.startup_manager.is_registered())
        self.start_minimized_checkbox.setChecked(self.settings.is_start_minimized())
        self.show_startup_notification.setChecked(self.settings.get('startup/show_notification', True))
        
        # Load behavior settings
        self.minimize_to_tray_checkbox.setChecked(self.settings.is_minimize_to_tray())
        self.close_to_tray_checkbox.setChecked(self.settings.is_close_to_tray())
        self.single_instance_checkbox.setChecked(self.settings.get('behavior/single_instance', True))
        self.show_notifications_checkbox.setChecked(self.settings.should_show_notifications())
        
        # Load appearance settings
        current_theme = self.settings.get_theme()
        self.theme_combo.setCurrentText(current_theme.capitalize())
    
    def apply_settings(self):
        try:
            # Save startup settings
            run_on_startup = self.run_on_startup_checkbox.isChecked()
            if not self.startup_manager.set_startup(run_on_startup):
                QMessageBox.warning(self, "Warning", 
                                   "Failed to update Windows startup settings. "
                                   "You may need to run the application as administrator.")
            
            self.settings.set_start_minimized(self.start_minimized_checkbox.isChecked())
            self.settings.set('startup/show_notification', self.show_startup_notification.isChecked())
            
            # Save behavior settings
            self.settings.set('behavior/minimize_to_tray', self.minimize_to_tray_checkbox.isChecked())
            self.settings.set('behavior/close_to_tray', self.close_to_tray_checkbox.isChecked())
            self.settings.set('behavior/single_instance', self.single_instance_checkbox.isChecked())
            self.settings.set('behavior/show_script_notifications', self.show_notifications_checkbox.isChecked())
            
            # Save appearance settings
            new_theme = self.theme_combo.currentText().lower()
            self.settings.set_theme(new_theme)
            
            # Sync settings
            self.settings.sync()
            
            # Emit signal that settings have changed
            self.settings_changed.emit()
            
            logger.info("Settings applied successfully")
            
        except Exception as e:
            logger.error(f"Error applying settings: {e}")
            QMessageBox.critical(self, "Error", f"Failed to apply settings: {str(e)}")
    
    def accept(self):
        self.apply_settings()
        super().accept()
    
    def _on_startup_changed(self, state):
        # Enable/disable "start minimized" when startup is toggled
        self.start_minimized_checkbox.setEnabled(state == Qt.CheckState.Checked.value)
        self.show_startup_notification.setEnabled(state == Qt.CheckState.Checked.value)