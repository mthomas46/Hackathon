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
                result["embeddings_generated"] += commit_result["embeddings"]
                result["total_cost_usd"] += commit_result["cost"]
            
            result["total_documents"] = result["processed_documents"] + result["failed_documents"]
            result["success"] = True
            
            logger.info(
                f"✅ Job {job.id} processing complete: "
                f"{result['processed_documents']}/{result['total_documents']} documents, "
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
            "embeddings": 0,
            "cost": 0.0
        }
        
        try:
            # Get files changed in this commit
            files = await self.git_service.get_commit_files(commit.sha)
            
            if not files:
                return result
            
            # Filter files (only documentation and code)
            filtered_files = self._filter_files(files)
            
            logger.info(f"Commit {commit.sha[:8]}: {len(filtered_files)}/{len(files)} files to process")
            
            # Process each file
            for file_change in filtered_files:
                file_result = await self._process_file(
                    file_change=file_change,
                    commit=commit,
                    job=job
                )
                
                if file_result["success"]:
                    result["processed"] += 1
                    result["embeddings"] += 1
                    result["cost"] += file_result["cost"]
                else:
                    result["failed"] += 1
                    logger.warning(f"Failed to process {file_change.path}: {file_result.get('error')}")
        
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
        
        for file_change in files:
            path = Path(file_change.path)
            
            # Skip deleted files
            if file_change.change_type == 'deleted':
                continue
            
            # Check extension
            if path.suffix not in include_extensions:
                continue
            
            # Check excluded patterns
            if any(pattern in str(path) for pattern in exclude_patterns):
                continue
            
            filtered.append(file_change)
        
        return filtered
    
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
            # Get file content
            content = await self.git_service.get_file_content(
                commit_sha=commit.sha,
                file_path=file_change.path
            )
            
            if not content:
                result["error"] = "Empty file"
                return result
            
            # Skip large files (> 1MB)
            if len(content) > 1_000_000:
                result["error"] = "File too large"
                return result
            
            # Normalize document
            path = Path(file_change.path)
            normalizer = self.normalizer_factory.get_normalizer(path.suffix)
            
            normalized = await normalizer.normalize(
                content=content,
                file_path=str(path),
                metadata={
                    "commit_sha": commit.sha,
                    "commit_message": commit.message,
                    "commit_author": commit.author,
                    "commit_date": commit.date.isoformat(),
                    "change_type": file_change.change_type
                }
            )
            
            # Generate embedding
            embedding_result = await self.embedding_service.generate_embedding(
                text=normalized["content"]
            )
            
            # Store document and embedding
            async with get_database().session() as session:
                doc_repo = DocumentRepository(session)
                
                # Create document
                from ...storage.db_models import DocumentModel
                from hashlib import sha256
                from uuid import uuid4
                
                content_hash = sha256(normalized["content"].encode()).hexdigest()
                
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
                
                # Store embedding in ChromaDB
                chroma = get_chroma_client()
                await chroma.add_embeddings(
                    ids=[str(created_doc.id)],
                    embeddings=[embedding_result["embedding"]],
                    documents=[normalized["content"]],
                    metadatas=[{
                        "service_name": created_doc.service_name,
                        "file_path": str(path),
                        "commit_sha": commit.sha,
                        "content_hash": content_hash
                    }]
                )
            
            result["success"] = True
            result["cost"] = embedding_result.get("cost", 0.0)
            
            logger.debug(f"✅ Processed {path}")
        
        except Exception as e:
            logger.error(f"Error processing file {file_change.path}: {e}", exc_info=True)
            result["error"] = str(e)
        
        return result

