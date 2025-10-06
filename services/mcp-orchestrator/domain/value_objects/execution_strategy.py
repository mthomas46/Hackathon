"""Execution Strategy Value Object."""

from enum import Enum
from typing import Dict


class ExecutionStrategy(str, Enum):
    """
    Defines how to execute a workflow across multiple MCPs.
    
    Different strategies optimize for different goals:
    speed, accuracy, cost, reliability, etc.
    """
    
    SEQUENTIAL = "sequential"
    """Execute MCPs one at a time, in order."""
    
    PARALLEL = "parallel"
    """Execute all MCPs simultaneously for maximum speed."""
    
    WATERFALL = "waterfall"
    """Each MCP passes results to the next (data pipeline)."""
    
    SCATTER_GATHER = "scatter_gather"
    """Parallel execution, then aggregate all results."""
    
    PRIORITY_FIRST = "priority_first"
    """Execute highest priority MCP first, others as needed."""
    
    LAZY = "lazy"
    """Only execute MCPs when their data is actually needed."""
    
    ADAPTIVE = "adaptive"
    """Dynamically choose strategy based on results."""
    
    FAILFAST = "failfast"
    """Stop immediately on first error."""
    
    RESILIENT = "resilient"
    """Continue even if some MCPs fail, aggregate partial results."""
    
    BUDGET_AWARE = "budget_aware"
    """Optimize for cost, skip expensive MCPs if possible."""
    
    @property
    def supports_parallel_execution(self) -> bool:
        """Check if strategy allows parallel execution."""
        return self in {
            ExecutionStrategy.PARALLEL,
            ExecutionStrategy.SCATTER_GATHER,
            ExecutionStrategy.ADAPTIVE,
            ExecutionStrategy.RESILIENT,
        }
    
    @property
    def is_fault_tolerant(self) -> bool:
        """Check if strategy handles failures gracefully."""
        return self in {
            ExecutionStrategy.RESILIENT,
            ExecutionStrategy.ADAPTIVE,
            ExecutionStrategy.BUDGET_AWARE,
        }
    
    @property
    def expected_latency_multiplier(self) -> float:
        """
        Expected latency multiplier vs single MCP query.
        
        Returns:
            Multiplier (1.0 = same as single query, 2.0 = double, etc.)
        """
        multipliers: Dict[ExecutionStrategy, float] = {
            ExecutionStrategy.SEQUENTIAL: 3.0,      # Sum of all MCPs
            ExecutionStrategy.PARALLEL: 1.2,        # Parallel overhead only
            ExecutionStrategy.WATERFALL: 3.5,       # Sequential + data transfer
            ExecutionStrategy.SCATTER_GATHER: 1.3,  # Parallel + aggregation
            ExecutionStrategy.PRIORITY_FIRST: 1.5,  # Primary + some secondaries
            ExecutionStrategy.LAZY: 2.0,            # Depends on data access
            ExecutionStrategy.ADAPTIVE: 2.5,        # Dynamic decision overhead
            ExecutionStrategy.FAILFAST: 2.0,        # May stop early
            ExecutionStrategy.RESILIENT: 3.2,       # All MCPs + retries
            ExecutionStrategy.BUDGET_AWARE: 1.8,    # Skips some MCPs
        }
        return multipliers.get(self, 2.0)
    
    @property
    def complexity_score(self) -> int:
        """
        Complexity score (1-10) for implementation.
        
        Returns:
            Score from 1 (simple) to 10 (complex)
        """
        scores: Dict[ExecutionStrategy, int] = {
            ExecutionStrategy.SEQUENTIAL: 2,
            ExecutionStrategy.PARALLEL: 4,
            ExecutionStrategy.WATERFALL: 5,
            ExecutionStrategy.SCATTER_GATHER: 6,
            ExecutionStrategy.PRIORITY_FIRST: 3,
            ExecutionStrategy.LAZY: 7,
            ExecutionStrategy.ADAPTIVE: 9,
            ExecutionStrategy.FAILFAST: 3,
            ExecutionStrategy.RESILIENT: 8,
            ExecutionStrategy.BUDGET_AWARE: 7,
        }
        return scores.get(self, 5)
    
    @classmethod
    def get_recommended(
        cls,
        num_mcps: int,
        requires_high_accuracy: bool = False,
        time_sensitive: bool = False,
        budget_constrained: bool = False,
    ) -> "ExecutionStrategy":
        """
        Recommend an execution strategy based on requirements.
        
        Args:
            num_mcps: Number of MCPs to query
            requires_high_accuracy: Whether accuracy is critical
            time_sensitive: Whether speed is critical
            budget_constrained: Whether cost is a concern
        
        Returns:
            Recommended execution strategy
        """
        # Single MCP - always sequential
        if num_mcps == 1:
            return cls.SEQUENTIAL
        
        # Budget constrained
        if budget_constrained:
            return cls.BUDGET_AWARE
        
        # Time sensitive
        if time_sensitive:
            return cls.PARALLEL if num_mcps <= 5 else cls.SCATTER_GATHER
        
        # High accuracy needed
        if requires_high_accuracy:
            return cls.RESILIENT  # Get all results, handle failures
        
        # Default: balance speed and reliability
        if num_mcps <= 3:
            return cls.PARALLEL
        else:
            return cls.SCATTER_GATHER

