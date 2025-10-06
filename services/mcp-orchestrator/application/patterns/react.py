"""ReAct (Reasoning + Acting) pattern implementation."""

from typing import Any, Dict, List, Optional
from datetime import datetime
import asyncio

from .base import BasePatternEngine, PatternResult, PatternStep


class ReActEngine(BasePatternEngine):
    """
    ReAct (Reasoning + Acting) pattern execution engine.
    
    Synergizes reasoning and acting in language models. The model generates
    reasoning traces AND task-specific actions in an interleaved manner.
    
    Process:
    1. Thought - Reason about current state
    2. Action - Take an action (query, search, calculate)
    3. Observation - Observe action result
    4. Repeat until solution found
    
    Reference: "ReAct: Synergizing Reasoning and Acting in Language Models"
    https://arxiv.org/abs/2210.03629
    
    Key Insight: Explicit reasoning traces help guide actions, and
    action results inform subsequent reasoning.
    """
    
    def __init__(self):
        super().__init__("react")
    
    async def execute(
        self,
        query: str,
        context: Dict[str, Any],
        config: Dict[str, Any]
    ) -> PatternResult:
        """Execute ReAct pattern."""
        start_time = datetime.utcnow()
        steps: List[PatternStep] = []
        
        try:
            # Configuration
            max_iterations = config.get("react_max_iterations", 5)
            available_actions = config.get("react_actions", [
                "search", "lookup", "calculate", "finish"
            ])
            
            # Initialize state
            current_state = {
                "query": query,
                "context": context,
                "history": []
            }
            
            # Iterative ReAct loop
            for iteration in range(max_iterations):
                # Step 1: Generate Thought
                thought_step = await self._generate_thought(
                    current_state,
                    config,
                    iteration
                )
                steps.append(thought_step)
                
                # Check if we should finish
                if self._should_finish(thought_step):
                    # Generate final answer
                    final_step = await self._generate_final_answer(
                        current_state,
                        thought_step,
                        config
                    )
                    steps.append(final_step)
                    break
                
                # Step 2: Generate Action
                action_step = await self._generate_action(
                    current_state,
                    thought_step,
                    config,
                    available_actions
                )
                steps.append(action_step)
                
                # Step 3: Execute Action & Get Observation
                observation_step = await self._execute_action(
                    action_step,
                    current_state,
                    config
                )
                steps.append(observation_step)
                
                # Update state with new information
                current_state["history"].append({
                    "thought": thought_step.response,
                    "action": action_step.response,
                    "observation": observation_step.response
                })
            
            # If we didn't finish naturally, force completion
            if not any(s.step_type == "final_answer" for s in steps):
                final_step = await self._generate_final_answer(
                    current_state,
                    steps[-1] if steps else None,
                    config
                )
                steps.append(final_step)
            
            # Calculate execution time
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Get final answer
            final_answer = next(
                (s.response for s in reversed(steps) if s.step_type == "final_answer"),
                "No answer generated"
            )
            
            # Calculate confidence
            confidence = self._calculate_react_confidence(steps)
            
            return PatternResult(
                pattern_type=self.pattern_type,
                success=True,
                steps=steps,
                final_answer=final_answer,
                confidence=confidence,
                total_duration_ms=duration_ms,
                metadata={
                    "iterations": len(current_state["history"]),
                    "actions_taken": [
                        h["action"][:50] for h in current_state["history"]
                    ],
                    "reasoning_quality": self._assess_reasoning_quality(steps)
                }
            )
        
        except Exception as e:
            self.logger.error(f"Error executing ReAct pattern: {e}", exc_info=True)
            
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            return PatternResult(
                pattern_type=self.pattern_type,
                success=False,
                steps=steps,
                total_duration_ms=duration_ms,
                error=str(e)
            )
    
    async def _generate_thought(
        self,
        state: Dict[str, Any],
        config: Dict[str, Any],
        iteration: int
    ) -> PatternStep:
        """Generate reasoning thought."""
        step = self.create_step(
            step_id=f"thought_{iteration}",
            step_type="thought",
            description=f"Reasoning step {iteration + 1}",
            prompt=self._build_thought_prompt(state, iteration)
        )
        
        try:
            response = await self.call_llm(step.prompt, config)
            self.complete_step(
                step,
                response,
                {
                    "stage": "thought",
                    "iteration": iteration
                }
            )
        except Exception as e:
            self.complete_step(step, f"Error: {e}", {"error": True})
        
        return step
    
    async def _generate_action(
        self,
        state: Dict[str, Any],
        thought_step: PatternStep,
        config: Dict[str, Any],
        available_actions: List[str]
    ) -> PatternStep:
        """Generate action based on thought."""
        step = self.create_step(
            step_id=f"action_{thought_step.metadata.get('iteration', 0)}",
            step_type="action",
            description="Action to take",
            prompt=self._build_action_prompt(state, thought_step, available_actions)
        )
        
        try:
            response = await self.call_llm(step.prompt, config)
            self.complete_step(
                step,
                response,
                {
                    "stage": "action",
                    "iteration": thought_step.metadata.get("iteration", 0)
                }
            )
        except Exception as e:
            self.complete_step(step, f"Error: {e}", {"error": True})
        
        return step
    
    async def _execute_action(
        self,
        action_step: PatternStep,
        state: Dict[str, Any],
        config: Dict[str, Any]
    ) -> PatternStep:
        """Execute action and get observation."""
        step = self.create_step(
            step_id=f"observation_{action_step.metadata.get('iteration', 0)}",
            step_type="observation",
            description="Observation from action",
            prompt=""  # Observations come from action execution, not LLM
        )
        
        try:
            # Parse action from response
            action_text = action_step.response or ""
            action_type = self._parse_action_type(action_text)
            action_input = self._parse_action_input(action_text)
            
            # Execute action (simulated - in real system would call actual tools)
            observation = await self._simulate_action_execution(
                action_type,
                action_input,
                state,
                config
            )
            
            self.complete_step(
                step,
                observation,
                {
                    "stage": "observation",
                    "iteration": action_step.metadata.get("iteration", 0),
                    "action_type": action_type,
                    "action_input": action_input
                }
            )
        except Exception as e:
            self.complete_step(step, f"Error: {e}", {"error": True})
        
        return step
    
    async def _generate_final_answer(
        self,
        state: Dict[str, Any],
        last_step: Optional[PatternStep],
        config: Dict[str, Any]
    ) -> PatternStep:
        """Generate final answer."""
        step = self.create_step(
            step_id="final_answer",
            step_type="final_answer",
            description="Final answer synthesis",
            prompt=self._build_final_answer_prompt(state)
        )
        
        try:
            response = await self.call_llm(step.prompt, config)
            self.complete_step(
                step,
                response,
                {
                    "stage": "final_answer",
                    "iterations_used": len(state["history"])
                }
            )
        except Exception as e:
            self.complete_step(step, f"Error: {e}", {"error": True})
        
        return step
    
    def _build_thought_prompt(
        self,
        state: Dict[str, Any],
        iteration: int
    ) -> str:
        """Build prompt for thought generation."""
        query = state["query"]
        context = state.get("context", {})
        history = state.get("history", [])
        
        context_str = self._format_context(context)
        
        # Format history
        history_str = ""
        if history:
            history_str = "\n\nPrevious Steps:\n"
            for i, h in enumerate(history, 1):
                history_str += f"\nIteration {i}:\n"
                history_str += f"Thought: {h['thought'][:150]}...\n"
                history_str += f"Action: {h['action'][:100]}...\n"
                history_str += f"Observation: {h['observation'][:100]}...\n"
        
        return f"""You are solving a problem using reasoning and actions.

Question: {query}

{context_str}{history_str}

Current Iteration: {iteration + 1}

Think about what you know so far and what you need to do next.

Instructions:
1. Analyze the current situation
2. Reason about what information you have
3. Identify what's missing
4. Decide on next step
5. Be concise but thorough

Thought:"""
    
    def _build_action_prompt(
        self,
        state: Dict[str, Any],
        thought_step: PatternStep,
        available_actions: List[str]
    ) -> str:
        """Build prompt for action generation."""
        thought = thought_step.response or ""
        
        actions_str = "\n".join([f"- {action}" for action in available_actions])
        
        return f"""Based on your reasoning, choose an action to take.

Your Thought:
{thought[:300]}...

Available Actions:
{actions_str}

Instructions:
1. Choose the most appropriate action
2. Specify action parameters/input
3. Format: "Action: [action_name]
   Input: [action_input]"
4. Be specific about what you're looking for

Action:"""
    
    def _build_final_answer_prompt(self, state: Dict[str, Any]) -> str:
        """Build prompt for final answer."""
        query = state["query"]
        history = state.get("history", [])
        context = state.get("context", {})
        
        context_str = self._format_context(context)
        
        # Summarize trajectory
        trajectory_str = ""
        if history:
            trajectory_str = "\n\nReasoning Trajectory:\n"
            for i, h in enumerate(history, 1):
                trajectory_str += f"\n{i}. {h['thought'][:100]}...\n"
                trajectory_str += f"   Action: {h['action'][:50]}...\n"
                trajectory_str += f"   Result: {h['observation'][:50]}...\n"
        
        return f"""Provide a final answer to the question based on your reasoning and actions.

Question: {query}

{context_str}{trajectory_str}

Instructions:
1. Answer the question directly
2. Use information from your observations
3. Be clear and concise
4. Support your answer with reasoning
5. Acknowledge any limitations

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
    
    def _should_finish(self, thought_step: PatternStep) -> bool:
        """Determine if we should finish based on thought."""
        if not thought_step.response:
            return False
        
        thought = thought_step.response.lower()
        
        # Check for finish indicators
        finish_indicators = [
            "i have enough information",
            "i can now answer",
            "ready to provide answer",
            "sufficient information",
            "final answer",
            "conclude that"
        ]
        
        return any(indicator in thought for indicator in finish_indicators)
    
    def _parse_action_type(self, action_text: str) -> str:
        """Parse action type from action text."""
        if not action_text:
            return "unknown"
        
        action_lower = action_text.lower()
        
        # Simple pattern matching
        if "search" in action_lower:
            return "search"
        elif "lookup" in action_lower or "find" in action_lower:
            return "lookup"
        elif "calculate" in action_lower or "compute" in action_lower:
            return "calculate"
        elif "finish" in action_lower or "answer" in action_lower:
            return "finish"
        else:
            return "unknown"
    
    def _parse_action_input(self, action_text: str) -> str:
        """Parse action input from action text."""
        if not action_text:
            return ""
        
        # Look for "Input:" or similar
        for pattern in ["input:", "query:", "for:", "about:"]:
            if pattern in action_text.lower():
                parts = action_text.lower().split(pattern, 1)
                if len(parts) > 1:
                    return parts[1].strip()[:200]
        
        # Fallback: return first sentence
        sentences = action_text.split('.')
        if sentences:
            return sentences[0].strip()[:200]
        
        return action_text[:200]
    
    async def _simulate_action_execution(
        self,
        action_type: str,
        action_input: str,
        state: Dict[str, Any],
        config: Dict[str, Any]
    ) -> str:
        """Simulate action execution (in real system, would call actual tools)."""
        # In a real implementation, this would:
        # - Call search APIs for "search"
        # - Query knowledge bases for "lookup"
        # - Execute calculations for "calculate"
        # - Interface with external tools
        
        # For now, simulate with LLM
        simulation_prompt = f"""Simulate the result of this action:

Action Type: {action_type}
Action Input: {action_input}

Question Context: {state['query']}

Provide a realistic observation/result that this action would return.
Be specific and informative.

Observation:"""
        
        try:
            observation = await self.call_llm(simulation_prompt, config)
            return observation
        except:
            return f"Simulated result for {action_type} on '{action_input}'"
    
    def _assess_reasoning_quality(self, steps: List[PatternStep]) -> float:
        """Assess quality of reasoning trajectory."""
        if not steps:
            return 0.0
        
        # Count different step types
        thoughts = [s for s in steps if s.step_type == "thought"]
        actions = [s for s in steps if s.step_type == "action"]
        observations = [s for s in steps if s.step_type == "observation"]
        
        # Quality indicators
        has_multiple_iterations = len(thoughts) > 1
        balanced_steps = (
            len(thoughts) > 0 and 
            len(actions) > 0 and 
            len(observations) > 0
        )
        reached_conclusion = any(s.step_type == "final_answer" for s in steps)
        
        quality = 0.0
        if has_multiple_iterations:
            quality += 0.3
        if balanced_steps:
            quality += 0.4
        if reached_conclusion:
            quality += 0.3
        
        return min(quality, 1.0)
    
    def _calculate_react_confidence(self, steps: List[PatternStep]) -> float:
        """Calculate confidence for ReAct pattern."""
        if not steps:
            return 0.0
        
        # Factors:
        # 1. Completed trajectory (thought→action→observation cycle)
        thoughts = [s for s in steps if s.step_type == "thought" and s.response]
        actions = [s for s in steps if s.step_type == "action" and s.response]
        observations = [s for s in steps if s.step_type == "observation" and s.response]
        
        cycle_completeness = min(len(thoughts), len(actions), len(observations)) / max(len(thoughts), 1)
        
        # 2. Final answer present
        has_final_answer = any(s.step_type == "final_answer" for s in steps)
        final_answer_factor = 1.0 if has_final_answer else 0.5
        
        # 3. Reasoning quality
        reasoning_quality = self._assess_reasoning_quality(steps)
        
        # Combine
        confidence = (
            cycle_completeness * 0.3 +
            final_answer_factor * 0.3 +
            reasoning_quality * 0.4
        )
        
        return min(confidence, 1.0)

