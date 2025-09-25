"""Report generation services for analysis results.

Provides functions for generating various types of reports and health assessments.
"""


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
            balance_ratio = (
                min(metrics.get("lines_added", 0), metrics.get("lines_removed", 0))
                / total_changes
            )
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
        structural_score = max(
            0.0, 1.0 - (len(structural_analysis["structural_risks"]) * 0.2)
        )
    scores.append((structural_score, 0.1))

    # Calculate weighted average
    if not scores:
        return 0.5

    total_weight = sum(weight for _, weight in scores)
    if total_weight == 0:
        return 0.5


def determine_pr_risk_level(health_score: float) -> str:
    """Determine risk level based on health score."""
    if health_score >= 0.8:
        return "low"
    elif health_score >= 0.6:
        return "medium"
    else:
        return "high"


def generate_pr_recommendations(pr_report: dict) -> list:
    """Generate high-level recommendations for the pull request."""
    recommendations = []

    pr_report.get("health_score", 0.5)
    risk_level = pr_report.get("risk_level", "medium")

    if risk_level == "high":
        recommendations.append(
            "🚨 High-risk changes detected - consider breaking into smaller PRs"
        )
        recommendations.append(
            "📋 Schedule thorough code review with senior developers"
        )

    elif risk_level == "medium":
        recommendations.append("⚠️ Medium-risk changes - ensure adequate test coverage")
        recommendations.append("👥 Consider pair programming for complex sections")

    # Specific recommendations based on analysis
    code_analysis = pr_report.get("code_analysis", {})

    if (
        code_analysis.get("change_metrics", {}).get("lines_added", 0)
        > config.limits.max_lines_added_threshold
    ):
        recommendations.append(
            "📊 Large PR detected - consider splitting into smaller, focused changes"
        )

    if code_analysis.get("file_types", {}).get("test", 0) == 0:
        recommendations.append("🧪 Consider adding tests for the changes introduced")

    # Commit analysis recommendations
    commit_analysis = pr_report.get("commit_analysis", {})
    if commit_analysis.get("message_quality", {}).get("poor_messages", 0) > 0:
        recommendations.append(
            "✍️ Improve commit message quality for better project history"
        )

    # Quality recommendations
    quality_analysis = pr_report.get("quality_analysis", {})
    if quality_analysis.get("quality_score", 1.0) < 0.7:
        recommendations.append("🔧 Address code quality issues before merging")

    return recommendations


def generate_analysis_markdown_report(report_data: dict) -> str:
    """Generate comprehensive Markdown report from analysis data."""
    md_lines = []

    # Header
    md_lines.append("# 📊 Comprehensive Analysis Report")
    md_lines.append("")
    md_lines.append(f"**Simulation ID:** {report_data['simulation_id']}")
    md_lines.append(f"**Report ID:** {report_data['report_id']}")
    md_lines.append(f"**Generated:** {report_data['timestamp']}")
    md_lines.append(f"**Documents Analyzed:** {report_data['documents_analyzed']}")
    md_lines.append("")

    # Summary section
    summary = report_data["summary"]
    md_lines.append("## 📈 Executive Summary")
    md_lines.append("")
    md_lines.append(f"- **Total Analyses:** {summary['total_analyses']}")
    md_lines.append(f"- **Analysis Types:** {', '.join(summary['analysis_types'])}")
    md_lines.append(f"- **Documents with Issues:** {summary['documents_with_issues']}")
    md_lines.append(
        f"- **Average Quality Score:** {summary['average_quality_score']:.2f}"
    )
    md_lines.append(f"- **Total Issues Found:** {summary['total_issues_found']}")
    md_lines.append("")

    # Overall quality indicator
    avg_score = summary["average_quality_score"]
    if avg_score >= 0.8:
        quality_indicator = (
            "🟢 **High Quality** - Documents are well-structured and clear"
        )
    elif avg_score >= 0.6:
        quality_indicator = "🟡 **Medium Quality** - Documents need some improvements"
    else:
        quality_indicator = (
            "🔴 **Low Quality** - Documents require significant attention"
        )

    md_lines.append(f"### Quality Assessment: {quality_indicator}")
    md_lines.append("")

    # Analysis Results section
    md_lines.append("## 🔍 Detailed Analysis Results")
    md_lines.append("")

    for i, result in enumerate(report_data["analysis_results"], 1):
        quality_score = result.get("quality_score", 0)
        issues_found = result.get("issues_found", 0)

        # Quality score emoji


def get_type_icon(doc_type: str) -> str:
    """Get appropriate icon for document type."""
    icons = {
        "confluence": "📄",
        "jira": "🎫",
        "pull_request": "🔄",
        "pr": "🔄",
        "unknown": "📋",
    }
    return icons.get(doc_type.lower(), "📋")


def format_timestamp(timestamp: str) -> str:
    """Format timestamp for display."""
    if not timestamp:
        return "N/A"

    try:
        # Try to parse and format the timestamp
        if "T" in timestamp:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        else:
            return timestamp
    except ValueError:
        return timestamp


def format_confluence_content(content: str) -> List[str]:
    """Format Confluence page content."""
    lines = []

    # Split into paragraphs and format
    paragraphs = content.split("\n\n")
    for para in paragraphs:
        if para.strip():
            # Basic formatting preservation
            formatted_para = para.replace("**", "**").replace("*", "*")
            lines.append(formatted_para)
            lines.append("")

    return lines


def format_jira_content(content: str) -> List[str]:
    """Format Jira ticket content."""
    lines = []

    # Jira tickets often have structured content
    if content.strip():
        # Preserve basic formatting
        formatted_content = content.replace("\n", "\n> ")
        lines.append(f"> {formatted_content}")
        lines.append("")

    return lines


def format_pr_content(content: str) -> List[str]:
    """Format Pull Request content."""
    lines = []

    # PR descriptions often contain code and structured content
