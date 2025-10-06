"""Adaptive Pattern Selection implementation."""

from typing import Any, Dict, List, Optional
from datetime import datetime

from .base import BasePatternEngine, PatternResult, PatternStep


class AdaptiveSelectionEngine(BasePatternEngine):
    """
    Adaptive Pattern Selection execution engine.
    
    Meta-pattern that intelligently selects the best pattern
    for a given query based on query characteristics, context,
    and performance requirements.
    
    Process:
    1. Analyze query characteristics
    2. Assess available resources/constraints
    3. Rank candidate patterns
    4. Select optimal pattern
    5. Execute selected pattern
    
    Key Innovation: Dynamic pattern selection based on
    query properties and constraints for optimal results.
    """
    
    def __init__(self):
        super().__init__("adaptive_selection")
    
    async def execute(
        self,
        query: str,
        context: Dict[str, Any],
        config: Dict[str, Any]
    ) -> PatternResult:
        """Execute Adaptive Pattern Selection."""
        start_time = datetime.utcnow()
        steps: List[PatternStep] = []
        
        try:
            # Step 1: Analyze query characteristics
            analysis_step = await self._analyze_query(
                query,
                context,
                config
            )
            steps.append(analysis_step)
            
            # Parse query characteristics
            characteristics = self._parse_characteristics(analysis_step.response)
            
            # Step 2: Assess constraints
            constraints_step = self._assess_constraints(
                config,
                context
            )
            steps.append(constraints_step)
            
            # Step 3: Rank candidate patterns
            ranking_step = await self._rank_patterns(
                query,
                characteristics,
                constraints_step.metadata,
                config
            )
            steps.append(ranking_step)
            
            # Step 4: Select optimal pattern
            selected_pattern = self._select_pattern(ranking_step.response)
            
            selection_step = self.create_step(
                step_id="selection",
                step_type="selection",
                description=f"Selected pattern: {selected_pattern}",
                prompt=""
            )
            self.complete_step(
                selection_step,
                f"Selected pattern: {selected_pattern} based on analysis",
                {
                    "stage": "selection",
                    "selected_pattern": selected_pattern,
                    "characteristics": characteristics
                }
            )
            steps.append(selection_step)
            
            # Step 5: Simulate execution (in production, would actually execute)
            execution_step = await self._simulate_pattern_execution(
                selected_pattern,
                query,
                context,
                config
            )
            steps.append(execution_step)
            
            # Calculate execution time
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Confidence based on pattern selection confidence
            confidence = self._calculate_selection_confidence(
                ranking_step,
                characteristics
            )
            
            return PatternResult(
                pattern_type=self.pattern_type,
                success=True,
                steps=steps,
                final_answer=execution_step.response,
                confidence=confidence,
                total_duration_ms=duration_ms,
                metadata={
                    "selected_pattern": selected_pattern,
                    "query_characteristics": characteristics,
                    "constraints": constraints_step.metadata,
                    "candidate_patterns": self._parse_candidates(ranking_step.response)
                }
            )
        
        except Exception as e:
            self.logger.error(f"Error executing Adaptive Selection: {e}", exc_info=True)
            
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            return PatternResult(
                pattern_type=self.pattern_type,
                success=False,
                steps=steps,
                total_duration_ms=duration_ms,
                error=str(e)
            )
    
    async def _analyze_query(
        self,
        query: str,
        context: Dict[str, Any],
        config: Dict[str, Any]
    ) -> PatternStep:
        """Analyze query characteristics."""
        step = self.create_step(
            step_id="analysis",
            step_type="analysis",
            description="Analyze query",
            prompt=self._build_analysis_prompt(query, context)
        )
        
        try:
            response = await self.call_llm(step.prompt, config)
            self.complete_step(
                step,
                response,
                {"stage": "analysis"}
            )
        except Exception as e:
            self.complete_step(step, f"Error: {e}", {"error": True})
        
        return step
    
    def _assess_constraints(
        self,
        config: Dict[str, Any],
        context: Dict[str, Any]
    ) -> PatternStep:
        """Assess available resources and constraints."""
        step = self.create_step(
            step_id="constraints",
            step_type="constraints",
            description="Assess constraints",
            prompt=""
        )
        
        # Parse constraints from config
        latency_constraint = config.get("max_latency_ms", 60000)
        budget_constraint = config.get("max_llm_calls", 10)
        quality_requirement = config.get("min_quality", "medium")
        
        constraints = {
            "max_latency_ms": latency_constraint,
            "max_llm_calls": budget_constraint,
            "min_quality": quality_requirement,
            "context_size": len(context.get("mcp_data", ""))
        }
        
        self.complete_step(
            step,
            f"Constraints: max_latency={latency_constraint}ms, max_calls={budget_constraint}, quality={quality_requirement}",
            constraints
        )
        
        return step
    
    async def _rank_patterns(
        self,
        query: str,
        characteristics: Dict[str, Any],
        constraints: Dict[str, Any],
        config: Dict[str, Any]
    ) -> PatternStep:
        """Rank candidate patterns."""
        step = self.create_step(
            step_id="ranking",
            step_type="ranking",
            description="Rank patterns",
            prompt=self._build_ranking_prompt(
                query,
                characteristics,
                constraints
            )
        )
        
        try:
            response = await self.call_llm(step.prompt, config)
            self.complete_step(
                step,
                response,
                {"stage": "ranking"}
            )
        except Exception as e:
            self.complete_step(step, f"Error: {e}", {"error": True})
        
        return step
    
    async def _simulate_pattern_execution(
        self,
        pattern: str,
        query: str,
        context: Dict[str, Any],
        config: Dict[str, Any]
    ) -> PatternStep:
        """Simulate execution of selected pattern."""
        step = self.create_step(
            step_id="execution",
            step_type="execution",
            description=f"Execute {pattern}",
            prompt=self._build_execution_prompt(pattern, query, context)
        )
        
        try:
            response = await self.call_llm(step.prompt, config)
            self.complete_step(
                step,
                response,
                {
                    "stage": "execution",
                    "pattern": pattern
                }
            )
        except Exception as e:
            self.complete_step(step, f"Error: {e}", {"error": True})
        
        return step
    
    def _build_analysis_prompt(
        self,
        query: str,
        context: Dict[str, Any]
    ) -> str:
        """Build prompt for query analysis."""
        return f"""Analyze this query to determine its characteristics.

Query: {query}

Analysis Categories:
1. Complexity: simple/medium/complex
2. Type: factual/analytical/creative/strategic
3. Requirements: accuracy/speed/depth/breadth
4. Uncertainty: low/medium/high
5. Multi-step: yes/no

Provide analysis in format:
- Complexity: [value]
- Type: [value]
- Requirements: [value]
- Uncertainty: [value]
- Multi-step: [yes/no]

Query Analysis:"""
    
    def _build_ranking_prompt(
        self,
        query: str,
        characteristics: Dict[str, Any],
        constraints: Dict[str, Any]
    ) -> str:
        """Build prompt for pattern ranking."""
        return f"""Rank these AI patterns for the given query and constraints.

Query: {query}

Characteristics:
- Complexity: {characteristics.get('complexity', 'medium')}
- Type: {characteristics.get('type', 'analytical')}
- Requirements: {characteristics.get('requirements', 'accuracy')}

Constraints:
- Max Latency: {constraints.get('max_latency_ms', 60000)}ms
- Max LLM Calls: {constraints.get('max_llm_calls', 10)}
- Min Quality: {constraints.get('min_quality', 'medium')}

Available Patterns:
1. Chain-of-Thought: Step-by-step reasoning (fast, simple)
2. Tree-of-Thought: Multi-path exploration (slow, complex)
3. Self-Consistency: Multiple attempts + voting (medium, accurate)
4. ReAct: Reasoning + actions (medium, iterative)
5. Multi-Agent Debate: Adversarial reasoning (slow, thorough)
6. Advanced RAG: Multi-source retrieval (medium, grounded)

Ranking Instructions:
1. Match pattern to query characteristics
2. Consider constraints
3. Rank top 3 patterns
4. Explain reasoning

Format:
1. [Pattern]: Score [0-10] - [reasoning]
2. [Pattern]: Score [0-10] - [reasoning]
3. [Pattern]: Score [0-10] - [reasoning]

Pattern Rankings:"""
    
    def _build_execution_prompt(
        self,
        pattern: str,
        query: str,
        context: Dict[str, Any]
    ) -> str:
        """Build prompt for pattern execution simulation."""
        context_str = context.get("mcp_data", "")[:400]
        
        return f"""Execute the {pattern} pattern for this query.

Query: {query}

Context:
{context_str}...

Instructions:
1. Apply {pattern} methodology
2. Provide thorough answer
3. Follow pattern principles

Answer ({pattern}):"""
    
    def _parse_characteristics(self, analysis_text: str) -> Dict[str, Any]:
        """Parse query characteristics from analysis."""
        if not analysis_text:
            return {"complexity": "medium", "type": "analytical"}
        
        characteristics = {}
        text_lower = analysis_text.lower()
        
        # Parse complexity
        if "simple" in text_lower:
            characteristics["complexity"] = "simple"
        elif "complex" in text_lower:
            characteristics["complexity"] = "complex"
        else:
            characteristics["complexity"] = "medium"
        
        # Parse type
        if "factual" in text_lower:
            characteristics["type"] = "factual"
        elif "creative" in text_lower:
            characteristics["type"] = "creative"
        elif "strategic" in text_lower:
            characteristics["type"] = "strategic"
        else:
            characteristics["type"] = "analytical"
        
        # Parse requirements
        if "speed" in text_lower:
            characteristics["requirements"] = "speed"
        elif "depth" in text_lower:
            characteristics["requirements"] = "depth"
        else:
            characteristics["requirements"] = "accuracy"
        
        return characteristics
    
    def _select_pattern(self, ranking_text: str) -> str:
        """Select pattern from rankings."""
        if not ranking_text:
            return "Chain-of-Thought"  # Default
        
        # Look for first pattern mentioned
        patterns = [
            "Chain-of-Thought", "Tree-of-Thought", "Self-Consistency",
            "ReAct", "Multi-Agent Debate", "Advanced RAG"
        ]
        
        text_lines = ranking_text.split('\n')
        for line in text_lines[:5]:  # Check first 5 lines
            for pattern in patterns:
                if pattern.lower() in line.lower():
                    return pattern
        
        return "Chain-of-Thought"  # Default fallback
    
    def _parse_candidates(self, ranking_text: str) -> List[str]:
        """Parse candidate patterns from ranking."""
        if not ranking_text:
            return []
        
        patterns = []
        candidates = [
            "Chain-of-Thought", "Tree-of-Thought", "Self-Consistency",
            "ReAct", "Multi-Agent Debate", "Advanced RAG"
        ]
        
        for candidate in candidates:
            if candidate.lower() in ranking_text.lower():
                patterns.append(candidate)
        
        return patterns[:3]  # Top 3
    
    def _calculate_selection_confidence(
        self,
        ranking_step: PatternStep,
        characteristics: Dict[str, Any]
    ) -> float:
        """Calculate confidence in pattern selection."""
        if not ranking_step:
            return 0.6
        
        # Higher confidence for clear characteristics
        complexity = characteristics.get("complexity", "medium")
        if complexity in ["simple", "complex"]:
            return 0.8
        
        return 0.7

