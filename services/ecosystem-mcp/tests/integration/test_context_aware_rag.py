"""
Integration Tests for Context-Aware RAG (Week 3, Day 2)

Tests:
- Context-aware queries
- Hierarchical filtering
- Multi-dimensional filtering
- Relevance scoring
- Context enhancement
- Batch queries
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import timedelta

from src.services.rag.context_aware_rag import (
    ContextAwareRAG,
    get_context_aware_rag
)
from src.services.analysis.hierarchical_context_manager import (
    HierarchicalContext,
    ContextLevel
)


@pytest.fixture
def mock_context():
    """Create mock hierarchical context."""
    return HierarchicalContext(
        id="test-context",
        name="Test Service",
        repo_id="test-repo",
        technologies=["python", "fastapi"],
        primary_language="python",
        services=["api-service"],
        description="Test service description",
        level=ContextLevel.SERVICE,
        full_path="test-repo/services/api",
        file_paths=["api/handler.py", "api/service.py"],
        level_files=2,
        level_lines=500
    )


@pytest.fixture
def mock_rag():
    """Create mock RAG instance with mocked dependencies."""
    rag = ContextAwareRAG()
    
    # Mock context manager
    rag.context_manager = Mock()
    rag.context_manager.get_context = AsyncMock()
    rag.context_manager.search_contexts = AsyncMock()
    rag.context_manager.get_children = AsyncMock(return_value=[])
    
    # Mock ChromaDB
    rag.chromadb = Mock()
    rag.chromadb.query = AsyncMock()
    
    # Mock embedding service
    rag.embedding_service = Mock()
    rag.embedding_service.generate_embedding = AsyncMock(return_value=[0.1] * 384)
    
    return rag


@pytest.mark.integration
@pytest.mark.asyncio
class TestContextAwareRAG:
    """Test context-aware RAG system."""
    
    async def test_query_without_context(self, mock_rag):
        """Test query without any context filtering."""
        # Mock ChromaDB response
        mock_rag.chromadb.query.return_value = {
            "documents": [["test document 1", "test document 2"]],
            "metadatas": [[{"file": "test1.py"}, {"file": "test2.py"}]],
            "distances": [[0.2, 0.3]]
        }
        
        result = await mock_rag.query_with_context(
            query="test query",
            limit=10
        )
        
        assert result["query"] == "test query"
        assert result["total"] == 2
        assert len(result["results"]) == 2
        assert result["metadata"]["filters_applied"] is False
        assert result["metadata"]["context_used"] is False
    
    async def test_query_with_repo_filter(self, mock_rag):
        """Test query with repository filter."""
        mock_rag.chromadb.query.return_value = {
            "documents": [["doc 1"]],
            "metadatas": [[{"repo_id": "test-repo"}]],
            "distances": [[0.1]]
        }
        
        result = await mock_rag.query_with_context(
            query="test query",
            repo_id="test-repo",
            limit=10
        )
        
        assert result["filters"]["repo_id"] == "test-repo"
        assert result["total"] == 1
    
    async def test_query_with_context_filter(self, mock_rag, mock_context):
        """Test query with hierarchical context filter."""
        # Mock context retrieval
        mock_rag.context_manager.get_context.return_value = mock_context
        
        mock_rag.chromadb.query.return_value = {
            "documents": [["service document"]],
            "metadatas": [[{"service": "api-service"}]],
            "distances": [[0.15]]
        }
        
        result = await mock_rag.query_with_context(
            query="test query",
            context_id="test-context",
            limit=10
        )
        
        assert result["filters"]["context_id"] == "test-context"
        assert result["context_info"] is not None
        assert result["context_info"]["name"] == "Test Service"
        assert result["context_info"]["level"] == "SERVICE"
    
    async def test_query_with_tech_filter(self, mock_rag):
        """Test query with technology stack filter."""
        mock_rag.chromadb.query.return_value = {
            "documents": [["python doc"]],
            "metadatas": [[{"technology": "python"}]],
            "distances": [[0.1]]
        }
        
        result = await mock_rag.query_with_context(
            query="python code",
            tech_filter=["python", "fastapi"],
            limit=10
        )
        
        assert result["filters"]["tech_stack"] == ["python", "fastapi"]
        assert result["total"] == 1
    
    async def test_query_with_language_filter(self, mock_rag):
        """Test query with programming language filter."""
        mock_rag.chromadb.query.return_value = {
            "documents": [["python file"]],
            "metadatas": [[{"language": "python"}]],
            "distances": [[0.12]]
        }
        
        result = await mock_rag.query_with_context(
            query="function",
            language_filter="python",
            limit=10
        )
        
        assert result["filters"]["language"] == "python"
    
    async def test_query_with_time_range(self, mock_rag):
        """Test query with time range filter."""
        mock_rag.chromadb.query.return_value = {
            "documents": [["recent doc"]],
            "metadatas": [[{"created_at": "2025-10-21T10:00:00"}]],
            "distances": [[0.1]]
        }
        
        result = await mock_rag.query_with_context(
            query="recent changes",
            time_range=timedelta(hours=24),
            limit=10
        )
        
        assert result["filters"]["time_range_hours"] == 24.0
    
    async def test_query_with_multiple_filters(self, mock_rag, mock_context):
        """Test query with multiple filters combined."""
        mock_rag.context_manager.get_context.return_value = mock_context
        mock_rag.chromadb.query.return_value = {
            "documents": [["filtered doc"]],
            "metadatas": [[{
                "repo_id": "test-repo",
                "service": "api-service",
                "technology": "python",
                "language": "python"
            }]],
            "distances": [[0.08]]
        }
        
        result = await mock_rag.query_with_context(
            query="api handler",
            repo_id="test-repo",
            context_id="test-context",
            service_filter="api-service",
            tech_filter=["python"],
            language_filter="python",
            limit=10
        )
        
        assert result["filters"]["repo_id"] == "test-repo"
        assert result["filters"]["context_id"] == "test-context"
        assert result["filters"]["service"] == "api-service"
        assert result["filters"]["tech_stack"] == ["python"]
        assert result["filters"]["language"] == "python"


@pytest.mark.integration
@pytest.mark.asyncio
class TestRelevanceScoring:
    """Test relevance scoring."""
    
    async def test_relevance_score_calculation(self, mock_rag):
        """Test relevance score combines vector + keyword scores."""
        mock_rag.chromadb.query.return_value = {
            "documents": [["python function test query code"]],
            "metadatas": [[{"file": "test.py"}]],
            "distances": [[0.2]]  # 0.8 vector score
        }
        
        result = await mock_rag.query_with_context(
            query="python test",
            limit=10
        )
        
        # Check scores are present
        assert result["results"][0]["relevance_score"] > 0
        assert result["results"][0]["vector_score"] > 0
        assert result["results"][0]["keyword_score"] > 0
        
        # Relevance should be weighted combination
        vector_score = result["results"][0]["vector_score"]
        keyword_score = result["results"][0]["keyword_score"]
        expected_relevance = (vector_score * 0.7) + (keyword_score * 0.3)
        
        assert abs(result["results"][0]["relevance_score"] - expected_relevance) < 0.01
    
    async def test_results_sorted_by_relevance(self, mock_rag):
        """Test results are sorted by relevance score."""
        mock_rag.chromadb.query.return_value = {
            "documents": [["doc1", "doc2 query match", "doc3"]],
            "metadatas": [[{"f": "1"}, {"f": "2"}, {"f": "3"}]],
            "distances": [[0.3, 0.1, 0.2]]
        }
        
        result = await mock_rag.query_with_context(
            query="query",
            limit=10
        )
        
        # Results should be sorted by relevance (descending)
        scores = [r["relevance_score"] for r in result["results"]]
        assert scores == sorted(scores, reverse=True)


@pytest.mark.integration
@pytest.mark.asyncio
class TestContextEnhancement:
    """Test context enhancement."""
    
    async def test_results_enhanced_with_context(self, mock_rag, mock_context):
        """Test results are enhanced with context metadata."""
        mock_rag.context_manager.get_context.return_value = mock_context
        mock_rag.chromadb.query.return_value = {
            "documents": [["doc"]],
            "metadatas": [[{"file": "test.py"}]],
            "distances": [[0.1]]
        }
        
        result = await mock_rag.query_with_context(
            query="test",
            context_id="test-context",
            limit=10
        )
        
        # Check context info is added
        doc = result["results"][0]
        assert doc["context"] is not None
        assert doc["context"]["name"] == "Test Service"
        assert doc["context"]["level"] == "SERVICE"
        assert doc["context"]["full_path"] == "test-repo/services/api"


@pytest.mark.integration
@pytest.mark.asyncio
class TestRepositoryContexts:
    """Test repository context queries."""
    
    async def test_get_repository_contexts(self, mock_rag):
        """Test getting all contexts for a repository."""
        # Mock contexts
        contexts = [
            Mock(id="ctx1", name="Service 1"),
            Mock(id="ctx2", name="Module 1")
        ]
        mock_rag.context_manager.search_contexts.return_value = contexts
        
        result = await mock_rag.get_repository_contexts("test-repo")
        
        assert len(result) == 2
        mock_rag.context_manager.search_contexts.assert_called_once()
    
    async def test_get_context_summary(self, mock_rag, mock_context):
        """Test getting context summary."""
        mock_rag.context_manager.get_context.return_value = mock_context
        mock_rag.context_manager.get_children.return_value = []
        
        summary = await mock_rag.get_context_summary("test-context")
        
        assert summary is not None
        assert summary["id"] == "test-context"
        assert summary["name"] == "Test Service"
        assert summary["level"] == "SERVICE"
        assert summary["file_count"] == 2
        assert "python" in summary["technologies"]
    
    async def test_get_context_summary_not_found(self, mock_rag):
        """Test getting summary for non-existent context."""
        mock_rag.context_manager.get_context.return_value = None
        
        summary = await mock_rag.get_context_summary("nonexistent")
        
        assert summary is None


@pytest.mark.integration
@pytest.mark.asyncio
class TestGracefulFallbacks:
    """Test graceful fallback handling."""
    
    async def test_fallback_on_filter_error(self, mock_rag):
        """Test fallback to no filters on error."""
        # First call with filters fails
        mock_rag.chromadb.query.side_effect = [
            Exception("Filter error"),
            {
                "documents": [["doc"]],
                "metadatas": [[{"file": "test.py"}]],
                "distances": [[0.1]]
            }
        ]
        
        result = await mock_rag.query_with_context(
            query="test",
            repo_id="test-repo",
            limit=10
        )
        
        # Should still return results
        assert result["total"] == 1
        assert mock_rag.chromadb.query.call_count == 2
    
    async def test_missing_context_handled(self, mock_rag):
        """Test query continues with missing context."""
        mock_rag.context_manager.get_context.return_value = None
        mock_rag.chromadb.query.return_value = {
            "documents": [["doc"]],
            "metadatas": [[{}]],
            "distances": [[0.1]]
        }
        
        result = await mock_rag.query_with_context(
            query="test",
            context_id="nonexistent",
            limit=10
        )
        
        # Should still work without context
        assert result["total"] == 1
        assert result["context_info"] is None


@pytest.mark.integration
class TestSingleton:
    """Test singleton pattern."""
    
    def test_singleton_returns_same_instance(self):
        """Test singleton returns same instance."""
        rag1 = get_context_aware_rag()
        rag2 = get_context_aware_rag()
        
        assert rag1 is rag2


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

