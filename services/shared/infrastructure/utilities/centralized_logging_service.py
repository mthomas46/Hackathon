"""Centralized Logging Service for log aggregation, storage, and analysis.

Provides enterprise-grade log management with:
- Log aggregation from multiple sources
- Structured log storage and indexing
- Advanced querying and filtering
- Log retention policies
- Real-time log streaming
- Integration with existing logging service
"""

import asyncio
import gzip
import hashlib
import json
import logging
import os
import re
import shutil
import sqlite3
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, AsyncIterator, Callable, Dict, List, Optional


logger = logging.getLogger(__name__)


class LogLevel(Enum):
    """Log levels for filtering and analysis."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogStorageType(Enum):
    """Storage types for log persistence."""

    MEMORY = "memory"  # In-memory only (development)
    SQLITE = "sqlite"  # SQLite database (small deployments)
    FILE = "file"  # File-based with rotation (medium deployments)
    DISTRIBUTED = "distributed"  # For future distributed storage


@dataclass
class LogEntry:
    """Structured log entry for storage."""

    id: str
    timestamp: float
    level: str
    service_name: str
    message: str
    correlation_id: Optional[str]
    operation: Optional[str]
    user_id: Optional[str]
    session_id: Optional[str]
    request_id: Optional[str]
    extra_data: Dict[str, Any] = field(default_factory=dict)
    stack_trace: Optional[str] = None
    performance_data: Optional[Dict[str, Any]] = None
    tags: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LogEntry":
        """Create LogEntry from dictionary."""
        return cls(
            id=data.get(
                "id",
                str(hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()),
            ),
            timestamp=data.get("timestamp", time.time()),
            level=data.get("level", "INFO"),
            service_name=data.get("service_name", "unknown"),
            message=data.get("message", ""),
            correlation_id=data.get("correlation_id"),
            operation=data.get("operation"),
            user_id=data.get("user_id"),
            session_id=data.get("session_id"),
            request_id=data.get("request_id"),
            extra_data=data.get("extra_data", {}),
            stack_trace=data.get("stack_trace"),
            performance_data=data.get("performance_data"),
            tags=data.get("tags", []),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "level": self.level,
            "service_name": self.service_name,
            "message": self.message,
            "correlation_id": self.correlation_id,
            "operation": self.operation,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "request_id": self.request_id,
            "extra_data": self.extra_data,
            "stack_trace": self.stack_trace,
            "performance_data": self.performance_data,
            "tags": self.tags,
        }


@dataclass
class LogQuery:
    """Query parameters for log retrieval."""

    service_name: Optional[str] = None
    level: Optional[str] = None
    correlation_id: Optional[str] = None
    operation: Optional[str] = None
    user_id: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    message_contains: Optional[str] = None
    tags: Optional[List[str]] = None
    limit: int = 100
    offset: int = 0
    order_by: str = "timestamp"
    order_desc: bool = True


@dataclass
class LogRetentionPolicy:
    """Log retention policy configuration."""

    max_age_days: int = 30
    max_size_mb: int = 1000
    compression_enabled: bool = True
    archive_path: Optional[str] = None


class LogStorageBackend:
    """Abstract base class for log storage backends."""

    async def store_log(self, log_entry: LogEntry) -> None:
        """Store a log entry."""
        raise NotImplementedError

    async def query_logs(self, query: LogQuery) -> List[LogEntry]:
        """Query logs based on parameters."""
        raise NotImplementedError

    async def get_log_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        raise NotImplementedError

    async def cleanup_old_logs(self, retention_policy: LogRetentionPolicy) -> int:
        """Clean up old logs based on retention policy."""
        raise NotImplementedError


class MemoryLogStorage(LogStorageBackend):
    """In-memory log storage for development."""

    def __init__(self):
        """Initialize in-memory log storage."""
        self._logs: List[LogEntry] = []
        self._lock = threading.Lock()

    async def store_log(self, log_entry: LogEntry) -> None:
        """Store log in memory."""
        with self._lock:
            self._logs.append(log_entry)
            # Keep only last 10,000 logs
            if len(self._logs) > 10000:
                self._logs.pop(0)

    async def query_logs(self, query: LogQuery) -> List[LogEntry]:
        """Query logs from memory with improved performance and maintainability."""
        with self._lock:
            logs_copy = self._logs.copy()

        # Apply filters using dedicated filter methods
        filtered_logs = self._apply_log_filters(logs_copy, query)

        # Apply ordering using dedicated sorting method
        ordered_logs = self._apply_log_ordering(filtered_logs, query)

        # Apply pagination
        return self._apply_log_pagination(ordered_logs, query)

    def _apply_log_filters(self, logs: List[LogEntry], query: LogQuery) -> List[LogEntry]:
        """Apply all query filters to the log list."""
        filters = [
            self._filter_by_service_name,
            self._filter_by_level,
            self._filter_by_correlation_id,
            self._filter_by_operation,
            self._filter_by_time_range,
            self._filter_by_message_content
        ]

        filtered_logs = logs
        for filter_func in filters:
            filtered_logs = filter_func(filtered_logs, query)

        return filtered_logs

    def _filter_by_service_name(self, logs: List[LogEntry], query: LogQuery) -> List[LogEntry]:
        """Filter logs by service name."""
        if not query.service_name:
            return logs
        return [log for log in logs if log.service_name == query.service_name]

    def _filter_by_level(self, logs: List[LogEntry], query: LogQuery) -> List[LogEntry]:
        """Filter logs by log level."""
        if not query.level:
            return logs
        return [log for log in logs if log.level == query.level]

    def _filter_by_correlation_id(self, logs: List[LogEntry], query: LogQuery) -> List[LogEntry]:
        """Filter logs by correlation ID."""
        if not query.correlation_id:
            return logs
        return [log for log in logs if log.correlation_id == query.correlation_id]

    def _filter_by_operation(self, logs: List[LogEntry], query: LogQuery) -> List[LogEntry]:
        """Filter logs by operation."""
        if not query.operation:
            return logs
        return [log for log in logs if log.operation == query.operation]

    def _filter_by_time_range(self, logs: List[LogEntry], query: LogQuery) -> List[LogEntry]:
        """Filter logs by time range."""
        filtered_logs = logs

        if query.start_time:
            filtered_logs = [log for log in filtered_logs if log.timestamp >= query.start_time]

        if query.end_time:
            filtered_logs = [log for log in filtered_logs if log.timestamp <= query.end_time]

        return filtered_logs

    def _filter_by_message_content(self, logs: List[LogEntry], query: LogQuery) -> List[LogEntry]:
        """Filter logs by message content."""
        if not query.message_contains:
            return logs

        search_term = query.message_contains.lower()
        return [log for log in logs if search_term in log.message.lower()]

    def _apply_log_ordering(self, logs: List[LogEntry], query: LogQuery) -> List[LogEntry]:
        """Apply ordering to the filtered logs."""
        if not query.order_by:
            return logs

        if query.order_by == "timestamp":
            return sorted(logs, key=lambda x: x.timestamp, reverse=query.order_desc)
        elif query.order_by == "level":
            level_order = {level.value: i for i, level in enumerate(LogLevel)}
            return sorted(
                logs,
                key=lambda x: level_order.get(x.level, 99),
                reverse=query.order_desc
            )

        return logs

    def _apply_log_pagination(self, logs: List[LogEntry], query: LogQuery) -> List[LogEntry]:
        """Apply pagination to the ordered logs."""
        start_idx = query.offset
        end_idx = start_idx + query.limit
        return logs[start_idx:end_idx]

    async def get_log_stats(self) -> Dict[str, Any]:
        """Get memory storage statistics."""
        with self._lock:
            total_logs = len(self._logs)
            service_counts = defaultdict(int)
            level_counts = defaultdict(int)

            for log in self._logs:
                service_counts[log.service_name] += 1
                level_counts[log.level] += 1

            return {
                "storage_type": "memory",
                "total_logs": total_logs,
                "services": dict(service_counts),
                "levels": dict(level_counts),
                "memory_usage_mb": len(self._logs) * 0.5,  # Rough estimate
            }

    async def cleanup_old_logs(self, retention_policy: LogRetentionPolicy) -> int:
        """Clean up old logs from memory."""
        cutoff_time = time.time() - (retention_policy.max_age_days * 24 * 60 * 60)

        with self._lock:
            old_count = len(self._logs)
            self._logs = [log for log in self._logs if log.timestamp >= cutoff_time]
            removed_count = old_count - len(self._logs)

        return removed_count


class SQLiteLogStorage(LogStorageBackend):
    """SQLite-based log storage for persistent storage."""

    def __init__(self, db_path: str = "logs.db"):
        """Initialize SQLite log storage.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """Initialize SQLite database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS logs (
                    id TEXT PRIMARY KEY,
                    timestamp REAL,
                    level TEXT,
                    service_name TEXT,
                    message TEXT,
                    correlation_id TEXT,
                    operation TEXT,
                    user_id TEXT,
                    session_id TEXT,
                    request_id TEXT,
                    extra_data TEXT,
                    stack_trace TEXT,
                    performance_data TEXT,
                    tags TEXT
                )
            """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON logs(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_service ON logs(service_name)")
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_correlation ON logs(correlation_id)"
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_level ON logs(level)")

    async def store_log(self, log_entry: LogEntry) -> None:
        """Store log in SQLite database."""

        def _store():
            """Store log entry in SQLite database."""
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO logs
                    (id, timestamp, level, service_name, message, correlation_id,
                    operation, user_id, session_id, request_id, extra_data,
                    stack_trace, performance_data, tags)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        log_entry.id,
                        log_entry.timestamp,
                        log_entry.level,
                        log_entry.service_name,
                        log_entry.message,
                        log_entry.correlation_id,
                        log_entry.operation,
                        log_entry.user_id,
                        log_entry.session_id,
                        log_entry.request_id,
                        json.dumps(log_entry.extra_data),
                        log_entry.stack_trace,
                        (
                            json.dumps(log_entry.performance_data)
                            if log_entry.performance_data
                            else None
                        ),
                        json.dumps(log_entry.tags),
                    ),
                )

        await asyncio.get_event_loop().run_in_executor(None, _store)

    async def query_logs(self, query: LogQuery) -> List[LogEntry]:
        """Query logs from SQLite database."""

        def _query():
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row

                conditions = []
                params = []

                if query.service_name:
                    conditions.append("service_name = ?")
                    params.append(query.service_name)
                if query.level:
                    conditions.append("level = ?")
                    params.append(query.level)
                if query.correlation_id:
                    conditions.append("correlation_id = ?")
                    params.append(query.correlation_id)
                if query.operation:
                    conditions.append("operation = ?")
                    params.append(query.operation)
                if query.start_time:
                    conditions.append("timestamp >= ?")
                    params.append(query.start_time)
                if query.end_time:
                    conditions.append("timestamp <= ?")
                    params.append(query.end_time)
                if query.message_contains:
                    conditions.append("message LIKE ?")
                    params.append(f"%{query.message_contains}%")

                where_clause = " AND ".join(conditions) if conditions else "1=1"
                order_clause = (
                    f"ORDER BY {query.order_by} {'DESC' if query.order_desc else 'ASC'}"
                )
                limit_clause = f"LIMIT {query.limit} OFFSET {query.offset}"

                sql = f"SELECT * FROM logs WHERE {where_clause} {order_clause} {limit_clause}"

                rows = conn.execute(sql, params).fetchall()
                return [self._row_to_log_entry(row) for row in rows]

        return await asyncio.get_event_loop().run_in_executor(None, _query)

    def _row_to_log_entry(self, row) -> LogEntry:
        """Convert database row to LogEntry."""
        return LogEntry(
            id=row["id"],
            timestamp=row["timestamp"],
            level=row["level"],
            service_name=row["service_name"],
            message=row["message"],
            correlation_id=row["correlation_id"],
            operation=row["operation"],
            user_id=row["user_id"],
            session_id=row["session_id"],
            request_id=row["request_id"],
            extra_data=json.loads(row["extra_data"]) if row["extra_data"] else {},
            stack_trace=row["stack_trace"],
            performance_data=(
                json.loads(row["performance_data"]) if row["performance_data"] else None
            ),
            tags=json.loads(row["tags"]) if row["tags"] else [],
        )

    async def get_log_stats(self) -> Dict[str, Any]:
        """Get SQLite storage statistics."""

        def _stats():
            with sqlite3.connect(self.db_path) as conn:
                # Get total count
                total_logs = conn.execute("SELECT COUNT(*) FROM logs").fetchone()[0]

                # Get service breakdown
                service_rows = conn.execute(
                    """
                    SELECT service_name, COUNT(*) as count
                    FROM logs GROUP BY service_name
                    ORDER BY count DESC LIMIT 10
                """
                ).fetchall()

                # Get level breakdown
                level_rows = conn.execute(
                    """
                    SELECT level, COUNT(*) as count
                    FROM logs GROUP BY level
                """
                ).fetchall()

                # Get database file size
                db_size = (
                    os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
                )

                return {
                    "storage_type": "sqlite",
                    "total_logs": total_logs,
                    "database_size_mb": db_size / (1024 * 1024),
                    "services": {row[0]: row[1] for row in service_rows},
                    "levels": {row[0]: row[1] for row in level_rows},
                }

        return await asyncio.get_event_loop().run_in_executor(None, _stats)

    async def cleanup_old_logs(self, retention_policy: LogRetentionPolicy) -> int:
        """Clean up old logs from SQLite database."""
        cutoff_time = time.time() - (retention_policy.max_age_days * 24 * 60 * 60)

        def _cleanup():
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "DELETE FROM logs WHERE timestamp < ?", (cutoff_time,)
                )
                return cursor.rowcount

        return await asyncio.get_event_loop().run_in_executor(None, _cleanup)


class FileLogStorage(LogStorageBackend):
    """File-based log storage with rotation and compression."""

    def __init__(self, log_directory: str = "logs"):
        """Initialize file-based log storage.

        Args:
            log_directory: Directory to store log files
        """
        self.log_directory = Path(log_directory)
        self.log_directory.mkdir(exist_ok=True)
        self.current_file: Optional[Path] = None
        self._lock = threading.Lock()

    async def store_log(self, log_entry: LogEntry) -> None:
        """Store log entry in file."""
        # Create filename based on date
        date_str = datetime.fromtimestamp(log_entry.timestamp).strftime("%Y-%m-%d")
        log_file = self.log_directory / f"logs_{date_str}.jsonl"

        # Rotate file if needed (daily rotation)
        if self.current_file != log_file:
            with self._lock:
                self.current_file = log_file

        # Write log entry as JSON line
        log_line = json.dumps(log_entry.to_dict()) + "\n"

        def _write():
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(log_line)

        await asyncio.get_event_loop().run_in_executor(None, _write)

    async def query_logs(self, query: LogQuery) -> List[LogEntry]:
        """Query logs from files (limited implementation)."""
        # This is a simplified implementation - in production, you'd want indexing
        results = []

        # Determine which files to search
        start_date = query.start_time or 0
        end_date = query.end_time or time.time()

        start_datetime = datetime.fromtimestamp(start_date)
        end_datetime = datetime.fromtimestamp(end_date)

        current_date = start_datetime
        while current_date <= end_datetime:
            log_file = (
                self.log_directory / f"logs_{current_date.strftime('%Y-%m-%d')}.jsonl"
            )

            if log_file.exists():
                file_results = await self._query_file(log_file, query)
                results.extend(file_results)

                if len(results) >= query.limit + query.offset:
                    break

            current_date += timedelta(days=1)

        # Apply final pagination
        if query.offset > 0:
            results = results[query.offset :]
        results = results[: query.limit]

        return results

    async def _query_file(self, log_file: Path, query: LogQuery) -> List[LogEntry]:
        """Query a specific log file."""

        def _read_file():
            entries = []
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            try:
                                data = json.loads(line)
                                entry = LogEntry.from_dict(data)
                                if self._matches_query(entry, query):
                                    entries.append(entry)
                            except json.JSONDecodeError:
                                continue
            except FileNotFoundError:
                pass
            return entries

        entries = await asyncio.get_event_loop().run_in_executor(None, _read_file)
        return entries

    def _matches_query(self, entry: LogEntry, query: LogQuery) -> bool:
        """Check if log entry matches query."""
        if query.service_name and entry.service_name != query.service_name:
            return False
        if query.level and entry.level != query.level:
            return False
        if query.correlation_id and entry.correlation_id != query.correlation_id:
            return False
        if query.operation and entry.operation != query.operation:
            return False
        if query.start_time and entry.timestamp < query.start_time:
            return False
        if query.end_time and entry.timestamp > query.end_time:
            return False
        if (
            query.message_contains
            and query.message_contains.lower() not in entry.message.lower()
        ):
            return False
        return True

    async def get_log_stats(self) -> Dict[str, Any]:
        """Get file storage statistics."""

        def _stats():
            total_size = 0
            file_count = 0
            service_counts = defaultdict(int)
            level_counts = defaultdict(int)

            for log_file in self.log_directory.glob("logs_*.jsonl"):
                file_count += 1
                total_size += log_file.stat().st_size

                # Sample some entries for stats (performance optimization)
                try:
                    with open(log_file, "r", encoding="utf-8") as f:
                        for i, line in enumerate(f):
                            if i >= 100:  # Sample first 100 entries per file
                                break
                            if line.strip():
                                try:
                                    data = json.loads(line)
                                    service_counts[
                                        data.get("service_name", "unknown")
                                    ] += 1
                                    level_counts[data.get("level", "INFO")] += 1
                                except json.JSONDecodeError:
                                    continue
                except Exception:
                    continue

            return {
                "storage_type": "file",
                "total_files": file_count,
                "total_size_mb": total_size / (1024 * 1024),
                "services_sample": dict(list(service_counts.items())[:10]),
                "levels_sample": dict(level_counts),
            }

        return await asyncio.get_event_loop().run_in_executor(None, _stats)

    async def cleanup_old_logs(self, retention_policy: LogRetentionPolicy) -> int:
        """Clean up old log files."""

        def _cleanup():
            removed_files = 0
            cutoff_date = datetime.now() - timedelta(days=retention_policy.max_age_days)

            for log_file in self.log_directory.glob("logs_*.jsonl"):
                # Extract date from filename
                date_match = re.search(
                    r"logs_(\d{4}-\d{2}-\d{2})\.jsonl", log_file.name
                )
                if date_match:
                    file_date = datetime.strptime(date_match.group(1), "%Y-%m-%d")
                    if file_date < cutoff_date:
                        # Archive if configured
                        if (
                            retention_policy.archive_path
                            and retention_policy.compression_enabled
                        ):
                            archive_file = (
                                Path(retention_policy.archive_path)
                                / f"{log_file.name}.gz"
                            )
                            archive_file.parent.mkdir(exist_ok=True)

                            with open(log_file, "rb") as f_in:
                                with gzip.open(archive_file, "wb") as f_out:
                                    shutil.copyfileobj(f_in, f_out)

                        # Remove original file
                        log_file.unlink()
                        removed_files += 1

            return removed_files

        return await asyncio.get_event_loop().run_in_executor(None, _cleanup)


class CentralizedLoggingService:
    """Centralized logging service with aggregation and analysis."""

    def __init__(self, storage_type: LogStorageType = LogStorageType.SQLITE):
        """Initialize centralized logging service.

        Args:
            storage_type: Type of storage backend to use
        """
        self.storage_type = storage_type

        # Initialize storage backend
        if storage_type == LogStorageType.MEMORY:
            self.storage = MemoryLogStorage()
        elif storage_type == LogStorageType.SQLITE:
            self.storage = SQLiteLogStorage()
        elif storage_type == LogStorageType.FILE:
            self.storage = FileLogStorage()
        else:
            raise ValueError(f"Unsupported storage type: {storage_type}")

        self.retention_policy = LogRetentionPolicy()
        self._alert_callbacks: List[Callable[[str, Dict[str, Any]], None]] = []
        self._cleanup_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()

        # Real-time streaming
        self._log_stream_listeners: List[asyncio.Queue] = []
        self._stream_task: Optional[asyncio.Task] = None

    async def store_log_entry(self, log_data: Dict[str, Any]) -> None:
        """Store a log entry from external source."""
        log_entry = LogEntry.from_dict(log_data)
        await self.storage.store_log(log_entry)

        # Notify stream listeners
        await self._notify_stream_listeners(log_entry)

    async def query_logs(self, **query_params) -> List[LogEntry]:
        """Query logs with flexible parameters."""
        query = LogQuery(**query_params)
        return await self.storage.query_logs(query)

    async def get_correlation_logs(self, correlation_id: str) -> List[LogEntry]:
        """Get all logs for a specific correlation ID."""
        return await self.query_logs(
            correlation_id=correlation_id, order_by="timestamp"
        )

    async def get_error_logs(
        self,
        service_name: Optional[str] = None,
        start_time: Optional[float] = None,
        limit: int = 100,
    ) -> List[LogEntry]:
        """Get error and critical logs."""
        return await self.query_logs(
            service_name=service_name,
            level="ERROR",
            start_time=start_time,
            limit=limit,
            order_desc=True,
        )

    async def get_performance_logs(
        self,
        service_name: Optional[str] = None,
        operation: Optional[str] = None,
        start_time: Optional[float] = None,
    ) -> List[LogEntry]:
        """Get performance-related logs."""
        logs = await self.query_logs(
            service_name=service_name, operation=operation, start_time=start_time
        )

        # Filter for logs with performance data
        return [log for log in logs if log.performance_data]

    async def get_log_stats(self) -> Dict[str, Any]:
        """Get comprehensive logging statistics."""
        storage_stats = await self.storage.get_log_stats()

        # Add additional analysis
        error_logs = await self.get_error_logs(limit=1000)
        error_rate = len(error_logs) / max(1, storage_stats.get("total_logs", 1))

        # Service health based on error rates
        service_health = {}
        if "services" in storage_stats:
            for service, count in storage_stats["services"].items():
                service_errors = await self.get_error_logs(
                    service_name=service, limit=100
                )
                error_rate = len(service_errors) / max(1, count)
                if error_rate > 0.1:  # 10% error rate threshold
                    service_health[service] = "unhealthy"
                elif error_rate > 0.05:  # 5% error rate threshold
                    service_health[service] = "degraded"
                else:
                    service_health[service] = "healthy"

        return {
            **storage_stats,
            "error_rate": error_rate,
            "service_health": service_health,
            "retention_policy": {
                "max_age_days": self.retention_policy.max_age_days,
                "max_size_mb": self.retention_policy.max_size_mb,
                "compression_enabled": self.retention_policy.compression_enabled,
            },
        }

    def add_alert_callback(
        self, callback: Callable[[str, Dict[str, Any]], None]
    ) -> None:
        """Add callback for logging alerts."""
        self._alert_callbacks.append(callback)

    async def stream_logs(
        self, service_name: Optional[str] = None, level: Optional[str] = None
    ) -> AsyncIterator[LogEntry]:
        """Stream logs in real-time."""
        queue = asyncio.Queue()
        self._log_stream_listeners.append(queue)

        try:
            while True:
                try:
                    log_entry = await asyncio.wait_for(queue.get(), timeout=30.0)

                    # Apply filters
                    if service_name and log_entry.service_name != service_name:
                        continue
                    if level and log_entry.level != level:
                        continue

                    yield log_entry

                except asyncio.TimeoutError:
                    # Send heartbeat
                    yield None

        finally:
            self._log_stream_listeners.remove(queue)

    async def _notify_stream_listeners(self, log_entry: LogEntry) -> None:
        """Notify all stream listeners of new log entry."""
        for queue in self._log_stream_listeners:
            try:
                await queue.put(log_entry)
            except Exception:
                # Remove broken listeners
                try:
                    self._log_stream_listeners.remove(queue)
                except ValueError:
                    pass

    async def cleanup_old_logs(self) -> int:
        """Manually trigger log cleanup."""
        return await self.storage.cleanup_old_logs(self.retention_policy)

    def set_retention_policy(self, policy: LogRetentionPolicy) -> None:
        """Set log retention policy."""
        self.retention_policy = policy

    async def start_background_tasks(self) -> None:
        """Start background tasks."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

        if self._stream_task is None:
            self._stream_task = asyncio.create_task(self._stream_maintenance())

    async def stop_background_tasks(self) -> None:
        """Stop background tasks."""
        self._shutdown_event.set()

        if self._cleanup_task:
            try:
                await asyncio.wait_for(self._cleanup_task, timeout=5.0)
            except asyncio.TimeoutError:
                self._cleanup_task.cancel()

        if self._stream_task:
            try:
                await asyncio.wait_for(self._stream_task, timeout=5.0)
            except asyncio.TimeoutError:
                self._stream_task.cancel()

    async def _cleanup_loop(self) -> None:
        """Background cleanup loop."""
        while not self._shutdown_event.is_set():
            try:
                # Run cleanup daily
                await asyncio.sleep(24 * 60 * 60)
                removed_count = await self.cleanup_old_logs()
                if removed_count > 0:
                    logger.info(f"Cleaned up {removed_count} old log entries")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                await asyncio.sleep(60)  # Retry after 1 minute

    async def _stream_maintenance(self) -> None:
        """Maintain stream listeners."""
        while not self._shutdown_event.is_set():
            try:
                await asyncio.sleep(60)  # Check every minute

                # Clean up dead listeners (simple heartbeat check)
                # In production, you'd want more sophisticated health checks

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in stream maintenance: {e}")

    async def export_logs(self, query: LogQuery, format: str = "jsonl") -> str:
        """Export logs in specified format."""
        logs = await self.storage.query_logs(query)

        if format == "jsonl":
            return "\n".join(json.dumps(log.to_dict()) for log in logs)
        elif format == "json":
            return json.dumps([log.to_dict() for log in logs], indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format}")


# Global instance
_centralized_logging_service: Optional[CentralizedLoggingService] = None


def get_centralized_logging_service() -> CentralizedLoggingService:
    """Get the global centralized logging service instance."""
    global _centralized_logging_service
    if _centralized_logging_service is None:
        # Use SQLite for persistence in production
        storage_type = (
            LogStorageType.SQLITE
            if os.getenv("ENVIRONMENT") != "development"
            else LogStorageType.MEMORY
        )
        _centralized_logging_service = CentralizedLoggingService(storage_type)
    return _centralized_logging_service


# Convenience functions
async def store_log_entry(log_data: Dict[str, Any]) -> None:
    """Store a log entry in centralized logging."""
    service = get_centralized_logging_service()
    await service.store_log_entry(log_data)


async def query_logs(**kwargs) -> List[LogEntry]:
    """Query logs from centralized storage."""
    service = get_centralized_logging_service()
    return await service.query_logs(**kwargs)


async def get_correlation_logs(correlation_id: str) -> List[LogEntry]:
    """Get all logs for a correlation ID."""
    service = get_centralized_logging_service()
    return await service.get_correlation_logs(correlation_id)
