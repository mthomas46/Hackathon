"""
Batched Commit Processor with Checkpointing

Processes git commits in batches with progress checkpointing to handle timeouts gracefully.
If a job times out, it can resume from the last completed batch instead of starting over.

Key Features:
- Configurable batch size (default: 10 commits per batch)
- Checkpoint after each batch completes
- Resume from last checkpoint on timeout/failure
- Progress tracking per batch
- Transforms timeout from failure to pause point
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

from ...storage.db_models import IngestionJobModel

logger = logging.getLogger(__name__)


class BatchedCommitProcessor:
    """
    Processes commits in batches with checkpointing for resilience.
    
    This solves the timeout problem by:
    1. Breaking 1000 commits into batches of 10 (100 batches)
    2. Processing each batch completely
    3. Checkpointing progress after each batch
    4. On timeout: Resume from last checkpoint, not from beginning
    
    Example:
        - Process commits 1-10 → Checkpoint
        - Process commits 11-20 → Checkpoint
        - TIMEOUT occurs at commit 25
        - Resume: Start from commit 21 (last checkpoint)
        - Continue processing remaining 979 commits
    """
    
    def __init__(
        self,
        job_processor,
        batch_size: int = 10,
        max_concurrent_per_batch: int = 10,
        checkpoint_manager=None
    ):
        """
        Initialize batched processor.
        
        Args:
            job_processor: Main JobProcessor instance
            batch_size: Number of commits per batch (default: 10)
            max_concurrent_per_batch: Max parallel commits within a batch (default: 10)
            checkpoint_manager: Optional checkpoint manager (uses job_processor's if None)
        """
        self.job_processor = job_processor
        self.batch_size = batch_size
        self.max_concurrent_per_batch = max_concurrent_per_batch
        self.checkpoint_manager = checkpoint_manager or job_processor.checkpoint_manager
        
        logger.info(
            f"BatchedCommitProcessor initialized: "
            f"batch_size={batch_size}, "
            f"max_concurrent_per_batch={max_concurrent_per_batch}"
        )
    
    async def process_commits_in_batches(
        self,
        commits: List[Any],
        job: IngestionJobModel,
        resume_from_batch: int = 0
    ) -> Dict[str, Any]:
        """
        Process commits in batches with checkpointing.
        
        Args:
            commits: List of commits to process
            job: Ingestion job model
            resume_from_batch: Batch number to resume from (0-based)
        
        Returns:
            Aggregated results from all batches
        """
        total_commits = len(commits)
        total_batches = (total_commits + self.batch_size - 1) // self.batch_size
        
        logger.info(
            f"📦 Processing {total_commits} commits in {total_batches} batches "
            f"(batch size: {self.batch_size}, resume from batch: {resume_from_batch})"
        )
        
        # Initialize results
        result = {
            "processed_documents": 0,
            "failed_documents": 0,
            "skipped_documents": 0,
            "embeddings_generated": 0,
            "total_cost_usd": 0.0,
            "batches_completed": 0,
            "batches_failed": 0
        }
        
        # Process each batch
        for batch_num in range(resume_from_batch, total_batches):
            batch_start = batch_num * self.batch_size
            batch_end = min(batch_start + self.batch_size, total_commits)
            batch_commits = commits[batch_start:batch_end]
            
            batch_info = f"Batch {batch_num + 1}/{total_batches} (commits {batch_start + 1}-{batch_end}/{total_commits})"
            logger.info(f"🔄 Starting {batch_info}")
            
            try:
                # Process this batch
                batch_result = await self._process_single_batch(
                    batch_commits,
                    job,
                    batch_num,
                    total_batches
                )
                
                # Aggregate results
                result["processed_documents"] += batch_result["processed"]
                result["failed_documents"] += batch_result["failed"]
                result["skipped_documents"] += batch_result.get("skipped", 0)
                result["embeddings_generated"] += batch_result["embeddings"]
                result["total_cost_usd"] += batch_result.get("cost", 0.0)
                result["batches_completed"] += 1
                
                # ✅ CHECKPOINT: Save progress after each batch
                await self._save_batch_checkpoint(
                    job,
                    batch_num + 1,  # Next batch to process
                    result
                )
                
                logger.info(
                    f"✅ Completed {batch_info}: "
                    f"{batch_result['processed']} processed, "
                    f"{batch_result['failed']} failed, "
                    f"{batch_result.get('skipped', 0)} skipped"
                )
                
                # Update job progress in database
                await self._update_job_counters(job, result)
                
            except Exception as e:
                logger.error(f"❌ Batch {batch_num + 1} failed: {e}", exc_info=True)
                result["batches_failed"] += 1
                
                # Save failure checkpoint (can resume from next batch)
                await self._save_batch_checkpoint(
                    job,
                    batch_num + 1,  # Try next batch on resume
                    result,
                    error=str(e)
                )
                
                # Continue with next batch (don't fail entire job on one batch failure)
                continue
        
        logger.info(
            f"🎉 All batches complete: "
            f"{result['batches_completed']}/{total_batches} succeeded, "
            f"{result['batches_failed']} failed, "
            f"{result['processed_documents']} total documents"
        )
        
        return result
    
    async def _process_single_batch(
        self,
        batch_commits: List[Any],
        job: IngestionJobModel,
        batch_num: int,
        total_batches: int
    ) -> Dict[str, Any]:
        """
        Process a single batch of commits in parallel.
        
        Args:
            batch_commits: Commits in this batch
            job: Ingestion job
            batch_num: Current batch number (0-based)
            total_batches: Total number of batches
        
        Returns:
            Batch processing results
        """
        batch_size = len(batch_commits)
        logger.debug(f"Processing batch {batch_num + 1}/{total_batches} with {batch_size} commits")
        
        # Create tasks for all commits in this batch
        commit_tasks = [
            self.job_processor._process_commit_parallel(
                commit,
                job,
                idx,
                batch_size
            )
            for idx, commit in enumerate(batch_commits, 1)
        ]
        
        # Process batch commits in parallel (limited by semaphore)
        commit_results = await asyncio.gather(*commit_tasks, return_exceptions=True)
        
        # Aggregate batch results
        batch_result = {
            "processed": 0,
            "failed": 0,
            "skipped": 0,
            "embeddings": 0,
            "cost": 0.0
        }
        
        for idx, commit_result in enumerate(commit_results, 1):
            if isinstance(commit_result, Exception):
                logger.error(f"Commit {idx} in batch {batch_num + 1} failed: {commit_result}")
                batch_result["failed"] += 1
            else:
                batch_result["processed"] += commit_result.get("processed", 0)
                batch_result["failed"] += commit_result.get("failed", 0)
                batch_result["skipped"] += commit_result.get("skipped", 0)
                batch_result["embeddings"] += commit_result.get("embeddings", 0)
                batch_result["cost"] += commit_result.get("cost", 0.0)
        
        return batch_result
    
    async def _save_batch_checkpoint(
        self,
        job: IngestionJobModel,
        next_batch: int,
        results: Dict[str, Any],
        error: Optional[str] = None
    ):
        """
        Save checkpoint after batch completion.
        
        Args:
            job: Ingestion job
            next_batch: Next batch number to process (0-based)
            results: Accumulated results so far
            error: Error message if batch failed
        """
        checkpoint_data = {
            "next_batch": next_batch,
            "batches_completed": results["batches_completed"],
            "batches_failed": results["batches_failed"],
            "processed_documents": results["processed_documents"],
            "failed_documents": results["failed_documents"],
            "skipped_documents": results["skipped_documents"],
            "embeddings_generated": results["embeddings_generated"],
            "total_cost_usd": results["total_cost_usd"],
            "checkpoint_time": datetime.utcnow().isoformat()
        }
        
        if error:
            checkpoint_data["last_error"] = error
        
        # Save to checkpoint manager
        await self.checkpoint_manager.save_checkpoint(
            job_id=str(job.id),
            checkpoint_data=checkpoint_data
        )
        
        logger.debug(f"💾 Checkpoint saved: next_batch={next_batch}, processed={results['processed_documents']}")
    
    async def _update_job_counters(self, job: IngestionJobModel, results: Dict[str, Any]):
        """
        Update job counters in database.
        
        Args:
            job: Ingestion job
            results: Current results
        """
        try:
            from ...storage import get_database
            from ...storage.repositories import IngestionJobRepository
            
            db = get_database()
            async with db.session() as session:
                repo = IngestionJobRepository(session)
                
                # Get fresh job instance
                current_job = await repo.get_by_id(job.id)
                if not current_job:
                    return
                
                # Update counters
                current_job.processed_documents = results["processed_documents"]
                current_job.failed_documents = results["failed_documents"]
                current_job.skipped_documents = results["skipped_documents"]
                current_job.embeddings_generated = results.get("embeddings_generated", 0)
                
                # Update total
                current_job.total_documents = (
                    results["processed_documents"] +
                    results["failed_documents"] +
                    results["skipped_documents"]
                )
                
                await repo.update(current_job)
                await session.commit()
                
                logger.debug(f"📊 Job counters updated: {current_job.processed_documents}/{current_job.total_documents}")
                
        except Exception as e:
            logger.warning(f"Failed to update job counters: {e}")
    
    async def load_checkpoint(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Load checkpoint for job.
        
        Args:
            job_id: Job ID
        
        Returns:
            Checkpoint data or None if no checkpoint
        """
        try:
            checkpoint = await self.checkpoint_manager.load_checkpoint(job_id)
            if checkpoint:
                logger.info(
                    f"📂 Loaded checkpoint: "
                    f"next_batch={checkpoint.get('next_batch', 0)}, "
                    f"processed={checkpoint.get('processed_documents', 0)}"
                )
            return checkpoint
        except Exception as e:
            logger.warning(f"Failed to load checkpoint: {e}")
            return None


def get_batched_commit_processor(
    job_processor,
    batch_size: int = 10,
    max_concurrent_per_batch: int = 10
) -> BatchedCommitProcessor:
    """
    Factory function to create batched commit processor.
    
    Args:
        job_processor: Main JobProcessor instance
        batch_size: Commits per batch (default: 10)
        max_concurrent_per_batch: Max parallel within batch (default: 10)
    
    Returns:
        BatchedCommitProcessor instance
    """
    return BatchedCommitProcessor(
        job_processor=job_processor,
        batch_size=batch_size,
        max_concurrent_per_batch=max_concurrent_per_batch
    )

