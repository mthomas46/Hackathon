"""LLM-as-a-Judge pattern."""
from typing import Any, Dict, List
from services.mcp_orchestrator.application.patterns.base import BasePattern
from services.mcp_orchestrator.infrastructure.config.settings import Settings

class LLMAsJudgePattern(BasePattern):
    def __init__(self, settings: Settings):
        super().__init__(settings)
        
    async def execute(self, query: str, context: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        responses = context.get("responses", [])
        criteria = kwargs.get("criteria", ["accuracy", "completeness", "clarity"])
        model = kwargs.get("model", self.settings.default_llm_model)
        
        # Evaluate each response
        evaluations = []
        for response in responses:
            evaluation = await self._evaluate_response(
                query, response, criteria, model
            )
            evaluations.append(evaluation)
        
        # Rank responses
        ranked = sorted(evaluations, key=lambda e: e["overall_score"], reverse=True)
        
        return {
            "query": query,
            "evaluations": evaluations,
            "ranked_responses": ranked,
            "best_response": ranked[0] if ranked else None
        }
    
    async def _evaluate_response(
        self, query: str, response: str, criteria: List[str], model: str
    ) -> Dict[str, Any]:
        criteria_str = ", ".join(criteria)
        prompt = (
            f"Evaluate this response to the query.\n"
            f"Query: {query}\n"
            f"Response: {response[:500]}...\n"
            f"Criteria: {criteria_str}\n"
            f"Provide scores 0-10 for each criterion and overall score.\n"
            f"Format: CRITERION: score\nOVERALL: score"
        )
        
        evaluation = await self._call_llm_gateway(prompt=prompt, model=model, max_tokens=200)
        
        # Parse scores
        scores = {}
        for line in evaluation.split("\n"):
            if ":" in line:
                key, val = line.split(":", 1)
                try:
                    scores[key.strip().lower()] = float(val.strip())
                except:
                    pass
        
        return {
            "response": response,
            "scores": scores,
            "overall_score": scores.get("overall", 5.0),
            "evaluation_text": evaluation
        }
    
    def get_pattern_info(self) -> Dict[str, Any]:
        return {
            "name": "LLM-as-a-Judge",
            "category": "Evaluation",
            "latency_impact": "Medium (10-30s)"
        }
