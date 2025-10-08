"""
Integration tests for GET endpoint fix.

Tests the complete flow: POST document → GET document → Validate response
"""
import pytest
import httpx
import json
from typing import Dict, Any


class TestGetEndpointFix:
    """Test suite for GET endpoint functionality."""
    
    BASE_URL = "http://localhost:5087"
    
    @pytest.fixture
    def test_document(self) -> Dict[str, Any]:
        """Return test document data (document will be created in test)."""
        return {
            "id": "test-get-endpoint-001",
            "content": "Test content for GET endpoint validation",
            "tags": ["test:get", "endpoint:validation", "priority:high"],
            "metadata": {
                "test": "get_endpoint",
                "created_by": "test_suite"
            }
        }
    
    @pytest.mark.asyncio
    async def test_get_document_returns_200(self, test_document):
        """Test that GET endpoint returns 200 OK."""
        # Create document first
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(
                f"{self.BASE_URL}/api/v1/documents",
                json=test_document
            )
        
        doc_id = test_document["id"]
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{self.BASE_URL}/api/v1/documents/{doc_id}"
            )
            
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    @pytest.mark.asyncio
    async def test_get_document_returns_correct_data(self, test_document):
        """Test that GET endpoint returns correct document data."""
        # Create document first
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(
                f"{self.BASE_URL}/api/v1/documents",
                json=test_document
            )
        
        doc_id = test_document["id"]
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{self.BASE_URL}/api/v1/documents/{doc_id}"
            )
            
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert "success" in data or "data" in data, "Response missing success/data field"
        
        # Extract actual document data
        doc_data = data.get("data", data)
        
        # Validate fields
        assert doc_data["id"] == doc_id, f"ID mismatch: {doc_data['id']} != {doc_id}"
        assert doc_data["content"] == test_document["content"], "Content mismatch"
        assert doc_data["tags"] is not None, "Tags should not be null"
        assert isinstance(doc_data["tags"], list), f"Tags should be list, got {type(doc_data['tags'])}"
        assert len(doc_data["tags"]) == 3, f"Expected 3 tags, got {len(doc_data['tags'])}"
    
    @pytest.mark.asyncio
    async def test_get_document_tags_match_posted(self, test_document):
        """Test that tags returned by GET match tags from POST."""
        # Create document first
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(
                f"{self.BASE_URL}/api/v1/documents",
                json=test_document
            )
        
        doc_id = test_document["id"]
        expected_tags = set(test_document["tags"])
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{self.BASE_URL}/api/v1/documents/{doc_id}"
            )
            
        assert response.status_code == 200
        data = response.json()
        doc_data = data.get("data", data)
        
        actual_tags = set(doc_data["tags"])
        assert actual_tags == expected_tags, f"Tags mismatch: {actual_tags} != {expected_tags}"
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_document_returns_404(self):
        """Test that GET endpoint returns 404 for nonexistent document."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{self.BASE_URL}/api/v1/documents/nonexistent-doc-999"
            )
            
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
    
    @pytest.mark.asyncio
    async def test_get_vs_debug_endpoint_consistency(self, test_document):
        """Test that GET and debug endpoints return consistent data."""
        # Create document first
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(
                f"{self.BASE_URL}/api/v1/documents",
                json=test_document
            )
        
        doc_id = test_document["id"]
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Get from standard endpoint
            get_response = await client.get(
                f"{self.BASE_URL}/api/v1/documents/{doc_id}"
            )
            
            # Get from debug endpoint
            debug_response = await client.get(
                f"{self.BASE_URL}/api/v1/debug/documents/{doc_id}/tags-debug"
            )
        
        assert get_response.status_code == 200, "GET endpoint failed"
        assert debug_response.status_code == 200, "Debug endpoint failed"
        
        get_data = get_response.json().get("data", get_response.json())
        debug_data = debug_response.json()
        
        # Compare tags
        get_tags = set(get_data["tags"])
        debug_tags = set(debug_data["tags_parsed"])
        
        assert get_tags == debug_tags, f"Tag mismatch: GET={get_tags}, DEBUG={debug_tags}"


class TestGetEndpointPerformance:
    """Performance tests for GET endpoint."""
    
    BASE_URL = "http://localhost:5087"
    
    @pytest.mark.asyncio
    async def test_get_endpoint_response_time(self):
        """Test that GET endpoint responds within acceptable time."""
        import time
        
        # Create test document
        doc_data = {
            "id": "test-perf-001",
            "content": "Performance test content",
            "tags": ["perf:test"]
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Create document
            await client.post(
                f"{self.BASE_URL}/api/v1/documents",
                json=doc_data
            )
            
            # Time the GET request
            start = time.time()
            response = await client.get(
                f"{self.BASE_URL}/api/v1/documents/{doc_data['id']}"
            )
            duration = time.time() - start
        
        assert response.status_code == 200
        assert duration < 1.0, f"GET took {duration:.2f}s, should be < 1s"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

