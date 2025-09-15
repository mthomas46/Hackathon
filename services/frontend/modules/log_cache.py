"""Log caching and streaming infrastructure for Frontend service.

Provides caching for log data from the log collector service and
supports real-time log streaming for visualization and troubleshooting.
"""
from typing import Dict, Any, List, Optional, AsyncGenerator
import asyncio
import json
from datetime import datetime, timedelta
from collections import defaultdict
import httpx

from services.shared.utilities import utc_now
from .shared_utils import get_log_collector_url, get_frontend_clients


class LogCache:
    """In-memory cache for log data from the log collector service."""

    def __init__(self):
        self._logs: List[Dict[str, Any]] = []
        self._stats_cache: Dict[str, Any] = {}
        self._last_stats_update = None
        self._max_logs = 1000  # Keep last 1000 logs in memory
        self._stats_cache_ttl = 30  # Cache stats for 30 seconds

    def add_logs(self, logs: List[Dict[str, Any]]) -> None:
        """Add new logs to the cache."""
        self._logs.extend(logs)

        # Maintain bounded history
        if len(self._logs) > self._max_logs:
            excess = len(self._logs) - self._max_logs
            self._logs = self._logs[excess:]

    def get_recent_logs(
        self,
        service: Optional[str] = None,
        level: Optional[str] = None,
        limit: int = 100,
        since: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get recent logs with optional filtering."""
        filtered_logs = self._logs

        # Filter by service
        if service:
            filtered_logs = [log for log in filtered_logs if log.get("service") == service]

        # Filter by level
        if level:
            level_lower = level.lower()
            filtered_logs = [log for log in filtered_logs if log.get("level", "").lower() == level_lower]

        # Filter by timestamp
        if since:
            try:
                since_dt = datetime.fromisoformat(since.replace('Z', '+00:00'))
                filtered_logs = [log for log in filtered_logs
                               if datetime.fromisoformat(log.get("timestamp", "").replace('Z', '+00:00')) > since_dt]
            except (ValueError, AttributeError):
                pass  # Invalid timestamp format, ignore filter

        return filtered_logs[-limit:] if limit > 0 else filtered_logs

    def get_stats(self) -> Optional[Dict[str, Any]]:
        """Get cached statistics if still fresh."""
        if self._stats_cache and self._last_stats_update:
            if utc_now() - self._last_stats_update < timedelta(seconds=self._stats_cache_ttl):
                return self._stats_cache
        return None

    def update_stats(self, stats: Dict[str, Any]) -> None:
        """Update the cached statistics."""
        self._stats_cache = stats
        self._last_stats_update = utc_now()

    def get_log_summary(self) -> Dict[str, Any]:
        """Get a summary of cached logs."""
        if not self._logs:
            return {
                "total_logs": 0,
                "services": [],
                "levels": [],
                "time_range": None,
                "last_log_time": None
            }

        services = set()
        levels = set()
        timestamps = []

        for log in self._logs:
            services.add(log.get("service", "unknown"))
            levels.add(log.get("level", "unknown"))

            try:
                ts = datetime.fromisoformat(log.get("timestamp", "").replace('Z', '+00:00'))
                timestamps.append(ts)
            except (ValueError, AttributeError):
                pass

        time_range = None
        if timestamps:
            min_time = min(timestamps)
            max_time = max(timestamps)
            time_range = {
                "start": min_time.isoformat(),
                "end": max_time.isoformat(),
                "duration_seconds": (max_time - min_time).total_seconds()
            }

        last_log_time = max(timestamps).isoformat() if timestamps else None

        return {
            "total_logs": len(self._logs),
            "services": sorted(list(services)),
            "levels": sorted(list(levels)),
            "time_range": time_range,
            "last_log_time": last_log_time
        }

    def clear_cache(self) -> None:
        """Clear all cached data."""
        self._logs.clear()
        self._stats_cache.clear()
        self._last_stats_update = None


# Global cache instance
log_cache = LogCache()


async def fetch_logs_from_collector(
    service: Optional[str] = None,
    level: Optional[str] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """Fetch logs from the log collector service."""
    try:
        clients = get_frontend_clients()
        log_collector_url = get_log_collector_url()

        params = {}
        if service:
            params["service"] = service
        if level:
            params["level"] = level
        if limit:
            params["limit"] = limit

        response = await clients.get_json(f"{log_collector_url}/logs", params=params)
        logs = response.get("items", [])

        # Update cache with fresh data
        log_cache.add_logs(logs)

        return logs

    except Exception as e:
        return [{"error": f"Failed to fetch logs: {str(e)}", "level": "error", "service": "frontend"}]


async def fetch_log_stats_from_collector() -> Dict[str, Any]:
    """Fetch log statistics from the log collector service."""
    try:
        clients = get_frontend_clients()
        log_collector_url = get_log_collector_url()

        stats = await clients.get_json(f"{log_collector_url}/stats")

        # Update cache
        log_cache.update_stats(stats)

        return stats

    except Exception as e:
        return {"error": f"Failed to fetch stats: {str(e)}", "count": 0}


async def stream_logs(
    service: Optional[str] = None,
    level: Optional[str] = None,
    poll_interval: int = 5
) -> AsyncGenerator[Dict[str, Any], None]:
    """Stream logs in real-time by polling the log collector."""
    last_timestamp = None

    while True:
        try:
            # Get recent logs since last poll
            logs = await fetch_logs_from_collector(service=service, level=level, limit=50)

            # Filter for new logs only
            if last_timestamp:
                new_logs = []
                for log in logs:
                    try:
                        log_ts = datetime.fromisoformat(log.get("timestamp", "").replace('Z', '+00:00'))
                        if log_ts > last_timestamp:
                            new_logs.append(log)
                    except (ValueError, AttributeError):
                        new_logs.append(log)  # Include logs with invalid timestamps
                logs = new_logs

            # Update last timestamp
            if logs:
                try:
                    latest_ts = max(
                        datetime.fromisoformat(log.get("timestamp", "").replace('Z', '+00:00'))
                        for log in logs
                        if log.get("timestamp")
                    )
                    last_timestamp = latest_ts
                except (ValueError, AttributeError):
                    pass

            # Yield each log
            for log in logs:
                yield log

        except Exception as e:
            yield {"error": f"Streaming error: {str(e)}", "level": "error", "service": "frontend"}
            await asyncio.sleep(1)  # Brief pause on error

        # Wait before next poll
        await asyncio.sleep(poll_interval)


def get_cached_logs_data() -> Dict[str, Any]:
    """Get all cached log data for visualization."""
    return {
        "logs": log_cache.get_recent_logs(limit=200),  # Return last 200 logs
        "stats": log_cache.get_stats(),
        "summary": log_cache.get_log_summary(),
        "last_updated": utc_now().isoformat()
    }


def analyze_log_patterns(logs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze logs for patterns and insights."""
    if not logs:
        return {"patterns": {}, "insights": []}

    # Count patterns
    patterns = {
        "error_rate": 0,
        "services_active": set(),
        "levels_distribution": defaultdict(int),
        "recent_errors": [],
        "frequent_messages": defaultdict(int)
    }

    recent_cutoff = utc_now() - timedelta(minutes=5)

    for log in logs:
        level = log.get("level", "").lower()
        service = log.get("service", "unknown")
        message = log.get("message", "")
        timestamp = log.get("timestamp")

        patterns["services_active"].add(service)
        patterns["levels_distribution"][level] += 1

        # Check for recent errors
        if level in ("error", "fatal") and timestamp:
            try:
                log_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                if log_time > recent_cutoff:
                    patterns["recent_errors"].append({
                        "service": service,
                        "message": message[:100],
                        "timestamp": timestamp
                    })
            except (ValueError, AttributeError):
                pass

        # Track frequent messages (first 50 chars as key)
        if message:
            msg_key = message[:50]
            patterns["frequent_messages"][msg_key] += 1

    # Calculate error rate
    total_logs = len(logs)
    error_count = patterns["levels_distribution"].get("error", 0) + patterns["levels_distribution"].get("fatal", 0)
    patterns["error_rate"] = (error_count / total_logs) * 100 if total_logs > 0 else 0

    patterns["services_active"] = list(patterns["services_active"])

    # Get top frequent messages
    top_messages = sorted(patterns["frequent_messages"].items(), key=lambda x: x[1], reverse=True)[:5]
    patterns["frequent_messages"] = [{"message": msg, "count": count} for msg, count in top_messages]

    # Generate insights
    insights = []
    if patterns["error_rate"] > 10:
        insights.append("High error rate detected (>10%)")
    if len(patterns["recent_errors"]) > 5:
        insights.append(f"Multiple recent errors: {len(patterns['recent_errors'])} in last 5 minutes")
    if len(patterns["services_active"]) < 3:
        insights.append("Limited service activity detected")

    return {
        "patterns": patterns,
        "insights": insights
    }
