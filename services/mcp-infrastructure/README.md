# MCP Infrastructure Service

**Version:** 1.0.0  
**Port:** 5500 (Internal) / 8150 (External)  
**Status:** 🚀 Phase 1 Complete

---

## Overview

The **MCP Infrastructure Service** is the memory, context, and coordination backbone for the entire MCP ecosystem. It provides centralized context management, training state tracking, knowledge graph metadata, and cross-service coordination.

**Inspired by:** `memory-agent` service  
**Architecture:** Domain-Driven Design (DDD)  
**Pattern:** Event-driven with TTL management

---

## Quick Start

### Docker Compose (Recommended)

```bash
# Start service
docker-compose up -d mcp-infrastructure

# View logs
docker-compose logs -f mcp-infrastructure

# Health check
curl http://localhost:8150/api/v1/health
```

### Local Development

```bash
cd services/mcp-infrastructure

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export PYTHONPATH=$(pwd)/../..
export REDIS_HOST=localhost

# Run service
python3 -m uvicorn services.mcp_infrastructure.main:app --reload --port 5500
```

---

## API Endpoints

### Context Management

- `POST /api/v1/context` - Store context
- `GET /api/v1/context/{id}` - Retrieve context
- `GET /api/v1/context` - List contexts (with filters)
- `DELETE /api/v1/context/{id}` - Delete context

### Health & Monitoring

- `GET /api/v1/health` - Health check
- `GET /api/v1/ready` - Readiness probe
- `GET /api/v1/live` - Liveness probe

### Documentation

- `GET /docs` - Swagger UI
- `GET /openapi.json` - OpenAPI spec

---

## Usage Examples

### Store Context

```python
import httpx

response = httpx.post(
    "http://localhost:8150/api/v1/context",
    json={
        "mcp_id": "mcp-123",
        "context_type": "instance",
        "data": {
            "status": "hot",
            "queries_today": 145
        },
        "ttl": 7200,
        "tags": ["tier-0", "production"]
    }
)

context = response.json()["data"]
print(f"Context ID: {context['id']}")
```

### Retrieve Context

```python
context_id = "550e8400-e29b-41d4-a716-446655440000"

response = httpx.get(
    f"http://localhost:8150/api/v1/context/{context_id}"
)

context = response.json()["data"]
print(f"MCP ID: {context['mcp_id']}")
print(f"Data: {context['data']}")
```

### List Contexts

```python
# By MCP ID
response = httpx.get(
    "http://localhost:8150/api/v1/context",
    params={"mcp_id": "mcp-123"}
)

# By context type
response = httpx.get(
    "http://localhost:8150/api/v1/context",
    params={"context_type": "training"}
)

# By tags
response = httpx.get(
    "http://localhost:8150/api/v1/context",
    params={"tags": ["tier-0", "production"]}
)
```

---

## Architecture

### DDD Layers

```
services/mcp-infrastructure/
├── domain/              # Business logic
│   ├── entities/       # MCPContext
│   ├── value_objects/  # MCPContextType, TrainingPhase
│   └── repositories/   # MCPContextRepository interface
│
├── application/        # Use cases
│   ├── dto/           # Request/Response DTOs
│   └── use_cases/     # Store, Retrieve, List, Delete
│
├── infrastructure/     # External integrations
│   ├── config/        # Settings
│   ├── repositories/  # RedisMCPContextRepository
│   └── cache/         # Ring buffer cache
│
└── presentation/      # API layer
    └── api/
        ├── routes/    # FastAPI routers
        └── models/    # Pydantic models
```

### Context Types

| Type | Description | Default TTL |
|------|-------------|-------------|
| `instance` | MCP instance metadata | 2 hours |
| `training` | Training state and progress | 24 hours |
| `knowledge` | Knowledge graph metadata | 4 hours |
| `performance` | Performance metrics | 1 hour |
| `coordination` | Cross-service state | 2 hours |
| `query` | Query history | 1 hour |
| `relationship` | Inter-MCP relationships | 4 hours |
| `error` | Error tracking | 24 hours |

---

## Integration

### MCP Provisioner

```python
from services.shared.clients.mcp_infrastructure_client import MCPInfraClient

mcp_infra = MCPInfraClient()

# After provisioning
await mcp_infra.store_context(
    mcp_id=mcp_instance.id,
    context_type="instance",
    data={
        "client_id": request.client_id,
        "tier": request.tier,
        "provisioned_at": datetime.utcnow().isoformat()
    }
)
```

### Training Coordinator

```python
# Track training progress
await mcp_infra.update_training_state(
    mcp_id=mcp_id,
    phase="embedding",
    progress=0.65,
    statistics={
        "entities_processed": 1250,
        "embeddings_generated": 1180
    }
)
```

### MCP Gateway

```python
# Get hot MCPs for routing
hot_mcps = await mcp_infra.get_hot_mcps(tier=0, limit=5)

# Track query
await mcp_infra.track_query(
    mcp_id=selected_mcp.id,
    response_time=elapsed_ms
)
```

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SERVICE_API_PORT` | `5500` | Internal API port |
| `REDIS_HOST` | `redis` | Redis hostname |
| `REDIS_PORT` | `6379` | Redis port |
| `REDIS_DB` | `1` | Redis database |
| `REDIS_KEY_PREFIX` | `mcp:infra:` | Redis key prefix |
| `MAX_CONTEXT_ITEMS` | `10000` | Max contexts in memory |
| `DEFAULT_TTL` | `3600` | Default TTL (seconds) |
| `LOG_LEVEL` | `INFO` | Logging level |

---

## Development

### Run Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=services/mcp_infrastructure --cov-report=html

# Specific tests
pytest tests/unit/domain/
pytest tests/unit/application/
```

### Code Quality

```bash
# Format code
black services/mcp_infrastructure/

# Sort imports
isort services/mcp_infrastructure/

# Type checking
mypy services/mcp_infrastructure/

# Linting
pylint services/mcp_infrastructure/
```

---

## Monitoring

### Health Checks

```bash
# Service health
curl http://localhost:8150/api/v1/health

# Expected response:
{
  "status": "healthy",
  "service": "mcp-infrastructure",
  "version": "1.0.0",
  "dependencies": {
    "redis": "healthy"
  }
}
```

### Metrics (Planned)

- Context count by type
- TTL expiration rate
- Query latency
- Memory usage

---

## Related Documentation

- **Design Spec:** [`docs/mcp-system-plan/MCP_INFRASTRUCTURE_SERVICE_DESIGN.md`](../../docs/mcp-system-plan/MCP_INFRASTRUCTURE_SERVICE_DESIGN.md)
- **Integration Diagram:** [`docs/mcp-system-plan/MCP_INFRASTRUCTURE_INTEGRATION_DIAGRAM.md`](../../docs/mcp-system-plan/MCP_INFRASTRUCTURE_INTEGRATION_DIAGRAM.md)
- **System Architecture:** [`docs/mcp-system-plan/MCP_SYSTEM_ARCHITECTURE.md`](../../docs/mcp-system-plan/MCP_SYSTEM_ARCHITECTURE.md)

---

**Status:** ✅ Phase 3 Complete - Production Ready (API + Docker)

## Running Tests

### Run All Tests

```bash
cd services/mcp-infrastructure

# Run all tests
pytest

# Run with coverage
pytest --cov=services/mcp_infrastructure --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Run Specific Test Suites

```bash
# Unit tests only (fast)
pytest tests/unit/

# Integration tests (require Redis)
pytest tests/integration/

# Specific test file
pytest tests/unit/domain/test_mcp_context.py

# Specific test
pytest tests/unit/domain/test_mcp_context.py::test_mcp_context_creation
```

### Test with Markers

```bash
# Run unit tests only
pytest -m unit

# Run integration tests only
pytest -m integration

# Exclude slow tests
pytest -m "not slow"
```

---
