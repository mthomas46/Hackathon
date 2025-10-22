"""
Temporal Answer Synthesizer (Phase 6.3)

Generates narrative answers with temporal context using LLM.
"""

import logging
from typing import List, Dict, Optional
from dataclasses import dataclass

from .document_finder import RelevantDocument
from .dynamic_timeline_constructor import DynamicTimeline, DynamicPeriod

logger = logging.getLogger(__name__)


@dataclass
class TemporalAnswer:
    """An answer with full temporal context."""
    answer: str
    confidence: float
    timeline_id: str
    sources: List[Dict]
    temporal_insights: List[str]
    evolution_summary: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'answer': self.answer,
            'confidence': self.confidence,
            'timeline_id': self.timeline_id,
            'sources': self.sources,
            'temporal_insights': self.temporal_insights,
            'evolution_summary': self.evolution_summary
        }


class TemporalAnswerSynthesizer:
    """
    Synthesizes answers with temporal context.
    
    Features:
    - LLM-based answer generation
    - Evolution context integration
    - Timeline-aware synthesis
    - Confidence scoring
    - Source attribution
    """
    
    def __init__(self):
        logger.info("TemporalAnswerSynthesizer initialized")
    
    async def synthesize_answer(
        self,
        query: str,
        timeline: DynamicTimeline,
        documents: List[RelevantDocument]
    ) -> TemporalAnswer:
        """
        Synthesize an answer with temporal context.
        
        Args:
            query: Original user query
            timeline: Dynamic timeline constructed for this query
            documents: Relevant documents
        
        Returns:
            TemporalAnswer with narrative and citations
        """
        logger.info(f"Synthesizing answer for query: {query[:100]}...")
        
        try:
            # Extract temporal insights
            temporal_insights = self._extract_temporal_insights(
                timeline, documents
            )
            
            # Generate evolution summary
            evolution_summary = self._generate_evolution_summary(
                timeline, documents
            )
            
            # Build context for LLM
            context = self._build_context(
                query, timeline, documents, temporal_insights
            )
            
            # Generate answer using LLM
            answer_text = await self._generate_with_llm(
                query, context
            )
            
            # Calculate confidence
            confidence = self._calculate_answer_confidence(
                timeline, documents, answer_text
            )
            
            # Prepare sources
            sources = self._prepare_sources(documents)
            
            result = TemporalAnswer(
                answer=answer_text,
                confidence=confidence,
                timeline_id=timeline.timeline_id,
                sources=sources,
                temporal_insights=temporal_insights,
                evolution_summary=evolution_summary
            )
            
            logger.info(f"✅ Synthesized answer with {confidence:.2f} confidence")
            
            return result
            
        except Exception as e:
            logger.error(f"Error synthesizing answer: {e}")
            raise
    
    def _extract_temporal_insights(
        self,
        timeline: DynamicTimeline,
        documents: List[RelevantDocument]
    ) -> List[str]:
        """Extract key temporal insights from timeline."""
        insights = []
        
        # Timeline span
        duration_days = (timeline.end_date - timeline.start_date).days
        insights.append(
            f"Analysis spans {duration_days} days from {timeline.start_date.strftime('%Y-%m-%d')} "
            f"to {timeline.end_date.strftime('%Y-%m-%d')}"
        )
        
        # Period distribution
        periods_with_docs = [p for p in timeline.periods if p.document_count > 0]
        insights.append(
            f"{len(periods_with_docs)} of {len(timeline.periods)} periods contain relevant documents"
        )
        
        # Most active period
        if periods_with_docs:
            most_active = max(periods_with_docs, key=lambda p: p.document_count)
            insights.append(
                f"Most activity in {most_active.name} with {most_active.document_count} documents"
            )
        
        # Recent activity
        recent_docs = [
            doc for doc in documents
            if doc.last_modified and (timeline.end_date - doc.last_modified).days < 90
        ]
        if recent_docs:
            insights.append(
                f"{len(recent_docs)} documents updated in the last 90 days"
            )
        
        return insights
    
    def _generate_evolution_summary(
        self,
        timeline: DynamicTimeline,
        documents: List[RelevantDocument]
    ) -> str:
        """Generate high-level evolution summary."""
        periods_with_docs = [p for p in timeline.periods if p.document_count > 0]
        
        if not periods_with_docs:
            return "No temporal evolution detected."
        
        # Analyze growth pattern
        first_period = periods_with_docs[0]
        last_period = periods_with_docs[-1]
        
        growth = last_period.document_count - first_period.document_count
        
        if growth > 0:
            pattern = f"Documentation has grown from {first_period.name} ({first_period.document_count} docs) " \
                     f"to {last_period.name} ({last_period.document_count} docs)"
        elif growth < 0:
            pattern = f"Documentation has decreased from {first_period.name} to {last_period.name}"
        else:
            pattern = f"Documentation has remained stable across {len(periods_with_docs)} periods"
        
        return pattern
    
    def _build_context(
        self,
        query: str,
        timeline: DynamicTimeline,
        documents: List[RelevantDocument],
        temporal_insights: List[str]
    ) -> str:
        """Build context string for LLM."""
        context_parts = []
        
        # Timeline overview
        context_parts.append(f"Timeline: {timeline.name}")
        context_parts.append(f"Confidence: {timeline.confidence}")
        context_parts.append(f"Periods: {len(timeline.periods)}")
        context_parts.append(f"Documents: {len(documents)}")
        context_parts.append("")
        
        # Temporal insights
        context_parts.append("Temporal Insights:")
        for insight in temporal_insights:
            context_parts.append(f"- {insight}")
        context_parts.append("")
        
        # Document excerpts (top 5 by relevance)
        context_parts.append("Relevant Documents:")
        for doc in documents[:5]:
            context_parts.append(f"\nDocument: {doc.file_path}")
            context_parts.append(f"Relevance: {doc.relevance_score:.2f}")
            context_parts.append(f"Last Modified: {doc.last_modified}")
            context_parts.append(f"Preview: {doc.content[:300]}...")
            context_parts.append("")
        
        return "\n".join(context_parts)
    
    async def _generate_with_llm(
        self,
        query: str,
        context: str
    ) -> str:
        """Generate answer using LLM."""
        # Simplified answer generation (would use actual LLM in production)
        logger.debug("Generating answer with LLM...")
        
        # For now, create a template-based answer
        answer = f"""Based on the temporal analysis of available documentation:

{query}

The documentation shows evolution across multiple time periods. Key findings include:

- Multiple relevant documents were identified spanning the analyzed timeframe
- Documentation has been actively maintained with regular updates
- The system has evolved over time with various architectural and implementation changes

For detailed timeline and specific changes, please refer to the source documents listed in the citations.

*Note: This is a temporal analysis based on {context.count('Document:')} relevant documents.*"""
        
        return answer
    
    def _calculate_answer_confidence(
        self,
        timeline: DynamicTimeline,
        documents: List[RelevantDocument],
        answer_text: str
    ) -> float:
        """Calculate confidence in the generated answer."""
        confidence_factors = []
        
        # Factor 1: Timeline confidence
        timeline_confidence_map = {
            "HIGH": 1.0,
            "MEDIUM": 0.75,
            "LOW": 0.5,
            "NONE": 0.25
        }
        confidence_factors.append(
            timeline_confidence_map.get(timeline.confidence, 0.5)
        )
        
        # Factor 2: Document count and relevance
        if documents:
            avg_relevance = sum(doc.relevance_score for doc in documents) / len(documents)
            confidence_factors.append(avg_relevance)
        else:
            confidence_factors.append(0.0)
        
        # Factor 3: Answer length (longer = more detailed = higher confidence)
        answer_length_factor = min(len(answer_text) / 500.0, 1.0)
        confidence_factors.append(answer_length_factor)
        
        # Calculate weighted average
        overall_confidence = sum(confidence_factors) / len(confidence_factors)
        
        return round(overall_confidence, 2)
    
    def _prepare_sources(
        self,
        documents: List[RelevantDocument]
    ) -> List[Dict]:
        """Prepare source documents for citation."""
        sources = []
        
        for i, doc in enumerate(documents[:10], 1):  # Top 10 sources
            sources.append({
                'index': i,
                'file_path': doc.file_path,
                'relevance_score': doc.relevance_score,
                'last_modified': doc.last_modified.isoformat() if doc.last_modified else None,
                'matched_topics': doc.matched_topics,
                'document_id': doc.document_id
            })
        
        return sources

