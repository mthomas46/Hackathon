"""Log statistics calculation for log collector service.

Provides comprehensive analytics and aggregations for log data
to support system monitoring and diagnostics.
"""
from typing import Dict, List, Any
from collections import defaultdict


def calculate_log_statistics(logs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate comprehensive statistics and analytics from log entries.

    Analyzes the complete log dataset to provide insights into system behavior,
    error rates, service activity levels, and other key metrics for monitoring.

    Args:
        logs: Complete list of log entries to analyze

    Returns:
        Dictionary containing various statistics and aggregations including:
        - Total count of logs
        - Breakdown by log level and service
        - Error rates by service
        - Top services by log volume
    """
    # Initialize counters for different aggregation types
    by_level: Dict[str, int] = defaultdict(int)
    by_service: Dict[str, int] = defaultdict(int)
    errors_by_service: Dict[str, int] = defaultdict(int)

    # Process each log entry to build aggregations
    for log in logs:
        level = str(log.get("level", "")).lower()
        service = log.get("service", "")

        # Count by log level (normalized to lowercase)
        by_level[level] += 1

        # Count by service
        by_service[service] += 1

        # Track errors separately for error rate analysis
        if level in ("error", "fatal"):
            errors_by_service[service] += 1

    # Identify top 5 services by log volume for quick diagnostics
    top_services = sorted(by_service.items(), key=lambda x: x[1], reverse=True)[:5]

    return {
        "count": len(logs),
        "by_level": dict(by_level),
        "by_service": dict(by_service),
        "errors_by_service": dict(errors_by_service),
        "top_services": top_services,
    }
