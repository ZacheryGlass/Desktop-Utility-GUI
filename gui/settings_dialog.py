import logging
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QCheckBox, QComboBox, QLabel, QPushButton,
                             QDialogButtonBox, QMessageBox, QWidget, QTabWidget,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QAbstractItemView, QFontComboBox, QSpinBox, QFileDialog,
                             QInputDialog)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from core.settings import SettingsManager
from core.startup_manager import StartupManager
from core.script_loader import ScriptLoader
from core.hotkey_registry import HotkeyRegistry
from gui.hotkey_configurator import HotkeyConfigDialog
from gui.preset_editor import PresetEditorDialog

# UI Theme Constants
CUSTOM_NAME_COLOR = Qt.GlobalColor.cyan

logger = logging.getLogger('GUI.SettingsDialog')

class ScriptNameWidget(QWidget):
    """Custom widget for script names with +/- buttons"""
    
    def __init__(self, script_name: str, is_external: bool, is_disabled: bool, parent=None):
        super().__init__(parent)
        self.script_name = script_name
        self.is_external = is_external
        self.is_disabled = is_disabled
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(8)
        
        # Script name label
        self.name_label = QLabel(script_name)
        self.name_label.setStyleSheet("color: white;")
        layout.addWidget(self.name_label)
        
        # Spacer to push button to the right
        layout.addStretch()
        
        # +/- button
        self.action_button = QPushButton()
        self.action_button.setMaximumSize(20, 20)
        self.action_button.setMinimumSize(20, 20)
        self.action_button.setStyleSheet("""
            QPushButton {
                background-color: #555555;
                border: 1px solid #777777;
                color: white;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #666666;
            }
            QPushButton:pressed {
                background-color: #444444;
            }
        """)
        
        self.update_button_state()
        layout.addWidget(self.action_button)
        
    def update_button_state(self):
        """Update button text and tooltip based on script state"""
        if self.is_external:
            # External scripts always show "-" for removal
            self.action_button.setText("-")
            self.action_button.setToolTip("Remove external script")
        elif self.is_disabled:
            # Disabled native scripts show "+" for enabling
            self.action_button.setText("+")
            self.action_button.setToolTip("Enable script")
            self.name_label.setStyleSheet("color: #888888;")  # Gray out disabled scripts
        else:
            # Enabled native scripts show "-" for disabling  
            self.action_button.setText("-")
            self.action_button.setToolTip("Disable script")
            self.name_label.setStyleSheet("color: white;")
    
    def set_disabled_state(self, disabled: bool):
        """Update the disabled state and refresh the UI"""
        self.is_disabled = disabled
        self.update_button_state()

class AddNewScriptWidget(QWidget):
    """Special widget for the 'Add New Script...' row"""
    add_script_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(8)
        
        # "Add New Script..." label
        self.label = QLabel("+ Add New Script...")
        self.label.setStyleSheet("color: cyan; font-style: italic;")
        self.label.setToolTip("Click to add an external Python script")
        layout.addWidget(self.label)
        
        # Spacer to fill the rest
        layout.addStretch()
        
        # Make the entire widget clickable
        self.setToolTip("Click to add an external Python script")
        
    def mousePressEvent(self, event):
        """Handle mouse clicks on the widget"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.add_script_clicked.emit()
        super().mousePressEvent(event)

class SettingsDialog(QDialog):
    settings_changed = pyqtSignal()
    hotkeys_changed = pyqtSignal()
    scripts_changed = pyqtSignal()  # Emitted when scripts are added/removed/disabled/enabled
    
    def __init__(self, script_loader: ScriptLoader = None, parent=None):
        super().__init__(parent)
        self.settings = SettingsManager()
        self.startup_manager = StartupManager()
        self.script_loader = script_loader
        self.hotkey_registry = HotkeyRegistry(self.settings)
        self.init_ui()
        self.load_settings()
        
    def init_ui(self):
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.setMinimumSize(800, 500)
        
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Create and add General tab
        self.general_tab = self._create_general_tab()
        self.tab_widget.addTab(self.general_tab, "General")
        
        # Create and add Scripts tab
        self.scripts_tab = self._create_scripts_tab()
        self.tab_widget.addTab(self.scripts_tab, "Scripts")
        
        # Create and add Presets tab
        self.presets_tab = self._create_presets_tab()
        self.tab_widget.addTab(self.presets_tab, "Script Args")
        
        # Create and add Reset tab
        self.reset_tab = self._create_reset_tab()
        self.tab_widget.addTab(self.reset_tab, "💀")
        
        # External script functionality is now integrated into Scripts tab
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        
        button_box.accepted.connect(self.accept)
        
        layout.addWidget(button_box)
    
    def _create_general_tab(self) -> QWidget:
        """Create the General settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
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
        
        # Font family selection
        font_layout = QHBoxLayout()
        font_layout.addWidget(QLabel("Font Family:"))
        self.font_combo = QFontComboBox()
        self.font_combo.setToolTip("Select the font family for the application")
        font_layout.addWidget(self.font_combo)
        appearance_layout.addLayout(font_layout)
        
        # Font size selection
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Font Size:"))
        self.font_size_spinbox = QSpinBox()
        self.font_size_spinbox.setRange(6, 24)
        self.font_size_spinbox.setSuffix(" pt")
        self.font_size_spinbox.setToolTip("Select the font size for the application")
        size_layout.addWidget(self.font_size_spinbox)
        size_layout.addStretch()  # Push spinbox to the left
        appearance_layout.addLayout(size_layout)
        
        appearance_group.setLayout(appearance_layout)
        layout.addWidget(appearance_group)
        
        # Add stretch to push content to top
        layout.addStretch()
        
        # Connect immediate save handlers
        # Startup settings
        self.run_on_startup_checkbox.stateChanged.connect(self._on_run_on_startup_changed)
        self.start_minimized_checkbox.stateChanged.connect(self._on_start_minimized_changed)
        self.show_startup_notification.stateChanged.connect(self._on_show_startup_notification_changed)
        
        # Behavior settings
        self.minimize_to_tray_checkbox.stateChanged.connect(self._on_minimize_to_tray_changed)
        self.close_to_tray_checkbox.stateChanged.connect(self._on_close_to_tray_changed)
        self.single_instance_checkbox.stateChanged.connect(self._on_single_instance_changed)
        self.show_notifications_checkbox.stateChanged.connect(self._on_show_notifications_changed)
        
        # Appearance settings
        self.font_combo.currentTextChanged.connect(self._on_font_family_changed)
        self.font_size_spinbox.valueChanged.connect(self._on_font_size_changed)
        
        # Handler for startup dependencies (enabling/disabling dependent controls)
        self.run_on_startup_checkbox.stateChanged.connect(self._on_startup_changed)
        
        return widget

    def _create_scripts_tab(self) -> QWidget:
        """Create the Scripts configuration tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Instructions
        instructions = QLabel(
            "Configure display names and hotkeys for scripts. Click on a cell to edit its value. "
            "Click the \"Add New Script...\" row at the bottom to add external Python scripts."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        # Create table for script configuration
        self.scripts_table = QTableWidget()
        self.scripts_table.setColumnCount(3)
        self.scripts_table.setHorizontalHeaderLabels(["Script", "Display Name", "Hotkey"])

        # Set table styling
        self.scripts_table.setStyleSheet("""
            QTableWidget {
                background-color: #2b2b2b;
                alternate-background-color: #3c3c3c;
                gridline-color: #555555;
                color: #ffffff;
            }
            QTableWidget::item {
                padding: 4px;
                color: #ffffff;
            }
            QTableWidget::item:selected {
                background-color: #0078d4;
            }
            QHeaderView::section {
                background-color: #404040;
                color: #ffffff;
                padding: 4px;
                border: 1px solid #555555;
            }
        """)

        # Configure table
        self.scripts_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.scripts_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.scripts_table.horizontalHeader().setStretchLastSection(True)
        self.scripts_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.scripts_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.scripts_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)

        # Connect cell click and context menu handlers
        self.scripts_table.cellClicked.connect(self._on_script_cell_clicked)

        layout.addWidget(self.scripts_table)

        # Refresh button
        refresh_button = QPushButton("Refresh Scripts")
        refresh_button.clicked.connect(self._refresh_all_script_data)
        layout.addWidget(refresh_button)

        # Load scripts table
        self._refresh_scripts_table()

        return widget
    
    def _create_presets_tab(self) -> QWidget:
        """Create the Script Presets configuration tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Instructions
        instructions = QLabel(
            "Manage preset configurations for scripts that require arguments. "
            "Create multiple presets with different argument values for easy execution."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Script selection
        script_selection_layout = QHBoxLayout()
        script_selection_layout.addWidget(QLabel("Script:"))
        
        self.presets_script_combo = QComboBox()
        self.presets_script_combo.currentTextChanged.connect(self._on_preset_script_changed)
        script_selection_layout.addWidget(self.presets_script_combo)
        
        script_selection_layout.addStretch()
        layout.addLayout(script_selection_layout)
        
        # Presets table
        self.presets_table = QTableWidget()
        self.presets_table.setColumnCount(2)
        self.presets_table.setHorizontalHeaderLabels(["Preset Name", "Arguments"])
        
        # Set table styling
        self.presets_table.setStyleSheet("""
            QTableWidget {
                background-color: #2b2b2b;
                alternate-background-color: #3c3c3c;
                gridline-color: #555555;
                color: #ffffff;
            }
            QTableWidget::item {
                padding: 4px;
                color: #ffffff;
            }
            QTableWidget::item:selected {
                background-color: #0078d4;
            }
            QHeaderView::section {
                background-color: #404040;
                color: #ffffff;
                padding: 4px;
                border: 1px solid #555555;
            }
        """)
        
        # Configure table
        self.presets_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.presets_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.presets_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.presets_table)
        
        # Buttons
        preset_buttons_layout = QHBoxLayout()
        
        add_preset_button = QPushButton("Add Preset")
        add_preset_button.clicked.connect(self._add_preset)
        preset_buttons_layout.addWidget(add_preset_button)
        
        edit_preset_button = QPushButton("Edit Preset")
        edit_preset_button.clicked.connect(self._edit_preset)
        preset_buttons_layout.addWidget(edit_preset_button)
        
        delete_preset_button = QPushButton("Delete Preset")
        delete_preset_button.clicked.connect(self._delete_preset)
        preset_buttons_layout.addWidget(delete_preset_button)
        
        preset_buttons_layout.addStretch()
        layout.addLayout(preset_buttons_layout)
        
        # Load initial data
        self._refresh_presets_script_combo()
        
        return widget
    
    def _create_reset_tab(self) -> QWidget:
        """Create the Reset Settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)
        
        # Warning section
        warning_group = QGroupBox("⚠️ Danger Zone")
        warning_layout = QVBoxLayout()
        
        warning_text = QLabel(
            "This will permanently delete all application settings, including:\n"
            "• General preferences and startup settings\n"
            "• Font and appearance settings\n"
            "• Script display names and hotkey assignments\n"
            "• External script configurations\n"
            "• Script presets and argument values\n"
            "• Disabled script states\n\n"
            "This action cannot be undone. The application will restart with default settings."
        )
        warning_text.setWordWrap(True)
        warning_text.setStyleSheet("""
            QLabel {
                color: #ffaa00;
                background-color: #2b2b2b;
                padding: 12px;
                border: 1px solid #555555;
                border-radius: 4px;
            }
        """)
        warning_layout.addWidget(warning_text)
        
        warning_group.setLayout(warning_layout)
        layout.addWidget(warning_group)
        
        # Button section
        button_section = QVBoxLayout()
        
        reset_button = QPushButton("💀 Reset All Settings 💀")
        reset_button.setMinimumHeight(50)
        reset_button.setStyleSheet("""
            QPushButton {
                background-color: #cc0000;
                color: white;
                font-weight: bold;
                font-size: 14px;
                border: 2px solid #ff0000;
                border-radius: 6px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #ff0000;
                border-color: #ff3333;
            }
            QPushButton:pressed {
                background-color: #990000;
                border-color: #cc0000;
            }
        """)
        reset_button.clicked.connect(self._reset_all_settings)
        
        button_section.addWidget(reset_button)
        layout.addLayout(button_section)
        
        # Add stretch to push content to top
        layout.addStretch()
        
        return widget

    def load_settings(self):
        # Block signals to prevent immediate-save handlers from firing during initialization
        controls_to_block = [
            self.run_on_startup_checkbox, self.start_minimized_checkbox,
            self.show_startup_notification, self.minimize_to_tray_checkbox,
            self.close_to_tray_checkbox, self.single_instance_checkbox,
            self.show_notifications_checkbox, self.font_combo, self.font_size_spinbox
        ]
        
        for control in controls_to_block:
            control.blockSignals(True)
        
        try:
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
            font_family = self.settings.get_font_family()
            if font_family != 'System Default':
                self.font_combo.setCurrentText(font_family)
            self.font_size_spinbox.setValue(self.settings.get_font_size())
        finally:
            # Re-enable signals
            for control in controls_to_block:
                control.blockSignals(False)
        
    
    
    def accept(self):
        super().accept()
    
    def _on_run_on_startup_changed(self, checked):
        """Handle immediate saving of run on startup setting"""
        try:
            if not self.startup_manager.set_startup(checked):
                QMessageBox.warning(self, "Warning", 
                                   "Failed to update Windows startup settings. "
                                   "You may need to run the application as administrator.")
                # Revert the checkbox if setting failed
                self.run_on_startup_checkbox.blockSignals(True)
                self.run_on_startup_checkbox.setChecked(not checked)
                self.run_on_startup_checkbox.blockSignals(False)
        except Exception as e:
            logger.error(f"Error setting startup: {e}")
            QMessageBox.critical(self, "Error", f"Failed to update startup settings: {str(e)}")
    
    def _on_start_minimized_changed(self, checked):
        """Handle immediate saving of start minimized setting"""
        try:
            self.settings.set_start_minimized(checked)
        except Exception as e:
            logger.error(f"Error setting start minimized: {e}")
    
    def _on_show_startup_notification_changed(self, checked):
        """Handle immediate saving of startup notification setting"""
        try:
            self.settings.set('startup/show_notification', checked)
        except Exception as e:
            logger.error(f"Error setting startup notification: {e}")
    
    def _on_minimize_to_tray_changed(self, checked):
        """Handle immediate saving of minimize to tray setting"""
        try:
            self.settings.set('behavior/minimize_to_tray', checked)
        except Exception as e:
            logger.error(f"Error setting minimize to tray: {e}")
    
    def _on_close_to_tray_changed(self, checked):
        """Handle immediate saving of close to tray setting"""
        try:
            self.settings.set('behavior/close_to_tray', checked)
        except Exception as e:
            logger.error(f"Error setting close to tray: {e}")
    
    def _on_single_instance_changed(self, checked):
        """Handle immediate saving of single instance setting"""
        try:
            self.settings.set('behavior/single_instance', checked)
        except Exception as e:
            logger.error(f"Error setting single instance: {e}")
    
    def _on_show_notifications_changed(self, checked):
        """Handle immediate saving of show notifications setting"""
        try:
            self.settings.set('behavior/show_script_notifications', checked)
        except Exception as e:
            logger.error(f"Error setting show notifications: {e}")
    
    def _on_font_family_changed(self, font_family):
        """Handle immediate saving of font family setting"""
        try:
            self.settings.set_font_family(font_family)
            self.settings_changed.emit()
        except Exception as e:
            logger.error(f"Error setting font family: {e}")
    
    def _on_font_size_changed(self, font_size):
        """Handle immediate saving of font size setting"""
        try:
            self.settings.set_font_size(font_size)
            self.settings_changed.emit()
        except Exception as e:
            logger.error(f"Error setting font size: {e}")
    
    def _on_startup_changed(self, state):
        # Enable/disable "start minimized" when startup is toggled
        self.start_minimized_checkbox.setEnabled(state == Qt.CheckState.Checked.value)
        self.show_startup_notification.setEnabled(state == Qt.CheckState.Checked.value)
    
    def _refresh_scripts_table(self):
        """Refresh the scripts table with current scripts"""
        self.scripts_table.setRowCount(0)
        
        if not self.script_loader:
            return
        
        scripts = self.script_loader.discover_scripts()
        external_scripts = self.settings.get_external_scripts()
        disabled_scripts = self.settings.get_disabled_scripts()
        
        for script_info in scripts:
            try:
                original_name = script_info.display_name
                script_filename = script_info.file_path.name
                display_name = self.script_loader.get_script_display_name(script_info)
                hotkey = self.hotkey_registry.get_hotkey(original_name)
                
                # Check script states
                is_external = original_name in external_scripts
                is_disabled = original_name in disabled_scripts and not is_external  # Only native scripts can be disabled

                row_position = self.scripts_table.rowCount()
                self.scripts_table.insertRow(row_position)

                # Custom script name widget with +/- button
                script_widget = ScriptNameWidget(script_filename, is_external, is_disabled, self)
                script_widget.action_button.clicked.connect(
                    lambda checked, name=original_name, external=is_external: 
                    self._on_script_action_button_clicked(name, external)
                )
                
                # Store script_info in the widget for later reference
                script_widget.setProperty("script_info", script_info)
                
                self.scripts_table.setCellWidget(row_position, 0, script_widget)

                # Display Name
                display_item = QTableWidgetItem(display_name)
                display_item.setToolTip("Click to edit display name")
                display_item.setData(Qt.ItemDataRole.UserRole, script_info)  # Store script_info for click handling
                
                # Apply styling based on script state
                if is_disabled:
                    display_item.setForeground(Qt.GlobalColor.gray)
                else:
                    custom_name = self.settings.get_custom_name(original_name)
                    if custom_name:
                        display_item.setForeground(CUSTOM_NAME_COLOR)
                        font = display_item.font()
                        font.setItalic(True)
                        display_item.setFont(font)
                    else:
                        display_item.setForeground(Qt.GlobalColor.white)
                self.scripts_table.setItem(row_position, 1, display_item)

                # Hotkey
                hotkey_item = QTableWidgetItem(hotkey if hotkey else "(empty)")
                hotkey_item.setData(Qt.ItemDataRole.UserRole, script_info)  # Store script_info for click handling
                
                if is_disabled:
                    hotkey_item.setForeground(Qt.GlobalColor.gray)
                else:
                    hotkey_item.setForeground(Qt.GlobalColor.white if hotkey else Qt.GlobalColor.gray)
                self.scripts_table.setItem(row_position, 2, hotkey_item)
                

            except Exception as e:
                logger.error(f"Error adding script to scripts table: {e}")
        
        # Add the "Add New Script..." row at the bottom
        row_position = self.scripts_table.rowCount()
        self.scripts_table.insertRow(row_position)
        
        # Create special ScriptNameWidget for adding new scripts
        add_script_widget = AddNewScriptWidget(self)
        add_script_widget.add_script_clicked.connect(self._add_external_script)
        self.scripts_table.setCellWidget(row_position, 0, add_script_widget)
        
        empty_item1 = QTableWidgetItem("")
        empty_item1.setForeground(Qt.GlobalColor.gray)
        self.scripts_table.setItem(row_position, 1, empty_item1)
        
        empty_item2 = QTableWidgetItem("")
        empty_item2.setForeground(Qt.GlobalColor.gray)
        self.scripts_table.setItem(row_position, 2, empty_item2)
        
    def _refresh_all_script_data(self):
        """Refresh all script-related data across all tabs for fluid updates"""
        if self.script_loader:
            self.script_loader.refresh_external_scripts()
        self._refresh_scripts_table()
        self._refresh_presets_script_combo()
        self.scripts_changed.emit()

    def _on_script_cell_clicked(self, row: int, column: int):
        """Handle clicks on cells in the scripts table"""
        if column == 0:
            # Column 0 uses custom widgets now, so clicks are handled by the +/- button
            return
        
        # For columns 1 and 2, get script info from the clicked item
        clicked_item = self.scripts_table.item(row, column)
        if not clicked_item:
            return
        
        script_data = clicked_item.data(Qt.ItemDataRole.UserRole)
        if not script_data:
            return
        
        # Regular script handling
        script_info = script_data
        original_name = script_info.display_name

        if column == 1:  # Display Name
            self._edit_display_name(row, original_name)
        elif column == 2:  # Hotkey
            self._edit_hotkey(row, original_name)
    
    def _on_script_action_button_clicked(self, script_name: str, is_external: bool):
        """Handle +/- button clicks with different logic for native vs external scripts"""
        if is_external:
            # External script: remove it entirely
            self._remove_external_script(script_name)
        else:
            # Native script: toggle enabled/disabled state
            current_disabled = self.settings.is_script_disabled(script_name)
            self.settings.set_script_disabled(script_name, not current_disabled)
            
            # Refresh the table to show the updated state
            self._refresh_scripts_table()
            
            # Refresh the Script Args tab since script availability may have changed
            self._refresh_presets_script_combo()
            
            # Emit signal to notify other components (like tray manager)
            self.scripts_changed.emit()

    def _edit_display_name(self, row: int, original_name: str):
        """Handle editing of display name"""
        from PyQt6.QtWidgets import QInputDialog
        
        current_custom_name = self.settings.get_custom_name(original_name)
        current_display = current_custom_name if current_custom_name else original_name
        
        new_name, ok = QInputDialog.getText(
            self,
            "Edit Display Name",
            f"Display name for '{original_name}':",
            text=current_display
        )
        
        if ok and new_name.strip():
            new_name = new_name.strip()
            if new_name != original_name:
                scripts = self.script_loader.discover_scripts()
                script_names = [script_info.display_name for script_info in scripts]
                
                if not self.settings.set_custom_name(original_name, new_name, script_names):
                    QMessageBox.warning(
                        self,
                        "Invalid Display Name",
                        f"The display name '{new_name}' is invalid. It may conflict with an existing script name "
                        f"or custom name, be too long (max 50 characters), or contain invalid characters."
                    )
                    return
            else:
                self.settings.remove_custom_name(original_name)
            
            self._update_display_name_in_table(row, original_name)

        elif ok and not new_name.strip():
            self.settings.remove_custom_name(original_name)
            self._update_display_name_in_table(row, original_name)

    def _update_display_name_in_table(self, row: int, original_name: str):
        """Update the display name cell in the scripts table"""
        display_item = self.scripts_table.item(row, 1)
        if not display_item:
            return

        script_info = self.scripts_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        new_display_name = self.script_loader.get_script_display_name(script_info)
        display_item.setText(new_display_name)

        custom_name = self.settings.get_custom_name(original_name)
        font = display_item.font()
        font.setItalic(bool(custom_name))
        display_item.setFont(font)
        display_item.setForeground(CUSTOM_NAME_COLOR if custom_name else Qt.GlobalColor.white)

    def _edit_hotkey(self, row: int, script_name: str):
        """Handle editing of hotkey"""
        current_hotkey = self.hotkey_registry.get_hotkey(script_name)
        
        dialog = HotkeyConfigDialog(script_name, current_hotkey, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_hotkey = dialog.get_hotkey()
            
            if new_hotkey != current_hotkey:
                conflict = self.hotkey_registry.get_hotkey_conflicts(new_hotkey, script_name)
                if conflict:
                    QMessageBox.warning(
                        self, 
                        "Hotkey Conflict",
                        f"The hotkey {new_hotkey} is already assigned to {conflict}."
                    )
                    return
                
                if new_hotkey:
                    success, error = self.hotkey_registry.add_hotkey(script_name, new_hotkey)
                    if not success:
                        QMessageBox.warning(self, "Error", error)
                        return
                else:
                    self.hotkey_registry.remove_hotkey(script_name)
                
                hotkey_item = self.scripts_table.item(row, 2)
                if hotkey_item:
                    hotkey_item.setText(new_hotkey if new_hotkey else "(empty)")
                    hotkey_item.setForeground(Qt.GlobalColor.white if new_hotkey else Qt.GlobalColor.gray)
                
                self.hotkeys_changed.emit()
    
    # Preset management methods
    def _refresh_presets_script_combo(self):
        """Refresh the script combo box with scripts that have arguments"""
        self.presets_script_combo.clear()
        
        if not self.script_loader:
            return
        
        scripts = self.script_loader.discover_scripts()
        
        for script_info in scripts:
            if script_info.arguments:  # Only scripts with arguments
                display_name = script_info.display_name
                self.presets_script_combo.addItem(display_name, script_info)
        
        # Load presets for first script
        if self.presets_script_combo.count() > 0:
            self._on_preset_script_changed(self.presets_script_combo.currentText())
    
    def _on_preset_script_changed(self, script_display_name: str):
        """Handle script selection change in presets tab"""
        self.presets_table.setRowCount(0)
        
        # Get selected script info
        current_index = self.presets_script_combo.currentIndex()
        if current_index < 0:
            return
        
        script_info = self.presets_script_combo.itemData(current_index)
        if not script_info:
            return
        
        script_name = script_info.file_path.stem
        presets = self.settings.get_script_presets(script_name)
        
        # Populate presets table
        for preset_name, arguments in presets.items():
            row_position = self.presets_table.rowCount()
            self.presets_table.insertRow(row_position)
            
            # Preset name
            name_item = QTableWidgetItem(preset_name)
            name_item.setData(Qt.ItemDataRole.UserRole, script_info)
            self.presets_table.setItem(row_position, 0, name_item)
            
            # Arguments summary
            args_text = ", ".join([f"{k}={v}" for k, v in arguments.items()])
            args_item = QTableWidgetItem(args_text)
            self.presets_table.setItem(row_position, 1, args_item)
    
    def _add_preset(self):
        """Add a new preset for the selected script"""
        current_index = self.presets_script_combo.currentIndex()
        if current_index < 0:
            QMessageBox.information(self, "No Script Selected", "Please select a script first.")
            return
        
        script_info = self.presets_script_combo.itemData(current_index)
        if not script_info:
            return
        
        # Open preset editor dialog
        self._open_preset_editor(script_info, None)
    
    def _edit_preset(self):
        """Edit the selected preset"""
        selected_rows = self.presets_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.information(self, "No Preset Selected", "Please select a preset to edit.")
            return
        
        row = selected_rows[0].row()
        preset_name_item = self.presets_table.item(row, 0)
        if not preset_name_item:
            return
        
        script_info = preset_name_item.data(Qt.ItemDataRole.UserRole)
        preset_name = preset_name_item.text()
        
        # Open preset editor dialog
        self._open_preset_editor(script_info, preset_name)
    
    def _delete_preset(self):
        """Delete the selected preset"""
        selected_rows = self.presets_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.information(self, "No Preset Selected", "Please select a preset to delete.")
            return
        
        row = selected_rows[0].row()
        preset_name_item = self.presets_table.item(row, 0)
        if not preset_name_item:
            return
        
        script_info = preset_name_item.data(Qt.ItemDataRole.UserRole)
        preset_name = preset_name_item.text()
        script_name = script_info.file_path.stem
        
        # Confirm deletion
        reply = QMessageBox.question(
            self, "Delete Preset",
            f"Are you sure you want to delete the preset '{preset_name}' for script '{script_info.display_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.settings.delete_script_preset(script_name, preset_name)
            self._on_preset_script_changed(self.presets_script_combo.currentText())
    
    def _open_preset_editor(self, script_info, preset_name=None):
        """Open the preset editor dialog"""
        script_name = script_info.file_path.stem
        
        # Get current arguments if editing
        current_args = {}
        if preset_name:
            current_args = self.settings.get_preset_arguments(script_name, preset_name)
        
        # Create and show the preset editor dialog
        editor = PresetEditorDialog(script_info, preset_name, current_args, self)
        
        if editor.exec() == QDialog.DialogCode.Accepted:
            # Get the results from the dialog
            new_preset_name = editor.get_preset_name()
            arguments = editor.get_arguments()
            
            if new_preset_name and arguments:
                # If preset name changed, delete the old one
                if preset_name and preset_name != new_preset_name:
                    self.settings.delete_script_preset(script_name, preset_name)
                
                # Save the new/updated preset
                self.settings.save_script_preset(script_name, new_preset_name, arguments)
                self._on_preset_script_changed(self.presets_script_combo.currentText())
    
    def _reset_all_settings(self):
        """Reset all application settings to defaults"""
        reply = QMessageBox.question(
            self,
            "Reset All Settings",
            "⚠️ WARNING ⚠️\n\n"
            "This will permanently delete ALL application settings and cannot be undone!\n\n"
            "This includes:\n"
            "• All preferences and startup settings\n"
            "• Font and appearance settings\n"
            "• Script display names and hotkey assignments\n"
            "• External script configurations\n"
            "• Script presets and argument values\n"
            "• Disabled script states\n\n"
            "The application will need to be restarted after reset.\n\n"
            "Are you absolutely sure you want to continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Clear all settings
                self.settings.settings.clear()
                self.settings.settings.sync()
                
                QMessageBox.information(
                    self,
                    "Settings Reset Complete",
                    "✅ All settings have been permanently deleted!\n\n"
                    "The application will now close and you'll need to restart it.\n\n"
                    "When you restart, all settings will be back to their defaults."
                )
                
                # Close the dialog and signal to close the application
                self.accept()
                
                # Exit the application
                from PyQt6.QtWidgets import QApplication
                QApplication.quit()
                
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to reset settings: {str(e)}\n\n"
                    "You may need to manually delete the registry entries at:\n"
                    "HKEY_CURRENT_USER\\Software\\DesktopUtils\\DesktopUtilityGUI"
                )
    
    # External scripts management methods
    
    def _add_external_script(self):
        """Add a new external script"""
        # Get script name from user
        script_name, ok = QInputDialog.getText(
            self,
            "Add External Script",
            "Enter a name for this script:"
        )
        
        if not ok or not script_name.strip():
            return
        
        script_name = script_name.strip()
        
        # Check if name already exists
        existing_externals = self.settings.get_external_scripts()
        if script_name in existing_externals:
            QMessageBox.warning(
                self,
                "Name Already Exists",
                f"An external script with the name '{script_name}' already exists. Please choose a different name."
            )
            return
        
        # Get script file from user
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Python Script",
            "",
            "Python Files (*.py)"
        )
        
        if not file_path:
            return
        
        # Add the external script
        if self.settings.add_external_script(script_name, file_path):
            QMessageBox.information(
                self,
                "Script Added",
                f"External script '{script_name}' has been added successfully."
            )
            # Refresh the main scripts table to include the new external script
            if self.script_loader:
                self.script_loader.refresh_external_scripts()
            self._refresh_scripts_table()
            
            # Refresh the Script Args tab to include new external script if it has arguments
            self._refresh_presets_script_combo()
            
            # Emit signal to notify other components (like tray manager)
            self.scripts_changed.emit()
        else:
            QMessageBox.warning(
                self,
                "Failed to Add Script",
                f"Failed to add external script '{script_name}'. The file path may be invalid or the name may contain invalid characters."
            )
    
    def _browse_external_script(self, script_name: str):
        """Browse for a new path for an existing external script"""
        current_path = self.settings.get_external_script_path(script_name)
        
        # Get new script file from user
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            f"Select New Path for '{script_name}'",
            current_path or "",
            "Python Files (*.py)"
        )
        
        if not file_path:
            return
        
        # Update the external script path
        if self.settings.update_external_script_path(script_name, file_path):
            QMessageBox.information(
                self,
                "Path Updated",
                f"Path for external script '{script_name}' has been updated successfully."
            )
            # Refresh the scripts table to show the updated external script
            if self.script_loader:
                self.script_loader.refresh_external_scripts()
            self._refresh_scripts_table()
            
            # Refresh the Script Args tab since script arguments may have changed
            self._refresh_presets_script_combo()
            
            # Emit signal to notify other components (like tray manager)
            self.scripts_changed.emit()
        else:
            QMessageBox.warning(
                self,
                "Failed to Update Path",
                f"Failed to update path for external script '{script_name}'. The file path may be invalid."
            )
    
    def _remove_external_script(self, script_name: str):
        """Remove an external script"""
        reply = QMessageBox.question(
            self, "Remove External Script",
            f"Are you sure you want to remove the external script '{script_name}'?\n\nThis will not delete the actual file.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.settings.remove_external_script(script_name)
            # Refresh the scripts table to remove the external script
            if self.script_loader:
                self.script_loader.refresh_external_scripts()
            self._refresh_scripts_table()
            
            # Refresh the Script Args tab to ensure external script is removed from dropdown
            self._refresh_presets_script_combo()
            
            # Emit signal to notify other components (like tray manager)
            self.scripts_changed.emit()