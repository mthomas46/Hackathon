"""Tests for health monitoring."""

import pytest
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.health_monitor import HealthMonitor, HealthStatus


class TestHealthStatus:
    """Test HealthStatus dataclass."""
    
    def test_health_status_creation(self):
        """Test creating a HealthStatus."""
        status = HealthStatus(
            name="Test",
            status="healthy",
            latency_ms=50.0,
            last_check=datetime.now()
        )
        
        assert status.name == "Test"
        assert status.status == "healthy"
        assert status.latency_ms == 50.0
        assert isinstance(status.last_check, datetime)
        assert status.error_message is None
        assert status.details == {}
    
    def test_health_status_with_error(self):
        """Test HealthStatus with error message."""
        status = HealthStatus(
            name="Test",
            status="unhealthy",
            latency_ms=1000.0,
            last_check=datetime.now(),
            error_message="Connection failed"
        )
        
        assert status.status == "unhealthy"
        assert status.error_message == "Connection failed"
    
    def test_health_status_with_details(self):
        """Test HealthStatus with details."""
        details = {"version": "1.0", "uptime": 3600}
        status = HealthStatus(
            name="Test",
            status="healthy",
            latency_ms=25.0,
            last_check=datetime.now(),
            details=details
        )
        
        assert status.details == details


class TestHealthMonitor:
    """Test HealthMonitor class."""
    
    def test_health_monitor_initialization(self):
        """Test health monitor initialization."""
        monitor = HealthMonitor("http://localhost:8000", timeout=5.0)
        
        assert monitor.api_base_url == "http://localhost:8000"
        assert monitor.timeout == 5.0
        assert monitor.health_history == []
        assert monitor.max_history == 100
    
    def test_check_api_health_sync(self):
        """Test synchronous API health check."""
        monitor = HealthMonitor("http://localhost:8000", timeout=3.0)
        result = monitor.check_api_health_sync()
        
        assert isinstance(result, HealthStatus)
        assert result.name == "API"
        assert result.status in ["healthy", "unhealthy", "unknown"]
        assert isinstance(result.latency_ms, float)
        assert isinstance(result.last_check, datetime)
    
    def test_check_datasource(self):
        """Test datasource health check."""
        monitor = HealthMonitor("http://localhost:8000", timeout=3.0)
        result = monitor.check_datasource("Redis", "/api/v1/redis/info")
        
        assert isinstance(result, HealthStatus)
        assert result.name == "Redis"
        assert result.status in ["healthy", "degraded", "unhealthy", "unknown"]
    
    def test_check_all_datasources(self):
        """Test checking all datasources."""
        monitor = HealthMonitor("http://localhost:8000", timeout=3.0)
        results = monitor.check_all_datasources()
        
        assert isinstance(results, dict)
        assert "API" in results
        
        # Should have stored in history
        assert len(monitor.health_history) == 1
        assert monitor.health_history[0] == results
        
        for name, status in results.items():
            assert isinstance(status, HealthStatus)
            assert status.name == name
    
    def test_get_overall_status(self):
        """Test overall status calculation."""
        monitor = HealthMonitor("http://localhost:8000")
        
        # All healthy
        results = {
            "API": HealthStatus("API", "healthy", 50.0, datetime.now()),
            "Redis": HealthStatus("Redis", "healthy", 30.0, datetime.now())
        }
        assert monitor.get_overall_status(results) == "healthy"
        
        # One unhealthy
        results["Redis"].status = "unhealthy"
        assert monitor.get_overall_status(results) == "unhealthy"
        
        # One degraded
        results["Redis"].status = "degraded"
        assert monitor.get_overall_status(results) == "degraded"
    
    def test_get_status_color(self):
        """Test status color emoji mapping."""
        monitor = HealthMonitor("http://localhost:8000")
        
        assert monitor.get_status_color("healthy") == "🟢"
        assert monitor.get_status_color("degraded") == "🟡"
        assert monitor.get_status_color("unhealthy") == "🔴"
        assert monitor.get_status_color("unknown") == "⚪"
        assert monitor.get_status_color("invalid") == "⚪"
    
    def test_health_history_limit(self):
        """Test that health history respects max_history limit."""
        monitor = HealthMonitor("http://localhost:8000")
        monitor.max_history = 5
        
        # Add more than max_history checks
        for i in range(10):
            monitor.check_all_datasources()
        
        # Should only keep last 5
        assert len(monitor.health_history) == 5
    
    def test_get_average_latency(self):
        """Test average latency calculation."""
        monitor = HealthMonitor("http://localhost:8000")
        
        # No history
        assert monitor.get_average_latency() == 0.0
        
        # Add some history
        monitor.health_history.append({
            "API": HealthStatus("API", "healthy", 50.0, datetime.now()),
            "Redis": HealthStatus("Redis", "healthy", 30.0, datetime.now())
        })
        monitor.health_history.append({
            "API": HealthStatus("API", "healthy", 60.0, datetime.now()),
            "Redis": HealthStatus("Redis", "healthy", 40.0, datetime.now())
        })
        
        avg = monitor.get_average_latency()
        assert avg == 45.0  # (50 + 30 + 60 + 40) / 4
    
    def test_get_uptime_percentage(self):
        """Test uptime percentage calculation."""
        monitor = HealthMonitor("http://localhost:8000")
        
        # No history
        assert monitor.get_uptime_percentage("API") == 0.0
        
        # Add history with some failures
        for i in range(10):
            status = "healthy" if i < 8 else "unhealthy"
            monitor.health_history.append({
                "API": HealthStatus("API", status, 50.0, datetime.now())
            })
        
        # Should be 80% uptime (8 out of 10)
        assert monitor.get_uptime_percentage("API") == 80.0

