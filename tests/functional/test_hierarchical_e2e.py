"""
Functional (E2E) tests for hierarchical tagging workflow.

Tests the complete end-to-end flow from document ingestion through
topic extraction to document generation.
"""
import pytest
from pathlib import Path
from ingestion.fandom_ingestor import FandomWikiIngestor
from ingestion.tagging import UniversalTaggingManager, UniversalTaggingConfig
from ingestion.utils.document_processor import DocumentProcessor


pytestmark = pytest.mark.functional


class TestHierarchicalE2E:
    """End-to-end functional tests for hierarchical tagging."""
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(
        True,  # Skip by default to avoid network calls
        reason="Requires network access and can be slow"
    )
    async def test_complete_workflow_with_real_crawl(self):
        """Test complete workflow: crawl → tag → organize → generate."""
        # Step 1: Crawl a page
        ingestor = FandomWikiIngestor(
            base_url="https://warhammer40k.fandom.com"
        )
        
        result = await ingestor.crawl_page(
            page_title="Horus_Heresy",
            max_depth=1,  # Shallow crawl
            max_surface_links=3
        )
        
        assert len(result.documents) > 0
        
        # Step 2: Apply tagging (with hierarchical topics if available)
        tagging_config = UniversalTaggingConfig(
            enable_contextual_tags=True,
            enable_hierarchical_topics=True,
            summarizer_url="http://localhost:5160"
        )
        
        tagging_manager = UniversalTaggingManager(tagging_config)
        tag_collection = await tagging_manager.tag_documents(result.documents)
        
        assert tag_collection is not None
        assert len(tag_collection.all_tags) > 0
        
        # Step 3: Organize documents by hierarchy
        processor = DocumentProcessor()
        hierarchical_tags = tag_collection.to_dict().get('hierarchical', [])
        
        if hierarchical_tags:
            # Convert documents to sections format
            sections = [
                (doc.title, doc.content_md, doc.metadata.get('page_url', ''), 1.0)
                for doc in result.documents
            ]
            
            organized = processor.organize_by_hierarchical_topics(
                sections=sections,
                hierarchical_tags=hierarchical_tags
            )
            
            assert 'main' in organized
            assert 'sub' in organized
            assert 'related' in organized
            
            # Step 4: Generate structured document
            document = processor.create_hierarchical_document_structure(
                main_sections=organized['main'],
                sub_sections=organized['sub'],
                related_sections=organized['related']
            )
            
            assert len(document) > 0
            assert "## Primary Topics" in document or "## Supporting Details" in document
    
    def test_document_processor_with_mock_data(self):
        """Test DocumentProcessor with mock hierarchical tags."""
        processor = DocumentProcessor()
        
        # Mock sections
        sections = [
            ("Horus Heresy Overview", "Content about the Horus Heresy", "url1", 0.9),
            ("Space Marine Legions", "Content about Space Marines", "url2", 0.8),
            ("The Emperor", "Content about the Emperor", "url3", 0.85),
            ("Chaos Gods", "Content about Chaos", "url4", 0.7),
        ]
        
        # Mock hierarchical tags
        hierarchical_tags = [
            "topic:main:horus-heresy",
            "topic:main:space-marines",
            "topic:sub:emperor",
            "topic:related:chaos"
        ]
        
        # Organize
        organized = processor.organize_by_hierarchical_topics(
            sections=sections,
            hierarchical_tags=hierarchical_tags
        )
        
        assert len(organized['main']) > 0
        assert len(organized['sub']) > 0
        assert len(organized['related']) > 0
        
        # Generate document
        document = processor.create_hierarchical_document_structure(
            main_sections=organized['main'][:2],
            sub_sections=organized['sub'][:2],
            related_sections=organized['related'][:1]
        )
        
        assert "## Primary Topics" in document
        assert "## Supporting Details" in document
        assert "## Related Context" in document
    
    def test_fallback_when_no_hierarchical_tags(self):
        """Test that system works without hierarchical tags."""
        processor = DocumentProcessor()
        
        sections = [
            ("Test 1", "Content 1", "url1", 0.9),
            ("Test 2", "Content 2", "url2", 0.8),
        ]
        
        # No hierarchical tags
        organized = processor.organize_by_hierarchical_topics(
            sections=sections,
            hierarchical_tags=None
        )
        
        # Should fall back to putting everything in main
        assert len(organized['main']) > 0
        assert len(organized['sub']) == 0
        assert len(organized['related']) == 0
    
    def test_tag_collection_hierarchical_breakdown(self):
        """Test that TagCollection properly tracks hierarchical tags."""
        from ingestion.tagging.tag_collection import TagCollection, TagType
        
        collection = TagCollection()
        collection.add_tags([
            "topic:main:space-marines",
            "topic:sub:legion-organization",
            "topic:related:great-crusade"
        ], TagType.HIERARCHICAL)
        
        breakdown = collection.breakdown  # This is a property, not a method
        assert isinstance(breakdown, dict)
        assert 'hierarchical' in breakdown
        assert breakdown['hierarchical'] == 3
        
        hierarchical_only = collection.filter_by_type(TagType.HIERARCHICAL)
        assert len(hierarchical_only) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "functional"])

