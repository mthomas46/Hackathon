"""HTTP Client for Project Simulation Service.

This module provides a comprehensive HTTP client for communicating with the
project-simulation service, handling all REST API interactions with proper
error handling, retries, and response caching.
"""

import asyncio
import json
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import time

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from infrastructure.config.config import SimulationServiceConfig, get_config
from infrastructure.logging.logger import get_dashboard_logger


class SimulationClientError(Exception):
    """Base exception for simulation client errors."""
    pass


class SimulationClient:
    """HTTP client for the project-simulation service."""

    def __init__(self, config: SimulationServiceConfig):
        """Initialize the simulation client."""
        self.config = config
        self.logger = get_dashboard_logger("simulation_client")

        # Create HTTP client with configuration
        self.client = httpx.AsyncClient(
            base_url=config.base_url,
            timeout=config.timeout,
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10)
        )

        # Cache for responses
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_timestamps: Dict[str, float] = {}

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    def _get_cache_key(self, method: str, url: str, params: Optional[Dict[str, Any]] = None) -> str:
        """Generate cache key for request."""
        key_parts = [method.upper(), url]
        if params:
            key_parts.append(json.dumps(params, sort_keys=True))
        return "|".join(key_parts)

    def _is_cache_valid(self, cache_key: str, ttl: int = 300) -> bool:
        """Check if cached response is still valid."""
        if cache_key not in self._cache_timestamps:
            return False
        return time.time() - self._cache_timestamps[cache_key] < ttl

    def _get_cached_response(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached response if valid."""
        if self._is_cache_valid(cache_key):
            return self._cache.get(cache_key)
        return None

    def _cache_response(self, cache_key: str, response: Dict[str, Any]) -> None:
        """Cache response with timestamp."""
        self._cache[cache_key] = response
        self._cache_timestamps[cache_key] = time.time()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError))
    )
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """Make HTTP request with retry logic and caching."""
        url = f"/api/v1/{endpoint.lstrip('/')}"
        cache_key = self._get_cache_key(method, url, params)

        # Check cache for GET requests
        if method.upper() == "GET" and use_cache:
            cached = self._get_cached_response(cache_key)
            if cached:
                self.logger.debug(f"Cache hit for {method} {url}")
                return cached

        start_time = time.time()

        try:
            # Make request
            response = await self.client.request(
                method=method.upper(),
                url=url,
                params=params,
                json=json_data
            )

            duration = time.time() - start_time

            # Log request
            self.logger.log_request(
                method=method.upper(),
                url=url,
                status_code=response.status_code,
                duration=duration
            )

            # Handle response
            if response.status_code >= 400:
                error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {"error": response.text}
                raise SimulationClientError(f"HTTP {response.status_code}: {error_data}")

            # Parse response
            if response.headers.get('content-type', '').startswith('application/json'):
                result = response.json()
            else:
                result = {"data": response.text}

            # Cache successful GET responses
            if method.upper() == "GET" and use_cache:
                self._cache_response(cache_key, result)

            return result

        except httpx.TimeoutException as e:
            self.logger.error(f"Request timeout for {method} {url}: {str(e)}")
            raise SimulationClientError(f"Request timeout: {str(e)}")
        except httpx.ConnectError as e:
            self.logger.error(f"Connection error for {method} {url}: {str(e)}")
            raise SimulationClientError(f"Connection error: {str(e)}")
        except Exception as e:
            self.logger.error(f"Request error for {method} {url}: {str(e)}")
            raise SimulationClientError(f"Request error: {str(e)}")

    # Simulation Management Endpoints

    async def create_simulation(self, simulation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new simulation."""
        return await self._make_request(
            "POST",
            "simulations",
            json_data=simulation_data,
            use_cache=False
        )

    async def get_simulation(self, simulation_id: str) -> Dict[str, Any]:
        """Get simulation details."""
        return await self._make_request(
            "GET",
            f"simulations/{simulation_id}"
        )

    async def list_simulations(
        self,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """List simulations with pagination."""
        params = {"page": page, "page_size": page_size}
        if status:
            params["status"] = status

        return await self._make_request(
            "GET",
            "simulations",
            params=params
        )

    async def execute_simulation(self, simulation_id: str) -> Dict[str, Any]:
        """Execute a simulation."""
        return await self._make_request(
            "POST",
            f"simulations/{simulation_id}/execute",
            use_cache=False
        )

    async def cancel_simulation(self, simulation_id: str) -> Dict[str, Any]:
        """Cancel a simulation."""
        return await self._make_request(
            "DELETE",
            f"simulations/{simulation_id}",
            use_cache=False
        )

    async def get_simulation_results(self, simulation_id: str) -> Dict[str, Any]:
        """Get simulation results."""
        return await self._make_request(
            "GET",
            f"simulations/{simulation_id}/results"
        )

    # Configuration Endpoints

    async def create_sample_config(self, file_path: str, project_name: str) -> Dict[str, Any]:
        """Create a sample configuration file."""
        return await self._make_request(
            "POST",
            "config/sample",
            json_data={"file_path": file_path, "project_name": project_name},
            use_cache=False
        )

    async def validate_config(self, config_file_path: str) -> Dict[str, Any]:
        """Validate a configuration file."""
        return await self._make_request(
            "POST",
            "config/validate",
            json_data={"config_file_path": config_file_path},
            use_cache=False
        )

    async def get_config_template(self) -> Dict[str, Any]:
        """Get configuration template."""
        return await self._make_request(
            "GET",
            "config/template"
        )

    async def create_simulation_from_config(self, config_file_path: str) -> Dict[str, Any]:
        """Create simulation from configuration file."""
        return await self._make_request(
            "POST",
            "simulations/from-config",
            json_data={"config_file_path": config_file_path},
            use_cache=False
        )

    # Reporting Endpoints

    async def generate_reports(self, simulation_id: str, report_types: List[str]) -> Dict[str, Any]:
        """Generate reports for a simulation."""
        return await self._make_request(
            "POST",
            f"simulations/{simulation_id}/reports/generate",
            json_data={"report_types": report_types},
            use_cache=False
        )

    async def get_simulation_reports(self, simulation_id: str) -> Dict[str, Any]:
        """Get available reports for a simulation."""
        return await self._make_request(
            "GET",
            f"simulations/{simulation_id}/reports"
        )

    async def get_simulation_report(self, simulation_id: str, report_type: str) -> Dict[str, Any]:
        """Get a specific report for a simulation."""
        return await self._make_request(
            "GET",
            f"simulations/{simulation_id}/reports/{report_type}"
        )

    async def export_report(self, simulation_id: str, report_type: str, format: str, output_path: Optional[str] = None) -> Dict[str, Any]:
        """Export a simulation report."""
        return await self._make_request(
            "POST",
            f"simulations/{simulation_id}/reports/export",
            json_data={
                "report_type": report_type,
                "format": format,
                "output_path": output_path
            },
            use_cache=False
        )

    # Event Endpoints

    async def get_simulation_events(
        self,
        simulation_id: Optional[str] = None,
        event_types: Optional[List[str]] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get simulation events with filtering."""
        params = {
            "limit": limit,
            "offset": offset
        }

        if simulation_id:
            params["simulation_id"] = simulation_id

        if event_types:
            params["event_types"] = ",".join(event_types)

        if start_time:
            params["start_time"] = start_time

        if end_time:
            params["end_time"] = end_time

        if tags:
            params["tags"] = ",".join(tags)

        return await self._make_request(
            "GET",
            "simulations/events" if simulation_id else "events",
            params=params
        )

    async def get_simulation_timeline(self, simulation_id: str) -> Dict[str, Any]:
        """Get timeline of events for a simulation."""
        return await self._make_request(
            "GET",
            f"simulations/{simulation_id}/timeline"
        )

    async def replay_events(
        self,
        simulation_id: str,
        event_types: Optional[List[str]] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        tags: Optional[List[str]] = None,
        speed_multiplier: float = 1.0,
        include_system_events: bool = False,
        max_events: Optional[int] = None
    ) -> Dict[str, Any]:
        """Replay simulation events."""
        return await self._make_request(
            "POST",
            f"simulations/{simulation_id}/events/replay",
            json_data={
                "event_types": event_types,
                "start_time": start_time,
                "end_time": end_time,
                "tags": tags,
                "speed_multiplier": speed_multiplier,
                "include_system_events": include_system_events,
                "max_events": max_events
            },
            use_cache=False
        )

    async def get_event_statistics(
        self,
        simulation_id: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get event statistics."""
        params = {}
        if simulation_id:
            params["simulation_id"] = simulation_id
        if start_time:
            params["start_time"] = start_time
        if end_time:
            params["end_time"] = end_time

        return await self._make_request(
            "GET",
            "events/statistics",
            params=params
        )

    # UI Monitoring Endpoints

    async def start_ui_monitoring(self, simulation_id: str, estimated_duration: int = 60) -> Dict[str, Any]:
        """Start UI monitoring for a simulation."""
        return await self._make_request(
            "POST",
            f"simulations/{simulation_id}/ui/start",
            json_data={"estimated_duration_minutes": estimated_duration},
            use_cache=False
        )

    async def stop_ui_monitoring(self, simulation_id: str, success: bool = True) -> Dict[str, Any]:
        """Stop UI monitoring for a simulation."""
        return await self._make_request(
            "POST",
            f"simulations/{simulation_id}/ui/stop",
            json_data={"success": success},
            use_cache=False
        )

    async def get_ui_monitoring_status(self, simulation_id: str) -> Dict[str, Any]:
        """Get UI monitoring status for a simulation."""
        return await self._make_request(
            "GET",
            f"simulations/{simulation_id}/ui/status"
        )

    # Health Endpoints

    async def get_health(self) -> Dict[str, Any]:
        """Get basic health status."""
        return await self._make_request(
            "GET",
            "health"
        )

    async def get_detailed_health(self) -> Dict[str, Any]:
        """Get detailed health status."""
        return await self._make_request(
            "GET",
            "health/detailed"
        )

    async def get_system_health(self) -> Dict[str, Any]:
        """Get system-wide health status."""
        return await self._make_request(
            "GET",
            "health/system"
        )

    # Clear cache methods
    def clear_cache(self) -> None:
        """Clear all cached responses."""
        self._cache.clear()
        self._cache_timestamps.clear()

    def clear_simulation_cache(self, simulation_id: str) -> None:
        """Clear cache for a specific simulation."""
        keys_to_remove = [
            key for key in self._cache.keys()
            if simulation_id in key
        ]
        for key in keys_to_remove:
            self._cache.pop(key, None)
            self._cache_timestamps.pop(key, None)
