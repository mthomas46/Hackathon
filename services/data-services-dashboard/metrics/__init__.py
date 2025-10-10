"""
Metrics calculation for data-services-dashboard.

Provides metric calculation and aggregation functionality.
"""

from .calculator import (
    calculate_metrics,
    aggregate_by_service,
    calculate_error_rate,
    calculate_avg_duration,
    calculate_operations_per_service
)

__all__ = [
    "calculate_metrics",
    "aggregate_by_service",
    "calculate_error_rate",
    "calculate_avg_duration",
    "calculate_operations_per_service",
]

