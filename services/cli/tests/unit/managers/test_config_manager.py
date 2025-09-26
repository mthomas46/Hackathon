"""Comprehensive tests for CLI ConfigManager."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add service path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from cli.modules.managers.config.config_manager import ConfigManager


class TestConfigManager:
    """Test ConfigManager functionality."""

    @pytest.fixture
    def config_manager(self):
        """Create ConfigManager instance."""
        return ConfigManager()

    def test_config_manager_initialization(self, config_manager):
        """Test ConfigManager initialization."""
        assert config_manager is not None
        assert hasattr(config_manager, 'load_config')
        assert hasattr(config_manager, 'save_config')
        assert hasattr(config_manager, 'get_config')
        assert hasattr(config_manager, 'set_config')

    @pytest.mark.asyncio
    async def test_load_config_success(self, config_manager):
        """Test successful config loading."""
        with patch('builtins.open') as mock_open, \
             patch('json.load') as mock_json_load:

            mock_json_load.return_value = {"test": "value"}

            result = await config_manager.load_config("test_config.json")
            assert result == {"test": "value"}
            mock_open.assert_called_once()

    @pytest.mark.asyncio
    async def test_load_config_file_not_found(self, config_manager):
        """Test config loading when file doesn't exist."""
        with patch('builtins.open', side_effect=FileNotFoundError):
            result = await config_manager.load_config("nonexistent.json")
            assert result == {}  # Should return empty dict for missing files

    @pytest.mark.asyncio
    async def test_save_config_success(self, config_manager):
        """Test successful config saving."""
        config_data = {"setting": "value", "number": 42}

        with patch('builtins.open') as mock_open, \
             patch('json.dump') as mock_json_dump:

            result = await config_manager.save_config("test_config.json", config_data)
            assert result is True
            mock_open.assert_called_once()
            mock_json_dump.assert_called_once_with(config_data, mock_open().__enter__())

    def test_get_config_existing_key(self, config_manager):
        """Test getting existing config value."""
        # Set up config data
        config_manager._config = {"database": {"host": "localhost", "port": 5432}}

        result = config_manager.get_config("database.host")
        assert result == "localhost"

    def test_get_config_nested_key(self, config_manager):
        """Test getting nested config value."""
        config_manager._config = {"services": {"api": {"timeout": 30}}}

        result = config_manager.get_config("services.api.timeout")
        assert result == 30

    def test_get_config_missing_key(self, config_manager):
        """Test getting config value for missing key."""
        config_manager._config = {"existing": "value"}

        result = config_manager.get_config("missing.key", "default")
        assert result == "default"

    def test_set_config_simple_key(self, config_manager):
        """Test setting simple config value."""
        result = config_manager.set_config("simple_key", "simple_value")
        assert result is True
        assert config_manager._config["simple_key"] == "simple_value"

    def test_set_config_nested_key(self, config_manager):
        """Test setting nested config value."""
        result = config_manager.set_config("database.host", "remotehost")
        assert result is True
        assert config_manager._config["database"]["host"] == "remotehost"

    def test_set_config_overwrite_existing(self, config_manager):
        """Test overwriting existing config value."""
        # Set initial value
        config_manager.set_config("test.key", "old_value")

        # Overwrite
        result = config_manager.set_config("test.key", "new_value")
        assert result is True
        assert config_manager._config["test"]["key"] == "new_value"

    @pytest.mark.asyncio
    async def test_merge_config(self, config_manager):
        """Test config merging functionality."""
        existing_config = {"database": {"host": "localhost"}}
        new_config = {"database": {"port": 5432}, "cache": {"ttl": 300}}

        result = await config_manager.merge_config(existing_config, new_config)
        expected = {
            "database": {"host": "localhost", "port": 5432},
            "cache": {"ttl": 300}
        }

        assert result == expected

    def test_validate_config_valid(self, config_manager):
        """Test config validation with valid config."""
        valid_config = {
            "database": {"host": "localhost", "port": 5432},
            "services": {"timeout": 30}
        }

        result = config_manager.validate_config(valid_config)
        assert result is True

    def test_validate_config_invalid_structure(self, config_manager):
        """Test config validation with invalid structure."""
        invalid_config = "not_a_dict"

        result = config_manager.validate_config(invalid_config)
        assert result is False

    @pytest.mark.asyncio
    async def test_backup_config(self, config_manager):
        """Test config backup functionality."""
        config_data = {"important": "data"}

        with patch('builtins.open') as mock_open, \
             patch('json.dump') as mock_json_dump:

            result = await config_manager.backup_config("backup_config.json", config_data)
            assert result is True
            mock_open.assert_called_once()

    def test_get_config_summary(self, config_manager):
        """Test config summary generation."""
        config_manager._config = {
            "database": {"host": "localhost", "port": 5432},
            "services": ["api", "worker"],
            "features": {"caching": True, "logging": False}
        }

        summary = config_manager.get_config_summary()
        assert isinstance(summary, dict)
        assert "total_keys" in summary
        assert "nested_levels" in summary

    @pytest.mark.asyncio
    async def test_reload_config(self, config_manager):
        """Test config reloading from file."""
        with patch.object(config_manager, 'load_config') as mock_load:
            mock_load.return_value = {"reloaded": "config"}

            result = await config_manager.reload_config("test_config.json")
            assert result == {"reloaded": "config"}
            mock_load.assert_called_once_with("test_config.json")

    def test_clear_config(self, config_manager):
        """Test config clearing."""
        # Set some config
        config_manager._config = {"test": "data"}

        # Clear it
        result = config_manager.clear_config()
        assert result is True
        assert config_manager._config == {}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
