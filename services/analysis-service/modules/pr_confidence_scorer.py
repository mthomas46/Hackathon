"""
PR Confidence Scoring Module

Advanced confidence scoring algorithm for PR approval recommendations
based on multiple factors including alignment, quality, risks, and completeness.
"""

import math
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

class ConfidenceLevel(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    CRITICAL = "critical"

class ApprovalRecommendation(Enum):
    APPROVE = "approve"
    REVIEW_REQUIRED = "review_required"
    REJECT = "reject"
    HOLD = "hold"

@dataclass
class ConfidenceScore:
    """Comprehensive confidence score for PR evaluation."""
    overall_score: float
    confidence_level: ConfidenceLevel
    approval_recommendation: ApprovalRecommendation
    component_scores: Dict[str, float]
    risk_factors: List[str]
    critical_concerns: List[str]
    strengths: List[str]
    improvement_areas: List[str]
    rationale: str

class PRConfidenceScorer:
    """Advanced confidence scoring for PR approval decisions."""

    def __init__(self):
        self.weights = {
            'requirements_alignment': 0.35,
            'code_quality': 0.25,
            'testing_completeness': 0.15,
            'documentation_consistency': 0.15,
            'security_compliance': 0.10
        }

        self.quality_indicators = {
            'code_review': ['peer review', 'code review', 'reviewed-by'],
            'testing': ['test', 'spec', 'assert', 'coverage', 'unit', 'integration'],
            'documentation': ['readme', 'doc', 'comment', 'javadoc', 'api_doc'],
            'security': ['security', 'encrypt', 'hash', 'sanitize', 'validate']
        }

    def calculate_confidence_score(
        self,
        pr_data: Dict[str, Any],
        jira_data: Dict[str, Any],
        confluence_docs: List[Dict[str, Any]],
        cross_reference_results: Dict[str, Any],
        code_analysis_results: Optional[Dict[str, Any]] = None
    ) -> ConfidenceScore:
        """
        Calculate comprehensive confidence score for PR approval.

        Args:
            pr_data: Pull request information
            jira_data: Associated Jira ticket data
            confluence_docs: Related documentation
            cross_reference_results: Results from cross-reference analysis
            code_analysis_results: Optional code quality analysis

        Returns:
            ConfidenceScore with detailed analysis
        """
        # Calculate component scores
        component_scores = {}

        # 1. Requirements Alignment Score
        component_scores['requirements_alignment'] = cross_reference_results.get('overall_alignment_score', 0.5)

        # 2. Code Quality Score
        component_scores['code_quality'] = self._calculate_code_quality_score(
            pr_data, code_analysis_results
        )

        # 3. Testing Completeness Score
        component_scores['testing_completeness'] = self._calculate_testing_score(pr_data)

        # 4. Documentation Consistency Score
        component_scores['documentation_consistency'] = cross_reference_results.get('documentation_consistency', {}).get('overall_score', 0.5)

        # 5. Security Compliance Score
        component_scores['security_compliance'] = self._calculate_security_score(pr_data)

        # Calculate weighted overall score
        overall_score = sum(
            score * self.weights[component]
            for component, score in component_scores.items()
        )

        # Determine confidence level and approval recommendation
        confidence_level = self._determine_confidence_level(overall_score)
        approval_recommendation = self._determine_approval_recommendation(
            overall_score, component_scores
        )

        # Identify risk factors and concerns
        risk_factors = self._identify_risk_factors(component_scores, cross_reference_results)
        critical_concerns = self._identify_critical_concerns(component_scores, cross_reference_results)
        strengths = self._identify_strengths(component_scores)
        improvement_areas = self._identify_improvement_areas(component_scores)

        # Generate rationale
        rationale = self._generate_rationale(overall_score, component_scores, risk_factors)

        return ConfidenceScore(
            overall_score=overall_score,
            confidence_level=confidence_level,
            approval_recommendation=approval_recommendation,
            component_scores=component_scores,
            risk_factors=risk_factors,
            critical_concerns=critical_concerns,
            strengths=strengths,
            improvement_areas=improvement_areas,
            rationale=rationale
        )

    def _calculate_code_quality_score(
        self,
        pr_data: Dict[str, Any],
        code_analysis_results: Optional[Dict[str, Any]] = None
    ) -> float:
        """Calculate code quality score based on various factors."""
        score = 0.7  # Base score

        pr_description = pr_data.get('description', '').lower()
        files_changed = pr_data.get('files_changed', [])

        # Check for code review indicators
        if any(indicator in pr_description for indicator in self.quality_indicators['code_review']):
            score += 0.1

        # Check file types and complexity
        code_files = [f for f in files_changed if any(ext in f for ext in ['.py', '.js', '.java', '.go', '.rb'])]
        test_files = [f for f in files_changed if 'test' in f.lower()]

        if len(code_files) > 10:  # Large PR
            score -= 0.1
        elif len(code_files) > 5:  # Medium PR
            score -= 0.05

        # Check for test files
        if len(test_files) == 0:
            score -= 0.15
        elif len(test_files) >= len(code_files) * 0.5:  # Good test coverage
            score += 0.1

        # Use code analysis results if available
        if code_analysis_results:
            quality_score = code_analysis_results.get('overall_quality', 0.5)
            score = (score + quality_score) / 2

        return max(0.0, min(1.0, score))

    def _calculate_testing_score(self, pr_data: Dict[str, Any]) -> float:
        """Calculate testing completeness score."""
        score = 0.5  # Base score

        pr_description = pr_data.get('description', '').lower()
        files_changed = pr_data.get('files_changed', [])

        # Check for testing indicators in description
        testing_indicators = sum(
            1 for indicator in self.quality_indicators['testing']
            if indicator in pr_description
        )

        if testing_indicators > 0:
            score += min(0.3, testing_indicators * 0.1)

        # Check for test files
        test_files = [f for f in files_changed if any(term in f.lower() for term in ['test', 'spec'])]
        code_files = [f for f in files_changed if any(ext in f for ext in ['.py', '.js', '.java', '.go'])]

        if test_files:
            test_ratio = len(test_files) / max(len(code_files), 1)
            if test_ratio >= 1.0:  # At least 1:1 test to code ratio
                score += 0.2
            elif test_ratio >= 0.5:  # At least 1:2 ratio
                score += 0.1
        else:
            score -= 0.2  # No test files found

        return max(0.0, min(1.0, score))

    def _calculate_security_score(self, pr_data: Dict[str, Any]) -> float:
        """Calculate security compliance score."""
        score = 0.6  # Base score

        pr_description = pr_data.get('description', '').lower()
        files_changed = pr_data.get('files_changed', [])

        # Check for security-related changes
        security_changes = [f for f in files_changed if any(term in f.lower() for term in ['auth', 'security', 'encrypt'])]

        if security_changes:
            score += 0.2  # Security-related changes get higher scrutiny

        # Check for security indicators in description
        security_indicators = sum(
            1 for indicator in self.quality_indicators['security']
            if indicator in pr_description
        )

        if security_indicators > 0:
            score += min(0.2, security_indicators * 0.1)

        # Penalty for potential security risks
        if any(risk_term in pr_description for risk_term in ['hack', 'vulnerability', 'exploit']):
            score -= 0.3

        return max(0.0, min(1.0, score))

    def _determine_confidence_level(self, overall_score: float) -> ConfidenceLevel:
        """Determine confidence level based on overall score."""
        if overall_score >= 0.8:
            return ConfidenceLevel.HIGH
        elif overall_score >= 0.6:
            return ConfidenceLevel.MEDIUM
        elif overall_score >= 0.3:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.CRITICAL

    def _determine_approval_recommendation(
        self,
        overall_score: float,
        component_scores: Dict[str, float]
    ) -> ApprovalRecommendation:
        """Determine approval recommendation based on scores and factors."""

        # Critical factors that would reject or hold
        if component_scores.get('security_compliance', 1.0) < 0.4:
            return ApprovalRecommendation.REJECT

        if component_scores.get('requirements_alignment', 0.0) < 0.3:
            return ApprovalRecommendation.REJECT

        if overall_score >= 0.8:
            return ApprovalRecommendation.APPROVE
        elif overall_score >= 0.6:
            return ApprovalRecommendation.REVIEW_REQUIRED
        elif overall_score >= 0.3:
            return ApprovalRecommendation.HOLD
        else:
            return ApprovalRecommendation.REJECT

    def _identify_risk_factors(
        self,
        component_scores: Dict[str, float],
        cross_reference_results: Dict[str, Any]
    ) -> List[str]:
        """Identify risk factors that could affect PR quality."""
        risks = []

        # Low alignment score
        if component_scores.get('requirements_alignment', 1.0) < 0.6:
            risks.append("Low requirements alignment may indicate incomplete implementation")

        # Poor testing
        if component_scores.get('testing_completeness', 1.0) < 0.5:
            risks.append("Inadequate testing coverage increases regression risk")

        # Documentation issues
        if component_scores.get('documentation_consistency', 1.0) < 0.6:
            risks.append("Documentation inconsistencies may cause maintenance issues")

        # Security concerns
        if component_scores.get('security_compliance', 1.0) < 0.7:
            risks.append("Security compliance concerns require additional review")

        # Cross-reference gaps
        gaps = cross_reference_results.get('identified_gaps', [])
        if len(gaps) > 2:
            risks.append(f"Multiple implementation gaps identified ({len(gaps)} total)")

        return risks

    def _identify_critical_concerns(
        self,
        component_scores: Dict[str, float],
        cross_reference_results: Dict[str, Any]
    ) -> List[str]:
        """Identify critical concerns that require immediate attention."""
        concerns = []

        # Critical alignment issues
        if component_scores.get('requirements_alignment', 1.0) < 0.4:
            concerns.append("CRITICAL: Major requirements not implemented")

        # No testing
        if component_scores.get('testing_completeness', 1.0) < 0.3:
            concerns.append("CRITICAL: No testing coverage detected")

        # Security violations
        if component_scores.get('security_compliance', 1.0) < 0.4:
            concerns.append("CRITICAL: Potential security vulnerabilities")

        # Breaking changes without documentation
        consistency_issues = cross_reference_results.get('consistency_issues', [])
        if any('breaking' in issue.lower() for issue in consistency_issues):
            concerns.append("CRITICAL: Breaking changes lack migration documentation")

        return concerns

    def _identify_strengths(self, component_scores: Dict[str, float]) -> List[str]:
        """Identify strengths in the PR implementation."""
        strengths = []

        for component, score in component_scores.items():
            if score >= 0.8:
                component_name = component.replace('_', ' ').title()
                strengths.append(f"Excellent {component_name} ({score:.1%})")
            elif score >= 0.7:
                component_name = component.replace('_', ' ').title()
                strengths.append(f"Good {component_name} ({score:.1%})")

        return strengths

    def _identify_improvement_areas(self, component_scores: Dict[str, float]) -> List[str]:
        """Identify areas that need improvement."""
        improvements = []

        for component, score in component_scores.items():
            if score < 0.6:
                component_name = component.replace('_', ' ').title()
                improvements.append(f"Improve {component_name} (currently {score:.1%})")
            elif score < 0.7:
                component_name = component.replace('_', ' ').title()
                improvements.append(f"Enhance {component_name} (currently {score:.1%})")

        return improvements

    def _generate_rationale(
        self,
        overall_score: float,
        component_scores: Dict[str, float],
        risk_factors: List[str]
    ) -> str:
        """Generate human-readable rationale for the confidence score."""
        confidence_level = self._determine_confidence_level(overall_score)

        rationale_parts = [
            f"Overall confidence score of {overall_score:.1%} indicates "
        ]

        if confidence_level == ConfidenceLevel.HIGH:
            rationale_parts.append("high confidence in the PR implementation. ")
        elif confidence_level == ConfidenceLevel.MEDIUM:
            rationale_parts.append("moderate confidence with some areas needing attention. ")
        elif confidence_level == ConfidenceLevel.LOW:
            rationale_parts.append("low confidence requiring significant review. ")
        else:
            rationale_parts.append("critical concerns requiring immediate attention. ")

        # Add component breakdown
        top_components = sorted(component_scores.items(), key=lambda x: x[1], reverse=True)
        rationale_parts.append("Key factors: ")
        rationale_parts.append(", ".join([
            f"{comp.replace('_', ' ')} ({score:.1%})"
            for comp, score in top_components[:3]
        ]))
        rationale_parts.append(". ")

        # Add risk assessment
        if risk_factors:
            rationale_parts.append(f"Identified {len(risk_factors)} risk factor(s) to consider.")

        return "".join(rationale_parts)


# Create singleton instance
pr_confidence_scorer = PRConfidenceScorer()
