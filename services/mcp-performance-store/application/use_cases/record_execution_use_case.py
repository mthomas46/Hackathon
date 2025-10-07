"""
Use case for recording orchestration executions.
"""
import logging
from datetime import datetime
from typing import Optional

from services.mcp_performance_store.domain.entities import OrchestrationExecution
from services.mcp_performance_store.domain.repositories import PerformanceRepository
from services.mcp_performance_store.application.dto import (
    RecordExecutionRequest,
    ExecutionResponse
)


class RecordExecutionUseCase:
    """
    Use case for recording orchestration execution metrics.
    
    Handles the business logic for saving execution data and
    updating aggregated pattern performance metrics.
    """
    
    def __init__(self, repository: PerformanceRepository):
        """
        Initialize use case.
        
        Args:
            repository: Performance repository
        """
        self.repository = repository
        self.logger = logging.getLogger(__name__)
    
    async def execute(self, request: RecordExecutionRequest) -> ExecutionResponse:
        """
        Record a new orchestration execution.
        
        Args:
            request: Execution data to record
        
        Returns:
            Response containing execution details
        """
        self.logger.info(
            f"Recording execution for MCP {request.mcp_id} "
            f"with pattern {request.pattern_used}"
        )
        
        # Create execution entity
        execution = OrchestrationExecution(
            timestamp=datetime.utcnow(),
            query=request.query,
            mcp_id=request.mcp_id,
            mcp_version=request.mcp_version,
            pattern_used=request.pattern_used,
            composition_id=request.composition_id,
            latency_ms=request.latency_ms,
            token_usage=request.token_usage,
            cost_cents=request.cost_cents,
            success=request.success,
            error=request.error,
            accuracy_score=request.accuracy_score,
            confidence=request.confidence,
            hallucination_detected=request.hallucination_detected,
            citation_count=request.citation_count,
            user_satisfaction=request.user_satisfaction,
            prompt=request.prompt,
            response=request.response,
            context_length=request.context_length,
            retrieved_sources=request.retrieved_sources,
            environment=request.environment,
            user_id=request.user_id,
            session_id=request.session_id,
            tags=request.tags,
            metadata=request.metadata
        )
        
        # Save to repository
        execution_id = await self.repository.save_execution(execution)
        
        self.logger.info(f"Execution recorded with ID: {execution_id}")
        
        # Update pattern performance metrics asynchronously
        # (In production, this could be a background task)
        try:
            await self._update_pattern_performance(execution)
        except Exception as e:
            self.logger.error(f"Failed to update pattern performance: {e}")
            # Don't fail the request if metrics update fails
        
        # Convert to response DTO
        return self._to_response(execution)
    
    async def _update_pattern_performance(self, execution: OrchestrationExecution):
        """
        Update aggregated pattern performance metrics.
        
        This is a simplified implementation. In production, this would:
        1. Use TimescaleDB continuous aggregates
        2. Update in batches/background jobs
        3. Handle concurrent updates properly
        """
        # Get existing pattern performance or create new
        pattern_performance = await self.repository.get_pattern_performance_by_name(
            execution.pattern_used,
            execution.mcp_version
        )
        
        if pattern_performance is None:
            # Create new pattern performance entry
            # In production, this would be more sophisticated
            self.logger.info(
                f"Creating new pattern performance entry for {execution.pattern_used}"
            )
            # For now, we'll just log - full implementation would create a new entry
        else:
            # Update existing metrics
            # In production, this would recalculate aggregates from continuous aggregates
            self.logger.debug(
                f"Pattern performance exists for {execution.pattern_used}"
            )
    
    def _to_response(self, execution: OrchestrationExecution) -> ExecutionResponse:
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
