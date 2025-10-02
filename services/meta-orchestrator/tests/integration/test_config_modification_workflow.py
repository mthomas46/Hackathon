"""End-to-end workflow tests for configuration modification"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient

from main import app


class TestConfigModificationWorkflow:
    """End-to-end tests for configuration modification workflows"""

    @pytest.fixture
    def client(self):
        """Test client for the FastAPI app"""
        return TestClient(app)

    @pytest.fixture
    def mock_orchestrator(self):
        """Mock orchestrator with comprehensive service setup"""
        orchestrator = Mock()
        orchestrator.services = {}

        # Create comprehensive service mocks
        services = {
            'web-frontend': {
                'image': 'nginx:alpine',
                'ports': ['80:80', '443:443'],
                'environment': {'NGINX_PORT': '80'},
                'volumes': ['/etc/nginx/conf.d'],
                'restart_policy': 'unless-stopped',
                'networks': ['web', 'default']
            },
            'api-backend': {
                'image': 'node:18-alpine',
                'ports': ['3000:3000'],
                'environment': {'NODE_ENV': 'production', 'PORT': '3000'},
                'volumes': ['./app:/app', '/app/node_modules'],
                'depends_on': [],
                'restart_policy': 'on-failure',
                'networks': ['api', 'default']
            },
            'database': {
                'image': 'postgres:13',
                'ports': ['5432:5432'],
                'environment': {
                    'POSTGRES_DB': 'app',
                    'POSTGRES_USER': 'appuser',
                    'POSTGRES_PASSWORD': 'securepass'
                },
                'volumes': ['postgres_data:/var/lib/postgresql/data'],
                'restart_policy': 'always',
                'networks': ['database', 'default']
            }
        }

        for service_name, config in services.items():
            service_info = Mock()
            service_info.name = service_name
            service_info.image = config['image']
            service_info.ports = config['ports']
            service_info.environment = config['environment']
            service_info.volumes = config['volumes']
            service_info.depends_on = config['depends_on']
            service_info.restart_policy = config['restart_policy']
            service_info.networks = config['networks']
            service_info.health_check_url = f"http://localhost:{config['ports'][0].split(':')[0]}/health"

            orchestrator.services[service_name] = service_info

        # Mock restart functionality
        orchestrator.restart_service = AsyncMock()

        return orchestrator

    def test_complete_single_service_modification_workflow(self, client, mock_orchestrator):
        """Test complete workflow for single service configuration modification"""
        # Step 1: Get current configuration
        with patch('api.routes.meta_orchestrator', mock_orchestrator):
            response = client.get("/api/v1/services/web-frontend/config/current")
            assert response.status_code == 200
            current_config = response.json()["current_config"]

            # Verify current state
            assert current_config["image"] == "nginx:alpine"
            assert "80:80" in current_config["ports"]
            assert current_config["restart"] == "unless-stopped"

        # Step 2: Validate configuration changes
        new_config = {
            "environment": {"NGINX_WORKER_PROCESSES": "2", "NGINX_PORT": "8080"},
            "ports": ["8080:80", "8443:443"],  # Change external ports
            "restart": "always",
            "volumes": ["/etc/nginx/conf.d", "/var/log/nginx:/var/log/nginx"]
        }

        with patch('api.routes.meta_orchestrator', mock_orchestrator):
            validation_request = {"services": {"web-frontend": new_config}}
            response = client.post("/api/v1/services/config/validate", json=validation_request)
            assert response.status_code == 200

            validation_result = response.json()["validation_result"]
            assert validation_result["overall_valid"] == True
            assert validation_result["services_valid"] == 1

        # Step 3: Apply configuration changes
        with patch('api.routes.meta_orchestrator', mock_orchestrator):
            response = client.put("/api/v1/services/web-frontend/config", json=new_config)
            assert response.status_code == 200

            modification_result = response.json()["config_modification"]
            assert modification_result["success"] == True
            assert modification_result["service_name"] == "web-frontend"
            assert "environment" in modification_result["changes_applied"]
            assert "ports" in modification_result["changes_applied"]
            assert "restart" in modification_result["changes_applied"]

            # Verify restart was called
            mock_orchestrator.restart_service.assert_called_once_with("web-frontend")

        # Step 4: Verify configuration was updated
        with patch('api.routes.meta_orchestrator', mock_orchestrator):
            response = client.get("/api/v1/services/web-frontend/config/current")
            assert response.status_code == 200
            updated_config = response.json()["current_config"]

            # Check that configuration was applied
            assert updated_config["restart"] == "always"
            assert "8080:80" in updated_config["ports"]

    def test_batch_configuration_modification_workflow(self, client, mock_orchestrator):
        """Test complete workflow for batch configuration modification"""
        # Step 1: Validate batch configuration
        batch_config = {
            "services": {
                "web-frontend": {
                    "environment": {"NGINX_WORKER_PROCESSES": "4"},
                    "restart": "on-failure"
                },
                "api-backend": {
                    "environment": {"NODE_ENV": "development", "DEBUG": "true"},
                    "ports": ["3001:3000"],  # Change port
                    "volumes": ["./app:/app", "/app/node_modules", "/tmp:/tmp"]
                },
                "database": {
                    "environment": {
                        "POSTGRES_DB": "app_dev",
                        "POSTGRES_USER": "devuser",
                        "POSTGRES_PASSWORD": "devpass"
                    },
                    "restart": "unless-stopped"
                }
            },
            "rollback_on_failure": True
        }

        with patch('api.routes.meta_orchestrator', mock_orchestrator):
            response = client.post("/api/v1/services/config/validate", json=batch_config)
            assert response.status_code == 200

            validation_result = response.json()["validation_result"]
            assert validation_result["overall_valid"] == True
            assert validation_result["services_validated"] == 3

        # Step 2: Apply batch configuration
        with patch('api.routes.meta_orchestrator', mock_orchestrator):
            response = client.put("/api/v1/services/config/batch", json=batch_config)
            assert response.status_code == 200

            batch_result = response.json()["batch_config_modification"]
            assert batch_result["total_services"] == 3
            assert batch_result["successful_modifications"] == 3

            # Verify all services were processed
            assert "web-frontend" in batch_result["results"]
            assert "api-backend" in batch_result["results"]
            assert "database" in batch_result["results"]

            # Verify all services were restarted
            assert mock_orchestrator.restart_service.call_count == 3

    def test_configuration_rollback_workflow(self, client, mock_orchestrator):
        """Test configuration rollback workflow"""
        # First, apply a configuration change
        original_config = {
            "environment": {"ORIGINAL_VAR": "original_value"},
            "restart": "unless-stopped"
        }

        new_config = {
            "environment": {"ORIGINAL_VAR": "modified_value", "NEW_VAR": "new_value"},
            "restart": "always"
        }

        with patch('api.routes.meta_orchestrator', mock_orchestrator):
            # Apply the change
            response = client.put("/api/v1/services/web-frontend/config", json=new_config)
            assert response.status_code == 200

            modification_result = response.json()["config_modification"]

            # Now rollback using the original config from the result
            rollback_data = {
                "original_config": modification_result["original_config"],
                "restart_after_rollback": True
            }

            response = client.post("/api/v1/services/web-frontend/config/rollback", json=rollback_data)
            assert response.status_code == 200

            rollback_result = response.json()["config_rollback"]
            assert rollback_result["success"] == True

            # Verify rollback restart was called
            assert mock_orchestrator.restart_service.call_count == 2  # One for change, one for rollback

    def test_configuration_validation_error_workflow(self, client, mock_orchestrator):
        """Test workflow when configuration validation fails"""
        # Try to apply invalid configuration
        invalid_config = {
            "ports": ["invalid_port_spec"],
            "environment": "not_a_valid_format",
            "restart": "invalid_restart_policy",
            "image": "nginx:latest",
            "build": "."  # Cannot have both image and build
        }

        with patch('api.routes.meta_orchestrator', mock_orchestrator):
            response = client.put("/api/v1/services/web-frontend/config", json=invalid_config)
            assert response.status_code == 400

            error_data = response.json()
            assert "validation_errors" in error_data
            assert "message" in error_data

            # Verify that no changes were applied (restart should not be called)
            mock_orchestrator.restart_service.assert_not_called()

    def test_batch_partial_failure_workflow(self, client, mock_orchestrator):
        """Test batch configuration with partial failures"""
        # Create a batch with one valid and one invalid configuration
        batch_config = {
            "services": {
                "web-frontend": {
                    "environment": {"VALID_VAR": "valid_value"},
                    "restart": "on-failure"
                },
                "api-backend": {
                    "ports": ["invalid_port_format"],
                    "environment": {"INVALID_ENV": "value"}
                }
            },
            "rollback_on_failure": False
        }

        with patch('api.routes.meta_orchestrator', mock_orchestrator):
            # This should fail validation
            response = client.put("/api/v1/services/config/batch", json=batch_config)
            assert response.status_code == 400

            # Verify no services were restarted due to validation failure
            mock_orchestrator.restart_service.assert_not_called()

    def test_configuration_warnings_workflow(self, client, mock_orchestrator):
        """Test configuration changes that generate warnings"""
        # Configuration that should generate warnings
        config_with_warnings = {
            "environment": {"DANGEROUS_VAR": "dangerous_value"},
            "restart": "always",  # This should generate a warning
            "depends_on": ["database"],  # Dependency changes should warn
            "networks": ["web", "api"]  # Network changes should warn
        }

        with patch('api.routes.meta_orchestrator', mock_orchestrator):
            # Validate - should pass but with warnings
            validation_request = {"services": {"web-frontend": config_with_warnings}}
            response = client.post("/api/v1/services/config/validate", json=validation_request)
            assert response.status_code == 200

            validation_result = response.json()["validation_result"]
            assert validation_result["overall_valid"] == True

            # Check that warnings were generated
            service_result = validation_result["service_results"]["web-frontend"]
            assert len(service_result["warnings"]) > 0
            assert "Restart policy 'always' may cause excessive container restarts" in service_result["warnings"]

    def test_service_dependency_modification_workflow(self, client, mock_orchestrator):
        """Test modifying service dependencies"""
        # Modify API backend to depend on database
        dependency_config = {
            "depends_on": ["database"],
            "environment": {"DB_DEPENDENCY": "true"}
        }

        with patch('api.routes.meta_orchestrator', mock_orchestrator):
            response = client.put("/api/v1/services/api-backend/config", json=dependency_config)
            assert response.status_code == 200

            modification_result = response.json()["config_modification"]
            assert modification_result["success"] == True
            assert "depends_on" in modification_result["changes_applied"]

            # Verify the dependency was set
            service_info = mock_orchestrator.services["api-backend"]
            assert service_info.depends_on == ["database"]

    def test_volume_configuration_workflow(self, client, mock_orchestrator):
        """Test modifying volume configurations"""
        volume_config = {
            "volumes": [
                "./config:/app/config:ro",
                "app_logs:/app/logs",
                "/host/path:/container/path"
            ]
        }

        with patch('api.routes.meta_orchestrator', mock_orchestrator):
            # Validate volume configuration
            validation_request = {"services": {"api-backend": volume_config}}
            response = client.post("/api/v1/services/config/validate", json=validation_request)
            assert response.status_code == 200

            validation_result = response.json()["validation_result"]
            assert validation_result["overall_valid"] == True

            # Apply volume configuration
            response = client.put("/api/v1/services/api-backend/config", json=volume_config)
            assert response.status_code == 200

            modification_result = response.json()["config_modification"]
            assert modification_result["success"] == True
            assert "volumes" in modification_result["changes_applied"]

    def test_network_configuration_workflow(self, client, mock_orchestrator):
        """Test modifying network configurations"""
        network_config = {
            "networks": ["web", "api", "monitoring"],
            "environment": {"NETWORK_CONFIG": "custom"}
        }

        with patch('api.routes.meta_orchestrator', mock_orchestrator):
            response = client.put("/api/v1/services/web-frontend/config", json=network_config)
            assert response.status_code == 200

            modification_result = response.json()["config_modification"]
            assert modification_result["success"] == True
            assert "networks" in modification_result["changes_applied"]

            # Verify warnings were generated for network changes
            # Note: This would be checked in validation step in real workflow

    def test_configuration_export_workflow(self, client, mock_orchestrator):
        """Test configuration export after modifications"""
        # First modify a service
        config_updates = {
            "environment": {"EXPORT_TEST": "true"},
            "restart": "on-failure"
        }

        with patch('api.routes.meta_orchestrator', mock_orchestrator):
            # Apply changes
            response = client.put("/api/v1/services/web-frontend/config", json=config_updates)
            assert response.status_code == 200

            # Export the configuration
            response = client.get("/api/v1/services/web-frontend/config/export?format=json")
            assert response.status_code == 200

            export_data = response.json()
            assert export_data["service_name"] == "web-frontend"
            assert export_data["format"] == "json"
            assert "content" in export_data

            # Parse the exported JSON
            import json
            exported_config = json.loads(export_data["content"])
            assert "config" in exported_config
            assert "sources" in exported_config

    def test_dry_run_validation_workflow(self, client, mock_orchestrator):
        """Test validation-only workflow (dry run)"""
        # Test configuration that would work but we want to validate only
        test_config = {
            "environment": {"DRY_RUN_TEST": "true"},
            "ports": ["9090:8080"],
            "restart": "unless-stopped"
        }

        with patch('api.routes.meta_orchestrator', mock_orchestrator):
            # Validate only
            validation_request = {"services": {"web-frontend": test_config}}
            response = client.post("/api/v1/services/config/validate", json=validation_request)
            assert response.status_code == 200

            validation_result = response.json()["validation_result"]
            assert validation_result["overall_valid"] == True

            # Verify no actual changes were made by checking current config
            response = client.get("/api/v1/services/web-frontend/config/current")
            assert response.status_code == 200

            current_config = response.json()["current_config"]
            # Should still have original configuration, not the test config
            assert current_config["restart"] == "unless-stopped"  # Original value
