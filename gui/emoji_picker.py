import logging
from typing import Optional, Dict, List
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QPushButton, QLabel, QLineEdit, QTabWidget, 
                             QWidget, QScrollArea, QDialogButtonBox, 
                             QMessageBox, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont

logger = logging.getLogger('GUI.EmojiPicker')

class EmojiPicker(QDialog):
    """Dialog for selecting emojis with categories and search functionality"""
    
    emoji_selected = pyqtSignal(str)
    
    # Emoji categories with commonly used emojis
    EMOJI_CATEGORIES = {
        'Faces & People': [
            '😀', '😃', '😄', '😁', '😆', '😅', '🤣', '😂', '🙂', '🙃', '😉', '😊',
            '😇', '🥰', '😍', '🤩', '😘', '😗', '😚', '😙', '😋', '😛', '😜', '🤪',
            '😝', '🤑', '🤗', '🤭', '🤫', '🤔', '🤐', '🤨', '😐', '😑', '😶', '😏',
            '😒', '🙄', '😬', '🤥', '😔', '😪', '🤤', '😴', '😷', '🤒', '🤕', '🤢'
        ],
        'Animals & Nature': [
            '🐶', '🐱', '🐭', '🐹', '🐰', '🦊', '🐻', '🐼', '🐨', '🐯', '🦁', '🐮',
            '🐷', '🐽', '🐸', '🐵', '🐒', '🦍', '🐣', '🐥', '🦆', '🦅', '🦉', '🦇',
            '🐺', '🐗', '🐴', '🦄', '🐝', '🐛', '🦋', '🐌', '🐞', '🐜', '🦗', '🕷️',
            '🦂', '🐢', '🐍', '🦎', '🐙', '🦑', '🦐', '🦀', '🐡', '🐠', '🐟', '🐬'
        ],
        'Food & Drink': [
            '🍇', '🍈', '🍉', '🍊', '🍋', '🍌', '🍍', '🥭', '🍎', '🍏', '🍐', '🍑',
            '🍒', '🍓', '🥝', '🍅', '🥥', '🥑', '🍆', '🥔', '🥕', '🌽', '🌶️', '🫒',
            '🥒', '🥬', '🥦', '🧄', '🧅', '🍄', '🥜', '🌰', '🍞', '🥐', '🥖', '🫓',
            '🥨', '🥯', '🥞', '🧇', '🧈', '🍯', '🥛', '☕', '🫖', '🍵', '🧃', '🥤'
        ],
        'Activities & Objects': [
            '⚽', '🏀', '🏈', '⚾', '🥎', '🎾', '🏐', '🏉', '🎱', '🪀', '🏓', '🏸',
            '⛳', '🪁', '🏹', '🎣', '🥊', '🥋', '🎽', '🛹', '🛷', '⛸️', '🥌', '🎿',
            '⛷️', '🏂', '🪂', '🏋️', '🤼', '🤸', '⛹️', '🤺', '🤾', '🏌️', '🏇', '🧘',
            '🏄', '🏊', '🤽', '🚣', '🧗', '🚵', '🚴', '🏆', '🥇', '🥈', '🥉', '🏅'
        ],
        'Technology & Tools': [
            '⌚', '📱', '📲', '💻', '⌨️', '🖥️', '🖨️', '🖱️', '🖲️', '🕹️', '🗜️', '💽',
            '💾', '💿', '📀', '📼', '📷', '📸', '📹', '🎥', '📽️', '🎞️', '📞', '☎️',
            '📟', '📠', '📺', '📻', '🎙️', '🎚️', '🎛️', '🧭', '⏱️', '⏲️', '⏰', '🕰️',
            '⏳', '⏰', '🔋', '🔌', '💡', '🔦', '🕯️', '🪔', '🧯', '🛢️', '💸', '💳'
        ],
        'Symbols': [
            '❤️', '🧡', '💛', '💚', '💙', '💜', '🖤', '🤍', '🤎', '💔', '❣️', '💕',
            '💞', '💓', '💗', '💖', '💘', '💝', '💟', '☮️', '✝️', '☪️', '🕉️', '☸️',
            '✡️', '🔯', '🕎', '☯️', '☦️', '🛐', '⛎', '♈', '♉', '♊', '♋', '♌',
            '♍', '♎', '♏', '♐', '♑', '♒', '♓', '🆔', '⚡', '⭐', '🌟', '💫'
        ]
    }
    
    def __init__(self, current_emoji: str = "", parent=None):
        super().__init__(parent)
        self.current_emoji = current_emoji
        self.selected_emoji = ""
        self.recent_emojis = self._load_recent_emojis()
        
        self.init_ui()
        self.setWindowTitle("Select Emoji")
        self.setModal(True)
        self.resize(500, 400)
        
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        
        # Search bar
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Type to search emojis...")
        self.search_input.textChanged.connect(self._on_search_changed)
        search_layout.addWidget(self.search_input)
        
        layout.addLayout(search_layout)
        
        # Current selection display
        current_layout = QHBoxLayout()
        current_layout.addWidget(QLabel("Current:"))
        
        self.current_label = QLabel(self.current_emoji if self.current_emoji else "(none)")
        self.current_label.setStyleSheet("font-size: 24px; padding: 5px; border: 1px solid #ccc;")
        self.current_label.setMinimumSize(60, 40)
        self.current_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        current_layout.addWidget(self.current_label)
        
        current_layout.addWidget(QLabel("Selected:"))
        self.selected_label = QLabel("(none)")
        self.selected_label.setStyleSheet("font-size: 24px; padding: 5px; border: 1px solid #ccc;")
        self.selected_label.setMinimumSize(60, 40)
        self.selected_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        current_layout.addWidget(self.selected_label)
        
        current_layout.addStretch()
        layout.addLayout(current_layout)
        
        # Emoji categories in tabs
        self.tab_widget = QTabWidget()
        
        # Add Recent tab if we have recent emojis
        if self.recent_emojis:
            self._create_emoji_tab("Recent", self.recent_emojis)
        
        # Add category tabs
        for category, emojis in self.EMOJI_CATEGORIES.items():
            self._create_emoji_tab(category, emojis)
        
        layout.addWidget(self.tab_widget)
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel |
            QDialogButtonBox.StandardButton.Reset
        )
        
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        # Reset button clears selection
        reset_button = button_box.button(QDialogButtonBox.StandardButton.Reset)
        reset_button.setText("Clear")
        reset_button.clicked.connect(self._clear_selection)
        
        layout.addWidget(button_box)
    
    def _create_emoji_tab(self, name: str, emojis: List[str]):
        """Create a tab with emoji grid"""
        tab = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Create grid widget
        grid_widget = QWidget()
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setSpacing(5)
        
        # Add emoji buttons to grid (8 columns)
        cols = 8
        for i, emoji in enumerate(emojis):
            row = i // cols
            col = i % cols
            
            emoji_button = QPushButton(emoji)
            emoji_button.setFixedSize(QSize(40, 40))
            emoji_button.setStyleSheet("""
                QPushButton {
                    font-size: 20px;
                    border: 1px solid #ddd;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #e6f3ff;
                    border: 2px solid #0078d4;
                }
                QPushButton:pressed {
                    background-color: #cce7ff;
                }
            """)
            emoji_button.clicked.connect(lambda checked, e=emoji: self._emoji_clicked(e))
            
            grid_layout.addWidget(emoji_button, row, col)
        
        # Add stretch to push buttons to top
        grid_layout.setRowStretch(grid_layout.rowCount(), 1)
        
        scroll.setWidget(grid_widget)
        
        tab_layout = QVBoxLayout(tab)
        tab_layout.addWidget(scroll)
        
        self.tab_widget.addTab(tab, name)
    
    def _emoji_clicked(self, emoji: str):
        """Handle emoji button clicks"""
        self.selected_emoji = emoji
        self.selected_label.setText(emoji)
        logger.debug(f"Emoji selected: {emoji}")
    
    def _clear_selection(self):
        """Clear the current selection"""
        self.selected_emoji = ""
        self.selected_label.setText("(none)")
    
    def _on_search_changed(self, text: str):
        """Handle search input changes"""
        if not text.strip():
            return
        
        # Simple search through all emojis
        # This could be enhanced with emoji names/descriptions
        search_term = text.lower().strip()
        
        # For now, just show message that search is limited
        if len(search_term) >= 2:
            # Could implement more sophisticated search here
            pass
    
    def get_selected_emoji(self) -> str:
        """Get the selected emoji"""
        return self.selected_emoji
    
    def accept(self):
        """Handle dialog acceptance"""
        if self.selected_emoji:
            self._add_to_recent(self.selected_emoji)
            self.emoji_selected.emit(self.selected_emoji)
        super().accept()
    
    def _load_recent_emojis(self) -> List[str]:
        """Load recently used emojis (placeholder for now)"""
        # This could be implemented to persist recent emojis
        # For now, return empty list
        return []
    
    def _add_to_recent(self, emoji: str):
        """Add emoji to recent list (placeholder for now)"""
        # This could be implemented to persist recent emojis
        pass


class EmojiButton(QPushButton):
    """Custom button for displaying emojis with better styling"""
    
    def __init__(self, emoji: str, parent=None):
        super().__init__(emoji, parent)
        self.emoji = emoji
        self.setFixedSize(QSize(35, 35))
        
        # Set consistent styling
        font = QFont()
        font.setPointSize(16)
        self.setFont(font)
        
        self.setStyleSheet("""
            QPushButton {
                border: 1px solid #ddd;
                border-radius: 3px;
                background-color: white;
            }
            QPushButton:hover {
                background-color: #e6f3ff;
                border: 2px solid #0078d4;
            }
            QPushButton:pressed {
                background-color: #cce7ff;
            }
        """)