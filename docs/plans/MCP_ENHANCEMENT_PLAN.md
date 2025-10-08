# MCP Lifecycle Demo - Enhancement Plan

**Date**: October 7, 2025  
**Status**: Implementation Planning

---

## 🎯 Objectives

### 1. Fix MCP Instance Deployment (Root Cause)
**Problem**: Evergreen docs contain synthetic content because MCP instances aren't actually running.

**Current State**:
- `mcp-provisioner` creates metadata and saves to Redis
- **No Docker container is actually deployed**
- `mcp-gateway` returns 503 "No available instances"
- All queries fall back to synthetic content

**Solution**:
- Extend `provision_mcp_use_case.py` to deploy Docker containers
- Use Docker Python SDK to create/start MCP containers
- Register running containers with gateway
- Implement health checks and startup verification

---

### 2. Enhanced Document Ingestion with Timestamps
**Problem**: Documents lack temporal context for versioning and freshness analysis.

**Required**:
- Extract `created_at` and `updated_at` from document metadata
- Parse timestamps from:
  - File system metadata (`os.stat()`)
  - Git commit history
  - Document frontmatter (YAML/Markdown headers)
  - API responses (GitHub, Confluence)
- Store timestamps as vector metadata for ChromaDB queries
- Enable time-based retrieval and freshness scoring

**Implementation**:
```python
{
    "document_id": "doc_123",
    "content": "...",
    "metadata": {
        "created_at": "2025-10-01T10:30:00Z",
        "updated_at": "2025-10-07T14:20:00Z",
        "last_commit": "abc123",
        "author": "user@example.com"
    }
}
```

---

### 3. GitHub Integration for Documentation Discovery
**Problem**: Need to ingest documentation directly from GitHub repos, branches, and PRs.

**Capabilities Needed**:

#### A. Commit Message Normalization
- Fetch commit history for repo/branch/PR
- Extract commit messages, diffs, and metadata
- Normalize into structured documents:
  ```markdown
  # Commit: <hash>
  **Author**: <name>  
  **Date**: <timestamp>  
  **Files Changed**: <count>
  
  ## Message
  <commit message>
  
  ## Changes
  <summary of diff>
  ```

#### B. Documentation File Discovery
- Traverse commit diffs to identify documentation files:
  - `*.md`, `*.rst`, `*.txt`, `README.*`, `CHANGELOG.*`
  - Files in `/docs`, `/documentation`, `/wiki` directories
- Track file changes (added, modified, deleted)
- Ingest full content of discovered documentation files
- Link to commit that modified them

#### C. PR-Specific Ingestion
- Fetch PR title, description, comments
- Identify documentation changes in PR diff
- Create summary document for the PR context

**Integration Points**:
- Use existing `mock-data-generator` GitHub client
- Extend with GitHub API v3 for commits, diffs, files
- Store in `doc_store` with GitHub-specific metadata

---

### 4. Code File Analysis with code-analyzer Service
**Problem**: Code files need to be analyzed and documented automatically.

**Capabilities Needed**:

#### A. Code Analysis via code-analyzer Service
Use `POST /api/v1/analysis/analyze` endpoint:
- **Input**: Source code content, language, file path
- **Output**:
  - Functions/classes/methods identified
  - API endpoints extracted
  - Comments and docstrings
  - Security issues
  - Style violations
  - Quality metrics

#### B. Generate Documentation from Analysis
For each code file, generate:
```markdown
# File: services/mcp-provisioner/main.py

**Language**: Python  
**Lines**: 250  
**Quality Score**: 85/100  
**Last Updated**: 2025-10-07

## Overview
<AI-generated summary of what the file does>

## Functions
- `provision_mcp(request)`: Creates and provisions MCP instance
  - **Parameters**: ProvisionRequestDTO
  - **Returns**: OperationResultDTO
  - **Description**: <extracted from docstring>

## API Endpoints
- POST `/api/v1/mcps` - Create new MCP instance

## Dependencies
- FastAPI, Redis, Docker SDK

## Security Considerations
- <list security issues found>

## Code Quality
- <list style violations>
- <complexity metrics>
```

#### C. Batch Processing for Repositories
- Identify all code files in a repository
- Batch submit to code-analyzer (parallel processing)
- Generate comprehensive documentation for entire codebase
- Cross-reference functions and dependencies

---

## 📋 Implementation Plan

### Phase 1: Fix MCP Deployment (Priority 1) ✅
**Goal**: Get real MCP instances running so queries return real content.

1. Add Docker SDK to `mcp-provisioner` dependencies
2. Implement `_deploy_container()` method in `provision_mcp_use_case.py`
3. Create Docker container from `image_name` with:
   - Environment variables from request
   - Resource limits (memory, CPU)
   - Port mapping
   - Network connectivity
4. Wait for health check to pass
5. Register running instance with gateway
6. Update instance status to `HOT`

**Success Criteria**:
- `docker ps` shows running MCP container
- Health endpoint responds 200 OK
- Gateway queries return real MCP responses
- Evergreen docs contain actual knowledge from training

---

### Phase 2: Timestamp Tracking (Priority 2)
**Goal**: Add temporal metadata to all ingested documents.

1. Extend `ingest_documents()` in `demo_mcp_lifecycle.py`:
   - Read file system timestamps
   - Parse Git commit dates if available
   - Extract frontmatter timestamps
2. Include timestamps in ingestion payload
3. Update `kafka-ingestion-service` to preserve timestamps
4. Store in vector DB metadata for time-based queries

**Success Criteria**:
- All documents have `created_at` and `updated_at`
- Can query "documents updated in last 7 days"
- Reports show document freshness metrics

---

### Phase 3: GitHub Commit Ingestion (Priority 3)
**Goal**: Ingest commit history and documentation files from GitHub.

1. Create `GitHubDocumentCollector` class:
   ```python
   class GitHubDocumentCollector:
       async def collect_commits(repo, branch) -> List[CommitDocument]
       async def collect_documentation_files(repo, branch) -> List[DocFile]
       async def analyze_pr(repo, pr_number) -> PRDocument
   ```

2. Integrate with `mock-data-generator` or create new helper
3. Normalize commit messages into documents
4. Identify and ingest doc files from commits
5. Create PR summary documents

**Success Criteria**:
- Can specify GitHub repo and ingest all commits
- All `*.md` files from repo are ingested
- PR context is captured in documents

---

### Phase 4: Code Analysis Integration (Priority 4)
**Goal**: Analyze code files and generate detailed documentation.

1. Create `CodeDocumentGenerator` class:
   ```python
   class CodeDocumentGenerator:
       async def analyze_file(file_path, content) -> CodeAnalysis
       async def generate_documentation(analysis) -> Document
       async def batch_analyze_repository(repo_path) -> List[Document]
   ```

2. For each code file:
   - Call `code-analyzer` service
   - Extract functions, classes, endpoints
   - Parse comments and docstrings
   - Generate comprehensive documentation
3. Ingest generated documentation into MCP

**Success Criteria**:
- Code files result in detailed documentation
- Functions and APIs are documented
- Can query "what does file X do?"
- MCP can answer code-specific questions

---

### Phase 5: End-to-End Testing (Priority 5)
**Goal**: Verify complete workflow with all enhancements.

**Test Scenarios**:
1. Ingest local docs (50 files) ✅
2. Ingest GitHub repo (commits + docs + code)
3. Query MCP with real running instance
4. Generate evergreen docs with real content
5. Verify timestamp-based queries work
6. Validate code documentation quality

**Success Criteria**:
- Demo completes without synthetic fallbacks
- Evergreen docs contain rich, accurate content
- Code files are fully documented
- Queries return relevant, time-aware responses

---

## 🔧 Technical Architecture

### Docker Container Deployment
```python
# In mcp-provisioner/provision_mcp_use_case.py
import docker

async def _deploy_container(self, mcp_instance: MCPInstance):
    client = docker.from_env()
    
    container = client.containers.run(
        image=mcp_instance.config.docker_image,
        name=f"mcp-{mcp_instance.mcp_id}",
        environment=mcp_instance.metadata.get("environment", {}),
        mem_limit=mcp_instance.resource_limits.memory_limit_mb * 1024 * 1024,
        cpu_shares=int(mcp_instance.resource_limits.cpu_limit * 1024),
        ports={f'{mcp_instance.config.port}/tcp': None},
        network='ams',
        detach=True,
        healthcheck={
            'test': ['CMD', 'curl', '-f', f'http://localhost:{mcp_instance.config.port}/health'],
            'interval': 10_000_000_000,  # 10s in nanoseconds
            'timeout': 5_000_000_000,
            'retries': 3
        }
    )
    
    # Wait for health check
    await self._wait_for_health(container, timeout=60)
    
    return container.id
```

### GitHub Integration
```python
# In services/mock-data-generator/github_collector.py
class GitHubCommitCollector:
    async def collect_commits(self, repo: str, branch: str = "main", limit: int = 100):
        commits = await self.github.get_commits(repo, branch, limit)
        
        documents = []
        for commit in commits:
            doc = {
                "document_id": f"commit-{commit.sha}",
                "title": commit.message.split('\n')[0],
                "content": self._normalize_commit(commit),
                "metadata": {
                    "type": "git_commit",
                    "repo": repo,
                    "branch": branch,
                    "sha": commit.sha,
                    "author": commit.author.login,
                    "created_at": commit.commit.author.date,
                    "updated_at": commit.commit.author.date,
                    "files_changed": len(commit.files)
                }
            }
            documents.append(doc)
        
        return documents
```

### Code Analysis Integration
```python
# In demo_mcp_lifecycle.py
async def analyze_and_ingest_code_files(self, repo_path: Path):
    code_files = list(repo_path.rglob("*.py")) + list(repo_path.rglob("*.js"))
    
    for file_path in code_files:
        with open(file_path) as f:
            content = f.read()
        
        # Analyze code
        analysis_response = await self.client.post(
            f"{self.services['code-analyzer']}/api/v1/analysis/analyze",
            json={
                "source_type": "local",
                "title": file_path.name,
                "content": content,
                "path": str(file_path),
                "include_endpoints": True,
                "include_style_check": True
            }
        )
        
        if analysis_response.status_code == 200:
            analysis = analysis_response.json()
            
            # Generate documentation from analysis
            doc_content = self._generate_code_documentation(file_path, content, analysis)
            
            # Ingest as document
            await self.ingest_single_document(
                document_id=f"code-{file_path.name}",
                title=f"Code Analysis: {file_path.name}",
                content=doc_content,
                metadata={
                    "type": "code_analysis",
                    "file_path": str(file_path),
                    "quality_score": analysis.get("quality_score"),
                    "endpoints": len(analysis.get("endpoints_found", [])),
                    "created_at": datetime.fromtimestamp(file_path.stat().st_ctime).isoformat(),
                    "updated_at": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                }
            )
```

---

## 📊 Expected Outcomes

### Before Enhancements
- ❌ MCP instances not deployed (gateway returns 503)
- ❌ Evergreen docs contain synthetic content only
- ❌ No timestamp tracking on documents
- ❌ Manual document discovery only
- ❌ Code files not analyzed or documented

### After Enhancements
- ✅ MCP containers deployed and running
- ✅ Evergreen docs with rich, accurate content from trained MCP
- ✅ All documents timestamped for freshness queries
- ✅ Automatic GitHub ingestion (commits, docs, code)
- ✅ Comprehensive code documentation generated automatically
- ✅ MCP can answer "what does file X do?" with detailed responses
- ✅ Query "recent changes" returns time-aware results

---

## 🚀 Next Steps

1. **Immediate**: Implement Docker container deployment in `mcp-provisioner`
2. **Short-term**: Add timestamp tracking to ingestion pipeline
3. **Medium-term**: Build GitHub integration for commits and docs
4. **Long-term**: Full code analysis and documentation generation

**Estimated Timeline**: 2-3 hours for Phase 1, 4-6 hours for complete implementation

---

**Status**: Ready for implementation ✅
