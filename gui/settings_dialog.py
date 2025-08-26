import logging
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QCheckBox, QComboBox, QLabel, QPushButton,
                             QDialogButtonBox, QMessageBox, QWidget, QTabWidget,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QAbstractItemView, QFontComboBox, QSpinBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from core.settings import SettingsManager
from core.startup_manager import StartupManager
from core.script_loader import ScriptLoader
from core.hotkey_registry import HotkeyRegistry
from gui.hotkey_configurator import HotkeyConfigDialog
from gui.emoji_picker import EmojiPicker

# UI Theme Constants
CUSTOM_NAME_COLOR = Qt.GlobalColor.cyan

logger = logging.getLogger('GUI.SettingsDialog')

class SettingsDialog(QDialog):
    settings_changed = pyqtSignal()
    hotkeys_changed = pyqtSignal()
    
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
        self.setMinimumSize(600, 500)
        
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Create and add General tab
        self.general_tab = self._create_general_tab()
        self.tab_widget.addTab(self.general_tab, "General")
        
        # Create and add Hotkeys tab
        self.hotkeys_tab = self._create_hotkeys_tab()
        self.tab_widget.addTab(self.hotkeys_tab, "Hotkeys")
        
        # Create and add Script Icons tab
        self.icons_tab = self._create_icons_tab()
        self.tab_widget.addTab(self.icons_tab, "Script Icons")
        
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
        
        # Connect change handlers
        self.run_on_startup_checkbox.stateChanged.connect(self._on_startup_changed)
        
        return widget
    
    def _create_hotkeys_tab(self) -> QWidget:
        """Create the Hotkeys configuration tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Instructions
        instructions = QLabel(
            "Configure keyboard shortcuts and display names for scripts. "
            "Click on a display name cell to edit the name, or click on a hotkey cell to set shortcuts."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Create table for hotkey configuration
        self.hotkeys_table = QTableWidget()
        self.hotkeys_table.setColumnCount(5)
        self.hotkeys_table.setHorizontalHeaderLabels(["Script", "Display Name", "Description", "Hotkey", "Actions"])
        
        # Set table styling for better visibility
        self.hotkeys_table.setStyleSheet("""
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
        self.hotkeys_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.hotkeys_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.hotkeys_table.horizontalHeader().setStretchLastSection(False)
        self.hotkeys_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.hotkeys_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.hotkeys_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.hotkeys_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.hotkeys_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        
        # Connect cell click handler
        self.hotkeys_table.cellClicked.connect(self._on_hotkey_cell_clicked)
        
        layout.addWidget(self.hotkeys_table)
        
        # Refresh button
        refresh_button = QPushButton("Refresh Scripts")
        refresh_button.clicked.connect(self._refresh_hotkeys_table)
        layout.addWidget(refresh_button)
        
        # Load hotkeys
        self._refresh_hotkeys_table()
        
        return widget
    
    def _create_icons_tab(self) -> QWidget:
        """Create the Script Icons configuration tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Instructions
        instructions = QLabel(
            "Customize emoji icons for scripts in the system tray menu. "
            "Click on an emoji cell to select a new emoji, or use the 'Set' button. "
            "Use 'Reset' to restore the default emoji for a script."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Create table for icon configuration
        self.icons_table = QTableWidget()
        self.icons_table.setColumnCount(5)
        self.icons_table.setHorizontalHeaderLabels(["Script", "Current Emoji", "Description", "Actions", "Preview"])
        
        # Set table styling similar to hotkeys table
        self.icons_table.setStyleSheet("""
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
        self.icons_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.icons_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.icons_table.horizontalHeader().setStretchLastSection(False)
        self.icons_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.icons_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.icons_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.icons_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.icons_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        
        layout.addWidget(self.icons_table)
        
        # Refresh button
        refresh_button = QPushButton("Refresh Scripts")
        refresh_button.clicked.connect(self._refresh_icons_table)
        layout.addWidget(refresh_button)
        
        # Load icons table
        self._refresh_icons_table()
        
        return widget
    
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
        font_family = self.settings.get_font_family()
        if font_family != 'System Default':
            self.font_combo.setCurrentText(font_family)
        self.font_size_spinbox.setValue(self.settings.get_font_size())
        
    
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
            self.settings.set_font_family(self.font_combo.currentText())
            self.settings.set_font_size(self.font_size_spinbox.value())
            
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
    
    def _refresh_hotkeys_table(self):
        """Refresh the hotkeys table with current scripts"""
        self.hotkeys_table.setRowCount(0)
        
        if not self.script_loader:
            return
        
        # Get all scripts
        scripts = self.script_loader.discover_scripts()
        
        # Populate table
        for script_info in scripts:
            try:
                # Use ScriptInfo properties directly
                original_name = script_info.display_name
                description = f"Script: {script_info.file_path.name}"
                
                # Get effective display name (custom or original)
                display_name = self.script_loader.get_script_display_name(script_info)
                
                # Get current hotkey for this script
                hotkey = self.hotkey_registry.get_hotkey(original_name)
                
                # Add row
                row_position = self.hotkeys_table.rowCount()
                self.hotkeys_table.insertRow(row_position)
                
                # Original script name
                name_item = QTableWidgetItem(original_name)
                name_item.setData(Qt.ItemDataRole.UserRole, script_info)  # Store script reference
                name_item.setForeground(Qt.GlobalColor.white)
                self.hotkeys_table.setItem(row_position, 0, name_item)
                
                # Display name (clickable for editing)
                display_item = QTableWidgetItem(display_name)
                display_item.setForeground(Qt.GlobalColor.white)
                display_item.setToolTip("Click to edit display name")
                # Add visual indicator if custom name is set
                custom_name = self.settings.get_custom_name(original_name)
                if custom_name:
                    display_item.setForeground(CUSTOM_NAME_COLOR)  # Different color for custom names
                    font = display_item.font()
                    font.setItalic(True)
                    display_item.setFont(font)
                self.hotkeys_table.setItem(row_position, 1, display_item)
                
                # Description
                desc_item = QTableWidgetItem(description)
                desc_item.setToolTip(description)
                desc_item.setForeground(Qt.GlobalColor.white)
                self.hotkeys_table.setItem(row_position, 2, desc_item)
                
                # Hotkey
                hotkey_item = QTableWidgetItem(hotkey if hotkey else "(empty)")
                if not hotkey:
                    hotkey_item.setForeground(Qt.GlobalColor.gray)
                else:
                    # Make sure hotkey text is white and visible
                    hotkey_item.setForeground(Qt.GlobalColor.white)
                self.hotkeys_table.setItem(row_position, 3, hotkey_item)
                
                # Clear button
                clear_button = QPushButton("Clear")
                clear_button.setMaximumWidth(60)
                clear_button.clicked.connect(lambda checked, row=row_position: self._clear_hotkey(row))
                self.hotkeys_table.setCellWidget(row_position, 4, clear_button)
                
            except Exception as e:
                logger.error(f"Error adding script to hotkeys table: {e}")
                import traceback
                traceback.print_exc()
    
    def _on_hotkey_cell_clicked(self, row: int, column: int):
        """Handle clicks on display name and hotkey cells"""
        # Get script info
        name_item = self.hotkeys_table.item(row, 0)
        if not name_item:
            return
        
        original_name = name_item.text()
        
        if column == 1:  # Display name column
            self._edit_display_name(row, original_name)
        elif column == 3:  # Hotkey column
            self._edit_hotkey(row, original_name)
    
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
                # Get all script names for conflict validation
                scripts = self.script_loader.discover_scripts()
                script_names = [script_info.display_name for script_info in scripts]
                
                # Set custom name with validation
                if not self.settings.set_custom_name(original_name, new_name, script_names):
                    # Validation failed - show error message
                    QMessageBox.warning(
                        self,
                        "Invalid Display Name",
                        f"The display name '{new_name}' is invalid. It may conflict with an existing script name "
                        f"or custom name, be too long (max 50 characters), or contain invalid characters."
                    )
                    return
            else:
                # Remove custom name (revert to original)
                self.settings.remove_custom_name(original_name)
            
            # Update table display
            display_item = self.hotkeys_table.item(row, 1)
            if display_item:
                display_item.setText(new_name)
                # Update color and font based on whether it's custom or original
                custom_name = self.settings.get_custom_name(original_name)
                if custom_name:
                    display_item.setForeground(CUSTOM_NAME_COLOR)  # Custom name
                    font = display_item.font()
                    font.setItalic(True)
                    display_item.setFont(font)
                else:
                    display_item.setForeground(Qt.GlobalColor.white)  # Original name
                    font = display_item.font()
                    font.setItalic(False)
                    display_item.setFont(font)
        elif ok and not new_name.strip():
            # Empty name - revert to original
            self.settings.remove_custom_name(original_name)
            display_item = self.hotkeys_table.item(row, 1)
            if display_item:
                display_item.setText(original_name)
                display_item.setForeground(Qt.GlobalColor.white)
                font = display_item.font()
                font.setItalic(False)
                display_item.setFont(font)
    
    def _edit_hotkey(self, row: int, script_name: str):
        """Handle editing of hotkey"""
        current_hotkey = self.hotkey_registry.get_hotkey(script_name)
        
        # Show hotkey configuration dialog
        dialog = HotkeyConfigDialog(script_name, current_hotkey, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_hotkey = dialog.get_hotkey()
            
            if new_hotkey != current_hotkey:
                # Check for conflicts
                conflict = self.hotkey_registry.get_hotkey_conflicts(new_hotkey, script_name)
                if conflict:
                    QMessageBox.warning(
                        self, 
                        "Hotkey Conflict",
                        f"The hotkey {new_hotkey} is already assigned to {conflict}."
                    )
                    return
                
                # Update hotkey
                if new_hotkey:
                    success, error = self.hotkey_registry.add_hotkey(script_name, new_hotkey)
                    if not success:
                        QMessageBox.warning(self, "Error", error)
                        return
                else:
                    self.hotkey_registry.remove_hotkey(script_name)
                
                # Update table display
                hotkey_item = self.hotkeys_table.item(row, 3)
                if hotkey_item:
                    hotkey_item.setText(new_hotkey if new_hotkey else "(empty)")
                    hotkey_item.setForeground(
                        Qt.GlobalColor.white if new_hotkey else Qt.GlobalColor.gray
                    )
                
                # Mark that hotkeys have changed
                self.hotkeys_changed.emit()
    
    def _clear_hotkey(self, row: int):
        """Clear the hotkey for a script"""
        # Get script info
        name_item = self.hotkeys_table.item(row, 0)
        if not name_item:
            return
        
        script_name = name_item.text()
        
        # Remove hotkey
        if self.hotkey_registry.remove_hotkey(script_name):
            # Update table display
            hotkey_item = self.hotkeys_table.item(row, 3)
            if hotkey_item:
                hotkey_item.setText("(empty)")
                hotkey_item.setForeground(Qt.GlobalColor.gray)
            
            # Mark that hotkeys have changed
            self.hotkeys_changed.emit()
    
    def _refresh_icons_table(self):
        """Refresh the script icons table with current scripts"""
        self.icons_table.setRowCount(0)
        
        if not self.script_loader:
            return
        
        # Get all scripts
        scripts = self.script_loader.discover_scripts()
        
        # Populate table
        for script_info in scripts:
            try:
                # Use ScriptInfo properties directly
                original_name = script_info.display_name
                description = f"Script: {script_info.file_path.name}"
                
                # Get current emoji (custom or default)
                current_emoji = self._get_effective_emoji_for_script(original_name)
                
                # Add row
                row_position = self.icons_table.rowCount()
                self.icons_table.insertRow(row_position)
                
                # Script name
                name_item = QTableWidgetItem(original_name)
                name_item.setData(Qt.ItemDataRole.UserRole, script_info)
                name_item.setForeground(Qt.GlobalColor.white)
                self.icons_table.setItem(row_position, 0, name_item)
                
                # Current emoji (large font for visibility)
                emoji_item = QTableWidgetItem(current_emoji if current_emoji else "(none)")
                emoji_item.setForeground(Qt.GlobalColor.white)
                emoji_item.setToolTip("Click to change emoji")
                if current_emoji:
                    font = emoji_item.font()
                    font.setPointSize(20)
                    emoji_item.setFont(font)
                self.icons_table.setItem(row_position, 1, emoji_item)
                
                # Description
                desc_item = QTableWidgetItem(description)
                desc_item.setToolTip(description)
                desc_item.setForeground(Qt.GlobalColor.white)
                self.icons_table.setItem(row_position, 2, desc_item)
                
                # Action buttons
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(2, 2, 2, 2)
                
                set_button = QPushButton("Set")
                set_button.setMaximumWidth(50)
                set_button.clicked.connect(lambda checked, row=row_position: self._set_script_emoji(row))
                actions_layout.addWidget(set_button)
                
                reset_button = QPushButton("Reset")
                reset_button.setMaximumWidth(50)
                reset_button.clicked.connect(lambda checked, row=row_position: self._reset_script_emoji(row))
                actions_layout.addWidget(reset_button)
                
                self.icons_table.setCellWidget(row_position, 3, actions_widget)
                
                # Preview (showing what it would look like in tray)
                display_name = self.script_loader.get_script_display_name(script_info)
                preview_text = f"{current_emoji} {display_name}" if current_emoji else display_name
                preview_item = QTableWidgetItem(preview_text)
                preview_item.setForeground(Qt.GlobalColor.lightGray)
                preview_item.setToolTip("Preview of how this will appear in the tray menu")
                if current_emoji:
                    font = preview_item.font()
                    font.setPointSize(10)
                    preview_item.setFont(font)
                self.icons_table.setItem(row_position, 4, preview_item)
                
            except Exception as e:
                logger.error(f"Error adding script to icons table: {e}")
                import traceback
                traceback.print_exc()
    
    def _get_effective_emoji_for_script(self, script_name: str) -> str:
        """Get effective emoji for script (custom or default)"""
        # First check for custom emoji
        custom_emoji = self.settings.get_script_emoji(script_name)
        if custom_emoji:
            return custom_emoji
        
        # Return default emoji based on script name/type
        return self._get_default_emoji(script_name)
    
    def _get_default_emoji(self, script_name: str) -> str:
        """Get default emoji based on script name"""
        name_lower = script_name.lower()
        
        # Audio related
        if any(word in name_lower for word in ['audio', 'sound', 'volume', 'speaker', 'microphone']):
            return '🔊'
        
        # Display related  
        if any(word in name_lower for word in ['display', 'monitor', 'screen', 'resolution']):
            return '🖥️'
        
        # Bluetooth related
        if any(word in name_lower for word in ['bluetooth', 'bt', 'wireless']):
            return '📶'
        
        # Power related
        if any(word in name_lower for word in ['power', 'battery', 'energy', 'plan']):
            return '⚡'
        
        # Network related
        if any(word in name_lower for word in ['network', 'wifi', 'internet', 'connection']):
            return '🌐'
        
        # File/clipboard related
        if any(word in name_lower for word in ['file', 'clipboard', 'copy', 'paste']):
            return '📋'
        
        # Test/debug related
        if any(word in name_lower for word in ['test', 'debug', 'sample']):
            return '🧪'
        
        # Default for unknown types
        return '⚙️'
    
    def _set_script_emoji(self, row: int):
        """Open emoji picker for script"""
        # Get script info
        name_item = self.icons_table.item(row, 0)
        if not name_item:
            return
        
        script_name = name_item.text()
        current_emoji = self._get_effective_emoji_for_script(script_name)
        
        # Show emoji picker
        picker = EmojiPicker(current_emoji, self)
        if picker.exec() == QDialog.DialogCode.Accepted:
            selected_emoji = picker.get_selected_emoji()
            if selected_emoji:
                # Save emoji
                self.settings.set_script_emoji(script_name, selected_emoji)
                
                # Update table display
                self._update_emoji_table_row(row, script_name, selected_emoji)
                
                logger.info(f"Set emoji '{selected_emoji}' for script '{script_name}'")
    
    def _reset_script_emoji(self, row: int):
        """Reset script emoji to default"""
        # Get script info
        name_item = self.icons_table.item(row, 0)
        if not name_item:
            return
        
        script_name = name_item.text()
        
        # Remove custom emoji
        self.settings.remove_script_emoji(script_name)
        
        # Get default emoji
        default_emoji = self._get_default_emoji(script_name)
        
        # Update table display
        self._update_emoji_table_row(row, script_name, default_emoji)
        
        logger.info(f"Reset emoji for script '{script_name}' to default '{default_emoji}'")
    
    def _update_emoji_table_row(self, row: int, script_name: str, emoji: str):
        """Update a table row with new emoji"""
        # Update emoji column
        emoji_item = self.icons_table.item(row, 1)
        if emoji_item:
            emoji_item.setText(emoji)
            if emoji:
                font = emoji_item.font()
                font.setPointSize(20)
                emoji_item.setFont(font)
        
        # Update preview column
        preview_item = self.icons_table.item(row, 4)
        if preview_item:
            # Get script for display name
            name_item = self.icons_table.item(row, 0)
            if name_item:
                script_info = name_item.data(Qt.ItemDataRole.UserRole)
                if script_info:
                    display_name = self.script_loader.get_script_display_name(script_info)
                    preview_text = f"{emoji} {display_name}" if emoji else display_name
                    preview_item.setText(preview_text)