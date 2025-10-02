"""Unit tests for settings configuration"""

import pytest
import os
from unittest.mock import patch

from config.settings import Settings, DockerSettings, ServiceSettings, SecuritySettings


class TestDockerSettings:
    """Test cases for DockerSettings"""

    @pytest.mark.unit
    def test_default_values(self):
        """Test default Docker settings values"""
        settings = DockerSettings()

        assert settings.host == "unix:///var/run/docker.sock"
        assert settings.tls_verify is False
        assert settings.cert_path is None
        assert settings.timeout == 60

    @pytest.mark.unit
    def test_environment_override(self):
        """Test environment variable overrides"""
        with patch.dict(os.environ, {
            'DOCKER_HOST': 'tcp://localhost:2376',
            'DOCKER_TLS_VERIFY': 'true',
            'DOCKER_CERT_PATH': '/path/to/certs',
            'DOCKER_TIMEOUT': '120'
        }):
            settings = DockerSettings()

            assert settings.host == 'tcp://localhost:2376'
            assert settings.tls_verify is True
            assert settings.cert_path == '/path/to/certs'
            assert settings.timeout == 120


class TestServiceSettings:
    """Test cases for ServiceSettings"""

    @pytest.mark.unit
    def test_default_values(self):
        """Test default service settings values"""
        settings = ServiceSettings()

        assert settings.name == "meta-orchestrator"
        assert settings.version == "1.0.0"
        assert settings.debug is False
        assert settings.log_level == "INFO"

    @pytest.mark.unit
    def test_environment_override(self):
        """Test environment variable overrides for service settings"""
        with patch.dict(os.environ, {
            'DEBUG': 'true',
            'LOG_LEVEL': 'DEBUG'
        }):
            settings = ServiceSettings()

            assert settings.debug is True
            assert settings.log_level == "DEBUG"


class TestSecuritySettings:
    """Test cases for SecuritySettings"""

    @pytest.mark.unit
    def test_default_values(self):
        """Test default security settings values"""
        settings = SecuritySettings()

        assert settings.allowed_networks == ["172.0.0.0/8", "10.0.0.0/8"]
        assert settings.enable_auth is False
        assert settings.api_key is None

    @pytest.mark.unit
    def test_environment_override(self):
        """Test environment variable overrides for security settings"""
        with patch.dict(os.environ, {
            'ENABLE_AUTH': 'true',
            'API_KEY': 'test-key-123'
        }):
            settings = SecuritySettings()

            assert settings.enable_auth is True
            assert settings.api_key == "test-key-123"

    @pytest.mark.unit
    def test_custom_allowed_networks(self):
        """Test custom allowed networks"""
        settings = SecuritySettings(allowed_networks=["192.168.0.0/16"])

        assert settings.allowed_networks == ["192.168.0.0/16"]


class TestSettings:
    """Test cases for main Settings class"""

    @pytest.mark.unit
    def test_default_values(self):
        """Test default main settings values"""
        settings = Settings()

        assert settings.workspace_path == "/app"
        assert settings.compose_file == "docker-compose.dev.yml"
        assert settings.enable_auto_scaling is False
        assert settings.enable_config_sync is True
        assert settings.enable_health_monitoring is True

        # Check nested objects
        assert isinstance(settings.docker, DockerSettings)
        assert isinstance(settings.service, ServiceSettings)
        assert isinstance(settings.security, SecuritySettings)

    @pytest.mark.unit
    def test_environment_override_main(self):
        """Test environment variable overrides for main settings"""
        with patch.dict(os.environ, {
            'WORKSPACE_PATH': '/custom/path',
            'COMPOSE_FILE': 'docker-compose.prod.yml',
            'ENABLE_AUTO_SCALING': 'true',
            'ENABLE_CONFIG_SYNC': 'false',
            'ENABLE_HEALTH_MONITORING': 'false'
        }):
            settings = Settings()

            assert settings.workspace_path == '/custom/path'
            assert settings.compose_file == 'docker-compose.prod.yml'
            assert settings.enable_auto_scaling is True
            assert settings.enable_config_sync is False
            assert settings.enable_health_monitoring is False

    @pytest.mark.unit
    def test_nested_settings_integration(self):
        """Test that nested settings work together"""
        with patch.dict(os.environ, {
            'DOCKER_HOST': 'tcp://docker-host:2376',
            'DEBUG': 'true',
            'ENABLE_AUTH': 'true',
            'API_KEY': 'secure-key',
            'WORKSPACE_PATH': '/test/workspace'
        }):
            settings = Settings()

            # Docker settings
            assert settings.docker.host == 'tcp://docker-host:2376'

            # Service settings
            assert settings.service.debug is True

            # Security settings
            assert settings.security.enable_auth is True
            assert settings.security.api_key == 'secure-key'

            # Main settings
            assert settings.workspace_path == '/test/workspace'

    @pytest.mark.unit
    def test_settings_initialization_order(self):
        """Test that settings initialization happens in correct order"""
        settings = Settings()

        # Should initialize nested objects
        assert settings.service is not None
        assert settings.docker is not None
        assert settings.security is not None

        # Should have called _load_from_env
        assert settings.workspace_path == "/app"  # Default value
