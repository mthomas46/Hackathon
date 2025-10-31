"""
Unit tests for BM25 search service.

Tests:
- Index building
- Basic search
- Quality filtering
- Tokenization
- Index statistics
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.services.rag.bm25_search import BM25SearchService


@pytest.fixture
def mock_documents():
    """Mock documents for testing."""
    return [
        Mock(
            id="doc1",
            file_path="test1.py",
            content="This is a test document about ingestion and processing",
            doc_metadata={"category": "code"},
            quality_score=85.0
        ),
        Mock(
            id="doc2",
            file_path="test2.py",
            content="ChromaDB error 500 connection failed",
            doc_metadata={"category": "error"},
            quality_score=60.0
        ),
        Mock(
            id="doc3",
            file_path="test3.md",
            content="How to start the ingestion worker for document processing",
            doc_metadata={"category": "documentation"},
            quality_score=90.0
        ),
    ]


@pytest.fixture
def bm25_service():
    """Create BM25 service instance."""
    return BM25SearchService()


class TestBM25Tokenization:
    """Test tokenization."""
    
    def test_basic_tokenization(self, bm25_service):
        """Test basic text tokenization."""
        text = "This is a test document"
        tokens = bm25_service._tokenize(text)
        
        assert tokens == ["this", "is", "a", "test", "document"]
    
    def test_tokenization_with_punctuation(self, bm25_service):
        """Test tokenization handles punctuation."""
        text = "Error: Connection failed! Code=500"
        tokens = bm25_service._tokenize(text)
        
        assert "error" in tokens
        assert "connection" in tokens
        assert "failed" in tokens
        assert "code" in tokens
        assert "500" in tokens
    
    def test_tokenization_preserves_underscores(self, bm25_service):
        """Test tokenization preserves underscores (for code)."""
        text = "def process_document(file_path):"
        tokens = bm25_service._tokenize(text)
        
        assert "process_document" in tokens
        assert "file_path" in tokens
    
    def test_empty_tokenization(self, bm25_service):
        """Test tokenization of empty string."""
        tokens = bm25_service._tokenize("")
        assert tokens == []


class TestBM25IndexBuilding:
    """Test index building."""
    
    @pytest.mark.asyncio
    async def test_build_index(self, bm25_service, mock_documents):
        """Test building BM25 index."""
        with patch('src.services.rag.bm25_search.get_database') as mock_db:
            # Mock database session and repository
            mock_session = AsyncMock()
            mock_repo = Mock()
            mock_repo.get_all_documents = AsyncMock(return_value=mock_documents)
            
            mock_db.return_value.__aenter__.return_value = mock_session
            
            with patch('src.services.rag.bm25_search.DocumentRepository', return_value=mock_repo):
                await bm25_service.build_index()
        
        # Check index was built
        assert bm25_service.bm25_index is not None
        assert bm25_service.index_size == 3
        assert len(bm25_service.document_ids) == 3
        assert len(bm25_service.documents_metadata) == 3
    
    @pytest.mark.asyncio
    async def test_build_index_no_documents(self, bm25_service):
        """Test building index with no documents."""
        with patch('src.services.rag.bm25_search.get_database') as mock_db:
            mock_session = AsyncMock()
            mock_repo = Mock()
            mock_repo.get_all_documents = AsyncMock(return_value=[])
            
            mock_db.return_value.__aenter__.return_value = mock_session
            
            with patch('src.services.rag.bm25_search.DocumentRepository', return_value=mock_repo):
                await bm25_service.build_index()
        
        assert bm25_service.bm25_index is None
    
    @pytest.mark.asyncio
    async def test_skip_rebuild_if_exists(self, bm25_service, mock_documents):
        """Test that rebuild is skipped if index exists."""
        # Build once
        with patch('src.services.rag.bm25_search.get_database') as mock_db:
            mock_session = AsyncMock()
            mock_repo = Mock()
            mock_repo.get_all_documents = AsyncMock(return_value=mock_documents)
            
            mock_db.return_value.__aenter__.return_value = mock_session
            
            with patch('src.services.rag.bm25_search.DocumentRepository', return_value=mock_repo):
                await bm25_service.build_index()
                first_index = bm25_service.bm25_index
                
                # Try to rebuild (should skip)
                await bm25_service.build_index()
                
                # Should be same index
                assert bm25_service.bm25_index is first_index


class TestBM25Search:
    """Test BM25 search functionality."""
    
    @pytest.mark.asyncio
    async def test_search_basic(self, bm25_service, mock_documents):
        """Test basic BM25 search."""
        # Build index first
        with patch('src.services.rag.bm25_search.get_database') as mock_db:
            mock_session = AsyncMock()
            mock_repo = Mock()
            mock_repo.get_all_documents = AsyncMock(return_value=mock_documents)
            
            mock_db.return_value.__aenter__.return_value = mock_session
            
            with patch('src.services.rag.bm25_search.DocumentRepository', return_value=mock_repo):
                await bm25_service.build_index()
        
        # Search
        results = await bm25_service.search("ingestion", n_results=2)
        
        assert len(results) <= 2
        assert all("bm25_score" in r for r in results)
        assert all("file_path" in r for r in results)
    
    @pytest.mark.asyncio
    async def test_search_exact_term(self, bm25_service, mock_documents):
        """Test search for exact term."""
        with patch('src.services.rag.bm25_search.get_database') as mock_db:
            mock_session = AsyncMock()
            mock_repo = Mock()
            mock_repo.get_all_documents = AsyncMock(return_value=mock_documents)
            
            mock_db.return_value.__aenter__.return_value = mock_session
            
            with patch('src.services.rag.bm25_search.DocumentRepository', return_value=mock_repo):
                await bm25_service.build_index()
        
        # Search for specific error code
        results = await bm25_service.search("500", n_results=5)
        
        # Should find doc with "500" in it
        assert len(results) > 0
        assert any("doc2" == r["id"] for r in results)
    
    @pytest.mark.asyncio
    async def test_search_with_quality_threshold(self, bm25_service, mock_documents):
        """Test search with quality filtering."""
        with patch('src.services.rag.bm25_search.get_database') as mock_db:
            mock_session = AsyncMock()
            mock_repo = Mock()
            mock_repo.get_all_documents = AsyncMock(return_value=mock_documents)
            
            mock_db.return_value.__aenter__.return_value = mock_session
            
            with patch('src.services.rag.bm25_search.DocumentRepository', return_value=mock_repo):
                await bm25_service.build_index()
        
        # Search with high quality threshold
        results = await bm25_service.search("ingestion", n_results=5, quality_threshold=80.0)
        
        # Should only return high-quality docs
        for result in results:
            quality = result.get("quality_score")
            if quality is not None:
                assert quality >= 80.0
    
    @pytest.mark.asyncio
    async def test_search_no_index(self, bm25_service):
        """Test search without built index triggers build."""
        with patch('src.services.rag.bm25_search.get_database') as mock_db:
            mock_session = AsyncMock()
            mock_repo = Mock()
            mock_repo.get_all_documents = AsyncMock(return_value=[])
            
            mock_db.return_value.__aenter__.return_value = mock_session
            
            with patch('src.services.rag.bm25_search.DocumentRepository', return_value=mock_repo):
                results = await bm25_service.search("test", n_results=5)
        
        assert results == []


class TestBM25Statistics:
    """Test index statistics."""
    
    def test_stats_no_index(self, bm25_service):
        """Test statistics with no index."""
        stats = bm25_service.get_index_stats()
        
        assert stats["indexed"] is False
        assert stats["index_size"] == 0
        assert stats["last_indexed"] is None
    
    @pytest.mark.asyncio
    async def test_stats_with_index(self, bm25_service, mock_documents):
        """Test statistics with built index."""
        with patch('src.services.rag.bm25_search.get_database') as mock_db:
            mock_session = AsyncMock()
            mock_repo = Mock()
            mock_repo.get_all_documents = AsyncMock(return_value=mock_documents)
            
            mock_db.return_value.__aenter__.return_value = mock_session
            
            with patch('src.services.rag.bm25_search.DocumentRepository', return_value=mock_repo):
                await bm25_service.build_index()
        
        stats = bm25_service.get_index_stats()
        
        assert stats["indexed"] is True
        assert stats["index_size"] == 3
        assert stats["last_indexed"] is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

