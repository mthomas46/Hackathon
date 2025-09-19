"""
Unit Tests for Environment Detection and Service URL Configuration
Following TDD principles: RED -> GREEN -> REFACTOR

These tests verify that the simulation service correctly detects its runtime environment
and configures service URLs appropriately for Docker vs local development.
"""

import pytest
import os
from unittest.mock import Mock, patch
from simulation.application.analysis.simulation_analyzer import SimulationAnalyzer


class TestEnvironmentDetection:
    """Test environment detection functionality."""

    def test_docker_environment_detection_no_docker(self):
        """Test Docker environment detection when not in Docker."""
        with patch('os.path.exists') as mock_exists, \
             patch('os.getenv') as mock_getenv:

            # Mock no Docker indicators
            mock_exists.return_value = False
            mock_getenv.return_value = None

            analyzer = SimulationAnalyzer()
            assert analyzer._is_docker_environment == False

    def test_docker_environment_detection_with_docker_env_file(self):
        """Test Docker environment detection with Docker env file."""
        with patch('os.path.exists') as mock_exists, \
             patch('os.getenv') as mock_getenv:

            # Mock Docker env file exists
            mock_exists.side_effect = lambda path: path == '/.dockerenv'
            mock_getenv.return_value = None

            analyzer = SimulationAnalyzer()
            assert analyzer._is_docker_environment == True

    def test_docker_environment_detection_with_env_var(self):
        """Test Docker environment detection with environment variable."""
        with patch('os.path.exists') as mock_exists, \
             patch('os.getenv') as mock_getenv:

            mock_exists.return_value = False
            mock_getenv.side_effect = lambda key, default=None: 'true' if key == 'DOCKER_CONTAINER' else None

            analyzer = SimulationAnalyzer()
            assert analyzer._is_docker_environment == True

    def test_docker_environment_detection_with_docker_host(self):
        """Test Docker environment detection with Docker host."""
        with patch('os.path.exists') as mock_exists, \
             patch('os.getenv') as mock_getenv:

            mock_exists.return_value = False
            mock_getenv.side_effect = lambda key, default=None: 'tcp://localhost:2376' if key == 'DOCKER_HOST' else None

            analyzer = SimulationAnalyzer()
            assert analyzer._is_docker_environment == True

    def test_docker_environment_detection_with_hostname(self):
        """Test Docker environment detection with Docker hostname pattern."""
        with patch('os.path.exists') as mock_exists, \
             patch('os.getenv') as mock_getenv:

            mock_exists.return_value = False
            mock_getenv.side_effect = lambda key, default=None: 'docker-container-123' if key == 'HOSTNAME' else None

            analyzer = SimulationAnalyzer()
            assert analyzer._is_docker_environment == True


class TestServiceUrlConfiguration:
    """Test service URL configuration based on environment."""

    @patch('os.getenv')
    def test_docker_service_url_configuration(self, mock_getenv):
        """Test service URL configuration in Docker environment."""
        # Mock Docker environment
        with patch.object(SimulationAnalyzer, '_detect_docker_environment', return_value=True):
            mock_getenv.return_value = None  # No overrides

            analyzer = SimulationAnalyzer()

            expected_urls = {
                "summarizer_hub": "http://summarizer-hub:5160",
                "doc_store": "http://doc-store:5010",
                "analysis_service": "http://analysis-service:5020",
                "code_analyzer": "http://code-analyzer:5025"
            }

            assert analyzer.service_urls == expected_urls

    @patch('os.getenv')
    def test_local_service_url_configuration(self, mock_getenv):
        """Test service URL configuration in local environment."""
        # Mock local environment
        with patch.object(SimulationAnalyzer, '_detect_docker_environment', return_value=False):
            mock_getenv.return_value = None  # No overrides

            analyzer = SimulationAnalyzer()

            expected_urls = {
                "summarizer_hub": "http://localhost:5160",
                "doc_store": "http://localhost:5087",
                "analysis_service": "http://localhost:5080",
                "code_analyzer": "http://localhost:5025"
            }

            assert analyzer.service_urls == expected_urls

    @patch('os.getenv')
    def test_environment_variable_overrides(self, mock_getenv):
        """Test that environment variables override default URLs."""
        # Mock local environment
        with patch.object(SimulationAnalyzer, '_detect_docker_environment', return_value=False):
            # Mock environment variable overrides
            def mock_getenv_side_effect(key):
                overrides = {
                    'SUMMARIZER_HUB_URL': 'http://custom-summarizer:9999',
                    'DOC_STORE_URL': 'http://custom-docstore:8888',
                    # analysis_service and code_analyzer not overridden
                }
                return overrides.get(key)

            mock_getenv.side_effect = mock_getenv_side_effect

            analyzer = SimulationAnalyzer()

            expected_urls = {
                "summarizer_hub": "http://custom-summarizer:9999",  # Overridden
                "doc_store": "http://custom-docstore:8888",        # Overridden
                "analysis_service": "http://localhost:5080",       # Default (not overridden)
                "code_analyzer": "http://localhost:5025"           # Default (not overridden)
            }

            assert analyzer.service_urls == expected_urls

    def test_environment_info_structure(self):
        """Test that environment info returns correct structure."""
        with patch.object(SimulationAnalyzer, '_detect_docker_environment', return_value=True):
            analyzer = SimulationAnalyzer()
            env_info = analyzer.get_environment_info()

            required_keys = [
                'is_docker_environment',
                'environment_type',
                'service_urls',
                'hostname',
                'docker_indicators'
            ]

            for key in required_keys:
                assert key in env_info

            assert env_info['is_docker_environment'] is True
            assert env_info['environment_type'] == 'docker'
            assert isinstance(env_info['service_urls'], dict)
            assert isinstance(env_info['docker_indicators'], dict)


class TestIntegrationWithEcosystem:
    """Integration tests for ecosystem service communication."""

    @pytest.mark.asyncio
    async def test_service_health_check_integration(self):
        """Test health check integration with ecosystem services."""
        # This would test actual connectivity to ecosystem services
        # For now, just verify the health check method exists and can be called
        analyzer = SimulationAnalyzer()

        # Test with a mock service
        result = await analyzer._get_service_health_status("summarizer_hub")
        # Result should be False since the service isn't actually running in tests
        assert isinstance(result, bool)

    def test_service_url_consistency(self):
        """Test that service URLs are consistent across different environment configurations."""
        # Test that both Docker and local configurations have the same service keys
        with patch.object(SimulationAnalyzer, '_detect_docker_environment', return_value=True):
            docker_analyzer = SimulationAnalyzer()

        with patch.object(SimulationAnalyzer, '_detect_docker_environment', return_value=False):
            local_analyzer = SimulationAnalyzer()

        # Both should have the same service keys
        assert set(docker_analyzer.service_urls.keys()) == set(local_analyzer.service_urls.keys())

        # Verify all expected services are configured
        expected_services = {"summarizer_hub", "doc_store", "analysis_service", "code_analyzer"}
        assert set(docker_analyzer.service_urls.keys()) == expected_services

    def test_environment_detection_is_deterministic(self):
        """Test that environment detection is deterministic for the same conditions."""
        # Test that multiple calls to environment detection return the same result
        with patch.object(SimulationAnalyzer, '_detect_docker_environment', return_value=True):
            analyzer1 = SimulationAnalyzer()
            analyzer2 = SimulationAnalyzer()

            assert analyzer1._is_docker_environment == analyzer2._is_docker_environment

        with patch.object(SimulationAnalyzer, '_detect_docker_environment', return_value=False):
            analyzer3 = SimulationAnalyzer()
            analyzer4 = SimulationAnalyzer()

            assert analyzer3._is_docker_environment == analyzer4._is_docker_environment
