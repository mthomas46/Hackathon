"""
End-to-end tests for Wikipedia crawling.
"""
import pytest
from ingestion.wikipedia_ingestor import WikipediaIngestor


@pytest.mark.e2e
@pytest.mark.asyncio
class TestWikipediaE2E:
    """E2E tests for Wikipedia crawling."""
    
    async def test_single_page_crawl_depth_0(self):
        """Test crawling single Wikipedia page (depth=0)."""
        ingestor = WikipediaIngestor()
        
        docs = await ingestor.crawl_and_ingest(
            original_page_url="https://en.wikipedia.org/wiki/Python_(programming_language)",
            max_surface_links=0,
            max_depth_distance=0
        )
        
        # Should have exactly 1 page
        assert len(docs) == 1
        assert docs[0].metadata['source'] == 'wikipedia'
        assert docs[0].metadata['crawl_depth'] == 0
        assert docs[0].original_format == 'wikipedia'
        assert 'Python' in docs[0].title
        
        # Verify crawl report
        report = ingestor.generate_crawl_report()
        assert report.total_pages == 1
        assert report.depth_distribution == {0: 1}
        assert report.link_statistics['total_links_followed'] == 0
    
    async def test_surface_links_depth_1(self):
        """Test crawling with surface links (depth=1)."""
        ingestor = WikipediaIngestor()
        
        docs = await ingestor.crawl_and_ingest(
            original_page_url="https://en.wikipedia.org/wiki/Machine_learning",
            max_surface_links=5,
            max_depth_distance=1
        )
        
        # Should have original + up to 5 linked pages
        assert 1 <= len(docs) <= 6
        
        # Check depth distribution
        depth_0 = [d for d in docs if d.metadata['crawl_depth'] == 0]
        depth_1 = [d for d in docs if d.metadata['crawl_depth'] == 1]
        
        assert len(depth_0) == 1  # Original page
        assert len(depth_1) <= 5  # Up to 5 linked pages
        
        # Verify all depth-1 pages have the origin as parent
        for doc in depth_1:
            assert doc.metadata['parent_page'] is not None
            assert doc.metadata['crawl_origin'] == "Machine learning"
        
        # Verify crawl report
        report = ingestor.generate_crawl_report()
        assert report.total_pages == len(docs)
        assert report.depth_distribution[0] == 1
        assert 0 < report.depth_distribution.get(1, 0) <= 5
    
    async def test_deep_crawl_depth_2(self):
        """Test deep crawling (depth=2)."""
        ingestor = WikipediaIngestor()
        
        docs = await ingestor.crawl_and_ingest(
            original_page_url="https://en.wikipedia.org/wiki/Artificial_intelligence",
            max_surface_links=3,
            max_depth_distance=2
        )
        
        # Should have:
        # Depth 0: 1 page
        # Depth 1: up to 3 pages
        # Depth 2: up to 3*3 = 9 pages
        # Total: 1 + 3 + 9 = up to 13 pages
        assert 1 <= len(docs) <= 13
        
        # Verify depth distribution
        report = ingestor.generate_crawl_report()
        assert report.depth_distribution[0] == 1
        
        # At least some depth-1 pages should exist
        depth_1_count = report.depth_distribution.get(1, 0)
        assert depth_1_count > 0
        
        # Depth-2 pages should be children of depth-1 pages
        depth_2_docs = [d for d in docs if d.metadata['crawl_depth'] == 2]
        for doc in depth_2_docs:
            # Parent should be a depth-1 page
            parent_title = doc.metadata['parent_page']
            assert parent_title is not None
            # Find parent in crawl graph
            assert parent_title in ingestor.crawl_graph
            assert ingestor.crawl_graph[parent_title]['depth'] == 1
    
    async def test_no_duplicate_pages(self):
        """Test that pages are not crawled twice."""
        ingestor = WikipediaIngestor()
        
        docs = await ingestor.crawl_and_ingest(
            original_page_url="https://en.wikipedia.org/wiki/Neural_network",
            max_surface_links=10,
            max_depth_distance=2
        )
        
        # Check for unique document IDs
        doc_ids = [d.document_id for d in docs]
        assert len(doc_ids) == len(set(doc_ids)), "Found duplicate document IDs"
        
        # Check for unique URLs
        urls = [d.metadata['url'] for d in docs]
        assert len(urls) == len(set(urls)), "Found duplicate URLs"
        
        # Check for unique page titles
        titles = [d.metadata['page_title'] for d in docs]
        assert len(titles) == len(set(titles)), "Found duplicate page titles"
    
    async def test_depth_limit_enforcement(self):
        """Test that depth limit is strictly enforced."""
        ingestor = WikipediaIngestor()
        
        docs = await ingestor.crawl_and_ingest(
            original_page_url="https://en.wikipedia.org/wiki/Docker_(software)",
            max_surface_links=5,
            max_depth_distance=1
        )
        
        # No document should have depth > 1
        for doc in docs:
            assert doc.metadata['crawl_depth'] <= 1, \
                f"Found document at depth {doc.metadata['crawl_depth']}, max was 1"
        
        # Verify in report
        report = ingestor.generate_crawl_report()
        for depth in report.depth_distribution.keys():
            assert depth <= 1, f"Found depth {depth} in distribution, max was 1"
    
    async def test_surface_link_limit_enforcement(self):
        """Test that surface link limit is enforced."""
        ingestor = WikipediaIngestor()
        
        max_links = 3
        docs = await ingestor.crawl_and_ingest(
            original_page_url="https://en.wikipedia.org/wiki/Kubernetes",
            max_surface_links=max_links,
            max_depth_distance=1
        )
        
        # Count depth-1 pages (children of origin)
        depth_1_count = len([d for d in docs if d.metadata['crawl_depth'] == 1])
        
        assert depth_1_count <= max_links, \
            f"Found {depth_1_count} depth-1 pages, max was {max_links}"
    
    async def test_markdown_normalization_complete(self):
        """Test that all documents are properly normalized to markdown."""
        ingestor = WikipediaIngestor()
        
        docs = await ingestor.crawl_and_ingest(
            original_page_url="https://en.wikipedia.org/wiki/Markdown",
            max_surface_links=2,
            max_depth_distance=1
        )
        
        for doc in docs:
            # All should be markdown
            assert doc.content_md.startswith('#'), \
                f"Document {doc.document_id} doesn't start with markdown header"
            
            # Should have required metadata sections
            assert '**Source**: Wikipedia' in doc.content_md
            assert '**URL**:' in doc.content_md
            assert '## Content' in doc.content_md
            
            # Should have proper tagging
            assert 'source:wikipedia' in doc.tags
            assert 'file_type:document' in doc.tags
            
            # Should have depth tag
            depth_tag = f"depth:{doc.metadata['crawl_depth']}"
            assert depth_tag in doc.tags
    
    async def test_crawl_graph_structure(self):
        """Test that crawl graph has correct parent-child relationships."""
        ingestor = WikipediaIngestor()
        
        docs = await ingestor.crawl_and_ingest(
            original_page_url="https://en.wikipedia.org/wiki/Deep_learning",
            max_surface_links=3,
            max_depth_distance=2
        )
        
        report = ingestor.generate_crawl_report()
        graph = report.crawl_graph
        
        # Origin should have no parent
        origin_node = graph.get("Deep learning")
        assert origin_node is not None
        assert origin_node['parent'] is None
        assert origin_node['depth'] == 0
        
        # All children should reference valid parents
        for page_title, node in graph.items():
            if node['parent'] is not None:
                # Parent should exist in graph
                assert node['parent'] in graph, \
                    f"Parent '{node['parent']}' of '{page_title}' not in graph"
                
                # Parent's depth should be one less
                parent_depth = graph[node['parent']]['depth']
                assert node['depth'] == parent_depth + 1, \
                    f"Depth mismatch: {page_title} at depth {node['depth']}, parent at {parent_depth}"
    
    async def test_complete_workflow_with_report(self):
        """Test complete workflow: crawl → generate report → verify."""
        ingestor = WikipediaIngestor()
        
        # Crawl
        docs = await ingestor.crawl_and_ingest(
            original_page_url="https://en.wikipedia.org/wiki/FastAPI",
            max_surface_links=4,
            max_depth_distance=1
        )
        
        # Generate report
        report = ingestor.generate_crawl_report()
        
        # Verify completeness
        assert report.total_pages == len(docs)
        assert report.duration_seconds > 0
        assert sum(report.depth_distribution.values()) == len(docs)
        
        # Verify statistics are accurate
        total_children = 0
        for node in report.crawl_graph.values():
            total_children += len(node['children'])
        
        assert report.link_statistics['total_links_followed'] == total_children
        
        # Verify all documents have required metadata
        for doc in docs:
            assert doc.document_id is not None
            assert doc.title is not None
            assert doc.content_md is not None
            assert doc.metadata['source'] == 'wikipedia'
            assert doc.metadata['crawl_origin'] is not None
            assert doc.metadata['crawl_max_depth'] == 1
            assert doc.metadata['crawl_max_surface'] == 4

