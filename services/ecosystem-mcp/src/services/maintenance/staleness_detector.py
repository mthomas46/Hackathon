"""
Staleness Detector Service

Detects documentation that has become outdated:
- Documents not updated despite code changes
- Documents with old timestamps relative to their code files
- Configurable staleness thresholds
- Integration with git history and timeline system
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from uuid import UUID
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from ...storage.db_models import DocumentModel, GitCommitModel
from ...storage.repositories import DocumentRepository
from ...storage.repositories.timeline_repository import (
    TimelineRepository,
    DocumentPlacementRepository
)
from ...storage import get_database

logger = logging.getLogger(__name__)


class StaleDocument:
    """Represents a stale document with metadata."""
    
    def __init__(
        self,
        document_id: UUID,
        file_path: str,
        last_updated: datetime,
        last_code_change: Optional[datetime],
        staleness_days: int,
        staleness_reason: str,
        severity: str
    ):
        self.document_id = document_id
        self.file_path = file_path
        self.last_updated = last_updated
        self.last_code_change = last_code_change
        self.staleness_days = staleness_days
        self.staleness_reason = staleness_reason
        self.severity = severity  # CRITICAL, HIGH, MEDIUM, LOW
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "document_id": str(self.document_id),
            "file_path": self.file_path,
            "last_updated": self.last_updated.isoformat(),
            "last_code_change": self.last_code_change.isoformat() if self.last_code_change else None,
            "staleness_days": self.staleness_days,
            "staleness_reason": self.staleness_reason,
            "severity": self.severity
        }


class StalenessDetector:
    """
    Detect stale documentation.
    
    Features:
    - Code-documentation drift detection
    - Age-based staleness detection
    - Timeline-aware staleness checks
    - Configurable thresholds
    - Severity classification
    """
    
    def __init__(
        self,
        staleness_threshold_days: int = 90,
        critical_threshold_days: int = 180
    ):
        """
        Initialize staleness detector.
        
        Args:
            staleness_threshold_days: Days after which docs are considered stale
            critical_threshold_days: Days after which staleness is critical
        """
        self.staleness_threshold = staleness_threshold_days
        self.critical_threshold = critical_threshold_days
        self.logger = logging.getLogger(__name__)
    
    async def detect_stale_documents(
        self,
        service_name: Optional[str] = None,
        timeline_id: Optional[UUID] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Detect stale documents.
        
        Args:
            service_name: Optional service filter
            timeline_id: Optional timeline filter
            limit: Maximum results
        
        Returns:
            Detection results with stale documents categorized by severity
        """
        try:
            self.logger.info(f"🔍 Detecting stale documents (service={service_name})")
            
            async with get_database().session() as session:
                # Get documents
                doc_repo = DocumentRepository(session)
                
                if timeline_id:
                    # Get documents in timeline
                    documents = await self._get_timeline_documents(session, timeline_id)
                elif service_name:
                    # Get documents by service
                    documents = await doc_repo.get_by_service(service_name, limit=limit * 2)
                else:
                    # Get all documents
                    documents = await doc_repo.get_all(limit=limit * 2)
                
                self.logger.info(f"   📄 Analyzing {len(documents)} documents")
                
                # Analyze each document for staleness
                stale_docs = []
                for doc in documents:
                    stale_info = await self._analyze_document_staleness(session, doc)
                    if stale_info:
                        stale_docs.append(stale_info)
                
                # Sort by severity and staleness
                stale_docs.sort(
                    key=lambda x: (
                        {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}[x.severity],
                        -x.staleness_days
                    )
                )
                
                # Limit results
                stale_docs = stale_docs[:limit]
                
                # Categorize by severity
                categorized = {
                    "CRITICAL": [d for d in stale_docs if d.severity == "CRITICAL"],
                    "HIGH": [d for d in stale_docs if d.severity == "HIGH"],
                    "MEDIUM": [d for d in stale_docs if d.severity == "MEDIUM"],
                    "LOW": [d for d in stale_docs if d.severity == "LOW"]
                }
                
                return {
                    "total_analyzed": len(documents),
                    "total_stale": len(stale_docs),
                    "stale_percentage": (len(stale_docs) / len(documents) * 100) if documents else 0,
                    "by_severity": {
                        "CRITICAL": len(categorized["CRITICAL"]),
                        "HIGH": len(categorized["HIGH"]),
                        "MEDIUM": len(categorized["MEDIUM"]),
                        "LOW": len(categorized["LOW"])
                    },
                    "stale_documents": {
                        "CRITICAL": [d.to_dict() for d in categorized["CRITICAL"]],
                        "HIGH": [d.to_dict() for d in categorized["HIGH"]],
                        "MEDIUM": [d.to_dict() for d in categorized["MEDIUM"]],
                        "LOW": [d.to_dict() for d in categorized["LOW"]]
                    },
                    "metadata": {
                        "service_name": service_name,
                        "timeline_id": str(timeline_id) if timeline_id else None,
                        "staleness_threshold_days": self.staleness_threshold,
                        "critical_threshold_days": self.critical_threshold,
                        "analyzed_at": datetime.utcnow().isoformat()
                    }
                }
                
        except Exception as e:
            self.logger.error(f"Failed to detect stale documents: {e}", exc_info=True)
            raise
    
    async def _analyze_document_staleness(
        self,
        session: AsyncSession,
        document: DocumentModel
    ) -> Optional[StaleDocument]:
        """
        Analyze a single document for staleness.
        
        Returns StaleDocument if stale, None otherwise.
        """
        try:
            now = datetime.utcnow()
            
            # Get document age
            doc_updated = document.updated_at or document.created_at
            days_since_update = (now - doc_updated).days
            
            # Check if document is old enough to be considered stale
            if days_since_update < self.staleness_threshold:
                return None
            
            # Find related git commits
            last_code_change = await self._find_last_code_change(session, document)
            
            # Determine staleness reason and severity
            staleness_info = self._determine_staleness(
                document,
                doc_updated,
                last_code_change,
                days_since_update
            )
            
            if staleness_info:
                return StaleDocument(
                    document_id=document.id,
                    file_path=document.file_path,
                    last_updated=doc_updated,
                    last_code_change=last_code_change,
                    staleness_days=days_since_update,
                    staleness_reason=staleness_info["reason"],
                    severity=staleness_info["severity"]
                )
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Failed to analyze document {document.id}: {e}")
            return None
    
    async def _find_last_code_change(
        self,
        session: AsyncSession,
        document: DocumentModel
    ) -> Optional[datetime]:
        """Find the last time the code file was changed."""
        try:
            # Try to find git commits related to this document
            # This is a simplified version - in production, you'd want more sophisticated matching
            
            # Extract file path from document
            file_path = Path(document.file_path)
            
            # Find commits that modified files in the same directory
            stmt = select(GitCommitModel).where(
                or_(
                    GitCommitModel.file_path.like(f"%{file_path.stem}%"),
                    GitCommitModel.file_path.like(f"%{file_path.parent}%")
                )
            ).order_by(GitCommitModel.commit_date.desc()).limit(1)
            
            result = await session.execute(stmt)
            commit = result.scalar_one_or_none()
            
            if commit:
                return commit.commit_date
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Failed to find last code change: {e}")
            return None
    
    def _determine_staleness(
        self,
        document: DocumentModel,
        doc_updated: datetime,
        last_code_change: Optional[datetime],
        days_since_update: int
    ) -> Optional[Dict[str, Any]]:
        """
        Determine if document is stale and classify severity.
        
        Returns dict with reason and severity, or None if not stale.
        """
        # Critical: Very old documents
        if days_since_update >= self.critical_threshold:
            return {
                "reason": f"Document not updated in {days_since_update} days (critical threshold: {self.critical_threshold})",
                "severity": "CRITICAL"
            }
        
        # High: Code changed but doc didn't
        if last_code_change and last_code_change > doc_updated:
            days_drift = (last_code_change - doc_updated).days
            if days_drift > 30:  # More than a month of drift
                return {
                    "reason": f"Code changed {days_drift} days after doc was updated",
                    "severity": "HIGH"
                }
            else:
                return {
                    "reason": f"Code changed {days_drift} days after doc was updated",
                    "severity": "MEDIUM"
                }
        
        # Medium: Old but not critical
        if days_since_update >= self.staleness_threshold:
            return {
                "reason": f"Document not updated in {days_since_update} days",
                "severity": "MEDIUM"
            }
        
        return None
    
    async def _get_timeline_documents(
        self,
        session: AsyncSession,
        timeline_id: UUID
    ) -> List[DocumentModel]:
        """Get all documents in a timeline."""
        placement_repo = DocumentPlacementRepository(session)
        doc_repo = DocumentRepository(session)
        
        # Get all periods in timeline
        from ...storage.repositories.timeline_repository import TimePeriodRepository
        period_repo = TimePeriodRepository(session)
        periods = await period_repo.get_by_timeline(timeline_id)
        
        # Get all documents from all periods
        document_ids = set()
        for period in periods:
            placements = await placement_repo.get_by_period(period.id, limit=10000)
            for placement in placements:
                document_ids.add(placement.document_id)
        
        # Fetch documents
        documents = []
        for doc_id in document_ids:
            doc = await doc_repo.get_by_id(doc_id)
            if doc:
                documents.append(doc)
        
        return documents
    
    async def get_staleness_summary(
        self,
        service_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get a summary of documentation staleness.
        
        Args:
            service_name: Optional service filter
        
        Returns:
            Summary statistics
        """
        try:
            self.logger.info("📊 Generating staleness summary")
            
            detection_results = await self.detect_stale_documents(
                service_name=service_name,
                limit=1000
            )
            
            return {
                "summary": {
                    "total_documents": detection_results["total_analyzed"],
                    "stale_documents": detection_results["total_stale"],
                    "stale_percentage": detection_results["stale_percentage"],
                    "critical_issues": detection_results["by_severity"]["CRITICAL"],
                    "high_issues": detection_results["by_severity"]["HIGH"],
                    "medium_issues": detection_results["by_severity"]["MEDIUM"],
                    "low_issues": detection_results["by_severity"]["LOW"]
                },
                "recommendations": self._generate_recommendations(detection_results),
                "metadata": detection_results["metadata"]
            }
            
        except Exception as e:
            self.logger.error(f"Failed to generate staleness summary: {e}", exc_info=True)
            raise
    
    def _generate_recommendations(self, detection_results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on staleness analysis."""
        recommendations = []
        
        critical_count = detection_results["by_severity"]["CRITICAL"]
        high_count = detection_results["by_severity"]["HIGH"]
        stale_pct = detection_results["stale_percentage"]
        
        if critical_count > 0:
            recommendations.append(
                f"⚠️ CRITICAL: {critical_count} documents severely outdated - "
                "immediate attention required"
            )
        
        if high_count > 0:
            recommendations.append(
                f"❗ {high_count} documents have code-documentation drift - "
                "review and update soon"
            )
        
        if stale_pct > 50:
            recommendations.append(
                f"📉 {stale_pct:.1f}% of documentation is stale - "
                "consider enabling automated refresh"
            )
        elif stale_pct > 25:
            recommendations.append(
                f"⚠️ {stale_pct:.1f}% of documentation is stale - "
                "schedule documentation review"
            )
        
        if not recommendations:
            recommendations.append("✅ Documentation freshness is good!")
        
        return recommendations

