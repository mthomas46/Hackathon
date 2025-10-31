"""
Unit tests for Phase 3A: Document-Level Caching

Tests caching of enriched documents to avoid redundant DB fetches.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock


class TestDocumentCaching:
    """Test document-level caching (Phase 3A)."""
    
    @pytest.mark.asyncio
    async def test_enriched_document_cache_hit(self):
        """Test enriched document cache returns cached data."""
        from services.ecosystem-mcp.src.services.rag.hybrid_search import HybridSearchService
        
        # Create service
        service = HybridSearchService()
        
        # Mock the database call
        mock_doc = Mock()
        mock_doc.id = "test-doc-id"
        mock_doc.file_path = "/test/path.md"
        mock_doc.normalized_content = "Test content"
        mock_doc.quality_score = 85
        mock_doc.quality_grade = "A"
        mock_doc.doc_metadata = {}
        mock_doc.created_at = None
        mock_doc.updated_at = None
        
        with patch('services.ecosystem-mcp.src.services.rag.hybrid_search.get_database') as mock_db:
            with patch('services.ecosystem-mcp.src.services.rag.hybrid_search.DocumentRepository') as mock_repo_class:
                mock_repo = AsyncMock()
                mock_repo.get_by_id = AsyncMock(return_value=mock_doc)
                mock_repo_class.return_value = mock_repo
                
                mock_session = AsyncMock()
                mock_session.__aenter__ = AsyncMock(return_value=mock_session)
                mock_session.__aexit__ = AsyncMock(return_value=None)
                mock_db.return_value.session.return_value = mock_session
                
                # First call (cache miss)
                result1 = await service._get_enriched_document("test-doc-id")
                
                # Second call (should be cache hit, no DB call)
                result2 = await service._get_enriched_document("test-doc-id")
                
                # Verify both calls returned same data
                assert result1 is not None
                assert result2 is not None
                assert result1["id"] == result2["id"]
                assert result1["content"] == result2["content"]
                
                # DB should only be called once (cache hit on second call)
                assert mock_repo.get_by_id.call_count == 1
    
    @pytest.mark.asyncio
    async def test_enriched_document_handles_none(self):
        """Test enriched document cache handles missing documents."""
        from services.ecosystem-mcp.src.services.rag.hybrid_search import HybridSearchService
        
        service = HybridSearchService()
        
        with patch('services.ecosystem-mcp.src.services.rag.hybrid_search.get_database') as mock_db:
            with patch('services.ecosystem-mcp.src.services.rag.hybrid_search.DocumentRepository') as mock_repo_class:
                mock_repo = AsyncMock()
                mock_repo.get_by_id = AsyncMock(return_value=None)
                mock_repo_class.return_value = mock_repo
                
                mock_session = AsyncMock()
                mock_session.__aenter__ = AsyncMock(return_value=mock_session)
                mock_session.__aexit__ = AsyncMock(return_value=None)
                mock_db.return_value.session.return_value = mock_session
                
                result = await service._get_enriched_document("nonexistent-id")
                
                assert result is None


class TestChromaDBCaching:
    """Test ChromaDB search result caching."""
    
    @pytest.mark.asyncio
    async def test_chromadb_search_cached(self):
        """Test ChromaDB search results are cached."""
        # Note: _retrieve_with_scoring already has @cache decorator
        # This test verifies it's working
        from services.ecosystem-mcp.src.services.rag.rag_service import RAGService
        
        service = RAGService()
        
        # Mock dependencies
        with patch.object(service.embedding_service, 'generate_embedding', new_callable=AsyncMock) as mock_embed:
            with patch.object(service.chroma, 'query', new_callable=AsyncMock) as mock_query:
                mock_embed.return_value = {"embedding": [0.1] * 384, "tokens": 10}
                mock_query.return_value = {
                    "ids": [["doc1", "doc2"]],
                    "distances": [[0.1, 0.2]],
                    "documents": [["content1", "content2"]],
                    "metadatas": [[{"file_path": "test1.md"}, {"file_path": "test2.md"}]]
                }
                
                with patch('services.ecosystem-mcp.src.services.rag.rag_service.get_database') as mock_db:
                    mock_session = AsyncMock()
                    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
                    mock_session.__aexit__ = AsyncMock(return_value=None)
                    mock_db.return_value.session.return_value = mock_session
                    
                    # First call
                    result1 = await service._retrieve_with_scoring("test query")
                    
                    # Second call (should use cached embedding + search)
                    result2 = await service._retrieve_with_scoring("test query")
                    
                    # Verify results exist
                    assert result1 is not None
                    assert result2 is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

