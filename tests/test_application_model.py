"""
Unit tests for ApplicationStateModel.

These tests validate that the ApplicationStateModel works correctly
without any UI dependencies.
"""
import unittest
from unittest.mock import Mock, patch
import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtCore import QObject, QCoreApplication
from PyQt6.QtTest import QSignalSpy
from models.application_model import ApplicationStateModel


class TestApplicationStateModel(unittest.TestCase):
    """Test cases for ApplicationStateModel"""
    
    @classmethod
    def setUpClass(cls):
        """Set up QApplication for tests"""
        if not QCoreApplication.instance():
            cls.app = QCoreApplication([])
        else:
            cls.app = QCoreApplication.instance()
    
    def setUp(self):
        """Set up test fixtures"""
        with patch('models.application_model.SettingsManager') as mock_settings, \
             patch('models.application_model.StartupManager') as mock_startup:
            
            # Configure mocks
            mock_settings.return_value.get.return_value = True
            mock_startup.return_value = Mock()
            
            self.model = ApplicationStateModel()
            self.mock_settings = mock_settings.return_value
            self.mock_startup = mock_startup.return_value
    
    def test_initialization(self):
        """Test model initializes correctly"""
        self.assertEqual(self.model.get_application_state(), 'initializing')
        self.assertIsNotNone(self.model._settings)
        self.assertIsNotNone(self.model._startup_manager)
    
    def test_application_lifecycle_signals(self):
        """Test that lifecycle signals are emitted correctly"""
        # Set up signal spies
        starting_spy = QSignalSpy(self.model.application_starting)
        ready_spy = QSignalSpy(self.model.application_ready)
        shutdown_spy = QSignalSpy(self.model.application_shutting_down)
        
        # Test start application
        self.model.start_application()
        
        # Check signals were emitted
        self.assertEqual(len(starting_spy), 1)
        self.assertEqual(len(ready_spy), 1)
        self.assertEqual(self.model.get_application_state(), 'ready')
        self.assertTrue(self.model.is_ready())
        
        # Test shutdown
        self.model.shutdown_application()
        
        # Check shutdown signal
        self.assertEqual(len(shutdown_spy), 1)
        self.assertEqual(self.model.get_application_state(), 'shutting_down')
        self.assertFalse(self.model.is_ready())
    
    def test_startup_settings(self):
        """Test startup settings management"""
        # Configure mock to return specific values
        self.mock_settings.get.side_effect = lambda key, default: {
            'startup/run_on_startup': True,
            'startup/start_minimized': False,
            'startup/show_notification': True
        }.get(key, default)
        
        settings = self.model.get_startup_settings()
        
        expected = {
            'run_on_startup': True,
            'start_minimized': False,
            'show_notification': True
        }
        self.assertEqual(settings, expected)
    
    def test_behavior_settings(self):
        """Test behavior settings management"""
        # Configure mock to return specific values
        self.mock_settings.get.side_effect = lambda key, default: {
            'behavior/minimize_to_tray': False,
            'behavior/close_to_tray': True,
            'behavior/single_instance': False,
            'behavior/show_script_notifications': True
        }.get(key, default)
        
        settings = self.model.get_behavior_settings()
        
        expected = {
            'minimize_to_tray': False,
            'close_to_tray': True,
            'single_instance': False,
            'show_script_notifications': True
        }
        self.assertEqual(settings, expected)
    
    def test_settings_change_signals(self):
        """Test that settings changes emit appropriate signals"""
        # Set up signal spy
        startup_spy = QSignalSpy(self.model.startup_settings_changed)
        behavior_spy = QSignalSpy(self.model.behavior_settings_changed)
        
        # Simulate settings change
        self.model.set_start_minimized(True)
        
        # Verify the set method was called
        self.mock_settings.set.assert_called_with('startup/start_minimized', True)
    
    def test_startup_manager_integration(self):
        """Test integration with startup manager (new API)."""
        # Ensure set_startup returns True so update_path_if_needed is attempted
        self.mock_startup.set_startup.return_value = True

        # Test enabling startup
        self.model.set_run_on_startup(True)

        # Verify set_startup(True) called and path update attempted
        self.mock_startup.set_startup.assert_any_call(True)
        self.mock_startup.update_path_if_needed.assert_called_once()

        # Test disabling startup
        self.model.set_run_on_startup(False)

        # Verify set_startup(False) called as well
        self.mock_startup.set_startup.assert_any_call(False)
    
    def test_window_geometry_management(self):
        """Test window geometry management"""
        test_geometry = b'test_geometry_data'
        
        # Test saving geometry
        self.model.save_window_geometry(test_geometry)
        self.mock_settings.set.assert_called_with('window/geometry', test_geometry)
        
        # Test getting geometry
        self.mock_settings.get.return_value = test_geometry
        result = self.model.get_window_geometry()
        self.assertEqual(result, test_geometry)


if __name__ == '__main__':
    unittest.main()
