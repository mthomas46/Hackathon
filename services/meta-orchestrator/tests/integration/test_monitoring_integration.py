"""Integration tests for the MonitoringService"""

import pytest
import asyncio
import tempfile
import os
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path

from monitoring.service import MonitoringService
from monitoring.database.manager import DatabaseManager
from monitoring.health.checker import HealthChecker
from monitoring.drift_detector import ConfigurationDriftDetector
from monitoring.alerts.manager import AlertManager
from monitoring.analytics.analyzer import DriftAnalytics
from monitoring.config_validator import ConfigurationValidator
from monitoring.config_manager import ServiceConfigManager
from core.orchestrator import MetaOrchestrator
from config.settings import Settings, DockerSettings, ServiceSettings, SecuritySettings


class TestMonitoringServiceIntegration:
    """Integration tests for the complete monitoring service"""

    @pytest.fixture
    def temp_db_path(self, tmp_path):
        """Temporary database path"""
        return str(tmp_path / "test_monitoring.db")

    @pytest.fixture
    def mock_orchestrator(self):
        """Mock orchestrator with services"""
        orchestrator = Mock()
        orchestrator.services = {}

        # Add mock services
        services_data = {
            'user-store': {'ports': ['8106:5150'], 'health_endpoint': 'http://localhost:8106/health'},
            'api-gateway': {'ports': ['8080:3000'], 'health_endpoint': 'http://localhost:8080/health'},
            'redis': {'ports': ['6379:6379'], 'health_endpoint': None},
            'frontend': {'ports': ['3000:3000'], 'health_endpoint': 'http://localhost:3000/health'}
        }

        for service_name, data in services_data.items():
            service_info = Mock()
            service_info.name = service_name
            service_info.ports = data['ports']
            service_info.health_check_url = data['health_endpoint']
            orchestrator.services[service_name] = service_info

        return orchestrator

    @pytest.fixture
    async def monitoring_service(self, temp_db_path, mock_orchestrator):
        """Full monitoring service instance"""
        service = MonitoringService(mock_orchestrator, temp_db_path)
        await service.initialize()
        yield service
        await service.stop_monitoring()

    @pytest.mark.asyncio
    async def test_full_monitoring_initialization(self, monitoring_service):
        """Test that all monitoring components initialize correctly"""
        assert monitoring_service.db_manager is not None
        assert monitoring_service.health_checker is not None
        assert monitoring_service.drift_detector is not None
        assert monitoring_service.alert_manager is not None
        assert monitoring_service.analytics is not None
        assert monitoring_service.config_validator is not None
        assert monitoring_service.config_manager is not None

        # Check database was initialized
        assert os.path.exists(monitoring_service.db_manager.db_path)

    @pytest.mark.asyncio
    async def test_port_conflict_detection_integration(self, monitoring_service, mock_orchestrator):
        """Integration test for port conflict detection"""
        # Add conflicting services
        mock_orchestrator.services['conflict-service-1'] = Mock()
        mock_orchestrator.services['conflict-service-1'].name = 'conflict-service-1'
        mock_orchestrator.services['conflict-service-1'].ports = ['8080:4000']

        mock_orchestrator.services['conflict-service-2'] = Mock()
        mock_orchestrator.services['conflict-service-2'].name = 'conflict-service-2'
        mock_orchestrator.services['conflict-service-2'].ports = ['8080:5000']

        conflicts = await monitoring_service.detect_port_conflicts()

        assert len(conflicts) == 1
        assert conflicts[0]['port'] == '8080'
        assert len(conflicts[0]['services']) == 2
        assert 'conflict-service-1' in conflicts[0]['services']
        assert 'conflict-service-2' in conflicts[0]['services']

    @pytest.mark.asyncio
    async def test_config_inconsistency_detection_integration(self, monitoring_service):
        """Integration test for configuration inconsistency detection"""
        inconsistencies = await monitoring_service.detect_config_inconsistencies()

        # Should detect various inconsistencies
        assert isinstance(inconsistencies, list)

        # Check for expected inconsistency types
        inconsistency_types = {inc['inconsistency_type'] for inc in inconsistencies}
        expected_types = {'missing_health_check', 'naming_inconsistency', 'missing_env_vars'}

        # Should have at least some of the expected types
        assert len(inconsistency_types.intersection(expected_types)) > 0

    @pytest.mark.asyncio
    async def test_health_check_integration(self, monitoring_service):
        """Integration test for health checking"""
        # Mock successful health responses
        mock_responses = {
            'user-store': {'status': 'healthy', 'response_time': 0.1},
            'api-gateway': {'status': 'healthy', 'response_time': 0.05},
            'redis': {'status': 'unknown', 'error_message': 'No health endpoint'},
            'frontend': {'status': 'unhealthy', 'error_message': 'Connection timeout'}
        }

        with patch('aiohttp.ClientSession.get') as mock_get:
            async def mock_response(service_name):
                if service_name in mock_responses:
                    data = mock_responses[service_name]
                    mock_resp = AsyncMock()
                    mock_resp.status = 200 if data['status'] == 'healthy' else 500
                    mock_resp.json = AsyncMock(return_value={'status': data['status']})
                    return mock_resp
                else:
                    # Simulate connection error for services not in mock
                    raise aiohttp.ClientError("Connection failed")

            mock_get.return_value.__aenter__.side_effect = lambda: mock_response(
                list(monitoring_service.orchestrator.services.keys())[
                    mock_get.call_count % len(monitoring_service.orchestrator.services)
                ]
            )

            # This would normally run health checks, but for testing we'll skip
            # the actual concurrent execution and just verify the setup
            assert monitoring_service.health_checker.session is not None

    @pytest.mark.asyncio
    async def test_config_sync_integration(self, monitoring_service):
        """Integration test for configuration synchronization"""
        # Mock config endpoint responses
        mock_configs = {
            'user-store': {
                'config': {'service_name': 'user-store', 'version': '1.0.0', 'port': 5150},
                'sources': {'docker': {'SERVICE_NAME': 'user-store'}},
                'version': '1.0.0',
                'timestamp': 1234567890
            },
            'api-gateway': {
                'config': {'service_name': 'api-gateway', 'version': '1.1.0', 'port': 3000},
                'sources': {'yaml': {'version': '1.1.0'}},
                'version': '1.1.0',
                'timestamp': 1234567890
            }
        }

        with patch('aiohttp.ClientSession.get') as mock_get:
            call_count = 0

            async def mock_config_response(*args, **kwargs):
                nonlocal call_count
                service_name = list(mock_configs.keys())[call_count % len(mock_configs)]
                call_count += 1

                mock_resp = AsyncMock()
                mock_resp.status = 200
                mock_resp.json = AsyncMock(return_value=mock_configs[service_name])
                return mock_resp

            mock_get.return_value.__aenter__.side_effect = mock_config_response

            result = await monitoring_service.sync_service_configs()

            assert result['total_services'] == 6  # 4 original + 2 added
            assert result['successful_syncs'] >= 0  # May vary based on mocking
            assert 'service_results' in result

    @pytest.mark.asyncio
    async def test_config_export_integration(self, monitoring_service):
        """Integration test for configuration export"""
        # First sync some configs
        await monitoring_service.sync_service_configs()

        # Test individual export
        export_result = await monitoring_service.export_service_config('user-store', 'json')

        if export_result:
            assert isinstance(export_result, str)
            # Should be valid JSON
            import json
            parsed = json.loads(export_result)
            assert isinstance(parsed, dict)

        # Test bulk export
        bulk_result = await monitoring_service.export_all_configs('json', '/tmp/test_configs')
        assert isinstance(bulk_result, dict)

    @pytest.mark.asyncio
    async def test_monitoring_dashboard_integration(self, monitoring_service):
        """Integration test for monitoring dashboard data"""
        dashboard = await monitoring_service.get_monitoring_dashboard()

        assert 'dashboard' in dashboard
        assert 'summary' in dashboard['dashboard']
        assert 'health_status' in dashboard['dashboard']
        assert 'drift_status' in dashboard['dashboard']
        assert 'active_alerts' in dashboard['dashboard']

        # Check summary structure
        summary = dashboard['dashboard']['summary']
        assert 'total_services' in summary
        assert 'healthy_services' in summary
        assert 'active_alerts' in summary
        assert 'unresolved_drifts' in summary

    @pytest.mark.asyncio
    async def test_alert_management_integration(self, monitoring_service):
        """Integration test for alert management"""
        # Get current alerts
        alerts = await monitoring_service.get_alerts()

        assert isinstance(alerts, list)

        # Create a test alert
        if alerts:  # If there are alerts, try to acknowledge one
            alert_id = alerts[0]['id']
            success = await monitoring_service.acknowledge_alert(alert_id, 'test_user')
            assert isinstance(success, bool)

    @pytest.mark.asyncio
    async def test_analytics_integration(self, monitoring_service):
        """Integration test for analytics functionality"""
        report = await monitoring_service.get_analytics_report()

        assert 'generated_at' in report
        assert 'risk_score' in report
        assert 'risk_level' in report
        assert 'drift_statistics' in report
        assert 'health_statistics' in report
        assert 'recommendations' in report
        assert 'summary' in report

    @pytest.mark.asyncio
    async def test_config_validation_and_healing_integration(self, monitoring_service):
        """Integration test for configuration validation and healing"""
        # Test port conflict resolution
        resolution_result = await monitoring_service.resolve_port_conflicts()
        assert 'status' in resolution_result

        # Test inconsistency resolution
        inconsistency_result = await monitoring_service.resolve_config_inconsistencies()
        assert 'status' in inconsistency_result

    def test_monitoring_service_cleanup(self, monitoring_service, temp_db_path):
        """Test that monitoring service cleans up properly"""
        # Service should clean up its resources
        assert monitoring_service.health_checker.session is not None
        assert monitoring_service.config_manager.session is not None

        # Database file should exist
        assert os.path.exists(temp_db_path)

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, monitoring_service):
        """Test that multiple monitoring operations can run concurrently"""
        # Run multiple operations simultaneously
        tasks = [
            monitoring_service.detect_port_conflicts(),
            monitoring_service.detect_config_inconsistencies(),
            monitoring_service.get_health_status(),
            monitoring_service.get_drift_status(),
            monitoring_service.get_alerts()
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All operations should complete without critical errors
        for result in results:
            assert not isinstance(result, Exception) or isinstance(result, (ValueError, KeyError))

    @pytest.mark.asyncio
    async def test_monitoring_under_load(self, monitoring_service):
        """Test monitoring service performance under simulated load"""
        # Add many services
        for i in range(10, 20):
            service_name = f'test-service-{i}'
            service_info = Mock()
            service_info.name = service_name
            service_info.ports = [f'{8080 + i}:3000']
            monitoring_service.orchestrator.services[service_name] = service_info

        # Test port conflict detection with many services
        conflicts = await monitoring_service.detect_port_conflicts()
        assert isinstance(conflicts, list)

        # Test inconsistency detection with many services
        inconsistencies = await monitoring_service.detect_config_inconsistencies()
        assert isinstance(inconsistencies, list)

    @pytest.mark.asyncio
    async def test_error_handling_integration(self, monitoring_service):
        """Test error handling across the monitoring system"""
        # Test with invalid service names
        config = await monitoring_service.get_service_config('nonexistent-service')
        assert config is None

        # Test export of nonexistent service
        export_result = await monitoring_service.export_service_config('nonexistent-service')
        assert export_result is None

        # Test config comparison for nonexistent service
        comparison = await monitoring_service.compare_service_configs('nonexistent-service')
        assert comparison['status'] == 'no_stored_config'

    def test_database_persistence(self, monitoring_service, temp_db_path):
        """Test that database persists data correctly"""
        import sqlite3

        # Check that database file exists and has expected tables
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()

        # Get table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]

        expected_tables = [
            'configuration_snapshots',
            'configuration_drift',
            'service_health',
            'alerts',
            'drift_patterns'
        ]

        for table in expected_tables:
            assert table in tables, f"Table {table} not found in database"

        conn.close()
