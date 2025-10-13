"""
Complexity Analyzer - Determines query complexity for intelligent routing.

Scores queries on 0.0-1.0 scale based on:
- Query length and structure
- Context size
- Task type (generation, reasoning, simple lookup)
- Language complexity
"""

import logging
import re
from typing import Optional
from enum import Enum

logger = logging.getLogger(__name__)


class ComplexityLevel(Enum):
    """Query complexity levels."""
    SIMPLE = "simple"        # 0.0-0.3: Simple lookups, calculations
    MEDIUM = "medium"        # 0.3-0.6: Standard queries, basic generation
    HEAVY = "heavy"          # 0.6-0.8: Complex generation, multi-step reasoning
    EXTREME = "extreme"      # 0.8-1.0: Synthesis, code gen, deep reasoning


class ComplexityAnalyzer:
    """
    Analyzes query complexity to route to appropriate LLM instance.
    
    Scoring factors:
    - Query length: Longer = more complex
    - Context size: More context = more complex
    - Keywords: "explain", "analyze", "synthesize" = complex
    - Multi-step: Multiple questions/tasks = complex
    - Code patterns: Code generation = complex
    - Reasoning: "why", "how", "compare" = complex
    """
    
    # Complexity indicators
    COMPLEX_KEYWORDS = [
        "explain", "analyze", "synthesize", "compare", "evaluate",
        "justify", "argue", "debate", "critique", "assess",
        "develop", "design", "architect", "implement", "refactor",
        "optimize", "improve", "enhance", "transform"
    ]
    
    SIMPLE_KEYWORDS = [
        "list", "show", "display", "get", "fetch", "find",
        "what is", "define", "lookup", "retrieve", "return"
    ]
    
    CODE_PATTERNS = [
        r"```", r"function\s+\w+", r"class\s+\w+", r"def\s+\w+",
        r"import\s+", r"from\s+\w+\s+import", r"<\w+>.*</\w+>",
        r"\{\s*[\w\s:,]+\}", r"=>", r"->"
    ]
    
    REASONING_KEYWORDS = [
        "why", "how", "explain why", "reason", "because",
        "cause", "effect", "impact", "consequence", "result"
    ]
    
    MULTI_STEP_INDICATORS = [
        "first", "then", "next", "finally", "step",
        "1.", "2.", "3.", "a)", "b)", "c)"
    ]
    
    def __init__(self):
        """Initialize complexity analyzer."""
        logger.info("ComplexityAnalyzer initialized")
    
    def analyze(
        self,
        query: str,
        context: Optional[str] = None,
        context_docs: Optional[list] = None,
        workload_type: Optional[str] = None
    ) -> float:
        """
        Analyze query complexity.
        
        Args:
            query: The user query
            context: Optional context/conversation history
            context_docs: Optional list of context documents
            workload_type: Optional workload hint ('rag', 'generation', etc.)
        
        Returns:
            Complexity score (0.0 = simple, 1.0 = extreme)
        """
        score = 0.0
        factors = []
        
        # Factor 1: Query length (0.0-0.2)
        length_score = self._score_length(query)
        score += length_score
        factors.append(f"length={length_score:.2f}")
        
        # Factor 2: Keyword complexity (0.0-0.25)
        keyword_score = self._score_keywords(query)
        score += keyword_score
        factors.append(f"keywords={keyword_score:.2f}")
        
        # Factor 3: Code patterns (0.0-0.2)
        code_score = self._score_code_patterns(query)
        score += code_score
        factors.append(f"code={code_score:.2f}")
        
        # Factor 4: Reasoning indicators (0.0-0.15)
        reasoning_score = self._score_reasoning(query)
        score += reasoning_score
        factors.append(f"reasoning={reasoning_score:.2f}")
        
        # Factor 5: Multi-step detection (0.0-0.1)
        multi_step_score = self._score_multi_step(query)
        score += multi_step_score
        factors.append(f"multi_step={multi_step_score:.2f}")
        
        # Factor 6: Context size (0.0-0.1)
        context_score = self._score_context(context, context_docs)
        score += context_score
        factors.append(f"context={context_score:.2f}")
        
        # Factor 7: Workload type hint (0.0-0.1)
        workload_score = self._score_workload_type(workload_type)
        score += workload_score
        factors.append(f"workload={workload_score:.2f}")
        
        # Normalize to 0.0-1.0
        score = min(score, 1.0)
        
        level = self._get_complexity_level(score)
        
        logger.debug(
            f"Complexity analysis: {score:.2f} ({level.value}) | "
            f"Factors: {', '.join(factors)}"
        )
        
        return score
    
    def _score_length(self, query: str) -> float:
        """Score based on query length (0.0-0.2)."""
        words = len(query.split())
        
        if words < 10:
            return 0.05  # Very short
        elif words < 30:
            return 0.10  # Short
        elif words < 100:
            return 0.15  # Medium
        else:
            return 0.20  # Long
    
    def _score_keywords(self, query: str) -> float:
        """Score based on keyword complexity (0.0-0.25)."""
        query_lower = query.lower()
        
        # Check for simple keywords (negative score)
        simple_count = sum(1 for kw in self.SIMPLE_KEYWORDS if kw in query_lower)
        if simple_count > 0:
            return 0.05  # Simple query
        
        # Check for complex keywords
        complex_count = sum(1 for kw in self.COMPLEX_KEYWORDS if kw in query_lower)
        
        if complex_count == 0:
            return 0.10  # Neutral
        elif complex_count == 1:
            return 0.15  # Somewhat complex
        elif complex_count == 2:
            return 0.20  # Complex
        else:
            return 0.25  # Very complex
    
    def _score_code_patterns(self, query: str) -> float:
        """Score based on code generation indicators (0.0-0.2)."""
        code_matches = sum(
            1 for pattern in self.CODE_PATTERNS
            if re.search(pattern, query, re.IGNORECASE)
        )
        
        if code_matches == 0:
            return 0.0
        elif code_matches <= 2:
            return 0.10
        else:
            return 0.20  # Significant code generation
    
    def _score_reasoning(self, query: str) -> float:
        """Score based on reasoning requirements (0.0-0.15)."""
        query_lower = query.lower()
        
        reasoning_count = sum(
            1 for kw in self.REASONING_KEYWORDS
            if kw in query_lower
        )
        
        if reasoning_count == 0:
            return 0.0
        elif reasoning_count == 1:
            return 0.08
        else:
            return 0.15  # Deep reasoning required
    
    def _score_multi_step(self, query: str) -> float:
        """Score based on multi-step task detection (0.0-0.1)."""
        multi_step_count = sum(
            1 for indicator in self.MULTI_STEP_INDICATORS
            if indicator in query.lower()
        )
        
        if multi_step_count >= 3:
            return 0.10  # Multi-step task
        elif multi_step_count >= 1:
            return 0.05  # Possible multi-step
        else:
            return 0.0
    
    def _score_context(
        self,
        context: Optional[str],
        context_docs: Optional[list]
    ) -> float:
        """Score based on context size (0.0-0.1)."""
        context_length = len(context) if context else 0
        doc_count = len(context_docs) if context_docs else 0
        
        if context_length > 5000 or doc_count > 10:
            return 0.10  # Large context
        elif context_length > 1000 or doc_count > 5:
            return 0.05  # Medium context
        else:
            return 0.0
    
    def _score_workload_type(self, workload_type: Optional[str]) -> float:
        """Score based on workload type hint (0.0-0.1)."""
        if not workload_type:
            return 0.0
        
        workload_lower = workload_type.lower()
        
        if workload_lower in ['rag', 'synthesis', 'heavy']:
            return 0.10
        elif workload_lower in ['generation', 'medium']:
            return 0.05
        else:
            return 0.0
    
    def _get_complexity_level(self, score: float) -> ComplexityLevel:
        """Convert score to complexity level."""
        if score < 0.3:
            return ComplexityLevel.SIMPLE
        elif score < 0.6:
            return ComplexityLevel.MEDIUM
        elif score < 0.8:
            return ComplexityLevel.HEAVY
        else:
            return ComplexityLevel.EXTREME
    
    def recommend_instance(
        self,
        complexity_score: float,
        cursor_enabled: bool = False,
        cursor_threshold: float = 0.7,
        desktop_enabled: bool = False
    ) -> str:
        """
        Recommend which instance to use based on complexity.
        
        Args:
            complexity_score: Complexity score (0.0-1.0)
            cursor_enabled: Whether Cursor IDE is available
            cursor_threshold: Threshold for Cursor routing
            desktop_enabled: Whether desktop Ollama is available
        
        Returns:
            Instance name: 'cursor', 'desktop', or 'docker'
        """
        # Extreme complexity: Use Cursor if available
        if cursor_enabled and complexity_score >= cursor_threshold:
            return "cursor"
        
        # Heavy/Medium complexity: Use desktop if available
        if desktop_enabled and complexity_score >= 0.4:
            return "desktop"
        
        # Simple/fallback: Use Docker
        return "docker"


# Singleton instance
_complexity_analyzer: Optional[ComplexityAnalyzer] = None


def get_complexity_analyzer() -> ComplexityAnalyzer:
    """
    Get the global complexity analyzer instance.
    
    Returns:
        ComplexityAnalyzer instance
    """
    global _complexity_analyzer
    
    if _complexity_analyzer is None:
        _complexity_analyzer = ComplexityAnalyzer()
    
    return _complexity_analyzer

