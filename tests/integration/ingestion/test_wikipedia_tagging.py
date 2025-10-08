"""
Integration tests for WikipediaIngestor with UniversalTaggingManager.
"""
import pytest
from ingestion.wikipedia_ingestor import WikipediaIngestor
from ingestion.tagging import UniversalTaggingConfig


@pytest.mark.integration
class TestWikipediaTaggingIntegration:
    """Test Wikipedia crawler integration with universal tagging."""
    
    @pytest.fixture
    def ingestor_with_tagging(self):
        """Wikipedia ingestor with tagging enabled."""
        config = UniversalTaggingConfig(
            enable_user_tags=True,
            user_tags=["domain:test", "source:wiki"]
        )
        return WikipediaIngestor(tagging_config=config, enable_tagging=True)
    
    @pytest.fixture
    def ingestor_without_tagging(self):
        """Wikipedia ingestor with tagging disabled."""
        return WikipediaIngestor(enable_tagging=False)
    
    @pytest.mark.asyncio
    async def test_tagging_enabled_single_page(self, ingestor_with_tagging):
        """Test that tagging is applied when enabled (single page)."""
        url = "https://en.wikipedia.org/wiki/FastAPI"
        
        documents = await ingestor_with_tagging.crawl_and_ingest(
            original_page_url=url,
            max_surface_links=0,
            max_depth_distance=0
        )
        
        assert len(documents) == 1
        doc = documents[0]
        
        # Check default tags
        assert any(tag.startswith("source:") for tag in doc.tags)
        assert "source:wikipedia" in doc.tags
        assert "file_type:document" in doc.tags
        
        # Check user-defined tags
        assert "domain:test" in doc.tags
        assert "source:wiki" in doc.tags
        
        # Check tag metadata
        assert 'tag_count' in doc.metadata
        assert 'tag_types' in doc.metadata
        assert doc.metadata['tag_count'] == len(doc.tags)
    
    @pytest.mark.asyncio
    async def test_tagging_disabled(self, ingestor_without_tagging):
        """Test that tagging is NOT applied when disabled."""
        url = "https://en.wikipedia.org/wiki/Python_(programming_language)"
        
        documents = await ingestor_without_tagging.crawl_and_ingest(
            original_page_url=url,
            max_surface_links=0,
            max_depth_distance=0
        )
        
        assert len(documents) == 1
        doc = documents[0]
        
        # Should still have base tags from normalization
        assert any(tag.startswith("source:") for tag in doc.tags)
        assert any(tag.startswith("file_type:") for tag in doc.tags)
        
        # Should NOT have user-defined tags
        assert "domain:test" not in doc.tags
        
        # Should NOT have tag metadata from UniversalTaggingManager
        assert 'has_user_tags' not in doc.metadata
    
    @pytest.mark.asyncio
    async def test_tag_collection_available(self, ingestor_with_tagging):
        """Test that tag collection is available after crawling."""
        url = "https://en.wikipedia.org/wiki/Machine_learning"
        
        documents = await ingestor_with_tagging.crawl_and_ingest(
            original_page_url=url,
            max_surface_links=0,
            max_depth_distance=0
        )
        
        # Get tag collection
        tag_collection = ingestor_with_tagging.get_tag_collection()
        
        assert tag_collection is not None
        assert tag_collection.total_count() > 0
        
        # Should have default tags
        assert len(tag_collection.default_tags) > 0
        assert any("source:" in t for t in tag_collection.default_tags)
        
        # Should have user-defined tags
        assert len(tag_collection.user_defined_tags) > 0
        assert "domain:test" in tag_collection.user_defined_tags
    
    @pytest.mark.asyncio
    async def test_crawl_report_includes_tags(self, ingestor_with_tagging):
        """Test that crawl report includes tag collection."""
        url = "https://en.wikipedia.org/wiki/Artificial_intelligence"
        
        await ingestor_with_tagging.crawl_and_ingest(
            original_page_url=url,
            max_surface_links=0,
            max_depth_distance=0
        )
        
        # Generate report
        report = ingestor_with_tagging.generate_crawl_report()
        
        assert report.total_pages == 1
        assert report.tag_collection is not None
        
        # Check tag collection in report
        assert 'default' in report.tag_collection
        assert 'contextual' in report.tag_collection
        assert 'user_defined' in report.tag_collection
        assert 'breakdown' in report.tag_collection
    
    @pytest.mark.asyncio
    async def test_multiple_documents_tagging(self, ingestor_with_tagging):
        """Test tagging with multiple documents (depth > 0)."""
        url = "https://en.wikipedia.org/wiki/Deep_learning"
        
        documents = await ingestor_with_tagging.crawl_and_ingest(
            original_page_url=url,
            max_surface_links=2,
            max_depth_distance=1
        )
        
        # Should have multiple documents
        assert len(documents) >= 1
        
        # All documents should have tags
        for doc in documents:
            assert len(doc.tags) > 0
            assert "source:wikipedia" in doc.tags
            assert "file_type:document" in doc.tags
            assert "domain:test" in doc.tags
            assert 'tag_count' in doc.metadata
        
        # Tag collection should aggregate across all documents
        tag_collection = ingestor_with_tagging.get_tag_collection()
        assert tag_collection is not None
        assert tag_collection.total_count() > 0
    
    @pytest.mark.asyncio
    async def test_timestamp_tags_added(self, ingestor_with_tagging):
        """Test that timestamp presence tags are added."""
        url = "https://en.wikipedia.org/wiki/Neural_network"
        
        documents = await ingestor_with_tagging.crawl_and_ingest(
            original_page_url=url,
            max_surface_links=0,
            max_depth_distance=0
        )
        
        doc = documents[0]
        
        # Wikipedia documents should have created_at/updated_at
        # from last_modified timestamp
        if 'created_at' in doc.metadata:
            assert "has_created_date:true" in doc.tags
        if 'updated_at' in doc.metadata:
            assert "has_updated_date:true" in doc.tags
    
    @pytest.mark.asyncio
    async def test_custom_user_tags_per_crawl(self):
        """Test that custom user tags can be configured per crawl."""
        config1 = UniversalTaggingConfig(
            enable_user_tags=True,
            user_tags=["project:ml-research", "priority:high"]
        )
        ingestor1 = WikipediaIngestor(tagging_config=config1)
        
        config2 = UniversalTaggingConfig(
            enable_user_tags=True,
            user_tags=["project:documentation", "priority:low"]
        )
        ingestor2 = WikipediaIngestor(tagging_config=config2)
        
        url = "https://en.wikipedia.org/wiki/Reinforcement_learning"
        
        docs1 = await ingestor1.crawl_and_ingest(url, 0, 0)
        docs2 = await ingestor2.crawl_and_ingest(url, 0, 0)
        
        # Different user tags
        assert "project:ml-research" in docs1[0].tags
        assert "priority:high" in docs1[0].tags
        assert "project:documentation" not in docs1[0].tags
        
        assert "project:documentation" in docs2[0].tags
        assert "priority:low" in docs2[0].tags
        assert "project:ml-research" not in docs2[0].tags
    
    @pytest.mark.asyncio
    async def test_tag_collection_breakdown(self, ingestor_with_tagging):
        """Test that tag collection breakdown is correctly calculated."""
        url = "https://en.wikipedia.org/wiki/Computer_science"
        
        await ingestor_with_tagging.crawl_and_ingest(url, 0, 0)
        
        tag_collection = ingestor_with_tagging.get_tag_collection()
        breakdown = tag_collection.breakdown()
        
        # Should have all three types
        assert breakdown['default'] > 0
        assert breakdown['user_defined'] > 0
        assert breakdown['total'] >= breakdown['default'] + breakdown['user_defined']
        
        # Total should match unique tags
        assert breakdown['total'] == tag_collection.total_count()

