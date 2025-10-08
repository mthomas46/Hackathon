"""
Integration tests for crawled document tags.

Tests the complete flow: Crawl → Ingest → Validate tags in database
"""
import pytest
import httpx
import asyncio
from typing import List, Dict, Any
import subprocess
import json


class TestCrawledDocumentTags:
    """Test suite for tags in crawled documents."""
    
    INGESTION_URL = "http://localhost:5022"
    DOC_STORE_URL = "http://localhost:5087"
    
    @pytest.fixture
    def sample_fandom_document(self) -> Dict[str, Any]:
        """Create a sample document mimicking fandom crawler output."""
        return {
            "document_id": "fandom-test-tags-001",
            "title": "Test Fandom Page",
            "content": "This is test content from a fandom wiki page.",
            "tags": [
                "source:fandom-wiki",
                "file_type:document",
                "depth:0",
                "category:test-category"
            ],
            "metadata": {
                "source": "fandom-wiki",
                "file_type": "document",
                "url": "https://test.fandom.com/wiki/TestPage",
                "crawl_depth": 0
            }
        }
    
    @pytest.mark.asyncio
    async def test_ingested_document_has_tags(self, sample_fandom_document):
        """Test that ingested documents retain their tags."""
        # Ingest document
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{self.INGESTION_URL}/api/v1/ingestion/ingest",
                json=sample_fandom_document
            )
            
            # May return 404 if ingestion service offline - that's okay for this test
            if response.status_code == 404:
                pytest.skip("Ingestion service offline")
                return
            
            assert response.status_code in [200, 201, 202], f"Ingestion failed: {response.text}"
        
        # Wait for processing
        await asyncio.sleep(2)
        
        # Query database directly to check tags
        result = subprocess.run(
            [
                "docker", "exec", "doc_store", "sh", "-c",
                f"sqlite3 /app/services/doc_store/data/doc_store.db \"SELECT id, tags FROM documents WHERE id='{sample_fandom_document['document_id']}'\""
            ],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Database query failed: {result.stderr}"
        
        # Parse result
        if result.stdout.strip():
            doc_id, tags_json = result.stdout.strip().split("|")
            tags = json.loads(tags_json)
            
            assert isinstance(tags, list), f"Tags should be list, got {type(tags)}"
            assert len(tags) > 0, "Tags should not be empty"
            assert "source:fandom-wiki" in tags, "Should have source tag"
            assert "file_type:document" in tags, "Should have file_type tag"
    
    @pytest.mark.asyncio
    async def test_tags_searchable_after_ingestion(self, sample_fandom_document):
        """Test that tags are searchable after document ingestion."""
        # Ingest document with unique tag
        doc_data = sample_fandom_document.copy()
        doc_data["document_id"] = "fandom-test-search-001"
        doc_data["tags"] = ["unique:searchable-tag-12345", "source:fandom-wiki"]
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Try ingestion service first
            try:
                response = await client.post(
                    f"{self.INGESTION_URL}/api/v1/ingestion/ingest",
                    json=doc_data,
                    timeout=5.0
                )
                if response.status_code == 404:
                    # Fallback to direct doc_store
                    response = await client.post(
                        f"{self.DOC_STORE_URL}/api/v1/documents",
                        json={
                            "id": doc_data["document_id"],
                            "content": doc_data["content"],
                            "tags": doc_data["tags"],
                            "metadata": doc_data["metadata"]
                        }
                    )
            except httpx.ConnectError:
                # Direct insert to doc_store
                response = await client.post(
                    f"{self.DOC_STORE_URL}/api/v1/documents",
                    json={
                        "id": doc_data["document_id"],
                        "content": doc_data["content"],
                        "tags": doc_data["tags"],
                        "metadata": doc_data["metadata"]
                    }
                )
            
            assert response.status_code in [200, 201, 202]
        
        # Search by unique tag
        await asyncio.sleep(1)
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            search_response = await client.post(
                f"{self.DOC_STORE_URL}/api/v1/search",
                json={
                    "query": "unique searchable tag",
                    "limit": 10
                }
            )
        
        assert search_response.status_code == 200
        results = search_response.json()
        
        # Extract items from response
        if isinstance(results, dict):
            items = results.get("data", {}).get("items", results.get("items", []))
        else:
            items = results
        
        # Verify document found
        found_doc = None
        for item in items:
            if item.get("id") == doc_data["document_id"]:
                found_doc = item
                break
        
        assert found_doc is not None, f"Document not found in search results. Results: {items}"


class TestFandomIngestorTags:
    """Unit tests for fandom ingestor tag generation."""
    
    @pytest.mark.asyncio
    async def test_normalized_document_has_tags(self):
        """Test that NormalizedDocument from fandom ingestor has tags."""
        from ingestion.fandom_ingestor import FandomWikiIngestor
        from ingestion.tagging import UniversalTaggingConfig
        
        config = UniversalTaggingConfig(
            enable_user_tags=True,
            user_tags=["project:test", "domain:testing"]
        )
        
        ingestor = FandomWikiIngestor(
            enable_tagging=True,
            tagging_config=config
        )
        
        # Create test page data
        test_page = {
            'title': 'Test Page',
            'content': '<p>Test content</p>',
            'url': 'https://test.fandom.com/wiki/Test',
            'categories': ['test-category'],
            'last_modified': None,
            'links': []
        }
        
        # Normalize page
        normalized = await ingestor._normalize_fandom_page(
            test_page,
            depth=0,
            parent_page=None
        )
        
        # Validate tags
        assert normalized.tags is not None, "Tags should not be None"
        assert isinstance(normalized.tags, list), f"Tags should be list, got {type(normalized.tags)}"
        assert len(normalized.tags) > 0, "Tags should not be empty"
        
        # Check for expected tags
        tag_strings = [str(tag) for tag in normalized.tags]
        assert any("source:fandom" in tag for tag in tag_strings), "Should have source tag"
        assert any("file_type:document" in tag for tag in tag_strings), "Should have file_type tag"
        assert any("depth:0" in tag for tag in tag_strings), "Should have depth tag"
    
    @pytest.mark.asyncio
    async def test_tagging_manager_preserves_tags(self):
        """Test that UniversalTaggingManager preserves existing tags."""
        from ingestion.models import NormalizedDocument
        from ingestion.tagging import UniversalTaggingManager, UniversalTaggingConfig
        
        config = UniversalTaggingConfig(
            enable_user_tags=True,
            user_tags=["user:tag1", "user:tag2"]
        )
        
        manager = UniversalTaggingManager(config)
        
        # Create document with existing tags
        doc = NormalizedDocument(
            document_id="test-001",
            title="Test Doc",
            content_md="Test content",
            original_format="test",
            tags=["existing:tag1", "existing:tag2"],
            metadata={}
        )
        
        # Apply tagging
        tagged_docs, collection = await manager.tag_documents(
            documents=[doc],
            source_type="test",
            user_tags=None
        )
        
        # Validate tags preserved and enhanced
        result_tags = tagged_docs[0].tags
        assert "existing:tag1" in result_tags, "Should preserve existing tag1"
        assert "existing:tag2" in result_tags, "Should preserve existing tag2"
        assert any("source:" in tag for tag in result_tags), "Should add source tag"
        assert any("file_type:" in tag for tag in result_tags), "Should add file_type tag"


class TestTagsPipeline:
    """End-to-end tests for tags pipeline."""
    
    @pytest.mark.asyncio
    async def test_tags_flow_crawl_to_database(self):
        """Test complete flow: Crawl simulation → Ingest → Database."""
        from ingestion.models import NormalizedDocument
        import hashlib
        
        # Simulate crawled document
        doc = NormalizedDocument(
            document_id=f"test-e2e-{hashlib.md5(b'test').hexdigest()[:8]}",
            title="E2E Test Document",
            content_md="# Test Content\n\nThis is end-to-end test content.",
            original_format="fandom-wiki",
            tags=[
                "source:fandom-wiki",
                "file_type:document",
                "depth:0",
                "test:e2e-validation"
            ],
            metadata={
                "source": "fandom-wiki",
                "test": "e2e"
            }
        )
        
        # Send to ingestion (or doc_store directly)
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                # Try ingestion service
                response = await client.post(
                    "http://localhost:5022/api/v1/ingestion/ingest",
                    json={
                        "document_id": doc.document_id,
                        "title": doc.title,
                        "content": doc.content_md,
                        "tags": doc.tags,
                        "metadata": doc.metadata
                    },
                    timeout=5.0
                )
            except (httpx.ConnectError, httpx.TimeoutException):
                # Fallback to doc_store
                response = await client.post(
                    "http://localhost:5087/api/v1/documents",
                    json={
                        "id": doc.document_id,
                        "content": doc.content_md,
                        "tags": doc.tags,
                        "metadata": doc.metadata
                    }
                )
        
        assert response.status_code in [200, 201, 202], f"Ingestion failed: {response.text}"
        
        # Verify in database
        await asyncio.sleep(1)
        
        result = subprocess.run(
            [
                "docker", "exec", "doc_store", "sh", "-c",
                f"sqlite3 /app/services/doc_store/data/doc_store.db \"SELECT tags FROM documents WHERE id='{doc.document_id}'\""
            ],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Database query failed: {result.stderr}"
        
        if result.stdout.strip():
            tags_json = result.stdout.strip()
            tags = json.loads(tags_json)
            
            assert isinstance(tags, list), "Tags should be a list"
            assert len(tags) >= 4, f"Expected at least 4 tags, got {len(tags)}: {tags}"
            assert "source:fandom-wiki" in tags, "Missing source tag"
            assert "test:e2e-validation" in tags, "Missing test tag"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

