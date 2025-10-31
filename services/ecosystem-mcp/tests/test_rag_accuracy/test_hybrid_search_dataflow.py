"""
Integration tests for hybrid search full data flow.

Tests the complete path:
Query → Semantic Search → BM25 Search → RRF Fusion → Enrichment → Results

Validates:
- Data structure integrity at each step
- Field presence and types
- ID format consistency
- Content availability
"""
import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from services.ecosystem_mcp.src.services.rag.hybrid_search import HybridSearchService


class TestHybridSearchDataFlow:
    """Test complete data flow through hybrid search."""
    
    @pytest.fixture
    def hybrid_service(self):
        """Create hybrid search service with mocked dependencies."""
        service = HybridSearchService()
        
        # Mock ChromaDB
        service.chroma_collection = Mock()
        
        return service
    
    @pytest.fixture
    def sample_doc_ids(self):
        """Generate sample document IDs."""
        return [str(uuid4()) for _ in range(5)]
    
    @pytest.fixture
    def mock_semantic_results(self, sample_doc_ids):
        """Mock ChromaDB semantic search results."""
        return {
            "ids": [sample_doc_ids[:3]],  # Top 3 from semantic
            "distances": [[0.2, 0.3, 0.4]],
            "metadatas": [[
                {
                    "file_path": "doc1.py",
                    "quality_score": 85.0,
                    "updated_at": "2025-10-01T00:00:00"
                },
                {
                    "file_path": "doc2.md",
                    "quality_score": 75.0,
                    "updated_at": "2025-10-15T00:00:00"
                },
                {
                    "file_path": "doc3.txt",
                    "quality_score": 65.0,
                    "updated_at": "2025-10-20T00:00:00"
                }
            ]],
            "documents": [[
                "Semantic content 1",
                "Semantic content 2",
                "Semantic content 3"
            ]]
        }
    
    @pytest.fixture
    def mock_bm25_results(self, sample_doc_ids):
        """Mock BM25 keyword search results."""
        return [
            {
                "id": sample_doc_ids[2],  # Overlap with semantic (doc3)
                "file_path": "doc3.txt",
                "content": "BM25 content 3",
                "bm25_score": 8.5,
                "metadata": {"quality_score": 65.0},
                "recency_days": 10
            },
            {
                "id": sample_doc_ids[3],  # BM25-only result
                "file_path": "doc4.py",
                "content": "BM25 content 4",
                "bm25_score": 7.2,
                "metadata": {"quality_score": 80.0},
                "recency_days": 5
            },
            {
                "id": sample_doc_ids[4],  # BM25-only result
                "file_path": "doc5.md",
                "content": "BM25 content 5",
                "bm25_score": 6.8,
                "metadata": {"quality_score": 70.0},
                "recency_days": 20
            }
        ]
    
    @pytest.fixture
    def mock_database_documents(self, sample_doc_ids):
        """Mock database documents for enrichment."""
        docs = []
        for idx, doc_id in enumerate(sample_doc_ids):
            doc = Mock()
            doc.id = doc_id  # String ID from BM25/Semantic
            doc.normalized_content = f"Full normalized content {idx + 1}" * 50  # Long content
            doc.original_content = f"Full original content {idx + 1}" * 50
            doc.doc_metadata = {
                "test_key": f"value_{idx}",
                "doc_type": ["py", "md", "txt", "py", "md"][idx]
            }
            doc.quality_score = [85.0, 75.0, 65.0, 80.0, 70.0][idx]
            doc.quality_grade = ["A", "B", "C", "A", "B"][idx]
            docs.append(doc)
        return docs
    
    @pytest.mark.asyncio
    async def test_complete_hybrid_search_flow(
        self, 
        hybrid_service,
        mock_semantic_results,
        mock_bm25_results,
        mock_database_documents
    ):
        """Test complete flow from query to enriched results."""
        
        # Setup mocks
        hybrid_service.chroma_collection.query.return_value = mock_semantic_results
        hybrid_service.bm25_search.search = AsyncMock(return_value=mock_bm25_results)
        
        with patch('services.ecosystem_mcp.src.services.rag.hybrid_search.get_database') as mock_db:
            mock_session = AsyncMock()
            mock_repo = AsyncMock()
            mock_repo.get_by_ids_bulk.return_value = mock_database_documents
            
            mock_session_ctx = Mock()
            mock_session_ctx.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_ctx.__aexit__ = AsyncMock()
            
            mock_db.return_value.session.return_value = mock_session_ctx
            
            with patch('services.ecosystem_mcp.src.services.rag.hybrid_search.DocumentRepository', return_value=mock_repo):
                # Execute hybrid search
                results = await hybrid_service.search(
                    query="test query",
                    n_results=5
                )
                
                # VALIDATION 1: Results returned
                assert len(results) > 0, "Hybrid search should return results"
                
                # VALIDATION 2: Required fields present
                required_fields = ["id", "file_path", "hybrid_score", "content_snippet"]
                for result in results:
                    for field in required_fields:
                        assert field in result, f"Result missing required field: {field}"
                
                # VALIDATION 3: Scores are numeric
                for result in results:
                    assert isinstance(result["hybrid_score"], (int, float)), "hybrid_score must be numeric"
                    assert result["hybrid_score"] > 0, "hybrid_score must be positive"
                
                # VALIDATION 4: Content snippets exist
                for result in results:
                    assert len(result["content_snippet"]) > 0, "content_snippet should not be empty"
                    assert result["content_snippet"] != "[Content not available]", "Content should be enriched"
                
                # VALIDATION 5: Quality metadata included
                for result in results:
                    assert "quality_score" in result, "quality_score should be enriched"
                    assert "full_metadata" in result, "full_metadata should be enriched"
    
    @pytest.mark.asyncio
    async def test_data_structure_consistency(
        self,
        hybrid_service,
        mock_semantic_results,
        mock_bm25_results,
        mock_database_documents
    ):
        """Test data structure remains consistent through each step."""
        
        hybrid_service.chroma_collection.query.return_value = mock_semantic_results
        hybrid_service.bm25_search.search = AsyncMock(return_value=mock_bm25_results)
        
        with patch('services.ecosystem_mcp.src.services.rag.hybrid_search.get_database') as mock_db:
            mock_session = AsyncMock()
            mock_repo = AsyncMock()
            mock_repo.get_by_ids_bulk.return_value = mock_database_documents
            
            mock_session_ctx = Mock()
            mock_session_ctx.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_ctx.__aexit__ = AsyncMock()
            
            mock_db.return_value.session.return_value = mock_session_ctx
            
            with patch('services.ecosystem_mcp.src.services.rag.hybrid_search.DocumentRepository', return_value=mock_repo):
                results = await hybrid_service.search("test", n_results=5)
                
                # Check ID types are consistent (all strings)
                id_types = [type(r["id"]) for r in results]
                assert all(t == str for t in id_types), "All IDs should be strings after enrichment"
                
                # Check all have same field structure
                first_keys = set(results[0].keys())
                for result in results[1:]:
                    # Allow some variation but core fields must match
                    core_fields = {"id", "file_path", "hybrid_score", "content_snippet"}
                    assert core_fields.issubset(result.keys()), "Core fields must be present"
    
    @pytest.mark.asyncio
    async def test_rrf_fusion_deduplication(
        self,
        hybrid_service,
        mock_semantic_results,
        mock_bm25_results,
        mock_database_documents,
        sample_doc_ids
    ):
        """Test RRF properly deduplicates overlapping results."""
        
        # Note: doc3 (sample_doc_ids[2]) appears in both semantic and BM25
        hybrid_service.chroma_collection.query.return_value = mock_semantic_results
        hybrid_service.bm25_search.search = AsyncMock(return_value=mock_bm25_results)
        
        with patch('services.ecosystem_mcp.src.services.rag.hybrid_search.get_database') as mock_db:
            mock_session = AsyncMock()
            mock_repo = AsyncMock()
            mock_repo.get_by_ids_bulk.return_value = mock_database_documents
            
            mock_session_ctx = Mock()
            mock_session_ctx.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_ctx.__aexit__ = AsyncMock()
            
            mock_db.return_value.session.return_value = mock_session_ctx
            
            with patch('services.ecosystem_mcp.src.services.rag.hybrid_search.DocumentRepository', return_value=mock_repo):
                results = await hybrid_service.search("test", n_results=10)
                
                # Check for duplicates
                result_ids = [r["id"] for r in results]
                assert len(result_ids) == len(set(result_ids)), "RRF should deduplicate results"
                
                # Doc3 should appear once with both semantic and keyword ranks
                doc3_results = [r for r in results if r["id"] == sample_doc_ids[2]]
                if doc3_results:
                    doc3 = doc3_results[0]
                    assert "semantic_rank" in doc3, "Overlapping doc should have semantic rank"
                    assert "keyword_rank" in doc3, "Overlapping doc should have keyword rank"
    
    @pytest.mark.asyncio
    async def test_empty_semantic_results(
        self,
        hybrid_service,
        mock_bm25_results,
        mock_database_documents
    ):
        """Test hybrid search when semantic returns no results."""
        
        # Empty semantic results
        empty_semantic = {
            "ids": [[]],
            "distances": [[]],
            "metadatas": [[]],
            "documents": [[]]
        }
        
        hybrid_service.chroma_collection.query.return_value = empty_semantic
        hybrid_service.bm25_search.search = AsyncMock(return_value=mock_bm25_results)
        
        with patch('services.ecosystem_mcp.src.services.rag.hybrid_search.get_database') as mock_db:
            mock_session = AsyncMock()
            mock_repo = AsyncMock()
            mock_repo.get_by_ids_bulk.return_value = mock_database_documents
            
            mock_session_ctx = Mock()
            mock_session_ctx.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_ctx.__aexit__ = AsyncMock()
            
            mock_db.return_value.session.return_value = mock_session_ctx
            
            with patch('services.ecosystem_mcp.src.services.rag.hybrid_search.DocumentRepository', return_value=mock_repo):
                results = await hybrid_service.search("test", n_results=5)
                
                # Should still get BM25 results
                assert len(results) > 0, "Should return BM25 results when semantic is empty"
                
                # All results should be from BM25
                for result in results:
                    assert "bm25_score" in result or "keyword_rank" in result, "Should be BM25 results"
    
    @pytest.mark.asyncio
    async def test_field_name_consistency(
        self,
        hybrid_service,
        mock_semantic_results,
        mock_bm25_results,
        mock_database_documents
    ):
        """Test that field names are consistent and predictable."""
        
        hybrid_service.chroma_collection.query.return_value = mock_semantic_results
        hybrid_service.bm25_search.search = AsyncMock(return_value=mock_bm25_results)
        
        with patch('services.ecosystem_mcp.src.services.rag.hybrid_search.get_database') as mock_db:
            mock_session = AsyncMock()
            mock_repo = AsyncMock()
            mock_repo.get_by_ids_bulk.return_value = mock_database_documents
            
            mock_session_ctx = Mock()
            mock_session_ctx.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_ctx.__aexit__ = AsyncMock()
            
            mock_db.return_value.session.return_value = mock_session_ctx
            
            with patch('services.ecosystem_mcp.src.services.rag.hybrid_search.DocumentRepository', return_value=mock_repo):
                results = await hybrid_service.search("test", n_results=5)
                
                # Define expected field names (no variations allowed)
                expected_fields = {
                    "id": str,
                    "file_path": str,
                    "hybrid_score": (int, float),
                    "content_snippet": str,  # Not "content" or "normalized_content"
                }
                
                for idx, result in enumerate(results):
                    for field_name, expected_type in expected_fields.items():
                        assert field_name in result, f"Result {idx} missing {field_name}"
                        assert isinstance(result[field_name], expected_type), \
                            f"Result {idx} {field_name} has wrong type: {type(result[field_name])}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

