#!/usr/bin/env python3
"""
Human-Readable Report Generator

A configurable component for generating human-readable reports from
analysis workflows. Can be integrated into any workflow that produces
structured analysis results.
"""

import json
import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from pathlib import Path

class HumanReadableReportGenerator:
    """
    Generates human-readable reports from structured analysis data.

    Supports multiple perspectives (developer, project manager, executive)
    and various output formats (Markdown, HTML, JSON).
    """

    def __init__(self, output_dir: str = "reports", include_perspectives: List[str] = None):
        """
        Initialize the report generator.

        Args:
            output_dir: Directory to save generated reports
            include_perspectives: List of perspectives to include
                                ['developer', 'project_manager', 'executive']
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        if include_perspectives is None:
            include_perspectives = ['developer', 'project_manager']

        self.include_perspectives = include_perspectives
        self.templates = self._load_templates()

    def _load_templates(self) -> Dict[str, str]:
        """Load report templates for different perspectives."""
        return {
            'developer': self._get_developer_template(),
            'project_manager': self._get_project_manager_template(),
            'executive': self._get_executive_template()
        }

    def generate_report(self,
                       analysis_results: Dict[str, Any],
                       workflow_type: str = "pr_analysis",
                       output_format: str = "markdown",
                       filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a human-readable report from analysis results.

        Args:
            analysis_results: Structured analysis results
            workflow_type: Type of workflow (pr_analysis, code_review, etc.)
            output_format: Output format (markdown, html, json)
            filename: Optional custom filename

        Returns:
            Dict containing report metadata and file paths
        """

        # Generate report content
        report_content = self._generate_report_content(analysis_results, workflow_type)

        # Generate filename if not provided
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            workflow_id = analysis_results.get('workflow_id', 'unknown')
            filename = f"{workflow_type}_{workflow_id}_{timestamp}"

        # Save report in requested format
        saved_files = self._save_report(report_content, filename, output_format)

        # Create report metadata
        report_metadata = {
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'workflow_type': workflow_type,
            'workflow_id': analysis_results.get('workflow_id', 'unknown'),
            'perspectives_included': self.include_perspectives,
            'output_format': output_format,
            'files_generated': saved_files,
            'confidence_score': analysis_results.get('executive_summary', {}).get('confidence_score'),
            'confidence_level': analysis_results.get('executive_summary', {}).get('confidence_level'),
            'recommendation': analysis_results.get('executive_summary', {}).get('approval_recommendation')
        }

        return report_metadata

    def _generate_report_content(self, analysis_results: Dict[str, Any], workflow_type: str) -> str:
        """Generate the complete report content."""

        # Extract key information
        executive_summary = analysis_results.get('executive_summary', {})
        confidence_score = executive_summary.get('confidence_score', 0)
        confidence_level = executive_summary.get('confidence_level', 'unknown')
        recommendation = executive_summary.get('approval_recommendation', 'unknown')

        # Generate header
        content = self._generate_header(workflow_type, confidence_score, confidence_level, recommendation)

        # Add perspectives
        for perspective in self.include_perspectives:
            if perspective in self.templates:
                content += self._generate_perspective_section(
                    perspective,
                    self.templates[perspective],
                    analysis_results
                )

        # Add key takeaways and next steps
        content += self._generate_key_takeaways(analysis_results)
        content += self._generate_analysis_details(analysis_results)

        return content

    def _generate_header(self, workflow_type: str, confidence_score: int,
                        confidence_level: str, recommendation: str) -> str:
        """Generate the report header."""

        title_map = {
            'pr_analysis': 'Pull Request Confidence Analysis',
            'code_review': 'Code Review Analysis',
            'security_audit': 'Security Audit Report',
            'performance_analysis': 'Performance Analysis Report'
        }

        title = title_map.get(workflow_type, f'{workflow_type.replace("_", " ").title()} Report')

        header = f"""# {title}

## 🎯 Executive Overview
**Confidence Score: {confidence_score}% ({confidence_level.upper()})**
**Recommendation: {recommendation.replace('_', ' ').title()}**

*Analysis generated on {datetime.now().strftime('%Y-%m-%d at %H:%M:%S UTC')}*

---

"""
        return header

    def _generate_perspective_section(self, perspective: str, template: str,
                                    analysis_results: Dict[str, Any]) -> str:
        """Generate a specific perspective section."""

        perspective_data = analysis_results.get('human_readable_summary', {}).get(f'{perspective}_perspective', {})

        if not perspective_data:
            return f"## {perspective.replace('_', ' ').title()} Perspective\n\n*No {perspective} perspective data available.*\n\n"

        # Fill template with actual data
        section_content = template
        for key, value in perspective_data.items():
            if isinstance(value, list):
                # Convert list to bullet points
                list_items = '\n'.join(f"- {item}" for item in value)
                section_content = section_content.replace(f"{{{key}}}", list_items)
            else:
                section_content = section_content.replace(f"{{{key}}}", str(value))

        return section_content

    def _generate_key_takeaways(self, analysis_results: Dict[str, Any]) -> str:
        """Generate key takeaways section."""

        takeaways = analysis_results.get('human_readable_summary', {}).get('key_takeaways', [
            "Analysis completed successfully",
            "Review recommendations for next steps",
            "Consider stakeholder feedback"
        ])

        takeaway_section = "\n## 🎯 Key Takeaways\n\n"
        for takeaway in takeaways:
            takeaway_section += f"• **{takeaway}**\n"
        takeaway_section += "\n---\n\n"

        return takeaway_section

    def _generate_analysis_details(self, analysis_results: Dict[str, Any]) -> str:
        """Generate analysis details section."""

        quick_ref = analysis_results.get('human_readable_summary', {}).get('quick_reference', {})

        details_section = "## 📊 Analysis Details\n\n"
        details_section += "| Aspect | Details |\n"
        details_section += "|--------|--------|\n"
        details_section += f"| **Generated** | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |\n"
        details_section += f"| **LLM Model** | {quick_ref.get('llm_model_used', 'Unknown')} |\n"
        details_section += f"| **Analysis Time** | {quick_ref.get('total_analysis_time', 'Unknown')} |\n"
        details_section += f"| **Documents Analyzed** | {analysis_results.get('executive_summary', {}).get('documents_analyzed', 'Unknown')} |\n"
        details_section += f"| **Prompts Used** | {analysis_results.get('executive_summary', {}).get('prompts_used', 'Unknown')} |\n"
        details_section += "\n---\n\n"

        return details_section

    def _save_report(self, content: str, filename: str, output_format: str) -> Dict[str, str]:
        """Save the report in the specified format."""

        saved_files = {}

        if output_format == 'markdown':
            md_file = self.output_dir / f"{filename}.md"
            with open(md_file, 'w') as f:
                f.write(content)
            saved_files['markdown'] = str(md_file)

        elif output_format == 'html':
            html_content = self._convert_to_html(content)
            html_file = self.output_dir / f"{filename}.html"
            with open(html_file, 'w') as f:
                f.write(html_content)
            saved_files['html'] = str(html_file)

        elif output_format == 'json':
            # Save the content as JSON metadata + markdown content
            json_data = {
                'metadata': {
                    'filename': filename,
                    'generated_at': datetime.now(timezone.utc).isoformat(),
                    'format': 'json'
                },
                'content': content
            }
            json_file = self.output_dir / f"{filename}.json"
            with open(json_file, 'w') as f:
                json.dump(json_data, f, indent=2)
            saved_files['json'] = str(json_file)

        return saved_files

    def _convert_to_html(self, markdown_content: str) -> str:
        """Convert markdown content to basic HTML."""
        # Simple markdown to HTML conversion
        html = markdown_content
        html = html.replace('# ', '<h1>').replace('\n\n', '</h1>\n\n')
        html = html.replace('## ', '<h2>').replace('\n\n', '</h2>\n\n')
        html = html.replace('### ', '<h3>').replace('\n\n', '</h3>\n\n')
        html = html.replace('**', '<strong>').replace('**', '</strong>')
        html = html.replace('*', '<em>').replace('*', '</em>')
        html = html.replace('\n- ', '\n<li>').replace('\n', '</li>\n')

        full_html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Analysis Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #2c3e50; }}
        h2 {{ color: #34495e; border-bottom: 2px solid #ecf0f1; padding-bottom: 10px; }}
        .highlight {{ background-color: #ecf0f1; padding: 20px; border-radius: 5px; margin: 20px 0; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
{html}
</body>
</html>"""

        return full_html

    def _get_developer_template(self) -> str:
        """Get the developer perspective template."""
        return """
## 👨‍💻 Developer Perspective

### Technical Assessment: {technical_assessment}

### Key Findings
{key_findings}

### Code Quality Notes
{code_quality_notes}

### Security Considerations
{security_considerations}

### Testing Recommendations
{testing_recommendations}

### Implementation Notes
{implementation_notes}

**Estimated Effort Remaining:** {estimated_effort_remaining}
**Risk Level:** {risk_level}

---

"""

    def _get_project_manager_template(self) -> str:
        """Get the project manager perspective template."""
        return """
## 👔 Project Manager Perspective

### Project Status: {project_status}

### Business Impact: {business_impact}

### Acceptance Criteria Status
{acceptance_criteria_status}

### Risk Assessment
{risk_assessment}

### Stakeholder Considerations
{stakeholder_considerations}

### Recommendation
{recommendation}

### Next Steps
{next_steps}

### Success Metrics
{success_metrics}

---

"""

    def _get_executive_template(self) -> str:
        """Get the executive perspective template."""
        return """
## 👔 Executive Perspective

### Strategic Importance: {strategic_importance}

### Business Value: {business_value}

### Risk Summary
{risk_summary}

### Timeline Impact
{timeline_impact}

### Resource Requirements
{resource_requirements}

### Go/No-Go Decision
{go_decision}

---

"""

# Global instance for easy access
human_readable_report_generator = HumanReadableReportGenerator()
