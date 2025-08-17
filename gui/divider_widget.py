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
        layout.setContentsMargins(24, 12, 24, 12)
        layout.setSpacing(8)
        
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
        self.setMaximumHeight(60 if self.label_text else 30)
        self.setMinimumHeight(50 if self.label_text else 25)
        
    def _get_line_style(self) -> str:
        """Get the style for the divider line based on style type."""
        styles = {
            "default": """
                QFrame {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 transparent, 
                                stop:0.2 rgba(226, 232, 240, 0.8), 
                                stop:0.8 rgba(226, 232, 240, 0.8), 
                                stop:1 transparent);
                    max-height: 1px;
                    min-height: 1px;
                    border: none;
                }
            """,
            "bold": """
                QFrame {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 transparent, 
                                stop:0.1 rgba(148, 163, 184, 0.8), 
                                stop:0.9 rgba(148, 163, 184, 0.8), 
                                stop:1 transparent);
                    max-height: 2px;
                    min-height: 2px;
                    border: none;
                }
            """,
            "section": """
                QFrame {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 transparent, 
                                stop:0.1 rgba(59, 130, 246, 0.6), 
                                stop:0.5 rgba(59, 130, 246, 0.8), 
                                stop:0.9 rgba(59, 130, 246, 0.6), 
                                stop:1 transparent);
                    max-height: 2px;
                    min-height: 2px;
                    border: none;
                    border-radius: 1px;
                }
            """,
            "subtle": """
                QFrame {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 transparent, 
                                stop:0.3 rgba(248, 250, 252, 0.9), 
                                stop:0.7 rgba(248, 250, 252, 0.9), 
                                stop:1 transparent);
                    max-height: 1px;
                    min-height: 1px;
                    border: none;
                }
            """,
            "dotted": """
                QFrame {
                    border: none;
                    border-top: 2px dotted rgba(203, 213, 225, 0.8);
                    max-height: 1px;
                    min-height: 1px;
                    background: transparent;
                }
            """
        }
        return styles.get(self.style_type, styles["default"])
    
    def _get_label_style(self) -> str:
        """Get the style for the label based on style type."""
        styles = {
            "default": """
                QLabel {
                    color: #64748b;
                    padding: 4px 16px;
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 rgba(255, 255, 255, 0.9), 
                                stop:1 rgba(248, 250, 252, 0.8));
                    border-radius: 12px;
                    font-size: 12px;
                    font-weight: 500;
                    border: 1px solid rgba(226, 232, 240, 0.6);
                }
            """,
            "bold": """
                QLabel {
                    color: #475569;
                    padding: 6px 18px;
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 rgba(255, 255, 255, 0.95), 
                                stop:1 rgba(241, 245, 249, 0.9));
                    border-radius: 14px;
                    font-size: 13px;
                    font-weight: 600;
                    border: 1px solid rgba(148, 163, 184, 0.4);
                }
            """,
            "section": """
                QLabel {
                    color: #1e40af;
                    padding: 8px 20px;
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 rgba(59, 130, 246, 0.1), 
                                stop:1 rgba(29, 78, 216, 0.05));
                    border-radius: 16px;
                    font-size: 14px;
                    font-weight: 700;
                    border: 1px solid rgba(59, 130, 246, 0.3);
                    letter-spacing: 0.5px;
                }
            """,
            "subtle": """
                QLabel {
                    color: #94a3b8;
                    padding: 3px 14px;
                    background: rgba(248, 250, 252, 0.7);
                    border-radius: 10px;
                    font-size: 11px;
                    font-weight: 500;
                    border: 1px solid rgba(226, 232, 240, 0.5);
                }
            """,
            "dotted": """
                QLabel {
                    color: #6b7280;
                    padding: 4px 16px;
                    background: rgba(249, 250, 251, 0.8);
                    border-radius: 12px;
                    font-size: 12px;
                    font-weight: 500;
                    font-style: italic;
                    border: 1px dotted rgba(203, 213, 225, 0.8);
                }
            """
        }
        return styles.get(self.style_type, styles["default"])