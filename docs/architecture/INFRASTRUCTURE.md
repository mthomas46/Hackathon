# Infrastructure Documentation

> Quick Guide: For local development use `docker-compose.dev.yml`. For a richer local stack (LB/metrics/tracing), use `docker-compose.infrastructure.yml`. The root `docker-compose.yml` is legacy and kept for reference.

## Quick Guide

### Compose Stacks
- dev: `docker-compose.dev.yml`
  - Live-code dev; mounts repo; runs `python .../main.py` directly.
  - Start: `docker compose -f docker-compose.dev.yml up -d`
- infrastructure: `docker-compose.infrastructure.yml`
  - Adds nginx, postgres, jaeger, prometheus, grafana, ELK; production-like.
  - Start: `docker compose -f docker-compose.infrastructure.yml up -d`
- services (optional): `docker-compose.services.yml`
  - Adds prompt-store, cli, interpreter to the stack.
- legacy: `docker-compose.yml`
  - Historical. Prefer the dev/infrastructure stacks above.

### Config Precedence
Central loader at `services/shared/config.py`:
1) Environment variables
2) `config/app.yaml` (sections: `redis`, `services`, `http_client`, `orchestrator`)
3) Code defaults

Helper: `get_config_value(key, default, section=None, env_key=None)`

### Common Environment Variables
- Core: `REDIS_HOST`, `DOC_STORE_URL`, `ANALYSIS_SERVICE_URL`, `SOURCE_AGENT_URL`, `REPORTING_URL`, `ORCHESTRATOR_PEERS`
- HTTP client: `HTTP_CLIENT_TIMEOUT`, `HTTP_RETRY_ATTEMPTS`, `HTTP_RETRY_BASE_MS`, `HTTP_CIRCUIT_ENABLED`
- Summarizer Hub: `RATE_LIMIT_ENABLED`, `OLLAMA_HOST`, `BEDROCK_ENDPOINT`, `BEDROCK_MODEL`, `BEDROCK_REGION`, `BEDROCK_API_KEY`

### Docker secrets example (compose)

```yaml
version: '3.9'
services:
  source-agent:
    image: python:3.12-slim
    working_dir: /app
    volumes: [ ./:/app ]
    # Map secrets into files and export to env at runtime, then start service
    secrets:
      - github_token
    command: bash -lc "export GITHUB_TOKEN=$(cat /run/secrets/github_token); \
      pip install --no-cache-dir fastapi uvicorn httpx pydantic && python services/source-agent/main.py"
    ports: ["5000:5000"]

secrets:
  github_token:
    file: ./secrets/github_token
```

Notes:
- Keep secret files out of git (e.g., `./secrets/*` in .gitignore).
- Services resolve secrets via `services/shared/credentials.get_secret("GITHUB_TOKEN")`.

---

> Comprehensive infrastructure setup for the LLM-orchestrated documentation consistency ecosystem.

## Overview

This document describes the infrastructure components that address the identified gaps in the documentation consistency ecosystem:

- **Event Ordering**: Guaranteed message ordering with sequence numbers and timestamps
- **Dead Letter Handling**: Enhanced DLQ with retry policies and exponential backoff
- **Cross-Service Transactions**: Saga pattern for distributed transactions
- **Event Replay**: Event persistence and replay mechanisms for recovery
- **Distributed Tracing**: Comprehensive correlation ID usage and observability
- **Load Balancing**: Nginx configuration with health checks and rate limiting
- **Service Mesh**: Istio integration for advanced traffic management

## Architecture Components

### 1. Event Ordering (`services/shared/event_ordering.py`)

**Purpose**: Ensures guaranteed message ordering and deduplication across services.

**Features**:
- Sequence numbers with timestamps
- Event priority levels (LOW, NORMAL, HIGH, CRITICAL)
- Duplicate detection with TTL windows
- Retry count tracking

**Usage**:
```python
from services.shared.event_ordering import EventOrderer, create_ordered_event

orderer = EventOrderer("service-name")
ordered_event = create_ordered_event(
    "event_type",
    payload,
    orderer,
    priority=EventPriority.HIGH,
    correlation_id="trace-123"
)
```

### 2. Dead Letter Queue (`services/shared/dead_letter_queue.py`)

**Purpose**: Enhanced DLQ implementation with retry policies and management.

**Features**:
- Multiple retry policies (immediate, exponential backoff, linear backoff, fixed delay)
- Configurable retry limits and timeouts
- DLQ statistics and management
- Background retry processor

**Usage**:
```python
from services.shared.dead_letter_queue import DeadLetterQueue, DLQProcessor

dlq = DeadLetterQueue()
await dlq.add_failed_event(
    event_id="evt-123",
    event_type="ingestion.requested",
    payload={"source": "github"},
    metadata={},
    failure_reason="Service unavailable",
    retry_policy=RetryPolicy.EXPONENTIAL_BACKOFF
)
```

### 3. Saga Pattern (`services/shared/saga_pattern.py`)

**Purpose**: Distributed transaction support using the saga pattern.

**Features**:
- Compensation-based transactions
- Step-by-step execution with rollback
- Retry mechanisms for failed steps
- Saga status tracking and statistics

**Usage**:
```python
from services.shared.saga_pattern import SagaOrchestrator, DocConsistencySaga

saga_orchestrator = SagaOrchestrator()
saga_steps = DocConsistencySaga.create_ingestion_saga("trace-123")
saga_id = await saga_orchestrator.create_saga("trace-123", saga_steps)
```

### 4. Event Replay (`services/shared/event_replay.py`)

**Purpose**: Event persistence and replay mechanisms for recovery and debugging.

**Features**:
- Event persistence in Redis
- Replay with filtering (event type, correlation ID, time range)
- Event history for debugging
- Automatic cleanup based on retention policy

**Usage**:
```python
from services.shared.event_replay import EventReplayManager

replay_manager = EventReplayManager()
await replay_manager.persist_event(
    "ingestion.requested",
    "ingestion.requested",
    payload,
    metadata,
    correlation_id="trace-123"
)

# Replay events
replayed_ids = await replay_manager.replay_events(
    event_types=["ingestion.requested"],
    correlation_id="trace-123"
)
```

### 5. Distributed Tracing (`services/shared/distributed_tracing.py`)

**Purpose**: Comprehensive tracing and correlation ID propagation.

**Features**:
- Span creation and management
- Trace context propagation
- Service-specific trace filtering
- Trace statistics and analysis

**Usage**:
```python
from services.shared.distributed_tracing import DistributedTracer, TraceContext

tracer = DistributedTracer("service-name")

with TraceContext(tracer, "operation_name", trace_id) as span:
    # Your operation here
    tracer.add_span_tag(span.span_id, "key", "value")
    tracer.add_span_log(span.span_id, "Operation completed", "info")
```

## Infrastructure Configuration

### Load Balancer (Nginx)

**File**: `infrastructure/nginx.conf`

**Features**:
- Upstream load balancing with health checks
- Rate limiting per endpoint type
- SSL termination support
- CORS headers for API access
- Retry policies and timeouts

**Key Endpoints**:
- `/orchestrator/` - Orchestrator API
- `/reporting/` - Reporting API
- `/consistency-engine/` - Consistency Engine API
- `/doc-store/` - Doc Store API
- `/ingest/` - Ingestion endpoints (higher rate limits)
- `/webhooks/` - Webhook endpoints

### Service Mesh (Istio)

**File**: `infrastructure/istio-gateway.yaml`

**Features**:
- Traffic management and routing
- Circuit breaking and outlier detection
- Security policies (mTLS, authorization)
- Observability integration (Jaeger)
- Load balancing strategies

**Configuration**:
- Gateway for external traffic
- VirtualService for routing rules
- DestinationRule for load balancing policies
- PeerAuthentication for mTLS
- AuthorizationPolicy for access control

### Enhanced Docker Compose

**File**: `docker-compose.infrastructure.yml`

**Services**:
- **Nginx**: Load balancer and reverse proxy
- **Redis**: Event store with persistence
- **PostgreSQL**: Production database
- **Jaeger**: Distributed tracing
- **Prometheus**: Metrics collection
- **Grafana**: Visualization dashboards
- **Elasticsearch**: Log aggregation
- **Kibana**: Log visualization
- **Logstash**: Log processing

## Deployment

### Prerequisites

1. **Docker and Docker Compose**
2. **Kubernetes** (for service mesh deployment)
3. **Istio** (for service mesh features)

### Local Development

```bash
# Start with infrastructure
docker-compose -f docker-compose.infrastructure.yml up -d

# Check service health
curl http://localhost/health

# View metrics
open http://localhost:3000  # Grafana
open http://localhost:16686  # Jaeger
open http://localhost:5601  # Kibana
```

### Production Deployment

1. **Deploy to Kubernetes**:
   ```bash
   kubectl apply -f infrastructure/istio-gateway.yaml
   ```

2. **Configure SSL certificates**:
   ```bash
   kubectl create secret tls doc-consistency-tls \
     --cert=path/to/cert.pem \
     --key=path/to/key.pem
   ```

3. **Set up monitoring**:
   - Configure Prometheus data sources in Grafana
   - Set up log shipping to Elasticsearch
   - Configure alerting rules

## Monitoring and Observability

### Metrics

- **Service Health**: Health check endpoints for all services
- **Performance**: Response times, throughput, error rates
- **Infrastructure**: CPU, memory, disk usage
- **Business**: Event processing rates, saga completion rates

### Tracing

- **Distributed Traces**: End-to-end request tracing
- **Service Maps**: Visual representation of service dependencies
- **Performance Analysis**: Identify bottlenecks and slow operations

### Logging

- **Structured Logs**: JSON-formatted logs with correlation IDs
- **Centralized Aggregation**: All logs collected in Elasticsearch
- **Search and Analysis**: Kibana for log exploration
- **Alerting**: Automated alerts for critical errors

## API Endpoints

### Infrastructure Management

All infrastructure management endpoints are available under `/infrastructure/`:

#### Dead Letter Queue
- `GET /infrastructure/dlq/stats` - DLQ statistics
- `POST /infrastructure/dlq/retry` - Retry failed events

#### Saga Management
- `GET /infrastructure/saga/stats` - Saga statistics
- `GET /infrastructure/saga/{saga_id}` - Saga status

#### Event Replay
- `GET /infrastructure/events/history` - Event history
- `POST /infrastructure/events/replay` - Replay events
- `POST /infrastructure/events/clear` - Clear events

#### Distributed Tracing
- `GET /infrastructure/tracing/stats` - Tracing statistics
- `GET /infrastructure/tracing/trace/{trace_id}` - Get trace
- `GET /infrastructure/tracing/service/{service_name}` - Service traces

## Configuration

### Environment Variables

```bash
# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379

# PostgreSQL Configuration
POSTGRES_HOST=postgres
POSTGRES_DB=doc_consistency
POSTGRES_USER=doc_user
POSTGRES_PASSWORD=doc_password

# Tracing Configuration
JAEGER_AGENT_HOST=jaeger
JAEGER_AGENT_PORT=14268

# Monitoring Configuration
PROMETHEUS_GATEWAY=prometheus:9090
LOG_LEVEL=INFO
```

### Service-Specific Configuration

Each service can be configured with:
- **Retry Policies**: Custom retry behavior for failed operations
- **Circuit Breakers**: Automatic failure detection and recovery
- **Rate Limiting**: Request throttling per service
- **Timeouts**: Request and connection timeouts

## Troubleshooting

### Common Issues

1. **Event Ordering Issues**:
   - Check sequence numbers in event metadata
   - Verify correlation ID propagation
   - Review event priority settings

2. **DLQ Processing**:
   - Monitor DLQ statistics
   - Check retry policies and limits
   - Review failure reasons

3. **Saga Failures**:
   - Check saga status and step failures
   - Review compensation logic
   - Verify service availability

4. **Tracing Issues**:
   - Verify correlation ID headers
   - Check span creation and completion
   - Review trace propagation

### Debugging Tools

- **Jaeger UI**: `http://localhost:16686`
- **Grafana Dashboards**: `http://localhost:3000`
- **Kibana Logs**: `http://localhost:5601`
- **Prometheus Metrics**: `http://localhost:9090`

## Security Considerations

### Network Security
- **mTLS**: Mutual TLS between services
- **Authorization**: Role-based access control
- **Rate Limiting**: DDoS protection
- **CORS**: Cross-origin request handling

### Data Security
- **Encryption**: Data encryption in transit and at rest
- **Secrets Management**: Secure credential storage
- **Audit Logging**: Comprehensive audit trails
- **Access Control**: Fine-grained permissions

## Performance Optimization

### Load Balancing
- **Least Connections**: Distribute load based on active connections
- **Health Checks**: Automatic removal of unhealthy instances
- **Circuit Breakers**: Prevent cascade failures

### Caching
- **Redis Caching**: Frequently accessed data
- **Connection Pooling**: Efficient database connections
- **CDN Integration**: Static content delivery

### Scaling
- **Horizontal Scaling**: Multiple service instances
- **Auto-scaling**: Dynamic resource allocation
- **Resource Limits**: Prevent resource exhaustion

## Maintenance

### Regular Tasks
- **Health Monitoring**: Daily health check reviews
- **Log Analysis**: Weekly log analysis for issues
- **Performance Review**: Monthly performance analysis
- **Security Updates**: Regular security patch updates

### Backup and Recovery
- **Database Backups**: Daily automated backups
- **Configuration Backups**: Version-controlled configurations
- **Disaster Recovery**: Tested recovery procedures

## Conclusion

The infrastructure components provide a robust, production-ready foundation for the documentation consistency ecosystem. With comprehensive monitoring, observability, and management capabilities, the system can handle complex distributed operations while maintaining reliability and performance.

The modular design allows for easy extension and customization based on specific requirements, while the standardized patterns ensure consistency across all services.
