# MCP Workers - Training Pipeline

**Version:** 1.0.0  
**Type:** Celery-based Background Workers

Complete training pipeline workers for MCP knowledge extraction, normalization, and embedding.

## 🏗️ Architecture

### Worker Types

#### 1. **Extractors** (3 workers)
Extract raw data from various sources:
- **GitHub Extractor** - Repos, PRs, issues, commits
- **Confluence Extractor** - Pages, attachments
- **Jira Extractor** - Issues, projects, workflows

#### 2. **Normalizers** (2 workers)
Standardize and classify documents:
- **Markdown Normalizer** - Convert to clean markdown
- **Scope Classifier** - Classify into MCP tiers

#### 3. **Embedders** (3 workers)
Enrich with AI-generated data:
- **Vector Generator** - Create embeddings via Ollama
- **Auto Tagger** - Generate relevant tags
- **Entity Extractor** - Extract named entities

---

## 📊 Worker Pipeline

```
┌─────────────────────┐
│ Training            │
│ Coordinator         │
│ (Microservice)      │
└──────────┬──────────┘
           │ Creates job
           │ Dispatches tasks
           ▼
┌─────────────────────────────┐
│   Redis Task Queue          │
│   (Celery Broker)           │
└─────────────────────────────┘
           │
     ┌─────┴─────┬─────────────────┐
     │           │                 │
     ▼           ▼                 ▼
┌──────────┐ ┌──────────┐  ┌──────────┐
│ EXTRACT  │ │NORMALIZE │  │  EMBED   │
└──────────┘ └──────────┘  └──────────┘
     │           │                 │
     │           │                 │
  GitHub      Markdown         Vectors
  Conflue     Scope            Tags
  Jira        Classifier       Entities
     │           │                 │
     └───────────┴─────────────────┘
                 │
                 ▼
        ┌─────────────────┐
        │  Documents with │
        │  - Content      │
        │  - Embeddings   │
        │  - Tags         │
        │  - Entities     │
        │  - Tier         │
        └─────────────────┘
```

---

## 🚀 Getting Started

### 1. Install Dependencies

```bash
cd services/workers
pip install -r requirements.txt
```

### 2. Start Redis (Broker)

```bash
docker-compose up redis
```

### 3. Start Workers

```bash
# Start all workers
celery -A services.workers.celery_app worker --loglevel=info

# Or start specific worker pools
celery -A services.workers.celery_app worker -Q extraction --loglevel=info
celery -A services.workers.celery_app worker -Q normalization --loglevel=info
celery -A services.workers.celery_app worker -Q embedding --loglevel=info
```

### 4. Monitor Workers

```bash
# Flower web UI
celery -A services.workers.celery_app flower

# Or use CLI
celery -A services.workers.celery_app status
celery -A services.workers.celery_app inspect active
```

---

## 📝 Worker Details

### GitHub Extractor

**Task:** `extract_github`

**Configuration:**
```python
{
    "repos": ["owner/repo1", "owner/repo2"],
    "include_readme": True,
    "include_prs": True,
    "include_issues": True,
    "include_commits": False,
    "max_items_per_repo": 100,
    "github_token": "optional"
}
```

**Output:** List of `Document` objects with GitHub content

---

### Confluence Extractor

**Task:** `extract_confluence`

**Configuration:**
```python
{
    "url": "https://your-domain.atlassian.net/wiki",
    "username": "user@example.com",
    "api_token": "your-token",
    "spaces": ["SPACE1", "SPACE2"],
    "include_attachments": False,
    "max_pages_per_space": 100,
    "labels": ["documentation"]
}
```

**Output:** List of `Document` objects with Confluence pages

---

### Jira Extractor

**Task:** `extract_jira`

**Configuration:**
```python
{
    "url": "https://your-domain.atlassian.net",
    "username": "user@example.com",
    "api_token": "your-token",
    "projects": ["PROJ1", "PROJ2"],
    "include_issues": True,
    "include_comments": True,
    "max_issues_per_project": 100,
    "jql_filter": "status != Closed"
}
```

**Output:** List of `Document` objects with Jira issues

---

### Markdown Normalizer

**Task:** `normalize_markdown`

**Input:** List of `Document` objects

**Processing:**
- HTML → Markdown conversion
- Confluence markup → Markdown
- Header normalization
- Link formatting
- Code block preservation
- Whitespace cleanup

**Output:** Normalized `Document` objects

---

### Scope Classifier

**Task:** `classify_scope`

**Input:** List of `Document` objects

**Processing:**
- Analyzes content and metadata
- Scores for each tier (0-1)
- Assigns best matching tier

**Tiers:**
1. **Client** - Client-specific
2. **Project** - Project-specific
3. **Team** - Team-specific
4. **Company** - Company-wide
5. **Ecosystem** - Cross-company

**Output:** Documents with `tier` assigned

---

### Vector Generator

**Task:** `generate_vectors`

**Input:** List of `Document` objects

**Processing:**
- Prepares text (title + content + metadata)
- Calls Ollama embedding API
- Uses `nomic-embed-text` model
- Stores embedding vector

**Configuration:**
```python
{
    "documents": [...],
    "ollama_url": "http://localhost:11434"
}
```

**Output:** Documents with `embeddings` field

---

### Auto Tagger

**Task:** `auto_tag`

**Input:** List of `Document` objects

**Processing:**
- Creates tagging prompt
- Calls Ollama LLM
- Parses generated tags
- Merges with existing tags

**Configuration:**
```python
{
    "documents": [...],
    "ollama_url": "http://localhost:11434"
}
```

**Output:** Documents with enriched `tags`

---

### Entity Extractor

**Task:** `extract_entities`

**Input:** List of `Document` objects

**Processing:**
- Uses spaCy NLP
- Extracts named entities:
  - People, Organizations, Locations
  - Products, Dates
- Technical term extraction
- Entity deduplication

**Output:** Documents with `entities` list

---

## 🔄 Complete Pipeline Example

### Python API

```python
from celery import chain
from services.workers.extractors.github_extractor import extract_github_task
from services.workers.normalizers.markdown_normalizer import normalize_markdown_task
from services.workers.normalizers.scope_classifier import classify_scope_task
from services.workers.embedders.vector_generator import generate_vectors_task
from services.workers.embedders.auto_tagger import auto_tag_task
from services.workers.embedders.entity_extractor import extract_entities_task

# Create task chain
pipeline = chain(
    extract_github_task.s({
        "repos": ["anthropics/anthropic-sdk-python"],
        "include_readme": True,
        "include_prs": True,
    }),
    normalize_markdown_task.s(),
    classify_scope_task.s(),
    generate_vectors_task.s(),
    auto_tag_task.s(),
    extract_entities_task.s(),
)

# Execute pipeline
result = pipeline.apply_async()

# Monitor progress
while not result.ready():
    print(f"Status: {result.state}")
    time.sleep(5)

# Get final result
documents = result.get()
print(f"Processed {len(documents)} documents")
```

---

## 📦 Document Format

### Input Document (from Extractor)
```python
Document(
    doc_id="abc123",
    source="github",
    source_type="readme",
    title="Project README",
    content="# Project...",
    raw_content="# Project...",
    metadata={"repo": "owner/repo"},
    created_at=datetime.now(),
    author="john.doe",
    url="https://github.com/...",
)
```

### Output Document (after full pipeline)
```python
Document(
    doc_id="abc123",
    source="github",
    source_type="readme",
    title="Project README",
    content="# Project...",  # Normalized markdown
    raw_content="# Project...",
    metadata={
        "repo": "owner/repo",
        "normalized": True,
        "format": "markdown",
        "tier": "project",
        "classified": True,
        "embedding_model": "nomic-embed-text",
        "embedding_dim": 768,
        "has_embeddings": True,
        "auto_tagged": True,
        "entities_extracted": True,
        "entity_count": 15,
    },
    tier="project",  # Classified tier
    tags=["documentation", "api", "python"],  # Auto-generated
    entities=[  # Extracted entities
        {"text": "Python", "type": "TECH", "category": "technology"},
        {"text": "Anthropic", "type": "ORG", "category": "organization"},
    ],
    embeddings=[0.1, -0.2, ...],  # 768-dim vector
)
```

---

## 🔧 Configuration

### Environment Variables

```bash
# Redis/Celery
CELERY_BROKER_URL=redis://localhost:6379/8
CELERY_RESULT_BACKEND=redis://localhost:6379/8

# GitHub
GITHUB_TOKEN=ghp_...

# Confluence
CONFLUENCE_URL=https://your-domain.atlassian.net/wiki
CONFLUENCE_USERNAME=user@example.com
CONFLUENCE_API_TOKEN=...

# Jira
JIRA_URL=https://your-domain.atlassian.net
JIRA_USERNAME=user@example.com
JIRA_API_TOKEN=...

# Ollama
OLLAMA_URL=http://localhost:11434
```

---

## 🧪 Testing

```bash
# Run worker tests
pytest tests/workers/ -v

# Test individual worker
python -c "
from services.workers.extractors.github_extractor import extract_github_task
result = extract_github_task.delay({
    'repos': ['test/repo'],
    'include_readme': True
})
print(result.get())
"
```

---

## 📈 Performance

### Throughput
- **Extraction:** ~10-50 docs/min (API limited)
- **Normalization:** ~100-500 docs/min
- **Embedding:** ~10-30 docs/min (LLM limited)

### Scaling
- **Horizontal:** Add more worker processes
- **Vertical:** Increase worker concurrency
- **Queue-based:** Automatically distributes load

```bash
# Scale to 4 workers
celery -A services.workers.celery_app worker --concurrency=4
```

---

## 🎯 Integration with Training Coordinator

The Training Coordinator microservice orchestrates these workers:

1. **User creates job** → Coordinator validates
2. **Coordinator dispatches tasks** → Workers process
3. **Workers report progress** → Coordinator tracks
4. **Pipeline completes** → Coordinator aggregates results
5. **Results stored** → Vector DB + Graph DB

---

## 🏆 Summary

**8 Complete Workers:**
- 3 Extractors (GitHub, Confluence, Jira)
- 2 Normalizers (Markdown, Scope)
- 3 Embedders (Vector, Tagger, Entity)

**~2,400 LOC total**

**Production-ready:**
- Retry logic
- Error handling
- Progress tracking
- Scalable architecture

---

**Part of the MCP Training Pipeline** 🚀

