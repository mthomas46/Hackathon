# 🔍 Deep Audit: Git History as Optional Feature - Refactoring Plan

**Date:** October 20, 2025  
**Status:** 🔴 AUDIT & PLANNING (DO NOT IMPLEMENT)  
**Purpose:** Make Git commit history optional for 10-100× faster ingestion

---

## 📊 Executive Summary

### Current State
- **Git History:** MANDATORY for all ingestion
- **Speed:** 2-4 hours for 5,000 documents (scanning 12,000+ commits)
- **Bottleneck:** 95% of time spent on Git operations (commit walking, file extraction)
- **Use Case Coverage:** 100% Git-based, 0% file system-based

### Proposed State
- **Git History:** OPTIONAL (user-selectable feature)
- **Speed (Git mode):** 2-4 hours (unchanged)
- **Speed (Snapshot mode):** 5-15 minutes (10-100× faster!)
- **Use Case Coverage:** Git-based + File system-based

### Performance Impact
```
Current (Git-only):
  5,000 documents = 2-4 hours
  
With Snapshot Mode:
  5,000 documents = 5-15 minutes (96% faster!)
  
Why So Fast?
  ❌ No commit walking (12,000 commits → 0)
  ❌ No Git object extraction
  ❌ No duplicate checking across history
  ✅ Direct file system scan
  ✅ Simple content hashing
  ✅ Single-pass processing
```

---

## 🚨 Critical Flaws Identified in Current Architecture

### Flaw #1: Git is Hardcoded Throughout the Stack

**Problem:** Git operations are deeply embedded in every layer

**Evidence:**
```python
# Layer 1: API (admin.py)
async def start_ingestion(request: IngestRequest):
    # Path validation REQUIRES git repo
    is_valid, message, resolved = validate_ingestion_path(request.repo_path)
    # ❌ Fails if not a git repo

# Layer 2: Job Processor (job_processor.py:87)
async def process(self, job: IngestionJobModel):
    self.git_service = GitService(repo_path=job.repo_path)  # ❌ Always initialized
    commits = await self._get_commits_for_mode(job.mode)    # ❌ Always fetches commits
    for commit in commits:
        await self._process_commit(commit, job)             # ❌ Always commit-based

# Layer 3: Database Schema (db_models.py:39)
class DocumentModel(Base):
    git_commit_sha = Column(String(40), ForeignKey("git_commits.sha"), index=True)  # ❌ NOT NULL
    is_latest = Column(Boolean, nullable=False, default=True, index=True)           # ❌ Git concept
    
    __table_args__ = (
        UniqueConstraint("file_path", "git_commit_sha", name="uq_document_file_commit"),  # ❌ Git required
    )

# Layer 4: Commit Optimizer (commit_optimizer.py:203)
async def check_commit_already_ingested(self, commit_sha: str):
    # ❌ Entire optimization strategy assumes Git commits
    result = await session.execute(
        select(DocumentModel.git_commit_sha)
        .where(DocumentModel.git_commit_sha == commit_sha)
    )

# Layer 5: Recovery System (recoverable_job_processor.py:109)
commits = await self._get_commits_for_mode(job.mode)  # ❌ Checkpoints tied to commits
await self.checkpoint(f"commit_{commit.sha}")         # ❌ Recovery assumes commit structure
```

**Impact:** Cannot bypass Git even if user doesn't need history

---

### Flaw #2: Performance Penalty for "Current State Only" Use Cases

**Problem:** Users who only want current files pay 100× time cost for unused history

**Use Cases Penalized:**
1. **Initial Knowledge Base Setup**
   - User: "I just want to ingest all current docs"
   - System: "Sure, let me scan 10 years of Git history first..." (2 hours)
   - User: "Why? I don't care about old versions!"

2. **Non-Git Document Collections**
   - User: "Ingest my SharePoint documents"
   - System: "Can't, no Git repo"
   - User: "They're just files, why do you need Git?"

3. **Rapid Prototyping**
   - Developer: "Quick test with 1000 docs"
   - System: (2 hours later) "Done!"
   - Developer: "I could have read them manually faster..."

4. **CI/CD Documentation Builds**
   - Pipeline: "Generate docs from current codebase"
   - System: (Scans entire history, times out)
   - Pipeline: ❌ Failed

**Real-World Example:**
```
Job ID: bc027f81-31c6-499c-97da-e66315323cc6
  Total Documents: 12,171 (from Git history)
  Actually Wanted: 993 (current files)
  Time Wasted: 95% (processing 11,178 historical duplicates)
  User Experience: "Why is this so slow?"
```

---

### Flaw #3: Database Schema Assumes Git

**Problem:** Schema design makes Git mandatory, not optional

**Schema Issues:**

1. **Foreign Key Constraint**
   ```sql
   -- db_models.py:39
   git_commit_sha = Column(String(40), ForeignKey("git_commits.sha"), index=True)
   
   -- Problem: Can't insert document without commit!
   -- For non-Git docs, what do we use?
   --   Option A: NULL (breaks foreign key)
   --   Option B: Fake SHA (hacky, breaks semantics)
   --   Option C: Remove constraint (breaks existing queries)
   ```

2. **Unique Constraint**
   ```sql
   -- db_models.py:51
   UniqueConstraint("file_path", "git_commit_sha", name="uq_document_file_commit")
   
   -- Problem: Prevents multiple versions of same file without Git!
   -- For file system ingestion:
   --   - Same file, different times → duplicate key error
   --   - Can't track versions without commit SHA
   ```

3. **is_latest Flag**
   ```sql
   -- db_models.py:40
   is_latest = Column(Boolean, nullable=False, default=True, index=True)
   
   -- Problem: "Latest" is a Git concept (HEAD)
   -- For file system:
   --   - What does "latest" mean?
   --   - Latest ingestion? Latest file mtime?
   --   - Ambiguous semantics
   ```

4. **Indexes Optimized for Git**
   ```sql
   -- add_performance_indexes.py:47
   CREATE INDEX idx_documents_commit_sha ON documents (git_commit_sha);
   CREATE INDEX idx_documents_service_latest ON documents (service_name, is_latest);
   
   -- Problem: Wasted space for non-Git documents
   -- NULL commit_sha → useless index entries
   ```

---

### Flaw #4: Duplicate Detection Tied to Git

**Problem:** Bloom filter and commit optimizer assume Git workflow

**Evidence:**
```python
# commit_optimizer.py:174
class CommitOptimizer:
    """
    Optimizes ingestion by detecting duplicate commits.
    
    Features:
    - Commit-level duplicate detection  # ❌ Git-specific
    - Skip entire commits if already ingested  # ❌ Git-specific
    """
    
    async def check_commit_already_ingested(self, commit_sha: str):
        # ❌ Entire method assumes Git commits
        result = await session.execute(
            select(func.count(DocumentModel.id))
            .where(DocumentModel.git_commit_sha == commit_sha)
        )

# job_processor.py:651
commit_check = await self.commit_optimizer.check_commit_already_ingested(commit.sha)
if commit_check["already_ingested"]:
    # ❌ Skip entire commit
    # For file system: Can't skip "commits" that don't exist!
```

**For File System Ingestion:**
- No commits to check
- No commit-level skipping
- Need file-level duplicate detection instead

---

### Flaw #5: Recovery/Checkpointing Assumes Commits

**Problem:** Job recovery uses commit boundaries as checkpoints

**Evidence:**
```python
# recoverable_job_processor.py:120
if can_resume and resume_state:
    start_index = resume_state['progress']['last_processed_commit_index']
    # ❌ Assumes commits as units of work

# checkpoint_manager.py (implied)
await self.checkpoint(f"commit_{commit.sha}")
# ❌ Checkpoint keys tied to commit SHAs
```

**For File System Ingestion:**
- No commits → no natural checkpoint boundaries
- Need different checkpoint strategy (e.g., file batches)

---

### Flaw #6: Progress Tracking Assumes Git Workflow

**Problem:** Progress metrics are commit-centric

**Evidence:**
```python
# job_processor.py:674
logger.info(f"Commit {commit.sha[:8]}: {len(filtered_files)}/{len(files)} files")
# ❌ Progress shown per commit

# job_progress.py (implied)
progress_data = {
    "phase": "processing_commits",  # ❌ Git terminology
    "current_commit": 100,
    "total_commits": 5000
}
```

**For File System Ingestion:**
- No commits to count
- Need file-based progress instead

---

### Flaw #7: Temporal Versioning Conflates Git and Content

**Problem:** Version tracking mixes Git metadata with content hashing

**Evidence:**
```python
# db_models.py:68
class DocumentVersionModel(Base):
    git_commit_sha = Column(String(40), ForeignKey("git_commits.sha"), nullable=False)  # ❌ Git required
    commit_message = Column(Text, nullable=False)  # ❌ Git metadata
    commit_date = Column(DateTime, nullable=False)  # ❌ Git timestamp
    content_hash = Column(String(64), nullable=False)  # ✅ Content-based (good!)
```

**Observation:** System ALREADY has content-based versioning (content_hash), but it's tangled with Git!

---

## 🎯 Proposed Solution: Dual-Mode Ingestion

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     INGESTION API                                │
│                  /api/v1/admin/ingest                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ├─ mode: "quick" | "full" | "snapshot"
                              ├─ versioning: "git" | "content" | "none"
                              └─ history: true | false
                              │
                ┌─────────────┴─────────────┐
                │                           │
                ▼                           ▼
┌───────────────────────────┐   ┌───────────────────────────┐
│   GIT HISTORY MODE        │   │   SNAPSHOT MODE           │
│   (Current behavior)      │   │   (New, 10-100× faster)   │
└───────────────────────────┘   └───────────────────────────┘
│                           │   │                           │
│ • Walk Git commits        │   │ • Scan file system        │
│ • Extract files @ commit  │   │ • Read current files      │
│ • Track versions          │   │ • Hash content            │
│ • Detect duplicates       │   │ • Store once              │
│ • 2-4 hours for 5K docs   │   │ • 5-15 min for 5K docs    │
│                           │   │                           │
└─────────────┬─────────────┘   └─────────────┬─────────────┘
              │                               │
              └───────────┬───────────────────┘
                          ▼
          ┌───────────────────────────────────┐
          │   UNIFIED STORAGE LAYER           │
          │   (Refactored for both modes)     │
          └───────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
    ┌──────────┐   ┌──────────┐   ┌──────────┐
    │PostgreSQL│   │ ChromaDB │   │  Redis   │
    └──────────┘   └──────────┘   └──────────┘
```

---

## 📋 Refactoring Plan (7 Phases)

### Phase 1: Database Schema Refactoring (Foundation)

**Goal:** Make Git fields optional, add versioning mode tracking

**Changes:**

1. **Make git_commit_sha nullable**
   ```sql
   -- Migration: 001_make_git_optional.sql
   ALTER TABLE documents 
   ALTER COLUMN git_commit_sha DROP NOT NULL;
   
   ALTER TABLE documents 
   DROP CONSTRAINT IF EXISTS fk_documents_git_commits;
   
   ALTER TABLE documents 
   ADD CONSTRAINT fk_documents_git_commits 
   FOREIGN KEY (git_commit_sha) REFERENCES git_commits(sha) 
   ON DELETE SET NULL;  -- Allow orphaned documents
   ```

2. **Add versioning_mode column**
   ```sql
   ALTER TABLE documents 
   ADD COLUMN versioning_mode VARCHAR(20) DEFAULT 'git' NOT NULL;
   
   -- Values: 'git', 'content', 'none'
   -- 'git': Full Git history tracking
   -- 'content': Content-hash based versioning (no Git)
   -- 'none': Single version only (fastest)
   
   CREATE INDEX idx_documents_versioning_mode ON documents(versioning_mode);
   ```

3. **Add ingestion_timestamp for non-Git versioning**
   ```sql
   ALTER TABLE documents 
   ADD COLUMN ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL;
   
   -- For non-Git docs, this is the "version time"
   CREATE INDEX idx_documents_ingestion_timestamp ON documents(ingestion_timestamp DESC);
   ```

4. **Relax unique constraint**
   ```sql
   -- Drop old constraint
   ALTER TABLE documents 
   DROP CONSTRAINT uq_document_file_commit;
   
   -- Add new flexible constraint
   -- Unique per (file_path, versioning_mode, version_id)
   -- version_id = git_commit_sha OR content_hash OR ingestion_timestamp
   ALTER TABLE documents 
   ADD CONSTRAINT uq_document_version 
   UNIQUE (file_path, versioning_mode, COALESCE(git_commit_sha, content_hash));
   ```

5. **Add ingestion_mode to jobs**
   ```sql
   ALTER TABLE ingestion_jobs 
   ADD COLUMN ingestion_mode VARCHAR(20) DEFAULT 'git_history' NOT NULL;
   
   -- Values: 'git_history', 'git_snapshot', 'filesystem'
   -- 'git_history': Current behavior (walk commits)
   -- 'git_snapshot': Git repo, but only current files (fast!)
   -- 'filesystem': No Git, just scan directory
   ```

**Backward Compatibility:**
- Existing documents: `versioning_mode='git'`, `git_commit_sha` populated
- Existing queries: Still work (git_commit_sha is indexed)
- New documents: Can have `git_commit_sha=NULL`

**Files to Create:**
- `services/ecosystem-mcp/src/storage/migrations/001_make_git_optional.sql`
- `services/ecosystem-mcp/src/storage/migrations/001_make_git_optional.py` (Python wrapper)

---

### Phase 2: Create Abstraction Layer (Strategy Pattern)

**Goal:** Decouple ingestion logic from Git-specific implementation

**New Architecture:**

```python
# services/ecosystem-mcp/src/services/ingestion/strategies/base.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, AsyncIterator

class IngestionStrategy(ABC):
    """
    Abstract base class for ingestion strategies.
    
    Strategies:
    - GitHistoryStrategy: Walk Git commits (current behavior)
    - GitSnapshotStrategy: Git repo, current files only (NEW)
    - FileSystemStrategy: No Git, scan directory (NEW)
    """
    
    @abstractmethod
    async def discover_documents(self) -> AsyncIterator[Dict[str, Any]]:
        """
        Discover documents to ingest.
        
        Yields:
            Document metadata dict with:
                - file_path: str
                - content: str
                - version_id: str (commit SHA, content hash, or timestamp)
                - version_metadata: dict (commit info, file mtime, etc.)
        """
        pass
    
    @abstractmethod
    async def get_total_estimate(self) -> int:
        """
        Estimate total documents (for progress tracking).
        
        Returns:
            Estimated document count
        """
        pass
    
    @abstractmethod
    async def supports_resume(self) -> bool:
        """
        Check if strategy supports job resumption.
        
        Returns:
            True if can resume from checkpoint
        """
        pass
    
    @abstractmethod
    async def create_checkpoint_key(self, doc_metadata: Dict[str, Any]) -> str:
        """
        Create checkpoint key for recovery.
        
        Args:
            doc_metadata: Document metadata
        
        Returns:
            Checkpoint key (commit SHA, file path, etc.)
        """
        pass
```

**Implementation 1: GitHistoryStrategy (Refactored Current Code)**

```python
# services/ecosystem-mcp/src/services/ingestion/strategies/git_history.py
from .base import IngestionStrategy
from ...git.git_service import GitService

class GitHistoryStrategy(IngestionStrategy):
    """
    Git history ingestion (current behavior).
    
    Walks Git commits and extracts files at each commit.
    Tracks full version history.
    """
    
    def __init__(self, repo_path: str, mode: str = "full"):
        self.repo_path = repo_path
        self.mode = mode  # quick, full, incremental
        self.git_service = GitService(repo_path)
    
    async def discover_documents(self) -> AsyncIterator[Dict[str, Any]]:
        """
        Walk Git commits and yield documents.
        
        This is the CURRENT behavior, just refactored.
        """
        # Get commits based on mode
        if self.mode == "quick":
            commits = await self.git_service.get_recent_commits(limit=10)
        elif self.mode == "full":
            commits = await self.git_service.get_all_commits()
        else:
            commits = await self.git_service.get_recent_commits(limit=200)
        
        # Process each commit
        for commit in commits:
            files = await self.git_service.get_commit_files(commit.sha)
            
            for file_path in files:
                content = await self.git_service.get_file_at_commit(file_path, commit.sha)
                
                if content:
                    yield {
                        "file_path": file_path,
                        "content": content,
                        "version_id": commit.sha,
                        "version_metadata": {
                            "commit_sha": commit.sha,
                            "commit_message": commit.message,
                            "commit_author": commit.author,
                            "commit_date": commit.date,
                            "versioning_mode": "git"
                        }
                    }
    
    async def get_total_estimate(self) -> int:
        """Estimate total documents from Git history."""
        commits = await self._get_commits()
        # Rough estimate: 50 files per commit
        return len(commits) * 50
    
    async def supports_resume(self) -> bool:
        return True  # Can resume from commit
    
    async def create_checkpoint_key(self, doc_metadata: Dict[str, Any]) -> str:
        return f"commit_{doc_metadata['version_metadata']['commit_sha']}"
```

**Implementation 2: GitSnapshotStrategy (NEW - 10-100× Faster!)**

```python
# services/ecosystem-mcp/src/services/ingestion/strategies/git_snapshot.py
from .base import IngestionStrategy
from pathlib import Path
import git

class GitSnapshotStrategy(IngestionStrategy):
    """
    Git snapshot ingestion (NEW - FAST!).
    
    Scans current files in Git repo (HEAD only).
    No commit walking, no history.
    
    Performance:
    - 10-100× faster than GitHistoryStrategy
    - 5,000 docs: 5-15 minutes (vs 2-4 hours)
    
    Use Cases:
    - Initial knowledge base setup
    - CI/CD documentation builds
    - Rapid prototyping
    - "I just want current docs!"
    """
    
    def __init__(self, repo_path: str, target_subdirectory: str = None):
        self.repo_path = Path(repo_path)
        self.target_subdirectory = target_subdirectory
        self.repo = git.Repo(repo_path)
        self.head_commit = self.repo.head.commit
    
    async def discover_documents(self) -> AsyncIterator[Dict[str, Any]]:
        """
        Scan current files (HEAD) only.
        
        This is MUCH faster than walking history!
        """
        # Get current commit SHA (for metadata only)
        current_sha = self.head_commit.hexsha
        current_date = datetime.fromtimestamp(self.head_commit.committed_date)
        
        # Scan file system (current files)
        base_path = self.repo_path
        if self.target_subdirectory:
            base_path = base_path / self.target_subdirectory
        
        # Supported extensions
        extensions = {".md", ".py", ".yaml", ".yml", ".json", ".txt", ".rst"}
        
        # Walk directory
        for file_path in base_path.rglob("*"):
            # Skip directories
            if file_path.is_dir():
                continue
            
            # Skip ignored paths
            if self._should_ignore(file_path):
                continue
            
            # Check extension
            if file_path.suffix.lower() not in extensions:
                continue
            
            # Read file
            try:
                content = file_path.read_text(encoding='utf-8')
            except Exception as e:
                logger.warning(f"Failed to read {file_path}: {e}")
                continue
            
            # Compute content hash for versioning
            content_hash = hashlib.sha256(content.encode()).hexdigest()
            
            # Get relative path
            rel_path = str(file_path.relative_to(self.repo_path))
            
            yield {
                "file_path": rel_path,
                "content": content,
                "version_id": content_hash,  # Use content hash, not commit!
                "version_metadata": {
                    "git_commit_sha": current_sha,  # Optional: for reference
                    "commit_date": current_date,
                    "file_mtime": datetime.fromtimestamp(file_path.stat().st_mtime),
                    "versioning_mode": "content",  # Content-based, not Git-based
                    "is_snapshot": True
                }
            }
    
    async def get_total_estimate(self) -> int:
        """Estimate by counting files (fast!)."""
        count = 0
        base_path = self.repo_path
        if self.target_subdirectory:
            base_path = base_path / self.target_subdirectory
        
        extensions = {".md", ".py", ".yaml", ".yml", ".json", ".txt", ".rst"}
        
        for file_path in base_path.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in extensions:
                if not self._should_ignore(file_path):
                    count += 1
        
        return count
    
    async def supports_resume(self) -> bool:
        return True  # Can resume from file path
    
    async def create_checkpoint_key(self, doc_metadata: Dict[str, Any]) -> str:
        return f"file_{doc_metadata['file_path']}"
    
    def _should_ignore(self, path: Path) -> bool:
        """Check if path should be ignored."""
        ignore_dirs = {".git", "__pycache__", "venv", "node_modules", ".pytest_cache"}
        
        for parent in path.parents:
            if parent.name in ignore_dirs:
                return True
        
        return False
```

**Implementation 3: FileSystemStrategy (NEW - No Git Required)**

```python
# services/ecosystem-mcp/src/services/ingestion/strategies/filesystem.py
from .base import IngestionStrategy
from pathlib import Path

class FileSystemStrategy(IngestionStrategy):
    """
    File system ingestion (NEW - No Git required).
    
    Scans any directory, no Git needed.
    
    Use Cases:
    - SharePoint documents
    - Network file shares
    - Cloud storage mounts
    - Any non-Git document collection
    """
    
    def __init__(self, directory_path: str):
        self.directory_path = Path(directory_path)
        
        if not self.directory_path.exists():
            raise ValueError(f"Directory does not exist: {directory_path}")
    
    async def discover_documents(self) -> AsyncIterator[Dict[str, Any]]:
        """
        Scan directory recursively.
        
        No Git required!
        """
        extensions = {".md", ".py", ".yaml", ".yml", ".json", ".txt", ".rst", ".pdf", ".docx"}
        
        for file_path in self.directory_path.rglob("*"):
            if file_path.is_dir():
                continue
            
            if file_path.suffix.lower() not in extensions:
                continue
            
            try:
                # Read file
                if file_path.suffix == ".pdf":
                    content = await self._extract_pdf(file_path)
                elif file_path.suffix == ".docx":
                    content = await self._extract_docx(file_path)
                else:
                    content = file_path.read_text(encoding='utf-8')
                
                # Compute content hash
                content_hash = hashlib.sha256(content.encode()).hexdigest()
                
                # Get file metadata
                stat = file_path.stat()
                
                yield {
                    "file_path": str(file_path.relative_to(self.directory_path)),
                    "content": content,
                    "version_id": content_hash,
                    "version_metadata": {
                        "file_mtime": datetime.fromtimestamp(stat.st_mtime),
                        "file_size": stat.st_size,
                        "versioning_mode": "content",
                        "source_type": "filesystem"
                    }
                }
            
            except Exception as e:
                logger.warning(f"Failed to process {file_path}: {e}")
                continue
    
    async def get_total_estimate(self) -> int:
        """Count files."""
        count = 0
        extensions = {".md", ".py", ".yaml", ".yml", ".json", ".txt", ".rst", ".pdf", ".docx"}
        
        for file_path in self.directory_path.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in extensions:
                count += 1
        
        return count
    
    async def supports_resume(self) -> bool:
        return True
    
    async def create_checkpoint_key(self, doc_metadata: Dict[str, Any]) -> str:
        return f"file_{doc_metadata['file_path']}"
```

**Files to Create:**
- `services/ecosystem-mcp/src/services/ingestion/strategies/__init__.py`
- `services/ecosystem-mcp/src/services/ingestion/strategies/base.py`
- `services/ecosystem-mcp/src/services/ingestion/strategies/git_history.py`
- `services/ecosystem-mcp/src/services/ingestion/strategies/git_snapshot.py`
- `services/ecosystem-mcp/src/services/ingestion/strategies/filesystem.py`

---

### Phase 3: Refactor JobProcessor to Use Strategies

**Goal:** Make JobProcessor strategy-agnostic

**Changes:**

```python
# services/ecosystem-mcp/src/services/ingestion/job_processor.py (REFACTORED)
from .strategies import IngestionStrategy, GitHistoryStrategy, GitSnapshotStrategy, FileSystemStrategy

class JobProcessor:
    """
    Processes ingestion jobs using pluggable strategies.
    
    Now supports:
    - Git history mode (current behavior)
    - Git snapshot mode (10-100× faster!)
    - File system mode (no Git required)
    """
    
    def __init__(self, worker_id: str = "unknown"):
        self.worker_id = worker_id
        self.normalizer_factory = NormalizerFactory()
        self.embedding_service = EmbeddingService()
        self.strategy: Optional[IngestionStrategy] = None
    
    async def process(self, job: IngestionJobModel) -> Dict[str, Any]:
        """
        Process ingestion job using appropriate strategy.
        
        Strategy selection based on job.ingestion_mode:
        - 'git_history': GitHistoryStrategy (current behavior)
        - 'git_snapshot': GitSnapshotStrategy (NEW - fast!)
        - 'filesystem': FileSystemStrategy (NEW - no Git)
        """
        # Select strategy
        self.strategy = self._select_strategy(job)
        
        # Initialize progress tracking
        await self._init_progress_tracking(str(job.id))
        
        # Get total estimate
        total_estimate = await self.strategy.get_total_estimate()
        await self._update_job_total(job.id, total_estimate)
        
        # Process documents
        result = {
            "processed": 0,
            "failed": 0,
            "skipped": 0,
            "embeddings": 0,
            "cost": 0.0
        }
        
        # Stream documents from strategy
        async for doc_metadata in self.strategy.discover_documents():
            try:
                # Check for duplicates (content-based)
                if await self._is_duplicate(doc_metadata):
                    result["skipped"] += 1
                    continue
                
                # Normalize document
                normalized = await self._normalize_document(doc_metadata)
                
                # Generate embedding
                embedding = await self.embedding_service.generate_embedding(normalized["content"])
                
                # Store document
                await self._store_document(normalized, embedding, doc_metadata["version_metadata"])
                
                result["processed"] += 1
                result["embeddings"] += 1
                
                # Update progress
                await self._update_progress(
                    "processing",
                    result["processed"],
                    total_estimate,
                    current_file=doc_metadata["file_path"]
                )
            
            except Exception as e:
                logger.error(f"Failed to process {doc_metadata['file_path']}: {e}")
                result["failed"] += 1
        
        return result
    
    def _select_strategy(self, job: IngestionJobModel) -> IngestionStrategy:
        """
        Select ingestion strategy based on job configuration.
        
        Args:
            job: Ingestion job
        
        Returns:
            Appropriate strategy instance
        """
        ingestion_mode = job.job_metadata.get("ingestion_mode", "git_history")
        
        if ingestion_mode == "git_history":
            # Current behavior: Walk Git commits
            return GitHistoryStrategy(
                repo_path=job.repo_path,
                mode=job.mode  # quick, full, incremental
            )
        
        elif ingestion_mode == "git_snapshot":
            # NEW: Git repo, current files only (FAST!)
            return GitSnapshotStrategy(
                repo_path=job.repo_path,
                target_subdirectory=job.job_metadata.get("target_subdirectory")
            )
        
        elif ingestion_mode == "filesystem":
            # NEW: No Git, scan directory
            return FileSystemStrategy(
                directory_path=job.repo_path
            )
        
        else:
            raise ValueError(f"Unknown ingestion mode: {ingestion_mode}")
    
    async def _is_duplicate(self, doc_metadata: Dict[str, Any]) -> bool:
        """
        Check if document is duplicate (content-based).
        
        Works for both Git and non-Git documents.
        """
        content_hash = hashlib.sha256(doc_metadata["content"].encode()).hexdigest()
        
        db = get_database()
        async with db.session() as session:
            result = await session.execute(
                select(DocumentModel.id)
                .where(DocumentModel.content_hash == content_hash)
                .limit(1)
            )
            
            return result.first() is not None
    
    async def _store_document(
        self,
        normalized: Dict[str, Any],
        embedding: Dict[str, Any],
        version_metadata: Dict[str, Any]
    ):
        """
        Store document with flexible versioning.
        
        Handles both Git and non-Git documents.
        """
        db = get_database()
        async with db.session() as session:
            # Create document
            doc = DocumentModel(
                service_name=normalized["service_name"],
                file_path=normalized["file_path"],
                original_format=normalized["original_format"],
                original_content=normalized["original_content"],
                normalized_content=normalized["normalized_content"],
                content_hash=normalized["content_hash"],
                
                # Git fields (optional now!)
                git_commit_sha=version_metadata.get("commit_sha"),  # NULL for non-Git
                
                # New fields
                versioning_mode=version_metadata.get("versioning_mode", "content"),
                ingestion_timestamp=datetime.utcnow(),
                
                # Metadata
                doc_metadata=version_metadata
            )
            
            session.add(doc)
            await session.commit()
```

**Files to Modify:**
- `services/ecosystem-mcp/src/services/ingestion/job_processor.py` (major refactor)
- `services/ecosystem-mcp/src/services/ingestion/recoverable_job_processor.py` (update to use strategies)

---

### Phase 4: Update API to Expose New Modes

**Goal:** Allow users to select ingestion mode

**Changes:**

```python
# services/ecosystem-mcp/src/api/routes/admin.py (UPDATED)
class IngestRequest(BaseModel):
    """Request to start ingestion."""
    repo_path: str = Field(..., description="Path to repository or directory")
    
    # OLD: mode (quick, full, incremental)
    mode: str = Field(default="quick", description="Ingestion depth: quick, full, incremental")
    
    # NEW: ingestion_mode (git_history, git_snapshot, filesystem)
    ingestion_mode: str = Field(
        default="git_snapshot",  # Default to FAST mode!
        description="""
        Ingestion mode:
        - 'git_history': Full Git history (slow, 2-4 hours for 5K docs)
        - 'git_snapshot': Current files only from Git repo (fast, 5-15 min for 5K docs) [RECOMMENDED]
        - 'filesystem': No Git, scan directory (fast, works with any directory)
        """
    )
    
    # NEW: versioning_preference
    versioning_preference: str = Field(
        default="content",
        description="""
        Versioning strategy:
        - 'git': Track Git commit history (requires git_history mode)
        - 'content': Content-hash based versioning (automatic deduplication)
        - 'none': No versioning (fastest, single version only)
        """
    )
    
    resolve_host_path: bool = Field(default=True, description="Auto-resolve host paths")
    target_subdirectory: Optional[str] = Field(default=None, description="Target subdirectory")


@router.post("/ingest", response_model=IngestResponse)
async def start_ingestion(request: IngestRequest, background_tasks: BackgroundTasks):
    """
    Start document ingestion.
    
    NEW: Supports three ingestion modes:
    
    1. Git History Mode (git_history):
       - Walks Git commit history
       - Tracks full version history
       - Slow (2-4 hours for 5K docs)
       - Use when: You need full Git history
    
    2. Git Snapshot Mode (git_snapshot) [RECOMMENDED]:
       - Scans current files in Git repo
       - 10-100× faster (5-15 min for 5K docs)
       - Use when: You just want current docs
    
    3. File System Mode (filesystem):
       - Scans any directory (no Git required)
       - Fast (5-15 min for 5K docs)
       - Use when: Documents not in Git
    """
    # Validate ingestion mode
    valid_modes = ["git_history", "git_snapshot", "filesystem"]
    if request.ingestion_mode not in valid_modes:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid ingestion_mode. Must be one of: {valid_modes}"
        )
    
    # Validate versioning compatibility
    if request.ingestion_mode == "git_history" and request.versioning_preference == "none":
        raise HTTPException(
            status_code=400,
            detail="git_history mode requires versioning (use 'git' or 'content')"
        )
    
    # Validate path based on mode
    if request.ingestion_mode in ["git_history", "git_snapshot"]:
        # Require Git repo
        if request.resolve_host_path:
            is_valid, message, resolved = validate_ingestion_path(request.repo_path)
            if not is_valid:
                raise HTTPException(status_code=400, detail=message)
            repo_path = resolved
        else:
            repo_path = request.repo_path
    else:
        # File system mode: just check directory exists
        repo_path = Path(request.repo_path)
        if not repo_path.exists():
            raise HTTPException(
                status_code=400,
                detail=f"Directory does not exist: {request.repo_path}"
            )
        repo_path = str(repo_path)
    
    # Create job
    db = get_database()
    async with db.session() as session:
        job = IngestionJobModel(
            mode=request.mode,
            status="queued",
            repo_path=repo_path,
            job_metadata={
                "ingestion_mode": request.ingestion_mode,  # NEW
                "versioning_preference": request.versioning_preference,  # NEW
                "target_subdirectory": request.target_subdirectory
            }
        )
        
        session.add(job)
        await session.commit()
        await session.refresh(job)
        
        job_id = str(job.id)
    
    # Queue job
    redis_client = get_redis_client()
    await redis_client.xadd(
        "ingestion_jobs",
        {
            "job_id": job_id,
            "mode": request.mode,
            "ingestion_mode": request.ingestion_mode,  # NEW
            "repo_path": repo_path
        }
    )
    
    return IngestResponse(
        job_id=job_id,
        status="queued",
        message=f"Ingestion job queued ({request.ingestion_mode} mode)"
    )
```

**Files to Modify:**
- `services/ecosystem-mcp/src/api/routes/admin.py` (update IngestRequest, start_ingestion)

---

### Phase 5: Update Dashboard UI

**Goal:** Expose new modes in user-friendly way

**Changes:**

```python
# services/ecosystem-mcp-dashboard/dashboard_views/ingestion_manager.py (UPDATED)
def render_ingestion_form():
    """Render ingestion form with new modes."""
    
    st.subheader("🚀 Start New Ingestion")
    
    with st.form("start_ingestion"):
        # Path input
        repo_path = st.text_input(
            "Repository Path",
            value="/host",
            help="Path to repository or directory"
        )
        
        # NEW: Ingestion Mode (prominent!)
        st.markdown("### Ingestion Mode")
        
        ingestion_mode = st.radio(
            "Select ingestion mode",
            options=["git_snapshot", "git_history", "filesystem"],
            format_func=lambda x: {
                "git_snapshot": "🚀 Git Snapshot (Fast - Recommended)",
                "git_history": "🐢 Git History (Slow - Full History)",
                "filesystem": "📁 File System (No Git Required)"
            }[x],
            help="""
            **Git Snapshot (Recommended):**
            - Scans current files in Git repo
            - 10-100× faster (5-15 min for 5K docs)
            - Use when you just want current documentation
            
            **Git History:**
            - Walks full Git commit history
            - Slow (2-4 hours for 5K docs)
            - Use when you need version history
            
            **File System:**
            - Scans any directory (no Git required)
            - Fast (5-15 min for 5K docs)
            - Use for non-Git document collections
            """
        )
        
        # Show mode-specific info
        if ingestion_mode == "git_snapshot":
            st.info(
                "⚡ **Fast Mode:** This will scan only current files, "
                "not Git history. Perfect for initial setup or CI/CD!"
            )
        elif ingestion_mode == "git_history":
            st.warning(
                "🐢 **Slow Mode:** This will scan full Git history. "
                "May take 2-4 hours for large repos. Use only if you need version history."
            )
        elif ingestion_mode == "filesystem":
            st.info(
                "📁 **File System Mode:** No Git required. "
                "Scans any directory. Perfect for SharePoint, network shares, etc."
            )
        
        # Depth (only for git_history)
        if ingestion_mode == "git_history":
            mode = st.selectbox(
                "Depth",
                options=["quick", "full", "incremental"],
                help="quick: 10 commits, full: all commits, incremental: since last run"
            )
        else:
            mode = "quick"  # Not used for snapshot/filesystem
        
        # Versioning (only for git_history)
        if ingestion_mode == "git_history":
            versioning = st.selectbox(
                "Versioning",
                options=["git", "content"],
                help="git: Track Git commits, content: Content-hash based"
            )
        else:
            versioning = "content"  # Always content-based for non-history modes
        
        # Target subdirectory
        target_subdir = st.text_input(
            "Target Subdirectory (optional)",
            value="",
            help="Limit ingestion to specific subdirectory"
        )
        
        # Submit
        submitted = st.form_submit_button("Start Ingestion")
        
        if submitted:
            # Start ingestion
            response = requests.post(
                f"{API_URL}/api/v1/admin/ingest",
                json={
                    "repo_path": repo_path,
                    "mode": mode,
                    "ingestion_mode": ingestion_mode,
                    "versioning_preference": versioning,
                    "target_subdirectory": target_subdir if target_subdir else None
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                st.success(f"✅ Ingestion started! Job ID: {data['job_id']}")
                
                # Show expected time
                if ingestion_mode == "git_snapshot":
                    st.info("⏱️ Expected time: 5-15 minutes")
                elif ingestion_mode == "git_history":
                    st.warning("⏱️ Expected time: 2-4 hours")
                else:
                    st.info("⏱️ Expected time: 5-15 minutes")
            else:
                st.error(f"❌ Failed: {response.text}")
```

**Files to Modify:**
- `services/ecosystem-mcp-dashboard/dashboard_views/ingestion_manager.py` (update form UI)

---

### Phase 6: Update Duplicate Detection

**Goal:** Make CommitOptimizer work with non-Git documents

**Changes:**

```python
# services/ecosystem-mcp/src/services/ingestion/commit_optimizer.py (REFACTORED)
class DuplicateDetector:
    """
    Detects duplicate documents (replaces CommitOptimizer).
    
    Works with both Git and non-Git documents.
    Uses content hashing for universal duplicate detection.
    """
    
    def __init__(self, use_bloom_filter: bool = True):
        self.use_bloom_filter = use_bloom_filter
        if use_bloom_filter:
            self.bloom = BloomFilter(redis_key="bloom:content_hashes")
    
    async def is_duplicate_content(self, content_hash: str) -> bool:
        """
        Check if content hash already exists.
        
        Works for both Git and non-Git documents.
        """
        # Check Bloom filter first (fast negative check)
        if self.use_bloom_filter:
            might_exist = await self.bloom.contains(content_hash)
            if not might_exist:
                return False  # Definitely not duplicate
        
        # Check database
        db = get_database()
        async with db.session() as session:
            result = await session.execute(
                select(DocumentModel.id)
                .where(DocumentModel.content_hash == content_hash)
                .limit(1)
            )
            
            exists = result.first() is not None
            
            # Add to Bloom filter if exists
            if exists and self.use_bloom_filter:
                await self.bloom.add(content_hash)
            
            return exists
    
    async def batch_check_content_hashes(
        self,
        content_hashes: List[str]
    ) -> Set[str]:
        """
        Batch check content hashes (Phase 2 optimization).
        
        Works for both Git and non-Git documents.
        """
        if not content_hashes:
            return set()
        
        # Bloom filter pre-check
        if self.use_bloom_filter:
            bloom_results = await self.bloom.check_batch(content_hashes)
            definitely_not = [h for h, might_exist in bloom_results.items() if not might_exist]
            might_exist = [h for h, might_exist in bloom_results.items() if might_exist]
            
            logger.info(
                f"🎯 Bloom filter: {len(definitely_not)} definitely new, "
                f"{len(might_exist)} need DB check"
            )
            
            hashes_to_check = might_exist
        else:
            hashes_to_check = content_hashes
        
        if not hashes_to_check:
            return set()
        
        # Database batch check
        db = get_database()
        async with db.session() as session:
            result = await session.execute(
                select(DocumentModel.content_hash)
                .where(DocumentModel.content_hash.in_(hashes_to_check))
                .distinct()
            )
            
            existing_hashes = {row[0] for row in result.fetchall()}
            
            # Update Bloom filter
            if existing_hashes and self.use_bloom_filter:
                await self.bloom.add_batch(list(existing_hashes))
            
            logger.info(
                f"✅ Database check: {len(existing_hashes)}/{len(hashes_to_check)} duplicates"
            )
            
            return existing_hashes
    
    # DEPRECATED: Git-specific methods (keep for backward compatibility)
    async def check_commit_already_ingested(self, commit_sha: str) -> Dict[str, Any]:
        """
        DEPRECATED: Use is_duplicate_content() instead.
        
        Kept for backward compatibility with git_history mode.
        """
        logger.warning("check_commit_already_ingested() is deprecated, use is_duplicate_content()")
        
        db = get_database()
        async with db.session() as session:
            result = await session.execute(
                select(
                    func.count(DocumentModel.id).label('count'),
                    func.min(DocumentModel.created_at).label('first_ingested')
                )
                .where(DocumentModel.git_commit_sha == commit_sha)
            )
            
            row = result.first()
            
            if row and row.count > 0:
                return {
                    "already_ingested": True,
                    "document_count": row.count,
                    "ingested_at": row.first_ingested
                }
            
            return {
                "already_ingested": False,
                "document_count": 0,
                "ingested_at": None
            }


# Factory function (updated)
_duplicate_detector_instance = None

def get_duplicate_detector(use_bloom_filter: bool = True) -> DuplicateDetector:
    """Get singleton duplicate detector instance."""
    global _duplicate_detector_instance
    if _duplicate_detector_instance is None:
        _duplicate_detector_instance = DuplicateDetector(use_bloom_filter=use_bloom_filter)
    return _duplicate_detector_instance


# Backward compatibility alias
def get_commit_optimizer(use_bloom_filter: bool = True):
    """DEPRECATED: Use get_duplicate_detector() instead."""
    logger.warning("get_commit_optimizer() is deprecated, use get_duplicate_detector()")
    return get_duplicate_detector(use_bloom_filter)
```

**Files to Modify:**
- `services/ecosystem-mcp/src/services/ingestion/commit_optimizer.py` (refactor to DuplicateDetector)

---

### Phase 7: Testing & Documentation

**Goal:** Comprehensive testing and user documentation

**Testing:**

1. **Unit Tests**
   ```python
   # tests/unit/test_ingestion_strategies.py
   async def test_git_snapshot_strategy():
       """Test GitSnapshotStrategy."""
       strategy = GitSnapshotStrategy(repo_path="/test/repo")
       
       docs = []
       async for doc in strategy.discover_documents():
           docs.append(doc)
       
       assert len(docs) > 0
       assert all(doc["versioning_mode"] == "content" for doc in docs)
   
   async def test_filesystem_strategy():
       """Test FileSystemStrategy."""
       strategy = FileSystemStrategy(directory_path="/test/docs")
       
       docs = []
       async for doc in strategy.discover_documents():
           docs.append(doc)
       
       assert len(docs) > 0
       assert all(doc["version_metadata"]["source_type"] == "filesystem" for doc in docs)
   ```

2. **Integration Tests**
   ```python
   # tests/integration/test_dual_mode_ingestion.py
   async def test_git_snapshot_vs_history_speed():
       """Verify snapshot mode is 10-100× faster."""
       # Test with same repo, different modes
       
       # Git history mode
       start = time.time()
       job1 = await start_ingestion(mode="git_history")
       await wait_for_completion(job1)
       history_time = time.time() - start
       
       # Git snapshot mode
       start = time.time()
       job2 = await start_ingestion(mode="git_snapshot")
       await wait_for_completion(job2)
       snapshot_time = time.time() - start
       
       # Verify speedup
       speedup = history_time / snapshot_time
       assert speedup >= 10, f"Expected 10× speedup, got {speedup:.1f}×"
   ```

3. **E2E Tests**
   ```python
   # tests/e2e/test_ingestion_modes.py
   async def test_full_ingestion_workflow():
       """Test complete ingestion workflow for all modes."""
       
       # Test 1: Git snapshot mode
       response = await client.post("/api/v1/admin/ingest", json={
           "repo_path": "/test/repo",
           "ingestion_mode": "git_snapshot"
       })
       assert response.status_code == 200
       
       # Test 2: File system mode
       response = await client.post("/api/v1/admin/ingest", json={
           "repo_path": "/test/docs",
           "ingestion_mode": "filesystem"
       })
       assert response.status_code == 200
   ```

**Documentation:**

1. **User Guide**
   ```markdown
   # Ingestion Modes Guide
   
   ## Which Mode Should I Use?
   
   ### Git Snapshot Mode (Recommended) 🚀
   **Use when:** You want current documentation, fast
   **Speed:** 5-15 minutes for 5,000 docs
   **Example:** Initial knowledge base setup, CI/CD builds
   
   ### Git History Mode 🐢
   **Use when:** You need full version history
   **Speed:** 2-4 hours for 5,000 docs
   **Example:** Compliance, audit trails, research
   
   ### File System Mode 📁
   **Use when:** Documents not in Git
   **Speed:** 5-15 minutes for 5,000 docs
   **Example:** SharePoint, network shares, cloud storage
   ```

2. **API Documentation**
   ```python
   # Update OpenAPI schema
   @router.post("/ingest")
   async def start_ingestion(request: IngestRequest):
       """
       Start document ingestion.
       
       ## Ingestion Modes
       
       ### git_snapshot (Recommended)
       - Scans current files in Git repo
       - 10-100× faster than git_history
       - Perfect for initial setup or CI/CD
       
       ### git_history
       - Walks full Git commit history
       - Tracks all versions
       - Slow but comprehensive
       
       ### filesystem
       - No Git required
       - Scans any directory
       - Perfect for non-Git documents
       """
   ```

**Files to Create:**
- `tests/unit/test_ingestion_strategies.py`
- `tests/integration/test_dual_mode_ingestion.py`
- `tests/e2e/test_ingestion_modes.py`
- `docs/INGESTION_MODES_GUIDE.md`
- `docs/MIGRATION_GUIDE_GIT_OPTIONAL.md`

---

## 📊 Performance Comparison

### Benchmark: 5,000 Documents

| Mode | Time | Speedup | Use Case |
|------|------|---------|----------|
| **Git History (current)** | 2-4 hours | 1× (baseline) | Full version history needed |
| **Git Snapshot (NEW)** | 5-15 minutes | **10-100×** | Current docs only |
| **File System (NEW)** | 5-15 minutes | **10-100×** | Non-Git documents |

### Why So Fast?

**Git History Mode (current):**
```
1. Walk 12,000 commits (slow)
2. For each commit:
   - Extract file tree (slow)
   - Read file content from Git objects (slow)
   - Check duplicates against history (slow)
3. Process 12,171 documents (11,178 duplicates!)

Total: 2-4 hours
```

**Git Snapshot Mode (NEW):**
```
1. Scan current directory (fast)
2. Read files from file system (fast)
3. Hash content (fast)
4. Check duplicates (fast, Bloom filter)
5. Store unique documents

Total: 5-15 minutes (96% faster!)
```

---

## 🎯 Migration Strategy

### Phase 1: Database (Week 1)
- Run migration scripts
- Add new columns
- Test backward compatibility

### Phase 2: Strategies (Week 2)
- Implement strategy pattern
- Create GitSnapshotStrategy
- Create FileSystemStrategy

### Phase 3: Integration (Week 3)
- Refactor JobProcessor
- Update API endpoints
- Update Dashboard UI

### Phase 4: Testing (Week 4)
- Unit tests
- Integration tests
- E2E tests
- Performance benchmarks

### Phase 5: Documentation (Week 5)
- User guides
- API docs
- Migration guide
- Video tutorials

### Phase 6: Rollout (Week 6)
- Beta testing
- Gradual rollout
- Monitor performance
- Gather feedback

---

## 🚨 Risks & Mitigation

### Risk 1: Breaking Changes

**Risk:** Existing code depends on Git fields

**Mitigation:**
- Make git_commit_sha nullable, not removed
- Keep backward compatibility
- Gradual deprecation (6 months)
- Comprehensive testing

### Risk 2: Data Migration

**Risk:** Existing documents need schema update

**Mitigation:**
- Run migration in transaction
- Backup database first
- Test on staging
- Rollback plan ready

### Risk 3: Performance Regression

**Risk:** New code slower than current

**Mitigation:**
- Benchmark before/after
- Keep optimizations (Bloom filter, batching)
- Profile hot paths
- Load testing

### Risk 4: User Confusion

**Risk:** Too many options, unclear which to use

**Mitigation:**
- Default to git_snapshot (fast mode)
- Clear UI guidance
- Tooltips and help text
- Video tutorials

---

## ✅ Success Criteria

1. **Performance:**
   - Git snapshot mode: 10-100× faster than history mode ✅
   - File system mode: 10-100× faster than history mode ✅

2. **Functionality:**
   - All three modes work correctly ✅
   - Backward compatibility maintained ✅
   - No data loss ✅

3. **User Experience:**
   - Clear mode selection in UI ✅
   - Accurate time estimates ✅
   - Helpful error messages ✅

4. **Quality:**
   - 90%+ test coverage ✅
   - Zero critical bugs ✅
   - Performance benchmarks pass ✅

---

## 📚 Related Documents

- `PERFORMANCE_TEST_SUCCESS.md` - Current performance baseline
- `JOB_STUCK_INVESTIGATION_COMPLETE.md` - Git bottleneck analysis
- `NON_GIT_REPOSITORY_GUIDE.md` - Content-based versioning
- `FASTMCP_CRITICAL_ANALYSIS.md` - Architecture analysis

---

## 🎉 Conclusion

### The Problem
- Git history scanning is slow (2-4 hours)
- 95% of time wasted on unused history
- Can't ingest non-Git documents

### The Solution
- Make Git history optional
- Add fast snapshot mode (10-100× faster!)
- Support file system ingestion

### The Impact
- **10-100× faster** for common use cases
- **Broader use cases** (non-Git documents)
- **Better UX** (clear mode selection)
- **Backward compatible** (existing code works)

### Next Steps
**DO NOT IMPLEMENT YET!**

This is a planning document. Review, discuss, and approve before implementation.

---

**Document Status:** 🔴 PLANNING ONLY - DO NOT IMPLEMENT  
**Estimated Effort:** 6 weeks (1 developer)  
**Expected ROI:** 10-100× performance improvement for 80% of use cases  
**Last Updated:** October 20, 2025


---

## 🤖 Phase 8: Intelligent Code Analysis with CodeLlama (NEW ENHANCEMENT)

### Goal
Automatically detect code files during ingestion and switch from regular Ollama models to CodeLlama for specialized code analysis, generating rich metadata and insights.

---

### Overview

**Problem:** Current system treats all files equally during ingestion. Code files (`.py`, `.js`, `.ts`, `.java`, etc.) contain structured information that could be better analyzed by specialized code models.

**Solution:** Add intelligent file type detection and automatic model switching to CodeLlama for code files, generating:
- Code complexity metrics
- Function/class summaries
- Dependency analysis
- Code quality insights
- Security pattern detection
- Architecture recommendations

**Performance Impact:**
- Code files: +2-5 seconds per file (deeper analysis)
- Non-code files: No change (same speed)
- Overall: +10-15% time for repos with 50% code files
- Value: 10× better code understanding and searchability

---

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  INGESTION PIPELINE                          │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
            ┌─────────────────────────┐
            │  File Type Detection    │
            │  (Extension + Content)  │
            └─────────────────────────┘
                          │
          ┌───────────────┴───────────────┐
          │                               │
          ▼                               ▼
┌───────────────────┐         ┌───────────────────┐
│  CODE FILES       │         │  NON-CODE FILES   │
│  (.py, .js, .ts,  │         │  (.md, .txt,      │
│   .java, .go...)  │         │   .yaml...)       │
└───────────────────┘         └───────────────────┘
          │                               │
          ▼                               ▼
┌───────────────────┐         ┌───────────────────┐
│  CodeNormalizer   │         │  Regular          │
│  (NEW!)           │         │  Normalizers      │
│                   │         │  (Existing)       │
│  • AST parsing    │         │                   │
│  • Complexity     │         │  • Markdown       │
│  • Dependencies   │         │  • Python         │
└───────────────────┘         │  • Text           │
          │                   └───────────────────┘
          ▼                               │
┌───────────────────┐                     │
│  CodeLlama        │                     │
│  Analysis         │                     │
│  (NEW!)           │                     │
│                   │                     │
│  • Summarize      │                     │
│  • Analyze        │                     │
│  • Recommend      │                     │
└───────────────────┘                     │
          │                               │
          └───────────────┬───────────────┘
                          ▼
              ┌───────────────────────┐
              │  Enhanced Document    │
              │  with Code Metadata   │
              └───────────────────────┘
                          │
                          ▼
          ┌───────────────────────────────┐
          │  Storage (PostgreSQL +        │
          │  ChromaDB with rich metadata) │
          └───────────────────────────────┘
```

---

### Implementation Details

#### 1. Code File Detection

**File:** `services/ecosystem-mcp/src/services/processing/code_detector.py` (NEW)

```python
"""
Code File Detector

Detects code files and determines programming language.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any
import re

logger = logging.getLogger(__name__)


class CodeFileDetector:
    """
    Detects code files and identifies programming language.
    
    Uses both extension and content analysis for accuracy.
    """
    
    # Programming language extensions
    CODE_EXTENSIONS = {
        # Python
        '.py': 'python',
        '.pyw': 'python',
        '.pyx': 'python',
        
        # JavaScript/TypeScript
        '.js': 'javascript',
        '.jsx': 'javascript',
        '.ts': 'typescript',
        '.tsx': 'typescript',
        '.mjs': 'javascript',
        '.cjs': 'javascript',
        
        # Java/Kotlin
        '.java': 'java',
        '.kt': 'kotlin',
        '.kts': 'kotlin',
        
        # C/C++
        '.c': 'c',
        '.cpp': 'cpp',
        '.cc': 'cpp',
        '.cxx': 'cpp',
        '.h': 'c_header',
        '.hpp': 'cpp_header',
        
        # Go
        '.go': 'go',
        
        # Rust
        '.rs': 'rust',
        
        # Ruby
        '.rb': 'ruby',
        
        # PHP
        '.php': 'php',
        
        # C#
        '.cs': 'csharp',
        
        # Swift
        '.swift': 'swift',
        
        # Scala
        '.scala': 'scala',
        
        # Shell
        '.sh': 'shell',
        '.bash': 'shell',
        '.zsh': 'shell',
        
        # SQL
        '.sql': 'sql',
        
        # R
        '.r': 'r',
        '.R': 'r',
    }
    
    # Shebang patterns for language detection
    SHEBANG_PATTERNS = {
        r'#!/usr/bin/env python': 'python',
        r'#!/usr/bin/python': 'python',
        r'#!/usr/bin/env node': 'javascript',
        r'#!/bin/bash': 'shell',
        r'#!/bin/sh': 'shell',
    }
    
    def is_code_file(self, file_path: str, content: Optional[str] = None) -> bool:
        """
        Check if file is a code file.
        
        Args:
            file_path: Path to file
            content: Optional file content for deeper analysis
        
        Returns:
            True if code file
        """
        ext = Path(file_path).suffix.lower()
        
        # Check extension
        if ext in self.CODE_EXTENSIONS:
            return True
        
        # Check shebang if content provided
        if content:
            return self._check_shebang(content) is not None
        
        return False
    
    def detect_language(self, file_path: str, content: Optional[str] = None) -> Optional[str]:
        """
        Detect programming language.
        
        Args:
            file_path: Path to file
            content: Optional file content for deeper analysis
        
        Returns:
            Language name or None
        """
        ext = Path(file_path).suffix.lower()
        
        # Check extension first
        if ext in self.CODE_EXTENSIONS:
            return self.CODE_EXTENSIONS[ext]
        
        # Check shebang
        if content:
            shebang_lang = self._check_shebang(content)
            if shebang_lang:
                return shebang_lang
        
        return None
    
    def _check_shebang(self, content: str) -> Optional[str]:
        """Check shebang line for language hints."""
        if not content.startswith('#!'):
            return None
        
        first_line = content.split('\n')[0]
        
        for pattern, language in self.SHEBANG_PATTERNS.items():
            if re.match(pattern, first_line):
                return language
        
        return None
    
    def get_language_metadata(self, language: str) -> Dict[str, Any]:
        """
        Get metadata about a programming language.
        
        Args:
            language: Language name
        
        Returns:
            Metadata dict
        """
        metadata = {
            'python': {
                'family': 'scripting',
                'paradigm': ['object-oriented', 'functional', 'imperative'],
                'typical_use': ['web', 'data-science', 'automation', 'ml'],
                'codellama_optimized': True
            },
            'javascript': {
                'family': 'scripting',
                'paradigm': ['object-oriented', 'functional', 'event-driven'],
                'typical_use': ['web', 'frontend', 'backend', 'mobile'],
                'codellama_optimized': True
            },
            'typescript': {
                'family': 'scripting',
                'paradigm': ['object-oriented', 'functional'],
                'typical_use': ['web', 'frontend', 'backend'],
                'codellama_optimized': True
            },
            'java': {
                'family': 'compiled',
                'paradigm': ['object-oriented'],
                'typical_use': ['enterprise', 'android', 'backend'],
                'codellama_optimized': True
            },
            'go': {
                'family': 'compiled',
                'paradigm': ['concurrent', 'imperative'],
                'typical_use': ['backend', 'cloud', 'systems'],
                'codellama_optimized': True
            },
            'rust': {
                'family': 'compiled',
                'paradigm': ['systems', 'functional'],
                'typical_use': ['systems', 'performance', 'safety'],
                'codellama_optimized': True
            },
        }
        
        return metadata.get(language, {
            'family': 'unknown',
            'paradigm': [],
            'typical_use': [],
            'codellama_optimized': False
        })


# Singleton instance
_detector_instance = None

def get_code_detector() -> CodeFileDetector:
    """Get singleton code detector instance."""
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = CodeFileDetector()
    return _detector_instance
```

---

#### 2. CodeLlama Analyzer

**File:** `services/ecosystem-mcp/src/services/analysis/codellama_analyzer.py` (NEW)

```python
"""
CodeLlama Analyzer

Uses CodeLlama model for deep code analysis.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
import json

from ...services.models.ollama_client import get_ollama_client
from ...config import settings

logger = logging.getLogger(__name__)


class CodeLlamaAnalyzer:
    """
    Analyzes code using CodeLlama model.
    
    Provides:
    - Code summarization
    - Complexity analysis
    - Dependency extraction
    - Security pattern detection
    - Architecture recommendations
    """
    
    def __init__(self, model_name: str = "codellama:7b"):
        """
        Initialize CodeLlama analyzer.
        
        Args:
            model_name: CodeLlama model to use
                       Options: codellama:7b, codellama:13b, codellama:34b
        """
        self.model_name = model_name
        self.ollama_client = get_ollama_client()
        self.timeout = 60  # 60 seconds for code analysis
    
    async def analyze_code(
        self,
        code: str,
        file_path: str,
        language: str,
        ast_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Perform comprehensive code analysis.
        
        Args:
            code: Source code
            file_path: File path
            language: Programming language
            ast_info: Optional AST parsing results
        
        Returns:
            Analysis results dict
        """
        logger.info(f"🤖 Analyzing {file_path} with CodeLlama ({language})")
        
        try:
            # Run analyses in parallel
            summary_task = self._generate_summary(code, file_path, language)
            complexity_task = self._analyze_complexity(code, language, ast_info)
            dependencies_task = self._extract_dependencies(code, language)
            security_task = self._check_security_patterns(code, language)
            
            # Wait for all analyses
            summary, complexity, dependencies, security = await asyncio.gather(
                summary_task,
                complexity_task,
                dependencies_task,
                security_task,
                return_exceptions=True
            )
            
            # Handle exceptions
            if isinstance(summary, Exception):
                logger.error(f"Summary failed: {summary}")
                summary = "Analysis failed"
            
            if isinstance(complexity, Exception):
                logger.error(f"Complexity analysis failed: {complexity}")
                complexity = {}
            
            if isinstance(dependencies, Exception):
                logger.error(f"Dependency extraction failed: {dependencies}")
                dependencies = []
            
            if isinstance(security, Exception):
                logger.error(f"Security check failed: {security}")
                security = []
            
            # Combine results
            analysis = {
                "summary": summary,
                "complexity": complexity,
                "dependencies": dependencies,
                "security_patterns": security,
                "language": language,
                "file_path": file_path,
                "model_used": self.model_name,
                "ast_available": ast_info is not None
            }
            
            logger.info(f"✅ CodeLlama analysis complete for {file_path}")
            return analysis
        
        except Exception as e:
            logger.error(f"❌ CodeLlama analysis failed for {file_path}: {e}", exc_info=True)
            return {
                "summary": "Analysis failed",
                "complexity": {},
                "dependencies": [],
                "security_patterns": [],
                "error": str(e)
            }
    
    async def _generate_summary(self, code: str, file_path: str, language: str) -> str:
        """
        Generate high-level code summary.
        
        Uses CodeLlama to understand what the code does.
        """
        prompt = f"""Analyze this {language} code and provide a concise summary.

File: {file_path}

Focus on:
1. Primary purpose and functionality
2. Key classes/functions
3. Design patterns used
4. Notable implementation details

Code:
```{language}
{code[:4000]}  # Limit to 4000 chars
```

Provide a 2-3 sentence summary:"""
        
        try:
            response = await asyncio.wait_for(
                self.ollama_client.generate(
                    model=self.model_name,
                    prompt=prompt,
                    options={"temperature": 0.3, "num_predict": 200}
                ),
                timeout=self.timeout
            )
            
            return response.get("response", "").strip()
        
        except asyncio.TimeoutError:
            logger.warning(f"CodeLlama summary timed out for {file_path}")
            return "Summary generation timed out"
        except Exception as e:
            logger.error(f"CodeLlama summary failed: {e}")
            raise
    
    async def _analyze_complexity(
        self,
        code: str,
        language: str,
        ast_info: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze code complexity.
        
        Combines AST metrics with CodeLlama insights.
        """
        complexity = {
            "lines_of_code": len(code.split('\n')),
            "estimated_complexity": "unknown"
        }
        
        # Add AST-based metrics if available
        if ast_info:
            complexity.update({
                "functions": len(ast_info.get("functions", [])),
                "classes": len(ast_info.get("classes", [])),
                "max_nesting_depth": ast_info.get("max_nesting_depth", 0)
            })
        
        # Ask CodeLlama for complexity assessment
        prompt = f"""Analyze the complexity of this {language} code.

Rate complexity as: LOW, MEDIUM, HIGH, or VERY_HIGH

Consider:
- Cyclomatic complexity
- Nesting depth
- Number of dependencies
- Code duplication

Code:
```{language}
{code[:2000]}
```

Respond with just the complexity rating:"""
        
        try:
            response = await asyncio.wait_for(
                self.ollama_client.generate(
                    model=self.model_name,
                    prompt=prompt,
                    options={"temperature": 0.1, "num_predict": 10}
                ),
                timeout=30
            )
            
            rating = response.get("response", "").strip().upper()
            if rating in ["LOW", "MEDIUM", "HIGH", "VERY_HIGH"]:
                complexity["estimated_complexity"] = rating
        
        except Exception as e:
            logger.warning(f"Complexity rating failed: {e}")
        
        return complexity
    
    async def _extract_dependencies(self, code: str, language: str) -> List[str]:
        """
        Extract code dependencies.
        
        Uses CodeLlama to identify imports and dependencies.
        """
        prompt = f"""List all external dependencies/imports in this {language} code.

Code:
```{language}
{code[:3000]}
```

List dependencies as JSON array:
["dependency1", "dependency2", ...]

Response:"""
        
        try:
            response = await asyncio.wait_for(
                self.ollama_client.generate(
                    model=self.model_name,
                    prompt=prompt,
                    options={"temperature": 0.1, "num_predict": 100}
                ),
                timeout=30
            )
            
            # Try to parse JSON response
            response_text = response.get("response", "").strip()
            
            # Extract JSON array
            import re
            json_match = re.search(r'\[.*?\]', response_text, re.DOTALL)
            if json_match:
                dependencies = json.loads(json_match.group(0))
                return dependencies if isinstance(dependencies, list) else []
        
        except Exception as e:
            logger.warning(f"Dependency extraction failed: {e}")
        
        return []
    
    async def _check_security_patterns(self, code: str, language: str) -> List[Dict[str, str]]:
        """
        Check for security patterns and anti-patterns.
        
        Uses CodeLlama to identify potential security issues.
        """
        prompt = f"""Analyze this {language} code for security concerns.

Code:
```{language}
{code[:3000]}
```

List any security concerns as JSON array:
[
  {{"pattern": "SQL Injection Risk", "severity": "HIGH", "line": "approximate line"}},
  ...
]

If no concerns, return empty array: []

Response:"""
        
        try:
            response = await asyncio.wait_for(
                self.ollama_client.generate(
                    model=self.model_name,
                    prompt=prompt,
                    options={"temperature": 0.2, "num_predict": 200}
                ),
                timeout=40
            )
            
            # Try to parse JSON response
            response_text = response.get("response", "").strip()
            
            # Extract JSON array
            import re
            json_match = re.search(r'\[.*?\]', response_text, re.DOTALL)
            if json_match:
                patterns = json.loads(json_match.group(0))
                return patterns if isinstance(patterns, list) else []
        
        except Exception as e:
            logger.warning(f"Security check failed: {e}")
        
        return []


# Singleton instance
_analyzer_instance = None

def get_codellama_analyzer(model_name: str = "codellama:7b") -> CodeLlamaAnalyzer:
    """Get singleton CodeLlama analyzer instance."""
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = CodeLlamaAnalyzer(model_name=model_name)
    return _analyzer_instance
```

---

#### 3. Enhanced Code Normalizer

**File:** `services/ecosystem-mcp/src/services/processing/code_normalizer.py` (NEW)

```python
"""
Code Normalizer

Enhanced normalizer for code files with CodeLlama analysis.
"""

import logging
import ast
import hashlib
from typing import Dict, Any, Optional

from .base_normalizer import BaseNormalizer
from ..analysis.codellama_analyzer import get_codellama_analyzer
from .code_detector import get_code_detector

logger = logging.getLogger(__name__)


class CodeNormalizer(BaseNormalizer):
    """
    Normalizer for code files with CodeLlama analysis.
    
    Features:
    - AST parsing (for supported languages)
    - CodeLlama deep analysis
    - Complexity metrics
    - Dependency extraction
    - Security pattern detection
    - Rich metadata generation
    """
    
    def __init__(self, enable_codellama: bool = True):
        """
        Initialize code normalizer.
        
        Args:
            enable_codellama: Enable CodeLlama analysis (adds 2-5s per file)
        """
        self.enable_codellama = enable_codellama
        self.code_detector = get_code_detector()
        if enable_codellama:
            self.codellama_analyzer = get_codellama_analyzer()
    
    async def normalize(
        self,
        content: str,
        file_path: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Normalize code file with deep analysis.
        
        Args:
            content: Raw code content
            file_path: Path to file
            metadata: Additional metadata
        
        Returns:
            Dict with normalized content and rich metadata
        """
        # Detect language
        language = self.code_detector.detect_language(file_path, content)
        
        if not language:
            logger.warning(f"Could not detect language for {file_path}, using text normalizer")
            # Fall back to text normalizer
            from .text_normalizer import TextNormalizer
            return await TextNormalizer().normalize(content, file_path, metadata)
        
        logger.info(f"📝 Normalizing {language} code: {file_path}")
        
        # Parse AST (if supported)
        ast_info = None
        if language == 'python':
            ast_info = self._parse_python_ast(content)
        # TODO: Add AST parsers for other languages
        
        # Run CodeLlama analysis (if enabled)
        codellama_analysis = None
        if self.enable_codellama:
            try:
                codellama_analysis = await self.codellama_analyzer.analyze_code(
                    code=content,
                    file_path=file_path,
                    language=language,
                    ast_info=ast_info
                )
            except Exception as e:
                logger.error(f"CodeLlama analysis failed for {file_path}: {e}")
                codellama_analysis = {"error": str(e)}
        
        # Build markdown representation
        markdown = self._build_markdown(
            content=content,
            file_path=file_path,
            language=language,
            ast_info=ast_info,
            codellama_analysis=codellama_analysis
        )
        
        # Build enhanced metadata
        enhanced_metadata = {
            **metadata,
            "service": self._extract_service_name(file_path),
            "file_type": "code",
            "language": language,
            "language_metadata": self.code_detector.get_language_metadata(language),
            "lines_of_code": len(content.split('\n')),
            "content_hash": hashlib.sha256(content.encode()).hexdigest(),
        }
        
        # Add AST metadata
        if ast_info:
            enhanced_metadata.update({
                "ast_functions": len(ast_info.get("functions", [])),
                "ast_classes": len(ast_info.get("classes", [])),
                "ast_imports": len(ast_info.get("imports", [])),
            })
        
        # Add CodeLlama metadata
        if codellama_analysis and "error" not in codellama_analysis:
            enhanced_metadata.update({
                "codellama_summary": codellama_analysis.get("summary"),
                "codellama_complexity": codellama_analysis.get("complexity", {}).get("estimated_complexity"),
                "codellama_dependencies": codellama_analysis.get("dependencies", []),
                "codellama_security_issues": len(codellama_analysis.get("security_patterns", [])),
                "codellama_analyzed": True
            })
        else:
            enhanced_metadata["codellama_analyzed"] = False
        
        return {
            "content": markdown,
            "metadata": enhanced_metadata,
            "tokens": self._estimate_tokens(markdown),
            "codellama_analysis": codellama_analysis  # Full analysis for storage
        }
    
    def _parse_python_ast(self, content: str) -> Optional[Dict[str, Any]]:
        """Parse Python code with AST."""
        try:
            tree = ast.parse(content)
            
            functions = []
            classes = []
            imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append({
                        "name": node.name,
                        "lineno": node.lineno,
                        "args": [arg.arg for arg in node.args.args]
                    })
                elif isinstance(node, ast.ClassDef):
                    classes.append({
                        "name": node.name,
                        "lineno": node.lineno
                    })
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, ast.Import):
                        imports.extend([alias.name for alias in node.names])
                    else:
                        imports.append(node.module)
            
            return {
                "functions": functions,
                "classes": classes,
                "imports": list(set(imports))
            }
        
        except Exception as e:
            logger.warning(f"AST parsing failed: {e}")
            return None
    
    def _build_markdown(
        self,
        content: str,
        file_path: str,
        language: str,
        ast_info: Optional[Dict[str, Any]],
        codellama_analysis: Optional[Dict[str, Any]]
    ) -> str:
        """Build markdown representation with analysis."""
        lines = []
        
        # Header
        lines.append(f"# Code: {file_path}")
        lines.append("")
        lines.append(f"**Language**: {language}")
        lines.append(f"**Lines**: {len(content.split('\\n'))}")
        lines.append("")
        
        # CodeLlama Summary
        if codellama_analysis and "summary" in codellama_analysis:
            lines.append("## 🤖 AI Summary")
            lines.append("")
            lines.append(codellama_analysis["summary"])
            lines.append("")
        
        # Complexity
        if codellama_analysis and "complexity" in codellama_analysis:
            complexity = codellama_analysis["complexity"]
            lines.append("## 📊 Complexity Analysis")
            lines.append("")
            lines.append(f"- **Estimated Complexity**: {complexity.get('estimated_complexity', 'Unknown')}")
            if "functions" in complexity:
                lines.append(f"- **Functions**: {complexity['functions']}")
            if "classes" in complexity:
                lines.append(f"- **Classes**: {complexity['classes']}")
            lines.append("")
        
        # Dependencies
        if codellama_analysis and codellama_analysis.get("dependencies"):
            lines.append("## 📦 Dependencies")
            lines.append("")
            for dep in codellama_analysis["dependencies"]:
                lines.append(f"- `{dep}`")
            lines.append("")
        
        # Security Patterns
        if codellama_analysis and codellama_analysis.get("security_patterns"):
            lines.append("## 🔒 Security Analysis")
            lines.append("")
            for pattern in codellama_analysis["security_patterns"]:
                severity = pattern.get("severity", "UNKNOWN")
                pattern_name = pattern.get("pattern", "Unknown")
                lines.append(f"- **{severity}**: {pattern_name}")
            lines.append("")
        
        # AST Structure (if available)
        if ast_info:
            if ast_info.get("classes"):
                lines.append("## 📦 Classes")
                lines.append("")
                for cls in ast_info["classes"]:
                    lines.append(f"- `{cls['name']}` (line {cls['lineno']})")
                lines.append("")
            
            if ast_info.get("functions"):
                lines.append("## 🔧 Functions")
                lines.append("")
                for func in ast_info["functions"]:
                    args = ", ".join(func["args"])
                    lines.append(f"- `{func['name']}({args})` (line {func['lineno']})")
                lines.append("")
        
        # Source Code
        lines.append("## 📄 Source Code")
        lines.append("")
        lines.append(f"```{language}")
        lines.append(content)
        lines.append("```")
        
        return "\\n".join(lines)
```

---

#### 4. Update Normalizer Factory

**File:** `services/ecosystem-mcp/src/services/processing/normalizer_factory.py` (MODIFIED)

```python
"""
Normalizer Factory

Factory for creating appropriate normalizer based on file extension.
"""

import logging
from typing import Dict

from .base_normalizer import BaseNormalizer
from .markdown_normalizer import MarkdownNormalizer
from .python_normalizer import PythonNormalizer
from .text_normalizer import TextNormalizer
from .code_normalizer import CodeNormalizer  # NEW
from .code_detector import get_code_detector  # NEW

logger = logging.getLogger(__name__)


class NormalizerFactory:
    """
    Factory for creating document normalizers.
    
    Returns the appropriate normalizer based on file extension.
    Now includes intelligent code file detection with CodeLlama analysis.
    """
    
    def __init__(self, enable_codellama: bool = True):
        """
        Initialize the factory with normalizer instances.
        
        Args:
            enable_codellama: Enable CodeLlama analysis for code files
        """
        self.enable_codellama = enable_codellama
        self.code_detector = get_code_detector()
        
        self._normalizers: Dict[str, BaseNormalizer] = {
            # Markdown files
            '.md': MarkdownNormalizer(),
            '.markdown': MarkdownNormalizer(),
            '.rst': MarkdownNormalizer(),
            
            # Config/data files (non-code)
            '.yaml': TextNormalizer(),
            '.yml': TextNormalizer(),
            '.json': TextNormalizer(),
            '.toml': TextNormalizer(),
            '.ini': TextNormalizer(),
            '.cfg': TextNormalizer(),
            '.conf': TextNormalizer(),
            '.txt': TextNormalizer(),
        }
        
        # Code normalizer (NEW - used for all code files)
        self._code_normalizer = CodeNormalizer(enable_codellama=enable_codellama)
        
        # Default normalizer for unknown types
        self._default_normalizer = TextNormalizer()
    
    def get_normalizer(self, file_ext: str, file_path: str = "") -> BaseNormalizer:
        """
        Get the appropriate normalizer for a file extension.
        
        Now intelligently detects code files and uses CodeNormalizer with CodeLlama.
        
        Args:
            file_ext: File extension (with leading dot, e.g., '.py')
            file_path: Full file path (for better detection)
        
        Returns:
            Normalizer instance
        """
        # Check if it's a code file
        if self.code_detector.is_code_file(file_path or file_ext):
            logger.info(f"🤖 Using CodeNormalizer with CodeLlama for {file_ext}")
            return self._code_normalizer
        
        # Use specific normalizer
        normalizer = self._normalizers.get(file_ext.lower(), self._default_normalizer)
        logger.debug(f"Using {normalizer.__class__.__name__} for {file_ext}")
        return normalizer
```

---

#### 5. Configuration

**File:** `services/ecosystem-mcp/src/config.py` (ADD)

```python
# CodeLlama Analysis Settings
codellama_enabled: bool = Field(
    default=True,
    description="Enable CodeLlama analysis for code files"
)

codellama_model: str = Field(
    default="codellama:7b",
    description="CodeLlama model to use (codellama:7b, codellama:13b, codellama:34b)"
)

codellama_timeout: int = Field(
    default=60,
    description="Timeout for CodeLlama analysis (seconds)"
)

codellama_parallel: bool = Field(
    default=True,
    description="Run CodeLlama analyses in parallel"
)
```

---

#### 6. Dashboard UI Enhancement

**File:** `services/ecosystem-mcp-dashboard/dashboard_views/ingestion_manager.py` (ADD)

```python
# In the ingestion form, add CodeLlama toggle
st.markdown("### 🤖 Code Analysis")

enable_codellama = st.checkbox(
    "Enable CodeLlama Analysis",
    value=True,
    help="""
    Use CodeLlama to analyze code files:
    • Generates AI summaries
    • Analyzes complexity
    • Extracts dependencies
    • Detects security patterns
    
    Impact: +2-5 seconds per code file
    """
)

if enable_codellama:
    codellama_model = st.selectbox(
        "CodeLlama Model",
        options=["codellama:7b", "codellama:13b", "codellama:34b"],
        help="Larger models = better analysis but slower"
    )
else:
    codellama_model = None

# Include in request
response = requests.post(
    f"{API_URL}/api/v1/admin/ingest",
    json={
        # ... existing fields ...
        "enable_codellama": enable_codellama,
        "codellama_model": codellama_model
    }
)
```

---

### Performance Impact

#### Benchmark: 1,000 Files (50% code, 50% docs)

| Mode | Time | Details |
|------|------|---------|
| **Without CodeLlama** | 5 minutes | Standard normalization only |
| **With CodeLlama (7b)** | 6-7 minutes | +2-3s per code file (500 files) |
| **With CodeLlama (13b)** | 7-9 minutes | +3-5s per code file (better analysis) |
| **With CodeLlama (34b)** | 10-15 minutes | +5-10s per code file (best analysis) |

**Recommendation:** Use `codellama:7b` for fast analysis, `codellama:13b` for production.

---

### Use Cases

#### 1. Code Search & Understanding
```
User: "Find all functions that handle authentication"

System:
  • Searches CodeLlama summaries
  • Finds: auth_handler.py, login_service.py, token_validator.py
  • Shows AI-generated summaries of each
  • Highlights security patterns detected
```

#### 2. Dependency Analysis
```
User: "What services depend on Redis?"

System:
  • Queries codellama_dependencies metadata
  • Lists all files importing redis
  • Shows dependency graph
  • Identifies potential issues
```

#### 3. Security Audit
```
User: "Find potential SQL injection risks"

System:
  • Filters by codellama_security_issues > 0
  • Shows files with SQL-related security patterns
  • Displays CodeLlama's analysis
  • Suggests fixes
```

#### 4. Code Quality Metrics
```
User: "Show me the most complex code files"

System:
  • Sorts by codellama_complexity
  • Lists VERY_HIGH complexity files
  • Shows refactoring recommendations
  • Tracks complexity over time
```

---

### Testing Strategy

#### Unit Tests
```python
# tests/unit/test_code_detector.py
def test_detect_python_file():
    detector = CodeFileDetector()
    assert detector.is_code_file("test.py")
    assert detector.detect_language("test.py") == "python"

# tests/unit/test_codellama_analyzer.py
async def test_analyze_python_code():
    analyzer = CodeLlamaAnalyzer()
    analysis = await analyzer.analyze_code(
        code="def hello(): pass",
        file_path="test.py",
        language="python"
    )
    assert "summary" in analysis
    assert "complexity" in analysis
```

#### Integration Tests
```python
# tests/integration/test_code_ingestion.py
async def test_ingest_code_with_codellama():
    """Test code file ingestion with CodeLlama analysis."""
    response = await client.post("/api/v1/admin/ingest", json={
        "repo_path": "/test/code_repo",
        "ingestion_mode": "git_snapshot",
        "enable_codellama": True
    })
    
    # Wait for completion
    job_id = response.json()["job_id"]
    await wait_for_job(job_id)
    
    # Verify CodeLlama metadata
    docs = await get_documents(service="test_repo")
    code_docs = [d for d in docs if d["file_type"] == "code"]
    
    assert len(code_docs) > 0
    for doc in code_docs:
        assert doc["codellama_analyzed"] == True
        assert "codellama_summary" in doc
```

#### E2E Tests
```python
# tests/e2e/test_code_search.py
async def test_search_by_codellama_summary():
    """Test searching code by AI-generated summaries."""
    # Ingest code
    await ingest_code_repo()
    
    # Search by functionality
    results = await search("authentication handler")
    
    # Verify results include code files with relevant summaries
    assert len(results) > 0
    assert any("auth" in r["codellama_summary"].lower() for r in results)
```

---

### Migration Plan

#### Week 1: Core Implementation
- Implement `CodeFileDetector`
- Implement `CodeLlamaAnalyzer`
- Implement `CodeNormalizer`
- Update `NormalizerFactory`

#### Week 2: Integration
- Add configuration settings
- Update API endpoints
- Update Dashboard UI
- Add database fields for CodeLlama metadata

#### Week 3: Testing
- Unit tests
- Integration tests
- E2E tests
- Performance benchmarks

#### Week 4: Optimization
- Parallel analysis
- Caching
- Model selection optimization
- Timeout tuning

#### Week 5: Documentation
- User guide
- API documentation
- Code examples
- Best practices

---

### Risks & Mitigation

#### Risk 1: Performance Impact
**Risk:** CodeLlama analysis adds 2-5s per file

**Mitigation:**
- Make it optional (user can disable)
- Run analyses in parallel
- Cache results for unchanged files
- Use smaller model (7b) by default

#### Risk 2: CodeLlama Not Available
**Risk:** CodeLlama model not installed

**Mitigation:**
- Graceful fallback to standard normalization
- Clear error messages
- Auto-download model on first use
- Preflight check in dashboard

#### Risk 3: Analysis Quality
**Risk:** CodeLlama may produce inaccurate analysis

**Mitigation:**
- Combine with AST parsing (ground truth)
- Use low temperature (0.1-0.3) for factual analysis
- Validate JSON responses
- Log analysis failures

#### Risk 4: Cost/Resource Usage
**Risk:** CodeLlama uses significant CPU/GPU

**Mitigation:**
- Batch processing
- Queue management
- Resource limits
- Monitoring and alerts

---

### Success Criteria

1. **Functionality:**
   - ✅ Automatically detects code files
   - ✅ Switches to CodeLlama for analysis
   - ✅ Generates rich metadata
   - ✅ Graceful fallback if CodeLlama unavailable

2. **Performance:**
   - ✅ Analysis completes in <5s per file (7b model)
   - ✅ Parallel processing works
   - ✅ Overall ingestion time increase <20%

3. **Quality:**
   - ✅ 90%+ accurate language detection
   - ✅ Meaningful summaries generated
   - ✅ Dependencies correctly extracted
   - ✅ Security patterns identified

4. **User Experience:**
   - ✅ Easy to enable/disable
   - ✅ Clear progress indicators
   - ✅ Searchable by code metadata
   - ✅ Helpful error messages

---

### Future Enhancements

1. **Multi-Model Support**
   - StarCoder for code generation
   - WizardCoder for explanations
   - DeepSeek Coder for specific languages

2. **Advanced Analysis**
   - Code smell detection
   - Refactoring suggestions
   - Performance optimization hints
   - Test coverage analysis

3. **Interactive Features**
   - "Explain this code" button
   - "Generate tests" button
   - "Suggest improvements" button
   - Code comparison across versions

4. **Integration**
   - IDE plugins
   - GitHub Actions
   - Code review automation
   - Documentation generation

---

## 📊 Updated Performance Comparison (with Phase 8)

### Benchmark: 5,000 Documents (50% code, 50% docs)

| Mode | Time | CodeLlama | Details |
|------|------|-----------|---------|
| Git History (current) | 2-4 hours | ❌ No | Full Git history, basic normalization |
| **Git Snapshot** | 5-15 min | ❌ No | Current files only, basic normalization |
| **Git Snapshot + CodeLlama (7b)** | 6-18 min | ✅ Yes | Current files + AI code analysis |
| **Git Snapshot + CodeLlama (13b)** | 8-25 min | ✅ Yes | Current files + better AI analysis |

**Recommendation:** Use Git Snapshot + CodeLlama 7b for best balance of speed and intelligence.

---

**Phase 8 Status:** 🔴 PLANNING ONLY - DO NOT IMPLEMENT  
**Estimated Effort:** 5 weeks (1 developer)  
**Expected Value:** 10× better code understanding and searchability  
**Dependencies:** Phases 1-7 must be completed first


---

## 🎯 Phase 9: Context-Aware RAG with Repository Contexts (NEW ENHANCEMENT)

### Goal
Create intelligent repository-specific contexts that weight RAG queries to specific ingested repositories, providing users with focused, context-aware search and auto-generated repository summaries.

---

### Overview

**Problem:** Current system treats all ingested documents equally. When querying, results from `repo1`, `repo2`, and `repo3` are mixed together, making it hard to focus on a specific codebase. No high-level overview of what's in each repository.

**Solution:** Implement repository contexts that:
- Create isolated "context spaces" per ingested repository
- Weight RAG queries to prioritize documents from selected context
- Auto-generate comprehensive repository summaries
- Display key metrics, technologies, endpoints, and architecture
- Work with both Git history and snapshot modes

**User Experience:**
```
User ingests "my-api-service" → Creates "my-api-service" context
User ingests "frontend-app" → Creates "frontend-app" context
User ingests "ml-pipeline" → Creates "ml-pipeline" context

User selects "my-api-service" context:
  → RAG queries weighted to my-api-service documents
  → Dashboard shows my-api-service summary
  → Metrics specific to my-api-service
  → Technologies used in my-api-service
  → Endpoints defined in my-api-service
```

---

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    INGESTION PIPELINE                            │
└─────────────────────────────────────────────────────────────────┘
                          │
                          ▼
            ┌─────────────────────────┐
            │  Repository Context     │
            │  Creation               │
            │                         │
            │  • Extract repo name    │
            │  • Create context ID    │
            │  • Tag all documents    │
            └─────────────────────────┘
                          │
                          ▼
          ┌───────────────────────────────┐
          │  Context Analyzer (NEW!)      │
          │                               │
          │  • Detect technologies        │
          │  • Extract endpoints          │
          │  • Analyze architecture       │
          │  • Generate summary           │
          │  • Calculate metrics          │
          └───────────────────────────────┘
                          │
                          ▼
          ┌───────────────────────────────┐
          │  Context Storage              │
          │                               │
          │  • PostgreSQL (metadata)      │
          │  • ChromaDB (tagged vectors)  │
          │  • Redis (cache)              │
          └───────────────────────────────┘
                          │
          ┌───────────────┴───────────────┐
          │                               │
          ▼                               ▼
┌───────────────────┐         ┌───────────────────┐
│  RAG Query        │         │  Context Summary  │
│  (Context-Aware)  │         │  Dashboard        │
│                   │         │                   │
│  • Filter by      │         │  • Technologies   │
│    context        │         │  • Endpoints      │
│  • Weight results │         │  • Architecture   │
│  • Boost scores   │         │  • Metrics        │
└───────────────────┘         │  • Summary        │
                              └───────────────────┘
```

---

### Database Schema Changes

#### 1. Repository Contexts Table (NEW)

```sql
-- Migration: 002_add_repository_contexts.sql
CREATE TABLE repository_contexts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    context_name VARCHAR(255) NOT NULL UNIQUE,
    context_id VARCHAR(100) NOT NULL UNIQUE,  -- Slug: my-api-service
    display_name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Source information
    repo_path TEXT NOT NULL,
    ingestion_mode VARCHAR(50) NOT NULL,  -- git_history, git_snapshot, filesystem
    git_url TEXT,  -- Optional: Git remote URL
    git_branch VARCHAR(255),  -- Optional: Branch name
    
    -- Metrics
    total_documents INTEGER DEFAULT 0,
    total_lines_of_code INTEGER DEFAULT 0,
    total_functions INTEGER DEFAULT 0,
    total_classes INTEGER DEFAULT 0,
    total_endpoints INTEGER DEFAULT 0,
    
    -- Analysis results (JSONB for flexibility)
    technologies JSONB DEFAULT '[]'::jsonb,  -- ["Python", "FastAPI", "PostgreSQL"]
    endpoints JSONB DEFAULT '[]'::jsonb,  -- [{"path": "/api/users", "method": "GET"}]
    architecture_summary JSONB DEFAULT '{}'::jsonb,  -- {"type": "microservice", "layers": [...]}
    ai_summary TEXT,  -- CodeLlama-generated summary
    
    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_ingestion_at TIMESTAMP,
    
    -- Status
    status VARCHAR(50) DEFAULT 'active',  -- active, archived, analyzing
    
    -- Metadata
    context_metadata JSONB DEFAULT '{}'::jsonb
);

-- Indexes
CREATE INDEX idx_contexts_context_id ON repository_contexts(context_id);
CREATE INDEX idx_contexts_status ON repository_contexts(status);
CREATE INDEX idx_contexts_created_at ON repository_contexts(created_at DESC);

-- Trigger for updated_at
CREATE TRIGGER update_repository_contexts_updated_at
    BEFORE UPDATE ON repository_contexts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

#### 2. Update Documents Table

```sql
-- Migration: 002_add_repository_contexts.sql (continued)
ALTER TABLE documents 
ADD COLUMN context_id VARCHAR(100) REFERENCES repository_contexts(context_id) ON DELETE SET NULL;

CREATE INDEX idx_documents_context_id ON documents(context_id);
CREATE INDEX idx_documents_context_service ON documents(context_id, service_name);
```

#### 3. Context Preferences Table (NEW)

```sql
-- User context preferences (for multi-user future)
CREATE TABLE context_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255),  -- For future multi-user support
    context_id VARCHAR(100) REFERENCES repository_contexts(context_id) ON DELETE CASCADE,
    is_default BOOLEAN DEFAULT FALSE,
    weight FLOAT DEFAULT 1.0,  -- Weight for RAG queries (0.0-1.0)
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_context_prefs_user ON context_preferences(user_id);
CREATE INDEX idx_context_prefs_context ON context_preferences(context_id);
```

---

### Implementation Details

#### 1. Context Manager

**File:** `services/ecosystem-mcp/src/services/context/context_manager.py` (NEW)

```python
"""
Repository Context Manager

Manages repository contexts for context-aware RAG.
"""

import logging
import re
from typing import Dict, Any, List, Optional
from pathlib import Path
from uuid import UUID
from datetime import datetime

from ...storage import get_database
from ...storage.db_models import DocumentModel
from sqlalchemy import select, func, and_

logger = logging.getLogger(__name__)


class ContextManager:
    """
    Manages repository contexts.
    
    Responsibilities:
    - Create/update/delete contexts
    - Extract context from repo path
    - Tag documents with context
    - Query documents by context
    """
    
    @staticmethod
    def extract_context_id(repo_path: str) -> str:
        """
        Extract context ID from repository path.
        
        Examples:
            /host/my-api-service → my-api-service
            /Users/user/projects/frontend-app → frontend-app
            /app/services/ecosystem-mcp → ecosystem-mcp
        
        Args:
            repo_path: Repository path
        
        Returns:
            Context ID (slug)
        """
        path = Path(repo_path)
        
        # Get the last directory name
        repo_name = path.name
        
        # If it's a generic name like 'app' or 'src', go up one level
        generic_names = {'app', 'src', 'services', 'projects', 'repos', 'code'}
        if repo_name.lower() in generic_names and path.parent.name:
            repo_name = path.parent.name
        
        # Convert to slug (lowercase, hyphens, alphanumeric)
        context_id = re.sub(r'[^a-z0-9-]', '-', repo_name.lower())
        context_id = re.sub(r'-+', '-', context_id).strip('-')
        
        logger.info(f"Extracted context ID: {repo_path} → {context_id}")
        return context_id
    
    @staticmethod
    def extract_display_name(repo_path: str, context_id: str) -> str:
        """
        Extract human-readable display name.
        
        Args:
            repo_path: Repository path
            context_id: Context ID
        
        Returns:
            Display name
        """
        # Convert slug to title case
        display_name = context_id.replace('-', ' ').title()
        return display_name
    
    async def create_or_update_context(
        self,
        repo_path: str,
        ingestion_mode: str,
        job_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create or update repository context.
        
        Args:
            repo_path: Repository path
            ingestion_mode: git_history, git_snapshot, filesystem
            job_metadata: Optional metadata from ingestion job
        
        Returns:
            Context dict
        """
        context_id = self.extract_context_id(repo_path)
        display_name = self.extract_display_name(repo_path, context_id)
        
        db = get_database()
        async with db.session() as session:
            # Check if context exists
            from ...storage.db_models import Base
            # Assume RepositoryContextModel exists (we'll create it)
            
            # For now, return dict (actual implementation would use SQLAlchemy)
            context = {
                "context_id": context_id,
                "context_name": context_id,
                "display_name": display_name,
                "repo_path": repo_path,
                "ingestion_mode": ingestion_mode,
                "status": "active",
                "created_at": datetime.utcnow(),
                "metadata": job_metadata or {}
            }
            
            logger.info(f"✅ Created/updated context: {context_id}")
            return context
    
    async def get_context(self, context_id: str) -> Optional[Dict[str, Any]]:
        """
        Get context by ID.
        
        Args:
            context_id: Context ID
        
        Returns:
            Context dict or None
        """
        db = get_database()
        async with db.session() as session:
            # Query context (implementation depends on model)
            # For now, return None
            return None
    
    async def list_contexts(
        self,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        List all contexts.
        
        Args:
            status: Filter by status (active, archived)
            limit: Maximum contexts
        
        Returns:
            List of context dicts
        """
        db = get_database()
        async with db.session() as session:
            # Query contexts
            # For now, return empty list
            return []
    
    async def get_context_documents(
        self,
        context_id: str,
        limit: int = 1000
    ) -> List[DocumentModel]:
        """
        Get all documents for a context.
        
        Args:
            context_id: Context ID
            limit: Maximum documents
        
        Returns:
            List of documents
        """
        db = get_database()
        async with db.session() as session:
            result = await session.execute(
                select(DocumentModel)
                .where(DocumentModel.context_id == context_id)
                .limit(limit)
            )
            return list(result.scalars().all())
    
    async def get_context_metrics(self, context_id: str) -> Dict[str, Any]:
        """
        Calculate metrics for a context.
        
        Args:
            context_id: Context ID
        
        Returns:
            Metrics dict
        """
        db = get_database()
        async with db.session() as session:
            # Count documents
            doc_count = await session.execute(
                select(func.count(DocumentModel.id))
                .where(DocumentModel.context_id == context_id)
            )
            total_docs = doc_count.scalar() or 0
            
            # Count by file type
            file_types = await session.execute(
                select(
                    DocumentModel.original_format,
                    func.count(DocumentModel.id)
                )
                .where(DocumentModel.context_id == context_id)
                .group_by(DocumentModel.original_format)
            )
            
            file_type_counts = {row[0]: row[1] for row in file_types.fetchall()}
            
            # Count code files (if CodeLlama metadata exists)
            code_docs = await session.execute(
                select(func.count(DocumentModel.id))
                .where(
                    and_(
                        DocumentModel.context_id == context_id,
                        DocumentModel.doc_metadata['file_type'].astext == 'code'
                    )
                )
            )
            total_code_files = code_docs.scalar() or 0
            
            return {
                "total_documents": total_docs,
                "total_code_files": total_code_files,
                "file_type_distribution": file_type_counts,
                "context_id": context_id
            }


# Singleton instance
_context_manager_instance = None

def get_context_manager() -> ContextManager:
    """Get singleton context manager instance."""
    global _context_manager_instance
    if _context_manager_instance is None:
        _context_manager_instance = ContextManager()
    return _context_manager_instance
```

---

#### 2. Context Analyzer

**File:** `services/ecosystem-mcp/src/services/context/context_analyzer.py` (NEW)

```python
"""
Context Analyzer

Analyzes ingested repositories to extract technologies, endpoints,
architecture patterns, and generate AI summaries.
"""

import logging
import re
import asyncio
from typing import Dict, Any, List, Set, Optional
from collections import Counter

from ...storage import get_database
from ...storage.db_models import DocumentModel
from ..models.ollama_client import get_ollama_client
from .context_manager import get_context_manager

logger = logging.getLogger(__name__)


class ContextAnalyzer:
    """
    Analyzes repository context to extract key information.
    
    Capabilities:
    - Technology detection (languages, frameworks, databases)
    - Endpoint extraction (REST APIs, GraphQL, gRPC)
    - Architecture pattern recognition
    - AI-powered summary generation
    - Metrics calculation
    """
    
    def __init__(self):
        self.context_manager = get_context_manager()
        self.ollama_client = get_ollama_client()
    
    async def analyze_context(self, context_id: str) -> Dict[str, Any]:
        """
        Perform comprehensive context analysis.
        
        Args:
            context_id: Context ID to analyze
        
        Returns:
            Analysis results
        """
        logger.info(f"🔍 Analyzing context: {context_id}")
        
        # Get all documents for context
        documents = await self.context_manager.get_context_documents(context_id)
        
        if not documents:
            logger.warning(f"No documents found for context: {context_id}")
            return {
                "context_id": context_id,
                "error": "No documents found"
            }
        
        # Run analyses in parallel
        technologies_task = self._detect_technologies(documents)
        endpoints_task = self._extract_endpoints(documents)
        architecture_task = self._analyze_architecture(documents)
        metrics_task = self.context_manager.get_context_metrics(context_id)
        summary_task = self._generate_ai_summary(context_id, documents)
        
        technologies, endpoints, architecture, metrics, ai_summary = await asyncio.gather(
            technologies_task,
            endpoints_task,
            architecture_task,
            metrics_task,
            summary_task
        )
        
        analysis = {
            "context_id": context_id,
            "technologies": technologies,
            "endpoints": endpoints,
            "architecture": architecture,
            "metrics": metrics,
            "ai_summary": ai_summary,
            "analyzed_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"✅ Context analysis complete: {context_id}")
        return analysis
    
    async def _detect_technologies(self, documents: List[DocumentModel]) -> Dict[str, Any]:
        """
        Detect technologies used in the repository.
        
        Detects:
        - Programming languages
        - Frameworks
        - Databases
        - Cloud services
        - Tools
        """
        tech_patterns = {
            # Languages
            "Python": [r"\.py$", r"import\s+", r"from\s+\w+\s+import"],
            "JavaScript": [r"\.js$", r"\.jsx$", r"require\(", r"import\s+.*\s+from"],
            "TypeScript": [r"\.ts$", r"\.tsx$", r"interface\s+\w+", r"type\s+\w+\s*="],
            "Java": [r"\.java$", r"public\s+class", r"import\s+java\."],
            "Go": [r"\.go$", r"package\s+main", r"func\s+\w+"],
            "Rust": [r"\.rs$", r"fn\s+\w+", r"use\s+std::"],
            
            # Frameworks
            "FastAPI": [r"from\s+fastapi\s+import", r"@app\.(get|post|put|delete)"],
            "Flask": [r"from\s+flask\s+import", r"@app\.route"],
            "Django": [r"from\s+django", r"django\."],
            "React": [r"import\s+React", r"from\s+['\"]react['\"]", r"\.jsx$"],
            "Vue": [r"import\s+Vue", r"\.vue$"],
            "Express": [r"const\s+express\s*=\s*require", r"app\.use\("],
            "Spring": [r"@SpringBootApplication", r"@RestController"],
            
            # Databases
            "PostgreSQL": [r"psycopg2", r"postgresql://", r"pg_"],
            "MySQL": [r"mysql", r"pymysql"],
            "MongoDB": [r"mongodb://", r"pymongo", r"mongoose"],
            "Redis": [r"redis://", r"import\s+redis", r"from\s+redis"],
            "ChromaDB": [r"chromadb", r"import\s+chromadb"],
            
            # Cloud
            "AWS": [r"boto3", r"aws-sdk", r"\.amazonaws\.com"],
            "GCP": [r"google-cloud", r"gcloud"],
            "Azure": [r"azure-", r"\.azure\.com"],
            "Docker": [r"Dockerfile", r"docker-compose"],
            "Kubernetes": [r"kubectl", r"k8s", r"deployment\.yaml"],
            
            # Tools
            "Git": [r"\.git", r"\.gitignore"],
            "Pytest": [r"import\s+pytest", r"def\s+test_"],
            "Jest": [r"jest", r"describe\(", r"it\("],
            "Webpack": [r"webpack\.config"],
            "Babel": [r"\.babelrc", r"babel\.config"],
        }
        
        detected_techs = Counter()
        
        for doc in documents:
            file_path = doc.file_path
            content = doc.normalized_content or doc.original_content
            
            for tech, patterns in tech_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, file_path, re.IGNORECASE) or \
                       re.search(pattern, content[:5000], re.IGNORECASE):  # Check first 5000 chars
                        detected_techs[tech] += 1
                        break  # Count once per document
        
        # Convert to list with confidence scores
        total_docs = len(documents)
        technologies = [
            {
                "name": tech,
                "count": count,
                "confidence": min(count / total_docs * 100, 100)  # Percentage
            }
            for tech, count in detected_techs.most_common(20)
        ]
        
        return {
            "detected": technologies,
            "total_unique": len(detected_techs),
            "top_5": [t["name"] for t in technologies[:5]]
        }
    
    async def _extract_endpoints(self, documents: List[DocumentModel]) -> Dict[str, Any]:
        """
        Extract API endpoints from code.
        
        Detects:
        - REST endpoints (@app.get, @router.post, etc.)
        - GraphQL schemas
        - gRPC services
        """
        endpoints = []
        
        # REST endpoint patterns
        rest_patterns = [
            # FastAPI/Flask
            r'@(?:app|router)\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']',
            # Express
            r'app\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']',
            # Spring
            r'@(Get|Post|Put|Delete|Patch)Mapping\(["\']([^"\']+)["\']',
            # Django
            r'path\(["\']([^"\']+)["\']',
        ]
        
        for doc in documents:
            content = doc.normalized_content or doc.original_content
            file_path = doc.file_path
            
            # Skip non-code files
            if not any(ext in file_path for ext in ['.py', '.js', '.ts', '.java', '.go']):
                continue
            
            for pattern in rest_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    if len(match.groups()) == 2:
                        method, path = match.groups()
                        endpoints.append({
                            "method": method.upper(),
                            "path": path,
                            "file": file_path,
                            "type": "REST"
                        })
        
        # Deduplicate
        unique_endpoints = []
        seen = set()
        for ep in endpoints:
            key = (ep["method"], ep["path"])
            if key not in seen:
                seen.add(key)
                unique_endpoints.append(ep)
        
        return {
            "endpoints": unique_endpoints,
            "total": len(unique_endpoints),
            "by_method": Counter(ep["method"] for ep in unique_endpoints),
            "by_type": Counter(ep["type"] for ep in unique_endpoints)
        }
    
    async def _analyze_architecture(self, documents: List[DocumentModel]) -> Dict[str, Any]:
        """
        Analyze architecture patterns.
        
        Detects:
        - Monolith vs Microservices
        - Layered architecture
        - Design patterns
        """
        # Simple heuristics
        total_docs = len(documents)
        
        # Check for microservice indicators
        has_docker = any("docker" in doc.file_path.lower() for doc in documents)
        has_k8s = any("k8s" in doc.file_path.lower() or "kubernetes" in doc.file_path.lower() for doc in documents)
        has_services_dir = any("/services/" in doc.file_path for doc in documents)
        
        # Check for layered architecture
        has_controllers = any("controller" in doc.file_path.lower() for doc in documents)
        has_services = any("service" in doc.file_path.lower() for doc in documents)
        has_models = any("model" in doc.file_path.lower() for doc in documents)
        has_repositories = any("repository" in doc.file_path.lower() for doc in documents)
        
        architecture_type = "Unknown"
        if has_services_dir or (has_docker and has_k8s):
            architecture_type = "Microservices"
        elif has_controllers and has_services and has_models:
            architecture_type = "Layered Monolith"
        elif total_docs < 50:
            architecture_type = "Simple Application"
        
        layers = []
        if has_controllers:
            layers.append("Controllers/Routes")
        if has_services:
            layers.append("Services/Business Logic")
        if has_models:
            layers.append("Models/Entities")
        if has_repositories:
            layers.append("Repositories/Data Access")
        
        return {
            "type": architecture_type,
            "layers": layers,
            "patterns": {
                "containerized": has_docker,
                "orchestrated": has_k8s,
                "layered": len(layers) >= 3
            }
        }
    
    async def _generate_ai_summary(
        self,
        context_id: str,
        documents: List[DocumentModel]
    ) -> str:
        """
        Generate AI-powered summary using Ollama.
        
        Uses CodeLlama to understand the repository.
        """
        # Sample documents for summary (limit to avoid token overflow)
        sample_size = min(20, len(documents))
        sample_docs = documents[:sample_size]
        
        # Build context for AI
        context_text = f"Repository: {context_id}\n\n"
        context_text += f"Total Documents: {len(documents)}\n\n"
        context_text += "Sample Files:\n"
        
        for doc in sample_docs:
            context_text += f"- {doc.file_path}\n"
            if doc.doc_metadata and doc.doc_metadata.get('codellama_summary'):
                context_text += f"  Summary: {doc.doc_metadata['codellama_summary'][:200]}...\n"
        
        # Prompt for Ollama
        prompt = f"""Analyze this codebase and provide a concise 3-4 sentence summary.

{context_text[:3000]}

Focus on:
1. What is the main purpose of this codebase?
2. What are the key technologies used?
3. What is the architecture style?
4. Who would use this?

Summary:"""
        
        try:
            response = await asyncio.wait_for(
                self.ollama_client.generate(
                    model="codellama:7b",
                    prompt=prompt,
                    options={"temperature": 0.3, "num_predict": 150}
                ),
                timeout=60
            )
            
            summary = response.get("response", "").strip()
            return summary if summary else "Unable to generate summary"
        
        except Exception as e:
            logger.error(f"AI summary generation failed: {e}")
            return "Summary generation failed"


# Singleton instance
_context_analyzer_instance = None

def get_context_analyzer() -> ContextAnalyzer:
    """Get singleton context analyzer instance."""
    global _context_analyzer_instance
    if _context_analyzer_instance is None:
        _context_analyzer_instance = ContextAnalyzer()
    return _context_analyzer_instance
```

---

#### 3. Context-Aware RAG Query

**File:** `services/ecosystem-mcp/src/api/routes/query_enhanced.py` (MODIFIED)

```python
# Add context parameter to EnhancedQueryRequest
class EnhancedQueryRequest(BaseModel):
    """Enhanced query request with context support."""
    question: str = Field(..., description="Question to answer")
    mode: QueryMode = Field(default=QueryMode.RAG, description="Query mode")
    tier: TierPreference = Field(default=TierPreference.DESKTOP, description="LLM tier")
    n_results: int = Field(default=5, description="Number of results")
    
    # NEW: Context support
    context_id: Optional[str] = Field(
        default=None,
        description="Repository context to focus on (e.g., 'my-api-service')"
    )
    context_weight: float = Field(
        default=0.8,
        description="Weight for context filtering (0.0-1.0). 1.0 = only context docs, 0.0 = all docs"
    )


@router.post("/query/enhanced")
async def enhanced_query(request: EnhancedQueryRequest):
    """
    Enhanced query with context-aware RAG.
    
    NEW: Supports repository context filtering.
    When context_id is provided, results are weighted towards that context.
    """
    # ... existing code ...
    
    # NEW: Apply context filtering
    chroma_where = None
    if request.context_id:
        chroma_where = {"context_id": request.context_id}
        logger.info(f"🎯 Context-aware query: {request.context_id} (weight: {request.context_weight})")
    
    # Query ChromaDB with context filter
    results = await chroma_client.query(
        query_embeddings=[embedding],
        n_results=request.n_results,
        where=chroma_where  # NEW: Filter by context
    )
    
    # If context weight < 1.0, also get some results from other contexts
    if request.context_id and request.context_weight < 1.0:
        # Get additional results from other contexts
        other_results = await chroma_client.query(
            query_embeddings=[embedding],
            n_results=int(request.n_results * (1 - request.context_weight)),
            where={"context_id": {"$ne": request.context_id}}  # Exclude current context
        )
        
        # Merge results with weighted scores
        # ... merging logic ...
    
    # ... rest of existing code ...
```

---

#### 4. Context Summary Dashboard Page

**File:** `services/ecosystem-mcp-dashboard/dashboard_views/context_summary.py` (NEW)

```python
"""
Context Summary Dashboard

Displays comprehensive summary of a repository context.
"""

import streamlit as st
import requests
import pandas as pd
from typing import Dict, Any, List

# Get API URL
API_URL = st.session_state.get("api_url", "http://ecosystem-mcp-service:8000")


def render_context_summary():
    """Render context summary page."""
    
    st.title("📚 Repository Context Summary")
    
    # Context selector
    contexts = get_contexts()
    
    if not contexts:
        st.warning("⚠️ No repository contexts found. Ingest a repository first.")
        return
    
    # Sidebar: Context selector
    with st.sidebar:
        st.header("🎯 Select Context")
        
        context_options = {ctx["display_name"]: ctx["context_id"] for ctx in contexts}
        selected_display = st.selectbox(
            "Repository",
            options=list(context_options.keys()),
            help="Select a repository to view its summary"
        )
        
        selected_context_id = context_options[selected_display]
        
        # Set as default context
        if st.button("Set as Default Context"):
            st.session_state["default_context"] = selected_context_id
            st.success(f"✅ Default context set to: {selected_display}")
    
    # Get context details
    context = get_context_details(selected_context_id)
    
    if not context:
        st.error(f"❌ Context not found: {selected_context_id}")
        return
    
    # Header
    st.header(f"📦 {context['display_name']}")
    st.caption(f"Context ID: `{context['context_id']}`")
    
    # AI Summary
    st.subheader("🤖 AI-Generated Summary")
    if context.get("ai_summary"):
        st.info(context["ai_summary"])
    else:
        st.warning("⚠️ Summary not yet generated. Run analysis to generate.")
        if st.button("🔍 Analyze Context"):
            with st.spinner("Analyzing context..."):
                analyze_context(selected_context_id)
                st.rerun()
    
    # Metrics Row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "📄 Total Documents",
            f"{context['metrics']['total_documents']:,}"
        )
    
    with col2:
        st.metric(
            "💻 Code Files",
            f"{context['metrics']['total_code_files']:,}"
        )
    
    with col3:
        st.metric(
            "🔗 Endpoints",
            f"{context['endpoints']['total']:,}"
        )
    
    with col4:
        st.metric(
            "🛠️ Technologies",
            f"{context['technologies']['total_unique']:,}"
        )
    
    # Technologies Section
    st.subheader("🛠️ Technologies Used")
    
    if context['technologies']['detected']:
        tech_df = pd.DataFrame(context['technologies']['detected'])
        
        # Display as cards
        cols = st.columns(5)
        for idx, tech in enumerate(context['technologies']['detected'][:10]):
            with cols[idx % 5]:
                st.metric(
                    tech['name'],
                    f"{tech['confidence']:.0f}%",
                    help=f"Found in {tech['count']} documents"
                )
    else:
        st.info("No technologies detected yet.")
    
    # Endpoints Section
    st.subheader("🔗 API Endpoints")
    
    if context['endpoints']['endpoints']:
        # Group by method
        endpoints_by_method = {}
        for ep in context['endpoints']['endpoints']:
            method = ep['method']
            if method not in endpoints_by_method:
                endpoints_by_method[method] = []
            endpoints_by_method[method].append(ep)
        
        # Display by method
        for method in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
            if method in endpoints_by_method:
                with st.expander(f"{method} ({len(endpoints_by_method[method])} endpoints)"):
                    for ep in endpoints_by_method[method]:
                        st.code(f"{ep['method']} {ep['path']}")
                        st.caption(f"📄 {ep['file']}")
    else:
        st.info("No endpoints detected yet.")
    
    # Architecture Section
    st.subheader("🏗️ Architecture")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Architecture Type:**")
        st.info(context['architecture']['type'])
        
        st.markdown("**Patterns:**")
        for pattern, enabled in context['architecture']['patterns'].items():
            icon = "✅" if enabled else "❌"
            st.write(f"{icon} {pattern.title()}")
    
    with col2:
        st.markdown("**Layers:**")
        if context['architecture']['layers']:
            for layer in context['architecture']['layers']:
                st.write(f"• {layer}")
        else:
            st.write("No layers detected")
    
    # File Distribution
    st.subheader("📊 File Distribution")
    
    if context['metrics']['file_type_distribution']:
        file_dist_df = pd.DataFrame([
            {"File Type": k, "Count": v}
            for k, v in context['metrics']['file_type_distribution'].items()
        ])
        
        st.bar_chart(file_dist_df.set_index("File Type"))
    
    # Context Metadata
    with st.expander("🔍 Context Metadata"):
        st.json(context)


def get_contexts() -> List[Dict[str, Any]]:
    """Get all contexts."""
    try:
        response = requests.get(f"{API_URL}/api/v1/contexts")
        if response.status_code == 200:
            return response.json()["contexts"]
        return []
    except Exception as e:
        st.error(f"Failed to fetch contexts: {e}")
        return []


def get_context_details(context_id: str) -> Dict[str, Any]:
    """Get context details with analysis."""
    try:
        response = requests.get(f"{API_URL}/api/v1/contexts/{context_id}")
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Failed to fetch context: {e}")
        return None


def analyze_context(context_id: str):
    """Trigger context analysis."""
    try:
        response = requests.post(f"{API_URL}/api/v1/contexts/{context_id}/analyze")
        if response.status_code == 200:
            st.success("✅ Analysis complete!")
        else:
            st.error(f"Analysis failed: {response.text}")
    except Exception as e:
        st.error(f"Analysis failed: {e}")


if __name__ == "__main__":
    render_context_summary()
```

---

#### 5. Context Picker Component

**File:** `services/ecosystem-mcp-dashboard/components/context_picker.py` (NEW)

```python
"""
Context Picker Component

Reusable component for selecting repository context.
"""

import streamlit as st
import requests
from typing import Optional

API_URL = st.session_state.get("api_url", "http://ecosystem-mcp-service:8000")


def render_context_picker(
    key: str = "context_picker",
    show_all_option: bool = True,
    default_context: Optional[str] = None
) -> Optional[str]:
    """
    Render context picker component.
    
    Args:
        key: Unique key for the component
        show_all_option: Show "All Contexts" option
        default_context: Default context ID
    
    Returns:
        Selected context ID or None (for "All Contexts")
    """
    # Get contexts
    try:
        response = requests.get(f"{API_URL}/api/v1/contexts")
        if response.status_code != 200:
            st.error("Failed to load contexts")
            return None
        
        contexts = response.json()["contexts"]
    except Exception as e:
        st.error(f"Failed to load contexts: {e}")
        return None
    
    if not contexts:
        st.warning("⚠️ No contexts available. Ingest a repository first.")
        return None
    
    # Build options
    options = {}
    if show_all_option:
        options["🌐 All Contexts"] = None
    
    for ctx in contexts:
        options[f"📦 {ctx['display_name']}"] = ctx['context_id']
    
    # Get default
    if default_context is None:
        default_context = st.session_state.get("default_context")
    
    # Find default display name
    default_display = "🌐 All Contexts"
    if default_context:
        for display, ctx_id in options.items():
            if ctx_id == default_context:
                default_display = display
                break
    
    # Render selector
    selected_display = st.selectbox(
        "🎯 Repository Context",
        options=list(options.keys()),
        index=list(options.keys()).index(default_display) if default_display in options else 0,
        key=key,
        help="Select a repository context to focus your query"
    )
    
    selected_context_id = options[selected_display]
    
    # Show context info
    if selected_context_id:
        context = next((c for c in contexts if c['context_id'] == selected_context_id), None)
        if context:
            st.caption(
                f"📄 {context['metrics']['total_documents']:,} documents | "
                f"💻 {context['metrics']['total_code_files']:,} code files"
            )
    
    return selected_context_id
```

---

### Integration with Existing Features

#### 1. Update Ingestion to Create Contexts

```python
# In services/ecosystem-mcp/src/api/routes/admin.py
@router.post("/ingest")
async def start_ingestion(request: IngestRequest):
    # ... existing code ...
    
    # NEW: Create/update context
    from ...services.context.context_manager import get_context_manager
    context_manager = get_context_manager()
    
    context = await context_manager.create_or_update_context(
        repo_path=str(repo_path),
        ingestion_mode=request.ingestion_mode,
        job_metadata=job_metadata
    )
    
    # Add context_id to job metadata
    job_metadata['context_id'] = context['context_id']
    
    # ... rest of existing code ...
```

#### 2. Tag Documents with Context

```python
# In services/ecosystem-mcp/src/services/ingestion/job_processor.py
async def _store_document(...):
    # ... existing code ...
    
    # NEW: Add context_id from job metadata
    context_id = job.job_metadata.get('context_id')
    
    doc = DocumentModel(
        # ... existing fields ...
        context_id=context_id,  # NEW
        # ... rest of fields ...
    )
```

#### 3. Add Context Picker to RAG Query Page

```python
# In services/ecosystem-mcp-dashboard/dashboard_views/rag_query.py
from components.context_picker import render_context_picker

def render_rag_query():
    st.title("🔍 RAG Query")
    
    # NEW: Context picker
    selected_context = render_context_picker(
        key="rag_context_picker",
        show_all_option=True
    )
    
    # Query form
    with st.form("rag_query_form"):
        question = st.text_area("Question")
        
        # Context weight slider (only if context selected)
        context_weight = 1.0
        if selected_context:
            context_weight = st.slider(
                "Context Focus",
                min_value=0.0,
                max_value=1.0,
                value=0.8,
                step=0.1,
                help="1.0 = Only this context, 0.0 = All contexts equally"
            )
        
        submitted = st.form_submit_button("Ask")
        
        if submitted:
            # Query with context
            response = requests.post(
                f"{API_URL}/api/v1/query/enhanced",
                json={
                    "question": question,
                    "context_id": selected_context,
                    "context_weight": context_weight
                }
            )
            # ... display results ...
```

---

### API Endpoints

#### 1. Context Management

```python
# GET /api/v1/contexts
# List all contexts

# GET /api/v1/contexts/{context_id}
# Get context details

# POST /api/v1/contexts/{context_id}/analyze
# Trigger context analysis

# DELETE /api/v1/contexts/{context_id}
# Delete context (and optionally documents)

# PUT /api/v1/contexts/{context_id}
# Update context metadata
```

#### 2. Context-Aware Query

```python
# POST /api/v1/query/enhanced
# Enhanced query with context support
# Body: {
#   "question": "How does authentication work?",
#   "context_id": "my-api-service",
#   "context_weight": 0.8
# }
```

---

### Performance Impact

#### Context Creation
- **Time:** +1-2 seconds per ingestion (one-time)
- **Storage:** +1KB per context (metadata only)

#### Context Analysis
- **Time:** 30-60 seconds (one-time, async)
- **Dependencies:** CodeLlama for AI summary

#### Context-Aware RAG
- **Time:** Same as regular RAG (filtering is fast)
- **Accuracy:** +20-30% relevance (focused results)

---

### Use Cases

#### 1. Multi-Repository Development
```
Developer working on 3 microservices:
  • Selects "auth-service" context
  • Asks: "How do we handle JWT tokens?"
  • Gets results ONLY from auth-service
  • No noise from other services
```

#### 2. Documentation Generation
```
Tech writer needs to document "payment-service":
  • Views payment-service context summary
  • Sees: 15 endpoints, Python/FastAPI, PostgreSQL
  • Generates focused documentation
```

#### 3. Code Review
```
Reviewer checking "frontend-app":
  • Selects frontend-app context
  • Asks: "What state management is used?"
  • Gets focused answer about Redux usage
```

#### 4. Onboarding
```
New developer joins team:
  • Views all context summaries
  • Understands: 5 microservices, technologies, architecture
  • Knows where to start
```

---

### Testing Strategy

#### Unit Tests
```python
# tests/unit/test_context_manager.py
def test_extract_context_id():
    assert ContextManager.extract_context_id("/host/my-api") == "my-api"
    assert ContextManager.extract_context_id("/app/frontend") == "frontend"

# tests/unit/test_context_analyzer.py
async def test_detect_technologies():
    analyzer = ContextAnalyzer()
    techs = await analyzer._detect_technologies(mock_documents)
    assert "Python" in [t["name"] for t in techs["detected"]]
```

#### Integration Tests
```python
# tests/integration/test_context_aware_rag.py
async def test_context_filtering():
    # Ingest two repos
    await ingest("repo1")
    await ingest("repo2")
    
    # Query with context
    response = await query("test", context_id="repo1")
    
    # Verify results are from repo1 only
    assert all(doc["context_id"] == "repo1" for doc in response["sources"])
```

---

### Migration Plan

#### Week 1: Database & Core
- Create repository_contexts table
- Update documents table
- Implement ContextManager

#### Week 2: Analysis
- Implement ContextAnalyzer
- Technology detection
- Endpoint extraction
- AI summary generation

#### Week 3: RAG Integration
- Update query endpoints
- Context filtering in ChromaDB
- Weighted result merging

#### Week 4: Dashboard
- Context summary page
- Context picker component
- Update RAG query page
- Update multi-pass RAG page

#### Week 5: Testing & Polish
- Unit tests
- Integration tests
- E2E tests
- Documentation

---

### Success Criteria

1. **Functionality:**
   - ✅ Contexts auto-created during ingestion
   - ✅ Context-aware RAG filtering works
   - ✅ Summary page displays all metrics
   - ✅ Works with all ingestion modes

2. **Performance:**
   - ✅ Context creation: <2s overhead
   - ✅ Context analysis: <60s
   - ✅ Context-aware query: same speed as regular

3. **User Experience:**
   - ✅ Easy context selection
   - ✅ Clear visual summaries
   - ✅ Accurate technology detection
   - ✅ Helpful AI summaries

4. **Quality:**
   - ✅ 90%+ accurate technology detection
   - ✅ 95%+ accurate endpoint extraction
   - ✅ Meaningful AI summaries

---

**Phase 9 Status:** 🔴 PLANNING ONLY - DO NOT IMPLEMENT  
**Estimated Effort:** 5 weeks (1 developer)  
**Expected Value:** 10× better focused search, clear repository understanding  
**Dependencies:** Phases 1-8 (especially Phase 8 for CodeLlama analysis)

