"""Execute Workflow Use Case."""

import logging
from typing import Optional
import uuid

from services.mcp_orchestrator.application.dto.execute_workflow_request import ExecuteWorkflowRequest
from services.mcp_orchestrator.application.dto.execution_result import ExecutionResult
from services.mcp_orchestrator.domain.entities.workflow import Workflow
from services.mcp_orchestrator.domain.repositories.workflow_repository import WorkflowRepository
from services.mcp_orchestrator.domain.value_objects.workflow_state import WorkflowState

logger = logging.getLogger(__name__)


class ExecuteWorkflowUseCase:
    """
    Use case for executing a workflow.
    
    This orchestrates the complete workflow execution:
    1. Validate workflow is ready
    2. Execute steps in order
    3. Apply LLM patterns
    4. Aggregate results
    5. Update workflow state
    """
    
    def __init__(
        self,
        workflow_repository: WorkflowRepository,
        mcp_gateway_client=None,  # MCPGatewayClient
        llm_gateway_client=None,  # LLMGatewayClient
    ):
        """
        Initialize the use case.
        
        Args:
            workflow_repository: Repository for workflows
            mcp_gateway_client: Client for MCP Gateway
            llm_gateway_client: Client for LLM Gateway
        """
        self.workflow_repository = workflow_repository
        self.mcp_gateway_client = mcp_gateway_client
        self.llm_gateway_client = llm_gateway_client
    
    async def execute(self, request: ExecuteWorkflowRequest) -> ExecutionResult:
        """
        Execute a workflow.
        
        Args:
            request: Execute workflow request
        
        Returns:
            Execution result
        """
        execution_id = str(uuid.uuid4())
        
        try:
            logger.info(f"Executing workflow {request.workflow_id} (execution: {execution_id})")
            
            # Step 1: Load workflow
            workflow = await self._load_workflow(request.workflow_id)
            if not workflow:
                raise ValueError(f"Workflow {request.workflow_id} not found")
            
            # Step 2: Validate workflow is ready
            self._validate_workflow_ready(workflow, request)
            
            # Step 3: Transition to EXECUTING state
            workflow.transition_to(WorkflowState.EXECUTING)
            await self.workflow_repository.save(workflow)
            
            # Step 4: Execute the workflow
            if request.async_execution:
                # For async execution, trigger background task and return immediately
                # In production, this would use Celery or similar
                logger.info(f"Starting async execution for workflow {workflow.id}")
                # TODO: Queue background task
                
                return ExecutionResult(
                    workflow_id=workflow.id,
                    execution_id=execution_id,
                    success=True,
                    state="executing",
                    message="Workflow execution started asynchronously",
                    result_data=None,
                    confidence_score=0.0,
                    steps_completed=0,
                    steps_total=len(workflow.execution_plan.steps) if workflow.execution_plan else 0,
                    queries_executed=0,
                    patterns_applied=[],
                    started_at=workflow.started_at.isoformat() if workflow.started_at else "",
                    completed_at="",
                    duration_ms=0.0,
                    error_message=None,
                    failed_step=None,
                )
            else:
                # Synchronous execution
                result = await self._execute_workflow_sync(workflow, request)
                await self.workflow_repository.save(workflow)
                return result
                
        except Exception as e:
            logger.error(f"Error executing workflow {request.workflow_id}: {e}", exc_info=True)
            
            # Try to load and mark workflow as failed
            try:
                workflow = await self._load_workflow(request.workflow_id)
                if workflow:
                    workflow.fail(str(e))
                    await self.workflow_repository.save(workflow)
                    
                    return ExecutionResult.failure_result(
                        workflow_id=workflow.id,
                        execution_id=execution_id,
                        error=str(e),
                        workflow=workflow,
                    )
            except Exception as save_error:
                logger.error(f"Error saving failed workflow: {save_error}")
            
            raise
    
    async def _load_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Load workflow from repository."""
        return await self.workflow_repository.find_by_id(workflow_id)
    
    def _validate_workflow_ready(self, workflow: Workflow, request: ExecuteWorkflowRequest) -> None:
        """
        Validate workflow is ready for execution.
        
        Args:
            workflow: Workflow to validate
            request: Execute request
        
        Raises:
            ValueError: If workflow is not ready
        """
        # Check state
        if workflow.state not in {WorkflowState.READY, WorkflowState.PENDING}:
            raise ValueError(f"Workflow is in state {workflow.state.value}, cannot execute")
        
        # Check execution plan exists
        if not workflow.execution_plan:
            raise ValueError("Workflow has no execution plan")
        
        # Check approval if required
        if workflow.execution_plan.requires_approval and not workflow.execution_plan.is_approved:
            if not request.approval_token or not request.approved_by:
                raise ValueError("Workflow requires approval but no approval provided")
            
            # Approve the plan
            workflow.execution_plan.approve(request.approved_by)
    
    async def _execute_workflow_sync(
        self,
        workflow: Workflow,
        request: ExecuteWorkflowRequest
    ) -> ExecutionResult:
        """
        Execute workflow synchronously.
        
        Args:
            workflow: Workflow to execute
            request: Execute request
        
        Returns:
            Execution result
        """
        try:
            # Execute steps in order based on strategy
            plan = workflow.execution_plan
            
            while not plan.is_complete():
                # Get steps ready to execute
                ready_steps = plan.get_ready_steps()
                
                if not ready_steps:
                    # No more steps ready, check if we're stuck
                    if plan.has_failures():
                        break  # Some steps failed
                    else:
                        break  # All done or waiting on dependencies
                
                # Execute ready steps
                for step in ready_steps:
                    await self._execute_step(step, workflow)
                
                # Update workflow progress
                workflow.update_progress()
                await self.workflow_repository.save(workflow)
            
            # Aggregate results
            workflow.transition_to(WorkflowState.AGGREGATING)
            await self.workflow_repository.save(workflow)
            
            final_result = await self._aggregate_results(workflow)
            
            # Complete workflow
            workflow.complete_successfully(
                result=final_result,
                confidence=plan.confidence_score
            )
            await self.workflow_repository.save(workflow)
            
            logger.info(f"Workflow {workflow.id} completed successfully")
            
            return ExecutionResult.success_result(
                workflow_id=workflow.id,
                execution_id=str(uuid.uuid4()),
                result_data=final_result,
                workflow=workflow,
            )
            
        except Exception as e:
            logger.error(f"Error in workflow execution: {e}", exc_info=True)
            workflow.fail(str(e))
            await self.workflow_repository.save(workflow)
            
            return ExecutionResult.failure_result(
                workflow_id=workflow.id,
                execution_id=str(uuid.uuid4()),
                error=str(e),
                workflow=workflow,
            )
    
    async def _execute_step(self, step, workflow: Workflow) -> None:
        """
        Execute a single workflow step.
        
        Args:
            step: WorkflowStep to execute
            workflow: Parent workflow
        """
        logger.info(f"Executing step {step.name} (id: {step.id})")
        
        step.start_execution()
        
        try:
            # Execute queries in this step
            # For now, this is a placeholder
            # In production, would query MCPs through gateway
            
            # Simulate step execution
            step_result = {
                "status": "success",
                "data": {},
                "step_name": step.name,
            }
            
            step.complete_execution(
                result=step_result,
                confidence=0.8
            )
            
            logger.info(f"Step {step.name} completed successfully")
            
        except Exception as e:
            logger.error(f"Step {step.name} failed: {e}")
            step.fail_execution(str(e))
            raise
    
    async def _aggregate_results(self, workflow: Workflow) -> dict:
        """
        Aggregate results from all completed steps.
        
        Args:
            workflow: Workflow with completed steps
        
        Returns:
            Aggregated results
        """
        plan = workflow.execution_plan
        
        aggregated = {
            "query": workflow.original_query,
            "intent": workflow.query_intent,
            "results": [],
            "summary": {},
        }
        
        # Collect results from all steps
        for step in plan.steps:
            if step.status == "completed" and step.result_data:
                aggregated["results"].append({
                    "step": step.name,
                    "data": step.result_data,
                    "confidence": step.confidence_score,
                })
        
        # Apply aggregation patterns if specified
        # For now, simple aggregation
        aggregated["summary"] = {
            "total_steps": len(plan.steps),
            "successful_steps": len([s for s in plan.steps if s.status == "completed"]),
            "patterns_applied": [p.value for p in workflow.applied_patterns],
        }
        
        return aggregated

