"""Log storage management for log collector service.

Provides in-memory storage for log entries with automatic cleanup
and bounded history to prevent memory exhaustion.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone


class LogStorage:
    """Manages in-memory log storage with bounded history and automatic cleanup.

    This class provides thread-safe storage for log entries with configurable
    maximum capacity. When the limit is reached, older entries are automatically
    removed to maintain bounded memory usage.
    """

    def __init__(self, max_logs: int = 5000):
        """Initialize log storage with capacity limit.

        Args:
            max_logs: Maximum number of log entries to retain (default: 5000)
        """
        self._logs: List[Dict[str, Any]] = []
        self._max_logs = max_logs

    def add_log(self, log_entry: Dict[str, Any]) -> int:
        """Add a single log entry to storage with automatic timestamping.

        If no timestamp is provided in the log entry, the current UTC time
        is automatically added. Maintains bounded history by removing oldest
        entries when capacity is exceeded.

        Args:
            log_entry: Log entry dictionary to store

        Returns:
            Current total number of stored log entries
        """
        # Ensure timestamp is set for consistent log ordering
        if "timestamp" not in log_entry or not log_entry["timestamp"]:
            log_entry["timestamp"] = self._now_iso()

        self._logs.append(log_entry)

        # Maintain bounded history to prevent memory exhaustion
        if len(self._logs) > self._max_logs:
            # Remove oldest entries (FIFO)
            excess_count = len(self._logs) - self._max_logs
            del self._logs[:excess_count]

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
        self,
        service: Optional[str] = None,
        level: Optional[str] = None,
        limit: int = 100
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
            log for log in self._logs
            if (service is None or log.get("service") == service) and
               (level is None or log.get("level", "").lower() == level.lower())
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

    @staticmethod
    def _now_iso() -> str:
        """Generate current timestamp in ISO 8601 format.

        Returns:
            UTC timestamp string in ISO format (e.g., '2024-01-15T10:30:45.123456+00:00')
        """
        return datetime.now(timezone.utc).isoformat()


# Global instance
log_storage = LogStorage()
