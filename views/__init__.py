"""
View layer for Desktop Utility GUI following MVC pattern.

Views contain UI components and display logic only.
They emit signals for user interactions and have slots for updating display.
"""

from .main_view import MainView
from .tray_view import TrayView

__all__ = [
    'MainView',
    'TrayView'
]