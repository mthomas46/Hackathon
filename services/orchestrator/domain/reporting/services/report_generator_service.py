"""Report Generator Service Domain Service"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from ..value_objects.pr_confidence_report import PRConfidenceReport
from ..value_objects.report_format import ReportFormat
from ..value_objects.report_type import ReportType
from ..value_objects.confidence_level import ConfidenceLevel
from ..value_objects.approval_recommendation import ApprovalRecommendation


class ReportGeneratorService:
    """Domain service for generating various types of reports."""

    def __init__(self):
        """Initialize report generator service."""
        self._templates = self._load_templates()

    def _load_templates(self) -> Dict[str, str]:
        """Load report templates."""
        # In a real implementation, these would be loaded from files
        return {
            'html_template': """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .score {{ font-size: 48px; font-weight: bold; color: #007bff; }}
        .section {{ margin-bottom: 20px; }}
        .metric {{ display: flex; justify-content: space-between; padding: 10px; border: 1px solid #ddd; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{title}</h1>
            <p>Generated on {timestamp}</p>
        </div>
        <div class="content">
            <section class="confidence-section">
                <h2>Confidence Analysis</h2>
                <div class="score">{confidence_percentage:.1f}%</div>
                <div>Level: {confidence_level}</div>
                <div>Recommendation: {approval_recommendation}</div>
                <div>Risk: {risk_assessment}</div>
            </section>

            <section class="components-section">
                <h2>Component Scores</h2>
                {component_scores_html}
            </section>

            <section class="gaps-section">
                <h2>Detected Gaps ({gap_count})</h2>
                {gaps_html}
            </section>

            <section class="recommendations-section">
                <h2>Recommendations</h2>
                <ul>
                {recommendations_html}
                </ul>
            </section>
        </div>
    </div>
</body>
</html>
"""
        }

    def generate_pr_confidence_report(
        self,
        workflow_id: str,
        pr_id: str,
        confidence_score: float,
        component_scores: Dict[str, float],
        cross_reference_results: Dict[str, Any],
        detected_gaps: List[Dict[str, Any]],
        recommendations: List[str],
        critical_concerns: List[str],
        strengths: List[str],
        improvement_areas: List[str],
        analysis_duration: float,
        jira_ticket: Optional[str] = None,
        ai_provider: str = "local_llm"
    ) -> PRConfidenceReport:
        """
        Generate a comprehensive PR confidence analysis report.

        Args:
            workflow_id: Unique workflow identifier
            pr_id: Pull request identifier
            confidence_score: Overall confidence score (0.0 to 1.0)
            component_scores: Scores for individual analysis components
            cross_reference_results: Cross-reference analysis results
            detected_gaps: List of detected gaps
            recommendations: List of recommendations
            critical_concerns: List of critical concerns
            strengths: List of strengths identified
            improvement_areas: List of improvement areas
            analysis_duration: Analysis duration in seconds
            jira_ticket: Optional Jira ticket reference
            ai_provider: AI provider used for analysis

        Returns:
            PRConfidenceReport: Complete confidence analysis report
        """
        # Determine confidence level from score
        confidence_level = ConfidenceLevel.from_score(confidence_score)

        # Determine approval recommendation based on confidence level and gaps
        blocking_gaps = [gap for gap in detected_gaps if gap.get('blocking_approval', False)]
        has_critical_concerns = len(critical_concerns) > 0

        if confidence_level == ConfidenceLevel.CRITICAL or blocking_gaps or has_critical_concerns:
            approval_recommendation = ApprovalRecommendation.REJECT
        elif confidence_level == ConfidenceLevel.LOW:
            approval_recommendation = ApprovalRecommendation.ESCALATE
        elif confidence_level == ConfidenceLevel.MEDIUM:
            approval_recommendation = ApprovalRecommendation.REVIEW_REQUIRED
        elif confidence_level == ConfidenceLevel.HIGH:
            approval_recommendation = ApprovalRecommendation.APPROVE_WITH_CONDITIONS
        else:  # EXCELLENT
            approval_recommendation = ApprovalRecommendation.APPROVE

        # Assess risk based on cross-reference results
        risk_assessment = self._assess_risk(cross_reference_results, detected_gaps)

        return PRConfidenceReport(
            workflow_id=workflow_id,
            pr_id=pr_id,
            confidence_score=confidence_score,
            confidence_level=confidence_level,
            approval_recommendation=approval_recommendation,
            component_scores=component_scores,
            cross_reference_results=cross_reference_results,
            detected_gaps=detected_gaps,
            risk_assessment=risk_assessment,
            recommendations=recommendations,
            critical_concerns=critical_concerns,
            strengths=strengths,
            improvement_areas=improvement_areas,
            analysis_duration=analysis_duration,
            jira_ticket=jira_ticket,
            ai_provider=ai_provider
        )

    def _assess_risk(
        self,
        cross_reference_results: Dict[str, Any],
        detected_gaps: List[Dict[str, Any]]
    ) -> str:
        """Assess overall risk based on analysis results."""
        # Calculate risk factors
        gap_count = len(detected_gaps)
        blocking_gaps = len([g for g in detected_gaps if g.get('blocking_approval', False)])

        # Get consistency scores
        doc_consistency = cross_reference_results.get('documentation_consistency_overall', 0.5)
        req_alignment = cross_reference_results.get('overall_alignment_score', 0.5)

        # Determine risk level
        if blocking_gaps > 0 or doc_consistency < 0.3 or req_alignment < 0.3:
            return "high"
        elif gap_count > 5 or doc_consistency < 0.5 or req_alignment < 0.5:
            return "medium"
        elif gap_count > 2 or doc_consistency < 0.7 or req_alignment < 0.7:
            return "low"
        else:
            return "minimal"

    def generate_html_report(self, report: PRConfidenceReport) -> str:
        """Generate HTML report from PRConfidenceReport."""
        title = f"PR Confidence Analysis - {report.pr_id}"

        return self._templates['html_template'].format(
            title=title,
            timestamp=report.analysis_timestamp.strftime("%Y-%m-%d %H:%M:%S UTC"),
            confidence_percentage=report.confidence_percentage,
            confidence_level=report.confidence_level.value,
            approval_recommendation=report.approval_recommendation.value,
            risk_assessment=report.risk_assessment,
            component_scores_html=self._generate_component_scores_html(report),
            gap_count=report.gap_count,
            gaps_html=self._generate_gaps_html(report),
            recommendations_html=self._generate_recommendations_html(report)
        )

    def _generate_component_scores_html(self, report: PRConfidenceReport) -> str:
        """Generate HTML for component scores."""
        if not report.component_scores:
            return "<p>No component scores available.</p>"

        items = []
        for component, score in report.component_scores.items():
            items.append(f'<div class="metric"><span>{component.replace("_", " ").title()}</span><span>{score * 100:.1f}%</span></div>')

        return '\n'.join(items)

    def _generate_gaps_html(self, report: PRConfidenceReport) -> str:
        """Generate HTML for detected gaps."""
        if not report.detected_gaps:
            return "<p>No gaps detected.</p>"

        items = []
        for gap in report.detected_gaps:
            blocking = " [BLOCKING]" if gap.get('blocking_approval', False) else ""
            items.append(f'<div><strong>{gap.get("gap_type", "Unknown").replace("_", " ").title()}{blocking}:</strong> {gap.get("description", "N/A")}</div>')

        return '\n'.join(items)

    def _generate_recommendations_html(self, report: PRConfidenceReport) -> str:
        """Generate HTML for recommendations."""
        if not report.recommendations:
            return "<li>No recommendations available.</li>"

        return '\n'.join(f'<li>{rec}</li>' for rec in report.recommendations)

    def _generate_confidence_section(self, report: PRConfidenceReport) -> str:
        """Generate the confidence score section."""
        return f"""
        <section class="section">
            <h2>Confidence Analysis</h2>
            <div style="text-align: center; margin: 20px 0;">
                <div class="score">{report.confidence_percentage:.1f}%</div>
                <div style="font-size: 18px; color: {report.confidence_level.color_code}; margin: 10px 0;">
                    {report.confidence_level.value.upper()}
                </div>
                <div style="font-size: 16px; margin: 10px 0;">
                    Recommendation: {report.approval_recommendation}
                </div>
                <div style="color: #666;">
                    Risk Level: {report.risk_assessment.upper()}
                </div>
            </div>
        </section>
        """

    def _generate_component_scores_section(self, report: PRConfidenceReport) -> str:
        """Generate the component scores section."""
        score_items = []
        for component, score in report.component_scores.items():
            score_items.append(f"""
            <div class="metric">
                <span>{component.replace('_', ' ').title()}</span>
                <span style="font-weight: bold;">{score * 100:.1f}%</span>
            </div>
            """)

        return f"""
        <section class="section">
            <h2>Component Analysis</h2>
            {''.join(score_items)}
        </section>
        """

    def _generate_gaps_section(self, report: PRConfidenceReport) -> str:
        """Generate the detected gaps section."""
        if not report.detected_gaps:
            return """
            <section class="section">
                <h2>Analysis Gaps</h2>
                <p>No significant gaps detected.</p>
            </section>
            """

        gap_items = []
        for gap in report.detected_gaps:
            blocking_badge = '<span style="color: red; font-weight: bold;">[BLOCKING]</span>' if gap.get('blocking_approval') else ''
            gap_items.append(f"""
            <div style="border: 1px solid #ddd; padding: 10px; margin: 10px 0;">
                <h4>{gap.get('gap_type', 'Unknown').replace('_', ' ').title()} {blocking_badge}</h4>
                <p><strong>Description:</strong> {gap.get('description', 'N/A')}</p>
                <p><strong>Severity:</strong> {gap.get('severity', 'medium').upper()}</p>
                <p><strong>Recommendation:</strong> {gap.get('recommendation', 'Review required')}</p>
            </div>
            """)

        return f"""
        <section class="section">
            <h2>Detected Gaps ({len(report.detected_gaps)})</h2>
            {''.join(gap_items)}
        </section>
        """

    def _generate_recommendations_section(self, report: PRConfidenceReport) -> str:
        """Generate the recommendations section."""
        if not report.recommendations:
            return ""

        rec_items = [f"<li>{rec}</li>" for rec in report.recommendations]

        concerns_section = ""
        if report.critical_concerns:
            concern_items = [f"<li style='color: red;'>{concern}</li>" for concern in report.critical_concerns]
            concerns_section = f"""
            <h3>Critical Concerns</h3>
            <ul>{''.join(concern_items)}</ul>
            """

        strengths_section = ""
        if report.strengths:
            strength_items = [f"<li style='color: green;'>{strength}</li>" for strength in report.strengths]
            strengths_section = f"""
            <h3>Strengths</h3>
            <ul>{''.join(strength_items)}</ul>
            """

        return f"""
        <section class="section">
            <h2>Analysis Summary</h2>
            <h3>Recommendations</h3>
            <ul>{''.join(rec_items)}</ul>
            {concerns_section}
            {strengths_section}
        </section>
        """

    def _generate_metadata_section(self, report: PRConfidenceReport) -> str:
        """Generate the metadata section."""
        return f"""
        <section class="section">
            <h2>Analysis Metadata</h2>
            <div class="metric">
                <span>Analysis Duration</span>
                <span>{report.analysis_duration:.2f} seconds</span>
            </div>
            <div class="metric">
                <span>AI Provider</span>
                <span>{report.ai_provider}</span>
            </div>
            <div class="metric">
                <span>Workflow ID</span>
                <span>{report.workflow_id}</span>
            </div>
            {'<div class="metric"><span>Jira Ticket</span><span>' + report.jira_ticket + '</span></div>' if report.jira_ticket else ''}
        </section>
        """

    def generate_json_report(self, report: PRConfidenceReport) -> str:
        """Generate JSON report from PRConfidenceReport."""
        return json.dumps(report.to_dict(), indent=2, default=str)

    def validate_report_data(self, report_data: Dict[str, Any]) -> List[str]:
        """Validate report data and return list of validation errors."""
        errors = []

        required_fields = ['workflow_id', 'pr_id', 'confidence_score']
        for field in required_fields:
            if field not in report_data:
                errors.append(f"Missing required field: {field}")

        if 'confidence_score' in report_data:
            score = report_data['confidence_score']
            if not isinstance(score, (int, float)) or not 0.0 <= score <= 1.0:
                errors.append("Confidence score must be a number between 0.0 and 1.0")

        return errors
