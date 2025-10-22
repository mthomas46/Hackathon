"""
Drift Detector Service

Detects code-documentation drift with hybrid approach:
- Full drift detection (git_history mode)
- Content comparison (snapshot mode)
- Hybrid mode (mixed documents)
- API/data contract change detection
- Confidence-aware drift analysis
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ...storage.db_models import DocumentModel, GitCommitModel
from ...storage.repositories import DocumentRepository
from ...storage.repositories.timeline_repository import TimelineRepository, TimePeriodRepository
from ...storage import get_database
from .confidence_calculator import TemporalConfidenceCalculator
from ...models.timeline import TemporalConfidence

logger = logging.getLogger(__name__)


class DriftDetection:
    """Represents a detected drift."""
    
    def __init__(
        self,
        drift_type: str,
        severity: str,
        description: str,
        document_id: UUID,
        file_path: str,
        detection_method: str,
        last_doc_update: datetime,
        last_code_update: Optional[datetime],
        drift_days: int,
        recommendation: str
    ):
        self.drift_type = drift_type
        self.severity = severity
        self.description = description
        self.document_id = document_id
        self.file_path = file_path
        self.detection_method = detection_method
        self.last_doc_update = last_doc_update
        self.last_code_update = last_code_update
        self.drift_days = drift_days
        self.recommendation = recommendation
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "drift_type": self.drift_type,
            "severity": self.severity,
            "description": self.description,
            "document_id": str(self.document_id),
            "file_path": self.file_path,
            "detection_method": self.detection_method,
            "last_doc_update": self.last_doc_update.isoformat(),
            "last_code_update": self.last_code_update.isoformat() if self.last_code_update else None,
            "drift_days": self.drift_days,
            "recommendation": self.recommendation
        }


class DriftDetector:
    """
    Detect code-documentation drift.
    
    Features:
    - Hybrid drift detection (git + content)
    - API/contract change detection
    - Confidence-aware analysis
    - Multiple detection strategies
    """
    
    def __init__(self):
        """Initialize drift detector."""
        self.logger = logging.getLogger(__name__)
        self.confidence_calculator = TemporalConfidenceCalculator()
    
    async def detect_drift(
        self,
        service_name: Optional[str] = None,
        timeline_id: Optional[UUID] = None,
        detection_mode: str = "hybrid"  # hybrid, git_only, content_only
    ) -> Dict[str, Any]:
        """
        Detect code-documentation drift.
        
        Args:
            service_name: Optional service filter
            timeline_id: Optional timeline filter
            detection_mode: Detection strategy (hybrid, git_only, content_only)
        
        Returns:
            Drift detection results
        """
        try:
            self.logger.info(f"🔍 Detecting drift (service={service_name}, mode={detection_mode})")
            
            drifts = []
            
            # Get confidence level for timeline
            confidence = await self._get_confidence_level(timeline_id, service_name)
            
            # Choose detection strategy based on mode and confidence
            if detection_mode == "hybrid" or confidence in ["HIGH", "MEDIUM"]:
                # Use git-based detection if available
                git_drifts = await self._detect_git_drift(service_name, timeline_id)
                drifts.extend(git_drifts)
            
            if detection_mode == "hybrid" or detection_mode == "content_only" or confidence in ["LOW", "NONE"]:
                # Fallback to content-based detection
                content_drifts = await self._detect_content_drift(service_name)
                drifts.extend(content_drifts)
            
            # Detect API/contract changes
            api_drifts = await self._detect_api_drift(service_name)
            drifts.extend(api_drifts)
            
            # Remove duplicates
            drifts = self._deduplicate_drifts(drifts)
            
            # Categorize by severity
            categorized = {
                "CRITICAL": [d for d in drifts if d.severity == "CRITICAL"],
                "HIGH": [d for d in drifts if d.severity == "HIGH"],
                "MEDIUM": [d for d in drifts if d.severity == "MEDIUM"],
                "LOW": [d for d in drifts if d.severity == "LOW"]
            }
            
            # Generate recommendations
            recommendations = self._generate_drift_recommendations(drifts, confidence)
            
            return {
                "total_drifts": len(drifts),
                "detection_mode": detection_mode,
                "confidence_level": confidence,
                "by_severity": {
                    "CRITICAL": len(categorized["CRITICAL"]),
                    "HIGH": len(categorized["HIGH"]),
                    "MEDIUM": len(categorized["MEDIUM"]),
                    "LOW": len(categorized["LOW"])
                },
                "by_type": self._group_by_type(drifts),
                "drifts": {
                    "CRITICAL": [d.to_dict() for d in categorized["CRITICAL"]],
                    "HIGH": [d.to_dict() for d in categorized["HIGH"]],
                    "MEDIUM": [d.to_dict() for d in categorized["MEDIUM"]],
                    "LOW": [d.to_dict() for d in categorized["LOW"]]
                },
                "recommendations": recommendations,
                "metadata": {
                    "service_name": service_name,
                    "timeline_id": str(timeline_id) if timeline_id else None,
                    "analyzed_at": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to detect drift: {e}", exc_info=True)
            raise
    
    async def _get_confidence_level(
        self,
        timeline_id: Optional[UUID],
        service_name: Optional[str]
    ) -> str:
        """Get confidence level for timeline or service."""
        if not timeline_id:
            return "LOW"  # Default
        
        async with get_database().session() as session:
            timeline_repo = TimelineRepository(session)
            timeline = await timeline_repo.get_by_id(timeline_id)
            
            if timeline:
                return timeline.confidence_level
            
            return "LOW"
    
    async def _detect_git_drift(
        self,
        service_name: Optional[str],
        timeline_id: Optional[UUID]
    ) -> List[DriftDetection]:
        """Detect drift using git history."""
        drifts = []
        
        async with get_database().session() as session:
            doc_repo = DocumentRepository(session)
            
            # Get documents
            if service_name:
                documents = await doc_repo.get_by_service(service_name, limit=1000)
            else:
                documents = await doc_repo.get_all(limit=1000)
            
            for doc in documents:
                # Try to find related git commits
                last_code_change = await self._find_last_code_change(session, doc)
                
                if not last_code_change:
                    continue
                
                doc_updated = doc.updated_at or doc.created_at
                
                # Check if code was updated after docs
                if last_code_change > doc_updated:
                    drift_days = (last_code_change - doc_updated).days
                    
                    if drift_days > 90:
                        severity = "CRITICAL"
                    elif drift_days > 30:
                        severity = "HIGH"
                    elif drift_days > 7:
                        severity = "MEDIUM"
                    else:
                        severity = "LOW"
                    
                    drifts.append(DriftDetection(
                        drift_type="code_doc_drift",
                        severity=severity,
                        description=f"Code updated {drift_days} days after documentation",
                        document_id=doc.id,
                        file_path=doc.file_path,
                        detection_method="git_history",
                        last_doc_update=doc_updated,
                        last_code_update=last_code_change,
                        drift_days=drift_days,
                        recommendation=f"Update documentation to reflect recent code changes"
                    ))
        
        return drifts
    
    async def _detect_content_drift(
        self,
        service_name: Optional[str]
    ) -> List[DriftDetection]:
        """Detect drift using content analysis."""
        drifts = []
        
        async with get_database().session() as session:
            doc_repo = DocumentRepository(session)
            
            # Get documents
            if service_name:
                documents = await doc_repo.get_by_service(service_name, limit=1000)
            else:
                documents = await doc_repo.get_all(limit=1000)
            
            # Look for markers of outdated content
            outdated_markers = [
                "deprecated",
                "obsolete",
                "to be updated",
                "coming soon",
                "not yet implemented"
            ]
            
            for doc in documents:
                if not doc.content:
                    continue
                
                content_lower = doc.content.lower()
                
                # Check for outdated markers
                for marker in outdated_markers:
                    if marker in content_lower:
                        drifts.append(DriftDetection(
                            drift_type="outdated_content",
                            severity="MEDIUM",
                            description=f"Document contains '{marker}' marker",
                            document_id=doc.id,
                            file_path=doc.file_path,
                            detection_method="content_analysis",
                            last_doc_update=doc.updated_at or doc.created_at,
                            last_code_update=None,
                            drift_days=0,
                            recommendation=f"Review and update content marked as '{marker}'"
                        ))
                        break  # Only report once per document
        
        return drifts
    
    async def _detect_api_drift(
        self,
        service_name: Optional[str]
    ) -> List[DriftDetection]:
        """Detect API/contract changes."""
        drifts = []
        
        # This is a simplified version
        # In production, you'd parse API definitions and compare versions
        
        async with get_database().session() as session:
            doc_repo = DocumentRepository(session)
            
            # Get API-related documents
            if service_name:
                documents = await doc_repo.get_by_service(service_name, limit=1000)
            else:
                documents = await doc_repo.get_all(limit=1000)
            
            api_docs = [
                d for d in documents
                if d.file_path and ('api' in d.file_path.lower() or 'endpoint' in d.file_path.lower())
            ]
            
            # Check for very old API docs (likely drift)
            for doc in api_docs:
                doc_age = (datetime.utcnow() - (doc.updated_at or doc.created_at)).days
                
                if doc_age > 180:  # 6 months
                    drifts.append(DriftDetection(
                        drift_type="api_drift",
                        severity="HIGH",
                        description=f"API documentation not updated in {doc_age} days",
                        document_id=doc.id,
                        file_path=doc.file_path,
                        detection_method="api_analysis",
                        last_doc_update=doc.updated_at or doc.created_at,
                        last_code_update=None,
                        drift_days=doc_age,
                        recommendation="Verify API documentation matches current implementation"
                    ))
        
        return drifts
    
    async def _find_last_code_change(
        self,
        session: AsyncSession,
        document: DocumentModel
    ) -> Optional[datetime]:
        """Find last code change related to document."""
        from pathlib import Path
        from sqlalchemy import select, or_
        
        # Extract path components
        file_path = Path(document.file_path)
        
        # Try to find commits
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
    
    def _deduplicate_drifts(
        self,
        drifts: List[DriftDetection]
    ) -> List[DriftDetection]:
        """Remove duplicate drift detections."""
        seen = set()
        unique_drifts = []
        
        for drift in drifts:
            key = (drift.document_id, drift.drift_type)
            if key not in seen:
                seen.add(key)
                unique_drifts.append(drift)
        
        return unique_drifts
    
    def _group_by_type(self, drifts: List[DriftDetection]) -> Dict[str, int]:
        """Group drifts by type."""
        from collections import defaultdict
        types = defaultdict(int)
        for drift in drifts:
            types[drift.drift_type] += 1
        return dict(types)
    
    def _generate_drift_recommendations(
        self,
        drifts: List[DriftDetection],
        confidence: str
    ) -> List[Dict[str, Any]]:
        """Generate prioritized recommendations."""
        recommendations = []
        
        critical_drifts = [d for d in drifts if d.severity == "CRITICAL"]
        high_drifts = [d for d in drifts if d.severity == "HIGH"]
        
        if critical_drifts:
            recommendations.append({
                "priority": "CRITICAL",
                "title": f"Address {len(critical_drifts)} critical drift issues",
                "actions": [
                    "Update documentation for affected files immediately",
                    "Review code changes and sync with docs",
                    "Set up automated drift detection"
                ]
            })
        
        if high_drifts:
            recommendations.append({
                "priority": "HIGH",
                "title": f"Address {len(high_drifts)} high-priority drift issues",
                "actions": [
                    "Schedule documentation update sprint",
                    "Review API changes and update docs",
                    "Establish doc update process"
                ]
            })
        
        # Confidence-based recommendations
        if confidence in ["LOW", "NONE"]:
            recommendations.append({
                "priority": "MEDIUM",
                "title": "Improve drift detection accuracy",
                "actions": [
                    "Enable git history tracking for better drift detection",
                    "Add temporal metadata to documents",
                    "Consider upgrading to git_history ingestion mode"
                ]
            })
        
        return recommendations
    
    async def get_drift_summary(
        self,
        service_name: str
    ) -> Dict[str, Any]:
        """
        Get drift summary for a service.
        
        Args:
            service_name: Service to analyze
        
        Returns:
            Drift summary with statistics
        """
        try:
            self.logger.info(f"📊 Generating drift summary for {service_name}")
            
            result = await self.detect_drift(service_name=service_name, detection_mode="hybrid")
            
            return {
                "service_name": service_name,
                "summary": {
                    "total_drifts": result["total_drifts"],
                    "critical_drifts": result["by_severity"]["CRITICAL"],
                    "high_drifts": result["by_severity"]["HIGH"],
                    "detection_mode": result["detection_mode"],
                    "confidence_level": result["confidence_level"]
                },
                "top_recommendations": result["recommendations"][:3],
                "metadata": result["metadata"]
            }
            
        except Exception as e:
            self.logger.error(f"Failed to generate drift summary: {e}", exc_info=True)
            raise

