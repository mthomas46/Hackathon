"""
Recoverable Job Processor

Enhanced job processor with checkpoint support for graceful recovery.
Allows interrupted ingestion jobs to resume from last checkpoint.
"""

import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
from uuid import UUID

from ...storage.db_models import IngestionJobModel
from ..git.git_service import GitService
from ..processing.normalizer_factory import NormalizerFactory
from ..embeddings.embedding_service import EmbeddingService
from ...storage import get_database
from ...storage.repositories import DocumentRepository
from ...storage.chromadb_client import get_chroma_client
from ...utils.job_recovery import (
    JobRecoveryManager,
    RecoverableJob,
    JobType,
    get_recovery_manager
)

logger = logging.getLogger(__name__)


class RecoverableJobProcessor(RecoverableJob):
    """
    Enhanced job processor with checkpoint support.
    
    Features:
    - Automatic checkpointing per commit
    - Resume from last completed commit
    - Skip already-processed files
    - Graceful interruption handling
    - Progress persistence
    """
    
    def __init__(self, job_id: str, recovery_manager: JobRecoveryManager):
        """Initialize recoverable job processor."""
        super().__init__(job_id, JobType.INGESTION, recovery_manager)
        
        self.git_service = None
        self.normalizer_factory = NormalizerFactory()
        self.embedding_service = EmbeddingService()
        
        logger.info(f"RecoverableJobProcessor initialized for job {job_id}")
    
    async def process(
        self,
        job: IngestionJobModel,
        resume: bool = True
    ) -> Dict[str, Any]:
        """
        Process ingestion job with checkpoint support.
        
        Args:
            job: Ingestion job to process
            resume: Whether to attempt resume from last checkpoint
        
        Returns:
            Processing results
        """
        logger.info(
            f"🔄 Processing job {job.id} (resume={resume}): "
            f"mode={job.mode}, repo={job.repo_path}"
        )
        
        result = {
            "success": False,
            "processed_documents": 0,
            "total_documents": 0,
            "failed_documents": 0,
            "skipped_documents": 0,
            "embeddings_generated": 0,
            "total_cost_usd": 0.0,
            "resumed_from_checkpoint": False,
            "error": None
        }
        
        try:
            # Initialize Git service
            self.git_service = GitService(repo_path=job.repo_path)
            
            # Load checkpoints from database
            await self.recovery_manager.load_checkpoints(str(job.id))
            
            # Check if we can resume
            can_resume = False
            resume_state = None
            
            if resume:
                can_resume = await self.can_resume()
                
                if can_resume:
                    resume_state = await self.get_resume_state()
                    logger.info(
                        f"📂 Resuming from checkpoint: "
                        f"completed={resume_state['progress']['completed_checkpoints']}, "
                        f"total={resume_state['progress']['total_checkpoints']}"
                    )
                    result["resumed_from_checkpoint"] = True
            
            # Get commits for processing
            commits = await self._get_commits_for_mode(job.mode)
            
            if not commits:
                result["error"] = "No commits found"
                return result
            
            logger.info(f"📚 Found {len(commits)} commits to process")
            
            # Determine starting point
            start_index = 0
            
            if can_resume and resume_state:
                # Resume from next checkpoint after last completed
                last_checkpoint_data = resume_state["last_checkpoint"]["data"]
                last_commit_sha = last_checkpoint_data.get("commit_sha")
                
                # Find the commit index to resume from
                for idx, commit in enumerate(commits):
                    if commit.sha == last_commit_sha:
                        start_index = idx + 1  # Start from next commit
                        
                        # Restore counters from last checkpoint
                        result["processed_documents"] = last_checkpoint_data.get("processed", 0)
                        result["failed_documents"] = last_checkpoint_data.get("failed", 0)
                        result["skipped_documents"] = last_checkpoint_data.get("skipped", 0)
                        result["embeddings_generated"] = last_checkpoint_data.get("embeddings", 0)
                        result["total_cost_usd"] = last_checkpoint_data.get("cost", 0.0)
                        
                        logger.info(
                            f"✅ Resuming from commit {idx + 1}/{len(commits)}: "
                            f"{commit.sha[:8]}"
                        )
                        break
            
            # Process commits starting from resume point
            for i in range(start_index, len(commits)):
                commit = commits[i]
                commit_num = i + 1
                
                logger.info(
                    f"📝 Processing commit {commit_num}/{len(commits)}: "
                    f"{commit.sha[:8]}"
                )
                
                # Create checkpoint for this commit
                checkpoint_id = f"commit_{commit.sha[:8]}_{commit_num}"
                
                await self.create_checkpoint(
                    checkpoint_id=checkpoint_id,
                    data={
                        "commit_sha": commit.sha,
                        "commit_index": i,
                        "commit_num": commit_num,
                        "total_commits": len(commits),
                        "processed": result["processed_documents"],
                        "failed": result["failed_documents"],
                        "skipped": result["skipped_documents"],
                        "embeddings": result["embeddings_generated"],
                        "cost": result["total_cost_usd"]
                    }
                )
                
                try:
                    # Process the commit
                    commit_result = await self._process_commit(commit, job)
                    
                    # Update counters
                    result["processed_documents"] += commit_result["processed"]
                    result["failed_documents"] += commit_result["failed"]
                    result["skipped_documents"] += commit_result.get("skipped", 0)
                    result["embeddings_generated"] += commit_result["embeddings"]
                    result["total_cost_usd"] += commit_result["cost"]
                    
                    # Mark checkpoint as completed
                    await self.complete_checkpoint(data={
                        "processed": result["processed_documents"],
                        "failed": result["failed_documents"],
                        "skipped": result["skipped_documents"],
                        "embeddings": result["embeddings_generated"],
                        "cost": result["total_cost_usd"]
                    })
                    
                    logger.info(
                        f"✅ Checkpoint {checkpoint_id} completed: "
                        f"+{commit_result['processed']} docs"
                    )
                
                except Exception as e:
                    # Mark checkpoint as failed but continue
                    await self.fail_checkpoint(str(e))
                    logger.error(
                        f"❌ Checkpoint {checkpoint_id} failed: {e}",
                        exc_info=True
                    )
                    # Continue to next commit instead of failing entire job
                    continue
            
            result["total_documents"] = (
                result["processed_documents"] +
                result["failed_documents"] +
                result["skipped_documents"]
            )
            result["success"] = True
            
            # Cleanup old checkpoints (keep last 5)
            await self.recovery_manager.cleanup_checkpoints(
                job_id=str(job.id),
                keep_last=5
            )
            
            logger.info(
                f"✅ Job {job.id} processing complete: "
                f"{result['processed_documents']}/{result['total_documents']} documents, "
                f"{result['skipped_documents']} skipped, "
                f"{result['embeddings_generated']} embeddings, "
                f"${result['total_cost_usd']:.4f} cost"
            )
        
        except Exception as e:
            logger.error(f"❌ Error processing job {job.id}: {e}", exc_info=True)
            result["error"] = str(e)
            
            # Try to save failure checkpoint
            try:
                await self.fail_checkpoint(str(e))
            except:
                pass
        
        return result
    
    async def _get_commits_for_mode(self, mode: str) -> List[Any]:
        """Get commits based on ingestion mode."""
        if mode == "quick":
            return await self.git_service.get_recent_commits(limit=10)
        elif mode == "recent":
            return await self.git_service.get_recent_commits(limit=200)
        elif mode == "full":
            return await self.git_service.get_all_commits()
        else:  # incremental
            # TODO: Implement incremental mode with last processed commit
            return await self.git_service.get_recent_commits(limit=10)
    
    async def _process_commit(
        self,
        commit,
        job: IngestionJobModel
    ) -> Dict[str, Any]:
        """
        Process a single commit.
        
        Args:
            commit: GitCommit object
            job: Ingestion job
        
        Returns:
            Commit processing results
        """
        result = {
            "processed": 0,
            "failed": 0,
            "skipped": 0,
            "embeddings": 0,
            "cost": 0.0
        }
        
        try:
            # Get files changed in this commit
            files = await self.git_service.get_files_in_commit(commit.sha)
            
            logger.info(f"Processing {len(files)} files from commit {commit.sha[:8]}")
            
            # Process each file with progress updates
            for file_idx, file_path in enumerate(files, 1):
                try:
                    # Update job progress
                    await self._update_job_progress(
                        job=job,
                        last_file=str(file_path),
                        current_commit=commit.sha[:8],
                        processed=result["processed"],
                        skipped=result["skipped"],
                        failed=result["failed"],
                        current_file_index=file_idx,
                        total_files=len(files)
                    )
                    
                    file_result = await self._process_file(
                        file_path=file_path,
                        commit=commit,
                        job=job
                    )
                    
                    result["processed"] += file_result["processed"]
                    result["failed"] += file_result["failed"]
                    result["skipped"] += file_result["skipped"]
                    result["embeddings"] += file_result["embeddings"]
                    result["cost"] += file_result["cost"]
                
                except Exception as e:
                    logger.error(f"Error processing file {file_path}: {e}")
                    result["failed"] += 1
        
        except Exception as e:
            logger.error(f"Error processing commit {commit.sha}: {e}", exc_info=True)
            raise
        
        return result
    
    async def _process_file(
        self,
        file_path: Path,
        commit,
        job: IngestionJobModel
    ) -> Dict[str, Any]:
        """Process a single file."""
        result = {
            "processed": 0,
            "failed": 0,
            "skipped": 0,
            "embeddings": 0,
            "cost": 0.0
        }
        
        try:
            # Get file content
            content = await self.git_service.get_file_content(
                commit.sha,
                str(file_path)
            )
            
            if not content:
                result["skipped"] += 1
                return result
            
            # Normalize to markdown
            normalizer = self.normalizer_factory.get_normalizer(file_path)
            
            if not normalizer:
                result["skipped"] += 1
                return result
            
            normalized = await normalizer.normalize(content)
            
            # Store in database
            db = get_database()
            async with db.session() as session:
                doc_repo = DocumentRepository(session)
                
                # Check if document already exists
                existing = await doc_repo.get_by_source_path(str(file_path))
                
                if existing:
                    result["skipped"] += 1
                    return result
                
                # Create new document
                doc = await doc_repo.create(
                    content=normalized,
                    source_path=str(file_path),
                    original_format=file_path.suffix,
                    service_id=job.service_id,
                    commit_sha=commit.sha
                )
                
                await session.commit()
                
                # Generate embedding
                embedding = await self.embedding_service.generate_embedding(
                    normalized
                )
                
                # Store in ChromaDB
                chroma = get_chroma_client()
                await chroma.add_document(
                    document_id=str(doc.id),
                    embedding=embedding,
                    metadata={
                        "source_path": str(file_path),
                        "service_id": job.service_id,
                        "commit_sha": commit.sha
                    }
                )
                
                result["processed"] += 1
                result["embeddings"] += 1
        
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            result["failed"] += 1
        
        return result
    
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
        """Update job progress metadata."""
        try:
            db = get_database()
            async with db.session() as session:
                from ...storage.repositories import IngestionJobRepository
                repo = IngestionJobRepository(session)
                
                current_job = await repo.get_by_id(job.id)
                
                if not current_job:
                    return
                
                if current_job.job_metadata is None:
                    current_job.job_metadata = {}
                
                current_job.job_metadata["last_processed_file"] = last_file
                current_job.job_metadata["current_commit"] = current_commit
                current_job.job_metadata["last_update"] = datetime.utcnow().isoformat()
                current_job.job_metadata["current_file_index"] = current_file_index
                current_job.job_metadata["total_files_in_commit"] = total_files
                current_job.job_metadata["progress_pct"] = round(
                    (current_file_index / total_files * 100) if total_files > 0 else 0,
                    1
                )
                
                current_job.processed_documents = processed
                current_job.skipped_documents = skipped
                current_job.failed_documents = failed
                
                await repo.update(current_job)
                await session.commit()
        
        except Exception as e:
            logger.warning(f"Failed to update job progress: {e}")

