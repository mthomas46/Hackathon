"""Reporting services for analysis results.

Provides functions for generating various types of reports and health assessments.
"""

from datetime import datetime
from typing import Any, Dict, List

from services.shared.infrastructure.config import load_service_config

config = load_service_config()


def calculate_pr_health_score(
    code_analysis: dict,
    commit_analysis: dict,
    structural_analysis: dict,
    quality_analysis: dict,
) -> float:
    """Calculate overall health score for the pull request."""
    scores = []

    # Code analysis score (40% weight)
    if "change_metrics" in code_analysis:
        metrics = code_analysis["change_metrics"]
        total_changes = metrics.get("lines_added", 0) + metrics.get("lines_removed", 0)

        # Prefer balanced changes over large additions/deletions
        if total_changes > 0:
            balance_ratio = min(metrics.get("lines_added", 0), metrics.get("lines_removed", 0)) / total_changes
            code_score = min(1.0, balance_ratio * 2)  # Reward balanced changes
            scores.append((code_score, 0.4))

    # Commit quality score (20% weight)
    if "message_quality" in commit_analysis:
        quality = commit_analysis["message_quality"]
        total_messages = sum(quality.values())
        if total_messages > 0:
            good_ratio = quality.get("good_messages", 0) / total_messages
            commit_score = good_ratio
            scores.append((commit_score, 0.2))

    # Quality score (config.limits.quality_score_weight% weight)
    quality_score = quality_analysis.get("quality_score", 0.5)
    scores.append((quality_score, config.limits.quality_score_weight / 100.0))

    # Structural risk penalty (10% weight)
    structural_score = 1.0
    if structural_analysis.get("structural_risks"):
        structural_score = max(0.0, 1.0 - (len(structural_analysis["structural_risks"]) * 0.2))
    scores.append((structural_score, 0.1))

    # Calculate weighted average
    if not scores:
        return 0.5

    total_weight = sum(weight for _, weight in scores)
    weighted_sum = sum(score * weight for score, weight in scores)

    return weighted_sum / total_weight if total_weight > 0 else 0.5


def determine_pr_risk_level(health_score: float) -> str:
    """Determine risk level based on health score."""
    if health_score >= 0.8:
        return "low"
    elif health_score >= 0.6:
        return "medium"
    elif health_score >= 0.4:
        return "high"
    else:
        return "critical"


def generate_pr_recommendations(pr_report: dict) -> list:
    """Generate recommendations based on PR analysis."""
    recommendations = []

    health_score = pr_report.get("health_score", 0.5)
    risk_level = pr_report.get("risk_level", "medium")

    if risk_level == "critical":
        recommendations.append("🚨 CRITICAL: This PR has severe issues that should be addressed immediately")
    elif risk_level == "high":
        recommendations.append("⚠️ HIGH RISK: This PR needs significant improvements before merge")
    elif risk_level == "medium":
        recommendations.append("📋 MEDIUM RISK: Consider the suggested improvements")

    # Code quality recommendations
    code_analysis = pr_report.get("code_analysis", {})
    if code_analysis.get("complex_functions"):
        recommendations.append("🔧 Refactor complex functions into smaller, focused methods")

    # Commit quality recommendations
    commit_analysis = pr_report.get("commit_analysis", {})
    if commit_analysis.get("issues"):
        recommendations.append("📝 Improve commit message quality and consistency")

    return recommendations


def generate_analysis_markdown_report(report_data: dict) -> str:
    """Generate a comprehensive markdown report."""
    report = ["# Analysis Report\n"]

    # Health score
    health_score = report_data.get("health_score", 0)
    risk_level = report_data.get("risk_level", "unknown")

    report.append(f"## Health Score: {health_score:.2f} ({risk_level.upper()})\n")

    # Code analysis
    if "code_analysis" in report_data:
        report.append("## Code Analysis\n")
        code = report_data["code_analysis"]
        if "change_metrics" in code:
            metrics = code["change_metrics"]
            report.append(f"- Lines added: {metrics.get('lines_added', 0)}")
            report.append(f"- Lines removed: {metrics.get('lines_removed', 0)}")
            report.append(f"- Files changed: {metrics.get('files_changed', 0)}")

    # Commit analysis
    if "commit_analysis" in report_data:
        report.append("\n## Commit Analysis\n")
        commit = report_data["commit_analysis"]
        quality = commit.get("message_quality", {})
        report.append(f"- Good messages: {quality.get('good_messages', 0)}")
        report.append(f"- Needs improvement: {quality.get('needs_improvement', 0)}")
        report.append(f"- Poor messages: {quality.get('poor_messages', 0)}")

    return "\n".join(report)


def generate_document_section(doc: Dict[str, Any], req) -> List[str]:
    """Generate document section for reporting."""
    sections = []

    # Document header
    sections.append(f"### Document: {doc.get('filename', 'Unknown')}")

    # Basic info
    if "analysis" in doc:
        analysis = doc["analysis"]
        sections.append(f"- **Type**: {analysis.get('file_type', 'Unknown')}")
        sections.append(f"- **Lines**: {analysis.get('lines_count', 0)}")

        # Issues summary
        issues = analysis.get("issues", [])
        if issues:
            sections.append(f"- **Issues**: {len(issues)} found")
            for issue in issues[:3]:  # Show first 3 issues
                sections.append(f"  - {issue}")

    return sections


def get_type_icon(doc_type: str) -> str:
    """Get icon for document type."""
    icons = {
        "python": "🐍",
        "javascript": "🟨",
        "typescript": "🔷",
        "java": "☕",
        "markdown": "📝",
        "json": "📄",
        "yaml": "📋",
    }
    return icons.get(doc_type.lower(), "📄")


def format_timestamp(timestamp: str) -> str:
    """Format timestamp for display."""
    try:
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    except (ValueError, AttributeError):
        return timestamp


def format_confluence_content(content: str) -> List[str]:
    """Format content for Confluence display."""
    lines = content.split("\n")
    formatted = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Convert markdown-style headers
        if line.startswith("# "):
            formatted.append(f"h1. {line[2:]}")
        elif line.startswith("## "):
            formatted.append(f"h2. {line[3:]}")
        elif line.startswith("### "):
            formatted.append(f"h3. {line[4:]}")
        else:
            formatted.append(line)

    return formatted


def format_jira_content(content: str) -> List[str]:
    """Format content for Jira display."""
    lines = content.split("\n")
    formatted = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Convert to Jira markup
        if line.startswith("# "):
            formatted.append(f"*h1.* {line[2:]}")
        elif line.startswith("## "):
            formatted.append(f"*h2.* {line[3:]}")
        elif line.startswith("### "):
            formatted.append(f"*h3.* {line[4:]}")
        elif line.startswith("- ") or line.startswith("* "):
            formatted.append(f"* {line[2:]}")
        else:
            formatted.append(line)

    return formatted


def format_pr_content(content: str) -> List[str]:
    """Format content for PR comments."""
    lines = content.split("\n")
    formatted = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Keep markdown formatting for PRs
        formatted.append(line)

    return formatted


def format_generic_content(content: str) -> List[str]:
    """Format content for generic display."""
    return content.split("\n")
