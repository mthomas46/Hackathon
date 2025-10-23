"""
Unit tests for DynamicTimelineConstructor.

Tests dynamic timeline building from document sets.
"""

import pytest
from datetime import datetime, timedelta
from src.services.dynamic_rag.dynamic_timeline_constructor import (
    DynamicTimelineConstructor, DynamicTimeline, DynamicPeriod, 
    DynamicPeriodStrategy
)
from src.services.dynamic_rag.document_finder import RelevantDocument


@pytest.mark.asyncio
class TestDynamicTimelineConstructorBasic:
    """Test basic timeline construction."""
    
    async def test_constructor_instantiation(self):
        """Test that constructor can be instantiated."""
        constructor = DynamicTimelineConstructor()
        assert constructor is not None
    
    async def test_build_timeline_empty_documents(self):
        """Test building timeline with empty document list."""
        constructor = DynamicTimelineConstructor()
        
        result = await constructor.construct_timeline(
            documents=[],
            timeline_name="test timeline"
        )
        
        assert result is not None
        assert isinstance(result, DynamicTimeline)
        # May have default periods even with no documents
        assert len(result.documents) == 0
    
    async def test_build_timeline_single_document(self):
        """Test building timeline with single document."""
        constructor = DynamicTimelineConstructor()
        
        doc = RelevantDocument(
            document_id="doc1",
            file_path="/test.md",
            content="Test content",
            relevance_score=0.8,
            commit_count=5,
            last_modified=datetime.utcnow(),
            ingestion_mode="git_history",
            matched_topics=["test"]
        )
        
        result = await constructor.construct_timeline(
            documents=[doc],
            timeline_name="test timeline"
        )
        
        assert result is not None
        assert isinstance(result, DynamicTimeline)
        assert len(result.documents) == 1
    
    async def test_build_timeline_multiple_documents(self):
        """Test building timeline with multiple documents."""
        constructor = DynamicTimelineConstructor()
        
        now = datetime.utcnow()
        docs = [
            RelevantDocument(
                document_id=f"doc{i}",
                file_path=f"/test{i}.md",
                content=f"Content {i}",
                relevance_score=0.8,
                commit_count=i,
                last_modified=now - timedelta(days=i*30),
                ingestion_mode="git_history",
                matched_topics=["test"]
            )
            for i in range(5)
        ]
        
        result = await constructor.construct_timeline(
            documents=docs,
            timeline_name="test timeline"
        )
        
        assert result is not None
        assert isinstance(result, DynamicTimeline)
        assert len(result.documents) == 5


@pytest.mark.asyncio
class TestDynamicTimelineConstructorPeriodGeneration:
    """Test period generation strategies."""
    
    async def test_auto_generate_periods_monthly(self):
        """Test auto-generating monthly periods."""
        constructor = DynamicTimelineConstructor()
        
        now = datetime.utcnow()
        docs = [
            RelevantDocument(
                document_id=f"doc{i}",
                file_path=f"/test{i}.md",
                content=f"Content {i}",
                relevance_score=0.8,
                commit_count=5,
                last_modified=now - timedelta(days=i*30),
                ingestion_mode="git_history",
                matched_topics=["test"]
            )
            for i in range(6)  # 6 months of docs
        ]
        
        result = await constructor.construct_timeline(
            documents=docs,
            timeline_name="test timeline",
            period_strategy=DynamicPeriodStrategy.MONTHLY
        )
        
        assert result is not None
        assert len(result.periods) > 0
        # Should have created monthly periods
        for period in result.periods:
            assert isinstance(period, DynamicPeriod)
    
    async def test_auto_generate_periods_adaptive(self):
        """Test auto-generating adaptive periods."""
        constructor = DynamicTimelineConstructor()
        
        now = datetime.utcnow()
        docs = [
            RelevantDocument(
                document_id=f"doc{i}",
                file_path=f"/test{i}.md",
                content=f"Content {i}",
                relevance_score=0.8,
                commit_count=5,
                last_modified=now - timedelta(days=i*10),
                ingestion_mode="git_history",
                matched_topics=["test"]
            )
            for i in range(10)
        ]
        
        result = await constructor.construct_timeline(
            documents=docs,
            timeline_name="test timeline",
            period_strategy=DynamicPeriodStrategy.ADAPTIVE
        )
        
        assert result is not None
        assert len(result.periods) > 0
    
    async def test_periods_ordered_chronologically(self):
        """Test that periods are ordered chronologically."""
        constructor = DynamicTimelineConstructor()
        
        now = datetime.utcnow()
        docs = [
            RelevantDocument(
                document_id=f"doc{i}",
                file_path=f"/test{i}.md",
                content=f"Content {i}",
                relevance_score=0.8,
                commit_count=5,
                last_modified=now - timedelta(days=i*30),
                ingestion_mode="git_history",
                matched_topics=["test"]
            )
            for i in range(4)
        ]
        
        result = await constructor.construct_timeline(
            documents=docs,
            timeline_name="test timeline"
        )
        
        if len(result.periods) > 1:
            # Check that periods are ordered
            for i in range(len(result.periods) - 1):
                assert result.periods[i].start_date <= result.periods[i+1].start_date


@pytest.mark.asyncio
class TestDynamicTimelineConstructorConfidence:
    """Test confidence calculation."""
    
    async def test_calculate_confidence_all_git_history(self):
        """Test confidence with all git_history documents."""
        constructor = DynamicTimelineConstructor()
        
        now = datetime.utcnow()
        docs = [
            RelevantDocument(
                document_id=f"doc{i}",
                file_path=f"/test{i}.md",
                content=f"Content {i}",
                relevance_score=0.8,
                commit_count=10,
                last_modified=now - timedelta(days=i*10),
                ingestion_mode="git_history",
                matched_topics=["test"]
            )
            for i in range(5)
        ]
        
        result = await constructor.construct_timeline(
            documents=docs,
            timeline_name="test timeline"
        )
        
        # Should have high confidence
        assert result.confidence in ["HIGH", "MEDIUM"]
    
    async def test_calculate_confidence_mixed_sources(self):
        """Test confidence with mixed document sources."""
        constructor = DynamicTimelineConstructor()
        
        now = datetime.utcnow()
        docs = [
            RelevantDocument(
                document_id=f"doc{i}",
                file_path=f"/test{i}.md",
                content=f"Content {i}",
                relevance_score=0.8,
                commit_count=5 if i % 2 == 0 else 0,
                last_modified=now - timedelta(days=i*10),
                ingestion_mode="git_history" if i % 2 == 0 else "snapshot",
                matched_topics=["test"]
            )
            for i in range(6)
        ]
        
        result = await constructor.construct_timeline(
            documents=docs,
            timeline_name="test timeline"
        )
        
        # Should have medium confidence
        assert result.confidence in ["HIGH", "MEDIUM", "LOW"]
    
    async def test_calculate_confidence_no_git_history(self):
        """Test confidence with no git history documents."""
        constructor = DynamicTimelineConstructor()
        
        now = datetime.utcnow()
        docs = [
            RelevantDocument(
                document_id=f"doc{i}",
                file_path=f"/test{i}.md",
                content=f"Content {i}",
                relevance_score=0.8,
                commit_count=0,
                last_modified=now - timedelta(days=i*10),
                ingestion_mode="snapshot",
                matched_topics=["test"]
            )
            for i in range(5)
        ]
        
        result = await constructor.construct_timeline(
            documents=docs,
            timeline_name="test timeline"
        )
        
        # Should have low confidence
        assert result.confidence in ["LOW", "NONE"]


@pytest.mark.asyncio
class TestDynamicTimelineConstructorMetadata:
    """Test timeline metadata generation."""
    
    async def test_timeline_includes_date_range(self):
        """Test that timeline includes date range."""
        constructor = DynamicTimelineConstructor()
        
        now = datetime.utcnow()
        docs = [
            RelevantDocument(
                document_id=f"doc{i}",
                file_path=f"/test{i}.md",
                content=f"Content {i}",
                relevance_score=0.8,
                commit_count=5,
                last_modified=now - timedelta(days=i*30),
                ingestion_mode="git_history",
                matched_topics=["test"]
            )
            for i in range(4)
        ]
        
        result = await constructor.construct_timeline(
            documents=docs,
            timeline_name="test timeline"
        )
        
        assert result.start_date is not None
        assert result.end_date is not None
        assert result.start_date <= result.end_date
    
    async def test_timeline_includes_name(self):
        """Test that timeline includes name."""
        constructor = DynamicTimelineConstructor()
        
        timeline_name = "Authentication Timeline"
        doc = RelevantDocument(
            document_id="doc1",
            file_path="/test.md",
            content="Content",
            relevance_score=0.8,
            commit_count=5,
            last_modified=datetime.utcnow(),
            ingestion_mode="git_history",
            matched_topics=["authentication"]
        )
        
        result = await constructor.construct_timeline(
            documents=[doc],
            timeline_name=timeline_name
        )
        
        assert result.name == timeline_name
    
    async def test_timeline_includes_document_count(self):
        """Test that timeline tracks document count."""
        constructor = DynamicTimelineConstructor()
        
        docs = [
            RelevantDocument(
                document_id=f"doc{i}",
                file_path=f"/test{i}.md",
                content=f"Content {i}",
                relevance_score=0.8,
                commit_count=5,
                last_modified=datetime.utcnow(),
                ingestion_mode="git_history",
                matched_topics=["test"]
            )
            for i in range(7)
        ]
        
        result = await constructor.construct_timeline(
            documents=docs,
            timeline_name="test timeline"
        )
        
        assert len(result.documents) == 7


@pytest.mark.asyncio
class TestDynamicTimelineConstructorEdgeCases:
    """Test edge cases and error handling."""
    
    async def test_documents_with_null_dates(self):
        """Test handling documents with None last_modified."""
        constructor = DynamicTimelineConstructor()
        
        doc = RelevantDocument(
            document_id="doc1",
            file_path="/test.md",
            content="Content",
            relevance_score=0.8,
            commit_count=5,
            last_modified=None,  # Could be None in some cases
            ingestion_mode="git_history",
            matched_topics=["test"]
        )
        
        # Should handle gracefully
        result = await constructor.construct_timeline(
            documents=[doc],
            timeline_name="test timeline"
        )
        
        assert result is not None
    
    async def test_documents_with_future_dates(self):
        """Test handling documents with future dates."""
        constructor = DynamicTimelineConstructor()
        
        future_date = datetime.utcnow() + timedelta(days=365)
        doc = RelevantDocument(
            document_id="doc1",
            file_path="/test.md",
            content="Content",
            relevance_score=0.8,
            commit_count=5,
            last_modified=future_date,
            ingestion_mode="git_history",
            matched_topics=["test"]
        )
        
        result = await constructor.construct_timeline(
            documents=[doc],
            timeline_name="test timeline"
        )
        
        assert result is not None
    
    async def test_very_old_documents(self):
        """Test handling very old documents (years old)."""
        constructor = DynamicTimelineConstructor()
        
        old_date = datetime.utcnow() - timedelta(days=3650)  # 10 years old
        doc = RelevantDocument(
            document_id="doc1",
            file_path="/test.md",
            content="Content",
            relevance_score=0.8,
            commit_count=100,
            last_modified=old_date,
            ingestion_mode="git_history",
            matched_topics=["test"]
        )
        
        result = await constructor.construct_timeline(
            documents=[doc],
            timeline_name="test timeline"
        )
        
        assert result is not None
        assert result.start_date is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

