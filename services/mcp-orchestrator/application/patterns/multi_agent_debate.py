"""Multi-Agent Debate pattern implementation."""

from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
import asyncio

from .base import BasePatternEngine, PatternResult, PatternStep


class MultiAgentDebateEngine(BasePatternEngine):
    """
    Multi-Agent Debate pattern execution engine.
    
    Multiple LLM agents debate a question, each taking different
    positions or perspectives. Through iterative argumentation,
    they converge toward a more robust answer.
    
    Process:
    1. Initialize multiple agents with different positions
    2. Each agent presents their argument
    3. Agents critique each other's arguments
    4. Agents refine their positions based on critiques
    5. Repeat for multiple debate rounds
    6. Judge/moderator synthesizes final answer
    
    Reference: "Improving Factuality and Reasoning via Multi-Agent Debate"
    https://arxiv.org/abs/2305.14325
    
    Key Innovation: Adversarial collaboration - agents challenge
    each other, leading to more thorough reasoning and better answers.
    """
    
    def __init__(self):
        super().__init__("multi_agent_debate")
    
    async def execute(
        self,
        query: str,
        context: Dict[str, Any],
        config: Dict[str, Any]
    ) -> PatternResult:
        """Execute Multi-Agent Debate pattern."""
        start_time = datetime.utcnow()
        steps: List[PatternStep] = []
        
        try:
            # Configuration
            num_agents = config.get("debate_num_agents", 3)
            num_rounds = config.get("debate_num_rounds", 2)
            agent_positions = config.get("debate_agent_positions", None)
            
            # Step 1: Initialize agents with positions
            agent_states = await self._initialize_agents(
                query,
                context,
                config,
                num_agents,
                agent_positions
            )
            
            # Add initialization steps
            for agent_id, state in agent_states.items():
                steps.append(state["init_step"])
            
            # Debate rounds
            for round_num in range(num_rounds):
                self.logger.info(f"Starting debate round {round_num + 1}")
                
                # Step 2: Each agent presents argument
                argument_steps = await self._present_arguments(
                    agent_states,
                    query,
                    context,
                    config,
                    round_num
                )
                steps.extend(argument_steps)
                
                # Update agent states with arguments
                for i, agent_id in enumerate(agent_states.keys()):
                    agent_states[agent_id]["current_argument"] = argument_steps[i].response
                
                # Step 3: Each agent critiques others
                critique_steps = await self._cross_critique(
                    agent_states,
                    query,
                    config,
                    round_num
                )
                steps.extend(critique_steps)
                
                # Update agent states with critiques received
                critique_idx = 0
                for agent_id in agent_states.keys():
                    agent_states[agent_id]["critiques_received"] = []
                    for other_id in agent_states.keys():
                        if other_id != agent_id:
                            agent_states[agent_id]["critiques_received"].append(
                                critique_steps[critique_idx].response
                            )
                            critique_idx += 1
            
            # Step 4: Judge/moderator synthesizes final answer
            synthesis_step = await self._synthesize_final_answer(
                agent_states,
                query,
                context,
                config,
                steps
            )
            steps.append(synthesis_step)
            
            # Calculate execution time
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Calculate confidence
            confidence = self._calculate_debate_confidence(agent_states, steps)
            
            return PatternResult(
                pattern_type=self.pattern_type,
                success=True,
                steps=steps,
                final_answer=synthesis_step.response,
                confidence=confidence,
                total_duration_ms=duration_ms,
                metadata={
                    "num_agents": num_agents,
                    "num_rounds": num_rounds,
                    "agent_positions": [
                        agent_states[aid]["position"] for aid in agent_states
                    ],
                    "total_arguments": len([s for s in steps if s.step_type == "argument"]),
                    "total_critiques": len([s for s in steps if s.step_type == "critique"])
                }
            )
        
        except Exception as e:
            self.logger.error(f"Error executing Multi-Agent Debate: {e}", exc_info=True)
            
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            return PatternResult(
                pattern_type=self.pattern_type,
                success=False,
                steps=steps,
                total_duration_ms=duration_ms,
                error=str(e)
            )
    
    async def _initialize_agents(
        self,
        query: str,
        context: Dict[str, Any],
        config: Dict[str, Any],
        num_agents: int,
        agent_positions: Optional[List[str]]
    ) -> Dict[str, Dict[str, Any]]:
        """Initialize debate agents with positions."""
        agent_states = {}
        
        # Generate or use provided positions
        if agent_positions and len(agent_positions) >= num_agents:
            positions = agent_positions[:num_agents]
        else:
            # Generate diverse positions
            positions_step = await self._generate_positions(
                query,
                context,
                config,
                num_agents
            )
            positions = self._parse_positions(positions_step.response, num_agents)
        
        # Create agent states
        for i in range(num_agents):
            agent_id = f"agent_{i+1}"
            position = positions[i] if i < len(positions) else f"Position {i+1}"
            
            init_step = self.create_step(
                step_id=f"init_{agent_id}",
                step_type="init",
                description=f"Initialize {agent_id}",
                prompt=""
            )
            self.complete_step(
                init_step,
                f"Agent {i+1} initialized with position: {position}",
                {
                    "agent_id": agent_id,
                    "position": position,
                    "stage": "initialization"
                }
            )
            
            agent_states[agent_id] = {
                "position": position,
                "init_step": init_step,
                "current_argument": "",
                "critiques_received": []
            }
        
        return agent_states
    
    async def _generate_positions(
        self,
        query: str,
        context: Dict[str, Any],
        config: Dict[str, Any],
        num_agents: int
    ) -> PatternStep:
        """Generate diverse debate positions."""
        step = self.create_step(
            step_id="generate_positions",
            step_type="position_generation",
            description="Generate debate positions",
            prompt=self._build_position_prompt(query, context, num_agents)
        )
        
        try:
            response = await self.call_llm(step.prompt, config)
            self.complete_step(
                step,
                response,
                {"stage": "position_generation"}
            )
        except Exception as e:
            self.complete_step(step, f"Error: {e}", {"error": True})
        
        return step
    
    async def _present_arguments(
        self,
        agent_states: Dict[str, Dict[str, Any]],
        query: str,
        context: Dict[str, Any],
        config: Dict[str, Any],
        round_num: int
    ) -> List[PatternStep]:
        """Each agent presents their argument."""
        tasks = []
        agent_ids = list(agent_states.keys())
        
        for agent_id in agent_ids:
            state = agent_states[agent_id]
            step = self.create_step(
                step_id=f"argument_{agent_id}_round_{round_num}",
                step_type="argument",
                description=f"{agent_id} argument (round {round_num + 1})",
                prompt=self._build_argument_prompt(
                    query,
                    context,
                    state,
                    agent_states,
                    round_num
                )
            )
            tasks.append(self._execute_argument_step(step, config))
        
        # Execute in parallel
        steps = await asyncio.gather(*tasks)
        return list(steps)
    
    async def _execute_argument_step(
        self,
        step: PatternStep,
        config: Dict[str, Any]
    ) -> PatternStep:
        """Execute a single argument step."""
        try:
            response = await self.call_llm(step.prompt, config)
            self.complete_step(
                step,
                response,
                {"stage": "argument"}
            )
        except Exception as e:
            self.complete_step(step, f"Error: {e}", {"error": True})
        
        return step
    
    async def _cross_critique(
        self,
        agent_states: Dict[str, Dict[str, Any]],
        query: str,
        config: Dict[str, Any],
        round_num: int
    ) -> List[PatternStep]:
        """Each agent critiques other agents' arguments."""
        tasks = []
        agent_ids = list(agent_states.keys())
        
        for agent_id in agent_ids:
            for other_id in agent_ids:
                if agent_id != other_id:
                    step = self.create_step(
                        step_id=f"critique_{agent_id}_to_{other_id}_round_{round_num}",
                        step_type="critique",
                        description=f"{agent_id} critiques {other_id} (round {round_num + 1})",
                        prompt=self._build_critique_prompt(
                            query,
                            agent_states[agent_id],
                            agent_states[other_id]
                        )
                    )
                    tasks.append(self._execute_critique_step(step, config))
        
        # Execute in parallel
        steps = await asyncio.gather(*tasks)
        return list(steps)
    
    async def _execute_critique_step(
        self,
        step: PatternStep,
        config: Dict[str, Any]
    ) -> PatternStep:
        """Execute a single critique step."""
        try:
            response = await self.call_llm(step.prompt, config)
            self.complete_step(
                step,
                response,
                {"stage": "critique"}
            )
        except Exception as e:
            self.complete_step(step, f"Error: {e}", {"error": True})
        
        return step
    
    async def _synthesize_final_answer(
        self,
        agent_states: Dict[str, Dict[str, Any]],
        query: str,
        context: Dict[str, Any],
        config: Dict[str, Any],
        all_steps: List[PatternStep]
    ) -> PatternStep:
        """Synthesize final answer from debate."""
        step = self.create_step(
            step_id="synthesis",
            step_type="synthesis",
            description="Synthesize final answer from debate",
            prompt=self._build_synthesis_prompt(
                query,
                context,
                agent_states,
                all_steps
            )
        )
        
        try:
            response = await self.call_llm(step.prompt, config)
            self.complete_step(
                step,
                response,
                {"stage": "synthesis"}
            )
        except Exception as e:
            self.complete_step(step, f"Error: {e}", {"error": True})
        
        return step
    
    def _build_position_prompt(
        self,
        query: str,
        context: Dict[str, Any],
        num_agents: int
    ) -> str:
        """Build prompt for generating debate positions."""
        context_str = self._format_context(context)
        
        return f"""Generate {num_agents} diverse debate positions for this question.

Question: {query}

{context_str}

Instructions:
1. Create {num_agents} distinct perspectives/positions
2. Each should be a valid viewpoint
3. Positions should be diverse and complementary
4. Number each position clearly
5. Keep each position to one sentence

Format:
Position 1: [position]
Position 2: [position]
...

Positions:"""
    
    def _build_argument_prompt(
        self,
        query: str,
        context: Dict[str, Any],
        agent_state: Dict[str, Any],
        all_states: Dict[str, Dict[str, Any]],
        round_num: int
    ) -> str:
        """Build prompt for agent argument."""
        context_str = self._format_context(context)
        position = agent_state["position"]
        
        # Include previous arguments and critiques if not first round
        history_str = ""
        if round_num > 0:
            if agent_state["current_argument"]:
                history_str += f"\n\nYour Previous Argument:\n{agent_state['current_argument'][:300]}...\n"
            
            if agent_state["critiques_received"]:
                history_str += "\n\nCritiques You Received:\n"
                for i, critique in enumerate(agent_state["critiques_received"][:2], 1):
                    history_str += f"{i}. {critique[:150]}...\n"
        
        return f"""You are a debate agent arguing from a specific position.

Question: {query}

{context_str}

Your Position: {position}

Round: {round_num + 1}{history_str}

Instructions:
1. Argue forcefully for your position
2. Use evidence and reasoning
3. If round > 1, address critiques
4. Be persuasive and clear
5. Focus on strengths of your view

Your Argument:"""
    
    def _build_critique_prompt(
        self,
        query: str,
        critic_state: Dict[str, Any],
        target_state: Dict[str, Any]
    ) -> str:
        """Build prompt for critiquing another agent."""
        critic_position = critic_state["position"]
        target_position = target_state["position"]
        target_argument = target_state["current_argument"]
        
        return f"""Critique the following argument from an opposing perspective.

Question: {query}

Their Position: {target_position}

Their Argument:
{target_argument[:500]}...

Your Position: {critic_position}

Critique Instructions:
1. Identify weaknesses in their argument
2. Point out logical flaws
3. Challenge their evidence
4. Highlight what they're missing
5. Be constructive but critical
6. Keep it brief

Your Critique:"""
    
    def _build_synthesis_prompt(
        self,
        query: str,
        context: Dict[str, Any],
        agent_states: Dict[str, Dict[str, Any]],
        all_steps: List[PatternStep]
    ) -> str:
        """Build prompt for synthesizing final answer."""
        context_str = self._format_context(context)
        
        # Summarize debate
        debate_summary = "\n\n".join([
            f"Position {i+1}: {state['position']}\n"
            f"Final Argument: {state['current_argument'][:200]}..."
            for i, state in enumerate(agent_states.values())
        ])
        
        return f"""Synthesize a final answer from this multi-agent debate.

Question: {query}

{context_str}

Debate Summary:
{debate_summary}

Synthesis Instructions:
1. Consider all perspectives presented
2. Identify common ground
3. Resolve contradictions
4. Synthesize the best elements
5. Provide a balanced final answer
6. Acknowledge complexity if needed

Final Answer:"""
    
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
    
    def _parse_positions(self, positions_text: str, num_agents: int) -> List[str]:
        """Parse positions from LLM response."""
        positions = []
        
        if not positions_text:
            # Fallback positions
            return [f"Perspective {i+1}" for i in range(num_agents)]
        
        # Parse numbered positions
        lines = positions_text.split('\n')
        for line in lines:
            if line.strip().startswith(('Position', '1.', '2.', '3.', '4.', '5.')):
                # Extract position text
                if ':' in line:
                    position = line.split(':', 1)[1].strip()
                    positions.append(position)
        
        # Fill in if not enough
        while len(positions) < num_agents:
            positions.append(f"Alternative Perspective {len(positions) + 1}")
        
        return positions[:num_agents]
    
    def _calculate_debate_confidence(
        self,
        agent_states: Dict[str, Dict[str, Any]],
        steps: List[PatternStep]
    ) -> float:
        """Calculate confidence based on debate quality."""
        if not steps:
            return 0.0
        
        # Factors:
        # 1. Number of agents (more = higher confidence)
        num_agents = len(agent_states)
        agent_factor = min(num_agents / 3, 1.0)
        
        # 2. Debate thoroughness (arguments + critiques)
        arguments = len([s for s in steps if s.step_type == "argument"])
        critiques = len([s for s in steps if s.step_type == "critique"])
        thoroughness = min((arguments + critiques) / 15, 1.0)
        
        # 3. Synthesis present
        has_synthesis = any(s.step_type == "synthesis" for s in steps)
        synthesis_factor = 1.0 if has_synthesis else 0.5
        
        # Combine
        confidence = (
            agent_factor * 0.3 +
            thoroughness * 0.4 +
            synthesis_factor * 0.3
        )
        
        return min(confidence, 1.0)

