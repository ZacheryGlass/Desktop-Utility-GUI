MAIN_STYLE = """
QMainWindow {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #f8fafc, stop:1 #f1f5f9);
    font-family: 'Segoe UI', 'SF Pro Display', system-ui, sans-serif;
}

QScrollArea {
    background: transparent;
    border: none;
    border-radius: 12px;
}

QScrollArea QScrollBar:vertical {
    background: rgba(0, 0, 0, 0.05);
    width: 8px;
    border-radius: 4px;
    margin: 4px;
}

QScrollArea QScrollBar::handle:vertical {
    background: rgba(0, 0, 0, 0.2);
    border-radius: 4px;
    min-height: 30px;
}

QScrollArea QScrollBar::handle:vertical:hover {
    background: rgba(0, 0, 0, 0.3);
}

QScrollArea QScrollBar::add-line:vertical, QScrollArea QScrollBar::sub-line:vertical {
    height: 0px;
}

QWidget#scriptListContainer {
    background: transparent;
    padding: 0px;
}

QLabel#titleLabel {
    font-size: 32px;
    font-weight: 700;
    color: #1e293b;
    padding: 24px 0px 8px 0px;
    letter-spacing: -0.5px;
}

QLabel#subtitleLabel {
    font-size: 16px;
    font-weight: 400;
    color: #64748b;
    padding: 0px 0px 24px 0px;
    margin-bottom: 8px;
}

QLabel#errorLabel {
    color: #ef4444;
    font-size: 13px;
    font-weight: 500;
    padding: 12px 16px;
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid rgba(239, 68, 68, 0.2);
    border-radius: 8px;
    margin: 8px 0px;
}

QLabel#statusLabel {
    color: #64748b;
    font-size: 14px;
    font-weight: 500;
    padding: 16px 24px;
    background: rgba(255, 255, 255, 0.8);
    border-top: 1px solid rgba(226, 232, 240, 0.8);
    backdrop-filter: blur(10px);
}

QPushButton#refreshButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #3b82f6, stop:1 #2563eb);
    color: white;
    border: none;
    border-radius: 10px;
    padding: 12px 24px;
    font-size: 14px;
    font-weight: 600;
    min-width: 80px;
}

QPushButton#refreshButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #2563eb, stop:1 #1d4ed8);
}

QPushButton#refreshButton:pressed {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #1d4ed8, stop:1 #1e40af);
}

QWidget#headerWidget {
    background: rgba(255, 255, 255, 0.95);
    border-radius: 16px;
    margin: 16px;
    border: 1px solid rgba(226, 232, 240, 0.8);
    backdrop-filter: blur(20px);
}

QWidget#scriptWidget {
    background: red;
    border: 10px solid blue;
    border-radius: 16px;
    margin: 16px;
}

QWidget#scriptWidget:hover {
    border: 2px solid rgba(59, 130, 246, 0.8);
    background: rgba(255, 255, 255, 1.0);
}

QLabel#scriptName {
    font-size: 18px;
    font-weight: 700;
    color: #1e293b;
    letter-spacing: -0.2px;
    margin-bottom: 4px;
}

QLabel#scriptDescription {
    font-size: 14px;
    color: #64748b;
    font-weight: 400;
    line-height: 1.4;
    margin-bottom: 8px;
}

QLabel#scriptStatus {
    font-size: 12px;
    color: #94a3b8;
    font-weight: 500;
    padding: 4px 8px;
    background: rgba(148, 163, 184, 0.1);
    border-radius: 6px;
    border: 1px solid rgba(148, 163, 184, 0.2);
}

QLabel#scriptStatus[status="success"] {
    color: #059669;
    background: rgba(5, 150, 105, 0.1);
    border: 1px solid rgba(5, 150, 105, 0.2);
}

QLabel#scriptStatus[status="error"] {
    color: #dc2626;
    background: rgba(220, 38, 38, 0.1);
    border: 1px solid rgba(220, 38, 38, 0.2);
}

QLabel#scriptStatus[status="running"] {
    color: #ea580c;
    background: rgba(234, 88, 12, 0.1);
    border: 1px solid rgba(234, 88, 12, 0.2);
}

QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #3b82f6, stop:1 #2563eb);
    color: white;
    border: none;
    border-radius: 10px;
    padding: 12px 20px;
    font-size: 14px;
    font-weight: 600;
    min-width: 120px;
}

QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #2563eb, stop:1 #1d4ed8);
}

QPushButton:pressed {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #1d4ed8, stop:1 #1e40af);
}

QPushButton:disabled {
    background: #e2e8f0;
    color: #94a3b8;
}

QPushButton#toggleButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #6b7280, stop:1 #4b5563);
}

QPushButton#toggleButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #4b5563, stop:1 #374151);
}

QPushButton#toggleButton[state="on"] {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #10b981, stop:1 #059669);
}

QPushButton#toggleButton[state="on"]:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #059669, stop:1 #047857);
}

QPushButton#cycleButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #f59e0b, stop:1 #d97706);
}

QPushButton#cycleButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #d97706, stop:1 #b45309);
}

QComboBox {
    background: rgba(255, 255, 255, 0.9);
    border: 1px solid rgba(226, 232, 240, 0.8);
    border-radius: 10px;
    padding: 10px 16px;
    font-size: 14px;
    font-weight: 500;
    min-width: 140px;
    color: #1e293b;
}

QComboBox:hover {
    border: 1px solid rgba(59, 130, 246, 0.5);
    background: rgba(255, 255, 255, 1.0);
}

QComboBox:focus {
    border: 1px solid #3b82f6;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

QComboBox::down-arrow {
    width: 12px;
    height: 12px;
    background: #64748b;
}

QComboBox QAbstractItemView {
    background: rgba(255, 255, 255, 0.95);
    border: 1px solid rgba(226, 232, 240, 0.8);
    border-radius: 8px;
    padding: 4px;
    backdrop-filter: blur(20px);
}

QComboBox QAbstractItemView::item {
    padding: 8px 12px;
    border-radius: 6px;
    margin: 1px;
}

QComboBox QAbstractItemView::item:hover {
    background: rgba(59, 130, 246, 0.1);
    color: #1e293b;
}

QComboBox QAbstractItemView::item:selected {
    background: #3b82f6;
    color: white;
}

QSlider {
    min-width: 180px;
    height: 40px;
}

QSlider::groove:horizontal {
    border: none;
    height: 6px;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #e2e8f0, stop:1 #cbd5e1);
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #3b82f6, stop:1 #2563eb);
    border: 2px solid white;
    width: 20px;
    height: 20px;
    margin: -8px 0;
    border-radius: 12px;
}

QSlider::handle:horizontal:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #2563eb, stop:1 #1d4ed8);
}

QSlider::sub-page:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #3b82f6, stop:1 #2563eb);
    border-radius: 3px;
}

QLineEdit {
    background: rgba(255, 255, 255, 0.9);
    border: 1px solid rgba(226, 232, 240, 0.8);
    border-radius: 10px;
    padding: 12px 16px;
    font-size: 14px;
    font-weight: 500;
    min-width: 180px;
    color: #1e293b;
}

QLineEdit:hover {
    border: 1px solid rgba(59, 130, 246, 0.5);
    background: rgba(255, 255, 255, 1.0);
}

QLineEdit:focus {
    border: 1px solid #3b82f6;
    background: white;
    outline: none;
}

QSpinBox, QDoubleSpinBox {
    background: rgba(255, 255, 255, 0.9);
    border: 1px solid rgba(226, 232, 240, 0.8);
    border-radius: 10px;
    padding: 10px 16px;
    font-size: 14px;
    font-weight: 500;
    min-width: 120px;
    color: #1e293b;
}

QSpinBox:hover, QDoubleSpinBox:hover {
    border: 1px solid rgba(59, 130, 246, 0.5);
    background: rgba(255, 255, 255, 1.0);
}

QSpinBox:focus, QDoubleSpinBox:focus {
    border: 1px solid #3b82f6;
    background: white;
}

QSpinBox::up-button, QDoubleSpinBox::up-button {
    border: none;
    background: transparent;
    width: 20px;
}

QSpinBox::down-button, QDoubleSpinBox::down-button {
    border: none;
    background: transparent;
    width: 20px;
}

QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {
    width: 8px;
    height: 8px;
    background: #64748b;
}

QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {
    width: 8px;
    height: 8px;
    background: #64748b;
}
"""

# Button and widget styling will be embedded in MAIN_STYLE above