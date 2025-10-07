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
  - microservices
  - event_sourcing
  - api_gateway
  - python
  - docker
  - kubernetes
  - llm_orchestration
  - context_management
  - rag
  - 5_tier_system
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

# MCP Ecosystem Architecture - Complete Service Map

**The Model Context Protocol System - Comprehensive Service Architecture**

## 🏗️ Complete Service Overview

The MCP Ecosystem consists of 14 microservices working together to provide intelligent LLM context management, orchestration, and deployment.

```
┌────────────────────────────────────────────────────────────────┐
│                      MCP ECOSYSTEM                              │
│                                                                 │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐         │
│  │  Gateway    │───│ Interpreter │───│ Orchestrator│         │
│  │  (Entry)    │   │  (NLU)      │   │ (Execution) │         │
│  └─────────────┘   └─────────────┘   └─────────────┘         │
│         │                  │                  │                │
│         ▼                  ▼                  ▼                │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐         │
│  │ Provisioner │   │  Composer   │   │  Registry   │         │
│  │ (Lifecycle) │   │ (Multi-MCP) │   │ (Packages)  │         │
│  └─────────────┘   └─────────────┘   └─────────────┘         │
│         │                  │                  │                │
│         ▼                  ▼                  ▼                │
│  ┌─────────────────────────────────────────────────┐          │
│  │          ADVANCED FEATURES (Phase 8)             │          │
│  ├─────────────┬─────────────┬─────────────────────┤          │
│  │Tier Manager │  Retrieval  │  Package Manager    │          │
│  │  (5-Tier)   │  (Context)  │  (Portability)      │          │
│  └─────────────┴─────────────┴─────────────────────┘          │
│         │                  │                  │                │
│         ▼                  ▼                  ▼                │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐         │
│  │   Logging   │   │  Logs MCP   │   │   Store     │         │
│  │ (Observ.)   │   │ (Intellig.) │   │ (Storage)   │         │
│  └─────────────┘   └─────────────┘   └─────────────┘         │
│         │                  │                  │                │
│         ▼                  ▼                  ▼                │
│  ┌──────────────────────────────────────────────────┐         │
│  │       Performance Store & Infrastructure         │         │
│  │         (Metrics, Monitoring, Health)            │         │
│  └──────────────────────────────────────────────────┘         │
└────────────────────────────────────────────────────────────────┘
```

---

## 📋 Service Catalog

### Core Services (Foundation)

| # | Service | Purpose | Port | Status |
|---|---------|---------|------|--------|
| 1 | **MCP Gateway** | API gateway & routing | 8001 | ✅ Production |
| 2 | **MCP Interpreter** | Natural language parsing | 8002 | ✅ Production |
| 3 | **MCP Orchestrator** | Pattern execution | 8004 | ✅ Production |
| 4 | **MCP Provisioner** | MCP lifecycle management | 8003 | ✅ Production |
| 5 | **MCP Composer** | Multi-MCP orchestration | 8005 | ✅ Production |

### Data & Storage Services

| # | Service | Purpose | Port | Status |
|---|---------|---------|------|--------|
| 6 | **MCP Store** | Knowledge storage | 8008 | ✅ Production |
| 7 | **MCP Registry** | Package catalog | 8006 | ✅ Production |
| 8 | **MCP Performance Store** | Metrics & analytics | 8009 | ✅ Production |

### Advanced Features (Phase 8)

| # | Service | Purpose | Port | Status |
|---|---------|---------|------|--------|
| 9 | **MCP Tier Manager** | 5-tier hierarchy | 8013 | ✅ Production |
| 10 | **MCP Retrieval** | Context management | 8014 | ✅ Production |
| 11 | **MCP Package Manager** | Package deployment | 8012 | ✅ Production |
| 12 | **MCP Logs** | Intelligent observability | 8011 | ⏳ In Progress |

### Infrastructure Services

| # | Service | Purpose | Port | Status |
|---|---------|---------|------|--------|
| 13 | **MCP Infrastructure** | Health & monitoring | 8007 | ✅ Production |
| 14 | **MCP Logging** | Log collection | 8010 | ✅ Production |

---

## 🔗 Service Interaction Matrix

### Complete Interaction Map

```
FROM ↓ / TO →  | Gateway | Interp | Orch | Prov | Comp | Reg | Store | Perf | Tier | Retr | Pkg | Logs | Infra | Log
─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
Gateway        |    -    |   ✓    |  ✓   |  ✓   |  ✓   |  ✓  |   ✓   |  ✓   |  ✓   |  ✓   |  ✓  |  ✓   |   ✓   |  ✓
Interpreter    |    ✓    |   -    |  ✓   |  -   |  -   |  -  |   ✓   |  ✓   |  ✓   |  ✓   |  -  |  ✓   |   -   |  ✓
Orchestrator   |    ✓    |   ✓    |  -   |  ✓   |  ✓   |  ✓  |   ✓   |  ✓   |  ✓   |  ✓   |  ✓  |  ✓   |   ✓   |  ✓
Provisioner    |    ✓    |   -    |  ✓   |  -   |  -   |  ✓  |   ✓   |  ✓   |  ✓   |  -   |  -  |  ✓   |   ✓   |  ✓
Composer       |    ✓    |   ✓    |  ✓   |  ✓   |  -   |  ✓  |   ✓   |  ✓   |  ✓   |  ✓   |  -  |  ✓   |   ✓   |  ✓
Registry       |    ✓    |   -    |  ✓   |  ✓   |  ✓   |  -  |   ✓   |  ✓   |  -   |  -   |  ✓  |  ✓   |   ✓   |  ✓
Store          |    ✓    |   ✓    |  ✓   |  ✓   |  ✓   |  ✓  |   -   |  ✓   |  ✓   |  ✓   |  ✓  |  ✓   |   ✓   |  ✓
Perf Store     |    ✓    |   ✓    |  ✓   |  ✓   |  ✓   |  ✓  |   ✓   |  -   |  ✓   |  ✓   |  ✓  |  ✓   |   ✓   |  ✓
Tier Manager   |    ✓    |   -    |  ✓   |  -   |  -   |  -  |   ✓   |  ✓   |  -   |  ✓   |  ✓  |  ✓   |   -   |  ✓
Retrieval      |    ✓    |   -    |  ✓   |  -   |  -   |  -  |   ✓   |  ✓   |  ✓   |  -   |  -  |  ✓   |   -   |  ✓
Package Mgr    |    ✓    |   -    |  ✓   |  -   |  -   |  ✓  |   ✓   |  ✓   |  ✓   |  -   |  -  |  ✓   |   -   |  ✓
Logs MCP       |    ✓    |   -    |  ✓   |  -   |  -   |  -  |   -   |  ✓   |  -   |  -   |  -  |  -   |   ✓   |  ✓
Infrastructure |    ✓    |   ✓    |  ✓   |  ✓   |  ✓   |  ✓  |   ✓   |  ✓   |  ✓   |  ✓   |  ✓  |  ✓   |   -   |  ✓
Logging        |    ✓    |   ✓    |  ✓   |  ✓   |  ✓   |  ✓  |   ✓   |  ✓   |  ✓   |  ✓   |  ✓  |  ✓   |   ✓   |  -
```

---

## 🎯 Service Groups

### 1. Request Processing Pipeline
**Flow**: User → Gateway → Interpreter → Orchestrator → Response

- **Gateway**: Entry point, authentication, routing
- **Interpreter**: Parse natural language to structured intent
- **Orchestrator**: Execute LLM patterns with context

**Key Interactions**:
- Gateway forwards requests to Interpreter
- Interpreter passes intents to Orchestrator
- Orchestrator retrieves context from Retrieval/Store

### 2. Context Management Layer
**Services**: Tier Manager, Retrieval, Store

- **Tier Manager**: 5-tier hierarchy management
- **Retrieval**: Hierarchical context retrieval & pruning
- **Store**: Knowledge persistence

**Key Interactions**:
- Tier Manager provides hierarchy to Retrieval
- Retrieval queries Store for actual content
- Store persists tier metadata

### 3. Deployment & Lifecycle
**Services**: Provisioner, Package Manager, Registry

- **Provisioner**: Create/start/stop/delete MCPs
- **Package Manager**: Package & deploy knowledge
- **Registry**: Catalog packages & versions

**Key Interactions**:
- Provisioner uses Registry for packages
- Package Manager stores in Store
- Registry tracks all packages

### 4. Observability & Intelligence
**Services**: Logs MCP, Logging, Performance Store, Infrastructure

- **Logs MCP**: Intelligent log analysis
- **Logging**: Log collection
- **Performance Store**: Metrics storage
- **Infrastructure**: Health monitoring

**Key Interactions**:
- All services send logs to Logging
- Logs MCP analyzes for patterns
- Performance Store tracks metrics
- Infrastructure monitors health

---

## 📊 Data Flow Patterns

### Pattern 1: User Query Flow
```
User Request
    ↓
Gateway (Authentication, Routing)
    ↓
Interpreter (Parse Intent)
    ↓
Tier Manager (Identify Tier)
    ↓
Retrieval (Get Context)
    ↓
Store (Fetch Knowledge)
    ↓
Orchestrator (Execute Pattern)
    ↓
Performance Store (Record Metrics)
    ↓
Gateway (Return Response)
    ↓
User
```

### Pattern 2: Package Deployment Flow
```
Developer
    ↓
Package Manager (Create Package)
    ↓
Store (Store .mcp file)
    ↓
Registry (Register Version)
    ↓
Package Manager (Hot-Swap)
    ↓
Orchestrator (Use New Package)
    ↓
Logs MCP (Monitor Deployment)
    ↓
Performance Store (Track Metrics)
```

### Pattern 3: MCP Provisioning Flow
```
User Request
    ↓
Gateway
    ↓
Provisioner (Create MCP)
    ↓
Tier Manager (Assign Tier)
    ↓
Store (Initialize Storage)
    ↓
Registry (Register MCP)
    ↓
Infrastructure (Health Check)
    ↓
Response
```

---

## 🔧 Integration Patterns

### Pattern A: Service-to-Service Communication
```python
# HTTP/REST for synchronous operations
response = await http_client.post(
    f"{service_url}/api/v1/endpoint",
    json=payload,
    headers={"Authorization": f"Bearer {token}"}
)

# Event-driven for async operations
await event_bus.publish(
    topic="mcp.package.deployed",
    data={"package_id": "pkg_123", "version": "2.0.0"}
)
```

### Pattern B: Data Synchronization
```python
# Cross-service data consistency
async with transaction_manager:
    # Update Store
    await store.update(data)
    # Update Registry
    await registry.sync(metadata)
    # Update Performance Store
    await perf_store.record(metrics)
```

### Pattern C: Circuit Breaker
```python
# Resilient service calls
from common.http_client import ServiceHTTPClient

client = ServiceHTTPClient(
    base_url=service_url,
    circuit_breaker_threshold=5,
    retry_attempts=3
)

result = await client.get("/api/endpoint")
```

---

## 📈 Scalability Architecture

### Horizontal Scaling Strategy

```
Load Balancer
    ├── Gateway Instance 1
    ├── Gateway Instance 2
    └── Gateway Instance 3
            ↓
    ├── Orchestrator Instance 1
    ├── Orchestrator Instance 2
    └── Orchestrator Instance 3
            ↓
Shared Storage Layer
    ├── Store (Replicated)
    ├── Registry (Replicated)
    └── Performance Store (Sharded)
```

### Service Tiers

1. **Stateless Services** (Easy to scale)
   - Gateway, Interpreter, Orchestrator
   - Composer, Provisioner

2. **Stateful Services** (Require coordination)
   - Store, Registry, Performance Store
   - Use database replication/sharding

3. **Singleton Services** (Single instance)
   - Infrastructure (can be HA pair)
   - Logging Aggregator

---

## 🔐 Security Architecture

### Authentication Flow
```
Client → Gateway (JWT Validation)
    ↓
Service-to-Service (mTLS + Service Tokens)
    ↓
Data Access (RBAC + Tier Isolation)
```

### Authorization Layers
1. **Gateway Level**: API key/JWT validation
2. **Service Level**: Service-to-service auth
3. **Data Level**: Tier-based access control
4. **Operation Level**: Role-based permissions

---

## 🚀 Deployment Architecture

### Docker Compose (Development)
```yaml
services:
  gateway:
    image: mcp-gateway:latest
    ports: ["8001:8001"]
    depends_on: [interpreter, orchestrator]
  
  orchestrator:
    image: mcp-orchestrator:latest
    ports: ["8004:8004"]
    depends_on: [store, registry]
  
  # ... all 14 services
```

### Kubernetes (Production)
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-orchestrator
spec:
  replicas: 3
  selector:
    matchLabels:
      app: mcp-orchestrator
  template:
    metadata:
      labels:
        app: mcp-orchestrator
    spec:
      containers:
      - name: orchestrator
        image: mcp-orchestrator:v1.0.0
        ports:
        - containerPort: 8004
```

---

## 📚 Documentation Index

### Service READMEs
- [MCP Gateway](./services/mcp-gateway/README.md)
- [MCP Interpreter](./services/mcp-interpreter/README.md)
- [MCP Orchestrator](./services/mcp-orchestrator/README.md)
- [MCP Provisioner](./services/mcp-provisioner/README.md)
- [MCP Composer](./services/mcp-composer/README.md)
- [MCP Registry](./services/mcp-registry/README.md)
- [MCP Store](./services/mcp-store/README.md)
- [MCP Performance Store](./services/mcp-performance-store/README.md)
- [MCP Tier Manager](./services/mcp_tier_manager/README.md)
- [MCP Retrieval](./services/mcp_retrieval/README.md)
- [MCP Package Manager](./services/mcp_package_manager/README.md)
- [MCP Logs](./services/mcp_logs/README.md)
- [MCP Infrastructure](./services/mcp-infrastructure/README.md)
- [MCP Logging](./services/mcp-logging/README.md)

### Feature Guides
- [5-Tier System Guide](./docs/5_TIER_SYSTEM_GUIDE.md)
- [MCP Portability Guide](./docs/MCP_PORTABILITY_GUIDE.md)
- [Hierarchical Retrieval Guide](./docs/HIERARCHICAL_RETRIEVAL_GUIDE.md)
- [Context Pruning Guide](./docs/CONTEXT_PRUNING_GUIDE.md)
- [HITL Workflows Guide](./docs/HITL_WORKFLOWS_GUIDE.md)
- [Service Integration Guide](./docs/SERVICE_INTEGRATION_GUIDE.md)

---

## 🎯 Quick Reference

### Service Ports
```
8001: Gateway
8002: Interpreter
8003: Provisioner
8004: Orchestrator
8005: Composer
8006: Registry
8007: Infrastructure
8008: Store
8009: Performance Store
8010: Logging
8011: Logs MCP
8012: Package Manager
8013: Tier Manager
8014: Retrieval
```

### Health Check Endpoints
```bash
curl http://localhost:8001/health  # Gateway
curl http://localhost:8004/health  # Orchestrator
# ... etc for all services
```

### Common Operations
```bash
# Start all services
docker-compose up -d

# Check service status
curl http://localhost:8007/health/all

# View logs
docker-compose logs -f orchestrator

# Scale service
docker-compose up -d --scale orchestrator=3
```

---

**Version**: 1.0.0  
**Last Updated**: October 7, 2025  
**Maintainer**: MCP Team

*This is a living document. See individual service READMEs for detailed information.*

