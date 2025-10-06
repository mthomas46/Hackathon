"""Iterative Refinement pattern implementation."""

from typing import Any, Dict, List, Optional
from datetime import datetime

from .base import BasePatternEngine, PatternResult, PatternStep


class IterativeRefinementEngine(BasePatternEngine):
    """
    Iterative Refinement pattern execution engine.
    
    Progressive improvement through feedback loops. Each iteration
    refines the response based on evaluation and feedback until
    quality goals are met.
    
    Process:
    1. Generate initial response
    2. Evaluate quality/completeness
    3. Identify improvement areas
    4. Refine based on feedback
    5. Repeat until satisfactory
    
    Key Innovation: Continuous improvement through
    iterative evaluation and targeted refinement.
    """
    
    def __init__(self):
        super().__init__("iterative_refinement")
    
    async def execute(
        self,
        query: str,
        context: Dict[str, Any],
        config: Dict[str, Any]
    ) -> PatternResult:
        """Execute Iterative Refinement pattern."""
        start_time = datetime.utcnow()
        steps: List[PatternStep] = []
        
        try:
            # Configuration
            max_iterations = config.get("refinement_max_iterations", 3)
            quality_threshold = config.get("refinement_quality_threshold", 0.8)
            
            current_response = ""
            quality_scores = []
            
            for iteration in range(max_iterations):
                self.logger.info(f"Refinement iteration {iteration + 1}")
                
                # Step 1: Generate or refine
                if iteration == 0:
                    generation_step = await self._initial_generation(
                        query,
                        context,
                        config
                    )
                else:
                    generation_step = await self._refine_response(
                        query,
                        current_response,
                        evaluation_step.response,
                        config,
                        iteration
                    )
                steps.append(generation_step)
                current_response = generation_step.response or ""
                
                # Step 2: Evaluate quality
                evaluation_step = await self._evaluate_quality(
                    query,
                    current_response,
                    context,
                    config,
                    iteration
                )
                steps.append(evaluation_step)
                
                quality_score = self._parse_quality_score(evaluation_step.response)
                quality_scores.append(quality_score)
                
                self.logger.info(f"Iteration {iteration + 1} quality: {quality_score:.2f}")
                
                # Check if threshold met
                if quality_score >= quality_threshold:
                    self.logger.info(f"Quality threshold met: {quality_score:.2f}")
                    break
                
                # Step 3: Identify improvements (if not last iteration)
                if iteration < max_iterations - 1:
                    improvement_step = await self._identify_improvements(
                        query,
                        current_response,
                        evaluation_step.response,
                        config
                    )
                    steps.append(improvement_step)
            
            # Final polish
            polish_step = await self._final_polish(
                query,
                current_response,
                config
            )
            steps.append(polish_step)
            final_answer = polish_step.response or current_response
            
            # Calculate execution time
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Calculate confidence
            confidence = self._calculate_refinement_confidence(quality_scores)
            
            return PatternResult(
                pattern_type=self.pattern_type,
                success=True,
                steps=steps,
                final_answer=final_answer,
                confidence=confidence,
                total_duration_ms=duration_ms,
                metadata={
                    "iterations": len(quality_scores),
                    "quality_scores": quality_scores,
                    "final_quality": quality_scores[-1] if quality_scores else 0.0,
                    "improvement_trajectory": self._calculate_improvement(quality_scores)
                }
            )
        
        except Exception as e:
            self.logger.error(f"Error executing Iterative Refinement: {e}", exc_info=True)
            
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            return PatternResult(
                pattern_type=self.pattern_type,
                success=False,
                steps=steps,
                total_duration_ms=duration_ms,
                error=str(e)
            )
    
    async def _initial_generation(
        self,
        query: str,
        context: Dict[str, Any],
        config: Dict[str, Any]
    ) -> PatternStep:
        """Generate initial response."""
        step = self.create_step(
            step_id="initial_generation",
            step_type="generation",
            description="Initial generation",
            prompt=self._build_initial_prompt(query, context)
        )
        
        try:
            response = await self.call_llm(step.prompt, config)
            self.complete_step(
                step,
                response,
                {"stage": "generation", "iteration": 0}
            )
        except Exception as e:
            self.complete_step(step, f"Error: {e}", {"error": True})
        
        return step
    
    async def _refine_response(
        self,
        query: str,
        current_response: str,
        evaluation: str,
        config: Dict[str, Any],
        iteration: int
    ) -> PatternStep:
        """Refine response based on evaluation."""
        step = self.create_step(
            step_id=f"refinement_{iteration}",
            step_type="refinement",
            description=f"Refinement iteration {iteration + 1}",
            prompt=self._build_refinement_prompt(
                query,
                current_response,
                evaluation
            )
        )
        
        try:
            response = await self.call_llm(step.prompt, config)
            self.complete_step(
                step,
                response,
                {"stage": "refinement", "iteration": iteration}
            )
        except Exception as e:
            self.complete_step(step, f"Error: {e}", {"error": True})
        
        return step
    
    async def _evaluate_quality(
        self,
        query: str,
        response: str,
        context: Dict[str, Any],
        config: Dict[str, Any],
        iteration: int
    ) -> PatternStep:
        """Evaluate response quality."""
        step = self.create_step(
            step_id=f"evaluation_{iteration}",
            step_type="evaluation",
            description=f"Quality evaluation (iteration {iteration + 1})",
            prompt=self._build_evaluation_prompt(query, response, context)
        )
        
        try:
            evaluation = await self.call_llm(step.prompt, config)
            self.complete_step(
                step,
                evaluation,
                {"stage": "evaluation", "iteration": iteration}
            )
        except Exception as e:
            self.complete_step(step, f"Error: {e}", {"error": True})
        
        return step
    
    async def _identify_improvements(
        self,
        query: str,
        response: str,
        evaluation: str,
        config: Dict[str, Any]
    ) -> PatternStep:
        """Identify specific improvement areas."""
        step = self.create_step(
            step_id="improvement_id",
            step_type="improvement",
            description="Identify improvements",
            prompt=self._build_improvement_prompt(query, response, evaluation)
        )
        
        try:
            improvements = await self.call_llm(step.prompt, config)
            self.complete_step(
                step,
                improvements,
                {"stage": "improvement_identification"}
            )
        except Exception as e:
            self.complete_step(step, f"Error: {e}", {"error": True})
        
        return step
    
    async def _final_polish(
        self,
        query: str,
        response: str,
        config: Dict[str, Any]
    ) -> PatternStep:
        """Apply final polish."""
        step = self.create_step(
            step_id="final_polish",
            step_type="polish",
            description="Final polish",
            prompt=self._build_polish_prompt(query, response)
        )
        
        try:
            polished = await self.call_llm(step.prompt, config)
            self.complete_step(
                step,
                polished,
                {"stage": "final_polish"}
            )
        except Exception as e:
            self.complete_step(step, f"Error: {e}", {"error": True})
        
        return step
    
    def _build_initial_prompt(
        self,
        query: str,
        context: Dict[str, Any]
    ) -> str:
        """Build prompt for initial generation."""
        context_str = context.get("mcp_data", "")[:400]
        
        return f"""Provide an initial answer to this query.

Query: {query}

Context:
{context_str}...

Instructions:
1. Answer comprehensively
2. Focus on key points
3. This is a first draft
4. Will be refined iteratively

Initial Answer:"""
    
    def _build_refinement_prompt(
        self,
        query: str,
        current_response: str,
        evaluation: str
    ) -> str:
        """Build prompt for refinement."""
        return f"""Refine this response based on evaluation feedback.

Query: {query}

Current Response:
{current_response[:600]}...

Evaluation Feedback:
{evaluation[:400]}...

Refinement Instructions:
1. Address all issues raised
2. Improve weak areas
3. Enhance strengths
4. Increase clarity
5. Add missing details

Refined Response:"""
    
    def _build_evaluation_prompt(
        self,
        query: str,
        response: str,
        context: Dict[str, Any]
    ) -> str:
        """Build prompt for quality evaluation."""
        return f"""Evaluate this response quality on multiple dimensions.

Query: {query}

Response:
{response[:600]}...

Evaluation Dimensions:
1. Completeness (0-10): Answers full query?
2. Accuracy (0-10): Factually correct?
3. Clarity (0-10): Easy to understand?
4. Depth (0-10): Sufficient detail?
5. Relevance (0-10): On-topic?

Provide scores and feedback:
- Completeness: [score] - [comments]
- Accuracy: [score] - [comments]
- Clarity: [score] - [comments]
- Depth: [score] - [comments]
- Relevance: [score] - [comments]
- Overall Quality: [0.0-1.0]

Evaluation:"""
    
    def _build_improvement_prompt(
        self,
        query: str,
        response: str,
        evaluation: str
    ) -> str:
        """Build prompt for improvement identification."""
        return f"""Identify specific improvements needed.

Query: {query}

Current Response:
{response[:500]}...

Evaluation:
{evaluation[:400]}...

Improvement Instructions:
1. List specific weaknesses
2. Prioritize by impact
3. Provide actionable suggestions
4. Be concrete and specific

Format:
1. [Issue]: [suggestion]
2. [Issue]: [suggestion]

Improvements Needed:"""
    
    def _build_polish_prompt(
        self,
        query: str,
        response: str
    ) -> str:
        """Build prompt for final polish."""
        return f"""Apply final polish to this response.

Query: {query}

Response:
{response[:700]}...

Polish Instructions:
1. Perfect grammar/spelling
2. Optimize flow
3. Enhance readability
4. Final quality check
5. Professional presentation

Polished Response:"""
    
    def _parse_quality_score(self, evaluation_text: str) -> float:
        """Parse quality score from evaluation."""
        if not evaluation_text:
            return 0.5
        
        # Look for "Overall Quality: X.XX"
        import re
        match = re.search(r'Overall Quality:\s*([0-9.]+)', evaluation_text, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass
        
        # Heuristic based on scores mentioned
        numbers = re.findall(r'\b([0-9]|10)\b', evaluation_text)
        if numbers:
            avg = sum(int(n) for n in numbers) / len(numbers)
            return min(avg / 10, 1.0)
        
        return 0.6
    
    def _calculate_improvement(self, scores: List[float]) -> str:
        """Calculate improvement trajectory."""
        if len(scores) < 2:
            return "insufficient_data"
        
        first = scores[0]
        last = scores[-1]
        improvement = last - first
        
        if improvement > 0.1:
            return "improving"
        elif improvement < -0.1:
            return "declining"
        else:
            return "stable"
    
    def _calculate_refinement_confidence(self, quality_scores: List[float]) -> float:
        """Calculate confidence based on quality trajectory."""
        if not quality_scores:
            return 0.5
        
        # Final quality is primary factor
        final_quality = quality_scores[-1]
        
        # Improvement trajectory is secondary
        if len(quality_scores) > 1:
            improvement = quality_scores[-1] - quality_scores[0]
            improvement_factor = min(max(improvement + 0.5, 0), 1)
        else:
            improvement_factor = 0.5
        
        confidence = (
            final_quality * 0.7 +
            improvement_factor * 0.3
        )
        
        return min(confidence, 1.0)

