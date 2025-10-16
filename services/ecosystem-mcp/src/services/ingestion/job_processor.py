"""
Job Processor

Orchestrates the document ingestion pipeline for a single job.
Coordinates Git extraction, document normalization, embedding generation,
and storage operations.
"""

import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
from uuid import UUID
from sqlalchemy.orm.attributes import flag_modified
import asyncio
import json

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
                 max_concurrent_commits: int = None):
        """
        Initialize the job processor.
        
        Args:
            worker_id: Unique identifier for the worker instance
            use_batch_optimization: Enable Phase 1 optimizations (batch embeddings, connection pooling, caching)
            max_concurrent_commits: Maximum number of commits to process in parallel (Phase 2)
                                   If None, automatically determined based on CPU count (2× cores, max 20)
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
        
        logger.info(
            f"JobProcessor initialized (worker: {worker_id}, "
            f"batch_optimization: {'✅ ENABLED' if use_batch_optimization else '❌ DISABLED'}, "
            f"parallel_commits: {max_concurrent_commits}, "
            f"commit_timeout: {self.commit_timeout_seconds}s)"
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
    
    async def process(self, job: IngestionJobModel) -> Dict[str, Any]:
        """
        Process a single ingestion job.
        
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
                "error": Optional[str]
            }
        """
        logger.info(f"Processing job {job.id}: mode={job.mode}, repo={job.repo_path}")
        
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
            # Initialize Git service for this job
            await self._update_progress("initializing", 0, 100, message="Initializing Git service...")
            self.git_service = GitService(repo_path=job.repo_path)
            
            # Get commits based on mode
            await self._update_progress("scanning", 10, 100, message="Scanning repository for commits...")
            commits = await self._get_commits_for_mode(job.mode)
            
            if not commits:
                result["error"] = "No commits found"
                await self._update_progress("failed", 0, 0, message="No commits found")
                return result
            
            logger.info(f"Found {len(commits)} commits to process")
            await self._update_progress("processing", 0, len(commits), message=f"Found {len(commits)} commits")
            
            # PHASE 2: Process commits in PARALLEL if enabled and multiple commits
            if self.use_batch_optimization and len(commits) > 1:
                logger.info(
                    f"🚀 PHASE 2: Processing {len(commits)} commits in PARALLEL "
                    f"(max {self.max_concurrent_commits} concurrent)"
                )
                
                # Create tasks for all commits
                import asyncio
                commit_tasks = [
                    self._process_commit_parallel(commit, job, i, len(commits))
                    for i, commit in enumerate(commits, 1)
                ]
                
                # Execute all commits in parallel (semaphore limits concurrency)
                commit_results = await asyncio.gather(*commit_tasks, return_exceptions=True)
                
                # Aggregate results from all commits
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
            result["success"] = True
            
            # Clear checkpoint after successful completion
            await self.checkpoint_manager.clear_checkpoint(job.id)
            
            # Update final progress
            await self._update_progress(
                "completed",
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
            
            logger.info(
                f"✅ Job {job.id} processing complete: "
                f"{result['processed_documents']}/{result['total_documents']} documents, "
                f"{result['skipped_documents']} skipped, "
                f"{result['embeddings_generated']} embeddings"
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
        
        return result
    
    async def _get_commits_for_mode(self, mode: str) -> List[Any]:
        """
        Get commits based on ingestion mode.
        
        Args:
            mode: Ingestion mode (quick, full, incremental, recent)
        
        Returns:
            List of GitCommit objects
        """
        if mode == "quick":
            # Last 10 commits
            return await self.git_service.get_recent_commits(limit=10)
        elif mode == "recent":
            # Last 200 commits
            return await self.git_service.get_recent_commits(limit=200)
        elif mode == "full":
            # All commits (limited to 1000 for safety)
            return await self.git_service.get_recent_commits(limit=1000)
        elif mode == "incremental":
            # TODO: Get commits since last ingestion
            # For now, same as quick
            return await self.git_service.get_recent_commits(limit=10)
        else:
            logger.warning(f"Unknown mode '{mode}', defaulting to quick")
            return await self.git_service.get_recent_commits(limit=10)
    
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
    
    async def _process_commit_parallel(
        self,
        commit: Any,
        job: IngestionJobModel,
        commit_num: int,
        total_commits: int
    ) -> Dict[str, Any]:
        """
        PHASE 2: Process a single commit with concurrency control and timeout protection.
        
        Uses semaphore to limit number of concurrent commits being processed.
        Wraps the optimized batch processing with parallel execution support.
        Includes timeout protection and git error handling.
        
        Args:
            commit: GitCommit object
            job: Parent ingestion job
            commit_num: Current commit number (for logging)
            total_commits: Total number of commits (for logging)
        
        Returns:
            Dict with processing results
        """
        async with self.commit_semaphore:
            logger.info(f"🔄 Starting commit {commit_num}/{total_commits}: {commit.sha[:8]}")
            
            try:
                # Add timeout protection
                if self.use_batch_optimization:
                    process_task = self._process_commit_with_batch_optimization(
                        commit, job, batch_size=20
                    )
                else:
                    process_task = self._process_commit(commit, job)
                
                # Apply timeout
                result = await asyncio.wait_for(
                    process_task,
                    timeout=self.commit_timeout_seconds
                )
                
                logger.info(
                    f"✅ Completed commit {commit_num}/{total_commits}: {commit.sha[:8]} "
                    f"({result['processed']} processed, {result['skipped']} skipped, {result['failed']} failed)"
                )
                return result
                
            except asyncio.TimeoutError:
                logger.error(
                    f"⏱️  TIMEOUT: Commit {commit_num}/{total_commits}: {commit.sha[:8]} "
                    f"exceeded {self.commit_timeout_seconds}s timeout"
                )
                return {
                    "processed": 0,
                    "failed": 1,
                    "skipped": 0,
                    "embeddings": 0,
                    "cost": 0.0,
                    "error": f"Timeout after {self.commit_timeout_seconds}s"
                }
                
            except GitCorruptionError as e:
                logger.error(
                    f"🔴 GIT CORRUPTION in commit {commit_num}/{total_commits}: {commit.sha[:8]} - {e}"
                )
                return {
                    "processed": 0,
                    "failed": 1,
                    "skipped": 0,
                    "embeddings": 0,
                    "cost": 0.0,
                    "error": f"Git corruption: {str(e)}"
                }
                
            except Exception as e:
                # Classify the error
                error_classification = self.git_error_handler.classify_error(
                    e,
                    {
                        "commit_sha": commit.sha,
                        "operation": "process_commit",
                        "commit_num": commit_num,
                        "total_commits": total_commits
                    }
                )
                
                logger.error(
                    f"❌ Failed commit {commit_num}/{total_commits}: {commit.sha[:8]} - "
                    f"{error_classification['category']}: {e}",
                    exc_info=True
                )
                
                return {
                    "processed": 0,
                    "failed": 1,
                    "skipped": 0,
                    "embeddings": 0,
                    "cost": 0.0,
                    "error": str(e),
                    "error_category": error_classification['category']
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
                            metadatas=[{
                                "file_path": str(e['path']),
                                "service": e['document'].service_name,
                                "commit_sha": commit.sha[:8],
                                "created_at": e['document'].created_at.isoformat()
                            } for e in embeddings_to_store],
                            documents=[e['document'].normalized_content[:1000] for e in embeddings_to_store]
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
                    metadatas=[{
                        "file_path": str(path),
                        "service": normalized["metadata"].get("service", "ecosystem-mcp"),
                        "commit_sha": commit.sha[:8],
                        "created_at": created_doc.created_at.isoformat()
                    }],
                    documents=[normalized["content"][:1000]]
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

