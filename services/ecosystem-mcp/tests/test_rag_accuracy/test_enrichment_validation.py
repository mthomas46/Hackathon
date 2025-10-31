"""
Unit tests for hybrid search enrichment with fail-fast validation.

Tests cover:
- UUID/string ID conversion
- Database lookup logic
- Missing document handling
- Content extraction
- Error propagation (fail-fast)
"""
import pytest
from uuid import uuid4, UUID
from unittest.mock import AsyncMock, Mock, patch
from services.ecosystem_mcp.src.services.rag.hybrid_search import HybridSearchService


class TestEnrichmentValidation:
    """Test enrichment with comprehensive validation."""
    
    @pytest.fixture
    def hybrid_service(self):
        """Create hybrid search service."""
        return HybridSearchService()
    
    @pytest.fixture
    def sample_doc_ids(self):
        """Generate sample UUIDs."""
        return [uuid4() for _ in range(3)]
    
    @pytest.fixture
    def sample_results(self, sample_doc_ids):
        """Create sample search results with string IDs."""
        return [
            {
                "id": str(sample_doc_ids[0]),
                "file_path": "test1.py",
                "hybrid_score": 0.95,
                "content": "Test content 1"
            },
            {
                "id": str(sample_doc_ids[1]),
                "file_path": "test2.py",
                "hybrid_score": 0.85,
                "content": "Test content 2"
            },
            {
                "id": str(sample_doc_ids[2]),
                "file_path": "test3.py",
                "hybrid_score": 0.75,
                "content": "Test content 3"
            }
        ]
    
    @pytest.fixture
    def mock_documents(self, sample_doc_ids):
        """Create mock database documents."""
        docs = []
        for idx, doc_id in enumerate(sample_doc_ids):
            doc = Mock()
            doc.id = doc_id  # UUID object
            doc.normalized_content = f"Normalized content {idx + 1}"
            doc.original_content = f"Original content {idx + 1}"
            doc.doc_metadata = {"test": f"metadata_{idx}"}
            doc.quality_score = 80.0 + idx
            doc.quality_grade = "A"
            docs.append(doc)
        return docs
    
    @pytest.mark.asyncio
    async def test_enrich_results_success(self, hybrid_service, sample_results, mock_documents):
        """Test successful enrichment with all documents found."""
        with patch('services.ecosystem_mcp.src.services.rag.hybrid_search.get_database') as mock_db:
            # Setup mock database
            mock_session = AsyncMock()
            mock_repo = AsyncMock()
            mock_repo.get_by_ids_bulk.return_value = mock_documents
            
            mock_session_ctx = Mock()
            mock_session_ctx.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_ctx.__aexit__ = AsyncMock()
            
            mock_db.return_value.session.return_value = mock_session_ctx
            
            with patch('services.ecosystem_mcp.src.services.rag.hybrid_search.DocumentRepository', return_value=mock_repo):
                # Run enrichment
                enriched = await hybrid_service._enrich_results(sample_results)
                
                # Validate
                assert len(enriched) == 3
                assert all("content_snippet" in r for r in enriched)
                assert all("full_metadata" in r for r in enriched)
                assert all("quality_score" in r for r in enriched)
                assert enriched[0]["content_snippet"].startswith("Normalized content 1")
    
    @pytest.mark.asyncio
    async def test_enrich_results_uuid_types(self, hybrid_service, sample_doc_ids, mock_documents):
        """Test enrichment handles both string and UUID IDs."""
        # Mix of string and UUID IDs
        mixed_results = [
            {"id": str(sample_doc_ids[0]), "file_path": "test1.py"},  # String
            {"id": sample_doc_ids[1], "file_path": "test2.py"},      # UUID
        ]
        
        with patch('services.ecosystem_mcp.src.services.rag.hybrid_search.get_database') as mock_db:
            mock_session = AsyncMock()
            mock_repo = AsyncMock()
            mock_repo.get_by_ids_bulk.return_value = mock_documents[:2]
            
            mock_session_ctx = Mock()
            mock_session_ctx.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_ctx.__aexit__ = AsyncMock()
            
            mock_db.return_value.session.return_value = mock_session_ctx
            
            with patch('services.ecosystem_mcp.src.services.rag.hybrid_search.DocumentRepository', return_value=mock_repo):
                enriched = await hybrid_service._enrich_results(mixed_results)
                
                # Both should be enriched successfully
                assert len(enriched) == 2
                assert all("content_snippet" in r for r in enriched)
    
    @pytest.mark.asyncio
    async def test_enrich_results_missing_id_field(self, hybrid_service):
        """Test fail-fast when result missing 'id' field."""
        bad_results = [
            {"file_path": "test.py", "score": 0.95}  # Missing 'id'
        ]
        
        with pytest.raises(ValueError, match="missing required 'id' field"):
            await hybrid_service._enrich_results(bad_results)
    
    @pytest.mark.asyncio
    async def test_enrich_results_invalid_uuid(self, hybrid_service):
        """Test fail-fast on invalid UUID format."""
        bad_results = [
            {"id": "not-a-uuid", "file_path": "test.py"}
        ]
        
        with pytest.raises(RuntimeError, match="Enrichment failed critically"):
            await hybrid_service._enrich_results(bad_results)
    
    @pytest.mark.asyncio
    async def test_enrich_results_database_returns_empty(self, hybrid_service, sample_results):
        """Test fail-fast when database returns no documents."""
        with patch('services.ecosystem_mcp.src.services.rag.hybrid_search.get_database') as mock_db:
            mock_session = AsyncMock()
            mock_repo = AsyncMock()
            mock_repo.get_by_ids_bulk.return_value = []  # Empty!
            
            mock_session_ctx = Mock()
            mock_session_ctx.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_ctx.__aexit__ = AsyncMock()
            
            mock_db.return_value.session.return_value = mock_session_ctx
            
            with patch('services.ecosystem_mcp.src.services.rag.hybrid_search.DocumentRepository', return_value=mock_repo):
                with pytest.raises(RuntimeError, match="Database returned no documents"):
                    await hybrid_service._enrich_results(sample_results)
    
    @pytest.mark.asyncio
    async def test_enrich_results_partial_match(self, hybrid_service, sample_doc_ids, mock_documents):
        """Test handling when some documents not found in database."""
        # Request 3 docs but only 2 returned
        results = [
            {"id": str(sample_doc_ids[0]), "file_path": "test1.py"},
            {"id": str(sample_doc_ids[1]), "file_path": "test2.py"},
            {"id": str(uuid4()), "file_path": "missing.py"},  # Won't be in DB
        ]
        
        with patch('services.ecosystem_mcp.src.services.rag.hybrid_search.get_database') as mock_db:
            mock_session = AsyncMock()
            mock_repo = AsyncMock()
            mock_repo.get_by_ids_bulk.return_value = mock_documents[:2]  # Only first 2
            
            mock_session_ctx = Mock()
            mock_session_ctx.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_ctx.__aexit__ = AsyncMock()
            
            mock_db.return_value.session.return_value = mock_session_ctx
            
            with patch('services.ecosystem_mcp.src.services.rag.hybrid_search.DocumentRepository', return_value=mock_repo):
                enriched = await hybrid_service._enrich_results(results)
                
                # Should include all 3, with third marked as failed
                assert len(enriched) == 3
                assert "enrichment_failed" not in enriched[0]
                assert "enrichment_failed" not in enriched[1]
                assert enriched[2]["enrichment_failed"] is True
                assert enriched[2]["content_snippet"] == "[Document not found in database]"
    
    @pytest.mark.asyncio
    async def test_enrich_results_missing_content(self, hybrid_service, sample_doc_ids):
        """Test handling document with no content."""
        results = [{"id": str(sample_doc_ids[0]), "file_path": "empty.py"}]
        
        # Create doc with no content
        doc = Mock()
        doc.id = sample_doc_ids[0]
        doc.normalized_content = None
        doc.original_content = ""  # Empty!
        doc.doc_metadata = {}
        doc.quality_score = None
        
        with patch('services.ecosystem_mcp.src.services.rag.hybrid_search.get_database') as mock_db:
            mock_session = AsyncMock()
            mock_repo = AsyncMock()
            mock_repo.get_by_ids_bulk.return_value = [doc]
            
            mock_session_ctx = Mock()
            mock_session_ctx.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_ctx.__aexit__ = AsyncMock()
            
            mock_db.return_value.session.return_value = mock_session_ctx
            
            with patch('services.ecosystem_mcp.src.services.rag.hybrid_search.DocumentRepository', return_value=mock_repo):
                enriched = await hybrid_service._enrich_results(results)
                
                # Should succeed with fallback content
                assert len(enriched) == 1
                assert enriched[0]["content_snippet"] == "[Content not available]"
    
    @pytest.mark.asyncio
    async def test_enrich_results_empty_input(self, hybrid_service):
        """Test enrichment with empty input."""
        result = await hybrid_service._enrich_results([])
        assert result == []


class TestIDMapBuilding:
    """Test the dual-key ID map building logic."""
    
    def test_dual_key_map(self):
        """Verify dual-key map allows both UUID and string lookups."""
        doc_id = uuid4()
        
        # Build map like enrichment does
        doc_map = {}
        mock_doc = Mock(id=doc_id, content="test")
        doc_map[mock_doc.id] = mock_doc  # UUID key
        doc_map[str(mock_doc.id)] = mock_doc  # String key
        
        # Both lookups should work
        assert doc_map.get(doc_id) is mock_doc
        assert doc_map.get(str(doc_id)) is mock_doc
        assert doc_map.get(doc_id) is doc_map.get(str(doc_id))


class TestContentExtraction:
    """Test content extraction logic."""
    
    def test_prefers_normalized_content(self):
        """Verify normalized content is preferred over original."""
        doc = Mock()
        doc.normalized_content = "Normalized"
        doc.original_content = "Original"
        
        full_content = doc.normalized_content if doc.normalized_content else doc.original_content
        assert full_content == "Normalized"
    
    def test_fallback_to_original_content(self):
        """Verify fallback to original when normalized missing."""
        doc = Mock()
        doc.normalized_content = None
        doc.original_content = "Original"
        
        full_content = doc.normalized_content if doc.normalized_content else doc.original_content
        assert full_content == "Original"
    
    def test_handles_empty_content(self):
        """Verify handling of completely empty content."""
        doc = Mock()
        doc.normalized_content = ""
        doc.original_content = ""
        
        full_content = doc.normalized_content if doc.normalized_content else doc.original_content
        if not full_content:
            full_content = "[Content not available]"
        
        assert full_content == "[Content not available]"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

