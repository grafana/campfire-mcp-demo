#!/usr/bin/env python3
"""
Integration tests using real HTTP requests.
Requires Docker Compose to be running.
"""

import requests
import pytest

@pytest.mark.integration
class TestAppIntegration:
    """Integration tests using real HTTP requests to running services"""

    @classmethod
    def setup_class(cls):
        """Set base URL for tests"""
        cls.base_url = "http://localhost:8000"

    def test_home_endpoint_real_http(self):
        """Test home endpoint with real HTTP request"""
        response = requests.get(f"{self.base_url}/")

        assert response.status_code == 200
        assert "Welcome to the Simplified Metrics Demo App!" in response.text

    def test_health_endpoint_real_http(self):
        """Test health endpoint with real HTTP request"""
        response = requests.get(f"{self.base_url}/health")

        assert response.status_code == 200
        health_data = response.json()

        assert health_data['status'] == 'healthy'
        assert 'timestamp' in health_data

    def test_metrics_endpoint_real_http(self):
        """Test metrics endpoint with real HTTP request"""
        response = requests.get(f"{self.base_url}/metrics")

        assert response.status_code == 200
        assert 'http_requests_total' in response.text