"""
Integration tests for API endpoints.

Tests FastAPI REST API endpoints using TestClient.
"""

import pytest
from fastapi.testclient import TestClient


# ============================================================================
# Health Endpoint Tests
# ============================================================================

@pytest.mark.integration
@pytest.mark.api
class TestHealthEndpoint:
    """Tests for /health endpoint."""
    
    def test_health_check_returns_200(self, test_client):
        """Test that health endpoint returns 200 OK."""
        response = test_client.get("/health")
        
        assert response.status_code == 200
    
    def test_health_check_response_structure(self, test_client):
        """Test health endpoint response structure."""
        response = test_client.get("/health")
        data = response.json()
        
        assert "status" in data
        assert "service" in data
        assert "version" in data
        assert "timestamp" in data
        assert "uptime_seconds" in data
        assert "dependencies" in data
    
    def test_health_check_status_healthy(self, test_client):
        """Test health endpoint returns healthy status."""
        response = test_client.get("/health")
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["service"] == "data-services-dashboard"
    
    def test_health_check_dependencies(self, test_client):
        """Test health endpoint includes dependency status."""
        response = test_client.get("/health")
        data = response.json()
        
        assert "log_collector" in data["dependencies"]
        assert "ui" in data["dependencies"]
        assert data["dependencies"]["ui"] == "running"


# ============================================================================
# About-Me Endpoint Tests
# ============================================================================

@pytest.mark.integration
@pytest.mark.api
class TestAboutMeEndpoint:
    """Tests for /about-me endpoint."""
    
    def test_about_me_returns_200(self, test_client):
        """Test that about-me endpoint returns 200 OK."""
        response = test_client.get("/about-me")
        
        assert response.status_code == 200
    
    def test_about_me_response_structure(self, test_client):
        """Test about-me endpoint response structure."""
        response = test_client.get("/about-me")
        data = response.json()
        
        # Top-level fields
        assert "service" in data
        assert "version" in data
        assert "type" in data
        assert "description" in data
        assert "interfaces" in data
        assert "capabilities" in data
        assert "dependencies" in data
    
    def test_about_me_interfaces(self, test_client):
        """Test about-me endpoint includes both interfaces."""
        response = test_client.get("/about-me")
        data = response.json()
        
        assert "web_ui" in data["interfaces"]
        assert "rest_api" in data["interfaces"]
        
        web_ui = data["interfaces"]["web_ui"]
        assert web_ui["type"] == "streamlit"
        assert web_ui["port"] == 8501
        
        rest_api = data["interfaces"]["rest_api"]
        assert rest_api["type"] == "rest"
        assert rest_api["port"] == 8080
    
    def test_about_me_capabilities(self, test_client):
        """Test about-me endpoint lists capabilities."""
        response = test_client.get("/about-me")
        data = response.json()
        
        assert isinstance(data["capabilities"], list)
        assert len(data["capabilities"]) > 0
    
    def test_about_me_dependencies(self, test_client):
        """Test about-me endpoint lists dependencies."""
        response = test_client.get("/about-me")
        data = response.json()
        
        assert "providers" in data["dependencies"]
        assert "consumers" in data["dependencies"]
        
        # Check log-collector is listed as provider
        providers = data["dependencies"]["providers"]
        log_collector = next((p for p in providers if p["service"] == "log-collector"), None)
        assert log_collector is not None
        assert log_collector["port"] == 8104


# ============================================================================
# Endpoints Listing Tests
# ============================================================================

@pytest.mark.integration
@pytest.mark.api
class TestEndpointsListing:
    """Tests for /endpoints endpoint."""
    
    def test_endpoints_returns_200(self, test_client):
        """Test that endpoints endpoint returns 200 OK."""
        response = test_client.get("/endpoints")
        
        assert response.status_code == 200
    
    def test_endpoints_response_structure(self, test_client):
        """Test endpoints endpoint response structure."""
        response = test_client.get("/endpoints")
        data = response.json()
        
        assert "service" in data
        assert "version" in data
        assert "base_url" in data
        assert "endpoints" in data
        assert "total_endpoints" in data
        assert "categories" in data
    
    def test_endpoints_lists_all_standard_endpoints(self, test_client):
        """Test that all 5 standard endpoints are listed."""
        response = test_client.get("/endpoints")
        data = response.json()
        
        endpoints = data["endpoints"]
        paths = [e["path"] for e in endpoints]
        
        assert "/health" in paths
        assert "/about-me" in paths
        assert "/endpoints" in paths
        assert "/provider-consumer" in paths
        assert "/openapi.json" in paths
    
    def test_endpoints_categorization(self, test_client):
        """Test endpoints are categorized."""
        response = test_client.get("/endpoints")
        data = response.json()
        
        categories = data["categories"]
        
        assert "monitoring" in categories
        assert "metadata" in categories
        assert "documentation" in categories
    
    def test_endpoints_documentation_links(self, test_client):
        """Test endpoints include documentation links."""
        response = test_client.get("/endpoints")
        data = response.json()
        
        assert "documentation" in data
        doc = data["documentation"]
        
        assert "swagger_ui" in doc
        assert "redoc" in doc
        assert "openapi_spec" in doc


# ============================================================================
# Provider-Consumer Endpoint Tests
# ============================================================================

@pytest.mark.integration
@pytest.mark.api
class TestProviderConsumerEndpoint:
    """Tests for /provider-consumer endpoint."""
    
    def test_provider_consumer_returns_200(self, test_client):
        """Test that provider-consumer endpoint returns 200 OK."""
        response = test_client.get("/provider-consumer")
        
        assert response.status_code == 200
    
    def test_provider_consumer_response_structure(self, test_client):
        """Test provider-consumer endpoint response structure."""
        response = test_client.get("/provider-consumer")
        data = response.json()
        
        assert "service" in data
        assert "version" in data
        assert "relationships" in data
        
        relationships = data["relationships"]
        assert "providers" in relationships
        assert "consumers" in relationships
        assert "provide_consume" in relationships
    
    def test_provider_consumer_providers(self, test_client):
        """Test provider-consumer lists providers."""
        response = test_client.get("/provider-consumer")
        data = response.json()
        
        providers = data["relationships"]["providers"]
        
        assert isinstance(providers, list)
        assert len(providers) > 0
        
        # Check log-collector is listed
        log_collector = next((p for p in providers if p["service"] == "log-collector"), None)
        assert log_collector is not None
        assert log_collector["criticality"] == "critical"
    
    def test_provider_consumer_consumers(self, test_client):
        """Test provider-consumer lists consumers."""
        response = test_client.get("/provider-consumer")
        data = response.json()
        
        consumers = data["relationships"]["consumers"]
        
        assert isinstance(consumers, list)
        assert len(consumers) >= 2  # human-operators + monitoring-systems
    
    def test_provider_consumer_network_resilience(self, test_client):
        """Test provider-consumer includes network resilience details."""
        response = test_client.get("/provider-consumer")
        data = response.json()
        
        assert "network_resilience" in data
        resilience = data["network_resilience"]
        
        assert "retry_attempts" in resilience
        assert "initial_delay" in resilience
        assert "backoff_multiplier" in resilience
        assert resilience["retry_attempts"] == 3


# ============================================================================
# OpenAPI Specification Tests
# ============================================================================

@pytest.mark.integration
@pytest.mark.api
class TestOpenAPISpec:
    """Tests for OpenAPI specification."""
    
    def test_openapi_json_returns_200(self, test_client):
        """Test that OpenAPI spec is accessible."""
        response = test_client.get("/openapi.json")
        
        assert response.status_code == 200
    
    def test_openapi_json_structure(self, test_client):
        """Test OpenAPI spec has required fields."""
        response = test_client.get("/openapi.json")
        data = response.json()
        
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data
    
    def test_openapi_includes_all_endpoints(self, test_client):
        """Test OpenAPI spec includes all endpoints."""
        response = test_client.get("/openapi.json")
        data = response.json()
        
        paths = data["paths"]
        
        assert "/health" in paths
        assert "/about-me" in paths
        assert "/endpoints" in paths
        assert "/provider-consumer" in paths


# ============================================================================
# CORS and Headers Tests
# ============================================================================

@pytest.mark.integration
@pytest.mark.api
class TestAPIHeaders:
    """Tests for API headers and CORS."""
    
    def test_health_endpoint_content_type(self, test_client):
        """Test health endpoint returns JSON content type."""
        response = test_client.get("/health")
        
        assert "application/json" in response.headers["content-type"]
    
    def test_all_endpoints_return_json(self, test_client):
        """Test all standard endpoints return JSON."""
        endpoints = ["/health", "/about-me", "/endpoints", "/provider-consumer"]
        
        for endpoint in endpoints:
            response = test_client.get(endpoint)
            assert "application/json" in response.headers["content-type"]

