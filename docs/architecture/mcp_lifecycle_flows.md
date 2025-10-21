---
llm_metadata:
  document_type: architecture
  content_focus: technical
  platform:
    primary: mcp
    secondary: []
  status: active
  created_date: '2025-10-01'
  last_modified: '2025-10-07'
  topics:
  - postgresql
  - rag
  - embeddings
  - vector_search
  - monitoring
  - documentation
  concepts: []
  technologies: []
  services_mentioned: []
  semantic_summary: Architecture document about technical aspects of the mcp platform
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

# 🔄 MCP Lifecycle - Complete Visual Flows

**Complete guide to creating, training, storing, and loading MCPs across the ecosystem**

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Phase 1: MCP Creation](#phase-1-mcp-creation)
3. [Phase 2: MCP Training](#phase-2-mcp-training)
4. [Phase 3: MCP Storage & Packaging](#phase-3-mcp-storage--packaging)
5. [Phase 4: MCP Loading & Usage](#phase-4-mcp-loading--usage)
6. [Complete End-to-End Flow](#complete-end-to-end-flow)
7. [Service Interaction Matrix](#service-interaction-matrix)

---

## 🎯 Overview

The MCP lifecycle consists of four major phases:

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   CREATE     │────►│    TRAIN     │────►│    STORE     │────►│     LOAD     │
│   Phase 1    │     │   Phase 2    │     │   Phase 3    │     │   Phase 4    │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
  Provisioning        Knowledge            Package              Query
  & Setup            Ingestion             Management          Execution
```

**Services Involved**: 14 MCP services work together to enable the complete MCP lifecycle.

---

## 🚀 Phase 1: MCP Creation

### Overview
Creating a new MCP instance involves provisioning, tier assignment, and initial setup.

### Services Involved
- **MCP Gateway** (8001): Entry point
- **MCP Provisioner** (8003): Orchestrates creation
- **MCP Tier Manager** (8013): Assigns tier
- **MCP Store** (8008): Initializes storage
- **MCP Registry** (8006): Registers MCP
- **MCP Infrastructure** (8007): Health checks

### Detailed Flow

```
┌──────────────┐
│     User     │
└──────┬───────┘
       │
       │ 1. POST /api/v1/mcps/create
       │    {
       │      "name": "acme-corp-dev",
       │      "tier": "Project",
       │      "parent_tier": "team-123",
       │      "config": {...}
       │    }
       │
       ▼
┌──────────────────┐
│   MCP Gateway    │
│   (Port 8001)    │
└──────┬───────────┘
       │
       │ 2. Authenticate & validate request
       │ 3. Route to Provisioner
       │
       ▼
┌──────────────────┐
│  MCP Provisioner │
│   (Port 8003)    │
└──────┬───────────┘
       │
       │ 4. Generate MCP ID: "mcp-acme-corp-dev-uuid"
       │ 5. Validate configuration
       │
       ├─────────────────────────────┐
       │                             │
       │ 6. Request tier assignment  │
       ▼                             │
┌──────────────────┐                │
│ MCP Tier Manager │                │
│   (Port 8013)    │                │
└──────┬───────────┘                │
       │                             │
       │ 7. Create tier node         │
       │    - Assign to hierarchy    │
       │    - Set inheritance rules  │
       │    - Configure policies     │
       │                             │
       │ 8. Return tier info         │
       │    {                        │
       │      "tier_id": "tier-123", │
       │      "level": "Project",    │
       │      "parent": "team-123"   │
       │    }                        │
       │                             │
       ▼                             │
┌──────────────────┐                │
│  MCP Provisioner │◄───────────────┘
│   (Port 8003)    │
└──────┬───────────┘
       │
       │ 9. Initialize storage
       ▼
┌──────────────────┐
│   MCP Store      │
│   (Port 8008)    │
└──────┬───────────┘
       │
       │ 10. Create storage structures
       │     - PostgreSQL: Metadata tables
       │     - Neo4j: Knowledge graph nodes
       │     - ChromaDB: Vector collections
       │     - MinIO: Binary storage bucket
       │
       │ 11. Confirm storage ready
       │
       ▼
┌──────────────────┐
│  MCP Provisioner │
│   (Port 8003)    │
└──────┬───────────┘
       │
       │ 12. Register in catalog
       ▼
┌──────────────────┐
│  MCP Registry    │
│   (Port 8006)    │
└──────┬───────────┘
       │
       │ 13. Register MCP package
       │     - Name: acme-corp-dev
       │     - Version: 0.1.0
       │     - Status: CREATED
       │     - Tier: Project
       │
       │ 14. Confirm registration
       │
       ▼
┌──────────────────┐
│  MCP Provisioner │
│   (Port 8003)    │
└──────┬───────────┘
       │
       │ 15. Health check
       ▼
┌──────────────────┐
│ MCP Infrastructure│
│   (Port 8007)    │
└──────┬───────────┘
       │
       │ 16. Register for monitoring
       │     - Add to health check list
       │     - Set up metrics collection
       │     - Configure alerts
       │
       │ 17. Confirm monitoring active
       │
       ▼
┌──────────────────┐
│  MCP Provisioner │
│   (Port 8003)    │
└──────┬───────────┘
       │
       │ 18. Return success
       ▼
┌──────────────────┐
│   MCP Gateway    │
│   (Port 8001)    │
└──────┬───────────┘
       │
       │ 19. Format response
       ▼
┌──────────────┐
│     User     │
└──────────────┘
       │
       │ Response:
       │ {
       │   "mcp_id": "mcp-acme-corp-dev-uuid",
       │   "name": "acme-corp-dev",
       │   "tier": "Project",
       │   "status": "CREATED",
       │   "storage_ready": true,
       │   "monitoring": "active"
       │ }
```

### Summary: Phase 1

**Time**: ~2-5 seconds  
**Services**: 6 services  
**Result**: Empty MCP instance ready for training

---

## 🎓 Phase 2: MCP Training

### Overview
Training populates the MCP with knowledge from various data sources.

### Services Involved
- **MCP Gateway** (8001): Entry point
- **Training Coordinator** (5600): Orchestrates training
- **Celery Workers**: Extract, normalize, embed data
- **MCP Store** (8008): Stores knowledge
- **MCP Tier Manager** (8013): Enforces tier boundaries
- **MCP Logs** (8011): Monitors training

### Detailed Flow

```
┌──────────────┐
│     User     │
└──────┬───────┘
       │
       │ 1. POST /api/v1/mcps/{mcp_id}/train
       │    {
       │      "data_sources": ["GITHUB", "CONFLUENCE"],
       │      "priority": "HIGH",
       │      "config": {
       │        "github": {
       │          "repos": ["acme/api", "acme/web"]
       │        },
       │        "confluence": {
       │          "spaces": ["ENG", "PROD"]
       │        }
       │      }
       │    }
       │
       ▼
┌──────────────────┐
│   MCP Gateway    │
│   (Port 8001)    │
└──────┬───────────┘
       │
       │ 2. Route to Training Coordinator
       │
       ▼
┌──────────────────────┐
│ Training Coordinator │
│   (Port 5600)        │
└──────┬───────────────┘
       │
       │ 3. Create training job: JOB-001
       │    Status: PENDING → VALIDATING
       │
       │ 4. Validate configuration
       │    - Check data source credentials
       │    - Verify MCP exists
       │    - Check tier permissions
       │
       ├──────────────────────────────┐
       │                              │
       │ 5. Check tier permissions    │
       ▼                              │
┌──────────────────┐                 │
│ MCP Tier Manager │                 │
│   (Port 8013)    │                 │
└──────┬───────────┘                 │
       │                              │
       │ 6. Verify user can train     │
       │    this tier                 │
       │ 7. Return tier scope         │
       │                              │
       ▼                              │
┌──────────────────────┐             │
│ Training Coordinator │◄────────────┘
│   (Port 5600)        │
└──────┬───────────────┘
       │
       │ 8. Status: VALIDATING → EXTRACTING
       │
       │ 9. Queue extraction tasks
       │
       ├───────────────┬───────────────┐
       │               │               │
       ▼               ▼               ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│  GitHub     │ │ Confluence  │ │   Slack     │
│  Worker     │ │  Worker     │ │   Worker    │
└──────┬──────┘ └──────┬──────┘ └──────┬──────┘
       │               │               │
       │ 10. Extract data from sources │
       │     - Repos, issues, PRs      │
       │     - Pages, attachments      │
       │     - Messages, threads       │
       │                               │
       │ 11. Progress updates (0-100%) │
       │                               │
       └───────────────┴───────────────┘
                       │
                       ▼
         ┌──────────────────────┐
         │ Training Coordinator │
         │   (Port 5600)        │
         └──────┬───────────────┘
                │
                │ 12. Status: EXTRACTING → NORMALIZING
                │
                │ 13. Queue normalization tasks
                │
                ▼
         ┌──────────────────────┐
         │ Normalization Worker │
         └──────┬───────────────┘
                │
                │ 14. Convert to markdown
                │     - Standardize format
                │     - Extract metadata
                │     - Clean content
                │
                │ 15. Progress updates
                │
                ▼
         ┌──────────────────────┐
         │ Training Coordinator │
         │   (Port 5600)        │
         └──────┬───────────────┘
                │
                │ 16. Status: NORMALIZING → EMBEDDING
                │
                │ 17. Queue embedding tasks
                │
                ▼
         ┌──────────────────────┐
         │  Embedding Worker    │
         └──────┬───────────────┘
                │
                │ 18. Generate embeddings
                │     - Use sentence transformers
                │     - Create vectors (768 dim)
                │     - Extract keywords
                │
                │ 19. Progress updates
                │
                ▼
         ┌──────────────────────┐
         │ Training Coordinator │
         │   (Port 5600)        │
         └──────┬───────────────┘
                │
                │ 20. Status: EMBEDDING → STORING
                │
                │ 21. Send to MCP Store
                │
                ▼
         ┌──────────────────────┐
         │    MCP Store         │
         │   (Port 8008)        │
         └──────┬───────────────┘
                │
                │ 22. Store knowledge
                │     
                │     PostgreSQL:
                │     - Document metadata
                │     - Source information
                │     - Timestamps
                │
                │     Neo4j:
                │     - Knowledge graph nodes
                │     - Relationships
                │     - Entity links
                │
                │     ChromaDB:
                │     - Vector embeddings
                │     - Similarity search index
                │
                │     MinIO:
                │     - Original files
                │     - Attachments
                │
                │ 23. Confirm storage (10,000 docs)
                │
                ▼
         ┌──────────────────────┐
         │ Training Coordinator │
         │   (Port 5600)        │
         └──────┬───────────────┘
                │
                │ 24. Status: STORING → VALIDATING_RESULTS
                │
                │ 25. Validate training results
                │     - Check document count
                │     - Verify embeddings
                │     - Test search
                │
                │ 26. Status: VALIDATING_RESULTS → COMPLETED
                │
                │ 27. Log training metrics
                │
                ▼
         ┌──────────────────────┐
         │     MCP Logs         │
         │   (Port 8011)        │
         └──────┬───────────────┘
                │
                │ 28. Record training event
                │     - Duration: 15 minutes
                │     - Documents: 10,000
                │     - Sources: GitHub, Confluence
                │     - Status: SUCCESS
                │
                ▼
         ┌──────────────────────┐
         │ Training Coordinator │
         │   (Port 5600)        │
         └──────┬───────────────┘
                │
                │ 29. Return results
                ▼
         ┌──────────────────┐
         │   MCP Gateway    │
         │   (Port 8001)    │
         └──────┬───────────┘
                │
                │ 30. Format response
                ▼
         ┌──────────────┐
         │     User     │
         └──────────────┘
                │
                │ Response:
                │ {
                │   "job_id": "JOB-001",
                │   "status": "COMPLETED",
                │   "duration_seconds": 900,
                │   "documents_processed": 10000,
                │   "embeddings_generated": 10000,
                │   "sources": {
                │     "GITHUB": 6000,
                │     "CONFLUENCE": 4000
                │   }
                │ }
```

### Summary: Phase 2

**Time**: ~15-30 minutes (depends on data volume)  
**Services**: 6 services + workers  
**Result**: MCP populated with searchable knowledge

---

## 📦 Phase 3: MCP Storage & Packaging

### Overview
Package the trained MCP for distribution, versioning, and portability.

### Services Involved
- **MCP Gateway** (8001): Entry point
- **MCP Package Manager** (8012): Creates packages
- **MCP Store** (8008): Source of knowledge
- **MCP Registry** (8006): Catalogs packages
- **MinIO/S3**: Stores package binaries

### Detailed Flow

```
┌──────────────┐
│     User     │
└──────┬───────┘
       │
       │ 1. POST /api/v1/packages/export
       │    {
       │      "mcp_id": "mcp-acme-corp-dev-uuid",
       │      "name": "acme-corp-dev",
       │      "version": "1.0.0",
       │      "description": "ACME Corp dev environment MCP",
       │      "include_binaries": true
       │    }
       │
       ▼
┌──────────────────┐
│   MCP Gateway    │
│   (Port 8001)    │
└──────┬───────────┘
       │
       │ 2. Route to Package Manager
       │
       ▼
┌──────────────────────┐
│  MCP Package Manager │
│   (Port 8012)        │
└──────┬───────────────┘
       │
       │ 3. Create package metadata
       │    {
       │      "name": "acme-corp-dev",
       │      "version": "1.0.0",
       │      "created_at": "2024-10-07T10:30:00Z",
       │      "size_bytes": 0,
       │      "description": "..."
       │    }
       │
       │ 4. Request knowledge from Store
       │
       ▼
┌──────────────────┐
│   MCP Store      │
│   (Port 8008)    │
└──────┬───────────┘
       │
       │ 5. Export knowledge
       │    
       │    PostgreSQL:
       │    - Export metadata as JSON
       │    - Document index
       │    - Source mappings
       │
       │    Neo4j:
       │    - Export graph as Cypher
       │    - Entity relationships
       │    - Knowledge structure
       │
       │    ChromaDB:
       │    - Export vectors
       │    - Embedding index
       │    - Search metadata
       │
       │    MinIO:
       │    - Copy binary files
       │    - Attachments
       │    - Original documents
       │
       │ 6. Return exported data
       │    {
       │      "metadata": {...},
       │      "graph": {...},
       │      "vectors": {...},
       │      "binaries": [...]
       │    }
       │
       ▼
┌──────────────────────┐
│  MCP Package Manager │
│   (Port 8012)        │
└──────┬───────────────┘
       │
       │ 7. Build .mcp package file
       │    
       │    .mcp (TAR format):
       │    ├── metadata.json
       │    ├── knowledge/
       │    │   ├── documents.json
       │    │   ├── graph.cypher
       │    │   └── vectors.parquet
       │    └── binaries/
       │        ├── file1.pdf
       │        └── file2.docx
       │
       │ 8. Compress with zstandard
       │    - Original: 2.5 GB
       │    - Compressed: 850 MB
       │
       │ 9. Calculate checksum
       │    - SHA256: abc123...
       │
       │ 10. Upload to storage
       │
       ▼
┌──────────────────┐
│  MinIO/S3        │
└──────┬───────────┘
       │
       │ 11. Store package binary
       │     Path: packages/acme-corp-dev-1.0.0.mcp
       │     Size: 850 MB
       │
       │ 12. Return storage URL
       │
       ▼
┌──────────────────────┐
│  MCP Package Manager │
│   (Port 8012)        │
└──────┬───────────────┘
       │
       │ 13. Register in catalog
       │
       ▼
┌──────────────────┐
│  MCP Registry    │
│   (Port 8006)    │
└──────┬───────────┘
       │
       │ 14. Register package
       │     {
       │       "name": "acme-corp-dev",
       │       "version": "1.0.0",
       │       "size_bytes": 891289600,
       │       "checksum": "abc123...",
       │       "download_url": "s3://...",
       │       "status": "PUBLISHED",
       │       "metadata": {...}
       │     }
       │
       │ 15. Confirm registration
       │
       ▼
┌──────────────────────┐
│  MCP Package Manager │
│   (Port 8012)        │
└──────┬───────────────┘
       │
       │ 16. Return success
       │
       ▼
┌──────────────────┐
│   MCP Gateway    │
│   (Port 8001)    │
└──────┬───────────┘
       │
       │ 17. Format response
       │
       ▼
┌──────────────┐
│     User     │
└──────────────┘
       │
       │ Response:
       │ {
       │   "package_id": "pkg-001",
       │   "name": "acme-corp-dev",
       │   "version": "1.0.0",
       │   "size_mb": 850,
       │   "download_url": "http://...",
       │   "checksum": "abc123...",
       │   "status": "PUBLISHED"
       │ }
```

### Summary: Phase 3

**Time**: ~5-15 minutes (depends on MCP size)  
**Services**: 4 services  
**Result**: Portable .mcp package ready for distribution

---

## 🔍 Phase 4: MCP Loading & Usage

### Overview
Load a packaged MCP and use it to answer queries.

### Services Involved
- **MCP Gateway** (8001): Entry point
- **MCP Orchestrator** (8004): Query execution
- **MCP Retrieval** (8014): Context retrieval
- **MCP Tier Manager** (8013): Hierarchical access
- **MCP Store** (8008): Knowledge source
- **MCP Performance Store** (8009): Metrics tracking

### Detailed Flow

```
┌──────────────┐
│     User     │
└──────┬───────┘
       │
       │ 1. POST /api/v1/query
       │    {
       │      "query": "What are our API best practices?",
       │      "mcp_id": "mcp-acme-corp-dev-uuid",
       │      "context": {
       │        "user_id": "user-123",
       │        "session_id": "sess-456"
       │      }
       │    }
       │
       ▼
┌──────────────────┐
│   MCP Gateway    │
│   (Port 8001)    │
└──────┬───────────┘
       │
       │ 2. Authenticate user
       │ 3. Route to Orchestrator
       │
       ▼
┌──────────────────┐
│ MCP Orchestrator │
│   (Port 8004)    │
└──────┬───────────┘
       │
       │ 4. Parse query
       │ 5. Determine pattern: RAG
       │ 6. Calculate token budget: 8000 tokens
       │
       │ 7. Request user's tier context
       │
       ▼
┌──────────────────┐
│ MCP Tier Manager │
│   (Port 8013)    │
└──────┬───────────┘
       │
       │ 8. Identify user tier
       │    User "user-123" → Project tier
       │
       │ 9. Build tier hierarchy
       │    Client → Project → Team → Company → Ecosystem
       │
       │ 10. Return tier context
       │     {
       │       "tier_id": "project-acme-dev",
       │       "level": "Project",
       │       "access_scopes": ["Client", "Project", "Team"],
       │       "weights": {
       │         "Client": 0.5,
       │         "Project": 0.3,
       │         "Team": 0.2
       │       }
       │     }
       │
       ▼
┌──────────────────┐
│ MCP Orchestrator │
│   (Port 8004)    │
└──────┬───────────┘
       │
       │ 11. Request context retrieval
       │     Query: "API best practices"
       │     Tiers: [Client, Project, Team]
       │     Budget: 8000 tokens
       │
       ▼
┌──────────────────┐
│  MCP Retrieval   │
│   (Port 8014)    │
└──────┬───────────┘
       │
       │ 12. Hierarchical retrieval
       │
       │ For each tier (Client → Project → Team):
       │   - Query: "API best practices"
       │   - Request from MCP Store
       │
       ├──────────────────┐
       │                  │
       ▼                  │
┌──────────────────┐     │
│   MCP Store      │     │
│   (Port 8008)    │     │
└──────┬───────────┘     │
       │                 │
       │ 13. Search for relevant docs
       │     
       │     ChromaDB:
       │     - Vector similarity search
       │     - Query embedding: [0.23, 0.45, ...]
       │     - Top 20 results by cosine similarity
       │
       │     Neo4j:
       │     - Graph traversal
       │     - Find related entities
       │     - Follow relationships
       │
       │     PostgreSQL:
       │     - Fetch document metadata
       │     - Apply tier filters
       │     - Sort by relevance
       │
       │ 14. Return results per tier
       │     Client tier: 5 documents
       │     Project tier: 10 documents
       │     Team tier: 8 documents
       │
       ▼                 │
┌──────────────────┐    │
│  MCP Retrieval   │◄───┘
│   (Port 8014)    │
└──────┬───────────┘
       │
       │ 15. Apply context pruning
       │     - Relevance scores
       │     - Recency weights
       │     - Token budget management
       │     - Tier weights
       │
       │ 16. Prune to fit budget
       │     Total: 23 documents
       │     After pruning: 12 documents (7,800 tokens)
       │
       │ 17. Return refined context
       │     {
       │       "documents": [12 docs],
       │       "tokens_used": 7800,
       │       "tiers_included": ["Client", "Project", "Team"],
       │       "relevance_scores": [...]
       │     }
       │
       ▼
┌──────────────────┐
│ MCP Orchestrator │
│   (Port 8004)    │
└──────┬───────────┘
       │
       │ 18. Build LLM prompt
       │     System: "You are an assistant..."
       │     Context: [12 documents]
       │     Query: "What are our API best practices?"
       │
       │ 19. Execute LLM (RAG pattern)
       │     Model: gpt-4
       │     Temperature: 0.7
       │     Max tokens: 500
       │
       │ 20. Receive LLM response
       │     "Based on your documentation, here are
       │      the API best practices:
       │      1. Use RESTful design...
       │      2. Implement rate limiting...
       │      3. ..."
       │
       │ 21. Record execution metrics
       │
       ▼
┌──────────────────────┐
│ MCP Performance Store│
│   (Port 8009)        │
└──────┬───────────────┘
       │
       │ 22. Record execution
       │     {
       │       "query": "What are our API...",
       │       "pattern": "RAG",
       │       "duration_ms": 2340,
       │       "tokens_prompt": 7800,
       │       "tokens_completion": 420,
       │       "cost": 0.15,
       │       "success": true,
       │       "tiers_used": ["Client", "Project", "Team"]
       │     }
       │
       │ 23. Confirm recorded
       │
       ▼
┌──────────────────┐
│ MCP Orchestrator │
│   (Port 8004)    │
└──────┬───────────┘
       │
       │ 24. Return response
       │
       ▼
┌──────────────────┐
│   MCP Gateway    │
│   (Port 8001)    │
└──────┬───────────┘
       │
       │ 25. Format response
       │
       ▼
┌──────────────┐
│     User     │
└──────────────┘
       │
       │ Response:
       │ {
       │   "query": "What are our API best practices?",
       │   "response": "Based on your documentation...",
       │   "sources": [12 documents],
       │   "confidence": 0.92,
       │   "execution_time_ms": 2340,
       │   "tokens_used": 8220
       │ }
```

### Summary: Phase 4

**Time**: ~2-5 seconds per query  
**Services**: 6 services  
**Result**: AI-powered response with context from MCP

---

## 🔄 Complete End-to-End Flow

### The Full Journey: From Creation to Query

```
USER REQUEST
     │
     ▼
═══════════════════════════════════════════════════════════════
PHASE 1: CREATE (5 seconds)
═══════════════════════════════════════════════════════════════
     │
     │ Gateway (8001) → Provisioner (8003)
     │                      ↓
     │                 Tier Manager (8013)
     │                      ↓
     │                 MCP Store (8008)
     │                      ↓
     │                 Registry (8006)
     │                      ↓
     │                 Infrastructure (8007)
     │
     ▼
 ✅ MCP Created: "mcp-acme-corp-dev-uuid"
     │
     ▼
═══════════════════════════════════════════════════════════════
PHASE 2: TRAIN (15-30 minutes)
═══════════════════════════════════════════════════════════════
     │
     │ Gateway (8001) → Training Coordinator (5600)
     │                      ↓
     │                 [EXTRACTION WORKERS]
     │                  GitHub, Confluence, Slack
     │                      ↓
     │                 [NORMALIZATION WORKER]
     │                      ↓
     │                 [EMBEDDING WORKER]
     │                      ↓
     │                 MCP Store (8008)
     │                  ├─ PostgreSQL (metadata)
     │                  ├─ Neo4j (graph)
     │                  ├─ ChromaDB (vectors)
     │                  └─ MinIO (binaries)
     │                      ↓
     │                 Logs MCP (8011)
     │
     ▼
 ✅ MCP Trained: 10,000 documents indexed
     │
     ▼
═══════════════════════════════════════════════════════════════
PHASE 3: PACKAGE (5-15 minutes)
═══════════════════════════════════════════════════════════════
     │
     │ Gateway (8001) → Package Manager (8012)
     │                      ↓
     │                 MCP Store (8008)
     │                   [Export all knowledge]
     │                      ↓
     │                 Package Manager (8012)
     │                   [Build .mcp file]
     │                      ↓
     │                 MinIO/S3
     │                   [Store package]
     │                      ↓
     │                 Registry (8006)
     │                   [Register package]
     │
     ▼
 ✅ Package Published: acme-corp-dev-1.0.0.mcp (850 MB)
     │
     ▼
═══════════════════════════════════════════════════════════════
PHASE 4: QUERY & USE (2-5 seconds per query)
═══════════════════════════════════════════════════════════════
     │
     │ Gateway (8001) → Orchestrator (8004)
     │                      ↓
     │                 Tier Manager (8013)
     │                   [Identify user tier]
     │                      ↓
     │                 Retrieval (8014)
     │                   [Hierarchical search]
     │                      ↓
     │                 MCP Store (8008)
     │                  ├─ ChromaDB (vector search)
     │                  ├─ Neo4j (graph traversal)
     │                  └─ PostgreSQL (metadata)
     │                      ↓
     │                 Retrieval (8014)
     │                   [Context pruning]
     │                      ↓
     │                 Orchestrator (8004)
     │                   [Execute RAG pattern]
     │                      ↓
     │                 Performance Store (8009)
     │                   [Record metrics]
     │
     ▼
 ✅ Query Answered: "Based on your documentation..."
```

---

## 📊 Service Interaction Matrix

### Who Talks to Whom

| Service | Creates | Trains | Packages | Queries |
|---------|---------|--------|----------|---------|
| **Gateway** | ✅ Entry | ✅ Entry | ✅ Entry | ✅ Entry |
| **Provisioner** | ✅ Orchestrate | - | - | - |
| **Tier Manager** | ✅ Assign | ✅ Scope | - | ✅ Context |
| **Store** | ✅ Initialize | ✅ Store | ✅ Export | ✅ Search |
| **Registry** | ✅ Register | - | ✅ Catalog | - |
| **Infrastructure** | ✅ Monitor | - | - | - |
| **Training Coord** | - | ✅ Orchestrate | - | - |
| **Workers** | - | ✅ Execute | - | - |
| **Logs MCP** | - | ✅ Monitor | - | - |
| **Package Manager** | - | - | ✅ Build | - |
| **MinIO/S3** | - | ✅ Binaries | ✅ Packages | - |
| **Orchestrator** | - | - | - | ✅ Execute |
| **Retrieval** | - | - | - | ✅ Search |
| **Performance Store** | - | - | - | ✅ Metrics |

### Dependency Graph

```
                    ┌──────────────┐
                    │   Gateway    │
                    │   (8001)     │
                    └──────┬───────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
   ┌────────┐      ┌─────────────┐    ┌─────────────┐
   │Provision│      │  Training   │    │ Orchestrator│
   │  8003  │      │    5600     │    │    8004     │
   └────┬───┘      └──────┬──────┘    └──────┬──────┘
        │                 │                   │
        │                 │                   │
        ├─────────────────┼───────────────────┤
        │                 │                   │
        ▼                 ▼                   ▼
   ┌─────────────────────────────────────────────┐
   │            MCP Store (8008)                  │
   │  ┌─────────────────────────────────────┐    │
   │  │ PostgreSQL │ Neo4j │ ChromaDB │MinIO│    │
   │  └─────────────────────────────────────┘    │
   └─────────────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
   ┌────────┐      ┌─────────────┐    ┌─────────────┐
   │ Tier   │      │  Registry   │    │ Performance │
   │  Mgr   │      │    8006     │    │    Store    │
   │  8013  │      └─────────────┘    │    8009     │
   └────────┘                          └─────────────┘
```

---

## 🎯 Key Insights

### Timing Breakdown
```
CREATE:      ~5 seconds     (6 services)
TRAIN:       ~20 minutes    (6 services + workers)
PACKAGE:     ~10 minutes    (4 services)
QUERY:       ~3 seconds     (6 services)
────────────────────────────────────────
TOTAL:       ~30 minutes    (14 unique services)
```

### Service Usage Frequency
```
Per MCP Lifecycle:
- Gateway:           Used 4 times  (all phases)
- MCP Store:         Used 4 times  (all phases)
- Tier Manager:      Used 3 times  (create, train, query)
- Provisioner:       Used 1 time   (create only)
- Training Coord:    Used 1 time   (train only)
- Package Manager:   Used 1 time   (package only)
- Orchestrator:      Used 1 time   (query only)
```

### Most Critical Services
1. **MCP Store** - Central to all phases
2. **MCP Gateway** - Entry point for all operations
3. **Tier Manager** - Enables hierarchical access
4. **Orchestrator** - Powers query execution
5. **Retrieval** - Enables intelligent search

---

## 📞 Related Documentation

- **Visual Architecture**: [MCP_VISUAL_ARCHITECTURE.md](/MCP_VISUAL_ARCHITECTURE.md)
- **Ecosystem Architecture**: [MCP_ECOSYSTEM_ARCHITECTURE.md](/MCP_ECOSYSTEM_ARCHITECTURE.md)
- **Service READMEs**: [/services/](/services/)

---

**Version**: 1.0.0  
**Created**: October 7, 2025  
**Maintainer**: MCP Team

*Complete visual guide to the MCP lifecycle!* 🔄✨

