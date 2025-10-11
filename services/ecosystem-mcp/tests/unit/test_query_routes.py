"""
Unit tests for query routes.
"""

import pytest
from uuid import uuid4

# Test data
SAMPLE_DOC_ID = str(uuid4())


def test_query_documents_structure():
    """Test DocumentQuery structure."""
    from src.api.routes.query import DocumentQuery
    
    query = DocumentQuery(
        service_name="test-service",
        limit=10
    )
    
    assert query.service_name == "test-service"
    assert query.limit == 10
    assert query.offset == 0


def test_document_result_structure():
    """Test DocumentResult structure."""
    from src.api.routes.query import DocumentResult
    
    result = DocumentResult(
        id=SAMPLE_DOC_ID,
        service_name="test-service",
        file_path="/path/to/file.md",
        original_format="markdown",
        normalized_content="# Test",
        content_hash="abc123",
        created_at="2025-01-01T00:00:00",
        updated_at="2025-01-01T00:00:00",
        is_latest=True,
        metadata={}
    )
    
    assert result.service_name == "test-service"
    assert result.is_latest is True


def test_document_validation_structure():
    """Test DocumentValidation structure."""
    from src.api.routes.query import DocumentValidation
    
    validation = DocumentValidation(
        document_id=SAMPLE_DOC_ID,
        is_valid=True,
        issues=[],
        content_length=100,
        has_metadata=True,
        has_embedding=True
    )
    
    assert validation.is_valid is True
    assert len(validation.issues) == 0

