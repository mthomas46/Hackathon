"""Chain-of-Thought (CoT) pattern implementation."""

from typing import Any, Dict, List
from datetime import datetime

from .base import BasePatternEngine, PatternResult, PatternStep


class ChainOfThoughtEngine(BasePatternEngine):
    """
    Chain-of-Thought pattern execution engine.
    
    Breaks down complex problems into step-by-step reasoning.
    
    Process:
    1. Problem decomposition - Break query into sub-problems
    2. Step-by-step reasoning - Solve each sub-problem
    3. Answer synthesis - Combine reasoning into final answer
    
    Reference: https://arxiv.org/abs/2201.11903
    "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models"
    """
    
    def __init__(self):
        super().__init__("chain_of_thought")
    
    async def execute(
        self,
        query: str,
        context: Dict[str, Any],
        config: Dict[str, Any]
    ) -> PatternResult:
        """Execute Chain-of-Thought pattern."""
        start_time = datetime.utcnow()
        steps: List[PatternStep] = []
        
        try:
            # Step 1: Problem Decomposition
            decomp_step = await self._decompose_problem(query, context, config)
            steps.append(decomp_step)
            
            # Extract sub-problems from decomposition
            sub_problems = self._extract_sub_problems(decomp_step.response or "")
            
            # Step 2: Reasoning Steps
            reasoning_steps = await self._execute_reasoning_steps(
                sub_problems,
                query,
                context,
                config
            )
            steps.extend(reasoning_steps)
            
            # Step 3: Synthesize Final Answer
            synthesis_step = await self._synthesize_answer(
                query,
                steps,
                context,
                config
            )
            steps.append(synthesis_step)
            
            # Calculate execution time
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Calculate confidence
            confidence = self.calculate_confidence(steps, config)
            
            return PatternResult(
                pattern_type=self.pattern_type,
                success=True,
                steps=steps,
                final_answer=synthesis_step.response,
                confidence=confidence,
                total_duration_ms=duration_ms,
                metadata={
                    "sub_problems_count": len(sub_problems),
                    "reasoning_steps_count": len(reasoning_steps),
                    "total_steps": len(steps)
                }
            )
        
        except Exception as e:
            self.logger.error(f"Error executing CoT pattern: {e}", exc_info=True)
            
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            return PatternResult(
                pattern_type=self.pattern_type,
                success=False,
                steps=steps,
                total_duration_ms=duration_ms,
                error=str(e)
            )
    
    async def _decompose_problem(
        self,
        query: str,
        context: Dict[str, Any],
        config: Dict[str, Any]
    ) -> PatternStep:
        """Decompose problem into sub-problems."""
        step = self.create_step(
            step_id="decompose",
            step_type="decomposition",
            description="Break down the problem into manageable sub-problems",
            prompt=self._build_decomposition_prompt(query, context)
        )
        
        try:
            response = await self.call_llm(step.prompt, config)
            self.complete_step(step, response, {"stage": "decomposition"})
        except Exception as e:
            self.complete_step(step, f"Error: {e}", {"error": True})
        
        return step
    
    async def _execute_reasoning_steps(
        self,
        sub_problems: List[str],
        original_query: str,
        context: Dict[str, Any],
        config: Dict[str, Any]
    ) -> List[PatternStep]:
        """Execute reasoning for each sub-problem."""
        reasoning_steps = []
        previous_reasoning = []
        
        for i, sub_problem in enumerate(sub_problems, 1):
            step = self.create_step(
                step_id=f"reason_{i}",
                step_type="reasoning",
                description=f"Reasoning step {i}: {sub_problem[:50]}...",
                prompt=self._build_reasoning_prompt(
                    sub_problem,
                    original_query,
                    previous_reasoning,
                    context
                )
            )
            
            try:
                response = await self.call_llm(step.prompt, config)
                self.complete_step(
                    step,
                    response,
                    {
                        "stage": "reasoning",
                        "step_number": i,
                        "sub_problem": sub_problem
                    }
                )
                previous_reasoning.append({
                    "problem": sub_problem,
                    "reasoning": response
                })
            except Exception as e:
                self.complete_step(step, f"Error: {e}", {"error": True})
            
            reasoning_steps.append(step)
        
        return reasoning_steps
    
    async def _synthesize_answer(
        self,
        query: str,
        steps: List[PatternStep],
        context: Dict[str, Any],
        config: Dict[str, Any]
    ) -> PatternStep:
        """Synthesize final answer from reasoning steps."""
        step = self.create_step(
            step_id="synthesize",
            step_type="synthesis",
            description="Combine reasoning steps into final answer",
            prompt=self._build_synthesis_prompt(query, steps, context)
        )
        
        try:
            response = await self.call_llm(step.prompt, config)
            self.complete_step(step, response, {"stage": "synthesis"})
        except Exception as e:
            self.complete_step(step, f"Error: {e}", {"error": True})
        
        return step
    
    def _build_decomposition_prompt(
        self,
        query: str,
        context: Dict[str, Any]
    ) -> str:
        """Build prompt for problem decomposition."""
        context_str = self._format_context(context)
        
        return f"""Given the following query, break it down into 3-5 clear, manageable sub-problems that need to be solved to answer the query.

Query: {query}

{context_str}

Instructions:
1. Identify the key components of the query
2. Break it into logical sub-problems
3. List each sub-problem on a new line, numbered
4. Keep sub-problems specific and actionable
5. Order sub-problems logically (dependencies first)

Sub-problems:"""
    
    def _build_reasoning_prompt(
        self,
        sub_problem: str,
        original_query: str,
        previous_reasoning: List[Dict[str, str]],
        context: Dict[str, Any]
    ) -> str:
        """Build prompt for reasoning step."""
        context_str = self._format_context(context)
        
        # Include previous reasoning if available
        previous_str = ""
        if previous_reasoning:
            previous_str = "\n\nPrevious reasoning:\n"
            for i, pr in enumerate(previous_reasoning, 1):
                previous_str += f"\n{i}. Problem: {pr['problem']}\n"
                previous_str += f"   Reasoning: {pr['reasoning'][:200]}...\n"
        
        return f"""Solve the following sub-problem as part of answering the original query.

Original Query: {original_query}

Current Sub-problem: {sub_problem}

{context_str}{previous_str}

Instructions:
1. Think through this sub-problem step-by-step
2. Show your reasoning process
3. Consider relevant information from context
4. Build on previous reasoning if applicable
5. Provide a clear, specific answer to this sub-problem

Reasoning:"""
    
    def _build_synthesis_prompt(
        self,
        query: str,
        steps: List[PatternStep],
        context: Dict[str, Any]
    ) -> str:
        """Build prompt for answer synthesis."""
        context_str = self._format_context(context)
        
        # Gather all reasoning
        reasoning_str = "\n\nReasoning steps:\n"
        reasoning_steps = [s for s in steps if s.step_type == "reasoning"]
        for i, step in enumerate(reasoning_steps, 1):
            reasoning_str += f"\n{i}. {step.metadata.get('sub_problem', 'Step ' + str(i))}\n"
            reasoning_str += f"   {step.response[:300]}...\n" if step.response else "   No response\n"
        
        return f"""Based on the step-by-step reasoning below, provide a comprehensive final answer to the original query.

Original Query: {query}

{context_str}{reasoning_str}

Instructions:
1. Synthesize insights from all reasoning steps
2. Address the original query directly
3. Provide a clear, coherent answer
4. Mention key insights or caveats
5. Be concise but complete

Final Answer:"""
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context for prompts."""
        if not context:
            return ""
        
        context_parts = []
        
        # Add MCP data if available
        if "mcp_data" in context:
            context_parts.append(f"MCP Context: {context['mcp_data'][:500]}...")
        
        # Add entities if available
        if "entities" in context:
            entities = context["entities"]
            if entities:
                context_parts.append(f"Entities: {', '.join(entities[:10])}")
        
        if context_parts:
            return "\n\nContext:\n" + "\n".join(context_parts)
        
        return ""
    
    def _extract_sub_problems(self, decomposition: str) -> List[str]:
        """Extract sub-problems from decomposition response."""
        if not decomposition:
            return []
        
        # Extract numbered lines
        lines = decomposition.strip().split('\n')
        sub_problems = []
        
        for line in lines:
            line = line.strip()
            # Match numbered patterns like "1.", "1)", "Step 1:", etc.
            if line and (
                line[0].isdigit() or 
                line.lower().startswith('step') or
                line.startswith('-') or
                line.startswith('•')
            ):
                # Remove numbering prefix
                clean_line = line
                for prefix in ['1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.', 
                              '1)', '2)', '3)', '4)', '5)', '6)', '7)', '8)', '9)',
                              'Step 1:', 'Step 2:', 'Step 3:', 'Step 4:', 'Step 5:',
                              '-', '•', '*']:
                    if clean_line.startswith(prefix):
                        clean_line = clean_line[len(prefix):].strip()
                        break
                
                if clean_line:
                    sub_problems.append(clean_line)
        
        # Limit to reasonable number of sub-problems
        return sub_problems[:7]
    
    def calculate_confidence(
        self,
        steps: List[PatternStep],
        config: Dict[str, Any]
    ) -> float:
        """Calculate confidence for CoT pattern."""
        if not steps:
            return 0.0
        
        # Check if all steps completed successfully
        completed = sum(1 for s in steps if s.response and not s.metadata.get("error"))
        completion_rate = completed / len(steps)
        
        # Check reasoning quality (heuristic: longer reasoning = more thorough)
        reasoning_steps = [s for s in steps if s.step_type == "reasoning"]
        if reasoning_steps:
            avg_reasoning_length = sum(
                len(s.response or "") for s in reasoning_steps
            ) / len(reasoning_steps)
            quality_factor = min(avg_reasoning_length / 200, 1.0)
        else:
            quality_factor = 0.5
        
        # Check if synthesis was successful
        synthesis_step = next((s for s in steps if s.step_type == "synthesis"), None)
        synthesis_factor = 1.0 if synthesis_step and synthesis_step.response else 0.5
        
        # Combine factors
        confidence = (
            completion_rate * 0.4 +
            quality_factor * 0.3 +
            synthesis_factor * 0.3
        )
        
        return min(confidence, 1.0)

