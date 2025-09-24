"""
Audit Trails and Compliance Monitoring

Comprehensive audit logging and compliance monitoring system:
- Detailed audit logs for all API operations
- Compliance monitoring for GDPR, HIPAA, SOX
- Data retention policies and automatic cleanup
- Audit trail integrity verification
- Compliance reporting and alerts
"""

import hashlib
import hmac
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from ...config import config


class AuditEventType(Enum):
    """Types of audit events."""

    AUTH_LOGIN = "auth.login"
    AUTH_LOGOUT = "auth.logout"
    AUTH_FAILED = "auth.failed"
    AUTH_TOKEN_REFRESH = "auth.token_refresh"

    API_ACCESS = "api.access"
    API_MODIFY = "api.modify"
    API_DELETE = "api.delete"
    API_CREATE = "api.create"

    USER_CREATE = "user.create"
    USER_UPDATE = "user.update"
    USER_DELETE = "user.delete"
    USER_DEACTIVATE = "user.deactivate"

    PERMISSION_CHANGE = "permission.change"
    ROLE_CHANGE = "role.change"

    SECURITY_ALERT = "security.alert"
    COMPLIANCE_VIOLATION = "compliance.violation"

    SYSTEM_CONFIG = "system.config"
    SYSTEM_MAINTENANCE = "system.maintenance"


class ComplianceStandard(Enum):
    """Supported compliance standards."""

    GDPR = "gdpr"
    HIPAA = "hipaa"
    SOX = "sox"
    PCI_DSS = "pci_dss"
    ISO_27001 = "iso_27001"


@dataclass
class AuditEvent:
    """Audit event record."""

    event_id: str
    event_type: AuditEventType
    user_id: str
    username: str
    timestamp: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    resource: Optional[str] = None
    action: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    compliance_flags: Set[ComplianceStandard] = field(default_factory=set)
    hash_chain: Optional[str] = None
    signature: Optional[str] = None


@dataclass
class ComplianceRule:
    """Compliance monitoring rule."""

    rule_id: str
    name: str
    description: str
    standard: ComplianceStandard
    severity: str  # "low", "medium", "high", "critical"
    conditions: Dict[str, Any]
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ComplianceViolation:
    """Compliance violation record."""

    violation_id: str
    rule_id: str
    event_id: str
    user_id: str
    details: Dict[str, Any]
    severity: str
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None


class AuditLogger:
    """
    Comprehensive audit logging system with tamper-proof records.

    Maintains immutable audit trails with cryptographic integrity.
    """

    def __init__(self, retention_days: int = 2555):  # ~7 years
        self.events: List[AuditEvent] = []
        self.retention_days = retention_days
        self.last_hash = None
        self.secret_key = config.security.audit_secret_key
        self._load_existing_audit_log()

    def _load_existing_audit_log(self):
        """Load existing audit log from storage."""
        # In production, this would load from secure database

    async def log_event(
        self,
        event_type: AuditEventType,
        user_id: str,
        username: str,
        resource: str = None,
        action: str = None,
        details: Dict[str, Any] = None,
        ip_address: str = None,
        user_agent: str = None,
        compliance_flags: Set[ComplianceStandard] = None,
    ) -> str:
        """Log an audit event with cryptographic integrity."""
        event_id = str(uuid.uuid4())

        event = AuditEvent(
            event_id=event_id,
            event_type=event_type,
            user_id=user_id,
            username=username,
            timestamp=datetime.now(),
            ip_address=ip_address,
            user_agent=user_agent,
            resource=resource,
            action=action,
            details=details or {},
            compliance_flags=compliance_flags or set(),
        )

        # Create hash chain for tamper-proof audit trail
        event_data = {
            "event_id": event.event_id,
            "event_type": event.event_type.value,
            "user_id": event.user_id,
            "timestamp": event.timestamp.isoformat(),
            "resource": event.resource,
            "action": event.action,
            "details": event.details,
        }

        data_str = json.dumps(event_data, sort_keys=True)
        current_hash = hashlib.sha256(data_str.encode()).hexdigest()

        # Chain with previous hash for integrity
        if self.last_hash:
            chain_data = f"{self.last_hash}:{current_hash}".encode()
            event.hash_chain = hashlib.sha256(chain_data).hexdigest()

        # Sign the event
        event.signature = hmac.new(
            self.secret_key.encode(), data_str.encode(), hashlib.sha256
        ).hexdigest()

        self.events.append(event)
        self.last_hash = current_hash

        # Auto-cleanup old events
        await self._cleanup_old_events()

        return event_id

    async def get_events(
        self,
        user_id: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AuditEvent]:
        """Query audit events with filtering."""
        filtered_events = self.events

        if user_id:
            filtered_events = [e for e in filtered_events if e.user_id == user_id]

        if event_type:
            filtered_events = [e for e in filtered_events if e.event_type == event_type]

        if start_date:
            filtered_events = [e for e in filtered_events if e.timestamp >= start_date]

        if end_date:
            filtered_events = [e for e in filtered_events if e.timestamp <= end_date]

        # Sort by timestamp descending
        filtered_events.sort(key=lambda e: e.timestamp, reverse=True)

        return filtered_events[offset : offset + limit]

    async def get_event_by_id(self, event_id: str) -> Optional[AuditEvent]:
        """Get specific audit event by ID."""
        return next((e for e in self.events if e.event_id == event_id), None)

    async def verify_integrity(self) -> Tuple[bool, List[str]]:
        """
        Verify audit log integrity by checking hash chains.

        Returns (is_valid, violations)
        """
        violations = []
        current_hash = None

        for event in sorted(self.events, key=lambda e: e.timestamp):
            event_data = {
                "event_id": event.event_id,
                "event_type": event.event_type.value,
                "user_id": event.user_id,
                "timestamp": event.timestamp.isoformat(),
                "resource": event.resource,
                "action": event.action,
                "details": event.details,
            }

            data_str = json.dumps(event_data, sort_keys=True)
            calculated_hash = hashlib.sha256(data_str.encode()).hexdigest()

            # Verify signature
            expected_signature = hmac.new(
                self.secret_key.encode(), data_str.encode(), hashlib.sha256
            ).hexdigest()

            if event.signature != expected_signature:
                violations.append(
                    f"Event {event.event_id}: signature verification failed"
                )

            # Verify hash chain
            if current_hash and event.hash_chain:
                expected_chain = hashlib.sha256(
                    f"{current_hash}:{calculated_hash}".encode()
                ).hexdigest()
                if event.hash_chain != expected_chain:
                    violations.append(
                        f"Event {event.event_id}: hash chain verification failed"
                    )

            current_hash = calculated_hash

        return len(violations) == 0, violations

    async def export_audit_log(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        format: str = "json",
    ) -> str:
        """Export audit log for compliance or backup."""
        events = await self.get_events(
            start_date=start_date, end_date=end_date, limit=10000
        )  # Large limit for export

        if format == "json":
            return json.dumps(
                [
                    {
                        "event_id": e.event_id,
                        "event_type": e.event_type.value,
                        "user_id": e.user_id,
                        "username": e.username,
                        "timestamp": e.timestamp.isoformat(),
                        "resource": e.resource,
                        "action": e.action,
                        "details": e.details,
                        "compliance_flags": [f.value for f in e.compliance_flags],
                    }
                    for e in events
                ],
                indent=2,
            )

        return ""

    async def _cleanup_old_events(self):
        """Remove events older than retention period."""
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        self.events = [e for e in self.events if e.timestamp >= cutoff_date]


class ComplianceMonitor:
    """
    Compliance monitoring and violation detection.

    Monitors system activity against compliance standards and generates alerts.
    """

    def __init__(self, audit_logger: AuditLogger):
        self.audit_logger = audit_logger
        self.rules: Dict[str, ComplianceRule] = {}
        self.violations: List[ComplianceViolation] = {}
        self._load_compliance_rules()

    def _load_compliance_rules(self):
        """Load predefined compliance rules."""
        self.rules = {
            "gdpr_data_access": ComplianceRule(
                rule_id="gdpr_data_access",
                name="GDPR Data Access Logging",
                description="All personal data access must be logged",
                standard=ComplianceStandard.GDPR,
                severity="high",
                conditions={
                    "event_types": ["api.access"],
                    "resources": ["personal_data", "user_data"],
                    "requires_audit": True,
                },
            ),
            "gdpr_data_deletion": ComplianceRule(
                rule_id="gdpr_data_deletion",
                name="GDPR Right to Erasure",
                description="Data deletion requests must be processed within 30 days",
                standard=ComplianceStandard.GDPR,
                severity="critical",
                conditions={
                    "event_types": ["api.delete"],
                    "resources": ["personal_data", "user_data"],
                    "max_processing_days": 30,
                },
            ),
            "hipaa_access_control": ComplianceRule(
                rule_id="hipaa_access_control",
                name="HIPAA Access Control",
                description="Access to protected health information must be controlled",
                standard=ComplianceStandard.HIPAA,
                severity="critical",
                conditions={
                    "event_types": ["api.access"],
                    "resources": ["health_data", "phi"],
                    "authorized_roles_only": ["admin", "manager", "auditor"],
                },
            ),
            "sox_financial_audit": ComplianceRule(
                rule_id="sox_financial_audit",
                name="SOX Financial Data Audit",
                description="All changes to financial data must be auditable",
                standard=ComplianceStandard.SOX,
                severity="high",
                conditions={
                    "event_types": ["api.modify", "api.create"],
                    "resources": ["financial_data", "billing"],
                    "requires_audit_trail": True,
                },
            ),
            "iso_security_incident": ComplianceRule(
                rule_id="iso_security_incident",
                name="ISO 27001 Security Incident Reporting",
                description="Security incidents must be reported within 24 hours",
                standard=ComplianceStandard.ISO_27001,
                severity="high",
                conditions={
                    "event_types": ["security.alert"],
                    "max_reporting_hours": 24,
                },
            ),
        }

    async def check_compliance(self, event: AuditEvent) -> List[ComplianceViolation]:
        """Check event against compliance rules and return violations."""
        violations = []

        for rule in self.rules.values():
            if not rule.enabled:
                continue

            violation = await self._check_rule_violation(rule, event)
            if violation:
                violations.append(violation)
                self.violations[violation.violation_id] = violation

        return violations

    async def _check_rule_violation(
        self, rule: ComplianceRule, event: AuditEvent
    ) -> Optional[ComplianceViolation]:
        """Check if event violates a specific compliance rule."""
        conditions = rule.conditions

        # Check event type
        if "event_types" in conditions:
            if event.event_type.value not in conditions["event_types"]:
                return None

        # Check resource type
        if "resources" in conditions:
            if not event.resource or event.resource not in conditions["resources"]:
                return None

        # Check role authorization for HIPAA
        if (
            "authorized_roles_only" in conditions
            and rule.standard == ComplianceStandard.HIPAA
        ):
            # In production, this would check user's actual role
            # For now, assume violation if accessing protected resources
            pass

        # Create violation record
        violation = ComplianceViolation(
            violation_id=str(uuid.uuid4()),
            rule_id=rule.rule_id,
            event_id=event.event_id,
            user_id=event.user_id,
            details={
                "rule_name": rule.name,
                "standard": rule.standard.value,
                "conditions": conditions,
                "event_details": {
                    "type": event.event_type.value,
                    "resource": event.resource,
                    "action": event.action,
                },
            },
            severity=rule.severity,
            timestamp=datetime.now(),
        )

        return violation

    async def get_violations(
        self,
        standard: Optional[ComplianceStandard] = None,
        resolved: Optional[bool] = None,
        limit: int = 100,
    ) -> List[ComplianceViolation]:
        """Get compliance violations with filtering."""
        violations = list(self.violations.values())

        if standard:
            violations = [
                v for v in violations if self.rules[v.rule_id].standard == standard
            ]

        if resolved is not None:
            violations = [v for v in violations if v.resolved == resolved]

        violations.sort(key=lambda v: v.timestamp, reverse=True)
        return violations[:limit]

    async def resolve_violation(self, violation_id: str, resolution_notes: str) -> bool:
        """Mark violation as resolved."""
        violation = self.violations.get(violation_id)
        if not violation:
            return False

        violation.resolved = True
        violation.resolved_at = datetime.now()
        violation.resolution_notes = resolution_notes
        return True

    async def generate_compliance_report(
        self, standard: ComplianceStandard, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Generate compliance report for a specific standard."""
        violations = await self.get_violations(standard=standard, resolved=False)

        # Filter by date range
        violations = [v for v in violations if start_date <= v.timestamp <= end_date]

        report = {
            "standard": standard.value,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            "summary": {
                "total_violations": len(violations),
                "severity_breakdown": {
                    "critical": len(
                        [v for v in violations if v.severity == "critical"]
                    ),
                    "high": len([v for v in violations if v.severity == "high"]),
                    "medium": len([v for v in violations if v.severity == "medium"]),
                    "low": len([v for v in violations if v.severity == "low"]),
                },
            },
            "violations": [
                {
                    "violation_id": v.violation_id,
                    "rule_id": v.rule_id,
                    "rule_name": self.rules[v.rule_id].name,
                    "user_id": v.user_id,
                    "severity": v.severity,
                    "timestamp": v.timestamp.isoformat(),
                    "details": v.details,
                }
                for v in violations
            ],
            "compliance_status": (
                "compliant" if len(violations) == 0 else "non_compliant"
            ),
            "generated_at": datetime.now().isoformat(),
        }

        return report

    async def get_compliance_status(self) -> Dict[str, Dict[str, Any]]:
        """Get overall compliance status across all standards."""
        status = {}

        for standard in ComplianceStandard:
            violations = await self.get_violations(standard=standard, resolved=False)
            critical_violations = len(
                [v for v in violations if v.severity == "critical"]
            )

            status[standard.value] = {
                "total_violations": len(violations),
                "critical_violations": critical_violations,
                "status": "compliant" if len(violations) == 0 else "non_compliant",
                "last_checked": datetime.now().isoformat(),
            }

        return status
