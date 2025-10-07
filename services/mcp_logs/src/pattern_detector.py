"""Pattern Detector - Identify patterns in log data."""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Any
from collections import Counter

from .log_processor import LogEntry, LogLevel


class PatternType(Enum):
    """Types of patterns that can be detected."""
    REPEATED_ERROR = "repeated_error"
    ERROR_SPIKE = "error_spike"
    CASCADING_FAILURE = "cascading_failure"
    SLOW_QUERY = "slow_query"
    UNUSUAL_ACTIVITY = "unusual_activity"


@dataclass
class Pattern:
    """Represents a detected pattern."""
    type: PatternType
    description: str
    occurrences: int
    severity: str = "medium"
    first_seen: datetime = field(default_factory=datetime.now)
    last_seen: datetime = field(default_factory=datetime.now)
    affected_services: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DetectionResult:
    """Result of pattern detection."""
    patterns_found: int
    patterns: List[Pattern]
    analyzed_entries: int
    time_range: tuple = None


class PatternDetector:
    """Detect patterns in log data."""
    
    def __init__(self):
        """Initialize pattern detector."""
        self.error_threshold = 3  # Min occurrences for repeated error
        self.spike_threshold = 5  # Min errors for spike
        self.cascade_window_seconds = 5  # Time window for cascading
    
    def detect_patterns(self, logs: List[LogEntry]) -> DetectionResult:
        """
        Detect patterns in logs.
        
        Args:
            logs: List of log entries to analyze
            
        Returns:
            DetectionResult with all detected patterns
        """
        patterns = []
        
        # Detect repeated errors
        patterns.extend(self._detect_repeated_errors(logs))
        
        # Detect error spikes
        patterns.extend(self._detect_error_spikes(logs))
        
        # Detect cascading failures
        patterns.extend(self._detect_cascading_failures(logs))
        
        # Detect slow queries
        patterns.extend(self._detect_slow_queries(logs))
        
        time_range = None
        if logs:
            time_range = (logs[0].timestamp, logs[-1].timestamp)
        
        return DetectionResult(
            patterns_found=len(patterns),
            patterns=patterns,
            analyzed_entries=len(logs),
            time_range=time_range
        )
    
    def _detect_repeated_errors(self, logs: List[LogEntry]) -> List[Pattern]:
        """Detect repeated error messages."""
        patterns = []
        
        # Count error messages
        error_messages = [
            log.message for log in logs
            if log.level == LogLevel.ERROR
        ]
        
        if not error_messages:
            return patterns
        
        message_counts = Counter(error_messages)
        
        for message, count in message_counts.items():
            if count >= self.error_threshold:
                # Find affected services
                affected = list(set(
                    log.service for log in logs
                    if log.message == message and log.level == LogLevel.ERROR
                ))
                
                # Find time range
                matching_logs = [
                    log for log in logs
                    if log.message == message and log.level == LogLevel.ERROR
                ]
                
                patterns.append(Pattern(
                    type=PatternType.REPEATED_ERROR,
                    description=f"Repeated error: {message[:50]}...",
                    occurrences=count,
                    severity="high" if count > 10 else "medium",
                    first_seen=matching_logs[0].timestamp,
                    last_seen=matching_logs[-1].timestamp,
                    affected_services=affected
                ))
        
        return patterns
    
    def _detect_error_spikes(self, logs: List[LogEntry]) -> List[Pattern]:
        """Detect sudden increases in error rate."""
        patterns = []
        
        if not logs:
            return patterns
        
        # Group by time windows (1 minute)
        errors_by_minute = {}
        for log in logs:
            if log.level == LogLevel.ERROR:
                minute_key = log.timestamp.replace(second=0, microsecond=0)
                errors_by_minute[minute_key] = errors_by_minute.get(minute_key, 0) + 1
        
        # Check for spikes
        for minute, count in errors_by_minute.items():
            if count >= self.spike_threshold:
                # Find affected services
                affected = list(set(
                    log.service for log in logs
                    if log.level == LogLevel.ERROR
                    and log.timestamp.replace(second=0, microsecond=0) == minute
                ))
                
                patterns.append(Pattern(
                    type=PatternType.ERROR_SPIKE,
                    description=f"Error spike detected: {count} errors in 1 minute",
                    occurrences=count,
                    severity="high",
                    first_seen=minute,
                    last_seen=minute + timedelta(minutes=1),
                    affected_services=affected
                ))
        
        return patterns
    
    def _detect_cascading_failures(self, logs: List[LogEntry]) -> List[Pattern]:
        """Detect cascading failures across services."""
        patterns = []
        
        error_logs = [log for log in logs if log.level == LogLevel.ERROR]
        
        if len(error_logs) < 2:
            return patterns
        
        # Check for errors in multiple services within short time window
        for i, log in enumerate(error_logs[:-1]):
            next_log = error_logs[i + 1]
            time_diff = (next_log.timestamp - log.timestamp).total_seconds()
            
            if time_diff <= self.cascade_window_seconds and log.service != next_log.service:
                # Found potential cascade
                cascade_logs = [log, next_log]
                
                # Look for more in the cascade
                for j in range(i + 2, len(error_logs)):
                    if (error_logs[j].timestamp - log.timestamp).total_seconds() <= self.cascade_window_seconds:
                        cascade_logs.append(error_logs[j])
                    else:
                        break
                
                if len(set(l.service for l in cascade_logs)) >= 2:
                    affected = list(set(l.service for l in cascade_logs))
                    
                    patterns.append(Pattern(
                        type=PatternType.CASCADING_FAILURE,
                        description=f"Cascading failure across {len(affected)} services",
                        occurrences=len(cascade_logs),
                        severity="critical",
                        first_seen=cascade_logs[0].timestamp,
                        last_seen=cascade_logs[-1].timestamp,
                        affected_services=affected
                    ))
                    break  # Only report first cascade
        
        return patterns
    
    def _detect_slow_queries(self, logs: List[LogEntry]) -> List[Pattern]:
        """Detect slow query patterns."""
        patterns = []
        
        slow_query_logs = [
            log for log in logs
            if "slow query" in log.message.lower()
            or (log.metadata and log.metadata.get("duration_ms", 0) > 1000)
        ]
        
        if len(slow_query_logs) >= 3:
            affected = list(set(log.service for log in slow_query_logs))
            
            patterns.append(Pattern(
                type=PatternType.SLOW_QUERY,
                description=f"Slow query pattern detected: {len(slow_query_logs)} occurrences",
                occurrences=len(slow_query_logs),
                severity="medium",
                first_seen=slow_query_logs[0].timestamp,
                last_seen=slow_query_logs[-1].timestamp,
                affected_services=affected
            ))
        
        return patterns
