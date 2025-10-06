"""Multi-Agent Collaboration pattern implementation."""

from typing import Any, Dict, List, Optional
from datetime import datetime
import asyncio

from .base import BasePatternEngine, PatternResult, PatternStep


class MultiAgentCollaborationEngine(BasePatternEngine):
    """
    Multi-Agent Collaboration pattern execution engine.
    
    Multiple LLM agents work together cooperatively, each with
    specialized roles or expertise, to solve complex problems
    through collaboration rather than debate.
    
    Process:
    1. Decompose problem into sub-tasks
    2. Assign sub-tasks to specialized agents
    3. Agents work on their tasks (parallel)
    4. Agents share intermediate results
    5. Coordinator integrates contributions
    6. Iterate if needed
    
    Key Innovation: Division of labor with specialization,
    similar to a collaborative team working on a project.
    """
    
    def __init__(self):
        super().__init__("multi_agent_collaboration")
    
    async def execute(
        self,
        query: str,
        context: Dict[str, Any],
        config: Dict[str, Any]
    ) -> PatternResult:
        """Execute Multi-Agent Collaboration pattern."""
        start_time = datetime.utcnow()
        steps: List[PatternStep] = []
        
        try:
            # Configuration
            agent_roles = config.get("collab_agent_roles", [
                "Researcher", "Analyst", "Strategist"
            ])
            num_iterations = config.get("collab_num_iterations", 1)
            
            # Step 1: Decompose problem into sub-tasks
            decomposition_step = await self._decompose_problem(
                query,
                context,
                config,
                agent_roles
            )
            steps.append(decomposition_step)
            
            # Parse sub-tasks
            subtasks = self._parse_subtasks(
                decomposition_step.response,
                agent_roles
            )
            
            # Step 2: Initialize agents with roles and sub-tasks
            agent_states = self._initialize_collaborative_agents(
                agent_roles,
                subtasks
            )
            
            # Add init steps
            for agent_id, state in agent_states.items():
                steps.append(state["init_step"])
            
            # Collaboration iterations
            for iteration in range(num_iterations):
                self.logger.info(f"Starting collaboration iteration {iteration + 1}")
                
                # Step 3: Agents work on their sub-tasks (parallel)
                work_steps = await self._execute_subtasks(
                    agent_states,
                    query,
                    context,
                    config,
                    iteration
                )
                steps.extend(work_steps)
                
                # Update agent states with results
                for i, agent_id in enumerate(agent_states.keys()):
                    agent_states[agent_id]["current_result"] = work_steps[i].response
                
                # Step 4: Share results between agents
                sharing_step = await self._share_intermediate_results(
                    agent_states,
                    query,
                    config,
                    iteration
                )
                steps.append(sharing_step)
                
                # Update agent states with shared context
                shared_context = sharing_step.response or ""
                for agent_id in agent_states.keys():
                    agent_states[agent_id]["shared_context"] = shared_context
            
            # Step 5: Coordinator integrates all contributions
            integration_step = await self._integrate_contributions(
                agent_states,
                query,
                context,
                config
            )
            steps.append(integration_step)
            
            # Calculate execution time
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Calculate confidence
            confidence = self._calculate_collaboration_confidence(agent_states, steps)
            
            return PatternResult(
                pattern_type=self.pattern_type,
                success=True,
                steps=steps,
                final_answer=integration_step.response,
                confidence=confidence,
                total_duration_ms=duration_ms,
                metadata={
                    "agent_roles": agent_roles,
                    "num_agents": len(agent_roles),
                    "subtasks": subtasks,
                    "iterations": num_iterations,
                    "total_work_steps": len([s for s in steps if s.step_type == "work"])
                }
            )
        
        except Exception as e:
            self.logger.error(f"Error executing Multi-Agent Collaboration: {e}", exc_info=True)
            
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
        config: Dict[str, Any],
        agent_roles: List[str]
    ) -> PatternStep:
        """Decompose problem into sub-tasks for agents."""
        step = self.create_step(
            step_id="decomposition",
            step_type="decomposition",
            description="Decompose problem into sub-tasks",
            prompt=self._build_decomposition_prompt(query, context, agent_roles)
        )
        
        try:
            response = await self.call_llm(step.prompt, config)
            self.complete_step(
                step,
                response,
                {"stage": "decomposition"}
            )
        except Exception as e:
            self.complete_step(step, f"Error: {e}", {"error": True})
        
        return step
    
    def _initialize_collaborative_agents(
        self,
        agent_roles: List[str],
        subtasks: Dict[str, str]
    ) -> Dict[str, Dict[str, Any]]:
        """Initialize collaborative agents with roles and tasks."""
        agent_states = {}
        
        for i, role in enumerate(agent_roles):
            agent_id = f"agent_{role.lower().replace(' ', '_')}"
            subtask = subtasks.get(role, f"Contribute expertise as {role}")
            
            init_step = self.create_step(
                step_id=f"init_{agent_id}",
                step_type="init",
                description=f"Initialize {role}",
                prompt=""
            )
            self.complete_step(
                init_step,
                f"{role} initialized with task: {subtask}",
                {
                    "agent_id": agent_id,
                    "role": role,
                    "subtask": subtask,
                    "stage": "initialization"
                }
            )
            
            agent_states[agent_id] = {
                "role": role,
                "subtask": subtask,
                "init_step": init_step,
                "current_result": "",
                "shared_context": ""
            }
        
        return agent_states
    
    async def _execute_subtasks(
        self,
        agent_states: Dict[str, Dict[str, Any]],
        query: str,
        context: Dict[str, Any],
        config: Dict[str, Any],
        iteration: int
    ) -> List[PatternStep]:
        """Agents work on their sub-tasks in parallel."""
        tasks = []
        agent_ids = list(agent_states.keys())
        
        for agent_id in agent_ids:
            state = agent_states[agent_id]
            step = self.create_step(
                step_id=f"work_{agent_id}_iter_{iteration}",
                step_type="work",
                description=f"{state['role']} working (iteration {iteration + 1})",
                prompt=self._build_work_prompt(
                    query,
                    context,
                    state,
                    iteration
                )
            )
            tasks.append(self._execute_work_step(step, config))
        
        # Execute in parallel
        steps = await asyncio.gather(*tasks)
        return list(steps)
    
    async def _execute_work_step(
        self,
        step: PatternStep,
        config: Dict[str, Any]
    ) -> PatternStep:
        """Execute a single work step."""
        try:
            response = await self.call_llm(step.prompt, config)
            self.complete_step(
                step,
                response,
                {"stage": "work"}
            )
        except Exception as e:
            self.complete_step(step, f"Error: {e}", {"error": True})
        
        return step
    
    async def _share_intermediate_results(
        self,
        agent_states: Dict[str, Dict[str, Any]],
        query: str,
        config: Dict[str, Any],
        iteration: int
    ) -> PatternStep:
        """Share intermediate results between agents."""
        step = self.create_step(
            step_id=f"sharing_iter_{iteration}",
            step_type="sharing",
            description=f"Share results (iteration {iteration + 1})",
            prompt=self._build_sharing_prompt(query, agent_states)
        )
        
        try:
            response = await self.call_llm(step.prompt, config)
            self.complete_step(
                step,
                response,
                {
                    "stage": "sharing",
                    "iteration": iteration
                }
            )
        except Exception as e:
            self.complete_step(step, f"Error: {e}", {"error": True})
        
        return step
    
    async def _integrate_contributions(
        self,
        agent_states: Dict[str, Dict[str, Any]],
        query: str,
        context: Dict[str, Any],
        config: Dict[str, Any]
    ) -> PatternStep:
        """Integrate all agent contributions into final answer."""
        step = self.create_step(
            step_id="integration",
            step_type="integration",
            description="Integrate all contributions",
            prompt=self._build_integration_prompt(query, context, agent_states)
        )
        
        try:
            response = await self.call_llm(step.prompt, config)
            self.complete_step(
                step,
                response,
                {"stage": "integration"}
            )
        except Exception as e:
            self.complete_step(step, f"Error: {e}", {"error": True})
        
        return step
    
    def _build_decomposition_prompt(
        self,
        query: str,
        context: Dict[str, Any],
        agent_roles: List[str]
    ) -> str:
        """Build prompt for problem decomposition."""
        context_str = self._format_context(context)
        roles_str = ", ".join(agent_roles)
        
        return f"""Decompose this problem into sub-tasks for a team of collaborative agents.

Problem: {query}

{context_str}

Team Roles: {roles_str}

Decomposition Instructions:
1. Break problem into {len(agent_roles)} complementary sub-tasks
2. Assign each sub-task to an agent role
3. Ensure sub-tasks cover the full problem
4. Sub-tasks should be parallelizable
5. Clear and specific

Format:
- {agent_roles[0]}: [sub-task description]
- {agent_roles[1]}: [sub-task description]
...

Sub-tasks:"""
    
    def _build_work_prompt(
        self,
        query: str,
        context: Dict[str, Any],
        agent_state: Dict[str, Any],
        iteration: int
    ) -> str:
        """Build prompt for agent work."""
        context_str = self._format_context(context)
        role = agent_state["role"]
        subtask = agent_state["subtask"]
        
        # Include previous work and shared context if available
        history_str = ""
        if iteration > 0:
            if agent_state["current_result"]:
                history_str += f"\n\nYour Previous Work:\n{agent_state['current_result'][:300]}...\n"
            if agent_state["shared_context"]:
                history_str += f"\nTeam Updates:\n{agent_state['shared_context'][:300]}...\n"
        
        return f"""You are a collaborative team member with a specific role and task.

Problem: {query}

{context_str}

Your Role: {role}

Your Task: {subtask}

Iteration: {iteration + 1}{history_str}

Work Instructions:
1. Focus on YOUR specific task
2. Provide thorough analysis/work
3. If iteration > 0, build on previous work
4. Consider team updates
5. Be specific and actionable
6. Prepare to share with team

Your Contribution:"""
    
    def _build_sharing_prompt(
        self,
        query: str,
        agent_states: Dict[str, Dict[str, Any]]
    ) -> str:
        """Build prompt for sharing intermediate results."""
        # Summarize each agent's contribution
        contributions = "\n\n".join([
            f"{state['role']}:\n{state['current_result'][:250]}..."
            for state in agent_states.values()
        ])
        
        return f"""Summarize the team's progress for inter-agent sharing.

Problem: {query}

Team Contributions:
{contributions}

Sharing Instructions:
1. Summarize key findings from each role
2. Identify connections between contributions
3. Note any gaps or overlaps
4. Provide context for next iteration
5. Be concise but informative

Team Progress Summary:"""
    
    def _build_integration_prompt(
        self,
        query: str,
        context: Dict[str, Any],
        agent_states: Dict[str, Dict[str, Any]]
    ) -> str:
        """Build prompt for integrating contributions."""
        context_str = self._format_context(context)
        
        # Compile all contributions
        all_contributions = "\n\n".join([
            f"=== {state['role']} ===" f"\nTask: {state['subtask']}\n"
            f"Contribution:\n{state['current_result'][:400]}..."
            for state in agent_states.values()
        ])
        
        return f"""Integrate all team contributions into a comprehensive final answer.

Problem: {query}

{context_str}

Team Contributions:
{all_contributions}

Integration Instructions:
1. Synthesize all contributions
2. Ensure coverage of all aspects
3. Resolve any conflicts
4. Create coherent narrative
5. Provide complete answer
6. Acknowledge team effort

Final Integrated Answer:"""
    
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
    
    def _parse_subtasks(
        self,
        decomposition_text: str,
        agent_roles: List[str]
    ) -> Dict[str, str]:
        """Parse sub-tasks from decomposition response."""
        subtasks = {}
        
        if not decomposition_text:
            # Fallback
            return {role: f"Contribute as {role}" for role in agent_roles}
        
        # Parse role-task pairs
        lines = decomposition_text.split('\n')
        for line in lines:
            line = line.strip()
            if ':' in line:
                for role in agent_roles:
                    if role.lower() in line.lower():
                        task = line.split(':', 1)[1].strip()
                        subtasks[role] = task
                        break
        
        # Fill in missing
        for role in agent_roles:
            if role not in subtasks:
                subtasks[role] = f"Contribute expertise as {role}"
        
        return subtasks
    
    def _calculate_collaboration_confidence(
        self,
        agent_states: Dict[str, Dict[str, Any]],
        steps: List[PatternStep]
    ) -> float:
        """Calculate confidence based on collaboration quality."""
        if not steps:
            return 0.0
        
        # Factors:
        # 1. All agents contributed
        num_agents = len(agent_states)
        agents_with_results = sum(
            1 for state in agent_states.values()
            if state["current_result"]
        )
        contribution_factor = agents_with_results / max(num_agents, 1)
        
        # 2. Decomposition quality
        has_decomposition = any(s.step_type == "decomposition" for s in steps)
        decomposition_factor = 1.0 if has_decomposition else 0.5
        
        # 3. Integration present
        has_integration = any(s.step_type == "integration" for s in steps)
        integration_factor = 1.0 if has_integration else 0.5
        
        # Combine
        confidence = (
            contribution_factor * 0.4 +
            decomposition_factor * 0.3 +
            integration_factor * 0.3
        )
        
        return min(confidence, 1.0)

