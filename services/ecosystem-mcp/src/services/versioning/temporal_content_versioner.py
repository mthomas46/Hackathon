"""
Temporal Content Versioning System

Hybrid approach combining content-addressable storage with temporal ordering:
- Content hash for deduplication and integrity
- Timestamps for timeline reconstruction and "as of" queries
- Efficient storage (content stored once, referenced many times)
"""

import hashlib
import logging
from datetime import datetime
from typing import Optional, Dict, List, Tuple
from uuid import UUID, uuid4

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from ...storage.db_models import DocumentModel, DocumentVersionModel
from ...storage import get_db

logger = logging.getLogger(__name__)


class DocumentVersion:
    """Represents a document version with temporal and content metadata."""
    
    def __init__(
        self,
        id: UUID,
        document_id: UUID,
        version_id: str,
        version_number: int,
        content_hash: str,
        content_size: int,
        created_at: datetime,
        modified_at: datetime,
        ingested_at: datetime,
        created_by: str,
        source_path: str,
        title: str,
        timeline_position: Optional[int] = None,
        effective_date: Optional[datetime] = None,
        is_latest: bool = True,
        previous_version_id: Optional[UUID] = None,
        next_version_id: Optional[UUID] = None,
        metadata: Optional[Dict] = None
    ):
        self.id = id
        self.document_id = document_id
        self.version_id = version_id
        self.version_number = version_number
        self.content_hash = content_hash
        self.content_size = content_size
        self.created_at = created_at
        self.modified_at = modified_at
        self.ingested_at = ingested_at
        self.created_by = created_by
        self.source_path = source_path
        self.title = title
        self.timeline_position = timeline_position
        self.effective_date = effective_date
        self.is_latest = is_latest
        self.previous_version_id = previous_version_id
        self.next_version_id = next_version_id
        self.metadata = metadata or {}


class TemporalContentVersioner:
    """
    Content-addressable storage with temporal ordering.
    
    Features:
    - Content deduplication via SHA256 hash
    - Timeline reconstruction
    - Temporal queries ("as of" date)
    - Efficient storage (content stored once)
    - Version relationships (previous/next)
    """
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.logger = logging.getLogger(__name__)
    
    async def calculate_content_hash(self, content: bytes) -> str:
        """Calculate SHA256 hash of content."""
        return hashlib.sha256(content).hexdigest()
    
    async def create_composite_version_id(
        self,
        content_hash: str,
        modified_at: datetime
    ) -> str:
        """
        Create composite version ID: content_hash + timestamp.
        
        Format: {first_16_chars_of_hash}:{timestamp}
        Example: abc123def4567890:20251015143022123456
        """
        timestamp_str = modified_at.strftime('%Y%m%d%H%M%S%f')
        return f"{content_hash[:16]}:{timestamp_str}"
    
    async def get_next_timeline_position(self) -> int:
        """Get next global timeline position."""
        result = await self.db.execute(
            select(func.max(DocumentVersionModel.timeline_position))
        )
        max_pos = result.scalar()
        return (max_pos or 0) + 1
    
    async def find_latest_version_by_path(
        self,
        source_path: str
    ) -> Optional[DocumentVersionModel]:
        """Find the latest version of a document by source path."""
        result = await self.db.execute(
            select(DocumentVersionModel)
            .where(DocumentVersionModel.source_path == source_path)
            .where(DocumentVersionModel.is_latest == True)
            .order_by(DocumentVersionModel.modified_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
    
    async def check_content_exists(self, content_hash: str) -> bool:
        """Check if content is already stored."""
        result = await self.db.execute(
            select(func.count())
            .select_from(self.db.bind.execute(
                "SELECT 1 FROM document_content_store WHERE content_hash = :hash",
                {"hash": content_hash}
            ))
        )
        return result.scalar() > 0
    
    async def store_content(
        self,
        content_hash: str,
        content: bytes,
        mime_type: str
    ) -> bool:
        """
        Store content in deduplicated storage.
        
        Returns:
            True if new content was stored, False if it already existed
        """
        # Check if content exists
        exists = await self.db.execute(
            "SELECT content_hash FROM document_content_store WHERE content_hash = :hash",
            {"hash": content_hash}
        )
        
        if exists.scalar_one_or_none():
            # Content already exists - increment reference count
            await self.db.execute(
                """
                UPDATE document_content_store 
                SET reference_count = reference_count + 1
                WHERE content_hash = :hash
                """,
                {"hash": content_hash}
            )
            return False  # Not new
        else:
            # Store new content
            await self.db.execute(
                """
                INSERT INTO document_content_store 
                (content_hash, content, mime_type, content_size, reference_count)
                VALUES (:hash, :content, :mime_type, :size, 1)
                """,
                {
                    "hash": content_hash,
                    "content": content,
                    "mime_type": mime_type,
                    "size": len(content)
                }
            )
            return True  # New content
    
    async def create_version(
        self,
        document_id: UUID,
        content: bytes,
        source_path: str,
        creator: str,
        title: str,
        modified_at: datetime,
        created_at: Optional[datetime] = None,
        effective_date: Optional[datetime] = None,
        mime_type: str = "text/plain",
        metadata: Optional[Dict] = None
    ) -> DocumentVersion:
        """
        Create a new document version with temporal tracking.
        
        Process:
        1. Calculate content hash
        2. Check if content already exists (deduplication)
        3. Create version record with timestamp
        4. Add to timeline
        5. Update relationships
        
        Args:
            document_id: Document UUID
            content: Raw document content
            source_path: File path or identifier
            creator: User who created/modified the document
            title: Document title
            modified_at: When the document was last modified
            created_at: When the document was originally created (defaults to modified_at)
            effective_date: Optional "as-of" date for the version
            mime_type: Content MIME type
            metadata: Additional metadata
        
        Returns:
            DocumentVersion object
        """
        try:
            # 1. Calculate content hash
            content_hash = await self.calculate_content_hash(content)
            self.logger.info(f"Content hash: {content_hash[:16]}... for {source_path}")
            
            # 2. Create composite version ID
            version_id = await self.create_composite_version_id(content_hash, modified_at)
            self.logger.info(f"Version ID: {version_id}")
            
            # 3. Store content (with deduplication)
            is_new_content = await self.store_content(content_hash, content, mime_type)
            if is_new_content:
                self.logger.info(f"Stored new content: {content_hash[:16]}...")
            else:
                self.logger.info(f"Content already exists (deduplicated): {content_hash[:16]}...")
            
            # 4. Find previous version (by source_path)
            previous = await self.find_latest_version_by_path(source_path)
            
            # 5. Calculate version number
            version_number = (previous.version_number + 1) if previous else 1
            
            # 6. Get next timeline position
            timeline_position = await self.get_next_timeline_position()
            
            # 7. Create version record
            new_version = DocumentVersionModel(
                id=uuid4(),
                document_id=document_id,
                version_id=version_id,
                version_number=version_number,
                content_hash=content_hash,
                content_size=len(content),
                timeline_position=timeline_position,
                
                # Temporal metadata
                created_at=created_at or modified_at,
                modified_at=modified_at,
                ingested_at=datetime.utcnow(),
                effective_date=effective_date,
                
                # Provenance
                created_by=creator,
                source_path=source_path,
                title=title,
                
                # Relationships
                previous_version_id=previous.id if previous else None,
                is_latest=True,
                
                # Metadata
                metadata=metadata
            )
            
            self.db.add(new_version)
            
            # 8. Update previous version
            if previous:
                previous.is_latest = False
                previous.next_version_id = new_version.id
                await self.db.flush()
            
            # 9. Add to timeline
            await self.add_to_timeline(
                version_id=new_version.id,
                document_id=document_id,
                event_timestamp=modified_at,
                event_type='version_created',
                actor=creator,
                metadata={
                    'content_hash': content_hash,
                    'version_number': version_number,
                    'is_new_content': is_new_content
                }
            )
            
            await self.db.commit()
            
            self.logger.info(
                f"Created version {version_number} for {source_path} "
                f"(timeline position: {timeline_position})"
            )
            
            return DocumentVersion(
                id=new_version.id,
                document_id=new_version.document_id,
                version_id=new_version.version_id,
                version_number=new_version.version_number,
                content_hash=new_version.content_hash,
                content_size=new_version.content_size,
                created_at=new_version.created_at,
                modified_at=new_version.modified_at,
                ingested_at=new_version.ingested_at,
                created_by=new_version.created_by,
                source_path=new_version.source_path,
                title=new_version.title,
                timeline_position=new_version.timeline_position,
                effective_date=new_version.effective_date,
                is_latest=new_version.is_latest,
                previous_version_id=new_version.previous_version_id,
                next_version_id=new_version.next_version_id,
                metadata=new_version.metadata
            )
            
        except Exception as e:
            await self.db.rollback()
            self.logger.error(f"Failed to create version: {e}", exc_info=True)
            raise
    
    async def add_to_timeline(
        self,
        version_id: UUID,
        document_id: UUID,
        event_timestamp: datetime,
        event_type: str,
        actor: str,
        metadata: Optional[Dict] = None
    ):
        """Add an event to the document timeline."""
        await self.db.execute(
            """
            INSERT INTO document_timeline 
            (id, version_id, document_id, event_timestamp, event_type, actor, metadata)
            VALUES (:id, :version_id, :document_id, :timestamp, :event_type, :actor, :metadata)
            """,
            {
                "id": uuid4(),
                "version_id": version_id,
                "document_id": document_id,
                "timestamp": event_timestamp,
                "event_type": event_type,
                "actor": actor,
                "metadata": metadata
            }
        )
    
    async def get_version_by_hash_and_timestamp(
        self,
        content_hash: str,
        timestamp: datetime
    ) -> Optional[DocumentVersionModel]:
        """Get a specific version by content hash and timestamp."""
        version_id_pattern = f"{content_hash[:16]}:{timestamp.strftime('%Y%m%d%H%M%S%f')}"
        
        result = await self.db.execute(
            select(DocumentVersionModel)
            .where(DocumentVersionModel.version_id == version_id_pattern)
            .limit(1)
        )
        return result.scalar_one_or_none()
    
    async def detect_duplicate_content(
        self,
        content: bytes,
        source_path: str
    ) -> Tuple[bool, Optional[str], Optional[datetime]]:
        """
        Detect if content already exists and when it was last seen.
        
        Returns:
            (is_duplicate, content_hash, last_seen_timestamp)
        """
        content_hash = await self.calculate_content_hash(content)
        
        # Check if this exact content exists
        result = await self.db.execute(
            """
            SELECT content_hash, first_seen_at 
            FROM document_content_store 
            WHERE content_hash = :hash
            """,
            {"hash": content_hash}
        )
        row = result.fetchone()
        
        if row:
            return True, row[0], row[1]
        else:
            return False, content_hash, None

