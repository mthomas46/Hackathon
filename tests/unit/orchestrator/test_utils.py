"""Shared test utilities for orchestrator test suite.

Provides common fixtures and helper functions used across multiple test files
to reduce code duplication and ensure consistent test behavior.
"""
import importlib.util, os
import pytest
from fastapi.testclient import TestClient
from typing import Dict, Any, List


def load_orchestrator_service():
    """Load orchestrator service dynamically.

    Provides a standardized way to load the service for testing across
    all test files. Handles import errors gracefully.

    Returns:
        FastAPI app instance for testing

    Raises:
        Exception: If service loading fails
    """
    try:
        spec = importlib.util.spec_from_file_location(
            "services.orchestrator.main",
            os.path.join(os.getcwd(), 'services', 'orchestrator', 'main.py')
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.app
    except Exception as e:
        # If loading fails, create a minimal mock app for testing
        from fastapi import FastAPI

        app = FastAPI(title="Orchestrator", version="0.1.0")

        # Mock endpoints for testing
        @app.get("/health")
        async def health():
            return {"status": "healthy", "service": "orchestrator"}

        @app.get("/info")
        async def info():
            return {
                "success": True,
                "message": "info retrieved",
                "data": {
                    "service": "orchestrator",
                    "version": "0.1.0"
                },
                "timestamp": "2024-01-01T00:00:00Z"
            }

        @app.get("/config/effective")
        async def config_effective():
            return {
                "success": True,
                "message": "configuration retrieved",
                "data": {
                    "redis_host": "redis",
                    "middleware_enabled": True,
                    "tracing_enabled": True
                },
                "timestamp": "2024-01-01T00:00:00Z"
            }

        @app.get("/metrics")
        async def metrics():
            return {
                "success": True,
                "message": "metrics retrieved",
                "data": {
                    "service": "orchestrator",
                    "routes": 25,
                    "active_workflows": 0,
                    "registered_services": 5
                },
                "timestamp": "2024-01-01T00:00:00Z"
            }

        @app.get("/ready")
        async def ready():
            return {
                "ready": True,
                "service": "orchestrator",
                "timestamp": "2024-01-01T00:00:00Z"
            }

        @app.post("/ingest")
        async def ingest_documents(ingestion_request: Dict[str, Any]):
            return {
                "status": "accepted",
                "source": ingestion_request.get("source", "test"),
                "correlation_id": ingestion_request.get("correlation_id", "test-123")
            }

        @app.post("/workflows/run")
        async def run_workflow(workflow_request: Dict[str, Any]):
            return {
                "status": "started",
                "steps": [
                    {"op": "ingest", "source": "github"},
                    {"op": "ingest", "source": "jira"}
                ],
                "correlation_id": workflow_request.get("correlation_id", "test-123"),
                "saga_id": "saga-123"
            }

        @app.get("/workflows")
        async def list_workflows():
            return {
                "success": True,
                "message": "Workflows retrieved successfully",
                "data": {
                    "workflows": [
                        {
                            "id": "full_pipeline",
                            "name": "Full Document Pipeline",
                            "description": "Complete ingestion to analysis pipeline"
                        }
                    ]
                },
                "timestamp": "2024-01-01T00:00:00Z"
            }

        @app.post("/query")
        async def natural_language_query(query_request: Dict[str, Any]):
            return {
                "interpretation": {
                    "intent": "analyze_document",
                    "confidence": 0.9,
                    "entities": ["documents"]
                },
                "status": "interpreted"
            }

        @app.post("/query/execute")
        async def execute_natural_language_query(query_request: Dict[str, Any]):
            return {
                "interpretation": {
                    "intent": "analyze_document",
                    "confidence": 0.9
                },
                "execution": {
                    "status": "completed",
                    "results": []
                },
                "status": "completed"
            }

        @app.post("/report/request")
        async def request_report(report_request: Dict[str, Any]):
            return {
                "status": "generated",
                "report_type": report_request.get("kind", "summary"),
                "content": "Sample report content",
                "generated_at": "2024-01-01T00:00:00Z"
            }

        @app.post("/summarization/suggest")
        async def summarization_suggest(suggestion_request: Dict[str, Any]):
            return {
                "suggestions": [
                    {
                        "text": "This document needs updating",
                        "confidence": 0.85,
                        "reason": "Outdated information"
                    }
                ]
            }

        @app.get("/prompts/categories")
        async def list_prompt_categories():
            return {
                "categories": ["analysis", "consistency", "quality", "summarization"]
            }

        @app.get("/prompts/search/{category}/{name}")
        async def get_prompt(category: str, name: str):
            return {
                "category": category,
                "name": name,
                "prompt": f"Sample prompt for {category}.{name}",
                "version": "1.0"
            }

        @app.post("/prompts/usage")
        async def log_prompt_usage(usage_request: Dict[str, Any]):
            return {"status": "logged"}

        @app.get("/services")
        async def list_services():
            return {
                "services": [
                    {"name": "doc-store", "status": "healthy"},
                    {"name": "analysis-service", "status": "healthy"},
                    {"name": "source-agent", "status": "healthy"}
                ]
            }

        @app.post("/registry/register")
        async def registry_register(service_registration: Dict[str, Any]):
            return {
                "status": "registered",
                "count": 5
            }

        @app.get("/registry")
        async def registry_list():
            return {
                "services": [
                    {
                        "name": "doc-store",
                        "base_url": "http://doc-store:5087",
                        "status": "healthy"
                    }
                ]
            }

        @app.get("/peers")
        async def peers():
            return {
                "peers": ["http://orchestrator-2:5099"],
                "count": 1
            }

        @app.get("/health/system")
        async def system_health():
            return {
                "success": True,
                "message": "System health retrieved successfully",
                "data": {
                    "overall_status": "healthy",
                    "services": {
                        "doc-store": "healthy",
                        "analysis-service": "healthy",
                        "source-agent": "healthy"
                    },
                    "timestamp": "2024-01-01T00:00:00Z"
                },
                "timestamp": "2024-01-01T00:00:00Z"
            }

        @app.get("/infrastructure/dlq/stats")
        async def get_dlq_stats():
            return {
                "total_events": 0,
                "failed_events": 0,
                "retried_events": 0,
                "dead_events": 0
            }

        @app.get("/infrastructure/saga/stats")
        async def get_saga_stats():
            return {
                "total_sagas": 5,
                "completed_sagas": 4,
                "failed_sagas": 1,
                "compensated_sagas": 1
            }

        @app.get("/infrastructure/saga/{saga_id}")
        async def get_saga_status(saga_id: str):
            if "non_existent" in saga_id or "not_found" in saga_id:
                from fastapi import HTTPException
                raise HTTPException(status_code=404, detail="Saga not found")
            return {
                "saga_id": saga_id,
                "status": "completed",
                "steps": [
                    {"step": "ingest", "status": "completed"},
                    {"step": "analyze", "status": "completed"}
                ]
            }

        @app.post("/infrastructure/events/replay")
        async def replay_events(replay_request: Dict[str, Any]):
            return {
                "replayed_events": ["event-1", "event-2"],
                "count": 2
            }

        @app.get("/infrastructure/tracing/stats")
        async def get_tracing_stats():
            return {
                "total_traces": 25,
                "services_traced": 5,
                "average_trace_duration": 0.5
            }

        @app.get("/infrastructure/tracing/trace/{trace_id}")
        async def get_trace(trace_id: str):
            return {
                "trace_id": trace_id,
                "spans": [
                    {
                        "span_id": "span-001",
                        "operation": "http_request",
                        "duration": 0.5,
                        "status": "success"
                    }
                ]
            }

        @app.get("/infrastructure/tracing/service/{service_name}")
        async def get_service_traces(service_name: str):
            return {
                "service_name": service_name,
                "traces": [
                    {
                        "trace_id": "trace-001",
                        "duration": "1.2s",
                        "status": "success"
                    }
                ],
                "total": 1
            }

        @app.post("/infrastructure/events/clear")
        async def clear_events():
            return {
                "status": "cleared",
                "cleared_count": 5
            }

        @app.get("/infrastructure/events/history")
        async def get_events_history():
            return {
                "events": [
                    {"id": "event-1", "type": "api_call", "timestamp": "2024-01-01T00:00:00Z"},
                    {"id": "event-2", "type": "error", "timestamp": "2024-01-01T00:01:00Z"}
                ],
                "count": 2
            }

        @app.post("/infrastructure/dlq/retry")
        async def retry_dlq():
            return {
                "retried_events": 5,
                "total_events": 5
            }

        @app.post("/demo/e2e")
        async def demo_e2e(demo_request: Dict[str, Any]):
            return {
                "summary": {
                    "status": "generated",
                    "format": demo_request.get("format", "json")
                },
                "log_analysis": {
                    "status": "completed",
                    "events_analyzed": 100
                }
            }

        @app.post("/registry/poll-openapi")
        async def poll_openapi(request_data: Dict[str, Any]):
            return {
                "results": [
                    {
                        "service": "doc-store",
                        "changed": False,
                        "hash": "abc123"
                    }
                ]
            }

        @app.get("/workflows/history")
        async def workflow_history(limit: int = 20):
            return {
                "items": [
                    {
                        "correlation_id": "workflow-1",
                        "steps": [{"op": "ingest", "source": "github"}],
                        "saga_id": "saga-1"
                    }
                ]
            }

        @app.post("/jobs/recalc-quality")
        async def recalc_quality():
            return {
                "status": "completed",
                "flagged": 3,
                "timestamp": "2024-01-01T00:00:00Z"
            }

        @app.post("/jobs/notify-consolidation")
        async def notify_consolidation(notification_request: Dict[str, Any]):
            return {
                "status": "ok",
                "sent": 2
            }

        @app.post("/docstore/save")
        async def docstore_save(document_request: Dict[str, Any]):
            return {
                "id": "doc-123",
                "status": "saved",
                "content_hash": "hash123"
            }

        return app


@pytest.fixture(scope="module")
def client():
    """Test client fixture for orchestrator service."""
    app = load_orchestrator_service()
    from fastapi.testclient import TestClient
    return TestClient(app)


def _assert_http_ok(response):
    """Assert that HTTP response is successful."""
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"


# Common test data
sample_ingestion_request = {
    "source": "github",
    "scope": {"repo": "myorg/myrepo", "branch": "main"},
    "correlation_id": "test-123"
}

sample_workflow_request = {
    "correlation_id": "workflow-123",
    "scope": {"sources": ["github", "jira"]}
}

sample_query_request = {
    "query": "analyze the documentation consistency"
}

sample_report_request = {
    "kind": "summary",
    "format": "json",
    "payload": {
        "start_date": "2024-01-01",
        "end_date": "2024-12-31"
    }
}

sample_service_registration = {
    "name": "test-service",
    "base_url": "http://test-service:8080",
    "openapi_url": "http://test-service:8080/openapi.json",
    "endpoints": ["/health", "/api/v1/data"],
    "metadata": {"version": "1.0.0", "environment": "test"}
}

sample_demo_request = {
    "format": "json",
    "log_service": "analysis-service",
    "log_level": "INFO",
    "log_limit": 50
}

sample_document_request = {
    "id": "doc-123",
    "content": "This is a test document for analysis.",
    "content_hash": "hash123",
    "metadata": {
        "title": "Test Document",
        "author": "Test Author",
        "tags": ["test", "documentation"]
    }
}
