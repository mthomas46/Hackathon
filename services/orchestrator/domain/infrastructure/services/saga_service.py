"""Saga Service Domain Service"""

from typing import List, Dict, Any, Optional

from ..value_objects.saga_instance import SagaInstance, SagaStep
from ..value_objects.saga_status import SagaStatus


class SagaService:
    """Domain service for managing saga orchestration."""

    def __init__(self):
        """Initialize saga service."""
        self._active_sagas: Dict[str, SagaInstance] = {}
        self._completed_sagas: Dict[str, SagaInstance] = {}

    def create_saga(
        self,
        saga_type: str,
        correlation_id: str,
        steps: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> SagaInstance:
        """Create a new saga instance."""
        saga_steps = []
        for step_data in steps:
            step = SagaStep(
                step_id=step_data["step_id"],
                service_name=step_data["service_name"],
                operation=step_data["operation"],
                compensation_operation=step_data.get("compensation_operation")
            )
            saga_steps.append(step)

        saga = SagaInstance(
            saga_type=saga_type,
            correlation_id=correlation_id,
            steps=saga_steps,
            metadata=metadata
        )

        self._active_sagas[saga.saga_id] = saga
        return saga

    def get_saga(self, saga_id: str) -> Optional[SagaInstance]:
        """Get a saga by ID."""
        return self._active_sagas.get(saga_id) or self._completed_sagas.get(saga_id)

    def start_saga(self, saga_id: str) -> bool:
        """Start a saga execution."""
        saga = self._active_sagas.get(saga_id)
        if not saga:
            return False

        try:
            saga.start()
            return True
        except ValueError:
            return False

    def complete_saga_step(self, saga_id: str, step_id: str) -> bool:
        """Complete a saga step."""
        saga = self._active_sagas.get(saga_id)
        if not saga:
            return False

        saga.complete_step(step_id)
        return True

    def fail_saga_step(self, saga_id: str, step_id: str, error_message: str) -> bool:
        """Fail a saga step and trigger compensation."""
        saga = self._active_sagas.get(saga_id)
        if not saga:
            return False

        saga.fail_step(step_id, error_message)

        # Trigger compensation
        self._compensate_saga(saga)
        return True

    def complete_saga(self, saga_id: str) -> bool:
        """Complete a saga successfully."""
        saga = self._active_sagas.get(saga_id)
        if not saga:
            return False

        saga.complete()

        # Move to completed sagas
        del self._active_sagas[saga_id]
        self._completed_sagas[saga_id] = saga

        return True

    def abort_saga(self, saga_id: str) -> bool:
        """Abort a saga."""
        saga = self._active_sagas.get(saga_id)
        if not saga:
            return False

        saga.abort()

        # Move to completed sagas
        del self._active_sagas[saga_id]
        self._completed_sagas[saga_id] = saga

        return True

    def _compensate_saga(self, saga: SagaInstance):
        """Execute compensation for failed saga steps."""
        saga.compensate()

        # In a real implementation, this would execute compensation operations
        # For now, we'll just mark the saga as failed
        saga.fail("Compensation required due to step failure")

    def list_active_sagas(
        self,
        saga_type_filter: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[SagaInstance]:
        """List active sagas with optional filtering."""
        sagas = list(self._active_sagas.values())

        if saga_type_filter:
            sagas = [s for s in sagas if s.saga_type == saga_type_filter]

        # Sort by creation time (newest first)
        sagas.sort(key=lambda s: s.created_at, reverse=True)

        start_idx = offset
        end_idx = start_idx + limit
        return sagas[start_idx:end_idx]

    def list_completed_sagas(
        self,
        saga_type_filter: Optional[str] = None,
        status_filter: Optional[SagaStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[SagaInstance]:
        """List completed sagas with optional filtering."""
        sagas = list(self._completed_sagas.values())

        if saga_type_filter:
            sagas = [s for s in sagas if s.saga_type == saga_type_filter]

        if status_filter:
            sagas = [s for s in sagas if s.status == status_filter]

        # Sort by completion time (newest first)
        sagas.sort(key=lambda s: s.completed_at or s.created_at, reverse=True)

        start_idx = offset
        end_idx = start_idx + limit
        return sagas[start_idx:end_idx]

    def get_saga_stats(self) -> Dict[str, Any]:
        """Get saga statistics."""
        active_sagas = list(self._active_sagas.values())
        completed_sagas = list(self._completed_sagas.values())

        total_completed = len(completed_sagas)
        successful_sagas = len([s for s in completed_sagas if s.status == SagaStatus.COMPLETED])
        failed_sagas = len([s for s in completed_sagas if s.status == SagaStatus.FAILED])

        return {
            "active_sagas": len(active_sagas),
            "completed_sagas": total_completed,
            "successful_sagas": successful_sagas,
            "failed_sagas": failed_sagas,
            "success_rate": successful_sagas / total_completed if total_completed > 0 else 0,
            "avg_completion_time": self._calculate_avg_completion_time(completed_sagas)
        }

    def _calculate_avg_completion_time(self, sagas: List[SagaInstance]) -> Optional[float]:
        """Calculate average completion time for sagas."""
        completion_times = []
        for saga in sagas:
            if saga.duration_seconds is not None:
                completion_times.append(saga.duration_seconds)

        return sum(completion_times) / len(completion_times) if completion_times else None

    def cleanup_completed_sagas(self, max_age_days: int = 30) -> int:
        """Clean up old completed sagas. Returns count removed."""
        # In a real implementation, this would remove sagas older than max_age_days
        # For now, return 0 as we don't have actual cleanup logic
        return 0
