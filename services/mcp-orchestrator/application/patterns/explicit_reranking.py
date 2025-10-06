"""Explicit Reranking pattern."""
from typing import Any, Dict, List
from services.mcp_orchestrator.application.patterns.base import BasePattern
from services.mcp_orchestrator.infrastructure.config.settings import Settings

class ExplicitRerankingPattern(BasePattern):
    def __init__(self, settings: Settings):
        super().__init__(settings)
        
    async def execute(self, query: str, context: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        documents = context.get("documents", [])
        strategy = kwargs.get("strategy", "relevance")
        model = kwargs.get("model", self.settings.default_llm_model)
        
        if strategy == "relevance":
            reranked = await self._rerank_by_relevance(query, documents, model)
        elif strategy == "diversity":
            reranked = self._rerank_by_diversity(documents)
        else:
            reranked = await self._rerank_hybrid(query, documents, model)
        
        return {
            "original_order": [d.get("id") for d in documents],
            "reranked_order": [d.get("id") for d in reranked],
            "strategy": strategy,
            "reranked_documents": reranked
        }
    
    async def _rerank_by_relevance(self, query: str, docs: List[Dict], model: str) -> List[Dict]:
        # Use LLM to score relevance
        scored = []
        for doc in docs:
            prompt = f"Rate relevance 0-10 of this doc to query '{query}':\n{doc.get('content', '')[:200]}"
            score_str = await self._call_llm_gateway(prompt=prompt, model=model, max_tokens=5)
            try:
                score = float(score_str.strip())
            except:
                score = 5.0
            scored.append((doc, score))
        
        scored.sort(key=lambda x: x[1], reverse=True)
        return [doc for doc, _ in scored]
    
    def _rerank_by_diversity(self, docs: List[Dict]) -> List[Dict]:
        # Simple diversity: alternate between high and low distance
        sorted_docs = sorted(docs, key=lambda d: d.get("distance", 0.5))
        diverse = []
        left, right = 0, len(sorted_docs) - 1
        while left <= right:
            diverse.append(sorted_docs[left])
            if left != right:
                diverse.append(sorted_docs[right])
            left += 1
            right -= 1
        return diverse
    
    async def _rerank_hybrid(self, query: str, docs: List[Dict], model: str) -> List[Dict]:
        relevance_ranked = await self._rerank_by_relevance(query, docs, model)
        return relevance_ranked
    
    def get_pattern_info(self) -> Dict[str, Any]:
        return {
            "name": "Explicit Reranking",
            "category": "RAG Utility",
            "latency_impact": "Low-Medium (5-15s)"
        }
