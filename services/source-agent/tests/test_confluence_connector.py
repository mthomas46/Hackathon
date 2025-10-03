"""
Tests for Confluence Connector
==============================

Unit tests for Confluence API integration and documentation intelligence.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock
import sys
from pathlib import Path

# Add service root to path
service_root = str(Path(__file__).parent.parent)
if service_root not in sys.path:
    sys.path.insert(0, service_root)

from domain.services.confluence_connector import (
    ConfluenceConnector,
    ConfluenceDocument,
    DocumentQuality,
    DocumentationAnalytics
)


@pytest.fixture
def mock_log_client():
    """Create mock log collector client."""
    client = Mock()
    client.log_info = AsyncMock()
    client.log_error = AsyncMock()
    client.log_warning = AsyncMock()
    client.log_business_event = AsyncMock()
    return client


@pytest.fixture
def confluence_connector(mock_log_client):
    """Create Confluence connector with mock log client."""
    config = {
        'url': 'https://test.atlassian.net',
        'username': 'test@example.com',
        'api_token': 'test-token',
        'space_key': 'TEST'
    }
    return ConfluenceConnector(config=config, log_client=mock_log_client)


@pytest.fixture
def sample_documents():
    """Create sample Confluence documents for testing."""
    base_date = datetime.now() - timedelta(days=180)
    
    documents = [
        ConfluenceDocument(
            id="page-1",
            title="API Reference Guide",
            space_key="TEST",
            content="This is a comprehensive API reference guide with examples. "
                   "API endpoint /users returns user data. Example request: GET /users/123 "
                   "Example response: {id: 123, name: John}. " * 20,
            content_type="page",
            created=base_date,
            updated=datetime.now() - timedelta(days=10),
            creator="John Doe",
            last_modifier="Jane Smith",
            labels=["api", "reference", "backend"],
            word_count=500,
            links_count=10,
            attachments_count=2,
            version=5,
            url="https://test.atlassian.net/wiki/spaces/TEST/pages/page-1"
        ),
        ConfluenceDocument(
            id="page-2",
            title="Getting Started Guide",
            space_key="TEST",
            content="Step 1: Install dependencies. First, run npm install. "
                   "Step 2: Configure environment. Next, create .env file. "
                   "Step 3: Start server. Finally, run npm start. " * 15,
            content_type="page",
            created=base_date,
            updated=datetime.now() - timedelta(days=30),
            creator="Jane Smith",
            last_modifier="Jane Smith",
            labels=["guide", "tutorial", "quickstart"],
            word_count=350,
            links_count=5,
            attachments_count=1,
            version=3,
            url="https://test.atlassian.net/wiki/spaces/TEST/pages/page-2"
        ),
        ConfluenceDocument(
            id="page-3",
            title="Architecture Overview",
            space_key="TEST",
            content="System architecture and design decisions. "
                   "This document is short and lacks details.",
            content_type="page",
            created=base_date,
            updated=base_date + timedelta(days=10),  # Very stale (170 days old, but in outdated range)
            creator="Bob Wilson",
            last_modifier="Bob Wilson",
            labels=["architecture"],
            word_count=50,
            links_count=0,
            attachments_count=0,
            version=1,
            url="https://test.atlassian.net/wiki/spaces/TEST/pages/page-3"
        ),
        ConfluenceDocument(
            id="page-4",
            title="Troubleshooting Common Issues",
            space_key="TEST",
            content="Common issues and solutions:\n"
                   "* Issue 1: Connection timeout\n"
                   "* Issue 2: Authentication failed\n"
                   "* Issue 3: Data sync error\n" * 20,
            content_type="page",
            created=base_date,
            updated=datetime.now() - timedelta(days=5),
            creator="Alice Brown",
            last_modifier="Alice Brown",
            labels=["troubleshooting", "support"],
            word_count=400,
            links_count=8,
            attachments_count=3,
            version=10,
            url="https://test.atlassian.net/wiki/spaces/TEST/pages/page-4"
        ),
        ConfluenceDocument(
            id="blog-1",
            title="Release Notes v2.0",
            space_key="TEST",
            content="New features in version 2.0. Bug fixes and improvements. " * 10,
            content_type="blogpost",
            created=datetime.now() - timedelta(days=7),
            updated=datetime.now() - timedelta(days=7),
            creator="Jane Smith",
            last_modifier="Jane Smith",
            labels=["release", "changelog"],
            word_count=120,
            links_count=3,
            attachments_count=0,
            version=1,
            url="https://test.atlassian.net/wiki/spaces/TEST/pages/blog-1"
        )
    ]
    
    return documents


class TestConfluenceConnector:
    """Test suite for Confluence Connector."""
    
    def test_connector_initialization(self, confluence_connector):
        """Test connector initializes with config."""
        assert confluence_connector is not None
        assert confluence_connector.config['url'] == 'https://test.atlassian.net'
        assert confluence_connector.config['space_key'] == 'TEST'
    
    def test_get_config_from_env(self, confluence_connector):
        """Test configuration from environment variables."""
        config = confluence_connector._get_config_from_env()
        assert 'url' in config
        assert 'username' in config
        assert 'api_token' in config
    
    @pytest.mark.asyncio
    async def test_fetch_documents_returns_mock_data(self, confluence_connector):
        """Test fetch_documents returns mock data when Confluence client unavailable."""
        documents = await confluence_connector.fetch_documents('TEST')
        
        assert len(documents) == 20  # Default mock count
        assert all(isinstance(d, ConfluenceDocument) for d in documents)
        assert all(d.space_key == 'TEST' for d in documents)
    
    @pytest.mark.asyncio
    async def test_assess_document_quality_high_quality(self, confluence_connector, sample_documents):
        """Test quality assessment for high-quality document."""
        # API Reference Guide - recent, good content
        quality = await confluence_connector.assess_document_quality(sample_documents[0])
        
        assert isinstance(quality, DocumentQuality)
        assert quality.overall_score > 0.7  # Should be high quality
        assert quality.freshness_score > 0.9  # Updated recently
        assert quality.completeness_score > 0.8  # Good word count and links
    
    @pytest.mark.asyncio
    async def test_assess_document_quality_low_quality(self, confluence_connector, sample_documents):
        """Test quality assessment for low-quality document."""
        # Architecture Overview - outdated, short, no links
        quality = await confluence_connector.assess_document_quality(sample_documents[2])
        
        assert isinstance(quality, DocumentQuality)
        assert quality.overall_score < 0.7  # Should be lower quality
        assert quality.freshness_score < 0.8  # Outdated
        assert quality.completeness_score < 0.5  # Too short
        assert len(quality.issues) > 0  # Should have issues
        assert len(quality.recommendations) > 0  # Should have recommendations
    
    @pytest.mark.asyncio
    async def test_assess_guide_document(self, confluence_connector, sample_documents):
        """Test quality assessment for guide document."""
        # Getting Started Guide - has steps
        quality = await confluence_connector.assess_document_quality(sample_documents[1])
        
        assert isinstance(quality, DocumentQuality)
        assert quality.coverage_score > 0.7  # Should recognize guide structure
    
    @pytest.mark.asyncio
    async def test_assess_api_documentation(self, confluence_connector, sample_documents):
        """Test quality assessment for API documentation."""
        # API Reference Guide - has examples
        quality = await confluence_connector.assess_document_quality(sample_documents[0])
        
        assert isinstance(quality, DocumentQuality)
        assert quality.coverage_score >= 0.8  # Should recognize API doc with examples
    
    @pytest.mark.asyncio
    async def test_analyze_documentation(self, confluence_connector, sample_documents):
        """Test documentation analysis."""
        analytics = await confluence_connector.analyze_documentation(sample_documents)
        
        assert isinstance(analytics, DocumentationAnalytics)
        assert analytics.total_documents == 5
        assert analytics.total_pages == 4
        assert analytics.total_blogposts == 1
        assert analytics.avg_word_count > 0
        assert 0 <= analytics.avg_quality_score <= 1
    
    @pytest.mark.asyncio
    async def test_analyze_empty_documents(self, confluence_connector):
        """Test analysis with empty document list."""
        analytics = await confluence_connector.analyze_documentation([])
        
        assert analytics.total_documents == 0
        assert analytics.avg_word_count == 0.0
        assert analytics.avg_quality_score == 0.0
    
    @pytest.mark.asyncio
    async def test_document_freshness_categorization(self, confluence_connector, sample_documents):
        """Test that documents are categorized by freshness."""
        analytics = await confluence_connector.analyze_documentation(sample_documents)
        
        # Should have recent and outdated documents
        assert analytics.recent_documents > 0
        assert analytics.outdated_documents > 0
        total_freshness = (
            analytics.recent_documents +
            analytics.outdated_documents +
            analytics.stale_documents
        )
        assert total_freshness == analytics.total_documents
    
    @pytest.mark.asyncio
    async def test_top_contributors_identified(self, confluence_connector, sample_documents):
        """Test that top contributors are identified."""
        analytics = await confluence_connector.analyze_documentation(sample_documents)
        
        assert len(analytics.top_contributors) > 0
        assert all('name' in c and 'document_count' in c for c in analytics.top_contributors)
        # Jane Smith should be top contributor (3 documents)
        top = analytics.top_contributors[0]
        assert top['name'] == 'Jane Smith'
        assert top['document_count'] == 3
    
    @pytest.mark.asyncio
    async def test_common_topics_extraction(self, confluence_connector, sample_documents):
        """Test common topics extraction from labels."""
        analytics = await confluence_connector.analyze_documentation(sample_documents)
        
        assert len(analytics.common_topics) > 0
        # Should include common labels
        all_topics = set(analytics.common_topics)
        assert any(topic in all_topics for topic in ['api', 'guide', 'troubleshooting'])
    
    @pytest.mark.asyncio
    async def test_coverage_gaps_identification(self, confluence_connector, sample_documents):
        """Test coverage gaps are identified."""
        analytics = await confluence_connector.analyze_documentation(sample_documents)
        
        # Should identify gaps in documentation
        assert isinstance(analytics.coverage_gaps, list)
        # Should notice missing testing/security docs
        gap_text = ' '.join(analytics.coverage_gaps).lower()
        assert 'testing' in gap_text or 'security' in gap_text
    
    def test_strip_html(self, confluence_connector):
        """Test HTML stripping."""
        html = "<p>This is <strong>bold</strong> text</p>"
        text = confluence_connector._strip_html(html)
        
        assert '<' not in text
        assert '>' not in text
        assert 'bold' in text
        assert 'This is' in text
    
    def test_calculate_completeness_short_document(self, confluence_connector):
        """Test completeness calculation for short document."""
        doc = ConfluenceDocument(
            id="test",
            title="Test",
            space_key="TEST",
            content="Short",
            content_type="page",
            created=datetime.now(),
            updated=datetime.now(),
            creator="Test",
            last_modifier="Test",
            labels=[],
            word_count=50,
            links_count=0,
            attachments_count=0,
            version=1,
            url="http://test.com"
        )
        
        issues = []
        recommendations = []
        score = confluence_connector._calculate_completeness(doc, issues, recommendations)
        
        assert score < 0.6  # Should be penalized for being short
        assert len(issues) > 0
        assert len(recommendations) > 0
    
    def test_calculate_freshness_recent(self, confluence_connector):
        """Test freshness calculation for recent document."""
        doc = ConfluenceDocument(
            id="test",
            title="Test",
            space_key="TEST",
            content="Content",
            content_type="page",
            created=datetime.now() - timedelta(days=30),
            updated=datetime.now() - timedelta(days=10),
            creator="Test",
            last_modifier="Test",
            labels=[],
            word_count=200,
            links_count=5,
            attachments_count=0,
            version=2,
            url="http://test.com"
        )
        
        issues = []
        recommendations = []
        score = confluence_connector._calculate_freshness(doc, issues, recommendations)
        
        assert score == 1.0  # Should be perfect for recent updates
        assert len(issues) == 0
    
    def test_calculate_freshness_stale(self, confluence_connector):
        """Test freshness calculation for stale document."""
        doc = ConfluenceDocument(
            id="test",
            title="Test",
            space_key="TEST",
            content="Content",
            content_type="page",
            created=datetime.now() - timedelta(days=400),
            updated=datetime.now() - timedelta(days=400),
            creator="Test",
            last_modifier="Test",
            labels=[],
            word_count=200,
            links_count=5,
            attachments_count=0,
            version=1,
            url="http://test.com"
        )
        
        issues = []
        recommendations = []
        score = confluence_connector._calculate_freshness(doc, issues, recommendations)
        
        assert score < 0.2  # Should be very low for stale docs
        assert len(issues) > 0
    
    def test_generate_mock_documents(self, confluence_connector):
        """Test mock document generation."""
        documents = confluence_connector._generate_mock_documents('TEST', 10)
        
        assert len(documents) == 10
        assert all(d.space_key == 'TEST' for d in documents)
        assert all(d.word_count > 0 for d in documents)
        assert all(d.content_type == 'page' for d in documents)
    
    @pytest.mark.asyncio
    async def test_get_space_overview(self, confluence_connector):
        """Test space overview retrieval."""
        overview = await confluence_connector.get_space_overview('TEST')
        
        assert 'space_key' in overview
        assert 'total_documents' in overview
        assert 'avg_quality_score' in overview
        assert 'freshness' in overview
        assert 'coverage_gaps' in overview
        assert 'top_contributors' in overview
        assert overview['space_key'] == 'TEST'
    
    @pytest.mark.asyncio
    async def test_logging_integration(self, confluence_connector, mock_log_client):
        """Test that operations are logged."""
        await confluence_connector.fetch_documents('TEST')
        
        # Should log warning about Confluence client not initialized
        mock_log_client.log_warning.assert_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

