# MCP SYSTEM ARCHITECTURE MAP

**Generated:** 2025-10-06T17:30:42.030406  
**Status:** Operational  
**Version:** 1.0.0  

---

## 🏗️ HIGH-LEVEL ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                            │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Dashboard   │  │ Project      │  │ IDE/Cursor   │          │
│  │  UI (8080)   │  │ Planning UI  │  │ MCP Client   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATION LAYER                           │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Interpreter  │→ │ Orchestrator │→ │   Gateway    │          │
│  │   (5100)     │  │   (5200)     │  │   (5300)     │          │
│  │              │  │              │  │              │          │
│  │ 17 Intents   │  │ 24 Patterns  │  │ Load Balance │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                   LIFECYCLE MANAGEMENT                           │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Provisioner  │  │ Infrastructure│  │  Registry    │          │
│  │   (5400)     │  │   (5500)     │  │   (5550)     │          │
│  │              │  │              │  │              │          │
│  │ Docker SDK   │  │ Context Mgmt │  │ Versioning   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    TRAINING PIPELINE                             │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Training     │→ │  Extractors  │→ │ Normalizers  │          │
│  │ Coordinator  │  │              │  │              │          │
│  │   (5600)     │  │ • GitHub     │  │ • Markdown   │          │
│  │              │  │ • Confluence │  │ • Classifier │          │
│  │ Job Mgmt     │  │ • Jira       │  │              │          │
│  │              │  │ • Wikipedia  │  │              │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                              ▼                   │
│                    ┌──────────────┐  ┌──────────────┐          │
│                    │  Embedders   │  │ MCP Logging  │          │
│                    │              │  │   (5650)     │          │
│                    │ • Vector     │  │              │          │
│                    │ • Tagger     │  │ Deep         │          │
│                    │ • Entity     │  │ Integration  │          │
│                    └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    INFRASTRUCTURE                                │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Redis      │  │  ChromaDB    │  │   Neo4j      │          │
│  │   (6379)     │  │  (Vector DB) │  │  (Graph DB)  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ LLM Gateway  │  │   Ollama     │  │   Celery     │          │
│  │   (5055)     │  │   (11434)    │  │  (Workers)   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📦 SERVICES INVENTORY

### Core MCP Services (8 services)

| # | Service | Port | Purpose | Status | LOC |
|---|---------|------|---------|--------|-----|
| 1 | **MCP Provisioner** | 5400 | Lifecycle management | ✅ | ~2,500 |
| 2 | **MCP Infrastructure** | 5500 | Context management | ✅ | ~4,200 |
| 3 | **MCP Gateway** | 5300 | Routing & LB | ✅ | ~3,200 |
| 4 | **MCP Interpreter** | 5100 | Query parsing | ✅ | ~2,800 |
| 5 | **MCP Orchestrator** | 5200 | Workflow engine | ✅ | ~5,300 |
| 6 | **MCP Registry** | 5550 | Package mgmt | ✅ | ~3,700 |
| 7 | **Training Coordinator** | 5600 | Job orchestration | ✅ | ~2,300 |
| 8 | **MCP Logging** | 5650 | Centralized logging | ✅ | ~450 |

**Total:** ~24,450 LOC

### Workers (9 workers)

| # | Worker | Type | Purpose | Status |
|---|--------|------|---------|--------|
| 1 | **GitHub Extractor** | Extraction | Repos, PRs, issues | ✅ |
| 2 | **Confluence Extractor** | Extraction | Pages, docs | ✅ |
| 3 | **Jira Extractor** | Extraction | Issues, projects | ✅ |
| 4 | **Wikipedia Extractor** | Extraction | Articles + crawl | ✅ |
| 5 | **Markdown Normalizer** | Normalization | Format std | ✅ |
| 6 | **Scope Classifier** | Normalization | Tier classification | ✅ |
| 7 | **Vector Generator** | Embedding | Embeddings | ✅ |
| 8 | **Auto Tagger** | Embedding | LLM tagging | ✅ |
| 9 | **Entity Extractor** | Embedding | NER | ✅ |

---

## 🔗 DATA FLOW

### 1. Query Workflow

```
User Query
    ↓
MCP Interpreter (5100)
    ↓ [Parse intent, extract entities]
Structured Query
    ↓
MCP Orchestrator (5200)
    ↓ [Select pattern, create workflow]
Workflow Plan
    ↓
MCP Gateway (5300)
    ↓ [Route to MCP instance]
MCP Instance
    ↓ [Execute query]
Results
    ↓
User
```

### 2. Training Workflow

```
Training Request
    ↓
Training Coordinator (5600)
    ↓ [Create job, schedule workers]
Extraction Workers
    ↓ [GitHub, Confluence, Jira, Wikipedia]
Raw Documents
    ↓
Normalization Workers
    ↓ [Markdown, Scope Classification]
Normalized Documents
    ↓
Embedding Workers
    ↓ [Vector, Tags, Entities]
Enriched Documents
    ↓
Storage (ChromaDB, Neo4j)
    ↓
MCP Instance Ready
```

### 3. Provisioning Workflow

```
Provision Request
    ↓
MCP Provisioner (5400)
    ↓ [Create Docker container]
COLD State
    ↓ [Load configuration]
WARMING State
    ↓ [Load knowledge base]
HOT State
    ↓ [Register with Gateway]
Ready for Queries
```

---

## 🎯 KEY CAPABILITIES

### Orchestration Layer
- **17 Query Intent Types** (search, analysis, comparison, etc.)
- **31 Entity Types** (person, org, project, etc.)
- **24 LLM Patterns** across 9 categories
- **Distributed Tracing** with trace_id/span_id

### Training Pipeline
- **4 Data Sources** (GitHub, Confluence, Jira, Wikipedia)
- **10 Job States** (pending → running → complete)
- **5 Priority Levels** (critical → low)
- **3 Worker Types** (extraction, normalization, embedding)

### Lifecycle Management
- **4 MCP States** (COLD → WARMING → HOT → COOLING)
- **5 Export Formats** (json, yaml, tar, zip, docker)
- **4 Storage Backends** (local, s3, gcs, azure)
- **Semantic Versioning** (major.minor.patch)

---

## 📊 SYSTEM METRICS

### Code Statistics
- **Total LOC:** ~34,000
- **Services:** 8
- **Workers:** 9
- **Tests:** 15+
- **Documentation:** 11 guides

### Performance Targets
- **Query Latency:** <500ms (p95)
- **Training Throughput:** 1000 docs/min
- **MCP Startup:** <30s (COLD → HOT)
- **Log Ingestion:** 10K logs/sec

---

## 🔐 SECURITY & RELIABILITY

### Security
- Non-root Docker containers
- Redis password authentication
- API key validation
- Network isolation (hackathon_default)

### Reliability
- Health checks on all services
- Retry logic with exponential backoff
- Circuit breakers
- Graceful degradation

---

## 📍 NETWORK TOPOLOGY

**Network:** `hackathon_default` (172.20.0.0/16)

```
┌─────────────────────────────────────┐
│   hackathon_default network          │
│                                       │
│  ┌─────────┐  ┌─────────┐           │
│  │ 5100-   │  │ 5400-   │           │
│  │ Interp  │  │ Prov    │           │
│  └─────────┘  └─────────┘           │
│                                       │
│  ┌─────────┐  ┌─────────┐           │
│  │ 5200-   │  │ 5500-   │           │
│  │ Orch    │  │ Infra   │           │
│  └─────────┘  └─────────┘           │
│                                       │
│  ┌─────────┐  ┌─────────┐           │
│  │ 5300-   │  │ 5550-   │           │
│  │ Gateway │  │ Registry│           │
│  └─────────┘  └─────────┘           │
│                                       │
│  ┌─────────┐  ┌─────────┐           │
│  │ 5600-   │  │ 5650-   │           │
│  │ Training│  │ Logging │           │
│  └─────────┘  └─────────┘           │
└─────────────────────────────────────┘
```

---

**Generated by MCP Report Generator**  
**Version:** 1.0.0  
**Timestamp:** 2025-10-06T17:30:42.030406  
