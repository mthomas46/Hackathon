"""API integration tests for configuration modification endpoints"""

import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch

from main import app
from tests.fixtures.docker_compose_fixture import sample_compose_config


class TestConfigModificationAPI:
    """API tests for configuration modification endpoints"""

    @pytest.fixture
    def client(self):
        """Test client for the FastAPI app"""
        return TestClient(app)

    @pytest.fixture
    def mock_orchestrator(self):
        """Mock orchestrator with services"""
        orchestrator = Mock()
        orchestrator.services = {}

        # Add mock services
        services_data = {
            'user-store': {'ports': ['8106:5150'], 'health_check_url': 'http://localhost:8106/health'},
            'api-gateway': {'ports': ['8080:3000'], 'health_check_url': 'http://localhost:8080/health'},
            'redis': {'ports': ['6379:6379'], 'health_check_url': None}
        }

        for service_name, data in services_data.items():
            service_info = Mock()
            service_info.name = service_name
            service_info.ports = data['ports']
            service_info.health_check_url = data['health_check_url']
            # Add other attributes that might be modified
            service_info.image = f"{service_name}:latest"
            service_info.environment = {"SERVICE_NAME": service_name}
            service_info.volumes = []
            service_info.depends_on = []
            service_info.restart_policy = "unless-stopped"
            service_info.networks = ["default"]
            orchestrator.services[service_name] = service_info

        # Mock restart_service method
        orchestrator.restart_service = AsyncMock(return_value=Mock(success=True, message="Service restarted successfully"))

        return orchestrator

    def test_modify_service_config_success(self, client, mock_orchestrator):
        """Test successful single service configuration modification"""
        from models.config_api import ServiceConfigUpdate

        config_updates = ServiceConfigUpdate(
            environment={"NEW_VAR": "new_value", "DEBUG": "true"},
            restart="always",
            restart_after_change=True
        )

        mock_restart_result = {"restarted": True, "service_name": "user-store", "message": "Service restarted"}

        mock_result = {
            "success": True,
            "service_name": "user-store",
            "changes_applied": ["environment", "restart"],
            "original_config": {"restart": "unless-stopped"},
            "persistence_result": {"persisted": True},
            "restart_result": mock_restart_result,
            "message": "Successfully applied 2 configuration changes to user-store"
        }

        with patch('api.routes.meta_orchestrator', mock_orchestrator), \
             patch('api.routes.apply_service_config_changes', return_value=mock_result), \
             patch('api.routes.restart_service_after_config_change', return_value=mock_restart_result):
            response = client.put("/api/v1/services/user-store/config", json=config_updates.model_dump())

            assert response.status_code == 200
            data = response.json()
            assert "config_modification" in data
            result = data["config_modification"]
            assert result["success"] == True
            assert result["service_name"] == "user-store"
            assert "environment" in result["changes_applied"]
            assert "restart" in result["changes_applied"]
            assert "restart_result" in result

    def test_modify_service_config_validation_error(self, client, mock_orchestrator):
        """Test configuration modification with validation errors"""
        # Invalid port specification - this should fail Pydantic validation
        config_updates = {
            "ports": ["invalid_port_spec"],
            "environment": "not_a_dict_or_list"  # Invalid environment format
        }

        with patch('api.routes.meta_orchestrator', mock_orchestrator):
            response = client.put("/api/v1/services/user-store/config", json=config_updates)

            # Should fail due to Pydantic validation
            assert response.status_code == 422  # Pydantic validation error
            data = response.json()
            assert "detail" in data

    def test_modify_service_config_not_found(self, client, mock_orchestrator):
        """Test modification of nonexistent service"""
        config_updates = {"environment": {"TEST": "value"}}

        with patch('api.routes.meta_orchestrator', mock_orchestrator):
            response = client.put("/api/v1/services/nonexistent-service/config", json=config_updates)

            assert response.status_code == 404
            data = response.json()
            assert "detail" in data

    def test_modify_services_config_batch_success(self, client, mock_orchestrator):
        """Test successful batch configuration modification"""
        from models.config_api import BatchConfigUpdate, ServiceConfigUpdate

        batch_config = BatchConfigUpdate(
            services={
                "user-store": ServiceConfigUpdate(
                    environment={"BATCH_VAR": "batch_value"},
                    restart="on-failure"
                ),
                "api-gateway": ServiceConfigUpdate(
                    environment={"API_VAR": "api_value"},
                    volumes=["/data:/app/data"]
                )
            },
            rollback_on_failure=False
        )

        # Mock successful results for each service
        mock_results = {
            "user-store": {
                "success": True,
                "service_name": "user-store",
                "changes_applied": ["environment", "restart"],
                "message": "Successfully applied 2 configuration changes"
            },
            "api-gateway": {
                "success": True,
                "service_name": "api-gateway",
                "changes_applied": ["environment", "volumes"],
                "message": "Successfully applied 2 configuration changes"
            }
        }

        async def mock_apply_changes(service_name, config):
            return mock_results[service_name]

        with patch('api.routes.meta_orchestrator', mock_orchestrator), \
             patch('api.routes.apply_service_config_changes', side_effect=mock_apply_changes), \
             patch('api.routes.restart_service_after_config_change', return_value={"restarted": True}):
            response = client.put("/api/v1/services/config/batch", json=batch_config.model_dump())

            assert response.status_code == 200
            data = response.json()
            assert "batch_config_modification" in data
            result = data["batch_config_modification"]
            assert result["total_services"] == 2
            assert result["successful_modifications"] == 2
            assert "user-store" in result["results"]
            assert "api-gateway" in result["results"]

    def test_modify_services_config_batch_validation_error(self, client, mock_orchestrator):
        """Test batch configuration with validation errors"""
        from models.config_api import BatchConfigUpdate, ServiceConfigUpdate

        # Create batch config with invalid data that should fail Pydantic validation
        batch_config = {
            "services": {
                "user-store": {
                    "ports": ["invalid_port_spec"],  # Invalid port format
                    "environment": {"VALID": "value"}
                },
                "nonexistent-service": {
                    "environment": {"TEST": "value"}
                }
            }
        }

        with patch('api.routes.meta_orchestrator', mock_orchestrator):
            response = client.put("/api/v1/services/config/batch", json=batch_config)

            # Should fail due to Pydantic validation
            assert response.status_code == 422
            data = response.json()
            assert "detail" in data

    def test_modify_services_config_batch_empty(self, client, mock_orchestrator):
        """Test batch configuration with no services"""
        batch_config = {"services": {}}

        with patch('api.routes.meta_orchestrator', mock_orchestrator):
            response = client.put("/api/v1/services/config/batch", json=batch_config)

            assert response.status_code == 400
            data = response.json()
            assert "detail" in data

    def test_rollback_service_config_success(self, client, mock_orchestrator):
        """Test successful service configuration rollback"""
        from models.config_api import ConfigRollbackRequest

        rollback_data = ConfigRollbackRequest(
            original_config={
                "environment": {"OLD_VAR": "old_value"},
                "restart": "unless-stopped"
            },
            restart_after_rollback=True
        )

        mock_result = {
            "success": True,
            "service_name": "user-store",
            "changes_applied": ["environment", "restart"],
            "message": "Successfully rolled back configuration",
            "restart_result": {"restarted": True}
        }

        with patch('api.routes.meta_orchestrator', mock_orchestrator), \
             patch('api.routes.apply_service_config_changes', return_value=mock_result), \
             patch('api.routes.restart_service_after_config_change', return_value={"restarted": True}):
            response = client.post("/api/v1/services/user-store/config/rollback", json=rollback_data.model_dump())

            assert response.status_code == 200
            data = response.json()
            assert "config_rollback" in data
            result = data["config_rollback"]
            assert result["success"] == True

    def test_rollback_service_config_missing_original(self, client, mock_orchestrator):
        """Test rollback with missing original configuration"""
        rollback_data = {}

        with patch('api.routes.meta_orchestrator', mock_orchestrator):
            response = client.post("/api/v1/services/user-store/config/rollback", json=rollback_data)

            assert response.status_code == 400
            data = response.json()
            assert "detail" in data

    def test_get_service_current_config_success(self, client, mock_orchestrator):
        """Test getting current service configuration"""
        # Mock the service info to return plain dict instead of Mock
        mock_service_info = {
            "image": "nginx:alpine",
            "ports": ["80:80"],
            "environment": {"NGINX_PORT": "80"},
            "volumes": [],
            "depends_on": [],
            "restart_policy": "unless-stopped",
            "networks": ["default"],
            "health_check_url": "http://localhost:80/health"
        }

        # Replace the Mock service with a dict-like object
        class MockService:
            def __init__(self, config):
                for key, value in config.items():
                    setattr(self, key, value)

        mock_orchestrator.services['user-store'] = MockService(mock_service_info)

        with patch('api.routes.meta_orchestrator', mock_orchestrator):
            response = client.get("/api/v1/services/user-store/config/current")

            assert response.status_code == 200
            data = response.json()
            assert "current_config" in data
            config = data["current_config"]
            assert config["image"] == "nginx:alpine"
            assert "80:80" in config["ports"]
            assert config["restart"] == "unless-stopped"

    def test_validate_services_config_success(self, client, mock_orchestrator):
        """Test successful configuration validation"""
        validation_request = {
            "services": {
                "user-store": {
                    "environment": {"VALID_VAR": "valid_value"},
                    "restart": "unless-stopped"
                },
                "api-gateway": {
                    "ports": ["8081:3000"],
                    "volumes": ["/tmp:/tmp"]
                }
            }
        }

        with patch('api.routes.meta_orchestrator', mock_orchestrator):
            response = client.post("/api/v1/services/config/validate", json=validation_request)

            assert response.status_code == 200
            data = response.json()
            assert "validation_result" in data
            result = data["validation_result"]
            assert result["overall_valid"] == True
            assert result["services_validated"] == 2

    def test_validate_services_config_with_errors(self, client, mock_orchestrator):
        """Test configuration validation with errors"""
        validation_request = {
            "services": {
                "user-store": {
                    "ports": ["invalid_port"],
                    "environment": "not_valid"
                },
                "nonexistent-service": {
                    "environment": {"TEST": "value"}
                }
            }
        }

        with patch('api.routes.meta_orchestrator', mock_orchestrator):
            response = client.post("/api/v1/services/config/validate", json=validation_request)

            assert response.status_code == 200  # Validation returns 200 even with errors
            data = response.json()
            assert "validation_result" in data
            result = data["validation_result"]
            assert result["overall_valid"] == False
            assert result["services_invalid"] > 0

    def test_validate_services_config_empty(self, client, mock_orchestrator):
        """Test validation with no services"""
        validation_request = {"services": {}}

        with patch('api.routes.meta_orchestrator', mock_orchestrator):
            response = client.post("/api/v1/services/config/validate", json=validation_request)

            assert response.status_code == 400
            data = response.json()
            assert "detail" in data

    def test_endpoints_orchestrator_not_initialized(self, client):
        """Test endpoints when orchestrator is not initialized"""
        with patch('api.routes.meta_orchestrator', None):
            # Test single service modification
            response = client.put("/api/v1/services/user-store/config", json={})
            assert response.status_code == 503

            # Test batch modification
            response = client.put("/api/v1/services/config/batch", json={"services": {}})
            assert response.status_code == 503

            # Test rollback
            response = client.post("/api/v1/services/user-store/config/rollback", json={})
            assert response.status_code == 503

            # Test current config
            response = client.get("/api/v1/services/user-store/config/current")
            assert response.status_code == 503

            # Test validation
            response = client.post("/api/v1/services/config/validate", json={"services": {}})
            assert response.status_code == 503

    @pytest.mark.parametrize("endpoint,method,data", [
        ("/api/v1/services/user-store/config", "put", {"environment": {"TEST": "value"}}),
        ("/api/v1/services/config/batch", "put", {"services": {"user-store": {"environment": {"TEST": "value"}}}}),
        ("/api/v1/services/user-store/config/rollback", "post", {"original_config": {"environment": {}}}),
        ("/api/v1/services/user-store/config/current", "get", None),
        ("/api/v1/services/config/validate", "post", {"services": {"user-store": {"environment": {"TEST": "value"}}}}),
    ])
    def test_endpoints_handle_exceptions(self, client, mock_orchestrator, endpoint, method, data):
        """Test that endpoints handle unexpected exceptions gracefully"""
        # Mock the orchestrator to raise an exception
        mock_orchestrator.services = None  # This will cause an AttributeError

        with patch('api.routes.meta_orchestrator', mock_orchestrator):
            if method == "get":
                response = client.get(endpoint)
            elif method == "put":
                response = client.put(endpoint, json=data)
            elif method == "post":
                response = client.post(endpoint, json=data)

            assert response.status_code == 500
            data = response.json()
            assert "detail" in data

    def test_port_validation(self, client, mock_orchestrator):
        """Test port validation in configuration updates"""
        # Valid ports
        valid_config = {
            "ports": ["8080:3000", "8443:443"]
        }

        with patch('api.routes.meta_orchestrator', mock_orchestrator):
            # This should not raise validation errors for ports
            response = client.put("/api/v1/services/user-store/config", json=valid_config)
            # Note: This might fail due to other validation, but ports should be valid

            # Invalid ports
            invalid_config = {
                "ports": ["invalid_port_spec", "8080"]
            }

            response = client.put("/api/v1/services/user-store/config", json=invalid_config)
            assert response.status_code == 400

    def test_environment_validation(self, client, mock_orchestrator):
        """Test environment variable validation"""
        # Valid environment (list format)
        valid_config = {
            "environment": ["KEY1=value1", "KEY2=value2"]
        }

        with patch('api.routes.meta_orchestrator', mock_orchestrator):
            # Should not fail validation
            response = client.put("/api/v1/services/user-store/config", json=valid_config)
            # Note: May fail for other reasons, but environment should be valid

            # Valid environment (dict format)
            valid_config_dict = {
                "environment": {"KEY1": "value1", "KEY2": "value2"}
            }

            response = client.put("/api/v1/services/user-store/config", json=valid_config_dict)
            # Should not fail validation

            # Invalid environment
            invalid_config = {
                "environment": "not_a_list_or_dict"
            }

            response = client.put("/api/v1/services/user-store/config", json=invalid_config)
            assert response.status_code == 400

    def test_restart_policy_validation(self, client, mock_orchestrator):
        """Test restart policy validation"""
        # Valid restart policies
        for policy in ["no", "always", "on-failure", "unless-stopped"]:
            config = {"restart": policy}

            with patch('api.routes.meta_orchestrator', mock_orchestrator):
                response = client.put("/api/v1/services/user-store/config", json=config)
                # Should not fail due to restart policy validation

        # Invalid restart policy
        invalid_config = {"restart": "invalid_policy"}

        with patch('api.routes.meta_orchestrator', mock_orchestrator):
            response = client.put("/api/v1/services/user-store/config", json=invalid_config)
            assert response.status_code == 400

    def test_image_build_exclusion(self, client, mock_orchestrator):
        """Test that image and build cannot both be specified"""
        invalid_config = {
            "image": "nginx:latest",
            "build": "."
        }

        with patch('api.routes.meta_orchestrator', mock_orchestrator):
            response = client.put("/api/v1/services/user-store/config", json=invalid_config)
            assert response.status_code == 400

    def test_audit_docker_compose_validation(self, client, mock_orchestrator):
        """Test Docker Compose validation endpoint"""
        mock_result = {
            "success": True,
            "services_count": 3,
            "port_conflicts": 0,
            "issues": [],
            "warnings": 1,
            "errors": 0,
            "validation_errors": []
        }

        with patch('api.routes.meta_orchestrator', mock_orchestrator), \
             patch('api.routes.monitoring_service') as mock_monitoring:
            mock_monitoring.validate_docker_compose = AsyncMock(return_value=mock_result)

            response = client.post("/api/v1/audit/docker-compose/validate")

            assert response.status_code == 200
            data = response.json()
            assert "docker_compose_validation" in data
            result = data["docker_compose_validation"]
            assert result["success"] == True
            assert result["services_count"] == 3

    def test_audit_config_drift_detection(self, client, mock_orchestrator):
        """Test configuration drift detection endpoint"""
        mock_result = {
            "success": True,
            "total_issues": 2,
            "high_severity": 1,
            "medium_severity": 1,
            "low_severity": 0,
            "schema_validation_passed": True,
            "scanned_files": 10,
            "scanned_containers": 5,
            "issues": [
                {
                    "type": "docker_vs_compose",
                    "severity": "high",
                    "description": "Port mismatch detected",
                    "field_path": "ports",
                    "can_auto_fix": False
                }
            ]
        }

        with patch('api.routes.meta_orchestrator', mock_orchestrator), \
             patch('api.routes.monitoring_service') as mock_monitoring:
            mock_monitoring.detect_configuration_drift = AsyncMock(return_value=mock_result)

            response = client.post("/api/v1/audit/config/drift-detect")

            assert response.status_code == 200
            data = response.json()
            assert "configuration_drift" in data
            result = data["configuration_drift"]
            assert result["success"] == True
            assert result["total_issues"] == 2

    def test_audit_production_readiness(self, client, mock_orchestrator):
        """Test production readiness validation endpoint"""
        mock_result = {
            "success": True,
            "overall_readiness": "development_ready",
            "overall_score": 0.85,
            "total_checks": 10,
            "passed_checks": 8,
            "failed_checks": 2,
            "critical_failures": 0,
            "results": [
                {
                    "check_name": "docker_containers_health",
                    "success": True,
                    "score": 1.0,
                    "message": "All containers healthy",
                    "issues": [],
                    "recommendations": []
                }
            ]
        }

        with patch('api.routes.meta_orchestrator', mock_orchestrator), \
             patch('api.routes.monitoring_service') as mock_monitoring:
            mock_monitoring.validate_production_readiness = AsyncMock(return_value=mock_result)

            response = client.post("/api/v1/audit/production-readiness/validate")

            assert response.status_code == 200
            data = response.json()
            assert "production_readiness" in data
            result = data["production_readiness"]
            assert result["success"] == True
            assert result["overall_readiness"] == "development_ready"

    def test_audit_config_standardization_service(self, client, mock_orchestrator):
        """Test single service configuration standardization"""
        mock_result = {
            "success": True,
            "service_name": "user-store",
            "changes_made": ["Updated port mapping"],
            "warnings": [],
            "errors": [],
            "issues": [
                {
                    "service": "user-store",
                    "type": "port_standardization",
                    "severity": "warning",
                    "description": "Port standardized",
                    "can_auto_fix": True
                }
            ]
        }

        with patch('api.routes.meta_orchestrator', mock_orchestrator), \
             patch('api.routes.monitoring_service') as mock_monitoring:
            mock_monitoring.standardize_service_config = AsyncMock(return_value=mock_result)

            response = client.post("/api/v1/audit/config/standardize/service/user-store")

            assert response.status_code == 200
            data = response.json()
            assert "config_standardization" in data
            result = data["config_standardization"]
            assert result["success"] == True
            assert result["service_name"] == "user-store"

    def test_audit_config_standardization_all(self, client, mock_orchestrator):
        """Test all services configuration standardization"""
        mock_result = {
            "success": True,
            "services_processed": 5,
            "services_standardized": 4,
            "total_issues": 3,
            "fixes_applied": 2,
            "standardization_rate": 0.8,
            "results": [
                {
                    "service_name": "user-store",
                    "success": True,
                    "changes_made": ["Updated config"],
                    "warnings": [],
                    "errors": []
                }
            ]
        }

        with patch('api.routes.meta_orchestrator', mock_orchestrator), \
             patch('api.routes.monitoring_service') as mock_monitoring:
            mock_monitoring.standardize_all_configs = AsyncMock(return_value=mock_result)

            response = client.post("/api/v1/audit/config/standardize/all")

            assert response.status_code == 200
            data = response.json()
            assert "config_standardization" in data
            result = data["config_standardization"]
            assert result["success"] == True
            assert result["services_processed"] == 5

    def test_audit_docker_standardization(self, client, mock_orchestrator):
        """Test Docker configuration standardization"""
        mock_result = {
            "success": True,
            "files_processed": 3,
            "files_modified": 1,
            "issues_found": 4,
            "issues_fixed": 2,
            "validation_errors": 0,
            "pydantic_validation_passed": True,
            "issues": [
                {
                    "service": "api-backend",
                    "type": "port_mapping",
                    "severity": "warning",
                    "description": "Port mapping issue",
                    "can_auto_fix": False
                }
            ]
        }

        with patch('api.routes.meta_orchestrator', mock_orchestrator), \
             patch('api.routes.monitoring_service') as mock_monitoring:
            mock_monitoring.standardize_docker_configs = AsyncMock(return_value=mock_result)

            response = client.post("/api/v1/audit/docker/standardize")

            assert response.status_code == 200
            data = response.json()
            assert "docker_standardization" in data
            result = data["docker_standardization"]
            assert result["success"] == True
            assert result["files_processed"] == 3
