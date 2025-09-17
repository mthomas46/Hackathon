"""Finding factory for creating findings with proper categorization."""

from typing import Dict, Any, Optional, List
from datetime import datetime

from ..entities import Finding, FindingId, Severity
from ..entities.document import DocumentId
from ..entities.value_objects import Location, Suggestion
from ..services import FindingService


class FindingFactory:
    """Factory for creating Finding entities with proper categorization."""

    def __init__(self, finding_service: Optional[FindingService] = None):
        """Initialize factory with optional finding service."""
        self.finding_service = finding_service or FindingService()

    def create_consistency_finding(self, document_id: str, analysis_id: str,
                                  title: str, description: str,
                                  severity: str = "medium",
                                  location: Optional[Dict[str, Any]] = None,
                                  suggestion: Optional[str] = None) -> Finding:
        """Create a consistency-related finding."""
        return self._create_finding(
            document_id=document_id,
            analysis_id=analysis_id,
            title=title,
            description=description,
            category="consistency",
            severity=severity,
            location=location,
            suggestion=suggestion
        )

    def create_quality_finding(self, document_id: str, analysis_id: str,
                              title: str, description: str,
                              severity: str = "low",
                              location: Optional[Dict[str, Any]] = None,
                              suggestion: Optional[str] = None) -> Finding:
        """Create a quality-related finding."""
        return self._create_finding(
            document_id=document_id,
            analysis_id=analysis_id,
            title=title,
            description=description,
            category="quality",
            severity=severity,
            location=location,
            suggestion=suggestion
        )

    def create_security_finding(self, document_id: str, analysis_id: str,
                               title: str, description: str,
                               severity: str = "high",
                               location: Optional[Dict[str, Any]] = None,
                               suggestion: Optional[str] = None) -> Finding:
        """Create a security-related finding."""
        return self._create_finding(
            document_id=document_id,
            analysis_id=analysis_id,
            title=title,
            description=description,
            category="security",
            severity=severity,
            location=location,
            suggestion=suggestion
        )

    def create_performance_finding(self, document_id: str, analysis_id: str,
                                  title: str, description: str,
                                  severity: str = "medium",
                                  location: Optional[Dict[str, Any]] = None,
                                  suggestion: Optional[str] = None) -> Finding:
        """Create a performance-related finding."""
        return self._create_finding(
            document_id=document_id,
            analysis_id=analysis_id,
            title=title,
            description=description,
            category="performance",
            severity=severity,
            location=location,
            suggestion=suggestion
        )

    def create_usability_finding(self, document_id: str, analysis_id: str,
                                title: str, description: str,
                                severity: str = "low",
                                location: Optional[Dict[str, Any]] = None,
                                suggestion: Optional[str] = None) -> Finding:
        """Create a usability-related finding."""
        return self._create_finding(
            document_id=document_id,
            analysis_id=analysis_id,
            title=title,
            description=description,
            category="usability",
            severity=severity,
            location=location,
            suggestion=suggestion
        )

    def create_from_analysis_result(self, document_id: str, analysis_id: str,
                                   analysis_result: Dict[str, Any]) -> List[Finding]:
        """Create findings from analysis result data."""
        findings = []

        if 'findings' not in analysis_result:
            return findings

        for finding_data in analysis_result['findings']:
            finding = self._create_from_data(
                document_id=document_id,
                analysis_id=analysis_id,
                finding_data=finding_data
            )
            findings.append(finding)

        return findings

    def create_staleness_finding(self, document_id: str, analysis_id: str,
                                days_since_update: int) -> Finding:
        """Create a finding for stale documentation."""
        severity = self._calculate_staleness_severity(days_since_update)

        title = f"Documentation is {days_since_update} days old"
        description = f"This document hasn't been updated for {days_since_update} days. " \
                     f"Consider reviewing and updating to ensure accuracy."

        suggestion = "Review the content for accuracy and update as needed. " \
                    "Consider setting up automated reminders for regular reviews."

        return self.create_consistency_finding(
            document_id=document_id,
            analysis_id=analysis_id,
            title=title,
            description=description,
            severity=severity,
            suggestion=suggestion
        )

    def create_complexity_finding(self, document_id: str, analysis_id: str,
                                 complexity_score: float,
                                 readability_score: float) -> Finding:
        """Create a finding for complex or hard-to-read documentation."""
        severity = self._calculate_complexity_severity(complexity_score)

        title = f"Documentation complexity: {complexity_score:.1f}"
        description = f"This document has a complexity score of {complexity_score:.1f} " \
                     f"and readability score of {readability_score:.1f}. " \
                     f"Consider simplifying the language and structure."

        suggestion = "Use simpler words, shorter sentences, and clearer structure. " \
                    "Consider adding examples or breaking complex concepts into smaller sections."

        return self.create_quality_finding(
            document_id=document_id,
            analysis_id=analysis_id,
            title=title,
            description=description,
            severity=severity,
            suggestion=suggestion
        )

    def create_inconsistency_finding(self, document_id: str, analysis_id: str,
                                    inconsistency_type: str,
                                    details: str) -> Finding:
        """Create a finding for documentation inconsistencies."""
        severity = "high" if inconsistency_type == "terminology" else "medium"

        title = f"Inconsistent {inconsistency_type}"
        description = f"Found inconsistency in {inconsistency_type}: {details}"

        suggestion = f"Standardize {inconsistency_type} throughout the documentation. " \
                    "Create and follow style guidelines."

        return self.create_consistency_finding(
            document_id=document_id,
            analysis_id=analysis_id,
            title=title,
            description=description,
            severity=severity,
            suggestion=suggestion
        )

    def create_missing_information_finding(self, document_id: str, analysis_id: str,
                                         missing_elements: List[str]) -> Finding:
        """Create a finding for missing documentation elements."""
        title = "Missing documentation elements"
        description = f"The following elements are missing from the documentation: " \
                     f"{', '.join(missing_elements)}"

        suggestion = f"Add the missing elements: {', '.join(missing_elements)}. " \
                    "Ensure comprehensive coverage of all necessary information."

        return self.create_quality_finding(
            document_id=document_id,
            analysis_id=analysis_id,
            title=title,
            description=description,
            severity="medium",
            suggestion=suggestion
        )

    def create_outdated_reference_finding(self, document_id: str, analysis_id: str,
                                         reference: str, location: Dict[str, Any]) -> Finding:
        """Create a finding for outdated references."""
        title = f"Outdated reference: {reference}"
        description = f"The reference '{reference}' appears to be outdated or no longer valid."

        suggestion = "Update the reference to the current valid location or remove if no longer applicable."

        return self.create_consistency_finding(
            document_id=document_id,
            analysis_id=analysis_id,
            title=title,
            description=description,
            severity="medium",
            location=location,
            suggestion=suggestion
        )

    def _create_finding(self, document_id: str, analysis_id: str,
                       title: str, description: str, category: str,
                       severity: str, location: Optional[Dict[str, Any]] = None,
                       suggestion: Optional[str] = None) -> Finding:
        """Internal method to create finding with proper validation."""
        doc_id = DocumentId(document_id)
        severity_enum = Severity(severity.lower())

        return self.finding_service.create_finding(
            document_id=doc_id,
            analysis_id=analysis_id,
            title=title,
            description=description,
            severity=severity_enum,
            category=category,
            confidence=0.8,  # Default confidence
            location=location,
            suggestion=suggestion
        )

    def _create_from_data(self, document_id: str, analysis_id: str,
                         finding_data: Dict[str, Any]) -> Finding:
        """Create finding from raw data dictionary."""
        return self._create_finding(
            document_id=document_id,
            analysis_id=analysis_id,
            title=finding_data.get('title', 'Unknown Issue'),
            description=finding_data.get('description', ''),
            category=finding_data.get('category', 'general'),
            severity=finding_data.get('severity', 'medium'),
            location=finding_data.get('location'),
            suggestion=finding_data.get('suggestion')
        )

    def _calculate_staleness_severity(self, days: int) -> str:
        """Calculate severity based on days since last update."""
        if days > 365:
            return "high"
        elif days > 180:
            return "medium"
        elif days > 90:
            return "low"
        else:
            return "info"

    def _calculate_complexity_severity(self, score: float) -> str:
        """Calculate severity based on complexity score."""
        if score > 20.0:
            return "high"
        elif score > 15.0:
            return "medium"
        elif score > 10.0:
            return "low"
        else:
            return "info"

    def get_finding_categories(self) -> List[str]:
        """Get list of available finding categories."""
        return ['consistency', 'quality', 'security', 'performance', 'usability']

    def get_severity_levels(self) -> List[str]:
        """Get list of available severity levels."""
        return [severity.value for severity in Severity]

    def validate_finding_data(self, finding_data: Dict[str, Any]) -> List[str]:
        """Validate finding data and return list of validation errors."""
        errors = []

        required_fields = ['title', 'description', 'category', 'severity']
        for field in required_fields:
            if field not in finding_data:
                errors.append(f"Missing required field: {field}")

        if 'category' in finding_data and finding_data['category'] not in self.get_finding_categories():
            errors.append(f"Invalid category: {finding_data['category']}")

        if 'severity' in finding_data and finding_data['severity'] not in self.get_severity_levels():
            errors.append(f"Invalid severity: {finding_data['severity']}")

        return errors
