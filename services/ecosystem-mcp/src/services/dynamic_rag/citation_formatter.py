"""
Citation Formatter (Phase 6.3)

Formats citations with temporal context and generates "see also" suggestions.
"""

import logging
from typing import List, Dict, Optional
from dataclasses import dataclass

from .answer_synthesizer import TemporalAnswer
from .document_finder import RelevantDocument

logger = logging.getLogger(__name__)


@dataclass
class FormattedCitation:
    """A formatted citation with temporal context."""
    citation_text: str
    format_type: str  # markdown, html, plain
    sources: List[Dict]
    see_also: List[Dict]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'citation_text': self.citation_text,
            'format_type': self.format_type,
            'sources': self.sources,
            'see_also': self.see_also
        }


class CitationFormatter:
    """
    Formats citations with temporal context.
    
    Features:
    - Multiple format types (Markdown, HTML, Plain Text)
    - Temporal attribution
    - Source document linking
    - "See also" suggestions
    - Inline and footnote styles
    """
    
    def __init__(self):
        logger.info("CitationFormatter initialized")
    
    def format_citations(
        self,
        answer: TemporalAnswer,
        format_type: str = "markdown",
        style: str = "footnote"
    ) -> FormattedCitation:
        """
        Format citations for an answer.
        
        Args:
            answer: Temporal answer with sources
            format_type: Output format (markdown/html/plain)
            style: Citation style (footnote/inline/bibliography)
        
        Returns:
            FormattedCitation with formatted text
        """
        logger.info(f"Formatting citations in {format_type} format")
        
        try:
            if format_type == "markdown":
                citation_text = self._format_markdown(answer, style)
            elif format_type == "html":
                citation_text = self._format_html(answer, style)
            else:  # plain
                citation_text = self._format_plain(answer, style)
            
            # Generate "see also" suggestions
            see_also = self._generate_see_also(answer)
            
            result = FormattedCitation(
                citation_text=citation_text,
                format_type=format_type,
                sources=answer.sources,
                see_also=see_also
            )
            
            logger.info(f"✅ Formatted {len(answer.sources)} citations")
            
            return result
            
        except Exception as e:
            logger.error(f"Error formatting citations: {e}")
            raise
    
    def _format_markdown(
        self,
        answer: TemporalAnswer,
        style: str
    ) -> str:
        """Format citations as Markdown."""
        parts = []
        
        # Answer text
        parts.append(answer.answer)
        parts.append("")
        
        # Temporal insights
        if answer.temporal_insights:
            parts.append("## Temporal Context")
            parts.append("")
            for insight in answer.temporal_insights:
                parts.append(f"- {insight}")
            parts.append("")
        
        # Evolution summary
        if answer.evolution_summary:
            parts.append("## Evolution Summary")
            parts.append("")
            parts.append(answer.evolution_summary)
            parts.append("")
        
        # Citations
        parts.append("## Sources")
        parts.append("")
        
        if style == "footnote":
            for source in answer.sources:
                parts.append(
                    f"[{source['index']}] `{source['file_path']}` "
                    f"(Relevance: {source['relevance_score']:.2f}, "
                    f"Modified: {source['last_modified'][:10] if source['last_modified'] else 'N/A'})"
                )
        else:  # inline
            for source in answer.sources:
                parts.append(f"- `{source['file_path']}` (Relevance: {source['relevance_score']:.2f})")
        
        parts.append("")
        
        # Confidence
        parts.append(f"**Confidence:** {answer.confidence:.0%}")
        parts.append(f"**Timeline ID:** `{answer.timeline_id}`")
        
        return "\n".join(parts)
    
    def _format_html(
        self,
        answer: TemporalAnswer,
        style: str
    ) -> str:
        """Format citations as HTML."""
        parts = []
        
        parts.append("<div class='temporal-answer'>")
        
        # Answer
        parts.append("<div class='answer'>")
        parts.append(f"<p>{self._escape_html(answer.answer)}</p>")
        parts.append("</div>")
        
        # Temporal insights
        if answer.temporal_insights:
            parts.append("<div class='temporal-context'>")
            parts.append("<h3>Temporal Context</h3>")
            parts.append("<ul>")
            for insight in answer.temporal_insights:
                parts.append(f"<li>{self._escape_html(insight)}</li>")
            parts.append("</ul>")
            parts.append("</div>")
        
        # Evolution summary
        if answer.evolution_summary:
            parts.append("<div class='evolution-summary'>")
            parts.append("<h3>Evolution Summary</h3>")
            parts.append(f"<p>{self._escape_html(answer.evolution_summary)}</p>")
            parts.append("</div>")
        
        # Sources
        parts.append("<div class='sources'>")
        parts.append("<h3>Sources</h3>")
        parts.append("<ol>")
        for source in answer.sources:
            parts.append(
                f"<li><code>{self._escape_html(source['file_path'])}</code> "
                f"<span class='relevance'>(Relevance: {source['relevance_score']:.2f})</span></li>"
            )
        parts.append("</ol>")
        parts.append("</div>")
        
        # Metadata
        parts.append("<div class='metadata'>")
        parts.append(f"<p><strong>Confidence:</strong> {answer.confidence:.0%}</p>")
        parts.append(f"<p><strong>Timeline ID:</strong> <code>{answer.timeline_id}</code></p>")
        parts.append("</div>")
        
        parts.append("</div>")
        
        return "\n".join(parts)
    
    def _format_plain(
        self,
        answer: TemporalAnswer,
        style: str
    ) -> str:
        """Format citations as plain text."""
        parts = []
        
        # Answer
        parts.append(answer.answer)
        parts.append("")
        parts.append("=" * 80)
        parts.append("")
        
        # Temporal insights
        if answer.temporal_insights:
            parts.append("TEMPORAL CONTEXT")
            parts.append("-" * 40)
            for insight in answer.temporal_insights:
                parts.append(f"  - {insight}")
            parts.append("")
        
        # Evolution summary
        if answer.evolution_summary:
            parts.append("EVOLUTION SUMMARY")
            parts.append("-" * 40)
            parts.append(answer.evolution_summary)
            parts.append("")
        
        # Sources
        parts.append("SOURCES")
        parts.append("-" * 40)
        for i, source in enumerate(answer.sources, 1):
            parts.append(
                f"[{i}] {source['file_path']} "
                f"(Relevance: {source['relevance_score']:.2f})"
            )
        
        parts.append("")
        parts.append(f"Confidence: {answer.confidence:.0%}")
        parts.append(f"Timeline ID: {answer.timeline_id}")
        
        return "\n".join(parts)
    
    def _generate_see_also(
        self,
        answer: TemporalAnswer
    ) -> List[Dict]:
        """Generate "see also" suggestions."""
        suggestions = []
        
        # Suggest related documents from sources
        for source in answer.sources[5:10]:  # Skip top 5, suggest next 5
            suggestions.append({
                'title': source['file_path'],
                'relevance': source['relevance_score'],
                'reason': 'Related documentation'
            })
        
        # Suggest exploring timeline periods
        suggestions.append({
            'title': f"Explore Timeline: {answer.timeline_id}",
            'reason': 'View full temporal analysis'
        })
        
        return suggestions
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#x27;'))

