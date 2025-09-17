"""Application Commands for Health Monitoring"""

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class CheckSystemHealthCommand:
    """Command to check overall system health."""
    include_metrics: bool = True
    timeout_seconds: float = 5.0


@dataclass
class CheckServiceHealthCommand:
    """Command to check health of a specific service."""
    service_name: str
    timeout_seconds: float = 5.0


@dataclass
class RegisterHealthCheckCommand:
    """Command to register a custom health check for a service."""
    service_name: str
    check_function_name: str  # Reference to check function
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class UpdateSystemMetricsCommand:
    """Command to update system metrics."""
    metrics: Dict[str, Any]
