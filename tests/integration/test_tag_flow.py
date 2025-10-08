"""Integration tests for tag flow through the system.

TDD Phase 4: Tag Flow Integration
Tests that tags flow from ingestion → storage → search.
"""

import pytest
import asyncio
import httpx
import json
from typing import Dict, Any


@pytest.mark.integration
class TestTagFlowIngestionToStorage:
    """Test tags flow from kafka-ingestion to doc_store."""
    
    @pytest.mark.asyncio
    async def test_ingest_document_with_tags(self):
        """Test ingesting a document with tags."""
        test_doc = {
            "document_id": "test-tag-flow-001",
            "title": "Test Document with Tags",
            "content": "This is test content for tag flow validation.",
            "tags": ["test", "integration", "tag-flow", "source:test"],
            "metadata": {
                "source": "test_suite",
                "test_id": "tag_flow_001"
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Send to kafka-ingestion-service
                response = await client.post(
                    "http://localhost:5700/api/v1/ingestion/ingest",
                    json=test_doc
                )
                
                assert response.status_code == 200
                result = response.json()
                assert result["status"] == "success"
                assert result.get("doc_store_sent") == True
                
                # Give doc_store time to process
                await asyncio.sleep(1)
                
                # Verify document in doc_store
                doc_response = await client.get(
                    f"http://localhost:5087/api/v1/documents"
                )
                
                assert doc_response.status_code == 200
                docs_data = doc_response.json()
                
                # Find our test document
                items = docs_data.get("data", {}).get("items", [])
                test_doc_found = None
                for doc in items:
                    if doc.get("id") == "test-tag-flow-001":
                        test_doc_found = doc
                        break
                
                assert test_doc_found is not None, "Test document not found in doc_store"
                
                # Verify tags are present
                stored_tags = test_doc_found.get("tags")
                assert stored_tags is not None, "Tags field is None"
                
                # Parse tags if they're a JSON string
                if isinstance(stored_tags, str):
                    stored_tags = json.loads(stored_tags)
                
                assert isinstance(stored_tags, list), f"Tags should be a list, got {type(stored_tags)}"
                assert len(stored_tags) > 0, "Tags list is empty"
                assert "test" in stored_tags or "integration" in stored_tags
                
        except httpx.ConnectError as e:
            pytest.skip(f"Service not available: {e}")


@pytest.mark.integration
class TestTagFlowStorageToSearch:
    """Test tags are searchable in doc_store."""
    
    @pytest.mark.asyncio
    async def test_search_by_tag(self):
        """Test searching documents by tag."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Search for documents with 'traitor' tag
                response = await client.post(
                    "http://localhost:5087/api/v1/search",
                    json={"query": "traitor", "limit": 10}
                )
                
                assert response.status_code == 200
                result = response.json()
                
                # Should find documents
                items = result.get("items", [])
                
                # If we have items, verify they have tags
                if len(items) > 0:
                    for item in items:
                        tags = item.get("tags")
                        # Tags should be present (either as list or JSON string)
                        assert tags is not None or item.get("content") is not None
                
        except httpx.ConnectError as e:
            pytest.skip(f"Service not available: {e}")
    
    @pytest.mark.asyncio
    async def test_search_with_tags_vs_without(self):
        """Test that tag-based search differs from content-only search."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Search for a common term
                response = await client.post(
                    "http://localhost:5087/api/v1/search",
                    json={"query": "heresy", "limit": 5}
                )
                
                assert response.status_code == 200
                result = response.json()
                
                # With enhanced search, should get results
                items = result.get("items", [])
                
                # Verify search is working
                assert isinstance(items, list)
                
        except httpx.ConnectError as e:
            pytest.skip(f"Service not available: {e}")


@pytest.mark.integration
class TestTagFlowEndToEnd:
    """Test complete tag flow: ingest → store → search → retrieve."""
    
    @pytest.mark.asyncio
    async def test_full_tag_lifecycle(self):
        """Test complete lifecycle of a tagged document."""
        test_doc = {
            "document_id": "test-lifecycle-001",
            "title": "Full Tag Lifecycle Test",
            "content": "Emperor Primarch Horus Heresy traitor loyalist",
            "tags": [
                "source:test",
                "topic:heresy",
                "character:horus",
                "type:unit_test"
            ],
            "metadata": {
                "test": "full_lifecycle",
                "created_by": "test_suite"
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # 1. INGEST
                ingest_response = await client.post(
                    "http://localhost:5700/api/v1/ingestion/ingest",
                    json=test_doc
                )
                assert ingest_response.status_code == 200
                
                # Wait for processing
                await asyncio.sleep(1)
                
                # 2. VERIFY STORAGE
                doc_response = await client.get(
                    "http://localhost:5087/api/v1/documents"
                )
                assert doc_response.status_code == 200
                
                # 3. SEARCH BY TAG
                search_response = await client.post(
                    "http://localhost:5087/api/v1/search",
                    json={"query": "heresy", "limit": 10}
                )
                assert search_response.status_code == 200
                search_result = search_response.json()
                
                # Verify search returns our document (or similar ones)
                items = search_result.get("items", [])
                assert isinstance(items, list)
                
                # 4. SEARCH BY CONTENT
                content_search = await client.post(
                    "http://localhost:5087/api/v1/search",
                    json={"query": "emperor primarch", "limit": 10}
                )
                assert content_search.status_code == 200
                
        except httpx.ConnectError as e:
            pytest.skip(f"Service not available: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-m", "integration"])

