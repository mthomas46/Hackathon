"""Lost in the Middle Mitigation pattern implementation."""

from typing import Any, Dict, List
from services.mcp_orchestrator.application.patterns.base import BasePattern
from services.mcp_orchestrator.infrastructure.config.settings import Settings


class LostInMiddlePattern(BasePattern):
    """
    Mitigates the "Lost in the Middle" problem where LLMs attend less
    to information in the middle of long contexts.
    """
    
    def __init__(self, settings: Settings):
        super().__init__(settings)
        self.logger.info("LostInMiddlePattern initialized.")
        
    async def execute(self, query: str, context: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Reorders context to avoid lost in the middle problem.
        
        Args:
            query (str): The user query.
            context (Dict[str, Any]): Contains documents/chunks to reorder.
            **kwargs: Additional parameters:
                - strategy (str): 'edges', 'relevance', 'interleave'
                - num_chunks (int): Number of top chunks to use
        
        Returns:
            Dict[str, Any]: Reordered context and final answer.
        """
        self.logger.info("Executing Lost in Middle mitigation...")
        
        documents = context.get("documents", [])
        strategy = kwargs.get("strategy", "edges")
        model = kwargs.get("model", self.settings.default_llm_model)
        
        if strategy == "edges":
            reordered = self._edges_strategy(documents)
        elif strategy == "relevance":
            reordered = await self._relevance_strategy(query, documents, model)
        else:
            reordered = self._interleave_strategy(documents)
        
        # Generate answer with reordered context
        final_answer = await self._generate_with_optimized_context(
            query, reordered, model
        )
        
        return {
            "original_order": [d.get("id") for d in documents],
            "reordered": [d.get("id") for d in reordered],
            "strategy": strategy,
            "final_answer": final_answer
        }
    
    def _edges_strategy(self, docs: List[Dict]) -> List[Dict]:
        """Place most relevant at beginning and end."""
        if len(docs) <= 2:
            return docs
        
        # Simple: put top relevance at edges
        mid_point = len(docs) // 2
        return [docs[0]] + docs[mid_point+1:] + [docs[mid_point]] + docs[1:mid_point]
    
    async def _relevance_strategy(self, query: str, docs: List[Dict], model: str) -> List[Dict]:
        """Reorder by relevance scores."""
        # Sort by distance/relevance (if available)
        sorted_docs = sorted(docs, key=lambda d: d.get("distance", 1.0))
        return sorted_docs
    
    def _interleave_strategy(self, docs: List[Dict]) -> List[Dict]:
        """Interleave high and low relevance docs."""
        if len(docs) <= 2:
            return docs
        
        high = docs[:len(docs)//2]
        low = docs[len(docs)//2:]
        
        interleaved = []
        for h, l in zip(high, low):
            interleaved.extend([h, l])
        
        return interleaved
    
    async def _generate_with_optimized_context(
        self, query: str, docs: List[Dict], model: str
    ) -> str:
        """Generate answer with optimized context ordering."""
        context = "\n\n".join([d.get("content", "")[:500] for d in docs])
        
        prompt = f"Question: {query}\n\nContext (optimized ordering):\n{context}\n\nAnswer:"
        
        return await self._call_llm_gateway(prompt=prompt, model=model)
    
    def get_pattern_info(self) -> Dict[str, Any]:
        return {
            "name": "Lost in the Middle Mitigation",
            "description": "Reorders context to avoid attention drop in middle of long contexts.",
            "category": "Context Management",
            "latency_impact": "Low (5-10s)",
            "complexity": "Medium"
        }
