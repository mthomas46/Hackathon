"""Record Execution Use Case - Application Layer.

Handles recording of new executions and updating pattern performance metrics.
"""

import logging
from typing import Optional

from services.mcp_performance_store.domain.entities.orchestration_execution import OrchestrationExecution
from services.mcp_performance_store.domain.entities.pattern_performance import PatternPerformance
from services.mcp_performance_store.domain.repositories.execution_repository import (
    ExecutionRepository,
    DuplicateEntityError,
    RepositoryError,
)
from services.mcp_performance_store.domain.repositories.pattern_performance_repository import (
    PatternPerformanceRepository,
)

logger = logging.getLogger(__name__)


class RecordExecutionError(Exception):
    """Raised when recording an execution fails."""
    pass


class RecordExecutionUseCase:
    """
    Use case for recording orchestration executions.
    
    Records a new execution and automatically updates the corresponding
    pattern performance metrics if the execution is associated with a pattern.
    """
    
    def __init__(
        self,
        execution_repo: ExecutionRepository,
        pattern_repo: PatternPerformanceRepository
    ):
        """
        Initialize use case.
        
        Args:
            execution_repo: Repository for execution persistence
            pattern_repo: Repository for pattern performance persistence
        """
        self.execution_repo = execution_repo
        self.pattern_repo = pattern_repo
        logger.info("RecordExecutionUseCase initialized")
    
    async def execute(self, execution: OrchestrationExecution) -> None:
        """
        Record an execution and update pattern performance.
        
        Args:
            execution: The execution to record
            
        Raises:
            RecordExecutionError: If recording fails
        """
        try:
            # Step 1: Save execution
            logger.info(f"Recording execution: {execution.execution_id}")
            
            try:
                await self.execution_repo.save(execution)
                logger.info(f"Execution saved: {execution.execution_id}")
            except DuplicateEntityError:
                logger.warning(f"Execution already exists: {execution.execution_id}")
                raise RecordExecutionError(f"Execution {execution.execution_id} already exists")
            
            # Step 2: Update pattern performance (if pattern exists)
            if execution.pattern_name:
                await self._update_pattern_performance(execution)
            else:
                logger.debug(f"No pattern associated with execution {execution.execution_id}")
                
        except RecordExecutionError:
            raise
        except Exception as e:
            logger.error(f"Failed to record execution {execution.execution_id}: {e}", exc_info=True)
            raise RecordExecutionError(f"Failed to record execution: {e}")
    
    async def _update_pattern_performance(self, execution: OrchestrationExecution) -> None:
        """
        Update pattern performance metrics from execution.
        
        Args:
            execution: The execution to process
        """
        try:
            pattern_name = execution.pattern_name
            logger.debug(f"Updating performance for pattern: {pattern_name}")
            
            # Get existing performance or create new
            performance = await self.pattern_repo.get_by_pattern(pattern_name)
            
            if performance is None:
                logger.info(f"Creating new performance tracking for pattern: {pattern_name}")
                performance = PatternPerformance(pattern_name=pattern_name)
                
                # Update from execution
                performance.update_from_execution(execution)
                
                # Save new
                await self.pattern_repo.save(performance)
                logger.info(f"New pattern performance created: {pattern_name}")
            else:
                logger.debug(f"Updating existing pattern performance: {pattern_name}")
                
                # Update from execution
                performance.update_from_execution(execution)
                
                # Update existing
                await self.pattern_repo.update(performance)
                logger.info(f"Pattern performance updated: {pattern_name}")
                
        except Exception as e:
            # Log error but don't fail the entire operation
            # The execution was already saved
            logger.error(
                f"Failed to update pattern performance for {execution.pattern_name}: {e}",
                exc_info=True
            )
    
    async def record_batch(self, executions: list[OrchestrationExecution]) -> dict[str, int]:
        """
        Record multiple executions in batch.
        
        Args:
            executions: List of executions to record
            
        Returns:
            Dictionary with counts: {"success": N, "failed": M, "skipped": K}
        """
        logger.info(f"Recording batch of {len(executions)} executions")
        
        results = {"success": 0, "failed": 0, "skipped": 0}
        
        for execution in executions:
            try:
                await self.execute(execution)
                results["success"] += 1
            except RecordExecutionError as e:
                if "already exists" in str(e):
                    results["skipped"] += 1
                else:
                    results["failed"] += 1
                logger.warning(f"Failed to record {execution.execution_id}: {e}")
            except Exception as e:
                results["failed"] += 1
                logger.error(f"Unexpected error recording {execution.execution_id}: {e}")
        
        logger.info(f"Batch complete: {results}")
        return results
