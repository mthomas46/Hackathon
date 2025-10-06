"""Query Intent Value Object."""

from enum import Enum


class QueryIntent(str, Enum):
    """
    Represents the intent/purpose of a natural language query.
    
    This determines what the user wants to do with the information.
    """
    
    # Information Retrieval
    SEARCH = "search"              # Find specific information
    LOOKUP = "lookup"              # Get details about something specific
    LIST = "list"                  # Get a list of items
    
    # Analysis & Understanding
    ANALYZE = "analyze"            # Deep analysis of data/patterns
    SUMMARIZE = "summarize"        # Summarize information
    EXPLAIN = "explain"            # Explain concepts or decisions
    
    # Comparison & Evaluation
    COMPARE = "compare"            # Compare multiple items
    EVALUATE = "evaluate"          # Assess quality or performance
    RANK = "rank"                  # Order items by criteria
    
    # Recommendation & Prediction
    RECOMMEND = "recommend"        # Suggest best options
    PREDICT = "predict"            # Forecast future outcomes
    SUGGEST = "suggest"            # Provide suggestions
    
    # Aggregation & Statistics
    COUNT = "count"                # Count items
    AGGREGATE = "aggregate"        # Compute statistics
    TREND = "trend"                # Identify trends over time
    
    # Creation & Planning
    GENERATE = "generate"          # Create new content
    PLAN = "plan"                  # Create plans or strategies
    
    # Unknown/Unclear
    UNKNOWN = "unknown"            # Intent not clear
    
    @property
    def requires_multiple_mcps(self) -> bool:
        """Check if intent typically requires querying multiple MCPs."""
        return self in {
            QueryIntent.COMPARE,
            QueryIntent.ANALYZE,
            QueryIntent.RECOMMEND,
            QueryIntent.PLAN,
            QueryIntent.AGGREGATE,
            QueryIntent.TREND,
        }
    
    @property
    def is_read_only(self) -> bool:
        """Check if intent is read-only (no mutations)."""
        return self not in {
            QueryIntent.GENERATE,
            QueryIntent.PLAN,
        }
    
    @property
    def complexity_score(self) -> int:
        """
        Get complexity score for the intent (1-10).
        Higher scores indicate more complex operations.
        """
        complexity_map = {
            QueryIntent.LOOKUP: 1,
            QueryIntent.SEARCH: 2,
            QueryIntent.LIST: 2,
            QueryIntent.COUNT: 2,
            QueryIntent.SUMMARIZE: 4,
            QueryIntent.EXPLAIN: 5,
            QueryIntent.COMPARE: 6,
            QueryIntent.EVALUATE: 6,
            QueryIntent.RANK: 6,
            QueryIntent.AGGREGATE: 6,
            QueryIntent.ANALYZE: 7,
            QueryIntent.TREND: 7,
            QueryIntent.RECOMMEND: 8,
            QueryIntent.SUGGEST: 7,
            QueryIntent.PREDICT: 9,
            QueryIntent.GENERATE: 8,
            QueryIntent.PLAN: 10,
            QueryIntent.UNKNOWN: 5,
        }
        return complexity_map.get(self, 5)

