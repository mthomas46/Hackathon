"""Finding domain service."""

from typing import List, Dict, Any, Optional
from collections import defaultdict

from ..entities import Finding, FindingId, Severity
from ..entities.document import DocumentId


class FindingService:
    """Domain service for finding operations."""

    def __init__(self):
        """Initialize finding service."""
        pass

    def create_finding(self, document_id: DocumentId, analysis_id: str,
                      title: str, description: str, severity: Severity,
                      category: str, confidence: float = 0.0,
                      location: Optional[Dict[str, Any]] = None,
                      suggestion: Optional[str] = None) -> Finding:
        """Create a new finding."""
        finding_id = FindingId(f"finding_{document_id.value}_{hash(title) % 10000}")

        finding = Finding(
            id=finding_id,
            document_id=document_id,
            analysis_id=analysis_id,
            title=title,
            description=description,
            severity=severity,
            category=category,
            confidence=confidence,
            location=location,
            suggestion=suggestion
        )

        return finding

    def categorize_findings(self, findings: List[Finding]) -> Dict[str, List[Finding]]:
        """Categorize findings by category."""
        categorized = defaultdict(list)

        for finding in findings:
            categorized[finding.category].append(finding)

        return dict(categorized)

    def filter_findings_by_severity(self, findings: List[Finding],
                                   min_severity: Severity) -> List[Finding]:
        """Filter findings by minimum severity level."""
        severity_order = {
            Severity.INFO: 1,
            Severity.LOW: 2,
            Severity.MEDIUM: 3,
            Severity.HIGH: 4,
            Severity.CRITICAL: 5
        }

        min_level = severity_order[min_severity]

        return [
            finding for finding in findings
            if severity_order[finding.severity] >= min_level
        ]

    def filter_findings_by_category(self, findings: List[Finding],
                                   categories: List[str]) -> List[Finding]:
        """Filter findings by category."""
        return [
            finding for finding in findings
            if finding.category in categories
        ]

    def get_findings_statistics(self, findings: List[Finding]) -> Dict[str, Any]:
        """Get statistics about findings."""
        if not findings:
            return {
                'total_findings': 0,
                'severity_distribution': {},
                'category_distribution': {},
                'avg_confidence': 0.0,
                'resolved_percentage': 0.0
            }

        # Severity distribution
        severity_counts = defaultdict(int)
        for finding in findings:
            severity_counts[finding.severity.value] += 1

        # Category distribution
        category_counts = defaultdict(int)
        for finding in findings:
            category_counts[finding.category] += 1

        # Other statistics
        total_findings = len(findings)
        avg_confidence = sum(f.confidence for f in findings) / total_findings
        resolved_count = sum(1 for f in findings if f.is_resolved())
        resolved_percentage = (resolved_count / total_findings) * 100

        return {
            'total_findings': total_findings,
            'severity_distribution': dict(severity_counts),
            'category_distribution': dict(category_counts),
            'avg_confidence': round(avg_confidence, 3),
            'resolved_percentage': round(resolved_percentage, 1),
            'unresolved_count': total_findings - resolved_count
        }

    def prioritize_findings(self, findings: List[Finding]) -> List[Finding]:
        """Prioritize findings by severity and confidence."""
        def priority_key(finding: Finding) -> tuple:
            # Sort by: severity (desc), confidence (desc), age (desc)
            severity_score = finding.severity_score
            confidence = finding.confidence
            age_days = finding.age_days
            return (-severity_score, -confidence, -age_days)

        return sorted(findings, key=priority_key)

    def get_findings_by_document(self, findings: List[Finding]) -> Dict[str, List[Finding]]:
        """Group findings by document ID."""
        grouped = defaultdict(list)

        for finding in findings:
            grouped[finding.document_id.value].append(finding)

        return dict(grouped)

    def get_high_priority_findings(self, findings: List[Finding],
                                  max_items: int = 10) -> List[Finding]:
        """Get top priority findings."""
        prioritized = self.prioritize_findings(findings)
        return prioritized[:max_items]

    def validate_finding(self, finding: Finding) -> List[str]:
        """Validate finding and return list of issues."""
        issues = []

        if len(finding.title) > 200:
            issues.append("Finding title too long (max 200 characters)")

        if len(finding.description) > 1000:
            issues.append("Finding description too long (max 1000 characters)")

        if not 0.0 <= finding.confidence <= 1.0:
            issues.append("Confidence must be between 0.0 and 1.0")

        if finding.category not in ['consistency', 'quality', 'security', 'performance', 'usability']:
            issues.append("Invalid category - must be one of: consistency, quality, security, performance, usability")

        return issues

    def merge_similar_findings(self, findings: List[Finding]) -> List[Finding]:
        """Merge similar findings to reduce duplicates."""
        # Simple implementation - in practice, this would use more sophisticated logic
        merged = []
        seen_titles = set()

        for finding in self.prioritize_findings(findings):
            if finding.title not in seen_titles:
                merged.append(finding)
                seen_titles.add(finding.title)

        return merged
