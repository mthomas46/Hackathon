"""Simulation Service Client - HTTP Client for Project Simulation Service.

This module provides a comprehensive HTTP client for interacting with the
project-simulation service, including REST API calls, WebSocket connections,
and real-time data streaming.
"""

import httpx
import asyncio
import websockets
import json
from typing import Dict, Any, Optional, List, Callable, AsyncGenerator
from datetime import datetime, timedelta
import logging
from urllib.parse import urljoin
import time

from infrastructure.config.config import get_config


class SimulationClientError(Exception):
    """Base exception for simulation client errors."""
    pass


class SimulationServiceConnectionError(SimulationClientError):
    """Exception raised when connection to simulation service fails."""
    pass


class SimulationAPIError(SimulationClientError):
    """Exception raised when simulation API returns an error."""
    pass


class SimulationClient:
    """HTTP client for interacting with the project-simulation service."""

    def __init__(self,
                 base_url: Optional[str] = None,
                 timeout: float = 30.0,
                 max_retries: int = 3):
        """Initialize the simulation client.

        Args:
            base_url: Base URL of the simulation service. If None, uses config.
            timeout: Request timeout in seconds.
            max_retries: Maximum number of retries for failed requests.
        """
        self.config = get_config()
        self.base_url = base_url or self._get_service_url()
        self.timeout = timeout
        self.max_retries = max_retries

        # HTTP client setup
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'SimulationDashboard/1.0'
            }
        )

        # WebSocket connection
        self.ws_url = self._get_websocket_url()
        self.websocket = None
        self.ws_connected = False

        # Event handlers
        self.event_handlers: Dict[str, List[Callable]] = {}

        # Logging
        self.logger = logging.getLogger(__name__)

    def _get_service_url(self) -> str:
        """Get the simulation service URL from configuration."""
        # Try to get from service discovery first
        try:
            from services.shared.utilities.discovery import get_service_url
            return get_service_url('project-simulation')
        except:
            # Fallback to direct configuration
            host = self.config.get('simulation_service', {}).get('host', 'localhost')
            port = self.config.get('simulation_service', {}).get('port', 5075)
            return f"http://{host}:{port}"

    def _get_websocket_url(self) -> str:
        """Get the WebSocket URL for the simulation service."""
        http_url = self._get_service_url()
        ws_url = http_url.replace('http://', 'ws://').replace('https://', 'wss://')
        return ws_url

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def close(self):
        """Close the client and cleanup resources."""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
            self.ws_connected = False

        await self.client.aclose()

    async def _make_request(self,
                           method: str,
                           endpoint: str,
                           **kwargs) -> Dict[str, Any]:
        """Make an HTTP request with retry logic.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            **kwargs: Additional arguments for the request

        Returns:
            Dict containing the response data

        Raises:
            SimulationAPIError: If the API returns an error
            SimulationServiceConnectionError: If connection fails
        """
        url = urljoin(self.base_url + '/', endpoint.lstrip('/'))

        for attempt in range(self.max_retries):
            try:
                response = await self.client.request(method, url, **kwargs)

                if response.status_code >= 500:
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    raise SimulationServiceConnectionError(
                        f"Server error: {response.status_code}"
                    )

                if response.status_code >= 400:
                    try:
                        error_data = response.json()
                        error_message = error_data.get('message', 'Unknown error')
                        raise SimulationAPIError(
                            f"API error {response.status_code}: {error_message}"
                        )
                    except json.JSONDecodeError:
                        raise SimulationAPIError(
                            f"API error {response.status_code}: {response.text}"
                        )

                # Success
                try:
                    return response.json()
                except json.JSONDecodeError:
                    return {'success': True, 'data': response.text}

            except (httpx.ConnectError, httpx.TimeoutException) as e:
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise SimulationServiceConnectionError(
                    f"Connection failed after {self.max_retries} attempts: {e}"
                )

        raise SimulationServiceConnectionError("Max retries exceeded")

    # Health and Status Endpoints

    async def get_health(self) -> Dict[str, Any]:
        """Get service health status."""
        return await self._make_request('GET', '/health')

    async def get_detailed_health(self) -> Dict[str, Any]:
        """Get detailed service health information."""
        return await self._make_request('GET', '/health/detailed')

    async def get_system_health(self) -> Dict[str, Any]:
        """Get system-wide health information."""
        return await self._make_request('GET', '/health/system')

    # Simulation Management Endpoints

    async def create_simulation(self, simulation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new simulation."""
        return await self._make_request('POST', '/api/v1/simulations', json=simulation_data)

    async def list_simulations(self,
                              status: Optional[str] = None,
                              page: int = 1,
                              page_size: int = 20) -> Dict[str, Any]:
        """List simulations with optional filtering and pagination."""
        params = {'page': page, 'page_size': page_size}
        if status:
            params['status'] = status

        return await self._make_request('GET', '/api/v1/simulations', params=params)

    async def get_simulation_status(self, simulation_id: str) -> Dict[str, Any]:
        """Get the status of a specific simulation."""
        return await self._make_request('GET', f'/api/v1/simulations/{simulation_id}')

    async def get_simulation_results(self, simulation_id: str) -> Dict[str, Any]:
        """Get the results of a completed simulation."""
        return await self._make_request('GET', f'/api/v1/simulations/{simulation_id}/results')

    async def cancel_simulation(self, simulation_id: str) -> Dict[str, Any]:
        """Cancel a running simulation."""
        return await self._make_request('DELETE', f'/api/v1/simulations/{simulation_id}')

    # Simulation Execution Endpoints

    async def execute_simulation(self, simulation_id: str) -> Dict[str, Any]:
        """Execute a simulation asynchronously."""
        return await self._make_request('POST', f'/api/v1/simulations/{simulation_id}/execute')

    async def start_ui_monitoring(self, simulation_id: str) -> Dict[str, Any]:
        """Start UI monitoring for a simulation."""
        return await self._make_request('POST', f'/api/v1/simulations/{simulation_id}/ui/start')

    async def stop_ui_monitoring(self, simulation_id: str, success: bool = True) -> Dict[str, Any]:
        """Stop UI monitoring for a simulation."""
        data = {'success': success}
        return await self._make_request('POST', f'/api/v1/simulations/{simulation_id}/ui/stop', json=data)

    async def get_ui_status(self, simulation_id: str) -> Dict[str, Any]:
        """Get the UI monitoring status for a simulation."""
        return await self._make_request('GET', f'/api/v1/simulations/{simulation_id}/ui/status')

    # Configuration Endpoints

    async def create_simulation_from_config(self, config_file_path: str) -> Dict[str, Any]:
        """Create a simulation from a configuration file."""
        data = {'config_file_path': config_file_path}
        return await self._make_request('POST', '/api/v1/simulations/from-config', json=data)

    async def create_sample_config(self,
                                  file_path: str,
                                  project_name: str = "Sample E-commerce Platform") -> Dict[str, Any]:
        """Create a sample configuration file."""
        data = {
            'file_path': file_path,
            'project_name': project_name
        }
        return await self._make_request('POST', '/api/v1/config/sample', json=data)

    async def validate_config(self, config_file_path: str) -> Dict[str, Any]:
        """Validate a configuration file."""
        data = {'config_file_path': config_file_path}
        return await self._make_request('POST', '/api/v1/config/validate', json=data)

    async def get_config_template(self) -> Dict[str, Any]:
        """Get a configuration template."""
        return await self._make_request('GET', '/api/v1/config/template')

    # Reporting Endpoints

    async def generate_reports(self,
                              simulation_id: str,
                              report_types: List[str]) -> Dict[str, Any]:
        """Generate reports for a simulation."""
        data = {'report_types': report_types}
        return await self._make_request('POST', f'/api/v1/simulations/{simulation_id}/reports/generate', json=data)

    async def get_simulation_reports(self, simulation_id: str) -> Dict[str, Any]:
        """Get available reports for a simulation."""
        return await self._make_request('GET', f'/api/v1/simulations/{simulation_id}/reports')

    async def get_simulation_report(self,
                                   simulation_id: str,
                                   report_type: str) -> Dict[str, Any]:
        """Get a specific report for a simulation."""
        return await self._make_request('GET', f'/api/v1/simulations/{simulation_id}/reports/{report_type}')

    async def export_report(self,
                           simulation_id: str,
                           report_type: str,
                           format: str = 'json',
                           output_path: Optional[str] = None) -> Dict[str, Any]:
        """Export a simulation report."""
        data = {
            'report_type': report_type,
            'format': format,
            'output_path': output_path
        }
        return await self._make_request('POST', f'/api/v1/simulations/{simulation_id}/reports/export', json=data)

    # Event Endpoints

    async def get_simulation_events(self,
                                   simulation_id: str,
                                   event_types: Optional[List[str]] = None,
                                   start_time: Optional[str] = None,
                                   end_time: Optional[str] = None,
                                   tags: Optional[List[str]] = None,
                                   limit: int = 50,
                                   offset: int = 0) -> Dict[str, Any]:
        """Get events for a simulation."""
        params = {
            'limit': limit,
            'offset': offset
        }

        if event_types:
            params['event_types'] = ','.join(event_types)
        if start_time:
            params['start_time'] = start_time
        if end_time:
            params['end_time'] = end_time
        if tags:
            params['tags'] = ','.join(tags)

        return await self._make_request('GET', f'/api/v1/simulations/{simulation_id}/events', params=params)

    async def get_simulation_timeline(self, simulation_id: str) -> Dict[str, Any]:
        """Get timeline of events for a simulation."""
        return await self._make_request('GET', f'/api/v1/simulations/{simulation_id}/timeline')

    async def replay_events(self,
                           simulation_id: str,
                           event_types: Optional[List[str]] = None,
                           start_time: Optional[str] = None,
                           end_time: Optional[str] = None,
                           tags: Optional[List[str]] = None,
                           speed_multiplier: float = 1.0,
                           include_system_events: bool = False,
                           max_events: Optional[int] = None) -> Dict[str, Any]:
        """Replay events for a simulation."""
        data = {
            'speed_multiplier': speed_multiplier,
            'include_system_events': include_system_events
        }

        if event_types:
            data['event_types'] = event_types
        if start_time:
            data['start_time'] = start_time
        if end_time:
            data['end_time'] = end_time
        if tags:
            data['tags'] = tags
        if max_events:
            data['max_events'] = max_events

        return await self._make_request('POST', f'/api/v1/simulations/{simulation_id}/events/replay', json=data)

    async def get_event_statistics(self,
                                  simulation_id: Optional[str] = None,
                                  start_time: Optional[str] = None,
                                  end_time: Optional[str] = None) -> Dict[str, Any]:
        """Get statistics about stored events."""
        params = {}
        if simulation_id:
            params['simulation_id'] = simulation_id
        if start_time:
            params['start_time'] = start_time
        if end_time:
            params['end_time'] = end_time

        return await self._make_request('GET', '/api/v1/events/statistics', params=params)

    # WebSocket Methods

    async def connect_websocket(self, simulation_id: Optional[str] = None) -> None:
        """Connect to the simulation service WebSocket.

        Args:
            simulation_id: Optional simulation ID to subscribe to specific updates
        """
        try:
            if simulation_id:
                ws_url = f"{self.ws_url}/ws/simulations/{simulation_id}"
            else:
                ws_url = f"{self.ws_url}/ws/system"

            self.websocket = await websockets.connect(ws_url)
            self.ws_connected = True
            self.logger.info(f"Connected to WebSocket: {ws_url}")

        except Exception as e:
            self.logger.error(f"Failed to connect to WebSocket: {e}")
            raise SimulationServiceConnectionError(f"WebSocket connection failed: {e}")

    async def disconnect_websocket(self) -> None:
        """Disconnect from the WebSocket."""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
            self.ws_connected = False
            self.logger.info("Disconnected from WebSocket")

    async def listen_for_events(self) -> AsyncGenerator[Dict[str, Any], None]:
        """Listen for real-time events from the WebSocket.

        Yields:
            Dict containing event data
        """
        if not self.ws_connected:
            raise SimulationServiceConnectionError("WebSocket not connected")

        try:
            async for message in self.websocket:
                try:
                    event_data = json.loads(message)
                    yield event_data
                except json.JSONDecodeError:
                    self.logger.warning(f"Received non-JSON message: {message}")
                    continue

        except websockets.exceptions.ConnectionClosed:
            self.logger.info("WebSocket connection closed")
            self.ws_connected = False
        except Exception as e:
            self.logger.error(f"Error listening for WebSocket events: {e}")
            self.ws_connected = False
            raise

    def add_event_handler(self, event_type: str, handler: Callable) -> None:
        """Add an event handler for a specific event type.

        Args:
            event_type: Type of event to handle
            handler: Callable that takes event data as parameter
        """
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)

    def remove_event_handler(self, event_type: str, handler: Callable) -> None:
        """Remove an event handler.

        Args:
            event_type: Type of event
            handler: Handler to remove
        """
        if event_type in self.event_handlers:
            try:
                self.event_handlers[event_type].remove(handler)
            except ValueError:
                pass  # Handler not found

    async def start_event_listener(self) -> None:
        """Start listening for events and dispatching to handlers."""
        try:
            async for event in self.listen_for_events():
                event_type = event.get('event_type', 'unknown')

                # Call specific handlers
                if event_type in self.event_handlers:
                    for handler in self.event_handlers[event_type]:
                        try:
                            await handler(event)
                        except Exception as e:
                            self.logger.error(f"Error in event handler for {event_type}: {e}")

                # Call general handlers
                if '*' in self.event_handlers:
                    for handler in self.event_handlers['*']:
                        try:
                            await handler(event)
                        except Exception as e:
                            self.logger.error(f"Error in general event handler: {e}")

        except Exception as e:
            self.logger.error(f"Event listener failed: {e}")
            raise

    # Utility Methods

    async def wait_for_simulation_completion(self,
                                           simulation_id: str,
                                           timeout_seconds: int = 3600,
                                           poll_interval: float = 5.0) -> Dict[str, Any]:
        """Wait for a simulation to complete.

        Args:
            simulation_id: ID of the simulation to wait for
            timeout_seconds: Maximum time to wait
            poll_interval: How often to check status

        Returns:
            Final simulation status
        """
        start_time = time.time()

        while time.time() - start_time < timeout_seconds:
            try:
                status = await self.get_simulation_status(simulation_id)
                sim_status = status.get('data', {}).get('status', '')

                if sim_status in ['completed', 'failed', 'cancelled']:
                    return status

                await asyncio.sleep(poll_interval)

            except Exception as e:
                self.logger.warning(f"Error checking simulation status: {e}")
                await asyncio.sleep(poll_interval)

        # Timeout
        raise SimulationClientError(f"Simulation {simulation_id} did not complete within {timeout_seconds} seconds")

    async def get_simulation_progress_stream(self,
                                           simulation_id: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Get a stream of simulation progress updates.

        Args:
            simulation_id: ID of the simulation to monitor

        Yields:
            Progress update data
        """
        try:
            # Connect to WebSocket for real-time updates
            await self.connect_websocket(simulation_id)

            async for event in self.listen_for_events():
                if event.get('simulation_id') == simulation_id:
                    event_type = event.get('event_type', '')

                    if event_type in ['simulation_started', 'phase_completed',
                                    'document_generated', 'workflow_executed',
                                    'simulation_completed', 'simulation_failed']:
                        yield event

        except Exception as e:
            self.logger.error(f"Error in progress stream: {e}")
            raise
        finally:
            await self.disconnect_websocket()

    # Helper Methods for Dashboard Integration

    def get_simulation_summary(self, simulation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract simulation summary information for dashboard display."""
        data = simulation_data.get('data', {})

        return {
            'id': data.get('simulation_id', ''),
            'name': data.get('name', 'Unknown'),
            'status': data.get('status', 'unknown'),
            'progress_percentage': data.get('progress_percentage', 0),
            'current_phase': data.get('current_phase', ''),
            'documents_generated': data.get('documents_generated', 0),
            'workflows_executed': data.get('workflows_executed', 0),
            'start_time': data.get('start_time'),
            'estimated_completion': data.get('estimated_completion'),
            'active_tasks': data.get('active_tasks', []),
            'completed_tasks': data.get('completed_tasks', []),
            'failed_tasks': data.get('failed_tasks', [])
        }

    def format_simulation_status_for_display(self, status: str) -> Dict[str, str]:
        """Format simulation status for dashboard display."""
        status_config = {
            'created': {'text': 'Created', 'color': 'gray', 'icon': '📝'},
            'running': {'text': 'Running', 'color': 'green', 'icon': '🚀'},
            'completed': {'text': 'Completed', 'color': 'blue', 'icon': '✅'},
            'failed': {'text': 'Failed', 'color': 'red', 'icon': '❌'},
            'cancelled': {'text': 'Cancelled', 'color': 'orange', 'icon': '⏹️'},
            'paused': {'text': 'Paused', 'color': 'yellow', 'icon': '⏸️'}
        }

        return status_config.get(status.lower(), {'text': status.title(), 'color': 'gray', 'icon': '❓'})