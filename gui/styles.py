MAIN_STYLE = """
QMainWindow {
    background-color: #f5f5f5;
}

QScrollArea {
    background-color: #ffffff;
    border: none;
}

QWidget#scriptListContainer {
    background-color: #ffffff;
}

QLabel#titleLabel {
    font-size: 24px;
    font-weight: bold;
    color: #333333;
    padding: 20px;
}

QLabel#errorLabel {
    color: #d32f2f;
    font-size: 12px;
    padding: 5px;
}

QLabel#statusLabel {
    color: #666666;
    font-size: 12px;
    padding: 10px;
}
"""

SCRIPT_WIDGET_STYLE = """
QWidget#scriptWidget {
    background-color: #ffffff;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 15px;
    margin: 5px;
}

QWidget#scriptWidget:hover {
    border: 1px solid #2196F3;
    background-color: #f9f9f9;
}

QLabel#scriptName {
    font-size: 16px;
    font-weight: 600;
    color: #333333;
}

QLabel#scriptDescription {
    font-size: 12px;
    color: #666666;
    margin-top: 2px;
}

QLabel#scriptStatus {
    font-size: 11px;
    color: #888888;
    font-style: italic;
}

QPushButton {
    background-color: #2196F3;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 8px 16px;
    font-size: 14px;
    font-weight: 500;
    min-width: 100px;
}

QPushButton:hover {
    background-color: #1976D2;
}

QPushButton:pressed {
    background-color: #0D47A1;
}

QPushButton:disabled {
    background-color: #cccccc;
    color: #666666;
}

QPushButton#toggleButton[state="on"] {
    background-color: #4CAF50;
}

QPushButton#toggleButton[state="on"]:hover {
    background-color: #45a049;
}

QPushButton#cycleButton {
    background-color: #FF9800;
}

QPushButton#cycleButton:hover {
    background-color: #F57C00;
}

QComboBox {
    background-color: white;
    border: 1px solid #cccccc;
    border-radius: 4px;
    padding: 6px 12px;
    font-size: 14px;
    min-width: 120px;
}

QComboBox:hover {
    border: 1px solid #2196F3;
}

QComboBox::drop-down {
    border: none;
}

QComboBox::down-arrow {
    width: 12px;
    height: 12px;
}

QSlider {
    min-width: 150px;
}

QSlider::groove:horizontal {
    border: 1px solid #cccccc;
    height: 6px;
    background: #e0e0e0;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: #2196F3;
    border: 1px solid #1976D2;
    width: 18px;
    margin: -6px 0;
    border-radius: 9px;
}

QSlider::handle:horizontal:hover {
    background: #1976D2;
}

QLineEdit {
    background-color: white;
    border: 1px solid #cccccc;
    border-radius: 4px;
    padding: 6px 12px;
    font-size: 14px;
    min-width: 150px;
}

QLineEdit:focus {
    border: 1px solid #2196F3;
    outline: none;
}

QSpinBox, QDoubleSpinBox {
    background-color: white;
    border: 1px solid #cccccc;
    border-radius: 4px;
    padding: 6px 12px;
    font-size: 14px;
    min-width: 100px;
}

QSpinBox:focus, QDoubleSpinBox:focus {
    border: 1px solid #2196F3;
}
"""