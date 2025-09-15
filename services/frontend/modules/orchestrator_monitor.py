"""Orchestrator monitoring infrastructure for Frontend service.

Provides visualization and monitoring capabilities for orchestrator Redis pub/sub
activity and service configuration.
"""
from typing import Dict, Any, List, Optional
import asyncio
import json
from datetime import datetime, timedelta
from collections import defaultdict

from services.shared.utilities import utc_now
from .shared_utils import get_orchestrator_url, get_frontend_clients


class OrchestratorMonitor:
    """Monitor for orchestrator Redis pub/sub activity and configuration."""

    def __init__(self):
        self._pubsub_activity = {
            "ingestion_requested": [],
            "findings_created": [],
            "other_events": []
        }
        self._config_cache = {}
        self._activity_cache = {}
        self._cache_ttl = 30  # Cache for 30 seconds

    def is_cache_fresh(self, cache_key: str) -> bool:
        """Check if cache is still fresh."""
        cache_time = self._activity_cache.get(f"{cache_key}_updated")
        if not cache_time:
            return False
        return (utc_now() - cache_time).total_seconds() < self._cache_ttl

    async def get_orchestrator_config(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Get orchestrator service configuration."""
        if not force_refresh and self.is_cache_fresh("config"):
            return self._config_cache

        try:
            clients = get_frontend_clients()
            orchestrator_url = get_orchestrator_url()

            # Get effective config
            config_response = await clients.get_json(f"{orchestrator_url}/config/effective")

            # Get info
            info_response = await clients.get_json(f"{orchestrator_url}/info")

            # Get metrics
            metrics_response = await clients.get_json(f"{orchestrator_url}/metrics")

            config_data = {
                "config": config_response.get("data", {}),
                "info": info_response.get("data", {}),
                "metrics": metrics_response.get("data", {}),
                "last_updated": utc_now().isoformat()
            }

            self._config_cache = config_data
            self._activity_cache["config_updated"] = utc_now()

            return config_data

        except Exception as e:
            return {
                "error": str(e),
                "config": {},
                "info": {},
                "metrics": {},
                "last_updated": utc_now().isoformat()
            }

    async def get_redis_pubsub_activity(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Get Redis pub/sub activity information."""
        if not force_refresh and self.is_cache_fresh("pubsub"):
            return self._activity_cache.get("pubsub", {})

        try:
            clients = get_frontend_clients()
            orchestrator_url = get_orchestrator_url()

            # Get health info which includes some Redis status
            health_response = await clients.get_json(f"{orchestrator_url}/health")

            # Try to get infrastructure info
            infrastructure_data = {}
            try:
                infra_response = await clients.get_json(f"{orchestrator_url}/infrastructure/events/history")
                infrastructure_data = infra_response
            except Exception:
                pass

            # Analyze activity patterns (this would be enhanced with actual Redis monitoring)
            activity_data = self._analyze_pubsub_activity(infrastructure_data)

            result = {
                "channels": {
                    "ingestion_requested": {
                        "description": "Document ingestion requests from various sources",
                        "estimated_activity": activity_data.get("ingestion_count", 0),
                        "last_activity": activity_data.get("last_ingestion")
                    },
                    "findings_created": {
                        "description": "Analysis findings and results publication",
                        "estimated_activity": activity_data.get("findings_count", 0),
                        "last_activity": activity_data.get("last_findings")
                    }
                },
                "infrastructure_events": infrastructure_data,
                "health_status": health_response,
                "estimated_total_events": activity_data.get("total_events", 0),
                "time_range": activity_data.get("time_range"),
                "last_updated": utc_now().isoformat()
            }

            self._activity_cache["pubsub"] = result
            self._activity_cache["pubsub_updated"] = utc_now()

            return result

        except Exception as e:
            return {
                "error": str(e),
                "channels": {},
                "infrastructure_events": {},
                "health_status": {},
                "estimated_total_events": 0,
                "last_updated": utc_now().isoformat()
            }

    async def get_orchestrator_workflows(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Get orchestrator workflow information."""
        if not force_refresh and self.is_cache_fresh("workflows"):
            return self._activity_cache.get("workflows", {})

        try:
            clients = get_frontend_clients()
            orchestrator_url = get_orchestrator_url()

            # Get available workflows
            workflows_response = await clients.get_json(f"{orchestrator_url}/workflows")

            # Get workflow history
            history_response = await clients.get_json(f"{orchestrator_url}/workflows/history")

            workflow_data = {
                "available_workflows": workflows_response.get("data", {}),
                "recent_history": history_response.get("items", []),
                "workflow_stats": self._calculate_workflow_stats(history_response.get("items", [])),
                "last_updated": utc_now().isoformat()
            }

            self._activity_cache["workflows"] = workflow_data
            self._activity_cache["workflows_updated"] = utc_now()

            return workflow_data

        except Exception as e:
            return {
                "error": str(e),
                "available_workflows": {},
                "recent_history": [],
                "workflow_stats": {},
                "last_updated": utc_now().isoformat()
            }

    def _analyze_pubsub_activity(self, infrastructure_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze pub/sub activity from infrastructure data."""
        # This is a simplified analysis - in a real implementation,
        # you'd have actual Redis monitoring data

        events = infrastructure_data.get("events", [])
        ingestion_count = 0
        findings_count = 0
        last_ingestion = None
        last_findings = None
        timestamps = []

        for event in events:
            event_type = event.get("type", "")
            timestamp = event.get("timestamp")

            if timestamp:
                try:
                    ts = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    timestamps.append(ts)
                except:
                    pass

            if "ingestion" in event_type.lower():
                ingestion_count += 1
                if timestamp and (not last_ingestion or timestamp > last_ingestion):
                    last_ingestion = timestamp
            elif "finding" in event_type.lower():
                findings_count += 1
                if timestamp and (not last_findings or timestamp > last_findings):
                    last_findings = timestamp

        time_range = None
        if timestamps:
            min_time = min(timestamps)
            max_time = max(timestamps)
            time_range = {
                "start": min_time.isoformat(),
                "end": max_time.isoformat(),
                "duration_hours": (max_time - min_time).total_seconds() / 3600
            }

        return {
            "ingestion_count": ingestion_count,
            "findings_count": findings_count,
            "total_events": len(events),
            "last_ingestion": last_ingestion,
            "last_findings": last_findings,
            "time_range": time_range
        }

    def _calculate_workflow_stats(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate workflow statistics from history."""
        if not history:
            return {
                "total_workflows": 0,
                "successful_workflows": 0,
                "failed_workflows": 0,
                "average_duration": 0,
                "most_common_workflow": None
            }

        total = len(history)
        successful = len([w for w in history if w.get("status") == "completed"])
        failed = len([w for w in history if w.get("status") == "failed"])

        # Calculate average duration
        durations = []
        for workflow in history:
            if workflow.get("duration"):
                try:
                    durations.append(float(workflow["duration"]))
                except:
                    pass

        avg_duration = sum(durations) / len(durations) if durations else 0

        # Find most common workflow
        workflow_counts = defaultdict(int)
        for workflow in history:
            workflow_type = workflow.get("workflow_type") or workflow.get("type") or "unknown"
            workflow_counts[workflow_type] += 1

        most_common = max(workflow_counts.items(), key=lambda x: x[1]) if workflow_counts else None

        return {
            "total_workflows": total,
            "successful_workflows": successful,
            "failed_workflows": failed,
            "success_rate": (successful / total * 100) if total > 0 else 0,
            "average_duration": round(avg_duration, 2),
            "most_common_workflow": most_common[0] if most_common else None
        }

    async def get_service_health_status(self) -> Dict[str, Any]:
        """Get overall service health status."""
        try:
            clients = get_frontend_clients()
            orchestrator_url = get_orchestrator_url()

            health_response = await clients.get_json(f"{orchestrator_url}/health")

            return {
                "orchestrator_healthy": health_response.get("status") == "healthy",
                "service": health_response.get("service"),
                "version": health_response.get("version"),
                "count": health_response.get("count", 0),
                "last_checked": utc_now().isoformat()
            }

        except Exception as e:
            return {
                "orchestrator_healthy": False,
                "error": str(e),
                "last_checked": utc_now().isoformat()
            }


# Global instance
orchestrator_monitor = OrchestratorMonitor()


def get_orchestrator_summary() -> Dict[str, Any]:
    """Get a summary of orchestrator monitoring data."""
    return {
        "config": orchestrator_monitor._config_cache,
        "pubsub_activity": orchestrator_monitor._activity_cache.get("pubsub", {}),
        "workflows": orchestrator_monitor._activity_cache.get("workflows", {}),
        "last_updated": max(
            orchestrator_monitor._activity_cache.get("config_updated"),
            orchestrator_monitor._activity_cache.get("pubsub_updated"),
            orchestrator_monitor._activity_cache.get("workflows_updated")
        ) if any(orchestrator_monitor._activity_cache.values()) else None
    }
