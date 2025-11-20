"""
Citation Manager

Tracks source documents used in generated documentation for full transparency
and traceability. Stores data in EXISTING documentation_citations table.
"""

import logging
from typing import Dict, List, Optional, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...storage.database import get_database
from ...storage.models_templates import DocumentationCitationModel

logger = logging.getLogger(__name__)


class CitationManager:
    """
    Manages source citations for generated documentation.
    
    Provides full transparency by linking generated content back to
    source documents. Stores data in EXISTING documentation_citations
    table created in Phase 1.
    """
    
    def __init__(self):
        """Initialize citation manager."""
        logger.info("CitationManager initialized")
    
    async def add_citation(
        self,
        artifact_id: UUID,
        document_id: UUID,
        section_name: str,
        relevance_score: float,
        excerpt: Optional[str] = None,
        start_line: Optional[int] = None,
        end_line: Optional[int] = None
    ) -> UUID:
        """
        Add a citation linking generated content to source document.
        
        Args:
            artifact_id: Generated documentation artifact ID
            document_id: Source document ID
            section_name: Section where this source was used
            relevance_score: Relevance/confidence score (0.0-1.0)
            excerpt: Optional excerpt from source document
            start_line: Optional starting line number
            end_line: Optional ending line number
        
        Returns:
            Citation ID
        """
        async with get_database().session() as session:
            citation = DocumentationCitationModel(
                artifact_id=artifact_id,
                document_id=document_id,
                section_name=section_name,
                relevance_score=relevance_score,
                excerpt=excerpt,
                start_line=start_line,
                end_line=end_line
            )
            
            session.add(citation)
            await session.commit()
            await session.refresh(citation)
            
            logger.debug(
                f"✅ Citation added: artifact={artifact_id}, "
                f"document={document_id}, relevance={relevance_score:.2f}"
            )
            
            return citation.id
    
    async def add_citations_batch(
        self,
        artifact_id: UUID,
        sources: List[Dict[str, Any]],
        section_name: str
    ) -> List[UUID]:
        """
        Add multiple citations at once (batch operation).
        
        Args:
            artifact_id: Generated documentation artifact ID
            sources: List of source documents with metadata
            section_name: Section where sources were used
        
        Returns:
            List of citation IDs
        """
        citation_ids = []
        
        async with get_database().session() as session:
            for idx, source in enumerate(sources):
                citation = DocumentationCitationModel(
                    artifact_id=artifact_id,
                    document_id=UUID(source["document_id"]),
                    section_name=section_name,
                    relevance_score=source.get("relevance_score", source.get("score", 0.0)),
                    excerpt=source.get("content", source.get("excerpt"))[:500] if source.get("content") or source.get("excerpt") else None,
                    citation_order=idx + 1
                )
                
                session.add(citation)
                citation_ids.append(citation.id)
            
            await session.commit()
            
            logger.info(
                f"✅ Batch citations added: {len(citation_ids)} citations "
                f"for artifact={artifact_id}"
            )
        
        return citation_ids
    
    async def get_citations_for_artifact(
        self,
        artifact_id: UUID,
        section_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all citations for a generated artifact.
        
        Args:
            artifact_id: Artifact ID
            section_name: Optional filter by section
        
        Returns:
            List of citations with details
        """
        async with get_database().session() as session:
            query = select(DocumentationCitationModel).filter(
                DocumentationCitationModel.artifact_id == artifact_id
            )
            
            if section_name:
                query = query.filter(
                    DocumentationCitationModel.section_name == section_name
                )
            
            query = query.order_by(DocumentationCitationModel.citation_order)
            
            result = await session.execute(query)
            citations = result.scalars().all()
            
            return [
                {
                    "id": str(c.id),
                    "document_id": str(c.document_id),
                    "section_name": c.section_name,
                    "relevance_score": c.relevance_score,
                    "excerpt": c.excerpt,
                    "start_line": c.start_line,
                    "end_line": c.end_line,
                    "citation_order": c.citation_order,
                    "created_at": c.created_at.isoformat() if c.created_at else None
                }
                for c in citations
            ]
    
    async def format_citations_section(
        self,
        artifact_id: UUID,
        style: str = "endnotes"
    ) -> str:
        """
        Format citations as a documentation section.
        
        Args:
            artifact_id: Artifact ID
            style: Citation style ("endnotes", "footnotes", "inline")
        
        Returns:
            Formatted citations section in markdown
        """
        citations = await self.get_citations_for_artifact(artifact_id)
        
        if not citations:
            return ""
        
        if style == "endnotes":
            return self._format_endnotes(citations)
        elif style == "footnotes":
            return self._format_footnotes(citations)
        elif style == "inline":
            return self._format_inline(citations)
        else:
            return self._format_endnotes(citations)
    
    def _format_endnotes(self, citations: List[Dict[str, Any]]) -> str:
        """Format citations as endnotes."""
        lines = [
            "---",
            "",
            "## Sources & References",
            "",
            "This documentation was generated from the following source documents:",
            ""
        ]
        
        # Group by section
        sections = {}
        for citation in citations:
            section = citation["section_name"]
            if section not in sections:
                sections[section] = []
            sections[section].append(citation)
        
        for section_name, section_citations in sections.items():
            lines.append(f"### {section_name}")
            lines.append("")
            
            for idx, citation in enumerate(section_citations, 1):
                relevance = citation["relevance_score"]
                relevance_pct = int(relevance * 100)
                
                line = f"{idx}. Document `{citation['document_id'][:8]}...` (relevance: {relevance_pct}%)"
                
                if citation["excerpt"]:
                    excerpt = citation["excerpt"][:100]
                    line += f"\n   > {excerpt}..."
                
                lines.append(line)
            
            lines.append("")
        
        lines.append("---")
        lines.append("")
        lines.append("*Generated by Ecosystem MCP - Adaptive Documentation System*")
        
        return "\n".join(lines)
    
    def _format_footnotes(self, citations: List[Dict[str, Any]]) -> str:
        """Format citations as footnotes."""
        # Simplified footnote format
        lines = []
        
        for idx, citation in enumerate(citations, 1):
            lines.append(
                f"[^{idx}]: Source: `{citation['document_id'][:8]}...` "
                f"(relevance: {int(citation['relevance_score'] * 100)}%)"
            )
        
        return "\n".join(lines)
    
    def _format_inline(self, citations: List[Dict[str, Any]]) -> str:
        """Format citations for inline use."""
        # Returns citation markers for inline use
        return ", ".join([
            f"[{i+1}]" for i in range(len(citations))
        ])
    
    async def get_citation_statistics(
        self,
        artifact_id: UUID
    ) -> Dict[str, Any]:
        """
        Get statistics about citations for an artifact.
        
        Args:
            artifact_id: Artifact ID
        
        Returns:
            Citation statistics
        """
        citations = await self.get_citations_for_artifact(artifact_id)
        
        if not citations:
            return {
                "total_citations": 0,
                "avg_relevance": 0.0,
                "sections_with_citations": 0
            }
        
        total = len(citations)
        avg_relevance = sum(c["relevance_score"] for c in citations) / total
        sections = len(set(c["section_name"] for c in citations))
        
        return {
            "total_citations": total,
            "avg_relevance": avg_relevance,
            "sections_with_citations": sections,
            "min_relevance": min(c["relevance_score"] for c in citations),
            "max_relevance": max(c["relevance_score"] for c in citations),
            "unique_documents": len(set(c["document_id"] for c in citations))
        }
    
    async def verify_citations(
        self,
        artifact_id: UUID,
        min_relevance: float = 0.5
    ) -> Dict[str, Any]:
        """
        Verify citation quality and completeness.
        
        Args:
            artifact_id: Artifact ID
            min_relevance: Minimum acceptable relevance score
        
        Returns:
            Verification results with warnings
        """
        citations = await self.get_citations_for_artifact(artifact_id)
        
        warnings = []
        errors = []
        
        if not citations:
            errors.append("No citations found - documentation has no source attribution")
            return {
                "valid": False,
                "errors": errors,
                "warnings": warnings
            }
        
        # Check relevance scores
        low_relevance = [c for c in citations if c["relevance_score"] < min_relevance]
        if low_relevance:
            warnings.append(
                f"{len(low_relevance)} citations have low relevance scores (< {min_relevance})"
            )
        
        # Check for sections without citations
        sections = set(c["section_name"] for c in citations)
        if len(sections) < 3:  # Arbitrary threshold
            warnings.append(
                f"Only {len(sections)} sections have citations - some sections may lack sources"
            )
        
        # Check excerpt availability
        missing_excerpts = sum(1 for c in citations if not c["excerpt"])
        if missing_excerpts > len(citations) * 0.5:
            warnings.append(
                f"{missing_excerpts} citations missing excerpts - harder to verify sources"
            )
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "total_citations": len(citations),
            "sections_covered": len(sections)
        }


# Singleton instance
_citation_manager: Optional[CitationManager] = None


def get_citation_manager() -> CitationManager:
    """Get or create singleton citation manager."""
    global _citation_manager
    if _citation_manager is None:
        _citation_manager = CitationManager()
    return _citation_manager

