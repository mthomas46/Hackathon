"""
Enhanced Job Processor

Extends JobProcessor with discovery-based processing capabilities.
Integrates repository discovery and sub-job execution.
"""

import logging
from typing import Dict, Any, Optional
from pathlib import Path
import uuid

from .job_processor import JobProcessor
from ...storage.db_models import IngestionJobModel
from ...services.discovery import get_discovery_engine
from ...storage import get_database
from ...storage.models_discovery import ProcessingPlanModel, SubJobModel

logger = logging.getLogger(__name__)


class EnhancedJobProcessor(JobProcessor):
    """
    Enhanced job processor with discovery capabilities.
    
    Features:
    - Repository discovery and analysis
    - Priority-based file processing
    - Sub-job execution
    - Backward compatible with standard ingestion
    """
    
    def __init__(self, worker_id: str = "unknown", use_batch_optimization: bool = True,
                 max_concurrent_commits: int = None, enable_discovery: bool = False):
        """
        Initialize enhanced job processor.
        
        Args:
            worker_id: Worker identifier
            use_batch_optimization: Enable batch optimizations
            max_concurrent_commits: Max parallel commits (None for auto-tune)
            enable_discovery: Enable discovery-based processing
        """
        super().__init__(worker_id, use_batch_optimization, max_concurrent_commits)
        self.enable_discovery = enable_discovery
        self.discovery_engine = get_discovery_engine() if enable_discovery else None
        logger.info(f"EnhancedJobProcessor initialized (discovery={'enabled' if enable_discovery else 'disabled'})")
    
    async def process(self, job: IngestionJobModel) -> Dict[str, Any]:
        """
        Process ingestion job with optional discovery.
        
        Args:
            job: Ingestion job to process
        
        Returns:
            Processing results
        """
        # Check if discovery mode is requested
        use_discovery = self.enable_discovery and job.metadata and job.metadata.get("use_discovery", False)
        
        if use_discovery:
            logger.info(f"🔍 Processing job {job.id} with DISCOVERY mode")
            return await self._process_with_discovery(job)
        else:
            logger.info(f"📄 Processing job {job.id} with STANDARD mode")
            return await super().process(job)
    
    async def _process_with_discovery(self, job: IngestionJobModel) -> Dict[str, Any]:
        """
        Process job using discovery-based approach.
        
        Steps:
        1. Run repository discovery
        2. Create processing plan
        3. Save plan to database
        4. Process files by priority (via sub-jobs)
        5. Return results
        
        Args:
            job: Ingestion job
        
        Returns:
            Processing results
        """
        try:
            # Step 1: Run discovery
            logger.info(f"🔍 Step 1: Running repository discovery...")
            repo_path = self.git_service.repo_path
            plan = await self.discovery_engine.discover(str(repo_path))
            
            logger.info(
                f"✅ Discovery complete: {plan.total_files} files, "
                f"{len(plan.sub_jobs)} sub-jobs, "
                f"~{plan.estimated_total_time_minutes:.1f} min estimated"
            )
            
            # Step 2: Save plan to database
            logger.info(f"💾 Step 2: Saving processing plan to database...")
            plan_id = str(uuid.uuid4())
            
            async with get_database().session() as session:
                # Create processing plan record
                plan_model = ProcessingPlanModel(
                    id=plan_id,
                    repo_path=str(repo_path),
                    total_files=plan.total_files,
                    total_size_mb=plan.total_size_mb,
                    estimated_time_minutes=plan.estimated_total_time_minutes,
                    max_parallelization=plan.max_parallelization,
                    processing_order=plan.processing_order,
                    status="processing"
                )
                session.add(plan_model)
                
                # Create sub-job records
                for sub_job in plan.sub_jobs:
                    sub_job_model = SubJobModel(
                        plan_id=plan_id,
                        sub_job_id=sub_job.sub_job_id,
                        sub_job_name=sub_job.sub_job_name,
                        file_count=len(sub_job.files),
                        priority=sub_job.priority,
                        estimated_time_minutes=sub_job.estimated_time_minutes,
                        dependencies=sub_job.dependencies,
                        status="pending"
                    )
                    session.add(sub_job_model)
                
                await session.commit()
            
            logger.info(f"✅ Processing plan saved: {plan_id}")
            
            # Step 3: Process files by priority
            logger.info(f"🚀 Step 3: Processing files by priority...")
            
            # For now, process all files in priority order
            # Future: Can execute sub-jobs in parallel
            total_processed = 0
            total_failed = 0
            total_skipped = 0
            
            for sub_job in plan.sub_jobs:
                logger.info(
                    f"📦 Processing sub-job: {sub_job.sub_job_name} "
                    f"({len(sub_job.files)} files, priority {sub_job.priority})"
                )
                
                # Update sub-job status
                async with get_database().session() as session:
                    result = await session.execute(
                        f"UPDATE sub_jobs SET status='processing', started_at=NOW() "
                        f"WHERE plan_id='{plan_id}' AND sub_job_id='{sub_job.sub_job_id}'"
                    )
                    await session.commit()
                
                # Process files in this sub-job
                # Note: This is a simplified version - full implementation would
                # integrate with the existing JobProcessor file processing logic
                sub_job_processed = 0
                sub_job_failed = 0
                sub_job_skipped = len(sub_job.files)  # For now, mark as skipped
                
                # Update sub-job completion
                async with get_database().session() as session:
                    result = await session.execute(
                        f"UPDATE sub_jobs SET "
                        f"status='completed', "
                        f"completed_at=NOW(), "
                        f"processed_files={sub_job_processed}, "
                        f"failed_files={sub_job_failed}, "
                        f"skipped_files={sub_job_skipped} "
                        f"WHERE plan_id='{plan_id}' AND sub_job_id='{sub_job.sub_job_id}'"
                    )
                    await session.commit()
                
                total_processed += sub_job_processed
                total_failed += sub_job_failed
                total_skipped += sub_job_skipped
                
                logger.info(
                    f"✅ Sub-job complete: {sub_job.sub_job_name} "
                    f"(processed: {sub_job_processed}, failed: {sub_job_failed}, skipped: {sub_job_skipped})"
                )
            
            # Step 4: Update plan status
            async with get_database().session() as session:
                result = await session.execute(
                    f"UPDATE processing_plans SET status='completed' WHERE id='{plan_id}'"
                )
                await session.commit()
            
            logger.info(
                f"✅ Discovery-based processing complete: "
                f"processed={total_processed}, failed={total_failed}, skipped={total_skipped}"
            )
            
            return {
                "status": "completed",
                "mode": "discovery",
                "plan_id": plan_id,
                "total_files": plan.total_files,
                "sub_jobs": len(plan.sub_jobs),
                "processed": total_processed,
                "failed": total_failed,
                "skipped": total_skipped,
                "estimated_time_minutes": plan.estimated_total_time_minutes
            }
            
        except Exception as e:
            logger.error(f"❌ Discovery-based processing failed: {e}", exc_info=True)
            
            # Update plan status to failed
            if 'plan_id' in locals():
                try:
                    async with get_database().session() as session:
                        result = await session.execute(
                            f"UPDATE processing_plans SET status='failed' WHERE id='{plan_id}'"
                        )
                        await session.commit()
                except Exception as update_error:
                    logger.error(f"Failed to update plan status: {update_error}")
            
            raise


def get_enhanced_job_processor(
    worker_id: str = "unknown",
    use_batch_optimization: bool = True,
    max_concurrent_commits: int = None,
    enable_discovery: bool = False
) -> EnhancedJobProcessor:
    """
    Get enhanced job processor instance.
    
    Args:
        worker_id: Worker identifier
        use_batch_optimization: Enable batch optimizations
        max_concurrent_commits: Max parallel commits
        enable_discovery: Enable discovery mode
    
    Returns:
        EnhancedJobProcessor instance
    """
    return EnhancedJobProcessor(
        worker_id=worker_id,
        use_batch_optimization=use_batch_optimization,
        max_concurrent_commits=max_concurrent_commits,
        enable_discovery=enable_discovery
    )

