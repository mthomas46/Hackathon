"""Discovery Agent monitoring infrastructure for Frontend service.

Provides visualization and monitoring capabilities for discovery agent
service endpoint registration and OpenAPI parsing operations.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from services.shared.utilities import utc_now
from .shared_utils import get_discovery_agent_url, get_frontend_clients


class DiscoveryAgentMonitor:
    """Monitor for discovery agent service endpoint registration and parsing operations."""

    def __init__(self):
        self._discovery_history = []
        self._cache_ttl = 30  # Cache for 30 seconds

    def is_cache_fresh(self, cache_key: str) -> bool:
        """Check if cache is still fresh."""
        cache_time = getattr(self, f"_{cache_key}_updated", None)
        if not cache_time:
            return False
        return (utc_now() - cache_time).total_seconds() < self._cache_ttl

    async def get_discovery_status(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Get comprehensive discovery agent service status."""
        if not force_refresh and self.is_cache_fresh("status"):
            return getattr(self, "_status_cache", {})

        try:
            clients = get_frontend_clients()
            discovery_url = get_discovery_agent_url()

            # Get health status
            health_response = await clients.get_json(f"{discovery_url}/health")

            status_data = {
                "health": health_response,
                "discovery_stats": self._calculate_discovery_stats(),
                "recent_discoveries": self._discovery_history[-10:] if self._discovery_history else [],  # Last 10 discoveries
                "last_updated": utc_now().isoformat()
            }

            self._status_cache = status_data
            self._status_updated = utc_now()

            return status_data

        except Exception as e:
            return {
                "error": str(e),
                "health": {},
                "discovery_stats": {},
                "recent_discoveries": [],
                "last_updated": utc_now().isoformat()
            }

    async def discover_endpoints(self, service_url: str, service_name: Optional[str] = None, dry_run: bool = False, spec_url: Optional[str] = None) -> Dict[str, Any]:
        """Trigger endpoint discovery for a service and cache the result."""
        try:
            clients = get_frontend_clients()
            discovery_url = get_discovery_agent_url()

            payload = {
                "service_url": service_url,
                "dry_run": dry_run
            }

            if service_name:
                payload["service_name"] = service_name
            if spec_url:
                payload["spec_url"] = spec_url

            response = await clients.post_json(f"{discovery_url}/discover", payload)

            if response.get("success") or "endpoints" in response:
                # Cache the discovery
                discovery_result = {
                    "id": f"discovery_{utc_now().isoformat()}",
                    "timestamp": utc_now().isoformat(),
                    "service_url": service_url,
                    "service_name": service_name or "Unknown",
                    "dry_run": dry_run,
                    "spec_url": spec_url,
                    "endpoints_discovered": len(response.get("endpoints", [])),
                    "response": response,
                    "status": "completed" if response.get("success") else "failed"
                }

                self._discovery_history.insert(0, discovery_result)  # Add to front

                # Keep only last 50 discoveries
                if len(self._discovery_history) > 50:
                    self._discovery_history = self._discovery_history[:50]

                return {
                    "success": True,
                    "discovery_id": discovery_result["id"],
                    "endpoints_discovered": discovery_result["endpoints_discovered"],
                    "response": response
                }

            return {
                "success": False,
                "error": "Discovery failed",
                "response": response
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": None
            }

    def _calculate_discovery_stats(self) -> Dict[str, Any]:
        """Calculate statistics from cached discoveries."""
        if not self._discovery_history:
            return {
                "total_discoveries": 0,
                "successful_discoveries": 0,
                "failed_discoveries": 0,
                "total_endpoints_discovered": 0,
                "unique_services": 0,
                "dry_run_count": 0
            }

        total = len(self._discovery_history)
        successful = sum(1 for d in self._discovery_history if d.get("status") == "completed")
        failed = total - successful
        total_endpoints = sum(d.get("endpoints_discovered", 0) for d in self._discovery_history)
        dry_runs = sum(1 for d in self._discovery_history if d.get("dry_run"))

        # Unique services
        services = set()
        for discovery in self._discovery_history:
            if discovery.get("service_name") and discovery["service_name"] != "Unknown":
                services.add(discovery["service_name"])

        return {
            "total_discoveries": total,
            "successful_discoveries": successful,
            "failed_discoveries": failed,
            "success_rate": round((successful / total) * 100, 1) if total > 0 else 0,
            "total_endpoints_discovered": total_endpoints,
            "unique_services": len(services),
            "dry_run_count": dry_runs,
            "services_discovered": list(services)
        }

    def get_discovery_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent discovery history."""
        return self._discovery_history[:limit]


# Global instance
discovery_agent_monitor = DiscoveryAgentMonitor()
