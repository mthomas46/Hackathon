"""
Automated Refresher Service

Automatically refreshes stale documentation:
- Auto-update docs when code changes
- Support incremental, full, and smart strategies
- Schedule-based and event-based triggers
- Integration with ingestion pipeline
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from uuid import UUID
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession

from ...storage.db_models import DocumentModel
from ...storage.repositories import DocumentRepository
from ...storage import get_database
from .staleness_detector import StalenessDetector

logger = logging.getLogger(__name__)


class RefreshStrategy(str, Enum):
    """Refresh strategy types."""
    INCREMENTAL = "incremental"  # Only refresh changed files
    FULL = "full"  # Refresh all files
    SMART = "smart"  # Intelligently decide what to refresh based on staleness


class RefreshTrigger(str, Enum):
    """Refresh trigger types."""
    MANUAL = "manual"  # User-initiated
    SCHEDULED = "scheduled"  # Time-based schedule
    EVENT_DRIVEN = "event_driven"  # Code change detected
    STALENESS_THRESHOLD = "staleness_threshold"  # Staleness threshold exceeded


class AutomatedRefresher:
    """
    Automate documentation refresh.
    
    Features:
    - Multiple refresh strategies
    - Event-driven and scheduled refresh
    - Smart refresh based on staleness
    - Integration with ingestion pipeline
    """
    
    def __init__(self):
        """Initialize automated refresher."""
        self.logger = logging.getLogger(__name__)
        self.staleness_detector = StalenessDetector()
    
    async def refresh_documentation(
        self,
        service_name: str,
        strategy: RefreshStrategy = RefreshStrategy.SMART,
        trigger: RefreshTrigger = RefreshTrigger.MANUAL,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Refresh documentation for a service.
        
        Args:
            service_name: Service to refresh
            strategy: Refresh strategy to use
            trigger: What triggered the refresh
            force: Force refresh even if not needed
        
        Returns:
            Refresh results
        """
        try:
            self.logger.info(
                f"🔄 Refreshing documentation for {service_name} "
                f"(strategy={strategy}, trigger={trigger})"
            )
            
            # Determine what needs refreshing
            if strategy == RefreshStrategy.INCREMENTAL:
                targets = await self._identify_incremental_targets(service_name)
            elif strategy == RefreshStrategy.FULL:
                targets = await self._identify_full_targets(service_name)
            else:  # SMART
                targets = await self._identify_smart_targets(service_name)
            
            if not targets and not force:
                return {
                    "service_name": service_name,
                    "strategy": strategy,
                    "trigger": trigger,
                    "status": "skipped",
                    "reason": "No documents need refreshing",
                    "documents_refreshed": 0
                }
            
            # Execute refresh
            refresh_results = await self._execute_refresh(targets, service_name)
            
            return {
                "service_name": service_name,
                "strategy": strategy,
                "trigger": trigger,
                "status": "completed",
                "documents_identified": len(targets),
                "documents_refreshed": refresh_results["refreshed"],
                "documents_failed": refresh_results["failed"],
                "refresh_details": refresh_results["details"],
                "started_at": refresh_results["started_at"],
                "completed_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to refresh documentation: {e}", exc_info=True)
            raise
    
    async def _identify_incremental_targets(
        self,
        service_name: str
    ) -> List[Dict[str, Any]]:
        """Identify documents for incremental refresh."""
        # Incremental: Only documents changed in last N days
        days_threshold = 7
        
        async with get_database().session() as session:
            doc_repo = DocumentRepository(session)
            documents = await doc_repo.get_by_service(service_name, limit=10000)
            
            cutoff_date = datetime.utcnow() - timedelta(days=days_threshold)
            
            targets = []
            for doc in documents:
                if doc.updated_at and doc.updated_at < cutoff_date:
                    targets.append({
                        "document_id": str(doc.id),
                        "file_path": doc.file_path,
                        "reason": f"Not updated in {days_threshold} days"
                    })
            
            return targets
    
    async def _identify_full_targets(
        self,
        service_name: str
    ) -> List[Dict[str, Any]]:
        """Identify all documents for full refresh."""
        async with get_database().session() as session:
            doc_repo = DocumentRepository(session)
            documents = await doc_repo.get_by_service(service_name, limit=10000)
            
            return [
                {
                    "document_id": str(doc.id),
                    "file_path": doc.file_path,
                    "reason": "Full refresh requested"
                }
                for doc in documents
            ]
    
    async def _identify_smart_targets(
        self,
        service_name: str
    ) -> List[Dict[str, Any]]:
        """Intelligently identify documents needing refresh."""
        # Use staleness detection to find what needs updating
        staleness_results = await self.staleness_detector.detect_stale_documents(
            service_name=service_name,
            limit=500
        )
        
        # Prioritize critical and high severity
        targets = []
        
        for severity in ["CRITICAL", "HIGH"]:
            stale_docs = staleness_results["stale_documents"][severity]
            for doc in stale_docs:
                targets.append({
                    "document_id": doc["document_id"],
                    "file_path": doc["file_path"],
                    "reason": doc["staleness_reason"],
                    "severity": severity
                })
        
        return targets
    
    async def _execute_refresh(
        self,
        targets: List[Dict[str, Any]],
        service_name: str
    ) -> Dict[str, Any]:
        """Execute the actual refresh."""
        # This is a placeholder - in production, you would:
        # 1. Trigger the ingestion pipeline for each target
        # 2. Track progress and results
        # 3. Handle errors and retries
        
        self.logger.info(f"   📝 Would refresh {len(targets)} documents")
        
        # For now, just return a simulation
        return {
            "refreshed": 0,  # Would be actual count
            "failed": 0,
            "details": {
                "note": "Refresh simulation - actual ingestion not triggered",
                "targets": targets[:10]  # First 10 for inspection
            },
            "started_at": datetime.utcnow().isoformat()
        }
    
    async def schedule_refresh(
        self,
        service_name: str,
        schedule: str,
        strategy: RefreshStrategy = RefreshStrategy.SMART
    ) -> Dict[str, Any]:
        """
        Schedule automatic refresh.
        
        Args:
            service_name: Service to refresh
            schedule: Cron-style schedule (e.g., "0 2 * * *" for daily at 2am)
            strategy: Refresh strategy
        
        Returns:
            Schedule configuration
        """
        try:
            self.logger.info(f"📅 Scheduling refresh for {service_name}: {schedule}")
            
            # This is a placeholder - in production, you would:
            # 1. Store schedule in database
            # 2. Register with scheduler (e.g., APScheduler, Celery)
            # 3. Return schedule ID
            
            return {
                "service_name": service_name,
                "schedule": schedule,
                "strategy": strategy,
                "status": "scheduled",
                "next_run": "To be implemented",
                "note": "Scheduling not yet implemented - would integrate with task scheduler"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to schedule refresh: {e}", exc_info=True)
            raise
    
    async def get_refresh_status(
        self,
        service_name: str
    ) -> Dict[str, Any]:
        """
        Get refresh status for a service.
        
        Args:
            service_name: Service to check
        
        Returns:
            Refresh status and history
        """
        try:
            self.logger.info(f"📊 Getting refresh status for {service_name}")
            
            # Check staleness
            staleness_summary = await self.staleness_detector.get_staleness_summary(
                service_name=service_name
            )
            
            # Determine if refresh is needed
            stale_pct = staleness_summary["summary"]["stale_percentage"]
            critical_count = staleness_summary["summary"]["critical_issues"]
            
            needs_refresh = stale_pct > 25 or critical_count > 0
            
            if needs_refresh:
                recommendation = (
                    f"⚠️ Refresh recommended: {stale_pct:.1f}% stale, "
                    f"{critical_count} critical issues"
                )
            else:
                recommendation = "✅ Documentation is fresh, no refresh needed"
            
            return {
                "service_name": service_name,
                "needs_refresh": needs_refresh,
                "staleness_summary": staleness_summary["summary"],
                "recommendation": recommendation,
                "suggested_strategy": (
                    RefreshStrategy.SMART if needs_refresh
                    else RefreshStrategy.INCREMENTAL
                ),
                "checked_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get refresh status: {e}", exc_info=True)
            raise
    
    async def refresh_single_document(
        self,
        document_id: UUID
    ) -> Dict[str, Any]:
        """
        Refresh a single document.
        
        Args:
            document_id: Document to refresh
        
        Returns:
            Refresh result
        """
        try:
            self.logger.info(f"🔄 Refreshing single document: {document_id}")
            
            async with get_database().session() as session:
                doc_repo = DocumentRepository(session)
                doc = await doc_repo.get_by_id(document_id)
                
                if not doc:
                    raise ValueError(f"Document not found: {document_id}")
                
                # Execute refresh for single document
                result = await self._execute_refresh(
                    [{
                        "document_id": str(document_id),
                        "file_path": doc.file_path,
                        "reason": "Manual single document refresh"
                    }],
                    doc.service_name or "unknown"
                )
                
                return {
                    "document_id": str(document_id),
                    "file_path": doc.file_path,
                    "status": "completed",
                    "result": result
                }
                
        except Exception as e:
            self.logger.error(f"Failed to refresh document: {e}", exc_info=True)
            raise

