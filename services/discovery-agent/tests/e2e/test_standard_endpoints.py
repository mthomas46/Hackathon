"""
End-to-end tests for standard endpoints.

These tests verify the 4 required standard endpoints:
- /health
- /about-me
- /endpoints
- /provider-consumer
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.e2e
@pytest.mark.api
class TestHealthEndpoint:
    """Test /health endpoint."""
    
    def test_health_endpoint_returns_200(self, test_client):
        """Test that /health endpoint returns 200 OK."""
        response = test_client.get("/health")
        assert response.status_code == 200
    
    def test_health_endpoint_returns_correct_data(self, test_client):
        """Test that /health returns correct health information."""
        response = test_client.get("/health")
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["service"] == "discovery-agent"
        assert "version" in data
        assert "timestamp" in data
        assert "uptime_seconds" in data


@pytest.mark.e2e
@pytest.mark.api
class TestAboutMeEndpoint:
    """Test /about-me endpoint."""
    
    def test_about_me_endpoint_exists(self, test_client):
        """Test that /about-me endpoint exists and returns 200."""
        response = test_client.get("/about-me")
        assert response.status_code == 200
    
    def test_about_me_returns_service_info(self, test_client):
        """Test that /about-me returns comprehensive service information."""
        response = test_client.get("/about-me")
        data = response.json()
        
        # Core fields
        assert data["service"] == "discovery-agent"
        assert "version" in data
        assert "description" in data
        
        # Capabilities
        assert "capabilities" in data
        assert isinstance(data["capabilities"], list)
        assert len(data["capabilities"]) > 0
        
        # Features
        assert "features" in data
        assert isinstance(data["features"], dict)
        
        # Ecosystem info
        assert "ecosystem_role" in data
        assert data["ecosystem_role"] == "integration"
        assert "tier" in data
        assert data["tier"] == 3
        
        # Dependencies
        assert "dependencies" in data
        dependencies = data["dependencies"]
        assert "providers" in dependencies
        assert "consumers" in dependencies
        
        # Architecture
        assert "architecture" in data
        architecture = data["architecture"]
        assert architecture["pattern"] == "DDD"
        assert "layers" in architecture
        assert "patterns" in architecture
    
    def test_about_me_includes_quality_metrics(self, test_client):
        """Test that /about-me includes quality metrics."""
        response = test_client.get("/about-me")
        data = response.json()
        
        assert "quality_metrics" in data
        metrics = data["quality_metrics"]
        assert "test_coverage" in metrics
        assert "total_tests" in metrics


@pytest.mark.e2e
@pytest.mark.api
class TestEndpointsListEndpoint:
    """Test /endpoints endpoint."""
    
    def test_endpoints_list_returns_200(self, test_client):
        """Test that /endpoints returns 200 OK."""
        response = test_client.get("/endpoints")
        assert response.status_code == 200
    
    def test_endpoints_lists_all_endpoints(self, test_client):
        """Test that /endpoints lists all available endpoints."""
        response = test_client.get("/endpoints")
        data = response.json()
        
        # Core fields
        assert data["service"] == "discovery-agent"
        assert "version" in data
        assert "base_url" in data
        
        # Endpoints list
        assert "endpoints" in data
        endpoints = data["endpoints"]
        assert isinstance(endpoints, list)
        assert len(endpoints) >= 6  # At least 6 endpoints
        
        # Check that standard endpoints are listed
        endpoint_paths = [e["path"] for e in endpoints]
        assert "/health" in endpoint_paths
        assert "/about-me" in endpoint_paths
        assert "/endpoints" in endpoint_paths
        assert "/provider-consumer" in endpoint_paths
        assert "/api/v1/discover" in endpoint_paths
        assert "/api/v1/discover/tools" in endpoint_paths
    
    def test_endpoints_have_required_fields(self, test_client):
        """Test that each endpoint has required fields."""
        response = test_client.get("/endpoints")
        data = response.json()
        
        endpoints = data["endpoints"]
        for endpoint in endpoints:
            assert "path" in endpoint
            assert "methods" in endpoint
            assert isinstance(endpoint["methods"], list)
            assert "description" in endpoint
            assert "authentication" in endpoint
            assert "category" in endpoint
    
    def test_endpoints_include_categories(self, test_client):
        """Test that endpoints are categorized."""
        response = test_client.get("/endpoints")
        data = response.json()
        
        assert "categories" in data
        categories = data["categories"]
        assert "standard" in categories
        assert categories["standard"] >= 4  # 4 standard endpoints
        assert "core" in categories
        
        assert "total_endpoints" in data
        assert data["total_endpoints"] >= 6


@pytest.mark.e2e
@pytest.mark.api
class TestProviderConsumerEndpoint:
    """Test /provider-consumer endpoint."""
    
    def test_provider_consumer_returns_200(self, test_client):
        """Test that /provider-consumer returns 200 OK."""
        response = test_client.get("/provider-consumer")
        assert response.status_code == 200
    
    def test_provider_consumer_shows_relationships(self, test_client):
        """Test that /provider-consumer shows service relationships."""
        response = test_client.get("/provider-consumer")
        data = response.json()
        
        # Core fields
        assert data["service"] == "discovery-agent"
        assert "version" in data
        
        # Relationships
        assert "relationships" in data
        relationships = data["relationships"]
        
        assert "providers" in relationships
        assert "consumers" in relationships
        assert "provide_consume" in relationships
        
        # Check providers
        providers = relationships["providers"]
        assert isinstance(providers, list)
        # Should have at least orchestrator as provider
        provider_names = [p["service"] for p in providers]
        assert "orchestrator" in provider_names
    
    def test_provider_consumer_shows_provider_details(self, test_client):
        """Test that provider relationships have detailed information."""
        response = test_client.get("/provider-consumer")
        data = response.json()
        
        providers = data["relationships"]["providers"]
        
        for provider in providers:
            assert "service" in provider
            assert "relationship" in provider
            assert "purpose" in provider
            assert "endpoints_used" in provider or "data_consumed" in provider
    
    def test_provider_consumer_shows_consumer_details(self, test_client):
        """Test that consumer relationships have detailed information."""
        response = test_client.get("/provider-consumer")
        data = response.json()
        
        consumers = data["relationships"]["consumers"]
        assert isinstance(consumers, list)
        
        for consumer in consumers:
            assert "service" in consumer
            assert "relationship" in consumer
            assert "purpose" in consumer
    
    def test_provider_consumer_includes_dependencies(self, test_client):
        """Test that /provider-consumer includes dependency information."""
        response = test_client.get("/provider-consumer")
        data = response.json()
        
        assert "dependencies" in data
        dependencies = data["dependencies"]
        
        assert "external_apis" in dependencies
        assert "databases" in dependencies
        assert "message_queues" in dependencies
        assert "cache_systems" in dependencies
    
    def test_provider_consumer_includes_data_flow(self, test_client):
        """Test that /provider-consumer includes data flow information."""
        response = test_client.get("/provider-consumer")
        data = response.json()
        
        assert "provides_data_to" in data
        assert "consumes_data_from" in data
        
        assert isinstance(data["provides_data_to"], list)
        assert isinstance(data["consumes_data_from"], list)
        
        # Discovery-agent provides data to orchestrator
        assert "orchestrator" in data["provides_data_to"]
    
    def test_provider_consumer_self_contained_flag(self, test_client):
        """Test that /provider-consumer indicates if service is self-contained."""
        response = test_client.get("/provider-consumer")
        data = response.json()
        
        assert "self_contained" in data
        # Discovery-agent requires orchestrator, so not self-contained
        assert data["self_contained"] is False


@pytest.mark.e2e
@pytest.mark.api
class TestStandardEndpointsConsistency:
    """Test consistency across standard endpoints."""
    
    def test_all_standard_endpoints_return_service_name(self, test_client):
        """Test that all standard endpoints return consistent service name."""
        endpoints = ["/health", "/about-me", "/endpoints", "/provider-consumer"]
        
        for endpoint in endpoints:
            response = test_client.get(endpoint)
            assert response.status_code == 200
            data = response.json()
            assert "service" in data
            assert data["service"] == "discovery-agent"
    
    def test_all_standard_endpoints_return_version(self, test_client):
        """Test that all standard endpoints return consistent version."""
        endpoints = ["/health", "/about-me", "/endpoints", "/provider-consumer"]
        
        versions = []
        for endpoint in endpoints:
            response = test_client.get(endpoint)
            assert response.status_code == 200
            data = response.json()
            if "version" in data:
                versions.append(data["version"])
        
        # All versions should be the same
        if versions:
            assert all(v == versions[0] for v in versions)
    
    def test_all_standard_endpoints_return_json(self, test_client):
        """Test that all standard endpoints return JSON."""
        endpoints = ["/health", "/about-me", "/endpoints", "/provider-consumer"]
        
        for endpoint in endpoints:
            response = test_client.get(endpoint)
            assert response.status_code == 200
            assert response.headers["content-type"] == "application/json"
    
    def test_standard_endpoints_no_authentication_required(self, test_client):
        """Test that standard endpoints don't require authentication."""
        endpoints = ["/health", "/about-me", "/endpoints", "/provider-consumer"]
        
        for endpoint in endpoints:
            # Should work without any authentication headers
            response = test_client.get(endpoint)
            assert response.status_code == 200

