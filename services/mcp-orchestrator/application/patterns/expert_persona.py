"""Expert Persona pattern."""
from typing import Any, Dict
from services.mcp_orchestrator.application.patterns.base import BasePattern
from services.mcp_orchestrator.infrastructure.config.settings import Settings

class ExpertPersonaPattern(BasePattern):
    def __init__(self, settings: Settings):
        super().__init__(settings)
        
    async def execute(self, query: str, context: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        model = kwargs.get("model", self.settings.default_llm_model)
        domain = kwargs.get("domain", "general")
        
        # Identify domain if not provided
        if domain == "general":
            domain = await self._identify_domain(query, model)
        
        # Apply expert persona
        expert_prompt = self._create_expert_prompt(query, domain)
        answer = await self._call_llm_gateway(prompt=expert_prompt, model=model)
        
        return {
            "domain": domain,
            "expert_answer": answer
        }
    
    async def _identify_domain(self, query: str, model: str) -> str:
        prompt = f"Identify the primary domain (medical/legal/technical/business/etc) for: {query}"
        return await self._call_llm_gateway(prompt=prompt, model=model, max_tokens=50)
    
    def _create_expert_prompt(self, query: str, domain: str) -> str:
        return (
            f"You are a world-renowned {domain} expert with 20+ years of experience. "
            f"Answer this question with deep domain knowledge: {query}"
        )
    
    def get_pattern_info(self) -> Dict[str, Any]:
        return {
            "name": "Expert Persona",
            "category": "Reasoning",
            "latency_impact": "Medium (15-30s)"
        }
