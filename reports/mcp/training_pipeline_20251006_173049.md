# MCP TRAINING PIPELINE FLOW

**Generated:** 2025-10-06T17:30:49.300170  
**Purpose:** Complete training workflow from raw data to MCP deployment  

---

## 📋 PIPELINE OVERVIEW

```
┌──────────────────────────────────────────────────────────────────┐
│                   TRAINING PIPELINE STAGES                        │
└──────────────────────────────────────────────────────────────────┘

Stage 1: JOB CREATION
├─ Input: Training request (topic, sources, config)
├─ Process: Create job in Training Coordinator
├─ Output: Job ID, initial state (PENDING)
└─ Duration: <1s

                    ↓

Stage 2: EXTRACTION
├─ Workers: GitHub, Confluence, Jira, Wikipedia
├─ Process: Extract raw documents from sources
├─ Output: Raw documents (text, HTML, JSON)
├─ Metrics: Documents extracted, sources queried
└─ Duration: 5-30 minutes (depends on sources)

                    ↓

Stage 3: NORMALIZATION
├─ Workers: Markdown Normalizer, Scope Classifier
├─ Process: Convert to .md, classify tier
├─ Output: Normalized markdown documents
├─ Metrics: Conversion success rate, tier distribution
└─ Duration: 2-10 minutes

                    ↓

Stage 4: EMBEDDING
├─ Workers: Vector Generator, Auto Tagger, Entity Extractor
├─ Process: Create embeddings, tags, entities
├─ Output: Enriched documents with vectors
├─ Metrics: Embedding dimension, tag count, entity count
└─ Duration: 10-60 minutes (LLM-intensive)

                    ↓

Stage 5: STORAGE
├─ Targets: ChromaDB (vectors), Neo4j (graph)
├─ Process: Store embeddings and relationships
├─ Output: Persisted knowledge base
├─ Metrics: Documents stored, relationships created
└─ Duration: 1-5 minutes

                    ↓

Stage 6: MCP CREATION
├─ Process: Package knowledge into MCP instance
├─ Output: MCP package (registry entry)
├─ Metrics: Package size, version number
└─ Duration: <1 minute

                    ↓

Stage 7: DEPLOYMENT
├─ Process: Provision MCP via Provisioner
├─ Output: Running MCP instance (HOT state)
├─ Metrics: Startup time, health status
└─ Duration: 10-30 seconds

                    ↓

COMPLETE: MCP Ready for Queries
```

---

## 🔄 WORKER ORCHESTRATION

### Extraction Phase

```
Training Coordinator
        │
        ├─→ [SPAWN] GitHub Extractor
        │     └─→ Extract repos, PRs, issues
        │
        ├─→ [SPAWN] Confluence Extractor
        │     └─→ Extract pages, attachments
        │
        ├─→ [SPAWN] Jira Extractor
        │     └─→ Extract issues, projects
        │
        └─→ [SPAWN] Wikipedia Extractor
              └─→ Extract articles + crawl links
        
        [WAIT] All extractors complete
        [AGGREGATE] Combine results
        [TRANSITION] → Normalization Phase
```

### Normalization Phase

```
Training Coordinator
        │
        ├─→ [SPAWN] Markdown Normalizer
        │     └─→ Convert all docs to .md
        │
        └─→ [SPAWN] Scope Classifier
              └─→ Classify into tiers
        
        [WAIT] All normalizers complete
        [VALIDATE] Check quality
        [TRANSITION] → Embedding Phase
```

### Embedding Phase

```
Training Coordinator
        │
        ├─→ [SPAWN] Vector Generator
        │     └─→ Create embeddings via Ollama
        │
        ├─→ [SPAWN] Auto Tagger
        │     └─→ Generate tags via LLM
        │
        └─→ [SPAWN] Entity Extractor
              └─→ Extract named entities
        
        [WAIT] All embedders complete
        [ENRICH] Combine metadata
        [TRANSITION] → Storage Phase
```

---

## 📊 JOB STATE MACHINE

```
PENDING
   │
   │ (Worker allocated)
   ▼
SCHEDULED
   │
   │ (Extraction started)
   ▼
EXTRACTING
   │
   │ (Extraction complete)
   ▼
NORMALIZING
   │
   │ (Normalization complete)
   ▼
EMBEDDING
   │
   │ (Embedding complete)
   ▼
STORING
   │
   │ (Storage complete)
   ▼
PACKAGING
   │
   │ (Package created)
   ▼
DEPLOYING
   │
   │ (MCP deployed)
   ▼
COMPLETE
   │
   │ (Optional cleanup)
   ▼
ARCHIVED
```

**Failure States:**
- `EXTRACTION_FAILED` → Retry extraction
- `NORMALIZATION_FAILED` → Retry normalization
- `EMBEDDING_FAILED` → Retry embedding
- `STORAGE_FAILED` → Retry storage
- `FAILED` → Manual intervention required

---

## 🎯 CONFIGURATION EXAMPLE

```yaml
training_job:
  name: "machine-learning-mcp"
  topic: "Machine Learning"
  tier: "company"
  
  sources:
    github:
      repos:
        - "scikit-learn/scikit-learn"
        - "pytorch/pytorch"
      max_commits: 1000
    
    confluence:
      spaces:
        - "ML Team"
      max_pages: 500
    
    jira:
      projects:
        - "ML"
      max_issues: 1000
    
    wikipedia:
      topics:
        - "Machine Learning"
        - "Neural Networks"
      crawl_links: true
      max_depth: 2
      max_articles: 50
  
  normalization:
    format: "markdown"
    min_quality_score: 0.7
  
  embedding:
    model: "nomic-embed-text"
    dimension: 768
    batch_size: 32
  
  storage:
    vector_db: "chromadb"
    graph_db: "neo4j"
  
  deployment:
    auto_deploy: true
    replicas: 2
```

---

## 📈 PERFORMANCE METRICS

### Throughput
- **Extraction:** 100-500 docs/minute
- **Normalization:** 500-1000 docs/minute
- **Embedding:** 50-200 docs/minute (LLM bottleneck)
- **Storage:** 1000+ docs/minute

### Resource Usage
- **CPU:** 2-4 cores per worker
- **Memory:** 512MB-2GB per worker
- **Disk:** 100MB per 1000 documents
- **Network:** 10-100 MB/s

### Quality Metrics
- **Extraction Accuracy:** >95%
- **Normalization Success:** >98%
- **Embedding Quality:** Depends on model
- **Storage Integrity:** 100%

---

## 🔍 MONITORING & LOGGING

### Training Job Logs

```
[INFO] Job created: job-abc123
[INFO] Extraction started: 4 workers spawned
[INFO] GitHub Extractor: 234 documents extracted
[INFO] Confluence Extractor: 89 pages extracted
[INFO] Jira Extractor: 156 issues extracted
[INFO] Wikipedia Extractor: 42 articles extracted
[INFO] Extraction complete: 521 total documents
[INFO] Normalization started
[INFO] Markdown Normalizer: 521 documents converted
[INFO] Scope Classifier: 521 documents classified
[INFO] Normalization complete: 100% success rate
[INFO] Embedding started
[INFO] Vector Generator: 521 embeddings created
[INFO] Auto Tagger: 2,130 tags generated
[INFO] Entity Extractor: 3,456 entities extracted
[INFO] Embedding complete
[INFO] Storage started
[INFO] ChromaDB: 521 documents stored
[INFO] Neo4j: 3,456 entities, 8,934 relationships stored
[INFO] Storage complete
[INFO] Packaging MCP: machine-learning-mcp v1.0.0
[INFO] Deploying MCP
[INFO] MCP deployed: COLD → WARMING → HOT
[INFO] Job complete: job-abc123 (Duration: 45m 23s)
```

---

## 🚀 QUICK START

### 1. Submit Training Job

```bash
curl -X POST http://training-coordinator:5600/api/v1/jobs \
  -H "Content-Type: application/json" \
  -d @training_config.json
```

### 2. Monitor Progress

```bash
curl http://training-coordinator:5600/api/v1/jobs/{job_id}
```

### 3. View Logs

```bash
curl http://mcp-logging:5650/api/v1/training/{job_id}/logs
```

### 4. Deploy MCP

```bash
curl -X POST http://mcp-provisioner:5400/api/v1/mcps/{mcp_id}/start
```

---

**Generated by MCP Report Generator**  
**Timestamp:** 2025-10-06T17:30:49.300170  
