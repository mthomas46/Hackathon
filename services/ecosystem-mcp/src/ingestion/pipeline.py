"""
Main ingestion pipeline orchestrator.

Coordinates scanning, parsing, normalizing, and storing documents.
"""

import asyncio
import hashlib
import logging
from pathlib import Path
from typing import Optional
from uuid import UUID
from datetime import datetime

from ..config import settings
from ..models import IngestionMode, IngestionStatus, IngestionJob, IngestionResult
from ..storage import get_database
from ..storage.repositories import DocumentRepository
from ..utils import get_redis_client
from ..utils.logging_config import OperationLogger, log_checkpoint, log_metric, create_progress
from .scanner import DocumentScanner
from .parser import DocumentParser
from .normalizer import DocumentNormalizer
from .metadata_extractor import MetadataExtractor

logger = logging.getLogger(__name__)


class IngestionPipeline:
    """
    Complete document ingestion pipeline.
    
    Orchestrates:
    1. Scanning for files
    2. Queueing documents
    3. Parallel processing
    4. Embedding generation
    5. Storage
    """
    
    def __init__(self):
        """Initialize ingestion pipeline."""
        self.scanner = None  # Initialized per job
        self.parser = DocumentParser()
        self.normalizer = DocumentNormalizer()
        self.metadata_extractor = MetadataExtractor()
        self.redis = get_redis_client()
        self.db = get_database()
        
        logger.info("Ingestion pipeline initialized")
    
    async def ingest_mode_1(
        self,
        repo_path: Optional[str] = None
    ) -> IngestionResult:
        """
        Mode 1: Quick ingestion (current .md only).
        
        Duration: ~1-2 minutes
        Files: ~100-200 .md files
        Cost: ~$0.10-0.20
        
        Args:
            repo_path: Repository path (uses settings if None)
        
        Returns:
            Ingestion result
        """
        repo_path = repo_path or str(settings.git_repo_path)
        logger.info(f"Starting Mode 1 ingestion: {repo_path}")
        
        # Create job
        job = await self._create_job(IngestionMode.QUICK)
        
        try:
            # Scan for markdown files
            self.scanner = DocumentScanner(repo_path)
            files = self.scanner.scan_markdown_only()
            
            logger.info(f"Found {len(files)} markdown files")
            
            # Update job with total
            await self._update_job_total(job.id, len(files))
            
            # Queue documents
            for file_path in files:
                await self._queue_document(file_path, job.id)
            
            # Process queue
            result = await self._process_queue(job.id)
            
            # Complete job
            await self._complete_job(job.id, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Mode 1 ingestion failed: {e}")
            await self._fail_job(job.id, str(e))
            raise
    
    async def ingest_mode_2(
        self,
        repo_path: Optional[str] = None
    ) -> IngestionResult:
        """
        Mode 2: Standard ingestion (current code + .md).
        
        Duration: ~5-10 minutes
        Files: All current files
        Cost: ~$0.50-1.00
        
        Args:
            repo_path: Repository path (uses settings if None)
        
        Returns:
            Ingestion result
        """
        repo_path = repo_path or str(settings.git_repo_path)
        logger.info(f"Starting Mode 2 ingestion: {repo_path}")
        
        # Create job
        job = await self._create_job(IngestionMode.STANDARD)
        
        try:
            # Scan for all supported files
            self.scanner = DocumentScanner(repo_path)
            files = self.scanner.scan_all_supported()
            
            logger.info(f"Found {len(files)} files")
            
            # Update job with total
            await self._update_job_total(job.id, len(files))
            
            # Queue documents
            for file_path in files:
                await self._queue_document(file_path, job.id)
            
            # Process queue
            result = await self._process_queue(job.id)
            
            # Complete job
            await self._complete_job(job.id, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Mode 2 ingestion failed: {e}")
            await self._fail_job(job.id, str(e))
            raise
    
    async def ingest_mode_3(
        self,
        repo_path: Optional[str] = None
    ) -> IngestionResult:
        """
        Mode 3: Historical docs (current + .md history).
        
        Duration: ~15-30 minutes
        Files: Current + all .md versions
        Cost: ~$2-5
        
        Args:
            repo_path: Repository path (uses settings if None)
        
        Returns:
            Ingestion result
        """
        repo_path = repo_path or str(settings.git_repo_path)
        logger.info(f"Starting Mode 3 ingestion: {repo_path}")
        
        # Create job
        job = await self._create_job(IngestionMode.HISTORICAL)
        
        try:
            # Step 1: Ingest all current files (Mode 2)
            logger.info("Step 1/2: Ingesting current files")
            await self.ingest_mode_2(repo_path)
            
            # Step 2: Get history of all .md files
            logger.info("Step 2/2: Processing .md file history")
            from ..services.git import get_git_service
            git_service = get_git_service()
            
            self.scanner = DocumentScanner(repo_path)
            md_files = self.scanner.scan_markdown_only()
            
            total_versions = 0
            for md_file in md_files:
                # Get history for this file
                file_path_str = self.scanner.get_relative_path(md_file)
                history = await git_service.get_file_history(file_path_str, max_commits=50)
                
                total_versions += len(history)
                
                # Queue each historical version
                for commit in history:
                    await self.redis.add_to_stream(
                        self.redis.INGESTION_STREAM,
                        {
                            "job_id": str(job.id),
                            "file_path": str(md_file),
                            "git_commit_sha": commit.sha,
                            "is_historical": "true"
                        }
                    )
            
            logger.info(f"Queued {total_versions} historical versions")
            
            # Process queue
            result = await self._process_queue(job.id)
            
            # Complete job
            await self._complete_job(job.id, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Mode 3 ingestion failed: {e}")
            await self._fail_job(job.id, str(e))
            raise
    
    async def ingest_mode_4(
        self,
        repo_path: Optional[str] = None
    ) -> IngestionResult:
        """
        Mode 4: Full history (everything).
        
        Duration: ~1-3 hours
        Files: Complete git history
        Cost: ~$10-50
        
        ⚠️ WARNING: Only run once, then use incremental!
        
        Args:
            repo_path: Repository path (uses settings if None)
        
        Returns:
            Ingestion result
        """
        repo_path = repo_path or str(settings.git_repo_path)
        logger.info(f"Starting Mode 4 ingestion (FULL HISTORY): {repo_path}")
        
        # Create job
        job = await self._create_job(IngestionMode.FULL)
        
        try:
            from ..services.git import get_git_service
            git_service = get_git_service()
            
            # Get all commits
            logger.info("Step 1/3: Analyzing git history...")
            commits = await git_service.get_all_commits(max_count=1000)  # Limit for safety
            logger.info(f"Found {len(commits)} commits")
            
            # Process commits in chronological order (oldest first)
            logger.info("Step 2/3: Processing commits...")
            commits.reverse()  # Oldest first
            
            processed_files = set()
            
            for i, commit in enumerate(commits):
                if i % 10 == 0:
                    logger.info(f"Processing commit {i+1}/{len(commits)}")
                
                # Get files at this commit
                files = await git_service.get_files_at_commit(commit.sha)
                
                # Filter for supported types
                supported_extensions = {".md", ".py", ".yaml", ".yml", ".json", ".txt"}
                for file_path in files:
                    ext = Path(file_path).suffix.lower()
                    if ext in supported_extensions:
                        # Queue this file at this commit
                        file_commit_key = f"{file_path}:{commit.sha}"
                        if file_commit_key not in processed_files:
                            await self.redis.add_to_stream(
                                self.redis.INGESTION_STREAM,
                                {
                                    "job_id": str(job.id),
                                    "file_path": file_path,
                                    "git_commit_sha": commit.sha,
                                    "is_historical": "true"
                                }
                            )
                            processed_files.add(file_commit_key)
            
            logger.info(f"Queued {len(processed_files)} file versions")
            
            # Process queue
            logger.info("Step 3/3: Processing documents...")
            result = await self._process_queue(job.id)
            
            # Complete job
            await self._complete_job(job.id, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Mode 4 ingestion failed: {e}")
            await self._fail_job(job.id, str(e))
            raise
    
    async def _create_job(self, mode: IngestionMode) -> IngestionJob:
        """Create ingestion job record."""
        # Persist to database
        async with self.db.session() as session:
            from ..storage.repositories import IngestionJobRepository
            repo = IngestionJobRepository(session)
            
            job_model = await repo.create_job(
                mode=mode.value,
                status="running"
            )
            await session.commit()
            
            # Convert to domain model
            job = IngestionJob(
                id=job_model.id,
                mode=mode,
                status=IngestionStatus.RUNNING
            )
            
            logger.info(f"Created ingestion job: {job.id}")
            return job
    
    async def _update_job_total(self, job_id: UUID, total: int):
        """Update job with total document count."""
        # Persist to database
        async with self.db.session() as session:
            from ..storage.repositories import IngestionJobRepository
            repo = IngestionJobRepository(session)
            
            await repo.update_total(job_id, total)
            await session.commit()
            
            logger.info(f"Job {job_id}: {total} documents to process")
    
    async def _queue_document(self, file_path: Path, job_id: UUID):
        """Queue document for processing."""
        await self.redis.add_to_stream(
            self.redis.INGESTION_STREAM,
            {
                "job_id": str(job_id),
                "file_path": str(file_path),
                "queued_at": datetime.utcnow().isoformat()
            }
        )
    
    async def _process_queue(self, job_id: UUID) -> IngestionResult:
        """
        Process documents from queue.
        
        Uses multiple workers for parallel processing.
        """
        # Start workers
        num_workers = min(settings.max_workers, 8)
        logger.info(f"Starting {num_workers} workers")
        
        workers = [
            self._worker(worker_id=i, job_id=job_id)
            for i in range(num_workers)
        ]
        
        # Wait for all workers to complete
        await asyncio.gather(*workers)
        
        # Get statistics from database
        async with self.db.session() as session:
            from ..storage.repositories import IngestionJobRepository
            repo = IngestionJobRepository(session)
            
            job_model = await repo.get_by_id(job_id)
            if not job_model:
                raise ValueError(f"Job {job_id} not found in database")
            
            # Calculate duration
            duration = (datetime.utcnow() - job_model.started_at).total_seconds()
            
            result = IngestionResult(
                job_id=job_id,
                mode=IngestionMode(job_model.mode),
                success=job_model.status == "completed",
                documents_processed=job_model.processed_documents,
                documents_failed=job_model.failed_documents,
                embeddings_generated=job_model.embeddings_generated,
                total_cost_usd=job_model.total_cost_usd,
                duration_seconds=duration,
                summary=job_model.error_message or "Ingestion complete"
            )
            
            return result
    
    async def _worker(self, worker_id: int, job_id: UUID):
        """
        Worker process for document ingestion.
        
        Reads from Redis queue and processes documents.
        """
        worker_name = f"worker-{worker_id}"
        logger.info(f"{worker_name} started")
        
        processed = 0
        
        while True:
            # Read from queue
            messages = await self.redis.read_from_stream(
                self.redis.INGESTION_STREAM,
                consumer_name=worker_name,
                count=1,
                block=1000
            )
            
            if not messages:
                # Queue empty, done
                break
            
            for message_id, data in messages:
                try:
                    # Process document
                    await self._process_document(data, job_id)
                    
                    # Acknowledge
                    await self.redis.ack_message(
                        self.redis.INGESTION_STREAM,
                        message_id
                    )
                    
                    processed += 1
                    
                except Exception as e:
                    logger.error(f"{worker_name} error processing document: {e}")
                    
                    # Update failure count in database
                    async with self.db.session() as session:
                        from ..storage.repositories import IngestionJobRepository
                        repo = IngestionJobRepository(session)
                        await repo.increment_failed(job_id)
                        await session.commit()
                    
                    # Move to DLQ after max retries
                    await self.redis.move_to_dlq(
                        self.redis.INGESTION_STREAM,
                        message_id,
                        data,
                        str(e)
                    )
        
        logger.info(f"{worker_name} completed: {processed} documents")
    
    async def _process_document(self, data: dict, job_id: UUID):
        """
        Process a single document.
        
        1. Parse file
        2. Normalize to markdown
        3. Extract metadata
        4. Calculate hash
        5. Store in database
        6. Queue for embedding
        7. Update job progress
        """
        file_path = Path(data["file_path"])
        
        # Parse
        parsed = self.parser.parse(file_path)
        
        # Normalize
        normalized = self.normalizer.normalize(parsed)
        
        # Extract metadata
        service_name = self.scanner.extract_service_name(file_path)
        metadata = self.metadata_extractor.extract(
            file_path=file_path,
            content=parsed["content"],
            normalized_content=normalized,
            parsed_metadata=parsed.get("metadata", {}),
            service_name=service_name
        )
        
        # Calculate content hash
        content_hash = hashlib.sha256(
            parsed["content"].encode()
        ).hexdigest()
        
        # Store in database
        async with self.db.session() as session:
            repo = DocumentRepository(session)
            
            # Check if already exists
            existing = await repo.get_by_content_hash(content_hash)
            if existing:
                logger.debug(f"Document already exists: {file_path}")
                return
            
            # Create document
            doc = await repo.create(
                service_name=service_name,
                file_path=self.scanner.get_relative_path(file_path),
                original_format=parsed["format"],
                original_content=parsed["content"],
                normalized_content=normalized,
                content_hash=content_hash,
                metadata=metadata.model_dump()
            )
            
            await session.commit()
            
            logger.info(f"Stored document: {file_path}")
            
            # Update job progress
            async with self.db.session() as session:
                from ..storage.repositories import IngestionJobRepository
                repo = IngestionJobRepository(session)
                await repo.increment_processed(job_id)
                await session.commit()
            
            # Queue for embedding
            await self.redis.add_to_stream(
                self.redis.EMBEDDING_STREAM,
                {
                    "document_id": str(doc.id),
                    "content": normalized[:5000],  # Limit size in queue
                    "service_name": service_name
                }
            )
    
    async def _complete_job(self, job_id: UUID, result: IngestionResult):
        """Mark job as complete."""
        # Persist to database
        async with self.db.session() as session:
            from ..storage.repositories import IngestionJobRepository
            repo = IngestionJobRepository(session)
            
            await repo.complete_job(
                job_id=job_id,
                total_cost=result.total_cost_usd,
                summary=result.summary
            )
            
            logger.info(f"Job {job_id} completed successfully")
    
    async def _fail_job(self, job_id: UUID, error: str):
        """Mark job as failed."""
        # Persist to database
        async with self.db.session() as session:
            from ..storage.repositories import IngestionJobRepository
            repo = IngestionJobRepository(session)
            
            await repo.fail_job(job_id=job_id, error=error)
            
            logger.error(f"Job {job_id} failed: {error}")

