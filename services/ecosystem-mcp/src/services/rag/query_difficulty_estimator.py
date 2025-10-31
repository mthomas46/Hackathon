"""
Query Difficulty Estimation Service

Predicts query difficulty BEFORE retrieval to set user expectations.

PHASE 7R: Advanced feature for improved UX
Expected Impact: +2-4% user satisfaction
"""

import logging
from typing import Dict, Any, List
import re

logger = logging.getLogger(__name__)


class QueryDifficultyEstimator:
    """
    Estimate query difficulty based on characteristics.
    
    Philosophy:
    - Fast heuristics (< 1ms)
    - Set realistic expectations
    - Help users rephrase if needed
    
    Difficulty Factors:
    - Complexity: Word count, structure
    - Specificity: Vague vs specific terms
    - Domain coverage: In-domain vs out-of-domain
    - Type: Factual (easy) vs conceptual (hard)
    
    PHASE 7R: Helps users understand if query is answerable
    """
    
    def __init__(self):
        """Initialize query difficulty estimator."""
        
        # Indicators of difficult queries
        self.difficulty_indicators = {
            "vague_terms": [
                "thing", "stuff", "something", "anything",
                "somehow", "somewhere", "someone",
                "kind of", "sort of", "maybe"
            ],
            "complex_operators": [
                "and", "or", "but", "however", "although",
                "compare", "contrast", "difference", "versus"
            ],
            "abstract_concepts": [
                "philosophy", "theory", "concept", "idea",
                "approach", "strategy", "methodology"
            ]
        }
        
        # Indicators of easy queries
        self.easy_indicators = {
            "specific_terms": [
                "what is", "define", "explain", "how to",
                "steps", "guide", "tutorial", "example"
            ],
            "technical_terms": [
                "api", "endpoint", "database", "function",
                "class", "method", "variable", "error"
            ]
        }
        
        logger.info("QueryDifficultyEstimator initialized")
    
    def estimate(self, query: str) -> Dict[str, Any]:
        """
        Estimate query difficulty.
        
        Returns difficulty score (0-100):
        - 0-30: Easy (high chance of good answer)
        - 31-60: Medium (moderate chance)
        - 61-100: Hard (low chance, suggest rephrase)
        
        Args:
            query: User's question
        
        Returns:
            Dict with:
            - difficulty_score: 0-100
            - difficulty_level: easy/medium/hard
            - expected_confidence: Predicted confidence (0-100)
            - factors: List of difficulty factors
            - suggestions: Optional suggestions to improve
        
        Performance: < 1ms
        """
        query_lower = query.lower().strip()
        words = query_lower.split()
        word_count = len(words)
        
        # Start with base difficulty
        difficulty_score = 50  # Medium baseline
        factors = []
        
        # === Factor 1: Query Length ===
        if word_count <= 3:
            # Very short: Can be easy (clear) or hard (vague)
            # Check if it's a clear question
            if any(kw in query_lower for kw in ["what", "who", "where", "when"]):
                difficulty_score -= 10
                factors.append("Short, clear question (-10)")
            else:
                difficulty_score += 15
                factors.append("Very short, potentially vague (+15)")
        elif word_count <= 8:
            difficulty_score -= 5
            factors.append("Good length (-5)")
        elif word_count <= 15:
            difficulty_score += 0
            factors.append("Moderate length (0)")
        else:
            difficulty_score += 10
            factors.append("Long, complex query (+10)")
        
        # === Factor 2: Vague Terms ===
        vague_count = sum(
            1 for term in self.difficulty_indicators["vague_terms"]
            if term in query_lower
        )
        if vague_count > 0:
            penalty = vague_count * 15
            difficulty_score += penalty
            factors.append(f"{vague_count} vague term(s) (+{penalty})")
        
        # === Factor 3: Complex Operators ===
        complex_count = sum(
            1 for term in self.difficulty_indicators["complex_operators"]
            if term in query_lower
        )
        if complex_count > 1:  # Multiple operators
            penalty = (complex_count - 1) * 10
            difficulty_score += penalty
            factors.append(f"Multiple operators (+{penalty})")
        
        # === Factor 4: Abstract Concepts ===
        abstract_count = sum(
            1 for term in self.difficulty_indicators["abstract_concepts"]
            if term in query_lower
        )
        if abstract_count > 0:
            penalty = abstract_count * 10
            difficulty_score += penalty
            factors.append(f"Abstract concepts (+{penalty})")
        
        # === Factor 5: Question Structure ===
        if not query.endswith("?"):
            difficulty_score += 5
            factors.append("Missing question mark (+5)")
        
        # === Factor 6: Specific/Technical Terms (BONUS) ===
        specific_count = sum(
            1 for term in self.easy_indicators["specific_terms"]
            if term in query_lower
        )
        technical_count = sum(
            1 for term in self.easy_indicators["technical_terms"]
            if term in query_lower
        )
        
        if specific_count > 0:
            bonus = specific_count * 5
            difficulty_score -= bonus
            factors.append(f"Specific terms (-{bonus})")
        
        if technical_count > 0:
            bonus = technical_count * 5
            difficulty_score -= bonus
            factors.append(f"Technical terms (-{bonus})")
        
        # === Factor 7: Named Entities (URLs, file paths, etc.) ===
        if self._has_named_entities(query):
            difficulty_score -= 10
            factors.append("Contains specific references (-10)")
        
        # Clamp to 0-100
        difficulty_score = max(0, min(100, difficulty_score))
        
        # Determine difficulty level
        if difficulty_score <= 30:
            difficulty_level = "easy"
            expected_confidence = 70 + (30 - difficulty_score)  # 70-100
        elif difficulty_score <= 60:
            difficulty_level = "medium"
            expected_confidence = 50 + (60 - difficulty_score) / 2  # 50-70
        else:
            difficulty_level = "hard"
            expected_confidence = 20 + (100 - difficulty_score) / 2  # 20-50
        
        # Generate suggestions for hard queries
        suggestions = []
        if difficulty_level == "hard":
            suggestions = self._generate_suggestions(query_lower, factors)
        
        logger.debug(
            f"   🎯 Query difficulty: {difficulty_level} "
            f"(score: {difficulty_score}, expected confidence: {expected_confidence:.0f}%)"
        )
        
        return {
            "difficulty_score": round(difficulty_score, 1),
            "difficulty_level": difficulty_level,
            "expected_confidence": round(expected_confidence, 1),
            "factors": factors,
            "suggestions": suggestions
        }
    
    def _has_named_entities(self, query: str) -> bool:
        """
        Check if query contains specific named entities.
        
        Indicators: URLs, file paths, version numbers, specific names
        
        Args:
            query: User's question
        
        Returns:
            True if named entities found
        """
        # Check for URLs
        if re.search(r'https?://', query):
            return True
        
        # Check for file paths
        if re.search(r'/[\w/]+\.\w+', query):
            return True
        
        # Check for version numbers
        if re.search(r'v?\d+\.\d+', query):
            return True
        
        # Check for capitalized proper nouns (simple heuristic)
        words = query.split()
        capitalized_count = sum(1 for w in words if w and w[0].isupper())
        if capitalized_count >= 2:
            return True
        
        return False
    
    def _generate_suggestions(
        self,
        query_lower: str,
        factors: List[str]
    ) -> List[str]:
        """
        Generate suggestions to improve hard queries.
        
        Args:
            query_lower: Lowercase query
            factors: Difficulty factors
        
        Returns:
            List of actionable suggestions
        """
        suggestions = []
        
        # Check for specific issues
        if any("vague" in f.lower() for f in factors):
            suggestions.append(
                "Replace vague terms (thing, stuff, something) with specific terms"
            )
        
        if any("long" in f.lower() or "complex" in f.lower() for f in factors):
            suggestions.append(
                "Break your question into smaller, simpler parts"
            )
        
        if not any("specific" in f.lower() or "technical" in f.lower() for f in factors):
            suggestions.append(
                "Add specific technical terms or examples"
            )
        
        if "?" not in factors:  # No question mark
            suggestions.append(
                "Rephrase as a clear question (who, what, where, when, why, how)"
            )
        
        # Always add general suggestion
        suggestions.append(
            "Try being more specific about what you want to know"
        )
        
        return suggestions[:3]  # Max 3 suggestions


# Singleton instance
_estimator_instance = None


def get_query_difficulty_estimator() -> QueryDifficultyEstimator:
    """Get or create singleton query difficulty estimator."""
    global _estimator_instance
    if _estimator_instance is None:
        _estimator_instance = QueryDifficultyEstimator()
    return _estimator_instance

