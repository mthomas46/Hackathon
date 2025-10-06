"""Rephrase and Respond (RaR) pattern."""
from typing import Any, Dict
from services.mcp_orchestrator.application.patterns.base import BasePattern
from services.mcp_orchestrator.infrastructure.config.settings import Settings

class RephraseAndRespondPattern(BasePattern):
    def __init__(self, settings: Settings):
        super().__init__(settings)
        
    async def execute(self, query: str, context: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        model = kwargs.get("model", self.settings.default_llm_model)
        
        # Step 1: Rephrase query for clarity
        rephrased = await self._rephrase_query(query, model)
        
        # Step 2: Answer based on rephrased query
        answer = await self._call_llm_gateway(
            prompt=f"Answer this question: {rephrased}",
            model=model
        )
        
        return {
            "original_query": query,
            "rephrased_query": rephrased,
            "final_answer": answer
        }
    
    async def _rephrase_query(self, query: str, model: str) -> str:
        prompt = f"Rephrase this question to be clearer and more specific: {query}"
        return await self._call_llm_gateway(prompt=prompt, model=model)
    
    def get_pattern_info(self) -> Dict[str, Any]:
        return {
            "name": "Rephrase and Respond (RaR)",
            "category": "Reasoning",
            "latency_impact": "Low (10-20s)"
        }
