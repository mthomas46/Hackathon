"""Log storage management for log collector service.

Provides in-memory storage for log entries with automatic cleanup,
bounded history to prevent memory exhaustion, and file-based log rotation.
"""

import os
import json
import gzip
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pathlib import Path


class LogStorage:
    """Manages in-memory log storage with bounded history and automatic cleanup.

    This class provides thread-safe storage for log entries with configurable
    maximum capacity. When the limit is reached, older entries are automatically
    removed to maintain bounded memory usage.
    """

    def __init__(self, max_logs: int = 5000, enable_rotation: bool = True,
                 rotation_dir: str = "/app/logs/archive",
                 max_file_size_mb: int = 10, max_files: int = 5):
        """Initialize log storage with capacity limit and rotation.

        Args:
            max_logs: Maximum number of log entries to retain in memory (default: 5000)
            enable_rotation: Whether to enable file-based log rotation (default: True)
            rotation_dir: Directory to store rotated log files (default: /app/logs/archive)
            max_file_size_mb: Maximum size of each log file before rotation (default: 10MB)
            max_files: Maximum number of rotated files to keep (default: 5)
        """
        self._logs: List[Dict[str, Any]] = []
        self._max_logs = max_logs
        self._enable_rotation = enable_rotation
        self._rotation_dir = Path(rotation_dir)
        self._max_file_size_mb = max_file_size_mb
        self._max_files = max_files
        self._current_file_size = 0
        self._current_file_path: Optional[Path] = None

        # Create rotation directory if it doesn't exist
        if self._enable_rotation:
            self._rotation_dir.mkdir(parents=True, exist_ok=True)
            self._create_new_log_file()

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

        # Write to file with rotation if enabled
        if self._enable_rotation:
            self._write_log_to_file(log_entry)

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
        limit: int = 100,
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

    def get_logs_advanced(self, service: Optional[str] = None, level: Optional[str] = None,
                         limit: int = 100, message_contains: Optional[str] = None,
                         start_time: Optional[str] = None, end_time: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get logs with advanced filtering capabilities.

        Args:
            service: Filter by service name
            level: Filter by log level
            limit: Maximum number of logs to return
            message_contains: Filter by message content (case-insensitive substring)
            start_time: Filter logs after this ISO timestamp
            end_time: Filter logs before this ISO timestamp

        Returns:
            List of matching log entries, most recent first
        """
        filtered_logs = []

        # Parse time filters
        start_dt = None
        end_dt = None
        if start_time:
            try:
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            except ValueError:
                pass  # Invalid timestamp, ignore filter
        if end_time:
            try:
                end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            except ValueError:
                pass  # Invalid timestamp, ignore filter

        # Filter logs (start from most recent)
        for log in reversed(self._logs):
            if len(filtered_logs) >= limit and limit > 0:
                break

            # Service filter
            if service and log.get("service") != service:
                continue

            # Level filter
            if level and log.get("level") != level:
                continue

            # Message content filter
            if message_contains:
                message = log.get("message", "").lower()
                if message_contains.lower() not in message:
                    continue

            # Time range filters
            if start_dt or end_dt:
                try:
                    log_time = datetime.fromisoformat(log.get("timestamp", "").replace('Z', '+00:00'))
                    if start_dt and log_time < start_dt:
                        continue
                    if end_dt and log_time > end_dt:
                        continue
                except (ValueError, AttributeError):
                    # If timestamp parsing fails, include the log (fail open)
                    pass

            filtered_logs.append(log)

        return filtered_logs

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

    def _create_new_log_file(self):
        """Create a new log file for writing."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"logs_{timestamp}.jsonl"
        self._current_file_path = self._rotation_dir / filename
        self._current_file_size = 0

        # Clean up old files if we exceed max_files
        self._cleanup_old_files()

    def _write_log_to_file(self, log_entry: Dict[str, Any]):
        """Write a log entry to the current file with rotation."""
        if not self._current_file_path:
            return

        # Convert log entry to JSON line
        log_line = json.dumps(log_entry, default=str) + "\n"
        log_size_bytes = len(log_line.encode('utf-8'))

        # Check if we need to rotate
        if (self._current_file_size + log_size_bytes) > (self._max_file_size_mb * 1024 * 1024):
            self._rotate_log_file()

        # Write to file
        try:
            with open(self._current_file_path, 'a', encoding='utf-8') as f:
                f.write(log_line)
            self._current_file_size += log_size_bytes
        except Exception as e:
            # Log error but don't fail - logging shouldn't break the application
            print(f"Failed to write log to file: {e}")

    def _rotate_log_file(self):
        """Rotate the current log file by compressing it."""
        if not self._current_file_path or not self._current_file_path.exists():
            self._create_new_log_file()
            return

        # Compress the current file
        compressed_path = self._current_file_path.with_suffix('.jsonl.gz')
        try:
            with open(self._current_file_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    f_out.writelines(f_in)

            # Remove the uncompressed file
            self._current_file_path.unlink()

        except Exception as e:
            print(f"Failed to compress log file: {e}")

        # Create new file
        self._create_new_log_file()

    def _cleanup_old_files(self):
        """Remove old rotated log files to maintain max_files limit."""
        try:
            # Get all compressed log files
            log_files = list(self._rotation_dir.glob("logs_*.jsonl.gz"))

            # Sort by modification time (newest first)
            log_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

            # Remove files beyond max_files
            if len(log_files) > self._max_files:
                files_to_remove = log_files[self._max_files:]
                for file_path in files_to_remove:
                    try:
                        file_path.unlink()
                    except Exception as e:
                        print(f"Failed to remove old log file {file_path}: {e}")

        except Exception as e:
            print(f"Failed to cleanup old log files: {e}")

    def get_rotation_stats(self) -> Dict[str, Any]:
        """Get statistics about log rotation."""
        try:
            log_files = list(self._rotation_dir.glob("logs_*.jsonl.gz"))
            total_size = sum(f.stat().st_size for f in log_files)

            return {
                "rotation_enabled": self._enable_rotation,
                "rotation_dir": str(self._rotation_dir),
                "current_file": str(self._current_file_path) if self._current_file_path else None,
                "current_file_size_mb": self._current_file_size / (1024 * 1024),
                "max_file_size_mb": self._max_file_size_mb,
                "rotated_files_count": len(log_files),
                "max_files": self._max_files,
                "total_rotated_size_mb": total_size / (1024 * 1024)
            }
        except Exception as e:
            return {
                "error": f"Failed to get rotation stats: {e}",
                "rotation_enabled": self._enable_rotation
            }


# Global instance with rotation enabled
log_storage = LogStorage(
    max_logs=int(os.environ.get("LOG_STORAGE_MAX_LOGS", "5000")),
    enable_rotation=os.environ.get("LOG_ROTATION_ENABLED", "true").lower() == "true",
    rotation_dir=os.environ.get("LOG_ROTATION_DIR", "/app/logs/archive"),
    max_file_size_mb=int(os.environ.get("LOG_MAX_FILE_SIZE_MB", "10")),
    max_files=int(os.environ.get("LOG_MAX_FILES", "5"))
)
