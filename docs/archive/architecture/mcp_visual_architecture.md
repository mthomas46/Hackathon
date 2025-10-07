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
  - service_mesh
  - redis
  - postgresql
  - context_management
  - rag
  - embeddings
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

# MCP Ecosystem - Complete Visual Architecture

**Visual guide to understanding how all 14 MCP services work together**

---

## 🏗️ High-Level Architecture Overview

```
┌────────────────────────────────────────────────────────────────────────────┐
│                           MCP ECOSYSTEM                                     │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                        ENTRY LAYER                                   │  │
│  │                                                                       │  │
│  │                    ┌─────────────────┐                              │  │
│  │                    │   MCP Gateway   │ ◄────── External Clients     │  │
│  │                    │   Port: 8001    │                              │  │
│  │                    └────────┬────────┘                              │  │
│  └─────────────────────────────┼──────────────────────────────────────┘  │
│                                 │                                          │
│  ┌─────────────────────────────┼──────────────────────────────────────┐  │
│  │                        INTELLIGENCE LAYER                            │  │
│  │                                 │                                    │  │
│  │              ┌──────────────────┴──────────────────┐                │  │
│  │              │                                      │                │  │
│  │         ┌────▼─────┐                        ┌──────▼──────┐        │  │
│  │         │Interpreter│                        │ Orchestrator │        │  │
│  │         │Port: 8002 │                        │  Port: 8004  │        │  │
│  │         └────┬──────┘                        └──────┬───────┘        │  │
│  │              │                                      │                │  │
│  └──────────────┼──────────────────────────────────────┼───────────────┘  │
│                 │                                      │                   │
│  ┌──────────────┼──────────────────────────────────────┼───────────────┐  │
│  │         CONTEXT & KNOWLEDGE LAYER                   │               │  │
│  │              │                                      │               │  │
│  │         ┌────▼────────┐    ┌───────────┐    ┌──────▼──────┐       │  │
│  │         │Tier Manager │    │ Retrieval │    │   Store     │       │  │
│  │         │Port: 8013   │◄──►│Port: 8014 │◄──►│ Port: 8008  │       │  │
│  │         └─────────────┘    └───────────┘    └─────────────┘       │  │
│  │                                                                     │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                    LIFECYCLE & DEPLOYMENT LAYER                      │  │
│  │                                                                       │  │
│  │    ┌────────────┐    ┌──────────┐    ┌─────────┐    ┌──────────┐  │  │
│  │    │Provisioner │    │ Composer │    │ Registry│    │  Package │  │  │
│  │    │Port: 8003  │◄──►│Port: 8005│◄──►│Port:8006│◄──►│  Manager │  │  │
│  │    └────────────┘    └──────────┘    └─────────┘    │Port: 8012│  │  │
│  │                                                       └──────────┘  │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                    OBSERVABILITY LAYER                               │  │
│  │                                                                       │  │
│  │    ┌─────────┐    ┌──────────┐    ┌──────────────┐    ┌─────────┐ │  │
│  │    │  Logs   │    │ Logging  │    │ Performance  │    │  Infra  │ │  │
│  │    │  MCP    │◄──►│Port: 8010│◄──►│    Store     │◄──►│Port:8007│ │  │
│  │    │Port:8011│    └──────────┘    │  Port: 8009  │    └─────────┘ │  │
│  │    └─────────┘                    └──────────────┘                  │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 Data Flow: User Query Journey

### Complete Request Flow

```
┌──────────┐
│  User    │ Submits Query: "What are our API best practices?"
└────┬─────┘
     │
     │ 1. HTTP Request
     ▼
┌─────────────────┐
│  MCP Gateway    │ • Authentication
│   (Port 8001)   │ • Rate limiting
└────┬────────────┘ • Request routing
     │
     │ 2. Route to Interpreter
     ▼
┌──────────────────┐
│  MCP Interpreter │ • Parse natural language
│   (Port 8002)    │ • Extract intent
└────┬─────────────┘ • Identify entities
     │
     │ 3. Structured Intent
     ▼
┌──────────────────┐
│  Tier Manager    │ • Identify user tier (Client)
│   (Port 8013)    │ • Get tier hierarchy
└────┬─────────────┘ • Determine scope
     │
     │ 4. Tier Context
     ▼
┌──────────────────┐
│  MCP Retrieval   │ • Hierarchical retrieval
│   (Port 8014)    │   (Client→Project→Team→Company→Ecosystem)
└────┬─────────────┘ • Token budget management
     │                • Context pruning
     │ 5. Query Store
     ▼
┌──────────────────┐
│   MCP Store      │ • Fetch knowledge from each tier
│   (Port 8008)    │ • Apply filters
└────┬─────────────┘ • Return results
     │
     │ 6. Retrieved Context
     ▼
┌──────────────────┐
│ MCP Orchestrator │ • Select pattern (e.g., RAG)
│   (Port 8004)    │ • Execute LLM
└────┬─────────────┘ • Generate response
     │
     │ 7. Log Execution
     ├──────────────────────────┐
     │                          │
     ▼                          ▼
┌──────────────────┐    ┌──────────────────┐
│ Performance Store│    │   MCP Logging    │
│   (Port 8009)    │    │   (Port 8010)    │
└──────────────────┘    └──────────────────┘
     │
     │ 8. Response
     ▼
┌─────────────────┐
│  MCP Gateway    │ • Format response
│   (Port 8001)   │ • Return to user
└────┬────────────┘
     │
     ▼
┌──────────┐
│  User    │ Receives: "Here are our API best practices: ..."
└──────────┘
```

---

## 🔄 Service Interaction Patterns

### Pattern 1: Package Deployment Flow

```
Developer                    Package Manager              MCP Store
    │                             │                          │
    │ 1. Create Package           │                          │
    ├────────────────────────────►│                          │
    │                             │                          │
    │                             │ 2. Store .mcp file       │
    │                             ├─────────────────────────►│
    │                             │                          │
    │                             │◄─────────────────────────┤
    │                             │ 3. Storage confirmed     │
    │                             │                          │
    │                             │                          │
    │                             ▼                          │
    │                        MCP Registry                    │
    │                             │                          │
    │                             │ 4. Register version      │
    │                             │                          │
    │                             ▼                          │
    │                      MCP Orchestrator                  │
    │                             │                          │
    │ 5. Hot-swap (0ms)           │                          │
    ├────────────────────────────►│                          │
    │                             │                          │
    │                             │ 6. Use new package       │
    │                             │                          │
    │                             ▼                          │
    │                        Logs MCP                        │
    │                             │                          │
    │                             │ 7. Monitor deployment    │
    │                             │                          │
    │◄────────────────────────────┤                          │
    │ 8. Success                  │                          │
```

### Pattern 2: MCP Provisioning Flow

```
User Request              MCP Provisioner           Tier Manager
    │                          │                        │
    │ 1. Create MCP            │                        │
    ├─────────────────────────►│                        │
    │                          │                        │
    │                          │ 2. Assign to tier      │
    │                          ├───────────────────────►│
    │                          │                        │
    │                          │◄───────────────────────┤
    │                          │ 3. Tier assigned       │
    │                          │                        │
    │                          ▼                        │
    │                     MCP Store                     │
    │                          │                        │
    │                          │ 4. Initialize storage  │
    │                          │                        │
    │                          ▼                        │
    │                     MCP Registry                  │
    │                          │                        │
    │                          │ 5. Register MCP        │
    │                          │                        │
    │                          ▼                        │
    │                  MCP Infrastructure               │
    │                          │                        │
    │                          │ 6. Health check        │
    │                          │                        │
    │◄─────────────────────────┤                        │
    │ 7. MCP Ready             │                        │
```

### Pattern 3: Intelligent Observability Flow

```
All Services              MCP Logging           Logs MCP            Performance Store
    │                         │                    │                      │
    │ 1. Generate logs        │                    │                      │
    ├────────────────────────►│                    │                      │
    │                         │                    │                      │
    │                         │ 2. Aggregate       │                      │
    │                         │                    │                      │
    │                         │ 3. Send to Logs    │                      │
    │                         ├───────────────────►│                      │
    │                         │                    │                      │
    │                         │                    │ 4. Analyze           │
    │                         │                    │  • Patterns          │
    │                         │                    │  • Anomalies         │
    │                         │                    │  • Root causes       │
    │                         │                    │                      │
    │                         │                    │ 5. Store results     │
    │                         │                    ├─────────────────────►│
    │                         │                    │                      │
    │                         │                    │ 6. Predict failures  │
    │                         │                    │                      │
    │                         │                    ▼                      │
    │                         │           MCP Orchestrator                │
    │                         │                    │                      │
    │                         │                    │ 7. Auto-remediation  │
    │                         │                    │                      │
```

---

## 🎯 Service Dependency Graph

### Core Dependencies

```
                        ┌──────────────┐
                        │  MCP Gateway │
                        │  (Entry)     │
                        └──────┬───────┘
                               │
                ┌──────────────┴──────────────┐
                │                             │
         ┌──────▼─────┐              ┌───────▼────┐
         │Interpreter │              │Orchestrator│
         └──────┬─────┘              └───────┬────┘
                │                             │
                │    ┌────────────────────────┤
                │    │                        │
         ┌──────▼────┴─┐    ┌─────────────┐  │
         │ Tier Manager│◄──►│  Retrieval  │  │
         └──────┬──────┘    └──────┬──────┘  │
                │                  │          │
                └──────────┬───────┴──────────┘
                           │
                    ┌──────▼──────┐
                    │  MCP Store  │
                    │  (Central)  │
                    └──────┬──────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
    ┌────▼────┐      ┌────▼────┐      ┌────▼────┐
    │Registry │      │  Perf   │      │Package  │
    │         │      │  Store  │      │ Manager │
    └─────────┘      └─────────┘      └─────────┘
```

### Observability Dependencies

```
┌─────────────────────────────────────────────────┐
│            All MCP Services                      │
│  (Gateway, Orchestrator, Store, etc.)           │
└─────────────┬───────────────────────────────────┘
              │
              │ Send Logs
              │
      ┌───────▼────────┐
      │  MCP Logging   │
      │  (Collector)   │
      └───────┬────────┘
              │
              │ Forward
              │
      ┌───────▼────────┐
      │   Logs MCP     │
      │  (Analysis)    │
      └───┬────────┬───┘
          │        │
          │        └────────────┐
          │                     │
  ┌───────▼────────┐    ┌──────▼───────┐
  │ Performance    │    │ Infrastructure│
  │    Store       │    │   Monitor     │
  └────────────────┘    └───────────────┘
```

---

## 🔐 Security & Authentication Flow

```
External Client
      │
      │ 1. Request with API Key/JWT
      ▼
┌─────────────┐
│  Gateway    │ ◄──────── Rate Limiter
│  (Auth)     │
└──────┬──────┘
       │ 2. Validate Token
       │
       │ 3. Extract User Context
       │      • User ID
       │      • Roles
       │      • Permissions
       │
       ▼
┌─────────────┐
│Tier Manager │
│ (RBAC)      │ ◄──────── Access Control Policies
└──────┬──────┘
       │ 4. Check Tier Access
       │
       │ 5. Authorized Context
       ▼
┌─────────────┐
│  Retrieval  │
│  (Filtered) │ ◄──────── Data Filtering
└──────┬──────┘
       │ 6. Apply Row-Level Security
       │
       ▼
┌─────────────┐
│    Store    │
│  (Encrypted)│ ◄──────── Encryption at Rest
└─────────────┘
```

---

## 💾 Data Storage Architecture

### Storage Layer Distribution

```
┌────────────────────────────────────────────────────────┐
│                    STORAGE LAYER                        │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │  MCP Store   │  │  Registry    │  │   Package   │ │
│  │              │  │              │  │   Manager   │ │
│  │ PostgreSQL   │  │ PostgreSQL   │  │   SQLite    │ │
│  │              │  │              │  │   + MinIO   │ │
│  │ • Knowledge  │  │ • Packages   │  │             │ │
│  │ • Embeddings │  │ • Versions   │  │ • .mcp files│ │
│  │ • Metadata   │  │ • Metadata   │  │ • Binaries  │ │
│  └──────────────┘  └──────────────┘  └─────────────┘ │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │ Performance  │  │    Tier      │  │   Logging   │ │
│  │    Store     │  │   Manager    │  │             │ │
│  │              │  │              │  │             │ │
│  │ TimescaleDB  │  │ PostgreSQL   │  │ ElasticSearch│
│  │              │  │              │  │             │ │
│  │ • Metrics    │  │ • Hierarchy  │  │ • Logs      │ │
│  │ • Executions │  │ • Policies   │  │ • Events    │ │
│  │ • Analytics  │  │ • Access     │  │ • Traces    │ │
│  └──────────────┘  └──────────────┘  └─────────────┘ │
└────────────────────────────────────────────────────────┘
```

---

## 🚀 Scalability Architecture

### Horizontal Scaling Strategy

```
                    ┌──────────────┐
                    │ Load Balancer│
                    └──────┬───────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
    ┌────▼────┐       ┌────▼────┐      ┌────▼────┐
    │Gateway 1│       │Gateway 2│      │Gateway 3│
    └────┬────┘       └────┬────┘      └────┬────┘
         │                 │                 │
         └─────────────────┼─────────────────┘
                           │
                    ┌──────▼───────┐
                    │ Service Mesh │
                    └──────┬───────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
    ┌────▼────┐       ┌────▼────┐      ┌────▼────┐
    │ Orch 1  │       │ Orch 2  │      │ Orch 3  │
    └────┬────┘       └────┬────┘      └────┬────┘
         │                 │                 │
         └─────────────────┼─────────────────┘
                           │
                    ┌──────▼───────┐
                    │ Cache Layer  │
                    │   (Redis)    │
                    └──────┬───────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
    ┌────▼────┐       ┌────▼────┐      ┌────▼────┐
    │ Store 1 │       │ Store 2 │      │ Store 3 │
    │(Primary)│       │(Replica)│      │(Replica)│
    └─────────┘       └─────────┘      └─────────┘
```

---

## 🔄 Real-Time Updates Flow

### WebSocket Architecture

```
Dashboard UI                  Gateway               Orchestrator
    │                            │                       │
    │ 1. WebSocket Connect       │                       │
    ├───────────────────────────►│                       │
    │                            │                       │
    │ 2. Subscribe to events     │                       │
    ├───────────────────────────►│                       │
    │                            │                       │
    │                            │ 3. Query execution    │
    │                            │◄──────────────────────┤
    │                            │                       │
    │ 4. Real-time update        │                       │
    │◄───────────────────────────┤                       │
    │                            │                       │
    │                            ▼                       │
    │                     Performance Store              │
    │                            │                       │
    │                            │ 5. Metrics update     │
    │                            │                       │
    │ 6. Push metrics            │                       │
    │◄───────────────────────────┤                       │
```

---

## 📊 Monitoring & Health Checks

### Health Check Cascade

```
MCP Infrastructure (8007)
        │
        │ Polls every 30s
        │
        ├──────────────┬──────────────┬──────────────┐
        │              │              │              │
   ┌────▼────┐    ┌────▼────┐   ┌────▼────┐   ┌────▼────┐
   │Gateway  │    │  Orch   │   │  Store  │   │Registry │
   │Health: ✓│    │Health: ✓│   │Health: ✓│   │Health: ✓│
   └────┬────┘    └────┬────┘   └────┬────┘   └────┬────┘
        │              │              │              │
        │              ├──────────────┴──────────────┘
        │              │
        │              │ Check dependencies
        │              │
        │         ┌────▼────┐
        │         │PostgreSQL│
        │         │Health: ✓│
        │         └────┬────┘
        │              │
        │         ┌────▼────┐
        │         │  Redis  │
        │         │Health: ✓│
        │         └─────────┘
        │
   ┌────▼────────────────┐
   │ Dashboard           │
   │ System Status: ✓    │
   │ All Services: 14/14 │
   └─────────────────────┘
```

---

## 🎯 Complete Service Port Map

```
┌─────────────────────────────────────────┐
│         MCP Service Ports               │
├─────────────────────────────────────────┤
│  8001  →  Gateway (Entry Point)        │
│  8002  →  Interpreter (NLU)            │
│  8003  →  Provisioner (Lifecycle)      │
│  8004  →  Orchestrator (Execution)     │
│  8005  →  Composer (Multi-MCP)         │
│  8006  →  Registry (Catalog)           │
│  8007  →  Infrastructure (Health)      │
│  8008  →  Store (Knowledge)            │
│  8009  →  Performance Store (Metrics)  │
│  8010  →  Logging (Collection)         │
│  8011  →  Logs MCP (Intelligence)      │
│  8012  →  Package Manager (Deploy)     │
│  8013  →  Tier Manager (Hierarchy)     │
│  8014  →  Retrieval (Context)          │
└─────────────────────────────────────────┘
```

---

## 💡 Quick Reference: Common Operations

### Operation 1: Execute a Query
```
User → Gateway(8001) → Interpreter(8002) → TierManager(8013) →
Retrieval(8014) → Store(8008) → Orchestrator(8004) → Gateway → User
```

### Operation 2: Deploy a Package
```
Dev → PackageManager(8012) → Store(8008) → Registry(8006) →
PackageManager → Orchestrator(8004) → LogsMCP(8011)
```

### Operation 3: Create MCP
```
User → Gateway(8001) → Provisioner(8003) → TierManager(8013) →
Store(8008) → Registry(8006) → Infrastructure(8007) → Gateway → User
```

### Operation 4: Monitor System
```
Services → Logging(8010) → LogsMCP(8011) → PerformanceStore(8009) →
Infrastructure(8007) → Dashboard
```

---

## 🎨 Legend

```
Symbol Guide:
─────────────
  →   Data flow direction
  ◄►  Bidirectional communication
  ▼   Hierarchical relationship
  │   Connection/dependency
  ✓   Healthy/operational
  ✗   Error/unavailable
  ⏳  In progress
  ├   Branch point
  └   End point
```

---

**Version**: 1.0.0  
**Created**: October 7, 2025  
**Maintainer**: MCP Team

*This visual guide provides a comprehensive view of how all MCP services interact and work together to provide intelligent LLM context management.*

