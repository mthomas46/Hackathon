"""Multi-MCP routing engine."""

from typing import Dict, Any, List, Tuple, Optional
import asyncio
import httpx
import logging
from datetime import datetime

from services.mcp_composer.domain.entities import (
    Composition,
    MCPReference,
    CompositionStrategy,
    ConflictResolution
)


class RoutingEngine:
    """
    Routes queries to multiple MCPs based on composition strategy.
    
    Handles sequential, parallel, hierarchical, weighted, and fallback routing.
    """
    
    def __init__(
        self,
        mcp_gateway_url: str = "http://mcp-gateway:5641",
        timeout: int = 60
    ):
        self.mcp_gateway_url = mcp_gateway_url
        self.timeout = timeout
        self.http_client = httpx.AsyncClient(timeout=timeout)
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def route_query(
        self,
        query: str,
        composition: Composition,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Route a query to MCPs according to the composition strategy.
        
        Args:
            query: The user query
            composition: The composition defining routing
            context: Optional additional context
        
        Returns:
            Dictionary containing responses from MCPs
        """
        self.logger.info(
            f"Routing query via {composition.strategy.value} strategy to "
            f"{len(composition.mcps)} MCPs"
        )
        
        start_time = datetime.now()
        
        try:
            if composition.strategy == CompositionStrategy.SEQUENTIAL:
                results = await self._route_sequential(query, composition, context)
            elif composition.strategy == CompositionStrategy.PARALLEL:
                results = await self._route_parallel(query, composition, context)
            elif composition.strategy == CompositionStrategy.HIERARCHICAL:
                results = await self._route_hierarchical(query, composition, context)
            elif composition.strategy == CompositionStrategy.WEIGHTED:
                results = await self._route_weighted(query, composition, context)
            elif composition.strategy == CompositionStrategy.FALLBACK:
                results = await self._route_fallback(query, composition, context)
            else:
                raise ValueError(f"Unknown strategy: {composition.strategy}")
            
            elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            self.logger.info(f"Routing completed in {elapsed_ms:.0f}ms")
            
            return {
                "query": query,
                "composition_id": composition.composition_id,
                "strategy": composition.strategy.value,
                "mcp_responses": results,
                "elapsed_ms": elapsed_ms,
                "timestamp": start_time.isoformat()
            }
        
        except Exception as e:
            self.logger.error(f"Routing error: {e}")
            raise
    
    async def _route_sequential(
        self,
        query: str,
        composition: Composition,
        context: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Route sequentially through MCPs."""
        results = []
        accumulated_context = context or {}
        
        for mcp in composition.get_sorted_mcps():
            try:
                response = await self._query_mcp(
                    mcp, query, accumulated_context
                )
                results.append({
                    "mcp_id": mcp.mcp_id,
                    "tier": mcp.tier,
                    "success": True,
                    "response": response
                })
                
                # Accumulate context for next MCP
                if response.get("context"):
                    accumulated_context.update(response["context"])
                
            except Exception as e:
                self.logger.error(f"MCP {mcp.mcp_id} failed: {e}")
                results.append({
                    "mcp_id": mcp.mcp_id,
                    "tier": mcp.tier,
                    "success": False,
                    "error": str(e)
                })
                
                if mcp.required:
                    raise
        
        return results
    
    async def _route_parallel(
        self,
        query: str,
        composition: Composition,
        context: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Route in parallel to all MCPs."""
        tasks = [
            self._query_mcp_safe(mcp, query, context)
            for mcp in composition.mcps
        ]
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        results = []
        for mcp, response in zip(composition.mcps, responses):
            if isinstance(response, Exception):
                results.append({
                    "mcp_id": mcp.mcp_id,
                    "tier": mcp.tier,
                    "success": False,
                    "error": str(response)
                })
            else:
                results.append({
                    "mcp_id": mcp.mcp_id,
                    "tier": mcp.tier,
                    "success": True,
                    "response": response
                })
        
        return results
    
    async def _route_hierarchical(
        self,
        query: str,
        composition: Composition,
        context: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Route hierarchically through MCP tiers.
        
        Order: ecosystem -> team -> company -> project -> client
        """
        tier_order = ["ecosystem", "team", "company", "project", "client"]
        results = []
        accumulated_context = context or {}
        
        for tier in tier_order:
            tier_mcps = composition.get_mcps_by_tier(tier)
            if not tier_mcps:
                continue
            
            self.logger.info(f"Processing tier: {tier} ({len(tier_mcps)} MCPs)")
            
            # Query MCPs in tier in parallel
            tasks = [
                self._query_mcp_safe(mcp, query, accumulated_context)
                for mcp in tier_mcps
            ]
            
            tier_responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            for mcp, response in zip(tier_mcps, tier_responses):
                if isinstance(response, Exception):
                    results.append({
                        "mcp_id": mcp.mcp_id,
                        "tier": mcp.tier,
                        "success": False,
                        "error": str(response)
                    })
                else:
                    results.append({
                        "mcp_id": mcp.mcp_id,
                        "tier": mcp.tier,
                        "success": True,
                        "response": response
                    })
                    
                    # Accumulate context for next tier
                    if response.get("context"):
                        accumulated_context.update(response["context"])
        
        return results
    
    async def _route_weighted(
        self,
        query: str,
        composition: Composition,
        context: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Route to MCPs and weight their responses.
        Similar to parallel but includes weights.
        """
        # Query all in parallel
        results = await self._route_parallel(query, composition, context)
        
        # Add weights to results
        for result, mcp in zip(results, composition.mcps):
            result["weight"] = mcp.weight
        
        return results
    
    async def _route_fallback(
        self,
        query: str,
        composition: Composition,
        context: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Route with fallback strategy.
        Try MCPs in priority order until one succeeds.
        """
        results = []
        
        for mcp in composition.get_sorted_mcps():
            try:
                response = await self._query_mcp(mcp, query, context)
                results.append({
                    "mcp_id": mcp.mcp_id,
                    "tier": mcp.tier,
                    "success": True,
                    "response": response,
                    "used_as_primary": True
                })
                
                # Success! Stop here unless we need to query all
                if not composition.metadata.get("query_all", False):
                    break
                
            except Exception as e:
                self.logger.warning(f"MCP {mcp.mcp_id} failed, trying next: {e}")
                results.append({
                    "mcp_id": mcp.mcp_id,
                    "tier": mcp.tier,
                    "success": False,
                    "error": str(e),
                    "tried_as_fallback": True
                })
        
        if not any(r.get("success") for r in results):
            raise RuntimeError("All MCPs in fallback chain failed")
        
        return results
    
    async def _query_mcp(
        self,
        mcp: MCPReference,
        query: str,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Query a single MCP."""
        self.logger.debug(f"Querying MCP: {mcp.mcp_id}")
        
        payload = {
            "mcp_id": mcp.mcp_id,
            "query": query,
            "context": context or {},
            "tier": mcp.tier,
            "timeout_ms": mcp.timeout_ms
        }
        
        # Route through MCP Gateway
        response = await self.http_client.post(
            f"{self.mcp_gateway_url}/api/v1/query",
            json=payload,
            timeout=mcp.timeout_ms / 1000
        )
        
        response.raise_for_status()
        return response.json()
    
    async def _query_mcp_safe(
        self,
        mcp: MCPReference,
        query: str,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Query MCP with retry logic."""
        last_error = None
        
        for attempt in range(mcp.retry_count):
            try:
                return await self._query_mcp(mcp, query, context)
            except Exception as e:
                last_error = e
                if attempt < mcp.retry_count - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    self.logger.warning(
                        f"MCP {mcp.mcp_id} attempt {attempt + 1} failed, "
                        f"retrying in {wait_time}s: {e}"
                    )
                    await asyncio.sleep(wait_time)
        
        raise last_error
    
    async def close(self):
        """Close HTTP client."""
        await self.http_client.aclose()
