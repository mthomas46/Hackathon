"""
Documentation Generation Worker

Automatically processes pending documentation runs in the background.
Similar to the ingestion worker but for documentation generation.
"""

import asyncio
import logging
from typing import Optional
from datetime import datetime, timedelta

from ...storage import get_database
from ...storage.models_documentation import DocumentationRunModel
from .adaptive_orchestrator import AdaptiveDocumentationOrchestrator
from sqlalchemy import select, and_

logger = logging.getLogger(__name__)


class DocumentationWorker:
    """
    Background worker that processes pending documentation runs.
    
    Features:
    - Polls for pending runs every 5 seconds
    - Processes runs in order (oldest first)
    - Updates status as it processes
    - Handles errors gracefully
    - Single-threaded (processes one at a time)
    """
    
    def __init__(self, poll_interval: int = 5):
        """
        Initialize documentation worker.
        
        Args:
            poll_interval: Seconds between polling for pending runs
        """
        self.poll_interval = poll_interval
        self.running = False
        self.orchestrator = AdaptiveDocumentationOrchestrator()
        logger.info(f"DocumentationWorker initialized (poll interval: {poll_interval}s)")
    
    async def start(self):
        """Start the worker (runs indefinitely)."""
        self.running = True
        logger.info("🚀 Documentation worker starting...")
        
        while self.running:
            try:
                # Get next pending run
                run = await self._get_next_pending_run()
                
                if run:
                    logger.info(f"📚 Processing documentation run: {run.id}")
                    await self._process_run(run)
                else:
                    # No pending runs, wait before checking again
                    await asyncio.sleep(self.poll_interval)
            
            except Exception as e:
                logger.error(f"❌ Worker error: {e}", exc_info=True)
                # Wait before retrying
                await asyncio.sleep(self.poll_interval)
    
    async def stop(self):
        """Stop the worker gracefully."""
        logger.info("⏸️  Stopping documentation worker...")
        self.running = False
    
    async def _get_next_pending_run(self) -> Optional[DocumentationRunModel]:
        """
        Get the oldest pending run that hasn't been processed.
        
        Returns:
            Next run to process, or None if no pending runs
        """
        try:
            db = get_database()
            async with db.session() as session:
                # Query for oldest pending run
                # Also check for runs stuck in "running" for > 30 minutes (failed worker)
                thirty_minutes_ago = datetime.utcnow() - timedelta(minutes=30)
                
                query = select(DocumentationRunModel).filter(
                    and_(
                        DocumentationRunModel.status.in_(['pending', 'running']),
                        # Either pending OR running but stuck
                        (DocumentationRunModel.status == 'pending') | 
                        (
                            and_(
                                DocumentationRunModel.status == 'running',
                                DocumentationRunModel.started_at < thirty_minutes_ago
                            )
                        )
                    )
                ).order_by(DocumentationRunModel.started_at).limit(1)
                
                result = await session.execute(query)
                run = result.scalar_one_or_none()
                
                if run:
                    logger.info(f"📋 Found pending run: {run.id} (age: {(datetime.utcnow() - run.started_at).total_seconds():.0f}s)")
                
                return run
        
        except Exception as e:
            logger.error(f"Failed to get next pending run: {e}", exc_info=True)
            return None
    
    async def _process_run(self, run: DocumentationRunModel):
        """
        Process a documentation run.
        
        Args:
            run: Run to process
        """
        run_id = str(run.id)
        
        try:
            # Update status to running
            await self._update_run_status(run_id, "running")
            
            # Extract config
            config = run.config or {}
            
            # ✅ ENSURE TRANSPARENCY MODE IS SET (for prompt disclosure)
            if "transparency_mode" not in config:
                config["transparency_mode"] = "normal"  # Show prompts when insufficient info
            
            logger.info(f"Config with transparency: {config}")
            
            # Determine template and service name
            # For now, we'll use metadata if available
            # Note: run.metadata might be SQLAlchemy MetaData or dict
            try:
                if hasattr(run, 'metadata') and isinstance(run.metadata, dict):
                    metadata = run.metadata
                else:
                    # Fallback: try to get metadata column directly
                    metadata = {}
                    if hasattr(run, '__table__'):
                        # It's a model, metadata is the column
                        metadata = getattr(run, 'metadata', None) or {}
                    
                    # If still not a dict, use empty dict
                    if not isinstance(metadata, dict):
                        metadata = {}
            except Exception as e:
                logger.warning(f"Could not access run.metadata: {e}, using defaults")
                metadata = {}
            
            template_name = metadata.get("template_name", "api_reference") if isinstance(metadata, dict) else "api_reference"
            service_name = metadata.get("service_name", run.repo_id or "unknown") if isinstance(metadata, dict) else (run.repo_id or "unknown")
            category = metadata.get("category", "backend") if isinstance(metadata, dict) else "backend"
            
            logger.info(
                f"Generating documentation: "
                f"service={service_name}, template={template_name}, category={category}"
            )
            
            # Generate documentation with timeout
            import asyncio
            try:
                # 5 minute timeout for generation
                async with asyncio.timeout(300):
                    result = await self.orchestrator.generate_adaptive_documentation(
                        service_name=service_name,
                        template_name=template_name,
                        category=category,
                        config=config,
                        run_id=run_id  # Pass existing run_id!
                    )
            except asyncio.TimeoutError:
                logger.error(f"⏱️  Documentation generation timed out after 5 minutes for run {run_id}")
                raise TimeoutError("Documentation generation exceeded 5 minute timeout")
            
            # Update run with results
            await self._update_run_completion(
                run_id=run_id,
                status="completed",
                sections_generated=result.get("sections_generated", 0),
                total_words=result.get("total_words", 0)
            )
            
            logger.info(f"✅ Documentation run {run_id} completed successfully")
        
        except Exception as e:
            logger.error(f"❌ Failed to process run {run_id}: {e}", exc_info=True)
            
            # Update run as failed
            await self._update_run_status(run_id, "failed", error_message=str(e))
    
    async def _update_run_status(
        self,
        run_id: str,
        status: str,
        error_message: Optional[str] = None
    ):
        """Update run status in database."""
        try:
            db = get_database()
            async with db.session() as session:
                query = select(DocumentationRunModel).filter(
                    DocumentationRunModel.id == run_id
                )
                result = await session.execute(query)
                run = result.scalar_one_or_none()
                
                if run:
                    run.status = status
                    if error_message:
                        # Log error (error_details column doesn't exist in model)
                        logger.error(f"Run {run_id} error: {error_message}")
                    if status == "running" and not run.started_at:
                        run.started_at = datetime.utcnow()
                    elif status in ["completed", "failed", "cancelled"]:
                        run.completed_at = datetime.utcnow()
                    
                    await session.commit()
                    logger.info(f"Updated run {run_id} status: {status}")
        
        except Exception as e:
            logger.error(f"Failed to update run status: {e}", exc_info=True)
    
    async def _update_run_completion(
        self,
        run_id: str,
        status: str,
        sections_generated: int = 0,
        total_words: int = 0
    ):
        """Update run with completion details."""
        try:
            db = get_database()
            async with db.session() as session:
                query = select(DocumentationRunModel).filter(
                    DocumentationRunModel.id == run_id
                )
                result = await session.execute(query)
                run = result.scalar_one_or_none()
                
                if run:
                    run.status = status
                    run.completed_at = datetime.utcnow()
                    run.passes_completed = run.total_passes  # Mark as complete
                    run.total_artifacts = sections_generated
                    run.total_words = total_words
                    
                    await session.commit()
                    logger.info(
                        f"Run {run_id} completed: "
                        f"{sections_generated} sections, {total_words} words"
                    )
        
        except Exception as e:
            logger.error(f"Failed to update run completion: {e}", exc_info=True)


# Singleton instance
_worker_instance: Optional[DocumentationWorker] = None


def get_documentation_worker() -> DocumentationWorker:
    """Get or create the documentation worker singleton."""
    global _worker_instance
    if _worker_instance is None:
        _worker_instance = DocumentationWorker()
    return _worker_instance


async def start_documentation_worker():
    """Start the documentation worker (call on app startup)."""
    worker = get_documentation_worker()
    logger.info("Starting documentation worker task...")
    asyncio.create_task(worker.start())

