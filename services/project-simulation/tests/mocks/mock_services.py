"""Mock Services - Comprehensive service mocking for testing.

Provides mock implementations of all major services used in the Project
Simulation Service, following ecosystem mocking patterns for consistent
test behavior and reliable isolation.
"""

import asyncio
from typing import Dict, Any, List, Optional, Union
from unittest.mock import AsyncMock, MagicMock, Mock
from datetime import datetime

from services.project_simulation.simulation.domain.value_objects import (
    ProjectType, ComplexityLevel, ProjectStatus
)


class MockLogger:
    """Mock logger that captures all logging calls for verification."""

    def __init__(self):
        self.info_calls = []
        self.error_calls = []
        self.warning_calls = []
        self.debug_calls = []

    def info(self, message: str, **kwargs):
        """Mock info logging."""
        self.info_calls.append({"message": message, "kwargs": kwargs})

    def error(self, message: str, **kwargs):
        """Mock error logging."""
        self.error_calls.append({"message": message, "kwargs": kwargs})

    def warning(self, message: str, **kwargs):
        """Mock warning logging."""
        self.warning_calls.append({"message": message, "kwargs": kwargs})

    def debug(self, message: str, **kwargs):
        """Mock debug logging."""
        self.debug_calls.append({"message": message, "kwargs": kwargs})

    def reset(self):
        """Reset all captured calls."""
        self.info_calls.clear()
        self.error_calls.clear()
        self.warning_calls.clear()
        self.debug_calls.clear()


class MockMonitoring:
    """Mock monitoring service that captures metrics."""

    def __init__(self):
        self.metrics = {}
        self.performance_calls = []
        self.health_calls = []

    def record_metric(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Record a metric."""
        if name not in self.metrics:
            self.metrics[name] = []
        self.metrics[name].append({"value": value, "tags": tags or {}, "timestamp": datetime.now()})

    def record_performance(self, operation: str, duration_ms: float, **kwargs):
        """Record performance metric."""
        self.performance_calls.append({
            "operation": operation,
            "duration_ms": duration_ms,
            "kwargs": kwargs,
            "timestamp": datetime.now()
        })

    def record_health_check(self, service: str, status: str, **kwargs):
        """Record health check."""
        self.health_calls.append({
            "service": service,
            "status": status,
            "kwargs": kwargs,
            "timestamp": datetime.now()
        })

    def reset(self):
        """Reset all captured data."""
        self.metrics.clear()
        self.performance_calls.clear()
        self.health_calls.clear()


class MockSimulationApplicationService:
    """Mock application service with configurable behavior."""

    def __init__(self):
        self.created_simulations = {}
        self.executed_simulations = {}
        self.cancelled_simulations = []
        self.should_fail = False
        self.delay_seconds = 0

        # Mock responses
        self.create_response = {
            "success": True,
            "simulation_id": "mock_simulation_001",
            "message": "Simulation created successfully"
        }

        self.execute_response = {
            "success": True,
            "simulation_id": "mock_simulation_001",
            "message": "Simulation execution started"
        }

        self.status_response = {
            "success": True,
            "simulation_id": "mock_simulation_001",
            "status": "completed",
            "message": "Simulation completed successfully"
        }

    async def create_simulation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock simulation creation."""
        if self.delay_seconds > 0:
            await asyncio.sleep(self.delay_seconds)

        if self.should_fail:
            return {"success": False, "error": "Mock failure"}

        simulation_id = f"mock_simulation_{len(self.created_simulations) + 1}"
        self.created_simulations[simulation_id] = data

        response = self.create_response.copy()
        response["simulation_id"] = simulation_id
        return response

    async def execute_simulation(self, simulation_id: str) -> Dict[str, Any]:
        """Mock simulation execution."""
        if self.delay_seconds > 0:
            await asyncio.sleep(self.delay_seconds)

        if self.should_fail:
            return {"success": False, "error": "Mock execution failure"}

        self.executed_simulations[simulation_id] = datetime.now()
        return self.execute_response

    async def get_simulation_status(self, simulation_id: str) -> Dict[str, Any]:
        """Mock get simulation status."""
        if self.delay_seconds > 0:
            await asyncio.sleep(self.delay_seconds)

        if simulation_id not in self.created_simulations:
            return {"success": False, "error": "Simulation not found"}

        if self.should_fail:
            return {"success": False, "error": "Mock status failure"}

        response = self.status_response.copy()
        response["simulation_id"] = simulation_id
        return response

    async def cancel_simulation(self, simulation_id: str) -> Dict[str, Any]:
        """Mock simulation cancellation."""
        if self.delay_seconds > 0:
            await asyncio.sleep(self.delay_seconds)

        if simulation_id not in self.created_simulations:
            return {"success": False, "error": "Simulation not found"}

        self.cancelled_simulations.append(simulation_id)
        return {"success": True, "message": "Simulation cancelled"}

    async def list_simulations(self, status: Optional[str] = None,
                             limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """Mock list simulations."""
        if self.delay_seconds > 0:
            await asyncio.sleep(self.delay_seconds)

        simulations = []
        for sim_id, data in self.created_simulations.items():
            if status is None or data.get("status") == status:
                simulations.append({
                    "id": sim_id,
                    "name": data.get("name", "Mock Simulation"),
                    "status": data.get("status", "created"),
                    "created_at": datetime.now().isoformat()
                })

        # Apply pagination
        total_count = len(simulations)
        paginated_simulations = simulations[offset:offset + limit]

        return {
            "success": True,
            "simulations": paginated_simulations,
            "total_count": total_count,
            "limit": limit,
            "offset": offset
        }

    def reset(self):
        """Reset mock state."""
        self.created_simulations.clear()
        self.executed_simulations.clear()
        self.cancelled_simulations.clear()
        self.should_fail = False
        self.delay_seconds = 0


class MockDomainService:
    """Mock domain service with configurable behavior."""

    def __init__(self):
        self.created_projects = {}
        self.assigned_teams = {}
        self.generated_timelines = {}
        self.should_fail = False
        self.delay_seconds = 0

    async def create_project(self, project_data: Dict[str, Any]) -> Any:
        """Mock project creation."""
        if self.delay_seconds > 0:
            await asyncio.sleep(self.delay_seconds)

        if self.should_fail:
            raise ValueError("Mock domain service failure")

        # Create a mock project object
        mock_project = MagicMock()
        mock_project.project_id = project_data.get("project_id", "mock_project_001")
        mock_project.name = project_data.get("name", "Mock Project")
        mock_project.project_type = project_data.get("project_type", ProjectType.WEB_APPLICATION)
        mock_project.complexity = project_data.get("complexity", ComplexityLevel.MEDIUM)
        mock_project.status = ProjectStatus.PLANNING
        mock_project.events = [MagicMock()]  # Mock domain events

        self.created_projects[mock_project.project_id] = mock_project
        return mock_project

    async def assign_team_to_project(self, project_id: str, team_members: List[Any]) -> Any:
        """Mock team assignment."""
        if self.delay_seconds > 0:
            await asyncio.sleep(self.delay_seconds)

        if project_id not in self.created_projects:
            raise ValueError(f"Project {project_id} not found")

        if self.should_fail:
            raise ValueError("Mock team assignment failure")

        project = self.created_projects[project_id]
        project.team_members = team_members
        self.assigned_teams[project_id] = team_members

        return project

    async def generate_project_timeline(self, project_id: str) -> Any:
        """Mock timeline generation."""
        if self.delay_seconds > 0:
            await asyncio.sleep(self.delay_seconds)

        if project_id not in self.created_projects:
            raise ValueError(f"Project {project_id} not found")

        if self.should_fail:
            raise ValueError("Mock timeline generation failure")

        # Create mock timeline
        mock_timeline = MagicMock()
        mock_timeline.phases = [
            MagicMock(name="Planning", start_date=datetime.now(), end_date=datetime.now()),
            MagicMock(name="Development", start_date=datetime.now(), end_date=datetime.now()),
            MagicMock(name="Testing", start_date=datetime.now(), end_date=datetime.now())
        ]

        self.generated_timelines[project_id] = mock_timeline
        return mock_timeline

    def reset(self):
        """Reset mock state."""
        self.created_projects.clear()
        self.assigned_teams.clear()
        self.generated_timelines.clear()
        self.should_fail = False
        self.delay_seconds = 0


class MockHealthService:
    """Mock health service for testing health endpoints."""

    def __init__(self):
        self.checks = {}
        self.should_fail = False
        self.response_delay = 0

    async def health_check(self) -> Dict[str, Any]:
        """Mock basic health check."""
        if self.response_delay > 0:
            await asyncio.sleep(self.response_delay)

        if self.should_fail:
            return {"status": "unhealthy", "error": "Mock health failure"}

        return {
            "status": "healthy",
            "service": "project-simulation",
            "version": "1.0.0",
            "uptime_seconds": 3600,
            "environment": "testing"
        }

    async def detailed_health_check(self) -> Dict[str, Any]:
        """Mock detailed health check."""
        if self.response_delay > 0:
            await asyncio.sleep(self.response_delay)

        if self.should_fail:
            return {"status": "unhealthy", "error": "Mock detailed health failure"}

        return {
            "status": "healthy",
            "service": "project-simulation",
            "version": "1.0.0",
            "uptime_seconds": 3600,
            "environment": "testing",
            "dependencies": {
                "database": {"status": "healthy", "response_time_ms": 10},
                "cache": {"status": "healthy", "response_time_ms": 5},
                "external_services": {"status": "healthy", "response_time_ms": 50}
            },
            "system_resources": {
                "cpu_usage": 45.2,
                "memory_usage": 67.8,
                "disk_usage": 23.1
            }
        }

    async def system_health_check(self) -> Dict[str, Any]:
        """Mock system-wide health check."""
        if self.response_delay > 0:
            await asyncio.sleep(self.response_delay)

        if self.should_fail:
            return {
                "overall_healthy": False,
                "services_checked": 5,
                "services_healthy": 3,
                "services_unhealthy": 2,
                "service_details": {
                    "project-simulation": {"status": "unhealthy", "error": "Mock failure"}
                }
            }

        return {
            "overall_healthy": True,
            "services_checked": 5,
            "services_healthy": 5,
            "services_unhealthy": 0,
            "timestamp": datetime.now().isoformat(),
            "service_details": {
                "project-simulation": {"status": "healthy", "response_time_ms": 10},
                "mock-data-generator": {"status": "healthy", "response_time_ms": 15},
                "analysis-service": {"status": "healthy", "response_time_ms": 25},
                "doc-store": {"status": "healthy", "response_time_ms": 8},
                "llm-gateway": {"status": "healthy", "response_time_ms": 30}
            },
            "environment_info": {
                "environment": "testing",
                "region": "us-east-1",
                "cluster": "test-cluster"
            }
        }

    def reset(self):
        """Reset mock state."""
        self.checks.clear()
        self.should_fail = False
        self.response_delay = 0


class MockWebSocketHandler:
    """Mock WebSocket handler for testing real-time features."""

    def __init__(self):
        self.connections = {}
        self.messages_sent = []
        self.should_fail = False

    async def handle_simulation_connection(self, websocket: Any, simulation_id: str):
        """Mock simulation WebSocket connection."""
        if self.should_fail:
            raise Exception("Mock WebSocket failure")

        self.connections[simulation_id] = websocket

        # Simulate connection handling
        try:
            while True:
                # In a real implementation, this would handle WebSocket messages
                await asyncio.sleep(1)
        except Exception:
            # Connection closed
            pass

    async def handle_general_connection(self, websocket: Any):
        """Mock general WebSocket connection."""
        if self.should_fail:
            raise Exception("Mock WebSocket failure")

        connection_id = f"general_{len(self.connections)}"
        self.connections[connection_id] = websocket

    async def send_message(self, simulation_id: str, message: Dict[str, Any]):
        """Mock sending message to simulation."""
        self.messages_sent.append({
            "simulation_id": simulation_id,
            "message": message,
            "timestamp": datetime.now()
        })

    async def broadcast_message(self, message: Dict[str, Any]):
        """Mock broadcasting message to all connections."""
        self.messages_sent.append({
            "type": "broadcast",
            "message": message,
            "timestamp": datetime.now(),
            "connections_count": len(self.connections)
        })

    def reset(self):
        """Reset mock state."""
        self.connections.clear()
        self.messages_sent.clear()
        self.should_fail = False


# Factory functions for easy mock creation
def create_mock_application_service(**kwargs) -> MockSimulationApplicationService:
    """Create configured mock application service."""
    service = MockSimulationApplicationService()

    for key, value in kwargs.items():
        if hasattr(service, key):
            setattr(service, key, value)

    return service


def create_mock_domain_service(**kwargs) -> MockDomainService:
    """Create configured mock domain service."""
    service = MockDomainService()

    for key, value in kwargs.items():
        if hasattr(service, key):
            setattr(service, key, value)

    return service


def create_mock_logger() -> MockLogger:
    """Create mock logger."""
    return MockLogger()


def create_mock_monitoring() -> MockMonitoring:
    """Create mock monitoring service."""
    return MockMonitoring()


def create_mock_health_service(**kwargs) -> MockHealthService:
    """Create configured mock health service."""
    service = MockHealthService()

    for key, value in kwargs.items():
        if hasattr(service, key):
            setattr(service, key, value)

    return service


def create_mock_websocket_handler(**kwargs) -> MockWebSocketHandler:
    """Create configured mock WebSocket handler."""
    handler = MockWebSocketHandler()

    for key, value in kwargs.items():
        if hasattr(handler, key):
            setattr(handler, key, value)

    return handler


__all__ = [
    'MockLogger',
    'MockMonitoring',
    'MockSimulationApplicationService',
    'MockDomainService',
    'MockHealthService',
    'MockWebSocketHandler',
    'create_mock_application_service',
    'create_mock_domain_service',
    'create_mock_logger',
    'create_mock_monitoring',
    'create_mock_health_service',
    'create_mock_websocket_handler'
]
