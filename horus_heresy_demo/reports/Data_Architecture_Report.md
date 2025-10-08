# 📊 Data Architecture Report: Horus Heresy Knowledge Base

**Generated:** 2025-10-08 15:21:15  
**System:** MCP Knowledge Base Ecosystem

---

## 🎯 Overview

This report details the data architecture supporting the Horus Heresy Knowledge Base demo, including data stores, relationships, and persistence strategies.

---

## 📁 Data Stores

### 1. doc-store (Port 5087)
**Purpose**: Primary document persistence and retrieval

**Schema**:
- `id`: Unique document identifier
- `content`: Full document text
- `metadata`: Document metadata (title, source, timestamps)
- `tags`: Categorical tags for organization
- `embeddings`: Vector embeddings for semantic search

**Operations**:
- POST /api/v1/documents - Ingest new documents
- GET /api/v1/documents - List/retrieve documents
- POST /api/v1/search - Semantic search

**Current State**:
- Documents stored: 207
- Status: ✅ Online

### 2. MCP Storage (Container-based)
**Purpose**: MCP instance data persistence

**Storage Model**:
- Container volumes for MCP state
- Training data associations
- Query history and context

**MCP Details**:
- MCP ID: mcp-horus-heresy-e97837f4
- Container ID: N/A

---

## 🔄 Data Flow

### Ingestion Flow

```
Source Data → Kafka Ingestion → doc-store → Training Coordinator → MCP
```

1. **Source Data**: Warhammer 40k Fandom Wiki pages
2. **Kafka Ingestion**: Content extraction and normalization
3. **doc-store**: Persistent storage with metadata
4. **Training Coordinator**: Associates documents with MCP
5. **MCP**: Trained model with query capability

### Query Flow

```
User Query → MCP Gateway → Trained MCP → doc-store (context) → Response
```

---

## 📦 Data Persistence

### Document Persistence
- **Storage**: PostgreSQL-backed doc-store
- **Indexing**: Full-text and semantic search indices
- **Retention**: Permanent storage
- **Backup**: Volume-based backups

### MCP Persistence
- **Storage**: Docker container volumes
- **State**: Model weights and configuration
- **Retention**: Until container destruction
- **Recovery**: Re-training from doc-store

---

## 🔗 Data Relationships

### Document-to-MCP Mapping
- Many documents → One MCP (training)
- One MCP → Many documents (queries)
- Documents tagged for categorical organization

### Service Dependencies
```
doc-store ←→ kafka-ingestion-service
doc-store ←→ mcp-training-coordinator
mcp-training-coordinator ←→ mcp-provisioner
mcp-gateway ←→ mcp-instances
```

---

## 📈 Scale Characteristics

### Current Scale
- Documents: 207 crawled, 207 ingested
- MCPs: 1 active instance
- Storage: ~414MB estimated

### Scalability
- **Horizontal**: Multiple doc-store replicas
- **Vertical**: Larger MCP containers (up to tier 5)
- **Distribution**: Geographic replication possible
- **Sharding**: Document sharding by category

---

## 🛡️ Data Quality

### Validation
- Schema validation on ingestion
- Content normalization
- Duplicate detection
- Tag consistency checks

### Metrics
- **Ingestion Success Rate**: 690.0%
- **Document Quality**: High (wiki-sourced)
- **Tag Coverage**: Comprehensive

---

**System:** MCP Knowledge Base Ecosystem  
**Architecture:** Microservices with centralized storage  
**Status:** Production-ready  
