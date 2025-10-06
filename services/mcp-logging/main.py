"""Main FastAPI application for MCP Logging Service."""

import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import redis.asyncio as redis
import structlog

from pydantic import BaseModel

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Global instances
redis_client: Optional[redis.Redis] = None


class LogEntry(BaseModel):
    """Log entry model."""
    service: str
    level: str
    message: str
    timestamp: Optional[str] = None
    context: dict = {}
    trace_id: Optional[str] = None
    span_id: Optional[str] = None


class LogQuery(BaseModel):
    """Log query model."""
    service: Optional[str] = None
    level: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    limit: int = 100


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager."""
    global redis_client
    
    # Startup
    logger.info("Starting MCP Logging Service")
    
    try:
        # Initialize Redis
        redis_client = redis.Redis(
            host="localhost",
            port=6379,
            db=9,  # Separate DB for MCP logging
            decode_responses=True
        )
        await redis_client.ping()
        logger.info("Redis connection established")
        
        yield
        
    except Exception as e:
        logger.error("Error during startup", error=str(e))
        raise
    
    finally:
        # Shutdown
        logger.info("Shutting down MCP Logging Service")
        if redis_client:
            await redis_client.close()


# Create FastAPI application
app = FastAPI(
    title="MCP Logging Service",
    description="Centralized logging for MCP ecosystem with deep service integration",
    version="1.0.0",
    docs_url="/docs",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        await redis_client.ping()
        return {
            "status": "healthy",
            "service": "mcp-logging",
            "version": "1.0.0",
            "timestamp": datetime.utcnow().isoformat()
        }
    except:
        return {
            "status": "unhealthy",
            "service": "mcp-logging",
            "version": "1.0.0"
        }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "mcp-logging",
        "version": "1.0.0",
        "status": "operational",
        "capabilities": [
            "log_ingestion",
            "log_query",
            "real_time_streaming",
            "mcp_integration",
            "training_tracking",
            "worker_monitoring",
        ]
    }


# Log ingestion
@app.post("/api/v1/logs")
async def ingest_log(log_entry: LogEntry):
    """Ingest a log entry."""
    try:
        # Add timestamp if not provided
        if not log_entry.timestamp:
            log_entry.timestamp = datetime.utcnow().isoformat()
        
        # Store in Redis (last 10000 logs per service)
        log_key = f"mcp:logs:{log_entry.service}"
        log_data = log_entry.model_dump_json()
        
        # Add to list (capped)
        await redis_client.lpush(log_key, log_data)
        await redis_client.ltrim(log_key, 0, 9999)  # Keep last 10000
        
        # Add to recent logs (last 1000 across all services)
        await redis_client.lpush("mcp:logs:recent", log_data)
        await redis_client.ltrim("mcp:logs:recent", 0, 999)
        
        # Index by level
        level_key = f"mcp:logs:{log_entry.service}:{log_entry.level.lower()}"
        await redis_client.lpush(level_key, log_data)
        await redis_client.ltrim(level_key, 0, 999)
        
        # Track error count
        if log_entry.level.upper() in ["ERROR", "CRITICAL"]:
            await redis_client.incr(f"mcp:errors:{log_entry.service}")
        
        logger.info(
            "Log ingested",
            service=log_entry.service,
            level=log_entry.level,
            trace_id=log_entry.trace_id
        )
        
        return {"status": "success", "message": "Log ingested"}
        
    except Exception as e:
        logger.error("Error ingesting log", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Query logs
@app.post("/api/v1/logs/query")
async def query_logs(query: LogQuery):
    """Query logs."""
    try:
        # Determine which key to query
        if query.service and query.level:
            log_key = f"mcp:logs:{query.service}:{query.level.lower()}"
        elif query.service:
            log_key = f"mcp:logs:{query.service}"
        else:
            log_key = "mcp:logs:recent"
        
        # Get logs from Redis
        logs = await redis_client.lrange(log_key, 0, query.limit - 1)
        
        # Parse logs
        import json
        parsed_logs = [json.loads(log) for log in logs]
        
        # Filter by time if specified
        if query.start_time or query.end_time:
            filtered_logs = []
            for log in parsed_logs:
                log_time = log.get("timestamp")
                if query.start_time and log_time < query.start_time:
                    continue
                if query.end_time and log_time > query.end_time:
                    continue
                filtered_logs.append(log)
            parsed_logs = filtered_logs
        
        return {
            "logs": parsed_logs,
            "count": len(parsed_logs),
            "query": query.model_dump()
        }
        
    except Exception as e:
        logger.error("Error querying logs", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Get logs for service
@app.get("/api/v1/logs/{service}")
async def get_service_logs(
    service: str,
    limit: int = Query(default=100, le=1000)
):
    """Get logs for a specific service."""
    try:
        log_key = f"mcp:logs:{service}"
        logs = await redis_client.lrange(log_key, 0, limit - 1)
        
        import json
        parsed_logs = [json.loads(log) for log in logs]
        
        return {
            "service": service,
            "logs": parsed_logs,
            "count": len(parsed_logs)
        }
        
    except Exception as e:
        logger.error("Error getting service logs", service=service, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Get error statistics
@app.get("/api/v1/stats/errors")
async def get_error_stats():
    """Get error statistics for all MCP services."""
    try:
        services = [
            "mcp-provisioner",
            "mcp-infrastructure",
            "mcp-gateway",
            "mcp-interpreter",
            "mcp-orchestrator",
            "mcp-registry",
            "training-coordinator"
        ]
        
        stats = {}
        for service in services:
            error_count = await redis_client.get(f"mcp:errors:{service}")
            stats[service] = int(error_count) if error_count else 0
        
        return {
            "error_stats": stats,
            "total_errors": sum(stats.values())
        }
        
    except Exception as e:
        logger.error("Error getting error stats", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Training job logging
@app.post("/api/v1/training/{job_id}/log")
async def log_training_event(job_id: str, log_entry: LogEntry):
    """Log training job event."""
    try:
        log_entry.context["job_id"] = job_id
        log_entry.service = "training-coordinator"
        
        # Store training-specific logs
        training_key = f"mcp:training:{job_id}"
        log_data = log_entry.model_dump_json()
        
        await redis_client.lpush(training_key, log_data)
        await redis_client.expire(training_key, 86400 * 7)  # Keep for 7 days
        
        # Also ingest normally
        await ingest_log(log_entry)
        
        return {"status": "success", "job_id": job_id}
        
    except Exception as e:
        logger.error("Error logging training event", job_id=job_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Get training logs
@app.get("/api/v1/training/{job_id}/logs")
async def get_training_logs(job_id: str):
    """Get logs for a training job."""
    try:
        training_key = f"mcp:training:{job_id}"
        logs = await redis_client.lrange(training_key, 0, -1)
        
        import json
        parsed_logs = [json.loads(log) for log in logs]
        
        return {
            "job_id": job_id,
            "logs": parsed_logs,
            "count": len(parsed_logs)
        }
        
    except Exception as e:
        logger.error("Error getting training logs", job_id=job_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Integration with original Log-Collector
@app.post("/api/v1/forward")
async def forward_to_log_collector(log_entry: LogEntry):
    """Forward logs to original Log-Collector (loose coupling)."""
    try:
        import httpx
        
        # Forward to Log-Collector if available
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    "http://log-collector:5080/api/logs",
                    json=log_entry.model_dump()
                )
                logger.info("Forwarded to Log-Collector", status=response.status_code)
        except:
            # Fail silently - loose coupling
            logger.debug("Log-Collector not available, skipping forward")
        
        # Always ingest locally
        return await ingest_log(log_entry)
        
    except Exception as e:
        logger.error("Error forwarding log", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=5650,
        reload=True,
        log_level="info"
    )

