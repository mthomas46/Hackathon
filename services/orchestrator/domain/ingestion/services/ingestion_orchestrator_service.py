"""Ingestion Orchestrator Service Domain Service"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio

from ..value_objects.ingestion_request import IngestionRequest
from ..value_objects.ingestion_result import IngestionResult
from ..value_objects.ingestion_status import IngestionStatus
from ..value_objects.ingestion_source_type import IngestionSourceType


class IngestionOrchestratorService:
    """Domain service for orchestrating ingestion workflows."""

    def __init__(self):
        """Initialize ingestion orchestrator service."""
        self._active_ingestions: Dict[str, IngestionResult] = {}
        self._completed_ingestions: Dict[str, IngestionResult] = {}

    def create_ingestion_request(
        self,
        source_url: str,
        source_type: IngestionSourceType,
        correlation_id: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        scope: Optional[Dict[str, Any]] = None,
        priority: int = 5,
        requested_by: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> IngestionRequest:
        """
        Create a new ingestion request.

        Args:
            source_url: URL or identifier of the source to ingest
            source_type: Type of the ingestion source
            correlation_id: Optional correlation ID for tracking
            parameters: Ingestion-specific parameters
            scope: Scope limitations for the ingestion
            priority: Priority level (1-10)
            requested_by: User who requested the ingestion
            tags: Tags for categorization

        Returns:
            IngestionRequest: The created ingestion request
        """
        return IngestionRequest(
            source_url=source_url,
            source_type=source_type,
            correlation_id=correlation_id,
            parameters=parameters,
            scope=scope,
            priority=priority,
            requested_by=requested_by,
            tags=tags
        )

    async def start_ingestion(self, request: IngestionRequest) -> IngestionResult:
        """
        Start an ingestion process for the given request.

        Args:
            request: The ingestion request to process

        Returns:
            IngestionResult: The initial ingestion result
        """
        # Create initial result
        result = IngestionResult(
            request_id=request.request_id,
            status=IngestionStatus.QUEUED
        )

        # Store as active ingestion
        self._active_ingestions[result.ingestion_id] = result

        # Start the ingestion process asynchronously
        asyncio.create_task(self._execute_ingestion(result, request))

        return result

    async def _execute_ingestion(self, result: IngestionResult, request: IngestionRequest):
        """
        Execute the ingestion process.

        Args:
            result: The ingestion result to update
            request: The ingestion request
        """
        try:
            # Mark as started
            result.mark_started()

            # Simulate ingestion workflow
            await self._perform_discovery_phase(result, request)
            await self._perform_download_phase(result, request)
            await self._perform_processing_phase(result, request)
            await self._perform_validation_phase(result, request)

            # Mark as completed
            if result.failed_items > 0 and result.successful_items > 0:
                result.mark_completed(IngestionStatus.PARTIAL_SUCCESS)
            elif result.successful_items > 0:
                result.mark_completed(IngestionStatus.COMPLETED)
            else:
                result.mark_completed(IngestionStatus.FAILED, error_message="No items were successfully processed")

        except Exception as e:
            result.mark_completed(IngestionStatus.FAILED, error_message=f"Ingestion failed: {str(e)}")

        # Move to completed ingestions
        del self._active_ingestions[result.ingestion_id]
        self._completed_ingestions[result.ingestion_id] = result

    async def _perform_discovery_phase(self, result: IngestionResult, request: IngestionRequest):
        """Perform the discovery phase of ingestion."""
        # Simulate discovery delay
        await asyncio.sleep(0.1)

        # Mock discovery results based on source type
        if request.source_type == IngestionSourceType.GITHUB:
            discovered_items = 25
        elif request.source_type == IngestionSourceType.JIRA:
            discovered_items = 15
        else:
            discovered_items = 10

        # Update result
        result._total_items = discovered_items

    async def _perform_download_phase(self, result: IngestionResult, request: IngestionRequest):
        """Perform the download phase of ingestion."""
        # Simulate download delay
        await asyncio.sleep(0.2)

        # Mock download results
        successful = int(result.total_items * 0.9)  # 90% success rate
        failed = result.total_items - successful

        result.update_counts(successful=successful, failed=failed)

    async def _perform_processing_phase(self, result: IngestionResult, request: IngestionRequest):
        """Perform the processing phase of ingestion."""
        # Simulate processing delay
        await asyncio.sleep(0.3)

        # Mock processing - convert failed items to successful
        if result.failed_items > 0:
            recovered = min(2, result.failed_items)  # Recover up to 2 failed items
            result.update_counts(successful=recovered, failed=-recovered)

    async def _perform_validation_phase(self, result: IngestionResult, request: IngestionRequest):
        """Perform the validation phase of ingestion."""
        # Simulate validation delay
        await asyncio.sleep(0.1)

        # Mock validation - might cause some items to be marked as failed
        if result.successful_items > 0:
            # Randomly mark 5% as failed during validation
            validation_failures = max(1, int(result.successful_items * 0.05))
            result.update_counts(successful=-validation_failures, failed=validation_failures)

    def get_ingestion_status(self, ingestion_id: str) -> Optional[IngestionResult]:
        """
        Get the status of an ingestion by ID.

        Args:
            ingestion_id: The ingestion ID to look up

        Returns:
            IngestionResult or None: The ingestion result if found
        """
        return (
            self._active_ingestions.get(ingestion_id) or
            self._completed_ingestions.get(ingestion_id)
        )

    def get_request_ingestions(self, request_id: str) -> List[IngestionResult]:
        """
        Get all ingestions for a specific request.

        Args:
            request_id: The request ID to look up

        Returns:
            List[IngestionResult]: List of ingestion results for the request
        """
        results = []

        # Check active ingestions
        for result in self._active_ingestions.values():
            if result.request_id == request_id:
                results.append(result)

        # Check completed ingestions
        for result in self._completed_ingestions.values():
            if result.request_id == request_id:
                results.append(result)

        return results

    def cancel_ingestion(self, ingestion_id: str) -> bool:
        """
        Cancel an active ingestion.

        Args:
            ingestion_id: The ingestion ID to cancel

        Returns:
            bool: True if cancelled successfully, False otherwise
        """
        result = self._active_ingestions.get(ingestion_id)
        if result and not result.is_complete:
            result.mark_completed(IngestionStatus.CANCELLED)

            # Move to completed
            del self._active_ingestions[ingestion_id]
            self._completed_ingestions[ingestion_id] = result

            return True

        return False

    def get_ingestion_stats(self) -> Dict[str, Any]:
        """
        Get overall ingestion statistics.

        Returns:
            Dict: Statistics about ingestion operations
        """
        active_count = len(self._active_ingestions)
        completed_count = len(self._completed_ingestions)

        total_successful = sum(r.successful_items for r in self._completed_ingestions.values())
        total_failed = sum(r.failed_items for r in self._completed_ingestions.values())

        successful_ingestions = len([
            r for r in self._completed_ingestions.values()
            if r.is_successful
        ])

        return {
            "active_ingestions": active_count,
            "completed_ingestions": completed_count,
            "total_ingestions": active_count + completed_count,
            "successful_ingestions": successful_ingestions,
            "failed_ingestions": completed_count - successful_ingestions,
            "success_rate": successful_ingestions / completed_count if completed_count > 0 else 0,
            "total_items_processed": total_successful + total_failed,
            "total_successful_items": total_successful,
            "total_failed_items": total_failed
        }

    def cleanup_old_ingestions(self, max_age_days: int = 30) -> int:
        """
        Clean up old completed ingestions.

        Args:
            max_age_days: Maximum age in days for completed ingestions

        Returns:
            int: Number of ingestions cleaned up
        """
        cutoff_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        to_remove = []
        for ingestion_id, result in self._completed_ingestions.items():
            if result.completed_at:
                age_days = (cutoff_date - result.completed_at.replace(hour=0, minute=0, second=0, microsecond=0)).days
                if age_days > max_age_days:
                    to_remove.append(ingestion_id)

        for ingestion_id in to_remove:
            del self._completed_ingestions[ingestion_id]

        return len(to_remove)
