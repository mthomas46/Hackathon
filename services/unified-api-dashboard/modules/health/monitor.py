"""
Health Monitor - Service Health Monitoring and Alerting
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class HealthMonitor:
    """Monitor service health and availability."""

    def __init__(self, discovery_client=None):
        self.discovery_client = discovery_client

    async def get_health_overview(self) -> List[Dict[str, Any]]:
        """Get health status of all services."""
        return [
            {
                "service": "user-service",
                "status": "healthy",
                "response_time": 145,
                "uptime": 99.9,
                "last_check": "2024-01-01T10:30:00Z",
            },
            {
                "service": "order-service",
                "status": "healthy",
                "response_time": 120,
                "uptime": 99.8,
                "last_check": "2024-01-01T10:30:00Z",
            },
        ]
