"""Unit tests for dashboard configuration."""

import pytest
import os
from unittest.mock import patch, MagicMock

from infrastructure.config.config import (
    get_config, DashboardSettings, SimulationServiceConfig,
    WebSocketConfig, LoggingConfig, PerformanceConfig
)


class TestSimulationServiceConfig:
    """Test cases for SimulationServiceConfig."""

    def test_config_initialization(self):
        """Test basic configuration initialization."""
        config = SimulationServiceConfig()
        assert config.host == "localhost"
        assert config.port == 5075
        assert config.timeout == 30.0
        assert config.retry_attempts == 3

    def test_base_url_generation(self):
        """Test automatic base URL generation."""
        config = SimulationServiceConfig(host="test-host", port=8080)
        assert config.base_url == "http://test-host:8080"

    def test_custom_base_url(self):
        """Test custom base URL override."""
        config = SimulationServiceConfig(
            host="test-host",
            port=8080,
            base_url="https://custom-url.com"
        )
        assert config.base_url == "https://custom-url.com"


class TestWebSocketConfig:
    """Test cases for WebSocketConfig."""

    def test_websocket_config_defaults(self):
        """Test WebSocket configuration defaults."""
        config = WebSocketConfig()
        assert config.enabled is True
        assert config.reconnect_attempts == 5
        assert config.heartbeat_interval == 30.0
        assert config.message_timeout == 10.0


class TestLoggingConfig:
    """Test cases for LoggingConfig."""

    def test_logging_config_defaults(self):
        """Test logging configuration defaults."""
        config = LoggingConfig()
        assert config.level == "INFO"
        assert config.format == "json"
        assert config.enable_structlog is True
        assert config.log_requests is True
        assert config.log_websocket is True


class TestPerformanceConfig:
    """Test cases for PerformanceConfig."""

    def test_performance_config_defaults(self):
        """Test performance configuration defaults."""
        config = PerformanceConfig()
        assert config.enable_compression is True
        assert config.max_concurrent_requests == 10
        assert config.connection_pool_size == 20
        assert config.cache_size == 1000


class TestDashboardSettings:
    """Test cases for DashboardSettings."""

    @patch.dict(os.environ, {
        'DASHBOARD_ENVIRONMENT': 'production',
        'DASHBOARD_DEBUG': 'false',
        'DASHBOARD_PORT': '9000',
        'DASHBOARD_SIMULATION_SERVICE_HOST': 'sim-host',
        'DASHBOARD_SIMULATION_SERVICE_PORT': '8080'
    })
    def test_environment_variable_loading(self):
        """Test loading configuration from environment variables."""
        config = DashboardSettings()

        assert config.environment == "production"
        assert config.debug is False
        assert config.port == 9000
        assert config.simulation_service.host == "sim-host"
        assert config.simulation_service.port == 8080
        assert config.simulation_service.base_url == "http://sim-host:8080"

    def test_development_environment_detection(self):
        """Test development environment detection."""
        config = DashboardSettings()
        config.environment = "development"
        assert config.is_development() is True
        assert config.is_production() is False

    def test_production_environment_detection(self):
        """Test production environment detection."""
        config = DashboardSettings()
        config.environment = "production"
        assert config.is_development() is False
        assert config.is_production() is True

    def test_simulation_service_url_generation(self):
        """Test simulation service URL generation."""
        config = DashboardSettings()
        config.simulation_service.host = "test-host"
        config.simulation_service.port = 9090

        # Test base URL
        assert config.get_simulation_service_url() == "http://test-host:9090"

        # Test URL with path
        assert config.get_simulation_service_url("api/v1/health") == "http://test-host:9090/api/v1/health"

    def test_optional_service_urls(self):
        """Test optional ecosystem service URLs."""
        config = DashboardSettings()
        assert config.analysis_service_url is None
        assert config.health_service_url is None

        # Set optional URLs
        config.analysis_service_url = "http://analysis:5080"
        config.health_service_url = "http://health:5130"

        assert config.analysis_service_url == "http://analysis:5080"
        assert config.health_service_url == "http://health:5130"


class TestGlobalConfig:
    """Test cases for global configuration management."""

    @patch('infrastructure.config.config.DashboardSettings')
    def test_get_config_singleton(self, mock_config_class):
        """Test that get_config returns a singleton instance."""
        mock_instance = MagicMock()
        mock_config_class.return_value = mock_instance

        # First call
        config1 = get_config()
        # Second call
        config2 = get_config()

        assert config1 is config2
        assert mock_config_class.call_count == 1

    @patch('infrastructure.config.config._config', None)
    @patch('infrastructure.config.config.DashboardSettings')
    def test_config_reload(self, mock_config_class):
        """Test configuration reloading."""
        from infrastructure.config.config import reload_config

        mock_instance = MagicMock()
        mock_config_class.return_value = mock_instance

        # Reload configuration
        config = reload_config()

        assert config is mock_instance
        mock_config_class.assert_called_once()


class TestConfigurationValidation:
    """Test cases for configuration validation."""

    def test_invalid_port_number(self):
        """Test handling of invalid port numbers."""
        with pytest.raises(ValueError):
            DashboardSettings(port=-1)

    def test_invalid_timeout_values(self):
        """Test handling of invalid timeout values."""
        config = SimulationServiceConfig()
        config.timeout = -5.0  # Invalid timeout

        # Should still work but may cause issues downstream
        assert config.timeout == -5.0

    def test_websocket_config_validation(self):
        """Test WebSocket configuration validation."""
        config = WebSocketConfig()
        config.reconnect_attempts = 0  # Edge case

        # Should still work
        assert config.reconnect_attempts == 0


class TestConfigurationFileLoading:
    """Test cases for configuration file loading."""

    @patch('infrastructure.config.config.BaseSettings.Config.env_file', '.env.test')
    def test_env_file_configuration(self):
        """Test loading configuration from .env file."""
        # This would require creating a test .env file
        # For now, just ensure the configuration can be created
        config = DashboardSettings()
        assert config.environment is not None

    def test_missing_environment_variables(self):
        """Test behavior with missing environment variables."""
        # Clear any existing environment
        with patch.dict(os.environ, {}, clear=True):
            config = DashboardSettings()

            # Should use defaults
            assert config.environment == "development"
            assert config.debug is False
            assert config.port == 8501


if __name__ == "__main__":
    pytest.main([__file__])
