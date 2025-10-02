"""Unit tests for ServiceConfigManager class"""

import pytest
import json
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
import aiohttp

from monitoring.config_manager import ServiceConfigManager, ServiceConfigReport
from tests.fixtures.docker_compose_fixture import sample_compose_config


class TestServiceConfigManager:
    """Test cases for ServiceConfigManager"""

    @pytest.fixture
    def mock_db_manager(self):
        """Mock database manager"""
        manager = Mock()
        manager.save_configuration_snapshot = Mock(return_value=1)
        manager.get_configuration_snapshots = Mock(return_value=[])
        manager.get_latest_snapshot = Mock(return_value=None)
        return manager

    @pytest.fixture
    def mock_orchestrator(self, sample_compose_config):
        """Mock orchestrator with sample services"""
        orchestrator = Mock()
        orchestrator.services = {}

        # Create mock services from sample config
        for service_name, service_config in sample_compose_config['services'].items():
            service_info = Mock()
            service_info.name = service_name
            service_info.ports = service_config.get('ports', [])
            orchestrator.services[service_name] = service_info

        return orchestrator

    @pytest.fixture
    def config_manager(self, mock_db_manager, mock_orchestrator):
        """Service config manager instance"""
        manager = ServiceConfigManager(mock_db_manager, mock_orchestrator)
        # Note: initialize/cleanup would be called in async tests
        return manager

    def test_initialization(self, config_manager):
        """Test config manager initialization"""
        assert config_manager.db_manager is not None
        assert config_manager.orchestrator is not None
        assert config_manager.session is not None

    @pytest.mark.asyncio
    async def test_query_service_config_success(self, config_manager, mock_orchestrator):
        """Test successful service config querying"""
        # Mock service with config endpoint
        service_info = Mock()
        service_info.ports = ['8080:3000']
        mock_orchestrator.services['test-service'] = service_info

        # Mock HTTP response
        mock_response_data = {
            'config': {
                'service_name': 'test-service',
                'version': '1.0.0',
                'port': 3000
            },
            'sources': {
                'docker': {'SERVICE_NAME': 'test-service'},
                'yaml': {'version': '1.0.0'}
            },
            'version': '1.0.0',
            'timestamp': 1234567890
        }

        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_get.return_value.__aenter__.return_value = mock_response

            result = await config_manager.query_service_config('test-service')

            assert result is not None
            assert result.service_name == 'test-service'
            assert result.version == '1.0.0'
            assert result.config_data['service_name'] == 'test-service'
            assert 'docker' in result.config_sources

    @pytest.mark.asyncio
    async def test_query_service_config_no_endpoint(self, config_manager, mock_orchestrator):
        """Test service config query when no endpoint available"""
        # Service without ports
        service_info = Mock()
        service_info.ports = []
        mock_orchestrator.services['test-service'] = service_info

        result = await config_manager.query_service_config('test-service')

        assert result is None

    @pytest.mark.asyncio
    async def test_query_service_config_http_error(self, config_manager, mock_orchestrator):
        """Test service config query with HTTP error"""
        service_info = Mock()
        service_info.ports = ['8080:3000']
        mock_orchestrator.services['test-service'] = service_info

        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 404
            mock_get.return_value.__aenter__.return_value = mock_response

            result = await config_manager.query_service_config('test-service')

            assert result is None

    @pytest.mark.asyncio
    async def test_query_service_config_connection_error(self, config_manager, mock_orchestrator):
        """Test service config query with connection error"""
        service_info = Mock()
        service_info.ports = ['8080:3000']
        mock_orchestrator.services['test-service'] = service_info

        with patch('aiohttp.ClientSession.get', side_effect=aiohttp.ClientError("Connection failed")):
            result = await config_manager.query_service_config('test-service')

            assert result is None

    @pytest.mark.asyncio
    async def test_query_all_service_configs(self, config_manager, mock_orchestrator):
        """Test querying all service configurations"""
        # Add services with endpoints
        for i in range(3):
            service_name = f'service-{i}'
            service_info = Mock()
            service_info.ports = ['8080:3000']
            mock_orchestrator.services[service_name] = service_info

        # Mock successful responses
        mock_response_data = {
            'config': {'service_name': 'test', 'version': '1.0.0'},
            'sources': {'docker': {}},
            'version': '1.0.0',
            'timestamp': 1234567890
        }

        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_get.return_value.__aenter__.return_value = mock_response

            results = await config_manager.query_all_service_configs()

            assert len(results) == 3
            for service_name in ['service-0', 'service-1', 'service-2']:
                assert service_name in results
                assert isinstance(results[service_name], ServiceConfigReport)

    def test_save_service_config(self, config_manager, mock_db_manager):
        """Test saving service configuration"""
        config_report = ServiceConfigReport(
            service_name='test-service',
            config_data={'version': '1.0.0', 'port': 8080},
            config_sources={'docker': {'SERVICE_NAME': 'test-service'}},
            timestamp=datetime.utcnow(),
            version='1.0.0'
        )

        result = config_manager.save_service_config(config_report)

        assert result == 1
        mock_db_manager.save_configuration_snapshot.assert_called_once()

        # Check the call arguments
        call_args = mock_db_manager.save_configuration_snapshot.call_args[0][0]
        assert call_args.service_name == 'test-service'
        assert call_args.source == 'service_endpoint'
        assert 'config' in call_args.config_data
        assert 'sources' in call_args.config_data

    def test_get_service_config_history(self, config_manager, mock_db_manager):
        """Test getting service configuration history"""
        mock_snapshots = [
            Mock(service_name='test-service', config_hash='hash1', timestamp=datetime.utcnow()),
            Mock(service_name='test-service', config_hash='hash2', timestamp=datetime.utcnow())
        ]
        mock_db_manager.get_configuration_snapshots.return_value = mock_snapshots

        result = config_manager.get_service_config_history('test-service', limit=5)

        assert len(result) == 2
        mock_db_manager.get_configuration_snapshots.assert_called_once_with('test-service', 5)

    def test_get_latest_service_config(self, config_manager, mock_db_manager):
        """Test getting latest service configuration"""
        mock_snapshot = Mock(service_name='test-service', config_hash='hash1')
        mock_db_manager.get_latest_snapshot.return_value = mock_snapshot

        result = config_manager.get_latest_service_config('test-service')

        assert result == mock_snapshot
        mock_db_manager.get_latest_snapshot.assert_called_once_with('test-service')

    def test_get_latest_service_config_none(self, config_manager, mock_db_manager):
        """Test getting latest service config when none exists"""
        mock_db_manager.get_latest_snapshot.return_value = None

        result = config_manager.get_latest_service_config('test-service')

        assert result is None

    def test_export_service_config_json(self, config_manager, mock_db_manager):
        """Test exporting service configuration as JSON"""
        mock_snapshot = Mock()
        mock_snapshot.config_data = {
            'config': {'version': '1.0.0', 'port': 8080},
            'sources': {'docker': {'SERVICE_NAME': 'test'}}
        }
        mock_db_manager.get_latest_snapshot.return_value = mock_snapshot

        result = config_manager.export_service_config('test-service', 'json')

        assert result is not None
        parsed = json.loads(result)
        assert parsed['config']['version'] == '1.0.0'
        assert parsed['config']['port'] == 8080

    def test_export_service_config_yaml(self, config_manager, mock_db_manager):
        """Test exporting service configuration as YAML"""
        mock_snapshot = Mock()
        mock_snapshot.config_data = {
            'config': {'version': '1.0.0', 'port': 8080},
            'sources': {'docker': {'SERVICE_NAME': 'test'}}
        }
        mock_db_manager.get_latest_snapshot.return_value = mock_snapshot

        result = config_manager.export_service_config('test-service', 'yaml')

        # Should fall back to JSON if yaml not available
        assert result is not None
        assert isinstance(result, str)

    def test_export_service_config_no_config(self, config_manager, mock_db_manager):
        """Test exporting when no configuration exists"""
        mock_db_manager.get_latest_snapshot.return_value = None

        result = config_manager.export_service_config('test-service', 'json')

        assert result is None

    def test_export_service_config_invalid_format(self, config_manager, mock_db_manager):
        """Test exporting with invalid format"""
        mock_snapshot = Mock()
        mock_snapshot.config_data = {'config': {'version': '1.0.0'}}
        mock_db_manager.get_latest_snapshot.return_value = mock_snapshot

        result = config_manager.export_service_config('test-service', 'xml')

        assert result is None

    @patch('builtins.open')
    @patch('os.makedirs')
    def test_export_all_configs(self, mock_makedirs, mock_open, config_manager, mock_db_manager):
        """Test exporting all service configurations"""
        # Mock file operations
        mock_file = Mock()
        mock_open.return_value.__enter__.return_value = mock_file

        # Mock services
        mock_services = ['service1', 'service2']
        config_manager.orchestrator.services = {name: Mock() for name in mock_services}

        # Mock config data
        mock_snapshot = Mock()
        mock_snapshot.config_data = {'config': {'version': '1.0.0'}}
        mock_db_manager.get_latest_snapshot.return_value = mock_snapshot

        result = config_manager.export_all_configs('json', '/tmp/configs')

        assert len(result) == 2
        assert 'service1' in result
        assert 'service2' in result
        mock_open.assert_called()

    @pytest.mark.asyncio
    async def test_sync_all_service_configs(self, config_manager, mock_db_manager, mock_orchestrator):
        """Test syncing all service configurations"""
        # Add a service
        service_info = Mock()
        service_info.ports = ['8080:3000']
        mock_orchestrator.services['test-service'] = service_info

        # Mock successful config query
        mock_response_data = {
            'config': {'service_name': 'test-service', 'version': '1.0.0'},
            'sources': {'docker': {}},
            'version': '1.0.0',
            'timestamp': 1234567890
        }

        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_get.return_value.__aenter__.return_value = mock_response

            result = await config_manager.sync_all_service_configs()

            assert result['total_services'] == 1
            assert result['successful_syncs'] == 1
            assert result['failed_syncs'] == 0
            assert 'test-service' in result['service_results']

    def test_compare_service_configs_with_history(self, config_manager, mock_db_manager):
        """Test configuration comparison with history"""
        # Mock snapshots with different versions
        old_snapshot = Mock()
        old_snapshot.config_data = {
            'config': {'version': '1.0.0', 'port': 8080},
            'sources': {'docker': {'PORT': '8080'}}
        }

        new_snapshot = Mock()
        new_snapshot.config_data = {
            'config': {'version': '1.1.0', 'port': 8081},
            'sources': {'docker': {'PORT': '8081'}}
        }

        mock_db_manager.get_configuration_snapshots.return_value = [new_snapshot, old_snapshot]

        result = config_manager.compare_service_configs('test-service')

        assert result['status'] == 'compared'
        assert result['changes_detected'] == True
        assert result['change_count'] > 0
        assert result['current_version'] == '1.1.0'
        assert result['previous_version'] == '1.0.0'

    def test_compare_service_configs_insufficient_history(self, config_manager, mock_db_manager):
        """Test configuration comparison with insufficient history"""
        # Only one snapshot
        snapshot = Mock()
        snapshot.config_data = {'config': {'version': '1.0.0'}}
        mock_db_manager.get_configuration_snapshots.return_value = [snapshot]

        result = config_manager.compare_service_configs('test-service')

        assert result['status'] == 'insufficient_history'

    def test_compare_service_configs_no_stored_config(self, config_manager, mock_db_manager):
        """Test configuration comparison when no config stored"""
        mock_db_manager.get_configuration_snapshots.return_value = []

        result = config_manager.compare_service_configs('test-service')

        assert result['status'] == 'no_stored_config'

    def test_get_config_endpoint_with_ports(self, config_manager, mock_orchestrator):
        """Test config endpoint construction with ports"""
        service_info = Mock()
        service_info.ports = ['8080:3000']
        mock_orchestrator.services['test-service'] = service_info

        endpoint = config_manager._get_config_endpoint(service_info)

        assert endpoint == 'http://localhost:8080/config'

    def test_get_config_endpoint_no_ports(self, config_manager, mock_orchestrator):
        """Test config endpoint construction without ports"""
        service_info = Mock()
        service_info.ports = []

        endpoint = config_manager._get_config_endpoint(service_info)

        assert endpoint is None

    def test_compare_configs_detect_changes(self, config_manager):
        """Test config comparison logic"""
        old_config = {
            'config': {'version': '1.0.0', 'port': 8080},
            'sources': {'docker': {'PORT': '8080'}}
        }
        new_config = {
            'config': {'version': '1.1.0', 'port': 8081},
            'sources': {'docker': {'PORT': '8081'}}
        }

        changes = config_manager._compare_configs(old_config, new_config)

        assert len(changes) > 0
        # Should detect version and port changes
        assert any(c['change_type'] == 'modified' for c in changes)

    def test_compare_configs_no_changes(self, config_manager):
        """Test config comparison with identical configs"""
        config = {
            'config': {'version': '1.0.0', 'port': 8080},
            'sources': {'docker': {'PORT': '8080'}}
        }

        changes = config_manager._compare_configs(config, config)

        assert len(changes) == 0
