"""Route Request Use Case."""

import logging
import time
from typing import Optional

from services.mcp_gateway.application.dto.route_request import RouteRequest
from services.mcp_gateway.application.dto.routing_response import RoutingResponse
from services.mcp_gateway.domain.entities.mcp_instance import MCPInstance
from services.mcp_gateway.domain.entities.routing_decision import RoutingDecision
from services.mcp_gateway.domain.repositories.mcp_registry_repository import MCPRegistryRepository
from services.mcp_gateway.domain.value_objects.routing_strategy import RoutingStrategy

logger = logging.getLogger(__name__)


class RouteRequestUseCase:
    """
    Use case for routing a request to an appropriate MCP instance.
    
    Implements load balancing, health-based routing, and observability.
    """
    
    def __init__(
        self,
        registry: MCPRegistryRepository,
        default_strategy: RoutingStrategy = RoutingStrategy.LEAST_LOADED
    ):
        """
        Initialize the use case.
        
        Args:
            registry: Repository for MCP instance storage
            default_strategy: Default routing strategy to use
        """
        self.registry = registry
        self.default_strategy = default_strategy
        self._round_robin_index = 0
    
    async def execute(self, request: RouteRequest) -> RoutingResponse:
        """
        Route a request to an MCP instance.
        
        Args:
            request: Request to route
        
        Returns:
            Routing response with result
        
        Raises:
            ValueError: If no instances available
        """
        start_time = time.time()
        
        try:
            # Get available instances for the MCP
            instances = await self.registry.find_available(
                mcp_id=request.mcp_id,
                tier=request.tier
            )
            
            if not instances:
                logger.warning(
                    f"No available instances for mcp_id={request.mcp_id}, tier={request.tier}"
                )
                return RoutingResponse(
                    success=False,
                    status_code=503,
                    error_message=f"No available instances for {request.mcp_id}",
                    error_type="NO_INSTANCES_AVAILABLE"
                )
            
            # Create routing decision
            decision = RoutingDecision(
                request_id=request.request_id or f"req-{int(time.time() * 1000)}",
                mcp_type=request.mcp_id,
                strategy_used=self.default_strategy,
                available_instances=len(instances),
                considered_instances=[inst.id for inst in instances]
            )
            
            # Select instance using routing strategy
            selected = await self._select_instance(
                instances,
                self.default_strategy,
                request.session_id
            )
            
            if not selected:
                logger.error("Failed to select an instance despite having available instances")
                return RoutingResponse(
                    success=False,
                    status_code=503,
                    error_message="Failed to select an instance",
                    error_type="ROUTING_FAILED"
                )
            
            # Update decision
            decision.selected_instance_id = selected.id
            decision.selected_instance_url = selected.base_url
            decision.selection_score = self._calculate_score(selected)
            
            # Mark request start
            selected.mark_request_start()
            await self.registry.update(selected)
            
            # Build target URL
            target_url = f"{selected.base_url}{request.path}"
            if request.query_params:
                query_string = "&".join(
                    f"{k}={v}" for k, v in request.query_params.items()
                )
                target_url += f"?{query_string}"
            
            # Calculate response time
            response_time_ms = (time.time() - start_time) * 1000
            
            # Mark decision success
            decision.mark_success(response_time_ms)
            
            logger.info(
                f"Routed request {decision.request_id} to instance {selected.id} "
                f"({selected.mcp_id}) - {response_time_ms:.2f}ms"
            )
            
            # Return response with routing metadata
            # Note: Actual HTTP request execution would happen in infrastructure layer
            return RoutingResponse(
                success=True,
                status_code=200,
                body=None,  # Would be populated by HTTP client
                instance_id=selected.id,
                instance_url=target_url,
                response_time_ms=response_time_ms,
                strategy_used=self.default_strategy.value
            )
            
        except Exception as e:
            logger.error(f"Error routing request: {e}", exc_info=True)
            return RoutingResponse(
                success=False,
                status_code=500,
                error_message=str(e),
                error_type="INTERNAL_ERROR"
            )
    
    async def _select_instance(
        self,
        instances: list[MCPInstance],
        strategy: RoutingStrategy,
        session_id: Optional[str] = None
    ) -> Optional[MCPInstance]:
        """
        Select an instance using the specified strategy.
        
        Args:
            instances: Available instances
            strategy: Routing strategy to use
            session_id: Optional session ID for sticky sessions
        
        Returns:
            Selected instance, or None if selection fails
        """
        if not instances:
            return None
        
        # Filter to only routable instances
        routable = [inst for inst in instances if inst.is_available_for_routing()]
        
        if not routable:
            logger.warning("No routable instances available")
            return None
        
        if strategy == RoutingStrategy.ROUND_ROBIN:
            # Simple round-robin
            selected = routable[self._round_robin_index % len(routable)]
            self._round_robin_index += 1
            return selected
        
        elif strategy == RoutingStrategy.LEAST_LOADED:
            # Select instance with lowest load factor
            return min(routable, key=lambda inst: inst.get_load_factor())
        
        elif strategy == RoutingStrategy.RANDOM:
            # Random selection
            import random
            return random.choice(routable)
        
        elif strategy == RoutingStrategy.STICKY_SESSION:
            # Session-based routing (simplified)
            if session_id:
                # Use session_id hash to consistently select same instance
                session_hash = hash(session_id)
                return routable[session_hash % len(routable)]
            # Fall back to round-robin if no session
            return routable[self._round_robin_index % len(routable)]
        
        elif strategy == RoutingStrategy.PRIORITY:
            # Select highest priority instance
            return max(routable, key=lambda inst: inst.priority)
        
        else:
            # Default to first available
            return routable[0]
    
    def _calculate_score(self, instance: MCPInstance) -> float:
        """
        Calculate a routing score for the instance.
        
        Higher score = better choice
        
        Args:
            instance: Instance to score
        
        Returns:
            Score between 0.0 and 100.0
        """
        # Base score from priority and weight
        score = instance.priority * 0.5 + instance.weight * 0.3
        
        # Penalty for high load
        load_factor = instance.get_load_factor()
        load_penalty = load_factor * 20
        score -= load_penalty
        
        # Penalty for slow response times
        if instance.average_response_time_ms > 1000:
            response_penalty = min(20, (instance.average_response_time_ms - 1000) / 100)
            score -= response_penalty
        
        # Penalty for recent failures
        failure_penalty = instance.consecutive_failures * 5
        score -= failure_penalty
        
        return max(0.0, score)

