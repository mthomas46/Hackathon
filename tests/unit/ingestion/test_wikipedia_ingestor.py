"""
Unit tests for Wikipedia ingestor.
"""
import pytest
from ingestion.wikipedia_ingestor import WikipediaIngestor


class TestWikipediaIngestor:
    """Unit tests for Wikipedia ingestor."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.ingestor = WikipediaIngestor()
    
    def test_extract_page_title(self):
        """Test extracting page title from URL."""
        url = "https://en.wikipedia.org/wiki/Machine_learning"
        title = self.ingestor._extract_page_title(url)
        
        assert title == "Machine learning"
    
    def test_extract_page_title_with_underscores(self):
        """Test extracting page title with underscores."""
        url = "https://en.wikipedia.org/wiki/Python_(programming_language)"
        title = self.ingestor._extract_page_title(url)
        
        assert title == "Python (programming language)"
    
    def test_filter_links_respects_max_limit(self):
        """Test that filter_links respects max limit."""
        links = [
            (f"Page_{i}", f"https://en.wikipedia.org/wiki/Page_{i}")
            for i in range(20)
        ]
        
        filtered = self.ingestor._filter_links(links, max_links=5)
        
        assert len(filtered) == 5
    
    def test_filter_links_excludes_navigation_pages(self):
        """Test that navigation pages are excluded."""
        links = [
            ("Machine learning", "https://en.wikipedia.org/wiki/Machine_learning"),
            ("List of algorithms", "https://en.wikipedia.org/wiki/List_of_algorithms"),
            ("Deep learning", "https://en.wikipedia.org/wiki/Deep_learning"),
            ("Index of AI", "https://en.wikipedia.org/wiki/Index_of_AI"),
        ]
        
        filtered = self.ingestor._filter_links(links, max_links=10)
        
        # Should only include Machine learning and Deep learning
        assert len(filtered) == 2
        assert filtered[0][0] == "Machine learning"
        assert filtered[1][0] == "Deep learning"
    
    def test_extract_categories_computer_science(self):
        """Test category extraction for computer science content."""
        title = "Python Programming"
        content = "Python is a programming language used for software development and algorithm implementation."
        
        categories = self.ingestor._extract_categories(title, content)
        
        assert 'computer-science' in categories
    
    def test_extract_categories_machine_learning(self):
        """Test category extraction for ML content."""
        title = "Neural Networks"
        content = "Neural networks are a type of machine learning model inspired by artificial intelligence."
        
        categories = self.ingestor._extract_categories(title, content)
        
        assert 'machine-learning' in categories
    
    def test_extract_categories_multiple(self):
        """Test extraction of multiple categories."""
        title = "AI Research"
        content = "Scientific research in artificial intelligence and machine learning technology for computer science applications."
        
        categories = self.ingestor._extract_categories(title, content)
        
        # Should detect multiple categories
        assert len(categories) >= 3
        assert 'machine-learning' in categories
        assert 'computer-science' in categories
        assert 'science' in categories or 'technology' in categories
    
    def test_calculate_depth_distribution(self):
        """Test depth distribution calculation."""
        # Manually populate crawl graph
        self.ingestor.crawl_graph = {
            'Page A': {'depth': 0, 'children': []},
            'Page B': {'depth': 1, 'children': []},
            'Page C': {'depth': 1, 'children': []},
            'Page D': {'depth': 2, 'children': []},
        }
        
        distribution = self.ingestor._calculate_depth_distribution()
        
        assert distribution[0] == 1  # 1 page at depth 0
        assert distribution[1] == 2  # 2 pages at depth 1
        assert distribution[2] == 1  # 1 page at depth 2
    
    def test_calculate_link_statistics(self):
        """Test link statistics calculation."""
        # Manually populate crawl graph
        self.ingestor.crawl_graph = {
            'Page A': {'depth': 0, 'children': ['Page B', 'Page C']},
            'Page B': {'depth': 1, 'children': ['Page D']},
            'Page C': {'depth': 1, 'children': []},
            'Page D': {'depth': 2, 'children': []},
        }
        
        stats = self.ingestor._calculate_link_statistics()
        
        assert stats['total_links_followed'] == 3  # A→B, A→C, B→D
        assert stats['average_links_per_page'] == 0.75  # 3 links / 4 pages
        assert stats['max_children'] == 2  # Page A has 2 children
    
    def test_visited_pages_tracking(self):
        """Test that visited pages are tracked."""
        assert len(self.ingestor.visited_pages) == 0
        
        self.ingestor.visited_pages.add("https://en.wikipedia.org/wiki/Test")
        
        assert len(self.ingestor.visited_pages) == 1
        assert "https://en.wikipedia.org/wiki/Test" in self.ingestor.visited_pages

