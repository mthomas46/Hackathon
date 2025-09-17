"""
PR Cross-Reference Analysis Module

Advanced cross-reference analysis between PR, Jira, and Confluence data
to identify alignment, gaps, and consistency issues.
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class AlignmentStatus(Enum):
    FULLY_ALIGNED = "fully_aligned"
    PARTIALLY_ALIGNED = "partially_aligned"
    MISALIGNED = "misaligned"
    NOT_IMPLEMENTED = "not_implemented"

class ConsistencyLevel(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    CRITICAL = "critical"

@dataclass
class CrossReferenceResult:
    """Result of cross-reference analysis between PR and requirements."""
    overall_alignment_score: float
    requirement_alignment: Dict[str, Dict[str, Any]]
    documentation_consistency: Dict[str, Dict[str, Any]]
    identified_gaps: List[str]
    consistency_issues: List[str]
    recommendations: List[str]
    risk_assessment: str

class PRCrossReferenceAnalyzer:
    """Analyzes cross-references between PR, Jira, and Confluence data."""

    def __init__(self):
        self.requirement_patterns = {
            'authentication': [
                r'auth', r'login', r'oauth', r'token', r'security', r'credential'
            ],
            'api_endpoints': [
                r'endpoint', r'api', r'rest', r'route', r'handler', r'controller'
            ],
            'testing': [
                r'test', r'spec', r'assert', r'validate', r'coverage', r'unit'
            ],
            'documentation': [
                r'doc', r'readme', r'comment', r'javadoc', r'swagger', r'api_doc'
            ],
            'security': [
                r'security', r'encrypt', r'hash', r'sanitize', r'validate', r'xss'
            ]
        }

    def analyze_pr_requirements_alignment(
        self,
        pr_data: Dict[str, Any],
        jira_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze alignment between PR implementation and Jira requirements.

        Returns:
            Dict containing alignment analysis with scores and gaps
        """
        pr_content = self._extract_pr_content(pr_data)
        jira_requirements = self._extract_jira_requirements(jira_data)

        alignment_results = {}

        for req_category, req_details in jira_requirements.items():
            alignment_results[req_category] = self._analyze_requirement_category(
                req_category, req_details, pr_content
            )

        # Calculate overall alignment score
        total_weight = sum(result.get('weight', 1) for result in alignment_results.values())
        weighted_score = sum(
            result.get('alignment_score', 0) * result.get('weight', 1)
            for result in alignment_results.values()
        )

        overall_score = weighted_score / total_weight if total_weight > 0 else 0

        # Identify gaps
        gaps = []
        for category, result in alignment_results.items():
            if result.get('status') == AlignmentStatus.NOT_IMPLEMENTED.value:
                gaps.append(f"Requirement not implemented: {category}")
            elif result.get('status') == AlignmentStatus.PARTIALLY_ALIGNED.value:
                gaps.append(f"Partial implementation: {category} - {result.get('missing_aspects', [])}")

        return {
            'overall_score': overall_score,
            'category_alignments': alignment_results,
            'gaps': gaps,
            'recommendations': self._generate_alignment_recommendations(alignment_results)
        }

    def analyze_documentation_consistency(
        self,
        pr_data: Dict[str, Any],
        confluence_docs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze consistency between PR changes and existing documentation.

        Returns:
            Dict containing consistency analysis with issues and recommendations
        """
        pr_changes = self._extract_pr_changes(pr_data)
        consistency_results = {}

        for doc in confluence_docs:
            doc_id = doc.get('id', 'unknown')
            consistency_results[doc_id] = self._analyze_doc_consistency(
                doc, pr_changes
            )

        # Calculate overall consistency score
        if consistency_results:
            total_docs = len(consistency_results)
            consistency_scores = [
                result.get('consistency_score', 0.5)
                for result in consistency_results.values()
            ]
            overall_score = sum(consistency_scores) / total_docs
        else:
            overall_score = 0.5  # Neutral if no docs to compare

        # Identify consistency issues
        issues = []
        for doc_id, result in consistency_results.items():
            if result.get('issues'):
                issues.extend(result['issues'])

        return {
            'overall_score': overall_score,
            'document_consistency': consistency_results,
            'issues': issues,
            'recommendations': self._generate_consistency_recommendations(consistency_results)
        }

    def perform_comprehensive_cross_reference(
        self,
        pr_data: Dict[str, Any],
        jira_data: Dict[str, Any],
        confluence_docs: List[Dict[str, Any]]
    ) -> CrossReferenceResult:
        """
        Perform comprehensive cross-reference analysis across all data sources.

        Returns:
            CrossReferenceResult with complete analysis
        """
        # Analyze PR-Jira alignment
        alignment_analysis = self.analyze_pr_requirements_alignment(pr_data, jira_data)

        # Analyze PR-Documentation consistency
        consistency_analysis = self.analyze_documentation_consistency(pr_data, confluence_docs)

        # Calculate overall cross-reference score
        alignment_weight = 0.6
        consistency_weight = 0.4
        overall_score = (
            alignment_analysis['overall_score'] * alignment_weight +
            consistency_analysis['overall_score'] * consistency_weight
        )

        # Combine gaps and issues
        all_gaps = alignment_analysis.get('gaps', [])
        all_issues = consistency_analysis.get('issues', [])

        # Combine recommendations
        all_recommendations = []
        all_recommendations.extend(alignment_analysis.get('recommendations', []))
        all_recommendations.extend(consistency_analysis.get('recommendations', []))

        # Assess overall risk
        risk_level = self._assess_overall_risk(overall_score, all_gaps, all_issues)

        return CrossReferenceResult(
            overall_alignment_score=overall_score,
            requirement_alignment=alignment_analysis.get('category_alignments', {}),
            documentation_consistency=consistency_analysis.get('document_consistency', {}),
            identified_gaps=all_gaps,
            consistency_issues=all_issues,
            recommendations=all_recommendations,
            risk_assessment=risk_level
        )

    def _extract_pr_content(self, pr_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract relevant content from PR data."""
        return {
            'title': pr_data.get('title', ''),
            'description': pr_data.get('description', ''),
            'files_changed': pr_data.get('files_changed', []),
            'diff_summary': pr_data.get('diff_summary', ''),
            'jira_ticket': pr_data.get('jira_ticket', '')
        }

    def _extract_jira_requirements(self, jira_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract requirements from Jira data."""
        requirements = {}

        # Extract from acceptance criteria
        acceptance_criteria = jira_data.get('acceptance_criteria', [])
        for i, criterion in enumerate(acceptance_criteria):
            category = self._categorize_requirement(criterion)
            if category not in requirements:
                requirements[category] = []
            requirements[category].append({
                'text': criterion,
                'type': 'acceptance_criterion',
                'priority': 'high' if 'must' in criterion.lower() else 'medium'
            })

        # Extract from description
        description = jira_data.get('description', '')
        desc_requirements = self._extract_requirements_from_text(description)
        for req in desc_requirements:
            category = self._categorize_requirement(req)
            if category not in requirements:
                requirements[category] = []
            requirements[category].append({
                'text': req,
                'type': 'description_requirement',
                'priority': 'medium'
            })

        return requirements

    def _extract_pr_changes(self, pr_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract changes and modifications from PR data."""
        return {
            'files_modified': pr_data.get('files_changed', []),
            'description': pr_data.get('description', ''),
            'diff_summary': pr_data.get('diff_summary', ''),
            'title': pr_data.get('title', '')
        }

    def _analyze_requirement_category(
        self,
        category: str,
        requirements: List[Dict[str, Any]],
        pr_content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze alignment for a specific requirement category."""
        pr_text = ' '.join([
            pr_content.get('title', ''),
            pr_content.get('description', ''),
            ' '.join(pr_content.get('files_changed', [])),
            pr_content.get('diff_summary', '')
        ]).lower()

        implemented_count = 0
        partial_count = 0
        missing_aspects = []

        for req in requirements:
            req_text = req.get('text', '').lower()
            req_keywords = self.requirement_patterns.get(category, [])

            # Check if requirement is addressed in PR
            if any(keyword in req_text for keyword in req_keywords):
                # Check if implementation evidence exists in PR
                if any(keyword in pr_text for keyword in req_keywords):
                    implemented_count += 1
                else:
                    partial_count += 1
                    missing_aspects.append(f"Missing implementation for: {req['text'][:50]}...")

        total_reqs = len(requirements)
        if total_reqs == 0:
            return {
                'status': AlignmentStatus.NOT_IMPLEMENTED.value,
                'alignment_score': 0.0,
                'weight': 1,
                'missing_aspects': []
            }

        # Calculate alignment score
        alignment_score = (implemented_count + partial_count * 0.5) / total_reqs

        if alignment_score >= 0.9:
            status = AlignmentStatus.FULLY_ALIGNED.value
        elif alignment_score >= 0.5:
            status = AlignmentStatus.PARTIALLY_ALIGNED.value
        elif alignment_score > 0:
            status = AlignmentStatus.MISALIGNED.value
        else:
            status = AlignmentStatus.NOT_IMPLEMENTED.value

        return {
            'status': status,
            'alignment_score': alignment_score,
            'weight': 1,
            'implemented_count': implemented_count,
            'partial_count': partial_count,
            'total_requirements': total_reqs,
            'missing_aspects': missing_aspects
        }

    def _analyze_doc_consistency(
        self,
        doc: Dict[str, Any],
        pr_changes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze consistency between a document and PR changes."""
        doc_content = doc.get('content', '').lower()
        pr_files = [f.lower() for f in pr_changes.get('files_modified', [])]

        consistency_score = 0.8  # Default good consistency
        issues = []

        # Check for API endpoint changes without documentation updates
        api_files = [f for f in pr_files if any(ext in f for ext in ['.py', '.js', '.java', '.go'])]
        if api_files and 'api' in doc_content:
            if not any(term in doc_content for term in ['endpoint', 'route', 'handler']):
                consistency_score -= 0.2
                issues.append("API changes detected but documentation may not reflect new endpoints")

        # Check for authentication changes
        auth_files = [f for f in pr_files if 'auth' in f]
        if auth_files and 'authentication' in doc_content:
            if not any(term in doc_content for term in ['oauth', 'token', 'login']):
                consistency_score -= 0.15
                issues.append("Authentication changes detected but security documentation may be outdated")

        # Check for breaking changes
        if 'breaking' in pr_changes.get('description', '').lower():
            if not any(term in doc_content for term in ['breaking', 'deprecated', 'migration']):
                consistency_score -= 0.25
                issues.append("Breaking changes detected but migration documentation may be missing")

        return {
            'consistency_score': max(0.0, min(1.0, consistency_score)),
            'issues': issues,
            'doc_id': doc.get('id'),
            'doc_title': doc.get('title')
        }

    def _categorize_requirement(self, requirement_text: str) -> str:
        """Categorize a requirement based on its content."""
        text_lower = requirement_text.lower()

        for category, patterns in self.requirement_patterns.items():
            if any(pattern in text_lower for pattern in patterns):
                return category

        return 'general'

    def _extract_requirements_from_text(self, text: str) -> List[str]:
        """Extract requirement statements from text."""
        # Simple extraction based on common requirement patterns
        sentences = re.split(r'[.!?]+', text)
        requirements = []

        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 10:  # Skip very short sentences
                continue

            # Look for requirement indicators
            if any(indicator in sentence.lower() for indicator in [
                'must', 'should', 'need to', 'required', 'implement',
                'add', 'create', 'support', 'provide', 'ensure'
            ]):
                requirements.append(sentence)

        return requirements

    def _generate_alignment_recommendations(self, alignment_results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on alignment analysis."""
        recommendations = []

        for category, result in alignment_results.items():
            status = result.get('status')
            missing_aspects = result.get('missing_aspects', [])

            if status == AlignmentStatus.NOT_IMPLEMENTED.value:
                recommendations.append(f"Implement missing {category} requirements")
            elif status == AlignmentStatus.PARTIALLY_ALIGNED.value:
                if missing_aspects:
                    recommendations.append(f"Complete partial {category} implementation: {len(missing_aspects)} aspects remaining")
            elif result.get('alignment_score', 0) < 0.8:
                recommendations.append(f"Review and improve {category} implementation quality")

        if not recommendations:
            recommendations.append("All requirements appear to be well-aligned with implementation")

        return recommendations

    def _generate_consistency_recommendations(self, consistency_results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on consistency analysis."""
        recommendations = []

        for doc_id, result in consistency_results.items():
            issues = result.get('issues', [])
            score = result.get('consistency_score', 1.0)

            if score < 0.7:
                recommendations.append(f"Update documentation '{result.get('doc_title', doc_id)}' to address {len(issues)} consistency issues")
            elif issues:
                recommendations.append(f"Review documentation '{result.get('doc_title', doc_id)}' for potential updates")

        if not recommendations:
            recommendations.append("Documentation appears consistent with implementation changes")

        return recommendations

    def _assess_overall_risk(self, overall_score: float, gaps: List[str], issues: List[str]) -> str:
        """Assess overall risk level based on analysis results."""
        risk_factors = len(gaps) + len(issues)

        if overall_score >= 0.8 and risk_factors <= 1:
            return "low"
        elif overall_score >= 0.6 and risk_factors <= 3:
            return "medium"
        else:
            return "high"


# Create singleton instance
pr_cross_reference_analyzer = PRCrossReferenceAnalyzer()
