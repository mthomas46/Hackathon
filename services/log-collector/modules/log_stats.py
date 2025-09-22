"""Log statistics calculation for log collector service.

Provides comprehensive analytics and aggregations for log data
to support system monitoring and diagnostics with enhanced metrics.
"""

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional


def calculate_log_statistics(logs: List[Dict[str, Any]], time_window_hours: Optional[int] = None) -> Dict[str, Any]:
    """Calculate comprehensive statistics and analytics from log entries.

    Analyzes the complete log dataset to provide insights into system behavior,
    error rates, service activity levels, and other key metrics for monitoring.

    Args:
        logs: Complete list of log entries to analyze
        time_window_hours: Optional time window in hours to analyze (None = all logs)

    Returns:
        Dictionary containing various statistics and aggregations including:
        - Total count of logs
        - Breakdown by log level and service
        - Error rates by service
        - Top services by log volume
        - Performance metrics and trends
        - Time-based analysis
    """
    # Filter logs by time window if specified
    if time_window_hours:
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=time_window_hours)
        filtered_logs = []
        for log in logs:
            try:
                log_time = datetime.fromisoformat(log.get("timestamp", "").replace("Z", "+00:00"))
                if log_time > cutoff_time:
                    filtered_logs.append(log)
            except (ValueError, AttributeError):
                # If timestamp parsing fails, include the log
                filtered_logs.append(log)
        logs = filtered_logs

    # Initialize counters for different aggregation types
    by_level: Dict[str, int] = defaultdict(int)
    by_service: Dict[str, int] = defaultdict(int)
    errors_by_service: Dict[str, int] = defaultdict(int)
    hourly_distribution: Dict[str, int] = defaultdict(int)
    response_times: List[float] = []
    message_patterns: Dict[str, int] = defaultdict(int)

    # Track time range
    timestamps = []
    error_messages = []

    # Process each log entry to build aggregations
    for log in logs:
        level = str(log.get("level", "")).lower()
        service = log.get("service", "")
        message = log.get("message", "")
        context = log.get("context", {})

        # Basic counts
        by_level[level] += 1
        by_service[service] += 1

        # Track errors separately for error rate analysis
        if level in ("error", "fatal"):
            errors_by_service[service] += 1
            error_messages.append(
                {
                    "service": service,
                    "message": message[:200],  # Truncate long messages
                    "timestamp": log.get("timestamp"),
                }
            )

        # Time-based analysis
        if log.get("timestamp"):
            try:
                dt = datetime.fromisoformat(log["timestamp"].replace("Z", "+00:00"))
                timestamps.append(dt)
                hour_key = f"{dt.hour:02d}:00"
                hourly_distribution[hour_key] += 1
            except (ValueError, AttributeError):
                pass

        # Response time analysis
        if isinstance(context.get("response_time"), (int, float)):
            response_times.append(context["response_time"])

        # Message pattern analysis (simplified keyword extraction)
        keywords = ["error", "failed", "timeout", "exception", "success", "completed", "started"]
        for keyword in keywords:
            if keyword.lower() in message.lower():
                message_patterns[keyword] += 1

    # Calculate time range
    time_range = {}
    if timestamps:
        time_range = {
            "start": min(timestamps).isoformat(),
            "end": max(timestamps).isoformat(),
            "duration_hours": (max(timestamps) - min(timestamps)).total_seconds() / 3600,
        }

    # Performance metrics
    performance = {}
    if response_times:
        performance["avg_response_time"] = sum(response_times) / len(response_times)
        performance["min_response_time"] = min(response_times)
        performance["max_response_time"] = max(response_times)
        performance["p95_response_time"] = sorted(response_times)[int(len(response_times) * 0.95)]

    # Calculate throughput
    if time_range and time_range.get("duration_hours", 0) > 0:
        performance["logs_per_hour"] = len(logs) / time_range["duration_hours"]

    # Error rate analysis
    error_rate = len(error_messages) / len(logs) if logs else 0

    # Service health scores (simplified)
    service_health = {}
    for service, count in by_service.items():
        error_count = errors_by_service.get(service, 0)
        health_score = max(0, 100 - (error_count / count * 100)) if count > 0 else 100
        service_health[service] = {
            "total_logs": count,
            "error_count": error_count,
            "error_rate": error_count / count if count > 0 else 0,
            "health_score": health_score,
        }

    # Identify top 5 services by log volume for quick diagnostics
    top_services = sorted(by_service.items(), key=lambda x: x[1], reverse=True)[:5]

    # Most common error patterns
    top_errors = sorted(message_patterns.items(), key=lambda x: x[1], reverse=True)[:5]

    return {
        "total_logs": len(logs),
        "time_window_hours": time_window_hours,
        "time_range": time_range,
        "by_level": dict(by_level),
        "by_service": dict(by_service),
        "errors_by_service": dict(errors_by_service),
        "top_services": top_services,
        "hourly_distribution": dict(hourly_distribution),
        "error_rate": error_rate,
        "recent_errors": error_messages[-10:],  # Last 10 errors
        "service_health": service_health,
        "performance": performance,
        "message_patterns": dict(message_patterns),
        "top_error_patterns": top_errors,
        "summary": {
            "healthy_services": sum(1 for s in service_health.values() if s["health_score"] > 80),
            "unhealthy_services": sum(1 for s in service_health.values() if s["health_score"] <= 80),
            "total_services": len(service_health),
            "avg_health_score": (
                sum(s["health_score"] for s in service_health.values()) / len(service_health) if service_health else 100
            ),
        },
    }
