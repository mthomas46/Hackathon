"""
Metrics endpoint for Prometheus.

Exposes metrics at /metrics in Prometheus format.
"""

import logging
from fastapi import APIRouter

from ...utils.metrics import get_metrics_response

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/metrics",
    summary="Prometheus metrics",
    description="Expose metrics in Prometheus format",
    include_in_schema=False  # Don't show in OpenAPI docs
)
async def metrics():
    """
    Get Prometheus metrics.
    
    Returns metrics in Prometheus text format for scraping.
    """
    return get_metrics_response()

