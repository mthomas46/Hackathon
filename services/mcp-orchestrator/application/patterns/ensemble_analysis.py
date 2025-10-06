"""Ensemble Analysis pattern implementation."""

from typing import Any, Dict, List, Optional
from datetime import datetime
import asyncio
import statistics

from .base import BasePatternEngine, PatternResult, PatternStep


class EnsembleAnalysisEngine(BasePatternEngine):
    """
    Ensemble Analysis pattern execution engine.
    
    Gets multiple independent LLM responses to the same query and uses
    consensus/voting to determine the best answer. This reduces hallucinations
    and increases reliability through redundancy.
    
    Process:
    1. Parallel execution - Same query to N LLMs
    2. Response collection - Gather all responses
    3. Consensus analysis - Find common themes, voting
    4. Confidence scoring - Based on agreement level
    5. Best answer selection - Choose or synthesize answer
    
    Advantages:
    - Reduces hallucinations (outliers filtered)
    - Increases reliability (consensus = confidence)
    - Self-checks quality (agreement = correctness)
    - Handles uncertainty (disagreement = flag)
    """
    
    def __init__(self):
        super().__init__("ensemble_analysis")
    
    async def execute(
        self,
        query: str,
        context: Dict[str, Any],
        config: Dict[str, Any]
    ) -> PatternResult:
        """Execute Ensemble Analysis pattern."""
        start_time = datetime.utcnow()
        steps: List[PatternStep] = []
        
        try:
            # Configuration
            ensemble_size = config.get("ensemble_size", 5)
            consensus_method = config.get("consensus_method", "voting")  # voting, averaging, synthesis
            agreement_threshold = config.get("agreement_threshold", 0.6)
            
            # Step 1: Execute query N times in parallel
            execution_steps = await self._execute_ensemble(
                query,
                context,
                config,
                ensemble_size
            )
            steps.extend(execution_steps)
            
            # Step 2: Analyze responses for consensus
            consensus_step = await self._analyze_consensus(
                query,
                execution_steps,
                context,
                config,
                consensus_method
            )
            steps.append(consensus_step)
            
            # Step 3: Calculate agreement level
            agreement_score = self._calculate_agreement(execution_steps)
            
            # Step 4: Select or synthesize best answer
            if agreement_score >= agreement_threshold:
                # High agreement - use consensus
                final_answer = consensus_step.response
                confidence = agreement_score
            else:
                # Low agreement - synthesize with uncertainty noted
                synthesis_step = await self._synthesize_with_uncertainty(
                    query,
                    execution_steps,
                    consensus_step,
                    context,
                    config,
                    agreement_score
                )
                steps.append(synthesis_step)
                final_answer = synthesis_step.response
                confidence = agreement_score * 0.7  # Penalize low agreement
            
            # Calculate execution time
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            return PatternResult(
                pattern_type=self.pattern_type,
                success=True,
                steps=steps,
                final_answer=final_answer,
                confidence=confidence,
                total_duration_ms=duration_ms,
                metadata={
                    "ensemble_size": ensemble_size,
                    "consensus_method": consensus_method,
                    "agreement_score": agreement_score,
                    "high_agreement": agreement_score >= agreement_threshold,
                    "response_diversity": self._calculate_diversity(execution_steps)
                }
            )
        
        except Exception as e:
            self.logger.error(f"Error executing Ensemble Analysis: {e}", exc_info=True)
            
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            return PatternResult(
                pattern_type=self.pattern_type,
                success=False,
                steps=steps,
                total_duration_ms=duration_ms,
                error=str(e)
            )
    
    async def _execute_ensemble(
        self,
        query: str,
        context: Dict[str, Any],
        config: Dict[str, Any],
        size: int
    ) -> List[PatternStep]:
        """Execute same query N times in parallel."""
        # Create N identical prompts
        prompt = self._build_ensemble_prompt(query, context)
        
        # Create coroutines for parallel execution
        coroutines = [
            self._execute_single_instance(i, query, prompt, config)
            for i in range(size)
        ]
        
        # Execute all in parallel
        execution_steps = await asyncio.gather(*coroutines)
        
        return list(execution_steps)
    
    async def _execute_single_instance(
        self,
        instance_id: int,
        query: str,
        prompt: str,
        config: Dict[str, Any]
    ) -> PatternStep:
        """Execute single instance."""
        step = self.create_step(
            step_id=f"instance_{instance_id}",
            step_type="instance_execution",
            description=f"LLM instance {instance_id + 1}",
            prompt=prompt
        )
        
        try:
            response = await self.call_llm(prompt, config)
            self.complete_step(
                step,
                response,
                {
                    "stage": "instance_execution",
                    "instance_id": instance_id
                }
            )
        except Exception as e:
            self.complete_step(step, f"Error: {e}", {"error": True})
        
        return step
    
    async def _analyze_consensus(
        self,
        query: str,
        execution_steps: List[PatternStep],
        context: Dict[str, Any],
        config: Dict[str, Any],
        method: str
    ) -> PatternStep:
        """Analyze responses for consensus."""
        step = self.create_step(
            step_id="analyze_consensus",
            step_type="consensus_analysis",
            description=f"Analyze consensus among {len(execution_steps)} responses",
            prompt=self._build_consensus_prompt(
                query,
                execution_steps,
                context,
                method
            )
        )
        
        try:
            response = await self.call_llm(step.prompt, config)
            self.complete_step(
                step,
                response,
                {
                    "stage": "consensus_analysis",
                    "method": method,
                    "responses_analyzed": len(execution_steps)
                }
            )
        except Exception as e:
            self.complete_step(step, f"Error: {e}", {"error": True})
        
        return step
    
    async def _synthesize_with_uncertainty(
        self,
        query: str,
        execution_steps: List[PatternStep],
        consensus_step: PatternStep,
        context: Dict[str, Any],
        config: Dict[str, Any],
        agreement_score: float
    ) -> PatternStep:
        """Synthesize answer when agreement is low."""
        step = self.create_step(
            step_id="synthesize_uncertain",
            step_type="uncertain_synthesis",
            description="Synthesize answer with low agreement",
            prompt=self._build_uncertain_synthesis_prompt(
                query,
                execution_steps,
                consensus_step,
                context,
                agreement_score
            )
        )
        
        try:
            response = await self.call_llm(step.prompt, config)
            self.complete_step(
                step,
                response,
                {
                    "stage": "uncertain_synthesis",
                    "agreement_score": agreement_score
                }
            )
        except Exception as e:
            self.complete_step(step, f"Error: {e}", {"error": True})
        
        return step
    
    def _build_ensemble_prompt(
        self,
        query: str,
        context: Dict[str, Any]
    ) -> str:
        """Build prompt for ensemble execution."""
        context_str = self._format_context(context)
        
        return f"""Answer the following query thoroughly and accurately.

Query: {query}

{context_str}

Instructions:
1. Provide a clear, complete answer
2. Be specific and factual
3. If uncertain, state your uncertainty
4. Support claims with reasoning
5. Be concise but comprehensive

Answer:"""
    
    def _build_consensus_prompt(
        self,
        query: str,
        execution_steps: List[PatternStep],
        context: Dict[str, Any],
        method: str
    ) -> str:
        """Build prompt for consensus analysis."""
        context_str = self._format_context(context)
        
        # Gather all responses
        responses_str = "\n\n".join([
            f"Response {i+1}:\n{step.response[:400]}..."
            if step.response else f"Response {i+1}: No response"
            for i, step in enumerate(execution_steps)
            if step.step_type == "instance_execution"
        ])
        
        method_instructions = {
            "voting": "Identify the most common answer. Look for majority agreement.",
            "averaging": "Find the middle ground. Balance all perspectives.",
            "synthesis": "Combine the best elements from all responses."
        }
        
        instruction = method_instructions.get(method, "Identify consensus.")
        
        return f"""Analyze multiple responses to find consensus.

Original Query: {query}

{context_str}

Responses from {len(execution_steps)} independent LLM instances:
{responses_str}

Instructions:
1. Identify common themes and agreements
2. {instruction}
3. Note any significant disagreements
4. Assess overall confidence level
5. Provide the consensus answer

Consensus Analysis:"""
    
    def _build_uncertain_synthesis_prompt(
        self,
        query: str,
        execution_steps: List[PatternStep],
        consensus_step: PatternStep,
        context: Dict[str, Any],
        agreement_score: float
    ) -> str:
        """Build prompt for synthesis with low agreement."""
        context_str = self._format_context(context)
        
        # Sample some responses
        sample_responses = "\n\n".join([
            f"Response {i+1}: {step.response[:200]}..."
            if step.response else f"Response {i+1}: No response"
            for i, step in enumerate(execution_steps[:3])
            if step.step_type == "instance_execution"
        ])
        
        consensus_text = consensus_step.response if consensus_step else "No consensus"
        
        return f"""Synthesize an answer despite low agreement among responses.

Original Query: {query}

{context_str}

Agreement Level: {agreement_score:.1%} (LOW)

Sample Responses:
{sample_responses}

Consensus Attempt:
{consensus_text[:300]}...

Instructions:
1. Acknowledge the uncertainty/disagreement
2. Present multiple perspectives if needed
3. Provide the most likely answer
4. Explain why there's disagreement
5. Suggest what additional information would help

Answer (with uncertainty noted):"""
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context for prompts."""
        if not context:
            return ""
        
        context_parts = []
        
        if "mcp_data" in context:
            context_parts.append(f"Context: {context['mcp_data'][:300]}...")
        
        if "entities" in context:
            entities = context["entities"]
            if entities:
                context_parts.append(f"Entities: {', '.join(entities[:5])}")
        
        if context_parts:
            return "\n".join(context_parts)
        
        return ""
    
    def _calculate_agreement(self, execution_steps: List[PatternStep]) -> float:
        """Calculate agreement level among responses."""
        responses = [
            step.response
            for step in execution_steps
            if step.step_type == "instance_execution" and step.response
        ]
        
        if len(responses) < 2:
            return 0.5
        
        # Simple heuristic: similarity of response lengths and starts
        lengths = [len(r) for r in responses]
        starts = [r[:100].lower() for r in responses]
        
        # Length agreement (normalized std dev)
        mean_length = statistics.mean(lengths)
        if mean_length > 0:
            length_variation = statistics.stdev(lengths) / mean_length
            length_agreement = max(0, 1 - length_variation)
        else:
            length_agreement = 0.5
        
        # Start similarity (how many share similar opening)
        unique_starts = len(set(starts))
        start_agreement = 1 - (unique_starts - 1) / len(starts)
        
        # Combine
        agreement = (length_agreement * 0.3 + start_agreement * 0.7)
        
        return min(max(agreement, 0.0), 1.0)
    
    def _calculate_diversity(self, execution_steps: List[PatternStep]) -> float:
        """Calculate response diversity."""
        responses = [
            step.response
            for step in execution_steps
            if step.step_type == "instance_execution" and step.response
        ]
        
        if len(responses) < 2:
            return 0.0
        
        # Count unique response starts
        unique_starts = len(set(r[:100].lower() for r in responses))
        diversity = unique_starts / len(responses)
        
        return diversity

