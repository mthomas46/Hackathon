"""
Mock API response fixtures for testing service integrations.
"""
from typing import Dict, Any, List
from datetime import datetime


def mock_mcp_provisioning_response(
    mcp_id: str = "mcp-test-001",
    tier: int = 1,
    status: str = "COLD"
) -> Dict[str, Any]:
    """Mock MCP provisioning API response."""
    return {
        "mcp_id": mcp_id,
        "status": status,
        "tier": tier,
        "created_at": datetime.now().isoformat(),
        "resource_limits": {
            "memory_limit_mb": 2048,
            "cpu_limit": 1.0,
            "disk_limit_mb": 10240
        },
        "config": {
            "port": 8080,
            "chromadb_path": "/data/chromadb",
            "neo4j_uri": "bolt://neo4j:7687"
        }
    }


def mock_training_job_response(
    job_id: str = "job-test-001",
    mcp_id: str = "mcp-test-001",
    status: str = "PENDING"
) -> Dict[str, Any]:
    """Mock training job API response."""
    return {
        "job_id": job_id,
        "mcp_id": mcp_id,
        "status": status,
        "created_at": datetime.now().isoformat(),
        "data_sources": ["doc_store"],
        "progress": 0,
        "documents_processed": 0
    }


def mock_query_response(
    query: str = "What is AI?",
    answer: str = "Artificial Intelligence is...",
    confidence: float = 0.95,
    sources: List[str] = None
) -> Dict[str, Any]:
    """Mock MCP query API response."""
    return {
        "query": query,
        "answer": answer,
        "response": answer,
        "confidence": confidence,
        "sources": sources or ["doc-001", "doc-002", "doc-003"],
        "mcp_id": "mcp-test-001",
        "timestamp": datetime.now().isoformat()
    }


def mock_ingestion_response(
    document_id: str = "doc-test-001",
    success: bool = True
) -> Dict[str, Any]:
    """Mock document ingestion API response."""
    if success:
        return {
            "success": True,
            "document_id": document_id,
            "status": "ingested",
            "timestamp": datetime.now().isoformat()
        }
    else:
        return {
            "success": False,
            "error": "Ingestion failed",
            "document_id": document_id,
            "timestamp": datetime.now().isoformat()
        }


def mock_registry_response(mcp_id: str = "mcp-test-001") -> Dict[str, Any]:
    """Mock MCP registry API response."""
    return {
        "mcp_id": mcp_id,
        "registered": True,
        "registry_entry": {
            "id": mcp_id,
            "name": "test-mcp",
            "tier": 1,
            "status": "active",
            "endpoints": {
                "query": f"http://localhost:8080/query",
                "health": f"http://localhost:8080/health"
            }
        },
        "timestamp": datetime.now().isoformat()
    }


def mock_tagging_response(
    document_id: str = "doc-test-001",
    tags: List[str] = None
) -> Dict[str, Any]:
    """Mock LLM tagging API response."""
    return {
        "document_id": document_id,
        "tags": tags or ["technology", "ai", "machine-learning"],
        "confidence": 0.92,
        "model": "ollama/llama2",
        "timestamp": datetime.now().isoformat()
    }


# Error responses for testing error handling
ERROR_RESPONSES = {
    '404': {
        "error": "Not Found",
        "status_code": 404,
        "message": "The requested resource was not found"
    },
    '422': {
        "error": "Unprocessable Entity",
        "status_code": 422,
        "detail": [
            {
                "loc": ["body", "field_name"],
                "msg": "field required",
                "type": "value_error.missing"
            }
        ]
    },
    '500': {
        "error": "Internal Server Error",
        "status_code": 500,
        "message": "An unexpected error occurred"
    },
    '503': {
        "error": "Service Unavailable",
        "status_code": 503,
        "message": "The service is temporarily unavailable"
    }
}

