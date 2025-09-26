"""Tests for request DTO validation."""

import pytest
from application.dto.request_dtos import (
    ValidationHelper,
    CreateDocumentRequest,
    UpdateDocumentRequest,
    PerformAnalysisRequest,
    CreateFindingRequest,
    UpdateFindingRequest,
)


class TestValidationHelper:
    """Test ValidationHelper utility methods."""

    def test_validate_required_field_success(self):
        """Test successful required field validation."""
        errors = []
        ValidationHelper.validate_required_field("test_value", "Test Field", errors)
        assert len(errors) == 0

    def test_validate_required_field_failure(self):
        """Test failed required field validation."""
        errors = []
        ValidationHelper.validate_required_field("", "Test Field", errors)
        assert len(errors) == 1
        assert "Test Field is required" in errors[0]

    def test_validate_required_field_none(self):
        """Test None value validation."""
        errors = []
        ValidationHelper.validate_required_field(None, "Test Field", errors)
        assert len(errors) == 1

    def test_validate_max_length_success(self):
        """Test successful max length validation."""
        errors = []
        ValidationHelper.validate_max_length("test", 10, "Test Field", errors)
        assert len(errors) == 0

    def test_validate_max_length_failure(self):
        """Test failed max length validation."""
        errors = []
        ValidationHelper.validate_max_length("very_long_string", 10, "Test Field", errors)
        assert len(errors) == 1
        assert "Test Field too long" in errors[0]

    def test_validate_enum_success(self):
        """Test successful enum validation."""
        errors = []
        ValidationHelper.validate_enum("option1", ["option1", "option2"], "Test Field", errors)
        assert len(errors) == 0

    def test_validate_enum_failure(self):
        """Test failed enum validation."""
        errors = []
        ValidationHelper.validate_enum("invalid", ["option1", "option2"], "Test Field", errors)
        assert len(errors) == 1
        assert "Invalid Test Field" in errors[0]

    def test_validate_range_success(self):
        """Test successful range validation."""
        errors = []
        ValidationHelper.validate_range(50, 0, 100, "Test Field", errors)
        assert len(errors) == 0

    def test_validate_range_failure(self):
        """Test failed range validation."""
        errors = []
        ValidationHelper.validate_range(150, 0, 100, "Test Field", errors)
        assert len(errors) == 1
        assert "Test Field must be between 0 and 100" in errors[0]

    def test_validate_tags_success(self):
        """Test successful tag validation."""
        errors = []
        ValidationHelper.validate_tags(["tag1", "tag2"], errors)
        assert len(errors) == 0

    def test_validate_tags_failure(self):
        """Test failed tag validation."""
        errors = []
        ValidationHelper.validate_tags(["tag1", "x" * 51], errors)  # 51 characters
        assert len(errors) == 1
        assert "Tag too long" in errors[0]

    def test_validate_at_least_one_field_success(self):
        """Test successful at least one field validation."""
        errors = []
        ValidationHelper.validate_at_least_one_field([None, "value", None], errors)
        assert len(errors) == 0

    def test_validate_at_least_one_field_failure(self):
        """Test failed at least one field validation."""
        errors = []
        ValidationHelper.validate_at_least_one_field([None, None, None], errors)
        assert len(errors) == 1
        assert "At least one field must be provided" in errors[0]


class TestCreateDocumentRequest:
    """Test CreateDocumentRequest validation."""

    def test_valid_request(self):
        """Test valid create document request."""
        request = CreateDocumentRequest(
            title="Test Document",
            content="Test content",
            format="markdown",
            author="Test Author",
            tags=["tag1", "tag2"]
        )
        errors = request.validate()
        assert len(errors) == 0

    def test_missing_required_fields(self):
        """Test missing required fields."""
        request = CreateDocumentRequest(
            title="",
            content="",
            format="markdown"
        )
        errors = request.validate()
        assert len(errors) == 2
        assert any("Title is required" in error for error in errors)
        assert any("Content is required" in error for error in errors)

    def test_title_too_long(self):
        """Test title length validation."""
        request = CreateDocumentRequest(
            title="x" * 201,  # 201 characters
            content="Test content",
            format="markdown"
        )
        errors = request.validate()
        assert len(errors) == 1
        assert "Title too long" in errors[0]

    def test_invalid_format(self):
        """Test format validation."""
        request = CreateDocumentRequest(
            title="Test Document",
            content="Test content",
            format="invalid"
        )
        errors = request.validate()
        assert len(errors) == 1
        assert "Invalid format" in errors[0]

    def test_author_too_long(self):
        """Test author name length validation."""
        request = CreateDocumentRequest(
            title="Test Document",
            content="Test content",
            format="markdown",
            author="x" * 101  # 101 characters
        )
        errors = request.validate()
        assert len(errors) == 1
        assert "Author name too long" in errors[0]

    def test_tags_too_long(self):
        """Test tag length validation."""
        request = CreateDocumentRequest(
            title="Test Document",
            content="Test content",
            format="markdown",
            tags=["tag1", "x" * 51]  # 51 characters
        )
        errors = request.validate()
        assert len(errors) == 1
        assert "Tag too long" in errors[0]


class TestUpdateDocumentRequest:
    """Test UpdateDocumentRequest validation."""

    def test_valid_request(self):
        """Test valid update document request."""
        request = UpdateDocumentRequest(
            document_id="doc123",
            title="Updated Title",
            content="Updated content"
        )
        errors = request.validate()
        assert len(errors) == 0

    def test_missing_document_id(self):
        """Test missing document ID."""
        request = UpdateDocumentRequest(
            document_id="",
            title="Updated Title"
        )
        errors = request.validate()
        assert len(errors) == 1
        assert "Document ID is required" in errors[0]

    def test_no_fields_to_update(self):
        """Test request with no fields to update."""
        request = UpdateDocumentRequest(
            document_id="doc123"
        )
        errors = request.validate()
        assert len(errors) == 1
        assert "At least one field must be provided" in errors[0]


class TestPerformAnalysisRequest:
    """Test PerformAnalysisRequest validation."""

    def test_valid_request(self):
        """Test valid analysis request."""
        request = PerformAnalysisRequest(
            document_id="doc123",
            analysis_type="content_quality",
            priority="high",
            timeout_seconds=300
        )
        errors = request.validate()
        assert len(errors) == 0

    def test_invalid_analysis_type(self):
        """Test invalid analysis type."""
        request = PerformAnalysisRequest(
            document_id="doc123",
            analysis_type="invalid_type"
        )
        errors = request.validate()
        assert len(errors) == 1
        assert "Invalid analysis type" in errors[0]

    def test_invalid_priority(self):
        """Test invalid priority."""
        request = PerformAnalysisRequest(
            document_id="doc123",
            analysis_type="content_quality",
            priority="invalid"
        )
        errors = request.validate()
        assert len(errors) == 1
        assert "Invalid priority" in errors[0]

    def test_timeout_out_of_range(self):
        """Test timeout range validation."""
        request = PerformAnalysisRequest(
            document_id="doc123",
            analysis_type="content_quality",
            timeout_seconds=4000  # > 3600
        )
        errors = request.validate()
        assert len(errors) == 1
        assert "Timeout must be between 10 and 3600" in errors[0]


class TestCreateFindingRequest:
    """Test CreateFindingRequest validation."""

    def test_valid_request(self):
        """Test valid create finding request."""
        request = CreateFindingRequest(
            document_id="doc123",
            analysis_id="analysis456",
            title="Test Finding",
            description="Test description",
            severity="medium",
            category="quality"
        )
        errors = request.validate()
        assert len(errors) == 0

    def test_missing_required_fields(self):
        """Test missing required fields."""
        request = CreateFindingRequest(
            document_id="",
            analysis_id="analysis456",
            title="Test Finding",
            description="Test description",
            severity="medium",
            category="quality"
        )
        errors = request.validate()
        assert len(errors) >= 1
        assert any("Document Id is required" in error for error in errors)

    def test_invalid_confidence_range(self):
        """Test confidence range validation."""
        request = CreateFindingRequest(
            document_id="doc123",
            analysis_id="analysis456",
            title="Test Finding",
            description="Test description",
            severity="medium",
            category="quality",
            confidence=1.5  # > 1.0
        )
        errors = request.validate()
        assert len(errors) == 1
        assert "Confidence must be between 0.0 and 1.0" in errors[0]


class TestUpdateFindingRequest:
    """Test UpdateFindingRequest validation."""

    def test_valid_request(self):
        """Test valid update finding request."""
        request = UpdateFindingRequest(
            finding_id="finding123",
            severity="high",
            confidence=0.8
        )
        errors = request.validate()
        assert len(errors) == 0

    def test_missing_finding_id(self):
        """Test missing finding ID."""
        request = UpdateFindingRequest(
            finding_id="",
            severity="high"
        )
        errors = request.validate()
        assert len(errors) == 1
        assert "Finding ID is required" in errors[0]

    def test_no_fields_to_update(self):
        """Test request with no fields to update."""
        request = UpdateFindingRequest(
            finding_id="finding123"
        )
        errors = request.validate()
        assert len(errors) == 1
        assert "At least one field must be provided" in errors[0]
