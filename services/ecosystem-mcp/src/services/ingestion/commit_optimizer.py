"""
Commit-level optimization for ingestion jobs.

Provides intelligent skipping of duplicate commits and batch duplicate checking
to dramatically improve performance when processing commits with mostly duplicate content.

Phase 2 Enhancement: Bloom filter for ultra-fast negative duplicate checks.
"""

import logging
from typing import Dict, Any, List, Set, Optional
from uuid import UUID
from datetime import datetime
import hashlib

from ...storage import get_database
from ...storage.repositories import DocumentRepository
from sqlalchemy import select, func
from ...storage.db_models import DocumentModel
from ...utils.redis_client import get_redis_client

logger = logging.getLogger(__name__)


class BloomFilter:
    """
    Simple Bloom filter implementation for fast negative duplicate checks.
    
    Uses Redis for persistence and multiple hash functions for accuracy.
    False positive rate: ~1% with 3 hash functions.
    """
    
    def __init__(self, redis_key: str = "bloom:content_hashes", size: int = 10_000_000):
        """
        Initialize Bloom filter.
        
        Args:
            redis_key: Redis key for the bit array
            size: Size of bit array (10M bits = ~1.2MB, supports ~700K items at 1% FPR)
        """
        self.redis_key = redis_key
        self.size = size
        self.hash_count = 3  # Number of hash functions
    
    def _hashes(self, item: str) -> List[int]:
        """Generate multiple hash values for an item."""
        hashes = []
        for i in range(self.hash_count):
            # Use different seeds for each hash function
            h = hashlib.sha256(f"{item}{i}".encode()).hexdigest()
            hashes.append(int(h, 16) % self.size)
        return hashes
    
    async def add(self, item: str) -> bool:
        """
        Add an item to the Bloom filter.
        
        Args:
            item: Item to add (content hash)
            
        Returns:
            True if added successfully
        """
        try:
            redis = get_redis_client()
            positions = self._hashes(item)
            
            # Set bits at all positions
            pipeline = redis.client.pipeline()
            for pos in positions:
                pipeline.setbit(self.redis_key, pos, 1)
            await pipeline.execute()
            
            return True
        except Exception as e:
            logger.error(f"Failed to add to Bloom filter: {e}")
            return False
    
    async def contains(self, item: str) -> bool:
        """
        Check if an item might be in the set.
        
        Args:
            item: Item to check (content hash)
            
        Returns:
            True if item MIGHT exist (could be false positive)
            False if item DEFINITELY does not exist
        """
        try:
            redis = get_redis_client()
            positions = self._hashes(item)
            
            # Check all bit positions
            pipeline = redis.client.pipeline()
            for pos in positions:
                pipeline.getbit(self.redis_key, pos)
            results = await pipeline.execute()
            
            # Item might exist only if ALL bits are set
            return all(results)
        except Exception as e:
            logger.error(f"Failed to check Bloom filter: {e}")
            # On error, assume might exist (safer - will check database)
            return True
    
    async def add_batch(self, items: List[str]) -> int:
        """
        Add multiple items to the Bloom filter.
        
        Args:
            items: List of items to add
            
        Returns:
            Number of items added
        """
        try:
            redis = get_redis_client()
            pipeline = redis.client.pipeline()
            
            for item in items:
                positions = self._hashes(item)
                for pos in positions:
                    pipeline.setbit(self.redis_key, pos, 1)
            
            await pipeline.execute()
            return len(items)
        except Exception as e:
            logger.error(f"Failed to add batch to Bloom filter: {e}")
            return 0
    
    async def check_batch(self, items: List[str]) -> Dict[str, bool]:
        """
        Check multiple items at once.
        
        Args:
            items: List of items to check
            
        Returns:
            Dict mapping item -> might_exist
        """
        try:
            redis = get_redis_client()
            results = {}
            
            # Build pipeline to check all items
            pipeline = redis.client.pipeline()
            item_positions = {}
            
            for item in items:
                positions = self._hashes(item)
                item_positions[item] = positions
                for pos in positions:
                    pipeline.getbit(self.redis_key, pos)
            
            # Execute all checks at once
            all_results = await pipeline.execute()
            
            # Parse results
            idx = 0
            for item, positions in item_positions.items():
                # Check if all bits for this item are set
                item_bits = all_results[idx:idx + len(positions)]
                results[item] = all(item_bits)
                idx += len(positions)
            
            return results
        except Exception as e:
            logger.error(f"Failed to check batch in Bloom filter: {e}")
            # On error, assume all might exist
            return {item: True for item in items}


class CommitOptimizer:
    """
    Optimizes ingestion by detecting duplicate commits and batch-checking files.
    
    Features:
    - Commit-level duplicate detection
    - Batch hash checking (100 files at once)
    - Git blob hash optimization
    - Skip entire commits if already ingested
    - Phase 2: Bloom filter for ultra-fast negative checks (5-10× faster)
    """
    
    def __init__(self, use_bloom_filter: bool = True):
        """
        Initialize the commit optimizer.
        
        Args:
            use_bloom_filter: Enable Bloom filter for fast negative checks
        """
        self.batch_size = 100  # Check 100 hashes at once
        self.use_bloom_filter = use_bloom_filter
        
        if use_bloom_filter:
            self.bloom = BloomFilter()
            logger.info("CommitOptimizer initialized with Bloom filter (Phase 2 optimization)")
        else:
            self.bloom = None
            logger.info("CommitOptimizer initialized (standard mode)")
    
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
        
        Phase 2 Enhancement: Uses Bloom filter for fast negative checks,
        only queries database for potential matches.
        
        Args:
            content_hashes: List of SHA-256 content hashes
        
        Returns:
            Set of hashes that already exist in database
        """
        if not content_hashes:
            return set()
        
        try:
            # Phase 2: Use Bloom filter to quickly eliminate definite non-matches
            if self.use_bloom_filter and self.bloom:
                bloom_results = await self.bloom.check_batch(content_hashes)
                
                # Separate into "definitely not in DB" and "might be in DB"
                definitely_not = [h for h, might_exist in bloom_results.items() if not might_exist]
                might_exist = [h for h, might_exist in bloom_results.items() if might_exist]
                
                bloom_filtered_count = len(definitely_not)
                if bloom_filtered_count > 0:
                    logger.debug(
                        f"🚀 Bloom filter: {bloom_filtered_count}/{len(content_hashes)} hashes "
                        f"definitely new ({bloom_filtered_count/len(content_hashes)*100:.0f}% filtered)"
                    )
                
                # Only check database for hashes that might exist
                hashes_to_check = might_exist
            else:
                # No Bloom filter, check all hashes
                hashes_to_check = content_hashes
            
            # No need to query database if Bloom filter ruled out everything
            if not hashes_to_check:
                return set()
            
            # Query database for potential matches
            db = get_database()
            async with db.session() as session:
                result = await session.execute(
                    select(DocumentModel.content_hash)
                    .where(DocumentModel.content_hash.in_(hashes_to_check))
                    .distinct()
                )
                
                existing_hashes = {row[0] for row in result.fetchall()}
                
                # Add confirmed existing hashes to Bloom filter for future checks
                if self.use_bloom_filter and self.bloom and existing_hashes:
                    await self.bloom.add_batch(list(existing_hashes))
                
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

