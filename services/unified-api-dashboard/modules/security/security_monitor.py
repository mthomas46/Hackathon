"""
Security Monitoring and Threat Detection

Advanced security monitoring system:
- Real-time threat detection and alerting
- Anomaly detection using behavioral analysis
- Security incident response and escalation
- Intrusion detection and prevention
- Security metrics and reporting
"""

import ipaddress
import statistics
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set


class ThreatLevel(Enum):
    """Threat severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ThreatType(Enum):
    """Types of security threats."""

    BRUTE_FORCE = "brute_force"
    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    CSRF = "csrf"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    SUSPICIOUS_TRAFFIC = "suspicious_traffic"
    ANOMALOUS_BEHAVIOR = "anomalous_behavior"
    MALWARE_SIGNATURE = "malware_signature"
    DATA_EXFILTRATION = "data_exfiltration"
    INSIDER_THREAT = "insider_threat"


@dataclass
class SecurityEvent:
    """Security event record."""

    event_id: str
    threat_type: ThreatType
    threat_level: ThreatLevel
    source_ip: str
    user_id: Optional[str]
    username: Optional[str]
    description: str
    details: Dict[str, Any]
    timestamp: datetime
    confidence_score: float  # 0.0 to 1.0
    mitigated: bool = False
    mitigation_action: Optional[str] = None
    false_positive: bool = False


@dataclass
class ThreatPattern:
    """Threat detection pattern."""

    pattern_id: str
    name: str
    threat_type: ThreatType
    description: str
    conditions: Dict[str, Any]
    severity: ThreatLevel
    enabled: bool = True
    false_positive_rate: float = 0.0
    detection_logic: Callable = None


@dataclass
class SecurityMetrics:
    """Security monitoring metrics."""

    total_events: int = 0
    events_by_threat_type: Dict[str, int] = field(default_factory=dict)
    events_by_severity: Dict[str, int] = field(default_factory=dict)
    false_positives: int = 0
    mitigated_threats: int = 0
    response_time_avg: float = 0.0
    uptime_percentage: float = 100.0


@dataclass
class BehavioralProfile:
    """User behavioral profile for anomaly detection."""

    user_id: str
    normal_patterns: Dict[str, Any] = field(default_factory=dict)
    login_times: List[datetime] = field(default_factory=list)
    ip_addresses: Set[str] = field(default_factory=set)
    request_patterns: Dict[str, float] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.now)


class SecurityMonitor:
    """
    Real-time security monitoring and alerting system.

    Monitors system activity for threats and generates alerts.
    """

    def __init__(self):
        self.events: List[SecurityEvent] = []
        self.threat_patterns: Dict[str, ThreatPattern] = {}
        self.behavioral_profiles: Dict[str, BehavioralProfile] = {}
        self.metrics = SecurityMetrics()
        self.alert_callbacks: List[Callable] = []
        self._load_threat_patterns()

    def _load_threat_patterns(self):
        """Load predefined threat detection patterns."""
        self.threat_patterns = {
            "brute_force_login": ThreatPattern(
                pattern_id="brute_force_login",
                name="Brute Force Login Attempts",
                threat_type=ThreatType.BRUTE_FORCE,
                description="Multiple failed login attempts from same IP",
                severity=ThreatLevel.HIGH,
                conditions={
                    "failed_logins_threshold": 5,
                    "time_window_minutes": 15,
                    "same_ip_only": True,
                },
            ),
            "unusual_login_time": ThreatPattern(
                pattern_id="unusual_login_time",
                name="Unusual Login Time",
                threat_type=ThreatType.ANOMALOUS_BEHAVIOR,
                description="Login at unusual time for user",
                severity=ThreatLevel.MEDIUM,
                conditions={
                    "deviation_threshold": 2.0,
                    "minimum_samples": 10,
                },  # Standard deviations
            ),
            "suspicious_ip": ThreatPattern(
                pattern_id="suspicious_ip",
                name="Suspicious IP Address",
                threat_type=ThreatType.UNAUTHORIZED_ACCESS,
                description="Access from known suspicious IP",
                severity=ThreatLevel.HIGH,
                conditions={"blacklist_check": True, "geographic_anomaly": True},
            ),
            "rapid_api_calls": ThreatPattern(
                pattern_id="rapid_api_calls",
                name="Rapid API Calls",
                threat_type=ThreatType.SUSPICIOUS_TRAFFIC,
                description="Unusually high number of API calls",
                severity=ThreatLevel.MEDIUM,
                conditions={
                    "calls_per_minute_threshold": 100,
                    "burst_window_seconds": 60,
                },
            ),
            "privilege_escalation": ThreatPattern(
                pattern_id="privilege_escalation",
                name="Privilege Escalation Attempt",
                threat_type=ThreatType.UNAUTHORIZED_ACCESS,
                description="Attempt to access higher privilege resources",
                severity=ThreatLevel.CRITICAL,
                conditions={"permission_denied_count": 3, "time_window_minutes": 10},
            ),
            "data_exfiltration": ThreatPattern(
                pattern_id="data_exfiltration",
                name="Potential Data Exfiltration",
                threat_type=ThreatType.DATA_EXFILTRATION,
                description="Large data downloads or unusual export patterns",
                severity=ThreatLevel.HIGH,
                conditions={
                    "data_volume_threshold_mb": 100,
                    "unusual_export_pattern": True,
                },
            ),
        }

    async def monitor_event(
        self,
        event_type: str,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        ip_address: str = None,
        details: Dict[str, Any] = None,
    ) -> List[SecurityEvent]:
        """Monitor an event and detect potential threats."""
        detected_threats = []

        for pattern in self.threat_patterns.values():
            if not pattern.enabled:
                continue

            threat = await self._check_pattern(
                pattern, event_type, user_id, username, ip_address, details
            )
            if threat:
                detected_threats.append(threat)
                self.events.append(threat)

                # Update metrics
                self.metrics.total_events += 1
                threat_type_key = pattern.threat_type.value
                self.metrics.events_by_threat_type[threat_type_key] = (
                    self.metrics.events_by_threat_type.get(threat_type_key, 0) + 1
                )

                severity_key = pattern.severity.value
                self.metrics.events_by_severity[severity_key] = (
                    self.metrics.events_by_severity.get(severity_key, 0) + 1
                )

                # Trigger alerts for high/critical threats
                if pattern.severity in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
                    await self._trigger_alert(threat)

        # Update behavioral profiles
        if user_id:
            await self._update_behavioral_profile(
                user_id, event_type, ip_address, details
            )

        return detected_threats

    async def _check_pattern(
        self,
        pattern: ThreatPattern,
        event_type: str,
        user_id: str,
        username: str,
        ip_address: str,
        details: Dict[str, Any],
    ) -> Optional[SecurityEvent]:
        """Check if an event matches a threat pattern."""
        conditions = pattern.conditions

        # Brute force detection
        if pattern.pattern_id == "brute_force_login" and event_type == "auth.failed":
            return await self._check_brute_force(pattern, ip_address, conditions)

        # Unusual login time
        elif pattern.pattern_id == "unusual_login_time" and event_type == "auth.login":
            return await self._check_unusual_login_time(pattern, user_id, conditions)

        # Suspicious IP
        elif pattern.pattern_id == "suspicious_ip":
            return await self._check_suspicious_ip(pattern, ip_address, conditions)

        # Rapid API calls
        elif pattern.pattern_id == "rapid_api_calls" and event_type.startswith("api."):
            return await self._check_rapid_api_calls(pattern, user_id, conditions)

        # Privilege escalation
        elif (
            pattern.pattern_id == "privilege_escalation" and event_type == "auth.denied"
        ):
            return await self._check_privilege_escalation(pattern, user_id, conditions)

        return None

    async def _check_brute_force(
        self, pattern: ThreatPattern, ip_address: str, conditions: Dict[str, Any]
    ) -> Optional[SecurityEvent]:
        """Check for brute force login attempts."""
        threshold = conditions["failed_logins_threshold"]
        time_window = conditions["time_window_minutes"]

        # Count failed logins from this IP in the time window
        cutoff_time = datetime.now() - timedelta(minutes=time_window)
        recent_failures = [
            e
            for e in self.events
            if e.threat_type == ThreatType.BRUTE_FORCE
            and e.source_ip == ip_address
            and e.timestamp > cutoff_time
        ]

        if len(recent_failures) >= threshold:
            return SecurityEvent(
                event_id=f"threat_{len(self.events) + 1}",
                threat_type=pattern.threat_type,
                threat_level=pattern.severity,
                source_ip=ip_address,
                user_id=None,
                username=None,
                description=f"Brute force attack detected from {ip_address}",
                details={
                    "failed_attempts": len(recent_failures) + 1,
                    "time_window_minutes": time_window,
                    "threshold": threshold,
                },
                timestamp=datetime.now(),
                confidence_score=0.9,
            )

        return None

    async def _check_unusual_login_time(
        self, pattern: ThreatPattern, user_id: str, conditions: Dict[str, Any]
    ) -> Optional[SecurityEvent]:
        """Check for unusual login times."""
        profile = self.behavioral_profiles.get(user_id)
        if not profile or len(profile.login_times) < conditions["minimum_samples"]:
            return None

        # Calculate normal login hour distribution
        login_hours = [dt.hour for dt in profile.login_times]
        if not login_hours:
            return None

        mean_hour = statistics.mean(login_hours)
        std_hour = statistics.stdev(login_hours) if len(login_hours) > 1 else 1

        current_hour = datetime.now().hour
        deviation = abs(current_hour - mean_hour) / std_hour if std_hour > 0 else 0

        if deviation > conditions["deviation_threshold"]:
            return SecurityEvent(
                event_id=f"threat_{len(self.events) + 1}",
                threat_type=pattern.threat_type,
                threat_level=pattern.severity,
                source_ip="",  # Would be filled from context
                user_id=user_id,
                username=None,
                description=f"Unusual login time for user {user_id}",
                details={
                    "current_hour": current_hour,
                    "normal_hour": mean_hour,
                    "deviation": deviation,
                    "threshold": conditions["deviation_threshold"],
                },
                timestamp=datetime.now(),
                confidence_score=min(0.8, deviation / 5.0),
            )

        return None

    async def _check_suspicious_ip(
        self, pattern: ThreatPattern, ip_address: str, conditions: Dict[str, Any]
    ) -> Optional[SecurityEvent]:
        """Check for suspicious IP addresses."""
        # Simplified IP blacklist check (would use real threat intelligence in production)
        suspicious_ranges = [
            "10.0.0.0/8",  # RFC 1918
            "172.16.0.0/12",  # RFC 1918
            "192.168.0.0/16",  # RFC 1918
        ]

        try:
            client_ip = ipaddress.ip_address(ip_address)
            for suspicious_range in suspicious_ranges:
                if client_ip in ipaddress.ip_network(suspicious_range):
                    return SecurityEvent(
                        event_id=f"threat_{len(self.events) + 1}",
                        threat_type=pattern.threat_type,
                        threat_level=pattern.severity,
                        source_ip=ip_address,
                        user_id=None,
                        username=None,
                        description=f"Access from suspicious IP range: {ip_address}",
                        details={
                            "ip_address": ip_address,
                            "suspicious_range": suspicious_range,
                            "check_type": "rfc1918_private",
                        },
                        timestamp=datetime.now(),
                        confidence_score=0.7,
                    )
        except ValueError:
            pass

        return None

    async def _check_rapid_api_calls(
        self, pattern: ThreatPattern, user_id: str, conditions: Dict[str, Any]
    ) -> Optional[SecurityEvent]:
        """Check for rapid API call patterns."""
        threshold = conditions["calls_per_minute_threshold"]
        window_seconds = conditions["burst_window_seconds"]

        # Count API calls in time window
        cutoff_time = datetime.now() - timedelta(seconds=window_seconds)
        recent_calls = [
            e
            for e in self.events
            if e.user_id == user_id
            and e.timestamp > cutoff_time
            and str(e.threat_type).startswith("api.")
        ]

        if len(recent_calls) >= threshold:
            return SecurityEvent(
                event_id=f"threat_{len(self.events) + 1}",
                threat_type=pattern.threat_type,
                threat_level=pattern.severity,
                source_ip="",  # Would be filled from context
                user_id=user_id,
                username=None,
                description=f"Rapid API calls detected for user {user_id}",
                details={
                    "call_count": len(recent_calls),
                    "threshold": threshold,
                    "time_window_seconds": window_seconds,
                },
                timestamp=datetime.now(),
                confidence_score=0.8,
            )

        return None

    async def _check_privilege_escalation(
        self, pattern: ThreatPattern, user_id: str, conditions: Dict[str, Any]
    ) -> Optional[SecurityEvent]:
        """Check for privilege escalation attempts."""
        threshold = conditions["permission_denied_count"]
        time_window = conditions["time_window_minutes"]

        # Count recent permission denials
        cutoff_time = datetime.now() - timedelta(minutes=time_window)
        recent_denials = [
            e
            for e in self.events
            if e.user_id == user_id
            and e.threat_type == ThreatType.UNAUTHORIZED_ACCESS
            and e.timestamp > cutoff_time
        ]

        if len(recent_denials) >= threshold:
            return SecurityEvent(
                event_id=f"threat_{len(self.events) + 1}",
                threat_type=pattern.threat_type,
                threat_level=pattern.severity,
                source_ip="",  # Would be filled from context
                user_id=user_id,
                username=None,
                description=f"Privilege escalation attempt detected for user {user_id}",
                details={
                    "denial_count": len(recent_denials),
                    "threshold": threshold,
                    "time_window_minutes": time_window,
                },
                timestamp=datetime.now(),
                confidence_score=0.9,
            )

        return None

    async def _update_behavioral_profile(
        self, user_id: str, event_type: str, ip_address: str, details: Dict[str, Any]
    ):
        """Update user behavioral profile."""
        if user_id not in self.behavioral_profiles:
            self.behavioral_profiles[user_id] = BehavioralProfile(user_id=user_id)

        profile = self.behavioral_profiles[user_id]

        if event_type == "auth.login":
            profile.login_times.append(datetime.now())

        if ip_address:
            profile.ip_addresses.add(ip_address)

        # Keep only recent login times (last 30 days)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        profile.login_times = [dt for dt in profile.login_times if dt > thirty_days_ago]

        profile.last_updated = datetime.now()

    async def _trigger_alert(self, threat: SecurityEvent):
        """Trigger security alerts for high-priority threats."""
        alert_message = {
            "alert_type": "security_threat",
            "threat_level": threat.threat_level.value,
            "threat_type": threat.threat_type.value,
            "description": threat.description,
            "user_id": threat.user_id,
            "source_ip": threat.source_ip,
            "timestamp": threat.timestamp.isoformat(),
            "confidence_score": threat.confidence_score,
        }

        # Call all registered alert callbacks
        for callback in self.alert_callbacks:
            try:
                await callback(alert_message)
            except Exception as e:
                print(f"Alert callback failed: {e}")

    def register_alert_callback(self, callback: Callable):
        """Register a callback for security alerts."""
        self.alert_callbacks.append(callback)

    async def mitigate_threat(self, threat_id: str, action: str) -> bool:
        """Apply mitigation action for a detected threat."""
        for event in self.events:
            if event.event_id == threat_id:
                event.mitigated = True
                event.mitigation_action = action
                self.metrics.mitigated_threats += 1
                return True
        return False

    async def get_security_metrics(self) -> SecurityMetrics:
        """Get current security metrics."""
        return self.metrics

    async def get_threats(
        self,
        threat_type: Optional[ThreatType] = None,
        severity: Optional[ThreatLevel] = None,
        mitigated: Optional[bool] = None,
        limit: int = 100,
    ) -> List[SecurityEvent]:
        """Query security events with filtering."""
        filtered_events = self.events

        if threat_type:
            filtered_events = [
                e for e in filtered_events if e.threat_type == threat_type
            ]

        if severity:
            filtered_events = [e for e in filtered_events if e.threat_level == severity]

        if mitigated is not None:
            filtered_events = [e for e in filtered_events if e.mitigated == mitigated]

        # Sort by timestamp descending
        filtered_events.sort(key=lambda e: e.timestamp, reverse=True)

        return filtered_events[:limit]


class ThreatDetector:
    """
    Advanced threat detection using machine learning and behavioral analysis.

    Uses statistical analysis and pattern recognition for anomaly detection.
    """

    def __init__(self, security_monitor: SecurityMonitor):
        self.security_monitor = security_monitor
        self.baseline_metrics: Dict[str, Dict[str, float]] = {}
        self.anomaly_thresholds: Dict[str, float] = {
            "login_frequency": 2.5,  # Standard deviations
            "api_call_volume": 3.0,
            "error_rate": 2.0,
            "session_duration": 2.5,
        }

    async def analyze_baseline(self, time_window_hours: int = 24):
        """Analyze baseline behavior patterns."""
        cutoff_time = datetime.now() - timedelta(hours=time_window_hours)

        # Analyze login patterns
        login_events = [
            e
            for e in self.security_monitor.events
            if e.timestamp > cutoff_time
            and e.threat_type == ThreatType.ANOMALOUS_BEHAVIOR
        ]

        if login_events:
            login_hours = [e.timestamp.hour for e in login_events]
            self.baseline_metrics["login_patterns"] = {
                "mean_hour": statistics.mean(login_hours),
                "std_hour": (
                    statistics.stdev(login_hours) if len(login_hours) > 1 else 1
                ),
                "sample_count": len(login_hours),
            }

        # This would be expanded with more sophisticated ML models in production

    async def detect_anomalies(
        self, current_metrics: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Detect anomalous behavior using statistical analysis."""
        anomalies = []

        # Check login time anomalies
        if "login_hour" in current_metrics:
            baseline = self.baseline_metrics.get("login_patterns", {})
            if baseline:
                login_hour = current_metrics["login_hour"]
                mean_hour = baseline["mean_hour"]
                std_hour = baseline["std_hour"]

                if std_hour > 0:
                    deviation = abs(login_hour - mean_hour) / std_hour
                    if deviation > self.anomaly_thresholds["login_frequency"]:
                        anomalies.append(
                            {
                                "anomaly_type": "unusual_login_time",
                                "severity": "medium",
                                "confidence": min(0.9, deviation / 5.0),
                                "details": {
                                    "current_hour": login_hour,
                                    "baseline_hour": mean_hour,
                                    "deviation": deviation,
                                },
                            }
                        )

        # Check API call volume anomalies
        if "api_calls_per_minute" in current_metrics:
            # Simplified volume check (would use time series analysis in production)
            call_rate = current_metrics["api_calls_per_minute"]
            if call_rate > 100:  # Arbitrary threshold
                anomalies.append(
                    {
                        "anomaly_type": "high_api_call_volume",
                        "severity": "low",
                        "confidence": 0.7,
                        "details": {"call_rate": call_rate, "threshold": 100},
                    }
                )

        return anomalies

    async def update_baseline(self, new_data: Dict[str, Any]):
        """Update baseline metrics with new data."""
        # Incremental update of statistical baselines
        # In production, this would use exponential moving averages or more sophisticated methods
