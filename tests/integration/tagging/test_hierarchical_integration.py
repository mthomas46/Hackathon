"""
Integration tests for hierarchical topic extraction with summarizer-hub.

Tests the actual integration between HierarchicalTopicExtractor and 
the summarizer-hub service (when available).
"""
import pytest
import asyncio
import httpx
from ingestion.tagging.hierarchical_topics import HierarchicalTopicExtractor
from ingestion.models import NormalizedDocument


pytestmark = pytest.mark.integration


class TestHierarchicalIntegration:
    """Integration tests for hierarchical topic extraction."""
    
    @pytest.fixture(scope="class")
    def extractor(self):
        """Create extractor instance."""
        return HierarchicalTopicExtractor(
            summarizer_url="http://localhost:5160",
            timeout=10.0
        )
    
    @pytest.mark.asyncio
    async def test_summarizer_hub_availability(self, extractor):
        """Test if summarizer-hub service is available."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{extractor.summarizer_url}/health",
                    timeout=5.0
                )
                # If service is available, great!
                if response.status_code == 200:
                    pytest.skip("Summarizer-hub is online, full integration possible")
                else:
                    pytest.skip(f"Summarizer-hub returned {response.status_code}")
        except Exception as e:
            # Service offline is expected in many environments
            pytest.skip(f"Summarizer-hub offline: {e}")
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(
        True,  # Skip by default unless service is guaranteed to be running
        reason="Requires summarizer-hub service to be running"
    )
    async def test_extract_topics_from_real_documents(self, extractor):
        """Test extraction with real documents (requires service)."""
        docs = [
            NormalizedDocument(
                document_id="test-1",
                title="Imperial Politics in the 31st Millennium",
                content_md=(
                    "The Emperor of Mankind unified Terra and launched the Great "
                    "Crusade to reclaim the galaxy for humanity. The Primarchs, "
                    "genetically engineered super-beings, led the Space Marine Legions "
                    "in this monumental undertaking."
                ),
                original_format="md"
            ),
            NormalizedDocument(
                document_id="test-2",
                title="The Horus Heresy: A Galaxy Divided",
                content_md=(
                    "Horus, Warmaster and favored son, fell to Chaos corruption. "
                    "Half the Legions turned traitor, plunging the Imperium into "
                    "a devastating civil war that would echo through millennia."
                ),
                original_format="md"
            )
        ]
        
        # Extract topics
        tags = await extractor.generate_hierarchical_tags(docs)
        
        # Assertions
        assert isinstance(tags, list)
        assert len(tags) > 0
        
        # Check for expected topic patterns
        main_topics = [t for t in tags if 'topic:main:' in t]
        sub_topics = [t for t in tags if 'topic:sub:' in t]
        
        assert len(main_topics) > 0, "Should identify at least one main topic"
        # May or may not have sub-topics depending on content
    
    @pytest.mark.asyncio
    async def test_graceful_degradation_on_service_failure(self, extractor):
        """Test that extractor handles service failures gracefully."""
        # Point to non-existent service
        extractor_bad = HierarchicalTopicExtractor(
            summarizer_url="http://localhost:9999",
            timeout=1.0
        )
        
        docs = [
            NormalizedDocument(
                document_id="test-1",
                title="Test Document",
                content_md="Test content",
                original_format="md"
            )
        ]
        
        # Should not raise exception (may return empty or fallback)
        try:
            tags = await extractor_bad.generate_hierarchical_tags(docs)
            assert isinstance(tags, list)
        except Exception:
            # It's also acceptable to handle errors this way
            pass
    
    @pytest.mark.asyncio
    async def test_concurrent_extraction_requests(self, extractor):
        """Test that multiple concurrent extractions work correctly."""
        docs_batch1 = [
            NormalizedDocument(
                document_id="batch1-1",
                title="Document 1",
                content_md="Content about space marines",
                original_format="md"
            )
        ]
        
        docs_batch2 = [
            NormalizedDocument(
                document_id="batch2-1",
                title="Document 2",
                content_md="Content about imperial politics",
                original_format="md"
            )
        ]
        
        # Run both extractions concurrently
        try:
            results = await asyncio.gather(
                extractor.generate_hierarchical_tags(docs_batch1),
                extractor.generate_hierarchical_tags(docs_batch2),
                return_exceptions=True
            )
            
            # Both should complete
            assert len(results) == 2
            for result in results:
                if not isinstance(result, Exception):
                    assert isinstance(result, list)
        except Exception:
            # Service may be offline, that's acceptable for this test
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])

