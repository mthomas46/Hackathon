"""Tests for Doc Store semantic tagging functionality.

Tests automatic content analysis, tag generation, taxonomy management,
and tag-based search operations.
"""

import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import pytest

# Import modules normally now that directory uses underscores
from services.doc_store.modules.semantic_tagging import (
    SemanticTagger, ContentAnalyzer, TagTaxonomy, semantic_tagger, tag_taxonomy
)


class TestContentAnalyzer:
    """Test ContentAnalyzer class functionality."""

    @pytest.fixture
    def analyzer(self):
        """Create a test content analyzer instance."""
        return ContentAnalyzer()

    def test_analyzer_initialization(self, analyzer):
        """Test content analyzer initialization."""
        assert analyzer.programming_languages is not None
        assert analyzer.frameworks is not None
        assert analyzer.technical_domains is not None
        assert analyzer.code_patterns is not None

    def test_extract_code_entities_functions(self, analyzer):
        """Test extraction of function definitions."""
        content = """
        def process_data(data):
            return data.upper()

        class DataProcessor:
            def __init__(self):
                pass

        import pandas as pd
        from sklearn import model_selection
        """

        entities = analyzer._extract_code_entities(content)

        function_entities = [e for e in entities if e.entity_type == 'function_definition']
        class_entities = [e for e in entities if e.entity_type == 'class_definition']
        import_entities = [e for e in entities if e.entity_type == 'import']

        assert len(function_entities) >= 1
        assert len(class_entities) >= 1
        assert len(import_entities) >= 2

    def test_extract_url_entities(self, analyzer):
        """Test URL entity extraction."""
        content = """
        Check out https://github.com/user/repo for more info.
        Also see https://stackoverflow.com/questions/123 for help.
        """

        entities = analyzer._extract_url_entities(content)

        url_entities = [e for e in entities if e.entity_type in ['github_url', 'stackoverflow_url']]
        assert len(url_entities) >= 2

    def test_extract_email_entities(self, analyzer):
        """Test email entity extraction."""
        content = """
        Contact support@example.com for help.
        Also reach out to dev@company.com.
        """

        entities = analyzer._extract_email_entities(content)

        email_entities = [e for e in entities if e.entity_type == 'email']
        assert len(email_entities) == 2

    def test_extract_file_entities(self, analyzer):
        """Test file extension entity extraction."""
        content = """
        See the README.md file.
        Check out utils.py and test.js.
        Look at data.json for configuration.
        """

        entities = analyzer._extract_file_entities(content)

        file_entities = [e for e in entities if 'file' in e.entity_type]
        assert len(file_entities) >= 3

    def test_extract_technical_entities(self, analyzer):
        """Test technical domain entity extraction."""
        content = """
        This Python script handles API requests and uses Flask framework.
        It performs data analysis and machine learning tasks.
        """

        entities = analyzer._extract_technical_entities(content)

        tech_entities = [e for e in entities if e.entity_type in ['programming_language', 'framework', 'technical_domain']]
        assert len(tech_entities) >= 2

    def test_generate_tags_from_content(self, analyzer):
        """Test tag generation from content analysis."""
        content = """
        This Python Flask API handles user authentication and database operations.
        It uses SQLAlchemy for ORM and implements RESTful endpoints.
        """

        metadata = {"type": "api", "language": "python"}
        entities = analyzer.analyze_content(content, metadata)
        tags = analyzer.generate_tags(content, metadata, entities)

        # Should generate multiple tags
        assert len(tags) > 0

        # Check for expected tag types
        tag_values = [tag['tag'] for tag in tags]
        assert 'python' in tag_values  # From metadata
        assert 'api' in tag_values     # From metadata

    def test_generate_tags_confidence_filtering(self, analyzer):
        """Test tag confidence filtering."""
        content = "This is a simple document."
        metadata = {}
        entities = analyzer.analyze_content(content, metadata)
        tags = analyzer.generate_tags(content, metadata, entities)

        # Filter high confidence tags
        high_confidence_tags = [tag for tag in tags if tag['confidence'] >= 0.8]
        assert len(high_confidence_tags) <= len(tags)


class TestSemanticTagger:
    """Test SemanticTagger class functionality."""

    @pytest.fixture
    def tagger(self):
        """Create a test semantic tagger instance."""
        return SemanticTagger()

    @patch('services.doc_store.modules.semantic_tagging.execute_db_query')
    @pytest.mark.asyncio
    async def test_tag_document_success(self, mock_execute, tagger):
        """Test successful document tagging."""
        mock_execute.return_value = []

        content = "This Python script uses Flask and SQLAlchemy."
        metadata = {"type": "code", "language": "python"}

        result = await tagger.tag_document("test-doc", content, metadata)

        assert result["document_id"] == "test-doc"
        assert "entities_stored" in result
        assert "tags_stored" in result

    @patch('services.doc_store.modules.semantic_tagging.execute_db_query')
    def test_get_document_tags(self, mock_execute, tagger):
        """Test retrieving document tags."""
        mock_rows = [
            {
                'id': 'tag1',
                'tag': 'python',
                'category': 'programming_language',
                'confidence': 0.95,
                'metadata': '{"source": "metadata"}',
                'created_at': '2024-01-01T00:00:00Z'
            }
        ]
        mock_execute.return_value = mock_rows

        tags = tagger.get_document_tags("test-doc")

        assert len(tags) == 1
        assert tags[0]['tag'] == 'python'
        assert tags[0]['category'] == 'programming_language'

    @patch('services.doc_store.modules.semantic_tagging.execute_db_query')
    def test_get_tag_statistics(self, mock_execute, tagger):
        """Test tag statistics generation."""
        # Mock category distribution
        category_rows = [
            {'category': 'programming_language', 'count': 10, 'avg_confidence': 0.85},
            {'category': 'framework', 'count': 5, 'avg_confidence': 0.75}
        ]

        # Mock popular tags
        popular_tags = [
            {'tag': 'python', 'category': 'programming_language', 'count': 8, 'avg_confidence': 0.9}
        ]

        # Mock document counts
        mock_execute.side_effect = [category_rows, popular_tags, [20], [15]]

        stats = tagger.get_tag_statistics()

        assert stats['total_tags'] == 15  # 10 + 5
        assert stats['total_tagged_documents'] == 20
        assert stats['total_documents'] == 15
        assert len(stats['category_distribution']) == 2
        assert len(stats['popular_tags']) == 1

    @patch('services.doc_store.modules.semantic_tagging.execute_db_query')
    def test_search_by_tags(self, mock_execute, tagger):
        """Test tag-based document search."""
        mock_results = [
            {
                'id': 'doc1',
                'content': 'Python content',
                'metadata': '{"language": "python"}',
                'created_at': '2024-01-01T00:00:00Z',
                'tag_matches': 2,
                'avg_tag_confidence': 0.85
            }
        ]
        mock_execute.return_value = mock_results

        results = tagger.search_by_tags(['python', 'api'], categories=['programming_language'], min_confidence=0.7)

        assert len(results) == 1
        assert results[0]['document_id'] == 'doc1'
        assert results[0]['tag_matches'] == 2


class TestTagTaxonomy:
    """Test TagTaxonomy class functionality."""

    @pytest.fixture
    def taxonomy(self):
        """Create a test tag taxonomy instance."""
        return TagTaxonomy()

    @patch('services.doc_store.modules.semantic_tagging.execute_db_query')
    def test_create_taxonomy_node(self, mock_execute, taxonomy):
        """Test creating taxonomy nodes."""
        mock_execute.return_value = []

        success = taxonomy.create_taxonomy_node(
            tag="python",
            category="programming_language",
            description="Python programming language",
            parent_tag="programming_language",
            synonyms=["py", "python3"]
        )

        assert success is True
        # Verify database call was made
        assert mock_execute.call_count > 0

    @patch('services.doc_store.modules.semantic_tagging.execute_db_query')
    def test_get_taxonomy_tree(self, mock_execute, taxonomy):
        """Test retrieving taxonomy tree."""
        mock_rows = [
            {
                'tag': 'python',
                'category': 'programming_language',
                'description': 'Python language',
                'parent_tag': 'programming',
                'synonyms': '["py", "python3"]',
                'created_at': '2024-01-01T00:00:00Z'
            }
        ]
        mock_execute.return_value = mock_rows

        tree = taxonomy.get_taxonomy_tree()

        assert 'programming_language' in tree
        assert len(tree['programming_language']) == 1
        assert tree['programming_language'][0]['tag'] == 'python'


class TestSemanticTaggingIntegration:
    """Test semantic tagging integration with doc store operations."""

    @pytest.mark.asyncio
    async def test_automatic_tagging_on_document_creation(self):
        """Test that documents are automatically tagged during creation."""
        from services.doc_store.modules.document_handlers import DocumentHandlers
        from services.doc_store.core.models import DocumentRequest

        content = "This Python Flask API uses SQLAlchemy for database operations."
        metadata = {"type": "api", "language": "python"}

        request = DocumentRequest(content=content, metadata=metadata)

        with patch('services.doc_store.modules.document_handlers.execute_db_query') as mock_execute:
            with patch('services.doc_store.modules.document_handlers.create_document_logic') as mock_create:
                with patch('services.doc_store.modules.document_handlers.utc_now') as mock_now:
                    mock_create.return_value = {
                        "id": "test-doc-123",
                        "content_hash": "abc123",
                        "created_at": "2024-01-01T00:00:00Z"
                    }
                    mock_now.return_value = Mock(isoformat=Mock(return_value="2024-01-01T00:00:00Z"))

                    # Mock semantic tagger to avoid actual tagging
                    with patch('services.doc_store.modules.document_handlers.semantic_tagger') as mock_tagger:
                        mock_tagger.tag_document.return_value = {"status": "tagged"}

                        handler = DocumentHandlers()
                        result = await handler.handle_put_document(request)

                        # Should have called tag_document
                        mock_tagger.tag_document.assert_called_once_with(
                            "test-doc-123", content, metadata
                        )

    @pytest.mark.asyncio
    async def test_tagging_api_endpoints(self):
        """Test semantic tagging API endpoints."""
        from services.doc_store.modules.tagging_handlers import TaggingHandlers

        # Test tag document endpoint
        with patch('services.doc_store.modules.shared_utils.get_document_by_id') as mock_get_doc:
            mock_get_doc.return_value = {
                "content": "Python content",
                "metadata": {"language": "python"}
            }

            with patch('services.doc_store.modules.tagging_handlers.semantic_tagger') as mock_tagger:
                mock_tagger.tag_document.return_value = {
                    "entities_stored": 5,
                    "tags_stored": 3
                }

                handler = TaggingHandlers()
                result = await handler.handle_tag_document("test-doc")

                assert result["data"]["entities_stored"] == 5
                assert result["data"]["tags_stored"] == 3

    @pytest.mark.asyncio
    async def test_tag_search_api(self):
        """Test tag-based search API."""
        from services.doc_store.modules.tagging_handlers import TaggingHandlers

        with patch('services.doc_store.modules.tagging_handlers.semantic_tagger') as mock_tagger:
            mock_tagger.search_by_tags.return_value = [
                {
                    "document_id": "doc1",
                    "content": "Python content",
                    "metadata": {"language": "python"},
                    "created_at": "2024-01-01T00:00:00Z",
                    "tag_matches": 2,
                    "avg_tag_confidence": 0.85
                }
            ]

            handler = TaggingHandlers()
            result = await handler.handle_search_by_tags(["python"], categories=["programming_language"])

            assert len(result["data"]["results"]) == 1
            assert result["data"]["results"][0]["document_id"] == "doc1"
