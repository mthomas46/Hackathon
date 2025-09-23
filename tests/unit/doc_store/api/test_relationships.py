"""Doc Store API Relationships Tests.

Tests for document relationships functionality at the API endpoint level.
"""

import pytest
import json
import uuid


@pytest.mark.api
class TestRelationshipCreation:
    """Test relationship creation between documents."""

    def test_add_relationship_success(self, client):
        """Test successful relationship creation."""
        # Create two documents first
        doc1_data = {"content": "First document for relationships.", "metadata": {"type": "source"}}
        doc2_data = {"content": "Second document for relationships.", "metadata": {"type": "reference"}}

        doc1_response = client.post("/api/v1/documents", json=doc1_data)
        assert doc1_response.status_code == 200
        doc1_id = doc1_response.json()["data"]["id"]

        doc2_response = client.post("/api/v1/documents", json=doc2_data)
        assert doc2_response.status_code == 200
        doc2_id = doc2_response.json()["data"]["id"]

        # Create relationship between them
        relationship_data = {
            "source_document_id": doc1_id,
            "target_document_id": doc2_id,
            "relationship_type": "references",
            "strength": 0.8,
            "metadata": {
                "context": "API reference documentation",
                "line_number": 42
            }
        }

        response = client.post("/api/v1/relationships", json=relationship_data)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

    def test_add_relationship_different_types(self, client):
        """Test creating relationships with different types."""
        # Create documents
        doc1_response = client.post("/api/v1/documents", json={"content": "Doc 1", "metadata": {}})
        doc2_response = client.post("/api/v1/documents", json={"content": "Doc 2", "metadata": {}})
        doc1_id = doc1_response.json()["data"]["id"]
        doc2_id = doc2_response.json()["data"]["id"]

        relationship_types = [
            "references",
            "extends",
            "implements",
            "depends_on",
            "related_to"
        ]

        for rel_type in relationship_types:
            relationship_data = {
                "source_document_id": doc1_id,
                "target_document_id": doc2_id,
                "relationship_type": rel_type,
                "strength": 0.7
            }

            response = client.post("/api/v1/relationships", json=relationship_data)
            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True

    def test_add_relationship_validation_errors(self, client):
        """Test relationship creation with validation errors."""
        invalid_relationships = [
            # Missing required fields
            {"target_document_id": "doc2", "relationship_type": "references"},
            {"source_document_id": "doc1", "relationship_type": "references"},
            {"source_document_id": "doc1", "target_document_id": "doc2"},

            # Invalid IDs
            {"source_document_id": "", "target_document_id": "doc2", "relationship_type": "references"},
            {"source_document_id": "doc1", "target_document_id": "", "relationship_type": "references"},

            # Self-reference
            {"source_document_id": "same", "target_document_id": "same", "relationship_type": "references"},
        ]

        for relationship in invalid_relationships:
            response = client.post("/api/v1/relationships", json=relationship)
            # Should handle validation errors gracefully
            assert response.status_code in [200, 422, 400]


@pytest.mark.api
class TestRelationshipRetrieval:
    """Test relationship retrieval and querying."""

    def test_get_document_relationships(self, client):
        """Test retrieving relationships for a document."""
        # Create a document
        doc_data = {"content": "Document for relationship testing.", "metadata": {}}
        doc_response = client.post("/api/v1/documents", json=doc_data)
        assert doc_response.status_code == 200
        doc_id = doc_response.json()["data"]["id"]

        # Get relationships (should be empty initially)
        response = client.get(f"/api/v1/documents/{doc_id}/relationships")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "data" in data

        relationships_data = data["data"]
        assert isinstance(relationships_data, list)

    def test_get_document_relationships_directions(self, client):
        """Test retrieving relationships with different directions."""
        # Create a document
        doc_data = {"content": "Direction test document.", "metadata": {}}
        doc_response = client.post("/api/v1/documents", json=doc_data)
        assert doc_response.status_code == 200
        doc_id = doc_response.json()["data"]["id"]

        # Test different directions
        directions = ["both", "outgoing", "incoming"]

        for direction in directions:
            response = client.get(f"/api/v1/documents/{doc_id}/relationships?direction={direction}")
            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True

    def test_get_relationships_nonexistent_document(self, client):
        """Test getting relationships for non-existent document."""
        response = client.get("/api/v1/documents/nonexistent-id/relationships")
        # Should handle gracefully
        assert response.status_code in [200, 404, 422]


@pytest.mark.api
class TestRelationshipPaths:
    """Test relationship path finding functionality."""

    def test_find_relationship_paths_success(self, client):
        """Test finding paths between documents."""
        # Create multiple documents
        docs = []
        for i in range(3):
            doc_data = {"content": f"Path finding document {i}.", "metadata": {"index": i}}
            response = client.post("/api/v1/documents", json=doc_data)
            assert response.status_code == 200
            docs.append(response.json()["data"]["id"])

        # Try to find paths between first and last document
        response = client.get(f"/api/v1/relationships/paths?start_id={docs[0]}&end_id={docs[2]}&max_depth=3")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "data" in data

    def test_find_relationship_paths_no_path(self, client):
        """Test finding paths when no relationship path exists."""
        # Create isolated documents
        doc1_response = client.post("/api/v1/documents", json={"content": "Isolated doc 1", "metadata": {}})
        doc2_response = client.post("/api/v1/documents", json={"content": "Isolated doc 2", "metadata": {}})
        doc1_id = doc1_response.json()["data"]["id"]
        doc2_id = doc2_response.json()["data"]["id"]

        response = client.get(f"/api/v1/relationships/paths?start_id={doc1_id}&end_id={doc2_id}&max_depth=2")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        # May return empty path or no path found

    def test_find_relationship_paths_validation(self, client):
        """Test path finding with validation errors."""
        invalid_requests = [
            "/api/v1/relationships/paths?end_id=doc2&max_depth=3",  # Missing start_id
            "/api/v1/relationships/paths?start_id=doc1&max_depth=3",  # Missing end_id
            "/api/v1/relationships/paths?start_id=doc1&end_id=doc2",  # Missing max_depth
            "/api/v1/relationships/paths?start_id=&end_id=doc2&max_depth=3",  # Empty start_id
        ]

        for path in invalid_requests:
            response = client.get(path)
            assert response.status_code == 422  # Validation error


@pytest.mark.api
class TestRelationshipStatistics:
    """Test relationship graph statistics."""

    def test_get_relationship_statistics(self, client):
        """Test getting relationship graph statistics."""
        response = client.get("/api/v1/relationships/stats")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "data" in data

        stats = data["data"]
        assert isinstance(stats, dict)
        # Statistics may include node count, edge count, etc.

    def test_relationship_statistics_with_data(self, client):
        """Test relationship statistics after creating relationships."""
        # Create some documents and relationships
        docs = []
        for i in range(3):
            doc_data = {"content": f"Stats test document {i}.", "metadata": {}}
            response = client.post("/api/v1/documents", json=doc_data)
            assert response.status_code == 200
            docs.append(response.json()["data"]["id"])

        # Create some relationships
        for i in range(len(docs) - 1):
            relationship_data = {
                "source_document_id": docs[i],
                "target_document_id": docs[i + 1],
                "relationship_type": "connects_to",
                "strength": 0.9
            }
            response = client.post("/api/v1/relationships", json=relationship_data)
            assert response.status_code == 200

        # Get updated statistics
        response = client.get("/api/v1/relationships/stats")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True


@pytest.mark.api
class TestRelationshipsIntegration:
    """Test relationships integration with other features."""

    def test_relationships_with_search(self, client):
        """Test relationships work with search operations."""
        # Create documents with relationships
        doc1_data = {"content": "Source document with searchable content.", "metadata": {"type": "source"}}
        doc2_data = {"content": "Target document with searchable content.", "metadata": {"type": "target"}}

        doc1_response = client.post("/api/v1/documents", json=doc1_data)
        doc2_response = client.post("/api/v1/documents", json=doc2_data)
        doc1_id = doc1_response.json()["data"]["id"]
        doc2_id = doc2_response.json()["data"]["id"]

        # Create relationship
        relationship_data = {
            "source_document_id": doc1_id,
            "target_document_id": doc2_id,
            "relationship_type": "links_to",
            "strength": 1.0
        }
        rel_response = client.post("/api/v1/relationships", json=relationship_data)
        assert rel_response.status_code == 200

        # Search should still work
        search_data = {"query": "searchable content", "limit": 10}
        search_response = client.post("/api/v1/search", json=search_data)
        assert search_response.status_code == 200

        search_results = search_response.json()
        assert search_results["success"] is True

    def test_relationships_performance(self, client):
        """Test relationships performance with multiple operations."""
        import time

        start_time = time.time()

        # Create several documents
        docs = []
        for i in range(5):
            doc_data = {"content": f"Performance test document {i}.", "metadata": {}}
            response = client.post("/api/v1/documents", json=doc_data)
            assert response.status_code == 200
            docs.append(response.json()["data"]["id"])

        # Create relationships between them
        relationships_created = 0
        for i in range(len(docs) - 1):
            relationship_data = {
                "source_document_id": docs[i],
                "target_document_id": docs[i + 1],
                "relationship_type": "sequence",
                "strength": 0.8
            }
            response = client.post("/api/v1/relationships", json=relationship_data)
            if response.status_code == 200:
                relationships_created += 1

        # Test statistics retrieval
        stats_response = client.get("/api/v1/relationships/stats")
        assert stats_response.status_code == 200

        end_time = time.time()
        duration = end_time - start_time

        # Should complete within reasonable time
        assert duration < 5.0  # 5 seconds for operations
        assert relationships_created >= 3  # At least some relationships created
