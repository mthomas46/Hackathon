---
llm_metadata:
  document_type: planning
  content_focus: technical
  platform:
    primary: mcp
    secondary: []
  status: active
  created_date: '2025-10-01'
  last_modified: '2025-10-07'
  topics:
  - domain_driven_design
  - bounded_contexts
  - fastapi
  - python
  - redis
  - postgresql
  - docker
  - ollama
  - llm_orchestration
  - rag
  concepts: []
  technologies: []
  services_mentioned: []
  semantic_summary: Planning document about technical aspects of the mcp platform
  archive_reason: n/a
  historical_value: current
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

# MCP System Architecture Plan

## Executive Summary

This document outlines the comprehensive architecture for a **Production MCP System** that enables the ecosystem to create, train, deploy, and orchestrate Model Context Protocol (MCP) servers as dynamic knowledge hubs. The system **integrates seamlessly with the existing `doc-ecosystem-dev` infrastructure** and follows established patterns from services like `analysis-service`, `orchestrator`, and `project-simulation`.

### Core Vision

Transform MCPs from static knowledge repositories into **dynamic, orchestrated intelligence layers** that can be:
- Automatically trained from ecosystem data sources
- Dynamically provisioned based on workload demands
- Composed and layered for multi-tier context resolution
- Exported, versioned, and shared across teams/clients
- Integrated into sophisticated LLM-powered workflows

### Ecosystem Integration Principles

- ✅ **DDD Architecture**: All services follow Domain-Driven Design with bounded contexts
- ✅ **Shared Infrastructure**: Leverage existing services (`llm-gateway`, `mock-data-generator`, `source-agent`, `redis`)
- ✅ **Docker Network**: All services on `doc-ecosystem-dev` (hackathon_default) network
- ✅ **REST Standards**: OpenAPI/Swagger annotations, standardized response formats
- ✅ **Test-Driven**: >90% test coverage using `mock-data-generator` for integration tests
- ✅ **DRY & KISS**: Reuse `services/shared/` libraries, keep logic simple and focused

---

## Ecosystem Integration Overview

### Leveraged Existing Services

The MCP System integrates with and extends the following existing ecosystem services:

| Service | Role in MCP System | Integration Point |
|---------|-------------------|-------------------|
| **llm-gateway** (5055) | Primary LLM interface for all MCP AI operations | Replace direct Ollama calls with gateway |
| **source-agent** (5085) | Extract training data from GitHub, Confluence, Jira | Training pipeline data source |
| **mock-data-generator** (5065) | Generate test data for MCP training and validation | Integration testing |
| **redis** (6379) | Caching, state management, message broker | All MCP services |
| **ollama** (11434) | Local LLM via llm-gateway | Indirect via gateway |
| **doc_store** (5087) | Store MCP metadata and training artifacts | MCP Registry backend |
| **orchestrator** (5099) | Workflow patterns for MCP orchestration | Reference implementation |

### Network Architecture

**All MCP services run on the existing `doc-ecosystem-dev` network:**
- Network Name: `doc-ecosystem-dev` (Docker internal: `hackathon_default`)
- Subnet: `172.20.0.0/16`
- Bridge: `hackathon_bridge`
- MTU: 1500

**Port Allocation Strategy:**
- MCP Interpreter: `5100` (matches ecosystem port range)
- MCP Orchestrator: `5200`
- MCP Gateway: `5300`
- MCP Provisioner: `5400` ✅ **IMPLEMENTED**
- MCP Infrastructure: `5500` 🆕 **NEW SERVICE**
- MCP Registry: `5550`
- MCP Composer: `5600`
- MCP Training Coordinator: `5700`

---

## System Overview

### High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                    EXISTING ECOSYSTEM SERVICES                        │
│  ┌───────────┐  ┌───────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ LLM       │  │ Source    │  │ Mock Data    │  │ Doc Store    │  │
│  │ Gateway   │  │ Agent     │  │ Generator    │  │              │  │
│  │ :5055     │  │ :5085     │  │ :5065        │  │ :5087        │  │
│  └───────────┘  └───────────┘  └──────────────┘  └──────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
                            ▲  ▲  ▲  ▲
                            │  │  │  │ (Integrates with existing services)
┌──────────────────────────────────────────────────────────────────────┐
│                      NEW MCP SERVICES                                 │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────┐     │
│  │ MCP Dashboard UI │  │ Project Planning │  │ Cursor/IDEs   │     │
│  │  (Port 8080)     │  │    Service UI    │  │  (MCP Client) │     │
│  └──────────────────┘  └──────────────────┘  └───────────────┘     │
└──────────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Orchestration Layer                           │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────┐ │
│  │ MCP Interpreter  │→│ MCP Orchestrator │→│ MCP Gateway   │ │
│  │  (Port 5100)     │  │   (Port 5200)    │  │ (Port 5300)   │ │
│  └──────────────────┘  └──────────────────┘  └───────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   MCP Lifecycle Management                       │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────┐ │
│  │ MCP Provisioner  │  │  MCP Registry    │  │ MCP Composer  │ │
│  │  (Port 5400)     │  │   (Port 5500)    │  │ (Port 5600)   │ │
│  └──────────────────┘  └──────────────────┘  └───────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Training Pipeline                           │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              MCP Training Coordinator                     │   │
│  │                    (Port 5700)                            │   │
│  │  ┌────────────┐  ┌─────────────┐  ┌──────────────────┐  │   │
│  │  │ Extraction │  │ Normalization│  │ Embedding &      │  │   │
│  │  │  Workers   │→│   Workers    │→│ Tagging Workers  │  │   │
│  │  └────────────┘  └─────────────┘  └──────────────────┘  │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Active MCP Instances                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Client MCP-A │  │ Project MCP-B│  │ Ecosystem MCP│  ...     │
│  │ (Dynamic)    │  │ (Dynamic)    │  │ (Persistent) │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│         Each has: ChromaDB + Neo4j + MCP Server + Agent         │
└─────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Shared Data & Infrastructure                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Source Agent │  │ Data Stores  │  │ Event Bus    │          │
│  │ Log Collector│  │ Observability│  │ LLM Services │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Core Services

### 1. MCP Interpreter Service (Port 5100)

**Purpose:** Translates natural language queries into structured MCP requests with intent classification and query optimization.

**Key Responsibilities:**
- Parse and understand user queries (natural language)
- Classify query intent (retrieval, analysis, generation, planning)
- Extract entities, topics, and context requirements
- Determine required MCP tiers and scopes
- Generate optimized query plan

**Technology Stack:**
- FastAPI framework
- Ollama (local LLM for intent classification)
- ChromaDB (query pattern matching)
- spaCy/NLTK (NLP preprocessing)

**Example Workflow:**
```
User Query: "What are the coding patterns used by Team Alpha in the last sprint?"

Interpreter Output:
{
  "intent": "retrieval_analysis",
  "entities": {
    "team": "Team Alpha",
    "time_scope": "last_sprint",
    "focus": "coding_patterns"
  },
  "required_mcps": ["team-mcp", "project-mcp"],
  "context_priority": ["team", "project", "company"],
  "query_plan": {
    "phase_1": "retrieve_team_commits",
    "phase_2": "extract_code_patterns",
    "phase_3": "compare_with_team_baseline"
  }
}
```

---

### 2. MCP Orchestrator Service (Port 5200)

**Purpose:** Converts interpreted queries into executable workflows, manages MCP provisioning, and coordinates multi-MCP operations.

**Key Responsibilities:**
- Receive structured query plans from Interpreter
- Determine which MCPs are needed (by tier, client, project, team)
- Check MCP availability and health status
- Trigger MCP provisioning if needed (via Provisioner)
- Coordinate parallel or sequential MCP queries
- Aggregate and synthesize responses across MCPs
- Apply LLM architecture patterns (ensemble, self-critique, etc.)
- Manage workflow state and error recovery

**Technology Stack:**
- FastAPI framework
- Temporal/Celery (workflow orchestration)
- Redis (state management, caching)
- Docker SDK (for resource monitoring)
- Ollama (for response synthesis and LLM patterns)

**Workflow Engine Features:**
- **Parallel Execution:** Query multiple MCPs simultaneously when independent
- **Sequential Execution:** Chain MCP queries when context depends on previous results
- **Ensemble Orchestration:** Run multiple strategies and synthesize results
- **Self-Consistency:** Generate multiple reasoning paths and vote on answers
- **Dynamic Context Pruning:** Intelligently limit context to stay within token budgets

**Example Orchestration:**
```python
# Workflow for: "Generate a project plan for Client X based on similar past projects"

workflow = {
  "steps": [
    {
      "step_id": "1",
      "action": "provision_mcp",
      "target": "client-x-mcp",
      "wait_for_hot": True,
      "timeout": 60
    },
    {
      "step_id": "2", 
      "action": "parallel_query",
      "targets": ["client-x-mcp", "project-mcp", "company-mcp"],
      "queries": {
        "client-x-mcp": "What are Client X's specific requirements and constraints?",
        "project-mcp": "What projects similar to {project_type} succeeded?",
        "company-mcp": "What are our standard project planning templates?"
      }
    },
    {
      "step_id": "3",
      "action": "llm_synthesis",
      "pattern": "ensemble_analysis",
      "inputs": ["step_2_results"],
      "prompt_template": "synthesize_project_plan"
    },
    {
      "step_id": "4",
      "action": "self_critique",
      "inputs": ["step_3_output"],
      "criteria": ["feasibility", "completeness", "client_alignment"]
    },
    {
      "step_id": "5",
      "action": "human_review",
      "confidence_threshold": 0.85,
      "timeout": 3600
    }
  ]
}
```

---

### 3. MCP Gateway Service (Port 5300)

**Purpose:** Single entry point for all MCP interactions, managing routing, load balancing, and connection pooling to dynamic MCP instances.

**Key Responsibilities:**
- Maintain real-time registry of active MCP instances
- Route requests to appropriate MCP instances
- Load balance across multiple instances of same MCP type
- Handle connection pooling and retry logic
- Monitor MCP health and auto-recover failures
- Enforce rate limiting and quotas
- Provide unified API for all MCP operations

**Technology Stack:**
- FastAPI framework
- Redis (service registry, health checks)
- Circuit breaker pattern (for fault tolerance)
- WebSocket support (for streaming responses)

**Key Features:**
- **Smart Routing:** Route queries to closest/healthiest MCP instance
- **Sticky Sessions:** Maintain session affinity for multi-turn conversations
- **Graceful Degradation:** Fall back to higher-tier MCP if specific tier unavailable
- **Query Caching:** Cache frequent queries to reduce MCP load
- **Metrics & Monitoring:** Track query latency, success rate, MCP utilization

---

### 4. MCP Provisioner Service (Port 5400)

**Purpose:** Manages the complete lifecycle of MCP instances - provisioning, health monitoring, scaling, and deprovisioning.

**Key Responsibilities:**
- Provision new MCP instances on-demand (Docker containers)
- Manage MCP state machine (COLD → WARMING → HOT → COOLING → COLD)
- Monitor resource usage (CPU, RAM, disk, network)
- Auto-scale MCP instances based on load
- Gracefully shutdown idle MCPs
- Export/import MCP snapshots
- Handle MCP versioning and hot-swaps

**Technology Stack:**
- FastAPI framework
- Docker SDK (container management)
- PostgreSQL (instance registry and state)
- Prometheus (metrics collection)
- Background tasks (asyncio, APScheduler)

**State Machine:**
```
COLD (stored in registry, not running)
  ↓ (provision request)
WARMING (container starting, loading databases, warming caches)
  ↓ (health check passes)
HOT (actively serving queries, <80% capacity)
  ↓ (idle for 15+ min OR overloaded)
COOLING (draining in-flight queries, preparing to shutdown)
  ↓ (all queries complete)
COLD (container stopped, snapshot saved)
```

**Provisioning Workflow:**
```python
async def provision_mcp(mcp_id: str, tier: str, metadata: dict):
    # 1. Check if already exists
    if exists := get_mcp_state(mcp_id):
        if exists.state == "HOT":
            return {"status": "already_hot", "endpoint": exists.endpoint}
        elif exists.state == "WARMING":
            return {"status": "warming", "eta": exists.eta}
    
    # 2. Set state to WARMING
    update_mcp_state(mcp_id, "WARMING", eta=60)
    
    # 3. Start Docker container
    container = docker_client.containers.run(
        image=f"mcp-server:{tier}",
        name=f"mcp-{tier}-{mcp_id}",
        environment={
            "MCP_ID": mcp_id,
            "TIER": tier,
            "CHROMADB_PATH": f"/data/{mcp_id}/chromadb",
            "NEO4J_URI": f"bolt://neo4j-{mcp_id}:7687"
        },
        volumes={
            f"/data/mcps/{mcp_id}": {"bind": f"/data/{mcp_id}", "mode": "rw"}
        },
        ports={f"3000/tcp": get_available_port()},
        detach=True,
        network="mcp-network"
    )
    
    # 4. Wait for health check
    await wait_for_health(container, timeout=90)
    
    # 5. Load data if first time
    if is_first_provision(mcp_id):
        await trigger_training_pipeline(mcp_id, tier, metadata)
    else:
        await restore_from_snapshot(mcp_id)
    
    # 6. Set state to HOT
    update_mcp_state(mcp_id, "HOT", endpoint=get_container_endpoint(container))
    
    return {"status": "hot", "endpoint": get_container_endpoint(container)}
```

---

### 5. MCP Registry Service (Port 5500)

**Purpose:** Central repository for MCP packages, metadata, versioning, and marketplace functionality.

**Key Responsibilities:**
- Store MCP packages (`.mcp` files) with versioning
- Maintain metadata (tier, tags, size, dependencies, changelog)
- Provide search and discovery (by tag, tier, client, project)
- Handle export/import operations
- Track usage metrics and ratings
- Enable public/private MCPs and access control
- Facilitate MCP sharing and marketplace

**Technology Stack:**
- FastAPI framework
- PostgreSQL (metadata database)
- S3/MinIO (object storage for `.mcp` files)
- Elasticsearch (search and discovery)
- Auth service integration (access control)

**MCP Package Format (`.mcp`):**
```
my-client-mcp_v1.2.3.mcp (tarball)
├── manifest.json          # Metadata, version, dependencies
├── chromadb/              # ChromaDB snapshot (embeddings, vectors)
│   ├── chroma.sqlite3
│   └── index/
├── neo4j/                 # Neo4j snapshot (graph data)
│   ├── dump.cypher
│   └── relationships.json
├── config/                # MCP configuration
│   ├── mcp-config.yaml
│   └── resources.yaml
├── metadata/              # Training metadata
│   ├── sources.json       # What data sources were used
│   ├── stats.json         # Dataset statistics
│   └── lineage.json       # Data lineage tracking
└── README.md              # Human-readable documentation
```

**Registry API:**
```python
# Export MCP
POST /registry/export
{
  "mcp_id": "client-acme-mcp",
  "version": "1.2.3",
  "changelog": "Added Q4 project data",
  "tags": ["client", "acme", "production"]
}

# Import MCP
POST /registry/import
{
  "package_url": "s3://mcp-registry/client-acme-mcp_v1.2.3.mcp",
  "target_mcp_id": "client-acme-mcp",
  "replace_existing": false
}

# Search MCPs
GET /registry/search?q=client&tier=0&tags=production

# Download MCP
GET /registry/download/client-acme-mcp/1.2.3
```

---

### 6. MCP Composer Service (Port 5600)

**Purpose:** Enables composition of multiple MCPs into layered, hierarchical knowledge stacks with defined priority and conflict resolution.

**Key Responsibilities:**
- Parse and validate `mcp-compose.yaml` configurations
- Orchestrate queries across composed MCP layers
- Apply context priority rules (Client > Project > Team > Company > Ecosystem)
- Resolve conflicts between MCP responses
- Enable MCP inheritance and overrides
- Support dynamic composition (add/remove layers at runtime)

**Technology Stack:**
- FastAPI framework
- YAML parser
- Redis (composition cache)
- Orchestrator integration

**MCP Composition File (`mcp-compose.yaml`):**
```yaml
version: "1.0"
name: "acme-project-alpha-context"
description: "Full context stack for ACME Corp's Project Alpha"

layers:
  - name: "client-context"
    mcp_id: "client-acme-mcp"
    tier: 0  # Client
    priority: 1  # Highest priority
    overrides:
      - "terminology"
      - "architecture_decisions"
      - "compliance_requirements"
  
  - name: "project-context"
    mcp_id: "project-alpha-mcp"
    tier: 1  # Project
    priority: 2
    overrides:
      - "timelines"
      - "team_assignments"
      - "project_goals"
  
  - name: "team-context"
    mcp_id: "team-backend-mcp"
    tier: 2  # Team
    priority: 3
    overrides:
      - "coding_patterns"
      - "tech_stack"
  
  - name: "company-context"
    mcp_id: "company-main-mcp"
    tier: 3  # Company
    priority: 4
    fallback: true  # Use if higher tiers don't have answer
  
  - name: "ecosystem-context"
    mcp_id: "ecosystem-mcp"
    tier: 4  # Ecosystem
    priority: 5  # Lowest priority, universal knowledge
    fallback: true

composition_rules:
  conflict_resolution: "priority_based"  # Higher priority wins
  aggregation: "layered"  # Stack results from all layers
  context_window: "smart_pruning"  # Intelligently prune to fit context window
  caching:
    enabled: true
    ttl: 3600  # 1 hour
```

**Composition Query Flow:**
```python
async def query_composed_mcp(composition_id: str, query: str):
    composition = load_composition(composition_id)
    results = []
    
    # Query all layers in parallel
    for layer in composition.layers:
        result = await gateway.query(layer.mcp_id, query)
        results.append({
            "layer": layer.name,
            "priority": layer.priority,
            "tier": layer.tier,
            "result": result
        })
    
    # Apply conflict resolution
    synthesized = resolve_conflicts(results, composition.rules)
    
    # Prune to fit context window
    pruned = dynamic_context_pruning(synthesized, max_tokens=8000)
    
    return pruned
```

---

### 7. MCP Training Coordinator Service (Port 5700)

**Purpose:** Orchestrates the distributed training pipeline that extracts, normalizes, embeds, and loads knowledge into MCPs.

**Key Responsibilities:**
- Coordinate distributed training workers
- Schedule training jobs (on-demand or scheduled)
- Monitor training progress and resource usage
- Handle incremental training (adding new data to existing MCP)
- Manage training pipelines for different data sources
- Ensure data quality and validation
- Track training lineage and metadata

**Technology Stack:**
- FastAPI framework
- Celery/Temporal (distributed task queue)
- Redis/RabbitMQ (message broker)
- PostgreSQL (training jobs database)
- Prometheus (metrics)

**Training Pipeline Architecture:**
```
Training Coordinator
       ↓
┌──────────────────────────────────────────┐
│    Distributed Worker Pool               │
├──────────────────────────────────────────┤
│  Extraction     Normalization  Embedding │
│   Workers    →    Workers    →  Workers  │
│  (10 workers)   (5 workers)  (5 workers) │
└──────────────────────────────────────────┘
       ↓
   MCP Instance (via Provisioner)
   ├─ ChromaDB (vectors loaded)
   └─ Neo4j (graph loaded)
```

**Training Job Workflow:**
```python
# Training Job Definition
{
  "job_id": "train-client-acme-2024-01",
  "mcp_id": "client-acme-mcp",
  "tier": 0,
  "data_sources": [
    {
      "type": "github",
      "repos": ["acme/backend", "acme/frontend"],
      "branches": ["main"],
      "since": "2024-01-01"
    },
    {
      "type": "confluence",
      "spaces": ["ACME Project Docs"],
      "labels": ["client-acme", "architecture"]
    },
    {
      "type": "jira",
      "projects": ["ACME"],
      "issue_types": ["Epic", "Story", "Bug"]
    }
  ],
  "training_params": {
    "embedding_model": "ollama:nomic-embed-text",
    "chunk_size": 500,
    "chunk_overlap": 50,
    "scope_classification": true,
    "auto_tagging": true
  },
  "incremental": false,
  "priority": "high"
}
```

---

## Training Pipeline Details

### Training Worker Types

#### 1. Extraction Workers
Extract raw data from various sources:
- **GitHub Extractor:** Code, commits, PRs, comments, README files
- **Confluence Extractor:** Pages, attachments, comments, page history
- **Jira Extractor:** Issues, comments, sprints, relationships
- **FullStory Extractor:** User sessions, events, funnels
- **Log Extractor:** Service logs, errors, traces
- **Data Store Extractor:** Existing data from PostgreSQL, Neo4j, ChromaDB

#### 2. Normalization Workers
Transform extracted data into consistent format:
- **Markdown Normalizer:** Convert all content to clean `.md` format
- **Code Parser:** Extract patterns, functions, classes using AST
- **Link Resolver:** Resolve cross-references and dependencies
- **Metadata Extractor:** Extract dates, authors, tags, categories
- **Scope Classifier:** Determine which MCP tier(s) the knowledge belongs to

#### 3. Embedding & Tagging Workers
Prepare data for LLM consumption:
- **Embedding Generator:** Create vector embeddings using Ollama
- **Auto-Tagger:** Generate semantic tags using LLM
- **Entity Extractor:** Identify entities (people, projects, tech stack)
- **Relationship Builder:** Build graph relationships for Neo4j
- **Quality Validator:** Ensure embeddings and tags meet quality thresholds

### Training Pipeline Phases

**Phase 1: Extraction (Parallel)**
```
Source Agent → GitHub Extractor → Raw JSON
             → Confluence Extractor → Raw JSON
             → Jira Extractor → Raw JSON
             → [Other Sources]
```

**Phase 2: Normalization (Parallel)**
```
Raw JSON → Markdown Normalizer → Clean .md files
         → Scope Classifier → Tier assignments
         → Metadata Extractor → Structured metadata
```

**Phase 3: Embedding & Tagging (Parallel)**
```
Clean .md → Chunking → Chunks (500 tokens)
         → Embedding Generator → Vectors
         → Auto-Tagger → Tags
         → Entity Extractor → Entities
         → Relationship Builder → Graph edges
```

**Phase 4: Loading (Sequential)**
```
Vectors + Metadata → ChromaDB (semantic search)
Entities + Relationships → Neo4j (graph traversal)
Metadata → MCP Config (resources, tools)
```

---

## MCP Agent

Each MCP instance includes an embedded **MCP Agent** similar to the Source Agent, providing:

### Agent Responsibilities:
- **Health Monitoring:** Report MCP status, resource usage, query latency
- **Query Logging:** Log all queries and responses for analysis
- **Incremental Learning:** Detect when new data is available for training
- **Self-Optimization:** Tune embedding/retrieval parameters based on usage
- **Anomaly Detection:** Alert when query patterns or errors are unusual
- **Feedback Loop:** Collect user feedback to improve MCP quality

### Agent API:
```python
# MCP Agent endpoints (embedded in each MCP)
GET  /agent/health         # Health status
GET  /agent/metrics        # Performance metrics
POST /agent/query          # Execute query (logged)
POST /agent/feedback       # Submit user feedback
GET  /agent/suggest-training  # Suggest when retraining needed
```

---

## Frontend Dashboard

**MCP Control Center (Port 8080)** - Comprehensive web UI for managing the MCP ecosystem.

### Dashboard Features:

#### 1. MCP Overview
- **Active MCPs:** List of HOT MCPs with status, tier, resource usage
- **Provisioning Queue:** MCPs in WARMING state with ETAs
- **Health Status:** System-wide health check (all services green/yellow/red)

#### 2. MCP Management
- **Create New MCP:** Wizard for defining new MCP (tier, sources, config)
- **Train MCP:** Trigger training job with source selection
- **Export/Import MCP:** Download or upload `.mcp` packages
- **Version Control:** View MCP versions, changelog, rollback capability
- **Hot-Swap:** Switch MCP versions with zero downtime

#### 3. Query Playground
- **Interactive Query:** Test queries against any MCP or composition
- **Query History:** View past queries with latency and response quality
- **Composition Builder:** Visually build `mcp-compose.yaml` files

#### 4. Training Insights
- **Training Jobs:** List of running/completed training jobs
- **Data Sources:** View what sources are indexed in each MCP
- **Training Metrics:** Dataset size, embedding count, training duration
- **Quality Scores:** Auto-generated quality metrics for MCPs

#### 5. Analytics
- **Query Analytics:** Most frequent queries, avg latency, success rate
- **MCP Utilization:** Which MCPs are most/least used
- **Cost Analysis:** Resource usage, storage costs, compute costs
- **ROI Metrics:** Value generated by MCP-enhanced workflows

---

## Integration with Project Planning Service

### Enhanced Project Planning Workflow

**Current State:** Project Planning Service generates plans based on templates and rules.

**Enhanced with MCP System:**

```
User Request: "Generate a project plan for ACME Corp's mobile app redesign"
     ↓
Project Planning Service
     ↓
MCP Interpreter: Parse request, identify:
  - Client: ACME Corp
  - Project Type: mobile app redesign
  - Required Context: client history, similar projects, team capacity
     ↓
MCP Orchestrator: Create workflow:
  Step 1: Provision Client ACME MCP (if COLD)
  Step 2: Parallel query:
    - Client MCP: "ACME's brand guidelines, past projects, tech stack preferences"
    - Project MCP: "Successful mobile redesign projects, timelines, risks"
    - Team MCP: "Available mobile developers, current capacity"
    - Company MCP: "Standard mobile project template, QA process"
  Step 3: Synthesize context with Ensemble Analysis
  Step 4: Generate plan using LLM with full context
  Step 5: Self-Critique plan for feasibility and client alignment
  Step 6: Human review (if confidence < 90%)
     ↓
Enhanced Project Plan:
  - Client-specific terminology and branding
  - Timeline based on similar past projects + team capacity
  - Tech stack aligned with client preferences
  - Risk mitigation from lessons learned
  - QA process from company standards
```

### New Project Planning Endpoints

```python
# Project Planning Service - Enhanced with MCP

@app.post("/projects/plan/enhanced")
async def create_enhanced_project_plan(request: ProjectPlanRequest):
    """
    Generate project plan enriched with MCP context
    """
    # Step 1: Interpret request
    interpreted = await mcp_interpreter.parse_project_request(request)
    
    # Step 2: Orchestrate MCP queries
    workflow = await mcp_orchestrator.create_workflow(interpreted)
    context = await mcp_orchestrator.execute_workflow(workflow)
    
    # Step 3: Generate plan with context
    plan = await generate_project_plan_with_context(request, context)
    
    # Step 4: Apply LLM patterns
    critiqued_plan = await self_critique_plan(plan, context)
    
    # Step 5: Human review if needed
    if critiqued_plan.confidence < 0.9:
        await request_human_review(critiqued_plan)
    
    return critiqued_plan
```

---

## Advanced LLM Architecture Integration

Based on `ADVANCED_LLM_ARCHITECTURE_PATTERNS.md`, the following patterns are integrated into the MCP Orchestrator:

### 1. Ensemble Orchestration
Run the same query through multiple MCP compositions and synthesize results:
```python
# Query three different MCP stacks in parallel
results = await asyncio.gather(
    query_composition("client-focused-stack", query),
    query_composition("project-historical-stack", query),
    query_composition("team-capacity-stack", query)
)
# Let LLM synthesize the three perspectives
final_result = await llm_consensus(results)
```

### 2. Chain-of-Thought (CoT)
Force step-by-step reasoning in project planning:
```python
prompt = """
To create a project plan, let's think step by step:

1. First, analyze the client's requirements from the Client MCP...
2. Next, identify similar past projects and their outcomes...
3. Then, assess team capacity and skills...
4. Finally, synthesize into a detailed plan...

Context from MCPs: {mcp_context}
"""
```

### 3. Self-Critique & Refinement
MCP Orchestrator critiques its own generated plans:
```python
# Generate initial plan
initial_plan = await generate_plan(context)

# Self-critique
critique_prompt = f"""
Review this project plan for:
- Feasibility given team capacity
- Alignment with client's past preferences
- Risk mitigation completeness
- Timeline realism

Plan: {initial_plan}
Context: {context}

Provide specific critiques and suggestions.
"""
critique = await llm(critique_prompt)

# Refine based on critique
refined_plan = await refine_plan(initial_plan, critique)
```

### 4. Hierarchical Retrieval
Query MCPs in order of context priority:
```python
# Start with most specific context
client_context = await query_mcp("client-acme-mcp", query)

# If insufficient, expand to project tier
if client_context.confidence < 0.8:
    project_context = await query_mcp("project-alpha-mcp", query)
    combined_context = merge_contexts(client_context, project_context)

# Continue up the hierarchy as needed
```

### 5. Self-Consistency
Generate multiple reasoning paths and vote:
```python
# Generate 5 different project plans with temperature=0.7
plans = await asyncio.gather(*[
    generate_plan_with_mcp(context, temperature=0.7) 
    for _ in range(5)
])

# Use LLM to identify the most consistent/best plan
best_plan = await llm_vote_on_plans(plans)
```

### 6. Human-in-the-Loop (Confidence-Based)
```python
if plan.confidence < 0.85:
    # Request human approval with explanation
    await request_approval(
        plan=plan,
        reason=f"Confidence {plan.confidence} below threshold",
        context=context,
        timeout=3600  # 1 hour
    )
```

---

## Data Flow: End-to-End Example

### Scenario: "Create a project plan for Client ACME's new feature"

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. User submits request via Project Planning Service UI         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. MCP Interpreter (Port 5100)                                   │
│    - Intent: "project_planning"                                  │
│    - Entities: {client: "ACME", feature: "new_feature"}         │
│    - Required MCPs: ["client-acme", "project", "company"]       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. MCP Orchestrator (Port 5200)                                  │
│    - Check MCP availability via Gateway                          │
│    - Client ACME MCP: COLD → Trigger provisioning               │
│    - Project MCP: HOT → Ready                                    │
│    - Company MCP: HOT → Ready                                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. MCP Provisioner (Port 5400)                                   │
│    - Start Docker container for Client ACME MCP                  │
│    - Load ChromaDB and Neo4j snapshots                           │
│    - Wait for health check (30-60 seconds)                       │
│    - State: COLD → WARMING → HOT                                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. MCP Gateway (Port 5300)                                       │
│    - Route queries to 3 MCP instances in parallel:               │
│      • Client ACME MCP: "ACME's requirements and preferences"    │
│      • Project MCP: "Similar features and timelines"             │
│      • Company MCP: "Standard feature development process"       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 6. Active MCP Instances                                          │
│    - Each MCP queries its ChromaDB (semantic search)             │
│    - Each MCP queries its Neo4j (relationship traversal)         │
│    - Each MCP synthesizes response via embedded LLM              │
│    - Responses sent back to Gateway                              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 7. MCP Orchestrator (Port 5200)                                  │
│    - Receive 3 responses from Gateway                            │
│    - Apply Ensemble Analysis (LLM synthesizes responses)         │
│    - Generate project plan with Chain-of-Thought reasoning       │
│    - Self-Critique plan for feasibility                          │
│    - Confidence score: 0.92 (high) → Auto-approve                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 8. Project Planning Service                                      │
│    - Receive enhanced project plan                               │
│    - Store plan in database                                      │
│    - Return to user                                              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 9. User receives hyper-contextualized project plan with:         │
│    - ACME-specific terminology and constraints                   │
│    - Timeline based on similar past features                     │
│    - Team assignments based on capacity                          │
│    - Risk mitigation from lessons learned                        │
│    - Compliance with company standards                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## Deployment Architecture

### Ecosystem Docker Compose Integration

**All MCP services integrate into existing `docker-compose.dev.yml`:**

**Key Integration Points:**
- ✅ Network: `hackathon_default` (maps to `doc-ecosystem-dev`)
- ✅ LLM: Via `llm-gateway:5055` (NOT direct ollama)
- ✅ Cache: Shared `redis:6379`
- ✅ Logging: `log-collector:5080`
- ✅ Testing: `mock-data-generator:5065`
- ✅ Shared libs: `services/shared/` mounted as volume

### Complete Docker Compose Configuration

**Add to `/Users/mykalthomas/Documents/work/Hackathon/docker-compose.dev.yml`:**

```yaml
# ============================================================================
# MCP SERVICES - Model Context Protocol System
# ============================================================================
# All MCP services follow ecosystem standards:
# - DDD architecture with bounded contexts
# - Integration with llm-gateway (NOT direct Ollama)
# - Shared infrastructure (redis, log-collector)
# - Standardized health checks and monitoring
# - >90% test coverage requirement
# ============================================================================

  mcp-interpreter:
    build:
      context: .
      dockerfile: services/mcp-interpreter/Dockerfile
    container_name: hackathon-mcp-interpreter
    ports:
      - "8144:5100"  # External:Internal
    environment:
      # Standard service configuration
      - PYTHONPATH=/app
      - SERVICE_NAME=mcp-interpreter
      - SERVICE_API_PORT=5100
      - ENVIRONMENT=development
      
      # Logging (ecosystem standard)
      - LOG_COLLECTOR_URL=http://log-collector:5080
      - LOG_COLLECTOR_ENABLED=true
      - LOG_LEVEL=INFO
      
      # Dependencies
      - REDIS_API_HOST=redis
      - LLM_GATEWAY_URL=http://llm-gateway:5055  # ⚠️ USE GATEWAY, NOT OLLAMA
      
      # DDD Architecture flag
      - DDD_ARCHITECTURE=true
      - DDD_CONFIG_FILE=config/ddd_config.yaml
      
      # Network resilience (ecosystem standard)
      - HTTP_CONNECTION_POOL_SIZE=10
      - HTTP_MAX_KEEPALIVE_CONNECTIONS=5
      - HTTP_TIMEOUT=30
      - CIRCUIT_BREAKER_FAILURE_THRESHOLD=3
      - CIRCUIT_BREAKER_RECOVERY_TIMEOUT=45
      - RETRY_MAX_ATTEMPTS=2
      - RETRY_BACKOFF_FACTOR=2.0
    
    volumes:
      - ./:/app:ro                                           # Read-only workspace
      - ./services/mcp-interpreter:/app/services/mcp-interpreter:rw  # Service code
      - ./services/shared:/app/services/shared:ro            # Shared libraries
    
    working_dir: /app
    
    depends_on:
      redis:
        condition: service_healthy
      llm-gateway:
        condition: service_healthy
      log-collector:
        condition: service_started
    
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5100/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    
    networks:
      - hackathon_default  # Ecosystem standard network
    
    profiles:
      - all
      - mcp_services
      - development
    
    restart: unless-stopped
  
  mcp-orchestrator:
    build: ./services/mcp-orchestrator
    ports: ["5200:5200"]
    environment:
      - TEMPORAL_URL=temporal:7233
      - REDIS_URL=redis:6379
    depends_on: [temporal, redis, mcp-interpreter, mcp-gateway]
  
  mcp-gateway:
    build: ./services/mcp-gateway
    ports: ["5300:5300"]
    environment:
      - REDIS_URL=redis:6379
    depends_on: [redis]
  
  mcp-provisioner:
    build: ./services/mcp-provisioner
    ports: ["5400:5400"]
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock  # Docker-in-Docker
      - ./data/mcps:/data/mcps
    environment:
      - POSTGRES_URL=postgresql://postgres:5432/mcp_registry
      - DOCKER_NETWORK=mcp-network
    depends_on: [postgres]
  
  mcp-registry:
    build: ./services/mcp-registry
    ports: ["5500:5500"]
    volumes:
      - ./data/registry:/data/registry
    environment:
      - POSTGRES_URL=postgresql://postgres:5432/mcp_registry
      - S3_ENDPOINT=http://minio:9000
      - ELASTICSEARCH_URL=http://elasticsearch:9200
    depends_on: [postgres, minio, elasticsearch]
  
  mcp-composer:
    build: ./services/mcp-composer
    ports: ["5600:5600"]
    environment:
      - REDIS_URL=redis:6379
      - GATEWAY_URL=http://mcp-gateway:5300
    depends_on: [redis, mcp-gateway]
  
  mcp-training-coordinator:
    build: ./services/mcp-training-coordinator
    ports: ["5700:5700"]
    environment:
      - CELERY_BROKER_URL=redis://redis:6379
      - POSTGRES_URL=postgresql://postgres:5432/mcp_training
      - OLLAMA_URL=http://ollama:11434
    depends_on: [redis, postgres, ollama]
  
  # Training Workers
  extraction-worker:
    build: ./services/mcp-training-workers/extraction
    deploy:
      replicas: 10
    environment:
      - CELERY_BROKER_URL=redis://redis:6379
      - SOURCE_AGENT_URL=http://source-agent:8020
    depends_on: [redis, source-agent]
  
  normalization-worker:
    build: ./services/mcp-training-workers/normalization
    deploy:
      replicas: 5
    environment:
      - CELERY_BROKER_URL=redis://redis:6379
    depends_on: [redis]
  
  embedding-worker:
    build: ./services/mcp-training-workers/embedding
    deploy:
      replicas: 5
    environment:
      - CELERY_BROKER_URL=redis://redis:6379
      - OLLAMA_URL=http://ollama:11434
    depends_on: [redis, ollama]
  
  # Frontend
  mcp-dashboard:
    build: ./services/mcp-dashboard
    ports: ["8080:8080"]
    environment:
      - INTERPRETER_URL=http://mcp-interpreter:5100
      - ORCHESTRATOR_URL=http://mcp-orchestrator:5200
      - GATEWAY_URL=http://mcp-gateway:5300
      - PROVISIONER_URL=http://mcp-provisioner:5400
      - REGISTRY_URL=http://mcp-registry:5500
      - COMPOSER_URL=http://mcp-composer:5600
    depends_on: [mcp-orchestrator, mcp-gateway, mcp-provisioner]
  
  # Infrastructure
  postgres:
    image: postgres:16
    environment:
      - POSTGRES_PASSWORD=postgres
    volumes:
      - postgres-data:/var/lib/postgresql/data
  
  redis:
    image: redis:7
    volumes:
      - redis-data:/data
  
  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    ports: ["9000:9000", "9001:9001"]
    volumes:
      - minio-data:/data
  
  elasticsearch:
    image: elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    volumes:
      - elasticsearch-data:/usr/share/elasticsearch/data
  
  temporal:
    image: temporalio/auto-setup:latest
    ports: ["7233:7233"]
    depends_on: [postgres]
  
  ollama:
    image: ollama/ollama:latest
    ports: ["11434:11434"]
    volumes:
      - ollama-data:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]

volumes:
  postgres-data:
  redis-data:
  minio-data:
  elasticsearch-data:
  ollama-data:

networks:
  default:
    name: mcp-network
```

---

## Implementation Roadmap

### Phase 1: Foundation (Weeks 1-4)
- **Week 1-2:** Set up infrastructure (Docker, databases, message queues)
- **Week 3-4:** Implement MCP Provisioner + basic lifecycle management
- **Deliverable:** Can provision/deprovision basic MCP instances

### Phase 2: Core Services (Weeks 5-10)
- **Week 5-6:** MCP Gateway (routing, load balancing)
- **Week 7-8:** MCP Interpreter (query parsing, intent classification)
- **Week 9-10:** MCP Orchestrator (workflow engine, basic patterns)
- **Deliverable:** End-to-end query → MCP → response workflow

### Phase 3: Training Pipeline (Weeks 11-16)
- **Week 11-12:** Training Coordinator + worker framework
- **Week 13-14:** Extraction workers (GitHub, Confluence, Jira)
- **Week 15-16:** Normalization + Embedding workers
- **Deliverable:** Can train MCPs from ecosystem data sources

### Phase 4: Advanced Features (Weeks 17-22)
- **Week 17-18:** MCP Registry (export/import, versioning)
- **Week 19-20:** MCP Composer (multi-MCP compositions)
- **Week 21-22:** Advanced LLM patterns (ensemble, self-critique, CoT)
- **Deliverable:** Full MCP lifecycle + advanced querying

### Phase 5: Integration (Weeks 23-26)
- **Week 23-24:** Project Planning Service integration
- **Week 25-26:** MCP Dashboard UI
- **Deliverable:** Production-ready MCP system for project planning

### Phase 6: Optimization (Weeks 27-30)
- **Week 27-28:** Performance tuning, caching strategies
- **Week 29-30:** Monitoring, alerting, observability
- **Deliverable:** Production-hardened system

---

## Resource Requirements

### Compute Resources
- **MCP Services:** 8 containers × 1 CPU × 2GB RAM = 16 GB RAM
- **Training Workers:** 20 workers × 0.5 CPU × 1GB RAM = 20 GB RAM
- **Active MCP Instances:** 5 concurrent × 2 CPU × 4GB RAM = 20 GB RAM
- **Infrastructure:** 10 GB RAM (databases, queues, LLM)
- **Total:** ~66 GB RAM, 30 CPU cores

### Storage Requirements
- **MCP Packages (Registry):** 100 MCPs × 500MB avg = 50 GB
- **Active MCP Data:** 5 MCPs × 2GB = 10 GB
- **Training Data Cache:** 50 GB
- **Logs & Metrics:** 20 GB
- **Total:** ~130 GB storage

### Network
- **Internal (MCP services):** <100 Mbps
- **External (LLM API calls):** Depends on Ollama usage (local = minimal)

---

## Success Metrics

### System Health
- **MCP Provisioning Time:** < 60 seconds (COLD → HOT)
- **Query Latency:** < 2 seconds (P95) for single MCP query
- **Composed Query Latency:** < 5 seconds (P95) for 5-tier composition
- **System Uptime:** 99.9%

### Quality Metrics
- **Context Relevance:** > 85% (user-rated)
- **Plan Accuracy:** > 90% (for project planning use case)
- **False Positive Rate:** < 5% (incorrect/irrelevant responses)

### Efficiency Metrics
- **MCP Resource Utilization:** > 60% (minimize idle HOT MCPs)
- **Training Job Success Rate:** > 95%
- **Cache Hit Rate:** > 70% (for frequent queries)

### Business Metrics
- **Project Planning Time Reduction:** 50% (manual → MCP-enhanced)
- **Plan Quality Score:** +40% (stakeholder satisfaction)
- **Knowledge Retrieval Speed:** 10x faster than manual search

---

## Security & Compliance

### Access Control
- **MCP-Level Permissions:** Who can query which MCPs
- **Tier-Based Access:** Client MCPs restricted to project teams
- **Audit Logging:** All queries, responses, and approvals logged

### Data Privacy
- **Client Data Isolation:** Client MCPs run in separate containers/networks
- **PII Redaction:** Training pipeline redacts sensitive data
- **Encryption:** MCP packages encrypted at rest (S3)

### Compliance
- **GDPR/CCPA:** Client MCP export/deletion on request
- **SOC 2:** Audit trails for all MCP operations
- **Data Lineage:** Track what data sources fed into each MCP

---

## Next Steps

1. **Review & Approve Architecture:** Stakeholder sign-off on this plan
2. **Prioritize Use Cases:** Confirm Project Planning Service as first integration
3. **Set Up Infrastructure:** Provision dev environment with Docker Compose
4. **Phase 1 Kickoff:** Begin MCP Provisioner implementation
5. **Continuous Iteration:** Weekly demos and feedback loops

---

## Related Documents

This architecture plan should be read alongside:
- `MCP_TRAINING_PIPELINE_DESIGN.md` - Detailed training pipeline specs
- `MCP_ORCHESTRATOR_PATTERNS.md` - Advanced LLM architecture patterns implementation
- `MCP_PROVISIONER_SPECIFICATION.md` - Provisioner service detailed design
- `MCP_GATEWAY_API_SPEC.md` - Gateway API documentation
- `PROJECT_PLANNING_MCP_INTEGRATION.md` - Integration guide for Project Planning Service

---

**Document Version:** 1.0  
**Last Updated:** 2025-10-06  
**Status:** Draft - Awaiting Review

