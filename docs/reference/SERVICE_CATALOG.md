---
llm_metadata:
  document_type: reference
  content_focus: technical
  platform:
    primary: mcp
    secondary: []
  status: active
  created_date: '2025-10-01'
  last_modified: '2025-10-07'
  topics:
  - fastapi
  - redis
  - docker
  - ollama
  - llm_orchestration
  - rag
  - embeddings
  - 5_tier_system
  - deployment
  - security
  concepts: []
  technologies: []
  services_mentioned: []
  semantic_summary: Reference document about technical aspects of the mcp platform
  archive_reason: n/a
  historical_value: current
  reference_value: high
semantic_embedding:
  model: text-embedding-ada-002
  embedding_date: '2025-10-07'
  embedding_checksum: pending
rag_metadata:
  chunk_strategy: semantic
  optimal_chunk_size: 512
  retrieval_priority: high
---

# 🏢 MCP Ecosystem - Service Catalog

**Last Updated:** October 7, 2025  
**Total Services:** 17  
**Status:** All Production-Ready ✅

---

## 🎯 **Quick Reference**

| Service | Port | Purpose | Status |
|---------|------|---------|--------|
| [mcp-provisioner](#mcp-provisioner) | 5400 | MCP lifecycle management | ✅ Production |
| [mcp-composer](#mcp-composer) | 5100 | Multi-MCP orchestration | ✅ Production |
| [mcp-orchestrator](#mcp-orchestrator) | 5200 | Pattern execution | ✅ Production |
| [mcp-interpreter](#mcp-interpreter) | 5300 | NLU → structured intents | ✅ Production |
| [mcp-gateway](#mcp-gateway) | 5000 | Unified API entry | ✅ Production |
| [mcp-infrastructure](#mcp-infrastructure) | 5500 | Infrastructure mgmt | ✅ Production |
| [mcp-logging](#mcp-logging) | 5700 | Centralized logging | ✅ Production |
| [mcp-store](#mcp-store) | 5800 | Package storage | ✅ Production |
| [mcp-performance-store](#mcp-performance-store) | 5900 | Metrics & analytics | ✅ Production |
| [mcp-registry](#mcp-registry) | 6000 | Package registry | ✅ Production |
| [mcp-retrieval](#mcp-retrieval) | 6100 | Hierarchical retrieval | ✅ Production |
| [mcp-tier-manager](#mcp-tier-manager) | 6200 | 5-Tier system | ✅ Production |
| [mcp-package-manager](#mcp-package-manager) | 6300 | Package portability | ✅ Production |
| [mcp_logs](#mcp_logs) | 6400 | Intelligent observability | ✅ Production |
| [mcp_evergreen_docs](#mcp_evergreen_docs) | 6500 | Self-healing docs | ✅ Production |
| [mcp_local_llm](#mcp_local_llm) | 6600 | Local LLM platform | ✅ Production |
| [mcp-training-coordinator](#mcp-training-coordinator) | 5600 | Training pipelines | ✅ Production |
| [mcp-dashboard](#mcp-dashboard) | 8015 | Web dashboard UI | ✅ Production |

---

## 📚 **Services by Category**

### **🎯 Core Services** (Entry & Orchestration)

#### **mcp-gateway**
**Port:** 5000  
**Purpose:** Unified API entry point for all MCP operations  
**Key Features:**
- Request routing
- Authentication
- Rate limiting
- Request validation

**README:** [services/mcp-gateway/README.md](../../services/mcp-gateway/README.md)

---

#### **mcp-composer**
**Port:** 5100  
**Purpose:** Multi-MCP orchestration with conflict resolution  
**Key Features:**
- Declarative YAML specifications
- 5 conflict resolution strategies
- Routing (sequential, parallel, conditional)
- Redis state persistence

**README:** [services/mcp-composer/README.md](../../services/mcp-composer/README.md)

---

#### **mcp-orchestrator**
**Port:** 5200  
**Purpose:** LLM pattern execution engine  
**Key Features:**
- 34 LLM patterns
- Pattern composition
- Workflow coordination
- Result aggregation

**README:** [services/mcp-orchestrator/README.md](../../services/mcp-orchestrator/README.md)

---

#### **mcp-interpreter**
**Port:** 5300  
**Purpose:** Natural language → structured intents  
**Key Features:**
- Intent classification
- Entity extraction
- Context understanding
- Query normalization

**README:** [services/mcp-interpreter/README.md](../../services/mcp-interpreter/README.md)

---

### **🔧 Management Services**

#### **mcp-provisioner**
**Port:** 5400  
**Purpose:** MCP instance lifecycle management  
**Key Features:**
- Provision MCPs
- Start/stop instances
- Delete MCPs
- Status tracking

**README:** [services/mcp-provisioner/README.md](../../services/mcp-provisioner/README.md)

---

#### **mcp-infrastructure**
**Port:** 5500  
**Purpose:** Infrastructure resource management  
**Key Features:**
- Resource allocation
- Dependency management
- Health monitoring
- Configuration

**README:** [services/mcp-infrastructure/README.md](../../services/mcp-infrastructure/README.md)

---

### **📊 Data Services**

#### **mcp-store**
**Port:** 5800  
**Purpose:** MCP package storage ("Docker for Knowledge Graphs")  
**Key Features:**
- SQLite metadata
- MinIO binary storage
- Package versioning
- Export/import (.mcp files)
- Marketplace (stars, trending)

**README:** [services/mcp-store/README.md](../../services/mcp-store/README.md)  
**Guide:** [MCP Store Guide](../guides/MCP_STORE_GUIDE.md)

---

#### **mcp-performance-store**
**Port:** 5900  
**Purpose:** Performance metrics & analytics  
**Key Features:**
- TimescaleDB integration
- Execution metrics
- Trend analysis
- Anomaly detection
- Degradation alerts

**README:** [services/mcp-performance-store/README.md](../../services/mcp-performance-store/README.md)

---

#### **mcp-registry**
**Port:** 6000  
**Purpose:** Package registry & versioning  
**Key Features:**
- Package metadata
- Version management
- Dependency tracking
- Search & discovery

**README:** [services/mcp-registry/README.md](../../services/mcp-registry/README.md)

---

### **🧠 Advanced Services**

#### **mcp-retrieval**
**Port:** 6100  
**Purpose:** Hierarchical retrieval & context pruning  
**Key Features:**
- 5-tier hierarchy support
- Token budget management
- 4 pruning strategies
- HITL workflows
- Feedback system

**README:** [services/mcp-retrieval/README.md](../../services/mcp-retrieval/README.md)  
**Guides:**
- [Hierarchical Retrieval](../guides/HIERARCHICAL_RETRIEVAL_GUIDE.md)
- [Context Pruning](../guides/CONTEXT_PRUNING_GUIDE.md)
- [HITL Workflows](../guides/HITL_WORKFLOWS_GUIDE.md)

---

#### **mcp-tier-manager**
**Port:** 6200  
**Purpose:** 5-Tier hierarchical system management  
**Key Features:**
- Tier CRUD operations
- Inheritance & cascading
- Progressive refinement (3 strategies)
- Access control
- Tier isolation

**README:** [services/mcp_tier_manager/README.md](../../services/mcp_tier_manager/README.md)  
**Guide:** [5-Tier System Guide](../guides/5_TIER_SYSTEM_GUIDE.md)

---

#### **mcp-package-manager**
**Port:** 6300  
**Purpose:** MCP portability & hot-swapping  
**Key Features:**
- Package export/import
- Hot-swapping (zero downtime)
- Version control & snapshots
- Rollback functionality
- Gradual rollout

**README:** [services/mcp_package_manager/README.md](../../services/mcp_package_manager/README.md)  
**Guide:** [MCP Portability Guide](../guides/MCP_PORTABILITY_GUIDE.md)

---

#### **mcp_logs**
**Port:** 6400  
**Purpose:** Intelligent observability system  
**Key Features:**
- Pattern detection
- Anomaly detection
- Root cause analysis
- Predictive maintenance
- Log enrichment

**README:** [services/mcp_logs/README.md](../../services/mcp_logs/README.md)  
**Guide:** [Logs MCP Guide](../guides/LOGS_MCP_GUIDE.md)

---

#### **mcp_evergreen_docs**
**Port:** 6500  
**Purpose:** Self-healing documentation system  
**Key Features:**
- Bi-directional sync (MCP ↔ Confluence)
- Change detection
- Self-healing (4 rules)
- Health scoring
- Auto-archiving

**README:** [services/mcp_evergreen_docs/README.md](../../services/mcp_evergreen_docs/README.md)  
**Guide:** [Evergreen Docs Guide](../guides/EVERGREEN_DOCS_GUIDE.md)

---

#### **mcp_local_llm**
**Port:** 6600  
**Purpose:** 100% local LLM platform  
**Key Features:**
- Ollama integration
- Local embeddings
- M4 Max optimization
- Semantic search
- Zero API costs

**README:** [services/mcp_local_llm/README.md](../../services/mcp_local_llm/README.md)  
**Guide:** [Local LLM Platform Guide](../guides/LOCAL_LLM_PLATFORM_GUIDE.md)

---

### **🔄 Training & ML**

#### **mcp-training-coordinator**
**Port:** 5600  
**Purpose:** Training pipeline orchestration  
**Key Features:**
- Job scheduling
- Worker management (Celery)
- Priority queue
- Status tracking
- Resource allocation

**README:** [services/mcp-training-coordinator/README.md](../../services/mcp-training-coordinator/README.md)

---

### **🎨 UI Services**

#### **mcp-dashboard**
**Port:** 8015  
**Purpose:** Web dashboard for MCP ecosystem  
**Key Features:**
- Real-time WebSocket updates
- 21 interactive pages
- Tight service integration
- Performance visualizations
- Package management UI

**README:** [services/mcp-dashboard/README.md](../../services/mcp-dashboard/README.md)

---

### **📝 Observability**

#### **mcp-logging**
**Port:** 5700  
**Purpose:** Centralized log collection  
**Key Features:**
- Log aggregation
- Structured logging
- Log forwarding
- Query interface

**README:** [services/mcp-logging/README.md](../../services/mcp-logging/README.md)

---

## 🔗 **Service Dependencies**

### **Core Flow**
```
User Request
    ↓
mcp-gateway (5000)
    ↓
mcp-interpreter (5300) ← Understand intent
    ↓
mcp-composer (5100) ← Orchestrate multiple MCPs
    ↓
mcp-orchestrator (5200) ← Execute patterns
    ↓
mcp-provisioner (5400) ← Manage MCP instances
```

### **Data Flow**
```
mcp-store (5800) ← Package storage
    ↔
mcp-registry (6000) ← Package metadata
    ↔
mcp-package-manager (6300) ← Portability
```

### **Monitoring Flow**
```
All Services
    ↓
mcp-logging (5700) ← Log collection
    ↓
mcp_logs (6400) ← Intelligent analysis
    ↓
mcp-dashboard (8015) ← Visualization
```

**Visual Diagram:** [MCP Visual Architecture](../architecture/MCP_VISUAL_ARCHITECTURE.md)

---

## 📊 **Service Statistics**

```
Total Services:                    17
Core Services:                      7
Data Services:                      3
Advanced Services:                  7
Total LOC:                  100,000+
Average LOC per Service:       5,882
Test Coverage:                   85%+
Production Readiness:            100%
```

---

## 🚀 **Getting Started**

### **Start All Services**
```bash
docker-compose -f docker-compose.dev.yml up -d
```

### **Start Specific Service**
```bash
docker-compose -f docker-compose.dev.yml up -d mcp-provisioner
```

### **Check Service Health**
```bash
curl http://localhost:5400/health
```

### **View Logs**
```bash
docker-compose -f docker-compose.dev.yml logs -f mcp-provisioner
```

**Full Guide:** [Service Startup Guide](../guides/SERVICE_STARTUP_GUIDE.md)

---

## 📚 **Additional Resources**

- [Architecture Overview](../architecture/MCP_ARCHITECTURE_COMPLETE.md)
- [Visual Architecture Diagrams](../architecture/MCP_VISUAL_ARCHITECTURE.md)
- [MCP Lifecycle Flows](../architecture/MCP_LIFECYCLE_FLOWS.md)
- [Getting Started Guide](../guides/GETTING_STARTED.md)
- [Production Deployment](../guides/PRODUCTION_DEPLOYMENT_GUIDE.md)

---

## 🔧 **Service Development**

### **Adding a New Service**
1. Follow [Development Guide](../development/DEVELOPMENT_GUIDE.md)
2. Implement health checks
3. Add to docker-compose.dev.yml
4. Create service README
5. Add integration tests
6. Update this catalog

### **Service Standards**
- ✅ FastAPI for REST APIs
- ✅ Domain-Driven Design
- ✅ Health check endpoint
- ✅ Comprehensive README
- ✅ 85%+ test coverage
- ✅ Type hints throughout
- ✅ Async/await patterns

---

**Maintained by:** MCP Team  
**Questions?** Check individual service READMEs or open an issue

