---
llm_metadata:
  document_type: architecture
  content_focus: technical
  platform:
    primary: mcp
    secondary: []
  status: archived
  created_date: '2024-09-01'
  archived_date: '2025-10-07'
  topics:
  - domain_driven_design
  - bounded_contexts
  - fastapi
  - llm_orchestration
  - rag
  concepts: []
  technologies: []
  services_mentioned: []
  semantic_summary: Architecture document about technical aspects of the mcp platform
  archive_reason: consolidated
  historical_value: medium
  reference_value: medium
semantic_embedding:
  model: text-embedding-ada-002
  embedding_date: '2025-10-07'
  embedding_checksum: pending
rag_metadata:
  chunk_strategy: semantic
  optimal_chunk_size: 512
  retrieval_priority: medium
---

# Architecture Overview

## System map
```
[CLI] ──► [Interpreter] ──► [Orchestrator] ──► [Source Agent] ──► [Doc Store]
                      │                  └──► [Analysis Service]
                      │                         └──► [Notification Service]
                      └──► [Prompt Store]

[Secure Analyzer] ─► [Summarizer Hub]
[GitHub MCP] ───────────────────────► [Code Analyzer] ─► [Doc Store]

All services ─► [Log Collector]
```

## Orchestrator Service - Domain Driven Design (DDD)

The orchestrator service has been completely refactored to follow **Domain-Driven Design** principles with **7 bounded contexts**:

```
Orchestrator Service (DDD Architecture)
├── 🎯 Workflow Management
│   ├── Domain Layer: Entities, Value Objects, Domain Services
│   ├── Application Layer: Use Cases, Commands, Queries
│   ├── Infrastructure Layer: Repositories, External Services
│   └── Presentation Layer: FastAPI Routes, DTOs
├── 🔍 Service Registry
│   ├── Service discovery and registration
│   ├── Service health tracking
│   └── Dynamic service management
├── 🏥 Health Monitoring
│   ├── System health checks
│   ├── Service monitoring
│   ├── Metrics collection
│   └── Readiness/liveness probes
├── ⚙️ Infrastructure
│   ├── Distributed sagas
│   ├── Event streaming
│   ├── Dead Letter Queue (DLQ)
│   └── Distributed tracing
├── 📥 Ingestion
│   ├── Multi-source data ingestion
│   ├── Ingestion workflows
│   └── Data pipeline management
├── ❓ Query Processing
│   ├── Natural language query interpretation
│   ├── Query execution
│   └── Result processing
└── 📊 Reporting
    ├── Analytics report generation
    ├── Performance metrics
    └── Custom reporting workflows
```

## Common patterns
- FastAPI + shared middleware (request id, metrics)
- Standard health endpoints and success/error envelopes
- Service discovery via Orchestrator registry (selected services self-register)
- **CLI Service**: Mixin-based architecture with 18+ standardized managers (100% test coverage)
- Tests organized per-service under `tests/unit/<service>`

## Envelopes
- Success envelope: `{ "success": true, "data": {...}, "message": "...", "request_id": "..." }`
- Error envelope: `{ "success": false, "error_code": "...", "details": {...}, "request_id": "..." }`

## Key responsibilities

### Core Services
- **CLI Service**: Interactive TUI with 18+ specialized managers for service operations
- Interpreter: intent recognition and workflow creation
- Prompt Store: prompt CRUD, A/B testing, analytics
- Analysis Service: consistency checks, reports
- Doc Store: content, analyses, search, quality
- Source Agent: ingest and normalization from GitHub/Jira/Confluence
- Secure Analyzer + Summarizer Hub: policy-aware summarization
- Code Analyzer: code endpoint detection and examples
- Log Collector: centralized logs and stats

### Orchestrator Service (DDD Architecture)
The orchestrator service now follows DDD with specialized bounded contexts:

- **🎯 Workflow Management**: Workflow orchestration, execution tracking, and lifecycle management
- **🔍 Service Registry**: Dynamic service discovery, registration, and health monitoring
- **🏥 Health Monitoring**: System health checks, metrics collection, and service monitoring
- **⚙️ Infrastructure**: Distributed transactions (sagas), event streaming, DLQ management, and tracing
- **📥 Ingestion**: Multi-source data ingestion pipelines and workflow management
- **❓ Query Processing**: Natural language query interpretation and execution
- **📊 Reporting**: Analytics report generation and performance metrics

## Observability
- **Health Endpoints**:
  - `/health` - Basic health check
  - `/api/v1/health/system` - Comprehensive system health (Orchestrator)
  - `/api/v1/health/services` - Service registry health (Orchestrator)
  - `/ready` - Readiness probes (some services)
- **Metrics/Logging**: middleware + optional external backends
- **API Documentation**: Swagger UI at `/docs` for all services

## Data flow examples
- Analyze query
  1) CLI/Frontend → Interpreter `/interpret`
  2) Interpreter creates workflow → Orchestrator/Analysis/Doc Store as needed
- Prompt retrieval
  - Services/CLI → Prompt Store `/prompts/search/{category}/{name}`

## Configuration
- Centralized helpers in `services/shared` (config, clients, constants)
- Prefer env and YAML-based defaults where available
