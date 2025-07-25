#!/usr/bin/env python3
"""
Tests for the load generation script
"""

from unittest.mock import Mock, patch
import sys
import os

# Add the scripts directory to the path so we can import generate_load
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from generate_load import LoadGenerator


class TestLoadGenerator:
    """Test cases for the LoadGenerator class"""

    def setup_method(self):
        """Set up test fixtures before each test method"""
        self.generator = LoadGenerator("http://test-server:8000", max_workers=2)

    @patch('generate_load.requests.get')
    def test_make_request_success(self, mock_get):
        """Test successful HTTP request"""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.elapsed.total_seconds.return_value = 0.5
        mock_get.return_value = mock_response

        status_code, duration = self.generator.make_request('/test')

        assert status_code == 200
        assert duration == 0.5
        mock_get.assert_called_once_with("http://test-server:8000/test", timeout=10)


class TestMainFunction:
    """Test cases for the main function and argument parsing"""

    @patch('generate_load.LoadGenerator')
    @patch('sys.argv', ['generate_load.py', '--scenario', 'demo'])
    def test_main_demo_scenario(self, mock_generator_class):
        """Test main function with demo scenario"""
        mock_generator = Mock()
        mock_generator_class.return_value = mock_generator

        from generate_load import main

        with patch('builtins.print'):
            try:
                main()
            except SystemExit:
                pass

        mock_generator.run_demo_scenario.assert_called_once()