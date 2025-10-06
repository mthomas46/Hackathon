"""Create Workflow Use Case."""

import logging
from typing import Optional

from services.mcp_orchestrator.application.dto.create_workflow_request import CreateWorkflowRequest
from services.mcp_orchestrator.application.dto.workflow_response import WorkflowResponse
from services.mcp_orchestrator.domain.entities.workflow import Workflow
from services.mcp_orchestrator.domain.entities.execution_plan import ExecutionPlan
from services.mcp_orchestrator.domain.entities.workflow_step import WorkflowStep
from services.mcp_orchestrator.domain.repositories.workflow_repository import WorkflowRepository
from services.mcp_orchestrator.domain.value_objects.execution_strategy import ExecutionStrategy
from services.mcp_orchestrator.domain.value_objects.llm_pattern import LLMPattern
from services.mcp_orchestrator.domain.value_objects.mcp_selection_criteria import MCPSelectionCriteria
from services.mcp_orchestrator.domain.value_objects.workflow_state import WorkflowState

logger = logging.getLogger(__name__)


class CreateWorkflowUseCase:
    """
    Use case for creating a new workflow.
    
    This includes:
    1. Creating the workflow entity
    2. Planning the execution (selecting MCPs, strategies, patterns)
    3. Creating the execution plan
    4. Persisting the workflow
    """
    
    def __init__(
        self,
        workflow_repository: WorkflowRepository,
        mcp_gateway_client=None,  # Will be MCPGatewayClient
    ):
        """
        Initialize the use case.
        
        Args:
            workflow_repository: Repository for workflows
            mcp_gateway_client: Client for MCP Gateway service
        """
        self.workflow_repository = workflow_repository
        self.mcp_gateway_client = mcp_gateway_client
    
    async def execute(self, request: CreateWorkflowRequest) -> WorkflowResponse:
        """
        Create a new workflow.
        
        Args:
            request: Create workflow request
        
        Returns:
            Workflow response with plan
        """
        try:
            logger.info(f"Creating workflow for query: {request.original_query[:50]}...")
            
            # Step 1: Create workflow entity
            workflow = self._create_workflow_entity(request)
            
            # Step 2: Select execution strategy
            strategy = self._select_execution_strategy(request, workflow)
            
            # Step 3: Select LLM patterns
            patterns = self._select_llm_patterns(request, workflow)
            
            # Step 4: Create MCP selection criteria
            criteria = self._create_mcp_selection_criteria(request)
            
            # Step 5: Select MCPs (if gateway available)
            selected_mcps = await self._select_mcps(criteria)
            
            # Step 6: Create execution plan
            execution_plan = self._create_execution_plan(
                workflow,
                strategy,
                patterns,
                criteria,
                selected_mcps
            )
            
            # Step 7: Attach plan to workflow
            workflow.set_execution_plan(execution_plan)
            
            # Step 8: Transition to PLANNING state
            workflow.transition_to(WorkflowState.PLANNING)
            
            # Step 9: If approval required, wait for approval
            if request.requires_approval:
                execution_plan.requires_approval = True
                logger.info(f"Workflow {workflow.id} requires approval")
            else:
                # Auto-transition to READY
                workflow.transition_to(WorkflowState.READY)
            
            # Step 10: Persist workflow
            await self.workflow_repository.save(workflow)
            
            logger.info(
                f"Created workflow {workflow.id}: "
                f"strategy={strategy.value}, "
                f"patterns={len(patterns)}, "
                f"mcps={len(selected_mcps)}"
            )
            
            return WorkflowResponse.from_entity(workflow)
            
        except Exception as e:
            logger.error(f"Error creating workflow: {e}", exc_info=True)
            raise
    
    def _create_workflow_entity(self, request: CreateWorkflowRequest) -> Workflow:
        """Create workflow entity from request."""
        workflow = Workflow(
            name=f"Workflow for: {request.original_query[:50]}...",
            description=f"Orchestrated query workflow",
            original_query=request.original_query,
            parsed_query_id=request.parsed_query_id or "",
            query_intent=request.query_intent or "unknown",
            query_complexity=request.query_complexity or 5,
            user_id=request.user_id,
            session_id=request.session_id,
            metadata=request.metadata,
        )
        return workflow
    
    def _select_execution_strategy(
        self,
        request: CreateWorkflowRequest,
        workflow: Workflow
    ) -> ExecutionStrategy:
        """Select execution strategy based on request and workflow."""
        # If explicitly provided, use it
        if request.execution_strategy:
            return ExecutionStrategy(request.execution_strategy)
        
        # Otherwise, recommend based on query characteristics
        num_mcps = len(request.required_tiers or [1])
        requires_high_accuracy = workflow.query_complexity >= 7
        time_sensitive = "urgent" in workflow.original_query.lower()
        budget_constrained = request.max_cost is not None
        
        return ExecutionStrategy.get_recommended(
            num_mcps=num_mcps,
            requires_high_accuracy=requires_high_accuracy,
            time_sensitive=time_sensitive,
            budget_constrained=budget_constrained,
        )
    
    def _select_llm_patterns(
        self,
        request: CreateWorkflowRequest,
        workflow: Workflow
    ) -> list[LLMPattern]:
        """Select LLM patterns to apply."""
        # If explicitly provided, use them
        if request.patterns_to_apply:
            return [LLMPattern(p) for p in request.patterns_to_apply]
        
        # Otherwise, recommend based on query characteristics
        requires_high_accuracy = workflow.query_complexity >= 7
        budget_constrained = request.max_cost is not None
        
        return LLMPattern.get_recommended_patterns(
            query_complexity=workflow.query_complexity,
            requires_high_accuracy=requires_high_accuracy,
            budget_constrained=budget_constrained,
        )
    
    def _create_mcp_selection_criteria(
        self,
        request: CreateWorkflowRequest
    ) -> MCPSelectionCriteria:
        """Create MCP selection criteria from request."""
        required_tiers = request.required_tiers or [4]  # Default to ECOSYSTEM tier
        
        return MCPSelectionCriteria(
            required_tiers=required_tiers,
            client_ids=set(request.client_ids) if request.client_ids else None,
            project_ids=set(request.project_ids) if request.project_ids else None,
            team_ids=set(request.team_ids) if request.team_ids else None,
            prefer_hot_instances=True,
            max_mcps=10,  # Reasonable default
        )
    
    async def _select_mcps(self, criteria: MCPSelectionCriteria) -> list[str]:
        """
        Select MCPs that match criteria.
        
        Args:
            criteria: Selection criteria
        
        Returns:
            List of MCP instance IDs
        """
        # If gateway client available, query for available MCPs
        if self.mcp_gateway_client:
            # This would call MCP Gateway to get available instances
            # For now, return empty list
            pass
        
        # Fallback: Return empty list (will be populated during execution)
        return []
    
    def _create_execution_plan(
        self,
        workflow: Workflow,
        strategy: ExecutionStrategy,
        patterns: list[LLMPattern],
        criteria: MCPSelectionCriteria,
        selected_mcps: list[str],
    ) -> ExecutionPlan:
        """
        Create execution plan with steps.
        
        Args:
            workflow: Workflow entity
            strategy: Execution strategy
            patterns: LLM patterns to apply
            criteria: MCP selection criteria
            selected_mcps: Selected MCP IDs
        
        Returns:
            Execution plan with steps
        """
        plan = ExecutionPlan(
            workflow_id=workflow.id,
            strategy=strategy,
            selection_criteria=criteria,
            selected_mcp_ids=selected_mcps,
        )
        
        # Create steps based on patterns
        # For now, create a simple plan with basic steps
        
        # Step 1: Query execution
        query_step = WorkflowStep(
            workflow_id=workflow.id,
            name="Query Execution",
            description="Execute queries across selected MCPs",
            sequence_number=0,
            patterns=patterns,
        )
        plan.add_step(query_step)
        
        # Step 2: Aggregation (depends on step 1)
        aggregation_step = WorkflowStep(
            workflow_id=workflow.id,
            name="Result Aggregation",
            description="Aggregate results from all MCPs",
            sequence_number=1,
            depends_on_steps=[query_step.id],
            patterns=[LLMPattern.ANALYSIS] if LLMPattern.ANALYSIS in patterns else [],
        )
        plan.add_step(aggregation_step)
        
        # Step 3: Refinement (if self-critique pattern)
        if LLMPattern.SELF_CRITIQUE in patterns:
            refinement_step = WorkflowStep(
                workflow_id=workflow.id,
                name="Result Refinement",
                description="Self-critique and refine results",
                sequence_number=2,
                depends_on_steps=[aggregation_step.id],
                patterns=[LLMPattern.SELF_CRITIQUE],
            )
            plan.add_step(refinement_step)
        
        # Estimate duration and cost
        plan.estimated_duration_ms = len(plan.steps) * 2000  # Simple estimate
        plan.estimated_cost = len(selected_mcps) * 0.01  # Simple estimate
        plan.confidence_score = 0.8  # Initial confidence
        
        return plan

