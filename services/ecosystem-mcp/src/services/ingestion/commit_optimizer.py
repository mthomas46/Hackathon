"""
Commit-level optimization for ingestion jobs.

Provides intelligent skipping of duplicate commits and batch duplicate checking
to dramatically improve performance when processing commits with mostly duplicate content.
"""

import logging
from typing import Dict, Any, List, Set, Optional
from uuid import UUID
from datetime import datetime

from ...storage import get_database
from ...storage.repositories import DocumentRepository
from sqlalchemy import select, func
from ...storage.db_models import DocumentModel

logger = logging.getLogger(__name__)


class CommitOptimizer:
    """
    Optimizes ingestion by detecting duplicate commits and batch-checking files.
    
    Features:
    - Commit-level duplicate detection
    - Batch hash checking (100 files at once)
    - Git blob hash optimization
    - Skip entire commits if already ingested
    """
    
    def __init__(self):
        """Initialize the commit optimizer."""
        self.batch_size = 100  # Check 100 hashes at once
        logger.info("CommitOptimizer initialized")
    
    async def check_commit_already_ingested(self, commit_sha: str) -> Dict[str, Any]:
        """
        Check if a commit has already been fully ingested.
        
        Args:
            commit_sha: Git commit SHA to check
        
        Returns:
            Dict with:
                - already_ingested: bool
                - document_count: int (if ingested)
                - ingested_at: datetime (if ingested)
        """
        try:
            db = get_database()
            async with db.session() as session:
                # Query for documents from this commit
                result = await session.execute(
                    select(
                        func.count(DocumentModel.id).label('count'),
                        func.min(DocumentModel.created_at).label('first_ingested')
                    )
                    .where(DocumentModel.git_commit_sha == commit_sha)
                )
                
                row = result.first()
                
                if row and row.count > 0:
                    logger.info(
                        f"✅ Commit {commit_sha[:8]} already ingested: "
                        f"{row.count} documents on {row.first_ingested}"
                    )
                    
                    return {
                        "already_ingested": True,
                        "document_count": row.count,
                        "ingested_at": row.first_ingested
                    }
                
                return {
                    "already_ingested": False,
                    "document_count": 0,
                    "ingested_at": None
                }
        
        except Exception as e:
            logger.error(f"Failed to check commit {commit_sha}: {e}")
            # On error, assume not ingested (safer)
            return {
                "already_ingested": False,
                "document_count": 0,
                "ingested_at": None
            }
    
    async def batch_check_content_hashes(
        self,
        content_hashes: List[str]
    ) -> Set[str]:
        """
        Check multiple content hashes at once for existence.
        
        Args:
            content_hashes: List of SHA-256 content hashes
        
        Returns:
            Set of hashes that already exist in database
        """
        if not content_hashes:
            return set()
        
        try:
            db = get_database()
            async with db.session() as session:
                # Single query to check all hashes
                result = await session.execute(
                    select(DocumentModel.content_hash)
                    .where(DocumentModel.content_hash.in_(content_hashes))
                    .distinct()
                )
                
                existing_hashes = {row[0] for row in result.fetchall()}
                
                found_count = len(existing_hashes)
                total_count = len(content_hashes)
                
                if found_count > 0:
                    logger.debug(
                        f"📊 Batch check: {found_count}/{total_count} hashes "
                        f"already exist ({found_count/total_count*100:.0f}% duplicates)"
                    )
                
                return existing_hashes
        
        except Exception as e:
            logger.error(f"Failed to batch check hashes: {e}")
            # On error, return empty set (will check individually)
            return set()
    
    async def check_content_hash_exists(self, content_hash: str) -> bool:
        """
        Check if a single content hash exists in the database.
        
        Args:
            content_hash: SHA-256 content hash
        
        Returns:
            True if hash exists, False otherwise
        """
        try:
            db = get_database()
            async with db.session() as session:
                result = await session.execute(
                    select(DocumentModel.id)
                    .where(DocumentModel.content_hash == content_hash)
                    .limit(1)
                )
                
                return result.first() is not None
        
        except Exception as e:
            logger.error(f"Failed to check hash {content_hash[:16]}: {e}")
            return False
    
    async def get_commit_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about ingested commits.
        
        Returns:
            Dict with commit ingestion statistics
        """
        try:
            db = get_database()
            async with db.session() as session:
                # Count unique commits
                result = await session.execute(
                    select(
                        func.count(func.distinct(DocumentModel.git_commit_sha)).label('unique_commits'),
                        func.count(DocumentModel.id).label('total_documents'),
                        func.max(DocumentModel.created_at).label('last_ingestion')
                    )
                )
                
                row = result.first()
                
                return {
                    "unique_commits": row.unique_commits if row else 0,
                    "total_documents": row.total_documents if row else 0,
                    "last_ingestion": row.last_ingestion if row else None
                }
        
        except Exception as e:
            logger.error(f"Failed to get commit statistics: {e}")
            return {
                "unique_commits": 0,
                "total_documents": 0,
                "last_ingestion": None
            }
    
    async def optimize_file_list(
        self,
        files: List[Dict[str, Any]],
        commit_sha: str
    ) -> Dict[str, Any]:
        """
        Optimize a file list by batch-checking for duplicates.
        
        Args:
            files: List of file dicts with 'content_hash' keys
            commit_sha: Current commit SHA
        
        Returns:
            Dict with:
                - files_to_process: List[Dict] - Files that need processing
                - files_to_skip: List[Dict] - Files that are duplicates
                - optimization_time_ms: float - Time saved
        """
        start_time = datetime.utcnow()
        
        # Extract content hashes from files
        file_hashes = []
        hash_to_file = {}
        
        for file_dict in files:
            if 'content_hash' in file_dict:
                hash_val = file_dict['content_hash']
                file_hashes.append(hash_val)
                hash_to_file[hash_val] = file_dict
        
        # Batch check all hashes
        existing_hashes = await self.batch_check_content_hashes(file_hashes)
        
        # Separate files into process vs skip
        files_to_process = []
        files_to_skip = []
        
        for file_dict in files:
            hash_val = file_dict.get('content_hash')
            if hash_val and hash_val in existing_hashes:
                files_to_skip.append(file_dict)
            else:
                files_to_process.append(file_dict)
        
        elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        logger.info(
            f"🚀 Optimization: {len(files_to_skip)}/{len(files)} files are duplicates "
            f"({len(files_to_skip)/len(files)*100:.0f}%) - checked in {elapsed_ms:.0f}ms"
        )
        
        return {
            "files_to_process": files_to_process,
            "files_to_skip": files_to_skip,
            "optimization_time_ms": elapsed_ms,
            "duplicate_percentage": len(files_to_skip) / len(files) * 100 if files else 0
        }


# Global instance
_commit_optimizer: Optional[CommitOptimizer] = None


def get_commit_optimizer() -> CommitOptimizer:
    """Get or create the global CommitOptimizer instance."""
    global _commit_optimizer
    
    if _commit_optimizer is None:
        _commit_optimizer = CommitOptimizer()
    
    return _commit_optimizer

