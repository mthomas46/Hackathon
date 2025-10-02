"""Unit tests for ConfigurationValidator class"""

import pytest
from unittest.mock import Mock, AsyncMock
from pathlib import Path

from monitoring.config_validator import ConfigurationValidator, PortConflict, ConfigInconsistency
from tests.fixtures.docker_compose_fixture import sample_compose_config


class TestConfigurationValidator:
    """Test cases for ConfigurationValidator"""

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
            service_info.environment = service_config.get('environment', [])
            service_info.health_check_url = service_config.get('healthcheck', {}).get('test', None)
            orchestrator.services[service_name] = service_info

        orchestrator.compose_config = sample_compose_config
        return orchestrator

    @pytest.fixture
    def config_validator(self, mock_orchestrator):
        """Configuration validator instance"""
        return ConfigurationValidator(None, mock_orchestrator)

    def test_detect_port_conflicts_no_conflicts(self, config_validator):
        """Test port conflict detection when no conflicts exist"""
        conflicts = config_validator.detect_port_conflicts()
        assert len(conflicts) == 0

    def test_detect_port_conflicts_with_conflicts(self, config_validator, mock_orchestrator):
        """Test port conflict detection with actual conflicts"""
        # Add conflicting services
        mock_orchestrator.services['service1'] = Mock()
        mock_orchestrator.services['service1'].name = 'service1'
        mock_orchestrator.services['service1'].ports = ['8080:3000']

        mock_orchestrator.services['service2'] = Mock()
        mock_orchestrator.services['service2'].name = 'service2'
        mock_orchestrator.services['service2'].ports = ['8080:4000']

        conflicts = config_validator.detect_port_conflicts()

        assert len(conflicts) == 1
        assert conflicts[0].port == '8080'
        assert len(conflicts[0].services) == 2
        assert 'service1' in conflicts[0].services
        assert 'service2' in conflicts[0].services
        assert conflicts[0].severity == 'high'

    def test_detect_port_conflicts_multiple_services_same_port(self, config_validator, mock_orchestrator):
        """Test port conflict detection with multiple services on same port"""
        # Add three services with same port
        for i in range(1, 4):
            service_name = f'service{i}'
            mock_orchestrator.services[service_name] = Mock()
            mock_orchestrator.services[service_name].name = service_name
            mock_orchestrator.services[service_name].ports = ['8080:3000']

        conflicts = config_validator.detect_port_conflicts()

        assert len(conflicts) == 1
        assert conflicts[0].port == '8080'
        assert len(conflicts[0].services) == 3
        assert conflicts[0].severity == 'critical'

    def test_resolve_port_conflicts_no_conflicts(self, config_validator):
        """Test port conflict resolution when no conflicts exist"""
        result = config_validator.resolve_port_conflicts([])

        assert result['status'] == 'no_conflicts'
        assert 'No port conflicts detected' in result['message']

    def test_resolve_port_conflicts_with_conflicts(self, config_validator, mock_orchestrator):
        """Test port conflict resolution with actual conflicts"""
        # Create mock conflicts
        conflicts = [
            PortConflict(port='8080', services=['service1', 'service2'], severity='high')
        ]

        # Mock the used ports method
        config_validator._get_used_ports = Mock(return_value=set(['8080']))

        result = config_validator.resolve_port_conflicts(conflicts)

        assert result['status'] == 'resolved'
        assert result['conflicts_found'] == 1
        assert 'service1' in result['details'] or 'service2' in result['details']

    def test_detect_config_inconsistencies_missing_health_check(self, config_validator, mock_orchestrator):
        """Test detection of missing health checks"""
        # Add a service that should have health check but doesn't
        mock_orchestrator.services['api-service'] = Mock()
        mock_orchestrator.services['api-service'].name = 'api-service'
        mock_orchestrator.services['api-service'].ports = ['8080:3000']
        mock_orchestrator.services['api-service'].environment = []
        mock_orchestrator.services['api-service'].health_check_url = None

        inconsistencies = config_validator.detect_config_inconsistencies()

        # Should detect missing health check
        health_check_issues = [i for i in inconsistencies if i.inconsistency_type == 'missing_health_check']
        assert len(health_check_issues) > 0

        api_service_issue = next((i for i in health_check_issues if i.service_name == 'api-service'), None)
        assert api_service_issue is not None
        assert api_service_issue.severity == 'medium'

    def test_detect_config_inconsistencies_naming_inconsistency(self, config_validator, mock_orchestrator):
        """Test detection of naming convention inconsistencies"""
        # Add service with non-standard naming
        mock_orchestrator.services['TestService'] = Mock()
        mock_orchestrator.services['TestService'].name = 'TestService'
        mock_orchestrator.services['TestService'].ports = ['8080:3000']
        mock_orchestrator.services['TestService'].environment = []
        mock_orchestrator.services['TestService'].health_check_url = None

        inconsistencies = config_validator.detect_config_inconsistencies()

        naming_issues = [i for i in inconsistencies if i.inconsistency_type == 'naming_inconsistency']
        assert len(naming_issues) > 0

        test_service_issue = next((i for i in naming_issues if i.service_name == 'TestService'), None)
        assert test_service_issue is not None
        assert test_service_issue.severity == 'low'

    def test_detect_config_inconsistencies_missing_env_vars(self, config_validator, mock_orchestrator):
        """Test detection of missing environment variables"""
        # Add service missing required environment variables
        mock_orchestrator.services['test-service'] = Mock()
        mock_orchestrator.services['test-service'].name = 'test-service'
        mock_orchestrator.services['test-service'].ports = ['8080:3000']
        mock_orchestrator.services['test-service'].environment = []  # No PYTHONPATH or ENVIRONMENT
        mock_orchestrator.services['test-service'].health_check_url = None

        inconsistencies = config_validator.detect_config_inconsistencies()

        env_var_issues = [i for i in inconsistencies if i.inconsistency_type == 'missing_env_vars']
        assert len(env_var_issues) > 0

        test_service_issue = next((i for i in env_var_issues if i.service_name == 'test-service'), None)
        assert test_service_issue is not None
        assert test_service_issue.severity == 'low'
        assert 'PYTHONPATH' in test_service_issue.description

    def test_resolve_config_inconsistencies_no_inconsistencies(self, config_validator):
        """Test inconsistency resolution when no issues exist"""
        result = config_validator.resolve_config_inconsistencies([])

        assert result['status'] == 'no_inconsistencies'
        assert 'No configuration inconsistencies detected' in result['message']

    def test_resolve_config_inconsistencies_with_issues(self, config_validator, mock_orchestrator):
        """Test inconsistency resolution with actual issues"""
        # Create mock inconsistencies
        inconsistencies = [
            ConfigInconsistency(
                service_name='test-service',
                inconsistency_type='missing_health_check',
                description='Missing health check',
                severity='medium',
                suggested_fix={'add_health_check': {'test': ['CMD', 'curl', '-f', 'http://localhost:8080/health']}}
            )
        ]

        # Mock apply fixes method
        config_validator.apply_configuration_fixes = Mock(return_value={'test-service': {'status': 'applied'}})

        result = config_validator.resolve_config_inconsistencies()

        # Should have called apply fixes
        config_validator.apply_configuration_fixes.assert_called_once()

        assert result['status'] == 'resolved'
        assert result['inconsistencies_found'] == 1
        assert result['fixes_applied'] == 1

    def test_service_needs_health_check(self, config_validator):
        """Test service health check requirement detection"""
        # Services that should need health checks
        assert config_validator._service_needs_health_check('api-service') == True
        assert config_validator._service_needs_health_check('user-store') == True
        assert config_validator._service_needs_health_check('frontend') == True
        assert config_validator._service_needs_health_check('dashboard') == True

        # Services that typically don't need health checks
        assert config_validator._service_needs_health_check('redis') == True  # This one does
        assert config_validator._service_needs_health_check('postgres') == False

    def test_validate_service_naming(self, config_validator):
        """Test service naming validation"""
        # Valid kebab-case names
        assert config_validator._validate_service_naming('user-store') == True
        assert config_validator._validate_service_naming('api-gateway') == True
        assert config_validator._validate_service_naming('my-service') == True

        # Invalid names
        assert config_validator._validate_service_naming('UserStore') == False
        assert config_validator._validate_service_naming('user_store') == False
        assert config_validator._validate_service_naming('userStore') == False
        assert config_validator._validate_service_naming('user-store-api') == True

    def test_check_required_env_vars(self, config_validator):
        """Test required environment variable checking"""
        # Service with all required vars
        service_info = Mock()
        service_info.environment = {'PYTHONPATH': '/app', 'ENVIRONMENT': 'production'}

        missing = config_validator._check_required_env_vars(service_info)
        assert len(missing) == 0

        # Service missing vars
        service_info.environment = {}
        missing = config_validator._check_required_env_vars(service_info)
        assert 'PYTHONPATH' in missing
        assert 'ENVIRONMENT' in missing

        # Service with partial vars
        service_info.environment = {'PYTHONPATH': '/app'}
        missing = config_validator._check_required_env_vars(service_info)
        assert 'ENVIRONMENT' in missing
        assert 'PYTHONPATH' not in missing

    def test_apply_configuration_fixes(self, config_validator):
        """Test configuration fix application"""
        fixes = {
            'service1': {'fix_type': 'port_change', 'new_port': '8081'},
            'service2': {'fix_type': 'add_health_check', 'health_check': {}}
        }

        # Mock the actual application (since we're not actually modifying files in tests)
        result = config_validator.apply_configuration_fixes(fixes)

        assert len(result) == 2
        assert result['service1']['status'] == 'applied'
        assert result['service2']['status'] == 'applied'

    def test_get_used_ports(self, config_validator, mock_orchestrator):
        """Test used ports collection"""
        # Add services with ports
        mock_orchestrator.services['service1'] = Mock()
        mock_orchestrator.services['service1'].ports = ['8080:3000', '8443:443']

        mock_orchestrator.services['service2'] = Mock()
        mock_orchestrator.services['service2'].ports = ['8081:3001']

        used_ports = config_validator._get_used_ports()

        assert '8080' in used_ports
        assert '8443' in used_ports
        assert '8081' in used_ports
        assert '3000' not in used_ports  # Internal ports not included

    def test_find_available_port(self, config_validator):
        """Test available port finding"""
        used_ports = {'8080', '8081', '8082'}

        # Should find next available port
        available = config_validator._find_available_port(8080, used_ports)
        assert available == 8083

        # Test with reserved ports
        available = config_validator._find_available_port(21, used_ports)  # FTP port
        assert available == 8083  # Should skip reserved ports

        # Test max attempts reached
        available = config_validator._find_available_port(8080, used_ports, max_attempts=1)
        assert available is None
