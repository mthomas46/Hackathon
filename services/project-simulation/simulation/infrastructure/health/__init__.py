"""Health Infrastructure Package.

This package contains health monitoring and checking functionality
for the project-simulation service.

Modules:
- simulation_health: Comprehensive health checks and monitoring
"""

# Re-export key functions from simulation_health for easier imports
from .simulation_health import (
    get_simulation_health_checker,
    get_simulation_health_endpoint
)

# Add mock function for create_simulation_health_endpoints
def create_simulation_health_endpoints():
    """Mock function for creating simulation health endpoints."""
    pass

__all__ = [
    'get_simulation_health_checker',
    'get_simulation_health_endpoint',
    'create_simulation_health_endpoints'
]