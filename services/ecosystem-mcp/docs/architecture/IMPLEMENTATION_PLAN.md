---
title: "🎯 ECOSYSTEM-MCP IMPLEMENTATION PLAN"
service: "ecosystem-mcp"
category: "architecture"
tags: ['architecture', 'background', 'cache', 'caching', 'config', 'configuration', 'database', 'deployment', 'design', 'docker']
related: ['INDEX.md', 'architecture/OVERVIEW.md', 'CODE_REFERENCE.md', 'API_ENDPOINTS_COMPLETE.md']
status: "current"
last_updated: "2025-10-28"
audience: "developer"
difficulty: "advanced"
semantic_keywords: ['architecture', 'background', 'cache', 'caching', 'config']
llm_search_hints: ['what is 🎯 ecosystem-mcp implementation plan', 'how does 🎯 ecosystem-mcp implementation plan work', 'guide to 🎯 ecosystem-mcp implementation plan']
---

# 🎯 ECOSYSTEM-MCP IMPLEMENTATION PLAN

## 📋 Executive Summary

**Project**: Ecosystem MCP - Intelligent refactoring knowledge base with MCP integration  
**Duration**: 6-8 weeks (staged implementation)  
**Purpose**: Enable LLM-powered refactoring assistance using project documentation  
**Status**: 🟢 Phase 0 - Planning (In Progress)

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      ECOSYSTEM MCP SERVICE                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  MCP Server (FastAPI)                                           │
│  ├── Tools: analyze, compare, search, suggest                   │
│  ├── Resources: docs/{service}, patterns/{name}, metrics        │
│  └── Prompts: optimization guides, refactoring templates        │
│                           ▼                                      │
│  Model Router Service                                           │
│  ├── Ollama (Local - M4 Max optimized)                         │
│  ├── Cursor Free Models (Cloud)                                │
│  └── Claude via Cursor (Premium tasks)                         │
│                           ▼                                      │
│  Ingestion Orchestrator                                         │
│  ├── Mode 1: Current .md (~1 min)                              │
│  ├── Mode 2: Current code + .md (~5 min)                       │
│  ├── Mode 3: Current + .md history (~15 min)                   │
│  └── Mode 4: Full history (~1-3 hours)                         │
│                           ▼                                      │
│  Redis Streams (Queue)                                          │
│  └── Consumer Groups → Parallel Workers (8)                     │
│                           ▼                                      │
│  Processing Pipeline                                            │
│  ├── Parse (parallel)                                           │
│  ├── Normalize (parallel)                                       │
│  ├── Extract metadata (parallel)                               │
│  ├── Generate embeddings (parallel API calls)                  │
│  └── Write to storage (sequential)                             │
│                           ▼                                      │
│  Storage Layer                                                  │
│  ├── PostgreSQL (metadata, versions, git commits)              │
│  ├── ChromaDB (embeddings, vector search)                      │
│  └── Redis (cache, queues, pub/sub)                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Implementation Stages

### **Stage 1: Core MVP** (Week 1-2)
**Goal**: Working MCP server with basic RAG capabilities

#### Phase 0: Planning & Setup ✅ CURRENT
- [x] Architecture decisions documented
- [x] Technology stack finalized
- [ ] Development environment setup
- [ ] Resource requirements validated

#### Phase 1.1: Project Structure
**Duration**: 2 hours  
**Status**: 🔴 Not Started

**Tasks**:
- [ ] Create project directory structure
- [ ] Setup Python virtual environment
- [ ] Create requirements.txt with dependencies
- [ ] Setup Docker Compose for services
- [ ] Create Makefile for common operations

**Deliverables**:
```
ecosystem-mcp/
├── src/
│   ├── __init__.py
│   ├── server.py                    # MCP server entry point
│   ├── config.py                    # Configuration management
│   ├── models/                      # Data models (Pydantic)
│   ├── services/                    # Business logic
│   ├── storage/                     # Database layer
│   ├── ingestion/                   # Document processing
│   └── utils/                       # Utilities
├── tests/
├── docs/
├── docker/
├── scripts/
├── requirements.txt
├── docker-compose.yml
├── Makefile
└── README.md
```

**Acceptance Criteria**:
- Project installs cleanly
- All services start via docker-compose
- Tests can be run

---

#### Phase 1.2: Database Setup
**Duration**: 4 hours  
**Status**: 🔴 Not Started

**Tasks**:
- [ ] Design PostgreSQL schema
- [ ] Create migration scripts
- [ ] Setup ChromaDB with optimal configuration
- [ ] Create database connection pooling
- [ ] Implement repository pattern

**PostgreSQL Schema**:
```sql
-- Core tables
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_name VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    original_format VARCHAR(50) NOT NULL,
    normalized_content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    git_commit_sha VARCHAR(40),
    is_latest BOOLEAN DEFAULT TRUE,
    embedding_id UUID,
    metadata JSONB,
    content_hash VARCHAR(64) NOT NULL,
    UNIQUE(file_path, git_commit_sha)
);

CREATE TABLE document_versions (
    id SERIAL PRIMARY KEY,
    document_id UUID NOT NULL REFERENCES documents(id),
    version_number INTEGER NOT NULL,
    git_commit_sha VARCHAR(40) NOT NULL,
    commit_message TEXT,
    commit_date TIMESTAMP WITH TIME ZONE NOT NULL,
    content TEXT NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    embedding_id UUID,
    UNIQUE(document_id, version_number)
);

CREATE TABLE git_commits (
    sha VARCHAR(40) PRIMARY KEY,
    author VARCHAR(255),
    author_email VARCHAR(255),
    date TIMESTAMP WITH TIME ZONE NOT NULL,
    message TEXT,
    files_changed JSONB,
    stats JSONB
);

CREATE TABLE embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id),
    model VARCHAR(100) NOT NULL,
    dimensions INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    token_count INTEGER,
    cost_usd DECIMAL(10, 6),
    chroma_id VARCHAR(255) NOT NULL
);

CREATE TABLE ingestion_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mode VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    documents_processed INTEGER DEFAULT 0,
    documents_total INTEGER,
    error_message TEXT,
    metadata JSONB
);

CREATE TABLE model_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    model VARCHAR(100) NOT NULL,
    task_type VARCHAR(100) NOT NULL,
    input_tokens INTEGER,
    output_tokens INTEGER,
    cost_usd DECIMAL(10, 6),
    latency_ms INTEGER,
    success BOOLEAN
);

-- Indexes for performance
CREATE INDEX idx_documents_service ON documents(service_name);
CREATE INDEX idx_documents_latest ON documents(is_latest) WHERE is_latest = TRUE;
CREATE INDEX idx_documents_commit ON documents(git_commit_sha);
CREATE INDEX idx_versions_document ON document_versions(document_id);
CREATE INDEX idx_commits_date ON git_commits(date);
CREATE INDEX idx_embeddings_document ON embeddings(document_id);
CREATE INDEX idx_model_requests_timestamp ON model_requests(timestamp);
CREATE INDEX idx_model_requests_model ON model_requests(model);
```

**ChromaDB Configuration**:
```python
import chromadb
from chromadb.config import Settings

client = chromadb.PersistentClient(
    path="./data/chroma_db",
    settings=Settings(
        anonymized_telemetry=False,
        allow_reset=True
    )
)

collection = client.get_or_create_collection(
    name="ecosystem_docs",
    metadata={
        "hnsw:space": "cosine",
        "hnsw:construction_ef": 200,
        "hnsw:search_ef": 100,
        "hnsw:M": 16
    }
)
```

**Acceptance Criteria**:
- PostgreSQL starts and accepts connections
- All tables created successfully
- ChromaDB persists data across restarts
- Connection pooling works efficiently

---

#### Phase 1.3: Redis Streams Setup
**Duration**: 3 hours  
**Status**: 🔴 Not Started

**Tasks**:
- [ ] Setup Redis with persistence
- [ ] Create ingestion queue with consumer groups
- [ ] Implement producer/consumer pattern
- [ ] Add retry logic and dead letter queue
- [ ] Create monitoring for queue depth

**Redis Streams Design**:
```python
# Stream: ingestion_queue
# Consumer Group: workers
# Consumers: worker-1, worker-2, ..., worker-8

# Message format:
{
    "document_id": "uuid",
    "file_path": "/path/to/file",
    "content": "...",
    "metadata": {...},
    "attempt": 1,
    "priority": "normal"
}

# Streams:
# - ingestion_queue: New documents to process
# - embedding_queue: Documents ready for embedding
# - failed_queue: Failed documents (DLQ)
```

**Acceptance Criteria**:
- Messages persist across Redis restarts
- Consumer groups distribute work evenly
- Failed messages move to DLQ after 3 retries
- Queue metrics exposed via API

---

#### Phase 1.4: Model Router Implementation
**Duration**: 6 hours  
**Status**: 🔴 Not Started

**Tasks**:
- [ ] Setup Ollama connection (optimized for M4 Max)
- [ ] Implement Cursor model integration
- [ ] Create model selection decision tree
- [ ] Add cost tracking per model
- [ ] Implement fallback mechanism

**Model Router Design**:
```python
class ModelRouter:
    """
    Intelligent model routing based on task complexity.
    
    Decision tree:
    1. Metadata extraction → Ollama Llama 3.1 8B (local, fast)
    2. Simple summarization → Ollama Mistral 7B (local, fast)
    3. Code analysis → Cursor free model or Claude Haiku
    4. Pattern recognition → Claude Sonnet
    5. Complex refactoring → Claude Opus
    """
    
    def __init__(self):
        self.ollama = OllamaClient(base_url="http://localhost:11434")
        self.cursor = CursorClient()
        self.claude = ClaudeClient()
        self.cost_tracker = CostTracker()
    
    async def route_task(self, task: Task) -> ModelResponse:
        """Route task to optimal model with fallback."""
        model = self._select_model(task)
        
        try:
            response = await self._execute_task(model, task)
            self.cost_tracker.record(model, task, response)
            return response
        except Exception as e:
            # Fallback to next best model
            fallback = self._get_fallback(model)
            return await self._execute_task(fallback, task)
    
    def _select_model(self, task: Task) -> Model:
        """Select optimal model based on task characteristics."""
        # Task complexity scoring
        complexity = self._calculate_complexity(task)
        
        if complexity < 0.3 and self.ollama.is_available():
            return Model.OLLAMA_LLAMA3_8B
        elif complexity < 0.5:
            return Model.CURSOR_FREE
        elif complexity < 0.8:
            return Model.CLAUDE_SONNET
        else:
            return Model.CLAUDE_OPUS
    
    def _calculate_complexity(self, task: Task) -> float:
        """Calculate task complexity (0.0 to 1.0)."""
        score = 0.0
        
        # Input size
        if task.input_tokens > 8000:
            score += 0.3
        elif task.input_tokens > 4000:
            score += 0.2
        elif task.input_tokens > 2000:
            score += 0.1
        
        # Task type
        task_complexity = {
            "metadata_extraction": 0.1,
            "summarization": 0.2,
            "code_analysis": 0.5,
            "pattern_recognition": 0.7,
            "refactoring_suggestion": 0.9
        }
        score += task_complexity.get(task.type, 0.5)
        
        # Reasoning required
        if task.requires_reasoning:
            score += 0.2
        
        return min(score, 1.0)
```

**Ollama Configuration for M4 Max**:
```bash
# Pull optimal models for M4 Max
ollama pull llama3.1:8b-instruct-q8_0      # 8GB model, high quality
ollama pull mistral:7b-instruct-q8_0       # 7GB model, fast
ollama pull nomic-embed-text:latest        # Embeddings model

# Configure for M4 Max performance
export OLLAMA_NUM_PARALLEL=4
export OLLAMA_MAX_LOADED_MODELS=2
export OLLAMA_KEEP_ALIVE=30m
```

**Acceptance Criteria**:
- Ollama responds within 2 seconds for simple tasks
- Model selection is accurate and cost-effective
- Fallback works when primary model fails
- Cost tracking is accurate

---

#### Phase 1.5: Ingestion Pipeline (Mode 1 & 2)
**Duration**: 8 hours  
**Status**: 🔴 Not Started

**Tasks**:
- [ ] Implement document scanner (find files)
- [ ] Create parallel document parser
- [ ] Build metadata extractor
- [ ] Implement embedding generator
- [ ] Create ChromaDB writer (single writer pattern)
- [ ] Add progress tracking and resumption

**Pipeline Architecture**:
```python
class IngestionPipeline:
    """
    Multi-stage ingestion pipeline with parallel processing.
    
    Stages:
    1. Discovery: Find files to process
    2. Queue: Push to Redis Streams
    3. Parse: Extract content (parallel, 8 workers)
    4. Normalize: Convert to markdown (parallel)
    5. Extract: Get metadata (parallel)
    6. Embed: Generate vectors (parallel API calls)
    7. Write: Store in databases (sequential)
    """
    
    async def ingest_mode_1(self, repo_path: str) -> IngestionResult:
        """
        Mode 1: Current .md files only
        Fast ingestion for quick start (~1-2 minutes)
        """
        # Stage 1: Discovery
        md_files = self._find_markdown_files(repo_path)
        logger.info(f"Found {len(md_files)} markdown files")
        
        # Stage 2: Queue for processing
        await self._queue_documents(md_files, priority="normal")
        
        # Stage 3-7: Process via workers
        result = await self._process_queue()
        
        return result
    
    async def ingest_mode_2(self, repo_path: str) -> IngestionResult:
        """
        Mode 2: All current files (code + docs)
        Comprehensive current state (~5-10 minutes)
        """
        # Stage 1: Discovery
        files = self._find_all_files(
            repo_path,
            extensions=[".py", ".md", ".yaml", ".yml", ".json", ".txt"]
        )
        logger.info(f"Found {len(files)} files")
        
        # Stage 2: Queue with batching
        await self._queue_documents(files, batch_size=100)
        
        # Stage 3-7: Process via workers
        result = await self._process_queue()
        
        return result
    
    async def _process_queue(self) -> IngestionResult:
        """Process documents from Redis queue."""
        # Start worker pool
        workers = [
            Worker(worker_id=i, queue=self.redis)
            for i in range(8)
        ]
        
        # Process in parallel
        tasks = [w.run() for w in workers]
        await asyncio.gather(*tasks)
        
        # Wait for embedding queue to drain
        await self._wait_for_embeddings()
        
        return self._get_ingestion_stats()
```

**Worker Implementation**:
```python
class Worker:
    """
    Ingestion worker that processes documents from Redis queue.
    """
    
    async def run(self):
        """Main worker loop."""
        while True:
            # Read from Redis Streams
            messages = await self.redis.xreadgroup(
                groupname="workers",
                consumername=f"worker-{self.worker_id}",
                streams={"ingestion_queue": ">"},
                count=1,
                block=1000
            )
            
            if not messages:
                break  # Queue empty
            
            for stream, message_list in messages:
                for message_id, data in message_list:
                    try:
                        await self._process_document(data)
                        await self.redis.xack("ingestion_queue", "workers", message_id)
                    except Exception as e:
                        await self._handle_error(message_id, data, e)
    
    async def _process_document(self, data: dict):
        """Process a single document."""
        # Stage 1: Parse
        parsed = await self.parser.parse(data["content"], data["file_path"])
        
        # Stage 2: Normalize
        normalized = await self.normalizer.normalize(
            parsed,
            original_format=data["metadata"]["format"]
        )
        
        # Stage 3: Extract metadata
        metadata = await self.metadata_extractor.extract(normalized)
        
        # Stage 4: Save to PostgreSQL
        doc_id = await self.db.save_document({
            "file_path": data["file_path"],
            "original_content": parsed.content,
            "normalized_content": normalized.markdown,
            "metadata": metadata,
            "git_commit_sha": data.get("git_commit_sha")
        })
        
        # Stage 5: Queue for embedding
        await self.redis.xadd(
            "embedding_queue",
            {
                "document_id": str(doc_id),
                "content": normalized.markdown,
                "metadata": json.dumps(metadata)
            }
        )
```

**Acceptance Criteria**:
- Mode 1 completes in under 2 minutes for 100 .md files
- Mode 2 completes in under 10 minutes for 1000 files
- Workers distribute load evenly
- Pipeline recovers from interruptions
- Progress is tracked and visible

---

#### Phase 1.6: MCP Server + REST API Implementation
**Duration**: 10 hours (increased from 8)  
**Status**: 🔴 Not Started

**Tasks**:
- [ ] Implement MCP protocol handlers (stdio-based)
- [ ] Create MCP tools (analyze, compare, search, suggest)
- [ ] Create MCP resources (docs, patterns, metrics)
- [ ] Create MCP prompts (optimization guides)
- [ ] **NEW**: Setup FastAPI REST API server
- [ ] **NEW**: Implement OpenAPI/Swagger documentation
- [ ] **NEW**: Create admin endpoints (job management, stats)
- [ ] **NEW**: Create search API endpoints
- [ ] **NEW**: Create health & metrics endpoints
- [ ] Add Cursor IDE configuration
- [ ] Test MCP integration
- [ ] **NEW**: Test REST API via Swagger UI

**MCP Server Implementation**:
```python
from mcp.server import Server
from mcp.types import Tool, Resource, Prompt, TextContent

app = Server("ecosystem-mcp")

@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools."""
    return [
        Tool(
            name="analyze_service",
            description="Analyze a service and provide refactoring recommendations",
            inputSchema={
                "type": "object",
                "properties": {
                    "service_name": {
                        "type": "string",
                        "description": "Name of the service to analyze"
                    },
                    "focus_areas": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Specific areas to focus on (optional)"
                    }
                },
                "required": ["service_name"]
            }
        ),
        Tool(
            name="compare_services",
            description="Compare a service with similar refactored services",
            inputSchema={
                "type": "object",
                "properties": {
                    "service_name": {"type": "string"},
                    "compare_to": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Services to compare against (optional)"
                    }
                },
                "required": ["service_name"]
            }
        ),
        Tool(
            name="search_documentation",
            description="Semantic search across all refactoring documentation",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    },
                    "service_filter": {
                        "type": "string",
                        "description": "Filter by service name (optional)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of results (default: 10)"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="suggest_optimizations",
            description="Get optimization suggestions based on service analysis",
            inputSchema={
                "type": "object",
                "properties": {
                    "service_name": {"type": "string"},
                    "current_phase": {
                        "type": "string",
                        "description": "Current refactoring phase"
                    }
                },
                "required": ["service_name"]
            }
        ),
        Tool(
            name="get_refactoring_pattern",
            description="Get refactoring pattern with examples from similar services",
            inputSchema={
                "type": "object",
                "properties": {
                    "pattern_name": {
                        "type": "string",
                        "description": "Pattern name (e.g., 'standard-endpoints', 'testing-strategy')"
                    },
                    "service_context": {
                        "type": "string",
                        "description": "Service context for tailored examples"
                    }
                },
                "required": ["pattern_name"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Execute MCP tool."""
    if name == "analyze_service":
        result = await analyze_service_handler(
            service_name=arguments["service_name"],
            focus_areas=arguments.get("focus_areas", [])
        )
        return [TextContent(type="text", text=result)]
    
    elif name == "search_documentation":
        results = await search_documentation_handler(
            query=arguments["query"],
            service_filter=arguments.get("service_filter"),
            limit=arguments.get("limit", 10)
        )
        return [TextContent(type="text", text=results)]
    
    elif name == "compare_services":
        comparison = await compare_services_handler(
            service_name=arguments["service_name"],
            compare_to=arguments.get("compare_to", [])
        )
        return [TextContent(type="text", text=comparison)]
    
    elif name == "suggest_optimizations":
        suggestions = await suggest_optimizations_handler(
            service_name=arguments["service_name"],
            current_phase=arguments.get("current_phase")
        )
        return [TextContent(type="text", text=suggestions)]
    
    elif name == "get_refactoring_pattern":
        pattern = await get_pattern_handler(
            pattern_name=arguments["pattern_name"],
            service_context=arguments.get("service_context")
        )
        return [TextContent(type="text", text=pattern)]

@app.list_resources()
async def list_resources() -> list[Resource]:
    """List available resources."""
    services = await get_all_services()
    
    resources = []
    
    # Documentation resources
    for service in services:
        resources.append(Resource(
            uri=f"ecosystem://docs/{service['name']}",
            name=f"{service['name']} Documentation",
            description=f"Complete refactoring documentation for {service['name']}",
            mimeType="text/markdown"
        ))
    
    # Pattern resources
    patterns = await get_all_patterns()
    for pattern in patterns:
        resources.append(Resource(
            uri=f"ecosystem://patterns/{pattern['name']}",
            name=pattern['display_name'],
            description=pattern['description'],
            mimeType="text/markdown"
        ))
    
    # Metrics resource
    resources.append(Resource(
        uri="ecosystem://metrics/overview",
        name="Ecosystem Metrics",
        description="Overall ecosystem refactoring metrics",
        mimeType="application/json"
    ))
    
    return resources

@app.read_resource()
async def read_resource(uri: str) -> str:
    """Read resource content."""
    if uri.startswith("ecosystem://docs/"):
        service_name = uri.split("/")[-1]
        return await get_service_documentation(service_name)
    
    elif uri.startswith("ecosystem://patterns/"):
        pattern_name = uri.split("/")[-1]
        return await get_pattern_documentation(pattern_name)
    
    elif uri == "ecosystem://metrics/overview":
        return await get_ecosystem_metrics()
```

**Cursor Configuration** (`.cursorrules` or workspace settings):
```json
{
  "mcp": {
    "servers": {
      "ecosystem-mcp": {
        "command": "python",
        "args": ["/Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp/src/server.py"],
        "env": {
          "DATABASE_URL": "postgresql://localhost:5432/ecosystem_mcp",
          "REDIS_URL": "redis://localhost:6379",
          "CHROMA_PATH": "./data/chroma_db"
        }
      }
    }
  }
}
```

**Acceptance Criteria**:
- MCP server starts and connects to Cursor
- All tools are callable from Cursor
- Resources are accessible
- Responses are fast (< 2 seconds)

---

### **Stage 2: Production-Ready** (Week 3-4)

#### Phase 2.1: Git History Integration
**Duration**: 6 hours  
**Status**: 🔴 Not Started

**Tasks**:
- [ ] Implement git history parser
- [ ] Create commit metadata extractor
- [ ] Build file version tracker
- [ ] Add commit-document linking
- [ ] Optimize for large repositories

**Git Service Implementation**:
```python
class GitService:
    """
    Git history integration for document versioning.
    """
    
    def __init__(self, repo_path: str):
        self.repo = git.Repo(repo_path)
        self.cache = GitCommitCache()
    
    async def get_file_history(self, file_path: str) -> list[GitCommit]:
        """
        Get complete history of a file (handles renames).
        """
        # Use --follow to track file renames
        commits = self.repo.git.log(
            "--follow",
            "--format=%H|%an|%ae|%at|%s",
            "--",
            file_path
        ).split("\n")
        
        history = []
        for commit_line in commits:
            if not commit_line:
                continue
            
            sha, author, email, timestamp, message = commit_line.split("|", 4)
            
            # Get file content at this commit
            try:
                content = self.repo.git.show(f"{sha}:{file_path}")
                content_hash = hashlib.sha256(content.encode()).hexdigest()
                
                history.append(GitCommit(
                    sha=sha,
                    author=author,
                    email=email,
                    date=datetime.fromtimestamp(int(timestamp)),
                    message=message,
                    file_path=file_path,
                    content=content,
                    content_hash=content_hash
                ))
            except git.GitCommandError:
                # File might have been renamed
                logger.warning(f"Could not get content for {file_path} at {sha}")
        
        return history
    
    async def get_files_at_commit(self, commit_sha: str) -> list[str]:
        """Get all files at a specific commit."""
        files = self.repo.git.ls_tree(
            "-r",
            "--name-only",
            commit_sha
        ).split("\n")
        return files
    
    async def get_commit_metadata(self, commit_sha: str) -> CommitMetadata:
        """Get detailed commit metadata."""
        if cached := self.cache.get(commit_sha):
            return cached
        
        commit = self.repo.commit(commit_sha)
        
        metadata = CommitMetadata(
            sha=commit_sha,
            author=commit.author.name,
            email=commit.author.email,
            date=datetime.fromtimestamp(commit.committed_date),
            message=commit.message,
            stats={
                "files_changed": commit.stats.total["files"],
                "insertions": commit.stats.total["insertions"],
                "deletions": commit.stats.total["deletions"]
            },
            files_changed=[item.a_path for item in commit.diff(commit.parents[0])]
            if commit.parents else []
        )
        
        self.cache.set(commit_sha, metadata)
        return metadata
```

**Acceptance Criteria**:
- Can retrieve complete file history
- Handles file renames correctly
- Processes 1000 commits in under 1 minute
- Commit metadata is cached efficiently

---

#### Phase 2.2: Document Versioning System
**Duration**: 6 hours  
**Status**: 🔴 Not Started

**Tasks**:
- [ ] Implement version comparison
- [ ] Create version diff generator
- [ ] Build version retrieval system
- [ ] Add version search capabilities
- [ ] Optimize storage for versions

**Version Manager**:
```python
class VersionManager:
    """
    Manage document versions linked to git commits.
    """
    
    async def create_version(
        self,
        document_id: UUID,
        content: str,
        git_commit: GitCommit
    ) -> DocumentVersion:
        """Create a new version of a document."""
        # Get current version number
        current_version = await self.db.get_latest_version(document_id)
        version_number = (current_version.version_number + 1) if current_version else 1
        
        # Check if content actually changed
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        if current_version and current_version.content_hash == content_hash:
            logger.info(f"Content unchanged for {document_id}, skipping version")
            return current_version
        
        # Create new version
        version = DocumentVersion(
            document_id=document_id,
            version_number=version_number,
            git_commit_sha=git_commit.sha,
            commit_message=git_commit.message,
            commit_date=git_commit.date,
            content=content,
            content_hash=content_hash
        )
        
        # Save to database
        await self.db.save_version(version)
        
        # Queue for embedding (if content changed significantly)
        if self._should_reembed(current_version, version):
            await self.embedding_queue.add(version)
        
        return version
    
    async def get_version_at_commit(
        self,
        document_id: UUID,
        commit_sha: str
    ) -> DocumentVersion:
        """Get document version at specific commit."""
        version = await self.db.get_version_by_commit(document_id, commit_sha)
        
        if not version:
            # Version not in database, retrieve from git
            doc = await self.db.get_document(document_id)
            content = await self.git.get_file_at_commit(
                doc.file_path,
                commit_sha
            )
            
            # Create version on-demand
            commit = await self.git.get_commit_metadata(commit_sha)
            version = await self.create_version(document_id, content, commit)
        
        return version
    
    async def compare_versions(
        self,
        document_id: UUID,
        v1: int,
        v2: int
    ) -> VersionDiff:
        """Generate diff between two versions."""
        version1 = await self.db.get_version(document_id, v1)
        version2 = await self.db.get_version(document_id, v2)
        
        # Generate unified diff
        diff = difflib.unified_diff(
            version1.content.splitlines(keepends=True),
            version2.content.splitlines(keepends=True),
            fromfile=f"v{v1}",
            tofile=f"v{v2}",
            lineterm=""
        )
        
        return VersionDiff(
            document_id=document_id,
            from_version=v1,
            to_version=v2,
            diff="".join(diff),
            summary=self._generate_diff_summary(version1, version2)
        )
```

**Acceptance Criteria**:
- Can retrieve any version of any document
- Diffs are accurate and readable
- Version queries are fast (< 100ms)
- Storage is optimized (deduplicated)

---

#### Phase 2.3: Mode 3 & 4 Ingestion
**Duration**: 8 hours  
**Status**: 🔴 Not Started

**Tasks**:
- [ ] Implement Mode 3 (current + .md history)
- [ ] Implement Mode 4 (full history)
- [ ] Add progress tracking for long runs
- [ ] Optimize for large repositories
- [ ] Add resumption capability

**Mode 3 & 4 Implementation**:
```python
async def ingest_mode_3(self, repo_path: str) -> IngestionResult:
    """
    Mode 3: Current files + complete .md history
    Duration: ~15-30 minutes
    Cost: ~$2-5 in embeddings
    """
    job_id = await self._create_ingestion_job("mode_3")
    
    try:
        # Step 1: Ingest all current files (Mode 2)
        logger.info("Step 1/3: Ingesting current files")
        await self.ingest_mode_2(repo_path)
        
        # Step 2: Get history of all .md files
        logger.info("Step 2/3: Analyzing .md file history")
        md_files = self._find_markdown_files(repo_path)
        
        total_versions = 0
        for md_file in md_files:
            history = await self.git.get_file_history(md_file)
            total_versions += len(history)
            
            # Process each version
            for commit in history:
                # Check if we already have this version
                if await self.db.version_exists(md_file, commit.sha):
                    continue
                
                # Queue for processing
                await self.redis.xadd("ingestion_queue", {
                    "file_path": md_file,
                    "content": commit.content,
                    "git_commit_sha": commit.sha,
                    "commit_message": commit.message,
                    "commit_date": commit.date.isoformat(),
                    "is_historical": "true"
                })
        
        logger.info(f"Step 3/3: Processing {total_versions} historical versions")
        
        # Step 3: Process queue
        result = await self._process_queue()
        
        await self._complete_ingestion_job(job_id, result)
        return result
        
    except Exception as e:
        await self._fail_ingestion_job(job_id, str(e))
        raise

async def ingest_mode_4(self, repo_path: str) -> IngestionResult:
    """
    Mode 4: Complete history of all files
    Duration: ~1-3 hours (depends on repo size)
    Cost: ~$10-50 in embeddings
    
    ⚠️ WARNING: Only run once, then use incremental!
    """
    job_id = await self._create_ingestion_job("mode_4")
    
    try:
        # Step 1: Get all commits (chronological)
        logger.info("Step 1/4: Analyzing git history")
        commits = await self.git.get_all_commits()
        logger.info(f"Found {len(commits)} commits")
        
        # Step 2: Process commits in batches
        logger.info("Step 2/4: Processing commits")
        batch_size = 100
        for i in range(0, len(commits), batch_size):
            batch = commits[i:i+batch_size]
            await self._process_commit_batch(batch)
            
            # Update progress
            progress = (i + len(batch)) / len(commits) * 100
            await self._update_job_progress(job_id, progress)
            
            logger.info(f"Processed {i+len(batch)}/{len(commits)} commits")
        
        # Step 3: Process document queue
        logger.info("Step 3/4: Processing documents")
        result = await self._process_queue()
        
        # Step 4: Build relationship graph
        logger.info("Step 4/4: Building relationship graph")
        await self._build_relationship_graph()
        
        await self._complete_ingestion_job(job_id, result)
        return result
        
    except Exception as e:
        await self._fail_ingestion_job(job_id, str(e))
        raise
```

**Acceptance Criteria**:
- Mode 3 completes in under 30 minutes
- Mode 4 can be resumed if interrupted
- Progress is visible and accurate
- Resource usage stays within limits

---

### **Stage 3: Advanced Features** (Week 5-6)

#### Phase 3.1: Advanced RAG Implementation
**Duration**: 8 hours  
**Status**: 🔴 Not Started

**Features**:
- [ ] Hybrid search (vector + keyword)
- [ ] Result reranking
- [ ] Context window optimization
- [ ] Multi-hop reasoning
- [ ] Citation tracking

---

#### Phase 3.2: Relationship Graph
**Duration**: 6 hours  
**Status**: 🔴 Not Started

**Features**:
- [ ] Service dependency graph
- [ ] Document relationship mapping
- [ ] Pattern usage tracking
- [ ] Evolution visualization

---

#### Phase 3.3: Fine-Tuning Framework (Documentation)
**Duration**: 8 hours  
**Status**: 🔴 Not Started

**Deliverables**:
- [ ] Fine-tuning strategy document
- [ ] Data preparation pipeline (documented)
- [ ] Training infrastructure design
- [ ] Evaluation framework
- [ ] Cost-benefit analysis

**Note**: Implementation is out of scope for MVP, but framework is documented for future use.

---

### **Stage 4: Production Deployment** (Week 7-8)

#### Phase 4.1: Monitoring & Observability
- [ ] Prometheus metrics
- [ ] Structured logging
- [ ] Health checks
- [ ] Admin dashboard

#### Phase 4.2: Performance Optimization
- [ ] Query optimization
- [ ] Caching strategy
- [ ] Connection pooling
- [ ] Resource tuning

#### Phase 4.3: Documentation
- [ ] API documentation
- [ ] Deployment guide
- [ ] Operations manual
- [ ] Case studies

---

## 📊 Success Metrics

### Stage 1 (MVP):
- [ ] Ingestion Mode 1: < 2 minutes for 100 .md files
- [ ] Ingestion Mode 2: < 10 minutes for 1000 files
- [ ] Search latency: < 500ms
- [ ] Embedding cost: < $10
- [ ] MCP response time: < 2 seconds

### Stage 2 (Production):
- [ ] Mode 3: < 30 minutes
- [ ] Mode 4: < 3 hours
- [ ] Search latency: < 100ms
- [ ] Uptime: > 99%
- [ ] Total embedding cost: < $50

---

## 🎯 Current Status

**Phase**: 0 - Planning  
**Progress**: 10% (Architecture defined, plan created)  
**Next Step**: Phase 1.1 - Create project structure

---

## 📅 Timeline

| Phase | Duration | Start Date | End Date | Status |
|-------|----------|------------|----------|--------|
| 0 - Planning | 2 days | Oct 10 | Oct 11 | 🟡 In Progress |
| 1.1 - Structure | 2 hours | TBD | TBD | 🔴 Not Started |
| 1.2 - Database | 4 hours | TBD | TBD | 🔴 Not Started |
| 1.3 - Redis | 3 hours | TBD | TBD | 🔴 Not Started |
| 1.4 - Model Router | 6 hours | TBD | TBD | 🔴 Not Started |
| 1.5 - Ingestion | 8 hours | TBD | TBD | 🔴 Not Started |
| 1.6 - MCP Server | 8 hours | TBD | TBD | 🔴 Not Started |
| **Stage 1 Total** | **~2 weeks** | | | |

---

## 🚨 Risk Register

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Embedding costs exceed budget | High | Medium | Cost tracking, daily limits |
| ChromaDB corruption | High | Low | Single writer pattern, backups |
| Ollama too slow | Medium | Low | Fallback to cloud models |
| Resource exhaustion | High | Medium | Resource budgeting, monitoring |
| Git history too large | Medium | Low | Incremental processing, caching |

---

## 📝 Notes

- M4 Max is optimal for Ollama (unified memory architecture)
- $50 embedding budget is sufficient for full repository history
- Redis Streams provides persistence and resumption
- PostgreSQL handles concurrent writes better than SQLite
- Single writer to ChromaDB prevents corruption
- Document versioning linked to git commits enables time travel

---

**Last Updated**: 2025-10-10  
**Version**: 1.0.0  
**Status**: Planning Phase

