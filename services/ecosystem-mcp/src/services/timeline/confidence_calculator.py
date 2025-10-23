"""
Temporal Confidence Calculator

Calculates confidence levels for timeline-based analysis based on the ingestion mode
distribution of documents. Determines what temporal features are available.

Confidence Levels:
- HIGH (90%+ git_history): Full temporal analysis available
- MEDIUM (50-90% git_history): Most features available with warnings
- LOW (1-50% git_history): Limited temporal features, heavy fallbacks
- NONE (0% git_history): No temporal analysis, content-based only
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ...storage.db_models import DocumentModel
from ...models.timeline import (
    TemporalConfidence,
    ConfidenceMetadata,
)

logger = logging.getLogger(__name__)


class TemporalConfidenceCalculator:
    """
    Calculates temporal confidence for a set of documents.
    
    Analyzes ingestion mode distribution to determine what temporal
    operations are reliable and which require fallback strategies.
    """
    
    def __init__(self, db_session: AsyncSession):
        """
        Initialize calculator with database session.
        
        Args:
            db_session: Async SQLAlchemy session
        """
        self.db = db_session
        self.logger = logging.getLogger(__name__)
    
    async def calculate_confidence(
        self,
        service_name: Optional[str] = None,
        document_ids: Optional[List[UUID]] = None,
        repo_path: Optional[str] = None
    ) -> ConfidenceMetadata:
        """
        Calculate temporal confidence for documents.
        
        Can calculate for:
        - All documents (no filters)
        - Documents for a specific service
        - Specific document IDs
        - Documents in a specific repository path
        
        Args:
            service_name: Optional service name filter
            document_ids: Optional list of specific document IDs
            repo_path: Optional repository path filter
        
        Returns:
            ConfidenceMetadata with confidence level and capabilities
        """
        try:
            self.logger.info(
                f"Calculating temporal confidence "
                f"(service={service_name}, repo={repo_path}, docs={len(document_ids) if document_ids else 'all'})"
            )
            
            # Build query based on filters
            query = select(
                func.count().label('total'),
                func.count().filter(DocumentModel.ingestion_mode == 'git_history').label('git_history'),
                func.count().filter(DocumentModel.ingestion_mode == 'snapshot').label('snapshot')
            )
            
            # Apply filters
            if service_name:
                query = query.where(DocumentModel.service_name == service_name)
            
            if document_ids:
                query = query.where(DocumentModel.id.in_(document_ids))
            
            if repo_path:
                # Match documents whose file_path starts with repo_path
                query = query.where(DocumentModel.file_path.like(f"{repo_path}%"))
            
            # Only consider latest versions
            query = query.where(DocumentModel.is_latest == True)
            
            # Execute query
            result = await self.db.execute(query)
            row = result.first()
            
            if not row:
                self.logger.warning("No documents found for confidence calculation")
                return self._create_none_confidence(0, 0, 0)
            
            total_docs = row.total or 0
            git_history_docs = row.git_history or 0
            snapshot_docs = row.snapshot or 0
            
            self.logger.info(
                f"Document distribution: total={total_docs}, "
                f"git_history={git_history_docs}, snapshot={snapshot_docs}"
            )
            
            # Handle edge case: no documents
            if total_docs == 0:
                return self._create_none_confidence(0, 0, 0)
            
            # Calculate confidence
            return self._determine_confidence(
                total_docs,
                git_history_docs,
                snapshot_docs
            )
            
        except Exception as e:
            self.logger.error(f"Failed to calculate confidence: {e}", exc_info=True)
            raise
    
    def _determine_confidence(
        self,
        total_docs: int,
        git_history_docs: int,
        snapshot_docs: int
    ) -> ConfidenceMetadata:
        """
        Determine confidence level based on document distribution.
        
        Args:
            total_docs: Total number of documents
            git_history_docs: Documents with git_history mode
            snapshot_docs: Documents with snapshot mode
        
        Returns:
            ConfidenceMetadata with appropriate level and capabilities
        """
        # Calculate percentage
        git_percentage = (git_history_docs / total_docs * 100) if total_docs > 0 else 0.0
        
        self.logger.debug(f"Git history percentage: {git_percentage:.1f}%")
        
        # Determine confidence level and capabilities
        if git_percentage >= 90.0:
            return self._create_high_confidence(total_docs, git_history_docs, snapshot_docs, git_percentage)
        elif git_percentage >= 50.0:
            return self._create_medium_confidence(total_docs, git_history_docs, snapshot_docs, git_percentage)
        elif git_percentage > 0.0:
            return self._create_low_confidence(total_docs, git_history_docs, snapshot_docs, git_percentage)
        else:
            return self._create_none_confidence(total_docs, git_history_docs, snapshot_docs)
    
    def _create_high_confidence(
        self,
        total: int,
        git_history: int,
        snapshot: int,
        git_pct: float
    ) -> ConfidenceMetadata:
        """Create HIGH confidence metadata."""
        self.logger.info(f"HIGH confidence: {git_pct:.1f}% git_history documents")
        
        return ConfidenceMetadata(
            total_documents=total,
            git_history_documents=git_history,
            snapshot_documents=snapshot,
            git_percentage=git_pct,
            can_show_evolution=True,
            can_detect_drift=True,
            can_show_timeline=True,
            can_compare_periods=True,
            fallback_strategy="minimal_fallback",
            warnings=[],
            calculated_at=datetime.utcnow()
        )
    
    def _create_medium_confidence(
        self,
        total: int,
        git_history: int,
        snapshot: int,
        git_pct: float
    ) -> ConfidenceMetadata:
        """Create MEDIUM confidence metadata."""
        warnings = [
            f"Only {git_pct:.1f}% of documents have git history.",
            "Some temporal features may have gaps.",
            "Evolution tracking will be partial for some documents."
        ]
        
        self.logger.info(f"MEDIUM confidence: {git_pct:.1f}% git_history documents")
        
        return ConfidenceMetadata(
            total_documents=total,
            git_history_documents=git_history,
            snapshot_documents=snapshot,
            git_percentage=git_pct,
            can_show_evolution=True,  # Partial
            can_detect_drift=True,    # Partial
            can_show_timeline=True,   # With gaps
            can_compare_periods=True, # With limitations
            fallback_strategy="hybrid_with_warnings",
            warnings=warnings,
            calculated_at=datetime.utcnow()
        )
    
    def _create_low_confidence(
        self,
        total: int,
        git_history: int,
        snapshot: int,
        git_pct: float
    ) -> ConfidenceMetadata:
        """Create LOW confidence metadata."""
        warnings = [
            f"Only {git_pct:.1f}% of documents have git history.",
            "Temporal analysis will be severely limited.",
            "Most features will use content-based fallbacks.",
            "Consider re-ingesting with git_history mode for better results."
        ]
        
        self.logger.warning(f"LOW confidence: {git_pct:.1f}% git_history documents")
        
        return ConfidenceMetadata(
            total_documents=total,
            git_history_documents=git_history,
            snapshot_documents=snapshot,
            git_percentage=git_pct,
            can_show_evolution=False,  # Too limited
            can_detect_drift=False,    # Not reliable
            can_show_timeline=True,    # Content-based only
            can_compare_periods=True,  # Content comparison only
            fallback_strategy="content_based_fallback",
            warnings=warnings,
            calculated_at=datetime.utcnow()
        )
    
    def _create_none_confidence(
        self,
        total: int,
        git_history: int,
        snapshot: int
    ) -> ConfidenceMetadata:
        """Create NONE confidence metadata."""
        warnings = [
            "No documents with git history available.",
            "Temporal analysis is not possible.",
            "Only content-based analysis available.",
            "Re-ingest with git_history mode to enable temporal features."
        ]
        
        self.logger.warning("NONE confidence: No git_history documents found")
        
        return ConfidenceMetadata(
            total_documents=total,
            git_history_documents=git_history,
            snapshot_documents=snapshot,
            git_percentage=0.0,
            can_show_evolution=False,
            can_detect_drift=False,
            can_show_timeline=False,
            can_compare_periods=False,
            fallback_strategy="no_temporal_features",
            warnings=warnings,
            calculated_at=datetime.utcnow()
        )
    
    async def check_pre_flight(
        self,
        service_name: str,
        minimum_confidence: TemporalConfidence = TemporalConfidence.MEDIUM,
        auto_adjust: bool = True
    ) -> Dict[str, any]:
        """
        Pre-flight check before creating a timeline.
        
        Validates that the service has sufficient temporal data for the
        requested operations.
        
        Args:
            service_name: Service to check
            minimum_confidence: Minimum required confidence level
            auto_adjust: If True, automatically allow NONE confidence for snapshot-only services
        
        Returns:
            Dict with:
                - can_proceed: bool
                - confidence_metadata: ConfidenceMetadata
                - recommendation: str
        """
        try:
            self.logger.info(f"Running pre-flight check for service: {service_name}")
            
            # Calculate confidence
            confidence_metadata = await self.calculate_confidence(service_name=service_name)
            
            # Map confidence to enum
            confidence_map = {
                0.0: TemporalConfidence.NONE,
                1.0: TemporalConfidence.LOW,     # > 0%
                50.0: TemporalConfidence.MEDIUM,  # >= 50%
                90.0: TemporalConfidence.HIGH,    # >= 90%
            }
            
            git_pct = confidence_metadata.git_percentage
            
            if git_pct >= 90.0:
                actual_confidence = TemporalConfidence.HIGH
            elif git_pct >= 50.0:
                actual_confidence = TemporalConfidence.MEDIUM
            elif git_pct > 0.0:
                actual_confidence = TemporalConfidence.LOW
            else:
                actual_confidence = TemporalConfidence.NONE
            
            # Check if meets minimum
            confidence_order = {
                TemporalConfidence.NONE: 0,
                TemporalConfidence.LOW: 1,
                TemporalConfidence.MEDIUM: 2,
                TemporalConfidence.HIGH: 3,
            }
            
            can_proceed = confidence_order[actual_confidence] >= confidence_order[minimum_confidence]
            
            # Auto-adjust for snapshot-only services
            if not can_proceed and auto_adjust and actual_confidence == TemporalConfidence.NONE:
                self.logger.warning(
                    f"Service '{service_name}' has no git history (snapshot-only). "
                    f"Auto-adjusting to allow timeline creation with limited temporal features."
                )
                can_proceed = True
                recommendation = (
                    f"⚠️  Service has {actual_confidence.value} confidence (snapshot-only data). "
                    f"Timeline created with limited temporal features. "
                    f"For full temporal analysis, consider re-ingesting with git_history mode."
                )
            elif can_proceed:
                recommendation = f"✅ Service has {actual_confidence.value} confidence. Proceed with timeline creation."
            else:
                recommendation = (
                    f"⚠️  Service has {actual_confidence.value} confidence, "
                    f"but {minimum_confidence.value} is required. "
                    f"Consider re-ingesting with git_history mode."
                )
            
            result = {
                "can_proceed": can_proceed,
                "actual_confidence": actual_confidence.value,
                "required_confidence": minimum_confidence.value,
                "confidence_metadata": confidence_metadata,
                "recommendation": recommendation
            }
            
            self.logger.info(
                f"Pre-flight check complete: can_proceed={can_proceed}, "
                f"confidence={actual_confidence.value}"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Pre-flight check failed: {e}", exc_info=True)
            raise
    
    async def suggest_upgrade_path(
        self,
        service_name: str
    ) -> Dict[str, any]:
        """
        Suggest upgrade path to improve temporal confidence.
        
        Args:
            service_name: Service to analyze
        
        Returns:
            Dict with upgrade suggestions and expected improvements
        """
        try:
            confidence_metadata = await self.calculate_confidence(service_name=service_name)
            
            git_pct = confidence_metadata.git_percentage
            
            suggestions = []
            
            if git_pct == 0.0:
                suggestions.append({
                    "action": "re_ingest_with_git_history",
                    "description": "Re-ingest all documents with git_history mode",
                    "expected_confidence": "HIGH",
                    "benefits": [
                        "Enable full temporal analysis",
                        "Track document evolution",
                        "Detect API/schema drift",
                        "Compare periods accurately"
                    ]
                })
            elif git_pct < 50.0:
                suggestions.append({
                    "action": "re_ingest_snapshot_documents",
                    "description": f"Re-ingest {confidence_metadata.snapshot_documents} snapshot documents with git_history mode",
                    "expected_confidence": "HIGH",
                    "benefits": [
                        "Fill temporal gaps",
                        "Improve evolution tracking",
                        "Enable reliable drift detection"
                    ]
                })
            elif git_pct < 90.0:
                suggestions.append({
                    "action": "complete_git_history",
                    "description": f"Complete git_history for remaining {confidence_metadata.snapshot_documents} documents",
                    "expected_confidence": "HIGH",
                    "benefits": [
                        "Achieve HIGH confidence",
                        "Remove all temporal gaps",
                        "Enable full feature set"
                    ]
                })
            else:
                suggestions.append({
                    "action": "no_action_needed",
                    "description": "Service already has HIGH confidence",
                    "expected_confidence": "HIGH",
                    "benefits": ["All temporal features available"]
                })
            
            return {
                "current_confidence": git_pct,
                "suggestions": suggestions,
                "estimated_documents_to_reingest": confidence_metadata.snapshot_documents
            }
            
        except Exception as e:
            self.logger.error(f"Failed to generate upgrade suggestions: {e}", exc_info=True)
            raise

