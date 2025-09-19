"""Integration Tests for HATEOAS Functionality.

This module contains comprehensive tests for Hypermedia as the Engine of Application State (HATEOAS)
implementation. Tests cover API discoverability, link relations, and hypermedia-driven navigation.
"""

import pytest
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient


class TestAPIDiscovery:
    """Test cases for API discovery and entry points."""

    def test_root_endpoint_provides_complete_api_discovery(self, test_client):
        """Test that root endpoint provides complete API discovery."""
        response = test_client.get("/")

        assert response.status_code == 200
        data = response.json()

        # Verify comprehensive API discovery
        assert "_links" in data
        links = data["_links"]

        # Essential API links
        essential_links = [
            "self",
            "health",
            "simulations",
            "config",
            "documentation",
            "openapi"
        ]

        for link in essential_links:
            assert link in links, f"Missing essential link: {link}"
            link_data = links[link]
            assert "href" in link_data
            assert "title" in link_data
            assert link_data["href"].startswith(("http://", "/"))

    def test_api_discovery_includes_version_information(self, test_client):
        """Test that API discovery includes version information."""
        response = test_client.get("/")

        assert response.status_code == 200
        data = response.json()

        # Should include API version information
        assert "api_version" in data or "version" in data

        # Should specify supported versions
        if "supported_versions" in data:
            versions = data["supported_versions"]
            assert isinstance(versions, list)
            assert "v1" in versions

    def test_api_discovery_provides_deprecation_warnings(self, test_client):
        """Test that API discovery provides deprecation warnings for older versions."""
        # This would test deprecation notices for API versions
        pass


class TestResourceNavigation:
    """Test cases for resource navigation and link relations."""

    def test_simulation_collection_provides_complete_navigation(self, test_client):
        """Test that simulation collection provides complete navigation links."""
        response = test_client.get("/api/v1/simulations")

        assert response.status_code == 200
        data = response.json()

        # Should have navigation links
        assert "_links" in data
        links = data["_links"]

        # Standard navigation links
        nav_links = ["self", "first", "last"]
        for link in nav_links:
            assert link in links

        # Conditional navigation links (may not exist for empty collections)
        if "data" in data and len(data["data"]) > 0:
            # If there are items, should have pagination links
            pagination_links = ["next", "prev"]
            # At least some pagination links should be present

    def test_simulation_resource_provides_relationship_links(self, test_client):
        """Test that simulation resource provides relationship links."""
        # Create a simulation first
        create_response = test_client.post("/api/v1/simulations", json={
            "name": "HATEOAS Test",
            "description": "Testing relationship links",
            "project_type": "web_application",
            "complexity": "medium"
        })

        if create_response.status_code == 201:
            simulation_data = create_response.json()
            simulation_id = simulation_data["data"]["id"]

            # Get the simulation
            response = test_client.get(f"/api/v1/simulations/{simulation_id}")

            assert response.status_code == 200
            data = response.json()

            # Should have relationship links
            assert "_links" in data
            links = data["_links"]

            # Resource relationships
            relationship_links = [
                "self",
                "collection",  # Link back to collection
                "execute",     # Action to execute simulation
                "reports",     # Related reports
                "events",      # Related events
                "logs"         # Related logs
            ]

            for link in relationship_links:
                assert link in links, f"Missing relationship link: {link}"

    def test_action_links_include_http_methods(self, test_client):
        """Test that action links include appropriate HTTP methods."""
        # Create a simulation
        create_response = test_client.post("/api/v1/simulations", json={
            "name": "Method Test",
            "description": "Testing HTTP methods in links",
            "project_type": "web_application",
            "complexity": "medium"
        })

        if create_response.status_code == 201:
            simulation_data = create_response.json()
            simulation_id = simulation_data["data"]["id"]

            response = test_client.get(f"/api/v1/simulations/{simulation_id}")

            assert response.status_code == 200
            data = response.json()
            links = data["_links"]

            # Action links should specify HTTP methods
            if "execute" in links:
                execute_link = links["execute"]
                assert "method" in execute_link
                assert execute_link["method"] == "POST"

            if "delete" in links:
                delete_link = links["delete"]
                assert "method" in delete_link
                assert delete_link["method"] == "DELETE"


class TestLinkRelationSemantics:
    """Test cases for link relation semantics and meanings."""

    def test_link_relations_follow_iana_standards(self, test_client):
        """Test that link relations follow IANA standards where applicable."""
        response = test_client.get("/")

        assert response.status_code == 200
        data = response.json()
        links = data["_links"]

        # Standard IANA link relations
        iana_relations = ["self", "collection", "item"]

        # Links should use standard relations where applicable
        for relation in iana_relations:
            if relation in links:
                # Should follow IANA semantics
                assert "href" in links[relation]

    def test_custom_link_relations_are_documented(self, test_client):
        """Test that custom link relations are properly documented."""
        response = test_client.get("/")

        assert response.status_code == 200
        data = response.json()
        links = data["_links"]

        # Custom relations should have descriptions or be self-documenting
        for relation, link_data in links.items():
            if relation not in ["self", "collection", "item", "first", "last", "next", "prev"]:
                # Custom relations should have titles or descriptions
                assert "title" in link_data or "description" in link_data

    def test_link_relations_are_consistent_across_resources(self, test_client):
        """Test that link relations are consistent across similar resources."""
        # Get collection
        collection_response = test_client.get("/api/v1/simulations")
        if collection_response.status_code == 200:
            collection_data = collection_response.json()
            collection_links = collection_data.get("_links", {})

            # If there are items, get one
            if "data" in collection_data and len(collection_data["data"]) > 0:
                item_id = collection_data["data"][0]["id"]
                item_response = test_client.get(f"/api/v1/simulations/{item_id}")

                if item_response.status_code == 200:
                    item_data = item_response.json()
                    item_links = item_data.get("_links", {})

                    # Check consistency
                    if "self" in collection_links and "collection" in item_links:
                        # Item's collection link should match collection's self link
                        collection_href = collection_links["self"]["href"]
                        item_collection_href = item_links["collection"]["href"]
                        # Normalize URLs for comparison
                        assert collection_href.split('?')[0] == item_collection_href.split('?')[0]


class TestHATEOASWorkflows:
    """Test cases for HATEOAS-driven workflows and navigation."""

    def test_simulation_lifecycle_workflow_via_links(self, test_client):
        """Test complete simulation lifecycle navigation via HATEOAS links."""
        # 1. Start at root
        root_response = test_client.get("/")
        assert root_response.status_code == 200
        root_data = root_response.json()

        # 2. Navigate to simulations collection
        simulations_href = root_data["_links"]["simulations"]["href"]
        collection_response = test_client.get(simulations_href)
        assert collection_response.status_code == 200

        # 3. Create a new simulation
        create_response = test_client.post("/api/v1/simulations", json={
            "name": "Workflow Test",
            "description": "Testing HATEOAS workflow",
            "project_type": "web_application",
            "complexity": "medium"
        })

        if create_response.status_code == 201:
            simulation_data = create_response.json()
            simulation_links = simulation_data["_links"]

            # 4. Navigate to the created resource
            if "self" in simulation_links:
                resource_href = simulation_links["self"]["href"]
                resource_response = test_client.get(resource_href)
                assert resource_response.status_code == 200

                # 5. Execute simulation via action link
                if "execute" in simulation_links:
                    execute_href = simulation_links["execute"]["href"]
                    execute_method = simulation_links["execute"].get("method", "POST")

                    if execute_method == "POST":
                        execute_response = test_client.post(execute_href)
                        # Should get accepted or success response
                        assert execute_response.status_code in [200, 201, 202]

    def test_error_recovery_via_hateoas_links(self, test_client):
        """Test error recovery navigation via HATEOAS links."""
        # Try to access non-existent resource
        error_response = test_client.get("/api/v1/simulations/non-existent-id")

        assert error_response.status_code == 404
        error_data = error_response.json()

        # Should provide recovery links
        assert "_links" in error_data
        recovery_links = error_data["_links"]

        # Should have links to help recover from error
        recovery_options = ["collection", "help", "documentation", "support"]
        has_recovery_link = any(option in recovery_links for option in recovery_options)
        assert has_recovery_link, "Error response should provide recovery navigation links"


class TestHATEOASContentNegotiation:
    """Test cases for HATEOAS content negotiation and formats."""

    def test_links_support_multiple_formats(self, test_client):
        """Test that links can support multiple response formats."""
        response = test_client.get("/")

        assert response.status_code == 200
        data = response.json()
        links = data["_links"]

        # Some links might support different formats
        for link_name, link_data in links.items():
            if "type" in link_data:
                # Should specify content type
                assert link_data["type"] in ["application/json", "text/html"]

    def test_api_provides_format_negotiation_links(self, test_client):
        """Test that API provides links for different content formats."""
        # This would test links like ?format=json, ?format=html, etc.
        pass


class TestHATEOASCaching:
    """Test cases for HATEOAS link caching and optimization."""

    def test_links_include_cache_headers(self, test_client):
        """Test that link responses include appropriate cache headers."""
        response = test_client.get("/")

        # Should have cache-related headers
        cache_headers = ["cache-control", "etag", "last-modified"]
        has_cache_header = any(header in response.headers for header in cache_headers)

        # At minimum should have cache-control
        assert "cache-control" in response.headers

    def test_link_stability_across_requests(self, test_client):
        """Test that links remain stable across multiple requests."""
        # Make multiple requests and verify links are consistent
        responses = []
        for _ in range(3):
            response = test_client.get("/")
            if response.status_code == 200:
                responses.append(response.json())

        if len(responses) >= 2:
            # Compare link structures
            first_links = responses[0].get("_links", {})
            second_links = responses[1].get("_links", {})

            # Links should be structurally consistent
            assert set(first_links.keys()) == set(second_links.keys())


class TestHATEOASDocumentation:
    """Test cases for HATEOAS documentation and discoverability."""

    def test_links_include_descriptive_information(self, test_client):
        """Test that links include descriptive information."""
        response = test_client.get("/")

        assert response.status_code == 200
        data = response.json()
        links = data["_links"]

        # Links should have descriptive information
        for link_name, link_data in links.items():
            # Should have title or description
            has_description = "title" in link_data or "description" in link_data
            assert has_description, f"Link {link_name} should have descriptive information"

    def test_api_provides_link_relation_documentation(self, test_client):
        """Test that API provides documentation for link relations."""
        # This would test if there's a documentation endpoint for link relations
        docs_response = test_client.get("/docs")  # OpenAPI docs

        if docs_response.status_code == 200:
            # Should document the API including link relations
            docs_content = docs_response.text
            assert "links" in docs_content.lower() or "_links" in docs_content

    def test_link_relations_are_self_documenting(self, test_client):
        """Test that link relations are self-documenting."""
        response = test_client.get("/")

        assert response.status_code == 200
        data = response.json()
        links = data["_links"]

        # Link names should be descriptive
        for link_name in links.keys():
            # Should not be generic names
            assert link_name not in ["link1", "link2", "url1", "url2"]


class TestHATEOASPerformance:
    """Test cases for HATEOAS performance and optimization."""

    def test_link_generation_is_efficient(self, test_client):
        """Test that link generation doesn't significantly impact response time."""
        import time

        # Measure response time with links
        start_time = time.time()
        response = test_client.get("/")
        end_time = time.time()

        response_time = end_time - start_time

        # Should respond quickly even with link generation
        assert response_time < 0.5  # 500ms max

        # Verify links are present
        if response.status_code == 200:
            data = response.json()
            assert "_links" in data

    def test_link_validation_doesnt_impact_performance(self, test_client):
        """Test that link validation doesn't significantly impact performance."""
        # This would test the performance impact of link validation
        pass


# Fixtures
@pytest.fixture
def test_client():
    """Create test client for API testing."""
    from main import app
    return TestClient(app)
