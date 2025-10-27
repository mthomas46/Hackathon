"""
Unit tests for configuration validation API endpoints.

✅ PHASE 5: Testing - Comprehensive test coverage for validation API
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from fastapi.testclient import TestClient

from src.api.app import create_app
from src.validation.types import ValidationResult as ValidatorResult, ValidationResults


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def mock_validator():
    """Mock ConfigValidator."""
    with patch('src.api.routes.config_validation.ConfigValidator') as mock:
        yield mock


@pytest.fixture
def mock_registry():
    """Mock get_registry."""
    with patch('src.api.routes.config_validation.get_registry') as mock:
        yield mock


@pytest.fixture
def mock_redis_client():
    """Mock get_redis_client."""
    with patch('src.api.routes.config_validation.get_redis_client') as mock:
        yield mock


@pytest.fixture
def mock_settings():
    """Mock settings."""
    with patch('src.api.routes.config_validation.settings') as mock:
        yield mock


# ============================================================================
# Mock Data
# ============================================================================

def create_mock_validation_result(
    check_name: str = "Test Check",
    passed: bool = True,
    severity: str = "medium",
    message: str = "Test passed"
) -> ValidatorResult:
    """Create a mock validation result."""
    return ValidatorResult(
        check_name=check_name,
        passed=passed,
        severity=severity,
        message=message,
        details={"test": "data"},
        remediation="No action needed" if passed else "Fix the issue",
        timestamp=datetime.now().isoformat()
    )


def create_mock_validation_results(
    total: int = 5,
    passed: int = 5,
    failed: int = 0
) -> ValidationResults:
    """Create mock validation results."""
    results = ValidationResults()
    
    for i in range(passed):
        results.add_result(create_mock_validation_result(
            check_name=f"Check {i+1}",
            passed=True,
            severity="medium",
            message=f"Check {i+1} passed"
        ))
    
    for i in range(failed):
        results.add_result(create_mock_validation_result(
            check_name=f"Check {passed+i+1}",
            passed=False,
            severity="critical",
            message=f"Check {passed+i+1} failed"
        ))
    
    return results


# ============================================================================
# Test /api/v1/config/validate
# ============================================================================

class TestValidateAll:
    """Tests for /api/v1/config/validate endpoint."""
    
    def test_validate_all_success(self, client, mock_validator):
        """Test successful validation of all configurations."""
        # Setup mock
        mock_results = create_mock_validation_results(total=9, passed=9, failed=0)
        mock_instance = mock_validator.return_value
        mock_instance.validate_all = AsyncMock(return_value=mock_results)
        
        # Make request
        response = client.get("/api/v1/config/validate")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["total_checks"] == 9
        assert data["passed"] == 9
        assert data["failed"] == 0
        assert data["critical_failures"] == 0
        assert data["overall_status"] == "healthy"
        assert len(data["results"]) == 9
    
    def test_validate_all_with_failures(self, client, mock_validator):
        """Test validation with some failures."""
        # Setup mock with failures
        mock_results = create_mock_validation_results(total=9, passed=6, failed=3)
        mock_instance = mock_validator.return_value
        mock_instance.validate_all = AsyncMock(return_value=mock_results)
        
        # Make request
        response = client.get("/api/v1/config/validate")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["total_checks"] == 9
        assert data["passed"] == 6
        assert data["failed"] == 3
        assert data["overall_status"] == "degraded"
    
    def test_validate_all_with_critical_failures(self, client, mock_validator):
        """Test validation with critical failures."""
        # Setup mock with critical failures
        mock_results = ValidationResults()
        mock_results.add_result(create_mock_validation_result(
            check_name="Critical Check",
            passed=False,
            severity="critical",
            message="Critical failure"
        ))
        mock_instance = mock_validator.return_value
        mock_instance.validate_all = AsyncMock(return_value=mock_results)
        
        # Make request
        response = client.get("/api/v1/config/validate")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["overall_status"] == "critical"
        assert data["critical_failures"] > 0
    
    def test_validate_all_fail_fast(self, client, mock_validator):
        """Test validation with fail_fast parameter."""
        # Setup mock
        mock_results = create_mock_validation_results(total=1, passed=0, failed=1)
        mock_instance = mock_validator.return_value
        mock_instance.validate_all = AsyncMock(return_value=mock_results)
        
        # Make request with fail_fast
        response = client.get("/api/v1/config/validate?fail_fast=true")
        
        # Assertions
        assert response.status_code == 200
        mock_instance.validate_all.assert_called_once_with(fail_fast=True)
    
    def test_validate_all_error(self, client, mock_validator):
        """Test validation system error."""
        # Setup mock to raise exception
        mock_instance = mock_validator.return_value
        mock_instance.validate_all = AsyncMock(side_effect=Exception("Test error"))
        
        # Make request
        response = client.get("/api/v1/config/validate")
        
        # Assertions
        assert response.status_code == 500
        assert "Test error" in response.json()["detail"]


# ============================================================================
# Test /api/v1/config/validate/redis
# ============================================================================

class TestValidateRedis:
    """Tests for /api/v1/config/validate/redis endpoint."""
    
    def test_validate_redis_success(self, client, mock_validator):
        """Test successful Redis validation."""
        # Setup mock
        mock_instance = mock_validator.return_value
        mock_instance.validate_redis_connection = AsyncMock(
            return_value=create_mock_validation_result(check_name="Redis Connection", passed=True)
        )
        mock_instance.validate_redis_streams = AsyncMock(
            return_value=create_mock_validation_result(check_name="Redis Streams", passed=True)
        )
        mock_instance.validate_redis_consumer_groups = AsyncMock(
            return_value=create_mock_validation_result(check_name="Consumer Groups", passed=True)
        )
        
        # Make request
        response = client.get("/api/v1/config/validate/redis")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["category"] == "Redis"
        assert data["total_checks"] == 3
        assert data["passed"] == 3
        assert data["failed"] == 0
        assert data["status"] == "healthy"
    
    def test_validate_redis_with_failures(self, client, mock_validator):
        """Test Redis validation with failures."""
        # Setup mock with one failure
        mock_instance = mock_validator.return_value
        mock_instance.validate_redis_connection = AsyncMock(
            return_value=create_mock_validation_result(check_name="Redis Connection", passed=False)
        )
        mock_instance.validate_redis_streams = AsyncMock(
            return_value=create_mock_validation_result(check_name="Redis Streams", passed=True)
        )
        mock_instance.validate_redis_consumer_groups = AsyncMock(
            return_value=create_mock_validation_result(check_name="Consumer Groups", passed=True)
        )
        
        # Make request
        response = client.get("/api/v1/config/validate/redis")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["failed"] > 0
    
    def test_validate_redis_error(self, client, mock_validator):
        """Test Redis validation error."""
        # Setup mock to raise exception
        mock_instance = mock_validator.return_value
        mock_instance.validate_redis_connection = AsyncMock(side_effect=Exception("Redis error"))
        
        # Make request
        response = client.get("/api/v1/config/validate/redis")
        
        # Assertions
        assert response.status_code == 500
        assert "Redis error" in response.json()["detail"]


# ============================================================================
# Test /api/v1/config/validate/database
# ============================================================================

class TestValidateDatabase:
    """Tests for /api/v1/config/validate/database endpoint."""
    
    def test_validate_database_success(self, client, mock_validator):
        """Test successful database validation."""
        # Setup mock
        mock_instance = mock_validator.return_value
        mock_instance.validate_database_connection = AsyncMock(
            return_value=create_mock_validation_result(check_name="DB Connection", passed=True)
        )
        mock_instance.validate_database_names = AsyncMock(
            return_value=create_mock_validation_result(check_name="DB Names", passed=True)
        )
        mock_instance.validate_database_schema = AsyncMock(
            return_value=create_mock_validation_result(check_name="DB Schema", passed=True)
        )
        
        # Make request
        response = client.get("/api/v1/config/validate/database")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["category"] == "Database"
        assert data["status"] == "healthy"
    
    def test_validate_database_error(self, client, mock_validator):
        """Test database validation error."""
        # Setup mock to raise exception
        mock_instance = mock_validator.return_value
        mock_instance.validate_database_connection = AsyncMock(side_effect=Exception("DB error"))
        
        # Make request
        response = client.get("/api/v1/config/validate/database")
        
        # Assertions
        assert response.status_code == 500


# ============================================================================
# Test /api/v1/config/validate/chromadb
# ============================================================================

class TestValidateChromaDB:
    """Tests for /api/v1/config/validate/chromadb endpoint."""
    
    def test_validate_chromadb_success(self, client, mock_validator):
        """Test successful ChromaDB validation."""
        # Setup mock
        mock_instance = mock_validator.return_value
        mock_instance.validate_chromadb_collection = AsyncMock(
            return_value=create_mock_validation_result(check_name="ChromaDB Collection", passed=True)
        )
        
        # Make request
        response = client.get("/api/v1/config/validate/chromadb")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["category"] == "ChromaDB"
        assert data["status"] == "healthy"
    
    def test_validate_chromadb_no_result(self, client, mock_validator):
        """Test ChromaDB validation with no result."""
        # Setup mock to return None
        mock_instance = mock_validator.return_value
        mock_instance.validate_chromadb_collection = AsyncMock(return_value=None)
        
        # Make request
        response = client.get("/api/v1/config/validate/chromadb")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unknown"
        assert data["total_checks"] == 0


# ============================================================================
# Test /api/v1/config/validate/services
# ============================================================================

class TestValidateServices:
    """Tests for /api/v1/config/validate/services endpoint."""
    
    def test_validate_services_success(self, client, mock_validator):
        """Test successful services validation."""
        # Setup mock
        mock_instance = mock_validator.return_value
        mock_instance.validate_service_ports = AsyncMock(
            return_value=create_mock_validation_result(check_name="Service Ports", passed=True)
        )
        mock_instance.validate_network_connectivity = AsyncMock(
            return_value=create_mock_validation_result(check_name="Network", passed=True)
        )
        
        # Make request
        response = client.get("/api/v1/config/validate/services")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["category"] == "Services"
        assert data["status"] == "healthy"


# ============================================================================
# Test /api/v1/config/health
# ============================================================================

class TestConfigHealth:
    """Tests for /api/v1/config/health endpoint."""
    
    def test_config_health_success(self, client, mock_registry):
        """Test successful config health check."""
        # Setup mock registry
        mock_reg = Mock()
        mock_reg.services = [
            Mock(name="service1", enabled=True, port=8001),
            Mock(name="service2", enabled=True, port=8002)
        ]
        mock_reg.redis.streams.model_dump.return_value = {
            "ingestion": {}, "embedding": {}, "retry": {}, "dead_letter": {}
        }
        mock_reg.database.connection.url = "postgresql://localhost"
        mock_registry.return_value = mock_reg
        
        # Make request
        response = client.get("/api/v1/config/health")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["registry_loaded"] is True
        assert len(data["services"]) == 2
        assert data["redis_streams"] == 4
    
    def test_config_health_degraded(self, client, mock_registry):
        """Test config health with degraded status."""
        # Setup mock to raise exception
        mock_registry.side_effect = Exception("Registry error")
        
        # Make request
        response = client.get("/api/v1/config/health")
        
        # Assertions
        assert response.status_code == 500
        data = response.json()
        assert data["status"] == "critical"
        assert data["registry_loaded"] is False


# ============================================================================
# Test /api/v1/config/diff
# ============================================================================

class TestConfigDiff:
    """Tests for /api/v1/config/diff endpoint."""
    
    def test_config_diff_no_differences(self, client, mock_registry, mock_redis_client, mock_settings):
        """Test config diff with no differences."""
        # Setup mocks with matching values
        mock_reg = Mock()
        mock_reg.redis.streams.ingestion.name = "ingestion-queue"
        mock_reg.redis.streams.ingestion.consumer_group = "ingestion-workers"
        mock_reg.database.connection.url = "postgresql://localhost"
        mock_reg.chromadb.collections.main.name = "ecosystem_mcp"
        mock_registry.return_value = mock_reg
        
        mock_redis = Mock()
        mock_redis.INGESTION_STREAM = "ingestion-queue"
        mock_redis.CONSUMER_GROUP = "ingestion-workers"
        mock_redis_client.return_value = mock_redis
        
        mock_settings.database_url = "postgresql://localhost"
        mock_settings.chroma_collection_name = "ecosystem_mcp"
        
        # Make request
        response = client.get("/api/v1/config/diff")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["total_differences"] == 0
        assert data["recommendation"] == "No critical issues"
    
    def test_config_diff_with_differences(self, client, mock_registry, mock_redis_client, mock_settings):
        """Test config diff with differences detected."""
        # Setup mocks with mismatched values
        mock_reg = Mock()
        mock_reg.redis.streams.ingestion.name = "ingestion-queue"
        mock_reg.redis.streams.ingestion.consumer_group = "ingestion-workers"  # Plural
        mock_reg.database.connection.url = "postgresql://localhost"
        mock_reg.chromadb.collections.main.name = "ecosystem_mcp"
        mock_registry.return_value = mock_reg
        
        mock_redis = Mock()
        mock_redis.INGESTION_STREAM = "ingestion-queue"
        mock_redis.CONSUMER_GROUP = "ingestion-worker"  # Singular - MISMATCH!
        mock_redis_client.return_value = mock_redis
        
        mock_settings.database_url = "postgresql://localhost"
        mock_settings.chroma_collection_name = "ecosystem_mcp"
        
        # Make request
        response = client.get("/api/v1/config/diff")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["total_differences"] == 1
        assert data["critical"] == 1
        assert data["recommendation"] == "Critical mismatches detected - restart required"
        
        # Check the specific difference
        diff = data["differences"][0]
        assert diff["category"] == "Redis"
        assert diff["field"] == "consumer_group"
        assert diff["registry_value"] == "ingestion-workers"
        assert diff["runtime_value"] == "ingestion-worker"
        assert diff["severity"] == "critical"
    
    def test_config_diff_error(self, client, mock_registry):
        """Test config diff error handling."""
        # Setup mock to raise exception
        mock_registry.side_effect = Exception("Diff error")
        
        # Make request
        response = client.get("/api/v1/config/diff")
        
        # Assertions
        assert response.status_code == 500
        assert "Diff error" in response.json()["detail"]


# ============================================================================
# Test /api/v1/config/registry
# ============================================================================

class TestGetRegistryConfig:
    """Tests for /api/v1/config/registry endpoint."""
    
    def test_get_registry_config_success(self, client, mock_registry):
        """Test successful registry retrieval."""
        # Setup mock
        mock_reg = Mock()
        mock_reg.model_dump.return_value = {
            "environment": "development",
            "services": [],
            "redis": {},
            "database": {}
        }
        mock_reg.environment = "development"
        mock_registry.return_value = mock_reg
        
        # Make request
        response = client.get("/api/v1/config/registry")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["source_file"] == "config/service_registry.yaml"
        assert data["environment"] == "development"
        assert "configuration" in data
    
    def test_get_registry_config_error(self, client, mock_registry):
        """Test registry retrieval error."""
        # Setup mock to raise exception
        mock_registry.side_effect = Exception("Registry error")
        
        # Make request
        response = client.get("/api/v1/config/registry")
        
        # Assertions
        assert response.status_code == 500
        assert "Registry error" in response.json()["detail"]


# ============================================================================
# Integration-like Tests (using TestClient)
# ============================================================================

class TestValidationAPIIntegration:
    """Integration-style tests for validation API."""
    
    def test_all_endpoints_accessible(self, client):
        """Test that all validation endpoints are accessible."""
        endpoints = [
            "/api/v1/config/validate",
            "/api/v1/config/validate/redis",
            "/api/v1/config/validate/database",
            "/api/v1/config/validate/chromadb",
            "/api/v1/config/validate/services",
            "/api/v1/config/health",
            "/api/v1/config/diff",
            "/api/v1/config/registry"
        ]
        
        for endpoint in endpoints:
            # Note: These will fail without proper mocking of dependencies
            # but at least we verify the routes are registered
            response = client.get(endpoint)
            # Should not be 404 (Not Found) - route exists
            assert response.status_code != 404, f"Endpoint {endpoint} not found"
    
    def test_openapi_schema_includes_validation_endpoints(self, client):
        """Test that validation endpoints are in OpenAPI schema."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        openapi_schema = response.json()
        paths = openapi_schema.get("paths", {})
        
        # Check that our validation endpoints are documented
        assert "/api/v1/config/validate" in paths
        assert "/api/v1/config/health" in paths
        assert "/api/v1/config/diff" in paths
        assert "/api/v1/config/registry" in paths


# ============================================================================
# Performance Tests
# ============================================================================

class TestValidationAPIPerformance:
    """Performance tests for validation API."""
    
    def test_health_check_is_fast(self, client, mock_registry):
        """Test that health check endpoint is fast (<500ms)."""
        import time
        
        # Setup mock
        mock_reg = Mock()
        mock_reg.services = []
        mock_reg.redis.streams.model_dump.return_value = {}
        mock_reg.database.connection.url = "test"
        mock_registry.return_value = mock_reg
        
        # Measure response time
        start = time.time()
        response = client.get("/api/v1/config/health")
        duration = time.time() - start
        
        # Assertions
        assert response.status_code == 200
        assert duration < 0.5, f"Health check took {duration}s (>500ms)"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

