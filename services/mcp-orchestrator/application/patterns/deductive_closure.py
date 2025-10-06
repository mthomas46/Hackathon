"""Deductive Closure Training (DCT) pattern."""
from typing import Any, Dict, List
from services.mcp_orchestrator.application.patterns.base import BasePattern
from services.mcp_orchestrator.infrastructure.config.settings import Settings

class DeductiveClosurePattern(BasePattern):
    def __init__(self, settings: Settings):
        super().__init__(settings)
        
    async def execute(self, query: str, context: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        model = kwargs.get("model", self.settings.default_llm_model)
        
        # Step 1: Initial reasoning
        initial_answer = await self._call_llm_gateway(
            prompt=f"Answer with step-by-step reasoning: {query}",
            model=model
        )
        
        # Step 2: Extract logical statements
        statements = await self._extract_statements(initial_answer, model)
        
        # Step 3: Apply deductive closure
        closure = await self._apply_closure(statements, model)
        
        # Step 4: Verify consistency
        consistent = await self._verify_consistency(closure, model)
        
        return {
            "initial_answer": initial_answer,
            "logical_statements": statements,
            "deductive_closure": closure,
            "is_consistent": consistent
        }
    
    async def _extract_statements(self, text: str, model: str) -> List[str]:
        prompt = f"Extract logical statements from: {text}"
        response = await self._call_llm_gateway(prompt=prompt, model=model)
        return response.split("\n")[:10]
    
    async def _apply_closure(self, statements: List[str], model: str) -> List[str]:
        prompt = f"Apply deductive closure to these statements:\n" + "\n".join(statements)
        response = await self._call_llm_gateway(prompt=prompt, model=model)
        return statements + response.split("\n")[:5]
    
    async def _verify_consistency(self, statements: List[str], model: str) -> bool:
        prompt = f"Are these statements logically consistent?\n" + "\n".join(statements)
        response = await self._call_llm_gateway(prompt=prompt, model=model, max_tokens=10)
        return "yes" in response.lower()
    
    def get_pattern_info(self) -> Dict[str, Any]:
        return {
            "name": "Deductive Closure Training (DCT)",
            "category": "Reasoning",
            "latency_impact": "Medium (20-40s)"
        }
