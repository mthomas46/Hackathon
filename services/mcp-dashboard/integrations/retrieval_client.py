"""MCP Retrieval integration client - TIGHT COUPLING."""

import httpx
from typing import Dict, List, Optional, Any


class RetrievalClient:
    """
    Tightly integrated client for MCP Retrieval service.
    
    Provides seamless dashboard integration for:
    - Hierarchical context retrieval
    - Multi-tier search
    - Context pruning visualization
    - Token budget management
    """
    
    def __init__(self, base_url: str = "http://mcp-retrieval:8014"):
        """
        Initialize Retrieval client.
        
        Args:
            base_url: Retrieval service URL
        """
        self.base_url = base_url.rstrip('/')
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def hierarchical_retrieve(
        self,
        query: str,
        user_id: str,
        token_budget: int = 8000,
        tiers: Optional[List[str]] = None,
        strategy: str = "HYBRID",
        tier_weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Perform hierarchical retrieval across tiers.
        
        Args:
            query: Search query
            user_id: User identifier
            token_budget: Maximum tokens for context
            tiers: List of tiers to search (default: all accessible)
            strategy: Retrieval strategy (BOTTOM_UP, TOP_DOWN, HYBRID)
            tier_weights: Optional custom tier weights
        
        Returns:
            Hierarchical results by tier
        """
        payload = {
            "query": query,
            "user_id": user_id,
            "token_budget": token_budget,
            "strategy": strategy
        }
        
        if tiers:
            payload["tiers"] = tiers
        if tier_weights:
            payload["tier_weights"] = tier_weights
        
        response = await self.client.post(
            f"{self.base_url}/api/v1/retrieve",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    async def get_tier_results(
        self,
        retrieval_id: str,
        tier: str
    ) -> List[Dict[str, Any]]:
        """
        Get results for a specific tier from a retrieval operation.
        
        Args:
            retrieval_id: Retrieval operation ID
            tier: Tier name
        
        Returns:
            Documents from that tier
        """
        response = await self.client.get(
            f"{self.base_url}/api/v1/retrievals/{retrieval_id}/tiers/{tier}"
        )
        response.raise_for_status()
        return response.json()
    
    async def get_retrieval_stats(
        self,
        user_id: Optional[str] = None,
        mcp_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get retrieval statistics for analytics.
        
        Args:
            user_id: Optional user filter
            mcp_id: Optional MCP filter
        
        Returns:
            Statistics
        """
        params = {}
        if user_id:
            params["user_id"] = user_id
        if mcp_id:
            params["mcp_id"] = mcp_id
        
        response = await self.client.get(
            f"{self.base_url}/api/v1/stats",
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    async def configure_retrieval(
        self,
        user_id: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Configure retrieval settings for a user.
        
        Args:
            user_id: User identifier
            config: Retrieval configuration
        
        Returns:
            Updated configuration
        """
        response = await self.client.put(
            f"{self.base_url}/api/v1/config",
            json={"user_id": user_id, "config": config}
        )
        response.raise_for_status()
        return response.json()
    
    async def preview_context_pruning(
        self,
        documents: List[Dict[str, Any]],
        token_budget: int,
        strategy: str = "RELEVANCE"
    ) -> Dict[str, Any]:
        """
        Preview how context will be pruned (for visualization).
        
        Args:
            documents: Documents to prune
            token_budget: Target token budget
            strategy: Pruning strategy
        
        Returns:
            Pruning preview with before/after
        """
        payload = {
            "documents": documents,
            "token_budget": token_budget,
            "strategy": strategy
        }
        
        response = await self.client.post(
            f"{self.base_url}/api/v1/prune/preview",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    async def get_tier_hierarchy(self, user_id: str) -> Dict[str, Any]:
        """
        Get user's accessible tier hierarchy for visualization.
        
        Args:
            user_id: User identifier
        
        Returns:
            Hierarchical tier structure
        """
        response = await self.client.get(
            f"{self.base_url}/api/v1/hierarchy",
            params={"user_id": user_id}
        )
        response.raise_for_status()
        return response.json()
    
    async def compare_strategies(
        self,
        query: str,
        user_id: str,
        strategies: List[str]
    ) -> Dict[str, Any]:
        """
        Compare different retrieval strategies.
        
        Args:
            query: Search query
            user_id: User identifier
            strategies: List of strategies to compare
        
        Returns:
            Comparison results
        """
        payload = {
            "query": query,
            "user_id": user_id,
            "strategies": strategies
        }
        
        response = await self.client.post(
            f"{self.base_url}/api/v1/compare",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    async def get_document_details(
        self,
        document_id: str
    ) -> Dict[str, Any]:
        """
        Get detailed information about a document.
        
        Args:
            document_id: Document identifier
        
        Returns:
            Document details with metadata
        """
        response = await self.client.get(
            f"{self.base_url}/api/v1/documents/{document_id}"
        )
        response.raise_for_status()
        return response.json()
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

