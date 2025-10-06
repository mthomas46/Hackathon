"""Self-Critique pattern implementation."""

from typing import Any, Dict, List, Optional
from datetime import datetime

from .base import BasePatternEngine, PatternResult, PatternStep


class SelfCritiqueEngine(BasePatternEngine):
    """
    Self-Critique pattern execution engine.
    
    Generates an initial answer, then critiques it, and iteratively
    refines based on self-identified issues. The model acts as both
    generator and critic.
    
    Process:
    1. Generate initial answer
    2. Critique the answer (identify flaws, issues, gaps)
    3. Refine answer based on critique
    4. Repeat until satisfactory or max iterations
    
    Advantages:
    - Self-improving through iteration
    - Catches own mistakes
    - Higher quality final answers
    - No external feedback needed
    """
    
    def __init__(self):
        super().__init__("self_critique")
    
    async def execute(
        self,
        query: str,
        context: Dict[str, Any],
        config: Dict[str, Any]
    ) -> PatternResult:
        """Execute Self-Critique pattern."""
        start_time = datetime.utcnow()
        steps: List[PatternStep] = []
        
        try:
            # Configuration
            max_iterations = config.get("critique_max_iterations", 3)
            min_quality_score = config.get("critique_min_quality", 0.8)
            
            # Step 1: Generate initial answer
            generation_step = await self._generate_initial_answer(
                query,
                context,
                config
            )
            steps.append(generation_step)
            
            current_answer = generation_step.response
            
            # Iterative critique and refinement
            for iteration in range(max_iterations):
                # Step 2: Critique current answer
                critique_step = await self._critique_answer(
                    query,
                    current_answer,
                    context,
                    config,
                    iteration
                )
                steps.append(critique_step)
                
                # Assess critique quality
                quality_score = self._assess_quality(critique_step)
                
                # If quality is sufficient, stop
                if quality_score >= min_quality_score:
                    self.logger.info(f"Quality threshold met: {quality_score:.2f}")
                    break
                
                # Step 3: Refine answer based on critique
                refinement_step = await self._refine_answer(
                    query,
                    current_answer,
                    critique_step,
                    context,
                    config,
                    iteration
                )
                steps.append(refinement_step)
                
                # Update current answer
                current_answer = refinement_step.response or current_answer
            
            # Step 4: Final polish
            final_step = await self._generate_final_answer(
                query,
                current_answer,
                steps,
                context,
                config
            )
            steps.append(final_step)
            
            # Calculate execution time
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Calculate confidence based on iterations and quality
            confidence = self._calculate_critique_confidence(steps)
            
            return PatternResult(
                pattern_type=self.pattern_type,
                success=True,
                steps=steps,
                final_answer=final_step.response,
                confidence=confidence,
                total_duration_ms=duration_ms,
                metadata={
                    "iterations": len([s for s in steps if s.step_type == "critique"]),
                    "refinements": len([s for s in steps if s.step_type == "refinement"]),
                    "improvement_trajectory": self._get_improvement_trajectory(steps)
                }
            )
        
        except Exception as e:
            self.logger.error(f"Error executing Self-Critique: {e}", exc_info=True)
            
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            return PatternResult(
                pattern_type=self.pattern_type,
                success=False,
                steps=steps,
                total_duration_ms=duration_ms,
                error=str(e)
            )
    
    async def _generate_initial_answer(
        self,
        query: str,
        context: Dict[str, Any],
        config: Dict[str, Any]
    ) -> PatternStep:
        """Generate initial answer."""
        step = self.create_step(
            step_id="initial_generation",
            step_type="generation",
            description="Generate initial answer",
            prompt=self._build_generation_prompt(query, context)
        )
        
        try:
            response = await self.call_llm(step.prompt, config)
            self.complete_step(
                step,
                response,
                {
                    "stage": "initial_generation",
                    "iteration": 0
                }
            )
        except Exception as e:
            self.complete_step(step, f"Error: {e}", {"error": True})
        
        return step
    
    async def _critique_answer(
        self,
        query: str,
        answer: str,
        context: Dict[str, Any],
        config: Dict[str, Any],
        iteration: int
    ) -> PatternStep:
        """Critique the current answer."""
        step = self.create_step(
            step_id=f"critique_{iteration}",
            step_type="critique",
            description=f"Critique answer (iteration {iteration + 1})",
            prompt=self._build_critique_prompt(query, answer, context)
        )
        
        try:
            response = await self.call_llm(step.prompt, config)
            
            # Assess quality from critique
            quality_score = self._assess_quality_from_text(response)
            
            self.complete_step(
                step,
                response,
                {
                    "stage": "critique",
                    "iteration": iteration,
                    "quality_score": quality_score
                }
            )
        except Exception as e:
            self.complete_step(step, f"Error: {e}", {"error": True})
        
        return step
    
    async def _refine_answer(
        self,
        query: str,
        current_answer: str,
        critique_step: PatternStep,
        context: Dict[str, Any],
        config: Dict[str, Any],
        iteration: int
    ) -> PatternStep:
        """Refine answer based on critique."""
        step = self.create_step(
            step_id=f"refinement_{iteration}",
            step_type="refinement",
            description=f"Refine answer (iteration {iteration + 1})",
            prompt=self._build_refinement_prompt(
                query,
                current_answer,
                critique_step.response or "",
                context
            )
        )
        
        try:
            response = await self.call_llm(step.prompt, config)
            self.complete_step(
                step,
                response,
                {
                    "stage": "refinement",
                    "iteration": iteration
                }
            )
        except Exception as e:
            self.complete_step(step, f"Error: {e}", {"error": True})
        
        return step
    
    async def _generate_final_answer(
        self,
        query: str,
        current_answer: str,
        steps: List[PatternStep],
        context: Dict[str, Any],
        config: Dict[str, Any]
    ) -> PatternStep:
        """Generate final polished answer."""
        step = self.create_step(
            step_id="final_answer",
            step_type="final_answer",
            description="Final polished answer",
            prompt=self._build_final_prompt(query, current_answer, context)
        )
        
        try:
            response = await self.call_llm(step.prompt, config)
            self.complete_step(
                step,
                response,
                {
                    "stage": "final_answer",
                    "total_iterations": len([s for s in steps if s.step_type == "critique"])
                }
            )
        except Exception as e:
            self.complete_step(step, f"Error: {e}", {"error": True})
        
        return step
    
    def _build_generation_prompt(
        self,
        query: str,
        context: Dict[str, Any]
    ) -> str:
        """Build prompt for initial generation."""
        context_str = self._format_context(context)
        
        return f"""Provide an initial answer to this query.

Query: {query}

{context_str}

Instructions:
1. Answer the query directly
2. Be thorough but not overly long
3. Use clear reasoning
4. This is a first draft that will be refined
5. Focus on accuracy and completeness

Initial Answer:"""
    
    def _build_critique_prompt(
        self,
        query: str,
        answer: str,
        context: Dict[str, Any]
    ) -> str:
        """Build prompt for critiquing answer."""
        context_str = self._format_context(context)
        
        return f"""Critique the following answer to identify flaws, gaps, and areas for improvement.

Original Query: {query}

{context_str}

Current Answer:
{answer[:800]}...

Critique Instructions:
1. Identify factual errors or inaccuracies
2. Note missing information or gaps
3. Point out unclear or confusing parts
4. Suggest improvements
5. Rate overall quality (1-10)
6. Be constructively critical

Critique:"""
    
    def _build_refinement_prompt(
        self,
        query: str,
        current_answer: str,
        critique: str,
        context: Dict[str, Any]
    ) -> str:
        """Build prompt for refining answer."""
        context_str = self._format_context(context)
        
        return f"""Improve the answer based on the critique provided.

Original Query: {query}

{context_str}

Current Answer:
{current_answer[:600]}...

Critique:
{critique[:600]}...

Refinement Instructions:
1. Address all issues raised in critique
2. Fix factual errors
3. Fill in gaps
4. Improve clarity
5. Keep what was good
6. Make it better overall

Refined Answer:"""
    
    def _build_final_prompt(
        self,
        query: str,
        current_answer: str,
        context: Dict[str, Any]
    ) -> str:
        """Build prompt for final answer."""
        context_str = self._format_context(context)
        
        return f"""Provide the final, polished version of this answer.

Original Query: {query}

{context_str}

Current Answer (refined):
{current_answer[:800]}...

Final Polish Instructions:
1. Ensure clarity and readability
2. Verify accuracy
3. Make sure it fully answers the query
4. Remove any redundancy
5. Professional tone
6. Concise but complete

Final Answer:"""
    
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
    
    def _assess_quality(self, critique_step: PatternStep) -> float:
        """Assess quality from critique step."""
        if not critique_step or not critique_step.response:
            return 0.5
        
        return critique_step.metadata.get("quality_score", 0.5)
    
    def _assess_quality_from_text(self, critique_text: str) -> float:
        """Extract quality score from critique text."""
        if not critique_text:
            return 0.5
        
        text_lower = critique_text.lower()
        
        # Look for explicit ratings
        if "10/10" in text_lower or "10 out of 10" in text_lower:
            return 1.0
        elif "9/10" in text_lower:
            return 0.9
        elif "8/10" in text_lower:
            return 0.8
        elif "7/10" in text_lower:
            return 0.7
        elif "6/10" in text_lower:
            return 0.6
        
        # Look for quality indicators
        positive_indicators = [
            "excellent", "great", "very good", "well done",
            "thorough", "comprehensive", "accurate"
        ]
        negative_indicators = [
            "poor", "weak", "incomplete", "missing",
            "unclear", "confusing", "incorrect", "error"
        ]
        
        positive_count = sum(1 for ind in positive_indicators if ind in text_lower)
        negative_count = sum(1 for ind in negative_indicators if ind in text_lower)
        
        # Heuristic scoring
        if positive_count > negative_count * 2:
            return 0.8
        elif negative_count > positive_count * 2:
            return 0.4
        else:
            return 0.6
    
    def _get_improvement_trajectory(self, steps: List[PatternStep]) -> List[float]:
        """Get quality improvement trajectory."""
        trajectory = []
        
        for step in steps:
            if step.step_type == "critique":
                quality = step.metadata.get("quality_score", 0.5)
                trajectory.append(quality)
        
        return trajectory
    
    def _calculate_critique_confidence(self, steps: List[PatternStep]) -> float:
        """Calculate confidence based on critique iterations."""
        if not steps:
            return 0.0
        
        # Factors:
        # 1. Final quality score
        critique_steps = [s for s in steps if s.step_type == "critique"]
        if critique_steps:
            final_quality = critique_steps[-1].metadata.get("quality_score", 0.5)
        else:
            final_quality = 0.5
        
        # 2. Improvement trajectory (did quality improve?)
        trajectory = self._get_improvement_trajectory(steps)
        if len(trajectory) >= 2:
            improvement = trajectory[-1] - trajectory[0]
            improvement_factor = min(max(improvement + 0.5, 0), 1)  # Normalize
        else:
            improvement_factor = 0.5
        
        # 3. Number of refinements (more = more thorough)
        refinements = len([s for s in steps if s.step_type == "refinement"])
        refinement_factor = min(refinements / 3, 1.0)
        
        # Combine
        confidence = (
            final_quality * 0.5 +
            improvement_factor * 0.3 +
            refinement_factor * 0.2
        )
        
        return min(confidence, 1.0)

