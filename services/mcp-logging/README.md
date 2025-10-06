# MCP Logging Service

**Version:** 1.0.0  
**Port:** 5650  
**Purpose:** Centralized logging for MCP ecosystem

## Overview

The MCP Logging Service provides centralized, structured logging specifically designed for the MCP ecosystem. It's deeply integrated with all 7 MCP services while maintaining loose coupling with the original Log-Collector service.

## Features

### Deep MCP Integration ✅
- **Service-Specific Logging** - Dedicated log streams for each MCP service
- **Training Job Tracking** - Special logging for training pipeline
- **Worker Monitoring** - Track worker execution and performance
- **Error Aggregation** - Real-time error counting per service
- **Trace Support** - Distributed tracing with trace_id/span_id

### Loose Log-Collector Coupling ✅
- **Optional Forwarding** - Can forward logs to original Log-Collector
- **Fail-Safe** - Continues working if Log-Collector unavailable
- **Independent** - Full functionality without Log-Collector

### Storage & Retrieval
- **Redis-Based** - Fast, in-memory log storage
- **Capped Storage** - Last 10,000 logs per service
- **Multi-Index** - Query by service, level, time
- **Real-Time** - Immediate log availability

## Architecture

```
┌─────────────────────────────────────────────┐
│        MCP Services (7 services)             │
│  Provisioner, Infrastructure, Gateway,       │
│  Interpreter, Orchestrator, Registry,        │
│  Training Coordinator                        │
└──────────────────┬──────────────────────────┘
                   │ Deep Integration
                   │ (Direct logging)
                   ▼
         ┌─────────────────────┐
         │  MCP Logging        │
         │  Service (5650)     │
         │                     │
         │  - Ingest logs      │
         │  - Query logs       │
         │  - Track training   │
         │  - Monitor workers  │
         └──────────┬──────────┘
                    │ Optional Forward
                    │ (Loose coupling)
                    ▼
         ┌─────────────────────┐
         │  Original           │
         │  Log-Collector      │
         │  (5080)             │
         └─────────────────────┘
```

## API Endpoints

### Core Logging

#### POST /api/v1/logs
Ingest a log entry.

**Request:**
```json
{
  "service": "mcp-orchestrator",
  "level": "INFO",
  "message": "Workflow created",
  "timestamp": "2025-10-06T12:00:00Z",
  "context": {
    "workflow_id": "wf-123",
    "pattern": "ensemble_orchestration"
  },
  "trace_id": "trace-abc",
  "span_id": "span-xyz"
}
```

#### POST /api/v1/logs/query
Query logs with filters.

**Request:**
```json
{
  "service": "mcp-orchestrator",
  "level": "ERROR",
  "start_time": "2025-10-06T00:00:00Z",
  "end_time": "2025-10-06T23:59:59Z",
  "limit": 100
}
```

#### GET /api/v1/logs/{service}
Get recent logs for a service.

**Example:** `/api/v1/logs/mcp-orchestrator?limit=50`

### Training Logging

#### POST /api/v1/training/{job_id}/log
Log training job event.

#### GET /api/v1/training/{job_id}/logs
Get all logs for a training job.

### Statistics

#### GET /api/v1/stats/errors
Get error counts for all MCP services.

**Response:**
```json
{
  "error_stats": {
    "mcp-provisioner": 0,
    "mcp-infrastructure": 2,
    "mcp-gateway": 1,
    "mcp-interpreter": 0,
    "mcp-orchestrator": 3,
    "mcp-registry": 0,
    "training-coordinator": 5
  },
  "total_errors": 11
}
```

### Integration

#### POST /api/v1/forward
Forward log to both MCP Logging and original Log-Collector.

## Configuration

### Environment Variables

```bash
# Service
SERVICE_NAME=mcp-logging
SERVICE_PORT=5650

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=9

# Log-Collector (optional)
LOG_COLLECTOR_URL=http://log-collector:5080
LOG_COLLECTOR_ENABLED=true

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

## Integration Example

### From MCP Service (Python)

```python
import httpx
import structlog

# Configure logger
logger = structlog.get_logger()

# Log to MCP Logging Service
async def log_to_mcp(service: str, level: str, message: str, **context):
    async with httpx.AsyncClient() as client:
        await client.post(
            "http://mcp-logging:5650/api/v1/logs",
            json={
                "service": service,
                "level": level,
                "message": message,
                "context": context
            }
        )

# Usage
await log_to_mcp(
    "mcp-orchestrator",
    "INFO",
    "Workflow created",
    workflow_id="wf-123",
    pattern="ensemble_orchestration"
)
```

### From Training Worker

```python
# Log training progress
await client.post(
    f"http://mcp-logging:5650/api/v1/training/{job_id}/log",
    json={
        "service": "training-coordinator",
        "level": "INFO",
        "message": "Extraction phase started",
        "context": {
            "phase": "extraction",
            "worker": "github_extractor",
            "documents": 100
        }
    }
)
```

## Storage Details

### Redis Keys

- `mcp:logs:{service}` - Last 10,000 logs per service
- `mcp:logs:recent` - Last 1,000 logs across all services
- `mcp:logs:{service}:{level}` - Last 1,000 logs per level
- `mcp:training:{job_id}` - All logs for training job (7 days TTL)
- `mcp:errors:{service}` - Error count per service

### Data Retention

- **Service Logs:** 10,000 most recent
- **Recent Logs:** 1,000 most recent across all services
- **Level Logs:** 1,000 per level per service
- **Training Logs:** All logs for 7 days

## Running

### Docker Compose

```bash
docker-compose up mcp-logging
```

### Local Development

```bash
cd services/mcp-logging
pip install -r requirements.txt
python main.py
```

### Access

- **API:** http://localhost:5650
- **Docs:** http://localhost:5650/docs
- **Health:** http://localhost:5650/health

## Benefits

### For MCP Services
- **Centralized** - Single place for all MCP logs
- **Structured** - JSON-formatted, queryable logs
- **Fast** - Redis-based, sub-millisecond queries
- **Traceable** - Support for distributed tracing

### For Training Pipeline
- **Job Tracking** - Dedicated logs per training job
- **Worker Monitoring** - Track all worker executions
- **Phase Tracking** - See extraction → normalization → embedding flow
- **Error Analysis** - Quick identification of failures

### For Operations
- **Real-Time** - Immediate log availability
- **Searchable** - Query by service, level, time, trace
- **Aggregated** - Error counts across services
- **Independent** - Works standalone or with Log-Collector

## Comparison: MCP Logging vs Log-Collector

| Feature | MCP Logging | Original Log-Collector |
|---------|-------------|------------------------|
| **Purpose** | MCP ecosystem | General ecosystem |
| **Integration** | Deep (MCP services) | Loose (all services) |
| **Storage** | Redis (fast) | Varies |
| **Specialization** | Training, workers, MCP | General purpose |
| **Retention** | 10K per service | Varies |
| **Training Focus** | ✅ Yes | ❌ No |
| **MCP-Specific** | ✅ Yes | ❌ No |

## Future Enhancements

- [ ] Elasticsearch integration for long-term storage
- [ ] Real-time log streaming via WebSocket
- [ ] Log pattern detection and alerting
- [ ] Automatic anomaly detection
- [ ] Log-based metrics generation
- [ ] Integration with Grafana dashboards

---

**Part of MCP System - Specialized logging for AI orchestration** 🚀

