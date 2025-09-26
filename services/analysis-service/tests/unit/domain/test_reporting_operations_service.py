"""Tests for Reporting Operations Domain Service"""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from services.analysis_service.domain.services.reporting_operations_service import ReportingOperationsService
from services.analysis_service.domain.entities.document import Document
from services.analysis_service.domain.entities.finding import Finding


class TestReportingOperationsService:
    """Test cases for ReportingOperationsService."""

    @pytest.fixture
    def service(self):
        """Create reporting operations service instance."""
        return ReportingOperationsService()

    @pytest.fixture
    def mock_document(self):
        """Create mock document for testing."""
        doc = Mock(spec=Document)
        doc.id = "test-doc-123"
        doc.title = "Test Document"
        doc.content = "This is test content for the document."
        doc.type = "markdown"
        doc.url = "https://example.com/doc123"
        doc.created_at = datetime(2024, 1, 1, 10, 0, 0)
        doc.updated_at = datetime(2024, 1, 2, 10, 0, 0)
        doc.author = "Test Author"
        doc.source = "test_source"
        doc.tags = ["test", "documentation"]
        doc.comments = [
            {
                "author": "Commenter1",
                "content": "This is a test comment",
                "timestamp": "2024-01-01T11:00:00Z"
            }
        ]
        return doc

    @pytest.fixture
    def mock_findings(self):
        """Create mock findings for testing."""
        finding1 = Mock(spec=Finding)
        finding1.severity = "critical"
        finding1.type = "drift"

        finding2 = Mock(spec=Finding)
        finding2.severity = "high"
        finding2.type = "missing_doc"

        finding3 = Mock(spec=Finding)
        finding3.severity = "medium"
        finding3.type = "consistency"

        return [finding1, finding2, finding3]

    @pytest.mark.asyncio
    async def test_generate_document_dump(self, service, mock_document):
        """Test generating document dump."""
        documents = [mock_document]
        format_options = {
            "include_metadata": True,
            "include_content": True,
            "max_content_length": 1000
        }

        result = await service.generate_document_dump(documents, format_options)

        assert result["document_count"] == 1
        assert len(result["sections"]) == 1
        assert result["sections"][0]["document_id"] == "test-doc-123"
        assert result["sections"][0]["title"] == "Test Document"
        assert len(result["sections"][0]["section_lines"]) > 0
        assert "generated_at" in result

    @pytest.mark.asyncio
    async def test_generate_document_dump_empty_list(self, service):
        """Test generating document dump with empty document list."""
        documents = []
        format_options = {}

        result = await service.generate_document_dump(documents, format_options)

        assert result["document_count"] == 0
        assert result["sections"] == []
        assert result["total_sections"] == 0

    def test_generate_document_header(self, service, mock_document):
        """Test generating document header."""
        format_options = {}

        header_lines = service._generate_document_header(mock_document, format_options)

        assert len(header_lines) > 0
        assert header_lines[0].startswith("# 📝")  # Markdown icon
        assert "Test Document" in header_lines[0]
        assert "Type: markdown" in header_lines[1]
        assert "ID: test-doc-123" in header_lines[1]
        assert "URL: https://example.com/doc123" in header_lines[2]

    def test_generate_document_metadata(self, service, mock_document):
        """Test generating document metadata."""
        metadata_lines = service._generate_document_metadata(mock_document)

        assert len(metadata_lines) > 0
        assert metadata_lines[0] == "## 📋 Metadata"
        assert any("Created:" in line for line in metadata_lines)
        assert any("Updated:" in line for line in metadata_lines)
        assert any("Author: Test Author" in line for line in metadata_lines)
        assert any("Source: test_source" in line for line in metadata_lines)
        assert any("Tags: test, documentation" in line for line in metadata_lines)

    def test_generate_document_content(self, service, mock_document):
        """Test generating document content."""
        format_options = {"max_content_length": 50}

        content_lines = service._generate_document_content(mock_document, format_options)

        assert len(content_lines) > 0
        assert content_lines[0] == "## 📄 Content"
        assert "This is test content" in content_lines[2]
        assert "..." in content_lines[2]  # Should be truncated

    def test_generate_document_content_no_truncation(self, service, mock_document):
        """Test generating document content without truncation."""
        format_options = {"max_content_length": 1000}

        content_lines = service._generate_document_content(mock_document, format_options)

        assert len(content_lines) > 0
        assert "This is test content for the document." in content_lines[2]
        assert "..." not in content_lines[2]  # Should not be truncated

    def test_generate_document_comments(self, service, mock_document):
        """Test generating document comments."""
        format_options = {}

        comment_lines = service._generate_document_comments(mock_document, format_options)

        assert len(comment_lines) > 0
        assert comment_lines[0] == "## 💬 Comments/Conversation"
        assert "### Comment 1" in comment_lines
        assert "Author: Commenter1" in comment_lines

    def test_generate_document_comments_no_comments(self, service):
        """Test generating document comments when none exist."""
        mock_doc_no_comments = Mock(spec=Document)
        mock_doc_no_comments.comments = []

        format_options = {}

        comment_lines = service._generate_document_comments(mock_doc_no_comments, format_options)

        assert comment_lines == []  # Should return empty list

    def test_get_type_icon(self, service):
        """Test getting type icons."""
        assert service._get_type_icon("confluence") == "📄"
        assert service._get_type_icon("jira") == "🎫"
        assert service._get_type_icon("pull_request") == "🔄"
        assert service._get_type_icon("unknown") == "📋"
        assert service._get_type_icon("nonexistent") == "📋"

    @pytest.mark.asyncio
    async def test_generate_analysis_summary(self, service, mock_findings):
        """Test generating analysis summary."""
        analysis_results = [
            {"document_id": "doc1", "status": "completed"},
            {"document_id": "doc2", "status": "completed"}
        ]

        result = await service.generate_analysis_summary(mock_findings, analysis_results)

        assert result["total_findings"] == 3
        assert result["severity_breakdown"]["critical"] == 1
        assert result["severity_breakdown"]["high"] == 1
        assert result["severity_breakdown"]["medium"] == 1
        assert result["type_breakdown"]["drift"] == 1
        assert result["type_breakdown"]["missing_doc"] == 1
        assert result["type_breakdown"]["consistency"] == 1
        assert len(result["insights"]) > 0
        assert "generated_at" in result

    def test_count_findings_by_severity(self, service, mock_findings):
        """Test counting findings by severity."""
        counts = service._count_findings_by_severity(mock_findings)

        assert counts["critical"] == 1
        assert counts["high"] == 1
        assert counts["medium"] == 1

    def test_count_findings_by_type(self, service, mock_findings):
        """Test counting findings by type."""
        counts = service._count_findings_by_type(mock_findings)

        assert counts["drift"] == 1
        assert counts["missing_doc"] == 1
        assert counts["consistency"] == 1

    def test_generate_analysis_insights_critical_findings(self, service, mock_findings):
        """Test generating insights when critical findings exist."""
        insights = service._generate_analysis_insights(mock_findings, [])

        assert any("Critical issues found" in insight for insight in insights)
        assert len(insights) > 0

    def test_generate_analysis_insights_no_issues(self, service):
        """Test generating insights when no findings exist."""
        insights = service._generate_analysis_insights([], [])

        assert len(insights) > 0
        assert any("manageable number" in insight.lower() for insight in insights)
