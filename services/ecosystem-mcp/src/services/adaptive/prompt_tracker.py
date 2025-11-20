"""
Prompt Execution Tracker

Tracks prompt usage, effectiveness, and findings for continuous improvement
and prompt evolution. Stores data in EXISTING prompt_execution_history table.
"""

import logging
from typing import Dict, List, Optional, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ...storage.database import get_database
from ...storage.models_templates import PromptExecutionHistoryModel

logger = logging.getLogger(__name__)


class PromptTracker:
    """
    Tracks prompt execution for adaptive learning.
    
    Stores all prompt executions in EXISTING prompt_execution_history table
    created in Phase 1. Provides analytics and insights for prompt evolution.
    """
    
    def __init__(self):
        """Initialize prompt tracker."""
        logger.info("PromptTracker initialized")
    
    async def track_prompt_execution(
        self,
        run_id: UUID,
        prompt_template: str,
        prompt_used: str,
        context_provided: Dict[str, Any],
        response: str,
        sources_used: List[Dict[str, Any]],
        section_name: Optional[str] = None,
        pass_number: Optional[int] = None
    ) -> UUID:
        """
        Track a single prompt execution.
        
        Args:
            run_id: Documentation run ID
            prompt_template: Template name/identifier
            prompt_used: Actual prompt sent to LLM
            context_provided: Context variables used
            response: LLM response
            sources_used: Source documents used
            section_name: Section being generated
            pass_number: Pass number (for multi-pass generation)
        
        Returns:
            Execution ID
        """
        # Calculate metrics
        response_length = len(response)
        code_examples_count = response.count("```")
        
        # Calculate effectiveness score
        effectiveness_score = self._calculate_effectiveness(
            response, sources_used, code_examples_count
        )
        
        # Calculate specificity score
        specificity_score = self._calculate_specificity(
            prompt_used, response, context_provided
        )
        
        # Extract findings
        findings = self._extract_findings(response, context_provided)
        
        async with get_database().session() as session:
            execution = PromptExecutionHistoryModel(
                run_id=run_id,
                prompt_template=prompt_template,
                prompt_used=prompt_used,
                context_provided=context_provided,
                pass_number=pass_number,
                section_name=section_name,
                response_length=response_length,
                tokens_used=None,  # Can be populated if token counting is available
                sources_used=sources_used,
                effectiveness_score=effectiveness_score,
                specificity_score=specificity_score,
                code_examples_count=code_examples_count,
                findings=findings
            )
            
            session.add(execution)
            await session.commit()
            await session.refresh(execution)
            
            logger.info(
                f"✅ Tracked prompt execution: {prompt_template} "
                f"(effectiveness: {effectiveness_score:.2f}, "
                f"specificity: {specificity_score:.2f})"
            )
            
            return execution.id
    
    def _calculate_effectiveness(
        self,
        response: str,
        sources_used: List[Dict[str, Any]],
        code_examples_count: int
    ) -> float:
        """
        Calculate prompt effectiveness score (0.0-1.0).
        
        Factors:
        - Response length (longer is generally better)
        - Number of sources used (more sources = better coverage)
        - Code examples (concrete examples improve quality)
        - Structure (sections, lists, tables)
        """
        score = 0.0
        
        # Response length score (0.0-0.3)
        if len(response) > 500:
            score += 0.3
        elif len(response) > 200:
            score += 0.2
        elif len(response) > 100:
            score += 0.1
        
        # Sources score (0.0-0.3)
        if len(sources_used) >= 5:
            score += 0.3
        elif len(sources_used) >= 3:
            score += 0.2
        elif len(sources_used) >= 1:
            score += 0.1
        
        # Code examples score (0.0-0.2)
        if code_examples_count >= 2:
            score += 0.2
        elif code_examples_count >= 1:
            score += 0.1
        
        # Structure score (0.0-0.2)
        structure_indicators = ["##", "###", "-", "*", "|", "1.", "2."]
        structure_count = sum(1 for indicator in structure_indicators if indicator in response)
        if structure_count >= 3:
            score += 0.2
        elif structure_count >= 1:
            score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_specificity(
        self,
        prompt: str,
        response: str,
        context: Dict[str, Any]
    ) -> float:
        """
        Calculate prompt specificity score (0.0-1.0).
        
        Measures how well the response is tailored to the specific codebase
        vs generic documentation.
        
        Factors:
        - Context terms mentioned in response
        - Service-specific terminology
        - Framework-specific details
        """
        score = 0.0
        
        # Check if service name is mentioned
        service_name = context.get("service_name", "")
        if service_name and service_name.lower() in response.lower():
            score += 0.3
        
        # Check if framework is mentioned
        frameworks = context.get("frameworks", [])
        framework_mentions = sum(1 for fw in frameworks if fw.lower() in response.lower())
        if framework_mentions > 0:
            score += 0.3
        
        # Check if languages are mentioned
        languages = context.get("languages", {})
        language_mentions = sum(1 for lang in languages.keys() if lang.lower() in response.lower())
        if language_mentions > 0:
            score += 0.2
        
        # Check if specific paths/files are mentioned
        if any(indicator in response for indicator in ["/", "src/", "app/", ".scala", ".java", ".py"]):
            score += 0.2
        
        return min(score, 1.0)
    
    def _extract_findings(
        self,
        response: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract findings from response for next pass refinement.
        
        Findings include:
        - New concepts discovered
        - Gaps identified
        - Questions raised
        - Suggestions for deeper investigation
        """
        findings = {
            "new_concepts": [],
            "gaps_identified": [],
            "extraction_timestamp": datetime.utcnow().isoformat()
        }
        
        # Extract capitalized terms (potential concepts)
        words = response.split()
        concepts = set()
        for word in words:
            # Look for capitalized words that aren't at sentence start
            if word and word[0].isupper() and len(word) > 3:
                # Remove punctuation
                clean_word = word.strip(".,!?:;")
                if clean_word:
                    concepts.add(clean_word)
        
        findings["new_concepts"] = sorted(list(concepts))[:20]  # Limit to top 20
        
        # Identify gaps (phrases suggesting missing information)
        gap_indicators = [
            "not found",
            "no information",
            "unclear",
            "unknown",
            "missing",
            "could not determine",
            "more investigation needed"
        ]
        
        for indicator in gap_indicators:
            if indicator in response.lower():
                findings["gaps_identified"].append(f"Possible gap: '{indicator}' mentioned")
        
        return findings
    
    async def get_prompt_effectiveness_trends(
        self,
        prompt_template: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get effectiveness trends for a specific prompt template.
        
        Args:
            prompt_template: Prompt template name
            limit: Number of recent executions to analyze
        
        Returns:
            List of execution metrics showing trends
        """
        async with get_database().session() as session:
            query = select(PromptExecutionHistoryModel).filter(
                PromptExecutionHistoryModel.prompt_template == prompt_template
            ).order_by(
                PromptExecutionHistoryModel.executed_at.desc()
            ).limit(limit)
            
            result = await session.execute(query)
            executions = result.scalars().all()
            
            return [
                {
                    "executed_at": e.executed_at.isoformat(),
                    "effectiveness_score": e.effectiveness_score,
                    "specificity_score": e.specificity_score,
                    "response_length": e.response_length,
                    "code_examples": e.code_examples_count,
                    "sources_count": len(e.sources_used) if e.sources_used else 0
                }
                for e in executions
            ]
    
    async def get_average_effectiveness(
        self,
        prompt_template: Optional[str] = None
    ) -> float:
        """
        Get average effectiveness score for prompt template(s).
        
        Args:
            prompt_template: Optional specific template, or None for all
        
        Returns:
            Average effectiveness score
        """
        async with get_database().session() as session:
            query = select(func.avg(PromptExecutionHistoryModel.effectiveness_score))
            
            if prompt_template:
                query = query.filter(
                    PromptExecutionHistoryModel.prompt_template == prompt_template
                )
            
            result = await session.execute(query)
            avg = result.scalar()
            
            return float(avg) if avg else 0.0
    
    async def get_low_performing_prompts(
        self,
        threshold: float = 0.5,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Identify prompts with low effectiveness for improvement.
        
        Args:
            threshold: Effectiveness threshold below which prompts are flagged
            limit: Maximum number of prompts to return
        
        Returns:
            List of low-performing prompts with metrics
        """
        async with get_database().session() as session:
            # Get average effectiveness per template
            query = select(
                PromptExecutionHistoryModel.prompt_template,
                func.avg(PromptExecutionHistoryModel.effectiveness_score).label("avg_effectiveness"),
                func.avg(PromptExecutionHistoryModel.specificity_score).label("avg_specificity"),
                func.count(PromptExecutionHistoryModel.id).label("execution_count")
            ).group_by(
                PromptExecutionHistoryModel.prompt_template
            ).having(
                func.avg(PromptExecutionHistoryModel.effectiveness_score) < threshold
            ).order_by(
                func.avg(PromptExecutionHistoryModel.effectiveness_score).asc()
            ).limit(limit)
            
            result = await session.execute(query)
            
            return [
                {
                    "prompt_template": row.prompt_template,
                    "avg_effectiveness": float(row.avg_effectiveness),
                    "avg_specificity": float(row.avg_specificity),
                    "execution_count": row.execution_count,
                    "needs_improvement": True
                }
                for row in result
            ]
    
    async def suggest_prompt_improvements(
        self,
        prompt_template: str
    ) -> Dict[str, Any]:
        """
        Suggest improvements for a prompt based on execution history.
        
        Args:
            prompt_template: Prompt template to analyze
        
        Returns:
            Suggestions for improvement
        """
        # Get recent executions
        trends = await self.get_prompt_effectiveness_trends(prompt_template, limit=20)
        
        if not trends:
            return {"suggestions": ["Not enough data for analysis"]}
        
        suggestions = []
        
        # Analyze trends
        avg_effectiveness = sum(t["effectiveness_score"] or 0 for t in trends) / len(trends)
        avg_specificity = sum(t["specificity_score"] or 0 for t in trends) / len(trends)
        avg_code_examples = sum(t["code_examples"] for t in trends) / len(trends)
        
        # Effectiveness suggestions
        if avg_effectiveness < 0.5:
            suggestions.append(
                "Low effectiveness - Consider adding more specific context variables"
            )
        
        # Specificity suggestions
        if avg_specificity < 0.5:
            suggestions.append(
                "Low specificity - Include more service-specific terms and framework details"
            )
        
        # Code example suggestions
        if avg_code_examples < 1.0:
            suggestions.append(
                "Few code examples - Explicitly request code examples in prompt"
            )
        
        # Length suggestions
        avg_length = sum(t["response_length"] for t in trends) / len(trends)
        if avg_length < 200:
            suggestions.append(
                "Short responses - Request more detailed explanations"
            )
        
        return {
            "prompt_template": prompt_template,
            "avg_effectiveness": avg_effectiveness,
            "avg_specificity": avg_specificity,
            "executions_analyzed": len(trends),
            "suggestions": suggestions if suggestions else ["Prompt is performing well"]
        }


# Singleton instance
_prompt_tracker: Optional[PromptTracker] = None


def get_prompt_tracker() -> PromptTracker:
    """Get or create singleton prompt tracker."""
    global _prompt_tracker
    if _prompt_tracker is None:
        _prompt_tracker = PromptTracker()
    return _prompt_tracker

