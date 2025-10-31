"""
Confidence Scoring Service

Calculates multi-factor confidence scores for RAG answers.

Factors:
1. Retrieval Quality (20 pts): How similar are retrieved docs to query?
2. Source Quality (20 pts): Are sources high-quality (A/S grade)?
3. Answer-Source Alignment (20 pts): Is answer clearly derived from sources?
4. Consensus (20 pts): Do multiple sources agree?
5. Completeness (20 pts): Is query fully answered?

Total: 0-100 confidence score

Expected: Better UX, trust calibration, uncertainty detection
"""

import logging
from typing import List, Dict, Any, Optional
import re

from ..models.ollama_router import get_ollama_router

logger = logging.getLogger(__name__)


class ConfidenceScorer:
    """
    Multi-factor confidence scoring for RAG answers.
    
    Provides:
    - Overall confidence score (0-100)
    - Breakdown by factor
    - Confidence level (Very High, High, Medium, Low, Very Low)
    - Actionable recommendations
    """
    
    def __init__(self):
        """Initialize confidence scorer."""
        self.ollama_router = get_ollama_router()
        
        logger.info("ConfidenceScorer initialized")
    
    async def score(
        self,
        query: str,
        retrieved_documents: List[Dict[str, Any]],
        answer: str,
        use_llm_for_alignment: bool = True
    ) -> Dict[str, Any]:
        """
        Calculate confidence score for RAG answer.
        
        Args:
            query: Original query
            retrieved_documents: Retrieved documents used for answer
            answer: Generated answer
            use_llm_for_alignment: Use LLM to assess answer-source alignment (slower but more accurate)
        
        Returns:
            Dict with:
            - confidence: Overall confidence (0-100)
            - confidence_level: "Very High" | "High" | "Medium" | "Low" | "Very Low"
            - breakdown: Scores for each factor
            - recommendation: Actionable advice
        """
        logger.info(f"📊 Calculating confidence for: '{query[:50]}...'")
        
        if not retrieved_documents:
            return self._no_documents_result()
        
        # Calculate each factor
        retrieval_score = self._calculate_retrieval_confidence(retrieved_documents)
        quality_score = self._calculate_source_quality(retrieved_documents)
        consensus_score = self._calculate_consensus(retrieved_documents)
        completeness_score = self._calculate_completeness(query, answer)
        
        # Answer-source alignment (expensive, can be disabled)
        if use_llm_for_alignment:
            alignment_score = await self._calculate_alignment_llm(answer, retrieved_documents)
        else:
            alignment_score = self._calculate_alignment_heuristic(answer, retrieved_documents)
        
        # Total confidence
        total_confidence = (
            retrieval_score +
            quality_score +
            alignment_score +
            consensus_score +
            completeness_score
        )
        
        # Confidence level
        confidence_level = self._get_confidence_level(total_confidence)
        
        # Recommendation
        recommendation = self._get_recommendation(
            total_confidence,
            retrieval_score,
            quality_score,
            alignment_score,
            consensus_score,
            completeness_score
        )
        
        result = {
            "confidence": round(total_confidence, 1),
            "confidence_level": confidence_level,
            "breakdown": {
                "retrieval_quality": round(retrieval_score, 1),
                "source_quality": round(quality_score, 1),
                "answer_source_alignment": round(alignment_score, 1),
                "consensus": round(consensus_score, 1),
                "completeness": round(completeness_score, 1)
            },
            "recommendation": recommendation
        }
        
        logger.info(f"✅ Confidence: {total_confidence:.1f}/100 ({confidence_level})")
        
        return result
    
    def _calculate_retrieval_confidence(self, documents: List[Dict[str, Any]]) -> float:
        """
        Calculate retrieval quality (0-20 points).
        
        High score if:
        - Top documents have high similarity/low distance
        - Multiple documents with good scores (not just one)
        """
        if not documents:
            return 0.0
        
        # Get top 5 similarity scores
        scores = []
        for doc in documents[:5]:
            # Try different score keys
            score = (
                doc.get("semantic_score") or
                doc.get("hybrid_score") or
                doc.get("similarity_score") or
                doc.get("adjusted_score") or
                0.0
            )
            
            # Convert distance to score if needed
            if "distance" in doc or "semantic_distance" in doc:
                distance = doc.get("distance") or doc.get("semantic_distance")
                if distance is not None:
                    score = 1.0 / (1.0 + distance)
            
            scores.append(score)
        
        if not scores:
            return 0.0
        
        # Average of top 5 scores
        avg_score = sum(scores) / len(scores)
        
        # Scale to 0-20
        retrieval_confidence = avg_score * 20
        
        return min(20.0, max(0.0, retrieval_confidence))
    
    def _calculate_source_quality(self, documents: List[Dict[str, Any]]) -> float:
        """
        Calculate source quality (0-20 points).
        
        High score if:
        - Documents have high quality_score (A/S grade)
        - Multiple high-quality sources
        """
        if not documents:
            return 0.0
        
        quality_scores = []
        for doc in documents[:5]:
            # Try to get quality score from different places
            quality = (
                doc.get("quality_score") or
                doc.get("metadata", {}).get("quality_score") or
                doc.get("full_metadata", {}).get("quality_score")
            )
            
            if quality is not None:
                quality_scores.append(quality)
        
        if not quality_scores:
            # No quality scores available, return neutral
            return 10.0
        
        # Average quality score (0-100) → scale to 0-20
        avg_quality = sum(quality_scores) / len(quality_scores)
        source_quality_confidence = (avg_quality / 100) * 20
        
        return min(20.0, max(0.0, source_quality_confidence))
    
    async def _calculate_alignment_llm(
        self,
        answer: str,
        documents: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate answer-source alignment using LLM (0-20 points).
        
        Uses LLM to assess if answer is clearly derived from sources.
        More accurate but slower.
        """
        try:
            # Build source text (first 3 documents)
            source_text = ""
            for i, doc in enumerate(documents[:3]):
                snippet = doc.get("content_snippet") or doc.get("content", "")[:300]
                source_text += f"Source {i+1}: {snippet}\n\n"
            
            prompt = f"""Assess if this answer is clearly derived from the provided sources.

Answer: "{answer[:500]}"

Sources:
{source_text}

Is the answer clearly supported by the sources? Rate from 0-10:
- 10: Fully supported, all claims backed by sources
- 7-9: Mostly supported, minor gaps
- 4-6: Partially supported, some claims not backed
- 1-3: Poorly supported, mostly unsupported
- 0: Not supported at all

Rating (just the number):"""
            
            response = await self.ollama_router.generate(
                prompt=prompt,
                max_tokens=10,
                temperature=0.1
            )
            
            # Extract number
            match = re.search(r'\d+', response)
            if match:
                rating = int(match.group())
                alignment_score = (rating / 10) * 20
                return min(20.0, max(0.0, alignment_score))
            
        except Exception as e:
            logger.warning(f"LLM alignment scoring failed: {e}")
        
        # Fallback to heuristic
        return self._calculate_alignment_heuristic(answer, documents)
    
    def _calculate_alignment_heuristic(
        self,
        answer: str,
        documents: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate answer-source alignment using heuristics (0-20 points).
        
        Fast but less accurate than LLM method.
        Checks for term overlap between answer and sources.
        """
        if not documents:
            return 0.0
        
        # Get answer terms (simple tokenization)
        answer_terms = set(re.findall(r'\w+', answer.lower()))
        
        # Get source terms
        source_terms = set()
        for doc in documents[:5]:
            content = doc.get("content_snippet") or doc.get("content", "")
            source_terms.update(re.findall(r'\w+', content.lower()[:500]))
        
        if not answer_terms or not source_terms:
            return 10.0  # Neutral
        
        # Calculate term overlap (Jaccard similarity)
        overlap = len(answer_terms & source_terms)
        total = len(answer_terms | source_terms)
        
        jaccard = overlap / total if total > 0 else 0
        
        # Scale to 0-20
        alignment_score = jaccard * 20 * 1.5  # 1.5x multiplier to be less harsh
        
        return min(20.0, max(0.0, alignment_score))
    
    def _calculate_consensus(self, documents: List[Dict[str, Any]]) -> float:
        """
        Calculate consensus (0-20 points).
        
        High score if:
        - Multiple documents retrieved (not just one)
        - Documents are diverse (different files/sources)
        - Scores are relatively consistent (not one outlier)
        """
        if not documents:
            return 0.0
        
        # Factor 1: Multiple documents (0-10 pts)
        num_docs = len(documents)
        if num_docs >= 5:
            count_score = 10.0
        elif num_docs >= 3:
            count_score = 7.0
        elif num_docs >= 2:
            count_score = 4.0
        else:
            count_score = 0.0
        
        # Factor 2: Source diversity (0-10 pts)
        unique_files = len(set(doc.get("file_path", "") for doc in documents[:5]))
        if unique_files >= 4:
            diversity_score = 10.0
        elif unique_files >= 3:
            diversity_score = 7.0
        elif unique_files >= 2:
            diversity_score = 4.0
        else:
            diversity_score = 0.0
        
        consensus_score = count_score + diversity_score
        
        return min(20.0, max(0.0, consensus_score))
    
    def _calculate_completeness(self, query: str, answer: str) -> float:
        """
        Calculate completeness (0-20 points).
        
        High score if:
        - Answer is sufficiently detailed (not too short)
        - Answer addresses key terms from query
        """
        if not answer:
            return 0.0
        
        # Factor 1: Answer length (0-10 pts)
        answer_length = len(answer)
        if answer_length >= 300:
            length_score = 10.0
        elif answer_length >= 150:
            length_score = 7.0
        elif answer_length >= 50:
            length_score = 4.0
        else:
            length_score = 1.0
        
        # Factor 2: Query term coverage (0-10 pts)
        query_terms = set(re.findall(r'\w+', query.lower()))
        answer_terms = set(re.findall(r'\w+', answer.lower()))
        
        # Remove common words
        stop_words = {'a', 'an', 'the', 'is', 'are', 'was', 'were', 'be', 'been', 
                     'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                     'would', 'should', 'could', 'can', 'may', 'might'}
        query_terms -= stop_words
        
        if query_terms:
            coverage = len(query_terms & answer_terms) / len(query_terms)
            coverage_score = coverage * 10
        else:
            coverage_score = 5.0  # Neutral
        
        completeness_score = length_score + coverage_score
        
        return min(20.0, max(0.0, completeness_score))
    
    def _get_confidence_level(self, confidence: float) -> str:
        """Map confidence score to level."""
        if confidence >= 90:
            return "Very High"
        elif confidence >= 75:
            return "High"
        elif confidence >= 60:
            return "Medium"
        elif confidence >= 40:
            return "Low"
        else:
            return "Very Low"
    
    def _get_recommendation(
        self,
        total: float,
        retrieval: float,
        quality: float,
        alignment: float,
        consensus: float,
        completeness: float
    ) -> str:
        """Generate actionable recommendation based on scores."""
        if total >= 90:
            return "Very high confidence. Answer is well-supported and reliable."
        
        elif total >= 75:
            return "High confidence. Answer is trustworthy."
        
        elif total >= 60:
            return "Medium confidence. Answer is likely correct but verify important details."
        
        else:
            # Identify weakest factor
            factors = {
                "retrieval quality": retrieval,
                "source quality": quality,
                "answer-source alignment": alignment,
                "consensus": consensus,
                "completeness": completeness
            }
            
            weakest = min(factors, key=factors.get)
            
            recommendations = {
                "retrieval quality": "Low confidence. Retrieved documents may not be relevant. Try rephrasing the query.",
                "source quality": "Low confidence. Sources are low-quality. Results may be unreliable.",
                "answer-source alignment": "Low confidence. Answer may not be well-supported by sources. Verify claims.",
                "consensus": "Low confidence. Limited consensus from sources. Cross-check information.",
                "completeness": "Low confidence. Answer may be incomplete. Ask for more details."
            }
            
            return recommendations.get(weakest, "Low confidence. Please verify this answer independently.")
    
    def _no_documents_result(self) -> Dict[str, Any]:
        """Return result when no documents retrieved."""
        return {
            "confidence": 0.0,
            "confidence_level": "Very Low",
            "breakdown": {
                "retrieval_quality": 0.0,
                "source_quality": 0.0,
                "answer_source_alignment": 0.0,
                "consensus": 0.0,
                "completeness": 0.0
            },
            "recommendation": "No relevant documents found. Cannot provide confident answer."
        }


# Singleton instance
_confidence_scorer = None


def get_confidence_scorer() -> ConfidenceScorer:
    """Get or create confidence scorer singleton."""
    global _confidence_scorer
    if _confidence_scorer is None:
        _confidence_scorer = ConfidenceScorer()
    return _confidence_scorer

