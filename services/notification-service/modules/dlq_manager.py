"""Dead letter queue management for notification service."""

import time
from typing import List, Dict, Any


class DLQManager:
    """Manages dead letter queue for failed notifications."""

    def __init__(self):
        self._dlq: List[Dict[str, Any]] = []

    def add_failed_notification(
        self,
        payload: Dict[str, Any],
        error: str
    ) -> None:
        """Add a failed notification to the dead letter queue."""
        entry = {
            "payload": payload,
            "error": error,
            "ts": time.time()
        }
        self._dlq.append(entry)

    def get_dlq_entries(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get dead letter queue entries with optional limit."""
        # Return most recent entries first, limited by the specified count
        max_limit = min(limit, 500)  # Cap at 500 to prevent excessive memory usage
        return self._dlq[-max_limit:] if max_limit > 0 else self._dlq

    def get_dlq_count(self) -> int:
        """Get the current count of DLQ entries."""
        return len(self._dlq)

    def clear_dlq(self) -> None:
        """Clear all entries from the dead letter queue."""
        self._dlq.clear()

    def prune_old_entries(self, max_age_seconds: int = 86400) -> int:
        """Remove entries older than max_age_seconds. Returns count of removed entries."""
        cutoff_time = time.time() - max_age_seconds
        old_count = len(self._dlq)
        self._dlq = [entry for entry in self._dlq if entry.get("ts", 0) > cutoff_time]
        return old_count - len(self._dlq)


# Global instance
dlq_manager = DLQManager()
