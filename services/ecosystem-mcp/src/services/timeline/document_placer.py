"""
Document Placer

Places documents into timeline periods based on temporal information.
Supports both git_history mode (commit dates) and snapshot mode (created_at dates).
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ...storage.db_models import (
    DocumentModel,
    TimePeriodModel,
    DocumentPlacementModel,
    GitCommitModel
)
from ...storage.repositories.timeline_repository import (
    TimePeriodRepository,
    DocumentPlacementRepository
)
from ...storage.repositories.document_repository import DocumentRepository
from ...models.timeline import (
    PlacementSource,
    DocumentPlacementCreate,
    PlacementMetadata
)

logger = logging.getLogger(__name__)


class DocumentPlacer:
    """
    Places documents into timeline periods based on temporal information.
    
    Handles:
    - Git history mode: Use commit dates
    - Snapshot mode: Use created_at dates
    - Mixed mode: Use appropriate date for each document
    - Relevance scoring
    """
    
    def __init__(self, db_session: AsyncSession):
        """
        Initialize document placer.
        
        Args:
            db_session: Async SQLAlchemy session
        """
        self.db = db_session
        self.period_repo = TimePeriodRepository(db_session)
        self.placement_repo = DocumentPlacementRepository(db_session)
        self.document_repo = DocumentRepository(db_session)
        self.logger = logging.getLogger(__name__)
    
    async def place_documents(
        self,
        timeline_id: UUID,
        service_name: str,
        repo_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Place all documents for a service into timeline periods.
        
        Args:
            timeline_id: Timeline ID
            service_name: Service name
            repo_path: Optional repository path filter
        
        Returns:
            Dict with placement statistics
        """
        try:
            self.logger.info(
                f"Placing documents for service '{service_name}' "
                f"in timeline {timeline_id}"
            )
            
            # Get all periods for this timeline
            periods = await self.period_repo.get_by_timeline(
                timeline_id,
                order_by_sequence=True
            )
            
            if not periods:
                self.logger.warning(
                    f"No periods found for timeline {timeline_id}"
                )
                return {
                    "total_documents": 0,
                    "placed_documents": 0,
                    "skipped_documents": 0,
                    "periods_updated": 0
                }
            
            self.logger.info(f"Found {len(periods)} periods")
            
            # Get all latest documents for service
            documents = await self._get_documents_for_service(
                service_name, repo_path
            )
            
            if not documents:
                self.logger.warning(
                    f"No documents found for service '{service_name}'"
                )
                return {
                    "total_documents": 0,
                    "placed_documents": 0,
                    "skipped_documents": 0,
                    "periods_updated": 0
                }
            
            self.logger.info(f"Found {len(documents)} documents to place")
            
            # Place each document in appropriate period(s)
            stats = {
                "total_documents": len(documents),
                "placed_documents": 0,
                "skipped_documents": 0,
                "placements_by_source": {
                    "git_commit": 0,
                    "created_at": 0,
                    "manual": 0
                },
                "periods_updated": 0,
                "period_stats": {}
            }
            
            period_document_counts = {p.id: 0 for p in periods}
            period_commit_counts = {p.id: 0 for p in periods}
            
            for document in documents:
                placement_result = await self._place_document(
                    document, periods
                )
                
                if placement_result:
                    stats["placed_documents"] += 1
                    stats["placements_by_source"][placement_result["source"]] += 1
                    
                    # Update counts
                    period_id = placement_result["period_id"]
                    period_document_counts[period_id] += 1
                    
                    if placement_result.get("has_commit"):
                        period_commit_counts[period_id] += 1
                else:
                    stats["skipped_documents"] += 1
            
            # Update period statistics
            for period in periods:
                doc_count = period_document_counts.get(period.id, 0)
                commit_count = period_commit_counts.get(period.id, 0)
                
                period.document_count = doc_count
                period.commit_count = commit_count
                period.updated_at = datetime.utcnow()
                
                if doc_count > 0:
                    stats["periods_updated"] += 1
                
                stats["period_stats"][str(period.id)] = {
                    "name": period.name,
                    "documents": doc_count,
                    "commits": commit_count
                }
            
            await self.db.commit()
            
            self.logger.info(
                f"✅ Placement complete: {stats['placed_documents']} documents placed, "
                f"{stats['skipped_documents']} skipped, "
                f"{stats['periods_updated']} periods updated"
            )
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to place documents: {e}", exc_info=True)
            await self.db.rollback()
            raise
    
    async def _get_documents_for_service(
        self,
        service_name: str,
        repo_path: Optional[str] = None
    ) -> List[DocumentModel]:
        """
        Get all documents for a service.
        
        Args:
            service_name: Service name
            repo_path: Optional repository path filter
        
        Returns:
            List of documents
        """
        query = select(DocumentModel).where(
            and_(
                DocumentModel.service_name == service_name,
                DocumentModel.is_latest == True
            )
        )
        
        if repo_path:
            query = query.where(DocumentModel.file_path.like(f"{repo_path}%"))
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def _place_document(
        self,
        document: DocumentModel,
        periods: List[TimePeriodModel]
    ) -> Optional[Dict[str, Any]]:
        """
        Place a single document in the appropriate period.
        
        Args:
            document: Document to place
            periods: List of timeline periods (ordered by sequence)
        
        Returns:
            Dict with placement info or None if document couldn't be placed
        """
        try:
            # Determine placement date and source
            placement_info = await self._determine_placement_date(document)
            
            if not placement_info:
                self.logger.warning(
                    f"Cannot determine placement date for document {document.id}"
                )
                return None
            
            placement_date = placement_info["date"]
            placement_source = placement_info["source"]
            git_commit_sha = placement_info.get("git_commit_sha")
            
            # Find the period that contains this date
            target_period = None
            for period in periods:
                if period.start_date <= placement_date <= period.end_date:
                    target_period = period
                    break
            
            if not target_period:
                self.logger.debug(
                    f"Document {document.id} date {placement_date} "
                    f"falls outside all periods"
                )
                return None
            
            # Check if placement already exists
            exists = await self.placement_repo.exists(
                period_id=target_period.id,
                document_id=document.id
            )
            
            if exists:
                self.logger.debug(
                    f"Placement already exists for document {document.id} "
                    f"in period {target_period.id}"
                )
                return {
                    "period_id": target_period.id,
                    "source": placement_source.value,
                    "has_commit": git_commit_sha is not None,
                    "existing": True
                }
            
            # Create placement
            placement_model = DocumentPlacementModel(
                period_id=target_period.id,
                document_id=document.id,
                placement_date=placement_date,
                placement_source=placement_source.value,
                git_commit_sha=git_commit_sha,
                relevance_score=1.0,  # Could be enhanced with relevance scoring
                placement_metadata=placement_info.get("metadata", {})
            )
            
            await self.placement_repo.create(placement_model)
            
            self.logger.debug(
                f"Placed document {document.id} in period {target_period.name} "
                f"(source: {placement_source.value})"
            )
            
            return {
                "period_id": target_period.id,
                "source": placement_source.value,
                "has_commit": git_commit_sha is not None,
                "existing": False
            }
            
        except Exception as e:
            self.logger.error(
                f"Failed to place document {document.id}: {e}",
                exc_info=True
            )
            return None
    
    async def _determine_placement_date(
        self,
        document: DocumentModel
    ) -> Optional[Dict[str, Any]]:
        """
        Determine placement date and source for a document.
        
        Priority:
        1. Git commit date (if git_history mode and commit exists)
        2. Document created_at (if snapshot mode)
        3. Document updated_at (fallback)
        
        Args:
            document: Document model
        
        Returns:
            Dict with date, source, and optional git_commit_sha
        """
        # ✅ FIX #2: Priority 1 - Use document.git_date directly if available
        if document.git_date:
            return {
                "date": document.git_date,
                "source": PlacementSource.GIT_COMMIT,
                "git_commit_sha": document.git_commit_sha,
                "metadata": {
                    "commit_message": document.git_commit_message,
                    "author": document.git_author,
                    "source": "git_date_column"
                }
            }
        
        # Priority 2 - Fallback to git_commits table lookup
        if (
            document.ingestion_mode in ['git_history', 'enriched'] and
            document.git_commit_sha
        ):
            # Get commit to get its date
            result = await self.db.execute(
                select(GitCommitModel).where(
                    GitCommitModel.sha == document.git_commit_sha
                )
            )
            commit = result.scalar_one_or_none()
            
            if commit:
                return {
                    "date": commit.date,
                    "source": PlacementSource.GIT_COMMIT,
                    "git_commit_sha": commit.sha,
                    "metadata": {
                        "commit_message": commit.message,
                        "author": commit.author,
                        "source": "git_commits_table"
                    }
                }
        
        # Priority 3 - Fallback to created_at (snapshot mode or no commit)
        if document.created_at:
            return {
                "date": document.created_at,
                "source": PlacementSource.CREATED_AT,
                "metadata": {
                    "ingestion_mode": document.ingestion_mode
                }
            }
        
        # Last resort: updated_at
        if document.updated_at:
            self.logger.warning(
                f"Using updated_at for document {document.id} "
                f"(no created_at or commit date)"
            )
            return {
                "date": document.updated_at,
                "source": PlacementSource.CREATED_AT,
                "metadata": {
                    "fallback": "updated_at",
                    "ingestion_mode": document.ingestion_mode
                }
            }
        
        return None
    
    async def recompute_placements(
        self,
        timeline_id: UUID
    ) -> Dict[str, Any]:
        """
        Recompute all document placements for a timeline.
        
        Useful when:
        - Periods have been regenerated
        - Documents have been re-ingested
        - Need to fix incorrect placements
        
        Args:
            timeline_id: Timeline ID
        
        Returns:
            Dict with recomputation statistics
        """
        try:
            self.logger.info(f"Recomputing placements for timeline {timeline_id}")
            
            # Get all periods
            periods = await self.period_repo.get_by_timeline(
                timeline_id,
                order_by_sequence=True
            )
            
            if not periods:
                raise ValueError(f"No periods found for timeline {timeline_id}")
            
            # Delete all existing placements
            total_deleted = 0
            for period in periods:
                deleted = await self.placement_repo.delete_by_period(period.id)
                total_deleted += deleted
            
            self.logger.info(f"Deleted {total_deleted} existing placements")
            
            # Get timeline to determine service
            timeline = await self.db.execute(
                select(TimePeriodModel).where(
                    TimePeriodModel.timeline_id == timeline_id
                ).limit(1)
            )
            first_period = timeline.scalar_one_or_none()
            
            if not first_period:
                raise ValueError(f"Cannot determine service for timeline {timeline_id}")
            
            # Get timeline model to find service name
            from ...storage.db_models import TimelineModel
            timeline_result = await self.db.execute(
                select(TimelineModel).where(TimelineModel.id == timeline_id)
            )
            timeline_model = timeline_result.scalar_one_or_none()
            
            if not timeline_model:
                raise ValueError(f"Timeline not found: {timeline_id}")
            
            # Place documents again
            placement_stats = await self.place_documents(
                timeline_id=timeline_id,
                service_name=timeline_model.service_name,
                repo_path=timeline_model.repo_path
            )
            
            return {
                "deleted_placements": total_deleted,
                **placement_stats
            }
            
        except Exception as e:
            self.logger.error(f"Failed to recompute placements: {e}", exc_info=True)
            await self.db.rollback()
            raise

