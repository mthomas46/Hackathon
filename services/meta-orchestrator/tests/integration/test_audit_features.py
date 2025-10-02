#!/usr/bin/env python3
"""
Comprehensive Audit Features Test Suite

Tests all audit and verification capabilities integrated into the meta-orchestrator.
These tests validate the complete audit ecosystem functionality.

Run with:
    # Run all audit tests
    python -m pytest tests/integration/test_audit_features.py -v

    # Run tests for specific service
    python -m pytest tests/integration/test_audit_features.py::TestAuditFeatures::test_docker_compose_validation -v

    # Run tests against running ecosystem
    python -m pytest tests/integration/test_audit_features.py -v --tb=short
"""

import pytest
import asyncio
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import requests
import subprocess
import time
from unittest.mock import Mock, patch, AsyncMock

from fastapi.testclient import TestClient
from main import app
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestAuditFeatures:
    """
    Comprehensive test suite for all audit features.

    Tests the complete audit ecosystem including:
    - Docker Compose validation
    - Configuration drift detection
    - Production readiness validation
    - Configuration standardization
    - Docker standardization
    """

    @pytest.fixture
    def client(self):
        """FastAPI test client"""
        return TestClient(app)

    @pytest.fixture
    def mock_orchestrator(self):
        """Mock orchestrator for testing"""
        orchestrator = Mock()
        orchestrator.services = {
            'user-store': Mock(),
            'doc_store': Mock(),
            'analysis-service': Mock(),
            'orchestrator': Mock(),
            'frontend': Mock()
        }
        orchestrator.settings = Mock()
        orchestrator.settings.workspace_path = Path.cwd()
        return orchestrator

    @pytest.fixture
    def mock_monitoring_service(self):
        """Mock monitoring service for testing"""
        service = Mock()

        # Mock all audit methods
        service.validate_docker_compose = AsyncMock()
        service.detect_configuration_drift = AsyncMock()
        service.validate_production_readiness = AsyncMock()
        service.standardize_service_config = AsyncMock()
        service.standardize_all_configs = AsyncMock()
        service.standardize_docker_configs = AsyncMock()

        return service

    def test_audit_endpoints_exist(self, client):
        """Test that all audit endpoints are properly registered"""
        # Check that audit endpoints are accessible
        audit_endpoints = [
            "/api/v1/audit/docker-compose/validate",
            "/api/v1/audit/config/drift-detect",
            "/api/v1/audit/production-readiness/validate",
            "/api/v1/audit/config/standardize/service/test-service",
            "/api/v1/audit/config/standardize/all",
            "/api/v1/audit/docker/standardize"
        ]

        for endpoint in audit_endpoints:
            # These should return 503 (service unavailable) when monitoring service isn't initialized
            # rather than 404 (not found), proving the endpoints exist
            if "service/test-service" in endpoint:
                response = client.post("/api/v1/audit/config/standardize/service/nonexistent-service")
                assert response.status_code == 503, f"Endpoint {endpoint} should exist but monitoring service unavailable"
            elif endpoint.endswith("/all") or endpoint.endswith("/standardize"):
                response = client.post(endpoint)
                assert response.status_code == 503, f"Endpoint {endpoint} should exist but monitoring service unavailable"

    def test_docker_compose_validation_functionality(self, client, mock_orchestrator, mock_monitoring_service):
        """Test Docker Compose validation functionality"""
        # Mock successful validation result
        mock_result = {
            "success": True,
            "services_count": 5,
            "port_conflicts": 0,
            "issues": [
                {
                    "service": "web-frontend",
                    "type": "health_check",
                    "severity": "warning",
                    "description": "Missing start_period in health check",
                    "can_auto_fix": False
                }
            ],
            "warnings": 1,
            "errors": 0,
            "validation_errors": []
        }

        with patch('api.routes.meta_orchestrator', mock_orchestrator), \
             patch('api.routes.monitoring_service', mock_monitoring_service):

            mock_monitoring_service.validate_docker_compose.return_value = mock_result

            response = client.post("/api/v1/audit/docker-compose/validate")

            assert response.status_code == 200
            data = response.json()
            assert "docker_compose_validation" in data

            result = data["docker_compose_validation"]
            assert result["success"] == True
            assert result["services_count"] == 5
            assert result["port_conflicts"] == 0
            assert len(result["issues"]) == 1
            assert result["issues"][0]["service"] == "web-frontend"
            assert result["issues"][0]["type"] == "health_check"

    def test_configuration_drift_detection(self, client, mock_orchestrator, mock_monitoring_service):
        """Test configuration drift detection functionality"""
        mock_result = {
            "success": True,
            "total_issues": 3,
            "high_severity": 1,
            "medium_severity": 2,
            "low_severity": 0,
            "schema_validation_passed": True,
            "scanned_files": 15,
            "scanned_containers": 8,
            "issues": [
                {
                    "type": "docker_vs_compose",
                    "severity": "high",
                    "description": "Port mapping mismatch for service 'api-gateway'",
                    "field_path": "ports",
                    "can_auto_fix": False
                },
                {
                    "type": "compose_vs_pydantic",
                    "severity": "medium",
                    "description": "Environment variable mismatch",
                    "field_path": "environment.DEBUG",
                    "can_auto_fix": True
                }
            ]
        }

        with patch('api.routes.meta_orchestrator', mock_orchestrator), \
             patch('api.routes.monitoring_service', mock_monitoring_service):

            mock_monitoring_service.detect_configuration_drift.return_value = mock_result

            response = client.post("/api/v1/audit/config/drift-detect")

            assert response.status_code == 200
            data = response.json()
            assert "configuration_drift" in data

            result = data["configuration_drift"]
            assert result["success"] == True
            assert result["total_issues"] == 3
            assert result["high_severity"] == 1
            assert result["schema_validation_passed"] == True
            assert len(result["issues"]) == 2

    def test_production_readiness_validation(self, client, mock_orchestrator, mock_monitoring_service):
        """Test production readiness validation functionality"""
        mock_result = {
            "success": True,
            "overall_readiness": "development_ready",
            "overall_score": 0.87,
            "total_checks": 12,
            "passed_checks": 10,
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
                },
                {
                    "check_name": "api_schema_compliance",
                    "success": False,
                    "score": 0.75,
                    "message": "Some APIs missing schema validation",
                    "issues": ["Missing response schemas"],
                    "recommendations": ["Add OpenAPI response schemas"]
                }
            ],
            "recommendations": [
                "Add health checks to remaining services",
                "Implement proper error response schemas"
            ]
        }

        with patch('api.routes.meta_orchestrator', mock_orchestrator), \
             patch('api.routes.monitoring_service', mock_monitoring_service):

            mock_monitoring_service.validate_production_readiness.return_value = mock_result

            response = client.post("/api/v1/audit/production-readiness/validate")

            assert response.status_code == 200
            data = response.json()
            assert "production_readiness" in data

            result = data["production_readiness"]
            assert result["success"] == True
            assert result["overall_readiness"] == "development_ready"
            assert result["overall_score"] == 0.87
            assert result["total_checks"] == 12
            assert len(result["results"]) == 2
            assert len(result["recommendations"]) == 2

    def test_config_standardization_single_service(self, client, mock_orchestrator, mock_monitoring_service):
        """Test configuration standardization for single service"""
        mock_result = {
            "success": True,
            "service_name": "user-store",
            "changes_made": ["Updated port to standardized value", "Fixed environment variable naming"],
            "warnings": ["Consider using newer configuration format"],
            "errors": [],
            "issues": [
                {
                    "service": "user-store",
                    "type": "port_standardization",
                    "severity": "warning",
                    "description": "Port updated from 8000 to 5150 (standardized)",
                    "can_auto_fix": True
                },
                {
                    "service": "user-store",
                    "type": "env_var_standardization",
                    "severity": "info",
                    "description": "Environment variable naming standardized",
                    "can_auto_fix": True
                }
            ]
        }

        with patch('api.routes.meta_orchestrator', mock_orchestrator), \
             patch('api.routes.monitoring_service', mock_monitoring_service):

            mock_monitoring_service.standardize_service_config.return_value = mock_result

            response = client.post("/api/v1/audit/config/standardize/service/user-store")

            assert response.status_code == 200
            data = response.json()
            assert "config_standardization" in data

            result = data["config_standardization"]
            assert result["success"] == True
            assert result["service_name"] == "user-store"
            assert len(result["changes_made"]) == 2
            assert len(result["issues"]) == 2

    def test_config_standardization_all_services(self, client, mock_orchestrator, mock_monitoring_service):
        """Test configuration standardization for all services"""
        mock_result = {
            "success": True,
            "services_processed": 8,
            "services_standardized": 6,
            "total_issues": 12,
            "fixes_applied": 9,
            "standardization_rate": 0.75,
            "issue_breakdown": {
                "port_standardization": 4,
                "env_var_standardization": 3,
                "config_format": 3,
                "missing_config": 2
            },
            "results": [
                {
                    "service_name": "user-store",
                    "success": True,
                    "changes_made": ["Port standardized", "Environment variables updated"],
                    "warnings": [],
                    "errors": []
                },
                {
                    "service_name": "doc_store",
                    "success": True,
                    "changes_made": ["Configuration file created"],
                    "warnings": ["Using default configuration"],
                    "errors": []
                }
            ]
        }

        with patch('api.routes.meta_orchestrator', mock_orchestrator), \
             patch('api.routes.monitoring_service', mock_monitoring_service):

            mock_monitoring_service.standardize_all_configs.return_value = mock_result

            response = client.post("/api/v1/audit/config/standardize/all")

            assert response.status_code == 200
            data = response.json()
            assert "config_standardization" in data

            result = data["config_standardization"]
            assert result["success"] == True
            assert result["services_processed"] == 8
            assert result["services_standardized"] == 6
            assert result["standardization_rate"] == 0.75
            assert len(result["results"]) == 2

    def test_docker_standardization(self, client, mock_orchestrator, mock_monitoring_service):
        """Test Docker configuration standardization"""
        mock_result = {
            "success": True,
            "files_processed": 3,
            "files_modified": 2,
            "issues_found": 8,
            "issues_fixed": 5,
            "validation_errors": 0,
            "pydantic_validation_passed": True,
            "issues": [
                {
                    "service": "api-backend",
                    "type": "port_mapping",
                    "severity": "warning",
                    "description": "Service should expose standardized port 8000",
                    "can_auto_fix": False
                },
                {
                    "service": "database",
                    "type": "environment_format",
                    "severity": "info",
                    "description": "Environment variables should use dictionary format",
                    "can_auto_fix": True
                },
                {
                    "service": "web-frontend",
                    "type": "missing_healthcheck",
                    "severity": "warning",
                    "description": "Dockerfile should include HEALTHCHECK directive",
                    "can_auto_fix": False
                }
            ]
        }

        with patch('api.routes.meta_orchestrator', mock_orchestrator), \
             patch('api.routes.monitoring_service', mock_monitoring_service):

            mock_monitoring_service.standardize_docker_configs.return_value = mock_result

            response = client.post("/api/v1/audit/docker/standardize")

            assert response.status_code == 200
            data = response.json()
            assert "docker_standardization" in data

            result = data["docker_standardization"]
            assert result["success"] == True
            assert result["files_processed"] == 3
            assert result["files_modified"] == 2
            assert result["issues_found"] == 8
            assert result["issues_fixed"] == 5
            assert len(result["issues"]) == 3

    def test_audit_endpoints_with_validation_errors(self, client, mock_orchestrator, mock_monitoring_service):
        """Test audit endpoints handle validation errors gracefully"""
        # Test with invalid service name
        with patch('api.routes.meta_orchestrator', mock_orchestrator), \
             patch('api.routes.monitoring_service', mock_monitoring_service):

            mock_monitoring_service.standardize_service_config.side_effect = Exception("Service not found")

            response = client.post("/api/v1/audit/config/standardize/service/invalid-service")

            assert response.status_code == 500
            data = response.json()
            assert "detail" in data

    def test_audit_endpoints_parameter_validation(self, client, mock_orchestrator, mock_monitoring_service):
        """Test audit endpoints validate parameters correctly"""
        # Test production readiness with different target levels
        mock_result = {"success": True, "overall_readiness": "testing_ready"}

        with patch('api.routes.meta_orchestrator', mock_orchestrator), \
             patch('api.routes.monitoring_service', mock_monitoring_service):

            mock_monitoring_service.validate_production_readiness.return_value = mock_result

            # Test different target levels
            for target in ["development_ready", "testing_ready", "production_ready"]:
                response = client.post(f"/api/v1/audit/production-readiness/validate?target_level={target}")
                assert response.status_code == 200

                data = response.json()
                assert "production_readiness" in data

    def test_audit_endpoints_response_structure_docker_compose(self, client, mock_orchestrator, mock_monitoring_service):
        """Test Docker Compose validation response structure"""
        mock_result = {"success": True, "services_count": 5, "issues": []}

        with patch('api.routes.meta_orchestrator', mock_orchestrator), \
             patch('api.routes.monitoring_service', mock_monitoring_service):

            mock_monitoring_service.validate_docker_compose.return_value = mock_result

            response = client.post("/api/v1/audit/docker-compose/validate")
            assert response.status_code == 200

            data = response.json()
            assert "docker_compose_validation" in data
            result = data["docker_compose_validation"]

            assert "success" in result
            assert "services_count" in result
            assert "issues" in result

    def test_audit_endpoints_response_structure_config_drift(self, client, mock_orchestrator, mock_monitoring_service):
        """Test configuration drift detection response structure"""
        mock_result = {"success": True, "total_issues": 3, "issues": []}

        with patch('api.routes.meta_orchestrator', mock_orchestrator), \
             patch('api.routes.monitoring_service', mock_monitoring_service):

            mock_monitoring_service.detect_configuration_drift.return_value = mock_result

            response = client.post("/api/v1/audit/config/drift-detect")
            assert response.status_code == 200

            data = response.json()
            assert "configuration_drift" in data
            result = data["configuration_drift"]

            assert "success" in result
            assert "total_issues" in result
            assert "issues" in result

    def test_audit_endpoints_response_structure_production_readiness(self, client, mock_orchestrator, mock_monitoring_service):
        """Test production readiness validation response structure"""
        mock_result = {"success": True, "overall_readiness": "development_ready", "results": []}

        with patch('api.routes.meta_orchestrator', mock_orchestrator), \
             patch('api.routes.monitoring_service', mock_monitoring_service):

            mock_monitoring_service.validate_production_readiness.return_value = mock_result

            response = client.post("/api/v1/audit/production-readiness/validate")
            assert response.status_code == 200

            data = response.json()
            assert "production_readiness" in data
            result = data["production_readiness"]

            assert "success" in result
            assert "overall_readiness" in result
            assert "results" in result

    def test_audit_endpoints_response_structure_config_standardization(self, client, mock_orchestrator, mock_monitoring_service):
        """Test configuration standardization response structure"""
        mock_result = {"success": True, "services_processed": 8, "results": []}

        with patch('api.routes.meta_orchestrator', mock_orchestrator), \
             patch('api.routes.monitoring_service', mock_monitoring_service):

            mock_monitoring_service.standardize_all_configs.return_value = mock_result

            response = client.post("/api/v1/audit/config/standardize/all")
            assert response.status_code == 200

            data = response.json()
            assert "config_standardization" in data
            result = data["config_standardization"]

            assert "success" in result
            assert "services_processed" in result
            assert "results" in result

    def test_audit_endpoints_response_structure_docker_standardization(self, client, mock_orchestrator, mock_monitoring_service):
        """Test Docker standardization response structure"""
        mock_result = {"success": True, "files_processed": 3, "issues": []}

        with patch('api.routes.meta_orchestrator', mock_orchestrator), \
             patch('api.routes.monitoring_service', mock_monitoring_service):

            mock_monitoring_service.standardize_docker_configs.return_value = mock_result

            response = client.post("/api/v1/audit/docker/standardize")
            assert response.status_code == 200

            data = response.json()
            assert "docker_standardization" in data
            result = data["docker_standardization"]

            assert "success" in result
            assert "files_processed" in result
            assert "issues" in result
