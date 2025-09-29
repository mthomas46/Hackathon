"""API endpoint tests for architecture-digitizer service."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import json

# Import the FastAPI app
from ..main import app

# Create test client
client = TestClient(app)


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_endpoint(self):
        """Test basic health check."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "service" in data
        assert "timestamp" in data

    def test_health_endpoint_content(self):
        """Test health endpoint returns proper content."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert data["service"] == "architecture-digitizer"
        assert "timestamp" in data
        assert "version" in data


class TestNormalizeEndpoint:
    """Test architecture normalization endpoints."""

    def test_normalize_architecture_valid_request(self):
        """Test normalizing architecture with valid request."""
        request_data = {
            "system": "aws",
            "architecture_data": {
                "resources": [
                    {
                        "type": "ec2",
                        "id": "i-12345",
                        "properties": {
                            "instance_type": "t2.micro",
                            "state": "running"
                        }
                    }
                ],
                "connections": []
            },
            "format": "json"
        }

        response = client.post("/api/v1/normalize", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert "normalized_architecture" in data
        assert "metadata" in data

    def test_normalize_architecture_invalid_system(self):
        """Test normalizing with invalid system."""
        request_data = {
            "system": "invalid_system",
            "architecture_data": {"resources": []},
            "format": "json"
        }

        response = client.post("/api/v1/normalize", json=request_data)

        assert response.status_code == 400
        data = response.json()
        assert "error" in data

    def test_normalize_architecture_missing_data(self):
        """Test normalizing with missing architecture data."""
        request_data = {
            "system": "aws",
            "format": "json"
            # Missing architecture_data
        }

        response = client.post("/api/v1/normalize", json=request_data)

        assert response.status_code == 422  # Validation error

    def test_normalize_architecture_unsupported_format(self):
        """Test normalizing with unsupported format."""
        request_data = {
            "system": "aws",
            "architecture_data": {"resources": []},
            "format": "unsupported"
        }

        response = client.post("/api/v1/normalize", json=request_data)

        assert response.status_code == 400
        data = response.json()
        assert "error" in data


class TestFileUploadEndpoint:
    """Test file upload normalization endpoints."""

    def test_normalize_file_upload_valid(self):
        """Test file upload normalization with valid file."""
        # Create mock file content
        file_content = json.dumps({
            "resources": [
                {
                    "type": "ec2",
                    "id": "i-12345",
                    "properties": {"instance_type": "t2.micro"}
                }
            ]
        })

        files = {
            "file": ("architecture.json", file_content, "application/json")
        }
        data = {
            "system": "aws",
            "format": "json"
        }

        response = client.post("/api/v1/normalize/upload", files=files, data=data)

        assert response.status_code == 200
        response_data = response.json()
        assert "normalized_architecture" in response_data

    def test_normalize_file_upload_no_file(self):
        """Test file upload without file."""
        data = {"system": "aws", "format": "json"}

        response = client.post("/api/v1/normalize/upload", data=data)

        assert response.status_code == 422  # Validation error

    def test_normalize_file_upload_invalid_json(self):
        """Test file upload with invalid JSON."""
        files = {
            "file": ("architecture.json", "invalid json content", "application/json")
        }
        data = {"system": "aws", "format": "json"}

        response = client.post("/api/v1/normalize/upload", files=files, data=data)

        assert response.status_code == 400
        response_data = response.json()
        assert "error" in response_data

    def test_normalize_file_upload_unsupported_file_type(self):
        """Test file upload with unsupported file type."""
        files = {
            "file": ("architecture.txt", "plain text content", "text/plain")
        }
        data = {"system": "aws", "format": "json"}

        response = client.post("/api/v1/normalize/upload", files=files, data=data)

        assert response.status_code == 400
        response_data = response.json()
        assert "error" in response_data


class TestSupportedSystemsEndpoint:
    """Test supported systems endpoint."""

    def test_get_supported_systems(self):
        """Test getting list of supported systems."""
        response = client.get("/api/v1/systems")

        assert response.status_code == 200
        data = response.json()

        assert "systems" in data
        assert isinstance(data["systems"], list)
        assert len(data["systems"]) > 0

        # Check that common systems are included
        system_names = [system["name"] for system in data["systems"]]
        assert "aws" in system_names or "AWS" in [name.upper() for name in system_names]

    def test_supported_systems_structure(self):
        """Test that supported systems have proper structure."""
        response = client.get("/api/v1/systems")

        assert response.status_code == 200
        data = response.json()

        for system in data["systems"]:
            assert "name" in system
            assert "description" in system
            assert "supported_formats" in system


class TestSupportedFormatsEndpoint:
    """Test supported formats endpoint."""

    def test_get_supported_formats_valid_system(self):
        """Test getting supported formats for valid system."""
        response = client.get("/api/v1/systems/aws/formats")

        assert response.status_code == 200
        data = response.json()

        assert "formats" in data
        assert isinstance(data["formats"], list)

    def test_get_supported_formats_invalid_system(self):
        """Test getting supported formats for invalid system."""
        response = client.get("/api/v1/systems/invalid_system/formats")

        assert response.status_code == 404
        data = response.json()
        assert "error" in data

    def test_supported_formats_content(self):
        """Test that formats include common types."""
        response = client.get("/api/v1/systems/aws/formats")

        if response.status_code == 200:
            data = response.json()
            formats = [fmt.lower() for fmt in data["formats"]]

            # Should include common formats
            common_formats = ["json", "yaml", "xml", "terraform"]
            assert any(fmt in formats for fmt in common_formats)


class TestErrorHandling:
    """Test error handling across endpoints."""

    def test_invalid_json_payload(self):
        """Test handling of invalid JSON payloads."""
        response = client.post(
            "/api/v1/normalize",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422  # Validation error

    def test_unsupported_content_type(self):
        """Test handling of unsupported content types."""
        response = client.post(
            "/api/v1/normalize",
            data="plain text",
            headers={"Content-Type": "text/plain"}
        )

        assert response.status_code == 422  # Validation error

    def test_missing_required_headers(self):
        """Test handling of missing required headers."""
        request_data = {"system": "aws", "architecture_data": {}}

        response = client.post("/api/v1/normalize", json=request_data)

        # Should handle gracefully
        assert response.status_code in [200, 400, 422]

    @patch('httpx.AsyncClient')
    def test_external_service_unavailable(self, mock_client):
        """Test handling when external services are unavailable."""
        # Mock connection error
        mock_client.return_value.__aenter__.side_effect = Exception("Connection failed")

        request_data = {
            "system": "aws",
            "architecture_data": {"resources": []},
            "format": "json"
        }

        response = client.post("/api/v1/normalize", json=request_data)

        # Should handle gracefully
        assert response.status_code in [200, 503]

    def test_large_payload(self):
        """Test handling of large payloads."""
        # Create a large architecture data
        large_resources = [
            {
                "type": "ec2",
                "id": f"i-{i}",
                "properties": {"instance_type": "t2.micro", "large_data": "x" * 1000}
            }
            for i in range(100)
        ]

        request_data = {
            "system": "aws",
            "architecture_data": {"resources": large_resources},
            "format": "json"
        }

        response = client.post("/api/v1/normalize", json=request_data)

        # Should handle large payloads appropriately
        assert response.status_code in [200, 413, 500]


class TestCORSHeaders:
    """Test CORS headers are properly set."""

    def test_cors_headers_present(self):
        """Test that CORS headers are present in responses."""
        response = client.options("/health")

        # Check for common CORS headers
        cors_headers = [
            "access-control-allow-origin",
            "access-control-allow-methods",
            "access-control-allow-headers"
        ]

        response_headers = {k.lower(): v for k, v in response.headers.items()}

        for header in cors_headers:
            assert header in response_headers

    def test_cors_preflight_request(self):
        """Test CORS preflight request handling."""
        response = client.options(
            "/api/v1/normalize",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type"
            }
        )

        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers


class TestResponseFormat:
    """Test response format consistency."""

    def test_json_response_format(self):
        """Test that all responses follow consistent JSON format."""
        endpoints = [
            "/health",
            "/api/v1/systems"
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 200

            try:
                data = response.json()
                assert isinstance(data, dict)
            except json.JSONDecodeError:
                pytest.fail(f"Endpoint {endpoint} did not return valid JSON")

    def test_error_response_format(self):
        """Test that error responses follow consistent format."""
        # Test with invalid system
        response = client.get("/api/v1/systems/invalid_system/formats")

        if response.status_code >= 400:
            data = response.json()
            assert "error" in data or "detail" in data

    def test_success_response_format(self):
        """Test that success responses follow consistent format."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()

        # Should have standard success fields
        assert "status" in data
        assert "service" in data
        assert "timestamp" in data
