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
from services.shared.clients import ServiceClients
from services.shared.constants_new import ServiceNames
from services.shared.logging import fire_and_forget


class OutputGenerator:
    """Generates various output formats from workflow execution results."""

    def __init__(self):
        # Service clients for ecosystem integration
        self.client = ServiceClients()
        self.doc_store_url = "http://doc-store:5087"
        self.prompt_store_url = "http://prompt-store:5110"
        
        # Output storage configuration (fallback for temporary files)
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
        """Generate output file from workflow result and store in doc_store."""
        try:
            if output_format not in self.supported_formats:
                raise ValueError(f"Unsupported output format: {output_format}")

            # Generate unique identifiers
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            file_id = str(uuid.uuid4())[:8]
            
            if filename_prefix:
                filename = f"{filename_prefix}_{timestamp}_{file_id}.{output_format}"
            else:
                workflow_name = workflow_result.get("workflow_name", "output")
                filename = f"{workflow_name}_{timestamp}_{file_id}.{output_format}"

            # Generate content in memory first
            content = await self._generate_content(workflow_result, output_format)
            
            # Create comprehensive provenance metadata
            provenance = await self._create_workflow_provenance(workflow_result)
            
            # Store in doc_store for persistence
            doc_store_result = await self._store_document_in_doc_store(
                content, filename, output_format, workflow_result, provenance
            )
            
            # Create enhanced metadata with doc_store integration
            download_info = {
                "file_id": file_id,
                "document_id": doc_store_result.get("document_id"),
                "filename": filename,
                "format": output_format,
                "size_bytes": len(content) if isinstance(content, (str, bytes)) else 0,
                "created_at": datetime.utcnow().isoformat(),
                "workflow_name": workflow_result.get("workflow_name", "unknown"),
                "storage_type": "doc_store",
                "download_url": f"/documents/download/{doc_store_result.get('document_id')}",
                "doc_store_url": f"{self.doc_store_url}/documents/{doc_store_result.get('document_id')}",
                "provenance": provenance,
                "metadata": {
                    "execution_id": workflow_result.get("execution_id"),
                    "user_id": workflow_result.get("user_id"),
                    "services_used": workflow_result.get("services_used", []),
                    "execution_time": workflow_result.get("execution_time"),
                    "status": workflow_result.get("status", "completed"),
                    "persistent": True,
                    "document_type": f"workflow_output_{output_format}"
                }
            }

            fire_and_forget(
                "persistent_document_created",
                f"Created persistent {output_format} document: {filename}",
                ServiceNames.INTERPRETER,
                {
                    "document_id": doc_store_result.get("document_id"),
                    "file_id": file_id,
                    "format": output_format,
                    "size_bytes": download_info["size_bytes"],
                    "workflow": workflow_result.get("workflow_name"),
                    "storage": "doc_store"
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

    # ============================================================================
    # DOC_STORE INTEGRATION AND PROVENANCE METHODS
    # ============================================================================

    async def _generate_content(self, workflow_result: Dict[str, Any], output_format: str) -> Union[str, bytes]:
        """Generate content in memory for the specified format."""
        if output_format == "json":
            return await self._generate_json_content(workflow_result)
        elif output_format == "pdf":
            return await self._generate_pdf_content(workflow_result)
        elif output_format == "csv":
            return await self._generate_csv_content(workflow_result)
        elif output_format == "markdown":
            return await self._generate_markdown_content(workflow_result)
        elif output_format == "txt":
            return await self._generate_text_content(workflow_result)
        elif output_format == "zip":
            return await self._generate_zip_content(workflow_result)
        else:
            raise ValueError(f"Unsupported format: {output_format}")

    async def _create_workflow_provenance(self, workflow_result: Dict[str, Any]) -> Dict[str, Any]:
        """Create comprehensive provenance metadata for the workflow execution."""
        provenance = {
            "workflow_execution": {
                "execution_id": workflow_result.get("execution_id"),
                "workflow_name": workflow_result.get("workflow_name"),
                "started_at": workflow_result.get("started_at"),
                "completed_at": datetime.utcnow().isoformat(),
                "execution_time": workflow_result.get("execution_time"),
                "status": workflow_result.get("status")
            },
            "services_chain": workflow_result.get("services_used", []),
            "user_context": {
                "user_id": workflow_result.get("user_id"),
                "query": workflow_result.get("original_query"),
                "intent": workflow_result.get("intent"),
                "entities": workflow_result.get("entities", {})
            },
            "prompts_used": await self._extract_prompts_from_workflow(workflow_result),
            "data_lineage": await self._create_data_lineage(workflow_result),
            "quality_metrics": {
                "confidence": workflow_result.get("confidence", 0.0),
                "completeness": 1.0,  # All steps completed
                "accuracy": workflow_result.get("accuracy", 0.0)
            },
            "created_by": "interpreter_service",
            "creation_timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0"
        }
        
        return provenance

    async def _extract_prompts_from_workflow(self, workflow_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract all prompts used in the workflow execution."""
        prompts_used = []
        
        # Get steps from workflow result
        steps = workflow_result.get("steps_executed", [])
        
        for step in steps:
            if "prompt_id" in step or "prompt_template" in step:
                prompt_info = {
                    "step_index": step.get("step_index"),
                    "service": step.get("service"),
                    "action": step.get("action"),
                    "prompt_id": step.get("prompt_id"),
                    "prompt_template": step.get("prompt_template"),
                    "prompt_variables": step.get("prompt_variables", {}),
                    "timestamp": step.get("timestamp")
                }
                prompts_used.append(prompt_info)
        
        # Try to get additional prompt information from prompt_store
        try:
            for prompt_info in prompts_used:
                if prompt_info.get("prompt_id"):
                    prompt_details = await self._get_prompt_details(prompt_info["prompt_id"])
                    prompt_info.update(prompt_details)
        except Exception as e:
            fire_and_forget(
                "prompt_details_error",
                f"Failed to get prompt details: {str(e)}",
                ServiceNames.INTERPRETER,
                {"error": str(e)}
            )
        
        return prompts_used

    async def _get_prompt_details(self, prompt_id: str) -> Dict[str, Any]:
        """Get detailed prompt information from prompt_store."""
        try:
            response = await self.client.get_json(f"{self.prompt_store_url}/prompts/{prompt_id}")
            return {
                "prompt_content": response.get("content", ""),
                "prompt_category": response.get("category", ""),
                "prompt_version": response.get("version", ""),
                "prompt_author": response.get("author", ""),
                "prompt_description": response.get("description", "")
            }
        except Exception:
            return {}

    async def _create_data_lineage(self, workflow_result: Dict[str, Any]) -> Dict[str, Any]:
        """Create data lineage information showing data flow through workflow."""
        lineage = {
            "input_sources": [],
            "processing_steps": [],
            "output_artifacts": [],
            "transformations": []
        }
        
        # Extract data sources from workflow steps
        steps = workflow_result.get("steps_executed", [])
        for step in steps:
            step_lineage = {
                "step_id": f"step_{step.get('step_index', 0)}",
                "service": step.get("service"),
                "action": step.get("action"),
                "inputs": step.get("inputs", []),
                "outputs": step.get("outputs", []),
                "transformations": step.get("transformations", []),
                "timestamp": step.get("timestamp")
            }
            lineage["processing_steps"].append(step_lineage)
        
        return lineage

    async def _store_document_in_doc_store(self, content: Union[str, bytes], filename: str, 
                                         format_type: str, workflow_result: Dict[str, Any], 
                                         provenance: Dict[str, Any]) -> Dict[str, Any]:
        """Store the generated document in doc_store for persistence."""
        try:
            # Create document metadata for doc_store
            document_metadata = {
                "title": f"Workflow Output: {workflow_result.get('workflow_name', 'Unknown')}",
                "description": f"Generated {format_type.upper()} output from {workflow_result.get('workflow_name')} workflow",
                "content_type": self._get_content_type(format_type),
                "format": format_type,
                "filename": filename,
                "category": "workflow_output",
                "tags": [
                    "workflow_generated",
                    f"format_{format_type}",
                    f"workflow_{workflow_result.get('workflow_name', 'unknown')}",
                    f"user_{workflow_result.get('user_id', 'anonymous')}"
                ],
                "author": workflow_result.get("user_id", "system"),
                "source": "interpreter_workflow_execution",
                "quality_score": workflow_result.get("confidence", 0.8),
                "workflow_provenance": provenance,
                "execution_metadata": {
                    "execution_id": workflow_result.get("execution_id"),
                    "services_used": workflow_result.get("services_used", []),
                    "execution_time": workflow_result.get("execution_time"),
                    "generated_at": datetime.utcnow().isoformat()
                }
            }
            
            # Convert content to appropriate format for storage
            if isinstance(content, bytes):
                # For binary content (PDFs, ZIPs), encode as base64
                import base64
                content_for_storage = base64.b64encode(content).decode('utf-8')
                document_metadata["content_encoding"] = "base64"
            else:
                content_for_storage = content
                document_metadata["content_encoding"] = "utf-8"
            
            # Store in doc_store
            store_request = {
                "content": content_for_storage,
                "metadata": document_metadata
            }
            
            response = await self.client.post_json(f"{self.doc_store_url}/documents", store_request)
            
            if response.get("success"):
                return {
                    "document_id": response.get("document_id"),
                    "storage_url": f"{self.doc_store_url}/documents/{response.get('document_id')}",
                    "stored_at": datetime.utcnow().isoformat()
                }
            else:
                raise Exception(f"Doc store failed: {response.get('error', 'Unknown error')}")
                
        except Exception as e:
            fire_and_forget(
                "doc_store_error",
                f"Failed to store document in doc_store: {str(e)}",
                ServiceNames.INTERPRETER,
                {"error": str(e), "filename": filename}
            )
            # Fallback: return temporary file info
            return {
                "document_id": None,
                "storage_url": None,
                "error": str(e),
                "fallback": True
            }

    def _get_content_type(self, format_type: str) -> str:
        """Get MIME content type for format."""
        content_types = {
            "json": "application/json",
            "pdf": "application/pdf",
            "csv": "text/csv",
            "markdown": "text/markdown",
            "txt": "text/plain",
            "zip": "application/zip"
        }
        return content_types.get(format_type, "application/octet-stream")

    # ============================================================================
    # CONTENT GENERATION METHODS (Memory-based)
    # ============================================================================

    async def _generate_json_content(self, workflow_result: Dict[str, Any]) -> str:
        """Generate JSON content in memory."""
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
        return json.dumps(output_data, indent=2, ensure_ascii=False)

    async def _generate_pdf_content(self, workflow_result: Dict[str, Any]) -> bytes:
        """Generate PDF content in memory."""
        from io import BytesIO
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
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

        # Generation Footer
        story.append(Spacer(1, 24))
        footer_text = f"Generated on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')} by LLM Documentation Ecosystem"
        story.append(Paragraph(footer_text, self.pdf_styles['Normal']))

        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()

    async def _generate_csv_content(self, workflow_result: Dict[str, Any]) -> str:
        """Generate CSV content in memory."""
        output = StringIO()
        writer = csv.writer(output)
        
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

        return output.getvalue()

    async def _generate_markdown_content(self, workflow_result: Dict[str, Any]) -> str:
        """Generate markdown content in memory."""
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

        # Footer
        md_content.append("---")
        md_content.append(f"*Generated on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')} by LLM Documentation Ecosystem*")

        return "\n".join(md_content)

    async def _generate_text_content(self, workflow_result: Dict[str, Any]) -> str:
        """Generate plain text content in memory."""
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

        # Footer
        content.append(f"Generated on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        content.append("by LLM Documentation Ecosystem")

        return "\n".join(content)

    async def _generate_zip_content(self, workflow_result: Dict[str, Any]) -> bytes:
        """Generate ZIP archive content in memory."""
        from io import BytesIO
        
        zip_buffer = BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Generate and add JSON
            json_content = await self._generate_json_content(workflow_result)
            zipf.writestr("results.json", json_content)

            # Generate and add markdown
            md_content = await self._generate_markdown_content(workflow_result)
            zipf.writestr("report.md", md_content)

            # Generate and add CSV
            csv_content = await self._generate_csv_content(workflow_result)
            zipf.writestr("data.csv", csv_content)

            # Generate and add text
            txt_content = await self._generate_text_content(workflow_result)
            zipf.writestr("summary.txt", txt_content)

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
            
            readme_content = f"LLM Documentation Ecosystem - Workflow Results Archive\n"
            readme_content += f"Generated: {metadata['archive_created']}\n"
            readme_content += f"Workflow: {metadata['workflow_name']}\n"
            readme_content += f"Execution ID: {metadata['execution_id']}\n\n"
            readme_content += "Contents:\n"
            for item in metadata['contents']:
                readme_content += f"- {item}\n"
            
            zipf.writestr("README.txt", readme_content)

        zip_buffer.seek(0)
        return zip_buffer.getvalue()

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
