"""Output Generator for Interpreter Service.

This module handles the generation of various output formats (JSON, PDF, CSV, markdown, ZIP)
from workflow execution results, enabling users to get tangible deliverables from their queries.
"""

import json
import csv
import zipfile
import tempfile
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union, BinaryIO
from pathlib import Path
from io import StringIO, BytesIO
import markdown
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from services.shared.constants_new import ServiceNames
from services.shared.logging import fire_and_forget


class OutputGenerator:
    """Generates various output formats from workflow execution results."""

    def __init__(self):
        # Output storage configuration
        self.output_directory = Path("/tmp/interpreter_outputs")
        self.output_directory.mkdir(exist_ok=True)
        
        # File retention settings
        self.file_retention = timedelta(hours=24)
        self.max_file_size = 100 * 1024 * 1024  # 100MB
        
        # Output format configurations
        self.supported_formats = {
            "json": self._generate_json,
            "pdf": self._generate_pdf,
            "csv": self._generate_csv,
            "markdown": self._generate_markdown,
            "zip": self._generate_zip,
            "txt": self._generate_text
        }
        
        # PDF styling
        self.pdf_styles = getSampleStyleSheet()
        self.pdf_styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.pdf_styles['Heading1'],
            fontSize=16,
            textColor=colors.darkblue,
            spaceAfter=12
        ))

    async def generate_output(self, workflow_result: Dict[str, Any], 
                            output_format: str = "json",
                            filename_prefix: str = None) -> Dict[str, Any]:
        """Generate output file from workflow result."""
        try:
            if output_format not in self.supported_formats:
                raise ValueError(f"Unsupported output format: {output_format}")

            # Generate unique filename
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            file_id = str(uuid.uuid4())[:8]
            
            if filename_prefix:
                filename = f"{filename_prefix}_{timestamp}_{file_id}.{output_format}"
            else:
                workflow_name = workflow_result.get("workflow_name", "output")
                filename = f"{workflow_name}_{timestamp}_{file_id}.{output_format}"

            filepath = self.output_directory / filename

            # Generate the output using the appropriate method
            generator_func = self.supported_formats[output_format]
            file_size = await generator_func(workflow_result, filepath)

            # Create download metadata
            download_info = {
                "file_id": file_id,
                "filename": filename,
                "filepath": str(filepath),
                "format": output_format,
                "size_bytes": file_size,
                "created_at": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow() + self.file_retention).isoformat(),
                "workflow_name": workflow_result.get("workflow_name", "unknown"),
                "download_url": f"/outputs/download/{file_id}",
                "metadata": {
                    "execution_id": workflow_result.get("execution_id"),
                    "user_id": workflow_result.get("user_id"),
                    "services_used": workflow_result.get("services_used", []),
                    "execution_time": workflow_result.get("execution_time"),
                    "status": workflow_result.get("status", "completed")
                }
            }

            fire_and_forget(
                "output_generated",
                f"Generated {output_format} output: {filename}",
                ServiceNames.INTERPRETER,
                {
                    "file_id": file_id,
                    "format": output_format,
                    "size_bytes": file_size,
                    "workflow": workflow_result.get("workflow_name")
                }
            )

            return download_info

        except Exception as e:
            fire_and_forget(
                "output_generation_error",
                f"Failed to generate {output_format} output: {str(e)}",
                ServiceNames.INTERPRETER,
                {
                    "format": output_format,
                    "error": str(e),
                    "workflow": workflow_result.get("workflow_name")
                }
            )
            raise

    async def _generate_json(self, workflow_result: Dict[str, Any], filepath: Path) -> int:
        """Generate JSON output."""
        # Create formatted JSON with metadata
        output_data = {
            "metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "format": "json",
                "workflow_name": workflow_result.get("workflow_name"),
                "execution_id": workflow_result.get("execution_id"),
                "status": workflow_result.get("status")
            },
            "execution_summary": {
                "services_used": workflow_result.get("services_used", []),
                "execution_time": workflow_result.get("execution_time"),
                "confidence": workflow_result.get("confidence"),
                "entities_extracted": workflow_result.get("entities", {})
            },
            "results": workflow_result.get("results", {}),
            "raw_data": workflow_result
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        return filepath.stat().st_size

    async def _generate_pdf(self, workflow_result: Dict[str, Any], filepath: Path) -> int:
        """Generate PDF report."""
        doc = SimpleDocTemplate(str(filepath), pagesize=A4)
        story = []

        # Title
        workflow_name = workflow_result.get("workflow_name", "Workflow Report")
        title = Paragraph(workflow_name.replace("_", " ").title(), self.pdf_styles['CustomTitle'])
        story.append(title)
        story.append(Spacer(1, 12))

        # Execution Summary
        story.append(Paragraph("Execution Summary", self.pdf_styles['Heading2']))
        
        summary_data = [
            ["Property", "Value"],
            ["Execution ID", workflow_result.get("execution_id", "N/A")],
            ["Status", workflow_result.get("status", "Unknown")],
            ["Execution Time", workflow_result.get("execution_time", "N/A")],
            ["Confidence", f"{workflow_result.get('confidence', 0):.2f}"],
            ["Services Used", ", ".join(workflow_result.get("services_used", []))]
        ]

        summary_table = Table(summary_data)
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        story.append(summary_table)
        story.append(Spacer(1, 12))

        # Results Section
        results = workflow_result.get("results", {})
        if results:
            story.append(Paragraph("Results", self.pdf_styles['Heading2']))
            
            if isinstance(results, dict):
                for key, value in results.items():
                    story.append(Paragraph(f"<b>{key}:</b>", self.pdf_styles['Normal']))
                    story.append(Paragraph(str(value), self.pdf_styles['Normal']))
                    story.append(Spacer(1, 6))
            else:
                story.append(Paragraph(str(results), self.pdf_styles['Normal']))

        # Entities Section
        entities = workflow_result.get("entities", {})
        if entities:
            story.append(Spacer(1, 12))
            story.append(Paragraph("Extracted Entities", self.pdf_styles['Heading2']))
            
            for entity_type, entity_list in entities.items():
                story.append(Paragraph(f"<b>{entity_type}:</b> {', '.join(entity_list)}", self.pdf_styles['Normal']))

        # Generation Footer
        story.append(Spacer(1, 24))
        footer_text = f"Generated on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')} by LLM Documentation Ecosystem"
        story.append(Paragraph(footer_text, self.pdf_styles['Normal']))

        doc.build(story)
        return filepath.stat().st_size

    async def _generate_csv(self, workflow_result: Dict[str, Any], filepath: Path) -> int:
        """Generate CSV output."""
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write metadata headers
            writer.writerow(["Metadata"])
            writer.writerow(["Workflow Name", workflow_result.get("workflow_name", "")])
            writer.writerow(["Execution ID", workflow_result.get("execution_id", "")])
            writer.writerow(["Status", workflow_result.get("status", "")])
            writer.writerow(["Execution Time", workflow_result.get("execution_time", "")])
            writer.writerow(["Generated At", datetime.utcnow().isoformat()])
            writer.writerow([])  # Empty row

            # Write results data
            results = workflow_result.get("results", {})
            if isinstance(results, dict):
                writer.writerow(["Results"])
                writer.writerow(["Key", "Value"])
                for key, value in results.items():
                    writer.writerow([key, str(value)])
                writer.writerow([])  # Empty row

            # Write entities data
            entities = workflow_result.get("entities", {})
            if entities:
                writer.writerow(["Extracted Entities"])
                writer.writerow(["Type", "Values"])
                for entity_type, entity_list in entities.items():
                    writer.writerow([entity_type, ", ".join(entity_list)])

        return filepath.stat().st_size

    async def _generate_markdown(self, workflow_result: Dict[str, Any], filepath: Path) -> int:
        """Generate markdown output."""
        md_content = []
        
        # Title
        workflow_name = workflow_result.get("workflow_name", "Workflow Report")
        md_content.append(f"# {workflow_name.replace('_', ' ').title()}")
        md_content.append("")

        # Execution Summary
        md_content.append("## Execution Summary")
        md_content.append("")
        md_content.append(f"- **Execution ID**: {workflow_result.get('execution_id', 'N/A')}")
        md_content.append(f"- **Status**: {workflow_result.get('status', 'Unknown')}")
        md_content.append(f"- **Execution Time**: {workflow_result.get('execution_time', 'N/A')}")
        md_content.append(f"- **Confidence**: {workflow_result.get('confidence', 0):.2f}")
        md_content.append(f"- **Services Used**: {', '.join(workflow_result.get('services_used', []))}")
        md_content.append("")

        # Results
        results = workflow_result.get("results", {})
        if results:
            md_content.append("## Results")
            md_content.append("")
            
            if isinstance(results, dict):
                for key, value in results.items():
                    md_content.append(f"### {key}")
                    md_content.append("")
                    md_content.append(f"{value}")
                    md_content.append("")
            else:
                md_content.append(str(results))
                md_content.append("")

        # Entities
        entities = workflow_result.get("entities", {})
        if entities:
            md_content.append("## Extracted Entities")
            md_content.append("")
            
            for entity_type, entity_list in entities.items():
                md_content.append(f"- **{entity_type}**: {', '.join(entity_list)}")
            md_content.append("")

        # Footer
        md_content.append("---")
        md_content.append(f"*Generated on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')} by LLM Documentation Ecosystem*")

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("\n".join(md_content))

        return filepath.stat().st_size

    async def _generate_text(self, workflow_result: Dict[str, Any], filepath: Path) -> int:
        """Generate plain text output."""
        content = []
        
        # Header
        workflow_name = workflow_result.get("workflow_name", "Workflow Report")
        content.append(f"{workflow_name.replace('_', ' ').title()}")
        content.append("=" * len(workflow_name))
        content.append("")

        # Execution Summary
        content.append("EXECUTION SUMMARY")
        content.append("-" * 17)
        content.append(f"Execution ID: {workflow_result.get('execution_id', 'N/A')}")
        content.append(f"Status: {workflow_result.get('status', 'Unknown')}")
        content.append(f"Execution Time: {workflow_result.get('execution_time', 'N/A')}")
        content.append(f"Confidence: {workflow_result.get('confidence', 0):.2f}")
        content.append(f"Services Used: {', '.join(workflow_result.get('services_used', []))}")
        content.append("")

        # Results
        results = workflow_result.get("results", {})
        if results:
            content.append("RESULTS")
            content.append("-" * 7)
            content.append(str(results))
            content.append("")

        # Entities
        entities = workflow_result.get("entities", {})
        if entities:
            content.append("EXTRACTED ENTITIES")
            content.append("-" * 18)
            for entity_type, entity_list in entities.items():
                content.append(f"{entity_type}: {', '.join(entity_list)}")
            content.append("")

        # Footer
        content.append(f"Generated on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        content.append("by LLM Documentation Ecosystem")

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("\n".join(content))

        return filepath.stat().st_size

    async def _generate_zip(self, workflow_result: Dict[str, Any], filepath: Path) -> int:
        """Generate ZIP archive with multiple formats."""
        with zipfile.ZipFile(filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Generate temporary files for each format
            temp_dir = Path(tempfile.mkdtemp())
            
            try:
                # Generate JSON
                json_path = temp_dir / "results.json"
                await self._generate_json(workflow_result, json_path)
                zipf.write(json_path, "results.json")

                # Generate markdown
                md_path = temp_dir / "report.md"
                await self._generate_markdown(workflow_result, md_path)
                zipf.write(md_path, "report.md")

                # Generate CSV
                csv_path = temp_dir / "data.csv"
                await self._generate_csv(workflow_result, csv_path)
                zipf.write(csv_path, "data.csv")

                # Generate text
                txt_path = temp_dir / "summary.txt"
                await self._generate_text(workflow_result, txt_path)
                zipf.write(txt_path, "summary.txt")

                # Add metadata file
                metadata = {
                    "archive_created": datetime.utcnow().isoformat(),
                    "workflow_name": workflow_result.get("workflow_name"),
                    "execution_id": workflow_result.get("execution_id"),
                    "contents": [
                        "results.json - Complete workflow results in JSON format",
                        "report.md - Formatted markdown report",
                        "data.csv - Structured data in CSV format", 
                        "summary.txt - Plain text summary"
                    ]
                }
                
                metadata_path = temp_dir / "README.txt"
                with open(metadata_path, 'w') as f:
                    f.write(f"LLM Documentation Ecosystem - Workflow Results Archive\n")
                    f.write(f"Generated: {metadata['archive_created']}\n")
                    f.write(f"Workflow: {metadata['workflow_name']}\n")
                    f.write(f"Execution ID: {metadata['execution_id']}\n\n")
                    f.write("Contents:\n")
                    for item in metadata['contents']:
                        f.write(f"- {item}\n")
                
                zipf.write(metadata_path, "README.txt")

            finally:
                # Cleanup temp files
                for temp_file in temp_dir.glob("*"):
                    temp_file.unlink()
                temp_dir.rmdir()

        return filepath.stat().st_size

    async def get_file_info(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a generated file."""
        # Find file by ID in filename
        for filepath in self.output_directory.glob(f"*_{file_id}.*"):
            stat = filepath.stat()
            return {
                "file_id": file_id,
                "filename": filepath.name,
                "filepath": str(filepath),
                "format": filepath.suffix[1:],  # Remove the dot
                "size_bytes": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "exists": True
            }
        return None

    async def cleanup_expired_files(self):
        """Clean up expired output files."""
        current_time = datetime.utcnow()
        cleaned_count = 0

        for filepath in self.output_directory.glob("*"):
            try:
                file_age = datetime.fromtimestamp(filepath.stat().st_ctime)
                if current_time - file_age > self.file_retention:
                    filepath.unlink()
                    cleaned_count += 1
            except Exception as e:
                fire_and_forget(
                    "file_cleanup_error",
                    f"Error cleaning up file {filepath}: {str(e)}",
                    ServiceNames.INTERPRETER,
                    {"filepath": str(filepath), "error": str(e)}
                )

        if cleaned_count > 0:
            fire_and_forget(
                "file_cleanup_completed",
                f"Cleaned up {cleaned_count} expired output files",
                ServiceNames.INTERPRETER,
                {"cleaned_count": cleaned_count}
            )

    def get_supported_formats(self) -> List[str]:
        """Get list of supported output formats."""
        return list(self.supported_formats.keys())


# Create singleton instance
output_generator = OutputGenerator()
