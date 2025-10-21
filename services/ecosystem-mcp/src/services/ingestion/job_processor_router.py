"""
Job Processor Router

Routes ingestion jobs to the appropriate processor based on mode:
- 'snapshot': Routes to SnapshotProcessor (fast, no Git history)
- 'git_history': Routes to JobProcessor (complete, with Git history)
"""

import logging
from pathlib import Path
from typing import Dict
from ...storage.db_models import IngestionJobModel
from .snapshot_processor import get_snapshot_processor
from .job_processor import JobProcessor

logger = logging.getLogger(__name__)


class JobProcessorRouter:
    """
    Routes ingestion jobs to correct processor based on mode.
    
    Supports:
    - snapshot: Fast mode (10-100× faster)
    - git_history: Complete mode with full Git history
    """
    
    @staticmethod
    async def process(job: IngestionJobModel) -> Dict:
        """
        Process an ingestion job using the appropriate processor.
        
        Args:
            job: Ingestion job model
            
        Returns:
            Processing result dictionary
        """
        mode = job.mode
        repo_path = Path(job.repo_path)
        job_id = str(job.id)
        
        logger.info(
            f"🔀 Routing ingestion job: "
            f"job_id={job_id}, mode={mode}, repo_path={repo_path}"
        )
        
        if mode == 'snapshot':
            # Route to snapshot processor (fast)
            logger.info(f"📸 Using SnapshotProcessor (fast mode)")
            processor = get_snapshot_processor(repo_path, job_id)
            result = await processor.process()
            
            logger.info(
                f"✅ Snapshot mode complete: "
                f"{result.get('processed', 0)} files processed "
                f"in {result.get('elapsed_seconds', 0):.1f}s"
            )
            return result
            
        elif mode == 'git_history':
            # Route to standard job processor (complete)
            logger.info(f"📚 Using JobProcessor (git_history mode)")
            processor = JobProcessor(job)
            result = await processor.process()
            
            logger.info(
                f"✅ Git history mode complete: "
                f"{result.get('processed_documents', 0)} documents processed"
            )
            return result
            
        else:
            # Unknown mode
            error_msg = f"Unknown ingestion mode: {mode}. Expected 'snapshot' or 'git_history'"
            logger.error(f"❌ {error_msg}")
            raise ValueError(error_msg)


# Convenience function
async def route_and_process_job(job: IngestionJobModel) -> Dict:
    """
    Route and process an ingestion job.
    
    Args:
        job: Ingestion job model
        
    Returns:
        Processing result dictionary
    """
    router = JobProcessorRouter()
    return await router.process(job)

