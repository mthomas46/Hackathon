"""
Integration tests for Wikipedia API.
"""
import pytest
import asyncio
from ingestion.wikipedia_ingestor import WikipediaIngestor


@pytest.mark.integration
@pytest.mark.asyncio
class TestWikipediaAPIIntegration:
    """Integration tests for Wikipedia API."""
    
    async def test_fetch_single_page(self):
        """Test fetching a single Wikipedia page."""
        ingestor = WikipediaIngestor()
        
        docs = await ingestor.crawl_and_ingest(
            original_page_url="https://en.wikipedia.org/wiki/Python_(programming_language)",
            max_surface_links=0,
            max_depth_distance=0
        )
        
        assert len(docs) == 1
        doc = docs[0]
        
        # Verify document structure
        assert doc.document_id.startswith("wikipedia-")
        assert "Python" in doc.title
        assert doc.original_format == "wikipedia"
        assert doc.metadata['source'] == 'wikipedia'
        assert doc.metadata['crawl_depth'] == 0
        assert doc.metadata['parent_page'] is None
        
        # Verify content
        assert len(doc.content_md) > 500  # Should have substantial content
        assert "# Python" in doc.content_md or "Python" in doc.content_md
        assert "**Source**: Wikipedia" in doc.content_md
        
        # Verify tags
        assert "source:wikipedia" in doc.tags
        assert "file_type:document" in doc.tags
        assert "depth:0" in doc.tags
    
    async def test_fetch_with_surface_links(self):
        """Test fetching page with surface links (depth=1)."""
        ingestor = WikipediaIngestor()
        
        docs = await ingestor.crawl_and_ingest(
            original_page_url="https://en.wikipedia.org/wiki/FastAPI",
            max_surface_links=3,
            max_depth_distance=1
        )
        
        # Should have original + up to 3 linked pages
        assert 1 <= len(docs) <= 4
        
        # Check depth distribution
        depth_0_docs = [d for d in docs if d.metadata['crawl_depth'] == 0]
        depth_1_docs = [d for d in docs if d.metadata['crawl_depth'] == 1]
        
        assert len(depth_0_docs) == 1  # Original page
        assert len(depth_1_docs) <= 3  # Up to 3 linked pages
        
        # Verify crawl graph
        report = ingestor.generate_crawl_report()
        assert report.total_pages == len(docs)
        assert report.depth_distribution[0] == 1
        assert report.duration_seconds > 0
    
    async def test_no_duplicate_crawling(self):
        """Test that pages are not crawled twice."""
        ingestor = WikipediaIngestor()
        
        docs = await ingestor.crawl_and_ingest(
            original_page_url="https://en.wikipedia.org/wiki/Microservices",
            max_surface_links=5,
            max_depth_distance=1
        )
        
        # Check for unique document IDs
        doc_ids = [d.document_id for d in docs]
        assert len(doc_ids) == len(set(doc_ids))
        
        # Check for unique URLs
        urls = [d.metadata['url'] for d in docs]
        assert len(urls) == len(set(urls))
        
        # Verify visited pages tracking
        assert len(ingestor.visited_pages) == len(docs)
    
    async def test_crawl_report_generation(self):
        """Test crawl report generation."""
        ingestor = WikipediaIngestor()
        
        await ingestor.crawl_and_ingest(
            original_page_url="https://en.wikipedia.org/wiki/Docker_(software)",
            max_surface_links=2,
            max_depth_distance=1
        )
        
        report = ingestor.generate_crawl_report()
        
        # Verify report structure
        assert report.total_pages > 0
        assert 'crawl_graph' in report.to_dict()
        assert 'depth_distribution' in report.to_dict()
        assert 'link_statistics' in report.to_dict()
        
        # Verify statistics
        assert report.link_statistics['total_links_followed'] >= 0
        assert report.link_statistics['average_links_per_page'] >= 0
        assert report.duration_seconds > 0
    
    async def test_markdown_normalization(self):
        """Test that Wikipedia content is properly normalized to markdown."""
        ingestor = WikipediaIngestor()
        
        docs = await ingestor.crawl_and_ingest(
            original_page_url="https://en.wikipedia.org/wiki/Markdown",
            max_surface_links=0,
            max_depth_distance=0
        )
        
        doc = docs[0]
        
        # Check markdown structure
        assert doc.content_md.startswith('#')
        assert '**Source**: Wikipedia' in doc.content_md
        assert '**URL**:' in doc.content_md
        assert '## Content' in doc.content_md
        
        # Check metadata
        assert 'wikipedia' in doc.metadata['url']
        assert doc.metadata['file_type'] == 'document'
        assert doc.metadata['language'] == 'en'
        
        # Check timestamps
        assert doc.created_at is not None or doc.updated_at is not None
    
    async def test_rate_limiting(self):
        """Test that rate limiting is working."""
        import time
        ingestor = WikipediaIngestor()
        
        start_time = time.time()
        
        docs = await ingestor.crawl_and_ingest(
            original_page_url="https://en.wikipedia.org/wiki/Kubernetes",
            max_surface_links=3,
            max_depth_distance=1
        )
        
        elapsed = time.time() - start_time
        
        # With rate limiting (0.5s between requests), should take at least:
        # (number_of_depth_1_pages * 0.5) seconds
        depth_1_count = len([d for d in docs if d.metadata['crawl_depth'] == 1])
        if depth_1_count > 0:
            expected_min_time = depth_1_count * 0.5
            assert elapsed >= expected_min_time * 0.8  # Allow 20% margin

