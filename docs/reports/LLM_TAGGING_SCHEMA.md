# 🏷️ LLM Tagging Schema & Embedding Metadata

**Purpose:** Semantic metadata for archived documents to enable AI-powered search and retrieval  
**Date:** October 7, 2025  
**Format:** YAML frontmatter + inline metadata

---

## 📋 Metadata Schema

### Document Frontmatter Template

```yaml
---
# LLM Processing Metadata
llm_metadata:
  # Document Classification
  document_type: "architecture|planning|audit|report|guide|reference|session"
  content_focus: "technical|strategic|operational|analytical|historical"
  
  # Platform Association
  platform:
    primary: "document_analysis|mcp|shared|both"
    secondary: []
  
  # Implementation Status
  status: "implemented|documented|archived|superseded|historical"
  superseded_by: "path/to/current/doc.md"  # if applicable
  
  # Temporal Context
  created_date: "YYYY-MM-DD"
  archived_date: "YYYY-MM-DD"
  last_relevant_date: "YYYY-MM-DD"
  
  # Semantic Tags
  topics:
    - "architecture"
    - "microservices"
    - "ddd"
    # ...
  
  concepts:
    - "service_orchestration"
    - "event_driven_architecture"
    # ...
  
  technologies:
    - "python"
    - "fastapi"
    - "redis"
    # ...
  
  services_mentioned:
    - "orchestrator"
    - "llm-gateway"
    # ...
  
  # Relationships
  related_docs:
    active:
      - "../architecture/ECOSYSTEM_ARCHITECTURE.md"
    archived:
      - "./other-archived-doc.md"
  
  # Content Characteristics
  content_features:
    has_code_examples: true|false
    has_diagrams: true|false
    has_metrics: true|false
    has_decisions: true|false
  
  # Search & Retrieval
  keywords:
    - "keyword1"
    - "keyword2"
  
  semantic_summary: "One-sentence description for LLM context"
  
  # Quality & Relevance
  archive_reason: "superseded|consolidated|historical|redundant"
  historical_value: "high|medium|low"
  reference_value: "high|medium|low"

# Semantic Embeddings (for vector search)
semantic_embedding:
  model: "text-embedding-ada-002"  # or your preferred model
  vector_dimension: 1536
  embedding_date: "2025-10-07"
  # Note: Actual embedding vectors would be stored separately
  embedding_checksum: "sha256_hash_of_content"

# RAG Enhancement
rag_metadata:
  chunk_strategy: "semantic|sliding_window|paragraph|section"
  optimal_chunk_size: 512  # tokens
  context_window_size: 2048  # tokens
  retrieval_priority: "high|medium|low"
---
```

---

## 🎨 Tag Categories & Values

### Document Types

| Type | Description | Example |
|------|-------------|---------|
| `architecture` | System design documents | Architecture diagrams, ADRs |
| `planning` | Strategic planning docs | Roadmaps, implementation plans |
| `audit` | Assessment reports | Code audits, quality reports |
| `report` | Analysis and status reports | Progress reports, metrics |
| `guide` | How-to documentation | Setup guides, tutorials |
| `reference` | Reference materials | API docs, glossaries |
| `session` | Session summaries | Dev session notes, meetings |
| `decision` | Decision records | ADRs, tech choices |

### Content Focus

| Focus | Description |
|-------|-------------|
| `technical` | Implementation details, code, architecture |
| `strategic` | High-level planning, roadmaps, vision |
| `operational` | Deployment, monitoring, maintenance |
| `analytical` | Metrics, analysis, assessments |
| `historical` | Past decisions, evolution, context |

### Platform Tags

| Platform | Description |
|----------|-------------|
| `document_analysis` | Document Analysis & Planning Platform |
| `mcp` | Model Context Protocol Platform |
| `shared` | Shared infrastructure/concepts |
| `both` | Relevant to both platforms |

### Implementation Status

| Status | Description |
|--------|-------------|
| `implemented` | Was implemented, now archived |
| `documented` | Design only, never implemented |
| `archived` | Replaced by newer approach |
| `superseded` | Newer version exists |
| `historical` | Historical reference only |

### Archive Reasons

| Reason | Description |
|--------|-------------|
| `superseded` | Replaced by newer version |
| `consolidated` | Merged into another document |
| `historical` | Historical reference only |
| `redundant` | Duplicate content removed |
| `obsolete` | No longer relevant |

---

## 🔍 Semantic Tag Taxonomies

### Topic Tags (Architecture)
```
- microservices
- domain_driven_design
- clean_architecture
- cqrs
- event_sourcing
- service_mesh
- api_gateway
- bounded_contexts
```

### Topic Tags (Technical)
```
- fastapi
- python
- redis
- postgresql
- docker
- kubernetes
- langchain
- langgraph
- ollama
```

### Topic Tags (Operational)
```
- deployment
- monitoring
- observability
- health_checks
- logging
- metrics
- alerting
- scaling
```

### Topic Tags (LLM/AI)
```
- llm_orchestration
- prompt_engineering
- context_management
- rag
- embeddings
- vector_search
- mcp
- 5_tier_system
```

### Concept Tags
```
- service_discovery
- workflow_orchestration
- document_analysis
- consistency_checking
- planning_generation
- user_intelligence
- expert_discovery
- hot_swapping
```

---

## 📊 Embedding Strategy

### Content Chunking for RAG

**Semantic Chunking:**
```python
{
  "strategy": "semantic",
  "chunk_by": ["heading", "section", "logical_unit"],
  "target_size": 512,  # tokens
  "overlap": 50,  # tokens
  "preserve_context": true
}
```

**Chunk Metadata:**
```yaml
chunk_metadata:
  chunk_id: "doc_name_chunk_001"
  chunk_index: 1
  total_chunks: 15
  parent_document: "path/to/doc.md"
  section_hierarchy: ["Main Section", "Subsection"]
  semantic_type: "architecture_description|code_example|decision|metric"
```

### Embedding Models

**Recommended Models:**
- `text-embedding-ada-002` (OpenAI) - General purpose
- `all-MiniLM-L6-v2` (Open source) - Fast, local
- `instructor-xl` (Open source) - Instruction-based

**Storage Format:**
```json
{
  "document_id": "archive/planning/ECOSYSTEM_QUALITY_IMPROVEMENT_PLAN.md",
  "embeddings": [
    {
      "chunk_id": "chunk_001",
      "text": "Chunk text here...",
      "embedding": [0.123, -0.456, ...],  # 1536 dimensions
      "metadata": {...}
    }
  ]
}
```

---

## 🔗 Relationship Mapping

### Document Relationships

```yaml
relationships:
  supersedes:
    - "old_doc.md"
  superseded_by:
    - "../current/new_doc.md"
  related_to:
    - "sibling_doc.md"
  referenced_by:
    - "../guides/GUIDE.md"
  references:
    - "another_doc.md"
  merged_into:
    - "../consolidated/MASTER_DOC.md"
```

---

## 🎯 Use Cases

### 1. Semantic Search
```
Query: "How was service orchestration implemented?"
→ Retrieves archived architecture docs with orchestration concepts
→ Shows evolution of implementation
→ Links to current documentation
```

### 2. Historical Context
```
Query: "Why did we choose DDD architecture?"
→ Finds archived decision documents
→ Shows reasoning and alternatives considered
→ Links to current implementation
```

### 3. Evolution Tracking
```
Query: "Show evolution of MCP platform design"
→ Timeline of archived planning docs
→ Changes in approach over time
→ Current state vs original vision
```

### 4. Knowledge Retrieval
```
Query: "What services were part of original architecture?"
→ Retrieves early architecture docs
→ Compares with current state
→ Shows architectural evolution
```

---

## 📚 Implementation Guide

### Step 1: Add Frontmatter to Documents

**For each archived document:**
```bash
# Add YAML frontmatter to top of file
# Include all relevant metadata fields
# Use consistent taxonomy
```

### Step 2: Generate Embeddings

**Create embedding vectors:**
```python
# For each document/chunk:
# 1. Extract text content
# 2. Generate embedding
# 3. Store with metadata
# 4. Create searchable index
```

### Step 3: Create Master Index

**Build archive index:**
```yaml
# archive_index.yaml
documents:
  - path: "planning/ECOSYSTEM_QUALITY_IMPROVEMENT_PLAN.md"
    metadata: {...}
    embedding_id: "emb_001"
    search_tags: [...]
```

### Step 4: Enable RAG Retrieval

**Set up retrieval system:**
```
1. Vector database (Pinecone, Weaviate, ChromaDB)
2. Semantic search endpoint
3. Context injection for LLM queries
4. Historical reference system
```

---

## 🎨 Enhanced Archive Document Template

```markdown
---
llm_metadata:
  document_type: "architecture"
  content_focus: "technical"
  platform:
    primary: "document_analysis"
    secondary: []
  status: "superseded"
  superseded_by: "../architecture/ECOSYSTEM_ARCHITECTURE.md"
  created_date: "2024-09-15"
  archived_date: "2025-10-07"
  topics: ["microservices", "ddd", "service_mesh"]
  concepts: ["service_orchestration", "bounded_contexts"]
  technologies: ["python", "fastapi", "redis"]
  services_mentioned: ["orchestrator", "llm-gateway", "doc_store"]
  semantic_summary: "Early architecture design for microservices-based document analysis platform"
  archive_reason: "superseded"
  historical_value: "high"
  reference_value: "medium"

semantic_embedding:
  model: "text-embedding-ada-002"
  embedding_date: "2025-10-07"
  embedding_checksum: "abc123..."

rag_metadata:
  chunk_strategy: "semantic"
  optimal_chunk_size: 512
  retrieval_priority: "medium"
---

# [Original Document Title]

> **Archive Notice:** This document has been superseded by [new doc](link).  
> **Historical Value:** Contains valuable context about early design decisions.  
> **Semantic Tags:** #microservices #ddd #architecture

[Original document content...]

<!--
LLM Context:
This document represents the initial architecture planning phase for the
Document Analysis platform, showing the reasoning behind microservices adoption
and DDD implementation. Useful for understanding architectural evolution.

Key Concepts: service_orchestration, event_driven_architecture, ddd_implementation
Related Services: orchestrator, llm-gateway, analysis-service
-->
```

---

## 🚀 Benefits

### For AI/LLM Systems
- ✅ Semantic search across archived content
- ✅ Historical context for current decisions
- ✅ Evolution tracking
- ✅ Concept relationship mapping
- ✅ Knowledge graph construction

### For Developers
- ✅ Quick historical reference lookup
- ✅ Understanding of design evolution
- ✅ Context for current architecture
- ✅ Decision rationale access
- ✅ Pattern identification

### For RAG Systems
- ✅ High-quality retrieval chunks
- ✅ Proper context preservation
- ✅ Relevance ranking
- ✅ Source attribution
- ✅ Temporal awareness

---

## 📊 Validation

### Quality Checks
- [ ] All documents have frontmatter
- [ ] Consistent taxonomy used
- [ ] Relationships mapped
- [ ] Embeddings generated
- [ ] Search index created
- [ ] Retrieval tested

### Completeness
- [ ] 100% of archived docs tagged
- [ ] All categories covered
- [ ] Cross-references validated
- [ ] Embeddings for all chunks
- [ ] Master index complete

---

**Status:** Schema Defined ✅  
**Next:** Apply to all archived documents  
**Integration:** RAG system, semantic search, knowledge graph

