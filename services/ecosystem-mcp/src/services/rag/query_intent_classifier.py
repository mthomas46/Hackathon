"""
Query Intent Classification Service

Classifies user queries to enable adaptive RAG strategies.

Features:
- Fast heuristic classification (< 1ms)
- Optional LLM-based classification for edge cases
- Query complexity estimation
- Adaptive parameter recommendations

Expected Impact: +6-10% accuracy, -10-15% latency
"""

import logging
import re
from typing import Dict, Any, Optional
from datetime import datetime

from ..models.ollama_router import get_ollama_router
from ...utils.cache_decorator import cache

logger = logging.getLogger(__name__)


class QueryIntentClassifier:
    """
    Classify query intent and complexity for adaptive RAG.
    
    Philosophy:
    - Heuristics are instant and good enough for most queries (80%)
    - LLM classification is optional, for edge cases only
    - Always returns valid intent (never fails)
    - Provides actionable recommendations (n_results, strategies)
    
    Query Types:
    - factual: "What is X?", "Define Y"
    - procedural: "How to X?", "Steps to Y"
    - temporal: "Recent X", "Latest Y"
    - comparative: "X vs Y", "Difference between X and Y"
    - conceptual: "Why X?", "Explain Y"
    
    Complexity Levels:
    - simple: 1-5 words, single concept
    - moderate: 6-12 words, clear question
    - complex: 13+ words, multiple concepts or vague
    """
    
    def __init__(self):
        """Initialize query intent classifier."""
        self.ollama_router = get_ollama_router()
        
        # Fast heuristic patterns (case-insensitive)
        self.factual_keywords = ["what", "define", "explain", "describe", "tell me about"]
        self.procedural_keywords = ["how", "steps", "guide", "tutorial", "process", "setup"]
        self.temporal_keywords = ["recent", "latest", "new", "updated", "current", "now"]
        self.comparative_keywords = ["compare", "difference", "vs", "versus", "better", "or"]
        self.conceptual_keywords = ["why", "reason", "purpose", "benefit", "advantage"]
        
        logger.info("QueryIntentClassifier initialized")
    
    def classify_heuristic(self, query: str) -> Dict[str, Any]:
        """
        Fast classification using heuristics (< 1ms).
        
        Args:
            query: User's question
        
        Returns:
            Classification dict with:
            - type: Query type (factual, procedural, etc.)
            - complexity: Query complexity (simple, moderate, complex)
            - confidence: Heuristic confidence (0.0-1.0)
            - n_results: Recommended number of results
            - enable_reranking: Whether to use reranking
            - enable_query_rewriting: Whether to use query rewriting
            - strategy: Recommended context optimization strategy
        
        Performance: < 1ms (pure Python regex + string ops)
        """
        start_time = datetime.now()
        
        query_lower = query.lower().strip()
        query_words = query_lower.split()
        query_length = len(query_words)
        
        # === Type Classification ===
        
        # Check temporal first (most specific)
        if any(kw in query_lower for kw in self.temporal_keywords):
            qtype = "temporal"
        
        # Check procedural (how-to)
        elif any(kw in query_lower for kw in self.procedural_keywords):
            qtype = "procedural"
        
        # Check comparative
        elif any(kw in query_lower for kw in self.comparative_keywords):
            qtype = "comparative"
        
        # Check conceptual (why)
        elif any(kw in query_lower for kw in self.conceptual_keywords):
            qtype = "conceptual"
        
        # Default to factual
        else:
            qtype = "factual"
        
        # === Complexity Classification ===
        
        # Consider word count + question structure
        has_question_mark = "?" in query
        has_multiple_concepts = " and " in query_lower or " or " in query_lower
        has_vague_terms = any(word in query_lower for word in ["thing", "stuff", "something", "anything"])
        
        if query_length <= 5 and has_question_mark and not has_multiple_concepts:
            complexity = "simple"
        elif query_length <= 12 and not has_multiple_concepts and not has_vague_terms:
            complexity = "moderate"
        else:
            complexity = "complex"
        
        # === Adaptive Parameters ===
        
        # n_results: More results for complex queries
        n_results_map = {
            "simple": 5,
            "moderate": 10,
            "complex": 15
        }
        n_results = n_results_map[complexity]
        
        # Reranking: Use for moderate+ complexity
        enable_reranking = complexity in ["moderate", "complex"]
        
        # Query rewriting: Use for complex queries only
        enable_query_rewriting = complexity == "complex"
        
        # Context optimization strategy
        if qtype == "factual":
            strategy = "quality_first"  # Prioritize high-quality docs
        elif qtype == "procedural":
            strategy = "relevance_first"  # Prioritize relevance + recency
        elif qtype == "temporal":
            strategy = "relevance_first"  # Prioritize recency
        else:
            strategy = "balanced"  # Default balanced
        
        # Confidence: Heuristics are pretty good (0.7-0.85)
        confidence = 0.7  # Base confidence
        if has_question_mark:
            confidence += 0.05
        if query_length >= 3:  # Not too short
            confidence += 0.05
        if not has_vague_terms:
            confidence += 0.05
        
        elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        result = {
            "type": qtype,
            "complexity": complexity,
            "confidence": confidence,
            "n_results": n_results,
            "enable_reranking": enable_reranking,
            "enable_query_rewriting": enable_query_rewriting,
            "strategy": strategy,
            "method": "heuristic",
            "elapsed_ms": round(elapsed_ms, 2)
        }
        
        logger.debug(
            f"Heuristic classification: {qtype}/{complexity} "
            f"(confidence: {confidence:.2f}, {elapsed_ms:.2f}ms)"
        )
        
        return result
    
    @cache(ttl=3600, key_prefix="query_intent_llm_v1")
    async def classify_llm(self, query: str) -> Dict[str, Any]:
        """
        LLM-based classification (50-100ms, cached).
        
        Use ONLY when:
        - Heuristic confidence is low (< 0.6)
        - Query is ambiguous
        - User explicitly requests
        
        Args:
            query: User's question
        
        Returns:
            Classification dict (same format as classify_heuristic)
        
        Performance:
        - First call: 50-100ms (LLM inference)
        - Cached calls: ~5ms (Redis lookup)
        """
        start_time = datetime.now()
        
        # Use FASTEST model for classification
        prompt = f"""Classify this query for a RAG system.

Query: "{query}"

Classify:
1. Type: factual, procedural, temporal, comparative, or conceptual
2. Complexity: simple, moderate, or complex

Output ONLY this JSON (no explanation):
{{
  "type": "...",
  "complexity": "..."
}}"""
        
        try:
            response = await self.ollama_router.generate(
                prompt=prompt,
                model="llama3.2:1b",  # Fastest model
                temperature=0.0,
                max_tokens=50
            )
            
            # Parse JSON response
            import json
            result = json.loads(response)
            
            qtype = result.get("type", "factual")
            complexity = result.get("complexity", "moderate")
            
            # Same parameter mapping as heuristic
            n_results_map = {"simple": 5, "moderate": 10, "complex": 15}
            n_results = n_results_map.get(complexity, 10)
            
            enable_reranking = complexity in ["moderate", "complex"]
            enable_query_rewriting = complexity == "complex"
            
            if qtype == "factual":
                strategy = "quality_first"
            elif qtype in ["procedural", "temporal"]:
                strategy = "relevance_first"
            else:
                strategy = "balanced"
            
            elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            result = {
                "type": qtype,
                "complexity": complexity,
                "confidence": 0.9,  # LLM has higher confidence
                "n_results": n_results,
                "enable_reranking": enable_reranking,
                "enable_query_rewriting": enable_query_rewriting,
                "strategy": strategy,
                "method": "llm",
                "elapsed_ms": round(elapsed_ms, 2)
            }
            
            logger.debug(
                f"LLM classification: {qtype}/{complexity} "
                f"(confidence: 0.9, {elapsed_ms:.2f}ms)"
            )
            
            return result
        
        except Exception as e:
            logger.warning(f"LLM classification failed: {e}, falling back to heuristic")
            # Fallback to heuristic
            result = self.classify_heuristic(query)
            result["method"] = "llm_fallback"
            return result
    
    async def classify(
        self,
        query: str,
        enable_llm: bool = False,
        min_confidence: float = 0.6
    ) -> Dict[str, Any]:
        """
        Classify query intent with optional LLM fallback.
        
        Args:
            query: User's question
            enable_llm: Use LLM for low-confidence cases
            min_confidence: Minimum confidence threshold for heuristic
        
        Returns:
            Classification dict
        
        Strategy:
        1. Try fast heuristic first (< 1ms)
        2. If confidence < threshold and LLM enabled, use LLM
        3. Always return valid classification (never fails)
        """
        # Always try heuristic first (fast)
        result = self.classify_heuristic(query)
        
        # If confidence is low and LLM enabled, try LLM
        if enable_llm and result["confidence"] < min_confidence:
            logger.debug(
                f"Heuristic confidence low ({result['confidence']:.2f}), "
                f"trying LLM classification"
            )
            llm_result = await self.classify_llm(query)
            
            # Use LLM result if available
            if llm_result:
                return llm_result
        
        return result


# Singleton instance
_classifier_instance = None


def get_query_intent_classifier() -> QueryIntentClassifier:
    """Get or create singleton query intent classifier."""
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = QueryIntentClassifier()
    return _classifier_instance

