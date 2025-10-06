"""Multi-Agent Voting pattern implementation."""

from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from collections import Counter
import asyncio

from .base import BasePatternEngine, PatternResult, PatternStep


class MultiAgentVotingEngine(BasePatternEngine):
    """
    Multi-Agent Voting pattern execution engine.
    
    Multiple LLM agents independently generate answers to a question,
    then vote on the best response. Democratic decision-making for
    robust, consensus-based answers.
    
    Process:
    1. Each agent independently generates an answer
    2. Agents review all answers
    3. Agents vote for the best answer
    4. Tally votes and determine winner
    5. Optional: Winner agent can refine based on feedback
    
    Key Innovation: Democratic consensus without debate -
    agents vote on pre-generated solutions.
    """
    
    def __init__(self):
        super().__init__("multi_agent_voting")
    
    async def execute(
        self,
        query: str,
        context: Dict[str, Any],
        config: Dict[str, Any]
    ) -> PatternResult:
        """Execute Multi-Agent Voting pattern."""
        start_time = datetime.utcnow()
        steps: List[PatternStep] = []
        
        try:
            # Configuration
            num_agents = config.get("voting_num_agents", 5)
            voting_method = config.get("voting_method", "majority")  # majority, ranked
            refine_winner = config.get("voting_refine_winner", False)
            
            # Step 1: Each agent generates an answer independently
            self.logger.info(f"Generating {num_agents} independent answers")
            generation_steps = await self._generate_independent_answers(
                query,
                context,
                config,
                num_agents
            )
            steps.extend(generation_steps)
            
            # Extract answers
            answers = [
                {"agent_id": f"agent_{i+1}", "answer": step.response}
                for i, step in enumerate(generation_steps)
            ]
            
            # Step 2: Agents review all answers
            review_step = await self._compile_answers_for_review(
                query,
                answers,
                config
            )
            steps.append(review_step)
            
            # Step 3: Each agent votes
            self.logger.info("Agents casting votes")
            voting_steps = await self._cast_votes(
                query,
                answers,
                config,
                num_agents
            )
            steps.extend(voting_steps)
            
            # Step 4: Tally votes
            tally_step = await self._tally_votes(
                voting_steps,
                answers,
                voting_method
            )
            steps.append(tally_step)
            
            # Determine winner
            winner_id, vote_counts = self._determine_winner(
                voting_steps,
                answers,
                voting_method
            )
            
            winner_answer = next(
                (a["answer"] for a in answers if a["agent_id"] == winner_id),
                answers[0]["answer"] if answers else "No answer"
            )
            
            # Step 5 (Optional): Refine winner based on feedback
            final_answer = winner_answer
            if refine_winner:
                refinement_step = await self._refine_winning_answer(
                    query,
                    winner_answer,
                    voting_steps,
                    config
                )
                steps.append(refinement_step)
                final_answer = refinement_step.response or winner_answer
            
            # Calculate execution time
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Calculate confidence based on vote distribution
            confidence = self._calculate_voting_confidence(vote_counts, num_agents)
            
            return PatternResult(
                pattern_type=self.pattern_type,
                success=True,
                steps=steps,
                final_answer=final_answer,
                confidence=confidence,
                total_duration_ms=duration_ms,
                metadata={
                    "num_agents": num_agents,
                    "voting_method": voting_method,
                    "winner_id": winner_id,
                    "vote_counts": vote_counts,
                    "refined": refine_winner
                }
            )
        
        except Exception as e:
            self.logger.error(f"Error executing Multi-Agent Voting: {e}", exc_info=True)
            
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            return PatternResult(
                pattern_type=self.pattern_type,
                success=False,
                steps=steps,
                total_duration_ms=duration_ms,
                error=str(e)
            )
    
    async def _generate_independent_answers(
        self,
        query: str,
        context: Dict[str, Any],
        config: Dict[str, Any],
        num_agents: int
    ) -> List[PatternStep]:
        """Generate independent answers from each agent."""
        tasks = []
        
        for i in range(num_agents):
            step = self.create_step(
                step_id=f"generate_agent_{i+1}",
                step_type="generation",
                description=f"Agent {i+1} generates answer",
                prompt=self._build_generation_prompt(query, context, i+1)
            )
            tasks.append(self._execute_generation_step(step, config))
        
        # Execute in parallel
        steps = await asyncio.gather(*tasks)
        return list(steps)
    
    async def _execute_generation_step(
        self,
        step: PatternStep,
        config: Dict[str, Any]
    ) -> PatternStep:
        """Execute a single generation step."""
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
    
    async def _compile_answers_for_review(
        self,
        query: str,
        answers: List[Dict[str, str]],
        config: Dict[str, Any]
    ) -> PatternStep:
        """Compile all answers for review."""
        step = self.create_step(
            step_id="compile_answers",
            step_type="compilation",
            description="Compile answers for voting",
            prompt=""
        )
        
        # Just summarize the answers
        compilation = "\n\n".join([
            f"=== {a['agent_id']} ===\n{a['answer'][:300]}..."
            for a in answers
        ])
        
        self.complete_step(
            step,
            compilation,
            {
                "stage": "compilation",
                "num_answers": len(answers)
            }
        )
        
        return step
    
    async def _cast_votes(
        self,
        query: str,
        answers: List[Dict[str, str]],
        config: Dict[str, Any],
        num_agents: int
    ) -> List[PatternStep]:
        """Each agent votes for the best answer."""
        tasks = []
        
        for i in range(num_agents):
            step = self.create_step(
                step_id=f"vote_agent_{i+1}",
                step_type="vote",
                description=f"Agent {i+1} votes",
                prompt=self._build_voting_prompt(query, answers, i+1)
            )
            tasks.append(self._execute_voting_step(step, config))
        
        # Execute in parallel
        steps = await asyncio.gather(*tasks)
        return list(steps)
    
    async def _execute_voting_step(
        self,
        step: PatternStep,
        config: Dict[str, Any]
    ) -> PatternStep:
        """Execute a single voting step."""
        try:
            response = await self.call_llm(step.prompt, config)
            self.complete_step(
                step,
                response,
                {"stage": "voting"}
            )
        except Exception as e:
            self.complete_step(step, f"Error: {e}", {"error": True})
        
        return step
    
    async def _tally_votes(
        self,
        voting_steps: List[PatternStep],
        answers: List[Dict[str, str]],
        voting_method: str
    ) -> PatternStep:
        """Tally all votes."""
        step = self.create_step(
            step_id="tally",
            step_type="tally",
            description="Tally votes",
            prompt=""
        )
        
        # Count votes
        votes = []
        for voting_step in voting_steps:
            if voting_step.response:
                voted_for = self._parse_vote(voting_step.response, answers)
                votes.append(voted_for)
        
        vote_counts = Counter(votes)
        
        tally_text = "\n".join([
            f"{agent_id}: {count} vote(s)"
            for agent_id, count in vote_counts.most_common()
        ])
        
        self.complete_step(
            step,
            tally_text,
            {
                "stage": "tally",
                "vote_counts": dict(vote_counts),
                "total_votes": len(votes)
            }
        )
        
        return step
    
    async def _refine_winning_answer(
        self,
        query: str,
        winner_answer: str,
        voting_steps: List[PatternStep],
        config: Dict[str, Any]
    ) -> PatternStep:
        """Refine winning answer based on voting feedback."""
        step = self.create_step(
            step_id="refinement",
            step_type="refinement",
            description="Refine winning answer",
            prompt=self._build_refinement_prompt(
                query,
                winner_answer,
                voting_steps
            )
        )
        
        try:
            response = await self.call_llm(step.prompt, config)
            self.complete_step(
                step,
                response,
                {"stage": "refinement"}
            )
        except Exception as e:
            self.complete_step(step, f"Error: {e}", {"error": True})
        
        return step
    
    def _build_generation_prompt(
        self,
        query: str,
        context: Dict[str, Any],
        agent_num: int
    ) -> str:
        """Build prompt for independent answer generation."""
        context_str = self._format_context(context)
        
        return f"""Provide your best answer to this question.

Question: {query}

{context_str}

Instructions (Agent {agent_num}):
1. Answer independently
2. Be thorough and accurate
3. Use clear reasoning
4. This will be reviewed by other agents
5. Your answer will be voted on

Your Answer:"""
    
    def _build_voting_prompt(
        self,
        query: str,
        answers: List[Dict[str, str]],
        agent_num: int
    ) -> str:
        """Build prompt for voting."""
        # Format all answers
        answers_text = "\n\n".join([
            f"### {a['agent_id']} ###\n{a['answer'][:400]}..."
            for a in answers
        ])
        
        return f"""Vote for the BEST answer to this question.

Question: {query}

Answers to Vote On:
{answers_text}

Voting Instructions (Agent {agent_num}):
1. Evaluate each answer objectively
2. Consider: accuracy, completeness, clarity
3. Vote for ONE answer (format: "VOTE: agent_X")
4. Briefly explain your choice
5. Cannot vote for yourself if you generated one

Your Vote:"""
    
    def _build_refinement_prompt(
        self,
        query: str,
        winner_answer: str,
        voting_steps: List[PatternStep]
    ) -> str:
        """Build prompt for refining winning answer."""
        # Extract voting feedback
        feedback = []
        for step in voting_steps:
            if step.response:
                # Extract reasoning (everything except "VOTE: agent_X")
                reasoning = step.response.replace("VOTE:", "").strip()
                if len(reasoning) > 20:
                    feedback.append(reasoning[:200])
        
        feedback_text = "\n".join([f"- {f}..." for f in feedback[:3]])
        
        return f"""Refine this winning answer based on voting feedback.

Question: {query}

Winning Answer:
{winner_answer[:600]}...

Voting Feedback:
{feedback_text}

Refinement Instructions:
1. Keep the core strengths
2. Address any concerns mentioned
3. Improve clarity if needed
4. Ensure completeness
5. Polish the final version

Refined Answer:"""
    
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
    
    def _parse_vote(
        self,
        vote_text: str,
        answers: List[Dict[str, str]]
    ) -> str:
        """Parse vote from agent response."""
        if not vote_text:
            return answers[0]["agent_id"] if answers else "agent_1"
        
        text_lower = vote_text.lower()
        
        # Look for "VOTE: agent_X" pattern
        for answer in answers:
            agent_id = answer["agent_id"]
            if agent_id.lower() in text_lower:
                return agent_id
        
        # Fallback: look for numbers
        for i, answer in enumerate(answers, 1):
            if f"agent_{i}" in text_lower or f"agent {i}" in text_lower:
                return answer["agent_id"]
        
        # Default to first
        return answers[0]["agent_id"] if answers else "agent_1"
    
    def _determine_winner(
        self,
        voting_steps: List[PatternStep],
        answers: List[Dict[str, str]],
        voting_method: str
    ) -> Tuple[str, Dict[str, int]]:
        """Determine winner from votes."""
        votes = []
        for voting_step in voting_steps:
            if voting_step.response:
                voted_for = self._parse_vote(voting_step.response, answers)
                votes.append(voted_for)
        
        if not votes:
            return answers[0]["agent_id"] if answers else "agent_1", {}
        
        vote_counts = Counter(votes)
        
        # Get winner (most votes)
        winner_id = vote_counts.most_common(1)[0][0]
        
        return winner_id, dict(vote_counts)
    
    def _calculate_voting_confidence(
        self,
        vote_counts: Dict[str, int],
        num_agents: int
    ) -> float:
        """Calculate confidence based on vote distribution."""
        if not vote_counts or num_agents == 0:
            return 0.5
        
        total_votes = sum(vote_counts.values())
        if total_votes == 0:
            return 0.5
        
        # Get winner's votes
        max_votes = max(vote_counts.values())
        
        # Confidence factors:
        # 1. Vote concentration (how many agents agreed on winner)
        concentration = max_votes / total_votes
        
        # 2. Margin of victory
        sorted_counts = sorted(vote_counts.values(), reverse=True)
        if len(sorted_counts) > 1:
            margin = (sorted_counts[0] - sorted_counts[1]) / total_votes
        else:
            margin = 1.0
        
        # 3. Participation (did everyone vote?)
        participation = total_votes / max(num_agents, 1)
        
        # Combine
        confidence = (
            concentration * 0.4 +
            margin * 0.4 +
            participation * 0.2
        )
        
        return min(confidence, 1.0)

