"""
Log Processor - Parse and process logs from multiple sources.
"""

import re
import json
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional


class LogLevel(Enum):
    """Log severity levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogSource(Enum):
    """Log source types."""
    APPLICATION = "application"
    DATABASE = "database"
    INFRASTRUCTURE = "infrastructure"
    SECURITY = "security"
    AUDIT = "audit"


@dataclass
class LogEntry:
    """Represents a parsed log entry."""
    timestamp: datetime
    level: LogLevel
    message: str
    source: LogSource
    service: str = "unknown"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ParseResult:
    """Result of log parsing."""
    success: bool
    entry: Optional[LogEntry] = None
    error: Optional[str] = None


class LogProcessor:
    """
    Process and analyze logs from multiple sources.
    
    Supports:
    - Multiple log formats (plain, JSON, syslog)
    - Filtering and aggregation
    - Time-based queries
    """
    
    def __init__(self):
        """Initialize log processor."""
        self.log_patterns = {
            'plain': re.compile(
                r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s+'
                r'(DEBUG|INFO|WARNING|ERROR|CRITICAL)\s+'
                r'\[([^\]]+)\]\s+(.+)'
            ),
            'syslog': re.compile(
                r'<(\d+)>(\w+\s+\d+\s+\d{2}:\d{2}:\d{2})\s+'
                r'(\S+)\s+(\S+):\s+(.+)'
            )
        }
    
    def parse_log(self, raw_log: str, format: str = "plain") -> ParseResult:
        """
        Parse a raw log entry.
        
        Args:
            raw_log: Raw log string
            format: Log format (plain, json, syslog)
        
        Returns:
            ParseResult with parsed entry or error
        """
        try:
            if format == "json":
                return self._parse_json_log(raw_log)
            elif format == "syslog":
                return self._parse_syslog(raw_log)
            else:
                return self._parse_plain_log(raw_log)
        
        except Exception as e:
            return ParseResult(
                success=False,
                error=f"Parse error: {str(e)}"
            )
    
    def _parse_plain_log(self, raw_log: str) -> ParseResult:
        """Parse plain text log format."""
        # Handle simple ERROR: format
        if raw_log.startswith("ERROR:"):
            return ParseResult(
                success=True,
                entry=LogEntry(
                    timestamp=datetime.now(),
                    level=LogLevel.ERROR,
                    message=raw_log.replace("ERROR:", "").strip(),
                    source=LogSource.APPLICATION,
                    service="unknown"
                )
            )
        
        # Try structured format
        match = self.log_patterns['plain'].match(raw_log)
        if match:
            timestamp_str, level_str, service, message = match.groups()
            
            return ParseResult(
                success=True,
                entry=LogEntry(
                    timestamp=datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S"),
                    level=LogLevel[level_str],
                    message=message,
                    source=LogSource.APPLICATION,
                    service=service
                )
            )
        
        # Fallback: treat as INFO
        return ParseResult(
            success=True,
            entry=LogEntry(
                timestamp=datetime.now(),
                level=LogLevel.INFO,
                message=raw_log,
                source=LogSource.APPLICATION,
                service="unknown"
            )
        )
    
    def _parse_json_log(self, raw_log: str) -> ParseResult:
        """Parse JSON formatted log."""
        data = json.loads(raw_log)
        
        timestamp = data.get('timestamp', datetime.now().isoformat())
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except:
                timestamp = datetime.now()
        
        return ParseResult(
            success=True,
            entry=LogEntry(
                timestamp=timestamp,
                level=LogLevel[data.get('level', 'INFO')],
                message=data.get('message', ''),
                source=LogSource.APPLICATION,
                service=data.get('service', 'unknown'),
                metadata=data.get('metadata', {})
            )
        )
    
    def _parse_syslog(self, raw_log: str) -> ParseResult:
        """Parse syslog format."""
        match = self.log_patterns['syslog'].match(raw_log)
        if match:
            priority, timestamp_str, host, app, message = match.groups()
            
            # Parse priority to level
            severity = int(priority) % 8
            level_map = {
                0: LogLevel.CRITICAL,
                1: LogLevel.CRITICAL,
                2: LogLevel.CRITICAL,
                3: LogLevel.ERROR,
                4: LogLevel.WARNING,
                5: LogLevel.INFO,
                6: LogLevel.INFO,
                7: LogLevel.DEBUG
            }
            
            return ParseResult(
                success=True,
                entry=LogEntry(
                    timestamp=datetime.now(),  # Simplified
                    level=level_map.get(severity, LogLevel.INFO),
                    message=message,
                    source=LogSource.APPLICATION,
                    service=app
                )
            )
        
        return ParseResult(success=False, error="Invalid syslog format")
    
    def filter_by_level(
        self,
        logs: List[LogEntry],
        level: LogLevel
    ) -> List[LogEntry]:
        """Filter logs by level."""
        return [log for log in logs if log.level == level]
    
    def filter_by_service(
        self,
        logs: List[LogEntry],
        service: str
    ) -> List[LogEntry]:
        """Filter logs by service."""
        return [log for log in logs if log.service == service]
    
    def filter_by_time_range(
        self,
        logs: List[LogEntry],
        start: datetime,
        end: datetime
    ) -> List[LogEntry]:
        """Filter logs by time range."""
        return [
            log for log in logs
            if start <= log.timestamp <= end
        ]
    
    def aggregate_by_service(
        self,
        logs: List[LogEntry]
    ) -> Dict[str, int]:
        """Aggregate log counts by service."""
        counts = {}
        for log in logs:
            counts[log.service] = counts.get(log.service, 0) + 1
        return counts
    
    def filter_logs(
        self,
        logs: List[LogEntry],
        level: Optional[LogLevel] = None,
        service: Optional[str] = None
    ) -> List[LogEntry]:
        """
        Filter logs by level and/or service.
        
        Args:
            logs: List of log entries
            level: Log level filter
            service: Service name filter
        
        Returns:
            Filtered list of log entries
        """
        filtered = logs
        
        if level:
            filtered = [log for log in filtered if log.level == level]
        
        if service:
            filtered = [log for log in filtered if log.service == service]
        
        return filtered
    
    def aggregate_logs(
        self,
        logs: List[LogEntry],
        by: str = "service"
    ) -> Dict[str, int]:
        """
        Aggregate logs by specified field.
        
        Args:
            logs: List of log entries
            by: Field to aggregate by ("service" or "level")
        
        Returns:
            Dictionary with counts per key
        """
        from collections import Counter
        
        if by == "service":
            return dict(Counter(log.service for log in logs))
        elif by == "level":
            return dict(Counter(log.level.value for log in logs))
        else:
            raise ValueError(f"Unsupported aggregation field: {by}")