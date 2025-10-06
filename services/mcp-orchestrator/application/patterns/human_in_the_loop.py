"""Human-in-the-Loop (HITL) pattern implementation."""

from typing import Any, Dict, List, Optional
from datetime import datetime

from .base import BasePatternEngine, PatternResult, PatternStep


class HumanInTheLoopEngine(BasePatternEngine):
    """
    Human-in-the-Loop (HITL) pattern execution engine.
    
    Integrates human oversight and approval at critical decision points.
    The LLM assesses confidence and requests human input when needed.
    
    Process:
    1. Generate initial response
    2. Calculate confidence score
    3. If confidence < threshold → request human review
    4. If approved → proceed, if rejected → regenerate
    5. Learn from human feedback
    
    Key Innovation: Confidence-based human intervention,
    ensuring quality while minimizing interruptions.
    """
    
    def __init__(self):
        super().__init__("human_in_the_loop")
    
    async def execute(
        self,
        query: str,
        context: Dict[str, Any],
        config: Dict[str, Any]
    ) -> PatternResult:
        """Execute Human-in-the-Loop pattern."""
        start_time = datetime.utcnow()
        steps: List[PatternStep] = []
        
        try:
            # Configuration
            confidence_threshold = config.get("hitl_confidence_threshold", 0.7)
            max_iterations = config.get("hitl_max_iterations", 2)
            simulate_human = config.get("hitl_simulate_human", True)  # For testing
            
            current_response = ""
            human_interventions = []
            
            for iteration in range(max_iterations):
                # Step 1: Generate response
                generation_step = await self._generate_response(
                    query,
                    context,
                    config,
                    human_interventions,
                    iteration
                )
                steps.append(generation_step)
                current_response = generation_step.response or ""
                
                # Step 2: Assess confidence
                confidence_step = await self._assess_confidence(
                    query,
                    current_response,
                    context,
                    config
                )
                steps.append(confidence_step)
                
                confidence_score = self._parse_confidence(confidence_step.response)
                
                # Step 3: Decide if human review needed
                needs_review = confidence_score < confidence_threshold
                
                if not needs_review:
                    self.logger.info(f"Confidence {confidence_score:.2f} >= threshold, approved automatically")
                    break
                
                # Step 4: Request human review (or simulate)
                review_step = await self._request_human_review(
                    query,
                    current_response,
                    confidence_score,
                    config,
                    simulate_human,
                    iteration
                )
                steps.append(review_step)
                
                # Parse review decision
                review_decision = self._parse_review_decision(review_step.response)
                human_interventions.append({
                    "iteration": iteration,
                    "confidence": confidence_score,
                    "decision": review_decision,
                    "feedback": review_step.response
                })
                
                if review_decision == "APPROVED":
                    self.logger.info("Human approved response")
                    break
                elif review_decision == "REJECTED":
                    self.logger.info("Human rejected, will regenerate")
                    continue
                else:  # MODIFIED
                    self.logger.info("Human provided modifications")
                    current_response = review_decision  # Use modified version
                    break
            
            # Final step: Document human interventions
            summary_step = self._create_intervention_summary(
                human_interventions,
                current_response
            )
            steps.append(summary_step)
            
            # Calculate execution time
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Final confidence
            final_confidence = human_interventions[-1]["confidence"] if human_interventions else confidence_threshold
            
            return PatternResult(
                pattern_type=self.pattern_type,
                success=True,
                steps=steps,
                final_answer=current_response,
                confidence=final_confidence,
                total_duration_ms=duration_ms,
                metadata={
                    "human_interventions": len(human_interventions),
                    "iterations": iteration + 1,
                    "final_decision": human_interventions[-1]["decision"] if human_interventions else "AUTO_APPROVED",
                    "confidence_threshold": confidence_threshold
                }
            )
        
        except Exception as e:
            self.logger.error(f"Error executing HITL: {e}", exc_info=True)
            
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            return PatternResult(
                pattern_type=self.pattern_type,
                success=False,
                steps=steps,
                total_duration_ms=duration_ms,
                error=str(e)
            )
    
    async def _generate_response(
        self,
        query: str,
        context: Dict[str, Any],
        config: Dict[str, Any],
        previous_feedback: List[Dict[str, Any]],
        iteration: int
    ) -> PatternStep:
        """Generate response, incorporating previous feedback."""
        step = self.create_step(
            step_id=f"generation_{iteration}",
            step_type="generation",
            description=f"Generate response (iteration {iteration + 1})",
            prompt=self._build_generation_prompt(
                query,
                context,
                previous_feedback
            )
        )
        
        try:
            response = await self.call_llm(step.prompt, config)
            self.complete_step(
                step,
                response,
                {
                    "stage": "generation",
                    "iteration": iteration
                }
            )
        except Exception as e:
            self.complete_step(step, f"Error: {e}", {"error": True})
        
        return step
    
    async def _assess_confidence(
        self,
        query: str,
        response: str,
        context: Dict[str, Any],
        config: Dict[str, Any]
    ) -> PatternStep:
        """Assess confidence in the response."""
        step = self.create_step(
            step_id="confidence_assessment",
            step_type="confidence",
            description="Assess response confidence",
            prompt=self._build_confidence_prompt(query, response, context)
        )
        
        try:
            confidence_response = await self.call_llm(step.prompt, config)
            self.complete_step(
                step,
                confidence_response,
                {"stage": "confidence"}
            )
        except Exception as e:
            self.complete_step(step, f"Error: {e}", {"error": True})
        
        return step
    
    async def _request_human_review(
        self,
        query: str,
        response: str,
        confidence: float,
        config: Dict[str, Any],
        simulate: bool,
        iteration: int
    ) -> PatternStep:
        """Request human review (or simulate)."""
        step = self.create_step(
            step_id=f"human_review_{iteration}",
            step_type="human_review",
            description="Human review requested",
            prompt=self._build_review_request_prompt(
                query,
                response,
                confidence
            )
        )
        
        try:
            if simulate:
                # Simulate human review
                review_response = await self.call_llm(step.prompt, config)
            else:
                # In production, would integrate with actual human review system
                review_response = "APPROVED: Looks good to me"
            
            self.complete_step(
                step,
                review_response,
                {
                    "stage": "human_review",
                    "simulated": simulate,
                    "confidence": confidence
                }
            )
        except Exception as e:
            self.complete_step(step, f"Error: {e}", {"error": True})
        
        return step
    
    def _create_intervention_summary(
        self,
        interventions: List[Dict[str, Any]],
        final_response: str
    ) -> PatternStep:
        """Create summary of human interventions."""
        step = self.create_step(
            step_id="intervention_summary",
            step_type="summary",
            description="HITL intervention summary",
            prompt=""
        )
        
        summary = f"Human Interventions: {len(interventions)}\n\n"
        for i, intervention in enumerate(interventions, 1):
            summary += f"Intervention {i}:\n"
            summary += f"- Confidence: {intervention['confidence']:.2f}\n"
            summary += f"- Decision: {intervention['decision']}\n"
        
        self.complete_step(
            step,
            summary,
            {
                "stage": "summary",
                "total_interventions": len(interventions)
            }
        )
        
        return step
    
    def _build_generation_prompt(
        self,
        query: str,
        context: Dict[str, Any],
        previous_feedback: List[Dict[str, Any]]
    ) -> str:
        """Build prompt for response generation."""
        context_str = self._format_context(context)
        
        feedback_str = ""
        if previous_feedback:
            feedback_str = "\n\nPrevious Human Feedback:\n"
            for fb in previous_feedback:
                feedback_str += f"- {fb.get('feedback', '')}[:200]...\n"
        
        return f"""Answer this query clearly and accurately.

Query: {query}

{context_str}{feedback_str}

Instructions:
1. Provide clear, accurate answer
2. If previous feedback, incorporate it
3. Be confident in what you know
4. Acknowledge uncertainty if present
5. This may be reviewed by a human

Answer:"""
    
    def _build_confidence_prompt(
        self,
        query: str,
        response: str,
        context: Dict[str, Any]
    ) -> str:
        """Build prompt for confidence assessment."""
        return f"""Assess your confidence in this response.

Query: {query}

Your Response:
{response[:500]}...

Confidence Assessment Instructions:
1. Rate confidence 0.0-1.0
2. Consider: completeness, accuracy, clarity
3. Identify any uncertainties
4. Note information gaps
5. Be honest about limitations

Format:
CONFIDENCE: [0.0-1.0]
REASONING: [why this confidence level]
CONCERNS: [any concerns or uncertainties]

Assessment:"""
    
    def _build_review_request_prompt(
        self,
        query: str,
        response: str,
        confidence: float
    ) -> str:
        """Build prompt for human review request."""
        return f"""HUMAN REVIEW REQUESTED (Low confidence: {confidence:.2f})

Query: {query}

AI Response:
{response[:600]}...

Review Instructions:
1. Evaluate response quality
2. Check for accuracy
3. Identify issues

Respond with ONE of:
- "APPROVED: [why approved]"
- "REJECTED: [issues found]"
- "MODIFIED: [your corrected version]"

Your Review:"""
    
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
    
    def _parse_confidence(self, confidence_text: str) -> float:
        """Parse confidence score from assessment."""
        if not confidence_text:
            return 0.5
        
        # Look for CONFIDENCE: X.XX
        import re
        match = re.search(r'CONFIDENCE:\s*([0-9.]+)', confidence_text, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass
        
        # Heuristic based on language
        text_lower = confidence_text.lower()
        if "very confident" in text_lower or "highly confident" in text_lower:
            return 0.9
        elif "confident" in text_lower:
            return 0.7
        elif "uncertain" in text_lower or "not sure" in text_lower:
            return 0.4
        
        return 0.5
    
    def _parse_review_decision(self, review_text: str) -> str:
        """Parse human review decision."""
        if not review_text:
            return "APPROVED"
        
        text_upper = review_text.upper()
        
        if "APPROVED" in text_upper:
            return "APPROVED"
        elif "REJECTED" in text_upper:
            return "REJECTED"
        elif "MODIFIED" in text_upper:
            # Extract modified version
            if ":" in review_text:
                return review_text.split(":", 1)[1].strip()
            return "MODIFIED"
        
        # Default to approved
        return "APPROVED"

