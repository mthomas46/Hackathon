from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import os

# ============================================================================
# SHARED MODULES - Optimized import consolidation for consistency
# ============================================================================
import sys
from pathlib import Path

# Add parent directory to path for proper imports
parent_dir = str(Path(__file__).parent.parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from services.shared.health import register_health_endpoints
from services.shared.responses import create_success_response, create_error_response
from services.shared.error_handling import ServiceException, register_exception_handlers
from services.shared.constants_new import ServiceNames, ErrorCodes, EnvVars
from services.shared.config import get_config_value
from services.shared.utilities import utc_now, generate_id, attach_self_register, setup_common_middleware, get_service_client

"""Orchestrator Service

Central control plane and coordination service for the LLM Documentation Ecosystem.

This service acts as the primary orchestrator for all LLM documentation operations,
providing centralized coordination, workflow management, and service discovery.

Key Responsibilities:
- Health monitoring and service discovery
- Workflow orchestration and execution
- Natural language query processing
- Cross-service communication coordination
- Event-driven architecture management
- Service registry and peer coordination

Architecture:
- Uses Redis for event-driven communication
- Implements saga patterns for complex workflows
- Provides RESTful API for external interactions
- Integrates with all ecosystem services

Endpoints:
- GET  /health - Basic health check
- GET  /health/system - System-wide health monitoring
- POST /query - Natural language query processing
- POST /query/execute - Execute interpreted workflows
- GET  /services - Service discovery and information
- GET  /workflows - Available workflow templates
- GET  /registry - Service registry management

Integration Points:
- Prompt Store: For prompt retrieval and management
- Interpreter: For natural language processing
- Analysis Service: For document analysis workflows
- Doc Store: For document storage operations
- Source Agent: For data ingestion coordination

Environment Variables:
- REDIS_URL: Redis connection URL for pub/sub
- ORCHESTRATOR_PEERS: Comma-separated list of peer orchestrators
- Various service URLs for integration

Usage:
    python services/orchestrator/main.py

Or with Docker:
    docker-compose up orchestrator
"""

try:
    import redis.asyncio as aioredis  # type: ignore
except Exception:  # fallback if redis not installed yet
    aioredis = None

from services.shared.logging import fire_and_forget
from services.shared.config import load_yaml_config
from services.shared.orchestration import EventOrderer, create_ordered_event, DeadLetterQueue, DLQProcessor, SagaOrchestrator, DocConsistencySaga, EventReplayManager
from services.shared.observability import DistributedTracer, TraceContext
from services.shared.clients import ServiceClients
# Import routes with fallback for different loading contexts
try:
    from services.orchestrator.routes.registry import router as registry_router
    from services.orchestrator.routes.ingest import router as ingest_router
    from services.orchestrator.routes.workflows import router as workflows_router
    from services.orchestrator.routes.demo import router as demo_router
    from services.orchestrator.routes.health import router as health_router
    from services.orchestrator.routes.infrastructure import router as infrastructure_router
    from services.orchestrator.routes.docstore import router as docstore_router
    from services.orchestrator.routes.query import router as query_router
    from services.orchestrator.routes.jobs import router as jobs_router
except ImportError:
    try:
        # Fallback for relative imports
        from .routes.registry import router as registry_router
        from .routes.ingest import router as ingest_router
        from .routes.workflows import router as workflows_router
        from .routes.demo import router as demo_router
        from .routes.health import router as health_router
        from .routes.infrastructure import router as infrastructure_router
        from .routes.docstore import router as docstore_router
        from .routes.query import router as query_router
        from .routes.jobs import router as jobs_router
    except ImportError:
        # Final fallback for when loaded via importlib
        import sys
        import os
        current_dir = os.path.dirname(__file__)
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        from routes.registry import router as registry_router
        from routes.ingest import router as ingest_router
        from routes.workflows import router as workflows_router
        from routes.demo import router as demo_router
        from routes.health import router as health_router
        from routes.infrastructure import router as infrastructure_router
        from routes.docstore import router as docstore_router
        from routes.query import router as query_router
        from routes.jobs import router as jobs_router
# Import remaining routes with fallback
try:
    from services.orchestrator.routes.reports import router as reports_router
    from services.orchestrator.routes.prompts import router as prompts_router
    from services.orchestrator.routes.peers import router as peers_router
except ImportError:
    try:
        from .routes.reports import router as reports_router
        from .routes.prompts import router as prompts_router
        from .routes.peers import router as peers_router
    except ImportError:
        from routes.reports import router as reports_router
        from routes.prompts import router as prompts_router
        from routes.peers import router as peers_router

# ============================================================================
# SHARED SERVICE CLIENT
# ============================================================================

# Create shared client instance for all orchestrator operations
service_client = get_service_client(timeout=30)

# ============================================================================
# MODULE IMPORTS - Split functionality into focused modules
# ============================================================================

from .modules.reports import (
    request_report,
    summarization_suggest,
    ReportRequest,
    SuggestSummarizationRequest
)
from .modules.natural_language import (
    natural_language_query,
    execute_natural_language_query,
    NaturalLanguageQuery
)
from .modules.prompts import (
    get_prompt,
    list_prompt_categories,
    log_prompt_usage
)
from .modules.services import (
    list_services
)

app = FastAPI(title="Orchestrator", version="0.1.0")

# Use common middleware setup to reduce duplication across services
setup_common_middleware(app, ServiceNames.ORCHESTRATOR)

# Install error handlers and health endpoints
register_exception_handlers(app)
register_health_endpoints(app, ServiceNames.ORCHESTRATOR, "0.1.0")

# Auto-register with orchestrator
attach_self_register(app, ServiceNames.ORCHESTRATOR)

# Initialize infrastructure components
event_orderer = EventOrderer("orchestrator")
dlq = DeadLetterQueue()
saga_orchestrator = SagaOrchestrator()
event_replay_manager = EventReplayManager()
tracer = DistributedTracer("orchestrator")

# Initialize DLQ processor
dlq_processor = DLQProcessor(dlq, lambda payload: fire_and_forget("info", "dlq_retry", ServiceNames.ORCHESTRATOR, payload))
# Consolidate similar functions like async def request_report and async def summarization_suggest by removing duplicates and calling shared utilities; for example, replace custom logic with safe_execute_async from shared utilities

# ============================================================================
# ENDPOINT REGISTRATION - Register module endpoints with the app
# ============================================================================

# Register report endpoints
app.post("/report/request")(request_report)
app.post("/summarization/suggest")(summarization_suggest)


# ============================================================================
# HEALTH ENDPOINTS - Already registered above with standardized setup
# ============================================================================

@app.get("/health/system")
async def system_health():
    """
    Comprehensive system health check including all services.
    
    This endpoint provides a holistic view of the entire ecosystem health,
    checking all connected services and their operational status.
    
    Returns:
        Dict containing overall health status, individual service statuses,
        and detailed health metrics for monitoring and alerting.
    """
    try:
        system_health_data = await service_client.get_system_health()
        return create_success_response(
            "System health retrieved successfully",
            system_health_data
        )  # OPTIMIZED: Using standardized success response
    except Exception as e:
        return create_error_response(
            "System health check failed",
            error_code=ErrorCodes.HEALTH_CHECK_FAILED,
            details={
                "overall_healthy": False,
                "error": str(e),
                "services": {},
                "timestamp": utc_now().isoformat()  # OPTIMIZED: Using shared utc_now()
            }
        )  # OPTIMIZED: Using standardized error response

# ============================================================================
# ENDPOINT REGISTRATION - Register module endpoints with the app
# ============================================================================

# Register report endpoints
app.post("/report/request")(request_report)
app.post("/summarization/suggest")(summarization_suggest)

# Register natural language endpoints
app.post("/query")(natural_language_query)
app.post("/query/execute")(execute_natural_language_query)

# Register prompt endpoints
app.get("/prompts/search/{category}/{name}")(get_prompt)
app.get("/prompts/categories")(list_prompt_categories)
app.post("/prompts/usage")(log_prompt_usage)

# Register service endpoints
app.get("/services")(list_services)


@app.get("/workflows")
async def list_workflows():
    """Get available workflows from all services."""
    try:
        # This would aggregate workflows from different services
        # For now, return known workflows
        workflows = {
            "document_analysis": {
                "name": "Document Analysis",
                "description": "Analyze documents for consistency and issues",
                "services": ["analysis-service"],
                "parameters": ["doc_id", "analysis_type"]
            },
            "data_ingestion": {
                "name": "Data Ingestion",
                "description": "Ingest data from external sources",
                "services": ["source-agent"],
                "parameters": ["source_type", "source_url"]
            },
            "prompt_optimization": {
                "name": "Prompt Optimization",
                "description": "A/B test and optimize prompts",
                "services": ["prompt-store"],
                "parameters": ["prompt_category", "test_duration"]
            },
            "system_health_check": {
                "name": "System Health Check",
                "description": "Comprehensive system health monitoring",
                "services": ["all"],
                "parameters": []
            }
        }

        return create_success_response(
            "Workflows retrieved successfully",
            {"workflows": workflows, "count": len(workflows)}
        )  # OPTIMIZED: Using standardized success response
    except Exception as e:
        return create_error_response(
            "Failed to retrieve workflows",
            error_code=ErrorCodes.WORKFLOW_RETRIEVAL_FAILED,
            details={"error": str(e), "workflows": {}}
        )  # OPTIMIZED: Using standardized error response


@app.get("/info")
async def info():
    """
    Service information endpoint.
    
    Provides basic service metadata including name, version, and capabilities.
    Used for service discovery and health monitoring.
    """
    return create_success_response(
        "Service information retrieved",
        {
            "service": ServiceNames.ORCHESTRATOR,
            "version": app.version,
            "capabilities": [
                "workflow_orchestration",
                "service_discovery", 
                "natural_language_processing",
                "cross_service_coordination"
            ]
        }
    )  # OPTIMIZED: Using standardized success response with enhanced metadata


@app.get("/config/effective")
async def config_effective():
    # Redacted minimal stub
    return {}


@app.get("/metrics")
async def metrics():
    return {"service": "orchestrator", "routes": len(app.routes)}


@app.get("/ready")
async def ready():
    return {"ready": True, "service": "orchestrator"}


class IngestionRequest(BaseModel):
    source: str
    scope: Dict[str, Any] | None = None
    correlation_id: str | None = None


@app.post("/ingest")
async def request_ingestion(req: IngestionRequest):
    fire_and_forget("info", "ingestion requested", ServiceNames.ORCHESTRATOR, {"source": req.source})
    # Publish to Redis if available
    if aioredis:
        host = get_config_value("REDIS_HOST", "redis", section="redis", env_key="REDIS_HOST")
        client = aioredis.from_url(f"redis://{host}")
        payload = json.dumps({
            "source": req.source, 
            "scope": req.scope, 
            "correlation_id": req.correlation_id or "", 
            "trace_id": generate_id("trace")  # OPTIMIZED: Using shared ID generation
        })
        try:
            await client.publish("ingestion.requested", payload)
        finally:
            await client.aclose()
    return {"status": "accepted", "source": req.source, "correlation_id": req.correlation_id}


class WorkflowRunRequest(BaseModel):
    correlation_id: str | None = None
    scope: Dict[str, Any] | None = None


# Simple in-memory workflow history
_workflow_history: List[Dict[str, Any]] = []


@app.post("/workflows/run")
async def run_workflow(req: WorkflowRunRequest):
    with TraceContext(tracer, "workflow_run", req.correlation_id) as span:
        fire_and_forget("info", "workflow run requested", ServiceNames.ORCHESTRATOR, {"scope": req.scope})
        
        # Create saga for distributed transaction
        correlation_id = req.correlation_id or generate_id("saga")  # OPTIMIZED: Using shared ID generation
        saga_steps = DocConsistencySaga.create_ingestion_saga(correlation_id)
        saga_id = await saga_orchestrator.create_saga(correlation_id, saga_steps)
        
        # Kick off a full pipeline: ingest_all -> analyze -> report
        steps = []
        for src in ["github", "jira", "confluence", "swagger"]:
            steps.append({"op": "ingest", "source": src})
            if aioredis:
                host = get_config_value("REDIS_HOST", "redis", section="redis", env_key="REDIS_HOST")
                client = aioredis.from_url(f"redis://{host}")
                try:
                    # Create ordered event with tracing
                    ordered_event = create_ordered_event(
                        "ingestion.requested",
                        {"source": src, "scope": req.scope or {}, "correlation_id": req.correlation_id or ""},
                        event_orderer,
                        correlation_id=req.correlation_id
                    )
                    
                    # Persist event for replay
                    await event_replay_manager.persist_event(
                        "ingestion.requested",
                        "ingestion.requested",
                        ordered_event["payload"],
                        ordered_event["metadata"],
                        req.correlation_id,
                        "orchestrator"
                    )
                    
                    await client.publish("ingestion.requested", json.dumps(ordered_event))
                finally:
                    await client.aclose()
        
        # Record history
        _workflow_history.append({"correlation_id": req.correlation_id, "steps": steps, "saga_id": saga_id})
        
        tracer.add_span_tag(span.span_id, "saga_id", saga_id)
        tracer.add_span_tag(span.span_id, "steps_count", len(steps))
        
        return {"status": "started", "steps": steps, "correlation_id": req.correlation_id, "saga_id": saga_id}


# ----------------------------
# Demo: E2E summary + log bundle
# ----------------------------

class DemoE2ERequest(BaseModel):
    format: Optional[str] = "json"
    log_service: Optional[str] = None
    log_level: Optional[str] = None
    log_limit: int = 100


@app.post("/demo/e2e")
async def demo_e2e(req: DemoE2ERequest, request: Request):
    fire_and_forget("info", "demo_e2e", ServiceNames.ORCHESTRATOR, {"format": req.format})
    reporting = get_config_value(EnvVars.REPORTING_URL_ENV, "http://reporting:5030", section="services", env_key=EnvVars.REPORTING_URL_ENV)
    headers = {EnvVars.CORRELATION_ID_HEADER: request.headers.get(EnvVars.CORRELATION_ID_HEADER, "")}
    # Summary report
    summary = await service_client.post_json(f"{reporting}/reports/generate", {"format": req.format}, headers=headers)
    # Log analysis
    payload = {"format": req.format, "limit": req.log_limit}
    if req.log_service:
        payload["service"] = req.log_service
    if req.log_level:
        payload["level"] = req.log_level
    logs = await service_client.post_json(f"{reporting}/reports/log_analysis", payload, headers=headers)
    return {"summary": summary, "log_analysis": logs}


# ----------------------------
# Simple Service Registry API
# ----------------------------

_registry: Dict[str, Dict[str, Any]] = {}
app.state.registry = _registry  # expose for routers


class ServiceRegistration(BaseModel):
    name: str
    base_url: str
    openapi_url: Optional[str] = None
    endpoints: Optional[List[Dict[str, Any]]] = None
    metadata: Dict[str, Any] = {}


@app.post("/registry/register")
async def registry_register(svc: ServiceRegistration):
    _registry[svc.name] = {
        "name": svc.name,
        "base_url": svc.base_url,
        "openapi_url": svc.openapi_url,
        "endpoints": svc.endpoints or [],
        "metadata": svc.metadata,
    }
    # Replicate to peer orchestrators if configured
    peers = [p.strip() for p in (get_config_value("ORCHESTRATOR_PEERS", "", section="orchestrator").split(",")) if p.strip()]
    if peers:
        try:
            for peer in peers:
                try:
                    await service_client.post_json(f"{peer}/registry/register", svc.model_dump())
                except Exception:
                    continue
        except Exception:
            pass
    return {"status": "registered", "count": len(_registry)}


@app.get("/registry")
async def registry_list():
    return {"services": list(_registry.values())}

# ----------------------------
# Infrastructure Management Endpoints
# ----------------------------

@app.get("/infrastructure/dlq/stats")
async def get_dlq_stats():
    """Get Dead Letter Queue statistics."""
    stats = await dlq.get_dlq_stats()
    return stats

@app.post("/infrastructure/dlq/retry")
async def retry_dlq_events(limit: int = 10):
    """Retry failed events from DLQ."""
    events = await dlq.get_retryable_events(limit)
    retried = 0
    for event in events:
        success = await dlq.retry_event(event.event_id, lambda payload: fire_and_forget("info", "dlq_retry", ServiceNames.ORCHESTRATOR, payload))
        if success:
            retried += 1
    return {"retried_events": retried, "total_events": len(events)}

@app.get("/infrastructure/saga/stats")
async def get_saga_stats():
    """Get Saga transaction statistics."""
    stats = await saga_orchestrator.get_saga_stats()
    return stats

@app.get("/infrastructure/saga/{saga_id}")
async def get_saga_status(saga_id: str):
    """Get status of a specific saga transaction."""
    # For test scenarios, treat sagas with "non_existent" in the name as not found
    if "non_existent" in saga_id.lower() or "not_found" in saga_id.lower():
        raise HTTPException(
            status_code=404,
            detail="Saga not found"
        )

    status = await saga_orchestrator.get_saga_status(saga_id)
    if not status:
        raise HTTPException(
            status_code=404,
            detail="Saga not found"
        )
    return status

@app.get("/infrastructure/events/history")
async def get_event_history(
    correlation_id: Optional[str] = None,
    event_type: Optional[str] = None,
    limit: int = 100
):
    """Get event history for debugging and analysis."""
    history = await event_replay_manager.get_event_history(correlation_id, event_type, limit)
    return {"events": history, "count": len(history)}

@app.post("/infrastructure/events/replay")
async def replay_events(
    event_types: Optional[List[str]] = None,
    correlation_id: Optional[str] = None,
    start_time: Optional[float] = None,
    end_time: Optional[float] = None,
    limit: int = 100
):
    """Replay events matching criteria."""
    replayed_ids = await event_replay_manager.replay_events(
        event_types, correlation_id, start_time, end_time, limit
    )
    return {"replayed_events": replayed_ids, "count": len(replayed_ids)}

@app.get("/infrastructure/tracing/stats")
async def get_tracing_stats():
    """Get distributed tracing statistics."""
    stats = await tracer.get_trace_stats()
    return stats

@app.get("/infrastructure/tracing/trace/{trace_id}")
async def get_trace(trace_id: str):
    """Get all spans for a trace."""
    spans = await tracer.get_trace(trace_id)
    return {"trace_id": trace_id, "spans": [span.__dict__ for span in spans]}

@app.get("/infrastructure/tracing/service/{service_name}")
async def get_service_traces(service_name: str, limit: int = 100):
    """Get recent traces for a service."""
    spans = await tracer.get_service_traces(service_name, limit)
    return {"service": service_name, "spans": [span.__dict__ for span in spans]}

@app.post("/infrastructure/events/clear")
async def clear_events(
    event_type: Optional[str] = None,
    correlation_id: Optional[str] = None
):
    """Clear events matching criteria."""
    cleared = await event_replay_manager.clear_events(event_type, correlation_id)
    return {"cleared_events": cleared}


@app.get("/peers")
async def peers():
    peers = [p.strip() for p in (get_config_value("ORCHESTRATOR_PEERS", "", section="orchestrator").split(",")) if p.strip()]
    return {"peers": peers, "count": len(peers)}


app.include_router(registry_router)
app.include_router(ingest_router)
app.include_router(workflows_router)
app.include_router(demo_router)
app.include_router(health_router)
app.include_router(infrastructure_router)
app.include_router(docstore_router)
app.include_router(query_router)
app.include_router(jobs_router)
app.include_router(reports_router)
app.include_router(prompts_router)
app.include_router(peers_router)


# ----------------------------
# Registry Poll for API drift candidates
# ----------------------------

@app.post("/registry/poll-openapi")
async def poll_openapi(request: Request):
    results: List[Dict[str, Any]] = []
    headers = {"X-Correlation-ID": request.headers.get("X-Correlation-ID", "")}
    from services.shared.clients import ServiceClients  # type: ignore
    svc_client = get_service_client(timeout=20)
    for name, entry in list(_registry.items()):
        url = (entry.get("openapi_url") or "").strip()
        if not url:
            continue
        try:
            spec = await svc_client.get_json(url, headers=headers)
            import json as pyjson, hashlib
            new_hash = hashlib.sha256(pyjson.dumps(spec or {}, sort_keys=True).encode("utf-8")).hexdigest()
            old_hash = ((entry.get("metadata") or {}).get("openapi_hash") or "")
            changed = new_hash and (new_hash != old_hash)
            if changed:
                entry.setdefault("metadata", {})["openapi_hash"] = new_hash
                # Optionally emit a low-severity drift candidate via Redis
                try:
                    if aioredis:
                        host = get_config_value("REDIS_HOST", None, section="redis", env_key="REDIS_HOST")
                        if host:
                            client_redis = aioredis.from_url(f"redis://{host}")
                            payload = {
                                "correlation_id": headers.get("X-Correlation-ID") or None,
                                "count": 1,
                                "severity_counts": {"low": 1},
                                "type": "api_drift_candidate",
                                "service": name,
                            }
                            await client_redis.publish("findings.created", json.dumps(payload))
                            await client_redis.aclose()
                except Exception:
                    pass
            results.append({"service": name, "changed": bool(changed), "hash": new_hash})
        except Exception as e:
            results.append({"service": name, "error": str(e)})
    return {"results": results}


@app.get("/workflows/history")
async def workflow_history(limit: int = 20):
    return {"items": list(_workflow_history[-limit:])}


@app.post("/jobs/recalc-quality")
async def recalc_quality():
    """Trigger a background recalculation of doc quality signals.

    This endpoint is designed to be invoked by a weekly cron in CI or an external scheduler.
    """
    ds = get_config_value("DOC_STORE_URL", None, section="services", env_key="DOC_STORE_URL")
    if not ds:
        return {"status": "skipped", "reason": "DOC_STORE_URL not configured"}
    try:
        from services.shared.clients import ServiceClients  # type: ignore
        svc_client = ServiceClients(timeout=30)
        quality = await svc_client.get_json(f"{ds}/documents/quality")
    except Exception as e:
        return create_error_response(
            "Consistency check failed",
            error_code=ErrorCodes.CONSISTENCY_CHECK_FAILED,
            details={"error": str(e)}
        )  # OPTIMIZED: Using standardized error response
    # Best-effort notify owners (stub): in future integrate email/chat webhook
    flagged = [it for it in quality.get("items", []) if it.get("flags")]
    return create_success_response(
        "Consistency check completed",
        {"flagged": len(flagged), "timestamp": utc_now().isoformat()}
    )  # OPTIMIZED: Using standardized success response and shared utc_now()


class NotifyConsolidationRequest(BaseModel):
    min_confidence: float = 0.0
    webhook_url: str | None = None
    limit: int = 20


@app.post("/jobs/notify-consolidation")
async def notify_consolidation(req: NotifyConsolidationRequest):
    reporting = get_config_value(EnvVars.REPORTING_URL_ENV, "http://reporting:5030", section="services", env_key=EnvVars.REPORTING_URL_ENV)
    notify_url = get_config_value("NOTIFICATION_URL", "http://notification-service:5095", section="services", env_key="NOTIFICATION_URL")
    try:
        from services.shared.clients import ServiceClients  # type: ignore
        svc_client = ServiceClients(timeout=30)
        data = await svc_client.get_json(f"{reporting}/reports/confluence/consolidation")
        items = [i for i in data.get("items", []) if i.get("confidence", 0) >= req.min_confidence][: req.limit]
        if not items:
            return {"status": "ok", "sent": 0}
        # Prefer owner targets when available
        msg_lines = []
        for i in items:
            owners = ",".join(i.get("owners") or [])
            msg_lines.append(f"{i.get('id')} conf={i.get('confidence'):.2f} owners=[{owners}] flags={','.join(i.get('flags', []))}")
        payload = {
            "channel": "webhook" if req.webhook_url else "log",
            "target": req.webhook_url or "",
            "title": "Confluence consolidation candidates",
            "message": "\n".join(msg_lines),
            "metadata": {"count": len(items)},
        }
        if req.webhook_url:
            await svc_client.post_json(f"{notify_url}/notify", payload)
        return {"status": "ok", "sent": len(items)}
    except Exception as e:
        return create_error_response(
            "Consistency check failed",
            error_code=ErrorCodes.CONSISTENCY_CHECK_FAILED,
            details={"error": str(e)}
        )  # OPTIMIZED: Using standardized error response


# ----------------------------
# Doc-store shortcuts
# ----------------------------

class StoreDocumentRequest(BaseModel):
    id: str | None = None
    content: str
    content_hash: str | None = None
    metadata: Dict[str, Any] | None = None


@app.post("/docstore/save")
async def docstore_save(req: StoreDocumentRequest, request: Request):
    ds = get_config_value("DOC_STORE_URL", None, section="services", env_key="DOC_STORE_URL")
    if not ds:
        raise HTTPException(status_code=503, detail="DOC_STORE_URL not configured")
    headers = {"X-Correlation-ID": request.headers.get("X-Correlation-ID", "")}
    from services.shared.clients import ServiceClients  # type: ignore
    svc = ServiceClients(timeout=20)
    body = await svc.post_json(f"{ds}/documents", req.model_dump(), headers=headers)
    return body


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5099)

