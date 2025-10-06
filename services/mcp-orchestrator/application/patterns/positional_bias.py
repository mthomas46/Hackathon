"""Positional Bias Exploitation pattern."""
from typing import Any, Dict, List
from services.mcp_orchestrator.application.patterns.base import BasePattern
from services.mcp_orchestrator.infrastructure.config.settings import Settings

class PositionalBiasPattern(BasePattern):
    def __init__(self, settings: Settings):
        super().__init__(settings)
        
    async def execute(self, query: str, context: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        documents = context.get("documents", [])
        strategy = kwargs.get("strategy", "importance_at_edges")
        model = kwargs.get("model", self.settings.default_llm_model)
        
        # Reorder based on positional bias strategy
        if strategy == "importance_at_edges":
            optimized = self._place_important_at_edges(documents)
        elif strategy == "primacy":
            optimized = self._primacy_ordering(documents)
        elif strategy == "recency":
            optimized = self._recency_ordering(documents)
        else:
            optimized = documents
        
        # Generate answer with optimized ordering
        answer = await self._generate_with_ordering(query, optimized, model)
        
        return {
            "original_order": [d.get("id") for d in documents],
            "optimized_order": [d.get("id") for d in optimized],
            "strategy": strategy,
            "final_answer": answer
        }
    
    def _place_important_at_edges(self, docs: List[Dict]) -> List[Dict]:
        # Most important at start and end
        sorted_docs = sorted(docs, key=lambda d: d.get("distance", 0.5))
        if len(docs) <= 2:
            return sorted_docs
        
        result = [sorted_docs[0]]  # Most important at start
        result.extend(sorted_docs[2:-1])  # Middle docs
        result.append(sorted_docs[1])  # Second most important at end
        return result
    
    def _primacy_ordering(self, docs: List[Dict]) -> List[Dict]:
        # Most important first (primacy effect)
        return sorted(docs, key=lambda d: d.get("distance", 0.5))
    
    def _recency_ordering(self, docs: List[Dict]) -> List[Dict]:
        # Most important last (recency effect)
        return sorted(docs, key=lambda d: d.get("distance", 0.5), reverse=True)
    
    async def _generate_with_ordering(self, query: str, docs: List[Dict], model: str) -> str:
        context = "\n\n".join([
            f"[{i+1}] {d.get('content', '')[:400]}"
            for i, d in enumerate(docs)
        ])
        
        prompt = f"Answer based on these ordered documents:\n{context}\n\nQuestion: {query}"
        return await self._call_llm_gateway(prompt=prompt, model=model)
    
    def get_pattern_info(self) -> Dict[str, Any]:
        return {
            "name": "Positional Bias Exploitation",
            "category": "Context Optimization",
            "latency_impact": "Low (5-10s)"
        }
