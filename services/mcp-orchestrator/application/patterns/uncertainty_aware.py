"""Uncertainty-Aware pattern implementation."""

from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

from .base import BasePatternEngine, PatternResult, PatternStep


class UncertaintyAwareEngine(BasePatternEngine):
    """
    Uncertainty-Aware pattern execution engine.
    
    Explicitly models and communicates uncertainty in LLM responses.
    Identifies what is known vs unknown, distinguishes facts from
    speculation, and provides confidence intervals.
    
    Process:
    1. Generate answer
    2. Identify uncertainty sources
    3. Classify statement confidence levels
    4. Separate facts vs speculation
    5. Provide calibrated final answer
    
    Key Innovation: Explicit uncertainty quantification and
    communication for more trustworthy AI outputs.
    """
    
    def __init__(self):
        super().__init__("uncertainty_aware")
    
    async def execute(
        self,
        query: str,
        context: Dict[str, Any],
        config: Dict[str, Any]
    ) -> PatternResult:
        """Execute Uncertainty-Aware pattern."""
        start_time = datetime.utcnow()
        steps: List[PatternStep] = []
        
        try:
            # Step 1: Generate initial answer
            generation_step = await self._generate_answer(
                query,
                context,
                config
            )
            steps.append(generation_step)
            
            # Step 2: Identify uncertainty sources
            uncertainty_step = await self._identify_uncertainties(
                query,
                generation_step.response,
                context,
                config
            )
            steps.append(uncertainty_step)
            
            # Step 3: Classify statement confidence levels
            classification_step = await self._classify_confidence_levels(
                generation_step.response,
                uncertainty_step.response,
                config
            )
            steps.append(classification_step)
            
            # Step 4: Separate facts from speculation
            separation_step = await self._separate_facts_speculation(
                generation_step.response,
                classification_step.response,
                config
            )
            steps.append(separation_step)
            
            # Step 5: Generate calibrated final answer
            calibration_step = await self._generate_calibrated_answer(
                query,
                generation_step.response,
                uncertainty_step.response,
                separation_step.response,
                config
            )
            steps.append(calibration_step)
            
            # Calculate execution time
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Calculate overall confidence
            confidence = self._calculate_uncertainty_confidence(
                uncertainty_step,
                classification_step
            )
            
            return PatternResult(
                pattern_type=self.pattern_type,
                success=True,
                steps=steps,
                final_answer=calibration_step.response,
                confidence=confidence,
                total_duration_ms=duration_ms,
                metadata={
                    "uncertainty_sources": self._count_uncertainty_sources(uncertainty_step),
                    "confidence_distribution": self._parse_confidence_distribution(classification_step),
                    "facts_vs_speculation": self._parse_fact_speculation_ratio(separation_step)
                }
            )
        
        except Exception as e:
            self.logger.error(f"Error executing Uncertainty-Aware: {e}", exc_info=True)
            
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            return PatternResult(
                pattern_type=self.pattern_type,
                success=False,
                steps=steps,
                total_duration_ms=duration_ms,
                error=str(e)
            )
    
    async def _generate_answer(
        self,
        query: str,
        context: Dict[str, Any],
        config: Dict[str, Any]
    ) -> PatternStep:
        """Generate initial answer."""
        step = self.create_step(
            step_id="generation",
            step_type="generation",
            description="Generate initial answer",
            prompt=self._build_generation_prompt(query, context)
        )
        
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
    
    async def _identify_uncertainties(
        self,
        query: str,
        answer: str,
        context: Dict[str, Any],
        config: Dict[str, Any]
    ) -> PatternStep:
        """Identify sources of uncertainty in the answer."""
        step = self.create_step(
            step_id="uncertainty_identification",
            step_type="uncertainty",
            description="Identify uncertainty sources",
            prompt=self._build_uncertainty_prompt(query, answer, context)
        )
        
        try:
            response = await self.call_llm(step.prompt, config)
            self.complete_step(
                step,
                response,
                {"stage": "uncertainty_identification"}
            )
        except Exception as e:
            self.complete_step(step, f"Error: {e}", {"error": True})
        
        return step
    
    async def _classify_confidence_levels(
        self,
        answer: str,
        uncertainties: str,
        config: Dict[str, Any]
    ) -> PatternStep:
        """Classify each statement by confidence level."""
        step = self.create_step(
            step_id="classification",
            step_type="classification",
            description="Classify confidence levels",
            prompt=self._build_classification_prompt(answer, uncertainties)
        )
        
        try:
            response = await self.call_llm(step.prompt, config)
            self.complete_step(
                step,
                response,
                {"stage": "classification"}
            )
        except Exception as e:
            self.complete_step(step, f"Error: {e}", {"error": True})
        
        return step
    
    async def _separate_facts_speculation(
        self,
        answer: str,
        classifications: str,
        config: Dict[str, Any]
    ) -> PatternStep:
        """Separate factual statements from speculation."""
        step = self.create_step(
            step_id="separation",
            step_type="separation",
            description="Separate facts from speculation",
            prompt=self._build_separation_prompt(answer, classifications)
        )
        
        try:
            response = await self.call_llm(step.prompt, config)
            self.complete_step(
                step,
                response,
                {"stage": "separation"}
            )
        except Exception as e:
            self.complete_step(step, f"Error: {e}", {"error": True})
        
        return step
    
    async def _generate_calibrated_answer(
        self,
        query: str,
        original_answer: str,
        uncertainties: str,
        facts_speculation: str,
        config: Dict[str, Any]
    ) -> PatternStep:
        """Generate calibrated answer with explicit uncertainty."""
        step = self.create_step(
            step_id="calibration",
            step_type="calibration",
            description="Generate calibrated answer",
            prompt=self._build_calibration_prompt(
                query,
                original_answer,
                uncertainties,
                facts_speculation
            )
        )
        
        try:
            response = await self.call_llm(step.prompt, config)
            self.complete_step(
                step,
                response,
                {"stage": "calibration"}
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
        
        return f"""Answer this query as completely as possible.

Query: {query}

{context_str}

Instructions:
1. Provide comprehensive answer
2. Be as specific as possible
3. Include all relevant information
4. Don't worry about uncertainty yet

Answer:"""
    
    def _build_uncertainty_prompt(
        self,
        query: str,
        answer: str,
        context: Dict[str, Any]
    ) -> str:
        """Build prompt for uncertainty identification."""
        return f"""Identify all sources of uncertainty in this answer.

Query: {query}

Answer:
{answer[:600]}...

Uncertainty Analysis Instructions:
1. List all uncertain elements
2. Identify missing information
3. Note assumptions made
4. Highlight speculation
5. Categorize uncertainty types:
   - Epistemic (lack of knowledge)
   - Aleatoric (inherent randomness)
   - Linguistic (ambiguity)

Uncertainty Sources:"""
    
    def _build_classification_prompt(
        self,
        answer: str,
        uncertainties: str
    ) -> str:
        """Build prompt for confidence classification."""
        return f"""Classify each statement in the answer by confidence level.

Answer:
{answer[:600]}...

Identified Uncertainties:
{uncertainties[:400]}...

Classification Instructions:
1. Break answer into individual statements
2. Assign confidence level to each:
   - HIGH (>80%): Well-established facts
   - MEDIUM (50-80%): Supported but some uncertainty
   - LOW (<50%): Speculation or weak support
3. Explain reasoning

Format:
Statement: "[statement]"
Confidence: [HIGH/MEDIUM/LOW]
Reasoning: [why]

Classifications:"""
    
    def _build_separation_prompt(
        self,
        answer: str,
        classifications: str
    ) -> str:
        """Build prompt for fact/speculation separation."""
        return f"""Separate factual statements from speculation.

Answer:
{answer[:600]}...

Classifications:
{classifications[:400]}...

Separation Instructions:
1. FACTS: Statements with HIGH confidence
2. LIKELY: Statements with MEDIUM confidence
3. SPECULATION: Statements with LOW confidence
4. List each category clearly

Separated Statements:"""
    
    def _build_calibration_prompt(
        self,
        query: str,
        original_answer: str,
        uncertainties: str,
        facts_speculation: str
    ) -> str:
        """Build prompt for calibrated answer generation."""
        return f"""Generate a calibrated answer that explicitly communicates uncertainty.

Query: {query}

Original Answer:
{original_answer[:500]}...

Uncertainty Analysis:
{uncertainties[:300]}...

Facts vs Speculation:
{facts_speculation[:300]}...

Calibration Instructions:
1. Start with high-confidence facts
2. Clearly distinguish speculation (use "possibly", "likely", "may")
3. Acknowledge what's unknown
4. Provide confidence indicators
5. Be honest about limitations
6. Format for clarity:
   - ✓ Facts: [statements]
   - ? Likely: [statements]
   - ⚠ Speculation: [statements]
   - ✗ Unknown: [what we don't know]

Calibrated Answer:"""
    
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
    
    def _count_uncertainty_sources(self, uncertainty_step: PatternStep) -> int:
        """Count identified uncertainty sources."""
        if not uncertainty_step or not uncertainty_step.response:
            return 0
        
        # Heuristic: count bullet points or numbered items
        text = uncertainty_step.response
        count = text.count('\n-') + text.count('\n•') + text.count('\n*')
        return max(count, 1)
    
    def _parse_confidence_distribution(self, classification_step: PatternStep) -> Dict[str, int]:
        """Parse distribution of confidence levels."""
        if not classification_step or not classification_step.response:
            return {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
        
        text = classification_step.response.upper()
        return {
            "HIGH": text.count("HIGH"),
            "MEDIUM": text.count("MEDIUM"),
            "LOW": text.count("LOW")
        }
    
    def _parse_fact_speculation_ratio(self, separation_step: PatternStep) -> Dict[str, int]:
        """Parse facts vs speculation ratio."""
        if not separation_step or not separation_step.response:
            return {"facts": 0, "speculation": 0}
        
        text = separation_step.response.lower()
        facts = text.count("fact") + text.count("✓")
        speculation = text.count("speculation") + text.count("⚠")
        
        return {"facts": facts, "speculation": speculation}
    
    def _calculate_uncertainty_confidence(
        self,
        uncertainty_step: PatternStep,
        classification_step: PatternStep
    ) -> float:
        """Calculate overall confidence considering uncertainties."""
        if not classification_step:
            return 0.5
        
        # Parse confidence distribution
        dist = self._parse_confidence_distribution(classification_step)
        total = sum(dist.values())
        
        if total == 0:
            return 0.5
        
        # Weight by confidence level
        weighted = (
            dist.get("HIGH", 0) * 1.0 +
            dist.get("MEDIUM", 0) * 0.6 +
            dist.get("LOW", 0) * 0.3
        )
        
        confidence = weighted / total
        return min(confidence, 1.0)

