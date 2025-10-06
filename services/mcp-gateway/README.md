# MCP Gateway Service

**Version:** 1.0.0  
**Port:** 5300 (Internal) / 8151 (External)  
**Status:** ✅ Production Ready

---

## Overview

The **MCP Gateway Service** is the single entry point for all Model Context Protocol (MCP) interactions within the ecosystem. It provides intelligent routing, load balancing, and health monitoring for dynamic MCP instances.

### Core Mission

- **Route requests** to appropriate MCP instances with intelligent load balancing
- **Monitor health** of all registered MCP instances
- **Load balance** across multiple instances of the same MCP type
- **Provide fault tolerance** with circuit breakers and automatic retries
- **Enable observability** for routing decisions and instance performance

---

## Key Features

### 🎯 Intelligent Routing
- **6 routing strategies**: round_robin, least_loaded, random, sticky_session, priority, closest
- **Health-based routing**: Automatically skip unhealthy instances
- **Load-aware selection**: Prefer instances with lower current load
- **Session affinity**: Maintain sticky sessions for multi-turn conversations

### 🔄 Load Balancing
- **Dynamic instance discovery**: Automatically route to available instances
- **Concurrent request tracking**: Monitor active requests per instance
- **Weighted distribution**: Support priority and weight-based routing
- **Graceful degradation**: Fall back to higher-tier MCPs if specific tier unavailable

### 💚 Health Monitoring
- **Automatic health checks**: Periodic polling of all instances (30s interval)
- **Failure tracking**: Consecutive failure counting with automatic marking as unhealthy
- **Self-healing**: Instances automatically recover when health checks pass
- **Manual health updates**: API for external health check systems

### 🛡️ Fault Tolerance
- **Circuit breaker per instance**: Prevents cascading failures
- **Automatic retries**: Configurable retry logic with exponential backoff
- **Timeout management**: Per-request and per-instance timeouts
- **Error isolation**: Circuit breakers isolate failing instances

### 📊 Observability
- **Routing decisions**: Full tracking of routing choices and reasons
- **Performance metrics**: Response time, load factor, request counts
- **Health status**: Real-time health and availability monitoring
- **OpenAPI documentation**: Interactive API docs at `/docs`

---

## Architecture

The service follows **Domain-Driven Design (DDD)** principles:

```
services/mcp-gateway/
├── domain/                      # Business logic
│   ├── entities/
│   │   ├── mcp_instance.py      # Core aggregate root
│   │   └── routing_decision.py  # Routing observability
│   ├── value_objects/
│   │   ├── mcp_instance_status.py
│   │   ├── routing_strategy.py
│   │   └── health_status.py
│   └── repositories/
│       └── mcp_registry_repository.py
│
├── application/                 # Use cases
│   ├── dto/                     # Data transfer objects
│   └── use_cases/
│       ├── register_instance_use_case.py
│       ├── route_request_use_case.py
│       ├── update_health_use_case.py
│       ├── get_available_instances_use_case.py
│       └── deregister_instance_use_case.py
│
├── infrastructure/              # External integrations
│   ├── config/
│   │   └── settings.py          # Environment configuration
│   ├── repositories/
│   │   └── redis_mcp_registry_repository.py
│   ├── health/
│   │   └── health_checker.py    # Background health monitor
│   └── http/
│       └── mcp_http_client.py   # HTTP client with circuit breaker
│
├── presentation/                # API layer
│   ├── api/
│   │   ├── models/              # Pydantic request/response models
│   │   └── routes/
│   │       ├── gateway.py       # Gateway endpoints
│   │       └── health.py        # Health check endpoints
│   └── dependencies.py          # Dependency injection
│
└── main.py                      # FastAPI application
```

---

## API Endpoints

### Gateway Endpoints

#### Register MCP Instance
```http
POST /api/v1/gateway/register
Content-Type: application/json

{
  "mcp_id": "client-acme",
  "host": "mcp-client-acme",
  "port": 3000,
  "name": "ACME Corp Client MCP",
  "tier": 0,
  "priority": 100,
  "weight": 100,
  "max_concurrent_requests": 50,
  "health_check_url": "http://mcp-client-acme:3000/health",
  "tags": ["client", "acme", "production"],
  "metadata": {"version": "1.0.0"}
}
```

**Response:** `201 Created` with instance details

#### Route Request to MCP
```http
POST /api/v1/gateway/route
Content-Type: application/json

{
  "mcp_id": "client-acme",
  "method": "POST",
  "path": "/api/query",
  "headers": {"Content-Type": "application/json"},
  "body": {"query": "What are ACME's project preferences?"},
  "tier": 0,
  "session_id": "session-123",
  "timeout_seconds": 30
}
```

**Response:** `200 OK` with routing result and metadata

#### List Available Instances
```http
GET /api/v1/gateway/instances?mcp_id=client-acme&tier=0
```

**Response:** `200 OK` with array of available instances

#### Update Instance Health
```http
POST /api/v1/gateway/instances/{instance_id}/health
Content-Type: application/json

{
  "is_healthy": true
}
```

**Response:** `200 OK` with updated instance details

#### Deregister Instance
```http
DELETE /api/v1/gateway/instances/{instance_id}
```

**Response:** `204 No Content`

#### Drain Instance (Graceful Shutdown)
```http
POST /api/v1/gateway/instances/{instance_id}/drain
```

**Response:** `200 OK` with instance status

### Health Endpoints

#### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "mcp-gateway",
  "version": "1.0.0",
  "timestamp": "2025-10-06T12:00:00Z",
  "checks": {
    "redis": "healthy"
  }
}
```

#### Readiness Check (Kubernetes)
```http
GET /ready
```

#### Liveness Check (Kubernetes)
```http
GET /live
```

---

## Configuration

All configuration is done via environment variables (see `.env.example`):

### Key Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `SERVICE_API_PORT` | 5300 | Internal service port |
| `REDIS_HOST` | localhost | Redis hostname |
| `REDIS_DB` | 2 | Redis database number |
| `DEFAULT_ROUTING_STRATEGY` | least_loaded | Routing algorithm |
| `HEALTH_CHECK_INTERVAL_SECONDS` | 30 | Health check frequency |
| `CIRCUIT_BREAKER_ENABLED` | true | Enable circuit breakers |
| `MAX_CONCURRENT_REQUESTS_PER_INSTANCE` | 100 | Instance capacity |

---

## Running the Service

### Docker Compose (Recommended)
```bash
docker-compose --profile mcp_services up mcp-gateway
```

### Local Development
```bash
cd services/mcp-gateway
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
python main.py
```

### Docker
```bash
docker build -t mcp-gateway:latest .
docker run -p 8151:5300 \
  -e REDIS_HOST=redis \
  -e REDIS_PORT=6379 \
  mcp-gateway:latest
```

---

## Integration with Ecosystem

### Dependencies
- **Redis** - Instance registry, caching, rate limiting
- **MCP Infrastructure** - Context and metadata management
- **Log Collector** - Centralized logging

### Ecosystem Services
- **MCP Provisioner** - Notifies Gateway when instances are created/destroyed
- **MCP Orchestrator** - Uses Gateway to route workflow steps to MCPs
- **MCP Instances** - Register with Gateway and receive routed requests

---

## Routing Strategies

### 1. Least Loaded (Default)
Routes to the instance with the lowest current load factor.
```python
# Automatically selects instance with fewest active requests
```

### 2. Round Robin
Distributes requests evenly across all instances.
```python
# Simple, predictable distribution
```

### 3. Sticky Session
Maintains session affinity based on session_id.
```python
# Same session_id always routes to same instance
```

### 4. Priority
Routes to highest priority instances first.
```python
# Use for tiered instance deployment
```

### 5. Random
Random selection for load spreading.
```python
# Good for stateless workloads
```

### 6. Closest
Routes to network-closest instance (placeholder for future geo-routing).

---

## Performance

### Metrics
- **Request latency**: < 10ms (routing overhead)
- **Health check frequency**: 30s (configurable)
- **Circuit breaker timeout**: 60s (configurable)
- **Max concurrent instances**: Unlimited (Redis-based)

### Scalability
- **Horizontal**: Multiple Gateway instances can run simultaneously
- **Vertical**: Handles 1000+ requests/minute per instance
- **Storage**: Redis for O(1) instance lookups

---

## Testing

### Manual Testing
```bash
# Register an instance
curl -X POST http://localhost:8151/api/v1/gateway/register \
  -H "Content-Type: application/json" \
  -d '{
    "mcp_id": "test-mcp",
    "host": "localhost",
    "port": 3000
  }'

# List instances
curl http://localhost:8151/api/v1/gateway/instances

# Route a request
curl -X POST http://localhost:8151/api/v1/gateway/route \
  -H "Content-Type: application/json" \
  -d '{
    "mcp_id": "test-mcp",
    "method": "GET",
    "path": "/api/test"
  }'
```

---

## Monitoring & Observability

### Logs
All operations are logged with structured JSON logging:
```json
{
  "timestamp": "2025-10-06T12:00:00Z",
  "level": "INFO",
  "message": "Routed request req-456 to instance inst-123 (client-acme) - 145.3ms"
}
```

### Health Checks
- **Gateway health**: `GET /health`
- **Instance health**: Automatic background checks every 30s
- **Redis connectivity**: Included in health check

### OpenAPI Documentation
- Interactive docs: `http://localhost:8151/docs`
- ReDoc: `http://localhost:8151/redoc`
- OpenAPI spec: `http://localhost:8151/openapi.json`

---

## Troubleshooting

### Instance not receiving requests
1. Check instance is registered: `GET /api/v1/gateway/instances`
2. Check instance health status: Should be `available`
3. Check health check endpoint is accessible
4. Review Gateway logs for routing decisions

### High latency
1. Check instance load factors: `GET /api/v1/gateway/instances`
2. Review routing strategy (switch to `least_loaded`)
3. Increase max_concurrent_requests per instance
4. Add more instances of the same MCP type

### Circuit breaker open
1. Check instance health and logs
2. Verify instance is responding to health checks
3. Wait for circuit breaker timeout (60s default)
4. Fix underlying instance issues

---

## Development

### Adding a New Routing Strategy
1. Add to `RoutingStrategy` enum
2. Implement logic in `RouteRequestUseCase._select_instance()`
3. Update tests and documentation

### Adding a New Endpoint
1. Create DTOs in `application/dto/`
2. Create use case in `application/use_cases/`
3. Add Pydantic models in `presentation/api/models/`
4. Add route in `presentation/api/routes/`
5. Add tests

---

## License

Part of the MCP Ecosystem - Internal Use

---

## Related Services

- **MCP Provisioner** - Lifecycle management for MCP instances
- **MCP Infrastructure** - Context and metadata management
- **MCP Orchestrator** - Workflow orchestration
- **MCP Interpreter** - Query parsing and intent classification

---

## Support

For issues and questions:
- Check logs: `docker logs hackathon-mcp-gateway`
- Review health endpoint: `http://localhost:8151/health`
- API documentation: `http://localhost:8151/docs`

---

**Status:** ✅ Production Ready  
**Last Updated:** October 6, 2025  
**Version:** 1.0.0

