"""
Test helper functions for creating test data.

All helpers automatically mark data as test data
to ensure proper isolation.
"""

from typing import Dict, Any, Optional
from datetime import datetime
import uuid
import hashlib

from src.utils.test_data_marker import TestDataMarker, get_current_test_name
from src.storage.db_models import DocumentModel


def create_test_document(
    content: str,
    file_path: Optional[str] = None,
    file_type: str = "python",
    service_name: str = "test-service",
    session_id: Optional[str] = None,
    **kwargs
) -> DocumentModel:
    """
    Create a test document with automatic test data marking.
    
    Args:
        content: Document content
        file_path: Optional file path
        file_type: Document file type
        service_name: Service name
        session_id: Optional test session ID
        **kwargs: Additional document fields
        
    Returns:
        DocumentModel: Document model marked as test data
    """
    if not file_path:
        file_path = f"test_{uuid.uuid4().hex[:8]}.{file_type}"
    
    # Calculate content hash
    content_hash = hashlib.sha256(content.encode()).hexdigest()
    
    # Create base metadata
    metadata = {
        "language": file_type,
        "size": len(content),
        "lines": content.count('\n') + 1,
    }
    
    # Add test markers (TestDataMarker nests them under 'metadata' key - that's expected)
    marked_data = TestDataMarker.mark_as_test_data(
        metadata,
        session_id=session_id,
        test_name=get_current_test_name()
    )
    
    # Create DocumentModel instance
    doc = DocumentModel(
        file_path=file_path,
        original_format=file_type,
        original_content=content,
        normalized_content=content,  # For tests, use same content
        content_hash=content_hash,
        service_name=service_name,
        ingestion_mode=kwargs.get("ingestion_mode", "snapshot"),
        doc_metadata=marked_data,  # Contains nested 'metadata' with test markers
        is_latest=True,
        **{k: v for k, v in kwargs.items() if k != "ingestion_mode"}
    )
    
    return doc


def create_test_timeline(
    service_name: str = "test-service",
    repo_path: str = "/test/repo",
    session_id: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Create a test timeline with automatic test data marking.
    
    Args:
        service_name: Service name
        repo_path: Repository path
        session_id: Optional test session ID
        **kwargs: Additional timeline fields
        
    Returns:
        Dict[str, Any]: Timeline data marked as test data
    """
    timeline_data = {
        "name": f"test_timeline_{uuid.uuid4().hex[:8]}",
        "service_name": service_name,
        "repo_path": repo_path,
        "start_date": datetime(2024, 1, 1),
        "end_date": datetime(2024, 12, 31),
        "strategy": "monthly",
        "confidence_level": "HIGH",
        "metadata": {
            "purpose": "testing",
        },
        **kwargs
    }
    
    # Mark as test data
    return TestDataMarker.mark_as_test_data(
        timeline_data,
        session_id=session_id,
        test_name=get_current_test_name()
    )


def create_test_commit(
    repo_path: str = "/test/repo",
    session_id: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Create a test git commit with automatic test data marking.
    
    Args:
        repo_path: Repository path
        session_id: Optional test session ID
        **kwargs: Additional commit fields
        
    Returns:
        Dict[str, Any]: Commit data marked as test data
    """
    commit_data = {
        "repo_path": repo_path,
        "commit_hash": uuid.uuid4().hex,
        "message": "Test commit",
        "author": "Test Author",
        "email": "test@example.com",
        "timestamp": datetime.utcnow(),
        "metadata": {
            "branch": "test",
        },
        **kwargs
    }
    
    # Mark as test data
    return TestDataMarker.mark_as_test_data(
        commit_data,
        session_id=session_id,
        test_name=get_current_test_name()
    )


def verify_test_data_marked(data) -> bool:
    """
    Verify that data is properly marked as test data.
    
    Args:
        data: Data to verify (dict or model with doc_metadata attribute)
        
    Returns:
        bool: True if properly marked
        
    Raises:
        AssertionError: If data is not properly marked
    """
    # Get metadata from model or dict
    if hasattr(data, 'doc_metadata'):
        metadata = data.doc_metadata
    elif hasattr(data, 'metadata'):
        metadata = data.metadata
    else:
        metadata = data
    
    assert TestDataMarker.is_test_data(metadata), "Data is not marked as test data"
    assert TestDataMarker.get_test_session(metadata) is not None, "Missing test session ID"
    assert TestDataMarker.get_test_created_at(metadata) is not None, "Missing creation timestamp"
    return True

