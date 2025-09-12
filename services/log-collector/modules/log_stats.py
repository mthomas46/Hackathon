"""Log statistics calculation for log collector service."""

from typing import Dict, List, Tuple, Any
from collections import defaultdict


def calculate_log_statistics(logs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate comprehensive statistics from log entries."""

    by_level: Dict[str, int] = defaultdict(int)
    by_service: Dict[str, int] = defaultdict(int)
    errors_by_service: Dict[str, int] = defaultdict(int)

    for log in logs:
        level = str(log.get("level", "")).lower()
        service = log.get("service", "")

        by_level[level] += 1
        by_service[service] += 1

        if level in ("error", "fatal"):
            errors_by_service[service] += 1

    # Get top services by log count
    top_services = sorted(by_service.items(), key=lambda x: x[1], reverse=True)[:5]

    return {
        "count": len(logs),
        "by_level": dict(by_level),
        "by_service": dict(by_service),
        "errors_by_service": dict(errors_by_service),
        "top_services": top_services,
    }
