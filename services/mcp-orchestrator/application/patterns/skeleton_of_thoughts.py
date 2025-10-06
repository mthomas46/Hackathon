"""Skeleton of Thoughts (SoT) pattern."""
from typing import Any, Dict, List
from services.mcp_orchestrator.application.patterns.base import BasePattern
from services.mcp_orchestrator.infrastructure.config.settings import Settings
import asyncio

class SkeletonOfThoughtsPattern(BasePattern):
    def __init__(self, settings: Settings):
        super().__init__(settings)
        
    async def execute(self, query: str, context: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        model = kwargs.get("model", self.settings.default_llm_model)
        
        # Step 1: Generate skeleton/outline
        skeleton = await self._generate_skeleton(query, model)
        
        # Step 2: Elaborate points in parallel
        elaborations = await asyncio.gather(*[
            self._elaborate_point(point, model)
            for point in skeleton
        ])
        
        # Step 3: Synthesize final answer
        final_answer = await self._synthesize(query, skeleton, elaborations, model)
        
        return {
            "skeleton": skeleton,
            "elaborations": elaborations,
            "final_answer": final_answer
        }
    
    async def _generate_skeleton(self, query: str, model: str) -> List[str]:
        prompt = f"Create a brief outline to answer: {query}\nProvide 3-5 main points."
        response = await self._call_llm_gateway(prompt=prompt, model=model)
        return response.split("\n")[:5]
    
    async def _elaborate_point(self, point: str, model: str) -> str:
        prompt = f"Elaborate on this point: {point}"
        return await self._call_llm_gateway(prompt=prompt, model=model)
    
    async def _synthesize(self, query: str, skeleton: List[str], elaborations: List[str], model: str) -> str:
        combined = "\n".join(f"{s}: {e}" for s, e in zip(skeleton, elaborations))
        prompt = f"Synthesize this into a coherent answer for: {query}\n\n{combined}"
        return await self._call_llm_gateway(prompt=prompt, model=model)
    
    def get_pattern_info(self) -> Dict[str, Any]:
        return {
            "name": "Skeleton of Thoughts (SoT)",
            "category": "Reasoning",
            "latency_impact": "Medium (20-40s)"
        }
