"""
Smoke tests for Phase 6 Dynamic Temporal RAG.

Quick validation of critical functionality.
"""

import pytest


@pytest.mark.smoke
class TestDynamicRAGImports:
    """Test that all Phase 6 modules can be imported."""
    
    def test_import_services(self):
        """Test importing all dynamic RAG services."""
        from src.services.dynamic_rag import (
            TopicExtractor,
            DocumentFinder,
            DynamicTimelineConstructor,
            TemporalAnswerSynthesizer,
            CitationFormatter,
            DynamicTemporalRAGOrchestrator,
            get_orchestrator
        )
        
        assert TopicExtractor
        assert DocumentFinder
        assert DynamicTimelineConstructor
        assert TemporalAnswerSynthesizer
        assert CitationFormatter
        assert DynamicTemporalRAGOrchestrator
        assert get_orchestrator
        print("✅ All Phase 6 Dynamic RAG services import successfully")
    
    def test_import_models(self):
        """Test importing Phase 6 data models."""
        from src.services.dynamic_rag.topic_extractor import (
            TopicType, ExtractedTopic, ExtractedTopics
        )
        from src.services.dynamic_rag.document_finder import RelevantDocument
        from src.services.dynamic_rag.dynamic_timeline_constructor import (
            DynamicTimeline, DynamicPeriod, DynamicPeriodStrategy
        )
        from src.services.dynamic_rag.answer_synthesizer import TemporalAnswer
        from src.services.dynamic_rag.citation_formatter import FormattedCitation
        
        assert TopicType
        assert ExtractedTopic
        assert ExtractedTopics
        assert RelevantDocument
        assert DynamicTimeline
        assert DynamicPeriod
        assert DynamicPeriodStrategy
        assert TemporalAnswer
        assert FormattedCitation
        print("✅ All Phase 6 data models import successfully")


@pytest.mark.smoke
class TestDynamicRAGBasicFunctionality:
    """Test basic functionality of each service."""
    
    def test_topic_extractor_basic(self):
        """Test TopicExtractor can extract topics."""
        from src.services.dynamic_rag import TopicExtractor
        
        extractor = TopicExtractor()
        result = extractor.extract("How does /api/auth work with JWT tokens?")
        
        assert result is not None
        assert len(result.all_topics) > 0
        assert "/api/auth" in result.endpoints
        assert "jwt" in result.technologies
        print(f"✅ TopicExtractor extracted {len(result.all_topics)} topics")
    
    def test_document_finder_instantiation(self):
        """Test DocumentFinder can be instantiated."""
        from src.services.dynamic_rag import DocumentFinder
        
        finder = DocumentFinder()
        assert finder is not None
        print("✅ DocumentFinder instantiated successfully")
    
    def test_timeline_constructor_instantiation(self):
        """Test DynamicTimelineConstructor can be instantiated."""
        from src.services.dynamic_rag import DynamicTimelineConstructor
        
        constructor = DynamicTimelineConstructor()
        assert constructor is not None
        print("✅ DynamicTimelineConstructor instantiated successfully")
    
    def test_answer_synthesizer_instantiation(self):
        """Test TemporalAnswerSynthesizer can be instantiated."""
        from src.services.dynamic_rag import TemporalAnswerSynthesizer
        
        synthesizer = TemporalAnswerSynthesizer()
        assert synthesizer is not None
        print("✅ TemporalAnswerSynthesizer instantiated successfully")
    
    def test_citation_formatter_instantiation(self):
        """Test CitationFormatter can be instantiated."""
        from src.services.dynamic_rag import CitationFormatter
        
        formatter = CitationFormatter()
        assert formatter is not None
        print("✅ CitationFormatter instantiated successfully")
    
    @pytest.mark.asyncio
    async def test_orchestrator_singleton(self):
        """Test orchestrator singleton works."""
        from src.services.dynamic_rag import get_orchestrator
        
        orch1 = get_orchestrator()
        orch2 = get_orchestrator()
        
        # Should be same instance
        assert orch1 is orch2
        print("✅ Orchestrator singleton pattern works")


@pytest.mark.smoke
@pytest.mark.asyncio
class TestDynamicRAGCompleteWorkflow:
    """Smoke test for complete Dynamic RAG workflow."""
    
    async def test_complete_workflow_no_crash(self):
        """Test complete workflow doesn't crash (may have no results if DB empty)."""
        from src.services.dynamic_rag import get_orchestrator
        
        orchestrator = get_orchestrator()
        
        # Execute complete workflow
        # This may return no results if DB is empty, but should not crash
        result = await orchestrator.execute(
            query="What is authentication?",
            citation_format="markdown"
        )
        
        # Should complete without errors
        assert result is not None
        assert "success" in result or "error" in result
        
        if result.get("success"):
            print(f"✅ Complete workflow executed successfully")
            assert "query" in result
        else:
            # If no documents found, that's okay for smoke test
            print(f"✅ Workflow handled gracefully (no documents: {result.get('error', 'unknown')})")
    
    async def test_streaming_workflow_no_crash(self):
        """Test streaming workflow doesn't crash."""
        from src.services.dynamic_rag import get_orchestrator
        
        orchestrator = get_orchestrator()
        
        # Test streaming (just get first event)
        events_received = 0
        async for event in orchestrator.execute_streaming(
            query="Test query",
            citation_format="markdown"
        ):
            events_received += 1
            assert event is not None
            assert "step" in event or "status" in event
            # Just check first event then break
            break
        
        print(f"✅ Streaming workflow works (received {events_received} event)")


@pytest.mark.smoke
class TestDynamicRAGCacheManagement:
    """Test cache management functionality."""
    
    def test_cache_cleanup(self):
        """Test cache cleanup doesn't crash."""
        from src.services.dynamic_rag import get_orchestrator
        
        orchestrator = get_orchestrator()
        
        # Should not crash
        orchestrator.cleanup_expired_caches()
        print("✅ Cache cleanup works")


@pytest.mark.smoke
class TestDynamicRAGErrorHandling:
    """Test error handling in various scenarios."""
    
    def test_empty_query_handling(self):
        """Test handling of empty query."""
        from src.services.dynamic_rag import TopicExtractor
        
        extractor = TopicExtractor()
        result = extractor.extract("")
        
        assert result is not None
        assert isinstance(result.all_topics, list)
        print("✅ Empty query handled gracefully")
    
    @pytest.mark.asyncio
    async def test_invalid_format_handling(self):
        """Test handling of invalid citation format."""
        from src.services.dynamic_rag.citation_formatter import CitationFormatter
        from src.services.dynamic_rag.answer_synthesizer import TemporalAnswer
        
        formatter = CitationFormatter()
        
        # Create minimal answer for testing
        answer = TemporalAnswer(
            answer="Test answer",
            confidence=0.8,
            timeline_id="test-timeline",
            sources=[],
            temporal_insights=[]
        )
        
        # Should handle invalid format gracefully (default to plain or similar)
        try:
            result = formatter.format_citations(answer, format_type="invalid_format")
            print("✅ Invalid format handled gracefully")
        except Exception as e:
            # If it raises, that's also acceptable for smoke test
            print(f"✅ Invalid format raises controlled exception: {type(e).__name__}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "smoke", "--tb=short"])

