"""
PR Gap Detection Module

Advanced gap detection for identifying missing requirements, tests,
documentation, and other critical implementation gaps in PRs.
"""

from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum

class GapType(Enum):
    REQUIREMENT = "requirement"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    SECURITY = "security"
    PERFORMANCE = "performance"
    CODE_QUALITY = "code_quality"
    DEPLOYMENT = "deployment"

class GapSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class DetectedGap:
    """Represents a detected gap in PR implementation."""
    gap_type: GapType
    severity: GapSeverity
    description: str
    evidence: str
    recommendation: str
    estimated_effort: str  # "low", "medium", "high"
    blocking_approval: bool

class PRGapDetector:
    """Advanced gap detection for PR analysis."""

    def __init__(self):
        self.gap_patterns = {
            GapType.REQUIREMENT: [
                r'acceptance criteria.*not.*implement',
                r'missing.*requirement',
                r'jira.*ticket.*not.*address',
                r'requirement.*gap',
                r'specification.*not.*met'
            ],
            GapType.TESTING: [
                r'no.*test',
                r'missing.*test.*coverage',
                r'untested.*code',
                r'no.*unit.*test',
                r'missing.*integration.*test'
            ],
            GapType.DOCUMENTATION: [
                r'missing.*documentation',
                r'no.*readme.*update',
                r'undocumented.*api',
                r'missing.*api.*doc',
                r'documentation.*gap'
            ],
            GapType.SECURITY: [
                r'missing.*security',
                r'no.*validation',
                r'unsanitized.*input',
                r'missing.*authentication',
                r'security.*vulnerability'
            ]
        }

        self.quality_patterns = {
            'error_handling': [
                r'try.*catch', r'except', r'error.*handling', r'exception'
            ],
            'logging': [
                r'log', r'logger', r'logging', r'audit'
            ],
            'input_validation': [
                r'validate', r'sanitize', r'check', r'verify'
            ],
            'configuration': [
                r'config', r'environment', r'setting', r'parameter'
            ]
        }

    def detect_gaps(
        self,
        pr_data: Dict[str, Any],
        jira_data: Dict[str, Any],
        confluence_docs: List[Dict[str, Any]],
        cross_reference_results: Dict[str, Any]
    ) -> List[DetectedGap]:
        """
        Detect all types of gaps in the PR implementation.

        Returns:
            List of DetectedGap objects representing all identified gaps
        """
        gaps = []

        # Detect requirement gaps
        gaps.extend(self._detect_requirement_gaps(pr_data, jira_data, cross_reference_results))

        # Detect testing gaps
        gaps.extend(self._detect_testing_gaps(pr_data, jira_data))

        # Detect documentation gaps
        gaps.extend(self._detect_documentation_gaps(pr_data, confluence_docs, cross_reference_results))

        # Detect security gaps
        gaps.extend(self._detect_security_gaps(pr_data))

        # Detect code quality gaps
        gaps.extend(self._detect_code_quality_gaps(pr_data))

        # Detect performance gaps
        gaps.extend(self._detect_performance_gaps(pr_data))

        # Detect deployment gaps
        gaps.extend(self._detect_deployment_gaps(pr_data))

        return gaps

    def _detect_requirement_gaps(
        self,
        pr_data: Dict[str, Any],
        jira_data: Dict[str, Any],
        cross_reference_results: Dict[str, Any]
    ) -> List[DetectedGap]:
        """Detect gaps in requirements implementation."""
        gaps = []

        # Check cross-reference results for alignment issues
        alignment_gaps = cross_reference_results.get('identified_gaps', [])
        for gap in alignment_gaps:
            severity = GapSeverity.HIGH if 'not implemented' in gap.lower() else GapSeverity.MEDIUM
            gaps.append(DetectedGap(
                gap_type=GapType.REQUIREMENT,
                severity=severity,
                description=gap,
                evidence="Cross-reference analysis",
                recommendation="Implement the missing requirement or update Jira ticket",
                estimated_effort="medium",
                blocking_approval=severity == GapSeverity.CRITICAL
            ))

        # Check acceptance criteria coverage
        acceptance_criteria = jira_data.get('acceptance_criteria', [])
        pr_description = pr_data.get('description', '').lower()

        for criterion in acceptance_criteria:
            criterion_lower = criterion.lower()
            # Simple check if criterion is mentioned in PR description
            if not any(word in pr_description for word in criterion_lower.split()):
                gaps.append(DetectedGap(
                    gap_type=GapType.REQUIREMENT,
                    severity=GapSeverity.MEDIUM,
                    description=f"Acceptance criterion may not be addressed: {criterion[:50]}...",
                    evidence=f"Jira acceptance criteria: {criterion}",
                    recommendation="Verify that this acceptance criterion is properly implemented",
                    estimated_effort="low",
                    blocking_approval=False
                ))

        return gaps

    def _detect_testing_gaps(self, pr_data: Dict[str, Any], jira_data: Dict[str, Any]) -> List[DetectedGap]:
        """Detect gaps in testing coverage."""
        gaps = []

        files_changed = pr_data.get('files_changed', [])
        pr_description = pr_data.get('description', '').lower()

        # Check for test files
        test_files = [f for f in files_changed if 'test' in f.lower() or 'spec' in f.lower()]
        code_files = [f for f in files_changed if any(ext in f for ext in ['.py', '.js', '.java', '.go'])]

        # No test files for code changes
        if code_files and not test_files:
            gaps.append(DetectedGap(
                gap_type=GapType.TESTING,
                severity=GapSeverity.HIGH,
                description="No test files found for code changes",
                evidence=f"Modified {len(code_files)} code files but no test files",
                recommendation="Add unit tests and integration tests for the modified code",
                estimated_effort="medium",
                blocking_approval=True
            ))

        # Insufficient test coverage
        if test_files and len(test_files) < len(code_files) * 0.5:
            gaps.append(DetectedGap(
                gap_type=GapType.TESTING,
                severity=GapSeverity.MEDIUM,
                description="Insufficient test coverage",
                evidence=f"Only {len(test_files)} test files for {len(code_files)} code files",
                recommendation="Add more comprehensive test coverage",
                estimated_effort="medium",
                blocking_approval=False
            ))

        # Check for testing mentions in PR description
        if 'test' not in pr_description and 'testing' not in pr_description:
            gaps.append(DetectedGap(
                gap_type=GapType.TESTING,
                severity=GapSeverity.LOW,
                description="No mention of testing in PR description",
                evidence="PR description lacks testing information",
                recommendation="Document what testing was performed and results",
                estimated_effort="low",
                blocking_approval=False
            ))

        # Check for critical functionality without tests
        critical_patterns = ['auth', 'security', 'payment', 'database']
        for file in code_files:
            file_lower = file.lower()
            if any(pattern in file_lower for pattern in critical_patterns):
                if not test_files:
                    gaps.append(DetectedGap(
                        gap_type=GapType.TESTING,
                        severity=GapSeverity.CRITICAL,
                        description=f"Critical functionality lacks testing: {file}",
                        evidence=f"Modified critical file {file} without test coverage",
                        recommendation="Add comprehensive tests for critical functionality",
                        estimated_effort="high",
                        blocking_approval=True
                    ))
                    break

        return gaps

    def _detect_documentation_gaps(
        self,
        pr_data: Dict[str, Any],
        confluence_docs: List[Dict[str, Any]],
        cross_reference_results: Dict[str, Any]
    ) -> List[DetectedGap]:
        """Detect gaps in documentation."""
        gaps = []

        files_changed = pr_data.get('files_changed', [])
        pr_description = pr_data.get('description', '').lower()

        # Check for API changes without documentation
        api_files = [f for f in files_changed if any(term in f.lower() for term in ['api', 'endpoint', 'route'])]
        doc_files = [f for f in files_changed if any(term in f.lower() for term in ['doc', 'readme', 'md'])]

        if api_files and not doc_files:
            gaps.append(DetectedGap(
                gap_type=GapType.DOCUMENTATION,
                severity=GapSeverity.HIGH,
                description="API changes without documentation updates",
                evidence=f"Modified {len(api_files)} API files but no documentation files",
                recommendation="Update API documentation to reflect changes",
                estimated_effort="medium",
                blocking_approval=False
            ))

        # Check consistency issues from cross-reference analysis
        consistency_issues = cross_reference_results.get('consistency_issues', [])
        for issue in consistency_issues:
            if 'documentation' in issue.lower():
                severity = GapSeverity.HIGH if 'missing' in issue.lower() else GapSeverity.MEDIUM
                gaps.append(DetectedGap(
                    gap_type=GapType.DOCUMENTATION,
                    severity=severity,
                    description=issue,
                    evidence="Cross-reference analysis",
                    recommendation="Update documentation to resolve consistency issues",
                    estimated_effort="medium",
                    blocking_approval=False
                ))

        # Check for breaking changes without migration docs
        if 'breaking' in pr_description or 'breaking change' in pr_description:
            migration_docs = [doc for doc in confluence_docs if 'migration' in doc.get('title', '').lower()]
            if not migration_docs:
                gaps.append(DetectedGap(
                    gap_type=GapType.DOCUMENTATION,
                    severity=GapSeverity.CRITICAL,
                    description="Breaking changes without migration documentation",
                    evidence="PR description mentions breaking changes",
                    recommendation="Create migration guide and update release notes",
                    estimated_effort="high",
                    blocking_approval=True
                ))

        return gaps

    def _detect_security_gaps(self, pr_data: Dict[str, Any]) -> List[DetectedGap]:
        """Detect gaps in security implementation."""
        gaps = []

        files_changed = pr_data.get('files_changed', [])
        pr_description = pr_data.get('description', '').lower()

        # Check for authentication/authorization changes without security review
        security_files = [f for f in files_changed if any(term in f.lower() for term in ['auth', 'security', 'login'])]
        if security_files and 'security' not in pr_description:
            gaps.append(DetectedGap(
                gap_type=GapType.SECURITY,
                severity=GapSeverity.HIGH,
                description="Security-related changes lack security review mention",
                evidence=f"Modified {len(security_files)} security-related files",
                recommendation="Document security review and testing performed",
                estimated_effort="low",
                blocking_approval=False
            ))

        # Check for input validation
        if any(term in f.lower() for f in files_changed for term in ['input', 'form', 'request']):
            if not any(pattern in pr_description for pattern in ['validate', 'sanitize', 'check']):
                gaps.append(DetectedGap(
                    gap_type=GapType.SECURITY,
                    severity=GapSeverity.MEDIUM,
                    description="Input handling changes without validation mention",
                    evidence="Modified files that handle user input",
                    recommendation="Ensure input validation and sanitization is implemented",
                    estimated_effort="medium",
                    blocking_approval=False
                ))

        return gaps

    def _detect_code_quality_gaps(self, pr_data: Dict[str, Any]) -> List[DetectedGap]:
        """Detect gaps in code quality."""
        gaps = []

        files_changed = pr_data.get('files_changed', [])
        pr_description = pr_data.get('description', '').lower()

        # Check for error handling
        if len(files_changed) > 3 and not any(pattern in pr_description for pattern in ['error', 'exception', 'handling']):
            gaps.append(DetectedGap(
                gap_type=GapType.CODE_QUALITY,
                severity=GapSeverity.LOW,
                description="No mention of error handling in PR description",
                evidence=f"Modified {len(files_changed)} files without error handling mention",
                recommendation="Verify proper error handling is implemented",
                estimated_effort="low",
                blocking_approval=False
            ))

        # Check for large PRs
        if len(files_changed) > 20:
            gaps.append(DetectedGap(
                gap_type=GapType.CODE_QUALITY,
                severity=GapSeverity.MEDIUM,
                description="Very large PR may need to be broken down",
                evidence=f"Modified {len(files_changed)} files in single PR",
                recommendation="Consider splitting into smaller, focused PRs",
                estimated_effort="high",
                blocking_approval=False
            ))

        # Check for configuration changes
        config_files = [f for f in files_changed if 'config' in f.lower() or '.yml' in f or '.yaml' in f]
        if config_files and not any(term in pr_description for term in ['config', 'environment', 'setting']):
            gaps.append(DetectedGap(
                gap_type=GapType.CODE_QUALITY,
                severity=GapSeverity.LOW,
                description="Configuration changes without documentation",
                evidence=f"Modified {len(config_files)} configuration files",
                recommendation="Document configuration changes and their impact",
                estimated_effort="low",
                blocking_approval=False
            ))

        return gaps

    def _detect_performance_gaps(self, pr_data: Dict[str, Any]) -> List[DetectedGap]:
        """Detect gaps in performance considerations."""
        gaps = []

        files_changed = pr_data.get('files_changed', [])
        pr_description = pr_data.get('description', '').lower()

        # Check for database-related changes
        db_files = [f for f in files_changed if any(term in f.lower() for term in ['database', 'db', 'sql', 'query'])]
        if db_files and not any(term in pr_description for term in ['performance', 'optimization', 'query']):
            gaps.append(DetectedGap(
                gap_type=GapType.PERFORMANCE,
                severity=GapSeverity.LOW,
                description="Database changes without performance consideration",
                evidence=f"Modified {len(db_files)} database-related files",
                recommendation="Verify query performance and add indexes if needed",
                estimated_effort="medium",
                blocking_approval=False
            ))

        # Check for large data processing
        if any(term in pr_description for term in ['bulk', 'batch', 'large', 'million']):
            if not any(term in pr_description for term in ['performance', 'optimization', 'memory']):
                gaps.append(DetectedGap(
                    gap_type=GapType.PERFORMANCE,
                    severity=GapSeverity.MEDIUM,
                    description="Large data processing without performance analysis",
                    evidence="PR description mentions large-scale data processing",
                    recommendation="Add performance testing and optimization analysis",
                    estimated_effort="high",
                    blocking_approval=False
                ))

        return gaps

    def _detect_deployment_gaps(self, pr_data: Dict[str, Any]) -> List[DetectedGap]:
        """Detect gaps in deployment considerations."""
        gaps = []

        files_changed = pr_data.get('files_changed', [])
        pr_description = pr_data.get('description', '').lower()

        # Check for infrastructure changes
        infra_files = [f for f in files_changed if any(term in f.lower() for term in ['docker', 'k8s', 'deploy', 'ci', 'cd'])]
        if infra_files and not any(term in pr_description for term in ['deploy', 'infrastructure', 'ci', 'cd']):
            gaps.append(DetectedGap(
                gap_type=GapType.DEPLOYMENT,
                severity=GapSeverity.MEDIUM,
                description="Infrastructure changes without deployment documentation",
                evidence=f"Modified {len(infra_files)} infrastructure files",
                recommendation="Document deployment changes and rollback procedures",
                estimated_effort="medium",
                blocking_approval=False
            ))

        # Check for environment variable changes
        if any(term in pr_description for term in ['environment', 'env', 'variable']):
            if not any(term in pr_description for term in ['documentation', 'readme']):
                gaps.append(DetectedGap(
                    gap_type=GapType.DEPLOYMENT,
                    severity=GapSeverity.LOW,
                    description="Environment changes without documentation",
                    evidence="PR mentions environment variable changes",
                    recommendation="Document required environment variables and their purpose",
                    estimated_effort="low",
                    blocking_approval=False
                ))

        return gaps

    def prioritize_gaps(self, gaps: List[DetectedGap]) -> List[DetectedGap]:
        """Prioritize gaps by severity and blocking status."""
        return sorted(gaps, key=lambda g: (
            0 if g.blocking_approval else 1,  # Blocking first
            {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}[g.severity.value]  # By severity
        ))

    def get_gap_summary(self, gaps: List[DetectedGap]) -> Dict[str, Any]:
        """Generate summary statistics for detected gaps."""
        total_gaps = len(gaps)
        blocking_gaps = len([g for g in gaps if g.blocking_approval])

        severity_counts = {
            'critical': len([g for g in gaps if g.severity == GapSeverity.CRITICAL]),
            'high': len([g for g in gaps if g.severity == GapSeverity.HIGH]),
            'medium': len([g for g in gaps if g.severity == GapSeverity.MEDIUM]),
            'low': len([g for g in gaps if g.severity == GapSeverity.LOW])
        }

        type_counts = {}
        for gap in gaps:
            gap_type = gap.gap_type.value
            type_counts[gap_type] = type_counts.get(gap_type, 0) + 1

        return {
            'total_gaps': total_gaps,
            'blocking_gaps': blocking_gaps,
            'severity_distribution': severity_counts,
            'type_distribution': type_counts,
            'overall_risk_level': self._calculate_risk_level(total_gaps, blocking_gaps, severity_counts)
        }

    def _calculate_risk_level(self, total_gaps: int, blocking_gaps: int, severity_counts: Dict[str, int]) -> str:
        """Calculate overall risk level based on gap analysis."""
        if blocking_gaps > 0 or severity_counts['critical'] > 0:
            return "critical"
        elif total_gaps > 5 or severity_counts['high'] > 2:
            return "high"
        elif total_gaps > 2 or severity_counts['high'] > 0:
            return "medium"
        elif total_gaps > 0:
            return "low"
        else:
            return "none"


# Create singleton instance
pr_gap_detector = PRGapDetector()
