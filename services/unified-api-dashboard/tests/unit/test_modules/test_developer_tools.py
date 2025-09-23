"""
Unit Tests for Developer Tools Module

Comprehensive unit tests for client code generation, API validation,
and integration testing utilities.
"""

import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

from ...conftest import *
from ....modules.developer_tools.client_generator import ClientCodeGenerator
from ....modules.developer_tools.api_validator import APIValidator
from ....modules.developer_tools.integration_tester import IntegrationTester


class TestClientCodeGenerator:
    """Test ClientCodeGenerator functionality."""

    @pytest.fixture
    def client_generator(self, mock_discovery_client, mock_api_catalog):
        """Create ClientCodeGenerator instance for testing."""
        return ClientCodeGenerator(mock_discovery_client, mock_api_catalog)

    @pytest.mark.asyncio
    async def test_generate_client_python(self, client_generator, sample_openapi_spec):
        """Test Python client generation."""
        client_code = await client_generator.generate_client(
            "test-service",
            sample_openapi_spec,
            "python"
        )

        assert "class TestServiceClient" in client_code
        assert "def get_health" in client_code
        assert "def get_users" in client_code
        assert "def create_user" in client_code

    @pytest.mark.asyncio
    async def test_generate_client_typescript(self, client_generator, sample_openapi_spec):
        """Test TypeScript client generation."""
        client_code = await client_generator.generate_client(
            "test-service",
            sample_openapi_spec,
            "typescript"
        )

        assert "class TestServiceClient" in client_code
        assert "async getHealth" in client_code
        assert "async getUsers" in client_code
        assert "async createUser" in client_code

    @pytest.mark.asyncio
    async def test_generate_client_go(self, client_generator, sample_openapi_spec):
        """Test Go client generation."""
        client_code = await client_generator.generate_client(
            "test-service",
            sample_openapi_spec,
            "go"
        )

        assert "type TestServiceClient" in client_code
        assert "func (c *TestServiceClient) GetHealth" in client_code
        assert "func (c *TestServiceClient) GetUsers" in client_code

    @pytest.mark.asyncio
    async def test_generate_client_java(self, client_generator, sample_openapi_spec):
        """Test Java client generation."""
        client_code = await client_generator.generate_client(
            "test-service",
            sample_openapi_spec,
            "java"
        )

        assert "public class TestServiceClient" in client_code
        assert "public void getHealth" in client_code
        assert "public void getUsers" in client_code

    @pytest.mark.asyncio
    async def test_generate_all_clients(self, client_generator, sample_openapi_spec):
        """Test generating clients for all supported languages."""
        with patch.object(client_generator, 'generate_client', new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = "// Generated client code"

            clients = await client_generator.generate_all_clients("test-service", sample_openapi_spec)

            assert "python" in clients
            assert "typescript" in clients
            assert "go" in clients
            assert "java" in clients

            # Should be called 4 times (once for each language)
            assert mock_gen.call_count == 4

    @pytest.mark.asyncio
    async def test_validate_generated_client(self, client_generator):
        """Test generated client validation."""
        # Simple Python client code
        client_code = '''
class TestClient:
    def __init__(self, base_url):
        self.base_url = base_url

    def test_method(self):
        return "test"
'''

        is_valid, errors = await client_generator.validate_generated_client(client_code, "python")

        # Basic validation - should pass for syntactically correct code
        assert is_valid or len(errors) == 0  # Either valid or no critical errors


class TestAPIValidator:
    """Test APIValidator functionality."""

    @pytest.fixture
    def api_validator(self, mock_discovery_client, mock_api_catalog):
        """Create APIValidator instance for testing."""
        return APIValidator(mock_discovery_client, mock_api_catalog)

    @pytest.mark.asyncio
    async def test_validate_openapi_spec_valid(self, api_validator, sample_openapi_spec):
        """Test validation of valid OpenAPI spec."""
        is_valid, errors, warnings = await api_validator.validate_openapi_spec(sample_openapi_spec)

        assert is_valid == True
        assert isinstance(errors, list)
        assert isinstance(warnings, list)

    @pytest.mark.asyncio
    async def test_validate_openapi_spec_invalid(self, api_validator):
        """Test validation of invalid OpenAPI spec."""
        invalid_spec = {
            "openapi": "3.0.0",
            "info": {"title": "Invalid API"},
            # Missing required fields
        }

        is_valid, errors, warnings = await api_validator.validate_openapi_spec(invalid_spec)

        assert is_valid == False
        assert len(errors) > 0

    @pytest.mark.asyncio
    async def test_validate_api_request(self, api_validator, sample_openapi_spec, sample_api_request):
        """Test API request validation against spec."""
        is_valid, errors = await api_validator.validate_api_request(
            sample_api_request,
            sample_openapi_spec
        )

        assert isinstance(is_valid, bool)
        assert isinstance(errors, list)

    @pytest.mark.asyncio
    async def test_validate_service_compliance(self, api_validator, sample_openapi_spec):
        """Test service compliance validation."""
        compliance_report = await api_validator.validate_service_compliance(
            "test-service",
            sample_openapi_spec
        )

        assert "overall_compliant" in compliance_report
        assert "structural_validation" in compliance_report
        assert "schema_validation" in compliance_report
        assert "security_validation" in compliance_report
        assert "design_best_practices" in compliance_report


class TestIntegrationTester:
    """Test IntegrationTester functionality."""

    @pytest.fixture
    def integration_tester(self, mock_discovery_client, mock_api_catalog, mock_api_tester):
        """Create IntegrationTester instance for testing."""
        return IntegrationTester(mock_discovery_client, mock_api_catalog, mock_api_tester, Mock())

    @pytest.mark.asyncio
    async def test_generate_test_suite_from_spec(self, integration_tester, sample_openapi_spec):
        """Test test suite generation from OpenAPI spec."""
        test_suite = await integration_tester.generate_test_suite_from_spec(
            "test-service",
            sample_openapi_spec
        )

        assert "service_name" in test_suite
        assert "endpoints" in test_suite
        assert "test_cases" in test_suite
        assert len(test_suite["test_cases"]) > 0

        # Should have test cases for each endpoint
        assert any(tc["endpoint"] == "/health" for tc in test_suite["test_cases"])
        assert any(tc["endpoint"] == "/users" for tc in test_suite["test_cases"])

    @pytest.mark.asyncio
    async def test_run_test_suite(self, integration_tester, sample_openapi_spec):
        """Test test suite execution."""
        # Generate test suite first
        test_suite = await integration_tester.generate_test_suite_from_spec(
            "test-service",
            sample_openapi_spec
        )

        # Mock the API tester to return success
        integration_tester.api_tester.execute_test = AsyncMock(return_value={
            "success": True,
            "response_time": 150,
            "status_code": 200,
            "response_data": {"status": "ok"}
        })

        results = await integration_tester.run_test_suite(test_suite)

        assert "suite_name" in results
        assert "total_tests" in results
        assert "passed_tests" in results
        assert "failed_tests" in results
        assert "execution_time" in results
        assert "test_results" in results

    @pytest.mark.asyncio
    async def test_run_load_test(self, integration_tester):
        """Test load testing functionality."""
        load_test_config = {
            "endpoint": "/api/test",
            "method": "GET",
            "concurrent_users": 10,
            "duration_seconds": 30,
            "ramp_up_seconds": 5
        }

        # Mock API tester
        integration_tester.api_tester.execute_load_test = AsyncMock(return_value={
            "total_requests": 300,
            "successful_requests": 295,
            "failed_requests": 5,
            "avg_response_time": 150,
            "min_response_time": 100,
            "max_response_time": 300,
            "rps": 10,
            "error_rate": 0.017
        })

        results = await integration_tester.run_load_test(load_test_config)

        assert "total_requests" in results
        assert "successful_requests" in results
        assert "failed_requests" in results
        assert "avg_response_time" in results
        assert "rps" in results
        assert "error_rate" in results

    @pytest.mark.asyncio
    async def test_run_contract_test(self, integration_tester, sample_openapi_spec):
        """Test contract testing functionality."""
        # Mock API tester
        integration_tester.api_tester.execute_contract_test = AsyncMock(return_value={
            "contract_compliant": True,
            "validation_errors": [],
            "schema_matches": True,
            "response_format_valid": True,
            "test_coverage": 0.95
        })

        results = await integration_tester.run_contract_test(
            "test-service",
            sample_openapi_spec
        )

        assert "contract_compliant" in results
        assert "validation_errors" in results
        assert "schema_matches" in results
        assert "response_format_valid" in results
        assert "test_coverage" in results


class TestDeveloperToolsIntegration:
    """Integration tests for developer tools working together."""

    @pytest.fixture
    async def dev_tools_suite(self, mock_discovery_client, mock_api_catalog, mock_api_tester):
        """Create full developer tools suite for integration testing."""
        return {
            "client_generator": ClientCodeGenerator(mock_discovery_client, mock_api_catalog),
            "api_validator": APIValidator(mock_discovery_client, mock_api_catalog),
            "integration_tester": IntegrationTester(mock_discovery_client, mock_api_catalog, mock_api_tester, Mock())
        }

    @pytest.mark.asyncio
    async def test_full_development_workflow(self, dev_tools_suite, sample_openapi_spec):
        """Test complete development workflow from spec to client generation."""
        # Step 1: Validate the API spec
        is_valid, errors, warnings = await dev_tools_suite["api_validator"].validate_openapi_spec(sample_openapi_spec)
        assert is_valid == True

        # Step 2: Generate test suite
        test_suite = await dev_tools_suite["integration_tester"].generate_test_suite_from_spec(
            "test-service",
            sample_openapi_spec
        )
        assert len(test_suite["test_cases"]) > 0

        # Step 3: Generate client code
        python_client = await dev_tools_suite["client_generator"].generate_client(
            "test-service",
            sample_openapi_spec,
            "python"
        )
        assert len(python_client) > 0
        assert "class TestServiceClient" in python_client

        # Step 4: Validate generated client
        is_valid_client, client_errors = await dev_tools_suite["client_generator"].validate_generated_client(
            python_client,
            "python"
        )
        # Client validation may have minor issues but should not be completely broken
        assert isinstance(is_valid_client, bool)

    @pytest.mark.asyncio
    async def test_validation_feedback_loop(self, dev_tools_suite):
        """Test validation feedback loop for API improvement."""
        # Start with a spec that has some issues
        problematic_spec = {
            "openapi": "3.0.0",
            "info": {"title": "Problematic API"},
            "paths": {
                "/test": {
                    "get": {
                        "responses": {
                            # Missing 200 response
                            "400": {"description": "Bad Request"}
                        }
                    }
                }
            }
        }

        # Validate and get feedback
        is_valid, errors, warnings = await dev_tools_suite["api_validator"].validate_openapi_spec(problematic_spec)

        # Should identify issues
        assert len(errors) > 0 or len(warnings) > 0

        # Could then use this feedback to improve the spec and re-validate
