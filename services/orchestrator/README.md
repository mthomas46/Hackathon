# 🏢 Orchestrator Service

<!--
LLM Processing Metadata:
- document_type: "service_documentation"
- service_name: "orchestrator"
- port: 5099
- key_concepts: ["ddd", "workflow_orchestration", "service_coordination", "langgraph"]
- architecture: "domain_driven_design"
- processing_hints: "Core service with DDD implementation, workflow management, and service registry"
- cross_references: ["../../ECOSYSTEM_MASTER_LIVING_DOCUMENT.md", "../shared/", "../../tests/orchestrator/"]
- integration_points: ["all_services", "redis", "service_registry", "event_streaming"]
-->

**Enterprise-Grade Workflow Orchestration Platform**

The Orchestrator service is the central coordination and control plane for the LLM Documentation Ecosystem. It provides comprehensive workflow management, multi-service orchestration, enterprise integration, and real-time monitoring capabilities.

[![Tests](https://img.shields.io/badge/tests-50+-brightgreen)](tests/orchestrator/)
[![API Endpoints](https://img.shields.io/badge/API-17-blue)](main.py)
[![Enterprise Ready](https://img.shields.io/badge/enterprise-ready-orange)](README.md)

Navigation: [Home](../../README.md) · [Architecture](../../docs/architecture/) · [Testing](../../docs/guides/TESTING_GUIDE.md) · [Services](../README_SERVICES.md)

## 🎯 Key Features

### 🔄 Workflow Management
- **Parameterized Workflows** - Dynamic input handling with validation
- **Complex Dependencies** - Action sequencing and dependency resolution
- **Execution Monitoring** - Real-time status tracking and progress reporting
- **Version Control** - Workflow versioning and change management
- **Template System** - Pre-built workflow templates for common scenarios

### 🤝 Multi-Service Orchestration
- **Service Discovery** - Automatic service location and health checking
- **Cross-Service Communication** - Secure inter-service messaging
- **Event-Driven Processing** - Real-time event handling and correlation
- **Load Balancing** - Intelligent request distribution
- **Circuit Breaking** - Fault tolerance and graceful degradation

### 🏢 Enterprise Integration
- **Service Mesh** - Mutual TLS, authentication, and traffic management
- **Event Streaming** - Real-time event publishing and subscription
- **Enterprise Monitoring** - Health checks, metrics, and alerting
- **Audit Trails** - Complete request tracking and compliance logging
- **Security** - Enterprise-grade authentication and authorization

## 🏗️ Architecture

### 🎨 Domain-Driven Design Implementation

The Orchestrator follows **enterprise-grade Domain-Driven Design (DDD)** principles with clear bounded contexts:

```
services/orchestrator/
├── domain/                    # Business logic organized by domain
│   ├── workflow_management/   # Workflow execution and management
│   ├── service_registry/      # Service discovery and registration  
│   ├── health_monitoring/     # System health and monitoring
│   ├── infrastructure/        # DLQ, saga, tracing, event streaming
│   ├── ingestion/            # Data ingestion orchestration
│   └── query_processing/      # Query execution coordination
├── application/               # Use cases and application services
├── infrastructure/           # External services and persistence
└── presentation/             # API controllers and endpoints
```

### 🔗 Service Interaction Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │  Orchestrator   │    │  Service Mesh   │
│   Interface     │◄──►│   Service       │◄──►│   (Security)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Workflow       │    │  Event          │    │  Health         │
│  Management     │    │  Streaming      │    │  Monitoring     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Ecosystem Services                       │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │ Interpreter │ │ Doc Store   │ │ Analysis    │ ...      │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

### 🎯 Key Design Decisions

#### **1. Microservices Orchestration**
- **Decision**: Adopt orchestration over choreography for complex workflows
- **Rationale**: Central coordination provides better visibility, debugging, and failure handling
- **Implementation**: Dependency injection container with clean separation of concerns

#### **2. Event-Driven Architecture**
- **Decision**: Redis-based event streaming with saga patterns
- **Rationale**: Asynchronous processing for AI workloads, resilience through event replay
- **Components**: Event ordering, saga orchestration, circuit breakers, dead letter queues

#### **3. LangGraph Integration**
- **Decision**: AI-powered workflow orchestration capabilities
- **Rationale**: Enable intelligent decision making and workflow optimization
- **Implementation**: Service-to-tool conversion, context-aware execution planning

### 🔄 Service Dependencies

**Primary Dependencies**:
- **Redis**: Service coordination, event streaming, caching
- **All Ecosystem Services**: Orchestration targets and health monitoring

**Service Interaction Patterns**:
```mermaid
orchestrator --> discovery-agent: Service registration
orchestrator --> llm-gateway: AI workflow coordination  
orchestrator --> doc_store: Document orchestration
orchestrator --> analysis-service: Analysis coordination
orchestrator --> memory-agent: Context management
```

## 🚀 Quick Start

### Prerequisites
```bash
Python 3.8+
pip install -r ../../../requirements.txt
```

### Running the Service
```bash
# Start the orchestrator service
python main.py

# Or run with uvicorn
uvicorn main:app --host 0.0.0.0 --port 5080 --reload
```

### Basic Usage
```python
from orchestrator.modules.workflow_management.service import WorkflowManagementService

# Create workflow service
workflow_service = WorkflowManagementService()

# Create a simple workflow
workflow_data = {
    "name": "Hello World Workflow",
    "description": "A simple notification workflow",
    "parameters": [
        {
            "name": "message",
            "type": "string",
            "description": "Message to display",
            "required": True
        }
    ],
    "actions": [
        {
            "action_id": "notify",
            "action_type": "notification",
            "name": "Send Notification",
            "description": "Send completion notification",
            "config": {
                "message": "{{message}}",
                "channels": ["log"]
            }
        }
    ]
}

# Create workflow
success, message, workflow = await workflow_service.create_workflow(
    workflow_data, "user@example.com"
)

# Execute workflow
success, message, execution = await workflow_service.execute_workflow(
    workflow.workflow_id,
    {"message": "Hello, World!"},
    "user@example.com"
)
```

## 📚 API Documentation

### Base URL
```
http://localhost:5080
```

### Authentication
All API endpoints support optional authentication via headers:
```
Authorization: Bearer <token>
X-User-ID: <user_id>
```

### Core Endpoints

#### 📝 Workflow Management

##### Create Workflow
```http
POST /workflows
Content-Type: application/json

{
  "name": "Document Analysis Workflow",
  "description": "Analyze documents for quality and insights",
  "parameters": [
    {
      "name": "document_url",
      "type": "string",
      "description": "URL of document to analyze",
      "required": true
    }
  ],
  "actions": [
    {
      "action_id": "analyze",
      "action_type": "service_call",
      "name": "Analyze Document",
      "config": {
        "service": "analysis_service",
        "endpoint": "/analyze",
        "method": "POST",
        "parameters": {
          "url": "{{document_url}}"
        }
      }
    }
  ]
}
```

##### List Workflows
```http
GET /workflows?page=1&page_size=50&status=active&created_by=user@example.com
```

##### Get Workflow Details
```http
GET /workflows/{workflow_id}
```

##### Update Workflow
```http
PUT /workflows/{workflow_id}
Content-Type: application/json

{
  "description": "Updated description",
  "tags": ["updated", "v2"]
}
```

##### Delete Workflow
```http
DELETE /workflows/{workflow_id}
```

#### 🚀 Workflow Execution

##### Execute Workflow
```http
POST /workflows/{workflow_id}/execute
Content-Type: application/json

{
  "parameters": {
    "document_url": "https://example.com/doc.pdf",
    "analysis_type": "comprehensive"
  }
}
```

##### Get Execution Status
```http
GET /workflows/executions/{execution_id}
```

##### List Workflow Executions
```http
GET /workflows/{workflow_id}/executions?limit=100
```

##### Cancel Execution
```http
POST /workflows/executions/{execution_id}/cancel
```

#### 🎯 Advanced Features

##### Create from Template
```http
POST /workflows/from-template
Content-Type: application/json

{
  "template_name": "document_analysis",
  "customizations": {
    "name": "Custom Document Analysis",
    "description": "Customized workflow"
  }
}
```

##### Search Workflows
```http
GET /workflows/search?q=document&limit=50
```

##### Get Statistics
```http
GET /workflows/statistics
```

##### Health Check
```http
GET /workflows/health
```

### Legacy API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET | /health/system | System health |
| GET | /workflows | List workflows |
| GET | /info | Service info |
| GET | /config/effective | Effective config |
| GET | /metrics | Metrics |
| GET | /ready | Readiness |
| POST | /ingest | Request ingestion |
| POST | /workflows/run | Trigger ingestion workflow |
| POST | /demo/e2e | Demo bundle |
| POST | /registry/register | Register a service |
| GET | /registry | List services |
| GET | /infrastructure/dlq/stats | DLQ stats |
| POST | /infrastructure/dlq/retry | DLQ retry |
| GET | /infrastructure/saga/stats | Saga stats |
| GET | /infrastructure/saga/{saga_id} | Saga by id |
| GET | /infrastructure/events/history | Event history |
| POST | /infrastructure/events/replay | Replay events |
| GET | /infrastructure/tracing/stats | Tracing stats |
| GET | /infrastructure/tracing/trace/{trace_id} | Trace by id |
| GET | /infrastructure/tracing/service/{service_name} | Traces for service |
| POST | /infrastructure/events/clear | Clear events |
| GET | /peers | Orchestrator peers |
| POST | /registry/poll-openapi | Poll OpenAPI |
| GET | /workflows/history | Workflow history |
| POST | /jobs/recalc-quality | Recalc quality |
| POST | /jobs/notify-consolidation | Notify consolidation |
| POST | /docstore/save | Save to doc store |

## 🧪 Testing

### Test Structure
```
tests/orchestrator/
├── test_orchestrator_features.py     # Unit tests for core features
├── test_integration_scenarios.py     # Integration and scenario tests
├── test_api_endpoints.py            # API endpoint tests
├── conftest.py                       # Test fixtures and configuration
└── test_runner.py                    # Automated test runner
```

### Running Tests

#### Run All Tests
```bash
cd /path/to/orchestrator
PYTHONPATH=/path/to/services python -m pytest tests/orchestrator/ -v
```

#### Run Specific Test Categories
```bash
# Unit tests
PYTHONPATH=/path/to/services python -m pytest tests/orchestrator/test_orchestrator_features.py -v

# Integration tests
PYTHONPATH=/path/to/services python -m pytest tests/orchestrator/test_integration_scenarios.py -v

# API tests
PYTHONPATH=/path/to/services python -m pytest tests/orchestrator/test_api_endpoints.py -v
```

#### Run with Coverage
```bash
PYTHONPATH=/path/to/services python -m pytest tests/orchestrator/ --cov=orchestrator --cov-report=html
```

### Test Fixtures

#### Available Fixtures
- `workflow_service` - Workflow management service instance
- `event_stream` - Event streaming processor
- `service_mesh` - Service mesh integration
- `sample_workflow_data` - Pre-configured workflow data
- `complex_workflow_data` - Advanced workflow scenarios
- `performance_monitor` - Test performance tracking

## 🎯 Workflow Examples

### 1. Document Analysis Workflow
```python
workflow_data = {
    "name": "Document Quality Analysis",
    "description": "Analyze document for quality and insights",
    "parameters": [
        {
            "name": "document_url",
            "type": "string",
            "description": "Document URL to analyze",
            "required": True
        }
    ],
    "actions": [
        {
            "action_id": "fetch_doc",
            "action_type": "service_call",
            "name": "Fetch Document",
            "config": {
                "service": "source_agent",
                "endpoint": "/fetch",
                "method": "POST",
                "parameters": {"url": "{{document_url}}"}
            }
        },
        {
            "action_id": "analyze_quality",
            "action_type": "service_call",
            "name": "Analyze Quality",
            "config": {
                "service": "analysis_service",
                "endpoint": "/analyze",
                "method": "POST",
                "parameters": {"content": "{{fetch_doc.response.content}}"}
            },
            "depends_on": ["fetch_doc"]
        }
    ]
}
```

### 2. PR Confidence Analysis
```python
workflow_data = {
    "name": "PR Confidence Analysis",
    "description": "Analyze PR confidence against requirements",
    "parameters": [
        {
            "name": "pr_number",
            "type": "integer",
            "required": True
        },
        {
            "name": "repository",
            "type": "string",
            "required": True
        }
    ],
    "actions": [
        {
            "action_id": "fetch_pr",
            "action_type": "service_call",
            "name": "Fetch PR Data",
            "config": {
                "service": "source_agent",
                "endpoint": "/github/pr",
                "method": "GET",
                "parameters": {
                    "pr_number": "{{pr_number}}",
                    "repository": "{{repository}}"
                }
            }
        },
        {
            "action_id": "analyze_confidence",
            "action_type": "service_call",
            "name": "Analyze Confidence",
            "config": {
                "service": "analysis_service",
                "endpoint": "/calculate_confidence",
                "method": "POST",
                "parameters": {"pr_data": "{{fetch_pr.response}}"}
            },
            "depends_on": ["fetch_pr"]
        }
    ]
}
```

## 🔧 Configuration

### Environment Variables
```bash
# Database
ORCHESTRATOR_DB_PATH=../../data/orchestrator_workflows.db

# Service Discovery
ORCHESTRATOR_SERVICE_HOST=localhost
ORCHESTRATOR_SERVICE_PORT=5080

# Enterprise Features
ORCHESTRATOR_ENABLE_TLS=true
ORCHESTRATOR_TLS_CERT_PATH=./certs/server.crt
ORCHESTRATOR_TLS_KEY_PATH=./certs/server.key

# Monitoring
ORCHESTRATOR_METRICS_ENABLED=true
ORCHESTRATOR_HEALTH_CHECK_INTERVAL=30

# Security
ORCHESTRATOR_JWT_SECRET=your-secret-key
ORCHESTRATOR_API_KEY=your-api-key

# Legacy Environment Variables
REDIS_HOST=redis
REPORTING_URL=http://reporting:5030
ORCHESTRATOR_PEERS=
DOC_STORE_URL=
NOTIFICATION_URL=http://notification-service:5095
```

### Configuration File
```yaml
# config/orchestrator.yaml
database:
  path: ../../data/orchestrator_workflows.db
  connection_pool_size: 10
  timeout_seconds: 30

services:
  host: localhost
  port: 5080
  workers: 4

security:
  enable_tls: true
  tls_cert_path: ./certs/server.crt
  tls_key_path: ./certs/server.key
  jwt_secret: your-secret-key

monitoring:
  enabled: true
  metrics_interval: 60
  health_check_interval: 30
  log_level: INFO

enterprise:
  service_mesh_enabled: true
  event_streaming_enabled: true
  circuit_breaker_enabled: true
  rate_limiting_enabled: true
```

## 🤝 Contributing

### Development Setup
```bash
# Clone repository
git clone <repository-url>
cd services/orchestrator

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r ../../../requirements.txt

# Install development dependencies
pip install pytest pytest-asyncio pytest-cov black isort mypy

# Set PYTHONPATH
export PYTHONPATH=/path/to/services:$PYTHONPATH
```

### Code Standards
- **Black** for code formatting
- **isort** for import sorting
- **mypy** for type checking
- **pytest** for testing

### Running Code Quality Checks
```bash
# Format code
black .

# Sort imports
isort .

# Type checking
mypy .

# Run tests
PYTHONPATH=/path/to/services python -m pytest tests/orchestrator/ -v

# Run with coverage
PYTHONPATH=/path/to/services python -m pytest tests/orchestrator/ --cov=orchestrator --cov-report=html
```

### Pull Request Process
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Update documentation
7. Submit pull request

### Commit Message Format
```
feat: add new workflow template system
fix: resolve parameter validation bug
docs: update API documentation
test: add integration tests for service mesh
refactor: improve error handling in workflow execution
```

## 📊 Features

### Core Functionality
- **Service registry** with peer replication and `/peers` listing
- **Workflow endpoints** and scheduled jobs (`/jobs/*`)
- **Event emission** with Redis events and trace IDs when configured
- **Health monitoring** with `/info`, `/config/effective`, `/metrics`, health/ready endpoints
- **Infrastructure management** with DLQ, saga, tracing, and event handling

### Enterprise Features
- **Workflow Management** - Complete CRUD operations for parameterized workflows
- **Multi-Service Orchestration** - Coordinate complex workflows across ecosystem services
- **Event-Driven Processing** - Real-time event handling and correlation
- **Service Mesh Integration** - Secure inter-service communication with mutual TLS
- **Enterprise Monitoring** - Comprehensive health checks and performance metrics
- **Template System** - Pre-built workflow templates for common use cases

---

## 🎉 Getting Started

1. **Set up the environment**:
   ```bash
   export PYTHONPATH=/path/to/services:$PYTHONPATH
   ```

2. **Start the orchestrator service**:
   ```bash
   python main.py
   ```

3. **Create your first workflow**:
   ```bash
   curl -X POST http://localhost:5080/workflows \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Hello World",
       "description": "My first workflow",
       "parameters": [{"name": "message", "type": "string", "required": true}],
       "actions": [{
         "action_id": "greet",
         "action_type": "notification",
         "name": "Send Greeting",
         "config": {"message": "{{message}}"}
       }]
     }'
   ```

4. **Execute the workflow**:
   ```bash
   curl -X POST http://localhost:5080/workflows/{workflow_id}/execute \
     -H "Content-Type: application/json" \
     -d '{"parameters": {"message": "Hello, Orchestrator!"}}'
   ```

5. **Monitor execution**:
   ```bash
   curl http://localhost:5080/workflows/executions/{execution_id}
   ```

Welcome to the Orchestrator service! 🚀

## Goal
- Coordinate ingestion workflows across agents (GitHub, Jira, Confluence, Swagger) and trigger analyses in the Consistency Engine.
- Act as the control plane API for scheduling, on-demand runs, and status.

## Overview and role in the ecosystem
- Acts as the central control plane: service registry, workflow runner, and operational endpoints.
- Provides eventing, DLQ management, tracing, and peer replication to keep the mesh healthy.
- Exposes job endpoints to kick off cross-service operations (quality recalculation, consolidation notifications).

> See also: [Glossary](../../docs/Glossary.md) · [Features & Interactions](../../docs/FEATURES_AND_INTERACTIONS.md)

## Endpoints (initial)
- `GET /health`: Liveness.
- `GET /ready`: Readiness.
- `POST /ingest`: Request ingestion `{source, scope, correlation_id}` (adds `trace_id`).
- `POST /workflows/run`: Trigger multi-source ingestion.
- `POST /registry/register`: Register a service.
- `GET /registry`: List registered services.
- `POST /registry/sync-peers`: Replicate registry to peer orchestrators.
- `POST /registry/poll-openapi`: Poll OpenAPI and compute drift.
- `POST /report/request`: Proxy to reporting service (`generate`, `life_of_ticket`, `pr_confidence`).
- `POST /summarization/suggest`: Policy-aware summarization via `secure-analyzer`.
- `POST /demo/e2e`: Returns a bundle `{ summary, log_analysis }` using reporting endpoints.

## Configuration
Configuration is config-first via `services/shared/config.get_config_value` with precedence: env > `config/app.yaml` > defaults.

- `PORT`: Service port (default 5099).
- `REPORTING_URL`: Base URL for reporting (default `http://reporting:5030`).
- `REDIS_HOST`: Redis hostname for events (optional).
- `ORCHESTRATOR_PEERS`: Comma-separated peer base URLs (also supported under `orchestrator.ORCHESTRATOR_PEERS` in `config/app.yaml`).
- `LOG_COLLECTOR_URL`: If set, emits structured logs to log-collector.

See also: `config/app.yaml` sections `services`, `redis`, `orchestrator`.

## Secrets
- Use `services/shared/credentials.get_secret(name)` to read secrets (env/secret backends).
- Pass secrets via env or Docker/K8s secrets; do not commit to git.

## Run locally

```bash
# Dev stack with live code
docker compose -f docker-compose.dev.yml up -d orchestrator redis

curl http://localhost:5099/health
```

## Shared utilities
- Request/metrics middleware: `services/shared/request_id.py`, `services/shared/metrics.py`.
- Config and constants: `services/shared/config.py`, `services/shared/constants.py`.
- JSON HTTP helpers (timeouts/retries/circuit): `services/shared/clients.py`.

## Demo: /demo/e2e
Example:
```bash
curl -s -X POST "$ORCHESTRATOR_URL/demo/e2e" -H 'content-type: application/json' -d '{"format":"json","log_limit":50}' | jq .
```
Response shape:
```json
{
  "summary": {"total": 3, "by_severity": {"low":2, "med":1}},
  "log_analysis": {"overview": {"count": 12, "by_level": {"info":9, "warn":2, "error":1}}, "sample": [ {"service":"orchestrator", "level":"info", "message":"workflow run requested"} ]}
}
```

## Roadmap
- Track workflow status and surface metrics.
- AuthN/Z for operator endpoints.
- End-to-end job that collects logs and returns a Log Analysis report.

## Related
- Doc Store: [../doc_store/README.md](../doc_store/README.md)
- Source Agent: [../source-agent/README.md](../source-agent/README.md)
- Analysis Service: [../analysis-service/README.md](../analysis-service/README.md)

## Testing
- Unit tests: [tests/unit/orchestrator](../../tests/unit/orchestrator)
- Strategies:
  - Registry endpoints (`/registry/*`) with envelope-aware assertions
  - Health/ready checks and config endpoints
  - Workflows/jobs stubs with flexible response validation
