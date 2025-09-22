"""Log storage management for log collector service.

Provides in-memory storage for log entries with automatic cleanup
and bounded history to prevent memory exhaustion. Now includes
persistent storage options and advanced search capabilities.
"""

import asyncio
import json
import os
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional


class LogStorage:
    """Manages log storage with multiple storage backends and advanced search.

    Supports in-memory storage with optional persistence to disk, automatic
    cleanup, and comprehensive search and filtering capabilities.
    """

    def __init__(
        self,
        max_logs: int = 5000,
        persist_to_disk: bool = False,
        storage_path: Optional[str] = None,
        retention_days: int = 7,
    ):
        """Initialize log storage with capacity limit and persistence options.

        Args:
            max_logs: Maximum number of log entries to retain in memory (default: 5000)
            persist_to_disk: Whether to persist logs to disk for durability
            storage_path: Path to store persistent logs (default: ./logs)
            retention_days: How many days to retain logs on disk (default: 7)
        """
        self._logs: List[Dict[str, Any]] = []
        self._max_logs = max_logs
        self._persist_to_disk = persist_to_disk
        self._retention_days = retention_days
        self._storage_path = Path(storage_path or "./logs")
        self._lock = threading.RLock()

        # Initialize persistent storage if enabled
        if self._persist_to_disk:
            self._storage_path.mkdir(parents=True, exist_ok=True)
            # Defer async initialization to avoid event loop issues during import
            self._needs_async_init = True
        else:
            self._needs_async_init = False

    async def initialize_async(self):
        """Initialize async components after event loop is running."""
        if self._needs_async_init and self._persist_to_disk:
            await self._load_persistent_logs()
            asyncio.create_task(self._cleanup_old_logs())
            self._needs_async_init = False

    def add_log(self, log_entry: Dict[str, Any]) -> int:
        """Add a single log entry to storage with automatic timestamping.

        If no timestamp is provided in the log entry, the current UTC time
        is automatically added. Maintains bounded history by removing oldest
        entries when capacity is exceeded. Persists to disk if enabled.

        Args:
            log_entry: Log entry dictionary to store

        Returns:
            Current total number of stored log entries
        """
        with self._lock:
            # Ensure timestamp is set for consistent log ordering
            if "timestamp" not in log_entry or not log_entry["timestamp"]:
                log_entry["timestamp"] = self._now_iso()

            self._logs.append(log_entry)

            # Maintain bounded history to prevent memory exhaustion
            if len(self._logs) > self._max_logs:
                # Remove oldest entries (FIFO)
                excess_count = len(self._logs) - self._max_logs
                del self._logs[:excess_count]

            # Persist to disk if enabled
            if self._persist_to_disk:
                asyncio.create_task(self._persist_log_entry(log_entry))

        return len(self._logs)

    def add_logs_batch(self, log_entries: List[Dict[str, Any]]) -> int:
        """Add multiple log entries efficiently in batch.

        Processes each log entry individually to ensure proper timestamping
        and capacity management.

        Args:
            log_entries: List of log entry dictionaries to store

        Returns:
            Current total number of stored log entries after batch addition
        """
        for entry in log_entries:
            self.add_log(entry)
        return len(self._logs)

    def get_logs(
        self, service: Optional[str] = None, level: Optional[str] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Retrieve filtered logs with optional pagination.

        Filters logs by service name and/or log level, then returns
        the most recent entries up to the specified limit.

        Args:
            service: Filter by service name (case-sensitive)
            level: Filter by log level (case-insensitive)
            limit: Maximum number of entries to return (0 = unlimited)

        Returns:
            List of matching log entries, most recent first
        """
        filtered = [
            log
            for log in self._logs
            if (service is None or log.get("service") == service)
            and (level is None or log.get("level", "").lower() == level.lower())
        ]
        return filtered[-limit:] if limit > 0 else filtered

    def get_all_logs(self) -> List[Dict[str, Any]]:
        """Get a copy of all stored log entries.

        Returns:
            Complete list of all log entries (defensive copy)
        """
        return self._logs.copy()

    def get_count(self) -> int:
        """Get the current number of stored log entries.

        Returns:
            Total count of log entries in storage
        """
        return len(self._logs)

    def clear_logs(self) -> None:
        """Clear all stored log entries (primarily for testing).

        This method removes all log entries from storage.
        Use with caution in production environments.
        """
        self._logs.clear()

    def search_logs(
        self, query: str, fields: Optional[List[str]] = None, case_sensitive: bool = False, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Search logs using full-text search across specified fields.

        Args:
            query: Search query string
            fields: Fields to search in (default: all text fields)
            case_sensitive: Whether search should be case sensitive
            limit: Maximum results to return

        Returns:
            List of matching log entries
        """
        if not query.strip():
            return []

        default_fields = ["message", "service", "level"]
        search_fields = fields or default_fields

        matches = []
        query_lower = query.lower() if not case_sensitive else query

        with self._lock:
            for log in reversed(self._logs):  # Search most recent first
                if len(matches) >= limit:
                    break

                for field in search_fields:
                    field_value = str(log.get(field, "")).lower() if not case_sensitive else str(log.get(field, ""))

                    if query_lower in field_value:
                        matches.append(log)
                        break  # Don't check other fields for this log

        return matches

    def get_logs_by_time_range(
        self, start_time: Optional[str] = None, end_time: Optional[str] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get logs within a specific time range.

        Args:
            start_time: ISO timestamp for start of range (inclusive)
            end_time: ISO timestamp for end of range (inclusive)
            limit: Maximum results to return

        Returns:
            List of log entries in the time range
        """
        results = []

        with self._lock:
            for log in reversed(self._logs):  # Most recent first
                if len(results) >= limit:
                    break

                log_time = log.get("timestamp", "")
                if start_time and log_time < start_time:
                    continue
                if end_time and log_time > end_time:
                    continue

                results.append(log)

        return results

    def get_service_metrics(self, service_name: Optional[str] = None, time_window_minutes: int = 60) -> Dict[str, Any]:
        """Get detailed metrics for a specific service or all services.

        Args:
            service_name: Specific service to analyze (None for all)
            time_window_minutes: Analysis window in minutes

        Returns:
            Detailed service metrics
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=time_window_minutes)

        with self._lock:
            relevant_logs = [
                log
                for log in self._logs
                if datetime.fromisoformat(log.get("timestamp", "2000-01-01T00:00:00+00:00").replace("Z", "+00:00"))
                > cutoff_time
            ]

        if service_name:
            relevant_logs = [log for log in relevant_logs if log.get("service") == service_name]

        # Calculate detailed metrics
        metrics = {
            "total_logs": len(relevant_logs),
            "time_window_minutes": time_window_minutes,
            "services": {},
            "levels": {},
            "errors": [],
            "performance": {
                "avg_response_time": None,
                "error_rate": 0.0,
                "throughput_per_minute": len(relevant_logs) / max(time_window_minutes, 1),
            },
        }

        response_times = []
        error_count = 0

        for log in relevant_logs:
            service = log.get("service", "unknown")
            level = log.get("level", "unknown").lower()

            # Count by service
            if service not in metrics["services"]:
                metrics["services"][service] = {"count": 0, "levels": {}}
            metrics["services"][service]["count"] += 1

            # Count by level per service
            if level not in metrics["services"][service]["levels"]:
                metrics["services"][service]["levels"][level] = 0
            metrics["services"][service]["levels"][level] += 1

            # Global level counts
            if level not in metrics["levels"]:
                metrics["levels"][level] = 0
            metrics["levels"][level] += 1

            # Collect errors
            if level in ("error", "fatal"):
                error_count += 1
                metrics["errors"].append(
                    {
                        "timestamp": log.get("timestamp"),
                        "service": service,
                        "message": log.get("message", "")[:200],  # Truncate long messages
                    }
                )

            # Collect response times from context
            if log.get("context") and "response_time" in log["context"]:
                response_times.append(log["context"]["response_time"])

        # Calculate performance metrics
        if response_times:
            metrics["performance"]["avg_response_time"] = sum(response_times) / len(response_times)

        if relevant_logs:
            metrics["performance"]["error_rate"] = error_count / len(relevant_logs)

        return metrics

    async def _persist_log_entry(self, log_entry: Dict[str, Any]) -> None:
        """Persist a log entry to disk asynchronously."""
        try:
            # Create filename based on date
            timestamp = log_entry.get("timestamp", "")
            if timestamp:
                date_part = timestamp.split("T")[0]  # YYYY-MM-DD
            else:
                date_part = self._now_iso().split("T")[0]

            log_file = self._storage_path / f"logs_{date_part}.jsonl"

            # Append to file (create if doesn't exist)
            async with asyncio.Lock():  # File access lock
                with open(log_file, "a", encoding="utf-8") as f:
                    json.dump(log_entry, f, ensure_ascii=False)
                    f.write("\n")

        except Exception as e:
            # Log persistence errors (without recursing)
            print(f"Warning: Failed to persist log entry: {e}")

    async def _load_persistent_logs(self) -> None:
        """Load recent persistent logs into memory on startup."""
        try:
            if not self._storage_path.exists():
                return

            # Load logs from the last few days
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=1)

            loaded_count = 0
            for log_file in sorted(self._storage_path.glob("logs_*.jsonl")):
                try:
                    with open(log_file, "r", encoding="utf-8") as f:
                        for line in f:
                            if line.strip():
                                log_entry = json.loads(line.strip())

                                # Only load recent entries
                                entry_time = datetime.fromisoformat(
                                    log_entry.get("timestamp", "2000-01-01T00:00:00+00:00").replace("Z", "+00:00")
                                )

                                if entry_time > cutoff_date:
                                    with self._lock:
                                        self._logs.append(log_entry)
                                        loaded_count += 1

                                        # Maintain memory bounds
                                        if len(self._logs) > self._max_logs:
                                            self._logs.pop(0)  # Remove oldest

                except Exception as e:
                    print(f"Warning: Failed to load log file {log_file}: {e}")

            if loaded_count > 0:
                # Sort by timestamp after loading
                with self._lock:
                    self._logs.sort(key=lambda x: x.get("timestamp", ""))

                print(f"Loaded {loaded_count} persistent log entries")

        except Exception as e:
            print(f"Warning: Failed to load persistent logs: {e}")

    async def _cleanup_old_logs(self) -> None:
        """Clean up old log files based on retention policy."""
        try:
            if not self._storage_path.exists():
                return

            cutoff_date = datetime.now(timezone.utc) - timedelta(days=self._retention_days)

            deleted_count = 0
            for log_file in self._storage_path.glob("logs_*.jsonl"):
                try:
                    # Extract date from filename
                    date_str = log_file.stem.replace("logs_", "")
                    file_date = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)

                    if file_date < cutoff_date:
                        log_file.unlink()
                        deleted_count += 1

                except (ValueError, OSError) as e:
                    print(f"Warning: Failed to process log file {log_file}: {e}")

            if deleted_count > 0:
                print(f"Cleaned up {deleted_count} old log files")

        except Exception as e:
            print(f"Warning: Failed to cleanup old logs: {e}")

    def export_logs(
        self, filepath: str, service: Optional[str] = None, level: Optional[str] = None, format: str = "json"
    ) -> int:
        """Export logs to a file with optional filtering.

        Args:
            filepath: Path to export file
            service: Filter by service name
            level: Filter by log level
            format: Export format ('json' or 'jsonl')

        Returns:
            Number of logs exported
        """
        logs_to_export = self.get_logs(service=service, level=level, limit=0)  # No limit

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                if format == "json":
                    json.dump(logs_to_export, f, indent=2, ensure_ascii=False)
                elif format == "jsonl":
                    for log in logs_to_export:
                        json.dump(log, f, ensure_ascii=False)
                        f.write("\n")
                else:
                    raise ValueError(f"Unsupported export format: {format}")

            return len(logs_to_export)

        except Exception as e:
            print(f"Error exporting logs: {e}")
            return 0

    @staticmethod
    def _now_iso() -> str:
        """Generate current timestamp in ISO 8601 format.

        Returns:
            UTC timestamp string in ISO format (e.g., '2024-01-15T10:30:45.123456+00:00')
        """
        return datetime.now(timezone.utc).isoformat()


# Global instance with default settings
log_storage = LogStorage()

# Enhanced instance with persistence (can be used as alternative)
persistent_log_storage = LogStorage(max_logs=10000, persist_to_disk=True, storage_path="./logs", retention_days=30)
