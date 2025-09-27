"""Security issue domain entity."""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field


@dataclass
class SecurityIssue:
    """Domain entity representing a security issue found in code.

    Encapsulates security vulnerability information including severity,
    location, description, and remediation guidance.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = ""  # sql_injection, xss, auth_bypass, etc.
    severity: str = ""  # critical, high, medium, low, info
    title: str = ""
    description: str = ""
    file_path: str = ""
    line_number: Optional[int] = None
    code_snippet: str = ""

    # Vulnerability details
    cwe_id: Optional[str] = None  # Common Weakness Enumeration ID
    owasp_category: Optional[str] = None  # OWASP Top 10 category
    cvss_score: Optional[float] = None  # CVSS v3 score

    # Remediation
    remediation: str = ""
    remediation_effort: str = ""  # low, medium, high
    references: List[str] = field(default_factory=list)

    # Metadata
    detected_by: str = ""  # scanner name/version
    confidence: str = ""  # high, medium, low
    false_positive_likelihood: str = ""  # high, medium, low
    tags: List[str] = field(default_factory=list)

    detected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    resolved: bool = False
    resolved_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate security issue after initialization."""
        if not self.type.strip():
            raise ValueError("Issue type cannot be empty")
        if not self.severity.strip():
            raise ValueError("Severity cannot be empty")
        if not self.title.strip():
            raise ValueError("Title cannot be empty")
        if not self.file_path.strip():
            raise ValueError("File path cannot be empty")

        # Ensure valid severities
        valid_severities = ["critical", "high", "medium", "low", "info"]
        if self.severity.lower() not in valid_severities:
            raise ValueError(f"Invalid severity: {self.severity}")

        # Ensure valid confidence levels
        valid_confidences = ["high", "medium", "low"]
        if self.confidence and self.confidence.lower() not in valid_confidences:
            raise ValueError(f"Invalid confidence: {self.confidence}")

        # Validate CVSS score
        if self.cvss_score is not None and (self.cvss_score < 0.0 or self.cvss_score > 10.0):
            raise ValueError("CVSS score must be between 0.0 and 10.0")

    @property
    def is_critical(self) -> bool:
        """Check if this is a critical security issue."""
        return self.severity.lower() == "critical"

    @property
    def is_high_severity(self) -> bool:
        """Check if this is a high-severity security issue."""
        return self.severity.lower() in ["critical", "high"]

    @property
    def severity_score(self) -> int:
        """Get numeric severity score for sorting/comparison."""
        severity_map = {
            "critical": 5,
            "high": 4,
            "medium": 3,
            "low": 2,
            "info": 1
        }
        return severity_map.get(self.severity.lower(), 0)

    @property
    def confidence_score(self) -> int:
        """Get numeric confidence score."""
        confidence_map = {
            "high": 3,
            "medium": 2,
            "low": 1
        }
        return confidence_map.get(self.confidence.lower(), 0)

    @property
    def risk_score(self) -> float:
        """Calculate overall risk score combining severity and confidence."""
        severity_weight = self.severity_score / 5.0  # Normalize to 0-1
        confidence_weight = self.confidence_score / 3.0  # Normalize to 0-1
        return severity_weight * confidence_weight * 100  # Scale to 0-100

    @property
    def age_days(self) -> float:
        """Get age of this security issue in days."""
        reference_time = self.resolved_at if self.resolved else self.detected_at
        return (datetime.now(timezone.utc) - reference_time).total_seconds() / 86400

    @property
    def needs_attention(self) -> bool:
        """Check if this issue needs immediate attention."""
        return (self.is_high_severity and not self.resolved and
                self.confidence.lower() in ["high", "medium"])

    def add_reference(self, reference: str) -> None:
        """Add a reference URL or documentation link."""
        if reference not in self.references:
            self.references.append(reference)

    def add_tag(self, tag: str) -> None:
        """Add a tag to this security issue."""
        if tag not in self.tags:
            self.tags.append(tag)

    def resolve(self, resolution_notes: str = "") -> None:
        """Mark this security issue as resolved."""
        self.resolved = True
        self.resolved_at = datetime.now(timezone.utc)
        if resolution_notes:
            self.add_tag(f"resolved:{resolution_notes}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "type": self.type,
            "severity": self.severity,
            "title": self.title,
            "description": self.description,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "code_snippet": self.code_snippet,
            "cwe_id": self.cwe_id,
            "owasp_category": self.owasp_category,
            "cvss_score": self.cvss_score,
            "remediation": self.remediation,
            "remediation_effort": self.remediation_effort,
            "references": self.references,
            "detected_by": self.detected_by,
            "confidence": self.confidence,
            "false_positive_likelihood": self.false_positive_likelihood,
            "tags": self.tags,
            "detected_at": self.detected_at.isoformat(),
            "resolved": self.resolved,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SecurityIssue':
        """Create SecurityIssue from dictionary."""
        # Handle datetime conversion
        for date_field in ['detected_at', 'resolved_at']:
            if isinstance(data.get(date_field), str):
                data[date_field] = datetime.fromisoformat(data[date_field].replace('Z', '+00:00'))

        return cls(**data)
