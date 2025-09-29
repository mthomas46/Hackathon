"""Main intelligent ingestion orchestrator."""

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from services.shared.infrastructure.caching.intelligent_caching import get_service_cache
from services.shared.infrastructure.monitoring.logging import fire_and_forget

from .types import DataIngestionJob, DataSource, IngestionPriority
from .predictive_model import PredictiveIngestionModel
from .conflict_resolution import ConflictResolutionEngine
from .change_detection import ChangeDetectionEngine


@dataclass
class IntelligentIngestionEngine:
    """Main intelligent data ingestion engine."""

    ingestion_jobs: Dict[str, DataIngestionJob] = field(default_factory=dict)
    predictive_models: Dict[str, PredictiveIngestionModel] = field(default_factory=dict)
    conflict_resolver: ConflictResolutionEngine = field(default_factory=ConflictResolutionEngine)
    change_detector: ChangeDetectionEngine = field(default_factory=ChangeDetectionEngine)
    cache = field(default_factory=lambda: get_service_cache("source-agent"))

    async def create_ingestion_job(
        self,
        source_type: DataSource,
        source_config: Dict[str, Any],
        target_config: Dict[str, Any],
    ) -> str:
        """Create a new data ingestion job."""
        job = DataIngestionJob(
            source=source_type,
            data_path=source_config.get("path", ""),
            metadata={"source_config": source_config, "target_config": target_config}
        )

        self.ingestion_jobs[job.id] = job

        # Create predictive model for this job
        model = PredictiveIngestionModel(
            data_source=source_type, prediction_type="usage_pattern"
        )
        self.predictive_models[job.id] = model

        # Cache job
        await self.cache.set(
            f"ingestion_job_{job.id}",
            {
                "job_id": job.id,
                "source_type": source_type.value,
                "status": job.status,
                "created_at": job.created_at.isoformat(),
            },
            ttl_seconds=3600,
        )

        fire_and_forget(
            "info",
            f"Created ingestion job {job.id} for {source_type.value}",
            "source-agent",
        )
        return job.id

    async def execute_ingestion_job(self, job_id: str) -> Dict[str, Any]:
        """Execute a data ingestion job."""
        if job_id not in self.ingestion_jobs:
            return {"error": "Job not found"}

        job = self.ingestion_jobs[job_id]
        job.start_job()

        try:
            # Get predictive parameters
            predictive_model = self.predictive_models.get(job_id)
            if predictive_model:
                predictions = predictive_model.predict_ingestion_parameters(
                    job.metadata.get("source_config", {})
                )
                predicted_priority = predictions.get("priority", IngestionPriority.MEDIUM)
                if isinstance(predicted_priority, str):
                    job.priority = IngestionPriority(predicted_priority)
                else:
                    job.priority = predicted_priority

            # Detect changes
            changes = await self.change_detector.detect_changes(
                f"{job.source.value}_{job_id}", job.metadata.get("source_config", {})
            )

            if not changes["requires_ingestion"]:
                job.complete_job()
                return {
                    "job_id": job_id,
                    "status": "completed",
                    "message": "No changes detected, ingestion skipped",
                    "changes": changes,
                }

            # Execute ingestion with quality assessment
            ingestion_result = await self._execute_ingestion(job)

            # Check for conflicts if multiple sources
            if len(job.dependencies) > 0:
                conflict_resolution = await self.conflict_resolver.resolve_conflict(
                    [ingestion_result], {"job_id": job_id}
                )
                ingestion_result = conflict_resolution.get("resolved_record", ingestion_result)

            job.complete_job()
            return {
                "job_id": job_id,
                "status": "completed",
                "result": ingestion_result,
                "changes": changes,
                "execution_time": job.get_duration_seconds(),
            }

        except Exception as e:
            job.fail_job(str(e))
            return {
                "job_id": job_id,
                "status": "failed",
                "error": str(e),
            }

    async def _execute_ingestion(self, job: DataIngestionJob) -> Dict[str, Any]:
        """Execute the actual data ingestion process."""
        # Simulate ingestion process
        await asyncio.sleep(0.1)  # Simulate processing time

        # Mock ingestion result
        result = {
            "job_id": job.id,
            "source_type": job.source.value,
            "records_processed": 100,
            "records_ingested": 95,
            "records_failed": 5,
            "data_quality_score": 0.92,
            "execution_timestamp": datetime.now().isoformat(),
        }

        return result

    async def get_ingestion_status(self, job_id: str) -> Dict[str, Any]:
        """Get the status of an ingestion job."""
        job = self.ingestion_jobs.get(job_id)
        if not job:
            return {"error": "Job not found"}

        return {
            "job_id": job.id,
            "status": job.status,
            "progress": job.progress,
            "priority": job.priority.value,
            "created_at": job.created_at.isoformat(),
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "error_message": job.error_message,
            "retry_count": job.retry_count,
        }

    async def cancel_ingestion_job(self, job_id: str) -> bool:
        """Cancel an ingestion job."""
        job = self.ingestion_jobs.get(job_id)
        if not job:
            return False

        if job.status in ["completed", "failed"]:
            return False

        job.status = "cancelled"
        job.completed_at = datetime.now()

        return True

    async def get_ingestion_statistics(self) -> Dict[str, Any]:
        """Get overall ingestion statistics."""
        total_jobs = len(self.ingestion_jobs)
        completed_jobs = sum(1 for job in self.ingestion_jobs.values() if job.status == "completed")
        failed_jobs = sum(1 for job in self.ingestion_jobs.values() if job.status == "failed")
        running_jobs = sum(1 for job in self.ingestion_jobs.values() if job.status == "running")

        return {
            "total_jobs": total_jobs,
            "completed_jobs": completed_jobs,
            "failed_jobs": failed_jobs,
            "running_jobs": running_jobs,
            "success_rate": completed_jobs / total_jobs if total_jobs > 0 else 0,
            "average_execution_time": await self._calculate_average_execution_time(),
        }

    async def _calculate_average_execution_time(self) -> Optional[float]:
        """Calculate average execution time for completed jobs."""
        completed_jobs = [
            job for job in self.ingestion_jobs.values()
            if job.status == "completed" and job.get_duration_seconds()
        ]

        if not completed_jobs:
            return None

        total_time = sum(job.get_duration_seconds() for job in completed_jobs)
        return total_time / len(completed_jobs)

    def add_conflict_resolution_rule(
        self, rule_name: str, conditions: Dict[str, Any], strategy: str
    ):
        """Add a conflict resolution rule."""
        from .types import ConflictResolutionStrategy
        strategy_enum = ConflictResolutionStrategy(strategy)
        self.conflict_resolver.add_resolution_rule(rule_name, conditions, strategy_enum)

    def add_change_detection_rule(
        self, rule_name: str, source_type: DataSource, conditions: Dict[str, Any]
    ):
        """Add a change detection rule."""
        self.change_detector.add_detection_rule(rule_name, source_type, conditions)

    async def optimize_ingestion_schedule(self) -> Dict[str, Any]:
        """Optimize ingestion schedule based on predictive models."""
        optimizations = []

        for job_id, model in self.predictive_models.items():
            prediction = model.predict_ingestion_parameters({})
            if prediction.get("frequency") != "daily":  # If different from default
                optimizations.append({
                    "job_id": job_id,
                    "recommended_frequency": prediction.get("frequency"),
                    "predicted_volume": prediction.get("volume"),
                    "confidence": prediction.get("confidence"),
                })

        return {
            "optimizations": optimizations,
            "total_optimized_jobs": len(optimizations),
            "schedule_efficiency_gain": len(optimizations) * 0.15,  # Estimated 15% improvement per optimization
        }
