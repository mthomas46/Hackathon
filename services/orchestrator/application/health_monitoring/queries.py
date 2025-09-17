"""Application Queries for Health Monitoring"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class GetSystemHealthQuery:
    """Query to get overall system health."""
    include_metrics: bool = True
    timeout_seconds: float = 5.0


@dataclass
class GetServiceHealthQuery:
    """Query to get health of a specific service."""
    service_name: str
    timeout_seconds: float = 5.0


@dataclass
class GetSystemInfoQuery:
    """Query to get system information."""


@dataclass
class GetSystemMetricsQuery:
    """Query to get system metrics."""


@dataclass
class GetSystemConfigQuery:
    """Query to get effective system configuration."""


@dataclass
class CheckSystemReadinessQuery:
    """Query to check if system is ready."""


@dataclass
class ListWorkflowsQuery:
    """Query to list available workflows (moved from old health handlers)."""
    limit: int = 50
    offset: int = 0
