---
title: "Ecosystem MCP - Database Schema Reference"
service: "ecosystem-mcp"
category: "architecture"
tags: ["database", "schema", "postgresql", "models", "tables"]
related: ["OVERVIEW.md", "../api/API_ENDPOINTS_COMPLETE.md"]
status: "current"
last_updated: "2025-10-28"
audience: "developer"
difficulty: "advanced"
---

# Ecosystem MCP - Database Schema Reference

**Complete PostgreSQL database schema documentation**

*Audited from actual implementation: 2025-10-28*

---

## 📊 Schema Overview

**Total Tables**: 15+ tables across 5 functional domains

**Databases**:
- **PostgreSQL**: Metadata, relationships, job tracking
- **ChromaDB**: Vector embeddings for semantic search
- **Redis**: Queues, cache, ephemeral data

---

## 1️⃣ Core Document Tables

### `documents`

**Purpose**: Main document storage with metadata and Git integration

```sql
CREATE TABLE documents (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Document Identity
    service_name VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    original_format VARCHAR(50) NOT NULL,
    
    -- Content
    original_content TEXT NOT NULL,
    normalized_content TEXT NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    
    -- Ingestion Mode Support
    ingestion_mode VARCHAR(20) NOT NULL DEFAULT 'git_history',
    version INTEGER NOT NULL DEFAULT 1,
    
    -- Git Integration (nullable for snapshot mode)
    git_commit_sha VARCHAR(40) REFERENCES git_commits(sha),
    git_date TIMESTAMP,
    git_author VARCHAR(255),
    git_author_email VARCHAR(255),
    git_commit_message TEXT,
    
    -- Metadata Schema Version
    metadata_version INTEGER NOT NULL DEFAULT 1,
    metadata_completeness JSONB,
    
    -- Timestamps (UTC)
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    -- Metadata
    document_metadata JSONB DEFAULT '{}',
    
    -- Indexes
    INDEX idx_documents_service (service_name),
    INDEX idx_documents_hash (content_hash),
    INDEX idx_documents_mode (ingestion_mode),
    INDEX idx_documents_git_sha (git_commit_sha),
    INDEX idx_documents_git_date (git_date)
);
```

**Key Features**:
- Supports multiple ingestion modes (snapshot, git_history, enriched, incremental)
- Tracks metadata completeness for each mode
- Content hash for deduplication
- JSONB for flexible metadata storage
- UTC timestamps for consistency

**Row Count** (typical): 10,000 - 100,000 documents

---

### `git_commits`

**Purpose**: Git commit history and file changes

```sql
CREATE TABLE git_commits (
    -- Primary Key
    sha VARCHAR(40) PRIMARY KEY,
    
    -- Commit Info
    message TEXT,
    author_name VARCHAR(255),
    author_email VARCHAR(255),
    commit_date TIMESTAMP NOT NULL,
    
    -- Repository Context
    repo_path TEXT NOT NULL,
    service_name VARCHAR(255),
    
    -- File Changes
    files_changed JSONB,  -- List of file paths
    stats JSONB,          -- Additions, deletions, etc.
    
    -- Parent Commits
    parent_shas JSONB,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Indexes
    INDEX idx_commits_date (commit_date),
    INDEX idx_commits_repo (repo_path),
    INDEX idx_commits_service (service_name)
);
```

**Key Features**:
- One commit can have multiple documents
- Files changed tracked as JSONB array
- Parent SHA tracking for commit graph

---

## 2️⃣ Ingestion & Job Management

### `ingestion_jobs`

**Purpose**: Track document ingestion jobs

```sql
CREATE TABLE ingestion_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Job Configuration
    mode VARCHAR(50) NOT NULL,  -- snapshot, git_history, enriched, incremental
    status VARCHAR(20) NOT NULL,  -- pending, running, completed, failed
    repo_path TEXT NOT NULL,
    
    -- Progress Tracking
    total_documents INTEGER DEFAULT 0,
    processed_documents INTEGER DEFAULT 0,
    failed_documents INTEGER DEFAULT 0,
    skipped_documents INTEGER DEFAULT 0,
    
    -- Performance Metrics
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    elapsed_seconds FLOAT,
    
    -- Error Tracking
    error_message TEXT,
    error_details JSONB,
    error_aggregation JSONB,  -- Aggregated error counts
    
    -- Metadata
    job_metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_jobs_status (status),
    INDEX idx_jobs_mode (mode),
    INDEX idx_jobs_created (created_at)
);
```

**Key Features**:
- Real-time progress tracking
- Error aggregation for debugging
- Performance metrics
- Support for multiple ingestion modes

---

### `processing_plans` *(Phase 1: Discovery)*

**Purpose**: Discovery and orchestration plans

```sql
CREATE TABLE processing_plans (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    repo_path TEXT NOT NULL,
    
    -- Discovery Results
    total_files INTEGER,
    supported_files INTEGER,
    unsupported_files INTEGER,
    estimated_time_seconds INTEGER,
    
    -- Execution
    status VARCHAR(20),  -- pending, running, completed, failed
    executed_at TIMESTAMP,
    
    -- Configuration
    batch_size INTEGER,
    parallel_workers INTEGER,
    
    -- Metadata
    plan_metadata JSONB,
    
    INDEX idx_plans_status (status),
    INDEX idx_plans_repo (repo_path)
);
```

---

## 3️⃣ Temporal Analysis Tables

### `timelines`

**Purpose**: Temporal analysis timelines for repositories

```sql
CREATE TABLE timelines (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Scope
    service_name VARCHAR(255) NOT NULL,
    repo_path TEXT NOT NULL,
    
    -- Time Range
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP NOT NULL,
    
    -- Confidence Tracking
    confidence_level VARCHAR(20) NOT NULL,  -- HIGH, MEDIUM, LOW, NONE
    confidence_metadata JSONB,
    
    -- Period Strategy
    period_strategy VARCHAR(50) DEFAULT 'adaptive',  -- monthly, quarterly, adaptive
    
    -- Metadata
    timeline_metadata JSONB,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(255),
    
    CONSTRAINT ck_timeline_date_range CHECK (start_date <= end_date),
    CONSTRAINT ck_confidence_level CHECK (confidence_level IN ('HIGH', 'MEDIUM', 'LOW', 'NONE')),
    
    INDEX idx_timelines_service (service_name),
    INDEX idx_timelines_confidence (confidence_level),
    INDEX idx_timelines_dates (start_date, end_date)
);
```

**Key Features**:
- Confidence-based operation
- Adaptive period generation
- Temporal metadata tracking

---

### `time_periods`

**Purpose**: Discrete time periods within timelines

```sql
CREATE TABLE time_periods (
    id UUID PRIMARY KEY,
    timeline_id UUID REFERENCES timelines(id) ON DELETE CASCADE,
    
    -- Period Info
    period_name VARCHAR(255) NOT NULL,  -- "Q1 2025", "Oct 2025"
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP NOT NULL,
    
    -- Documents in Period
    document_count INTEGER DEFAULT 0,
    document_ids JSONB,  -- Array of document UUIDs
    
    -- Statistics
    total_changes INTEGER,
    authors JSONB,  -- List of contributors
    
    -- Confidence
    confidence_level VARCHAR(20),
    confidence_score FLOAT,
    confidence_factors JSONB,
    
    -- Metadata
    period_metadata JSONB,
    
    CONSTRAINT ck_period_dates CHECK (start_date < end_date),
    
    INDEX idx_periods_timeline (timeline_id),
    INDEX idx_periods_dates (start_date, end_date),
    INDEX idx_periods_doc_count (document_count)
);
```

---

## 4️⃣ Analysis & Discovery Tables

### `repository_contexts`

**Purpose**: Repository-level context metadata

```sql
CREATE TABLE repository_contexts (
    id UUID PRIMARY KEY,
    repo_id VARCHAR(500) UNIQUE NOT NULL,
    repo_name VARCHAR(500),
    
    -- Technology Stack
    languages JSONB,  -- {"python": 120, "javascript": 45}
    frameworks JSONB,  -- {"fastapi": ["src/api/app.py"]}
    databases JSONB,  -- ["postgresql", "redis"]
    tools JSONB,  -- ["docker", "kubernetes"]
    deployment_platforms JSONB,
    
    -- Architecture
    architecture_type VARCHAR(50),  -- "microservices", "mvc"
    architecture_confidence FLOAT,
    service_count INTEGER,
    component_count INTEGER,
    layers JSONB,
    
    -- API Summary
    endpoint_count INTEGER DEFAULT 0,
    endpoints JSONB,
    has_rest_api BOOLEAN DEFAULT FALSE,
    has_graphql BOOLEAN DEFAULT FALSE,
    has_websocket BOOLEAN DEFAULT FALSE,
    
    -- Code Metrics
    total_files INTEGER,
    total_lines INTEGER,
    code_files INTEGER,
    test_files INTEGER,
    doc_files INTEGER,
    modularity_score FLOAT,
    
    -- Entry Points
    entry_points JSONB,
    main_flows JSONB,
    
    -- AI Summary
    brief_description TEXT,
    key_features JSONB,
    technical_highlights JSONB,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

---

### `detected_services`

**Purpose**: Detected microservices within repositories

```sql
CREATE TABLE detected_services (
    id UUID PRIMARY KEY,
    repo_id VARCHAR(500) REFERENCES repository_contexts(repo_id) ON DELETE CASCADE,
    service_name VARCHAR(200) NOT NULL,
    root_path VARCHAR(500),
    
    -- Service Details
    file_count INTEGER,
    entry_point VARCHAR(500),
    internal_dependencies JSONB,
    external_dependencies JSONB,
    
    -- Technology
    languages JSONB,
    frameworks JSONB,
    databases JSONB,
    
    -- API
    has_api BOOLEAN DEFAULT FALSE,
    endpoints JSONB,
    
    -- Deployment
    has_dockerfile BOOLEAN DEFAULT FALSE,
    has_k8s_config BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

---

## 5️⃣ Tree Context System

### `context_nodes`

**Purpose**: 3D tree structure for repository navigation

```sql
CREATE TABLE context_nodes (
    id UUID PRIMARY KEY,
    node_type VARCHAR(50) NOT NULL,  -- ROOT, SERVICE, MODULE, COMPONENT
    name VARCHAR(255) NOT NULL,
    path TEXT NOT NULL,
    
    -- Spatial Coordinates (3D tree)
    coordinates JSONB,  -- {x, y, z}
    depth INTEGER NOT NULL,
    
    -- Hierarchy
    parent_id UUID REFERENCES context_nodes(id) ON DELETE CASCADE,
    children_ids JSONB,  -- Array of child UUIDs
    
    -- Repository Context
    repo_id VARCHAR(500),
    service_name VARCHAR(255),
    
    -- Documents
    document_ids JSONB,  -- Documents attached to this node
    document_count INTEGER DEFAULT 0,
    
    -- Metadata
    node_metadata JSONB,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_nodes_type (node_type),
    INDEX idx_nodes_repo (repo_id),
    INDEX idx_nodes_depth (depth),
    INDEX idx_nodes_parent (parent_id)
);
```

---

## 6️⃣ Documentation Generation

### `documentation_runs`

**Purpose**: Track documentation generation jobs

```sql
CREATE TABLE documentation_runs (
    id UUID PRIMARY KEY,
    name VARCHAR(255),
    repo_path TEXT NOT NULL,
    
    -- Configuration
    sections INTEGER,
    questions_per_section INTEGER,
    documents_per_section INTEGER,
    
    -- Status
    status VARCHAR(20),  -- pending, running, completed, failed
    progress FLOAT,
    
    -- Results
    generated_documents JSONB,  -- Array of generated doc paths
    total_tokens INTEGER,
    total_cost_usd FLOAT,
    
    -- Performance
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    elapsed_seconds FLOAT,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

### `quality_checks`

**Purpose**: Document quality metrics

```sql
CREATE TABLE quality_checks (
    id UUID PRIMARY KEY,
    document_id UUID REFERENCES documents(id),
    
    -- Quality Scores
    completeness_score FLOAT,
    accuracy_score FLOAT,
    readability_score FLOAT,
    overall_score FLOAT,
    
    -- Issues
    issues JSONB,  -- Array of detected issues
    suggestions JSONB,  -- Improvement suggestions
    
    -- Check Metadata
    check_type VARCHAR(50),
    checker_version VARCHAR(20),
    
    -- Timestamps
    checked_at TIMESTAMP DEFAULT NOW()
);
```

---

## 7️⃣ LLM Usage Tracking

### `model_requests`

**Purpose**: Track LLM API usage and costs

```sql
CREATE TABLE model_requests (
    id UUID PRIMARY KEY,
    
    -- Request Info
    model_name VARCHAR(100) NOT NULL,
    provider VARCHAR(50) NOT NULL,  -- ollama, cursor, claude
    task_type VARCHAR(50),  -- embedding, generation, analysis
    
    -- Usage
    input_tokens INTEGER,
    output_tokens INTEGER,
    total_tokens INTEGER,
    cost_usd FLOAT,
    
    -- Performance
    latency_ms INTEGER,
    success BOOLEAN,
    error_message TEXT,
    
    -- Context
    endpoint VARCHAR(255),
    job_id UUID,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_requests_model (model_name),
    INDEX idx_requests_provider (provider),
    INDEX idx_requests_task_type (task_type),
    INDEX idx_requests_created (created_at)
);
```

---

## 🔗 Relationships & Constraints

### Foreign Key Relationships

```
documents
  └─> git_commits (git_commit_sha → sha)

timelines
  └─> time_periods (timeline_id → id)

repository_contexts
  └─> detected_services (repo_id → repo_id)

context_nodes
  └─> context_nodes (parent_id → id) [self-referential]

documentation_runs
  └─> generated documents (via JSONB references)
```

### Key Constraints

1. **Temporal Consistency**: `start_date <= end_date` on timelines and periods
2. **Confidence Levels**: Enum constraint on confidence fields
3. **Cascade Deletes**: ON DELETE CASCADE for hierarchical data
4. **Unique Constraints**: Repo IDs, commit SHAs unique
5. **Check Constraints**: Valid status values, date ranges

---

## 📈 Index Strategy

### High-Traffic Queries

1. **Document Search by Service**: `idx_documents_service`
2. **Git History Lookup**: `idx_documents_git_sha`, `idx_commits_date`
3. **Job Monitoring**: `idx_jobs_status`, `idx_jobs_created`
4. **Timeline Queries**: `idx_timelines_dates`, `idx_periods_dates`
5. **Tree Navigation**: `idx_nodes_type`, `idx_nodes_depth`

### JSONB Indexes (GIN)

```sql
-- For JSONB search
CREATE INDEX idx_documents_metadata_gin ON documents USING GIN (document_metadata);
CREATE INDEX idx_job_metadata_gin ON ingestion_jobs USING GIN (job_metadata);
```

---

## 💾 Storage Estimates

**Typical Installation** (50,000 documents):

| Table | Rows | Size | Description |
|-------|------|------|-------------|
| documents | 50,000 | ~500 MB | Main storage |
| git_commits | 10,000 | ~100 MB | Git history |
| ingestion_jobs | 500 | ~5 MB | Job history |
| timelines | 50 | <1 MB | Timeline defs |
| time_periods | 500 | ~10 MB | Period data |
| context_nodes | 5,000 | ~50 MB | Tree structure |
| repository_contexts | 10 | <1 MB | Repo metadata |
| model_requests | 100,000 | ~100 MB | LLM tracking |
| **Total** | | **~766 MB** | PostgreSQL |

**ChromaDB**: ~2-3 GB (embeddings)  
**Redis**: ~50-100 MB (ephemeral)

---

## 🔄 Migration Strategy

**Migration Files**: `src/storage/migrations/`

**Current Version**: 13 migrations

**Key Migrations**:
1. Initial schema (documents, git_commits)
2. Ingestion jobs
3. Timeline analysis tables
4. Tree context nodes
5. Discovery & analysis tables
6. Documentation generation
7. Quality checks
8. Model request tracking
9. Confidence tracking
10. Metadata versioning
11. Error aggregation
12. Retry infrastructure
13. Context nodes table

**Running Migrations**:
```bash
# Apply all migrations
python -m src.storage.migrations.run_migrations

# Rollback (if supported)
python -m src.storage.migrations.rollback
```

---

## 🔗 Related Documentation

- [Architecture Overview](OVERVIEW.md)
- [API Reference](../api/API_ENDPOINTS_COMPLETE.md)
- [Configuration Guide](../guides/CONFIGURATION.md)

---

**Last Updated**: 2025-10-28  
**Schema Version**: 13  
**Total Tables**: 15+  
**Status**: Production-Ready


