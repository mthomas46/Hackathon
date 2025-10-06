"""Constitutional AI pattern implementation."""

from typing import Any, Dict, List, Optional
from datetime import datetime

from .base import BasePatternEngine, PatternResult, PatternStep


# Default constitutional principles
DEFAULT_CONSTITUTION = [
    {
        "id": "helpful",
        "principle": "Be helpful, harmless, and honest",
        "description": "Provide useful information while avoiding harm and being truthful"
    },
    {
        "id": "accurate",
        "principle": "Prioritize accuracy over speculation",
        "description": "Base responses on facts, acknowledge uncertainty when present"
    },
    {
        "id": "respectful",
        "principle": "Treat all individuals and groups with respect",
        "description": "Avoid bias, discrimination, or disrespectful language"
    },
    {
        "id": "safe",
        "principle": "Do not provide harmful or dangerous information",
        "description": "Refuse requests that could lead to harm"
    },
    {
        "id": "transparent",
        "principle": "Be transparent about limitations and uncertainty",
        "description": "Clearly communicate when uncertain or lacking information"
    },
    {
        "id": "privacy",
        "principle": "Respect privacy and confidentiality",
        "description": "Do not request or share personal/confidential information inappropriately"
    }
]


class ConstitutionalAIEngine(BasePatternEngine):
    """
    Constitutional AI pattern execution engine.
    
    Implements Constitutional AI principles to ensure value-aligned,
    ethical responses. The model generates an answer, evaluates it
    against a set of constitutional principles, and revises as needed.
    
    Process:
    1. Generate initial response
    2. Evaluate against constitutional principles
    3. Identify violations or concerns
    4. Revise response to align with principles
    5. Repeat until constitutional
    
    Reference: "Constitutional AI: Harmlessness from AI Feedback"
    Anthropic (2022)
    
    Key Innovation: Self-governance through explicit principles
    rather than external human feedback.
    """
    
    def __init__(self):
        super().__init__("constitutional_ai")
        self.constitution = DEFAULT_CONSTITUTION
    
    async def execute(
        self,
        query: str,
        context: Dict[str, Any],
        config: Dict[str, Any]
    ) -> PatternResult:
        """Execute Constitutional AI pattern."""
        start_time = datetime.utcnow()
        steps: List[PatternStep] = []
        
        try:
            # Configuration
            max_iterations = config.get("constitutional_max_iterations", 3)
            custom_constitution = config.get("constitutional_principles")
            if custom_constitution:
                self.constitution = custom_constitution
            
            # Step 1: Generate initial response
            generation_step = await self._generate_initial_response(
                query,
                context,
                config
            )
            steps.append(generation_step)
            
            current_response = generation_step.response
            all_violations = []
            
            # Iterative constitutional checking and revision
            for iteration in range(max_iterations):
                # Step 2: Evaluate against constitution
                evaluation_step = await self._evaluate_constitutionality(
                    query,
                    current_response,
                    context,
                    config,
                    iteration
                )
                steps.append(evaluation_step)
                
                # Extract violations
                violations = self._extract_violations(evaluation_step)
                all_violations.extend(violations)
                
                # If no violations, we're done
                if not violations:
                    self.logger.info(f"Constitutional compliance achieved at iteration {iteration}")
                    break
                
                # Step 3: Revise to address violations
                revision_step = await self._revise_for_constitution(
                    query,
                    current_response,
                    violations,
                    context,
                    config,
                    iteration
                )
                steps.append(revision_step)
                
                # Update current response
                current_response = revision_step.response or current_response
            
            # Step 4: Final constitutional check
            final_check_step = await self._final_constitutional_check(
                query,
                current_response,
                context,
                config
            )
            steps.append(final_check_step)
            
            # Calculate execution time
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Calculate confidence
            confidence = self._calculate_constitutional_confidence(
                steps,
                all_violations
            )
            
            # Check if constitutional
            is_constitutional = len(self._extract_violations(final_check_step)) == 0
            
            return PatternResult(
                pattern_type=self.pattern_type,
                success=True,
                steps=steps,
                final_answer=current_response,
                confidence=confidence,
                total_duration_ms=duration_ms,
                metadata={
                    "is_constitutional": is_constitutional,
                    "iterations": len([s for s in steps if s.step_type == "evaluation"]),
                    "total_violations_found": len(all_violations),
                    "final_violations": self._extract_violations(final_check_step),
                    "principles_checked": [p["id"] for p in self.constitution]
                }
            )
        
        except Exception as e:
            self.logger.error(f"Error executing Constitutional AI: {e}", exc_info=True)
            
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            return PatternResult(
                pattern_type=self.pattern_type,
                success=False,
                steps=steps,
                total_duration_ms=duration_ms,
                error=str(e)
            )
    
    async def _generate_initial_response(
        self,
        query: str,
        context: Dict[str, Any],
        config: Dict[str, Any]
    ) -> PatternStep:
        """Generate initial response."""
        step = self.create_step(
            step_id="initial_generation",
            step_type="generation",
            description="Generate initial response",
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
    
    async def _evaluate_constitutionality(
        self,
        query: str,
        response: str,
        context: Dict[str, Any],
        config: Dict[str, Any],
        iteration: int
    ) -> PatternStep:
        """Evaluate response against constitutional principles."""
        step = self.create_step(
            step_id=f"evaluation_{iteration}",
            step_type="evaluation",
            description=f"Evaluate constitutionality (iteration {iteration + 1})",
            prompt=self._build_evaluation_prompt(query, response)
        )
        
        try:
            response_text = await self.call_llm(step.prompt, config)
            self.complete_step(
                step,
                response_text,
                {
                    "stage": "evaluation",
                    "iteration": iteration
                }
            )
        except Exception as e:
            self.complete_step(step, f"Error: {e}", {"error": True})
        
        return step
    
    async def _revise_for_constitution(
        self,
        query: str,
        current_response: str,
        violations: List[Dict[str, str]],
        context: Dict[str, Any],
        config: Dict[str, Any],
        iteration: int
    ) -> PatternStep:
        """Revise response to address constitutional violations."""
        step = self.create_step(
            step_id=f"revision_{iteration}",
            step_type="revision",
            description=f"Revise for constitution (iteration {iteration + 1})",
            prompt=self._build_revision_prompt(
                query,
                current_response,
                violations
            )
        )
        
        try:
            response = await self.call_llm(step.prompt, config)
            self.complete_step(
                step,
                response,
                {
                    "stage": "revision",
                    "iteration": iteration,
                    "violations_addressed": len(violations)
                }
            )
        except Exception as e:
            self.complete_step(step, f"Error: {e}", {"error": True})
        
        return step
    
    async def _final_constitutional_check(
        self,
        query: str,
        final_response: str,
        context: Dict[str, Any],
        config: Dict[str, Any]
    ) -> PatternStep:
        """Perform final constitutional check."""
        step = self.create_step(
            step_id="final_check",
            step_type="final_check",
            description="Final constitutional verification",
            prompt=self._build_final_check_prompt(query, final_response)
        )
        
        try:
            response = await self.call_llm(step.prompt, config)
            
            # Check if constitutional
            is_constitutional = self._is_constitutional(response)
            
            self.complete_step(
                step,
                response,
                {
                    "stage": "final_check",
                    "is_constitutional": is_constitutional
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
        
        return f"""Provide an answer to this query.

Query: {query}

{context_str}

Instructions:
1. Answer directly and completely
2. Be helpful and informative
3. This will be checked for alignment with ethical principles
4. Be accurate and honest

Answer:"""
    
    def _build_evaluation_prompt(
        self,
        query: str,
        response: str
    ) -> str:
        """Build prompt for constitutional evaluation."""
        # Format constitution
        constitution_str = "\n".join([
            f"{i+1}. {p['principle']}: {p['description']}"
            for i, p in enumerate(self.constitution)
        ])
        
        return f"""Evaluate this response against constitutional principles.

Original Query: {query}

Response to Evaluate:
{response[:800]}...

Constitutional Principles:
{constitution_str}

Evaluation Instructions:
1. Check response against EACH principle
2. Identify any violations or concerns
3. Note degree of violation (minor/major)
4. Provide specific examples
5. If fully compliant, state "CONSTITUTIONAL"
6. Be thorough but fair

Format your evaluation as:
- Principle [ID]: [PASS/CONCERN/VIOLATION]
- Issue: [specific issue if any]
- Example: [quote from response if violation]

Evaluation:"""
    
    def _build_revision_prompt(
        self,
        query: str,
        current_response: str,
        violations: List[Dict[str, str]]
    ) -> str:
        """Build prompt for constitutional revision."""
        violations_str = "\n".join([
            f"- {v['principle']}: {v['issue']}"
            for v in violations
        ])
        
        return f"""Revise this response to address constitutional violations.

Original Query: {query}

Current Response:
{current_response[:700]}...

Constitutional Violations to Address:
{violations_str}

Revision Instructions:
1. Maintain the helpful core of the response
2. Remove or revise violating content
3. Ensure alignment with all principles
4. Keep the response useful
5. Do not be overly cautious
6. Be clear and direct

Revised Response:"""
    
    def _build_final_check_prompt(
        self,
        query: str,
        final_response: str
    ) -> str:
        """Build prompt for final constitutional check."""
        constitution_str = "\n".join([
            f"{i+1}. {p['principle']}"
            for i, p in enumerate(self.constitution)
        ])
        
        return f"""Perform a final constitutional check on this response.

Original Query: {query}

Final Response:
{final_response[:800]}...

Constitutional Principles:
{constitution_str}

Final Check Instructions:
1. Verify compliance with all principles
2. Confirm no violations remain
3. If compliant, respond "CONSTITUTIONAL - APPROVED"
4. If concerns remain, list them clearly
5. Be definitive

Final Check:"""
    
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
    
    def _extract_violations(self, evaluation_step: PatternStep) -> List[Dict[str, str]]:
        """Extract violations from evaluation step."""
        if not evaluation_step or not evaluation_step.response:
            return []
        
        response = evaluation_step.response
        violations = []
        
        # Parse evaluation for violations
        lines = response.lower().split('\n')
        current_principle = None
        current_issue = None
        
        for line in lines:
            # Look for principle evaluations
            if 'violation' in line or 'concern' in line:
                # Extract principle and issue
                for principle in self.constitution:
                    if principle['id'].lower() in line:
                        current_principle = principle['principle']
                        # Try to extract issue description
                        if ':' in line:
                            current_issue = line.split(':', 1)[1].strip()
                        else:
                            current_issue = "Violation detected"
                        
                        violations.append({
                            "principle": current_principle,
                            "issue": current_issue
                        })
                        break
        
        return violations
    
    def _is_constitutional(self, check_response: str) -> bool:
        """Determine if response is constitutional from check text."""
        if not check_response:
            return False
        
        text_lower = check_response.lower()
        
        # Strong positive indicators
        if "constitutional - approved" in text_lower:
            return True
        if "fully compliant" in text_lower:
            return True
        if "no violations" in text_lower and "all principles" in text_lower:
            return True
        
        # Strong negative indicators
        if "violation" in text_lower:
            return False
        if "concern" in text_lower and "major" in text_lower:
            return False
        
        # Default to true if checks passed
        return "constitutional" in text_lower
    
    def _calculate_constitutional_confidence(
        self,
        steps: List[PatternStep],
        all_violations: List[Dict[str, str]]
    ) -> float:
        """Calculate confidence based on constitutional alignment."""
        if not steps:
            return 0.0
        
        # Factors:
        # 1. Final check passed
        final_check = next(
            (s for s in reversed(steps) if s.step_type == "final_check"),
            None
        )
        if final_check:
            is_constitutional = final_check.metadata.get("is_constitutional", False)
            constitutional_factor = 1.0 if is_constitutional else 0.3
        else:
            constitutional_factor = 0.5
        
        # 2. Number of violations found (fewer is better)
        total_violations = len(all_violations)
        if total_violations == 0:
            violation_factor = 1.0
        elif total_violations == 1:
            violation_factor = 0.7
        elif total_violations == 2:
            violation_factor = 0.5
        else:
            violation_factor = 0.3
        
        # 3. Number of revisions needed (fewer is better)
        revisions = len([s for s in steps if s.step_type == "revision"])
        if revisions == 0:
            revision_factor = 1.0
        elif revisions == 1:
            revision_factor = 0.8
        elif revisions == 2:
            revision_factor = 0.6
        else:
            revision_factor = 0.4
        
        # Combine
        confidence = (
            constitutional_factor * 0.5 +
            violation_factor * 0.3 +
            revision_factor * 0.2
        )
        
        return min(confidence, 1.0)

