"""Root Cause Analyzer - Automated incident investigation."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional

from .log_processor import LogEntry, LogLevel


@dataclass
class RootCause:
    """Represents a root cause."""
    description: str
    confidence: float
    category: str
    evidence: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IncidentTimeline:
    """Timeline of incident events."""
    start_time: datetime
    end_time: datetime
    events: List[Dict[str, Any]]
    duration_seconds: float = 0.0


@dataclass
class CorrelationScore:
    """Correlation between events."""
    event1_id: str
    event2_id: str
    score: float
    reason: str


@dataclass
class IncidentAnalysis:
    """Complete incident analysis."""
    incident_id: str
    root_cause: Optional[RootCause]
    contributing_factors: List[str]
    timeline: Optional[IncidentTimeline] = None
    correlations: List[CorrelationScore] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class RootCauseAnalyzer:
    """Analyze incidents to determine root causes."""
    
    def __init__(self):
        """Initialize root cause analyzer."""
        self.correlation_threshold = 0.7
    
    async def analyze_incident(
        self,
        incident_id: str,
        logs: List[LogEntry]
    ) -> IncidentAnalysis:
        """
        Analyze an incident to find root cause.
        
        Args:
            incident_id: Incident identifier
            logs: Related log entries
        
        Returns:
            IncidentAnalysis with findings
        """
        # Build timeline
        timeline = await self.build_timeline(logs)
        
        # Identify correlations
        correlations = await self.identify_correlations(logs)
        
        # Determine root cause
        root_cause = await self._determine_root_cause(logs, correlations)
        
        # Get contributing factors
        contributing = self._get_contributing_factors(logs)
        
        # Generate recommendations
        recommendations = await self.suggest_remediation(root_cause) if root_cause else []
        
        return IncidentAnalysis(
            incident_id=incident_id,
            root_cause=root_cause,
            contributing_factors=contributing,
            timeline=timeline,
            correlations=correlations,
            recommendations=recommendations
        )
    
    async def build_timeline(self, logs: List[LogEntry]) -> IncidentTimeline:
        """Build timeline of events."""
        if not logs:
            now = datetime.now()
            return IncidentTimeline(
                start_time=now,
                end_time=now,
                events=[]
            )
        
        events = []
        for log in logs:
            events.append({
                "timestamp": log.timestamp,
                "level": log.level.value,
                "service": log.service,
                "message": log.message[:100]
            })
        
        duration = (logs[-1].timestamp - logs[0].timestamp).total_seconds()
        
        return IncidentTimeline(
            start_time=logs[0].timestamp,
            end_time=logs[-1].timestamp,
            events=events,
            duration_seconds=duration
        )
    
    async def identify_correlations(
        self,
        logs: List[LogEntry]
    ) -> List[CorrelationScore]:
        """Identify correlations between events."""
        correlations = []
        
        error_logs = [log for log in logs if log.level == LogLevel.ERROR]
        
        for i in range(len(error_logs) - 1):
            log1 = error_logs[i]
            log2 = error_logs[i + 1]
            
            # Calculate time proximity score
            time_diff = (log2.timestamp - log1.timestamp).total_seconds()
            time_score = max(0, 1.0 - (time_diff / 60.0))  # Within 1 minute
            
            # Service correlation
            service_score = 0.5 if log1.service != log2.service else 0.2
            
            # Message similarity (simple check)
            message_score = 0.3 if any(
                word in log2.message.lower()
                for word in log1.message.lower().split()[:3]
            ) else 0.0
            
            total_score = time_score * 0.5 + service_score * 0.3 + message_score * 0.2
            
            if total_score > self.correlation_threshold:
                correlations.append(CorrelationScore(
                    event1_id=f"{log1.service}_{log1.timestamp.timestamp()}",
                    event2_id=f"{log2.service}_{log2.timestamp.timestamp()}",
                    score=total_score,
                    reason="Temporal and contextual correlation"
                ))
        
        return correlations
    
    async def _determine_root_cause(
        self,
        logs: List[LogEntry],
        correlations: List[CorrelationScore]
    ) -> Optional[RootCause]:
        """Determine root cause from analysis."""
        error_logs = [log for log in logs if log.level == LogLevel.ERROR]
        
        if not error_logs:
            return None
        
        # Find most common error type
        from collections import Counter
        error_keywords = Counter()
        
        for log in error_logs:
            words = log.message.lower().split()
            for word in ['database', 'connection', 'timeout', 'memory', 'network']:
                if word in words:
                    error_keywords[word] += 1
        
        if error_keywords:
            most_common = error_keywords.most_common(1)[0]
            keyword, count = most_common
            
            confidence = min(count / len(error_logs), 1.0)
            
            category_map = {
                'database': 'database',
                'connection': 'network',
                'timeout': 'performance',
                'memory': 'resource',
                'network': 'network'
            }
            
            return RootCause(
                description=f"{keyword.capitalize()} issue detected",
                confidence=confidence,
                category=category_map.get(keyword, 'unknown'),
                evidence=[log.message[:100] for log in error_logs[:3]]
            )
        
        # Generic root cause
        return RootCause(
            description="Multiple error types detected",
            confidence=0.5,
            category="unknown",
            evidence=[log.message[:100] for log in error_logs[:3]]
        )
    
    def _get_contributing_factors(self, logs: List[LogEntry]) -> List[str]:
        """Identify contributing factors."""
        factors = []
        
        # Check for warnings before errors
        warnings = [log for log in logs if log.level == LogLevel.WARNING]
        if warnings:
            factors.append(f"{len(warnings)} warnings preceded errors")
        
        # Check for multiple services
        services = set(log.service for log in logs if log.level == LogLevel.ERROR)
        if len(services) > 1:
            factors.append(f"Multiple services affected: {', '.join(services)}")
        
        # Check time span
        if logs:
            duration = (logs[-1].timestamp - logs[0].timestamp).total_seconds()
            if duration < 60:
                factors.append("Rapid failure (< 1 minute)")
        
        return factors
    
    async def suggest_remediation(self, root_cause: RootCause) -> List[str]:
        """Suggest remediation actions."""
        recommendations = []
        
        category = root_cause.category.lower()
        
        if 'database' in category:
            recommendations.append("Check database connection pool")
            recommendations.append("Verify database server health")
            recommendations.append("Review slow query logs")
        elif 'network' in category:
            recommendations.append("Check network connectivity")
            recommendations.append("Verify DNS resolution")
            recommendations.append("Review firewall rules")
        elif 'performance' in category:
            recommendations.append("Check resource utilization")
            recommendations.append("Review application performance metrics")
            recommendations.append("Consider scaling resources")
        elif 'resource' in category:
            recommendations.append("Check memory usage")
            recommendations.append("Review resource limits")
            recommendations.append("Investigate memory leaks")
        else:
            recommendations.append("Review error logs")
            recommendations.append("Check service health")
        
        return recommendations
