"""
Sub-Job Executor

Executes individual sub-jobs by processing files through the ingestion pipeline.
Integrates with normalization, embedding, and storage services.
"""

import logging
import asyncio
from typing import List, Dict, Optional, Set
from datetime import datetime
from pathlib import Path

from ...storage import get_database
from ...storage.models_discovery import SubJobModel, FileClassificationModel
from ..processing.normalizer_factory import NormalizerFactory
from ..git.git_service import GitService
from ...utils.redis_client import get_redis_client

logger = logging.getLogger(__name__)


class SubJobExecutor:
    """
    Executes sub-jobs by processing files through the ingestion pipeline.
    
    Features:
    - File processing with normalization
    - Embedding generation
    - Database storage
    - Progress tracking
    - Error handling and retry
    - Duplicate detection
    """
    
    def __init__(self):
        self.normalizer_factory = NormalizerFactory()
        self.redis = get_redis_client()
        
        # Embedding service integration
        self.embedding_service_url = None
        self._init_embedding_service()
        
        logger.info("SubJobExecutor initialized")
    
    def _init_embedding_service(self):
        """Initialize embedding service connection."""
        import os
        self.embedding_service_url = os.getenv(
            "EMBEDDING_SERVICE_URL",
            "http://ecosystem-mcp-embedding:8003"
        )
        logger.info(f"Embedding service URL: {self.embedding_service_url}")
    
    async def execute_sub_job(
        self,
        sub_job: SubJobModel,
        repo_path: str,
        progress_callback: Optional[callable] = None,
        dependency_order: Optional[List[str]] = None  # PHASE 10 (Gap #2): Topological order
    ) -> Dict[str, int]:
        """
        Execute a sub-job by processing its files.
        
        Args:
            sub_job: Sub-job to execute
            repo_path: Repository path
            progress_callback: Optional callback for progress updates
            dependency_order: PHASE 10 - Optional topological order for file processing
        
        Returns:
            Dictionary with execution statistics
        """
        logger.info(f"🚀 Executing sub-job {sub_job.sub_job_id}: {sub_job.file_count} files")
        
        stats = {
            "processed": 0,
            "failed": 0,
            "skipped": 0,
            "embeddings_generated": 0
        }
        
        try:
            # Load file classifications for this sub-job
            files = await self._load_sub_job_files(sub_job.id)
            
            if not files:
                logger.warning(f"No files found for sub-job {sub_job.sub_job_id}")
                return stats
            
            # PHASE 10 (Gap #2): Order files by dependencies if provided
            if dependency_order:
                files = self._order_files_by_dependencies(files, dependency_order)
                logger.info(f"   📋 Using dependency-based processing order")
            
            logger.info(f"Processing {len(files)} files for sub-job {sub_job.sub_job_id}")
            
            # Initialize Git manager
            git_manager = GitService(repo_path)
            
            # Process files
            for idx, file_class in enumerate(files):
                try:
                    # Check for duplicates
                    if await self._is_duplicate(file_class.file_path, file_class.content_hash):
                        logger.debug(f"Skipping duplicate: {file_class.file_path}")
                        stats["skipped"] += 1
                        continue
                    
                    # Process file
                    result = await self._process_file(
                        file_class,
                        repo_path,
                        git_manager
                    )
                    
                    if result["success"]:
                        stats["processed"] += 1
                        if result.get("embedding_generated"):
                            stats["embeddings_generated"] += 1
                    else:
                        stats["failed"] += 1
                        logger.warning(f"Failed to process {file_class.file_path}: {result.get('error')}")
                    
                    # Progress callback
                    if progress_callback:
                        await progress_callback(
                            processed=stats["processed"],
                            failed=stats["failed"],
                            skipped=stats["skipped"],
                            total=len(files)
                        )
                    
                    # Log progress every 10 files
                    if (idx + 1) % 10 == 0:
                        logger.info(
                            f"Progress: {idx + 1}/{len(files)} files "
                            f"(processed={stats['processed']}, failed={stats['failed']}, skipped={stats['skipped']})"
                        )
                    
                except Exception as e:
                    logger.error(f"Error processing file {file_class.file_path}: {e}", exc_info=True)
                    stats["failed"] += 1
            
            logger.info(
                f"✅ Sub-job {sub_job.sub_job_id} complete: "
                f"processed={stats['processed']}, failed={stats['failed']}, "
                f"skipped={stats['skipped']}, embeddings={stats['embeddings_generated']}"
            )
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Sub-job execution failed: {e}", exc_info=True)
            raise
    
    async def _load_sub_job_files(self, sub_job_id: str) -> List[FileClassificationModel]:
        """Load file classifications for a sub-job."""
        from sqlalchemy import select
        
        async with get_database().session() as session:
            result = await session.execute(
                select(FileClassificationModel)
                .where(FileClassificationModel.sub_job_id == sub_job_id)
                .order_by(FileClassificationModel.importance_score.desc())
            )
            files = result.scalars().all()
            return list(files)
    
    async def _is_duplicate(self, file_path: str, content_hash: str) -> bool:
        """
        Check if file is a duplicate.
        
        Args:
            file_path: File path
            content_hash: Content hash
        
        Returns:
            True if duplicate, False otherwise
        """
        try:
            from sqlalchemy import select, text
            from ...storage.models import DocumentModel
            
            async with get_database().session() as session:
                # Check by content hash
                result = await session.execute(
                    select(DocumentModel.id)
                    .where(DocumentModel.content_hash == content_hash)
                    .limit(1)
                )
                
                if result.scalar_one_or_none():
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"Error checking duplicate: {e}")
            return False
    
    async def _process_file(
        self,
        file_class: FileClassificationModel,
        repo_path: str,
        git_manager: GitService
    ) -> Dict:
        """
        Process a single file through the ingestion pipeline.
        
        Args:
            file_class: File classification
            repo_path: Repository path
            git_manager: Git manager instance
        
        Returns:
            Processing result dictionary
        """
        try:
            file_path = file_class.file_path
            
            # Read file content
            full_path = Path(repo_path) / file_path
            if not full_path.exists():
                return {"success": False, "error": "File not found"}
            
            content = full_path.read_text(encoding='utf-8', errors='ignore')
            
            # Normalize content
            normalized = await self._normalize_content(
                content=content,
                file_path=file_path,
                file_type=file_class.file_type
            )
            
            if not normalized:
                return {"success": False, "error": "Normalization failed"}
            
            # Get Git metadata
            git_metadata = await self._get_git_metadata(file_path, git_manager)
            
            # Generate embedding
            embedding = await self._generate_embedding(normalized["content"])
            
            # Store document
            doc_id = await self._store_document(
                file_path=file_path,
                content=content,
                normalized_content=normalized["content"],
                embedding=embedding,
                metadata={
                    "file_type": file_class.file_type,
                    "language": file_class.language,
                    "importance_score": file_class.importance_score,
                    "importance_level": file_class.importance_level,
                    "content_hash": file_class.content_hash,
                    **git_metadata
                }
            )
            
            return {
                "success": True,
                "document_id": doc_id,
                "embedding_generated": embedding is not None
            }
            
        except Exception as e:
            logger.error(f"File processing error: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    async def _normalize_content(
        self,
        content: str,
        file_path: str,
        file_type: str
    ) -> Optional[Dict]:
        """
        Normalize file content.
        
        Args:
            content: Raw file content
            file_path: File path
            file_type: File type
        
        Returns:
            Normalized content dictionary or None
        """
        try:
            # Get appropriate normalizer
            normalizer = self.normalizer_factory.get_normalizer(file_type)
            
            if not normalizer:
                # Use markdown normalizer as fallback
                normalizer = self.normalizer_factory.get_normalizer(".md")
            
            # Normalize
            result = await normalizer.normalize(
                content=content,
                file_path=file_path,
                metadata={"file_type": file_type}
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Normalization error for {file_path}: {e}")
            return None
    
    async def _generate_embedding(self, content: str) -> Optional[List[float]]:
        """
        Generate embedding for content.
        
        Args:
            content: Content to embed
        
        Returns:
            Embedding vector or None
        """
        try:
            import httpx
            
            # Call embedding service
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.embedding_service_url}/api/v1/embeddings/generate",
                    json={
                        "texts": [content[:8000]],  # Limit to 8K chars
                        "model": "fastembed"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("embeddings"):
                        return data["embeddings"][0]
                else:
                    logger.warning(f"Embedding generation failed: HTTP {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Embedding generation error: {e}")
            return None
    
    async def _get_git_metadata(
        self,
        file_path: str,
        git_manager: GitService
    ) -> Dict:
        """
        Get Git metadata for a file.
        
        Args:
            file_path: File path
            git_manager: Git manager instance
        
        Returns:
            Git metadata dictionary
        """
        try:
            # Get latest commit for file
            commits = git_manager.get_file_history(file_path, max_commits=1)
            
            if commits:
                commit = commits[0]
                return {
                    "commit_sha": commit.hexsha,
                    "commit_author": commit.author.name,
                    "commit_date": commit.committed_datetime.isoformat(),
                    "commit_message": commit.message.strip()
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"Git metadata error for {file_path}: {e}")
            return {}
    
    async def _store_document(
        self,
        file_path: str,
        content: str,
        normalized_content: str,
        embedding: Optional[List[float]],
        metadata: Dict
    ) -> str:
        """
        Store document in database and vector store.
        
        Args:
            file_path: File path
            content: Original content
            normalized_content: Normalized content
            embedding: Embedding vector
            metadata: Document metadata
        
        Returns:
            Document ID
        """
        from ...storage.models import DocumentModel
        from sqlalchemy import select
        import hashlib
        import uuid
        
        # Generate content hash
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        
        async with get_database().session() as session:
            # Check if document exists
            result = await session.execute(
                select(DocumentModel)
                .where(DocumentModel.file_path == file_path)
                .where(DocumentModel.content_hash == content_hash)
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                return existing.id
            
            # Create new document
            doc = DocumentModel(
                id=str(uuid.uuid4()),
                file_path=file_path,
                content=content,
                normalized_content=normalized_content,
                content_hash=content_hash,
                file_type=metadata.get("file_type"),
                language=metadata.get("language"),
                metadata_=metadata,
                has_embedding=embedding is not None,
                is_latest_version=True,
                created_at=datetime.utcnow()
            )
            
            session.add(doc)
            await session.commit()
            
            # Store embedding in ChromaDB if available
            if embedding:
                await self._store_embedding(doc.id, file_path, embedding, normalized_content)
            
            return doc.id
    
    async def _store_embedding(
        self,
        doc_id: str,
        file_path: str,
        embedding: List[float],
        content: str
    ) -> None:
        """
        Store embedding in ChromaDB.
        
        Args:
            doc_id: Document ID
            file_path: File path
            embedding: Embedding vector
            content: Document content
        """
        try:
            import httpx
            
            # Call ChromaDB via embedding service
            async with httpx.AsyncClient(timeout=10.0) as client:
                await client.post(
                    f"{self.embedding_service_url}/api/v1/embeddings/store",
                    json={
                        "collection": "ecosystem_docs",
                        "ids": [doc_id],
                        "embeddings": [embedding],
                        "documents": [content[:1000]],  # Store preview
                        "metadatas": [{"file_path": file_path}]
                    }
                )
                
        except Exception as e:
            logger.error(f"Failed to store embedding in ChromaDB: {e}")
    
    def _order_files_by_dependencies(
        self,
        files: List[FileClassificationModel],
        dependency_order: List[str]
    ) -> List[FileClassificationModel]:
        """
        Order files according to dependency topological order (PHASE 10 - Gap #2).
        
        Files that appear in the dependency order are processed in that order.
        Files not in the order are appended at the end.
        
        Args:
            files: List of file classifications
            dependency_order: Topological order of files
        
        Returns:
            Ordered list of file classifications
        """
        try:
            # Create mapping of file path to file classification
            file_map = {f.file_path: f for f in files}
            
            # Build ordered list
            ordered_files = []
            processed_paths = set()
            
            # First, add files in dependency order
            for path in dependency_order:
                if path in file_map:
                    ordered_files.append(file_map[path])
                    processed_paths.add(path)
            
            # Then, add remaining files (not in dependency order)
            remaining = [f for f in files if f.file_path not in processed_paths]
            ordered_files.extend(remaining)
            
            logger.debug(
                f"   Ordered {len(ordered_files)} files: "
                f"{len(processed_paths)} by dependency, "
                f"{len(remaining)} remaining"
            )
            
            return ordered_files
            
        except Exception as e:
            logger.error(f"Error ordering files by dependencies: {e}", exc_info=True)
            # Fallback to original order
            return files


# Singleton instance
_sub_job_executor_instance = None

def get_sub_job_executor() -> SubJobExecutor:
    """Get singleton sub-job executor instance."""
    global _sub_job_executor_instance
    if _sub_job_executor_instance is None:
        _sub_job_executor_instance = SubJobExecutor()
    return _sub_job_executor_instance

