"""
Job Processor

Orchestrates the document ingestion pipeline for a single job.
Coordinates Git extraction, document normalization, embedding generation,
and storage operations.
"""

import logging
from typing import Dict, Any, List
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
    
    def __init__(self):
        """Initialize the job processor."""
        self.git_service = None  # Initialized per job
        self.normalizer_factory = NormalizerFactory()
        self.embedding_service = EmbeddingService()
        logger.info("JobProcessor initialized")
    
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
                if current_job.job_metadata is None:
                    current_job.job_metadata = {}
                
                current_job.job_metadata["last_processed_file"] = last_file
                current_job.job_metadata["current_commit"] = current_commit
                current_job.job_metadata["last_update"] = datetime.utcnow().isoformat()
                current_job.job_metadata["current_file_index"] = current_file_index
                current_job.job_metadata["total_files_in_commit"] = total_files
                current_job.job_metadata["progress_pct"] = round((current_file_index / total_files * 100) if total_files > 0 else 0, 1)
                
                # Update counters
                current_job.processed_documents = processed
                current_job.skipped_documents = skipped
                current_job.failed_documents = failed
                
                await repo.update(current_job)
                await session.commit()
                
                logger.debug(f"Updated job progress: {current_file_index}/{total_files} files ({current_job.job_metadata['progress_pct']}%)")
                
        except Exception as e:
            # Don't fail the job if metadata update fails
            logger.warning(f"Failed to update job progress metadata: {e}")
    
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
            self.git_service = GitService(repo_path=job.repo_path)
            
            # Get commits based on mode
            commits = await self._get_commits_for_mode(job.mode)
            
            if not commits:
                result["error"] = "No commits found"
                return result
            
            logger.info(f"Found {len(commits)} commits to process")
            
            # Process each commit
            for i, commit in enumerate(commits, 1):
                logger.info(f"Processing commit {i}/{len(commits)}: {commit.sha[:8]}")
                
                commit_result = await self._process_commit(commit, job)
                
                result["processed_documents"] += commit_result["processed"]
                result["failed_documents"] += commit_result["failed"]
                result["skipped_documents"] += commit_result.get("skipped", 0)  # NEW
                result["embeddings_generated"] += commit_result["embeddings"]
                result["total_cost_usd"] += commit_result["cost"]
            
            result["total_documents"] = result["processed_documents"] + result["failed_documents"] + result["skipped_documents"]
            result["success"] = True
            
            logger.info(
                f"✅ Job {job.id} processing complete: "
                f"{result['processed_documents']}/{result['total_documents']} documents, "
                f"{result['skipped_documents']} skipped, "
                f"{result['embeddings_generated']} embeddings"
            )
        
        except Exception as e:
            logger.error(f"Error processing job {job.id}: {e}", exc_info=True)
            result["error"] = str(e)
        
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
            # Get target_subdirectory from job metadata if specified
            target_subdirectory = job.job_metadata.get('target_subdirectory') if job.job_metadata else None
            
            # Get files changed in this commit (filtered by subdirectory if specified)
            files = await self.git_service.get_commit_files(commit.sha, target_subdirectory)
            
            if not files:
                return result
            
            # Filter files (only documentation and code)
            filtered_files = self._filter_files(files)
            
            logger.info(f"Commit {commit.sha[:8]}: {len(filtered_files)}/{len(files)} files to process")
            
            # Process each file
            for idx, file_change in enumerate(filtered_files):
                # Get file path for logging
                file_path_str = file_change if isinstance(file_change, str) else file_change.path
                
                # Log every file being processed (INFO level so it appears in logs)
                logger.info(f"📄 Processing [{idx+1}/{len(filtered_files)}]: {file_path_str}")
                
                file_result = await self._process_file(
                    file_change=file_change,
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
                if (idx + 1) % 5 == 0 or idx == len(filtered_files) - 1:
                    await self._update_job_progress(
                        job=job,
                        last_file=file_path_str,
                        current_commit=commit.sha[:8],
                        processed=result["processed"],
                        skipped=result["skipped"],
                        failed=result["failed"],
                        current_file_index=idx + 1,
                        total_files=len(filtered_files)
                    )
        
        except Exception as e:
            logger.error(f"Error processing commit {commit.sha}: {e}", exc_info=True)
        
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

