"""
Content Deduplicator

Handles content storage with deduplication:
- Stores content once, referenced many times
- Tracks reference counts
- Manages content lifecycle
- Provides content retrieval
"""

import hashlib
import logging
from typing import Optional, Tuple, Dict
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class ContentDeduplicator:
    """
    Handle content storage with deduplication.
    
    Features:
    - Content-addressable storage (SHA256)
    - Reference counting
    - Automatic cleanup of unreferenced content
    - Content retrieval by hash
    """
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.logger = logging.getLogger(__name__)
    
    async def calculate_content_hash(self, content: bytes) -> str:
        """Calculate SHA256 hash of content."""
        return hashlib.sha256(content).hexdigest()
    
    async def store_content(
        self,
        content: bytes,
        mime_type: str = "text/plain",
        compression_type: Optional[str] = None
    ) -> Tuple[str, bool]:
        """
        Store content with deduplication.
        
        Args:
            content: Raw content bytes
            mime_type: MIME type of content
            compression_type: Optional compression algorithm used
        
        Returns:
            Tuple of (content_hash, is_duplicate)
            - content_hash: SHA256 hash of the content
            - is_duplicate: True if content already existed, False if new
        """
        try:
            # Calculate hash
            content_hash = await self.calculate_content_hash(content)
            self.logger.debug(f"Content hash: {content_hash[:16]}...")
            
            # Check if content exists
            check_query = text("""
                SELECT content_hash, reference_count 
                FROM document_content_store 
                WHERE content_hash = :hash
            """)
            
            result = await self.db.execute(check_query, {"hash": content_hash})
            existing = result.fetchone()
            
            if existing:
                # Content exists - increment reference count
                self.logger.info(
                    f"Content {content_hash[:16]}... already exists "
                    f"(refs: {existing[1]} -> {existing[1] + 1})"
                )
                
                update_query = text("""
                    UPDATE document_content_store 
                    SET reference_count = reference_count + 1
                    WHERE content_hash = :hash
                """)
                
                await self.db.execute(update_query, {"hash": content_hash})
                await self.db.commit()
                
                return content_hash, True  # Duplicate
            
            else:
                # New content - store it
                self.logger.info(f"Storing new content: {content_hash[:16]}... ({len(content)} bytes)")
                
                insert_query = text("""
                    INSERT INTO document_content_store 
                    (content_hash, content, mime_type, compression_type, content_size, reference_count)
                    VALUES (:hash, :content, :mime_type, :compression_type, :size, 1)
                """)
                
                await self.db.execute(
                    insert_query,
                    {
                        "hash": content_hash,
                        "content": content,
                        "mime_type": mime_type,
                        "compression_type": compression_type,
                        "size": len(content)
                    }
                )
                await self.db.commit()
                
                return content_hash, False  # New content
        
        except Exception as e:
            await self.db.rollback()
            self.logger.error(f"Failed to store content: {e}", exc_info=True)
            raise
    
    async def get_content(self, content_hash: str) -> Optional[bytes]:
        """
        Retrieve content by hash.
        
        Args:
            content_hash: SHA256 hash of the content
        
        Returns:
            Content bytes or None if not found
        """
        try:
            query = text("""
                SELECT content 
                FROM document_content_store 
                WHERE content_hash = :hash
            """)
            
            result = await self.db.execute(query, {"hash": content_hash})
            row = result.fetchone()
            
            if row:
                return row[0]
            else:
                self.logger.warning(f"Content not found: {content_hash[:16]}...")
                return None
        
        except Exception as e:
            self.logger.error(f"Failed to retrieve content: {e}", exc_info=True)
            raise
    
    async def increment_reference(self, content_hash: str) -> int:
        """
        Increment reference count for content.
        
        Args:
            content_hash: SHA256 hash of the content
        
        Returns:
            New reference count
        """
        try:
            query = text("""
                UPDATE document_content_store 
                SET reference_count = reference_count + 1
                WHERE content_hash = :hash
                RETURNING reference_count
            """)
            
            result = await self.db.execute(query, {"hash": content_hash})
            await self.db.commit()
            
            row = result.fetchone()
            if row:
                self.logger.debug(f"Incremented refs for {content_hash[:16]}... to {row[0]}")
                return row[0]
            else:
                self.logger.warning(f"Content not found for increment: {content_hash[:16]}...")
                return 0
        
        except Exception as e:
            await self.db.rollback()
            self.logger.error(f"Failed to increment reference: {e}", exc_info=True)
            raise
    
    async def decrement_reference(
        self,
        content_hash: str,
        auto_cleanup: bool = False
    ) -> int:
        """
        Decrement reference count for content.
        
        Args:
            content_hash: SHA256 hash of the content
            auto_cleanup: If True, delete content when refs reach 0
        
        Returns:
            New reference count
        """
        try:
            query = text("""
                UPDATE document_content_store 
                SET reference_count = GREATEST(reference_count - 1, 0)
                WHERE content_hash = :hash
                RETURNING reference_count
            """)
            
            result = await self.db.execute(query, {"hash": content_hash})
            row = result.fetchone()
            
            if row:
                new_count = row[0]
                self.logger.debug(f"Decremented refs for {content_hash[:16]}... to {new_count}")
                
                # Optional: cleanup if no references
                if auto_cleanup and new_count == 0:
                    await self.delete_content(content_hash)
                    self.logger.info(f"Auto-cleaned content: {content_hash[:16]}...")
                
                await self.db.commit()
                return new_count
            else:
                self.logger.warning(f"Content not found for decrement: {content_hash[:16]}...")
                return 0
        
        except Exception as e:
            await self.db.rollback()
            self.logger.error(f"Failed to decrement reference: {e}", exc_info=True)
            raise
    
    async def delete_content(self, content_hash: str) -> bool:
        """
        Delete content from store.
        
        Args:
            content_hash: SHA256 hash of the content
        
        Returns:
            True if deleted, False if not found
        """
        try:
            query = text("""
                DELETE FROM document_content_store 
                WHERE content_hash = :hash
                RETURNING content_hash
            """)
            
            result = await self.db.execute(query, {"hash": content_hash})
            await self.db.commit()
            
            row = result.fetchone()
            if row:
                self.logger.info(f"Deleted content: {content_hash[:16]}...")
                return True
            else:
                self.logger.warning(f"Content not found for deletion: {content_hash[:16]}...")
                return False
        
        except Exception as e:
            await self.db.rollback()
            self.logger.error(f"Failed to delete content: {e}", exc_info=True)
            raise
    
    async def cleanup_unreferenced(self, dry_run: bool = True) -> Dict:
        """
        Clean up content with zero references.
        
        Args:
            dry_run: If True, only report what would be deleted
        
        Returns:
            Dictionary with cleanup statistics
        """
        try:
            # Find unreferenced content
            find_query = text("""
                SELECT content_hash, content_size, first_seen_at
                FROM document_content_store
                WHERE reference_count = 0
            """)
            
            result = await self.db.execute(find_query)
            unreferenced = result.fetchall()
            
            total_items = len(unreferenced)
            total_size = sum(row[1] or 0 for row in unreferenced)
            
            self.logger.info(
                f"Found {total_items} unreferenced items "
                f"({total_size / 1024 / 1024:.2f} MB)"
            )
            
            if not dry_run and total_items > 0:
                # Delete unreferenced content
                delete_query = text("""
                    DELETE FROM document_content_store
                    WHERE reference_count = 0
                """)
                
                await self.db.execute(delete_query)
                await self.db.commit()
                
                self.logger.info(f"Deleted {total_items} unreferenced items")
            
            return {
                "total_items": total_items,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / 1024 / 1024, 2),
                "dry_run": dry_run,
                "deleted": total_items if not dry_run else 0
            }
        
        except Exception as e:
            if not dry_run:
                await self.db.rollback()
            self.logger.error(f"Failed to cleanup unreferenced content: {e}", exc_info=True)
            raise
    
    async def get_content_info(self, content_hash: str) -> Optional[Dict]:
        """
        Get information about stored content.
        
        Args:
            content_hash: SHA256 hash of the content
        
        Returns:
            Dictionary with content metadata or None if not found
        """
        try:
            query = text("""
                SELECT 
                    content_hash,
                    mime_type,
                    compression_type,
                    content_size,
                    first_seen_at,
                    reference_count,
                    storage_location
                FROM document_content_store
                WHERE content_hash = :hash
            """)
            
            result = await self.db.execute(query, {"hash": content_hash})
            row = result.fetchone()
            
            if row:
                return {
                    "content_hash": row[0],
                    "mime_type": row[1],
                    "compression_type": row[2],
                    "content_size": row[3],
                    "first_seen_at": row[4].isoformat() if row[4] else None,
                    "reference_count": row[5],
                    "storage_location": row[6]
                }
            else:
                return None
        
        except Exception as e:
            self.logger.error(f"Failed to get content info: {e}", exc_info=True)
            raise
    
    async def verify_integrity(self, content_hash: str) -> bool:
        """
        Verify that stored content matches its hash.
        
        Args:
            content_hash: Expected SHA256 hash
        
        Returns:
            True if content integrity is verified, False otherwise
        """
        try:
            content = await self.get_content(content_hash)
            if not content:
                self.logger.warning(f"Content not found for verification: {content_hash[:16]}...")
                return False
            
            actual_hash = await self.calculate_content_hash(content)
            
            if actual_hash == content_hash:
                self.logger.debug(f"Integrity verified: {content_hash[:16]}...")
                return True
            else:
                self.logger.error(
                    f"Integrity check FAILED: {content_hash[:16]}... "
                    f"(actual: {actual_hash[:16]}...)"
                )
                return False
        
        except Exception as e:
            self.logger.error(f"Failed to verify integrity: {e}", exc_info=True)
            return False

