"""Reporting Operations Domain Service.

This service encapsulates reporting and document generation operations
that were previously in the monolithic main.py file.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime

from ..entities.document import Document
from ..entities.finding import Finding
from ..exceptions.domain_exceptions import AnalysisOperationException
from ...infrastructure.utilities.error_handling_utils import handle_analysis_error
from ...modules.shared_utils import build_analysis_context


class ReportingOperationsService:
    """Domain service for reporting and document generation operations.

    This service handles the business logic for generating reports,
    document dumps, and formatted outputs.
    """

    def __init__(self):
        """Initialize the reporting operations service."""
        pass

    async def generate_document_dump(
        self,
        documents: List[Document],
        format_options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate a comprehensive document dump report.

        Args:
            documents: List of documents to include
            format_options: Formatting options for the dump

        Returns:
            Document dump report
        """
        operation_context = build_analysis_context(
            "generate_document_dump",
            document_count=len(documents),
            format_options=format_options
        )

        try:
            dump_sections = []

            for doc in documents:
                section = await self._generate_document_section(doc, format_options)
                dump_sections.append(section)

            return {
                "document_count": len(documents),
                "sections": dump_sections,
                "format_options": format_options,
                "generated_at": datetime.utcnow().isoformat(),
                "total_sections": len(dump_sections),
            }

        except Exception as e:
            operation_exception = AnalysisOperationException(
                operation="generate_document_dump",
                error_message=str(e),
                context=operation_context
            )
            handle_analysis_error(
                "generate document dump",
                operation_exception,
                document_count=len(documents),
                **operation_context
            )
            raise operation_exception from e

    async def _generate_document_section(
        self,
        document: Document,
        format_options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate a formatted section for a single document."""
        try:
            section_lines = []

            # Generate document header
            header = self._generate_document_header(document, format_options)
            section_lines.extend(header)

            # Add metadata if requested
            if format_options.get("include_metadata", True):
                metadata = self._generate_document_metadata(document)
                section_lines.extend(metadata)

            # Add content if requested
            if format_options.get("include_content", True):
                content = self._generate_document_content(document, format_options)
                section_lines.extend(content)

            # Add comments/conversation if available
            comments = self._generate_document_comments(document, format_options)
            section_lines.extend(comments)

            return {
                "document_id": getattr(document, 'id', 'unknown'),
                "title": getattr(document, 'title', 'Untitled'),
                "section_lines": section_lines,
                "line_count": len(section_lines),
            }

        except Exception as e:
            # Return minimal section on error
            return {
                "document_id": getattr(document, 'id', 'unknown'),
                "title": getattr(document, 'title', 'Untitled'),
                "section_lines": [f"Error generating section: {str(e)}"],
                "line_count": 1,
                "error": str(e)
            }

    def _generate_document_header(
        self,
        document: Document,
        format_options: Dict[str, Any]
    ) -> List[str]:
        """Generate document header section."""
        lines = []

        doc_type = getattr(document, 'type', 'unknown')
        doc_id = getattr(document, 'id', 'unknown')
        title = getattr(document, 'title', 'Untitled Document')

        # Add header with icon
        icon = self._get_type_icon(doc_type)
        lines.append(f"# {icon} {title}")
        lines.append(f"**Type:** {doc_type} | **ID:** {doc_id}")

        if hasattr(document, 'url') and document.url:
            lines.append(f"**URL:** {document.url}")

        lines.append("")  # Empty line

        return lines

    def _generate_document_metadata(self, document: Document) -> List[str]:
        """Generate document metadata section."""
        lines = ["## 📋 Metadata", ""]

        # Add metadata fields
        metadata_fields = [
            ("Created", getattr(document, 'created_at', None)),
            ("Updated", getattr(document, 'updated_at', None)),
            ("Author", getattr(document, 'author', None)),
            ("Source", getattr(document, 'source', None)),
            ("Tags", getattr(document, 'tags', None)),
        ]

        for label, value in metadata_fields:
            if value:
                if isinstance(value, list):
                    value = ", ".join(str(v) for v in value)
                lines.append(f"- **{label}:** {value}")

        lines.append("")  # Empty line
        return lines

    def _generate_document_content(
        self,
        document: Document,
        format_options: Dict[str, Any]
    ) -> List[str]:
        """Generate document content section."""
        lines = ["## 📄 Content", ""]

        content = getattr(document, 'content', '')
        if content:
            # Apply content formatting options
            max_length = format_options.get("max_content_length", 5000)
            if len(content) > max_length:
                content = content[:max_length] + "..."
                lines.append(f"*Content truncated to {max_length} characters*")
                lines.append("")

            lines.append(content)
        else:
            lines.append("*No content available*")

        lines.append("")  # Empty line
        return lines

    def _generate_document_comments(
        self,
        document: Document,
        format_options: Dict[str, Any]
    ) -> List[str]:
        """Generate document comments/conversation section."""
        lines = []

        # Check if document has comments/conversation
        if hasattr(document, 'comments') and document.comments:
            lines.extend(["## 💬 Comments/Conversation", ""])

            max_comments = format_options.get("max_comments", 10)
            comments = document.comments[:max_comments]

            for i, comment in enumerate(comments, 1):
                author = comment.get('author', 'Unknown')
                content = comment.get('content', '')
                timestamp = comment.get('timestamp', '')

                lines.append(f"### Comment {i}")
                lines.append(f"**Author:** {author}")
                if timestamp:
                    lines.append(f"**Time:** {timestamp}")
                lines.append("")
                lines.append(content)
                lines.append("")

            if len(document.comments) > max_comments:
                lines.append(f"*... and {len(document.comments) - max_comments} more comments*")
                lines.append("")

        return lines

    def _get_type_icon(self, doc_type: str) -> str:
        """Get appropriate icon for document type."""
        icons = {
            "confluence": "📄",
            "jira": "🎫",
            "pull_request": "🔄",
            "pr": "🔄",
            "github": "🐙",
            "readme": "📖",
            "markdown": "📝",
            "unknown": "📋",
        }
        return icons.get(doc_type.lower(), "📋")

    async def generate_analysis_summary(
        self,
        findings: List[Finding],
        analysis_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate a comprehensive analysis summary report.

        Args:
            findings: List of analysis findings
            analysis_results: Raw analysis results

        Returns:
            Summary report
        """
        operation_context = build_analysis_context(
            "generate_analysis_summary",
            finding_count=len(findings),
            result_count=len(analysis_results)
        )

        try:
            # Calculate summary statistics
            severity_counts = self._count_findings_by_severity(findings)
            type_counts = self._count_findings_by_type(findings)

            # Generate insights
            insights = self._generate_analysis_insights(findings, analysis_results)

            return {
                "total_findings": len(findings),
                "severity_breakdown": severity_counts,
                "type_breakdown": type_counts,
                "insights": insights,
                "analysis_summary": {
                    "documents_analyzed": len(analysis_results),
                    "findings_per_document": len(findings) / max(len(analysis_results), 1),
                    "critical_findings": severity_counts.get("critical", 0),
                    "high_priority_findings": severity_counts.get("high", 0),
                },
                "generated_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            operation_exception = AnalysisOperationException(
                operation="generate_analysis_summary",
                error_message=str(e),
                context=operation_context
            )
            handle_analysis_error(
                "generate analysis summary",
                operation_exception,
                finding_count=len(findings),
                **operation_context
            )
            raise operation_exception from e

    def _count_findings_by_severity(self, findings: List[Finding]) -> Dict[str, int]:
        """Count findings by severity level."""
        counts = {}
        for finding in findings:
            severity = getattr(finding, 'severity', 'unknown')
            counts[severity] = counts.get(severity, 0) + 1
        return counts

    def _count_findings_by_type(self, findings: List[Finding]) -> Dict[str, int]:
        """Count findings by type."""
        counts = {}
        for finding in findings:
            finding_type = getattr(finding, 'type', 'unknown')
            counts[finding_type] = counts.get(finding_type, 0) + 1
        return counts

    def _generate_analysis_insights(
        self,
        findings: List[Finding],
        analysis_results: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate insights from analysis results."""
        insights = []

        severity_counts = self._count_findings_by_severity(findings)

        if severity_counts.get("critical", 0) > 0:
            insights.append("🚨 Critical issues found that require immediate attention")

        if severity_counts.get("high", 0) > 5:
            insights.append("⚠️ High number of high-priority findings detected")

        total_findings = len(findings)
        if total_findings > 50:
            insights.append("📊 Large number of findings suggests comprehensive analysis completed")

        if not insights:
            insights.append("✅ Analysis completed with manageable number of findings")

        return insights
