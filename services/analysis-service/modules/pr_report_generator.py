"""
PR Confidence Analysis Report Generator

Generates comprehensive HTML and JSON reports for PR confidence analysis
with detailed findings, recommendations, and executive summaries.
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass
from jinja2 import Template

@dataclass
class PRConfidenceReport:
    """Complete PR confidence analysis report."""
    workflow_id: str
    pr_id: str
    jira_ticket: Optional[str]
    analysis_timestamp: str
    confidence_score: float
    confidence_level: str
    approval_recommendation: str

    # Component scores
    component_scores: Dict[str, float]

    # Analysis results
    cross_reference_results: Dict[str, Any]
    detected_gaps: List[Dict[str, Any]]
    risk_assessment: str

    # Recommendations and insights
    recommendations: List[str]
    critical_concerns: List[str]
    strengths: List[str]
    improvement_areas: List[str]

    # Metadata
    analysis_duration: float
    ai_provider: str = "local_llm"

class PRReportGenerator:
    """Generates comprehensive PR confidence analysis reports."""

    def __init__(self):
        self.templates = self._load_templates()

    def _load_templates(self) -> Dict[str, Template]:
        """Load report templates."""
        templates = {}

        # HTML Report Template
        templates['html'] = Template("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PR Confidence Analysis Report - {{ pr_id }}</title>
    <style>
        {{ css_styles }}
    </style>
</head>
<body>
    <div class="container">
        <header class="report-header">
            <h1>PR Confidence Analysis Report</h1>
            <div class="report-meta">
                <div class="meta-item"><strong>PR:</strong> {{ pr_id }}</div>
                <div class="meta-item"><strong>Jira:</strong> {{ jira_ticket or 'N/A' }}</div>
                <div class="meta-item"><strong>Analysis Date:</strong> {{ analysis_timestamp }}</div>
                <div class="meta-item"><strong>Workflow ID:</strong> {{ workflow_id }}</div>
            </div>
        </header>

        <section class="confidence-summary">
            <h2>Executive Summary</h2>
            <div class="confidence-score">
                <div class="score-display score-{{ confidence_level.lower() }}">
                    <div class="score-value">{{ "%.1f"|format(confidence_score * 100) }}%</div>
                    <div class="score-label">{{ confidence_level|upper }}</div>
                </div>
                <div class="recommendation">
                    <h3>Recommendation: {{ approval_recommendation|replace('_', ' ')|title }}</h3>
                    <p>{{ rationale }}</p>
                </div>
            </div>
        </section>

        <section class="component-scores">
            <h2>Component Analysis</h2>
            <div class="score-grid">
                {% for component, score in component_scores.items() %}
                <div class="score-item">
                    <div class="component-name">{{ component|replace('_', ' ')|title }}</div>
                    <div class="component-score">{{ "%.1f"|format(score * 100) }}%</div>
                    <div class="score-bar">
                        <div class="score-fill" style="width: {{ (score * 100)|int }}%"></div>
                    </div>
                </div>
                {% endfor %}
            </div>
        </section>

        {% if strengths %}
        <section class="strengths">
            <h2>✅ Strengths</h2>
            <ul>
                {% for strength in strengths %}
                <li>{{ strength }}</li>
                {% endfor %}
            </ul>
        </section>
        {% endif %}

        {% if critical_concerns %}
        <section class="critical-concerns">
            <h2>🚨 Critical Concerns</h2>
            <ul class="concerns-list">
                {% for concern in critical_concerns %}
                <li>{{ concern }}</li>
                {% endfor %}
            </ul>
        </section>
        {% endif %}

        {% if detected_gaps %}
        <section class="gaps-analysis">
            <h2>🔍 Identified Gaps</h2>
            <div class="gaps-summary">
                <p><strong>Total Gaps:</strong> {{ detected_gaps|length }}</p>
                {% for gap in detected_gaps %}
                <div class="gap-item severity-{{ gap.severity }}">
                    <div class="gap-header">
                        <span class="gap-type">{{ gap.gap_type|replace('_', ' ')|title }}</span>
                        <span class="gap-severity">{{ gap.severity|upper }}</span>
                        {% if gap.blocking_approval %}
                        <span class="blocking-badge">BLOCKING</span>
                        {% endif %}
                    </div>
                    <div class="gap-description">{{ gap.description }}</div>
                    <div class="gap-evidence">{{ gap.evidence }}</div>
                    <div class="gap-recommendation">
                        <strong>Recommendation:</strong> {{ gap.recommendation }}
                    </div>
                    <div class="gap-effort">
                        <strong>Estimated Effort:</strong> {{ gap.estimated_effort|title }}
                    </div>
                </div>
                {% endfor %}
            </div>
        </section>
        {% endif %}

        <section class="cross-reference-analysis">
            <h2>🔗 Cross-Reference Analysis</h2>
            <div class="cross-ref-grid">
                <div class="cross-ref-item">
                    <h3>Requirements Alignment</h3>
                    <div class="alignment-score">
                        {{ "%.1f"|format(cross_reference_results.overall_alignment_score * 100) }}%
                    </div>
                    <p>{{ cross_reference_results.requirement_alignment|length }} requirement categories analyzed</p>
                </div>
                <div class="cross-ref-item">
                    <h3>Documentation Consistency</h3>
                    <div class="consistency-score">
                        {{ "%.1f"|format(cross_reference_results.documentation_consistency_overall * 100) }}%
                    </div>
                    <p>{{ cross_reference_results.documentation_consistency|length }} documents analyzed</p>
                </div>
                <div class="cross-ref-item">
                    <h3>Risk Assessment</h3>
                    <div class="risk-level risk-{{ cross_reference_results.risk_assessment.lower() }}">
                        {{ cross_reference_results.risk_assessment|upper }}
                    </div>
                    <p>{{ risk_factors|length }} risk factors identified</p>
                </div>
            </div>
        </section>

        {% if recommendations %}
        <section class="recommendations">
            <h2>💡 Recommendations</h2>
            <ol>
                {% for recommendation in recommendations %}
                <li>{{ recommendation }}</li>
                {% endfor %}
            </ol>
        </section>
        {% endif %}

        {% if improvement_areas %}
        <section class="improvement-areas">
            <h2>📈 Areas for Improvement</h2>
            <ul>
                {% for area in improvement_areas %}
                <li>{{ area }}</li>
                {% endfor %}
            </ul>
        </section>
        {% endif %}

        <footer class="report-footer">
            <div class="footer-content">
                <p><strong>Analysis Duration:</strong> {{ "%.2f"|format(analysis_duration) }} seconds</p>
                <p><strong>AI Provider:</strong> {{ ai_provider }}</p>
                <p><em>Report generated by LLM Documentation Ecosystem</em></p>
            </div>
        </footer>
    </div>
</body>
</html>
        """)

        # CSS Styles for the HTML report
        self.css_styles = """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f8f9fa;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: white;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
        }

        .report-header {
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #e9ecef;
        }

        .report-header h1 {
            color: #2c3e50;
            margin-bottom: 15px;
        }

        .report-meta {
            display: flex;
            justify-content: center;
            gap: 30px;
            flex-wrap: wrap;
        }

        .meta-item {
            font-size: 14px;
            color: #6c757d;
        }

        .confidence-summary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            text-align: center;
        }

        .confidence-score {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 40px;
            flex-wrap: wrap;
        }

        .score-display {
            text-align: center;
        }

        .score-display.high { border-color: #28a745; }
        .score-display.medium { border-color: #ffc107; }
        .score-display.low { border-color: #fd7e14; }
        .score-display.critical { border-color: #dc3545; }

        .score-value {
            font-size: 48px;
            font-weight: bold;
            margin-bottom: 5px;
        }

        .score-label {
            font-size: 18px;
            opacity: 0.9;
        }

        .recommendation h3 {
            margin-bottom: 10px;
            font-size: 24px;
        }

        .component-scores {
            margin-bottom: 30px;
        }

        .component-scores h2 {
            margin-bottom: 20px;
            color: #2c3e50;
        }

        .score-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
        }

        .score-item {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #007bff;
        }

        .component-name {
            font-weight: bold;
            margin-bottom: 10px;
            color: #495057;
        }

        .component-score {
            font-size: 24px;
            font-weight: bold;
            color: #007bff;
            margin-bottom: 10px;
        }

        .score-bar {
            width: 100%;
            height: 8px;
            background: #e9ecef;
            border-radius: 4px;
            overflow: hidden;
        }

        .score-fill {
            height: 100%;
            background: linear-gradient(90deg, #28a745, #20c997);
            transition: width 0.3s ease;
        }

        .strengths, .critical-concerns, .recommendations, .improvement-areas {
            margin-bottom: 30px;
        }

        .strengths h2 { color: #28a745; }
        .critical-concerns h2 { color: #dc3545; }
        .recommendations h2 { color: #007bff; }
        .improvement-areas h2 { color: #ffc107; }

        .strengths ul, .recommendations ol, .improvement-areas ul {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid currentColor;
        }

        .strengths li, .recommendations li, .improvement-areas li {
            margin-bottom: 8px;
        }

        .critical-concerns {
            background: #fff5f5;
            border: 1px solid #fed7d7;
            border-radius: 8px;
            padding: 20px;
        }

        .concerns-list {
            color: #c53030;
        }

        .concerns-list li {
            margin-bottom: 10px;
            font-weight: 500;
        }

        .gaps-analysis {
            margin-bottom: 30px;
        }

        .gaps-analysis h2 {
            color: #fd7e14;
            margin-bottom: 20px;
        }

        .gaps-summary {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 8px;
            padding: 20px;
        }

        .gap-item {
            background: white;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
        }

        .gap-item.severity-critical { border-left: 4px solid #dc3545; }
        .gap-item.severity-high { border-left: 4px solid #fd7e14; }
        .gap-item.severity-medium { border-left: 4px solid #ffc107; }
        .gap-item.severity-low { border-left: 4px solid #28a745; }

        .gap-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }

        .gap-type {
            font-weight: bold;
            color: #495057;
        }

        .gap-severity {
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
        }

        .gap-item.severity-critical .gap-severity { background: #f8d7da; color: #721c24; }
        .gap-item.severity-high .gap-severity { background: #fff3cd; color: #856404; }
        .gap-item.severity-medium .gap-severity { background: #d1ecf1; color: #0c5460; }
        .gap-item.severity-low .gap-severity { background: #d4edda; color: #155724; }

        .blocking-badge {
            background: #dc3545;
            color: white;
            padding: 2px 6px;
            border-radius: 10px;
            font-size: 10px;
            font-weight: bold;
        }

        .gap-description, .gap-evidence, .gap-recommendation, .gap-effort {
            margin-bottom: 8px;
            font-size: 14px;
        }

        .gap-description { font-weight: bold; }
        .gap-evidence { color: #6c757d; font-style: italic; }
        .gap-recommendation { color: #007bff; }
        .gap-effort { color: #28a745; }

        .cross-reference-analysis {
            margin-bottom: 30px;
        }

        .cross-reference-analysis h2 {
            color: #6f42c1;
            margin-bottom: 20px;
        }

        .cross-ref-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
        }

        .cross-ref-item {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }

        .cross-ref-item h3 {
            color: #495057;
            margin-bottom: 15px;
        }

        .alignment-score, .consistency-score {
            font-size: 32px;
            font-weight: bold;
            color: #007bff;
            margin-bottom: 10px;
        }

        .risk-level {
            font-size: 24px;
            font-weight: bold;
            padding: 10px;
            border-radius: 8px;
            margin-bottom: 10px;
        }

        .risk-critical { background: #f8d7da; color: #721c24; }
        .risk-high { background: #fff3cd; color: #856404; }
        .risk-medium { background: #d1ecf1; color: #0c5460; }
        .risk-low { background: #d4edda; color: #155724; }
        .risk-none { background: #f8f9fa; color: #6c757d; }

        .report-footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #dee2e6;
            text-align: center;
            color: #6c757d;
            font-size: 14px;
        }

        .footer-content p {
            margin-bottom: 5px;
        }

        @media (max-width: 768px) {
            .container {
                padding: 10px;
            }

            .confidence-score {
                flex-direction: column;
                gap: 20px;
            }

            .report-meta {
                flex-direction: column;
                gap: 10px;
            }

            .cross-ref-grid {
                grid-template-columns: 1fr;
            }

            .score-grid {
                grid-template-columns: 1fr;
            }
        }
        """

        templates['html'] = Template(templates['html'].template.replace('{{ css_styles }}', self.css_styles))

        return templates

    def generate_report(
        self,
        pr_data: Dict[str, Any],
        jira_data: Dict[str, Any],
        confluence_docs: List[Dict[str, Any]],
        cross_reference_results: Any,
        confidence_score: Any,
        detected_gaps: List[Any],
        analysis_duration: float
    ) -> PRConfidenceReport:
        """
        Generate a comprehensive PR confidence report.

        Returns:
            PRConfidenceReport object with all analysis data
        """
        # Extract key data
        workflow_id = f"pr-analysis-{int(datetime.now().timestamp())}"
        pr_id = pr_data.get('id', 'unknown')
        jira_ticket = pr_data.get('jira_ticket')

        # Convert complex objects to dictionaries for JSON serialization
        cross_ref_dict = {
            'overall_alignment_score': cross_reference_results.overall_alignment_score,
            'requirement_alignment': dict(cross_reference_results.requirement_alignment),
            'documentation_consistency': dict(cross_reference_results.documentation_consistency),
            'documentation_consistency_overall': sum(
                result.get('consistency_score', 0)
                for result in cross_reference_results.documentation_consistency.values()
            ) / len(cross_reference_results.documentation_consistency) if cross_reference_results.documentation_consistency else 0,
            'identified_gaps': cross_reference_results.identified_gaps,
            'consistency_issues': cross_reference_results.consistency_issues
        }

        gaps_list = [
            {
                'gap_type': gap.gap_type.value,
                'severity': gap.severity.value,
                'description': gap.description,
                'evidence': gap.evidence,
                'recommendation': gap.recommendation,
                'estimated_effort': gap.estimated_effort,
                'blocking_approval': gap.blocking_approval
            }
            for gap in detected_gaps
        ]

        return PRConfidenceReport(
            workflow_id=workflow_id,
            pr_id=pr_id,
            jira_ticket=jira_ticket,
            analysis_timestamp=datetime.now().isoformat(),
            confidence_score=confidence_score.overall_score,
            confidence_level=confidence_score.confidence_level.value,
            approval_recommendation=confidence_score.approval_recommendation.value,
            component_scores=confidence_score.component_scores,
            cross_reference_results=cross_ref_dict,
            detected_gaps=gaps_list,
            risk_assessment=cross_reference_results.risk_assessment,
            recommendations=confidence_score.improvement_areas + [
                "Review all critical concerns before approval",
                "Address all blocking gaps identified",
                "Consider additional testing for security-related changes"
            ],
            critical_concerns=confidence_score.critical_concerns,
            strengths=confidence_score.strengths,
            improvement_areas=confidence_score.improvement_areas,
            analysis_duration=analysis_duration,
            ai_provider="ollama_llama3.2"
        )

    def generate_html_report(self, report: PRConfidenceReport) -> str:
        """Generate HTML report from PRConfidenceReport."""
        template_data = {
            'workflow_id': report.workflow_id,
            'pr_id': report.pr_id,
            'jira_ticket': report.jira_ticket,
            'analysis_timestamp': report.analysis_timestamp,
            'confidence_score': report.confidence_score,
            'confidence_level': report.confidence_level,
            'approval_recommendation': report.approval_recommendation,
            'component_scores': report.component_scores,
            'cross_reference_results': type('obj', (object,), report.cross_reference_results),
            'detected_gaps': report.detected_gaps,
            'risk_assessment': report.risk_assessment,
            'recommendations': report.recommendations,
            'critical_concerns': report.critical_concerns,
            'strengths': report.strengths,
            'improvement_areas': report.improvement_areas,
            'analysis_duration': report.analysis_duration,
            'ai_provider': report.ai_provider,
            'rationale': getattr(report, 'rationale', 'Analysis completed successfully'),
            'risk_factors': getattr(report, 'risk_factors', [])
        }

        return self.templates['html'].render(**template_data)

    def generate_json_report(self, report: PRConfidenceReport) -> str:
        """Generate JSON report from PRConfidenceReport."""
        report_dict = {
            'workflow_id': report.workflow_id,
            'pr_id': report.pr_id,
            'jira_ticket': report.jira_ticket,
            'analysis_timestamp': report.analysis_timestamp,
            'confidence_score': report.confidence_score,
            'confidence_level': report.confidence_level,
            'approval_recommendation': report.approval_recommendation,
            'component_scores': report.component_scores,
            'cross_reference_results': report.cross_reference_results,
            'detected_gaps': report.detected_gaps,
            'risk_assessment': report.risk_assessment,
            'recommendations': report.recommendations,
            'critical_concerns': report.critical_concerns,
            'strengths': report.strengths,
            'improvement_areas': report.improvement_areas,
            'analysis_duration': report.analysis_duration,
            'ai_provider': report.ai_provider,
            'metadata': {
                'generated_by': 'LLM Documentation Ecosystem',
                'version': '2.0.0',
                'analysis_type': 'pr_confidence_analysis'
            }
        }

        return json.dumps(report_dict, indent=2, default=str)

    def save_reports(self, report: PRConfidenceReport, output_dir: str = "reports"):
        """Save both HTML and JSON reports to files."""
        import os

        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Generate filenames
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"pr_confidence_report_{report.pr_id}_{timestamp}"

        # Generate and save HTML report
        html_content = self.generate_html_report(report)
        html_filename = f"{base_filename}.html"
        html_filepath = os.path.join(output_dir, html_filename)

        with open(html_filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)

        # Generate and save JSON report
        json_content = self.generate_json_report(report)
        json_filename = f"{base_filename}.json"
        json_filepath = os.path.join(output_dir, json_filename)

        with open(json_filepath, 'w', encoding='utf-8') as f:
            f.write(json_content)

        return {
            'html_report': html_filepath,
            'json_report': json_filepath
        }


# Create singleton instance
pr_report_generator = PRReportGenerator()
