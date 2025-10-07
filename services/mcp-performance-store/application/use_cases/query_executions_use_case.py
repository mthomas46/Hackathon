"""
Use case for querying orchestration executions.
"""
import logging
from typing import List

from services.mcp_performance_store.domain.repositories import PerformanceRepository
from services.mcp_performance_store.application.dto import (
    ExecutionQueryRequest,
    ExecutionResponse
)


class QueryExecutionsUseCase:
    """
    Use case for querying orchestration executions.
    
    Handles filtering, pagination, and conversion to response DTOs.
    """
    
    def __init__(self, repository: PerformanceRepository):
        """
        Initialize use case.
        
        Args:
            repository: Performance repository
        """
        self.repository = repository
        self.logger = logging.getLogger(__name__)
    
    async def execute(self, request: ExecutionQueryRequest) -> List[ExecutionResponse]:
        """
        Query orchestration executions with filters.
        
        Args:
            request: Query parameters
        
        Returns:
            List of execution responses
        """
        self.logger.info(
            f"Querying executions with filters: "
            f"mcp_id={request.mcp_id}, pattern={request.pattern_used}, "
            f"success={request.success}, limit={request.limit}"
        )
        
        # Query repository
        executions = await self.repository.list_executions(
            mcp_id=request.mcp_id,
            pattern_used=request.pattern_used,
            success=request.success,
            start_time=request.start_time,
            end_time=request.end_time,
            limit=request.limit,
            offset=request.offset
        )
        
        self.logger.info(f"Found {len(executions)} matching executions")
        
        # Convert to response DTOs
        return [self._to_response(execution) for execution in executions]
    
    async def get_execution_count(self, request: ExecutionQueryRequest) -> int:
        """
        Get count of matching executions.
        
        Args:
            request: Query parameters
        
        Returns:
            Count of matching executions
        """
        count = await self.repository.count_executions(
            mcp_id=request.mcp_id,
            pattern_used=request.pattern_used,
            success=request.success,
            start_time=request.start_time,
            end_time=request.end_time
        )
        
        return count
    
    def _to_response(self, execution) -> ExecutionResponse:
        """Convert execution entity to response DTO."""
        quality_score = execution.calculate_quality_score()
        
        return ExecutionResponse(
            execution_id=execution.execution_id,
            timestamp=execution.timestamp,
            query=execution.query,
            mcp_id=execution.mcp_id,
            mcp_version=execution.mcp_version,
            pattern_used=execution.pattern_used,
            composition_id=execution.composition_id,
            latency_ms=execution.latency_ms,
            token_usage=execution.token_usage,
            cost_cents=execution.cost_cents,
            success=execution.success,
            error=execution.error,
            accuracy_score=execution.accuracy_score,
            confidence=execution.confidence,
            hallucination_detected=execution.hallucination_detected,
            citation_count=execution.citation_count,
            user_satisfaction=execution.user_satisfaction,
            quality_score=quality_score,
            prompt_preview=execution.prompt[:200] + "..." if len(execution.prompt) > 200 else execution.prompt,
            response_preview=execution.response[:200] + "..." if len(execution.response) > 200 else execution.response,
            context_length=execution.context_length,
            sources_count=len(execution.retrieved_sources),
            environment=execution.environment,
            user_id=execution.user_id,
            session_id=execution.session_id,
            tags=execution.tags
        )
