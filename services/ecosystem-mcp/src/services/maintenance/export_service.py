"""
Export Service

Export documentation in various formats:
- Export to Markdown
- Export to HTML
- Export to PDF
- Export to DOCX
- GitHub Pages integration
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID
from pathlib import Path
import json

from sqlalchemy.ext.asyncio import AsyncSession

from ...storage.db_models import DocumentModel
from ...storage.repositories import DocumentRepository
from ...storage.repositories.timeline_repository import TimelineRepository, TimePeriodRepository
from ...storage import get_database

logger = logging.getLogger(__name__)


class ExportService:
    """
    Export documentation in various formats.
    
    Features:
    - Multiple export formats
    - Timeline-aware export
    - Customizable templates
    - Batch export support
    """
    
    def __init__(self):
        """Initialize export service."""
        self.logger = logging.getLogger(__name__)
    
    async def export_documentation(
        self,
        export_format: str,  # markdown, html, pdf, docx, json
        service_name: Optional[str] = None,
        timeline_id: Optional[UUID] = None,
        output_path: Optional[str] = None,
        include_metadata: bool = True
    ) -> Dict[str, Any]:
        """
        Export documentation.
        
        Args:
            export_format: Format to export to
            service_name: Optional service filter
            timeline_id: Optional timeline filter
            output_path: Optional output directory
            include_metadata: Whether to include metadata
        
        Returns:
            Export results with file paths
        """
        try:
            self.logger.info(f"📤 Exporting documentation (format={export_format}, service={service_name})")
            
            # Get documents to export
            documents = await self._get_documents_for_export(service_name, timeline_id)
            
            self.logger.info(f"   📄 Exporting {len(documents)} documents")
            
            # Export based on format
            if export_format == "markdown":
                result = await self._export_markdown(documents, output_path, include_metadata)
            elif export_format == "html":
                result = await self._export_html(documents, output_path, include_metadata)
            elif export_format == "json":
                result = await self._export_json(documents, output_path, include_metadata)
            elif export_format == "pdf":
                result = await self._export_pdf(documents, output_path, include_metadata)
            elif export_format == "docx":
                result = await self._export_docx(documents, output_path, include_metadata)
            else:
                raise ValueError(f"Unsupported export format: {export_format}")
            
            return {
                "export_format": export_format,
                "documents_exported": len(documents),
                "output_files": result["files"],
                "total_size_bytes": result.get("total_size", 0),
                "metadata": {
                    "service_name": service_name,
                    "timeline_id": str(timeline_id) if timeline_id else None,
                    "exported_at": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to export documentation: {e}", exc_info=True)
            raise
    
    async def _get_documents_for_export(
        self,
        service_name: Optional[str],
        timeline_id: Optional[UUID]
    ) -> List[DocumentModel]:
        """Get documents to export."""
        async with get_database().session() as session:
            doc_repo = DocumentRepository(session)
            
            if timeline_id:
                # Get documents from timeline
                from ...storage.repositories.timeline_repository import DocumentPlacementRepository
                period_repo = TimePeriodRepository(session)
                placement_repo = DocumentPlacementRepository(session)
                
                # Get all periods
                periods = await period_repo.get_by_timeline(timeline_id)
                
                # Get all documents
                document_ids = set()
                for period in periods:
                    placements = await placement_repo.get_by_period(period.id, limit=10000)
                    for placement in placements:
                        document_ids.add(placement.document_id)
                
                # Fetch documents
                documents = []
                for doc_id in document_ids:
                    doc = await doc_repo.get_by_id(doc_id)
                    if doc:
                        documents.append(doc)
                
                return documents
            
            elif service_name:
                return await doc_repo.get_by_service(service_name, limit=10000)
            else:
                return await doc_repo.get_all(limit=10000)
    
    async def _export_markdown(
        self,
        documents: List[DocumentModel],
        output_path: Optional[str],
        include_metadata: bool
    ) -> Dict[str, Any]:
        """Export to Markdown format."""
        files = []
        total_size = 0
        
        for doc in documents:
            # Generate markdown content
            content = self._generate_markdown(doc, include_metadata)
            
            # Simulate file creation (in production, would write to disk)
            file_info = {
                "path": f"{output_path or '.'}/{Path(doc.file_path).stem}.md",
                "size": len(content.encode('utf-8')),
                "format": "markdown"
            }
            
            files.append(file_info)
            total_size += file_info["size"]
        
        return {
            "files": files,
            "total_size": total_size
        }
    
    async def _export_html(
        self,
        documents: List[DocumentModel],
        output_path: Optional[str],
        include_metadata: bool
    ) -> Dict[str, Any]:
        """Export to HTML format."""
        files = []
        total_size = 0
        
        for doc in documents:
            # Generate HTML content
            content = self._generate_html(doc, include_metadata)
            
            file_info = {
                "path": f"{output_path or '.'}/{Path(doc.file_path).stem}.html",
                "size": len(content.encode('utf-8')),
                "format": "html"
            }
            
            files.append(file_info)
            total_size += file_info["size"]
        
        # Generate index.html
        index_content = self._generate_html_index(documents)
        index_info = {
            "path": f"{output_path or '.'}/index.html",
            "size": len(index_content.encode('utf-8')),
            "format": "html"
        }
        files.append(index_info)
        total_size += index_info["size"]
        
        return {
            "files": files,
            "total_size": total_size
        }
    
    async def _export_json(
        self,
        documents: List[DocumentModel],
        output_path: Optional[str],
        include_metadata: bool
    ) -> Dict[str, Any]:
        """Export to JSON format."""
        # Generate JSON export
        export_data = {
            "documents": [
                {
                    "id": str(doc.id),
                    "file_path": doc.file_path,
                    "service_name": doc.service_name,
                    "content": doc.normalized_content,
                    "created_at": doc.created_at.isoformat() if doc.created_at else None,
                    "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
                    "metadata": {
                        "ingestion_mode": doc.ingestion_mode,
                        "file_size": doc.file_size
                    } if include_metadata else {}
                }
                for doc in documents
            ],
            "export_metadata": {
                "exported_at": datetime.utcnow().isoformat(),
                "total_documents": len(documents)
            }
        }
        
        content = json.dumps(export_data, indent=2)
        
        file_info = {
            "path": f"{output_path or '.'}/documentation_export.json",
            "size": len(content.encode('utf-8')),
            "format": "json"
        }
        
        return {
            "files": [file_info],
            "total_size": file_info["size"]
        }
    
    async def _export_pdf(
        self,
        documents: List[DocumentModel],
        output_path: Optional[str],
        include_metadata: bool
    ) -> Dict[str, Any]:
        """Export to PDF format (placeholder)."""
        # Note: Actual PDF generation would require libraries like reportlab or weasyprint
        return {
            "files": [{
                "path": f"{output_path or '.'}/documentation.pdf",
                "size": 0,
                "format": "pdf",
                "note": "PDF generation requires additional libraries (reportlab/weasyprint)"
            }],
            "total_size": 0
        }
    
    async def _export_docx(
        self,
        documents: List[DocumentModel],
        output_path: Optional[str],
        include_metadata: bool
    ) -> Dict[str, Any]:
        """Export to DOCX format (placeholder)."""
        # Note: Actual DOCX generation would require python-docx library
        return {
            "files": [{
                "path": f"{output_path or '.'}/documentation.docx",
                "size": 0,
                "format": "docx",
                "note": "DOCX generation requires python-docx library"
            }],
            "total_size": 0
        }
    
    def _generate_markdown(self, doc: DocumentModel, include_metadata: bool) -> str:
        """Generate Markdown content."""
        content = []
        
        # Title
        content.append(f"# {Path(doc.file_path).stem}\n")
        
        # Metadata
        if include_metadata:
            content.append("## Metadata\n")
            content.append(f"- **Service:** {doc.service_name}\n")
            content.append(f"- **Path:** `{doc.file_path}`\n")
            content.append(f"- **Last Updated:** {doc.updated_at or doc.created_at}\n")
            content.append("\n---\n\n")
        
        # Content
        content.append("## Content\n\n")
        content.append(doc.normalized_content or "No content available")
        
        return "\n".join(content)
    
    def _generate_html(self, doc: DocumentModel, include_metadata: bool) -> str:
        """Generate HTML content."""
        metadata_html = ""
        if include_metadata:
            metadata_html = f"""
            <div class="metadata">
                <p><strong>Service:</strong> {doc.service_name}</p>
                <p><strong>Path:</strong> <code>{doc.file_path}</code></p>
                <p><strong>Last Updated:</strong> {doc.updated_at or doc.created_at}</p>
            </div>
            <hr>
            """
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{Path(doc.file_path).stem}</title>
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
                .metadata {{ background: #f5f5f5; padding: 15px; border-radius: 5px; }}
                code {{ background: #eee; padding: 2px 5px; border-radius: 3px; }}
            </style>
        </head>
        <body>
            <h1>{Path(doc.file_path).stem}</h1>
            {metadata_html}
            <div class="content">
                <pre>{doc.normalized_content or 'No content available'}</pre>
            </div>
        </body>
        </html>
        """
    
    def _generate_html_index(self, documents: List[DocumentModel]) -> str:
        """Generate HTML index page."""
        doc_links = "\n".join([
            f'<li><a href="{Path(doc.file_path).stem}.html">{Path(doc.file_path).stem}</a> - {doc.service_name}</li>'
            for doc in documents
        ])
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Documentation Index</title>
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
                ul {{ list-style: none; padding: 0; }}
                li {{ margin: 10px 0; padding: 10px; background: #f5f5f5; border-radius: 5px; }}
                a {{ text-decoration: none; color: #0066cc; font-weight: bold; }}
            </style>
        </head>
        <body>
            <h1>Documentation Index</h1>
            <p>Total Documents: {len(documents)}</p>
            <ul>
                {doc_links}
            </ul>
        </body>
        </html>
        """
    
    async def export_github_pages(
        self,
        service_name: str,
        output_path: str = "./docs"
    ) -> Dict[str, Any]:
        """
        Export for GitHub Pages.
        
        Args:
            service_name: Service to export
            output_path: Output directory
        
        Returns:
            Export result with GitHub Pages configuration
        """
        try:
            self.logger.info(f"📤 Exporting for GitHub Pages: {service_name}")
            
            # Export as HTML
            result = await self.export_documentation(
                export_format="html",
                service_name=service_name,
                output_path=output_path,
                include_metadata=True
            )
            
            # Generate _config.yml for Jekyll
            config_content = f"""
title: {service_name} Documentation
description: Auto-generated documentation
theme: jekyll-theme-cayman
            """
            
            return {
                **result,
                "github_pages_config": {
                    "config_file": f"{output_path}/_config.yml",
                    "config_content": config_content,
                    "instructions": [
                        "1. Commit files to 'docs/' directory",
                        "2. Enable GitHub Pages in repository settings",
                        "3. Set source to 'main branch /docs folder'",
                        "4. Visit https://<username>.github.io/<repo>"
                    ]
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to export for GitHub Pages: {e}", exc_info=True)
            raise

