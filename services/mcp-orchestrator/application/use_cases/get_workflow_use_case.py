"""Get Workflow Use Case."""

import logging
from typing import Optional

from services.mcp_orchestrator.application.dto.workflow_response import WorkflowResponse, WorkflowSummaryResponse
from services.mcp_orchestrator.domain.repositories.workflow_repository import WorkflowRepository

logger = logging.getLogger(__name__)


class GetWorkflowUseCase:
    """
    Use case for retrieving workflow information.
    
    Provides methods to get workflow details and summaries.
    """
    
    def __init__(self, workflow_repository: WorkflowRepository):
        """
        Initialize the use case.
        
        Args:
            workflow_repository: Repository for workflows
        """
        self.workflow_repository = workflow_repository
    
    async def execute(self, workflow_id: str) -> Optional[WorkflowResponse]:
        """
        Get workflow by ID.
        
        Args:
            workflow_id: Workflow ID
        
        Returns:
            Workflow response if found, None otherwise
        """
        try:
            workflow = await self.workflow_repository.find_by_id(workflow_id)
            
            if not workflow:
                logger.warning(f"Workflow {workflow_id} not found")
                return None
            
            return WorkflowResponse.from_entity(workflow)
            
        except Exception as e:
            logger.error(f"Error getting workflow {workflow_id}: {e}", exc_info=True)
            raise
    
    async def get_user_workflows(
        self,
        user_id: str,
        limit: Optional[int] = None
    ) -> list[WorkflowSummaryResponse]:
        """
        Get workflows for a user.
        
        Args:
            user_id: User ID
            limit: Optional limit
        
        Returns:
            List of workflow summaries
        """
        try:
            workflows = await self.workflow_repository.find_by_user_id(user_id, limit)
            return [WorkflowSummaryResponse.from_entity(w) for w in workflows]
            
        except Exception as e:
            logger.error(f"Error getting workflows for user {user_id}: {e}", exc_info=True)
            raise
    
    async def get_active_workflows(
        self,
        limit: Optional[int] = None
    ) -> list[WorkflowSummaryResponse]:
        """
        Get all active workflows.
        
        Args:
            limit: Optional limit
        
        Returns:
            List of active workflow summaries
        """
        try:
            workflows = await self.workflow_repository.find_active_workflows(limit)
            return [WorkflowSummaryResponse.from_entity(w) for w in workflows]
            
        except Exception as e:
            logger.error(f"Error getting active workflows: {e}", exc_info=True)
            raise

