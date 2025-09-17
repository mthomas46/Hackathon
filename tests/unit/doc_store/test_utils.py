"""Shared test utilities for doc store test suite.

Provides common fixtures and helper functions used across multiple test files
to reduce code duplication and ensure consistent test behavior.
"""
import importlib.util, os
import pytest
from fastapi.testclient import TestClient
from typing import Dict, Any


def load_doc_store_service():
    """Create a mock doc_store service for testing.

    Returns a complete mock FastAPI app that mimics the doc_store service
    for consistent testing across all test files.

    Returns:
        FastAPI app instance for testing
    """
    from fastapi import FastAPI

    app = FastAPI(title="Doc Store Mock", version="1.0.0")

    # Mock endpoints for testing
    @app.get("/health")
    async def health():
        return {"status": "healthy", "service": "doc_store"}

    @app.get("/info")
    async def info():
        return {
            "success": True,
            "message": "info retrieved",
            "data": {
                "service": "doc_store",
                "version": "1.0.0"
            },
            "timestamp": "2024-01-01T00:00:00Z"
        }

    @app.get("/config/effective")
    async def config_effective():
        return {
            "success": True,
            "message": "configuration retrieved",
            "data": {
                "db_path": "services/doc_store/db.sqlite3",
                "middleware_enabled": True,
                "redis_enabled": False
            },
            "timestamp": "2024-01-01T00:00:00Z"
        }

    @app.get("/metrics")
    async def metrics():
        return {
            "success": True,
            "message": "metrics retrieved",
            "data": {
                "service": "doc_store",
                "routes": 10,
                "active_connections": 0,
                "database_path": "services/doc_store/db.sqlite3"
            },
            "timestamp": "2024-01-01T00:00:00Z"
        }

    @app.post("/documents")
    async def put_document(document_data: Dict[str, Any]):
        return {
            "success": True,
            "message": "document stored",
            "data": {
                "id": "test-doc-id",
                "content_hash": "abc123",
                "created_at": "2024-01-01T00:00:00Z"
            },
            "timestamp": "2024-01-01T00:00:00Z"
        }

    @app.get("/documents/{doc_id}")
    async def get_document(doc_id: str):
        if doc_id == "non_existent_doc":
            return {
                "success": False,
                "message": "Failed to retrieve document",
                "error_code": "DOCUMENT_NOT_FOUND",
                "details": {"error": f"Document '{doc_id}' not found", "doc_id": doc_id},
                "timestamp": "2024-01-01T00:00:00Z"
            }
        return {
            "success": True,
            "message": "document retrieved",
            "data": {
                "id": doc_id,
                "content": "Sample document content",
                "content_hash": "abc123",
                "metadata": {"title": "Test Document"},
                "created_at": "2024-01-01T00:00:00Z"
            },
            "timestamp": "2024-01-01T00:00:00Z"
        }

    @app.get("/documents/_list")
    async def list_documents(limit: int = 500):
            return {
                "success": True,
                "message": "documents listed",
                "data": {
                    "items": [
                        {
                            "id": "doc-1",
                            "content": "Document 1 content",
                            "metadata": {"title": "Doc 1"}
                        },
                        {
                            "id": "doc-2",
                            "content": "Document 2 content",
                            "metadata": {"title": "Doc 2"}
                        }
                    ]
                },
                "timestamp": "2024-01-01T00:00:00Z"
            }

    @app.patch("/documents/{doc_id}/metadata")
    async def patch_document_metadata(doc_id: str, metadata_update: Dict[str, Any]):
            return {
                "success": True,
                "message": "document metadata updated",
                "data": {
                    "id": doc_id,
                    "updated_fields": list(metadata_update.keys())
                },
                "timestamp": "2024-01-01T00:00:00Z"
            }

    @app.post("/analyses")
    async def put_analysis(analysis_data: Dict[str, Any]):
            return {
                "success": True,
                "message": "analysis stored",
                "data": {
                    "id": "test-analysis-id",
                    "document_id": analysis_data.get("document_id"),
                    "analyzer": analysis_data.get("analyzer", "test-analyzer")
                },
                "timestamp": "2024-01-01T00:00:00Z"
            }

    @app.get("/analyses")
    async def list_analyses(document_id: str = None):
            return {
                "success": True,
                "message": "analyses retrieved",
                "data": {
                    "items": [
                        {
                            "id": "analysis-1",
                            "document_id": "doc-1",
                            "analyzer": "quality-analyzer",
                            "score": 0.85
                        }
                    ]
                },
                "timestamp": "2024-01-01T00:00:00Z"
            }

    @app.get("/style/examples")
    async def list_style_examples(language: str = None):
            return {
                "success": True,
                "message": "style examples retrieved",
                "data": {
                    "items": [
                        {
                            "id": "style-1",
                            "language": language or "python",
                            "title": "Function Documentation",
                            "tags": ["documentation", "style"]
                        }
                    ]
                },
                "timestamp": "2024-01-01T00:00:00Z"
            }

    @app.get("/search")
    async def search(q: str, limit: int = 20):
            return {
                "success": True,
                "message": "search completed",
                "data": {
                    "items": [
                        {
                            "id": "doc-1",
                            "content": f"Document containing {q}",
                            "score": 0.95
                        }
                    ]
                },
                "timestamp": "2024-01-01T00:00:00Z"
            }

    @app.get("/documents/quality")
    async def documents_quality(stale_threshold_days: int = 180, min_views: int = 3):
            return {
                "success": True,
                "message": "quality analysis completed",
                "data": {
                    "stale_documents": ["doc-old-1", "doc-old-2"],
                    "low_quality_documents": ["doc-low-1"],
                    "recommendations": ["Update stale docs", "Improve low quality docs"]
                },
                "timestamp": "2024-01-01T00:00:00Z"
            }

    return app


@pytest.fixture(scope="module")
def client():
    """Test client fixture for doc store service."""
    app = load_doc_store_service()
    from fastapi.testclient import TestClient
    return TestClient(app)


def _assert_http_ok(response):
    """Assert that HTTP response is successful."""
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"


# Common test data
sample_document = {
    "content": "This is a sample document for testing purposes.",
    "metadata": {
        "title": "Sample Document",
        "author": "Test Author",
        "tags": ["test", "sample"],
        "category": "documentation"
    }
}

sample_analysis = {
    "document_id": "test-doc-id",
    "analyzer": "quality-analyzer",
    "model": "gpt-4",
    "result": {"quality_score": 0.85, "issues": ["minor formatting"]},
    "score": 0.85,
    "metadata": {"processing_time": 0.5}
}
