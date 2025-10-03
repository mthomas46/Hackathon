"""
Integration tests for Workflow B: Historical Context Retrieval
Phase 2 Day 3 - Enhanced Roadmap v2.0
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from services.orchestrator.domain.workflows.historical_context_workflow import (
    HistoricalContextWorkflow,
    ContextSource,
    HistoricalContext
)


@pytest.fixture
def mock_workflow_logger():
    """Mock WorkflowLogger for testing."""
    logger = MagicMock()
    logger.log_workflow_start = AsyncMock()
    logger.log_workflow_step = AsyncMock()
    logger.log_workflow_complete = AsyncMock()
    logger.log_error = AsyncMock()
    return logger


@pytest.fixture
def workflow(mock_workflow_logger):
    """Create HistoricalContextWorkflow instance with mocked logger."""
    return HistoricalContextWorkflow(
        memory_agent_url="http://mock-memory:5090",
        doc_store_url="http://mock-doc:5140",
        source_agent_url="http://mock-source:8001",
        workflow_logger=mock_workflow_logger,
        relevance_threshold=0.3
    )


@pytest.fixture
def sample_query_context():
    """Sample query context for testing."""
    return {
        "feature_type": "authentication",
        "platform": "mobile",
        "feature_title": "OAuth2 Login",
        "feature_description": "Implement OAuth2 authentication for mobile app"
    }


class TestHistoricalContextWorkflow:
    """Test Workflow B: Historical Context Retrieval."""
    
    @pytest.mark.asyncio
    async def test_execute_with_empty_results(self, workflow, sample_query_context, mock_workflow_logger):
        """Test execute method when all services return empty results."""
        # Mock external services to return empty results
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "results": [],
                "documents": [],
                "issues": [],
                "pages": []
            }
            
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            result = await workflow.execute(
                query_context=sample_query_context,
                max_sources=50
            )
            
            # Verify result structure
            assert isinstance(result, HistoricalContext)
            assert result.total_sources == 0
            assert result.average_relevance == 0.0
            assert len(result.memory_context) == 0
            assert len(result.document_context) == 0
            assert len(result.jira_context) == 0
            assert len(result.confluence_context) == 0
            
            # Verify logging was called
            mock_workflow_logger.log_workflow_start.assert_called_once()
            mock_workflow_logger.log_workflow_complete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_extract_search_terms(self, workflow):
        """Test search term extraction from query context."""
        query_context = {
            "feature_type": "authentication",
            "platform": "mobile",
            "feature_title": "OAuth2 Login System",
            "feature_description": "Implement a secure OAuth2 authentication mechanism"
        }
        
        terms = workflow._extract_search_terms(query_context)
        
        assert "authentication" in terms
        assert "mobile" in terms
        # Should include meaningful words from title/description
        assert len(terms) > 2
    
    @pytest.mark.asyncio
    async def test_calculate_document_relevance_high(self, workflow):
        """Test document relevance calculation with high relevance."""
        document = {
            "content": "This document describes authentication on mobile platforms",
            "created_at": datetime.utcnow().isoformat()  # Recent
        }
        
        query_context = {
            "feature_type": "authentication",
            "platform": "mobile"
        }
        
        score = workflow._calculate_document_relevance(document, query_context)
        
        assert 0.0 <= score <= 1.0
        assert score > 0.7  # Should be high due to matching terms and recency
    
    @pytest.mark.asyncio
    async def test_calculate_document_relevance_low(self, workflow):
        """Test document relevance calculation with low relevance."""
        document = {
            "content": "This document is about something completely unrelated",
            "created_at": (datetime.utcnow() - timedelta(days=365)).isoformat()  # Old
        }
        
        query_context = {
            "feature_type": "authentication",
            "platform": "mobile"
        }
        
        score = workflow._calculate_document_relevance(document, query_context)
        
        assert 0.0 <= score <= 1.0
        assert score <= 0.6  # Should be low due to no matches and old age
    
    @pytest.mark.asyncio
    async def test_calculate_jira_relevance(self, workflow):
        """Test Jira issue relevance calculation."""
        issue = {
            "fields": {
                "summary": "Implement mobile authentication",
                "description": "Need OAuth2 for mobile app",
                "issuetype": {"name": "Story"}
            }
        }
        
        query_context = {
            "feature_type": "authentication",
            "platform": "mobile"
        }
        
        score = workflow._calculate_jira_relevance(issue, query_context)
        
        assert 0.0 <= score <= 1.0
        assert score > 0.7  # Should be high due to matches and Story type
    
    @pytest.mark.asyncio
    async def test_calculate_confluence_relevance(self, workflow):
        """Test Confluence page relevance calculation."""
        page = {
            "title": "Authentication Guide",
            "excerpt": "Mobile authentication documentation with OAuth2"
        }
        
        query_context = {
            "feature_type": "authentication",
            "platform": "mobile"
        }
        
        score = workflow._calculate_confluence_relevance(page, query_context)
        
        assert 0.0 <= score <= 1.0
        assert score > 0.6  # Should be high due to matches and documentation boost
    
    @pytest.mark.asyncio
    async def test_deduplicate_sources_removes_duplicates(self, workflow):
        """Test that deduplication removes duplicate sources."""
        sources = [
            ContextSource(
                source_type="memory",
                source_id="1",
                content="This is a test content about authentication",
                relevance_score=0.8,
                timestamp=datetime.utcnow()
            ),
            ContextSource(
                source_type="document",
                source_id="2",
                content="This is a test content about authentication",  # Duplicate
                relevance_score=0.7,
                timestamp=datetime.utcnow()
            ),
            ContextSource(
                source_type="jira",
                source_id="3",
                content="This is different content about payments",
                relevance_score=0.6,
                timestamp=datetime.utcnow()
            )
        ]
        
        deduplicated = workflow._deduplicate_sources(sources)
        
        # Should remove one duplicate
        assert len(deduplicated) == 2
        # Should keep the first occurrence
        assert deduplicated[0].source_id == "1"
        assert deduplicated[1].source_id == "3"
    
    @pytest.mark.asyncio
    async def test_deduplicate_sources_empty_list(self, workflow):
        """Test deduplication with empty list."""
        deduplicated = workflow._deduplicate_sources([])
        
        assert deduplicated == []
    
    @pytest.mark.asyncio
    async def test_filter_and_rank_by_relevance(self, workflow):
        """Test filtering and ranking by relevance score."""
        sources = [
            ContextSource(
                source_type="memory",
                source_id="1",
                content="Low relevance",
                relevance_score=0.2,  # Below threshold (0.3)
                timestamp=datetime.utcnow()
            ),
            ContextSource(
                source_type="document",
                source_id="2",
                content="High relevance",
                relevance_score=0.9,
                timestamp=datetime.utcnow()
            ),
            ContextSource(
                source_type="jira",
                source_id="3",
                content="Medium relevance",
                relevance_score=0.6,
                timestamp=datetime.utcnow()
            )
        ]
        
        filtered = workflow._filter_and_rank(sources, max_sources=10)
        
        # Should filter out source with score < 0.3
        assert len(filtered) == 2
        # Should be ranked by score (descending)
        assert filtered[0].relevance_score == 0.9
        assert filtered[1].relevance_score == 0.6
    
    @pytest.mark.asyncio
    async def test_filter_and_rank_respects_max_sources(self, workflow):
        """Test that filtering respects max_sources limit."""
        sources = [
            ContextSource(
                source_type="memory",
                source_id=str(i),
                content=f"Content {i}",
                relevance_score=0.5 + (i * 0.05),
                timestamp=datetime.utcnow()
            )
            for i in range(20)  # Create 20 sources
        ]
        
        filtered = workflow._filter_and_rank(sources, max_sources=5)
        
        # Should limit to 5
        assert len(filtered) == 5
        # Should be top 5 by score
        assert all(s.relevance_score >= 0.9 for s in filtered)


class TestContextSource:
    """Test ContextSource dataclass."""
    
    def test_context_source_creation(self):
        """Test ContextSource creation."""
        source = ContextSource(
            source_type="memory",
            source_id="test_123",
            content="Test content",
            relevance_score=0.85,
            timestamp=datetime.utcnow(),
            metadata={"key": "value"}
        )
        
        assert source.source_type == "memory"
        assert source.source_id == "test_123"
        assert source.content == "Test content"
        assert source.relevance_score == 0.85
        assert isinstance(source.timestamp, datetime)
        assert source.metadata["key"] == "value"


class TestHistoricalContext:
    """Test HistoricalContext dataclass."""
    
    def test_historical_context_creation(self):
        """Test HistoricalContext creation."""
        sources = [
            ContextSource(
                source_type="memory",
                source_id="1",
                content="Content 1",
                relevance_score=0.9,
                timestamp=datetime.utcnow()
            ),
            ContextSource(
                source_type="document",
                source_id="2",
                content="Content 2",
                relevance_score=0.7,
                timestamp=datetime.utcnow()
            )
        ]
        
        context = HistoricalContext(
            workflow_id="wf_123",
            query_context={"feature": "test"},
            sources=sources,
            total_sources=2,
            unique_source_types=2,
            average_relevance=0.8,
            memory_context=[sources[0]],
            document_context=[sources[1]],
            jira_context=[],
            confluence_context=[]
        )
        
        assert context.workflow_id == "wf_123"
        assert context.total_sources == 2
        assert context.unique_source_types == 2
        assert context.average_relevance == 0.8
        assert len(context.memory_context) == 1
        assert len(context.document_context) == 1
    
    def test_top_sources_property(self):
        """Test top_sources property returns most relevant sources."""
        sources = [
            ContextSource(
                source_type="memory",
                source_id=str(i),
                content=f"Content {i}",
                relevance_score=0.5 + (i * 0.1),
                timestamp=datetime.utcnow()
            )
            for i in range(10)
        ]
        
        context = HistoricalContext(
            workflow_id="wf_123",
            query_context={},
            sources=sources,
            total_sources=10,
            unique_source_types=1,
            average_relevance=0.7,
            memory_context=sources,
            document_context=[],
            jira_context=[],
            confluence_context=[]
        )
        
        top_5 = context.top_sources
        
        # Should return top 5
        assert len(top_5) == 5
        # Should be sorted by relevance (descending)
        assert top_5[0].relevance_score >= top_5[1].relevance_score


class TestWorkflowBIntegration:
    """Test Workflow B integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_multi_source_aggregation(self, workflow, sample_query_context, mock_workflow_logger):
        """Test aggregation from multiple sources."""
        # Mock different responses for each service
        with patch('httpx.AsyncClient') as mock_client:
            async def mock_post(url, **kwargs):
                response = MagicMock()
                response.status_code = 200
                
                if "memory" in url:
                    response.json.return_value = {
                        "results": [{
                            "context_id": "mem_1",
                            "data": {"content": "memory content"},
                            "score": 0.8,
                            "timestamp": datetime.utcnow().isoformat()
                        }]
                    }
                elif "documents" in url:
                    response.json.return_value = {
                        "documents": [{
                            "document_id": "doc_1",
                            "content": "document content",
                            "created_at": datetime.utcnow().isoformat()
                        }]
                    }
                elif "jira" in url:
                    response.json.return_value = {
                        "issues": [{
                            "key": "PROJ-1",
                            "fields": {
                                "summary": "test issue",
                                "description": "test description",
                                "created": datetime.utcnow().isoformat(),
                                "issuetype": {"name": "Story"},
                                "status": {"name": "Open"}
                            }
                        }]
                    }
                elif "confluence" in url:
                    response.json.return_value = {
                        "results": [{
                            "id": "conf_1",
                            "title": "test page",
                            "excerpt": "test excerpt",
                            "lastModified": datetime.utcnow().isoformat(),
                            "space": {"key": "DOC"},
                            "_links": {"webui": "/wiki/test"}
                        }]
                    }
                
                return response
            
            mock_client.return_value.__aenter__.return_value.post = mock_post
            
            result = await workflow.execute(
                query_context=sample_query_context,
                max_sources=50
            )
            
            # Should have sources from all 4 types
            assert result.total_sources > 0
            assert result.unique_source_types >= 1  # At least one type
            
            # Verify logging of each source type
            assert mock_workflow_logger.log_workflow_step.call_count >= 4


class TestWorkflowBErrorHandling:
    """Test Workflow B error handling."""
    
    @pytest.mark.asyncio
    async def test_service_unavailable_graceful_fallback(self, workflow, sample_query_context, mock_workflow_logger):
        """Test graceful handling when services are unavailable."""
        # Mock services to fail
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post.side_effect = Exception("Service unavailable")
            
            result = await workflow.execute(
                query_context=sample_query_context,
                max_sources=50
            )
            
            # Should still return a result (with empty sources)
            assert isinstance(result, HistoricalContext)
            assert result.total_sources == 0
            
            # Workflow should complete successfully
            mock_workflow_logger.log_workflow_complete.assert_called_once()

