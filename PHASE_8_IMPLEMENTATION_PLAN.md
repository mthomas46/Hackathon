# Phase 8: Git-Optional Ingestion Mode - Implementation Plan

**Status:** 🟢 READY TO IMPLEMENT  
**Created:** October 21, 2025  
**Dependencies:** Phases 1-7 Complete  
**Estimated Effort:** 12-16 hours

---

## 📋 Executive Summary

### Goal
Make Git commit history **optional** for ingestion, enabling 10-100× faster processing for users who only need current file snapshots, while maintaining full backward compatibility for users who need version tracking.

### Impact
- **Current (Git-only):** 5,000 documents = 2-4 hours
- **New (Snapshot mode):** 5,000 documents = 5-15 minutes (96% faster!)
- **Backward compatible:** Existing Git mode unchanged

### Success Criteria
- ✅ Users can choose "snapshot" or "git_history" mode
- ✅ Snapshot mode processes 10-100× faster
- ✅ All existing Git functionality preserved
- ✅ Database supports both modes
- ✅ Dashboard allows mode selection
- ✅ Comprehensive tests for both modes
- ✅ 100% logging coverage

---

## 🎯 Architecture Overview

### Two Processing Modes

```
┌─────────────────────────────────────────────────────────────┐
│                    INGESTION REQUEST                         │
│                                                              │
│  POST /api/v1/ingestion/start                               │
│  {                                                           │
│    "repo_path": "/path/to/repo",                            │
│    "mode": "snapshot" | "git_history"  ← NEW PARAMETER     │
│  }                                                           │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
         ▼                               ▼
┌─────────────────┐           ┌──────────────────┐
│  SNAPSHOT MODE  │           │  GIT HISTORY     │
│                 │           │  MODE (existing) │
│  • Direct FS    │           │                  │
│  • No Git ops   │           │  • Commit walk   │
│  • Content hash │           │  • Git objects   │
│  • Single pass  │           │  • Deduplication │
│  • 5-15 min     │           │  • 2-4 hours     │
└─────────────────┘           └──────────────────┘
```

### Database Schema Evolution

```sql
-- Current (Git-centric)
CREATE TABLE documents (
  git_commit_sha VARCHAR(40) NOT NULL,  -- ❌ Mandatory
  is_latest BOOLEAN,                     -- ❌ Git concept
  UNIQUE(file_path, git_commit_sha)     -- ❌ Git required
);

-- New (Mode-agnostic)
CREATE TABLE documents (
  ingestion_mode VARCHAR(20) NOT NULL,   -- ✅ 'snapshot' or 'git_history'
  git_commit_sha VARCHAR(40),            -- ✅ Optional (NULL for snapshot)
  content_hash VARCHAR(64) NOT NULL,     -- ✅ Always present
  version INTEGER NOT NULL DEFAULT 1,    -- ✅ Incremental for snapshot mode
  is_latest BOOLEAN,                     -- ✅ Works for both modes
  UNIQUE(file_path, content_hash)       -- ✅ Dedup for both modes
);
```

---

## 📦 Implementation Phases

### Phase 8.1: Database Schema Migration (2-3 hours)

#### Components

**1. Migration Script**
- **File:** `src/storage/migrations/008_add_snapshot_mode.py`
- **Changes:**
  - Add `ingestion_mode` column (NOT NULL, default='git_history')
  - Add `content_hash` column (NOT NULL, indexed)
  - Add `version` column (NOT NULL, default=1)
  - Make `git_commit_sha` nullable
  - Update unique constraint to use `content_hash`
  - Backfill existing records with mode='git_history'

```python
"""
Migration: Add snapshot mode support

Makes Git history optional by:
- Adding ingestion_mode field
- Making git_commit_sha nullable
- Adding content_hash for deduplication
- Adding version for snapshot versioning
"""

async def upgrade(connection):
    # Add new columns
    await connection.execute("""
        ALTER TABLE documents 
        ADD COLUMN ingestion_mode VARCHAR(20) NOT NULL DEFAULT 'git_history',
        ADD COLUMN content_hash VARCHAR(64),
        ADD COLUMN version INTEGER NOT NULL DEFAULT 1;
    """)
    
    # Compute content_hash for existing documents
    await connection.execute("""
        UPDATE documents 
        SET content_hash = md5(content)
        WHERE content_hash IS NULL;
    """)
    
    # Make content_hash NOT NULL after backfill
    await connection.execute("""
        ALTER TABLE documents 
        ALTER COLUMN content_hash SET NOT NULL;
    """)
    
    # Make git_commit_sha nullable
    await connection.execute("""
        ALTER TABLE documents 
        ALTER COLUMN git_commit_sha DROP NOT NULL;
    """)
    
    # Update unique constraint
    await connection.execute("""
        ALTER TABLE documents 
        DROP CONSTRAINT IF EXISTS uq_document_file_commit;
    """)
    
    await connection.execute("""
        ALTER TABLE documents 
        ADD CONSTRAINT uq_document_file_hash 
        UNIQUE(file_path, content_hash);
    """)
    
    # Add indexes
    await connection.execute("""
        CREATE INDEX idx_documents_mode ON documents(ingestion_mode);
        CREATE INDEX idx_documents_content_hash ON documents(content_hash);
    """)

async def downgrade(connection):
    # Revert changes
    await connection.execute("""
        ALTER TABLE documents 
        DROP COLUMN ingestion_mode,
        DROP COLUMN content_hash,
        DROP COLUMN version;
    """)
    # ... restore original constraints
```

**2. Update ORM Models**
- **File:** `src/storage/db_models.py`

```python
class DocumentModel(Base):
    __tablename__ = "documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_path = Column(Text, nullable=False, index=True)
    
    # NEW: Ingestion mode
    ingestion_mode = Column(String(20), nullable=False, default='git_history', index=True)
    
    # MODIFIED: Now nullable
    git_commit_sha = Column(String(40), nullable=True, index=True)
    
    # NEW: Content-based deduplication
    content_hash = Column(String(64), nullable=False, index=True)
    
    # NEW: Version for snapshot mode
    version = Column(Integer, nullable=False, default=1)
    
    is_latest = Column(Boolean, nullable=False, default=True, index=True)
    
    __table_args__ = (
        UniqueConstraint("file_path", "content_hash", name="uq_document_file_hash"),
        Index("idx_documents_mode", "ingestion_mode"),
        Index("idx_documents_content_hash", "content_hash"),
    )
```

**Testing:**
- ✅ Unit tests for migration up/down
- ✅ Test backfill of existing data
- ✅ Verify indexes created
- ✅ Test constraint enforcement

**Logging:**
- Migration start/complete
- Rows migrated count
- Backfill progress
- Index creation time

---

### Phase 8.2: Snapshot Processor (4-5 hours)

#### Components

**1. SnapshotProcessor**
- **File:** `src/services/ingestion/snapshot_processor.py`
- **Purpose:** Fast direct file system processing without Git operations

```python
"""
Snapshot Processor

Fast ingestion mode for current file state only (no Git history).
Processes files directly from file system with content-based versioning.
"""

import logging
import hashlib
from pathlib import Path
from typing import Dict, List, Optional
import asyncio

logger = logging.getLogger(__name__)


class SnapshotProcessor:
    """
    Processes files in snapshot mode (no Git history).
    
    Features:
    - Direct file system scan
    - Content-based deduplication (MD5 hash)
    - Incremental versioning
    - 10-100× faster than Git mode
    - No Git operations
    """
    
    def __init__(self, repo_path: Path, job_id: str):
        self.repo_path = Path(repo_path)
        self.job_id = job_id
        self.ignore_patterns = {
            ".git", "__pycache__", "node_modules", ".venv", "venv",
            ".pytest_cache", ".mypy_cache", "dist", "build"
        }
        
        logger.info(f"SnapshotProcessor initialized for {repo_path}")
    
    async def process(self) -> Dict:
        """
        Process all files in snapshot mode.
        
        Returns:
            Processing statistics
        """
        logger.info(f"🚀 Starting snapshot mode ingestion: {self.repo_path}")
        
        start_time = time.time()
        
        # Discover files
        files = await self._discover_files()
        logger.info(f"📁 Discovered {len(files)} files")
        
        # Process files in parallel batches
        stats = await self._process_files_batch(files)
        
        elapsed = time.time() - start_time
        logger.info(
            f"✅ Snapshot ingestion complete: "
            f"{stats['processed']} processed, "
            f"{stats['skipped']} skipped, "
            f"{stats['failed']} failed "
            f"in {elapsed:.1f}s"
        )
        
        return {
            **stats,
            'elapsed_seconds': elapsed,
            'mode': 'snapshot'
        }
    
    async def _discover_files(self) -> List[Path]:
        """Discover all processable files."""
        files = []
        
        for path in self.repo_path.rglob("*"):
            if not path.is_file():
                continue
            
            # Skip ignored patterns
            if any(pattern in str(path) for pattern in self.ignore_patterns):
                continue
            
            # Skip binary files
            if self._is_binary(path):
                continue
            
            files.append(path)
        
        return files
    
    async def _process_files_batch(self, files: List[Path]) -> Dict:
        """Process files in parallel batches."""
        batch_size = 50
        stats = {'processed': 0, 'skipped': 0, 'failed': 0}
        
        for i in range(0, len(files), batch_size):
            batch = files[i:i + batch_size]
            
            # Process batch in parallel
            tasks = [self._process_file(f) for f in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Aggregate stats
            for result in results:
                if isinstance(result, Exception):
                    stats['failed'] += 1
                elif result == 'skipped':
                    stats['skipped'] += 1
                else:
                    stats['processed'] += 1
            
            # Progress update
            logger.info(f"📊 Progress: {i + len(batch)}/{len(files)} files")
        
        return stats
    
    async def _process_file(self, file_path: Path) -> str:
        """
        Process a single file.
        
        Returns:
            'processed', 'skipped', or raises exception
        """
        try:
            # Read content
            content = await self._read_file(file_path)
            
            # Calculate content hash
            content_hash = self._calculate_hash(content)
            
            # Check if already ingested
            if await self._is_duplicate(file_path, content_hash):
                logger.debug(f"⏭️  Skipping duplicate: {file_path}")
                return 'skipped'
            
            # Normalize content
            normalized = await self._normalize(file_path, content)
            
            # Generate embedding
            embedding = await self._generate_embedding(normalized)
            
            # Store document
            await self._store_document(
                file_path=str(file_path.relative_to(self.repo_path)),
                content=content,
                normalized_content=normalized,
                content_hash=content_hash,
                embedding=embedding
            )
            
            logger.debug(f"✅ Processed: {file_path}")
            return 'processed'
            
        except Exception as e:
            logger.error(f"❌ Failed to process {file_path}: {e}")
            raise
    
    def _calculate_hash(self, content: str) -> str:
        """Calculate MD5 hash of content."""
        return hashlib.md5(content.encode()).hexdigest()
    
    async def _is_duplicate(self, file_path: Path, content_hash: str) -> bool:
        """Check if file with same content already exists."""
        # Query database for existing document with same path and hash
        # This is MUCH faster than Git commit walking
        pass
    
    def _is_binary(self, path: Path) -> bool:
        """Check if file is binary."""
        try:
            with open(path, 'rb') as f:
                chunk = f.read(1024)
                return b'\x00' in chunk
        except:
            return True
    
    async def _read_file(self, path: Path) -> str:
        """Read file content."""
        # Async file reading
        pass
    
    async def _normalize(self, path: Path, content: str) -> str:
        """Normalize content to markdown."""
        # Use existing normalizer
        pass
    
    async def _generate_embedding(self, content: str):
        """Generate embedding vector."""
        # Use existing embedding service
        pass
    
    async def _store_document(self, **kwargs):
        """Store document in database."""
        # Store with mode='snapshot', version=auto-increment
        pass
```

**Testing:**
- ✅ Unit tests for file discovery
- ✅ Unit tests for content hashing
- ✅ Unit tests for duplicate detection
- ✅ Integration test: process small repo
- ✅ Integration test: verify deduplication
- ✅ Performance test: compare to Git mode

**Logging:**
- Process start/complete with timing
- File discovery count
- Batch progress (every 50 files)
- Processed/skipped/failed counts
- Individual file processing (debug level)

---

### Phase 8.3: Mode Selection & API (3-4 hours)

#### Components

**1. Update Ingestion Request Model**
- **File:** `src/api/models.py`

```python
from enum import Enum
from pydantic import BaseModel, Field

class IngestionMode(str, Enum):
    """Ingestion processing mode."""
    SNAPSHOT = "snapshot"          # Fast: current files only
    GIT_HISTORY = "git_history"    # Complete: full commit history

class IngestRequest(BaseModel):
    """Ingestion job request."""
    repo_path: str = Field(..., description="Repository path")
    
    mode: IngestionMode = Field(
        default=IngestionMode.GIT_HISTORY,
        description="Processing mode: 'snapshot' (fast) or 'git_history' (complete)"
    )
    
    # Existing fields...
    include_patterns: Optional[List[str]] = None
    exclude_patterns: Optional[List[str]] = None
```

**2. Update Job Processor Router**
- **File:** `src/services/ingestion/job_processor_router.py`

```python
"""
Job Processor Router

Routes ingestion jobs to appropriate processor based on mode.
"""

from .job_processor import JobProcessor  # Git mode (existing)
from .snapshot_processor import SnapshotProcessor  # New

class JobProcessorRouter:
    """Routes jobs to correct processor based on mode."""
    
    async def process(self, job: IngestionJobModel):
        if job.mode == 'snapshot':
            processor = SnapshotProcessor(job.repo_path, job.id)
            return await processor.process()
        else:
            processor = JobProcessor(job)
            return await processor.process()
```

**3. Update API Endpoint**
- **File:** `src/api/routes/admin.py`

```python
@router.post("/ingestion/start", response_model=IngestionJobResponse)
async def start_ingestion(request: IngestRequest):
    """
    Start an ingestion job.
    
    Modes:
    - **snapshot**: Fast ingestion of current files (5-15 min for 5K files)
    - **git_history**: Full Git commit history (2-4 hours for 5K files)
    """
    # Validate path
    if not Path(request.repo_path).exists():
        raise HTTPException(400, "Path does not exist")
    
    # Create job with mode
    job = IngestionJobModel(
        repo_path=request.repo_path,
        mode=request.mode.value,
        status='queued'
    )
    
    # Queue for processing
    await queue_job(job)
    
    logger.info(f"Ingestion job queued: {job.id} (mode={request.mode})")
    
    return job
```

**Testing:**
- ✅ API test: POST with mode='snapshot'
- ✅ API test: POST with mode='git_history'
- ✅ API test: default mode is git_history
- ✅ Test routing logic
- ✅ Test backward compatibility (no mode specified)

**Logging:**
- Job creation with mode
- Routing decision
- Mode-specific processor instantiation

---

### Phase 8.4: Dashboard Integration (2-3 hours)

#### Components

**1. Update Ingestion Form**
- **File:** `services/ecosystem-mcp-dashboard/dashboard_views/ingestion_manager.py`

```python
with st.form("start_ingestion_form"):
    st.subheader("🚀 Start New Ingestion")
    
    repo_path = st.text_input("Repository Path", value="/app")
    
    # NEW: Mode selection
    mode = st.radio(
        "Processing Mode",
        options=["snapshot", "git_history"],
        format_func=lambda x: {
            "snapshot": "🚀 Snapshot (Fast: 5-15 min)",
            "git_history": "📚 Git History (Complete: 2-4 hours)"
        }[x],
        help="""
        **Snapshot Mode:** Process current files only (10-100× faster)
        - Use for: Initial setup, periodic updates, non-Git repos
        - Speed: 5-15 minutes for 5,000 files
        
        **Git History Mode:** Process full commit history
        - Use for: Complete versioning, historical context
        - Speed: 2-4 hours for 5,000 files
        """
    )
    
    submit = st.form_submit_button("Start Ingestion")
    
    if submit:
        response = requests.post(
            f"{api_url}/api/v1/ingestion/start",
            json={"repo_path": repo_path, "mode": mode}
        )
```

**2. Update Job Display**
- Show mode badge in job list
- Different color for snapshot vs git_history
- Speed estimate based on mode

**Testing:**
- ✅ Manual UI test: select snapshot mode
- ✅ Manual UI test: select git_history mode
- ✅ Verify API request includes mode
- ✅ Verify job list shows mode

**Logging:**
- UI form submission with mode
- API request sent

---

### Phase 8.5: Testing & Validation (2-3 hours)

#### Test Suite

**1. Unit Tests**
```python
# tests/unit/test_snapshot_processor.py
class TestSnapshotProcessor:
    def test_file_discovery(self):
        """Test file discovery ignores patterns."""
        
    def test_content_hashing(self):
        """Test MD5 hash calculation."""
        
    def test_duplicate_detection(self):
        """Test duplicate content detection."""
        
    def test_binary_file_detection(self):
        """Test binary file skipping."""

# tests/unit/test_job_processor_router.py
class TestJobProcessorRouter:
    def test_route_to_snapshot(self):
        """Test routing to snapshot processor."""
        
    def test_route_to_git_history(self):
        """Test routing to git history processor."""
```

**2. Integration Tests**
```python
# tests/integration/test_snapshot_mode.py
class TestSnapshotModeIntegration:
    @pytest.mark.asyncio
    async def test_snapshot_ingestion_end_to_end(self):
        """Test complete snapshot mode workflow."""
        # Create test repo
        # Start ingestion with mode='snapshot'
        # Verify documents created
        # Verify no git_commit_sha
        # Verify content_hash populated
        
    @pytest.mark.asyncio
    async def test_incremental_snapshot(self):
        """Test re-ingesting with file changes."""
        # Initial ingestion
        # Modify file
        # Re-ingest
        # Verify version incremented
        # Verify old version still exists
```

**3. Performance Tests**
```python
# tests/performance/test_snapshot_speed.py
class TestSnapshotPerformance:
    @pytest.mark.slow
    def test_snapshot_vs_git_speed(self):
        """Compare snapshot vs git_history speed."""
        # Process same repo with both modes
        # Assert snapshot is 10-100× faster
        
    @pytest.mark.slow
    def test_large_repo_snapshot(self):
        """Test snapshot mode on 5K+ files."""
        # Verify completes in < 15 minutes
```

**4. Smoke Tests**
```python
# tests/smoke/test_snapshot_mode.py
@pytest.mark.smoke
class TestSnapshotModeSmoke:
    def test_api_accepts_snapshot_mode(self):
        """Test API accepts mode parameter."""
        
    def test_both_modes_work(self):
        """Test both modes process successfully."""
```

---

## 📊 Success Metrics

### Performance
- ✅ Snapshot mode: 5,000 files in < 15 minutes
- ✅ Git history mode: unchanged performance
- ✅ 10-100× speedup for snapshot vs git_history

### Functionality
- ✅ Both modes process correctly
- ✅ Deduplication works in both modes
- ✅ No breaking changes to existing code
- ✅ Database supports both modes

### Quality
- ✅ 100% logging coverage
- ✅ 100+ new tests (unit + integration + performance)
- ✅ All existing tests still pass
- ✅ Documentation updated

---

## 🔄 Backward Compatibility

### Ensuring No Breaking Changes

1. **Default Mode:** Git history remains default
2. **Existing Jobs:** Continue working unchanged
3. **Database:** Existing records work with new schema
4. **API:** Optional mode parameter (backward compatible)

### Migration Strategy

1. Deploy database migration first
2. Backfill existing records with mode='git_history'
3. Deploy backend code with both processors
4. Deploy dashboard with mode selection
5. Test both modes
6. Document new feature

---

## 📝 Documentation Updates

### User-Facing
- ✅ API documentation: mode parameter
- ✅ Dashboard help text: mode selection
- ✅ Performance comparison guide
- ✅ When to use each mode

### Developer-Facing
- ✅ Architecture decision record (ADR)
- ✅ Database schema changes
- ✅ New processor implementation
- ✅ Testing strategy

---

## ⏱️ Timeline

| Phase | Component | Effort | Status |
|-------|-----------|--------|--------|
| 8.1 | Database Migration | 2-3h | ⚪ Not Started |
| 8.2 | Snapshot Processor | 4-5h | ⚪ Not Started |
| 8.3 | Mode Selection & API | 3-4h | ⚪ Not Started |
| 8.4 | Dashboard Integration | 2-3h | ⚪ Not Started |
| 8.5 | Testing & Validation | 2-3h | ⚪ Not Started |
| **Total** | | **13-18h** | **0% Complete** |

---

## 🎯 Next Steps

1. ✅ Review and approve this plan
2. ⏳ Implement Phase 8.1 (Database Migration)
3. ⏳ Implement Phase 8.2 (Snapshot Processor)
4. ⏳ Continue through phases sequentially
5. ⏳ Test comprehensively
6. ⏳ Deploy to production

---

**Phase 8 Ready for Implementation!** 🚀

