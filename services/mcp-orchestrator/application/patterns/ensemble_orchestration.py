"""Ensemble Orchestration pattern implementation."""

from typing import Any, Dict, List, Optional
from datetime import datetime
import asyncio

from .base import BasePatternEngine, PatternResult, PatternStep


class EnsembleOrchestrationEngine(BasePatternEngine):
    """
    Ensemble Orchestration pattern execution engine.
    
    Coordinates multiple LLMs working on different aspects of a problem.
    Each LLM specializes in a specific role (analysis, synthesis, critique, etc.)
    
    Process:
    1. Problem decomposition - Break into parallel tasks
    2. Parallel execution - Each LLM works on assigned task
    3. Result integration - Combine outputs intelligently
    4. Synthesis - Create unified answer
    
    Advantages:
    - Parallel execution (faster than sequential)
    - Specialization (each LLM has specific role)
    - Diverse perspectives
    - Quality through complementary strengths
    """
    
    def __init__(self):
        super().__init__("ensemble_orchestration")
    
    async def execute(
        self,
        query: str,
        context: Dict[str, Any],
        config: Dict[str, Any]
    ) -> PatternResult:
        """Execute Ensemble Orchestration pattern."""
        start_time = datetime.utcnow()
        steps: List[PatternStep] = []
        
        try:
            # Configuration
            roles = config.get("ensemble_roles", ["analyst", "synthesizer", "critic"])
            parallel_execution = config.get("parallel_execution", True)
            
            # Step 1: Decompose problem into role-specific tasks
            decomp_step = await self._decompose_by_roles(
                query,
                context,
                config,
                roles
            )
            steps.append(decomp_step)
            
            # Extract tasks from decomposition
            tasks = self._extract_tasks(decomp_step.response or "", roles)
            
            # Step 2: Execute tasks (parallel or sequential)
            if parallel_execution:
                execution_steps = await self._execute_parallel(
                    tasks,
                    query,
                    context,
                    config
                )
            else:
                execution_steps = await self._execute_sequential(
                    tasks,
                    query,
                    context,
                    config
                )
            steps.extend(execution_steps)
            
            # Step 3: Integrate results
            integration_step = await self._integrate_results(
                query,
                execution_steps,
                context,
                config
            )
            steps.append(integration_step)
            
            # Step 4: Synthesize final answer
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
            confidence = self._calculate_ensemble_confidence(execution_steps)
            
            return PatternResult(
                pattern_type=self.pattern_type,
                success=True,
                steps=steps,
                final_answer=synthesis_step.response,
                confidence=confidence,
                total_duration_ms=duration_ms,
                metadata={
                    "roles_used": roles,
                    "parallel_execution": parallel_execution,
                    "tasks_completed": len(execution_steps),
                    "integration_quality": self._assess_integration(integration_step)
                }
            )
        
        except Exception as e:
            self.logger.error(f"Error executing Ensemble Orchestration: {e}", exc_info=True)
            
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            return PatternResult(
                pattern_type=self.pattern_type,
                success=False,
                steps=steps,
                total_duration_ms=duration_ms,
                error=str(e)
            )
    
    async def _decompose_by_roles(
        self,
        query: str,
        context: Dict[str, Any],
        config: Dict[str, Any],
        roles: List[str]
    ) -> PatternStep:
        """Decompose problem into role-specific tasks."""
        step = self.create_step(
            step_id="decompose_roles",
            step_type="decomposition",
            description=f"Assign tasks to {len(roles)} specialist roles",
            prompt=self._build_role_decomposition_prompt(query, context, roles)
        )
        
        try:
            response = await self.call_llm(step.prompt, config)
            self.complete_step(
                step,
                response,
                {
                    "stage": "role_decomposition",
                    "roles": roles,
                    "role_count": len(roles)
                }
            )
        except Exception as e:
            self.complete_step(step, f"Error: {e}", {"error": True})
        
        return step
    
    async def _execute_parallel(
        self,
        tasks: List[Dict[str, str]],
        query: str,
        context: Dict[str, Any],
        config: Dict[str, Any]
    ) -> List[PatternStep]:
        """Execute all tasks in parallel."""
        # Create all tasks as coroutines
        coroutines = [
            self._execute_role_task(task, query, context, config)
            for task in tasks
        ]
        
        # Execute in parallel
        execution_steps = await asyncio.gather(*coroutines)
        
        return list(execution_steps)
    
    async def _execute_sequential(
        self,
        tasks: List[Dict[str, str]],
        query: str,
        context: Dict[str, Any],
        config: Dict[str, Any]
    ) -> List[PatternStep]:
        """Execute tasks sequentially."""
        execution_steps = []
        
        for task in tasks:
            step = await self._execute_role_task(task, query, context, config)
            execution_steps.append(step)
        
        return execution_steps
    
    async def _execute_role_task(
        self,
        task: Dict[str, str],
        query: str,
        context: Dict[str, Any],
        config: Dict[str, Any]
    ) -> PatternStep:
        """Execute a single role-specific task."""
        role = task["role"]
        task_description = task["task"]
        
        step = self.create_step(
            step_id=f"execute_{role}",
            step_type="role_execution",
            description=f"{role.title()} role: {task_description[:50]}...",
            prompt=self._build_role_execution_prompt(
                role,
                task_description,
                query,
                context
            )
        )
        
        try:
            response = await self.call_llm(step.prompt, config)
            self.complete_step(
                step,
                response,
                {
                    "stage": "role_execution",
                    "role": role,
                    "task": task_description
                }
            )
        except Exception as e:
            self.complete_step(step, f"Error: {e}", {"error": True})
        
        return step
    
    async def _integrate_results(
        self,
        query: str,
        execution_steps: List[PatternStep],
        context: Dict[str, Any],
        config: Dict[str, Any]
    ) -> PatternStep:
        """Integrate results from all roles."""
        step = self.create_step(
            step_id="integrate",
            step_type="integration",
            description=f"Integrate insights from {len(execution_steps)} specialists",
            prompt=self._build_integration_prompt(query, execution_steps, context)
        )
        
        try:
            response = await self.call_llm(step.prompt, config)
            self.complete_step(
                step,
                response,
                {
                    "stage": "integration",
                    "inputs_integrated": len(execution_steps),
                    "roles_integrated": [
                        s.metadata.get("role")
                        for s in execution_steps
                        if s.metadata.get("role")
                    ]
                }
            )
        except Exception as e:
            self.complete_step(step, f"Error: {e}", {"error": True})
        
        return step
    
    async def _synthesize_answer(
        self,
        query: str,
        steps: List[PatternStep],
        context: Dict[str, Any],
        config: Dict[str, Any]
    ) -> PatternStep:
        """Synthesize final answer from integrated results."""
        step = self.create_step(
            step_id="synthesize",
            step_type="synthesis",
            description="Create final comprehensive answer",
            prompt=self._build_synthesis_prompt(query, steps, context)
        )
        
        try:
            response = await self.call_llm(step.prompt, config)
            self.complete_step(step, response, {"stage": "synthesis"})
        except Exception as e:
            self.complete_step(step, f"Error: {e}", {"error": True})
        
        return step
    
    def _build_role_decomposition_prompt(
        self,
        query: str,
        context: Dict[str, Any],
        roles: List[str]
    ) -> str:
        """Build prompt for role-based decomposition."""
        context_str = self._format_context(context)
        
        role_descriptions = {
            "analyst": "Deep analysis of the problem, data patterns, and implications",
            "synthesizer": "Combining information and creating coherent narratives",
            "critic": "Identifying flaws, limitations, and potential issues",
            "strategist": "Planning approaches and long-term considerations",
            "implementer": "Practical execution details and concrete steps",
            "evaluator": "Assessing quality, feasibility, and risks"
        }
        
        roles_str = "\n".join([
            f"- {role.title()}: {role_descriptions.get(role, 'Specialized perspective')}"
            for role in roles
        ])
        
        return f"""Decompose this query into specific tasks for each specialist role.

Query: {query}

{context_str}

Available specialist roles:
{roles_str}

Instructions:
1. Assign a specific, focused task to each role
2. Tasks should be complementary (not overlapping)
3. Each task should leverage the role's expertise
4. Format: "Role: [task description]"
5. Be specific about what each role should analyze/produce

Task assignments:"""
    
    def _build_role_execution_prompt(
        self,
        role: str,
        task: str,
        query: str,
        context: Dict[str, Any]
    ) -> str:
        """Build prompt for role-specific execution."""
        context_str = self._format_context(context)
        
        role_instructions = {
            "analyst": "Provide deep, data-driven analysis. Look for patterns, trends, and insights.",
            "synthesizer": "Combine information into coherent narrative. Connect disparate pieces.",
            "critic": "Identify potential flaws, limitations, and risks. Be constructively critical.",
            "strategist": "Think long-term. Consider approaches, trade-offs, and planning.",
            "implementer": "Focus on practical execution. Provide concrete, actionable steps.",
            "evaluator": "Assess quality and feasibility. Rate options and identify best path."
        }
        
        instruction = role_instructions.get(role, "Provide your specialized perspective.")
        
        return f"""You are a {role.title()} specialist. Complete your assigned task.

Original Query: {query}

Your Task: {task}

{context_str}

Role Instructions:
{instruction}

Focus on your specialty. Be thorough but concise.

{role.title()}'s Response:"""
    
    def _build_integration_prompt(
        self,
        query: str,
        execution_steps: List[PatternStep],
        context: Dict[str, Any]
    ) -> str:
        """Build prompt for integrating results."""
        context_str = self._format_context(context)
        
        # Gather all role outputs
        outputs_str = "\n\n".join([
            f"{step.metadata.get('role', 'Unknown').title()} Output:\n{step.response[:500]}..."
            if step.response else f"{step.metadata.get('role', 'Unknown').title()}: No output"
            for step in execution_steps
            if step.step_type == "role_execution"
        ])
        
        return f"""Integrate the insights from multiple specialist perspectives into a coherent analysis.

Original Query: {query}

{context_str}

Specialist Outputs:
{outputs_str}

Instructions:
1. Identify common themes across specialists
2. Resolve any contradictions intelligently
3. Highlight unique insights from each perspective
4. Create an integrated understanding
5. Note areas of agreement and disagreement

Integrated Analysis:"""
    
    def _build_synthesis_prompt(
        self,
        query: str,
        steps: List[PatternStep],
        context: Dict[str, Any]
    ) -> str:
        """Build prompt for final synthesis."""
        context_str = self._format_context(context)
        
        # Get integration result
        integration_step = next(
            (s for s in steps if s.step_type == "integration"),
            None
        )
        integration_text = integration_step.response if integration_step else "No integration available"
        
        return f"""Based on the integrated analysis from multiple specialists, provide a comprehensive final answer.

Original Query: {query}

{context_str}

Integrated Analysis:
{integration_text[:800]}...

Instructions:
1. Answer the original query directly and completely
2. Incorporate insights from all specialists
3. Provide balanced perspective
4. Be clear and actionable
5. Mention key considerations

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
    
    def _extract_tasks(self, response: str, roles: List[str]) -> List[Dict[str, str]]:
        """Extract role-task assignments from response."""
        if not response:
            # Fallback: generic tasks
            return [
                {"role": role, "task": f"Provide {role} perspective on the query"}
                for role in roles
            ]
        
        tasks = []
        lines = response.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if ':' in line:
                # Look for "Role: Task" pattern
                parts = line.split(':', 1)
                potential_role = parts[0].strip().lower()
                
                # Check if this matches one of our roles
                if any(role in potential_role for role in roles):
                    role = next(r for r in roles if r in potential_role)
                    task = parts[1].strip()
                    tasks.append({"role": role, "task": task})
        
        # If we didn't extract enough tasks, add generic ones
        roles_covered = {t["role"] for t in tasks}
        for role in roles:
            if role not in roles_covered:
                tasks.append({
                    "role": role,
                    "task": f"Provide {role} perspective on the query"
                })
        
        return tasks
    
    def _assess_integration(self, integration_step: PatternStep) -> float:
        """Assess quality of integration."""
        if not integration_step or not integration_step.response:
            return 0.0
        
        response = integration_step.response.lower()
        
        # Quality indicators
        quality_score = 0.0
        
        # Check for synthesis indicators
        synthesis_words = ["integrate", "combine", "together", "both", "all"]
        quality_score += sum(0.1 for word in synthesis_words if word in response)
        
        # Check for balance indicators
        balance_words = ["however", "while", "although", "perspective", "view"]
        quality_score += sum(0.1 for word in balance_words if word in response)
        
        # Check length (longer = more thorough)
        if len(response) > 200:
            quality_score += 0.3
        
        return min(quality_score, 1.0)
    
    def _calculate_ensemble_confidence(
        self,
        execution_steps: List[PatternStep]
    ) -> float:
        """Calculate confidence based on ensemble execution."""
        if not execution_steps:
            return 0.0
        
        # Check completion rate
        completed = sum(
            1 for s in execution_steps
            if s.response and not s.metadata.get("error")
        )
        completion_rate = completed / len(execution_steps)
        
        # Check response quality (average length)
        avg_length = sum(
            len(s.response or "")
            for s in execution_steps
        ) / len(execution_steps)
        quality_factor = min(avg_length / 200, 1.0)
        
        # Check diversity (different responses)
        unique_starts = len(set(
            (s.response or "")[:50]
            for s in execution_steps
        ))
        diversity_factor = min(unique_starts / len(execution_steps), 1.0)
        
        # Combine factors
        confidence = (
            completion_rate * 0.4 +
            quality_factor * 0.3 +
            diversity_factor * 0.3
        )
        
        return min(confidence, 1.0)

