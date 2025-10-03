"""
Workflow Integration - Phase 3 Day 3
Integrates Memory Agent with all 4 workflows for automatic result storage and artifact capture.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime

try:
    # Try relative imports first (when used within package)
    from ...domain.entities.memory_context import (
        MemoryContext,
        WorkflowResult,
        ArtifactLink,
        WorkflowType
    )
    from ...domain.services.context_manager import ContextManager
    from ...domain.services.artifact_linker import ArtifactLinker
except ImportError:
    # Fall back to absolute imports (when used from outside package)
    from domain.entities.memory_context import (
        MemoryContext,
        WorkflowResult,
        ArtifactLink,
        WorkflowType
    )
    from domain.services.context_manager import ContextManager
    from domain.services.artifact_linker import ArtifactLinker


class WorkflowIntegrationHelper:
    """
    Helper class for integrating Memory Agent with orchestrated workflows.
    
    This class provides convenience methods for workflows to automatically:
    - Store results in Memory Agent
    - Link artifacts as they're created
    - Track cross-service calls
    - Maintain context across workflow execution
    
    Part of Enhanced Roadmap v2.0 Phase 3 implementation.
    """
    
    def __init__(
        self,
        context_manager: ContextManager,
        artifact_linker: ArtifactLinker
    ):
        """
        Initialize Workflow Integration Helper.
        
        Args:
            context_manager: ContextManager instance
            artifact_linker: ArtifactLinker instance
        """
        self.context_manager = context_manager
        self.artifact_linker = artifact_linker
    
    async def store_workflow_a_result(
        self,
        workflow_id: str,
        feature_breakdown: Dict[str, Any],
        prompts_used: List[str],
        documents_generated: List[str],
        duration_ms: float,
        parent_workflow_id: Optional[str] = None
    ) -> WorkflowResult:
        """
        Store Workflow A (Feature Decomposition) result.
        
        Args:
            workflow_id: Workflow identifier
            feature_breakdown: Complete feature breakdown data
            prompts_used: List of prompt IDs used
            documents_generated: List of document IDs generated
            duration_ms: Execution duration in milliseconds
            parent_workflow_id: Parent workflow if this is a child
            
        Returns:
            WorkflowResult instance
        """
        # Store main result
        result = await self.context_manager.store_workflow_result(
            workflow_id=workflow_id,
            workflow_type=WorkflowType.WORKFLOW_A,
            result_data=feature_breakdown,
            success=True,
            duration_ms=duration_ms,
            services_called=["llm-gateway", "prompt-store", "analysis-service"],
            parent_workflow_id=parent_workflow_id
        )
        
        # Get context for artifact linking
        context = await self.context_manager.get_context(workflow_id)
        
        if context:
            # Link prompts used
            if prompts_used:
                await self.artifact_linker.bulk_link_prompts(
                    context=context,
                    prompt_ids=prompts_used,
                    metadata={"workflow": "decomposition", "stage": "generation"}
                )
            
            # Link documents generated
            if documents_generated:
                await self.artifact_linker.bulk_link_documents(
                    context=context,
                    document_ids=documents_generated,
                    metadata={"workflow": "decomposition", "type": "output"}
                )
            
            # Save updated context
            await self.context_manager._save_context(context)
        
        return result
    
    async def store_workflow_b_result(
        self,
        workflow_id: str,
        historical_context: Dict[str, Any],
        documents_retrieved: List[str],
        jira_tickets: List[str],
        confluence_pages: List[str],
        duration_ms: float,
        parent_workflow_id: Optional[str] = None
    ) -> WorkflowResult:
        """
        Store Workflow B (Historical Context) result.
        
        Args:
            workflow_id: Workflow identifier
            historical_context: Complete historical context data
            documents_retrieved: List of document IDs retrieved
            jira_tickets: List of Jira ticket IDs
            confluence_pages: List of Confluence page IDs
            duration_ms: Execution duration in milliseconds
            parent_workflow_id: Parent workflow if this is a child
            
        Returns:
            WorkflowResult instance
        """
        # Store main result
        result = await self.context_manager.store_workflow_result(
            workflow_id=workflow_id,
            workflow_type=WorkflowType.WORKFLOW_B,
            result_data=historical_context,
            success=True,
            duration_ms=duration_ms,
            services_called=["memory-agent", "doc-store", "source-agent"],
            parent_workflow_id=parent_workflow_id
        )
        
        # Get context for artifact linking
        context = await self.context_manager.get_context(workflow_id)
        
        if context:
            # Link retrieved documents
            if documents_retrieved:
                await self.artifact_linker.bulk_link_documents(
                    context=context,
                    document_ids=documents_retrieved,
                    metadata={"workflow": "historical_context", "source": "doc-store"}
                )
            
            # Link Jira tickets as custom artifacts
            for ticket_id in jira_tickets:
                await self.artifact_linker.link_custom_artifact(
                    context=context,
                    artifact_id=ticket_id,
                    artifact_type="jira_ticket",
                    source_service="jira",
                    artifact_url=f"https://jira.company.com/browse/{ticket_id}",
                    metadata={"workflow": "historical_context"}
                )
            
            # Link Confluence pages as custom artifacts
            for page_id in confluence_pages:
                await self.artifact_linker.link_custom_artifact(
                    context=context,
                    artifact_id=page_id,
                    artifact_type="confluence_page",
                    source_service="confluence",
                    artifact_url=f"https://confluence.company.com/pages/{page_id}",
                    metadata={"workflow": "historical_context"}
                )
            
            # Save updated context
            await self.context_manager._save_context(context)
        
        return result
    
    async def store_workflow_c_result(
        self,
        workflow_id: str,
        timeline_analysis: Dict[str, Any],
        simulation_results: List[str],
        reports_generated: List[str],
        duration_ms: float,
        parent_workflow_id: Optional[str] = None
    ) -> WorkflowResult:
        """
        Store Workflow C (Timeline Analysis) result.
        
        Args:
            workflow_id: Workflow identifier
            timeline_analysis: Complete timeline analysis data
            simulation_results: List of simulation result IDs
            reports_generated: List of report document IDs
            duration_ms: Execution duration in milliseconds
            parent_workflow_id: Parent workflow if this is a child
            
        Returns:
            WorkflowResult instance
        """
        # Store main result
        result = await self.context_manager.store_workflow_result(
            workflow_id=workflow_id,
            workflow_type=WorkflowType.WORKFLOW_C,
            result_data=timeline_analysis,
            success=True,
            duration_ms=duration_ms,
            services_called=["project-simulation", "analysis-service", "user-store"],
            parent_workflow_id=parent_workflow_id
        )
        
        # Get context for artifact linking
        context = await self.context_manager.get_context(workflow_id)
        
        if context:
            # Link simulation results as custom artifacts
            for sim_id in simulation_results:
                await self.artifact_linker.link_custom_artifact(
                    context=context,
                    artifact_id=sim_id,
                    artifact_type="simulation",
                    source_service="project-simulation",
                    artifact_url=f"http://project-simulation:5075/simulations/{sim_id}",
                    metadata={"workflow": "timeline_analysis"}
                )
            
            # Link generated reports
            if reports_generated:
                await self.artifact_linker.bulk_link_documents(
                    context=context,
                    document_ids=reports_generated,
                    metadata={"workflow": "timeline_analysis", "type": "report"}
                )
            
            # Save updated context
            await self.context_manager._save_context(context)
        
        return result
    
    async def store_workflow_d_result(
        self,
        workflow_id: str,
        skills_matching: Dict[str, Any],
        team_members: List[str],
        allocations: List[Dict[str, str]],
        duration_ms: float,
        parent_workflow_id: Optional[str] = None
    ) -> WorkflowResult:
        """
        Store Workflow D (Skills Matching) result.
        
        Args:
            workflow_id: Workflow identifier
            skills_matching: Complete skills matching data
            team_members: List of user IDs involved
            allocations: List of task allocations
            duration_ms: Execution duration in milliseconds
            parent_workflow_id: Parent workflow if this is a child
            
        Returns:
            WorkflowResult instance
        """
        # Store main result
        result = await self.context_manager.store_workflow_result(
            workflow_id=workflow_id,
            workflow_type=WorkflowType.WORKFLOW_D,
            result_data=skills_matching,
            success=True,
            duration_ms=duration_ms,
            services_called=["user-store", "project-planning"],
            parent_workflow_id=parent_workflow_id
        )
        
        # Get context for artifact linking
        context = await self.context_manager.get_context(workflow_id)
        
        if context:
            # Link team members
            if team_members:
                await self.artifact_linker.bulk_link_users(
                    context=context,
                    user_ids=team_members,
                    metadata={"workflow": "skills_matching", "role": "team_member"}
                )
            
            # Link allocations as custom artifacts
            for i, allocation in enumerate(allocations):
                await self.artifact_linker.link_custom_artifact(
                    context=context,
                    artifact_id=f"allocation_{workflow_id}_{i}",
                    artifact_type="allocation",
                    source_service="project-planning",
                    artifact_url=f"http://project-planning:8000/allocations/{workflow_id}_{i}",
                    metadata={
                        "workflow": "skills_matching",
                        "member_id": allocation.get("member_id"),
                        "task_id": allocation.get("task_id")
                    }
                )
            
            # Save updated context
            await self.context_manager._save_context(context)
        
        return result
    
    async def store_orchestration_result(
        self,
        workflow_id: str,
        orchestration_data: Dict[str, Any],
        child_workflow_ids: List[str],
        duration_ms: float
    ) -> WorkflowResult:
        """
        Store orchestration workflow result.
        
        Args:
            workflow_id: Workflow identifier
            orchestration_data: Complete orchestration data
            child_workflow_ids: List of child workflow IDs
            duration_ms: Execution duration in milliseconds
            
        Returns:
            WorkflowResult instance
        """
        # Store main result
        result = await self.context_manager.store_workflow_result(
            workflow_id=workflow_id,
            workflow_type=WorkflowType.ORCHESTRATION,
            result_data=orchestration_data,
            success=True,
            duration_ms=duration_ms,
            services_called=["orchestrator", "memory-agent"]
        )
        
        # Get context for cross-referencing child workflows
        context = await self.context_manager.get_context(workflow_id)
        
        if context:
            # Link child workflow results as custom artifacts
            for child_id in child_workflow_ids:
                await self.artifact_linker.link_custom_artifact(
                    context=context,
                    artifact_id=child_id,
                    artifact_type="workflow",
                    source_service="orchestrator",
                    artifact_url=f"http://orchestrator:5099/workflows/{child_id}",
                    metadata={"type": "child_workflow"}
                )
            
            # Save updated context
            await self.context_manager._save_context(context)
        
        return result
    
    async def get_workflow_context(
        self,
        workflow_id: str
    ) -> Optional[MemoryContext]:
        """
        Get complete context for a workflow.
        
        Args:
            workflow_id: Workflow identifier
            
        Returns:
            MemoryContext if found, None otherwise
        """
        return await self.context_manager.get_context(workflow_id)
    
    async def get_aggregated_results(
        self,
        parent_workflow_id: str
    ) -> Dict[str, Any]:
        """
        Get aggregated results from all child workflows.
        
        Args:
            parent_workflow_id: Parent workflow identifier
            
        Returns:
            Aggregated results dictionary
        """
        return await self.context_manager.aggregate_workflow_results(parent_workflow_id)
    
    async def get_synthesized_context(
        self,
        workflow_id: str
    ) -> Dict[str, Any]:
        """
        Get synthesized unified context view.
        
        Args:
            workflow_id: Workflow identifier
            
        Returns:
            Synthesized context dictionary
        """
        return await self.context_manager.synthesize_context(workflow_id)
    
    async def track_service_call(
        self,
        workflow_id: str,
        service_name: str,
        operation: str,
        duration_ms: float,
        success: bool,
        error_message: Optional[str] = None
    ) -> None:
        """
        Track a service call within a workflow.
        
        Args:
            workflow_id: Workflow identifier
            service_name: Name of service called
            operation: Operation performed
            duration_ms: Duration in milliseconds
            success: Whether call succeeded
            error_message: Error message if failed
        """
        context = await self.context_manager.get_context(workflow_id)
        
        if context:
            # Add service call to metadata
            if "service_calls" not in context.metadata:
                context.metadata["service_calls"] = []
            
            context.metadata["service_calls"].append({
                "service": service_name,
                "operation": operation,
                "duration_ms": duration_ms,
                "success": success,
                "error": error_message,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Save updated context
            await self.context_manager._save_context(context)
    
    async def link_workflow_artifacts(
        self,
        workflow_id: str,
        documents: Optional[List[str]] = None,
        prompts: Optional[List[str]] = None,
        users: Optional[List[str]] = None
    ) -> int:
        """
        Link multiple artifacts to a workflow at once.
        
        Args:
            workflow_id: Workflow identifier
            documents: List of document IDs to link
            prompts: List of prompt IDs to link
            users: List of user IDs to link
            
        Returns:
            Total number of artifacts linked
        """
        context = await self.context_manager.get_context(workflow_id)
        
        if not context:
            return 0
        
        total_linked = 0
        
        if documents:
            await self.artifact_linker.bulk_link_documents(context, documents)
            total_linked += len(documents)
        
        if prompts:
            await self.artifact_linker.bulk_link_prompts(context, prompts)
            total_linked += len(prompts)
        
        if users:
            await self.artifact_linker.bulk_link_users(context, users)
            total_linked += len(users)
        
        # Save updated context
        await self.context_manager._save_context(context)
        
        return total_linked

