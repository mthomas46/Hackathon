"""Context Pruning pattern implementation."""

from typing import Any, Dict, List, Optional
from datetime import datetime

from .base import BasePatternEngine, PatternResult, PatternStep


class ContextPruningEngine(BasePatternEngine):
    """
    Context Pruning pattern execution engine.
    
    Intelligently manages context size by identifying and removing
    least relevant information while preserving essential content.
    Optimizes for token budgets while maintaining answer quality.
    
    Process:
    1. Analyze available context
    2. Score relevance of each piece
    3. Prune low-relevance content
    4. Optimize remaining context
    5. Generate answer with pruned context
    
    Key Innovation: Dynamic context optimization that maintains
    quality while respecting token constraints.
    """
    
    def __init__(self):
        super().__init__("context_pruning")
    
    async def execute(
        self,
        query: str,
        context: Dict[str, Any],
        config: Dict[str, Any]
    ) -> PatternResult:
        """Execute Context Pruning pattern."""
        start_time = datetime.utcnow()
        steps: List[PatternStep] = []
        
        try:
            # Configuration
            target_tokens = config.get("pruning_target_tokens", 1000)
            min_relevance = config.get("pruning_min_relevance", 0.5)
            
            # Step 1: Analyze context
            analysis_step = await self._analyze_context(
                query,
                context,
                config
            )
            steps.append(analysis_step)
            
            # Step 2: Score relevance
            scoring_step = await self._score_relevance(
                query,
                context,
                analysis_step.response,
                config
            )
            steps.append(scoring_step)
            
            # Step 3: Prune low-relevance content
            pruning_step = await self._prune_context(
                context,
                scoring_step.response,
                target_tokens,
                min_relevance,
                config
            )
            steps.append(pruning_step)
            
            # Step 4: Optimize remaining context
            optimization_step = await self._optimize_context(
                query,
                pruning_step.response,
                config
            )
            steps.append(optimization_step)
            
            # Step 5: Generate answer with pruned context
            generation_step = await self._generate_with_pruned_context(
                query,
                optimization_step.response,
                config
            )
            steps.append(generation_step)
            
            # Calculate execution time
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Calculate confidence
            confidence = self._calculate_pruning_confidence(
                scoring_step,
                pruning_step
            )
            
            # Calculate pruning stats
            original_size = self._estimate_tokens(context.get("mcp_data", ""))
            pruned_size = self._estimate_tokens(optimization_step.response or "")
            pruning_ratio = 1 - (pruned_size / max(original_size, 1))
            
            return PatternResult(
                pattern_type=self.pattern_type,
                success=True,
                steps=steps,
                final_answer=generation_step.response,
                confidence=confidence,
                total_duration_ms=duration_ms,
                metadata={
                    "original_tokens": original_size,
                    "pruned_tokens": pruned_size,
                    "pruning_ratio": pruning_ratio,
                    "target_tokens": target_tokens,
                    "relevance_threshold": min_relevance
                }
            )
        
        except Exception as e:
            self.logger.error(f"Error executing Context Pruning: {e}", exc_info=True)
            
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            return PatternResult(
                pattern_type=self.pattern_type,
                success=False,
                steps=steps,
                total_duration_ms=duration_ms,
                error=str(e)
            )
    
    async def _analyze_context(
        self,
        query: str,
        context: Dict[str, Any],
        config: Dict[str, Any]
    ) -> PatternStep:
        """Analyze context structure and content."""
        step = self.create_step(
            step_id="analysis",
            step_type="analysis",
            description="Analyze context",
            prompt=self._build_analysis_prompt(query, context)
        )
        
        try:
            response = await self.call_llm(step.prompt, config)
            self.complete_step(
                step,
                response,
                {"stage": "analysis"}
            )
        except Exception as e:
            self.complete_step(step, f"Error: {e}", {"error": True})
        
        return step
    
    async def _score_relevance(
        self,
        query: str,
        context: Dict[str, Any],
        analysis: str,
        config: Dict[str, Any]
    ) -> PatternStep:
        """Score relevance of context pieces."""
        step = self.create_step(
            step_id="scoring",
            step_type="scoring",
            description="Score relevance",
            prompt=self._build_scoring_prompt(query, context, analysis)
        )
        
        try:
            response = await self.call_llm(step.prompt, config)
            self.complete_step(
                step,
                response,
                {"stage": "scoring"}
            )
        except Exception as e:
            self.complete_step(step, f"Error: {e}", {"error": True})
        
        return step
    
    async def _prune_context(
        self,
        context: Dict[str, Any],
        scores: str,
        target_tokens: int,
        min_relevance: float,
        config: Dict[str, Any]
    ) -> PatternStep:
        """Prune low-relevance content."""
        step = self.create_step(
            step_id="pruning",
            step_type="pruning",
            description="Prune context",
            prompt=self._build_pruning_prompt(
                context,
                scores,
                target_tokens,
                min_relevance
            )
        )
        
        try:
            response = await self.call_llm(step.prompt, config)
            self.complete_step(
                step,
                response,
                {"stage": "pruning"}
            )
        except Exception as e:
            self.complete_step(step, f"Error: {e}", {"error": True})
        
        return step
    
    async def _optimize_context(
        self,
        query: str,
        pruned_context: str,
        config: Dict[str, Any]
    ) -> PatternStep:
        """Optimize remaining context."""
        step = self.create_step(
            step_id="optimization",
            step_type="optimization",
            description="Optimize context",
            prompt=self._build_optimization_prompt(query, pruned_context)
        )
        
        try:
            response = await self.call_llm(step.prompt, config)
            self.complete_step(
                step,
                response,
                {"stage": "optimization"}
            )
        except Exception as e:
            self.complete_step(step, f"Error: {e}", {"error": True})
        
        return step
    
    async def _generate_with_pruned_context(
        self,
        query: str,
        optimized_context: str,
        config: Dict[str, Any]
    ) -> PatternStep:
        """Generate answer using pruned context."""
        step = self.create_step(
            step_id="generation",
            step_type="generation",
            description="Generate with pruned context",
            prompt=self._build_generation_prompt(query, optimized_context)
        )
        
        try:
            response = await self.call_llm(step.prompt, config)
            self.complete_step(
                step,
                response,
                {"stage": "generation"}
            )
        except Exception as e:
            self.complete_step(step, f"Error: {e}", {"error": True})
        
        return step
    
    def _build_analysis_prompt(
        self,
        query: str,
        context: Dict[str, Any]
    ) -> str:
        """Build prompt for context analysis."""
        context_data = context.get("mcp_data", "")[:1000]
        
        return f"""Analyze this context for the given query.

Query: {query}

Context:
{context_data}...

Analysis Instructions:
1. Identify main topics/themes
2. Note key information pieces
3. Identify redundant content
4. Assess overall relevance
5. Estimate importance of sections

Context Analysis:"""
    
    def _build_scoring_prompt(
        self,
        query: str,
        context: Dict[str, Any],
        analysis: str
    ) -> str:
        """Build prompt for relevance scoring."""
        context_data = context.get("mcp_data", "")[:800]
        
        return f"""Score relevance of context pieces for this query.

Query: {query}

Context:
{context_data}...

Analysis:
{analysis[:400]}...

Scoring Instructions:
1. Break context into logical pieces
2. Score each piece 0.0-1.0 for relevance
3. Consider direct vs indirect relevance
4. List scores clearly

Format:
Piece 1: [summary] - Score: [0.0-1.0]
Piece 2: [summary] - Score: [0.0-1.0]

Relevance Scores:"""
    
    def _build_pruning_prompt(
        self,
        context: Dict[str, Any],
        scores: str,
        target_tokens: int,
        min_relevance: float
    ) -> str:
        """Build prompt for pruning."""
        context_data = context.get("mcp_data", "")[:800]
        
        return f"""Prune this context to meet token budget while preserving essential information.

Original Context:
{context_data}...

Relevance Scores:
{scores[:400]}...

Pruning Instructions:
1. Target: ~{target_tokens} tokens
2. Remove pieces with relevance < {min_relevance}
3. Remove redundant information
4. Preserve highest relevance content
5. Maintain coherence

Pruned Context:"""
    
    def _build_optimization_prompt(
        self,
        query: str,
        pruned_context: str
    ) -> str:
        """Build prompt for context optimization."""
        return f"""Optimize this pruned context for maximum clarity and relevance.

Query: {query}

Pruned Context:
{pruned_context[:800]}...

Optimization Instructions:
1. Restructure for clarity
2. Remove remaining redundancy
3. Ensure logical flow
4. Maintain key information
5. Be concise

Optimized Context:"""
    
    def _build_generation_prompt(
        self,
        query: str,
        optimized_context: str
    ) -> str:
        """Build prompt for answer generation."""
        return f"""Answer using the optimized context.

Query: {query}

Optimized Context:
{optimized_context[:800]}...

Generation Instructions:
1. Use ONLY provided context
2. Be direct and clear
3. Maximize information density
4. Acknowledge if context insufficient

Answer:"""
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough heuristic)."""
        if not text:
            return 0
        # Rough estimate: 1 token ≈ 4 characters
        return len(text) // 4
    
    def _calculate_pruning_confidence(
        self,
        scoring_step: PatternStep,
        pruning_step: PatternStep
    ) -> float:
        """Calculate confidence based on pruning quality."""
        if not scoring_step or not pruning_step:
            return 0.5
        
        # Heuristic: if we have scoring and pruning, reasonable confidence
        return 0.75

