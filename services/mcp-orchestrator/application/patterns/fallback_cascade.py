"""Fallback Cascade pattern implementation."""

from typing import Any, Dict, List, Optional
from datetime import datetime

from .base import BasePatternEngine, PatternResult, PatternStep


class FallbackCascadeEngine(BasePatternEngine):
    """
    Fallback Cascade pattern execution engine.
    
    Implements a hierarchy of strategies, gracefully falling back
    to simpler/more reliable methods when preferred approaches fail.
    
    Process:
    1. Try primary strategy (most sophisticated)
    2. If failure → fallback to secondary
    3. Continue cascading until success
    4. Each level has increasing reliability, decreasing sophistication
    
    Key Innovation: Graceful degradation with multiple backup
    strategies ensuring robust operation even when optimal fails.
    """
    
    def __init__(self):
        super().__init__("fallback_cascade")
    
    async def execute(
        self,
        query: str,
        context: Dict[str, Any],
        config: Dict[str, Any]
    ) -> PatternResult:
        """Execute Fallback Cascade pattern."""
        start_time = datetime.utcnow()
        steps: List[PatternStep] = []
        
        try:
            # Configuration
            strategies = config.get("fallback_strategies", [
                "advanced", "standard", "simple", "basic"
            ])
            
            final_answer = None
            successful_strategy = None
            
            # Try each strategy in order
            for i, strategy in enumerate(strategies):
                self.logger.info(f"Attempting strategy: {strategy}")
                
                # Try this strategy
                attempt_step = await self._attempt_strategy(
                    query,
                    context,
                    config,
                    strategy,
                    i
                )
                steps.append(attempt_step)
                
                # Check if successful
                is_successful = await self._validate_result(
                    attempt_step.response,
                    query,
                    config
                )
                
                if is_successful:
                    self.logger.info(f"Strategy '{strategy}' succeeded!")
                    final_answer = attempt_step.response
                    successful_strategy = strategy
                    break
                else:
                    self.logger.info(f"Strategy '{strategy}' failed, falling back...")
                    # Create fallback step
                    fallback_step = self.create_step(
                        step_id=f"fallback_from_{strategy}",
                        step_type="fallback",
                        description=f"Fallback from {strategy}",
                        prompt=""
                    )
                    self.complete_step(
                        fallback_step,
                        f"Strategy '{strategy}' failed, attempting next level",
                        {
                            "stage": "fallback",
                            "failed_strategy": strategy
                        }
                    )
                    steps.append(fallback_step)
            
            # If all strategies failed, use last attempt
            if final_answer is None:
                final_answer = steps[-2].response if len(steps) >= 2 else "All strategies failed"
                successful_strategy = "none"
            
            # Calculate execution time
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Calculate confidence based on which strategy succeeded
            confidence = self._calculate_fallback_confidence(
                successful_strategy,
                strategies
            )
            
            return PatternResult(
                pattern_type=self.pattern_type,
                success=successful_strategy != "none",
                steps=steps,
                final_answer=final_answer,
                confidence=confidence,
                total_duration_ms=duration_ms,
                metadata={
                    "successful_strategy": successful_strategy,
                    "attempts": len([s for s in steps if s.step_type == "attempt"]),
                    "fallbacks": len([s for s in steps if s.step_type == "fallback"]),
                    "strategy_hierarchy": strategies
                }
            )
        
        except Exception as e:
            self.logger.error(f"Error executing Fallback Cascade: {e}", exc_info=True)
            
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            return PatternResult(
                pattern_type=self.pattern_type,
                success=False,
                steps=steps,
                total_duration_ms=duration_ms,
                error=str(e)
            )
    
    async def _attempt_strategy(
        self,
        query: str,
        context: Dict[str, Any],
        config: Dict[str, Any],
        strategy: str,
        attempt_num: int
    ) -> PatternStep:
        """Attempt a specific strategy."""
        step = self.create_step(
            step_id=f"attempt_{strategy}",
            step_type="attempt",
            description=f"Attempt {strategy} strategy",
            prompt=self._build_strategy_prompt(query, context, strategy)
        )
        
        try:
            response = await self.call_llm(step.prompt, config)
            self.complete_step(
                step,
                response,
                {
                    "stage": "attempt",
                    "strategy": strategy,
                    "attempt_number": attempt_num
                }
            )
        except Exception as e:
            self.complete_step(
                step,
                f"Strategy failed: {e}",
                {
                    "error": True,
                    "strategy": strategy
                }
            )
        
        return step
    
    async def _validate_result(
        self,
        result: str,
        query: str,
        config: Dict[str, Any]
    ) -> bool:
        """Validate if result is acceptable."""
        if not result or len(result) < 20:
            return False
        
        # Simple validation: check for error indicators
        result_lower = result.lower()
        error_indicators = [
            "error", "failed", "unable", "cannot",
            "don't know", "insufficient"
        ]
        
        has_errors = any(indicator in result_lower for indicator in error_indicators)
        return not has_errors
    
    def _build_strategy_prompt(
        self,
        query: str,
        context: Dict[str, Any],
        strategy: str
    ) -> str:
        """Build prompt for specific strategy."""
        context_str = self._format_context(context)
        
        if strategy == "advanced":
            return f"""Use advanced reasoning to answer this query comprehensively.

Query: {query}

{context_str}

Advanced Strategy Instructions:
1. Apply sophisticated analysis
2. Consider multiple perspectives
3. Provide detailed reasoning
4. Include nuanced insights
5. Be thorough and comprehensive

Answer:"""
        
        elif strategy == "standard":
            return f"""Use standard approach to answer this query.

Query: {query}

{context_str}

Standard Strategy Instructions:
1. Apply straightforward reasoning
2. Focus on main points
3. Provide clear answer
4. Include key details
5. Be direct and accurate

Answer:"""
        
        elif strategy == "simple":
            return f"""Use simple, direct approach to answer this query.

Query: {query}

{context_str}

Simple Strategy Instructions:
1. Answer directly
2. Keep it straightforward
3. Focus on essentials
4. Minimal complexity
5. Clear and concise

Answer:"""
        
        else:  # basic
            return f"""Provide a basic answer to this query.

Query: {query}

Basic Strategy Instructions:
1. Answer the question
2. Be brief
3. State what you know
4. Don't overcomplicate

Answer:"""
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context for prompts."""
        if not context:
            return ""
        
        context_parts = []
        
        if "mcp_data" in context:
            context_parts.append(f"Context: {context['mcp_data'][:300]}...")
        
        if context_parts:
            return "\n".join(context_parts)
        
        return ""
    
    def _calculate_fallback_confidence(
        self,
        successful_strategy: str,
        strategies: List[str]
    ) -> float:
        """Calculate confidence based on which strategy succeeded."""
        if successful_strategy == "none":
            return 0.2
        
        try:
            index = strategies.index(successful_strategy)
            # Earlier strategies (lower index) = higher confidence
            # First strategy: 1.0, second: 0.8, third: 0.6, etc.
            confidence = 1.0 - (index * 0.2)
            return max(confidence, 0.4)
        except ValueError:
            return 0.5

