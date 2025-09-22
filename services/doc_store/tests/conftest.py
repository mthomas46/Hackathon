"""Pytest configuration and shared fixtures for Document Store Service tests.

This module provides comprehensive test fixtures for enterprise-grade testing
of document lifecycle management, search capabilities, versioning, relationships,
analytics, and bulk operations.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List, Optional
import uuid
from datetime import datetime, timedelta

from core.entities import Document, DocumentVersion, DocumentRelationship, DocumentTag
from core.models import DocumentContent, DocumentMetadata, SearchQuery, SearchResult


# =============================================================================
# SHARED TEST FIXTURES
# =============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def request_id():
    """Generate a unique request ID for each test."""
    return str(uuid.uuid4())


@pytest.fixture(scope="function")
def correlation_id():
    """Generate a unique correlation ID for each test."""
    return str(uuid.uuid4())


@pytest.fixture(scope="function")
def test_timestamp():
    """Provide a consistent timestamp for testing."""
    return datetime(2024, 1, 1, 12, 0, 0)


# =============================================================================
# DOMAIN ENTITY FIXTURES
# =============================================================================

@pytest.fixture
def sample_document():
    """Sample Document entity."""
    return Document(
        id=str(uuid.uuid4()),
        title="Sample Technical Document",
        content="This is a comprehensive technical document covering advanced AI concepts...",
        content_type="text/markdown",
        metadata=DocumentMetadata(
            author="John Doe",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            language="en",
            word_count=1250,
            page_count=5,
            file_size_bytes=25600,
            checksum="abc123def456",
            custom_fields={"category": "technical", "priority": "high"}
        ),
        version_id=str(uuid.uuid4()),
        tags=["ai", "technical", "documentation"],
        relationships=[],
        status="published",
        access_control={
            "owner": "john.doe@company.com",
            "readers": ["team@company.com"],
            "writers": ["john.doe@company.com"],
            "public": False
        },
        analytics={
            "view_count": 150,
            "download_count": 45,
            "search_relevance_score": 0.89,
            "last_accessed": datetime.now()
        }
    )


@pytest.fixture
def sample_document_version():
    """Sample DocumentVersion entity."""
    return DocumentVersion(
        id=str(uuid.uuid4()),
        document_id=str(uuid.uuid4()),
        version_number=2,
        title="Updated Technical Document",
        content="This updated version includes additional AI concepts and examples...",
        content_type="text/markdown",
        change_summary="Added new AI concepts section and updated examples",
        change_type="content_update",
        created_by="jane.smith@company.com",
        created_at=datetime.now(),
        file_size_bytes=28900,
        checksum="def456ghi789",
        is_current=False,
        parent_version_id=str(uuid.uuid4())
    )


@pytest.fixture
def sample_document_relationship():
    """Sample DocumentRelationship entity."""
    return DocumentRelationship(
        id=str(uuid.uuid4()),
        source_document_id=str(uuid.uuid4()),
        target_document_id=str(uuid.uuid4()),
        relationship_type="references",
        strength=0.85,
        bidirectional=True,
        created_by="system",
        created_at=datetime.now(),
        metadata={
            "context": "technical_reference",
            "relevance_score": 0.85,
            "discovered_via": "content_analysis"
        }
    )


@pytest.fixture
def sample_document_tag():
    """Sample DocumentTag entity."""
    return DocumentTag(
        id=str(uuid.uuid4()),
        name="artificial-intelligence",
        display_name="Artificial Intelligence",
        category="technology",
        color="#FF6B35",
        description="Documents related to artificial intelligence and machine learning",
        usage_count=45,
        created_by="admin",
        created_at=datetime.now(),
        is_system_tag=False,
        synonyms=["AI", "machine learning", "ML"]
    )


@pytest.fixture
def sample_search_query():
    """Sample SearchQuery for search testing."""
    return SearchQuery(
        query_id=str(uuid.uuid4()),
        query_text="artificial intelligence machine learning",
        search_type="semantic",
        filters={
            "content_type": ["text/markdown", "text/plain"],
            "tags": ["technical", "ai"],
            "date_range": {"start": "2024-01-01", "end": "2024-12-31"},
            "language": ["en"],
            "author": ["john.doe@company.com"]
        },
        sort_by="relevance",
        sort_order="desc",
        limit=50,
        offset=0,
        user_id="test_user",
        session_id=str(uuid.uuid4()),
        query_timestamp=datetime.now()
    )


@pytest.fixture
def sample_search_result():
    """Sample SearchResult for search testing."""
    return SearchResult(
        query_id=str(uuid.uuid4()),
        total_results=125,
        returned_results=25,
        execution_time_ms=450,
        results=[
            {
                "document_id": str(uuid.uuid4()),
                "title": "AI Fundamentals",
                "relevance_score": 0.95,
                "snippets": ["artificial intelligence algorithms", "machine learning models"],
                "metadata": {"author": "John Doe", "created": "2024-01-15"}
            },
            {
                "document_id": str(uuid.uuid4()),
                "title": "Machine Learning Guide",
                "relevance_score": 0.87,
                "snippets": ["machine learning techniques", "AI applications"],
                "metadata": {"author": "Jane Smith", "created": "2024-01-10"}
            }
        ],
        facets={
            "content_type": {"text/markdown": 85, "text/plain": 40},
            "tags": {"technical": 67, "ai": 58, "tutorial": 32},
            "language": {"en": 125}
        },
        suggestions=[
            "Consider also searching for 'deep learning'",
            "Try filtering by date range for more recent content"
        ],
        cache_used=False,
        result_timestamp=datetime.now()
    )


@pytest.fixture
def sample_document_content():
    """Sample DocumentContent for content processing."""
    return DocumentContent(
        document_id=str(uuid.uuid4()),
        content="""# Artificial Intelligence Overview

## Introduction
Artificial Intelligence (AI) refers to the simulation of human intelligence in machines that are programmed to think like humans and mimic their actions.

## Machine Learning
Machine Learning is a subset of AI that provides systems the ability to automatically learn and improve from experience without being explicitly programmed.

### Types of Machine Learning
1. **Supervised Learning**: Learning from labeled training data
2. **Unsupervised Learning**: Finding patterns in unlabeled data
3. **Reinforcement Learning**: Learning through interaction with environment

## Applications
- Natural Language Processing
- Computer Vision
- Robotics
- Expert Systems
- Recommendation Systems

## Future Directions
The future of AI involves more sophisticated algorithms, better hardware, and increased integration with human workflows.""",
        content_type="text/markdown",
        encoding="utf-8",
        processed_content={
            "tokens": ["artificial", "intelligence", "overview", "introduction", "machine", "learning"],
            "sentences": 15,
            "paragraphs": 8,
            "headings": ["Artificial Intelligence Overview", "Introduction", "Machine Learning"],
            "code_blocks": 0,
            "links": 0
        },
        extracted_metadata={
            "title": "Artificial Intelligence Overview",
            "headings": ["Introduction", "Machine Learning", "Types of Machine Learning", "Applications", "Future Directions"],
            "keywords": ["artificial intelligence", "machine learning", "supervised learning", "unsupervised learning"],
            "summary": "Comprehensive overview of artificial intelligence concepts and applications"
        },
        quality_metrics={
            "completeness_score": 0.88,
            "readability_score": 72.5,
            "technical_accuracy": 0.91,
            "structure_score": 0.85
        }
    )


@pytest.fixture
def sample_bulk_operation():
    """Sample bulk operation data."""
    return {
        "operation_id": str(uuid.uuid4()),
        "operation_type": "bulk_import",
        "documents": [
            {
                "title": f"Bulk Document {i}",
                "content": f"Content for bulk document {i}",
                "tags": ["bulk", f"batch_{i//10}"]
            }
            for i in range(100)
        ],
        "configuration": {
            "validate_content": True,
            "extract_metadata": True,
            "create_relationships": False,
            "batch_size": 25,
            "concurrent_batches": 4
        },
        "status": "processing",
        "progress": {
            "total_documents": 100,
            "processed_documents": 75,
            "successful_documents": 72,
            "failed_documents": 3,
            "estimated_completion_time": datetime.now() + timedelta(minutes=5)
        },
        "errors": [
            {"document_index": 45, "error": "Invalid content format"},
            {"document_index": 67, "error": "Missing required metadata"},
            {"document_index": 89, "error": "Duplicate document title"}
        ]
    }


# =============================================================================
# MOCK FIXTURES
# =============================================================================

@pytest.fixture
def mock_repository():
    """Mock document repository for data persistence."""
    mock_repo = AsyncMock()
    mock_repo.save_document = AsyncMock(return_value=str(uuid.uuid4()))
    mock_repo.get_document_by_id = AsyncMock(return_value=None)
    mock_repo.list_documents = AsyncMock(return_value=[])
    mock_repo.update_document = AsyncMock(return_value=True)
    mock_repo.delete_document = AsyncMock(return_value=True)
    mock_repo.search_documents = AsyncMock(return_value=[])
    mock_repo.get_document_versions = AsyncMock(return_value=[])
    mock_repo.save_version = AsyncMock(return_value=str(uuid.uuid4()))
    mock_repo.get_relationships = AsyncMock(return_value=[])
    mock_repo.add_relationship = AsyncMock(return_value=str(uuid.uuid4()))
    return mock_repo


@pytest.fixture
def mock_cache():
    """Mock caching service for performance optimization."""
    mock_cache = AsyncMock()
    mock_cache.get = AsyncMock(return_value=None)
    mock_cache.set = AsyncMock(return_value=True)
    mock_cache.delete = AsyncMock(return_value=1)
    mock_cache.exists = AsyncMock(return_value=False)
    mock_cache.clear = AsyncMock(return_value=True)
    return mock_cache


@pytest.fixture
def mock_event_bus():
    """Mock event bus for domain events."""
    mock_bus = AsyncMock()
    mock_bus.publish = AsyncMock(return_value=True)
    mock_bus.subscribe = AsyncMock(return_value=True)
    mock_bus.unsubscribe = AsyncMock(return_value=True)
    return mock_bus


@pytest.fixture
def mock_search_engine():
    """Mock search engine for document indexing and querying."""
    mock_search = AsyncMock()
    mock_search.index_document = AsyncMock(return_value=True)
    mock_search.remove_document = AsyncMock(return_value=True)
    mock_search.search = AsyncMock(return_value={
        "total_hits": 25,
        "hits": [],
        "facets": {},
        "took_ms": 150
    })
    mock_search.suggest = AsyncMock(return_value=["artificial intelligence", "machine learning"])
    mock_search.get_stats = AsyncMock(return_value={
        "total_documents": 1000,
        "total_size_bytes": 50000000,
        "avg_document_size": 50000
    })
    return mock_search


@pytest.fixture
def mock_file_storage():
    """Mock file storage service."""
    mock_storage = AsyncMock()
    mock_storage.save_file = AsyncMock(return_value="storage://documents/doc_123.pdf")
    mock_storage.get_file = AsyncMock(return_value=b"mock file content")
    mock_storage.delete_file = AsyncMock(return_value=True)
    mock_storage.get_file_info = AsyncMock(return_value={
        "size_bytes": 25600,
        "content_type": "application/pdf",
        "last_modified": datetime.now(),
        "checksum": "abc123def456"
    })
    mock_storage.list_files = AsyncMock(return_value=["doc1.pdf", "doc2.docx", "doc3.txt"])
    return mock_storage


@pytest.fixture
def mock_ai_service():
    """Mock AI service for content analysis and insights."""
    mock_ai = AsyncMock()
    mock_ai.analyze_content = AsyncMock(return_value={
        "topics": ["artificial intelligence", "machine learning"],
        "sentiment": "neutral",
        "complexity": "intermediate",
        "summary": "Document discusses AI and ML concepts",
        "confidence": 0.87
    })
    mock_ai.extract_keywords = AsyncMock(return_value=[
        "artificial intelligence", "machine learning", "algorithms", "neural networks"
    ])
    mock_ai.classify_document = AsyncMock(return_value={
        "category": "technical",
        "subcategory": "ai_ml",
        "confidence": 0.92
    })
    mock_ai.detect_language = AsyncMock(return_value="en")
    mock_ai.translate_content = AsyncMock(return_value="Translated content...")
    return mock_ai


@pytest.fixture
def mock_notification_service():
    """Mock notification service for document events."""
    mock_notification = AsyncMock()
    mock_notification.send_notification = AsyncMock(return_value=True)
    mock_notification.subscribe_to_events = AsyncMock(return_value=True)
    mock_notification.get_notification_history = AsyncMock(return_value=[])
    return mock_notification


@pytest.fixture
def mock_audit_service():
    """Mock audit service for compliance and tracking."""
    mock_audit = AsyncMock()
    mock_audit.log_document_event = AsyncMock(return_value=str(uuid.uuid4()))
    mock_audit.get_audit_trail = AsyncMock(return_value=[])
    mock_audit.generate_compliance_report = AsyncMock(return_value={
        "compliant_documents": 95,
        "non_compliant_documents": 5,
        "issues": ["missing_metadata", "expired_retention"]
    })
    return mock_audit


# =============================================================================
# INTEGRATION TEST FIXTURES
# =============================================================================

@pytest.fixture
def integration_config():
    """Configuration for integration tests."""
    return {
        "database_url": "sqlite:///test_doc_store.db",
        "redis_url": "redis://localhost:6379/1",
        "search_engine_url": "elasticsearch://localhost:9200",
        "file_storage_path": "/tmp/test_doc_store",
        "ai_service_url": "http://localhost:5020",
        "notification_service_url": "http://localhost:5100",
        "test_timeout": 30,
        "cleanup_after_tests": True,
        "test_data": {
            "documents": 50,
            "versions": 25,
            "relationships": 30,
            "tags": 15
        }
    }


@pytest.fixture
def mock_external_services():
    """Mock external services for integration testing."""
    return {
        "search_engine": AsyncMock(),
        "file_storage": AsyncMock(),
        "ai_service": AsyncMock(),
        "notification_service": AsyncMock(),
        "audit_service": AsyncMock(),
        "cache_service": AsyncMock()
    }


# =============================================================================
# PERFORMANCE TEST FIXTURES
# =============================================================================

@pytest.fixture
def performance_test_data():
    """Test data for performance benchmarking."""
    return {
        "documents": [
            {
                "title": f"Performance Test Document {i}",
                "content": f"This is test content for document {i}. " * 100,  # ~3000 chars
                "tags": ["performance", f"batch_{i//10}"],
                "metadata": {
                    "author": f"author_{i%5}@company.com",
                    "created": datetime.now() - timedelta(days=i%30),
                    "word_count": 300 + (i * 10)
                }
            }
            for i in range(1000)  # 1000 documents for performance testing
        ],
        "search_queries": [
            {
                "query": f"performance test document {i}",
                "filters": {"tags": ["performance"]},
                "expected_results": 10
            }
            for i in range(100)
        ],
        "bulk_operations": [
            {
                "operation": "bulk_update",
                "documents": [f"doc_{i}" for i in range(100)],
                "update_data": {"tags": ["bulk_updated"]}
            },
            {
                "operation": "bulk_delete",
                "documents": [f"doc_{i}" for i in range(50, 100)],
            }
        ]
    }


@pytest.fixture
def load_test_scenario():
    """Load testing scenario configuration."""
    return {
        "duration_seconds": 300,
        "concurrent_users": 50,
        "ramp_up_seconds": 60,
        "scenarios": {
            "document_operations": {
                "weight": 40,
                "steps": ["create_document", "read_document", "update_document", "search_documents"]
            },
            "bulk_operations": {
                "weight": 25,
                "steps": ["bulk_import", "bulk_update", "bulk_export", "bulk_delete"]
            },
            "search_operations": {
                "weight": 20,
                "steps": ["simple_search", "complex_search", "faceted_search", "suggest_search"]
            },
            "version_operations": {
                "weight": 15,
                "steps": ["create_version", "list_versions", "revert_version", "compare_versions"]
            }
        },
        "thresholds": {
            "avg_response_time_ms": 1000,
            "error_rate_percent": 1.0,
            "throughput_documents_per_sec": 50,
            "search_response_time_ms": 500
        }
    }


# =============================================================================
# CHAOS ENGINEERING FIXTURES
# =============================================================================

@pytest.fixture
def chaos_experiment_config():
    """Configuration for chaos engineering experiments."""
    return {
        "experiment_name": "document_store_resilience_test",
        "duration_minutes": 15,
        "failure_scenarios": [
            {
                "type": "search_engine_failure",
                "target": "elasticsearch",
                "duration_seconds": 120,
                "impact": "high",
                "fallback_test": True
            },
            {
                "type": "database_connection_loss",
                "target": "postgresql",
                "duration_seconds": 180,
                "impact": "critical",
                "data_integrity_check": True
            },
            {
                "type": "file_storage_unavailable",
                "target": "s3_storage",
                "duration_seconds": 90,
                "impact": "medium",
                "cache_fallback_test": True
            },
            {
                "type": "high_memory_pressure",
                "target": "document_cache",
                "memory_limit_mb": 50,
                "duration_seconds": 300,
                "impact": "medium"
            }
        ],
        "monitoring": {
            "metrics": ["document_create_success_rate", "search_response_time", "cache_hit_rate", "error_rate"],
            "alerts": ["error_rate > 10%", "search_response_time > 5000ms", "document_create_failures > 5"],
            "recovery_time_sla": 300
        },
        "data_integrity_checks": [
            "document_content_preservation",
            "relationship_consistency",
            "version_history_integrity",
            "search_index_accuracy"
        ]
    }


@pytest.fixture
def mock_failure_injector():
    """Mock failure injector for chaos testing."""
    mock_injector = MagicMock()
    mock_injector.inject_search_failure = MagicMock(return_value=True)
    mock_injector.inject_database_failure = MagicMock(return_value=True)
    mock_injector.inject_storage_failure = MagicMock(return_value=True)
    mock_injector.inject_memory_pressure = MagicMock(return_value=True)
    mock_injector.restore_normal_operation = MagicMock(return_value=True)
    mock_injector.get_system_health = MagicMock(return_value={
        "status": "degraded",
        "active_failures": ["search_down", "high_memory"],
        "recovery_eta_seconds": 60,
        "data_integrity_score": 0.95
    })
    return mock_injector
