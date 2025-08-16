import logging
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QFrame, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

logger = logging.getLogger('GUI.DividerWidget')

class DividerWidget(QWidget):
    """A visual separator widget with optional label."""
    
    def __init__(self, label: str = None, style: str = "default"):
        super().__init__()
        self.label_text = label
        self.style_type = style
        self.init_ui()
        
    def init_ui(self):
        logger.debug(f"Creating divider widget: '{self.label_text or 'no label'}' with style '{self.style_type}'")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(2)
        
        if self.label_text:
            # Create a labeled divider
            container = QHBoxLayout()
            container.setSpacing(10)
            
            # Left line
            left_line = QFrame()
            left_line.setFrameShape(QFrame.Shape.HLine)
            left_line.setFrameShadow(QFrame.Shadow.Sunken)
            left_line.setStyleSheet(self._get_line_style())
            container.addWidget(left_line, 1)
            
            # Label
            label = QLabel(self.label_text)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet(self._get_label_style())
            
            # Make label bold if it's a section header
            if self.style_type == "section":
                font = label.font()
                font.setBold(True)
                font.setPointSize(font.pointSize() + 1)
                label.setFont(font)
            
            container.addWidget(label)
            
            # Right line
            right_line = QFrame()
            right_line.setFrameShape(QFrame.Shape.HLine)
            right_line.setFrameShadow(QFrame.Shadow.Sunken)
            right_line.setStyleSheet(self._get_line_style())
            container.addWidget(right_line, 1)
            
            layout.addLayout(container)
        else:
            # Simple line divider
            line = QFrame()
            line.setFrameShape(QFrame.Shape.HLine)
            line.setFrameShadow(QFrame.Shadow.Sunken)
            line.setStyleSheet(self._get_line_style())
            layout.addWidget(line)
        
        # Set widget properties
        self.setMaximumHeight(40 if self.label_text else 20)
        
    def _get_line_style(self) -> str:
        """Get the style for the divider line based on style type."""
        styles = {
            "default": """
                QFrame {
                    color: #d0d0d0;
                    background-color: #d0d0d0;
                    max-height: 1px;
                    min-height: 1px;
                }
            """,
            "bold": """
                QFrame {
                    color: #a0a0a0;
                    background-color: #a0a0a0;
                    max-height: 2px;
                    min-height: 2px;
                }
            """,
            "section": """
                QFrame {
                    color: #2196F3;
                    background-color: #2196F3;
                    max-height: 2px;
                    min-height: 2px;
                }
            """,
            "subtle": """
                QFrame {
                    color: #e8e8e8;
                    background-color: #e8e8e8;
                    max-height: 1px;
                    min-height: 1px;
                }
            """,
            "dotted": """
                QFrame {
                    border: none;
                    border-top: 1px dotted #c0c0c0;
                    max-height: 1px;
                    min-height: 1px;
                }
            """
        }
        return styles.get(self.style_type, styles["default"])
    
    def _get_label_style(self) -> str:
        """Get the style for the label based on style type."""
        styles = {
            "default": """
                QLabel {
                    color: #666666;
                    padding: 0px 10px;
                    background-color: transparent;
                }
            """,
            "bold": """
                QLabel {
                    color: #444444;
                    padding: 0px 10px;
                    background-color: transparent;
                    font-weight: 600;
                }
            """,
            "section": """
                QLabel {
                    color: #2196F3;
                    padding: 0px 15px;
                    background-color: transparent;
                    font-weight: bold;
                }
            """,
            "subtle": """
                QLabel {
                    color: #999999;
                    padding: 0px 10px;
                    background-color: transparent;
                    font-size: 11px;
                }
            """,
            "dotted": """
                QLabel {
                    color: #888888;
                    padding: 0px 10px;
                    background-color: transparent;
                    font-style: italic;
                }
            """
        }
        return styles.get(self.style_type, styles["default"])