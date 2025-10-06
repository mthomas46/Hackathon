"""LLM Pattern Value Objects.

Based on ADVANCED_LLM_ARCHITECTURE_PATTERNS.md - 24 patterns across 9 categories.
"""

from enum import Enum
from typing import Dict, List, Optional


class LLMPatternCategory(str, Enum):
    """Categories of LLM patterns."""
    
    ENSEMBLE = "ensemble"                   # Multiple models working together
    REASONING = "reasoning"                 # Enhanced reasoning techniques
    SELF_IMPROVEMENT = "self_improvement"   # Self-critique and refinement
    MULTI_AGENT = "multi_agent"             # Multiple agents collaborating
    RETRIEVAL = "retrieval"                 # RAG and context patterns
    UNCERTAINTY = "uncertainty"             # Confidence and uncertainty handling
    HUMAN_IN_LOOP = "human_in_loop"         # Human oversight patterns
    ROBUSTNESS = "robustness"               # Fallback and error handling
    OPTIMIZATION = "optimization"           # Performance optimization


class LLMPattern(str, Enum):
    """
    Advanced LLM patterns for sophisticated query processing.
    
    Each pattern represents a specific technique for improving
    LLM performance, accuracy, or capabilities.
    """
    
    # ========================================
    # ENSEMBLE APPROACHES (3 patterns)
    # ========================================
    ORCHESTRATION = "orchestration"
    """Route queries to specialized models based on task type."""
    
    ANALYSIS = "analysis"
    """Multiple models analyze, combine weighted results."""
    
    SELECTIVE_ENSEMBLE = "selective_ensemble"
    """Hybrid approach: simple queries → single model, complex → ensemble."""
    
    # ========================================
    # REASONING ENHANCEMENT (3 patterns)
    # ========================================
    CHAIN_OF_THOUGHT = "chain_of_thought"
    """Step-by-step reasoning before final answer."""
    
    TREE_OF_THOUGHTS = "tree_of_thoughts"
    """Explore multiple reasoning paths, backtrack if needed."""
    
    GRAPH_OF_THOUGHTS = "graph_of_thoughts"
    """Network of interconnected reasoning nodes."""
    
    # ========================================
    # SELF-IMPROVEMENT (3 patterns)
    # ========================================
    SELF_CONSISTENCY = "self_consistency"
    """Generate multiple answers, select most consistent."""
    
    SELF_CRITIQUE = "self_critique"
    """Model critiques own output, refines iteratively."""
    
    CONSTITUTIONAL_AI = "constitutional_ai"
    """Guided by explicit principles and values."""
    
    # ========================================
    # MULTI-AGENT (3 patterns)
    # ========================================
    DEBATE = "debate"
    """Agents debate different positions, synthesize conclusion."""
    
    COLLABORATION = "collaboration"
    """Agents work on subtasks, combine results."""
    
    VOTING = "voting"
    """Multiple agents vote, aggregate decisions."""
    
    # ========================================
    # RETRIEVAL & CONTEXT (3 patterns)
    # ========================================
    ADVANCED_RAG = "advanced_rag"
    """Retrieval-Augmented Generation with reranking."""
    
    HIERARCHICAL_RETRIEVAL = "hierarchical_retrieval"
    """Tier-by-tier context gathering (MCP-specific)."""
    
    DYNAMIC_CONTEXT_PRUNING = "dynamic_context_pruning"
    """Token budget management with relevance scoring."""
    
    # ========================================
    # UNCERTAINTY & CONFIDENCE (3 patterns)
    # ========================================
    CONFIDENCE_SCORING = "confidence_scoring"
    """Explicit confidence scores for outputs."""
    
    EPISTEMIC_UNCERTAINTY = "epistemic_uncertainty"
    """Model uncertainty estimation."""
    
    CALIBRATION = "calibration"
    """Align confidence with actual accuracy."""
    
    # ========================================
    # HUMAN-IN-THE-LOOP (2 patterns)
    # ========================================
    CONFIDENCE_BASED_APPROVAL = "confidence_based_approval"
    """Low confidence → human review."""
    
    ACTIVE_LEARNING = "active_learning"
    """Identify uncertain cases for human labeling."""
    
    # ========================================
    # ROBUSTNESS & FALLBACKS (2 patterns)
    # ========================================
    FALLBACK_CASCADE = "fallback_cascade"
    """Chain of fallback models/strategies."""
    
    ERROR_RECOVERY = "error_recovery"
    """Graceful degradation and retry logic."""
    
    # ========================================
    # OPTIMIZATION (2 patterns)
    # ========================================
    PROMPT_CACHING = "prompt_caching"
    """Cache prompt embeddings and responses."""
    
    PARALLEL_EXECUTION = "parallel_execution"
    """Execute independent subtasks in parallel."""
    
    @property
    def category(self) -> LLMPatternCategory:
        """Get the category for this pattern."""
        pattern_categories: Dict[LLMPattern, LLMPatternCategory] = {
            # Ensemble
            LLMPattern.ORCHESTRATION: LLMPatternCategory.ENSEMBLE,
            LLMPattern.ANALYSIS: LLMPatternCategory.ENSEMBLE,
            LLMPattern.SELECTIVE_ENSEMBLE: LLMPatternCategory.ENSEMBLE,
            
            # Reasoning
            LLMPattern.CHAIN_OF_THOUGHT: LLMPatternCategory.REASONING,
            LLMPattern.TREE_OF_THOUGHTS: LLMPatternCategory.REASONING,
            LLMPattern.GRAPH_OF_THOUGHTS: LLMPatternCategory.REASONING,
            
            # Self-improvement
            LLMPattern.SELF_CONSISTENCY: LLMPatternCategory.SELF_IMPROVEMENT,
            LLMPattern.SELF_CRITIQUE: LLMPatternCategory.SELF_IMPROVEMENT,
            LLMPattern.CONSTITUTIONAL_AI: LLMPatternCategory.SELF_IMPROVEMENT,
            
            # Multi-agent
            LLMPattern.DEBATE: LLMPatternCategory.MULTI_AGENT,
            LLMPattern.COLLABORATION: LLMPatternCategory.MULTI_AGENT,
            LLMPattern.VOTING: LLMPatternCategory.MULTI_AGENT,
            
            # Retrieval
            LLMPattern.ADVANCED_RAG: LLMPatternCategory.RETRIEVAL,
            LLMPattern.HIERARCHICAL_RETRIEVAL: LLMPatternCategory.RETRIEVAL,
            LLMPattern.DYNAMIC_CONTEXT_PRUNING: LLMPatternCategory.RETRIEVAL,
            
            # Uncertainty
            LLMPattern.CONFIDENCE_SCORING: LLMPatternCategory.UNCERTAINTY,
            LLMPattern.EPISTEMIC_UNCERTAINTY: LLMPatternCategory.UNCERTAINTY,
            LLMPattern.CALIBRATION: LLMPatternCategory.UNCERTAINTY,
            
            # Human-in-loop
            LLMPattern.CONFIDENCE_BASED_APPROVAL: LLMPatternCategory.HUMAN_IN_LOOP,
            LLMPattern.ACTIVE_LEARNING: LLMPatternCategory.HUMAN_IN_LOOP,
            
            # Robustness
            LLMPattern.FALLBACK_CASCADE: LLMPatternCategory.ROBUSTNESS,
            LLMPattern.ERROR_RECOVERY: LLMPatternCategory.ROBUSTNESS,
            
            # Optimization
            LLMPattern.PROMPT_CACHING: LLMPatternCategory.OPTIMIZATION,
            LLMPattern.PARALLEL_EXECUTION: LLMPatternCategory.OPTIMIZATION,
        }
        return pattern_categories[self]
    
    @property
    def complexity_score(self) -> int:
        """
        Complexity score (1-10) for this pattern.
        Higher = more complex/expensive to execute.
        """
        complexity: Dict[LLMPattern, int] = {
            # Simple patterns (1-3)
            LLMPattern.PROMPT_CACHING: 1,
            LLMPattern.ORCHESTRATION: 2,
            LLMPattern.CHAIN_OF_THOUGHT: 3,
            LLMPattern.CONFIDENCE_SCORING: 2,
            LLMPattern.FALLBACK_CASCADE: 2,
            
            # Medium patterns (4-6)
            LLMPattern.PARALLEL_EXECUTION: 4,
            LLMPattern.ADVANCED_RAG: 5,
            LLMPattern.HIERARCHICAL_RETRIEVAL: 5,
            LLMPattern.SELF_CONSISTENCY: 5,
            LLMPattern.DYNAMIC_CONTEXT_PRUNING: 4,
            LLMPattern.ERROR_RECOVERY: 4,
            LLMPattern.EPISTEMIC_UNCERTAINTY: 5,
            LLMPattern.CALIBRATION: 5,
            LLMPattern.CONFIDENCE_BASED_APPROVAL: 3,
            
            # Complex patterns (7-10)
            LLMPattern.ANALYSIS: 7,
            LLMPattern.SELECTIVE_ENSEMBLE: 7,
            LLMPattern.TREE_OF_THOUGHTS: 8,
            LLMPattern.GRAPH_OF_THOUGHTS: 9,
            LLMPattern.SELF_CRITIQUE: 7,
            LLMPattern.CONSTITUTIONAL_AI: 8,
            LLMPattern.DEBATE: 8,
            LLMPattern.COLLABORATION: 7,
            LLMPattern.VOTING: 6,
            LLMPattern.ACTIVE_LEARNING: 6,
        }
        return complexity.get(self, 5)
    
    @property
    def requires_multiple_models(self) -> bool:
        """Check if pattern requires multiple LLM invocations."""
        multi_model_patterns = {
            LLMPattern.ANALYSIS,
            LLMPattern.SELECTIVE_ENSEMBLE,
            LLMPattern.SELF_CONSISTENCY,
            LLMPattern.DEBATE,
            LLMPattern.COLLABORATION,
            LLMPattern.VOTING,
            LLMPattern.FALLBACK_CASCADE,
        }
        return self in multi_model_patterns
    
    @property
    def requires_human_review(self) -> bool:
        """Check if pattern involves human oversight."""
        human_patterns = {
            LLMPattern.CONFIDENCE_BASED_APPROVAL,
            LLMPattern.ACTIVE_LEARNING,
        }
        return self in human_patterns
    
    @classmethod
    def get_by_category(cls, category: LLMPatternCategory) -> List["LLMPattern"]:
        """Get all patterns in a category."""
        return [p for p in cls if p.category == category]
    
    @classmethod
    def get_recommended_patterns(
        cls, 
        query_complexity: int,
        requires_high_accuracy: bool = False,
        budget_constrained: bool = False
    ) -> List["LLMPattern"]:
        """
        Recommend patterns based on query characteristics.
        
        Args:
            query_complexity: Query complexity (1-10)
            requires_high_accuracy: Whether high accuracy is critical
            budget_constrained: Whether to prefer cheaper patterns
        
        Returns:
            List of recommended patterns
        """
        patterns = []
        
        # Always include these foundational patterns
        patterns.extend([
            LLMPattern.CHAIN_OF_THOUGHT,
            LLMPattern.CONFIDENCE_SCORING,
        ])
        
        # For complex queries
        if query_complexity >= 7:
            patterns.extend([
                LLMPattern.TREE_OF_THOUGHTS,
                LLMPattern.HIERARCHICAL_RETRIEVAL,
            ])
            
            if requires_high_accuracy:
                patterns.extend([
                    LLMPattern.SELF_CRITIQUE,
                    LLMPattern.DEBATE,
                ])
        
        # For medium complexity
        elif query_complexity >= 4:
            patterns.extend([
                LLMPattern.ADVANCED_RAG,
                LLMPattern.SELF_CONSISTENCY,
            ])
        
        # Optimization patterns
        if not budget_constrained:
            patterns.append(LLMPattern.PARALLEL_EXECUTION)
        else:
            patterns.append(LLMPattern.PROMPT_CACHING)
        
        # Always include fallback
        patterns.append(LLMPattern.FALLBACK_CASCADE)
        
        return patterns

