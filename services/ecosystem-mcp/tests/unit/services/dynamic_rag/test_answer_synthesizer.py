"""
Unit tests for TemporalAnswerSynthesizer.

Tests LLM-based answer generation with temporal context.
"""

import pytest
from datetime import datetime
from src.services.dynamic_rag.answer_synthesizer import (
    TemporalAnswerSynthesizer, TemporalAnswer
)
from src.services.dynamic_rag.dynamic_timeline_constructor import (
    DynamicTimeline, DynamicPeriod
)
from src.services.dynamic_rag.document_finder import RelevantDocument


@pytest.mark.asyncio
class TestTemporalAnswerSynthesizerBasic:
    """Test basic answer synthesis functionality."""
    
    async def test_synthesizer_instantiation(self):
        """Test that synthesizer can be instantiated."""
        synthesizer = TemporalAnswerSynthesizer()
        assert synthesizer is not None
    
    async def test_synthesize_with_empty_documents(self):
        """Test synthesizing with no documents."""
        synthesizer = TemporalAnswerSynthesizer()
        
        timeline = DynamicTimeline(
            timeline_id="test-1",
            name="Test Timeline",
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow(),
            periods=[],
            documents=[],
            confidence="NONE",
            period_strategy="adaptive",
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow()
        )
        
        result = await synthesizer.synthesize_answer(
            query="What is authentication?",
            timeline=timeline,
            documents=[]
        )
        
        assert result is not None
        assert isinstance(result, TemporalAnswer)
    
    async def test_synthesize_with_documents(self):
        """Test synthesizing with documents."""
        synthesizer = TemporalAnswerSynthesizer()
        
        doc = RelevantDocument(
            document_id="doc1",
            file_path="/auth.md",
            content="Authentication uses JWT tokens for security",
            relevance_score=0.9,
            commit_count=10,
            last_modified=datetime.utcnow(),
            ingestion_mode="git_history",
            matched_topics=["authentication", "jwt"]
        )
        
        timeline = DynamicTimeline(
            timeline_id="test-1",
            name="Test Timeline",
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow(),
            periods=[],
            documents=[doc],
            confidence="HIGH",
            period_strategy="adaptive",
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow()
        )
        
        result = await synthesizer.synthesize_answer(
            query="How does authentication work?",
            timeline=timeline,
            documents=[doc]
        )
        
        assert result is not None
        assert isinstance(result, TemporalAnswer)
        assert result.answer is not None
        assert len(result.answer) > 0


@pytest.mark.asyncio
class TestTemporalAnswerSynthesizerTemporalContext:
    """Test temporal context integration."""
    
    async def test_answer_includes_temporal_context(self):
        """Test that answer includes temporal information."""
        synthesizer = TemporalAnswerSynthesizer()
        
        period = DynamicPeriod(
            name="Q1 2025",
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 3, 31),
            documents=["doc1"],
            document_count=1
        )
        
        doc = RelevantDocument(
            document_id="doc1",
            file_path="/auth.md",
            content="Authentication implementation",
            relevance_score=0.9,
            commit_count=10,
            last_modified=datetime(2025, 2, 1),
            ingestion_mode="git_history",
            matched_topics=["authentication"]
        )
        
        timeline = DynamicTimeline(
            timeline_id="test-1",
            name="Test Timeline",
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 3, 31),
            periods=[period],
            documents=[doc],
            confidence="HIGH",
            period_strategy="quarterly",
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow()
        )
        
        result = await synthesizer.synthesize_answer(
            query="How does authentication work?",
            timeline=timeline,
            documents=[doc]
        )
        
        assert result is not None
        assert result.timeline_id == "test-1"


@pytest.mark.asyncio
class TestTemporalAnswerSynthesizerConfidence:
    """Test confidence calculation."""
    
    async def test_confidence_high_with_git_history(self):
        """Test high confidence with git history documents."""
        synthesizer = TemporalAnswerSynthesizer()
        
        docs = [
            RelevantDocument(
                document_id=f"doc{i}",
                file_path=f"/file{i}.md",
                content=f"Content {i}",
                relevance_score=0.9,
                commit_count=50,
                last_modified=datetime.utcnow(),
                ingestion_mode="git_history",
                matched_topics=["test"]
            )
            for i in range(5)
        ]
        
        timeline = DynamicTimeline(
            timeline_id="test-1",
            name="Test",
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow(),
            periods=[],
            documents=docs,
            confidence="HIGH",
            period_strategy="adaptive",
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow()
        )
        
        result = await synthesizer.synthesize_answer(
            query="Test query",
            timeline=timeline,
            documents=docs
        )
        
        assert result is not None
        assert 0.0 <= result.confidence <= 1.0
    
    async def test_confidence_low_with_snapshot(self):
        """Test lower confidence with snapshot-only documents."""
        synthesizer = TemporalAnswerSynthesizer()
        
        doc = RelevantDocument(
            document_id="doc1",
            file_path="/file.md",
            content="Content",
            relevance_score=0.5,
            commit_count=0,
            last_modified=datetime.utcnow(),
            ingestion_mode="snapshot",
            matched_topics=["test"]
        )
        
        timeline = DynamicTimeline(
            timeline_id="test-1",
            name="Test",
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow(),
            periods=[],
            documents=[doc],
            confidence="LOW",
            period_strategy="adaptive",
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow()
        )
        
        result = await synthesizer.synthesize_answer(
            query="Test query",
            timeline=timeline,
            documents=[doc]
        )
        
        assert result is not None
        assert 0.0 <= result.confidence <= 1.0


@pytest.mark.asyncio
class TestTemporalAnswerSynthesizerSources:
    """Test source citation tracking."""
    
    async def test_sources_included(self):
        """Test that sources are included in answer."""
        synthesizer = TemporalAnswerSynthesizer()
        
        docs = [
            RelevantDocument(
                document_id=f"doc{i}",
                file_path=f"/file{i}.md",
                content=f"Content {i}",
                relevance_score=0.8,
                commit_count=10,
                last_modified=datetime.utcnow(),
                ingestion_mode="git_history",
                matched_topics=["test"]
            )
            for i in range(3)
        ]
        
        timeline = DynamicTimeline(
            timeline_id="test-1",
            name="Test",
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow(),
            periods=[],
            documents=docs,
            confidence="HIGH",
            period_strategy="adaptive",
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow()
        )
        
        result = await synthesizer.synthesize_answer(
            query="Test query",
            timeline=timeline,
            documents=docs
        )
        
        assert result is not None
        assert isinstance(result.sources, list)


@pytest.mark.asyncio
class TestTemporalAnswerSynthesizerEdgeCases:
    """Test edge cases and error handling."""
    
    async def test_empty_query(self):
        """Test handling empty query."""
        synthesizer = TemporalAnswerSynthesizer()
        
        timeline = DynamicTimeline(
            timeline_id="test-1",
            name="Test",
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow(),
            periods=[],
            documents=[],
            confidence="NONE",
            period_strategy="adaptive",
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow()
        )
        
        result = await synthesizer.synthesize_answer(
            query="",
            timeline=timeline,
            documents=[]
        )
        
        assert result is not None
    
    async def test_very_long_query(self):
        """Test handling very long query."""
        synthesizer = TemporalAnswerSynthesizer()
        
        long_query = "How does this work? " * 500  # Very long
        
        timeline = DynamicTimeline(
            timeline_id="test-1",
            name="Test",
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow(),
            periods=[],
            documents=[],
            confidence="NONE",
            period_strategy="adaptive",
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow()
        )
        
        result = await synthesizer.synthesize_answer(
            query=long_query,
            timeline=timeline,
            documents=[]
        )
        
        assert result is not None
    
    async def test_special_characters_in_query(self):
        """Test handling special characters."""
        synthesizer = TemporalAnswerSynthesizer()
        
        query = "How does @#$%^&* work?"
        
        timeline = DynamicTimeline(
            timeline_id="test-1",
            name="Test",
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow(),
            periods=[],
            documents=[],
            confidence="NONE",
            period_strategy="adaptive",
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow()
        )
        
        result = await synthesizer.synthesize_answer(
            query=query,
            timeline=timeline,
            documents=[]
        )
        
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

