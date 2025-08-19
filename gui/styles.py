# Modern Color Palette - Unified Blue Theme
COLORS = {
    'light': {
        'primary': '#3b82f6',           # Blue-500
        'primary_hover': '#2563eb',     # Blue-600  
        'primary_pressed': '#1d4ed8',   # Blue-700
        'primary_light': '#dbeafe',     # Blue-100
        'primary_lighter': '#eff6ff',   # Blue-50
        
        'background': '#ffffff',        # White
        'background_secondary': '#f8fafc', # Slate-50
        'background_tertiary': '#f1f5f9',  # Slate-100
        
        'surface': '#ffffff',           # White
        'surface_hover': '#f8fafc',     # Slate-50
        'surface_border': '#e2e8f0',    # Slate-200
        'surface_border_light': '#f1f5f9', # Slate-100
        
        'text_primary': '#0f172a',      # Slate-900
        'text_secondary': '#475569',    # Slate-600
        'text_tertiary': '#64748b',     # Slate-500
        'text_muted': '#94a3b8',        # Slate-400
        'text_on_primary': '#ffffff',   # White
        
        'success': '#059669',           # Emerald-600
        'success_bg': '#d1fae5',        # Emerald-100
        'warning': '#d97706',           # Amber-600
        'warning_bg': '#fef3c7',        # Amber-100
        'error': '#dc2626',             # Red-600
        'error_bg': '#fee2e2',          # Red-100
    },
    'dark': {
        'primary': '#60a5fa',           # Blue-400 (brighter for dark mode)
        'primary_hover': '#93c5fd',     # Blue-300
        'primary_pressed': '#3b82f6',   # Blue-500
        'primary_light': '#1e40af',     # Blue-800
        'primary_lighter': '#312e81',   # Indigo-800
        
        'background': '#111827',        # Gray-900 (true dark)
        'background_secondary': '#1f2937', # Gray-800
        'background_tertiary': '#374151',  # Gray-700
        
        'surface': '#1f2937',           # Gray-800 (card backgrounds)
        'surface_hover': '#374151',     # Gray-700
        'surface_border': '#4b5563',    # Gray-600
        'surface_border_light': '#374151', # Gray-700
        
        'text_primary': '#ffffff',      # Pure white for primary text
        'text_secondary': '#d1d5db',    # Gray-300 (high contrast secondary)
        'text_tertiary': '#9ca3af',     # Gray-400
        'text_muted': '#6b7280',        # Gray-500
        'text_on_primary': '#111827',   # Dark text on primary buttons
        
        'success': '#34d399',           # Emerald-400 (brighter for dark)
        'success_bg': '#065f46',        # Emerald-800
        'warning': '#fbbf24',           # Amber-400 (brighter for dark)
        'warning_bg': '#92400e',        # Amber-800
        'error': '#f87171',             # Red-400 (brighter for dark)
        'error_bg': '#991b1b',          # Red-800
    }
}

def get_theme_style(theme='light'):
    colors = COLORS[theme]
    
    return f"""
QMainWindow {{
    background: {colors['background']};
    font-family: 'Segoe UI', 'SF Pro Display', system-ui, sans-serif;
    color: {colors['text_primary']};
}}

QScrollArea {{
    background: transparent;
    border: none;
    border-radius: 12px;
}}

QScrollArea QScrollBar:vertical {{
    background: {colors['surface_border_light']};
    width: 8px;
    border-radius: 4px;
    margin: 4px;
}}

QScrollArea QScrollBar::handle:vertical {{
    background: {colors['text_muted']};
    border-radius: 4px;
    min-height: 30px;
}}

QScrollArea QScrollBar::handle:vertical:hover {{
    background: {colors['text_tertiary']};
}}

QScrollArea QScrollBar::add-line:vertical, QScrollArea QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QWidget#scriptListContainer {{
    background: transparent;
    padding: 0px;
}}

QLabel#titleLabel {{
    font-size: 32px;
    font-weight: 700;
    color: {colors['text_primary']};
    padding: 32px 0px 8px 0px;
    letter-spacing: -0.5px;
}}

QLabel#subtitleLabel {{
    font-size: 16px;
    font-weight: 400;
    color: {colors['text_secondary']};
    padding: 0px 0px 32px 0px;
    margin-bottom: 8px;
}}

QLabel#errorLabel {{
    color: {colors['error']};
    font-size: 13px;
    font-weight: 500;
    padding: 12px 16px;
    background: {colors['error_bg']};
    border: 1px solid {colors['error']};
    border-radius: 8px;
    margin: 8px 0px;
}}

QLabel#statusLabel {{
    color: {colors['text_secondary']};
    font-size: 14px;
    font-weight: 500;
    padding: 16px 32px;
    background: {colors['surface']};
    border-top: 1px solid {colors['surface_border']};
}}

QPushButton#refreshButton {{
    background: {colors['primary']};
    color: {colors['text_on_primary']};
    border: none;
    border-radius: 12px;
    padding: 14px 28px;
    font-size: 14px;
    font-weight: 600;
    min-width: 100px;
}}

QPushButton#refreshButton:hover {{
    background: {colors['primary_hover']};
}}

QPushButton#refreshButton:pressed {{
    background: {colors['primary_pressed']};
}}

QPushButton#themeButton {{
    background: {colors['surface']};
    color: {colors['text_primary']};
    border: 1px solid {colors['surface_border']};
    border-radius: 22px;
    padding: 8px;
    font-size: 16px;
    min-width: 44px;
    max-width: 44px;
}}

QPushButton#themeButton:hover {{
    background: {colors['surface_hover']};
    border: 1px solid {colors['primary']};
}}

QPushButton#themeButton:pressed {{
    background: {colors['primary_lighter']};
}}

QWidget#headerWidget {{
    background: {colors['surface']};
    border-radius: 20px;
    margin: 20px;
    border: 1px solid {colors['surface_border']};
    padding: 8px;
}}

QWidget#scriptWidget {{
    background: {colors['surface']};
    border: 1px solid {colors['surface_border']};
    border-radius: 12px;
    margin: 4px;
}}

QWidget#scriptWidget:hover {{
    border: 1px solid {colors['primary']};
    background: {colors['surface_hover']};
}}

QLabel#scriptName {{
    font-size: 20px;
    font-weight: 700;
    color: {colors['text_primary']};
    letter-spacing: -0.3px;
    margin-bottom: 6px;
}}

QLabel#scriptDescription {{
    font-size: 14px;
    color: {colors['text_secondary']};
    font-weight: 400;
    line-height: 1.5;
    margin-bottom: 12px;
}}

QLabel#scriptStatus {{
    font-size: 12px;
    color: {colors['text_tertiary']};
    font-weight: 500;
    padding: 6px 12px;
    background: {colors['surface_border_light']};
    border-radius: 8px;
    border: 1px solid {colors['surface_border']};
}}

QLabel#scriptStatus[status="success"] {{
    color: {colors['success']};
    background: {colors['success_bg']};
    border: 1px solid {colors['success']};
}}

QLabel#scriptStatus[status="error"] {{
    color: {colors['error']};
    background: {colors['error_bg']};
    border: 1px solid {colors['error']};
}}

QLabel#scriptStatus[status="running"] {{
    color: {colors['warning']};
    background: {colors['warning_bg']};
    border: 1px solid {colors['warning']};
}}

QPushButton {{
    background: {colors['primary']};
    color: {colors['text_on_primary']};
    border: none;
    border-radius: 12px;
    padding: 14px 24px;
    font-size: 14px;
    font-weight: 600;
    min-width: 140px;
}}

QPushButton:hover {{
    background: {colors['primary_hover']};
}}

QPushButton:pressed {{
    background: {colors['primary_pressed']};
}}

QPushButton:disabled {{
    background: {colors['surface_border']};
    color: {colors['text_muted']};
}}

QPushButton#toggleButton {{
    background: {colors['surface_border']};
    color: {colors['text_secondary']};
}}

QPushButton#toggleButton:hover {{
    background: {colors['text_muted']};
    color: {colors['text_on_primary']};
}}

QPushButton#toggleButton[state="on"] {{
    background: {colors['success']};
    color: {colors['text_on_primary']};
}}

QPushButton#toggleButton[state="on"]:hover {{
    background: {colors['success']};
    color: {colors['text_on_primary']};
}}

QPushButton#cycleButton {{
    background: {colors['primary']};
    color: {colors['text_on_primary']};
}}

QPushButton#cycleButton:hover {{
    background: {colors['primary_hover']};
}}

QComboBox {{
    background: {colors['surface']};
    border: 1px solid {colors['surface_border']};
    border-radius: 12px;
    padding: 12px 16px;
    font-size: 14px;
    font-weight: 500;
    min-width: 160px;
    color: {colors['text_primary']};
}}

QComboBox:hover {{
    border: 1px solid {colors['primary']};
    background: {colors['surface_hover']};
}}

QComboBox:focus {{
    border: 1px solid {colors['primary']};
}}

QComboBox::drop-down {{
    border: none;
    width: 24px;
}}

QComboBox::down-arrow {{
    width: 12px;
    height: 12px;
    background: {colors['text_tertiary']};
}}

QComboBox QAbstractItemView {{
    background: {colors['surface']};
    border: 1px solid {colors['surface_border']};
    border-radius: 12px;
    padding: 8px;
}}

QComboBox QAbstractItemView::item {{
    padding: 12px 16px;
    border-radius: 8px;
    margin: 2px;
    color: {colors['text_primary']};
}}

QComboBox QAbstractItemView::item:hover {{
    background: {colors['primary_lighter']};
    color: {colors['text_primary']};
}}

QComboBox QAbstractItemView::item:selected {{
    background: {colors['primary']};
    color: {colors['text_on_primary']};
}}

QSlider {{
    min-width: 200px;
    height: 44px;
}}

QSlider::groove:horizontal {{
    border: none;
    height: 8px;
    background: {colors['surface_border']};
    border-radius: 4px;
}}

QSlider::handle:horizontal {{
    background: {colors['primary']};
    border: 3px solid {colors['surface']};
    width: 24px;
    height: 24px;
    margin: -10px 0;
    border-radius: 12px;
}}

QSlider::handle:horizontal:hover {{
    background: {colors['primary_hover']};
}}

QSlider::sub-page:horizontal {{
    background: {colors['primary']};
    border-radius: 4px;
}}

QLineEdit {{
    background: {colors['surface']};
    border: 1px solid {colors['surface_border']};
    border-radius: 12px;
    padding: 14px 16px;
    font-size: 14px;
    font-weight: 500;
    min-width: 200px;
    color: {colors['text_primary']};
}}

QLineEdit:hover {{
    border: 1px solid {colors['primary']};
    background: {colors['surface_hover']};
}}

QLineEdit:focus {{
    border: 1px solid {colors['primary']};
    background: {colors['surface']};
    outline: none;
}}

QSpinBox, QDoubleSpinBox {{
    background: {colors['surface']};
    border: 1px solid {colors['surface_border']};
    border-radius: 12px;
    padding: 12px 16px;
    font-size: 14px;
    font-weight: 500;
    min-width: 140px;
    color: {colors['text_primary']};
}}

QSpinBox:hover, QDoubleSpinBox:hover {{
    border: 1px solid {colors['primary']};
    background: {colors['surface_hover']};
}}

QSpinBox:focus, QDoubleSpinBox:focus {{
    border: 1px solid {colors['primary']};
    background: {colors['surface']};
}}

QSpinBox::up-button, QDoubleSpinBox::up-button {{
    border: none;
    background: transparent;
    width: 24px;
}}

QSpinBox::down-button, QDoubleSpinBox::down-button {{
    border: none;
    background: transparent;
    width: 24px;
}}

QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{
    width: 10px;
    height: 10px;
    background: {colors['text_tertiary']};
}}

QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{
    width: 10px;
    height: 10px;
    background: {colors['text_tertiary']};
}}

/* Modern Segmented Control */
QPushButton#segmentButton {{
    background: {colors['surface']};
    color: {colors['text_secondary']};
    border: 1px solid {colors['surface_border']};
    padding: 12px 16px;
    font-size: 14px;
    font-weight: 500;
    min-width: 80px;
}}

QPushButton#segmentButton[position="single"] {{
    border-radius: 12px;
}}

QPushButton#segmentButton[position="first"] {{
    border-radius: 12px 0px 0px 12px;
    border-right: none;
}}

QPushButton#segmentButton[position="middle"] {{
    border-radius: 0px;
    border-right: none;
}}

QPushButton#segmentButton[position="last"] {{
    border-radius: 0px 12px 12px 0px;
}}

QPushButton#segmentButton:hover {{
    background: {colors['surface_hover']};
    color: {colors['text_primary']};
}}

QPushButton#segmentButton[selected="true"] {{
    background: {colors['primary']};
    color: {colors['text_on_primary']};
    border: 1px solid {colors['primary']};
}}

QPushButton#segmentButton[selected="true"]:hover {{
    background: {colors['primary_hover']};
}}

/* Modern Button Group */
QPushButton#groupButton {{
    text-align: left;
    padding: 14px 20px;
    border: 1px solid {colors['surface_border']};
    border-radius: 12px;
    background: {colors['surface']};
    color: {colors['text_primary']};
    font-weight: 500;
    font-size: 14px;
    margin: 2px 0px;
}}

QPushButton#groupButton:hover {{
    border: 1px solid {colors['primary']};
    background: {colors['surface_hover']};
}}

QPushButton#groupButton:checked {{
    background: {colors['primary']};
    color: {colors['text_on_primary']};
    border: 1px solid {colors['primary']};
}}

/* Enhanced Slider Value Label */
QLabel#sliderValue {{
    font-size: 12px;
    font-weight: 600;
    color: {colors['primary']};
    padding: 4px 10px;
    background: {colors['primary_lighter']};
    border-radius: 8px;
    border: 1px solid {colors['primary']};
}}
"""

# Default to light theme
MAIN_STYLE = get_theme_style('light')