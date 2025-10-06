# MCP Provisioner Service

## Overview

The **MCP Provisioner** is the foundational service for the MCP System that manages the complete lifecycle of Model Context Protocol (MCP) instances. It handles provisioning, health monitoring, resource management, and graceful shutdown of MCP containers.

**Status:** 🚧 Phase 1 - In Development  
**Port:** `5400` (Internal) / `8147` (External)  
**Version:** `1.0.0-alpha`  
**Architecture:** Domain-Driven Design (DDD)

---

## Core Responsibilities

### 1. **Lifecycle Management**
- Provision new MCP instances on-demand (Docker containers)
- Manage MCP state machine: `COLD → WARMING → HOT → COOLING → COLD`
- Graceful shutdown of idle MCPs
- Failure detection and recovery

### 2. **Health Monitoring**
- Periodic health checks of HOT instances
- Automatic failover on health check failures (3 strikes → FAILED)
- Health status tracking and reporting

### 3. **Resource Management**
- Monitor CPU, memory, and disk usage
- Enforce resource limits per MCP
- Detect and handle resource overload

### 4. **State Persistence**
- Store MCP instance metadata in Redis
- Track instance state across restarts
- Export/import MCP snapshots

---

## Architecture

### Domain-Driven Design Structure

```
services/mcp-provisioner/
├── domain/                     # Business logic (NO infrastructure dependencies)
│   ├── entities/
│   │   └── mcp_instance.py     # Aggregate root with state machine
│   ├── value_objects/
│   │   ├── mcp_state.py        # State enum with transition logic
│   │   ├── mcp_config.py       # MCP configuration
│   │   └── resource_limits.py  # Resource allocation settings
│   ├── repositories/           # Repository interfaces (abstract)
│   │   └── mcp_repository.py
│   └── services/               # Domain services
│       └── provisioning_service.py
├── application/                # Use cases & orchestration
│   └── use_cases/
│       ├── provision_mcp.py    # Provision new MCP
│       ├── shutdown_mcp.py     # Shutdown MCP
│       └── check_health.py     # Health check
├── infrastructure/             # External concerns
│   ├── repositories/
│   │   └── redis_mcp_repository.py
│   ├── external_services/
│   │   └── docker_client.py    # Docker SDK wrapper
│   └── config/
│       └── settings.py
├── presentation/               # API layer
│   └── api/
│       ├── routes/
│       │   ├── provisioning.py
│       │   └── health.py
│       └── models/
│           ├── requests.py
│           └── responses.py
├── tests/                      # Tests mirror source structure
│   ├── unit/
│   │   └── domain/
│   │       ├── test_mcp_state.py
│   │       └── test_mcp_instance.py
│   ├── integration/
│   └── e2e/
├── main.py                     # FastAPI app composition
├── Dockerfile
├── requirements.txt
└── README.md                   # This file
```

---

## State Machine

### MCP Instance States

```
┌──────┐  provision()   ┌─────────┐  health_ok   ┌─────┐
│ COLD │───────────────→│ WARMING │─────────────→│ HOT │
└──────┘                └─────────┘              └─────┘
   ↑                         │                       │
   │                         │ failed                │ shutdown()
   │                         ↓                       ↓
   │                    ┌────────┐           ┌─────────┐
   └────────────────────│ FAILED │           │ COOLING │
                        └────────┘           └─────────┘
                             ↑                       │
                             │                       │
                             └───────────────────────┘
                                   all_drained
```

### State Descriptions

| State | Description | Resources Required | Can Serve Queries |
|-------|-------------|-------------------|-------------------|
| **COLD** | Not running, stored in registry | None | No |
| **WARMING** | Container starting, loading DBs | Allocated | No |
| **HOT** | Actively serving queries | Allocated | Yes |
| **COOLING** | Draining queries, preparing shutdown | Allocated | No (draining only) |
| **FAILED** | Failed to start or crashed | None | No |

### Transition Rules

- `COLD → WARMING`: Manual provision request
- `WARMING → HOT`: Health check passes, DBs loaded
- `WARMING → FAILED`: Startup timeout or error
- `HOT → COOLING`: Manual shutdown or idle timeout
- `HOT → FAILED`: Too many health check failures (3 strikes)
- `COOLING → COLD`: All in-flight queries drained
- `FAILED → COLD`: Manual recovery

---

## API Endpoints

### Provisioning Endpoints

#### `POST /mcp/provision`
Provision a new MCP instance.

**Request:**
```json
{
  "mcp_id": "client-acme-mcp",
  "tier": 0,
  "config": {
    "docker_image": "mcp-server:tier-0",
    "port": 3000,
    "chromadb_path": "/data/client-acme-mcp/chromadb",
    "neo4j_uri": "bolt://neo4j-client-acme:7687"
  },
  "resource_limits": {
    "cpu_limit": 2.0,
    "memory_limit_mb": 4096,
    "disk_limit_mb": 10240
  }
}
```

**Response (202 Accepted):**
```json
{
  "mcp_id": "client-acme-mcp",
  "state": "warming",
  "message": "Provisioning started",
  "estimated_time_seconds": 60
}
```

#### `POST /mcp/{mcp_id}/shutdown`
Gracefully shutdown an MCP instance.

**Response (200 OK):**
```json
{
  "mcp_id": "client-acme-mcp",
  "state": "cooling",
  "message": "Shutdown initiated"
}
```

#### `GET /mcp/{mcp_id}/status`
Get status of an MCP instance.

**Response (200 OK):**
```json
{
  "mcp_id": "client-acme-mcp",
  "state": "hot",
  "container_id": "abc123",
  "endpoint": "http://mcp-client-acme:3000",
  "host_port": 8200,
  "created_at": "2025-10-06T10:30:00Z",
  "updated_at": "2025-10-06T10:35:00Z",
  "last_health_check": "2025-10-06T10:34:50Z",
  "is_healthy": true,
  "query_count": 145,
  "resource_usage": {
    "cpu": 1.2,
    "memory_mb": 2048
  }
}
```

#### `GET /mcp`
List all MCP instances with optional filters.

**Query Parameters:**
- `state`: Filter by state (cold, warming, hot, cooling, failed)
- `tier`: Filter by tier (0-4)

**Response (200 OK):**
```json
{
  "instances": [
    {
      "mcp_id": "client-acme-mcp",
      "state": "hot",
      "tier": 0,
      "query_count": 145
    },
    ...
  ],
  "total": 5
}
```

### Health Endpoints

#### `GET /health`
Service health check.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "service": "mcp-provisioner",
  "version": "1.0.0",
  "docker_available": true,
  "redis_available": true
}
```

---

## Domain Model

### MCPInstance Entity (Aggregate Root)

**Key Attributes:**
- `mcp_id`: Unique identifier
- `state`: Current lifecycle state
- `config`: MCP configuration
- `resource_limits`: CPU/memory/disk limits
- `container_id`: Docker container ID (when running)
- `endpoint`: HTTP endpoint for queries
- `query_count`: Total queries processed
- `health_check_failures`: Consecutive failures

**Key Business Logic:**
- `start_provisioning()`: COLD → WARMING
- `mark_as_hot()`: WARMING → HOT
- `start_cooling()`: HOT → COOLING
- `mark_as_cold()`: COOLING → COLD
- `mark_as_failed()`: Any state → FAILED
- `recover_from_failure()`: FAILED → COLD
- `record_query()`: Increment query count
- `update_health_status()`: Track health
- `is_idle()`: Check if idle > threshold
- `is_overloaded()`: Check resource usage

### Value Objects

#### MCPState
- Immutable state representation
- State transition validation
- Query methods (`is_active()`, `is_transitioning()`, `is_stopped()`)

#### MCPConfig
- Docker image, port, database paths
- Tier information (0-4)
- Environment variables

#### ResourceLimits
- CPU, memory, disk limits
- Validation logic
- Scaling operations

---

## Integration with Ecosystem

### Docker Network
- Network: `hackathon_default` (doc-ecosystem-dev)
- Subnet: `172.20.0.0/16`

### Dependencies
- **Redis** (`redis:6379`): State persistence
- **Docker SDK**: Container management
- **Log Collector** (`http://log-collector:5080`): Centralized logging

### Shared Components
```python
from services.shared.domain.repositories.base_repository import BaseRepository
from services.shared.infrastructure.config import load_service_config
from services.shared.infrastructure.monitoring.health import register_health_endpoints
from services.shared.presentation.api.responses import create_success_response, create_error_response
```

---

## Development

### Prerequisites
- Python 3.11+
- Docker with Docker SDK
- Redis
- Access to `doc-ecosystem-dev` network

### Setup

```bash
# Navigate to service
cd services/mcp-provisioner

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export PYTHONPATH=/Users/mykalthomas/Documents/work/Hackathon
export SERVICE_NAME=mcp-provisioner
export SERVICE_API_PORT=5400
export REDIS_API_HOST=redis
export ENVIRONMENT=development
```

### Running Locally

```bash
# Option 1: Direct Python
python main.py

# Option 2: Via run script
chmod +x run.sh
./run.sh

# Option 3: Via Docker Compose
docker-compose -f ../../docker-compose.dev.yml up mcp-provisioner
```

### Testing

```bash
# Run all tests
pytest tests/ -v --cov=. --cov-report=html

# Run unit tests only
pytest tests/unit/ -v

# Run specific test file
pytest tests/unit/domain/test_mcp_instance.py -v

# Run with coverage
pytest tests/ -v --cov=domain --cov=application --cov-report=term-missing
```

### Test Coverage Requirements
- **Domain Layer**: >95% coverage (business logic)
- **Application Layer**: >90% coverage (use cases)
- **Infrastructure Layer**: >85% coverage (external integrations)
- **Overall**: >90% coverage

---

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SERVICE_NAME` | Service name | `mcp-provisioner` | Yes |
| `SERVICE_API_PORT` | Internal port | `5400` | Yes |
| `REDIS_API_HOST` | Redis hostname | `redis` | Yes |
| `REDIS_API_PORT` | Redis port | `6379` | No |
| `ENVIRONMENT` | Environment (dev/prod) | `development` | Yes |
| `LOG_LEVEL` | Logging level | `INFO` | No |
| `LOG_COLLECTOR_URL` | Log collector URL | `http://log-collector:5080` | No |
| `DOCKER_HOST` | Docker daemon socket | `unix:///var/run/docker.sock` | No |
| `MCP_DATA_PATH` | MCP data directory | `/data/mcps` | No |
| `HEALTH_CHECK_INTERVAL` | Health check interval (sec) | `30` | No |
| `IDLE_TIMEOUT_MINUTES` | Idle timeout before shutdown | `15` | No |

---

## Monitoring

### Metrics Exposed

- `mcp_instances_total`: Total MCP instances by state
- `mcp_provisioning_duration_seconds`: Time to provision MCP (histogram)
- `mcp_health_check_failures_total`: Health check failures counter
- `mcp_query_count_total`: Total queries processed
- `mcp_resource_usage_cpu`: CPU usage per instance
- `mcp_resource_usage_memory_mb`: Memory usage per instance

### Health Check Endpoints

- `GET /health`: Basic health check
- `GET /health/ready`: Readiness check (can accept traffic)
- `GET /health/live`: Liveness check (service is alive)

---

## Troubleshooting

### Issue: MCP stuck in WARMING state
**Cause:** Container failed to start or health check not passing  
**Solution:**
1. Check container logs: `docker logs <container_id>`
2. Verify ChromaDB and Neo4j are accessible
3. Check resource availability (CPU, memory)
4. Review health check endpoint in MCP service

### Issue: MCP marked as FAILED
**Cause:** 3 consecutive health check failures  
**Solution:**
1. Check `GET /mcp/{mcp_id}/status` for details
2. Review container logs
3. Manually recover: `POST /mcp/{mcp_id}/recover`

### Issue: High resource usage
**Cause:** MCP instance is overloaded  
**Solution:**
1. Check query patterns and volume
2. Increase resource limits
3. Consider horizontal scaling (multiple instances)

---

## Roadmap

### Phase 1 (Current) - Foundation
- [x] Domain model (entities, value objects)
- [x] State machine implementation
- [x] Unit tests (>95% coverage)
- [ ] Repository implementations (Redis)
- [ ] Use cases (provision, shutdown, health check)
- [ ] FastAPI presentation layer
- [ ] Integration tests
- [ ] Docker integration
- [ ] Add to docker-compose.dev.yml

### Phase 2 - Advanced Features
- [ ] MCP export/import
- [ ] Hot-swap capability
- [ ] Resource auto-scaling
- [ ] Multi-node support (clustering)
- [ ] Advanced monitoring (Prometheus)

### Phase 3 - Production
- [ ] Performance optimization
- [ ] Load testing
- [ ] Security hardening
- [ ] Production deployment
- [ ] Documentation completion

---

## Contributing

### Code Standards
- Follow DDD architecture (no shortcuts)
- Write tests BEFORE implementation (TDD)
- >90% test coverage required
- Full OpenAPI annotations on all endpoints
- Use `services/shared/` components (DRY)
- Keep logic simple (KISS)

### Pull Request Checklist
- [ ] Tests pass (`pytest tests/ -v`)
- [ ] Coverage >90% (`pytest --cov`)
- [ ] Linting passes (`flake8`, `mypy`)
- [ ] OpenAPI docs complete (`/docs` endpoint)
- [ ] README updated if needed
- [ ] No direct Ollama calls (use llm-gateway)

---

## References

### Documentation
- [Ecosystem Integration Guide](../../docs/mcp-system-plan/ECOSYSTEM_INTEGRATION_GUIDE.md)
- [MCP System Architecture](../../docs/mcp-system-plan/MCP_SYSTEM_ARCHITECTURE.md)
- [DDD Migration Guide](../../docs/architecture/DDD_MIGRATION.md)

### Related Services
- [MCP Gateway](../mcp-gateway/README.md) - Routes queries to MCPs
- [MCP Registry](../mcp-registry/README.md) - Stores MCP packages
- [MCP Orchestrator](../mcp-orchestrator/README.md) - Workflow orchestration

---

**Status:** 🚧 Under Active Development (Phase 1)  
**Last Updated:** 2025-10-06  
**Maintainer:** MCP System Team  
**Contact:** [Slack #mcp-system-dev]

