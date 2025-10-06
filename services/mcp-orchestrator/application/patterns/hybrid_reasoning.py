"""Hybrid Reasoning pattern implementation."""

from typing import Any, Dict, List, Optional
from datetime import datetime
import asyncio

from .base import BasePatternEngine, PatternResult, PatternStep


class HybridReasoningEngine(BasePatternEngine):
    """
    Hybrid Reasoning pattern execution engine.
    
    Combines multiple reasoning approaches (symbolic, neural,
    retrieval, etc.) to leverage strengths of each for robust,
    comprehensive problem-solving.
    
    Process:
    1. Decompose problem by reasoning type
    2. Apply appropriate reasoning method to each
    3. Execute reasoning approaches in parallel
    4. Synthesize results
    5. Validate hybrid solution
    
    Key Innovation: Multi-method reasoning that combines
    symbolic logic, neural inference, and retrieval for
    more robust and comprehensive answers.
    """
    
    def __init__(self):
        super().__init__("hybrid_reasoning")
    
    async def execute(
        self,
        query: str,
        context: Dict[str, Any],
        config: Dict[str, Any]
    ) -> PatternResult:
        """Execute Hybrid Reasoning pattern."""
        start_time = datetime.utcnow()
        steps: List[PatternStep] = []
        
        try:
            # Step 1: Decompose by reasoning type
            decomposition_step = await self._decompose_by_reasoning_type(
                query,
                context,
                config
            )
            steps.append(decomposition_step)
            
            # Parse reasoning components
            components = self._parse_components(decomposition_step.response)
            
            # Step 2: Execute reasoning approaches in parallel
            reasoning_steps = await self._execute_reasoning_methods(
                components,
                query,
                context,
                config
            )
            steps.extend(reasoning_steps)
            
            # Step 3: Synthesize results
            synthesis_step = await self._synthesize_hybrid_results(
                query,
                components,
                reasoning_steps,
                config
            )
            steps.append(synthesis_step)
            
            # Step 4: Validate hybrid solution
            validation_step = await self._validate_hybrid_solution(
                query,
                synthesis_step.response,
                reasoning_steps,
                config
            )
            steps.append(validation_step)
            
            # Calculate execution time
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Calculate confidence
            confidence = self._calculate_hybrid_confidence(
                reasoning_steps,
                validation_step
            )
            
            return PatternResult(
                pattern_type=self.pattern_type,
                success=True,
                steps=steps,
                final_answer=synthesis_step.response,
                confidence=confidence,
                total_duration_ms=duration_ms,
                metadata={
                    "reasoning_methods": list(components.keys()),
                    "method_count": len(components),
                    "validation_passed": validation_step.metadata.get("is_valid", False)
                }
            )
        
        except Exception as e:
            self.logger.error(f"Error executing Hybrid Reasoning: {e}", exc_info=True)
            
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            return PatternResult(
                pattern_type=self.pattern_type,
                success=False,
                steps=steps,
                total_duration_ms=duration_ms,
                error=str(e)
            )
    
    async def _decompose_by_reasoning_type(
        self,
        query: str,
        context: Dict[str, Any],
        config: Dict[str, Any]
    ) -> PatternStep:
        """Decompose problem by reasoning type needed."""
        step = self.create_step(
            step_id="decomposition",
            step_type="decomposition",
            description="Decompose by reasoning type",
            prompt=self._build_decomposition_prompt(query, context)
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
    
    async def _execute_reasoning_methods(
        self,
        components: Dict[str, str],
        query: str,
        context: Dict[str, Any],
        config: Dict[str, Any]
    ) -> List[PatternStep]:
        """Execute different reasoning methods in parallel."""
        tasks = []
        
        for method, component in components.items():
            step = self.create_step(
                step_id=f"reasoning_{method}",
                step_type="reasoning",
                description=f"{method} reasoning",
                prompt=self._build_reasoning_prompt(method, component, query, context)
            )
            tasks.append(self._execute_reasoning_step(step, config))
        
        # Execute in parallel
        steps = await asyncio.gather(*tasks)
        return list(steps)
    
    async def _execute_reasoning_step(
        self,
        step: PatternStep,
        config: Dict[str, Any]
    ) -> PatternStep:
        """Execute a single reasoning step."""
        try:
            response = await self.call_llm(step.prompt, config)
            self.complete_step(
                step,
                response,
                {"stage": "reasoning"}
            )
        except Exception as e:
            self.complete_step(step, f"Error: {e}", {"error": True})
        
        return step
    
    async def _synthesize_hybrid_results(
        self,
        query: str,
        components: Dict[str, str],
        reasoning_steps: List[PatternStep],
        config: Dict[str, Any]
    ) -> PatternStep:
        """Synthesize results from multiple reasoning methods."""
        step = self.create_step(
            step_id="synthesis",
            step_type="synthesis",
            description="Synthesize hybrid results",
            prompt=self._build_synthesis_prompt(query, components, reasoning_steps)
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
    
    async def _validate_hybrid_solution(
        self,
        query: str,
        solution: str,
        reasoning_steps: List[PatternStep],
        config: Dict[str, Any]
    ) -> PatternStep:
        """Validate the hybrid solution."""
        step = self.create_step(
            step_id="validation",
            step_type="validation",
            description="Validate hybrid solution",
            prompt=self._build_validation_prompt(query, solution, reasoning_steps)
        )
        
        try:
            response = await self.call_llm(step.prompt, config)
            is_valid = self._parse_validation(response)
            
            self.complete_step(
                step,
                response,
                {
                    "stage": "validation",
                    "is_valid": is_valid
                }
            )
        except Exception as e:
            self.complete_step(step, f"Error: {e}", {"error": True})
        
        return step
    
    def _build_decomposition_prompt(
        self,
        query: str,
        context: Dict[str, Any]
    ) -> str:
        """Build prompt for decomposition."""
        return f"""Decompose this problem by reasoning type needed.

Query: {query}

Reasoning Types:
1. Symbolic: Logical deduction, rules, formulas
2. Neural: Pattern recognition, intuition, analogies
3. Retrieval: Fact lookup, knowledge retrieval
4. Causal: Cause-effect relationships
5. Probabilistic: Uncertainty, likelihood

Decomposition Instructions:
1. Identify which reasoning types apply
2. Assign problem components to types
3. Be specific about what each handles

Format:
- Symbolic: [component needing logical reasoning]
- Neural: [component needing pattern recognition]
- Retrieval: [component needing facts]
- Causal: [component needing cause-effect]
- Probabilistic: [component needing uncertainty handling]

Reasoning Decomposition:"""
    
    def _build_reasoning_prompt(
        self,
        method: str,
        component: str,
        query: str,
        context: Dict[str, Any]
    ) -> str:
        """Build prompt for specific reasoning method."""
        context_str = context.get("mcp_data", "")[:300]
        
        if method == "symbolic":
            return f"""Apply symbolic/logical reasoning to this component.

Original Query: {query}

Component: {component}

Context:
{context_str}...

Symbolic Reasoning Instructions:
1. Apply formal logic
2. Use deductive reasoning
3. Apply rules and formulas
4. Logical step-by-step
5. Precise conclusions

Symbolic Reasoning Result:"""
        
        elif method == "neural":
            return f"""Apply neural/intuitive reasoning to this component.

Original Query: {query}

Component: {component}

Context:
{context_str}...

Neural Reasoning Instructions:
1. Pattern recognition
2. Analogical reasoning
3. Intuitive insights
4. Holistic understanding
5. Creative connections

Neural Reasoning Result:"""
        
        elif method == "retrieval":
            return f"""Apply retrieval-based reasoning to this component.

Original Query: {query}

Component: {component}

Context:
{context_str}...

Retrieval Reasoning Instructions:
1. Extract relevant facts
2. Retrieve specific information
3. Ground in knowledge
4. Cite sources
5. Factual answers

Retrieval Reasoning Result:"""
        
        elif method == "causal":
            return f"""Apply causal reasoning to this component.

Original Query: {query}

Component: {component}

Causal Reasoning Instructions:
1. Identify causes
2. Trace effects
3. Causal chains
4. Mechanisms
5. Explanations

Causal Reasoning Result:"""
        
        else:  # probabilistic
            return f"""Apply probabilistic reasoning to this component.

Original Query: {query}

Component: {component}

Probabilistic Reasoning Instructions:
1. Assess uncertainty
2. Estimate probabilities
3. Handle ambiguity
4. Risk analysis
5. Confidence intervals

Probabilistic Reasoning Result:"""
    
    def _build_synthesis_prompt(
        self,
        query: str,
        components: Dict[str, str],
        reasoning_steps: List[PatternStep]
    ) -> str:
        """Build prompt for synthesis."""
        results_str = "\n\n".join([
            f"=== {step.step_id} ===\n{step.response[:300]}..."
            for step in reasoning_steps
            if step.response
        ])
        
        return f"""Synthesize results from multiple reasoning methods.

Original Query: {query}

Reasoning Results:
{results_str}

Synthesis Instructions:
1. Integrate all reasoning approaches
2. Combine strengths of each
3. Resolve any conflicts
4. Create unified answer
5. Acknowledge method contributions

Format:
- Answer: [synthesized answer]
- Methods Used: [list]
- Key Insights: [from each method]

Hybrid Synthesis:"""
    
    def _build_validation_prompt(
        self,
        query: str,
        solution: str,
        reasoning_steps: List[PatternStep]
    ) -> str:
        """Build prompt for validation."""
        return f"""Validate this hybrid reasoning solution.

Original Query: {query}

Hybrid Solution:
{solution[:600]}...

Validation Instructions:
1. Check logical consistency
2. Verify factual grounding
3. Assess completeness
4. Validate reasoning paths
5. Respond "VALID" or "INVALID: [reason]"

Validation:"""
    
    def _parse_components(self, decomposition_text: str) -> Dict[str, str]:
        """Parse reasoning components from decomposition."""
        if not decomposition_text:
            return {"neural": "general reasoning"}
        
        components = {}
        methods = ["symbolic", "neural", "retrieval", "causal", "probabilistic"]
        
        lines = decomposition_text.split('\n')
        for line in lines:
            for method in methods:
                if method in line.lower() and ':' in line:
                    component = line.split(':', 1)[1].strip()
                    if len(component) > 10:
                        components[method] = component
        
        # Ensure at least one method
        if not components:
            components["neural"] = "Apply general reasoning"
        
        return components
    
    def _parse_validation(self, validation_text: str) -> bool:
        """Parse validation result."""
        if not validation_text:
            return False
        
        text_lower = validation_text.lower()
        return "valid" in text_lower and "invalid" not in text_lower
    
    def _calculate_hybrid_confidence(
        self,
        reasoning_steps: List[PatternStep],
        validation_step: PatternStep
    ) -> float:
        """Calculate confidence for hybrid reasoning."""
        if not reasoning_steps:
            return 0.5
        
        # Factors:
        # 1. Number of reasoning methods used
        methods_count = len([s for s in reasoning_steps if s.response])
        method_factor = min(methods_count / 3, 1.0)
        
        # 2. Validation passed
        is_valid = validation_step.metadata.get("is_valid", False) if validation_step else False
        validation_factor = 1.0 if is_valid else 0.5
        
        # Combine
        confidence = (
            method_factor * 0.4 +
            validation_factor * 0.6
        )
        
        return min(confidence, 0.95)

