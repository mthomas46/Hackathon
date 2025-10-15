"""
Timeline Query Engine

Provides temporal query capabilities for document versioning:
- "As of" date queries
- Document timelines
- Change tracking between dates
- Activity analysis
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class TimelineEvent:
    """Represents a single event in a document's timeline."""
    
    def __init__(
        self,
        version_id: UUID,
        version_number: int,
        event_timestamp: datetime,
        event_type: str,
        actor: str,
        content_hash: str,
        title: str,
        is_latest: bool,
        metadata: Optional[Dict] = None
    ):
        self.version_id = version_id
        self.version_number = version_number
        self.event_timestamp = event_timestamp
        self.event_type = event_type
        self.actor = actor
        self.content_hash = content_hash
        self.title = title
        self.is_latest = is_latest
        self.metadata = metadata or {}


class DocumentSnapshot:
    """Represents a document at a specific point in time."""
    
    def __init__(
        self,
        document_id: UUID,
        version_id: UUID,
        version_number: int,
        content_hash: str,
        modified_at: datetime,
        created_by: str,
        title: str,
        source_path: str,
        content_size: int
    ):
        self.document_id = document_id
        self.version_id = version_id
        self.version_number = version_number
        self.content_hash = content_hash
        self.modified_at = modified_at
        self.created_by = created_by
        self.title = title
        self.source_path = source_path
        self.content_size = content_size


class DocumentChange:
    """Represents changes to a document over a time period."""
    
    def __init__(
        self,
        document_id: UUID,
        title: str,
        version_count: int,
        first_change: datetime,
        last_change: datetime,
        contributors: List[str],
        source_path: str
    ):
        self.document_id = document_id
        self.title = title
        self.version_count = version_count
        self.first_change = first_change
        self.last_change = last_change
        self.contributors = contributors
        self.source_path = source_path


class TimelineQueryEngine:
    """
    Query documents across time.
    
    Supports:
    - Point-in-time queries ("as of" date)
    - Document history timelines
    - Change detection between dates
    - Activity analysis
    """
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.logger = logging.getLogger(__name__)
    
    async def get_documents_as_of(
        self,
        as_of_date: datetime,
        filters: Optional[Dict] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[DocumentSnapshot]:
        """
        Get all documents as they existed at a specific point in time.
        
        Example:
            "Show me all documents as of October 1, 2025"
        
        Returns the version of each document that was current at that timestamp.
        
        Args:
            as_of_date: The point in time to query
            filters: Optional filters (creator, source_path pattern, etc.)
            limit: Maximum number of results
            offset: Pagination offset
        
        Returns:
            List of DocumentSnapshot objects
        """
        try:
            self.logger.info(f"Querying documents as of {as_of_date}")
            
            # Use the PostgreSQL function we created
            query = text("""
                SELECT 
                    document_id,
                    version_id,
                    version_number,
                    content_hash,
                    modified_at,
                    created_by,
                    title,
                    source_path
                FROM get_all_documents_as_of(:as_of_date)
                LIMIT :limit OFFSET :offset
            """)
            
            result = await self.db.execute(
                query,
                {
                    "as_of_date": as_of_date,
                    "limit": limit,
                    "offset": offset
                }
            )
            
            snapshots = []
            for row in result:
                snapshots.append(DocumentSnapshot(
                    document_id=row[0],
                    version_id=row[1],
                    version_number=row[2],
                    content_hash=row[3],
                    modified_at=row[4],
                    created_by=row[5],
                    title=row[6],
                    source_path=row[7],
                    content_size=0  # Would need to join with content_store for this
                ))
            
            self.logger.info(f"Found {len(snapshots)} documents as of {as_of_date}")
            return snapshots
            
        except Exception as e:
            self.logger.error(f"Failed to query documents as of {as_of_date}: {e}", exc_info=True)
            raise
    
    async def get_document_timeline(
        self,
        document_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[TimelineEvent]:
        """
        Get complete timeline for a document.
        
        Returns:
        - All versions
        - Modification events
        - Chronologically ordered
        
        Args:
            document_id: Document UUID
            start_date: Optional start of time range
            end_date: Optional end of time range
        
        Returns:
            List of TimelineEvent objects
        """
        try:
            self.logger.info(f"Fetching timeline for document {document_id}")
            
            # Use the PostgreSQL function we created
            query_params = {"document_id": document_id}
            
            if start_date and end_date:
                query = text("""
                    SELECT * FROM get_document_timeline(:document_id, :start_date, :end_date)
                """)
                query_params["start_date"] = start_date
                query_params["end_date"] = end_date
            elif start_date:
                query = text("""
                    SELECT * FROM get_document_timeline(:document_id, :start_date, NULL)
                """)
                query_params["start_date"] = start_date
            elif end_date:
                query = text("""
                    SELECT * FROM get_document_timeline(:document_id, NULL, :end_date)
                """)
                query_params["end_date"] = end_date
            else:
                query = text("""
                    SELECT * FROM get_document_timeline(:document_id, NULL, NULL)
                """)
            
            result = await self.db.execute(query, query_params)
            
            events = []
            for row in result:
                events.append(TimelineEvent(
                    version_id=row[0],
                    version_number=row[1],
                    event_timestamp=row[2],
                    event_type=row[3],
                    actor=row[4],
                    content_hash=row[5],
                    title=row[6],
                    is_latest=row[7]
                ))
            
            self.logger.info(f"Found {len(events)} events in timeline")
            return events
            
        except Exception as e:
            self.logger.error(f"Failed to fetch timeline: {e}", exc_info=True)
            raise
    
    async def get_changes_between(
        self,
        start_date: datetime,
        end_date: datetime,
        limit: int = 100
    ) -> List[DocumentChange]:
        """
        Get all document changes in a time range.
        
        Example:
            "What changed between Oct 1 and Oct 15?"
        
        Args:
            start_date: Start of time range
            end_date: End of time range
            limit: Maximum number of results
        
        Returns:
            List of DocumentChange objects
        """
        try:
            self.logger.info(f"Querying changes between {start_date} and {end_date}")
            
            query = text("""
                SELECT 
                    v.document_id,
                    MAX(v.title) as title,
                    COUNT(*) as version_count,
                    MIN(v.modified_at) as first_change,
                    MAX(v.modified_at) as last_change,
                    ARRAY_AGG(DISTINCT v.created_by) as contributors,
                    MAX(v.source_path) as source_path
                FROM document_versions v
                WHERE v.modified_at BETWEEN :start_date AND :end_date
                GROUP BY v.document_id
                ORDER BY version_count DESC
                LIMIT :limit
            """)
            
            result = await self.db.execute(
                query,
                {
                    "start_date": start_date,
                    "end_date": end_date,
                    "limit": limit
                }
            )
            
            changes = []
            for row in result:
                changes.append(DocumentChange(
                    document_id=row[0],
                    title=row[1],
                    version_count=row[2],
                    first_change=row[3],
                    last_change=row[4],
                    contributors=row[5],
                    source_path=row[6]
                ))
            
            self.logger.info(f"Found {len(changes)} documents with changes")
            return changes
            
        except Exception as e:
            self.logger.error(f"Failed to query changes: {e}", exc_info=True)
            raise
    
    async def get_version_by_id(
        self,
        version_id: UUID
    ) -> Optional[DocumentSnapshot]:
        """Get a specific version by its ID."""
        try:
            query = text("""
                SELECT 
                    document_id,
                    id as version_id,
                    version_number,
                    content_hash,
                    modified_at,
                    created_by,
                    title,
                    source_path,
                    content_size
                FROM document_versions
                WHERE id = :version_id
            """)
            
            result = await self.db.execute(query, {"version_id": version_id})
            row = result.fetchone()
            
            if row:
                return DocumentSnapshot(
                    document_id=row[0],
                    version_id=row[1],
                    version_number=row[2],
                    content_hash=row[3],
                    modified_at=row[4],
                    created_by=row[5],
                    title=row[6],
                    source_path=row[7],
                    content_size=row[8] or 0
                )
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to fetch version: {e}", exc_info=True)
            raise
    
    async def get_activity_summary(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict:
        """
        Get activity summary statistics.
        
        Returns:
            Dictionary with:
            - total_versions
            - unique_documents
            - unique_contributors
            - activity_by_day
            - top_contributors
        """
        try:
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=30)
            if not end_date:
                end_date = datetime.utcnow()
            
            self.logger.info(f"Generating activity summary from {start_date} to {end_date}")
            
            # Total versions created
            total_query = text("""
                SELECT COUNT(*) 
                FROM document_versions
                WHERE modified_at BETWEEN :start_date AND :end_date
            """)
            total_result = await self.db.execute(
                total_query,
                {"start_date": start_date, "end_date": end_date}
            )
            total_versions = total_result.scalar()
            
            # Unique documents modified
            docs_query = text("""
                SELECT COUNT(DISTINCT document_id)
                FROM document_versions
                WHERE modified_at BETWEEN :start_date AND :end_date
            """)
            docs_result = await self.db.execute(
                docs_query,
                {"start_date": start_date, "end_date": end_date}
            )
            unique_documents = docs_result.scalar()
            
            # Unique contributors
            contributors_query = text("""
                SELECT COUNT(DISTINCT created_by)
                FROM document_versions
                WHERE modified_at BETWEEN :start_date AND :end_date
                AND created_by IS NOT NULL
            """)
            contributors_result = await self.db.execute(
                contributors_query,
                {"start_date": start_date, "end_date": end_date}
            )
            unique_contributors = contributors_result.scalar()
            
            # Activity by day
            daily_query = text("""
                SELECT 
                    DATE(modified_at) as activity_date,
                    COUNT(*) as version_count
                FROM document_versions
                WHERE modified_at BETWEEN :start_date AND :end_date
                GROUP BY DATE(modified_at)
                ORDER BY activity_date DESC
            """)
            daily_result = await self.db.execute(
                daily_query,
                {"start_date": start_date, "end_date": end_date}
            )
            activity_by_day = {str(row[0]): row[1] for row in daily_result}
            
            # Top contributors
            top_query = text("""
                SELECT 
                    created_by,
                    COUNT(*) as contribution_count
                FROM document_versions
                WHERE modified_at BETWEEN :start_date AND :end_date
                AND created_by IS NOT NULL
                GROUP BY created_by
                ORDER BY contribution_count DESC
                LIMIT 10
            """)
            top_result = await self.db.execute(
                top_query,
                {"start_date": start_date, "end_date": end_date}
            )
            top_contributors = {row[0]: row[1] for row in top_result}
            
            return {
                "total_versions": total_versions,
                "unique_documents": unique_documents,
                "unique_contributors": unique_contributors,
                "activity_by_day": activity_by_day,
                "top_contributors": top_contributors,
                "period_start": start_date.isoformat(),
                "period_end": end_date.isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to generate activity summary: {e}", exc_info=True)
            raise
    
    async def get_deduplication_stats(self) -> Dict:
        """
        Get content deduplication statistics.
        
        Returns:
            Dictionary with:
            - unique_content_items
            - total_versions
            - deduplicated_items
            - total_content_size
            - size_without_dedup
            - space_saved
            - deduplication_ratio
        """
        try:
            query = text("""
                SELECT * FROM content_deduplication_stats
            """)
            
            result = await self.db.execute(query)
            row = result.fetchone()
            
            if row:
                space_saved = row[5] or 0
                total_size = row[4] or 1  # Avoid division by zero
                
                return {
                    "unique_content_items": row[0] or 0,
                    "total_versions": row[1] or 0,
                    "deduplicated_items": row[2] or 0,
                    "total_content_size": row[3] or 0,
                    "size_without_dedup": row[4] or 0,
                    "space_saved": space_saved,
                    "deduplication_ratio": round((space_saved / total_size) * 100, 2) if total_size > 0 else 0
                }
            
            return {
                "unique_content_items": 0,
                "total_versions": 0,
                "deduplicated_items": 0,
                "total_content_size": 0,
                "size_without_dedup": 0,
                "space_saved": 0,
                "deduplication_ratio": 0
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get deduplication stats: {e}", exc_info=True)
            raise

