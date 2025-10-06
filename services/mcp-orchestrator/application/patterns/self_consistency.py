"""Self-Consistency pattern implementation."""

from typing import Any, Dict, List, Optional
from datetime import datetime
import asyncio
from collections import Counter

from .base import BasePatternEngine, PatternResult, PatternStep


class SelfConsistencyEngine(BasePatternEngine):
    """
    Self-Consistency pattern execution engine.
    
    Generates multiple diverse reasoning paths and selects the most
    consistent answer through majority voting. Improves accuracy by
    marginalizing over multiple reasoning paths.
    
    Process:
    1. Generate N diverse reasoning paths (using temperature sampling)
    2. Extract final answers from each path
    3. Count answer frequencies (majority voting)
    4. Select most consistent answer
    5. Verify consistency across paths
    
    Reference: "Self-Consistency Improves Chain of Thought Reasoning in Language Models"
    https://arxiv.org/abs/2203.11171
    
    Key Insight: Diverse reasoning paths that arrive at the same answer
    indicate higher confidence in that answer.
    """
    
    def __init__(self):
        super().__init__("self_consistency")
    
    async def execute(
        self,
        query: str,
        context: Dict[str, Any],
        config: Dict[str, Any]
    ) -> PatternResult:
        """Execute Self-Consistency pattern."""
        start_time = datetime.utcnow()
        steps: List[PatternStep] = []
        
        try:
            # Configuration
            num_paths = config.get("consistency_paths", 5)
            temperature = config.get("temperature", 0.8)  # Higher for diversity
            
            # Step 1: Generate diverse reasoning paths in parallel
            reasoning_steps = await self._generate_diverse_paths(
                query,
                context,
                config,
                num_paths,
                temperature
            )
            steps.extend(reasoning_steps)
            
            # Step 2: Extract answers from each path
            extraction_step = await self._extract_answers(
                reasoning_steps,
                query,
                context,
                config
            )
            steps.append(extraction_step)
            
            # Step 3: Analyze consistency and vote
            consistency_step = await self._analyze_consistency(
                reasoning_steps,
                extraction_step,
                query,
                context,
                config
            )
            steps.append(consistency_step)
            
            # Step 4: Select most consistent answer
            answer_counts = self._count_answers(reasoning_steps)
            most_common_answer, frequency = self._get_most_common(answer_counts)
            
            # Step 5: Calculate consistency score
            consistency_score = frequency / len(reasoning_steps) if reasoning_steps else 0.0
            
            # Step 6: Generate final explanation
            explanation_step = await self._generate_explanation(
                query,
                most_common_answer,
                consistency_score,
                reasoning_steps,
                context,
                config
            )
            steps.append(explanation_step)
            
            # Calculate execution time
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            return PatternResult(
                pattern_type=self.pattern_type,
                success=True,
                steps=steps,
                final_answer=explanation_step.response,
                confidence=consistency_score,
                total_duration_ms=duration_ms,
                metadata={
                    "num_paths": num_paths,
                    "consistency_score": consistency_score,
                    "answer_distribution": dict(answer_counts),
                    "most_common_frequency": frequency,
                    "reasoning_diversity": self._calculate_diversity(reasoning_steps)
                }
            )
        
        except Exception as e:
            self.logger.error(f"Error executing Self-Consistency: {e}", exc_info=True)
            
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            return PatternResult(
                pattern_type=self.pattern_type,
                success=False,
                steps=steps,
                total_duration_ms=duration_ms,
                error=str(e)
            )
    
    async def _generate_diverse_paths(
        self,
        query: str,
        context: Dict[str, Any],
        config: Dict[str, Any],
        num_paths: int,
        temperature: float
    ) -> List[PatternStep]:
        """Generate diverse reasoning paths."""
        # Create config with higher temperature for diversity
        diverse_config = config.copy()
        diverse_config["temperature"] = temperature
        
        # Create coroutines for parallel execution
        coroutines = [
            self._generate_single_path(i, query, context, diverse_config)
            for i in range(num_paths)
        ]
        
        # Execute all in parallel
        reasoning_steps = await asyncio.gather(*coroutines)
        
        return list(reasoning_steps)
    
    async def _generate_single_path(
        self,
        path_id: int,
        query: str,
        context: Dict[str, Any],
        config: Dict[str, Any]
    ) -> PatternStep:
        """Generate a single reasoning path."""
        step = self.create_step(
            step_id=f"path_{path_id}",
            step_type="reasoning_path",
            description=f"Reasoning path {path_id + 1}",
            prompt=self._build_reasoning_prompt(query, context)
        )
        
        try:
            response = await self.call_llm(step.prompt, config)
            
            # Extract answer from response
            answer = self._extract_answer_from_text(response)
            
            self.complete_step(
                step,
                response,
                {
                    "stage": "reasoning_path",
                    "path_id": path_id,
                    "extracted_answer": answer
                }
            )
        except Exception as e:
            self.complete_step(step, f"Error: {e}", {"error": True})
        
        return step
    
    async def _extract_answers(
        self,
        reasoning_steps: List[PatternStep],
        query: str,
        context: Dict[str, Any],
        config: Dict[str, Any]
    ) -> PatternStep:
        """Extract and normalize answers from reasoning paths."""
        step = self.create_step(
            step_id="extract_answers",
            step_type="answer_extraction",
            description="Extract final answers from reasoning paths",
            prompt=self._build_extraction_prompt(reasoning_steps, query, context)
        )
        
        try:
            response = await self.call_llm(step.prompt, config)
            
            # Update extracted answers in metadata
            answers = self._parse_extracted_answers(response, len(reasoning_steps))
            
            self.complete_step(
                step,
                response,
                {
                    "stage": "answer_extraction",
                    "extracted_answers": answers,
                    "unique_answers": len(set(answers))
                }
            )
        except Exception as e:
            self.complete_step(step, f"Error: {e}", {"error": True})
        
        return step
    
    async def _analyze_consistency(
        self,
        reasoning_steps: List[PatternStep],
        extraction_step: PatternStep,
        query: str,
        context: Dict[str, Any],
        config: Dict[str, Any]
    ) -> PatternStep:
        """Analyze consistency across paths."""
        step = self.create_step(
            step_id="analyze_consistency",
            step_type="consistency_analysis",
            description="Analyze consistency and vote for best answer",
            prompt=self._build_consistency_prompt(
                reasoning_steps,
                extraction_step,
                query,
                context
            )
        )
        
        try:
            response = await self.call_llm(step.prompt, config)
            
            # Calculate statistics
            answer_counts = self._count_answers(reasoning_steps)
            
            self.complete_step(
                step,
                response,
                {
                    "stage": "consistency_analysis",
                    "answer_distribution": dict(answer_counts),
                    "total_paths": len(reasoning_steps)
                }
            )
        except Exception as e:
            self.complete_step(step, f"Error: {e}", {"error": True})
        
        return step
    
    async def _generate_explanation(
        self,
        query: str,
        selected_answer: str,
        consistency_score: float,
        reasoning_steps: List[PatternStep],
        context: Dict[str, Any],
        config: Dict[str, Any]
    ) -> PatternStep:
        """Generate final explanation with consistency information."""
        step = self.create_step(
            step_id="explain",
            step_type="explanation",
            description="Generate final answer with consistency explanation",
            prompt=self._build_explanation_prompt(
                query,
                selected_answer,
                consistency_score,
                reasoning_steps,
                context
            )
        )
        
        try:
            response = await self.call_llm(step.prompt, config)
            self.complete_step(
                step,
                response,
                {
                    "stage": "explanation",
                    "selected_answer": selected_answer,
                    "consistency_score": consistency_score
                }
            )
        except Exception as e:
            self.complete_step(step, f"Error: {e}", {"error": True})
        
        return step
    
    def _build_reasoning_prompt(
        self,
        query: str,
        context: Dict[str, Any]
    ) -> str:
        """Build prompt for reasoning path generation."""
        context_str = self._format_context(context)
        
        return f"""Think through this query step-by-step and provide your reasoning.

Query: {query}

{context_str}

Instructions:
1. Break down the problem
2. Reason through each step
3. State your final answer clearly
4. Be specific and concrete

Think step-by-step:"""
    
    def _build_extraction_prompt(
        self,
        reasoning_steps: List[PatternStep],
        query: str,
        context: Dict[str, Any]
    ) -> str:
        """Build prompt for answer extraction."""
        context_str = self._format_context(context)
        
        # Sample reasoning paths
        paths_str = "\n\n".join([
            f"Path {i+1}:\n{step.response[:300]}..."
            if step.response else f"Path {i+1}: No response"
            for i, step in enumerate(reasoning_steps[:5])
        ])
        
        return f"""Extract the final answer from each reasoning path.

Original Query: {query}

{context_str}

Reasoning Paths:
{paths_str}

Instructions:
1. For each path, identify the final answer
2. Normalize answers (make them comparable)
3. Format: "Path X: [answer]"
4. Be consistent in formatting

Extracted Answers:"""
    
    def _build_consistency_prompt(
        self,
        reasoning_steps: List[PatternStep],
        extraction_step: PatternStep,
        query: str,
        context: Dict[str, Any]
    ) -> str:
        """Build prompt for consistency analysis."""
        context_str = self._format_context(context)
        
        # Get answer counts
        answer_counts = self._count_answers(reasoning_steps)
        distribution_str = "\n".join([
            f"  {answer}: {count} paths ({count/len(reasoning_steps)*100:.0f}%)"
            for answer, count in answer_counts.most_common()
        ])
        
        return f"""Analyze the consistency of answers across multiple reasoning paths.

Original Query: {query}

{context_str}

Answer Distribution:
{distribution_str}

Total Paths: {len(reasoning_steps)}

Instructions:
1. Identify the most consistent answer
2. Assess the level of agreement
3. Note any significant disagreements
4. Explain why certain paths differ
5. Recommend the best answer

Consistency Analysis:"""
    
    def _build_explanation_prompt(
        self,
        query: str,
        selected_answer: str,
        consistency_score: float,
        reasoning_steps: List[PatternStep],
        context: Dict[str, Any]
    ) -> str:
        """Build prompt for final explanation."""
        context_str = self._format_context(context)
        
        # Get sample supporting reasoning
        supporting_paths = [
            step.response[:200]
            for step in reasoning_steps
            if step.metadata.get("extracted_answer") == selected_answer
        ][:2]
        
        support_str = "\n\n".join([
            f"Supporting Path {i+1}:\n{path}..."
            for i, path in enumerate(supporting_paths)
        ])
        
        return f"""Provide a final answer with consistency information.

Original Query: {query}

{context_str}

Selected Answer: {selected_answer}
Consistency Score: {consistency_score:.1%} ({int(consistency_score * len(reasoning_steps))}/{len(reasoning_steps)} paths)

Sample Supporting Reasoning:
{support_str}

Instructions:
1. State the answer clearly
2. Mention the consistency level
3. Explain why this answer is reliable
4. Note any caveats if consistency is low
5. Be confident if consistency is high

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
    
    def _extract_answer_from_text(self, text: str) -> str:
        """Extract answer from reasoning text."""
        if not text:
            return "no_answer"
        
        # Look for common answer patterns
        text_lower = text.lower()
        
        # Try to find explicit answer statements
        for pattern in ["answer:", "therefore", "conclusion:", "final answer:", "result:"]:
            if pattern in text_lower:
                # Get text after pattern
                parts = text_lower.split(pattern, 1)
                if len(parts) > 1:
                    # Take first sentence
                    answer_part = parts[1].strip()
                    sentences = answer_part.split('.')
                    if sentences:
                        return sentences[0].strip()[:100]
        
        # Fallback: last sentence
        sentences = text.strip().split('.')
        if sentences:
            return sentences[-1].strip()[:100]
        
        return text[:100]
    
    def _count_answers(self, reasoning_steps: List[PatternStep]) -> Counter:
        """Count answer frequencies."""
        answers = [
            step.metadata.get("extracted_answer", "unknown")
            for step in reasoning_steps
            if step.step_type == "reasoning_path" and step.response
        ]
        
        # Normalize answers (lowercase, strip)
        normalized = [a.lower().strip() for a in answers]
        
        return Counter(normalized)
    
    def _get_most_common(self, answer_counts: Counter) -> tuple[str, int]:
        """Get most common answer and its frequency."""
        if not answer_counts:
            return "no_answer", 0
        
        most_common = answer_counts.most_common(1)
        if most_common:
            return most_common[0]
        
        return "no_answer", 0
    
    def _parse_extracted_answers(
        self,
        extraction_text: str,
        num_paths: int
    ) -> List[str]:
        """Parse extracted answers from text."""
        if not extraction_text:
            return ["unknown"] * num_paths
        
        answers = []
        lines = extraction_text.strip().split('\n')
        
        for line in lines:
            if ':' in line:
                # Try to extract answer after colon
                parts = line.split(':', 1)
                if len(parts) > 1:
                    answer = parts[1].strip()
                    answers.append(answer[:100])
        
        # Fill missing answers
        while len(answers) < num_paths:
            answers.append("unknown")
        
        return answers[:num_paths]
    
    def _calculate_diversity(self, reasoning_steps: List[PatternStep]) -> float:
        """Calculate diversity of reasoning paths."""
        if not reasoning_steps:
            return 0.0
        
        # Count unique answer beginnings
        starts = set()
        for step in reasoning_steps:
            if step.response:
                starts.add(step.response[:50].lower())
        
        diversity = len(starts) / len(reasoning_steps)
        return diversity

