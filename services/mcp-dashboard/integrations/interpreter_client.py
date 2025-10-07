"""MCP Interpreter integration client - TIGHT COUPLING."""

import httpx
from typing import Dict, List, Optional, Any


class InterpreterClient:
    """
    Tightly integrated client for MCP Interpreter service.
    
    Provides seamless dashboard integration for:
    - Natural language query parsing
    - Intent visualization
    - Entity extraction
    - Query suggestions
    """
    
    def __init__(self, base_url: str = "http://mcp-interpreter:8002"):
        """
        Initialize Interpreter client.
        
        Args:
            base_url: Interpreter service URL
        """
        self.base_url = base_url.rstrip('/')
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def interpret_query(
        self,
        query: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Interpret natural language query.
        
        Args:
            query: User's natural language query
            user_id: User identifier
            session_id: Session identifier
            context: Additional context
        
        Returns:
            Interpretation result with intent, entities, confidence
        """
        payload = {
            "query": query,
            "context": context or {}
        }
        
        if user_id:
            payload["context"]["user_id"] = user_id
        if session_id:
            payload["context"]["session_id"] = session_id
        
        response = await self.client.post(
            f"{self.base_url}/api/v1/interpret",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    async def get_interpretation_history(
        self,
        user_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get user's interpretation history for query history display.
        
        Args:
            user_id: User identifier
            limit: Max results
        
        Returns:
            List of past interpretations
        """
        response = await self.client.get(
            f"{self.base_url}/api/v1/history",
            params={"user_id": user_id, "limit": limit}
        )
        response.raise_for_status()
        return response.json()
    
    async def get_suggested_queries(
        self,
        user_id: Optional[str] = None,
        context: Optional[str] = None
    ) -> List[str]:
        """
        Get suggested queries for quick actions.
        
        Args:
            user_id: Optional user ID for personalized suggestions
            context: Optional context for contextual suggestions
        
        Returns:
            List of suggested query strings
        """
        params = {}
        if user_id:
            params["user_id"] = user_id
        if context:
            params["context"] = context
        
        response = await self.client.get(
            f"{self.base_url}/api/v1/suggestions",
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    async def get_intent_details(self, intent_id: str) -> Dict[str, Any]:
        """
        Get detailed information about an intent.
        
        Args:
            intent_id: Intent identifier
        
        Returns:
            Intent details including examples, patterns
        """
        response = await self.client.get(
            f"{self.base_url}/api/v1/intents/{intent_id}"
        )
        response.raise_for_status()
        return response.json()
    
    async def refine_query(
        self,
        original_query: str,
        interpretation: Dict[str, Any],
        refinement_hints: List[str]
    ) -> str:
        """
        Refine a query based on interpretation and hints.
        
        Args:
            original_query: Original query string
            interpretation: Previous interpretation
            refinement_hints: User-provided refinement hints
        
        Returns:
            Refined query string
        """
        payload = {
            "original_query": original_query,
            "interpretation": interpretation,
            "refinement_hints": refinement_hints
        }
        
        response = await self.client.post(
            f"{self.base_url}/api/v1/refine",
            json=payload
        )
        response.raise_for_status()
        return response.json()["refined_query"]
    
    async def validate_query(self, query: str) -> Dict[str, Any]:
        """
        Validate query before execution.
        
        Args:
            query: Query to validate
        
        Returns:
            Validation result
        """
        response = await self.client.post(
            f"{self.base_url}/api/v1/validate",
            json={"query": query}
        )
        response.raise_for_status()
        return response.json()
    
    async def get_common_intents(self) -> List[Dict[str, Any]]:
        """
        Get list of common intents for UI display.
        
        Returns:
            List of intents with names, descriptions, examples
        """
        response = await self.client.get(
            f"{self.base_url}/api/v1/intents"
        )
        response.raise_for_status()
        return response.json()
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

