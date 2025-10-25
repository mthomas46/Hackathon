"""
Job Processor

Orchestrates the document ingestion pipeline for a single job.
Coordinates Git extraction, document normalization, embedding generation,
and storage operations.
"""

import logging
import os
import asyncio
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
from uuid import UUID
from sqlalchemy.orm.attributes import flag_modified

from ...storage.db_models import IngestionJobModel
from ..git.git_service import GitService
from ..processing.normalizer_factory import NormalizerFactory
from ..embeddings.embedding_service import EmbeddingService
from ...storage import get_database
from ...storage.repositories import DocumentRepository
from ...storage.chromadb_client import get_chroma_client
from .commit_optimizer import get_commit_optimizer
from ...utils.redis_client import get_redis_client
from ..git.git_error_handler import get_git_error_handler, GitCorruptionError

logger = logging.getLogger(__name__)


class JobProcessor:
    """
    Processes ingestion jobs by coordinating the entire pipeline.
    
    Pipeline stages:
    1. Read commits from Git repository
    2. Extract files from each commit
    3. Normalize documents to markdown
    4. Generate embeddings
    5. Store in PostgreSQL + ChromaDB
    
    Features:
    - Progress tracking
    - Error handling with retries
    - Batch processing
    - Performance optimization
    """
    
    def __init__(self, worker_id: str = "unknown", use_batch_optimization: bool = True,
                 max_concurrent_commits: int = None, commit_batch_size: int = 10,
                 use_batched_processing: bool = True, max_commits_to_process: int = 100):
        """
        Initialize the job processor.
        
        Args:
            worker_id: Unique identifier for the worker instance
            use_batch_optimization: Enable Phase 1 optimizations (batch embeddings, connection pooling, caching)
            max_concurrent_commits: Maximum number of commits to process in parallel (Phase 2)
                                   If None, automatically determined based on CPU count (2× cores, max 20)
            commit_batch_size: Number of commits per batch for checkpointing (default: 10)
            use_batched_processing: Enable batched processing with checkpoints (default: True)
            max_commits_to_process: Maximum commits to process per job (default: 100, limits exposure to hangs)
        """
        self.worker_id = worker_id
        self.git_service = None  # Initialized per job
        self.normalizer_factory = NormalizerFactory()
        self.embedding_service = EmbeddingService()
        
        # Checkpoint manager for job recovery
        from .checkpoint_manager import get_checkpoint_manager
        self.checkpoint_manager = get_checkpoint_manager(checkpoint_interval=50)
        
        # Commit optimizer for duplicate detection
        self.commit_optimizer = get_commit_optimizer()
        
        # Phase 1 optimizations flag
        self.use_batch_optimization = use_batch_optimization
        
        # Batched processing configuration
        self.use_batched_processing = use_batched_processing
        self.commit_batch_size = commit_batch_size
        self.max_commits_to_process = max_commits_to_process
        
        # Phase 2: Parallel commit processing (auto-tune based on CPU count)
        import os
        import asyncio
        if max_concurrent_commits is None:
            # Auto-tune: 2× CPU cores, capped at 20
            cpu_count = os.cpu_count() or 4
            self.max_concurrent_commits = min(cpu_count * 2, 20)
            logger.info(f"🎯 Auto-tuned parallelism: {self.max_concurrent_commits} concurrent commits (CPU count: {cpu_count})")
        else:
            self.max_concurrent_commits = max_concurrent_commits
        
        self.commit_semaphore = asyncio.Semaphore(self.max_concurrent_commits)
        
        # Real-time progress tracking
        self.redis_client = None  # Initialized per job
        self.current_job_id: Optional[str] = None
        
        # Error handling
        self.git_error_handler = get_git_error_handler()
        
        # Timeout configuration (per commit)
        self.commit_timeout_seconds = 600  # 10 minutes per commit max
        
        # Batched commit processor (initialized lazily)
        self._batched_processor = None
        
        logger.info(
            f"JobProcessor initialized (worker: {worker_id}, "
            f"max_commits: {max_commits_to_process}, "
            f"batched_processing: {use_batched_processing}, "
            f"batch_size: {commit_batch_size}, "
            f"batch_optimization: {'✅ ENABLED' if use_batch_optimization else '❌ DISABLED'}, "
            f"parallel_commits: {max_concurrent_commits}, "
            f"commit_timeout: {self.commit_timeout_seconds}s, "
            f"graceful_degradation: ✅ ENABLED)"
        )
    
    async def _init_progress_tracking(self, job_id: str):
        """Initialize real-time progress tracking for a job."""
        self.current_job_id = job_id
        try:
            self.redis_client = get_redis_client()
            logger.info(f"✅ Real-time progress tracking initialized for job {job_id}")
        except Exception as e:
            logger.warning(f"⚠️  Could not initialize Redis progress tracking: {e}")
            self.redis_client = None
    
    async def _update_progress(self, phase: str, current: int, total: int, **extra_data):
        """Update real-time progress in Redis."""
        if not self.redis_client or not self.current_job_id:
            return
        
        try:
            progress_key = f"job_progress:{self.current_job_id}"
            progress_data = {
                "job_id": self.current_job_id,
                "phase": phase,
                "current": current,
                "total": total,
                "percentage": round((current / total * 100) if total > 0 else 0, 2),
                "timestamp": datetime.utcnow().isoformat(),
                **extra_data
            }
            
            await self.redis_client.set(
                progress_key,
                json.dumps(progress_data),
                ex=3600  # Expire after 1 hour
            )
            
            # Also publish to pub/sub for real-time updates
            await self.redis_client.publish(
                f"job_progress_channel:{self.current_job_id}",
                json.dumps(progress_data)
            )
            
        except Exception as e:
            logger.debug(f"Could not update progress: {e}")
    
    def calculate_optimal_batch_size(self, files: List[Dict[str, Any]]) -> int:
        """
        PHASE 3: Calculate optimal batch size based on file size distribution.
        
        Strategy:
        - Sample first 10 files to estimate average size
        - Adjust batch size to target ~10MB per batch for optimal throughput
        - Constrain to reasonable min/max to prevent edge cases
        
        Args:
            files: List of file dicts with 'content' key
        
        Returns:
            Optimal batch size (5-50)
        """
        if not files:
            return 20  # Default fallback
        
        # Sample first 10 files to get average size estimate
        sample_size = min(10, len(files))
        total_size = 0
        for f in files[:sample_size]:
            content = f.get('content', '')
            total_size += len(content) if content else 0
        
        avg_size_kb = (total_size / sample_size) / 1024 if sample_size > 0 else 50
        
        # Target: ~10MB per batch for optimal memory/throughput balance
        target_batch_mb = 10
        target_batch_bytes = target_batch_mb * 1024 * 1024
        
        # Determine batch size based on file size category
        if avg_size_kb < 10:  # Very small files (< 10KB)
            batch_size = min(50, len(files))
            category = "very small"
        elif avg_size_kb < 50:  # Small files (10-50KB)
            batch_size = min(30, len(files))
            category = "small"
        elif avg_size_kb < 100:  # Medium files (50-100KB)
            batch_size = 20  # Current Phase 2 optimal
            category = "medium"
        else:  # Large files (> 100KB)
            # Calculate to stay under memory target
            avg_size_bytes = avg_size_kb * 1024
            batch_size = max(5, int(target_batch_bytes / avg_size_bytes))
            batch_size = min(batch_size, 15)
            category = "large"
        
        # Ensure batch size doesn't exceed total files
        batch_size = min(batch_size, len(files))
        
        logger.info(
            f"📏 Dynamic batch size: {batch_size} files "
            f"({category}: avg {avg_size_kb:.1f}KB, target {target_batch_mb}MB/batch)"
        )
        
        return batch_size
    
    def is_binary_file_extension(self, file_path: str) -> bool:
        """
        PHASE 3: Check if file extension indicates binary content.
        
        Helps skip binary files early before attempting to read them,
        saving I/O and processing time.
        
        Args:
            file_path: Path to file
        
        Returns:
            True if file extension indicates binary content
        """
        binary_extensions = {
            # Images
            '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.svg', '.webp',
            # Archives
            '.zip', '.tar', '.gz', '.bz2', '.7z', '.rar',
            # Executables
            '.exe', '.dll', '.so', '.dylib', '.bin',
            # Media
            '.mp4', '.mp3', '.avi', '.mov', '.wav', '.flac',
            # Documents
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            # Fonts
            '.ttf', '.otf', '.woff', '.woff2',
            # Other
            '.db', '.sqlite', '.pkl', '.pyc', '.class'
        }
        
        ext = Path(file_path).suffix.lower()
        return ext in binary_extensions
    
    async def _check_job_timeout(self, job: IngestionJobModel) -> bool:
        """
        Check if job has exceeded maximum runtime.
        
        Args:
            job: The ingestion job to check
        
        Returns:
            True if job exceeded timeout, False otherwise
        """
        from datetime import timedelta
        
        MAX_JOB_RUNTIME = timedelta(hours=24)
        
        if not job.started_at:
            return False
        
        runtime = datetime.utcnow() - job.started_at
        
        if runtime > MAX_JOB_RUNTIME:
            logger.error(
                f"Job {job.id} exceeded timeout: {runtime} > {MAX_JOB_RUNTIME}"
            )
            
            # Fail the job in database
            try:
                db = get_database()
                async with db.session() as session:
                    from ...storage.repositories import IngestionJobRepository
                    repo = IngestionJobRepository(session)
                    current_job = await repo.get_by_id(job.id)
                    
                    if current_job and current_job.status == "processing":
                        current_job.status = "failed"
                        current_job.error_message = (
                            f"Job timeout: exceeded maximum runtime of {MAX_JOB_RUNTIME} "
                            f"(actual: {runtime})"
                        )
                        current_job.completed_at = datetime.utcnow()
                        
                        # Update metadata
                        if current_job.job_metadata:
                            metadata = current_job.job_metadata.copy()
                        else:
                            metadata = {}
                        
                        metadata["timeout_detected_at"] = datetime.utcnow().isoformat()
                        metadata["runtime_seconds"] = runtime.total_seconds()
                        metadata["max_runtime_seconds"] = MAX_JOB_RUNTIME.total_seconds()
                        metadata["timeout_reason"] = "exceeded_max_runtime"
                        current_job.job_metadata = metadata
                        
                        flag_modified(current_job, "job_metadata")
                        await repo.update(current_job)
                        await session.commit()
                        
                        logger.warning(f"Job {job.id} marked as failed due to timeout")
            
            except Exception as e:
                logger.error(f"Failed to update job timeout status: {e}", exc_info=True)
            
            return True
        
        return False
    
    async def _update_worker_heartbeat(self, job: IngestionJobModel):
        """
        Update worker heartbeat in job metadata.
        
        Called every 30 files to indicate worker is alive and processing.
        Used to detect truly stuck workers.
        
        Args:
            job: The ingestion job
        """
        try:
            db = get_database()
            async with db.session() as session:
                from ...storage.repositories import IngestionJobRepository
                repo = IngestionJobRepository(session)
                current_job = await repo.get_by_id(job.id)
                
                if not current_job:
                    return
                
                # Update heartbeat in metadata
                if current_job.job_metadata:
                    metadata = current_job.job_metadata.copy()
                else:
                    metadata = {}
                
                metadata["worker_heartbeat"] = datetime.utcnow().isoformat()
                metadata["worker_id"] = self.worker_id
                current_job.job_metadata = metadata
                
                flag_modified(current_job, "job_metadata")
                await repo.update(current_job)
                await session.commit()
                
                logger.debug(f"Worker heartbeat updated for job {job.id}")
        
        except Exception as e:
            # Don't fail job if heartbeat update fails
            logger.debug(f"Failed to update worker heartbeat: {e}")
    
    async def _update_job_progress(
        self,
        job: IngestionJobModel,
        last_file: str,
        current_commit: str,
        processed: int,
        skipped: int,
        failed: int,
        current_file_index: int = 0,
        total_files: int = 0
    ):
        """
        Update job metadata with current progress.
        
        Args:
            job: The ingestion job
            last_file: Last file that was processed
            current_commit: Current commit SHA (short)
            processed: Number of documents processed
            skipped: Number of documents skipped
            failed: Number of documents failed
            current_file_index: Current file index being processed
            total_files: Total files in current commit
        """
        try:
            db = get_database()
            async with db.session() as session:
                from ...storage.repositories import IngestionJobRepository
                repo = IngestionJobRepository(session)
                
                # Get fresh job instance
                current_job = await repo.get_by_id(job.id)
                if not current_job:
                    return
                
                # Update metadata
                # IMPORTANT: Create new dict to ensure SQLAlchemy detects the change
                metadata = current_job.job_metadata.copy() if current_job.job_metadata else {}
                metadata["last_processed_file"] = last_file
                metadata["current_commit"] = current_commit
                metadata["last_update"] = datetime.utcnow().isoformat()
                metadata["current_file_index"] = current_file_index
                metadata["total_files_in_commit"] = total_files
                metadata["progress_pct"] = round((current_file_index / total_files * 100) if total_files > 0 else 0, 1)
                current_job.job_metadata = metadata  # Assign new dict to trigger change detection
                
                # Update counters
                current_job.processed_documents = processed
                current_job.skipped_documents = skipped
                current_job.failed_documents = failed
                
                # Mark the JSONB column as modified so SQLAlchemy knows to update it
                flag_modified(current_job, "job_metadata")
                
                await repo.update(current_job)
                await session.commit()
                
                logger.debug(f"Updated job progress: {current_file_index}/{total_files} files ({metadata.get('progress_pct', 0)}%)")
                
        except Exception as e:
            # Don't fail the job if metadata update fails
            logger.error(f"Failed to update job progress metadata: {type(e).__name__}: {e}", exc_info=True)
            if 'current_job' in locals():
                logger.error(f"Job ID: {current_job.id}")
                logger.error(f"Job metadata type: {type(current_job.job_metadata)}")
                logger.error(f"Job metadata value: {current_job.job_metadata}")
            
            # Record failure in monitoring system
            try:
                from ...utils.database_update_monitor import record_update_failure
                await record_update_failure(
                    operation="update",
                    table="ingestion_jobs",
                    error=e,
                    job_id=str(job.id)
                )
            except Exception as monitor_error:
                logger.debug(f"Failed to record monitoring failure: {monitor_error}")
    
    async def _load_checkpoint(self, job_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Load checkpoint for job recovery.
        
        Args:
            job_id: Job ID to load checkpoint for
        
        Returns:
            Checkpoint data or None if no checkpoint exists
        """
        try:
            checkpoint = await self.checkpoint_manager.load_checkpoint(str(job_id))
            return checkpoint
        except Exception as e:
            logger.debug(f"No checkpoint found or failed to load: {e}")
            return None
    
    def _finalize_result(self, result: Dict[str, Any], job: IngestionJobModel) -> Dict[str, Any]:
        """
        Apply error aggregation logic to job result before returning.
        
        This ensures ALL code paths apply consistent success/failure logic.
        
        Args:
            result: The result dict to finalize
            job: The ingestion job
            
        Returns:
            The finalized result dict with success field properly set
        """
        # Calculate total if not already set
        if "total_documents" not in result or result["total_documents"] == 0:
            result["total_documents"] = (result.get("processed_documents", 0) + 
                                         result.get("failed_documents", 0) + 
                                         result.get("skipped_documents", 0))
        
        # DEBUG: Log values before error aggregation check
        logger.info(
            f"🔍 FINALIZE RESULT for job {job.id}: "
            f"processed={result.get('processed_documents', 0)}, "
            f"skipped={result.get('skipped_documents', 0)}, "
            f"failed={result.get('failed_documents', 0)}, "
            f"total={result['total_documents']}"
        )
        
        # Apply GRACEFUL error aggregation logic
        processed = result.get("processed_documents", 0)
        failed = result.get("failed_documents", 0)
        skipped = result.get("skipped_documents", 0)
        cancelled = result.get("cancelled_documents", 0)  # New: track cancelled/hung commits
        total = result["total_documents"]
        
        # Check if all commits failed (no documents processed or skipped)
        if processed == 0 and skipped == 0 and failed > 0:
            result["success"] = False
            result["error"] = f"All {failed} commits failed processing. Check git repository integrity."
            logger.error(
                f"❌ Job {job.id} FAILED: All {failed} documents failed to process. "
                f"This may indicate git repository corruption or configuration issues."
            )
            logger.info(f"🔍 FINALIZE: Set success=False (all commits failed)")
        elif processed == 0 and total > 0:
            # Some files were skipped but none processed (partial failure)
            result["success"] = False
            result["error"] = "No documents were processed successfully"
            logger.warning(
                f"⚠️  Job {job.id} FAILED: No successful processing. "
                f"Skipped: {skipped}, Failed: {failed}, Cancelled: {cancelled}"
            )
            logger.info(f"🔍 FINALIZE: Set success=False (no processing)")
        else:
            # GRACEFUL SUCCESS: Some processing succeeded (even if some failed)
            result["success"] = True
            
            # Add warning if there were failures/cancellations but still partial success
            if failed > 0 or cancelled > 0:
                success_rate = (processed / total) * 100 if total > 0 else 0
                result["warning"] = (
                    f"Partial success: {processed}/{total} commits succeeded ({success_rate:.1f}%). "
                    f"Failed: {failed}, Cancelled: {cancelled}, Skipped: {skipped}"
                )
                logger.warning(
                    f"⚠️  Job {job.id} PARTIAL SUCCESS: {processed}/{total} commits processed ({success_rate:.1f}%). "
                    f"Failed: {failed}, Cancelled: {cancelled}, Skipped: {skipped}"
                )
            else:
                # Full success
                logger.info(
                    f"✅ Job {job.id} FULL SUCCESS: {processed} documents processed, "
                    f"{skipped} skipped (already up-to-date)"
                )
            
            logger.info(f"🔍 FINALIZE: Set success=True (processing succeeded)")
        
        return result
    
    async def _ensure_git_commit_exists(
        self,
        git_commit_sha: str,
        git_metadata: Dict[str, Any],
        repo_path: str
    ) -> Optional[str]:
        """
        Ensure git commit exists in database using SEPARATE transaction.
        
        This is critical to avoid foreign key violations when documents reference commits.
        Creates commit in its own isolated transaction before document insert.
        
        Args:
            git_commit_sha: The commit SHA to ensure exists
            git_metadata: Metadata about the commit
            repo_path: Repository path
        
        Returns:
            The commit SHA if successful, None if failed
        """
        logger.debug(f"🔍 [COMMIT-CREATE-1] Starting separate transaction for commit: {git_commit_sha[:8]}")
        
        try:
            from ...storage.db_models import GitCommitModel
            from sqlalchemy import select
            
            # Create commit in its OWN session/transaction
            db = get_database()
            async with db.session() as commit_session:
                logger.debug(f"🔍 [COMMIT-CREATE-2] Checking if commit exists...")
                
                # Check if commit already exists
                result = await commit_session.execute(
                    select(GitCommitModel).where(GitCommitModel.sha == git_commit_sha)
                )
                existing_commit = result.scalar_one_or_none()
                
                if existing_commit:
                    logger.debug(f"♻️  [COMMIT-CREATE-3-EXISTS] Commit already exists: {git_commit_sha[:8]}")
                    return git_commit_sha
                
                # Create new commit
                logger.info(f"📝 [COMMIT-CREATE-3-NEW] Creating git commit: {git_commit_sha[:8]}")
                
                git_commit = GitCommitModel(
                    sha=git_commit_sha,
                    author=git_metadata.get("last_commit_author", "Unknown"),
                    author_email=git_metadata.get("last_commit_author_email", ""),
                    commit_date=datetime.fromisoformat(git_metadata["last_commit_date"]) if git_metadata.get("last_commit_date") else datetime.now(),
                    message=git_metadata.get("last_commit_message", ""),
                    repo_path=str(repo_path)
                )
                
                commit_session.add(git_commit)
                logger.debug(f"🔍 [COMMIT-CREATE-4] Committing transaction...")
                await commit_session.commit()  # ✅ SEPARATE COMMIT!
                logger.info(f"✅ [COMMIT-CREATE-5] Git commit committed successfully: {git_commit_sha[:8]}")
                
                return git_commit_sha
                
        except Exception as e:
            logger.error(f"❌ [COMMIT-CREATE-ERROR] Failed to create commit {git_commit_sha[:8]}: {e}", exc_info=True)
            return None
    
    async def process(self, job: IngestionJobModel) -> Dict[str, Any]:
        """
        Process a single ingestion job.
        
        PHASE 10 ENHANCEMENT: Supports sub-job orchestration for parallel processing.
        
        Args:
            job: Ingestion job to process
        
        Returns:
            Dict with processing results:
            {
                "success": bool,
                "processed_documents": int,
                "total_documents": int,
                "failed_documents": int,
                "embeddings_generated": int,
                "total_cost_usd": float,
                "error": Optional[str],
                "subjobs_executed": Optional[int],  # NEW (if orchestration used)
                "subjobs_failed": Optional[int]  # NEW (if orchestration used)
            }
        """
        logger.info(f"🔍 DEBUG: process() ENTRY for job {job.id}: mode={job.mode}, repo={job.repo_path}")
        logger.info(f"Processing job {job.id}: mode={job.mode}, repo={job.repo_path}")
        
        # PHASE 10: Check if sub-job orchestration requested
        use_subjobs = job.job_metadata.get('use_subjobs', False) if job.job_metadata else False
        
        if use_subjobs and await self._should_use_orchestration(job):
            logger.info(f"🚀 Using sub-job orchestration for job {job.id}")
            orch_result = await self._process_with_orchestration(job)
            logger.info(f"🔍 DEBUG: process() EXIT (orchestration path) for job {job.id}")
            return self._finalize_result(orch_result, job)
        else:
            if use_subjobs:
                logger.info(f"📝 Repository too small for orchestration, using standard processing")
            else:
                logger.info(f"📝 Using standard processing (orchestration not requested)")
        
        # If not using orchestration, continue with standard processing below
        if not (use_subjobs and await self._should_use_orchestration(job)):
            # Continue with existing standard processing logic
            pass
        else:
            # Return orchestration result
            orch_result = await self._process_with_orchestration(job)
            logger.info(f"🔍 DEBUG: process() EXIT (orchestration path 2) for job {job.id}")
            return self._finalize_result(orch_result, job)
        
        # ========================================================================
        # STANDARD PROCESSING (Existing Logic Below)
        # ========================================================================
        
        # Initialize real-time progress tracking
        await self._init_progress_tracking(str(job.id))
        
        result = {
            "success": False,
            "processed_documents": 0,
            "total_documents": 0,
            "failed_documents": 0,
            "skipped_documents": 0,  # NEW: Track skipped separately
            "embeddings_generated": 0,
            "total_cost_usd": 0.0,
            "error": None
        }
        
        try:
            # 🎯 FIX: Don't initialize GitService for snapshot/enriched modes yet
            # These modes may be given subdirectory paths, not git roots
            # GitService will be lazy-initialized when needed
            if job.mode not in ["snapshot", "enriched"]:
                # Only initialize for full/incremental modes that need git history upfront
                await self._update_progress("initializing", 0, 100, message="Initializing Git service...")
                self.git_service = GitService(repo_path=job.repo_path)
            
            # Get commits based on mode
            await self._update_progress("scanning", 10, 100, message="Scanning repository for commits...")
            commits = await self._get_commits_for_mode(job.mode) if job.mode not in ["snapshot", "enriched"] else []
            
            # Special handling for snapshot and enriched modes (no full git history)
            if (job.mode == "snapshot" or job.mode == "enriched") and not commits:
                if job.mode == "enriched":
                    logger.info("✨ Enriched mode: processing current filesystem state WITH git metadata")
                    await self._update_progress("processing", 0, 1, message="Processing current files with git metadata (enriched mode)")
                else:
                    logger.info("📸 Snapshot mode: processing current filesystem state without git history")
                    await self._update_progress("processing", 0, 1, message="Processing current filesystem state (snapshot mode)")
                
                # Process current filesystem directly (enriched mode will fetch git metadata per file)
                snapshot_result = await self._process_snapshot_mode(job)
                logger.info(f"🔍 DEBUG: process() EXIT ({job.mode} mode) for job {job.id}")
                return self._finalize_result(snapshot_result, job)
            
            if not commits:
                result["error"] = "No commits found"
                await self._update_progress("failed", 0, 0, message="No commits found")
                logger.info(f"🔍 DEBUG: process() EXIT (no commits) for job {job.id}")
                return self._finalize_result(result, job)
            
            logger.info(f"Found {len(commits)} commits to process")
            await self._update_progress("processing", 0, len(commits), message=f"Found {len(commits)} commits")
            
            # PHASE 2: Process commits with BATCHING and CHECKPOINTING for resilience
            if self.use_batched_processing and len(commits) > self.commit_batch_size:
                logger.info(
                    f"📦 PHASE 2: Processing {len(commits)} commits in BATCHES "
                    f"(batch size: {self.commit_batch_size}, max {self.max_concurrent_commits} concurrent per batch)"
                )
                
                # Check for existing checkpoint to resume from
                checkpoint = await self._load_checkpoint(job.id)
                resume_from_batch = 0
                
                if checkpoint:
                    resume_from_batch = checkpoint.get("next_batch", 0)
                    if resume_from_batch > 0:
                        logger.info(
                            f"🔄 Resuming from checkpoint: batch {resume_from_batch + 1}, "
                            f"{checkpoint.get('processed_documents', 0)} documents already processed"
                        )
                        # Restore previous results
                        result["processed_documents"] = checkpoint.get("processed_documents", 0)
                        result["failed_documents"] = checkpoint.get("failed_documents", 0)
                        result["skipped_documents"] = checkpoint.get("skipped_documents", 0)
                        result["embeddings_generated"] = checkpoint.get("embeddings_generated", 0)
                        result["total_cost_usd"] = checkpoint.get("total_cost_usd", 0.0)
                
                # Initialize batched processor
                from .batched_commit_processor import get_batched_commit_processor
                if self._batched_processor is None:
                    self._batched_processor = get_batched_commit_processor(
                        job_processor=self,
                        batch_size=self.commit_batch_size,
                        max_concurrent_per_batch=self.max_concurrent_commits
                    )
                
                # Process commits in batches with checkpointing
                batch_result = await self._batched_processor.process_commits_in_batches(
                    commits=commits,
                    job=job,
                    resume_from_batch=resume_from_batch
                )
                
                # Merge batch results into main result
                result["processed_documents"] += batch_result["processed_documents"]
                result["failed_documents"] += batch_result["failed_documents"]
                result["skipped_documents"] += batch_result["skipped_documents"]
                result["embeddings_generated"] += batch_result["embeddings_generated"]
                result["total_cost_usd"] += batch_result["total_cost_usd"]
                
            # FALLBACK: Process commits in PARALLEL without batching (original behavior)
            elif self.use_batch_optimization and len(commits) > 1:
                logger.info(
                    f"🚀 PHASE 2: Processing {len(commits)} commits in PARALLEL "
                    f"(max {self.max_concurrent_commits} concurrent, no batching)"
                )
                
                # Create tasks for all commits (wrap coroutines in tasks for asyncio.wait())
                import asyncio
                commit_tasks = [
                    asyncio.create_task(self._process_commit_parallel(commit, job, i, len(commits)))
                    for i, commit in enumerate(commits, 1)
                ]
                
                # ENHANCEMENT: Add progress monitoring during parallel execution
                # This helps detect hangs by logging periodic status
                start_time = datetime.utcnow()
                
                # Create a monitoring task that logs progress every 30 seconds
                async def monitor_progress():
                    """Monitor and log commit processing progress."""
                    while True:
                        await asyncio.sleep(30)
                        elapsed = (datetime.utcnow() - start_time).total_seconds()
                        logger.info(
                            f"⏳ Parallel processing ongoing: {elapsed:.0f}s elapsed, "
                            f"{len(commits)} commits in flight"
                        )
                
                # Start monitoring task (will be cancelled when processing completes)
                monitor_task = asyncio.create_task(monitor_progress())
                
                # GRACEFUL DEGRADATION: Use asyncio.wait() instead of gather()
                # This allows us to handle partial results and cancel hung tasks
                commit_tasks_set = set(commit_tasks)
                max_wait_time = len(commits) * 90  # 90s per commit max (generous for graceful handling)
                
                try:
                    # Wait for all tasks with timeout (graceful degradation enabled)
                    done, pending = await asyncio.wait(
                        commit_tasks_set,
                        timeout=max_wait_time,
                        return_when=asyncio.ALL_COMPLETED
                    )
                    
                    # Handle pending (hung) tasks
                    if pending:
                        hung_count = len(pending)
                        logger.warning(
                            f"⚠️  {hung_count} commit(s) still pending after {max_wait_time}s - "
                            f"CANCELLING hung tasks for graceful degradation"
                        )
                        
                        # Cancel all pending tasks
                        for task in pending:
                            task.cancel()
                        
                        # Wait briefly for cancellations to complete
                        if pending:
                            await asyncio.wait(pending, timeout=5)
                        
                        logger.info(
                            f"✅ Cancelled {hung_count} hung tasks - "
                            f"proceeding with {len(done)} completed commits"
                        )
                    
                    # Extract results from completed tasks
                    commit_results = []
                    for task in done:
                        try:
                            result = task.result()
                            commit_results.append(result)
                        except Exception as e:
                            logger.error(f"Task failed with exception: {e}")
                            commit_results.append(e)
                    
                    # For cancelled tasks, add placeholder results
                    for task in pending:
                        commit_results.append({
                            "processed": 0,
                            "failed": 1,
                            "skipped": 0,
                            "embeddings": 0,
                            "cost": 0.0,
                            "error": "Task cancelled due to hang/timeout",
                            "cancelled": True
                        })
                    
                finally:
                    # Stop monitoring
                    monitor_task.cancel()
                    try:
                        await monitor_task
                    except asyncio.CancelledError:
                        pass
                
                # Log completion
                total_elapsed = (datetime.utcnow() - start_time).total_seconds()
                completed_count = len(commit_results)
                logger.info(
                    f"✅ Parallel processing complete: {completed_count}/{len(commits)} commits processed in {total_elapsed:.1f}s "
                    f"({total_elapsed/completed_count:.1f}s per commit avg)"
                )
                
                # Aggregate results from all commits
                partial_successes = 0
                for idx, commit_result in enumerate(commit_results, 1):
                    if isinstance(commit_result, Exception):
                        logger.error(f"Commit {idx} failed with exception: {commit_result}")
                        result["failed_documents"] += 1
                    else:
                        result["processed_documents"] += commit_result["processed"]
                        result["failed_documents"] += commit_result["failed"]
                        result["skipped_documents"] += commit_result.get("skipped", 0)
                        result["embeddings_generated"] += commit_result["embeddings"]
                        result["total_cost_usd"] += commit_result.get("cost", 0.0)
                        
                        # Track partial successes (metadata extracted but processing failed)
                        if commit_result.get("partial_success"):
                            partial_successes += 1
                    
                    # Update progress after each commit
                    await self._update_progress(
                        "processing",
                        idx,
                        len(commits),
                        message=f"Processed {idx}/{len(commits)} commits",
                        processed=result["processed_documents"],
                        failed=result["failed_documents"],
                        skipped=result["skipped_documents"],
                        embeddings=result["embeddings_generated"]
                    )
                
                # Log summary with partial success info
                if partial_successes > 0:
                    logger.info(
                        f"📋 Partial successes: {partial_successes} commits had metadata extracted "
                        f"despite processing failures"
                    )
            else:
                # Fallback to sequential processing for single commit or non-batch mode
                logger.info(f"Processing {len(commits)} commits sequentially")
                
                for i, commit in enumerate(commits, 1):
                    logger.info(f"Processing commit {i}/{len(commits)}: {commit.sha[:8]}")
                    
                    await self._update_progress(
                        "processing",
                        i - 1,
                        len(commits),
                        message=f"Processing commit {i}/{len(commits)}: {commit.sha[:8]}",
                        current_commit=commit.sha[:8]
                    )
                    
                    # Use optimized batch processing if enabled
                    if self.use_batch_optimization:
                        # Phase 1.5: Increased batch size from 10 to 20 for better throughput
                        commit_result = await self._process_commit_with_batch_optimization(
                            commit, job, batch_size=20
                        )
                    else:
                        commit_result = await self._process_commit(commit, job)
                    
                    result["processed_documents"] += commit_result["processed"]
                    result["failed_documents"] += commit_result["failed"]
                    result["skipped_documents"] += commit_result.get("skipped", 0)
                    result["embeddings_generated"] += commit_result["embeddings"]
                    result["total_cost_usd"] += commit_result.get("cost", 0.0)
                    
                    # Update progress after each commit
                    await self._update_progress(
                        "processing",
                        i,
                        len(commits),
                        message=f"Processed {i}/{len(commits)} commits",
                        processed=result["processed_documents"],
                        failed=result["failed_documents"],
                        skipped=result["skipped_documents"],
                        embeddings=result["embeddings_generated"]
                    )
            
            result["total_documents"] = result["processed_documents"] + result["failed_documents"] + result["skipped_documents"]
            
            # Apply error aggregation via _finalize_result
            result = self._finalize_result(result, job)
            
            # Clear checkpoint after completion (successful or failed)
            await self.checkpoint_manager.clear_checkpoint(job.id)
            
            # Update final progress
            final_status = "completed" if result["success"] else "failed"
            await self._update_progress(
                final_status,
                result["total_documents"],
                result["total_documents"],
                message=f"Completed: {result['processed_documents']} processed, {result['embeddings_generated']} embeddings",
                processed=result["processed_documents"],
                failed=result["failed_documents"],
                skipped=result["skipped_documents"],
                embeddings=result["embeddings_generated"],
                cost=result["total_cost_usd"]
            )
            
            # Log git error summary
            self.git_error_handler.log_error_summary()
            
            if result["success"]:
                logger.info(
                    f"✅ Job {job.id} processing complete: "
                    f"{result['processed_documents']}/{result['total_documents']} documents, "
                    f"{result['skipped_documents']} skipped, "
                    f"{result['embeddings_generated']} embeddings"
                )
            else:
                logger.error(
                    f"❌ Job {job.id} processing failed: {result['error']}"
                )
        
        except Exception as e:
            logger.error(f"Error processing job {job.id}: {e}", exc_info=True)
            result["error"] = str(e)
            
            # Log git error summary even on failure
            self.git_error_handler.log_error_summary()
            
            await self._update_progress(
                "failed",
                0,
                0,
                message=f"Failed: {str(e)}",
                error=str(e)
            )
            
            # Finalize result even on exception
            result = self._finalize_result(result, job)
        
        logger.info(f"🔍 DEBUG: process() EXIT (main return) for job {job.id}")
        return result
    
    async def _process_snapshot_mode(self, job: IngestionJobModel) -> Dict[str, Any]:
        """
        Process files in snapshot mode (no git history).
        
        Scans the current filesystem and processes all files directly without
        accessing git history. This is useful for:
        - Repositories with git corruption
        - Quick ingestion without historical context
        - Non-git directories (if supported)
        
        Args:
            job: The ingestion job
        
        Returns:
            Result dictionary with processing statistics
        """
        from pathlib import Path
        import os
        
        result = {
            "success": False,
            "processed_documents": 0,
            "total_documents": 0,
            "failed_documents": 0,
            "skipped_documents": 0,
            "embeddings_generated": 0,
            "embeddings_failed": 0,
            "embeddings_skipped": 0,
            "total_cost_usd": 0.0,
            "error": None
        }
        
        # Initialize embedding error tracking
        self._embedding_errors = []
        
        try:
            repo_path = Path(job.repo_path)
            
            # Scan for all files - NOW WITH ASYNC YIELDING
            logger.info(f"📂 Scanning directory: {repo_path}")
            all_files = []
            
            file_count = 0
            for root, dirs, files in os.walk(repo_path):
                # Skip common directories that shouldn't be processed
                dirs[:] = [d for d in dirs if d not in {
                    '.git', '__pycache__', 'node_modules', 'venv', 'env',
                    '.venv', '.tox', 'dist', 'build', '.egg-info',
                    'htmlcov', '.pytest_cache', '.mypy_cache', 'data',
                    'pgdata', 'pg_wal', 'chroma_db', 'postgresql', 'redis',
                    'backups', '.pytest_cache', '.mypy_cache', 'htmlcov',
                    'node_modules', 'venv_audit', 'venv_hardening', 'venv_validation',
                    'test_env', 'demo_venv', '.venv', 'logs'
                }]
                
                # Yield control every 100 files to prevent blocking
                for file in files:
                    file_count += 1
                    if file_count % 100 == 0:
                        await asyncio.sleep(0)  # Yield control to event loop
                        logger.debug(f"📂 Scanned {file_count} files...")
                    file_path = Path(root) / file
                    
                    # Skip symlinks and special files
                    if file_path.is_symlink() or not file_path.is_file():
                        logger.debug(f"Skipping symlink/special file: {file}")
                        continue
                    
                    # Skip binary files by extension
                    binary_extensions = {
                        '.so', '.pyc', '.pyd', '.dll', '.exe', '.bin', '.dat',
                        '.db', '.sqlite', '.sqlite3', '.whl', '.egg', '.jar',
                        '.class', '.o', '.a', '.dylib', '.png', '.jpg', '.jpeg',
                        '.gif', '.ico', '.pdf', '.zip', '.tar', '.gz', '.bz2',
                        '.7z', '.rar', '.mp3', '.mp4', '.avi', '.mov', '.woff',
                        '.woff2', '.ttf', '.eot', '.otf', '.npz', '.npy'
                    }
                    
                    if file_path.suffix.lower() in binary_extensions:
                        logger.debug(f"Skipping binary file: {file}")
                        continue
                    
                    # Skip files with no extension that are likely binary
                    try:
                        if not file_path.suffix and file_path.stat().st_size > 1024 * 1024:  # 1MB
                            logger.debug(f"Skipping large file without extension: {file}")
                            continue
                    except (OSError, FileNotFoundError):
                        logger.debug(f"Skipping inaccessible file: {file}")
                        continue
                    
                    # Get relative path from repo root
                    try:
                        rel_path = file_path.relative_to(repo_path)
                        all_files.append(str(rel_path))
                    except ValueError:
                        continue
            
            logger.info(f"📊 Found {len(all_files)} files to process")
            
            # 🛡️  SAFETY: Limit maximum files to prevent runaway processing
            MAX_FILES_PER_JOB = 10000
            if len(all_files) > MAX_FILES_PER_JOB:
                logger.warning(
                    f"⚠️  Too many files ({len(all_files)})! Limiting to {MAX_FILES_PER_JOB}. "
                    f"Please use a more specific directory path."
                )
                all_files = all_files[:MAX_FILES_PER_JOB]
            
            result["total_documents"] = len(all_files)
            
            if not all_files:
                result["success"] = True
                result["error"] = "No files found in directory"
                await self._update_progress("completed", 0, 0, message="No files found")
                return result
            
            await self._update_progress("processing", 0, len(all_files), message=f"Processing {len(all_files)} files")
            
            # Process files in batches
            batch_size = 50
            for i in range(0, len(all_files), batch_size):
                batch = all_files[i:i + batch_size]
                
                for file_path in batch:
                    try:
                        full_path = repo_path / file_path
                        
                        # Read file content
                        try:
                            content = full_path.read_text(encoding='utf-8', errors='ignore')
                        except Exception as e:
                            logger.debug(f"Skipping binary/unreadable file: {file_path}")
                            result["skipped_documents"] += 1
                            continue
                        
                        # Process the document
                        doc_result = await self._process_snapshot_document(
                            file_path=str(file_path),
                            content=content,
                            job=job
                        )
                        
                        if doc_result["success"]:
                            # Check if it was skipped (duplicate)
                            if doc_result.get("skipped"):
                                result["skipped_documents"] += 1
                                # Track if duplicate had embedding
                                if doc_result.get("embedding_exists"):
                                    result["embeddings_skipped"] += 1
                            else:
                                result["processed_documents"] += 1
                                # Track embedding results
                                if doc_result.get("embedding_generated"):
                                    result["embeddings_generated"] += 1
                                elif doc_result.get("embedding_error"):
                                    result["embeddings_failed"] += 1
                                    logger.warning(f"⚠️  Embedding failed for {file_path}: {doc_result['embedding_error']}")
                        else:
                            result["failed_documents"] += 1
                            if doc_result.get("embedding_error"):
                                result["embeddings_failed"] += 1
                    
                    except Exception as e:
                        logger.error(f"Error processing {file_path}: {e}")
                        result["failed_documents"] += 1
                
                # Update progress after each batch
                processed_so_far = min(i + batch_size, len(all_files))
                await self._update_progress(
                    "processing",
                    processed_so_far,
                    len(all_files),
                    message=f"Processed {processed_so_far}/{len(all_files)} files",
                    processed=result["processed_documents"],
                    failed=result["failed_documents"],
                    skipped=result["skipped_documents"],
                    embeddings=result["embeddings_generated"]
                )
                
                # ✅ FIXED: Update job counters in database after each batch
                await self._update_job_counters_snapshot(job, result)
            
            result["success"] = True
            await self._update_progress(
                "completed",
                result["total_documents"],
                result["total_documents"],
                message=f"Snapshot complete: {result['processed_documents']} processed",
                processed=result["processed_documents"],
                failed=result["failed_documents"],
                skipped=result["skipped_documents"],
                embeddings=result["embeddings_generated"]
            )
            
            # ✅ FIXED: Final update of job counters in database
            await self._update_job_counters_snapshot(job, result)
            
            # Calculate embedding coverage
            embedding_coverage = 0
            if result['processed_documents'] > 0:
                embedding_coverage = (result['embeddings_generated'] / result['processed_documents']) * 100
            
            logger.info(
                f"✅ Snapshot mode complete: "
                f"{result['processed_documents']}/{result['total_documents']} documents, "
                f"{result['skipped_documents']} skipped"
            )
            logger.info(
                f"📊 Embeddings: {result['embeddings_generated']} generated, "
                f"{result['embeddings_failed']} failed, "
                f"{result['embeddings_skipped']} skipped (duplicates), "
                f"coverage: {embedding_coverage:.1f}%"
            )
            
            # Log embedding errors summary if any
            if self._embedding_errors:
                logger.error(f"⚠️  Embedding errors encountered: {len(self._embedding_errors)} total")
                error_types = {}
                for err in self._embedding_errors[:10]:  # Show first 10
                    error_type = err.get("error_type", "unknown")
                    error_types[error_type] = error_types.get(error_type, 0) + 1
                    logger.error(f"   - {err['file_path']}: {err['error'][:100]}")
                
                if len(self._embedding_errors) > 10:
                    logger.error(f"   ... and {len(self._embedding_errors) - 10} more")
                
                logger.error(f"📊 Error types: {error_types}")
        
        except Exception as e:
            logger.error(f"Error in snapshot mode: {e}", exc_info=True)
            result["error"] = str(e)
            await self._update_progress("failed", 0, 0, message=f"Failed: {str(e)}", error=str(e))
        
        return result
    
    async def _update_job_counters_snapshot(self, job: IngestionJobModel, result: Dict[str, Any]):
        """
        Update job counters in database for snapshot mode.
        
        Args:
            job: Ingestion job
            result: Current result dictionary with counters
        """
        try:
            db = get_database()
            async with db.session() as session:
                from ...storage.repositories import IngestionJobRepository
                repo = IngestionJobRepository(session)
                
                # Get fresh job instance
                current_job = await repo.get_by_id(job.id)
                if not current_job:
                    logger.warning(f"Job {job.id} not found in database, skipping counter update")
                    return
                
                # Update counters
                current_job.processed_documents = result["processed_documents"]
                current_job.failed_documents = result["failed_documents"]
                current_job.skipped_documents = result["skipped_documents"]
                current_job.embeddings_generated = result.get("embeddings_generated", 0)
                current_job.total_documents = result.get("total_documents", 0)
                
                await repo.update(current_job)
                await session.commit()
                
                logger.debug(
                    f"📊 Database counters updated: "
                    f"processed={current_job.processed_documents}, "
                    f"skipped={current_job.skipped_documents}, "
                    f"failed={current_job.failed_documents}, "
                    f"embeddings={current_job.embeddings_generated}"
                )
                
        except Exception as e:
            logger.warning(f"Failed to update job counters in database: {e}")
            # Don't raise - this is not critical enough to fail the job
    
    async def _process_snapshot_document(
        self,
        file_path: str,
        content: str,
        job: IngestionJobModel
    ) -> Dict[str, Any]:
        """
        Process a single document in snapshot mode.
        
        In enriched mode, also fetches git metadata (last commit) for the file.
        
        Args:
            file_path: Relative path to file
            content: File content
            job: The ingestion job
        
        Returns:
            Result dictionary
        """
        from ...storage.repositories import DocumentRepository
        from ...storage import get_database
        from ...storage.db_models import DocumentModel
        import hashlib
        
        # 🛡️ CRITICAL: Skip binary files to prevent PostgreSQL errors
        if self.is_binary_file_extension(file_path):
            logger.info(f"⏭️  Skipping binary file (by extension): {file_path}")
            return {
                "success": True,
                "skipped": True,
                "reason": "binary_file_extension"
            }
        
        # 🛡️ CRITICAL: Check for null bytes in content (binary file indicator)
        if '\x00' in content:
            logger.warning(f"⚠️  Skipping file with null bytes (binary content): {file_path}")
            return {
                "success": True,
                "skipped": True,
                "reason": "binary_content_detected"
            }
        
        # ✨ ENRICHED MODE: Fetch metadata with fail-fast protections
        git_metadata = None
        git_commit_sha = None
        
        if job.mode == "enriched":
            logger.info(f"🔍 [ENRICH-1] Starting enriched metadata extraction for: {file_path}")
            import time
            enrich_start = time.time()
            
            try:
                logger.debug(f"🔍 [ENRICH-2] Checking GitService initialization...")
                # 🎯 FIX: Lazy-initialize GitService for enriched mode
                if not self.git_service:
                    logger.info(f"🔍 [ENRICH-3] Initializing GitService...")
                    from ..git.git_service import find_git_root
                    init_start = time.time()
                    git_root = find_git_root(job.repo_path)
                    logger.info(f"✅ [ENRICH-4] Found git root: {git_root} (took {time.time()-init_start:.2f}s)")
                    
                    self.git_service = GitService(repo_path=git_root)
                    logger.info(f"✅ [ENRICH-5] GitService initialized")
                else:
                    logger.debug(f"♻️  [ENRICH-3-SKIP] GitService already initialized")
                
                # ⏱️ FAIL-FAST: Timeout git operations after 5 seconds
                logger.debug(f"🔍 [ENRICH-6] Fetching git history for file...")
                git_start = time.time()
                
                try:
                    file_history = await asyncio.wait_for(
                        self.git_service.get_file_history(file_path, max_commits=1),
                        timeout=5.0  # 5 second timeout
                    )
                    git_duration = time.time() - git_start
                    logger.debug(f"⏱️  [ENRICH-7] Git history fetch took {git_duration:.2f}s")
                    
                    if file_history:
                        last_commit = file_history[0]
                        git_metadata = {
                            "last_commit_sha": last_commit.sha,
                            "last_commit_author": last_commit.author,
                            "last_commit_date": last_commit.date.isoformat() if last_commit.date else None,
                            "last_commit_message": last_commit.message,
                            "enriched_mode": True,
                            "metadata_source": "git",
                            "extraction_time_sec": git_duration
                        }
                        git_commit_sha = last_commit.sha
                        logger.info(f"✅ [ENRICH-8] Git metadata extracted: {last_commit.sha[:8]} by {last_commit.author} ({git_duration:.2f}s)")
                    else:
                        logger.warning(f"⚠️  [ENRICH-8-EMPTY] No git history for {file_path}")
                        
                except asyncio.TimeoutError:
                    logger.error(f"⏱️  [ENRICH-7-TIMEOUT] Git history fetch timed out after 5s for {file_path}")
                    raise  # Re-raise to trigger fallback
                    
            except Exception as e:
                logger.warning(f"⚠️  [ENRICH-9-ERROR] Failed to fetch git metadata: {e}")
                logger.info(f"📁 [ENRICH-10] Falling back to filesystem metadata...")
            
            # 🆕 FALLBACK: Use filesystem metadata when git info unavailable
            if not git_metadata:
                logger.debug(f"🔍 [ENRICH-11] Starting filesystem metadata fallback...")
                try:
                    fs_start = time.time()
                    full_path = Path(job.repo_path) / file_path
                    
                    if full_path.exists():
                        logger.debug(f"🔍 [ENRICH-12] Getting file stats...")
                        stat = os.stat(full_path)
                        fs_duration = time.time() - fs_start
                        
                        git_metadata = {
                            "file_mtime": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            "file_ctime": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                            "file_size": stat.st_size,
                            "enriched_mode": True,
                            "metadata_source": "filesystem",
                            "fallback_reason": "git_unavailable",
                            "extraction_time_sec": fs_duration
                        }
                        logger.info(f"✅ [ENRICH-13] Filesystem metadata extracted: mtime={datetime.fromtimestamp(stat.st_mtime)}, size={stat.st_size} ({fs_duration:.3f}s)")
                    else:
                        logger.error(f"❌ [ENRICH-12-NOTFOUND] File does not exist: {full_path}")
                        
                except Exception as fs_error:
                    logger.error(f"❌ [ENRICH-14-ERROR] Filesystem metadata failed: {fs_error}")
                    # Continue without any metadata
            
            enrich_total = time.time() - enrich_start
            logger.info(f"✅ [ENRICH-COMPLETE] Metadata extraction finished in {enrich_total:.2f}s (source: {git_metadata.get('metadata_source', 'none') if git_metadata else 'none'})")
        
        try:
            # Generate content hash for deduplication
            content_hash = hashlib.sha256(content.encode()).hexdigest()
            
            # Normalize the document
            from ..processing.normalizer_factory import NormalizerFactory
            normalizer_factory = NormalizerFactory()
            
            file_extension = Path(file_path).suffix
            if not file_extension:
                file_extension = '.txt'  # Default for files without extension
            
            normalizer = normalizer_factory.get_normalizer(file_extension)
            
            # Call with correct signature: content, file_path, metadata
            norm_result = await normalizer.normalize(
                content=content,
                file_path=file_path,
                metadata={"ingestion_job_id": str(job.id), "mode": "snapshot"}
            )
            normalized_content = norm_result["content"]
            
            # Store in database
            db = get_database()
            async with db.session() as session:
                doc_repo = DocumentRepository(session)
                
                # Check for duplicates (handle multiple rows gracefully)
                from sqlalchemy import select
                result_query = await session.execute(
                    select(DocumentModel)
                    .where(DocumentModel.content_hash == content_hash)
                    .where(DocumentModel.is_latest == True)
                    .limit(1)
                )
                existing = result_query.scalar_one_or_none()
                
                # Check for duplicates and handle missing embeddings
                if existing:
                    # Check if we should force update (e.g., to fix truncated content in ChromaDB)
                    force_update = job.job_metadata.get('force_update', False) if job.job_metadata else False
                    
                    # Check if embedding is missing
                    needs_embedding = not existing.embedding_id
                    
                    logger.debug(
                        f"🔍 Duplicate check: {file_path} - "
                        f"embedding_id={existing.embedding_id}, needs_embedding={needs_embedding}, force_update={force_update}"
                    )
                    
                    if needs_embedding or force_update:
                        if force_update:
                            logger.info(
                                f"🔄 FORCE UPDATE: Re-processing existing document: {file_path} "
                                f"(doc_id: {existing.id}) - will update ChromaDB content"
                            )
                        else:
                            logger.warning(
                                f"⚠️  Document exists but MISSING EMBEDDING: {file_path} "
                                f"(doc_id: {existing.id}) - will generate embedding"
                            )
                        # Use existing document and generate/update embedding
                        document = existing
                        should_generate_embedding = True
                        is_new_document = False
                    else:
                        logger.debug(f"⏭️  Skipping duplicate with embedding: {file_path}")
                        return {
                            "success": True,
                            "duplicate": True,
                            "skipped": True,
                            "embedding_generated": False,
                            "embedding_exists": True
                        }
                else:
                    # Create new document
                    # Build metadata with optional git metadata
                    doc_metadata = {
                        "ingestion_job_id": str(job.id),
                        "mode": job.mode,  # "snapshot" or "enriched"
                        "snapshot": True,
                        "word_count": len(normalized_content.split())
                    }
                    
                    # ✨ Add git metadata if in enriched mode
                    if git_metadata:
                        doc_metadata.update(git_metadata)
                        # Extract commit SHA (might be None if using filesystem metadata)
                        git_commit_sha = git_metadata.get("last_commit_sha")
                        
                        # 🔧 CRITICAL FIX: Create git commit in SEPARATE transaction
                        if git_commit_sha:
                            logger.info(f"🔍 [COMMIT-1] Ensuring git commit exists: {git_commit_sha[:8]}")
                            commit_start = time.time()
                            
                            try:
                                # ⏱️ FAIL-FAST: Timeout commit creation after 3 seconds
                                git_commit_sha = await asyncio.wait_for(
                                    self._ensure_git_commit_exists(
                                        git_commit_sha,
                                        git_metadata,
                                        job.repo_path
                                    ),
                                    timeout=3.0
                                )
                                commit_duration = time.time() - commit_start
                                
                                if git_commit_sha:
                                    logger.info(f"✅ [COMMIT-2] Git commit ready: {git_commit_sha[:8]} ({commit_duration:.2f}s)")
                                else:
                                    logger.warning(f"⚠️  [COMMIT-2-NONE] Git commit creation returned None")
                                    
                            except asyncio.TimeoutError:
                                logger.error(f"⏱️  [COMMIT-2-TIMEOUT] Commit creation timed out after 3s")
                                git_commit_sha = None
                            except Exception as commit_error:
                                logger.error(f"❌ [COMMIT-2-ERROR] Failed to create git commit: {commit_error}")
                                git_commit_sha = None
                                logger.warning(f"⚠️  [COMMIT-3] Proceeding without git commit reference for {file_path}")
                    
                    # ✅ PHASE 2: Extract temporal metadata for database storage
                    git_date_value = None
                    git_author_value = None
                    git_author_email_value = None
                    git_commit_message_value = None
                    
                    if git_metadata:
                        # Try git metadata first
                        if git_metadata.get("last_commit_date"):
                            try:
                                git_date_value = datetime.fromisoformat(git_metadata["last_commit_date"])
                            except Exception as e:
                                logger.warning(f"Failed to parse git_date: {e}")
                        
                        git_author_value = git_metadata.get("last_commit_author")
                        git_author_email_value = git_metadata.get("last_commit_author_email")
                        git_commit_message_value = git_metadata.get("last_commit_message")
                        
                        # Fallback to file mtime if git date not available
                        if not git_date_value and git_metadata.get("file_mtime"):
                            try:
                                git_date_value = datetime.fromisoformat(git_metadata["file_mtime"])
                            except Exception as e:
                                logger.warning(f"Failed to parse file_mtime: {e}")
                    
                    document = DocumentModel(
                        service_name=job.mode,  # "snapshot" or "enriched"
                        file_path=file_path,
                        original_format=file_extension,
                        original_content=content[:10000] if len(content) <= 10000 else content[:10000] + "...",
                        normalized_content=normalized_content,
                        content_hash=content_hash,
                        ingestion_mode=job.mode,
                        version=1,
                        is_latest=True,
                        git_commit_sha=git_commit_sha,  # ✨ Last commit SHA
                        git_date=git_date_value,  # ✅ PHASE 2: Temporal metadata
                        git_author=git_author_value,  # ✅ PHASE 2
                        git_author_email=git_author_email_value,  # ✅ PHASE 2
                        git_commit_message=git_commit_message_value,  # ✅ PHASE 2
                        doc_metadata=doc_metadata
                    )
                    document = await doc_repo.create(document)
                    await session.commit()
                    should_generate_embedding = True
                    is_new_document = True
                
                # Generate embedding if needed
                embedding_generated = False
                embedding_error = None
                
                if should_generate_embedding and self.embedding_service:
                    try:
                        # Log embedding attempt
                        logger.debug(f"🔄 Attempting embedding generation for {file_path} ({len(normalized_content)} chars)")
                        
                        # Generate embedding vector with timing
                        import time
                        start_time = time.time()
                        embedding_result = await self.embedding_service.generate_embedding(normalized_content)
                        duration = time.time() - start_time
                        
                        logger.debug(f"✅ Embedding generated in {duration:.2f}s for {file_path}")
                        
                        # Extract and validate embedding vector
                        if isinstance(embedding_result, dict):
                            embedding_vector = embedding_result.get("embedding")
                            if not embedding_vector:
                                raise ValueError("Embedding result missing 'embedding' key")
                            model = embedding_result.get("model", "unknown")
                        else:
                            embedding_vector = embedding_result
                            model = "unknown"
                        
                        if not embedding_vector or len(embedding_vector) == 0:
                            raise ValueError(f"Empty embedding vector returned (type: {type(embedding_vector)})")
                        
                        logger.debug(f"📊 Embedding vector: {len(embedding_vector)} dimensions, model: {model}")
                        
                        # Store in ChromaDB
                        chroma = get_chroma_client()
                        
                        logger.debug(f"💾 Storing embedding in ChromaDB for {file_path}")
                        
                        # Build ChromaDB metadata
                        chroma_metadata = {
                            "id": str(document.id),
                            "file_path": file_path,
                            "service_name": job.mode,  # "snapshot" or "enriched"
                            "ingestion_mode": job.mode,
                            "content_hash": content_hash,
                            "job_id": str(job.id),
                            "embedding_duration_sec": duration,
                            "embedding_model": model,
                            "timestamp": time.time()
                        }
                        
                        # ✨ Add git metadata to ChromaDB for enriched mode
                        if git_metadata:
                            chroma_metadata.update({
                                "git_commit_sha": git_metadata.get("last_commit_sha", "")[:8],
                                "git_author": git_metadata.get("last_commit_author", ""),
                                "git_date": git_metadata.get("last_commit_date", "")
                            })
                        
                        await chroma.add_embeddings(
                            embeddings=[embedding_vector],
                            documents=[normalized_content],  # ✅ FIXED: Store full content
                            metadatas=[chroma_metadata],
                            ids=[str(document.id)]
                        )
                        
                        logger.debug(f"✅ Stored embedding in ChromaDB for {file_path}")
                        
                        # Create entry in embeddings table
                        from ...storage.db_models import EmbeddingModel
                        from uuid import uuid4
                        
                        embedding_record = EmbeddingModel(
                            id=uuid4(),
                            document_id=document.id,
                            chroma_id=str(document.id),
                            model=model,
                            dimensions=len(embedding_vector),
                            token_count=len(normalized_content.split()),
                            cost_usd=0.0,  # Local embeddings are free
                            extra_metadata={
                                "duration_sec": duration,
                                "backend": "fastembed" if "BAAI" in model else "ollama"
                            }
                        )
                        session.add(embedding_record)
                        await session.flush()  # Get the ID
                        
                        # Update document with embedding reference
                        document.embedding_id = embedding_record.id
                        await session.commit()
                        
                        embedding_generated = True
                        logger.info(
                            f"✅ EMBEDDING SUCCESS: {file_path} "
                            f"({duration:.2f}s, {len(embedding_vector)} dims, model: {model})"
                        )
                        
                    except Exception as e:
                        embedding_error = str(e)
                        error_type = type(e).__name__
                        
                        # Check if it's a circuit breaker error
                        if "CircuitBreaker" in error_type or "circuit" in str(e).lower():
                            logger.error(f"🔴 EMBEDDING BLOCKED (circuit breaker): {file_path}")
                            logger.error(f"   Reason: {embedding_error}")
                        else:
                            logger.error(f"❌ EMBEDDING FAILED: {file_path}")
                            logger.error(f"   Error type: {error_type}")
                            logger.error(f"   Error message: {embedding_error}")
                            logger.error(f"   Content length: {len(normalized_content)} chars")
                            logger.error(f"   Content preview: {normalized_content[:100]}...")
                        
                        # Track embedding errors for summary
                        if not hasattr(self, '_embedding_errors'):
                            self._embedding_errors = []
                        self._embedding_errors.append({
                            "file_path": file_path,
                            "error": embedding_error,
                            "error_type": error_type,
                            "timestamp": time.time()
                        })
                elif not self.embedding_service:
                    logger.warning(f"⚠️  No embedding service configured - skipping embedding for {file_path}")
            
            return {
                "success": True,
                "duplicate": False,
                "skipped": False,
                "embedding_generated": embedding_generated,
                "embedding_error": embedding_error,
                "is_new_document": is_new_document
            }
        
        except Exception as e:
            logger.error(f"❌ Error processing snapshot document {file_path}: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "embedding_generated": False,
                "embedding_error": str(e),
                "skipped": False
            }
    
    async def _get_commits_for_mode(self, mode: str) -> List[Any]:
        """
        Get commits based on ingestion mode, respecting max_commits_to_process limit.
        
        Args:
            mode: Ingestion mode (quick, full, incremental, recent, snapshot)
        
        Returns:
            List of GitCommit objects (empty list for snapshot mode)
        """
        if mode == "snapshot":
            # Snapshot mode: no git history, just current state
            logger.info("📸 Snapshot mode: skipping git history, will process current files only")
            return []  # Empty list signals to use current filesystem state
        elif mode == "enriched":
            # Enriched mode: current files + last commit metadata for each file
            # Returns empty list to trigger filesystem scan, but will fetch git metadata per file
            logger.info("✨ Enriched mode: processing current files with git metadata (last commit per file)")
            return []
        elif mode == "quick":
            # Last 10 commits (or max limit)
            limit = min(10, self.max_commits_to_process)
            return await self.git_service.get_recent_commits(limit=limit)
        elif mode == "recent":
            # Last 200 commits (or max limit)
            limit = min(200, self.max_commits_to_process)
            return await self.git_service.get_recent_commits(limit=limit)
        elif mode == "full":
            # All commits (limited by max_commits_to_process, default 100)
            logger.info(f"📚 Full mode: processing up to {self.max_commits_to_process} most recent commits")
            return await self.git_service.get_recent_commits(limit=self.max_commits_to_process)
        elif mode == "incremental":
            # TODO: Get commits since last ingestion
            # For now, same as quick but respects max limit
            limit = min(10, self.max_commits_to_process)
            return await self.git_service.get_recent_commits(limit=limit)
        else:
            logger.warning(f"Unknown mode '{mode}', defaulting to quick")
            limit = min(10, self.max_commits_to_process)
            return await self.git_service.get_recent_commits(limit=limit)
    
    async def _process_commit(self, commit: Any, job: IngestionJobModel) -> Dict[str, Any]:
        """
        Process a single commit.
        
        Args:
            commit: GitCommit object
            job: Parent ingestion job
        
        Returns:
            Dict with processing results
        """
        result = {
            "processed": 0,
            "failed": 0,
            "skipped": 0,  # NEW: Track skipped separately
            "embeddings": 0,
            "cost": 0.0
        }
        
        try:
            # 🚀 OPTIMIZATION 1: Check if commit already fully ingested
            commit_check = await self.commit_optimizer.check_commit_already_ingested(commit.sha)
            
            if commit_check["already_ingested"]:
                logger.info(
                    f"⏭️  Skipping commit {commit.sha[:8]}: Already ingested "
                    f"({commit_check['document_count']} documents on "
                    f"{commit_check['ingested_at'].strftime('%Y-%m-%d')})"
                )
                result["skipped"] = commit_check["document_count"]
                return result
            
            # Get target_subdirectory from job metadata if specified
            target_subdirectory = job.job_metadata.get('target_subdirectory') if job.job_metadata else None
            
            # Get files changed in this commit (filtered by subdirectory if specified)
            files = await self.git_service.get_commit_files(commit.sha, target_subdirectory)
            
            if not files:
                return result
            
            # Filter files (only documentation and code)
            filtered_files = self._filter_files(files)
            
            logger.info(
                f"Commit {commit.sha[:8]}: {len(filtered_files)}/{len(files)} files after filtering"
            )
            
            # 🚀 OPTIMIZATION 2: Batch pre-check files for duplicates
            # Read all files and compute hashes first, then batch-check database
            files_with_hashes = []
            files_failed_read = []
            
            for file_path in filtered_files:
                try:
                    file_path_str = file_path if isinstance(file_path, str) else file_path.path
                    content = await self.git_service.get_file_content_at_commit(
                        commit_sha=commit.sha,
                        file_path=file_path_str
                    )
                    
                    if content and len(content) <= 1_000_000:  # Skip empty and large files
                        # Compute content hash
                        from hashlib import sha256
                        content_hash = sha256(content.encode()).hexdigest()
                        
                        files_with_hashes.append({
                            'file_path': file_path_str,
                            'content': content,
                            'content_hash': content_hash,
                            'original': file_path
                        })
                    else:
                        files_failed_read.append((file_path_str, "Empty or too large"))
                except Exception as e:
                    files_failed_read.append((file_path_str if isinstance(file_path, str) else file_path.path, str(e)))
            
            # Batch check which hashes already exist
            if files_with_hashes:
                hashes_to_check = [f['content_hash'] for f in files_with_hashes]
                existing_hashes = await self.commit_optimizer.batch_check_content_hashes(hashes_to_check)
                
                # Separate into duplicates and new files
                files_to_process = []
                files_to_skip = []
                
                for file_dict in files_with_hashes:
                    if file_dict['content_hash'] in existing_hashes:
                        files_to_skip.append(file_dict)
                    else:
                        files_to_process.append(file_dict)
                
                logger.info(
                    f"📊 Batch check complete: {len(files_to_process)} new, "
                    f"{len(files_to_skip)} duplicates, {len(files_failed_read)} failed"
                )
            else:
                files_to_process = []
                files_to_skip = []
            
            # Update results for skipped files
            result["skipped"] += len(files_to_skip)
            result["failed"] += len(files_failed_read)
            
            # Use the optimized file list instead of filtered_files
            optimized_files = files_to_process
            
            # Check for checkpoint and resume if applicable
            checkpoint = None
            start_index = 0
            if await self.checkpoint_manager.should_resume(job.id):
                checkpoint = await self.checkpoint_manager.load_checkpoint(job.id)
                if checkpoint and checkpoint.commit_sha == commit.sha:
                    start_index = checkpoint.current_file_index
                    result["processed"] = checkpoint.processed_count
                    result["skipped"] = checkpoint.skipped_count
                    result["failed"] = checkpoint.failed_count
                    result["embeddings"] = checkpoint.embeddings_count
                    
                    await self.checkpoint_manager.mark_resumed(job.id)
                    
                    resume_info = self.checkpoint_manager.get_resume_info(checkpoint)
                    logger.info(
                        f"📂 Resuming job {job.id} from checkpoint: "
                        f"file {start_index}/{len(optimized_files)} "
                        f"({resume_info['progress_percent']}% complete)"
                    )
            
            logger.info(
                f"Commit {commit.sha[:8]}: {len(optimized_files)} files to process (after optimization)"
                + (f" (resuming from file {start_index})" if start_index > 0 else "")
            )
            
            # Process each file (starting from checkpoint if resuming)
            # Note: optimized_files contains dicts with content already loaded
            for idx, file_dict in enumerate(optimized_files):
                # Skip files that were already processed (checkpoint resume)
                if idx < start_index:
                    continue
                # Check if job still exists in database every 10 files (graceful shutdown)
                if idx > 0 and idx % 10 == 0:
                    try:
                        # Refresh job from database to check if it was cancelled
                        db = self.db_service
                        async with db.session() as session:
                            from ...storage.repositories.ingestion_job_repository import IngestionJobRepository
                            job_repo = IngestionJobRepository(session)
                            current_job = await job_repo.get_by_id(job.id)
                            
                            if not current_job:
                                logger.warning(f"Job {job.id} no longer exists in database, stopping processing")
                                result["skipped"] += len(filtered_files) - idx
                                break
                            
                            if current_job.status == "failed":
                                logger.warning(f"Job {job.id} was marked as failed, stopping processing")
                                result["skipped"] += len(filtered_files) - idx
                                break
                    except Exception as e:
                        logger.debug(f"Could not check job status: {e}")
                
                # Check job timeout every 100 files (prevent indefinite runs)
                if idx > 0 and idx % 100 == 0:
                    if await self._check_job_timeout(job):
                        logger.error(f"Job {job.id} exceeded timeout, stopping processing")
                        result["error"] = "Job timeout exceeded"
                        result["skipped"] += len(filtered_files) - idx
                        break
                
                # Update worker heartbeat every 30 files (detect stuck workers)
                if idx > 0 and idx % 30 == 0:
                    await self._update_worker_heartbeat(job)
                
                # Save checkpoint every N files (enable job recovery)
                if self.checkpoint_manager.should_save_checkpoint(idx + 1):
                    # Collect processed file paths for checkpoint
                    processed_files = [f['file_path'] for f in optimized_files[:idx + 1]]
                    
                    await self.checkpoint_manager.save_checkpoint(
                        job_id=job.id,
                        commit_sha=commit.sha,
                        processed_files=processed_files,
                        current_file_index=idx + 1,
                        total_files=len(optimized_files),
                        processed_count=result["processed"],
                        skipped_count=result["skipped"],
                        failed_count=result["failed"],
                        embeddings_count=result["embeddings"]
                    )
                
                # Get file path for logging
                file_path_str = file_dict['file_path']
                
                # Log every file being processed (INFO level so it appears in logs)
                logger.info(f"📄 Processing [{idx+1}/{len(optimized_files)}]: {file_path_str}")
                
                # Pass the pre-loaded content to avoid re-reading
                file_result = await self._process_file_optimized(
                    file_dict=file_dict,
                    commit=commit,
                    job=job
                )
                
                if file_result["success"]:
                    result["processed"] += 1
                    if not file_result.get("embedding_failed"):
                        result["embeddings"] += 1
                    result["cost"] += file_result["cost"]
                    logger.info(f"✅ Processed: {file_path_str}")
                elif file_result.get("skipped"):
                    # Duplicate, not an error
                    result["skipped"] += 1
                    if file_result.get("enriched"):
                        logger.info(f"⏭️  Skipped (enriched): {file_path_str}")
                    else:
                        logger.info(f"⏭️  Skipped (duplicate): {file_path_str}")
                else:
                    # Actual error
                    result["failed"] += 1
                    logger.warning(f"❌ Failed to process {file_path_str}: {file_result.get('error')}")
                
                # Update job metadata with progress (every 5 files or last file for more frequent updates)
                if (idx + 1) % 5 == 0 or idx == len(optimized_files) - 1:
                    await self._update_job_progress(
                        job=job,
                        last_file=file_path_str,
                        current_commit=commit.sha[:8],
                        processed=result["processed"],
                        skipped=result["skipped"],
                        failed=result["failed"],
                        current_file_index=idx + 1,
                        total_files=len(optimized_files)
                    )
        
        except Exception as e:
            logger.error(f"Error processing commit {commit.sha}: {e}", exc_info=True)
        
        return result
    
    async def _extract_commit_metadata(self, commit: Any) -> Dict[str, Any]:
        """
        Extract basic commit metadata as a fallback when full processing fails.
        
        This allows us to capture valuable information even when git parsing 
        or file processing fails. Acts as graceful degradation.
        
        Args:
            commit: GitCommit object
        
        Returns:
            Dict with commit metadata, or minimal info if extraction fails
        """
        try:
            # Try to extract basic commit info (usually safe even with git issues)
            metadata = {
                "sha": commit.sha[:8] if hasattr(commit, 'sha') else "unknown",
                "message": commit.message[:100] if hasattr(commit, 'message') else "N/A",
                "author": str(commit.author) if hasattr(commit, 'author') else "unknown",
                "date": commit.date.isoformat() if hasattr(commit, 'date') else None,
                "extracted_at": datetime.utcnow().isoformat(),
                "extraction_reason": "fallback"
            }
            
            # Try to get file list (may fail with git corruption)
            try:
                if hasattr(commit, 'stats') and hasattr(commit.stats, 'files'):
                    metadata["files_changed"] = list(commit.stats.files.keys())
                    metadata["files_count"] = len(commit.stats.files)
            except Exception:
                metadata["files_changed"] = []
                metadata["files_count"] = 0
            
            logger.info(f"📋 Extracted metadata for commit {metadata['sha']}: {metadata['files_count']} files")
            return metadata
            
        except Exception as e:
            # Even metadata extraction failed - return absolute minimum
            logger.warning(f"⚠️  Metadata extraction failed: {e}")
            return {
                "sha": "unknown",
                "message": "Metadata extraction failed",
                "extracted_at": datetime.utcnow().isoformat(),
                "extraction_error": str(e)
            }
    
    async def _process_commit_parallel(
        self,
        commit: Any,
        job: IngestionJobModel,
        commit_num: int,
        total_commits: int
    ) -> Dict[str, Any]:
        """
        PHASE 2: Process a single commit with enhanced timeout protection and graceful fallbacks.
        
        Features:
        - Blacklist checking (skip known problematic commits)
        - Concurrency control via semaphore
        - Aggressive timeout protection (prevents silent hangs)
        - Metadata extraction fallback (captures data even on failure)
        - Comprehensive error classification
        - Progress heartbeat logging
        
        Args:
            commit: GitCommit object
            job: Parent ingestion job
            commit_num: Current commit number (for logging)
            total_commits: Total number of commits (for logging)
        
        Returns:
            Dict with processing results (always returns, never hangs)
        """
        commit_sha = commit.sha[:8] if hasattr(commit, 'sha') else "unknown"
        commit_sha_full = commit.sha if hasattr(commit, 'sha') else "unknown"
        
        # CHECK BLACKLIST FIRST - Skip known problematic commits
        from .commit_blacklist import is_blacklisted, get_blacklist_reason
        
        if is_blacklisted(commit_sha_full):
            reason = get_blacklist_reason(commit_sha_full)
            logger.warning(
                f"🚫 BLACKLISTED: Skipping commit {commit_num}/{total_commits}: {commit_sha} - {reason[:100]}"
            )
            
            # Extract metadata even for blacklisted commits (for audit trail)
            metadata = await self._extract_commit_metadata(commit)
            
            return {
                "processed": 0,
                "failed": 0,
                "skipped": 1,  # Count as skipped, not failed
                "embeddings": 0,
                "cost": 0.0,
                "blacklisted": True,
                "blacklist_reason": reason,
                "metadata_extracted": True,
                "metadata": metadata
            }
        
        async with self.commit_semaphore:
            logger.info(f"🔄 Starting commit {commit_num}/{total_commits}: {commit_sha}")
            
            # Track start time for hang detection
            start_time = datetime.utcnow()
            
            try:
                # Prepare processing task with batch optimization
                if self.use_batch_optimization:
                    process_task = self._process_commit_with_batch_optimization(
                        commit, job, batch_size=20
                    )
                else:
                    process_task = self._process_commit(commit, job)
                
                # Apply AGGRESSIVE timeout (reduced from default to catch hangs faster)
                # Use 50% of configured timeout for faster hang detection
                aggressive_timeout = max(30, self.commit_timeout_seconds // 2)
                
                logger.debug(f"⏱️  Commit {commit_sha}: timeout set to {aggressive_timeout}s")
                
                result = await asyncio.wait_for(
                    process_task,
                    timeout=aggressive_timeout
                )
                
                # Success!
                elapsed = (datetime.utcnow() - start_time).total_seconds()
                logger.info(
                    f"✅ Completed commit {commit_num}/{total_commits}: {commit_sha} "
                    f"({result['processed']} processed, {result['skipped']} skipped, "
                    f"{result['failed']} failed) in {elapsed:.1f}s"
                )
                return result
                
            except asyncio.TimeoutError:
                elapsed = (datetime.utcnow() - start_time).total_seconds()
                logger.error(
                    f"⏱️  TIMEOUT: Commit {commit_num}/{total_commits}: {commit_sha} "
                    f"exceeded {aggressive_timeout}s timeout (elapsed: {elapsed:.1f}s)"
                )
                
                # GRACEFUL FALLBACK: Try to extract metadata before giving up
                metadata = await self._extract_commit_metadata(commit)
                
                logger.warning(
                    f"🔄 Fallback: Extracted metadata for timed-out commit {commit_sha}: "
                    f"{metadata.get('files_count', 0)} files"
                )
                
                return {
                    "processed": 0,
                    "failed": 1,
                    "skipped": 0,
                    "embeddings": 0,
                    "cost": 0.0,
                    "error": f"Timeout after {aggressive_timeout}s",
                    "metadata_extracted": True,
                    "metadata": metadata,
                    "partial_success": True  # We got metadata at least
                }
                
            except GitCorruptionError as e:
                logger.error(
                    f"🔴 GIT CORRUPTION in commit {commit_num}/{total_commits}: {commit_sha} - {e}"
                )
                
                # GRACEFUL FALLBACK: Try to extract metadata
                metadata = await self._extract_commit_metadata(commit)
                
                return {
                    "processed": 0,
                    "failed": 1,
                    "skipped": 0,
                    "embeddings": 0,
                    "cost": 0.0,
                    "error": f"Git corruption: {str(e)}",
                    "metadata_extracted": True,
                    "metadata": metadata,
                    "partial_success": True
                }
                
            except Exception as e:
                # Classify the error for better diagnostics
                error_classification = self.git_error_handler.classify_error(
                    e,
                    {
                        "commit_sha": commit_sha,
                        "operation": "process_commit",
                        "commit_num": commit_num,
                        "total_commits": total_commits
                    }
                )
                
                logger.error(
                    f"❌ Failed commit {commit_num}/{total_commits}: {commit_sha} - "
                    f"{error_classification['category']}: {e}"
                )
                
                # GRACEFUL FALLBACK: Try to extract metadata
                metadata = await self._extract_commit_metadata(commit)
                
                # Log what we were able to salvage
                if metadata.get('files_count', 0) > 0:
                    logger.info(
                        f"🔄 Salvaged metadata for failed commit {commit_sha}: "
                        f"{metadata['files_count']} files identified"
                    )
                
                return {
                    "processed": 0,
                    "failed": 1,
                    "skipped": 0,
                    "embeddings": 0,
                    "cost": 0.0,
                    "error": str(e),
                    "error_category": error_classification['category'],
                    "metadata_extracted": True,
                    "metadata": metadata,
                    "partial_success": metadata.get('files_count', 0) > 0
                }
    
    async def _process_commit_with_batch_optimization(
        self, 
        commit: Any, 
        job: IngestionJobModel,
        batch_size: int = 10
    ) -> Dict[str, Any]:
        """
        Process commit with PHASE 1 OPTIMIZATIONS:
        - Batch embedding generation
        - Connection pooling (reuse session)
        - Smart caching (normalizers)
        
        Args:
            commit: GitCommit object
            job: Parent ingestion job
            batch_size: Number of files to process per batch
        
        Returns:
            Dict with processing results
        """
        result = {
            "processed": 0,
            "failed": 0,
            "skipped": 0,
            "embeddings": 0,
            "cost": 0.0
        }
        
        try:
            # OPTIMIZATION 1: Check if commit already fully ingested
            commit_check = await self.commit_optimizer.check_commit_already_ingested(commit.sha)
            
            if commit_check["already_ingested"]:
                logger.info(
                    f"⏭️  Skipping commit {commit.sha[:8]}: Already ingested "
                    f"({commit_check['document_count']} documents on "
                    f"{commit_check['ingested_at'].strftime('%Y-%m-%d')})"
                )
                result["skipped"] = commit_check["document_count"]
                return result
            
            # Get and filter files with error handling
            target_subdirectory = job.job_metadata.get('target_subdirectory') if job.job_metadata else None
            
            try:
                files = await self.git_service.get_commit_files(commit.sha, target_subdirectory)
            except Exception as e:
                # Classify git error
                error_classification = self.git_error_handler.classify_error(
                    e,
                    {
                        "commit_sha": commit.sha,
                        "operation": "get_commit_files",
                        "subdirectory": target_subdirectory
                    }
                )
                
                if self.git_error_handler.should_skip_commit(error_classification):
                    logger.warning(
                        f"⏭️  Skipping corrupt commit {commit.sha[:8]}: {error_classification['error_message']}"
                    )
                    result["failed"] = 1
                    result["error"] = error_classification['error_message']
                    return result
                else:
                    raise
            
            if not files:
                return result
            
            filtered_files = self._filter_files(files)
            
            logger.info(
                f"Commit {commit.sha[:8]}: {len(filtered_files)}/{len(files)} files after filtering"
            )
            
            # PHASE 3: Pre-filter files by extension and size BEFORE reading
            logger.info(f"🔍 Phase 3: Pre-filtering {len(filtered_files)} files by extension and size...")
            
            # Step 1: Filter out binary files by extension (no I/O needed)
            text_files = []
            for file_path in filtered_files:
                file_path_str = file_path if isinstance(file_path, str) else file_path.path
                if self.is_binary_file_extension(file_path_str):
                    logger.debug(f"⏭️  Skipping binary extension: {file_path_str}")
                    result["skipped"] += 1
                else:
                    text_files.append(file_path)
            
            # Step 2: Check file sizes in parallel (uses Git metadata, very fast)
            if text_files:
                size_check_tasks = [
                    self.git_service.get_file_size_at_commit(
                        commit.sha,
                        fp if isinstance(fp, str) else fp.path
                    )
                    for fp in text_files
                ]
                file_sizes = await asyncio.gather(*size_check_tasks)
                
                # Step 3: Filter by size
                files_to_read = []
                for file_path, size in zip(text_files, file_sizes):
                    file_path_str = file_path if isinstance(file_path, str) else file_path.path
                    
                    if size is None:
                        # Can't determine size, include it
                        files_to_read.append(file_path)
                    elif size == 0:
                        logger.debug(f"⏭️  Skipping empty file: {file_path_str}")
                        result["skipped"] += 1
                    elif size > 1_000_000:  # 1MB limit
                        logger.debug(f"⏭️  Skipping large file ({size/1024:.1f}KB): {file_path_str}")
                        result["skipped"] += 1
                    else:
                        files_to_read.append(file_path)
                
                logger.info(
                    f"📊 Phase 3 filter: {len(files_to_read)}/{len(filtered_files)} files to read "
                    f"(skipped {len(filtered_files) - len(files_to_read)} binary/empty/large)"
                )
            else:
                files_to_read = []
            
            if not files_to_read:
                logger.info(f"✅ Commit {commit.sha[:8]}: All files filtered out")
                return result
            
            # OPTIMIZATION 2: Batch pre-check files for duplicates
            # Phase 1.5: Read all files IN PARALLEL for 4× faster I/O
            files_with_hashes = []
            files_failed_read = []
            
            async def read_file_with_hash(file_path):
                """Read a single file and compute its hash."""
                try:
                    file_path_str = file_path if isinstance(file_path, str) else file_path.path
                    content = await self.git_service.get_file_content_at_commit(
                        commit_sha=commit.sha,
                        file_path=file_path_str
                    )
                    
                    if content and len(content) <= 1_000_000:
                        from hashlib import sha256
                        content_hash = sha256(content.encode()).hexdigest()
                        
                        return {
                            'file_path': file_path_str,
                            'content': content,
                            'content_hash': content_hash,
                            'original': file_path,
                            'success': True
                        }
                    else:
                        return {
                            'file_path': file_path_str,
                            'error': "Empty or too large",
                            'success': False
                        }
                except Exception as e:
                    return {
                        'file_path': file_path if isinstance(file_path, str) else file_path.path,
                        'error': str(e),
                        'success': False
                    }
            
            # 🚀 Read all files in parallel using asyncio.gather
            logger.info(f"📖 Reading {len(files_to_read)} files in parallel...")
            import asyncio
            read_tasks = [read_file_with_hash(f) for f in files_to_read]
            read_results = await asyncio.gather(*read_tasks, return_exceptions=True)
            
            # Process results
            for result in read_results:
                if isinstance(result, Exception):
                    files_failed_read.append(("unknown", str(result)))
                elif result.get('success'):
                    files_with_hashes.append(result)
                else:
                    files_failed_read.append((result.get('file_path', 'unknown'), result.get('error', 'Unknown error')))
            
            # Batch check which hashes already exist
            if files_with_hashes:
                hashes_to_check = [f['content_hash'] for f in files_with_hashes]
                existing_hashes = await self.commit_optimizer.batch_check_content_hashes(hashes_to_check)
                
                files_to_process = [f for f in files_with_hashes if f['content_hash'] not in existing_hashes]
                files_to_skip = [f for f in files_with_hashes if f['content_hash'] in existing_hashes]
                
                logger.info(
                    f"📊 Batch check complete: {len(files_to_process)} new, "
                    f"{len(files_to_skip)} duplicates, {len(files_failed_read)} failed"
                )
            else:
                files_to_process = []
                files_to_skip = []
            
            result["skipped"] += len(files_to_skip)
            result["failed"] += len(files_failed_read)
            
            if not files_to_process:
                logger.info(f"✅ Commit {commit.sha[:8]}: No new files to process")
                return result
            
            # PHASE 3: Calculate optimal batch size dynamically based on file sizes
            optimal_batch_size = self.calculate_optimal_batch_size(files_to_process)
            
            # 🚀 Process in batches with DYNAMIC SIZING + BATCH EMBEDDINGS
            logger.info(f"🚀 Processing {len(files_to_process)} files with dynamic batching")
            
            for batch_idx in range(0, len(files_to_process), optimal_batch_size):
                batch_files = files_to_process[batch_idx:batch_idx + optimal_batch_size]
                
                # Phase 1.5: Log every 10 batches instead of every batch (reduce I/O overhead)
                batch_num = batch_idx//optimal_batch_size + 1
                total_batches = (len(files_to_process)-1)//optimal_batch_size + 1
                if batch_num % 10 == 0 or batch_num == 1 or batch_num == total_batches:
                    logger.info(
                        f"📦 Batch {batch_num}/{total_batches}: "
                        f"{len(batch_files)} files"
                    )
                
                # Process batch with optimizations
                batch_result = await self._process_batch_optimized(
                    batch_files=batch_files,
                    commit=commit,
                    job=job
                )
                
                # Aggregate results
                result["processed"] += batch_result["processed"]
                result["failed"] += batch_result["failed"]
                result["embeddings"] += batch_result["embeddings"]
                result["cost"] += batch_result["cost"]
                
                # Update progress
                await self._update_job_progress(
                    job=job,
                    last_file=batch_files[-1]['file_path'],
                    current_commit=commit.sha[:8],
                    processed=result["processed"],
                    skipped=result["skipped"],
                    failed=result["failed"],
                    current_file_index=batch_idx + len(batch_files),
                    total_files=len(files_to_process)
                )
        
        except Exception as e:
            logger.error(f"Error processing commit {commit.sha}: {e}", exc_info=True)
        
        return result
    
    async def _process_batch_optimized(
        self,
        batch_files: List[Dict[str, Any]],
        commit: Any,
        job: IngestionJobModel
    ) -> Dict[str, Any]:
        """
        Process a batch of files with PHASE 1 optimizations.
        
        Features:
        - Batch embedding generation (8× faster)
        - Connection pooling (10× fewer connections)
        - Cached normalizers (reuse instances)
        
        Args:
            batch_files: List of file dicts with pre-loaded content
            commit: GitCommit object
            job: Parent ingestion job
        
        Returns:
            Dict with batch processing results
        """
        result = {
            "processed": 0,
            "failed": 0,
            "embeddings": 0,
            "cost": 0.0
        }
        
        try:
            # OPTIMIZATION 3: Cache normalizers (reuse instead of creating per file)
            normalizer_cache = {}
            
            def get_cached_normalizer(file_extension):
                if file_extension not in normalizer_cache:
                    normalizer_cache[file_extension] = self.normalizer_factory.get_normalizer(file_extension)
                return normalizer_cache[file_extension]
            
            # PHASE 2: Normalize all documents in PARALLEL
            logger.info(f"📝 Normalizing {len(batch_files)} files in parallel...")
            
            async def normalize_file(file_dict):
                """Normalize a single file (for parallel execution)."""
                try:
                    path = Path(file_dict['file_path'])
                    normalizer = get_cached_normalizer(path.suffix)
                    
                    normalized = await normalizer.normalize(
                        content=file_dict['content'],
                        file_path=str(path),
                        metadata={
                            "commit_sha": commit.sha,
                            "commit_message": commit.message,
                            "commit_author": commit.author,
                            "commit_date": commit.date.isoformat(),
                            "change_type": "modified"
                        }
                    )
                    
                    return {
                        'file_dict': file_dict,
                        'path': path,
                        'normalized': normalized,
                        'success': True
                    }
                except Exception as e:
                    logger.error(f"Failed to normalize {file_dict['file_path']}: {e}")
                    return {
                        'file_dict': file_dict,
                        'error': str(e),
                        'success': False
                    }
            
            # 🚀 Normalize all files in parallel using asyncio.gather
            import asyncio
            normalize_tasks = [normalize_file(f) for f in batch_files]
            normalization_results = await asyncio.gather(*normalize_tasks)
            
            # Separate successful and failed normalizations
            normalized_docs = [r for r in normalization_results if r.get('success')]
            result["failed"] = len([r for r in normalization_results if not r.get('success')])
            
            if not normalized_docs:
                return result
            
            # 🚀 OPTIMIZATION: Batch embedding generation (8× faster!)
            logger.info(f"🔮 Generating {len(normalized_docs)} embeddings in BATCH...")
            
            texts = [doc['normalized']['content'] for doc in normalized_docs]
            embedding_results = await self.embedding_service.generate_batch(
                texts=texts,
                batch_size=len(texts)  # Process all at once
            )
            
            # OPTIMIZATION: Reuse single database session for entire batch (10× fewer connections)
            async with get_database().session() as session:
                doc_repo = DocumentRepository(session)
                
                from ...storage.db_models import DocumentModel, GitCommitModel
                from sqlalchemy import select
                from uuid import uuid4
                
                # Check/create commit once per batch
                commit_query = select(GitCommitModel).where(GitCommitModel.sha == commit.sha)
                commit_result = await session.execute(commit_query)
                existing_commit = commit_result.scalar_one_or_none()
                
                if not existing_commit:
                    author_parts = commit.author.split("<")
                    author_name = author_parts[0].strip() if author_parts else commit.author
                    author_email = author_parts[1].rstrip(">") if len(author_parts) > 1 else "unknown@unknown.com"
                    
                    git_commit = GitCommitModel(
                        sha=commit.sha,
                        message=commit.message,
                        author=author_name,
                        author_email=author_email,
                        date=commit.date,
                        commit_metadata={"repo_path": str(self.git_service.repo_path)}
                    )
                    session.add(git_commit)
                    await session.flush()
                
                # Process all documents in batch
                documents_to_create = []
                embeddings_to_store = []
                
                for doc_data, embedding_result in zip(normalized_docs, embedding_results):
                    try:
                        file_dict = doc_data['file_dict']
                        path = doc_data['path']
                        normalized = doc_data['normalized']
                        
                        # Create document
                        document = DocumentModel(
                            id=uuid4(),
                            service_name=normalized["metadata"].get("service", "ecosystem-mcp"),
                            file_path=str(path),
                            original_format=path.suffix[1:],
                            original_content=file_dict['content'],
                            normalized_content=normalized["content"],
                            content_hash=file_dict['content_hash'],
                            created_at=datetime.utcnow(),
                            updated_at=datetime.utcnow(),
                            git_commit_sha=commit.sha,
                            is_latest=True,
                            doc_metadata=normalized["metadata"]
                        )
                        
                        documents_to_create.append(document)
                        
                        # Store embedding info for later
                        if embedding_result and not embedding_result.get("error"):
                            embeddings_to_store.append({
                                'document': document,
                                'embedding': embedding_result,
                                'path': path
                            })
                            result["cost"] += embedding_result.get("cost", 0.0)
                        
                        # Mark previous versions as not latest
                        await doc_repo.mark_as_outdated(str(path))
                    
                    except Exception as e:
                        logger.error(f"Failed to prepare document: {e}")
                        result["failed"] += 1
                
                # 🚀 OPTIMIZATION: Bulk insert all documents at once
                if documents_to_create:
                    session.add_all(documents_to_create)
                    await session.commit()
                    
                    result["processed"] = len(documents_to_create)
                    logger.info(f"✅ Bulk inserted {len(documents_to_create)} documents")
                
                # Store all embeddings in ChromaDB
                if embeddings_to_store:
                    chroma = get_chroma_client()
                    
                    try:
                        success = await chroma.add_embeddings_with_retry(
                            ids=[str(e['document'].id) for e in embeddings_to_store],
                            embeddings=[e['embedding']['embedding'] for e in embeddings_to_store],
                            documents=[e['document'].normalized_content for e in embeddings_to_store],  # ✅ FIXED: Full content
                            metadatas=[{
                                "file_path": str(e['path']),
                                "service": e['document'].service_name,
                                "commit_sha": commit.sha[:8],
                                "created_at": e['document'].created_at.isoformat()
                            } for e in embeddings_to_store]
                        )
                        
                        if success:
                            result["embeddings"] = len(embeddings_to_store)
                            logger.info(f"✅ Stored {len(embeddings_to_store)} embeddings in ChromaDB")
                        else:
                            logger.warning(f"⚠️  Failed to store some embeddings in ChromaDB")
                    
                    except Exception as e:
                        logger.error(f"Failed to store embeddings batch: {e}")
        
        except Exception as e:
            logger.error(f"Error in batch processing: {e}", exc_info=True)
            result["failed"] += len(batch_files)
        
        return result
    
    def _filter_files(self, files: List[Any]) -> List[Any]:
        """
        Filter files to only include relevant documentation and code.
        
        Args:
            files: List of FileChange objects
        
        Returns:
            Filtered list of FileChange objects
        """
        # Extensions to include
        include_extensions = {
            '.md', '.py', '.yaml', '.yml', '.json', '.txt',
            '.rst', '.toml', '.ini', '.cfg', '.conf'
        }
        
        # Paths to exclude
        exclude_patterns = [
            'node_modules/', '.git/', '__pycache__/', '.venv/',
            'venv/', '.pytest_cache/', '.mypy_cache/', 'htmlcov/',
            '.tox/', 'dist/', 'build/', '*.egg-info/', '.idea/',
            '.vscode/', '.DS_Store'
        ]
        
        filtered = []
        
        for file_path in files:
            # ✅ FIXED: files are strings, not objects
            path = Path(file_path) if isinstance(file_path, str) else Path(file_path.path)
            
            # Check extension
            if path.suffix not in include_extensions:
                continue
            
            # Check excluded patterns
            if any(pattern in str(path) for pattern in exclude_patterns):
                continue
            
            filtered.append(file_path)
        
        return filtered
    
    async def _enrich_duplicate_metadata(
        self,
        existing_doc: Any,
        new_metadata: Dict[str, Any],
        session: Any
    ) -> bool:
        """
        Enrich existing document with missing metadata from duplicate.
        
        Args:
            existing_doc: Existing document model
            new_metadata: New metadata from duplicate document
            session: Database session
        
        Returns:
            True if any metadata was added, False otherwise
        """
        enriched = False
        current_metadata = existing_doc.doc_metadata or {}
        
        # Fields to potentially enrich (only add if missing)
        enrichable_fields = [
            'author', 'last_modified', 'description',
            'word_count', 'has_code', 'has_diagrams', 'language',
            'commit_sha', 'commit_message', 'commit_author', 'commit_date'
        ]
        
        for field in enrichable_fields:
            # If field is missing or empty in existing doc
            if field not in current_metadata or not current_metadata[field]:
                # And new metadata has it
                if field in new_metadata and new_metadata[field]:
                    current_metadata[field] = new_metadata[field]
                    enriched = True
                    logger.debug(f"  ✨ Added {field}: {new_metadata[field]}")
        
        # Special handling for tags (merge, don't replace)
        if 'tags' in new_metadata and new_metadata['tags']:
            existing_tags = set(current_metadata.get('tags', []))
            new_tags = set(new_metadata['tags'])
            merged_tags = existing_tags | new_tags
            
            if len(merged_tags) > len(existing_tags):
                current_metadata['tags'] = list(merged_tags)
                enriched = True
                added_tags = merged_tags - existing_tags
                logger.debug(f"  ✨ Merged tags: {', '.join(added_tags)}")
        
        # Update if enriched
        if enriched:
            existing_doc.doc_metadata = current_metadata
            existing_doc.updated_at = datetime.utcnow()
            await session.commit()
            logger.info(f"✨ Enriched metadata for document: {existing_doc.file_path}")
        
        return enriched
    
    async def _process_file_optimized(
        self,
        file_dict: Dict[str, Any],
        commit: Any,
        job: IngestionJobModel
    ) -> Dict[str, Any]:
        """
        Process a single file from a commit (optimized version with pre-loaded content).
        
        Args:
            file_dict: Dict with 'file_path', 'content', 'content_hash' keys
            commit: GitCommit object
            job: Parent ingestion job
        
        Returns:
            Dict with processing results
        """
        result = {
            "success": False,
            "cost": 0.0,
            "error": None
        }
        
        try:
            file_path_str = file_dict['file_path']
            content = file_dict['content']
            content_hash = file_dict['content_hash']
            
            # Content is already loaded and hash computed
            # Skip duplicate check - already done in batch
            
            # Normalize document
            path = Path(file_path_str)
            normalizer = self.normalizer_factory.get_normalizer(path.suffix)
            
            normalized = await normalizer.normalize(
                content=content,
                file_path=str(path),
                metadata={
                    "commit_sha": commit.sha,
                    "commit_message": commit.message,
                    "commit_author": commit.author,
                    "commit_date": commit.date.isoformat(),
                    "change_type": "modified"
                }
            )
            
            # Generate embedding
            embedding_result = await self.embedding_service.generate_embedding(
                text=normalized["content"]
            )
            
            # Store document and embedding
            async with get_database().session() as session:
                doc_repo = DocumentRepository(session)
                
                from ...storage.db_models import DocumentModel, GitCommitModel
                from sqlalchemy import select
                from uuid import uuid4
                
                # Check if commit exists, if not create it
                commit_query = select(GitCommitModel).where(GitCommitModel.sha == commit.sha)
                commit_result = await session.execute(commit_query)
                existing_commit = commit_result.scalar_one_or_none()
                
                if not existing_commit:
                    author_parts = commit.author.split("<")
                    author_name = author_parts[0].strip() if author_parts else commit.author
                    author_email = author_parts[1].rstrip(">") if len(author_parts) > 1 else "unknown@unknown.com"
                    
                    git_commit = GitCommitModel(
                        sha=commit.sha,
                        message=commit.message,
                        author=author_name,
                        author_email=author_email,
                        date=commit.date,
                        commit_metadata={"repo_path": str(self.git_service.repo_path)}
                    )
                    session.add(git_commit)
                    await session.flush()
                
                # Create document (we know it's not a duplicate from batch check)
                document = DocumentModel(
                    id=uuid4(),
                    service_name=normalized["metadata"].get("service", "ecosystem-mcp"),
                    file_path=str(path),
                    original_format=path.suffix[1:],
                    original_content=content,
                    normalized_content=normalized["content"],
                    content_hash=content_hash,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                    git_commit_sha=commit.sha,
                    is_latest=True,
                    doc_metadata=normalized["metadata"]
                )
                
                # Mark previous versions as not latest
                await doc_repo.mark_as_outdated(str(path))
                
                # Save document
                created_doc = await doc_repo.create(document)
                await session.commit()
                
                # Store embedding in ChromaDB with retry
                chroma = get_chroma_client()
                embedding_success = await chroma.add_embeddings_with_retry(
                    ids=[str(created_doc.id)],
                    embeddings=[embedding_result["embedding"]],
                    documents=[normalized["content"]],  # ✅ FIXED: Store full content (no truncation)
                    metadatas=[{
                        "file_path": str(path),
                        "service": normalized["metadata"].get("service", "ecosystem-mcp"),
                        "commit_sha": commit.sha[:8],
                        "created_at": created_doc.created_at.isoformat()
                    }]
                )
                
                if not embedding_success:
                    logger.warning(f"Failed to store embedding for {path}")
                    result["embedding_failed"] = True
                
                result["success"] = True
                result["cost"] = embedding_result.get("cost", 0.0)
        
        except Exception as e:
            logger.error(f"Error processing file: {e}", exc_info=True)
            result["error"] = str(e)
        
        return result
    
    async def _process_file(
        self,
        file_change: Any,
        commit: Any,
        job: IngestionJobModel
    ) -> Dict[str, Any]:
        """
        Process a single file from a commit.
        
        Args:
            file_change: FileChange object
            commit: GitCommit object
            job: Parent ingestion job
        
        Returns:
            Dict with processing results
        """
        result = {
            "success": False,
            "cost": 0.0,
            "error": None
        }
        
        try:
            # ✅ FIXED: file_change is a string, not an object
            file_path_str = file_change if isinstance(file_change, str) else file_change.path
            
            # Get file content
            # ✅ FIXED: Method is get_file_content_at_commit
            content = await self.git_service.get_file_content_at_commit(
                commit_sha=commit.sha,
                file_path=file_path_str
            )
            
            if not content:
                result["error"] = "Empty file"
                return result
            
            # Skip large files (> 1MB)
            if len(content) > 1_000_000:
                result["error"] = "File too large"
                return result
            
            # Normalize document
            path = Path(file_path_str)
            normalizer = self.normalizer_factory.get_normalizer(path.suffix)
            
            normalized = await normalizer.normalize(
                content=content,
                file_path=str(path),
                metadata={
                    "commit_sha": commit.sha,
                    "commit_message": commit.message,
                    "commit_author": commit.author,
                    "commit_date": commit.date.isoformat(),
                    "change_type": "modified"  # ✅ Default since we don't track change type
                }
            )
            
            # Generate embedding
            embedding_result = await self.embedding_service.generate_embedding(
                text=normalized["content"]
            )
            
            # Store document and embedding
            async with get_database().session() as session:
                doc_repo = DocumentRepository(session)
                
                # ✅ CRITICAL FIX: Ensure commit exists in git_commits table first
                from ...storage.db_models import DocumentModel, GitCommitModel
                from sqlalchemy import select
                from hashlib import sha256
                from uuid import uuid4
                
                # Check if commit exists, if not create it
                commit_query = select(GitCommitModel).where(GitCommitModel.sha == commit.sha)
                commit_result = await session.execute(commit_query)
                existing_commit = commit_result.scalar_one_or_none()
                
                if not existing_commit:
                    # ✅ Parse author and email from author string
                    # Format is usually: "Name <email@domain.com>"
                    author_parts = commit.author.split("<")
                    author_name = author_parts[0].strip() if author_parts else commit.author
                    author_email = author_parts[1].rstrip(">") if len(author_parts) > 1 else "unknown@unknown.com"
                    
                    git_commit = GitCommitModel(
                        sha=commit.sha,
                        message=commit.message,
                        author=author_name,
                        author_email=author_email,
                        date=commit.date,
                        commit_metadata={"repo_path": str(self.git_service.repo_path)}
                    )
                    session.add(git_commit)
                    await session.flush()  # Ensure it's inserted before document
                    logger.debug(f"✅ Inserted commit {commit.sha[:8]} by {author_name} into git_commits table")
                
                content_hash = sha256(normalized["content"].encode()).hexdigest()
                
                # ✅ DUPLICATE PROTECTION: Check if identical document exists
                existing_doc = await doc_repo.get_by_content_hash(content_hash)
                if existing_doc:
                    logger.debug(f"⏭️  Duplicate found: {path} (hash: {content_hash[:8]})")
                    
                    # Try to enrich existing metadata
                    enriched = await self._enrich_duplicate_metadata(
                        existing_doc,
                        normalized["metadata"],
                        session
                    )
                    
                    if enriched:
                        logger.info(f"✨ Enriched metadata for: {path}")
                        result["enriched"] = True
                    
                    result["skipped"] = True  # Mark as skipped, not error
                    return result
                
                document = DocumentModel(
                    id=uuid4(),
                    service_name=normalized["metadata"].get("service", "ecosystem-mcp"),
                    file_path=str(path),
                    original_format=path.suffix[1:],  # Remove leading dot
                    original_content=content,
                    normalized_content=normalized["content"],
                    content_hash=content_hash,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                    git_commit_sha=commit.sha,
                    is_latest=True,
                    doc_metadata=normalized["metadata"]
                )
                
                # Mark previous versions as not latest
                await doc_repo.mark_as_outdated(str(path))
                
                # Save document
                created_doc = await doc_repo.create(document)
                await session.commit()
                
                # Store embedding in ChromaDB with retry
                chroma = get_chroma_client()
                embedding_success = await chroma.add_embeddings_with_retry(
                    ids=[str(created_doc.id)],
                    embeddings=[embedding_result["embedding"]],
                    documents=[normalized["content"]],
                    metadatas=[{
                        "service_name": created_doc.service_name,
                        "file_path": str(path),
                        "commit_sha": commit.sha,
                        "content_hash": content_hash
                    }],
                    max_retries=3
                )
                
                if not embedding_success:
                    logger.error(f"⚠️ Failed to store embedding for {path} after retries, but document saved")
                    result["embedding_failed"] = True
            
            result["success"] = True
            result["cost"] = embedding_result.get("cost", 0.0)
            
            logger.debug(f"✅ Processed {path}")
        
        except Exception as e:
            # ✅ FIXED: file_change is a string
            file_path_display = file_change if isinstance(file_change, str) else file_change.path
            logger.error(f"Error processing file {file_path_display}: {e}", exc_info=True)
            result["error"] = str(e)
        
        return result
    
    # ============================================================================
    # PHASE 10: Sub-Job Orchestration Integration
    # ============================================================================
    
    async def _should_use_orchestration(self, job: IngestionJobModel) -> bool:
        """
        Determine if job should use sub-job orchestration.
        
        Criteria:
        - Repository has enough files (>500 files worth orchestration overhead)
        - Not in quick mode (quick mode is already fast)
        
        Args:
            job: Ingestion job
        
        Returns:
            True if orchestration should be used
        """
        try:
            # Quick mode doesn't benefit from orchestration
            if job.mode == "quick":
                logger.info("Quick mode doesn't use orchestration (already optimized)")
                return False
            
            # Check repository size
            # For now, use a simple file count heuristic
            # TODO: Could be more sophisticated (check git history size, etc.)
            try:
                from pathlib import Path
                repo_path = Path(job.repo_path)
                
                if not repo_path.exists():
                    logger.warning(f"Repository path doesn't exist: {job.repo_path}")
                    return False
                
                # Count files (simple heuristic)
                file_count = sum(1 for _ in repo_path.rglob('*') if _.is_file())
                
                logger.info(f"Repository has ~{file_count} files")
                
                # Use orchestration if >500 files
                if file_count > 500:
                    logger.info(f"✅ Repository large enough for orchestration ({file_count} files)")
                    return True
                else:
                    logger.info(f"📝 Repository too small for orchestration ({file_count} files, need >500)")
                    return False
                    
            except Exception as e:
                logger.warning(f"Could not count files: {e}, using orchestration anyway")
                return True
                
        except Exception as e:
            logger.error(f"Error determining orchestration: {e}", exc_info=True)
            # On error, default to standard processing (safer)
            return False
    
    async def _process_with_orchestration(self, job: IngestionJobModel) -> Dict[str, Any]:
        """
        Process job using sub-job orchestration for parallel processing.
        
        Pipeline:
        1. Discovery: Scan and classify files
        2. Planning: Create sub-jobs with priorities
        3. Orchestration: Execute sub-jobs in parallel
        4. Aggregation: Combine results
        
        Args:
            job: Ingestion job
        
        Returns:
            Processing results with orchestration metrics
        """
        logger.info(f"🚀 Starting orchestrated processing for job {job.id}")
        
        result = {
            "success": False,
            "processed_documents": 0,
            "total_documents": 0,
            "failed_documents": 0,
            "skipped_documents": 0,
            "embeddings_generated": 0,
            "total_cost_usd": 0.0,
            "subjobs_executed": 0,
            "subjobs_failed": 0,
            "error": None
        }
        
        try:
            # Initialize progress tracking
            await self._update_progress("orchestration_init", 0, 100, message="Initializing orchestration...")
            
            # Phase 1: Discovery (scan and classify files)
            logger.info("📊 Phase 1/3: Discovery and classification")
            await self._update_progress("discovery", 10, 100, message="Scanning repository...")
            
            try:
                from ..discovery.discovery_engine import get_discovery_engine
                from ..discovery.repository_scanner import get_repository_scanner
                from ..discovery.file_classifier import get_file_classifier
                
                # Scan repository
                scanner = get_repository_scanner()
                inventory = await scanner.scan(job.repo_path)
                
                logger.info(f"   Scanned {inventory.total_files} files")
                result["total_documents"] = inventory.total_files
                
                # Classify files by importance
                classifier = get_file_classifier()
                classified_files = await classifier.classify(inventory.files)
                
                logger.info(f"   Classified {len(classified_files)} files")
                
            except Exception as e:
                logger.error(f"❌ Discovery failed: {e}", exc_info=True)
                result["error"] = f"Discovery failed: {str(e)}"
                return result
            
            # Phase 2: Planning (create processing plan with sub-jobs)
            logger.info("📋 Phase 2/4: Creating processing plan")
            await self._update_progress("planning", 25, 100, message="Creating sub-jobs...")
            
            plan = None
            try:
                from ..discovery.processing_planner import get_processing_planner
                
                planner = get_processing_planner()
                plan = await planner.create_plan(
                    inventory=inventory,
                    classified_files=classified_files,
                    repo_path=job.repo_path
                )
                
                logger.info(f"   Created plan with {len(plan.sub_jobs)} sub-jobs")
                logger.info(f"   Estimated time: {plan.estimated_time_minutes:.1f} minutes")
                
            except Exception as e:
                logger.error(f"❌ Planning failed: {e}", exc_info=True)
                result["error"] = f"Planning failed: {str(e)}"
                return result
            
            # Phase 3: Analysis (PHASE 10 - Gap #2: Get dependency order)
            logger.info("🔬 Phase 3/4: Analyzing dependencies")
            await self._update_progress("analysis", 45, 100, message="Analyzing dependencies...")
            
            topological_order = None
            try:
                from ..analysis.analysis_engine import get_analysis_engine
                
                # Perform analysis
                analysis_engine = get_analysis_engine()
                file_dicts = [{'path': f.file_path, 'language': f.language or 'unknown'} 
                             for f in classified_files]
                
                analysis_report = await analysis_engine.analyze(
                    plan_id=str(plan.id) if hasattr(plan, 'id') else "temp",
                    files=file_dicts,
                    repo_path=job.repo_path
                )
                
                # Extract topological order
                if analysis_report and analysis_report.dependency_graph:
                    topological_order = analysis_report.dependency_graph.topological_order
                    if topological_order:
                        logger.info(f"   ✅ Dependency order computed: {len(topological_order)} files")
                        
                        # Store in plan metadata for orchestrator to use
                        if not hasattr(plan, 'processing_order') or not plan.processing_order:
                            plan.processing_order = {}
                        if isinstance(plan.processing_order, dict):
                            plan.processing_order['topological_order'] = topological_order
                    else:
                        logger.info(f"   No dependency order computed (no dependencies)")
                
            except Exception as e:
                logger.warning(f"⚠️ Analysis failed (continuing without dependency order): {e}")
                # Continue without dependency order - not critical
            
            # Phase 4: Orchestration (execute sub-jobs in parallel)
            logger.info("⚡ Phase 4/4: Executing sub-jobs in parallel")
            await self._update_progress("orchestration", 60, 100, message=f"Executing {len(plan.sub_jobs)} sub-jobs...")
            
            try:
                from ..orchestration.job_orchestrator import JobOrchestrator
                
                # Create orchestrator with parallelism
                max_concurrent = 5  # TODO: Make configurable
                orchestrator = JobOrchestrator(max_concurrent=max_concurrent)
                
                logger.info(f"   Orchestrator initialized (max {max_concurrent} concurrent)")
                
                # Execute plan
                exec_result = await orchestrator.execute_plan(plan.id)
                
                # Aggregate results
                result["success"] = exec_result.status == "completed"
                result["processed_documents"] = exec_result.total_files_processed
                result["failed_documents"] = exec_result.total_files_failed
                result["skipped_documents"] = exec_result.total_files_skipped
                result["subjobs_executed"] = exec_result.sub_jobs_completed
                result["subjobs_failed"] = exec_result.sub_jobs_failed
                
                # Calculate embeddings (approximate from sub-jobs)
                # TODO: Could track more precisely
                result["embeddings_generated"] = int(exec_result.total_files_processed * 0.8)  # Estimate
                
                logger.info(
                    f"✅ Orchestration complete: "
                    f"{result['processed_documents']}/{result['total_documents']} documents processed "
                    f"({result['subjobs_executed']} sub-jobs completed, "
                    f"{result['subjobs_failed']} failed)"
                )
                
                await self._update_progress("completed", 100, 100, message="Orchestration complete")
                
            except Exception as e:
                logger.error(f"❌ Orchestration failed: {e}", exc_info=True)
                result["error"] = f"Orchestration failed: {str(e)}"
                return result
            
        except Exception as e:
            logger.error(f"❌ Orchestrated processing failed: {e}", exc_info=True)
            result["error"] = str(e)
            await self._update_progress("failed", 0, 0, message=f"Failed: {str(e)}")
        
        return result

