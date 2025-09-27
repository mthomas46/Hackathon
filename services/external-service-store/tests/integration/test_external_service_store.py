"""Integration tests for External Service Store."""

import pytest
import os
from httpx import AsyncClient


@pytest.mark.asyncio
class TestExternalServiceStore:
    """Integration tests for the External Service Store."""

    @pytest.fixture(autouse=True)
    async def cleanup_db(self):
        """Clean up test database before each test."""
        db_path = "data/external_service_store.db"
        if os.path.exists(db_path):
            os.remove(db_path)
        yield
        if os.path.exists(db_path):
            os.remove(db_path)

    async def test_create_and_get_service(self, client):
        """Test creating and retrieving a service."""
        service_data = {
            "name": "test-service",
            "display_name": "Test Service",
            "description": "A test service for integration testing",
            "service_type": "api",
            "version": "1.0.0",
            "technologies": ["python", "fastapi"],
            "base_url": "http://localhost:8001",
            "health_endpoint": "/health"
        }

        # Create service
        response = await client.post("/services", json=service_data)
        assert response.status_code == 200

        service = response.json()
        assert service["name"] == "test-service"
        assert service["version"] == "1.0.0"
        assert "python" in service["technologies"]

        service_id = service["id"]

        # Retrieve service
        response = await client.get(f"/services/{service_id}")
        assert response.status_code == 200

        retrieved = response.json()
        assert retrieved["name"] == "test-service"
        assert retrieved["description"] == service_data["description"]

    async def test_add_and_get_endpoints(self, client):
        """Test adding and retrieving service endpoints."""
        # Create service first
        service_data = {
            "name": "api-service",
            "display_name": "API Service",
            "service_type": "api",
            "version": "1.0.0"
        }

        response = await client.post("/services", json=service_data)
        service_id = response.json()["id"]

        # Add endpoint
        endpoint_data = {
            "path": "/users",
            "method": "GET",
            "description": "Get all users",
            "response_contract": {
                "users": [{"id": "string", "name": "string"}]
            },
            "authentication_required": True
        }

        response = await client.post(f"/services/{service_id}/endpoints", json=endpoint_data)
        assert response.status_code == 200

        # Get endpoints
        response = await client.get(f"/services/{service_id}/endpoints")
        assert response.status_code == 200

        endpoints = response.json()
        assert len(endpoints["endpoints"]) == 1
        assert endpoints["endpoints"][0]["path"] == "/users"
        assert endpoints["endpoints"][0]["method"] == "GET"

    async def test_service_dependencies(self, client):
        """Test service dependency management."""
        # Create two services
        service1_data = {
            "name": "dependent-service",
            "display_name": "Dependent Service",
            "service_type": "api",
            "version": "1.0.0"
        }

        service2_data = {
            "name": "dependency-service",
            "display_name": "Dependency Service",
            "service_type": "database",
            "version": "2.0.0"
        }

        response1 = await client.post("/services", json=service1_data)
        service1_id = response1.json()["id"]

        response2 = await client.post("/services", json=service2_data)
        service2_id = response2.json()["id"]

        # Add dependency
        dependency_data = {
            "dependent_service_id": service1_id,
            "dependency_service_id": service2_id,
            "dependency_type": "runtime",
            "version_constraint": ">=2.0.0",
            "description": "Requires database service for data persistence",
            "is_required": True
        }

        response = await client.post("/services/dependencies", json=dependency_data)
        assert response.status_code == 200

        # Get dependencies
        response = await client.get(f"/services/{service1_id}/dependencies")
        assert response.status_code == 200

        dependencies = response.json()
        assert len(dependencies["dependencies"]) == 1
        assert dependencies["dependencies"][0]["dependency_service_id"] == service2_id

        # Get dependents
        response = await client.get(f"/services/{service2_id}/dependents")
        assert response.status_code == 200

        dependents = response.json()
        assert len(dependents["dependents"]) == 1
        assert dependents["dependents"][0]["dependent_service_id"] == service1_id

    async def test_document_relationships(self, client):
        """Test service-document relationship management."""
        # Create service
        service_data = {
            "name": "doc-service",
            "display_name": "Documented Service",
            "service_type": "api",
            "version": "1.0.0"
        }

        response = await client.post("/services", json=service_data)
        service_id = response.json()["id"]

        # Add document relationship
        doc_data = {
            "document_id": "confluence:API_DOCS",
            "document_type": "confluence",
            "relationship_type": "documentation",
            "description": "API documentation for the service",
            "tags": ["api", "documentation"]
        }

        response = await client.post(f"/services/{service_id}/documents", json=doc_data)
        assert response.status_code == 200

        # Get service documents
        response = await client.get(f"/services/{service_id}/documents")
        assert response.status_code == 200

        documents = response.json()
        assert len(documents["documents"]) == 1
        assert documents["documents"][0]["document_id"] == "confluence:API_DOCS"

        # Get services by document
        response = await client.get("/documents/confluence:API_DOCS/services")
        assert response.status_code == 200

        services = response.json()
        assert len(services["services"]) == 1
        assert services["services"][0]["service_id"] == service_id

    async def test_user_relationships(self, client):
        """Test service-user relationship management."""
        # Create service
        service_data = {
            "name": "user-service",
            "display_name": "User-Related Service",
            "service_type": "api",
            "version": "1.0.0"
        }

        response = await client.post("/services", json=service_data)
        service_id = response.json()["id"]

        # Add user relationship
        user_data = {
            "user_id": "john.doe",
            "relationship_type": "maintainer",
            "role": "Lead Developer",
            "permissions": ["read", "write", "admin"]
        }

        response = await client.post(f"/services/{service_id}/users", json=user_data)
        assert response.status_code == 200

        # Get service users
        response = await client.get(f"/services/{service_id}/users")
        assert response.status_code == 200

        users = response.json()
        assert len(users["users"]) == 1
        assert users["users"][0]["user_id"] == "john.doe"
        assert users["users"][0]["relationship_type"] == "maintainer"

        # Get user services
        response = await client.get("/users/john.doe/services")
        assert response.status_code == 200

        services = response.json()
        assert len(services["services"]) == 1
        assert services["services"][0]["service_id"] == service_id

    async def test_topic_relationships(self, client):
        """Test service-topic relationship management."""
        # Create service
        service_data = {
            "name": "topic-service",
            "display_name": "Topic-Related Service",
            "service_type": "api",
            "version": "1.0.0"
        }

        response = await client.post("/services", json=service_data)
        service_id = response.json()["id"]

        # Add topic relationship
        topic_data = {
            "topic": "machine-learning",
            "relevance_score": 90,
            "description": "Core service provides ML capabilities",
            "tags": ["ai", "ml", "prediction"]
        }

        response = await client.post(f"/services/{service_id}/topics", json=topic_data)
        assert response.status_code == 200

        # Get service topics
        response = await client.get(f"/services/{service_id}/topics")
        assert response.status_code == 200

        topics = response.json()
        assert len(topics["topics"]) == 1
        assert topics["topics"][0]["topic"] == "machine-learning"
        assert topics["topics"][0]["relevance_score"] == 90

        # Get services by topic
        response = await client.get("/topics/machine-learning/services")
        assert response.status_code == 200

        services = response.json()
        assert len(services["services"]) == 1
        assert services["services"][0]["service_id"] == service_id

    async def test_service_search_and_discovery(self, client):
        """Test service search and discovery features."""
        # Create multiple services
        services_data = [
            {
                "name": "ml-service",
                "display_name": "Machine Learning Service",
                "description": "Provides ML model training and inference",
                "service_type": "api",
                "version": "1.0.0",
                "technologies": ["python", "tensorflow", "kubernetes"]
            },
            {
                "name": "data-service",
                "display_name": "Data Processing Service",
                "description": "Handles data ingestion and processing",
                "service_type": "api",
                "version": "2.0.0",
                "technologies": ["python", "spark", "hadoop"]
            }
        ]

        service_ids = []
        for service_data in services_data:
            response = await client.post("/services", json=service_data)
            service_ids.append(response.json()["id"])

        # Search services
        response = await client.get("/services/search?q=machine")
        assert response.status_code == 200

        search_results = response.json()
        assert search_results["total_count"] >= 1
        assert "machine" in search_results["query"].lower()

        # Find services by technology
        response = await client.get("/services/by-technology/python")
        assert response.status_code == 200

        tech_results = response.json()
        assert tech_results["total"] >= 2  # Both services use Python

        # Test ecosystem overview
        response = await client.get("/analytics/overview")
        assert response.status_code == 200

        overview = response.json()
        assert "total_services" in overview
        assert "active_services" in overview
        assert "service_types" in overview

    async def test_service_lifecycle(self, client):
        """Test complete service lifecycle management."""
        # Create service
        service_data = {
            "name": "lifecycle-service",
            "display_name": "Lifecycle Test Service",
            "description": "Testing complete service lifecycle",
            "service_type": "api",
            "version": "1.0.0",
            "technologies": ["python", "fastapi"]
        }

        response = await client.post("/services", json=service_data)
        assert response.status_code == 200
        service_id = response.json()["id"]

        # Update service
        update_data = {
            "version": "1.1.0",
            "description": "Updated description for lifecycle test"
        }

        response = await client.put(f"/services/{service_id}", json=update_data)
        assert response.status_code == 200

        updated_service = response.json()
        assert updated_service["version"] == "1.1.0"
        assert "Updated description" in updated_service["description"]

        # Add relationships
        # Add a maintainer
        await client.post(f"/services/{service_id}/users", json={
            "user_id": "maintainer@example.com",
            "relationship_type": "maintainer",
            "role": "Service Owner"
        })

        # Add a topic
        await client.post(f"/services/{service_id}/topics", json={
            "topic": "testing",
            "relevance_score": 80,
            "description": "Service for testing purposes"
        })

        # Verify relationships were added
        service_details = await client.get(f"/services/{service_id}")
        service = service_details.json()

        assert len(service["users"]) == 1
        assert len(service["topics"]) == 1
        assert service["users"][0]["relationship_type"] == "maintainer"
        assert service["topics"][0]["topic"] == "testing"

        # Delete service
        response = await client.delete(f"/services/{service_id}")
        assert response.status_code == 200

        # Verify service is deleted
        response = await client.get(f"/services/{service_id}")
        assert response.status_code == 404
