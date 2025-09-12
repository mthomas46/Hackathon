"""Log storage management for log collector service."""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone


class LogStorage:
    """Manages in-memory log storage with bounded history."""

    def __init__(self, max_logs: int = 5000):
        self._logs: List[Dict[str, Any]] = []
        self._max_logs = max_logs

    def add_log(self, log_entry: Dict[str, Any]) -> int:
        """Add a log entry and return the current count."""
        # Ensure timestamp is set
        if "timestamp" not in log_entry or not log_entry["timestamp"]:
            log_entry["timestamp"] = self._now_iso()

        self._logs.append(log_entry)

        # Maintain bounded history
        if len(self._logs) > self._max_logs:
            del self._logs[: len(self._logs) - self._max_logs]

        return len(self._logs)

    def add_logs_batch(self, log_entries: List[Dict[str, Any]]) -> int:
        """Add multiple log entries and return the current count."""
        for entry in log_entries:
            self.add_log(entry)
        return len(self._logs)

    def get_logs(
        self,
        service: Optional[str] = None,
        level: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get filtered logs with optional limit."""
        filtered = [
            log for log in self._logs
            if (service is None or log.get("service") == service) and
               (level is None or log.get("level") == level)
        ]
        return filtered[-limit:] if limit > 0 else filtered

    def get_all_logs(self) -> List[Dict[str, Any]]:
        """Get all logs."""
        return self._logs.copy()

    def get_count(self) -> int:
        """Get current log count."""
        return len(self._logs)

    def clear_logs(self) -> None:
        """Clear all logs (for testing)."""
        self._logs.clear()

    @staticmethod
    def _now_iso() -> str:
        """Get current timestamp in ISO format."""
        return datetime.now(timezone.utc).isoformat()


# Global instance
log_storage = LogStorage()
