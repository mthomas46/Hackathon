"""Source Agent monitoring infrastructure for Frontend service.

Provides visualization and monitoring capabilities for source agent
service document fetching, normalization, and code analysis operations.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from services.shared.utilities import utc_now
from .shared_utils import get_source_agent_url, get_frontend_clients


class SourceAgentMonitor:
    """Monitor for source agent service document operations and source integrations."""

    def __init__(self):
        self._fetches = []
        self._normalizations = []
        self._analyses = []
        self._cache_ttl = 30  # Cache for 30 seconds

    def is_cache_fresh(self, cache_key: str) -> bool:
        """Check if cache is still fresh."""
        cache_time = getattr(self, f"_{cache_key}_updated", None)
        if not cache_time:
            return False
        return (utc_now() - cache_time).total_seconds() < self._cache_ttl

    async def get_source_status(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Get comprehensive source agent service status."""
        if not force_refresh and self.is_cache_fresh("status"):
            return getattr(self, "_status_cache", {})

        try:
            clients = get_frontend_clients()
            source_url = get_source_agent_url()

            # Get health and sources info
            health_response = await clients.get_json(f"{source_url}/health")
            sources_response = await clients.get_json(f"{source_url}/sources")

            status_data = {
                "health": health_response,
                "sources": sources_response,
                "operation_stats": self._calculate_operation_stats(),
                "recent_fetches": self._fetches[-10:] if self._fetches else [],  # Last 10 fetches
                "recent_normalizations": self._normalizations[-10:] if self._normalizations else [],  # Last 10 normalizations
                "recent_analyses": self._analyses[-10:] if self._analyses else [],  # Last 10 analyses
                "last_updated": utc_now().isoformat()
            }

            self._status_cache = status_data
            self._status_updated = utc_now()

            return status_data

        except Exception as e:
            return {
                "error": str(e),
                "health": {},
                "sources": {},
                "operation_stats": {},
                "recent_fetches": [],
                "recent_normalizations": [],
                "recent_analyses": [],
                "last_updated": utc_now().isoformat()
            }

    async def fetch_document(self, source: str, identifier: str, scope: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Fetch document from specified source."""
        try:
            clients = get_frontend_clients()
            source_url = get_source_agent_url()

            payload = {
                "source": source,
                "identifier": identifier,
                "scope": scope or {}
            }

            response = await clients.post_json(f"{source_url}/docs/fetch", payload)

            # Cache the fetch result
            fetch_result = {
                "id": f"fetch_{utc_now().isoformat()}",
                "timestamp": utc_now().isoformat(),
                "source": source,
                "identifier": identifier,
                "scope": scope,
                "success": "document" in response,
                "response": response
            }

            self._fetches.insert(0, fetch_result)  # Add to front
            # Keep only last 50 fetches
            if len(self._fetches) > 50:
                self._fetches = self._fetches[:50]

            return {
                "success": True,
                "fetch_id": fetch_result["id"],
                "source": source,
                "document": response.get("document"),
                "response": response
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "source": source,
                "identifier": identifier,
                "response": None
            }

    async def normalize_data(self, source: str, data: Dict[str, Any], correlation_id: Optional[str] = None) -> Dict[str, Any]:
        """Normalize data from specified source."""
        try:
            clients = get_frontend_clients()
            source_url = get_source_agent_url()

            payload = {
                "source": source,
                "data": data,
                "correlation_id": correlation_id
            }

            response = await clients.post_json(f"{source_url}/normalize", payload)

            # Cache the normalization result
            normalization_result = {
                "id": f"normalize_{utc_now().isoformat()}",
                "timestamp": utc_now().isoformat(),
                "source": source,
                "correlation_id": correlation_id,
                "success": "envelope" in response,
                "envelope_id": response.get("envelope", {}).get("id") if "envelope" in response else None,
                "response": response
            }

            self._normalizations.insert(0, normalization_result)  # Add to front
            # Keep only last 50 normalizations
            if len(self._normalizations) > 50:
                self._normalizations = self._normalizations[:50]

            return {
                "success": True,
                "normalization_id": normalization_result["id"],
                "source": source,
                "envelope": response.get("envelope"),
                "response": response
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "source": source,
                "correlation_id": correlation_id,
                "response": None
            }

    async def analyze_code(self, text: str) -> Dict[str, Any]:
        """Analyze code for API endpoints and patterns."""
        try:
            clients = get_frontend_clients()
            source_url = get_source_agent_url()

            payload = {"text": text}

            response = await clients.post_json(f"{source_url}/code/analyze", payload)

            # Cache the analysis result
            analysis_result = {
                "id": f"analysis_{utc_now().isoformat()}",
                "timestamp": utc_now().isoformat(),
                "code_length": len(text),
                "success": "analysis" in response,
                "endpoint_count": response.get("endpoint_count", 0),
                "patterns_found": response.get("patterns_found", []),
                "response": response
            }

            self._analyses.insert(0, analysis_result)  # Add to front
            # Keep only last 50 analyses
            if len(self._analyses) > 50:
                self._analyses = self._analyses[:50]

            return {
                "success": True,
                "analysis_id": analysis_result["id"],
                "analysis": response.get("analysis"),
                "endpoint_count": analysis_result["endpoint_count"],
                "patterns_found": analysis_result["patterns_found"],
                "response": response
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "code_length": len(text),
                "response": None
            }

    def _calculate_operation_stats(self) -> Dict[str, Any]:
        """Calculate statistics from cached operations."""
        if not self._fetches and not self._normalizations and not self._analyses:
            return {
                "total_operations": 0,
                "fetch_operations": 0,
                "normalization_operations": 0,
                "analysis_operations": 0,
                "success_rate": 0
            }

        total_fetches = len(self._fetches)
        total_normalizations = len(self._normalizations)
        total_analyses = len(self._analyses)
        total_operations = total_fetches + total_normalizations + total_analyses

        # Calculate success rates
        successful_operations = (
            sum(1 for f in self._fetches if f.get("success")) +
            sum(1 for n in self._normalizations if n.get("success")) +
            sum(1 for a in self._analyses if a.get("success"))
        )

        success_rate = round((successful_operations / total_operations) * 100, 1) if total_operations > 0 else 0

        # Source distribution
        source_counts = {}
        for fetch in self._fetches:
            source = fetch.get("source", "unknown")
            source_counts[source] = source_counts.get(source, 0) + 1

        return {
            "total_operations": total_operations,
            "fetch_operations": total_fetches,
            "normalization_operations": total_normalizations,
            "analysis_operations": total_analyses,
            "success_rate": success_rate,
            "source_distribution": source_counts
        }

    def get_fetch_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent document fetch history."""
        return self._fetches[:limit]

    def get_normalization_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent data normalization history."""
        return self._normalizations[:limit]

    def get_analysis_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent code analysis history."""
        return self._analyses[:limit]


# Global instance
source_agent_monitor = SourceAgentMonitor()
