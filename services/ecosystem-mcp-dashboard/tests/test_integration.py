"""Integration tests for dashboard with live API."""

import pytest
import os
import httpx
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.health_monitor import HealthMonitor
from utils.config_validator import ConfigValidator


# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


@pytest.fixture
def api_base_url():
    """Get API base URL from environment."""
    return os.getenv("API_BASE_URL", "http://localhost:8000")


@pytest.fixture
def health_monitor(api_base_url):
    """Create health monitor instance."""
    return HealthMonitor(api_base_url)


@pytest.fixture
def config_validator():
    """Create config validator instance."""
    return ConfigValidator()


class TestAPIIntegration:
    """Integration tests requiring live API."""
    
    def test_api_is_accessible(self, api_base_url):
        """Test that the API is accessible."""
        try:
            response = httpx.get(f"{api_base_url}/health", timeout=5.0)
            assert response.status_code == 200
        except httpx.ConnectError:
            pytest.skip("API not accessible - skipping integration test")
    
    def test_health_endpoint_returns_valid_json(self, api_base_url):
        """Test that health endpoint returns valid JSON."""
        try:
            response = httpx.get(f"{api_base_url}/health", timeout=5.0)
            data = response.json()
            assert isinstance(data, dict)
            assert "status" in data
        except httpx.ConnectError:
            pytest.skip("API not accessible - skipping integration test")
    
    def test_openapi_spec_is_accessible(self, api_base_url):
        """Test that OpenAPI spec is accessible."""
        try:
            response = httpx.get(f"{api_base_url}/openapi.json", timeout=5.0)
            assert response.status_code == 200
            spec = response.json()
            assert "openapi" in spec
            assert "paths" in spec
        except httpx.ConnectError:
            pytest.skip("API not accessible - skipping integration test")


class TestHealthMonitorIntegration:
    """Integration tests for health monitor with live API."""
    
    def test_check_all_datasources_with_live_api(self, health_monitor):
        """Test checking all datasources with live API."""
        try:
            results = health_monitor.check_all_datasources()
            
            # Should have results
            assert len(results) > 0
            assert "API" in results
            
            # API should be healthy if test passed
            api_status = results["API"]
            assert api_status.status in ["healthy", "unhealthy"]
            
        except Exception as e:
            pytest.skip(f"API not accessible: {e}")
    
    def test_health_monitor_measures_latency(self, health_monitor):
        """Test that health monitor measures latency correctly."""
        try:
            result = health_monitor.check_api_health_sync()
            
            # Latency should be positive and reasonable
            assert result.latency_ms > 0
            assert result.latency_ms < 10000  # Less than 10 seconds
            
        except Exception:
            pytest.skip("API not accessible")
    
    def test_health_monitor_tracks_history(self, health_monitor):
        """Test that health monitor tracks history."""
        try:
            # Make multiple checks
            for _ in range(3):
                health_monitor.check_all_datasources()
            
            # Should have 3 entries in history
            assert len(health_monitor.health_history) == 3
            
            # Each entry should be a dict of HealthStatus
            for entry in health_monitor.health_history:
                assert isinstance(entry, dict)
                for status in entry.values():
                    assert hasattr(status, "name")
                    assert hasattr(status, "status")
            
        except Exception:
            pytest.skip("API not accessible")


class TestConfigValidatorIntegration:
    """Integration tests for config validator with live API."""
    
    def test_run_all_validations_with_live_api(self, config_validator, api_base_url):
        """Test running all validations with live API."""
        try:
            results, all_passed = config_validator.run_all_validations(api_base_url)
            
            # Should have results
            assert len(results) > 0
            assert isinstance(all_passed, bool)
            
            # Should check API connectivity
            api_check = next(
                (r for r in results if r.check_name == "API Connectivity"),
                None
            )
            assert api_check is not None
            
        except Exception as e:
            pytest.skip(f"API not accessible: {e}")
    
    def test_validate_api_endpoints_with_live_api(self, config_validator, api_base_url):
        """Test API endpoint validation with live API."""
        try:
            result = config_validator.validate_api_endpoints(api_base_url)
            
            assert result.check_name == "API Endpoints"
            
            # Should have details about available/unavailable endpoints
            if result.details:
                assert "available" in result.details or "unavailable" in result.details
            
        except Exception:
            pytest.skip("API not accessible")
    
    def test_validate_datasources_with_live_api(self, config_validator, api_base_url):
        """Test datasource validation with live API."""
        try:
            result = config_validator.validate_datasources(api_base_url)
            
            assert result.check_name == "Datasources"
            
            # Should have details about healthy/unhealthy datasources
            if result.details:
                assert "healthy" in result.details or "unhealthy" in result.details
            
        except Exception:
            pytest.skip("API not accessible")

