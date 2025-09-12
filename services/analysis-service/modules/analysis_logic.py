"""Analysis logic and detection functions for the Analysis Service.

This module contains all the core analysis and detection functionality,
extracted from the main analysis service to improve maintainability.
"""

import re
from typing import List, Dict, Any, Set
from services.shared.models import Document, Finding

# Import shared utilities for consistency across analysis modules
from .shared_utils import (
    handle_analysis_error,
    build_analysis_context,
    validate_analysis_targets,
    get_drift_overlap_threshold,
    get_critical_score,
    get_high_priority_score,
    get_medium_priority_score
)


# Constants for analysis thresholds and scoring (using shared configuration)
DRIFT_OVERLAP_THRESHOLD = get_drift_overlap_threshold()
CRITICAL_SCORE = get_critical_score()
HIGH_PRIORITY_SCORE = get_high_priority_score()
MEDIUM_PRIORITY_SCORE = get_medium_priority_score()

# Finding type constants
FINDING_TYPE_DRIFT = "drift"
FINDING_TYPE_MISSING_DOC = "missing_doc"
FINDING_TYPE_MISSING_IMPL = "missing_impl"

# Severity constants
SEVERITY_CRITICAL = "critical"
SEVERITY_HIGH = "high"
SEVERITY_MEDIUM = "medium"
SEVERITY_LOW = "low"


def _create_finding(
    finding_id: str,
    finding_type: str,
    title: str,
    description: str,
    severity: str,
    source_refs: List[Dict[str, str]],
    evidence: List[str],
    suggestion: str,
    score: int,
    rationale: str
) -> Finding:
    """Create a standardized Finding object with consistent structure."""
    return Finding(
        id=finding_id,
        type=finding_type,
        title=title,
        description=description,
        severity=severity,
        source_refs=source_refs,
        evidence=evidence,
        suggestion=suggestion,
        correlation_id=finding_id,
        score=score,
        rationale=rationale
    )


def _extract_text_overlap(text1: str, text2: str) -> float:
    """Calculate text overlap ratio between two texts with performance optimizations."""
    if not text1 or not text2:
        return 0.0

    # Performance optimization: Early exit for very different lengths
    len_ratio = len(text1) / len(text2) if text2 else 0
    if len_ratio < 0.1 or len_ratio > 10:
        return 0.0

    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())

    if not words1 or not words2:
        return 0.0

    # Performance optimization: Use smaller set for intersection
    if len(words1) > len(words2):
        words1, words2 = words2, words1

    intersection = len(words1 & words2)
    union = len(words1) + len(words2) - intersection  # More efficient than | operator

    return intersection / union if union > 0 else 0.0


def _extract_endpoints_from_docs(docs: List[Document]) -> Set[str]:
    """Extract API endpoints from documentation."""
    endpoints = set()

    for doc in docs:
        if not doc.content:
            continue

        # Find API endpoint patterns in documentation
        matches = re.findall(r'`(GET|POST|PUT|DELETE|PATCH)\s+(/[^`\s]+)`', doc.content)
        for method, path in matches:
            endpoints.add(f"{method} {path}")

    return endpoints


def _extract_endpoints_from_apis(apis: List[Dict[str, Any]]) -> Set[str]:
    """Extract API endpoints from API specifications."""
    endpoints = set()

    for api in apis:
        if not isinstance(api, dict) or "endpoints" not in api:
            continue

        for endpoint in api["endpoints"]:
            method = endpoint.get('method', 'GET')
            path = endpoint.get('path', '/')
            endpoints.add(f"{method} {path}")

    return endpoints


def detect_readme_drift(docs: List[Document]) -> List[Finding]:
    """Detect drift between README and other documentation with improved analysis and performance optimizations."""
    findings = []
    context = build_analysis_context("detect_readme_drift", doc_count=len(docs))

    try:
        if not docs:
            return findings

        # Performance optimization: Pre-filter and cache document properties
        valid_docs = [(d, d.title.lower() if d.title else "", d.content or "") for d in docs if d.content]

        # Separate READMEs from other documentation
        readmes = [(d, title, content) for d, title, content in valid_docs if "readme" in title]
        other_docs = [(d, title, content) for d, title, content in valid_docs if "readme" not in title]

        if not readmes or not other_docs:
            return findings

        # Performance optimization: Early exit for large datasets
        if len(readmes) * len(other_docs) > 1000:  # Limit computational complexity
            context["optimization"] = "early_exit_large_dataset"
            return findings

        for readme_doc, readme_title, readme_content in readmes:
            # Performance optimization: Pre-calculate word sets for README
            readme_words = set(readme_content.lower().split())

            for doc_doc, doc_title, doc_content in other_docs:
                # Performance optimization: Skip obviously different documents
                if abs(len(readme_content) - len(doc_content)) > len(readme_content) * 0.8:
                    continue

                # Calculate text overlap using optimized helper function
                overlap = _extract_text_overlap(readme_content, doc_content)

                # Check if overlap indicates potential drift
                if overlap < DRIFT_OVERLAP_THRESHOLD:
                    finding_id = f"drift:{readme_doc.id}:{doc_doc.id}"

                    findings.append(_create_finding(
                        finding_id=finding_id,
                        finding_type=FINDING_TYPE_DRIFT,
                        title="Documentation Drift Detected",
                        description=f"Low content overlap between {readme_title} and {doc_title}",
                        severity=SEVERITY_MEDIUM,
                        source_refs=[
                            {"id": readme_doc.id, "type": "document"},
                            {"id": doc_doc.id, "type": "document"}
                        ],
                        evidence=[f"Content overlap ratio: {overlap:.3f}"],
                        suggestion="Review and synchronize documentation to ensure consistency",
                        score=int(overlap * 100),
                        rationale=f"Low content overlap ({overlap:.3f}) suggests documentation drift requiring attention"
                    ))

        return findings

    except Exception as e:
        # Log error and return empty findings rather than failing completely
        handle_analysis_error("detect README drift", e, doc_count=len(docs), **context)
        return []


def detect_api_mismatches(docs: List[Document], apis: List[Dict[str, Any]]) -> List[Finding]:
    """Detect mismatches between API documentation and implementation with improved analysis."""
    findings = []
    context = build_analysis_context("detect_api_mismatches", docs_count=len(docs), apis_count=len(apis))

    try:
        if not docs and not apis:
            return findings

        # Extract endpoints using improved helper functions
        doc_endpoints = _extract_endpoints_from_docs(docs)
        api_endpoints = _extract_endpoints_from_apis(apis)

        # Find mismatches between documented and implemented endpoints
        undocumented = api_endpoints - doc_endpoints  # In API but not documented
        unimplemented = doc_endpoints - api_endpoints  # In docs but not implemented

        # Create findings for undocumented endpoints
        for endpoint in undocumented:
            findings.append(_create_finding(
                finding_id=f"undocumented:{endpoint}",
                finding_type=FINDING_TYPE_MISSING_DOC,
                title="Undocumented API Endpoint",
                description=f"API endpoint '{endpoint}' exists in implementation but lacks documentation",
                severity=SEVERITY_HIGH,
                source_refs=[{"id": endpoint, "type": "endpoint"}],
                evidence=[f"Endpoint {endpoint} found in API implementation but missing from documentation"],
                suggestion="Add comprehensive documentation for this endpoint including parameters and responses",
                score=CRITICAL_SCORE,
                rationale="Undocumented endpoints create maintenance burden and usability issues for API consumers"
            ))

        # Create findings for unimplemented endpoints
        for endpoint in unimplemented:
            findings.append(_create_finding(
                finding_id=f"unimplemented:{endpoint}",
                finding_type=FINDING_TYPE_MISSING_IMPL,
                title="Unimplemented Documented Endpoint",
                description=f"Documented endpoint '{endpoint}' lacks implementation",
                severity=SEVERITY_HIGH,
                source_refs=[{"id": endpoint, "type": "endpoint"}],
                evidence=[f"Endpoint {endpoint} documented but not found in API implementation"],
                suggestion="Implement the documented endpoint or remove it from documentation to avoid confusion",
                score=HIGH_PRIORITY_SCORE,
                rationale="Documentation promises functionality that doesn't exist, breaking developer expectations"
            ))

        return findings

    except Exception as e:
        # Log error and return empty findings rather than failing completely
        handle_analysis_error("detect API mismatches", e, docs_count=len(docs), apis_count=len(apis), **context)
        return []


def _count_by_attribute(findings: List[Finding], attribute: str) -> Dict[str, int]:
    """Count findings by a specific attribute."""
    counts = {}
    for finding in findings:
        value = getattr(finding, attribute, "unknown")
        counts[value] = counts.get(value, 0) + 1
    return counts

def _filter_by_severity(findings: List[Finding], severities: List[str]) -> List[Finding]:
    """Filter findings by severity levels."""
    return [f for f in findings if f.severity in severities]

def _calculate_health_score(findings: List[Finding]) -> int:
    """Calculate documentation health score based on findings."""
    high_priority_count = len(_filter_by_severity(findings, [SEVERITY_CRITICAL, SEVERITY_HIGH]))
    # Deduct 5 points per high-priority finding, minimum score of 0
    return max(0, 100 - (high_priority_count * 5))

def generate_summary_report(findings: List[Finding]) -> Dict[str, Any]:
    """Generate comprehensive summary report of findings with improved analysis."""
    context = build_analysis_context("generate_summary_report", total_findings=len(findings))

    try:
        if not findings:
            return {
                "total_findings": 0,
                "severity_breakdown": {},
                "type_breakdown": {},
                "critical_issues": 0,
                "high_priority": 0,
                "health_score": 100,
                "recommendations": ["Documentation appears healthy - no issues found"]
            }

        # Calculate various metrics
        severity_counts = _count_by_attribute(findings, "severity")
        type_counts = _count_by_attribute(findings, "type")

        critical_issues = _filter_by_severity(findings, [SEVERITY_CRITICAL])
        high_priority = _filter_by_severity(findings, [SEVERITY_CRITICAL, SEVERITY_HIGH])

        health_score = _calculate_health_score(findings)

        # Generate recommendations based on findings
        recommendations = []
        if critical_issues:
            recommendations.append("🚨 Review critical findings immediately")
        if high_priority:
            recommendations.append("⚠️ Address high-severity issues within 24 hours")
        if FINDING_TYPE_DRIFT in type_counts:
            recommendations.append("📝 Consider documentation synchronization to reduce drift")
        if not recommendations:
            recommendations.append("✅ Documentation appears healthy")

        return {
            "total_findings": len(findings),
            "severity_breakdown": severity_counts,
            "type_breakdown": type_counts,
            "critical_issues": len(critical_issues),
            "high_priority": len(high_priority),
            "health_score": health_score,
            "recommendations": recommendations
        }

    except Exception as e:
        # Return a minimal report on error rather than failing completely
        handle_analysis_error("generate summary report", e, total_findings=len(findings), **context)
        return {
            "total_findings": len(findings) if findings else 0,
            "severity_breakdown": {},
            "type_breakdown": {},
            "critical_issues": 0,
            "high_priority": 0,
            "health_score": 0,
            "recommendations": ["Error occurred during report generation"],
            "error": str(e)
        }


def _analyze_trends(findings: List[Finding]) -> Dict[str, Any]:
    """Analyze trends in findings to identify patterns."""
    if not findings:
        return {
            "increasing": [],
            "stable": [],
            "decreasing": [],
            "insights": ["No findings available for trend analysis"]
        }

    # Count findings by type for trend analysis
    type_counts = _count_by_attribute(findings, "type")

    # Identify trends (simplified - in real implementation would compare with historical data)
    drift_count = type_counts.get(FINDING_TYPE_DRIFT, 0)
    missing_doc_count = type_counts.get(FINDING_TYPE_MISSING_DOC, 0)
    missing_impl_count = type_counts.get(FINDING_TYPE_MISSING_IMPL, 0)

    # Determine trend categories based on relative frequencies
    increasing = []
    stable = []
    decreasing = []

    if drift_count > max(missing_doc_count, missing_impl_count):
        increasing.append(FINDING_TYPE_DRIFT)

    if missing_doc_count > 0:
        stable.append(FINDING_TYPE_MISSING_DOC)

    if missing_impl_count < missing_doc_count:
        decreasing.append(FINDING_TYPE_MISSING_IMPL)

    # Generate insights based on analysis
    insights = []
    if drift_count > 0:
        insights.append("📊 Drift detection is actively identifying documentation inconsistencies")
    if missing_doc_count > 0:
        insights.append("📝 API documentation gaps require ongoing attention")
    if missing_impl_count > 0:
        insights.append("🔧 Implementation gaps suggest areas for development focus")
    if not insights:
        insights.append("✅ No significant trends identified in current findings")

    return {
        "increasing": increasing,
        "stable": stable,
        "decreasing": decreasing,
        "insights": insights
    }

def generate_trends_report(findings: List[Finding], time_window: str = "7d") -> Dict[str, Any]:
    """Generate comprehensive trends report showing patterns over time."""
    context = build_analysis_context("generate_trends_report", total_findings=len(findings), time_window=time_window)

    try:
        if not findings:
            return {
                "time_window": time_window,
                "total_findings": 0,
                "severity_trends": {"increasing": [], "stable": [], "decreasing": []},
                "type_distribution": {},
                "insights": ["No findings available for trend analysis"]
            }

        # Analyze trends and patterns
        trends_analysis = _analyze_trends(findings)
        type_distribution = _count_by_attribute(findings, "type")

        return {
            "time_window": time_window,
            "total_findings": len(findings),
            "severity_trends": {
                "increasing": trends_analysis["increasing"],
                "stable": trends_analysis["stable"],
                "decreasing": trends_analysis["decreasing"]
            },
            "type_distribution": type_distribution,
            "insights": trends_analysis["insights"],
            "recommendations": [
                "Monitor increasing trend categories closely",
                "Address stable issues to prevent escalation",
                "Track decreasing trends as indicators of improvement"
            ]
        }

    except Exception as e:
        # Return a minimal report on error rather than failing completely
        handle_analysis_error("generate trends report", e, total_findings=len(findings), time_window=time_window, **context)
        return {
            "time_window": time_window,
            "total_findings": len(findings) if findings else 0,
            "severity_trends": {"increasing": [], "stable": [], "decreasing": []},
            "type_distribution": {},
            "insights": ["Error occurred during trend analysis"],
            "recommendations": ["Unable to generate trend analysis due to error"],
            "error": str(e)
        }
