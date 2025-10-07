---
llm_metadata:
  document_type: planning
  content_focus: strategic
  platform:
    primary: mcp
    secondary: []
  status: archived
  created_date: '2024-09-01'
  archived_date: '2025-10-07'
  topics:
  - fastapi
  - python
  - redis
  - postgresql
  - docker
  - llm_orchestration
  - rag
  - embeddings
  concepts: []
  technologies: []
  services_mentioned: []
  semantic_summary: Planning document about strategic aspects of the mcp platform
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

# 🎯 **NEW SERVICES IMPLEMENTATION PLAN**

**Date:** October 6, 2025  
**Version:** 1.0  
**Status:** Planning Phase  

---

## 📊 **OVERVIEW**

Two critical new services to complete the MCP ecosystem based on planning documents review:

1. **MCP Orchestration Performance Store** (Port 5647)
2. **MCP Store** (Port 5648)

---

## 🆕 **SERVICE 1: MCP ORCHESTRATION PERFORMANCE STORE**

### **Purpose**
Track performance metrics, pattern scores, and prompts from all orchestration operations across the MCP ecosystem.

### **Key Responsibilities**
- ✅ Track pattern performance (latency, accuracy, cost, success rate)
- ✅ Store prompts sent to MCPs (permanent and temporary)
- ✅ Record final scores for each orchestration
- ✅ Maintain pattern usage history
- ✅ Enable performance analytics and optimization
- ✅ Feed data to adaptive learning system

### **Integration Points**

| Service | Integration Type | Purpose |
|---------|-----------------|---------|
| **MCP Orchestrator** | Tightly Coupled | Report pattern execution metrics |
| **MCP Composer** | Tightly Coupled | Report composition performance |
| **MCP Gateway** | Tightly Coupled | Report MCP query metrics |
| **MCP Interpreter** | Coupled | Report query parsing metrics |
| **MCP Store** | Connected | Link performance to MCP versions |
| **MCP Infrastructure** | Coupled | Coordinate state and metadata |
| **Redis** | Backend | Cache and real-time metrics |
| **TimescaleDB/InfluxDB** | Backend | Time-series data storage |

### **Data Model**

#### **OrchestrationExecution**
```python
{
    "execution_id": "uuid",
    "query": "str",
    "timestamp": "datetime",
    "mcp_id": "str",
    "mcp_version": "str",
    "pattern_used": "str",  # e.g., "chain-of-thought", "crag"
    "composition_id": "str?",  # If multi-MCP
    
    # Performance Metrics
    "latency_ms": int,
    "token_usage": int,
    "cost_cents": float,
    "success": bool,
    "error": "str?",
    
    # Quality Metrics
    "accuracy_score": float,  # 0-1
    "confidence": float,  # 0-1
    "hallucination_detected": bool,
    "citation_count": int,
    "user_satisfaction": float?,  # 0-1, from feedback
    
    # Context
    "prompt": "str",  # Full prompt sent
    "response": "str",  # Response received
    "context_length": int,
    "retrieved_sources": List[Dict],
    
    # Environment
    "environment": "str",  # "dev", "staging", "prod"
    "user_id": "str?",
    "session_id": "str?",
    
    # Metadata
    "tags": List[str],
    "metadata": Dict[str, Any]
}
```

#### **PatternPerformance**
```python
{
    "pattern_id": "str",
    "pattern_name": "str",
    "version": "str",
    
    # Aggregated Metrics (rolling windows)
    "total_executions": int,
    "success_rate": float,
    "avg_latency_ms": float,
    "p50_latency_ms": float,
    "p95_latency_ms": float,
    "p99_latency_ms": float,
    "avg_cost_cents": float,
    "avg_accuracy": float,
    "avg_confidence": float,
    
    # Time windows
    "last_hour": Dict,
    "last_day": Dict,
    "last_week": Dict,
    "last_month": Dict,
    
    # Trends
    "trend_direction": "str",  # "improving", "degrading", "stable"
    "anomalies_detected": List[Dict],
    
    # Updated
    "last_updated": "datetime"
}
```

### **API Endpoints**

```
POST /api/v1/performance/record
  - Record new orchestration execution

GET /api/v1/performance/executions
  - Query execution history
  - Filters: pattern, mcp_id, date range, success

GET /api/v1/performance/patterns/{pattern_id}
  - Get pattern performance metrics

GET /api/v1/performance/patterns/{pattern_id}/history
  - Get pattern performance over time

GET /api/v1/performance/mcps/{mcp_id}
  - Get MCP performance metrics

GET /api/v1/performance/analytics/trends
  - Get performance trends and insights

GET /api/v1/performance/analytics/anomalies
  - Get detected performance anomalies

POST /api/v1/performance/feedback
  - Record user feedback on execution

GET /api/v1/performance/prompts/{execution_id}
  - Retrieve stored prompt

GET /health
  - Health check
```

### **Architecture**

```
┌────────────────────────────────────────────────────┐
│  MCP Orchestration Performance Store (Port 5647)   │
├────────────────────────────────────────────────────┤
│                                                    │
│  ┌──────────────────────────────────────────┐    │
│  │  Presentation Layer (FastAPI)            │    │
│  │  - REST API                              │    │
│  │  - Metrics endpoints                     │    │
│  │  - Analytics endpoints                   │    │
│  └──────────────────────────────────────────┘    │
│                      ↓                             │
│  ┌──────────────────────────────────────────┐    │
│  │  Application Layer                       │    │
│  │  - Record execution use case             │    │
│  │  - Query performance use case            │    │
│  │  - Analytics use case                    │    │
│  │  - Anomaly detection use case            │    │
│  └──────────────────────────────────────────┘    │
│                      ↓                             │
│  ┌──────────────────────────────────────────┐    │
│  │  Domain Layer                            │    │
│  │  - OrchestrationExecution entity         │    │
│  │  - PatternPerformance entity             │    │
│  │  - Performance repository                │    │
│  │  - Analytics service                     │    │
│  └──────────────────────────────────────────┘    │
│                      ↓                             │
│  ┌──────────────────────────────────────────┐    │
│  │  Infrastructure Layer                    │    │
│  │  - Redis (real-time cache)               │    │
│  │  - TimescaleDB (time-series)             │    │
│  │  - Performance metrics calculator        │    │
│  │  - Anomaly detector                      │    │
│  └──────────────────────────────────────────┘    │
│                                                    │
└────────────────────────────────────────────────────┘
```

### **Implementation Steps**

1. **Phase 1: Foundation** (2 days)
   - [ ] Domain entities (OrchestrationExecution, PatternPerformance)
   - [ ] Repository interfaces
   - [ ] Basic infrastructure (Redis, TimescaleDB)

2. **Phase 2: Core Functionality** (3 days)
   - [ ] Record execution use case
   - [ ] Query performance use case
   - [ ] Performance calculator service
   - [ ] REST API endpoints

3. **Phase 3: Analytics** (2 days)
   - [ ] Analytics service
   - [ ] Trend detection
   - [ ] Anomaly detection
   - [ ] Aggregation pipelines

4. **Phase 4: Integration** (2 days)
   - [ ] MCP Orchestrator integration
   - [ ] MCP Composer integration
   - [ ] MCP Gateway integration
   - [ ] Dashboard integration

5. **Phase 5: Testing & Documentation** (1 day)
   - [ ] Unit tests
   - [ ] Integration tests
   - [ ] API documentation
   - [ ] Docker integration

**Total Estimate:** 10 days, ~1,500 LOC

---

## 🆕 **SERVICE 2: MCP STORE**

### **Purpose**
Centralized storage for created, trained, and compressed MCPs with versioning and comprehensive metadata.

### **Key Responsibilities**
- ✅ Store compressed MCP packages
- ✅ Version management (semantic versioning)
- ✅ Metadata tracking (training data, performance, capabilities)
- ✅ Export/import functionality
- ✅ MCP marketplace foundation
- ✅ Backup and archival

### **Integration Points**

| Service | Integration Type | Purpose |
|---------|-----------------|---------|
| **MCP Registry** | Tightly Coupled | Register MCPs and versions |
| **Training Coordinator** | Coupled | Store trained MCPs |
| **MCP Orchestrator** | Connected | Load MCPs for execution |
| **MCP Gateway** | Connected | Retrieve MCP instances |
| **Performance Store** | Connected | Link to performance data |
| **Redis** | Backend | Caching |
| **S3/MinIO** | Backend | Binary storage |
| **PostgreSQL** | Backend | Metadata |

### **Data Model**

#### **MCPPackage**
```python
{
    "package_id": "uuid",
    "name": "str",
    "slug": "str",  # URL-friendly name
    "description": "str",
    "version": "str",  # Semantic version
    
    # Classification
    "tier": "str",  # "ecosystem", "team", "company", "project", "client"
    "domain": List[str],  # ["backend", "frontend", "devops"]
    "tags": List[str],
    
    # Package Contents
    "storage_path": "str",  # S3/MinIO path
    "compressed_size_bytes": int,
    "uncompressed_size_bytes": int,
    "compression_format": "str",  # "tar.gz", "zip"
    "checksum": "str",  # SHA256
    
    # Training Info
    "training_job_id": "str",
    "training_data_sources": List[str],
    "training_completion_date": "datetime",
    "training_duration_minutes": int,
    "training_cost_cents": float,
    
    # Knowledge Stats
    "document_count": int,
    "total_tokens": int,
    "embedding_model": "str",
    "vector_count": int,
    "graph_node_count": int,
    "graph_edge_count": int,
    
    # Capabilities
    "supported_queries": List[str],
    "primary_use_cases": List[str],
    "languages": List[str],
    "confidence_threshold": float,
    
    # Performance Profile
    "avg_response_time_ms": float,
    "avg_accuracy": float,
    "usage_count": int,
    "success_rate": float,
    "performance_summary_id": "str",  # Link to Performance Store
    
    # Versioning
    "parent_version": "str?",
    "is_latest": bool,
    "is_deprecated": bool,
    "deprecation_reason": "str?",
    
    # Lifecycle
    "status": "str",  # "draft", "active", "deprecated", "archived"
    "created_at": "datetime",
    "updated_at": "datetime",
    "created_by": "str",
    
    # Dependencies
    "requires_mcps": List[str],  # Other MCP dependencies
    "compatible_with": List[str],  # Compatible MCP versions
    
    # Metadata
    "license": "str",
    "readme": "str",
    "changelog": "str",
    "metadata": Dict[str, Any]
}
```

#### **MCPVersion**
```python
{
    "version_id": "uuid",
    "package_id": "str",
    "version": "str",
    "version_major": int,
    "version_minor": int,
    "version_patch": int,
    
    # Changes
    "changes": List[str],
    "breaking_changes": List[str],
    "new_features": List[str],
    "bug_fixes": List[str],
    
    # Compatibility
    "backward_compatible": bool,
    "migration_required": bool,
    "migration_guide": "str?",
    
    # Release
    "release_date": "datetime",
    "release_notes": "str",
    "released_by": "str",
    
    # Statistics
    "download_count": int,
    "active_instances": int,
    
    # Links
    "previous_version": "str?",
    "next_version": "str?"
}
```

### **API Endpoints**

```
# Package Management
POST /api/v1/store/packages
  - Upload new MCP package

GET /api/v1/store/packages
  - List all packages
  - Filters: tier, domain, tags, status

GET /api/v1/store/packages/{package_id}
  - Get package details

PUT /api/v1/store/packages/{package_id}
  - Update package metadata

DELETE /api/v1/store/packages/{package_id}
  - Archive package

# Versioning
GET /api/v1/store/packages/{package_id}/versions
  - List all versions

GET /api/v1/store/packages/{package_id}/versions/{version}
  - Get specific version

POST /api/v1/store/packages/{package_id}/versions
  - Create new version

# Download/Export
GET /api/v1/store/packages/{package_id}/download
  - Download package binary

GET /api/v1/store/packages/{package_id}/export
  - Export package with metadata

POST /api/v1/store/packages/import
  - Import external package

# Search & Discovery
GET /api/v1/store/search
  - Search packages
  - Filters: query, tier, domain, tags

GET /api/v1/store/packages/{package_id}/similar
  - Find similar packages

GET /api/v1/store/trending
  - Get trending packages

# Statistics
GET /api/v1/store/packages/{package_id}/stats
  - Get package statistics

GET /api/v1/store/packages/{package_id}/performance
  - Get performance history (links to Performance Store)

# Marketplace
GET /api/v1/store/marketplace
  - Marketplace view of public packages

GET /api/v1/store/marketplace/{package_id}/reviews
  - Get package reviews

POST /api/v1/store/marketplace/{package_id}/reviews
  - Add package review

GET /health
  - Health check
```

### **Architecture**

```
┌────────────────────────────────────────────────────┐
│        MCP Store Service (Port 5648)               │
├────────────────────────────────────────────────────┤
│                                                    │
│  ┌──────────────────────────────────────────┐    │
│  │  Presentation Layer (FastAPI)            │    │
│  │  - REST API                              │    │
│  │  - Package management                    │    │
│  │  - Marketplace API                       │    │
│  └──────────────────────────────────────────┘    │
│                      ↓                             │
│  ┌──────────────────────────────────────────┐    │
│  │  Application Layer                       │    │
│  │  - Upload package use case               │    │
│  │  - Version management use case           │    │
│  │  - Download package use case             │    │
│  │  - Search packages use case              │    │
│  │  - Export/import use case                │    │
│  └──────────────────────────────────────────┘    │
│                      ↓                             │
│  ┌──────────────────────────────────────────┐    │
│  │  Domain Layer                            │    │
│  │  - MCPPackage entity                     │    │
│  │  - MCPVersion entity                     │    │
│  │  - Package repository                    │    │
│  │  - Version service                       │    │
│  │  - Compression service                   │    │
│  └──────────────────────────────────────────┘    │
│                      ↓                             │
│  ┌──────────────────────────────────────────┐    │
│  │  Infrastructure Layer                    │    │
│  │  - PostgreSQL (metadata)                 │    │
│  │  - S3/MinIO (binary storage)             │    │
│  │  - Redis (caching)                       │    │
│  │  - Compression utilities                 │    │
│  └──────────────────────────────────────────┘    │
│                                                    │
└────────────────────────────────────────────────────┘
```

### **Storage Strategy**

**Binary Storage (S3/MinIO):**
```
s3://mcp-store/
  ├── packages/
  │   ├── {tier}/
  │   │   ├── {domain}/
  │   │   │   ├── {package_id}/
  │   │   │   │   ├── {version}/
  │   │   │   │   │   ├── package.tar.gz
  │   │   │   │   │   ├── metadata.json
  │   │   │   │   │   └── checksums.txt
```

**Metadata Storage (PostgreSQL):**
- `mcp_packages` table
- `mcp_versions` table
- `mcp_tags` table
- `mcp_reviews` table
- `mcp_downloads` table (audit)

### **Implementation Steps**

1. **Phase 1: Foundation** (2 days)
   - [ ] Domain entities (MCPPackage, MCPVersion)
   - [ ] Repository interfaces
   - [ ] Storage infrastructure (S3/MinIO, PostgreSQL)

2. **Phase 2: Core Functionality** (3 days)
   - [ ] Upload/download use cases
   - [ ] Version management
   - [ ] Compression/decompression
   - [ ] REST API endpoints

3. **Phase 3: Search & Discovery** (2 days)
   - [ ] Search service
   - [ ] Similarity detection
   - [ ] Trending algorithm
   - [ ] Marketplace views

4. **Phase 4: Integration** (2 days)
   - [ ] MCP Registry integration
   - [ ] Training Coordinator integration
   - [ ] Performance Store linkage
   - [ ] Export/import workflows

5. **Phase 5: Testing & Documentation** (1 day)
   - [ ] Unit tests
   - [ ] Integration tests
   - [ ] API documentation
   - [ ] Docker integration

**Total Estimate:** 10 days, ~1,500 LOC

---

## 📊 **INTEGRATION ARCHITECTURE**

### **Service Interaction Flow**

```
┌──────────────────────────────────────────────────────────┐
│                   MCP Query Flow                         │
└──────────────────────────────────────────────────────────┘

1. Query arrives at MCP Interpreter
   ↓
2. MCP Orchestrator selects pattern
   ↓
3. Pattern execution via MCP Gateway
   ↓
4. MCP Gateway loads MCP from MCP Store ←──────┐
   ↓                                             │
5. Query execution on MCP                       │ (retrieves
   ↓                                             │  package)
6. Response returned                             │
   ↓                                             │
7. Performance recorded in Performance Store ───┘
   - Pattern used
   - Execution metrics
   - Prompt/response
   - MCP version used
```

### **Service Dependencies**

```
MCP Orchestration Performance Store (5647)
  ├─ Depends on: Redis, TimescaleDB
  ├─ Integrates with: MCP Orchestrator, Composer, Gateway, Interpreter
  └─ Connects to: MCP Store (link performance to versions)

MCP Store (5648)
  ├─ Depends on: PostgreSQL, S3/MinIO, Redis
  ├─ Integrates with: MCP Registry, Training Coordinator
  └─ Connects to: Performance Store (performance data linkage)
```

---

## 📋 **IMPLEMENTATION PRIORITIES**

### **Phase 3.5: New Services** (3 weeks)

**Week 1: MCP Orchestration Performance Store**
- Days 1-2: Foundation (entities, repositories)
- Days 3-5: Core functionality (recording, querying)
- Days 6-7: Analytics and integration

**Week 2: MCP Store**
- Days 1-2: Foundation (entities, storage)
- Days 3-5: Core functionality (upload, download, versioning)
- Days 6-7: Search and integration

**Week 3: Integration & Testing**
- Days 1-2: Cross-service integration
- Days 3-4: E2E testing
- Days 5-6: Performance optimization
- Day 7: Documentation and deployment

---

## 🎯 **SUCCESS CRITERIA**

### **MCP Orchestration Performance Store**
- ✅ Track 100% of orchestration executions
- ✅ Store all prompts and responses
- ✅ Real-time metrics (<100ms latency)
- ✅ Analytics dashboard ready
- ✅ Anomaly detection operational
- ✅ >90% test coverage

### **MCP Store**
- ✅ Store and version all MCPs
- ✅ Upload/download <5s for typical packages
- ✅ Search results <500ms
- ✅ Metadata complete for all packages
- ✅ Export/import functional
- ✅ >90% test coverage

---

## 📊 **UPDATED SYSTEM ARCHITECTURE**

```
Current: 48.6% complete
With new services: 55.7% complete

Phase 1: Foundation              ████████████████████ 100% ✅
Phase 2: Pattern Library         ████████████████████ 100% ✅
Phase 3: MCP Composer            ████████████████░░░░  89% ✅
Phase 3.5: New Services          ░░░░░░░░░░░░░░░░░░░░   0% 🔜
Phase 4: Dashboard UI            ░░░░░░░░░░░░░░░░░░░░   0% 🔜
Phase 5: Integration             ░░░░░░░░░░░░░░░░░░░░   0% 🔜
Phase 6: Advanced Features       ░░░░░░░░░░░░░░░░░░░░   0% 🔜
Phase 7: Production              ░░░░░░░░░░░░░░░░░░░░   0% 🔜
```

---

**Document Created:** October 6, 2025  
**Status:** ✅ **READY FOR IMPLEMENTATION**  
**Estimated Total:** 3 weeks, ~3,000 LOC  
**Priority:** High (Critical infrastructure services)
