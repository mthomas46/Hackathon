"""Workflow domain service."""

from typing import List, Optional
from datetime import datetime

from ..entities.workflow import Workflow
from ..entities.job import Job
from ..repositories.workflow_repository import WorkflowRepository
from ..repositories.job_repository import JobRepository
from ..value_objects.workflow_id import WorkflowId
from ..value_objects.workflow_status import WorkflowStatus
from ..value_objects.workflow_type import WorkflowType
from ..value_objects.job_id import JobId
from ..value_objects.job_status import JobStatus


class WorkflowService:
    """Domain service for workflow orchestration business logic."""

    def __init__(
        self,
        workflow_repository: WorkflowRepository,
        job_repository: JobRepository
    ):
        self.workflow_repository = workflow_repository
        self.job_repository = job_repository

    async def create_workflow(
        self,
        name: str,
        workflow_type: WorkflowType,
        parameters: dict,
        steps: List[dict],
        dependencies: Optional[List[str]] = None
    ) -> Workflow:
        """Create a new workflow."""
        workflow_id = WorkflowId.generate()
        workflow = Workflow(
            id=workflow_id,
            name=name,
            type=workflow_type,
            status=WorkflowStatus.PENDING,
            parameters=parameters,
            steps=steps,
            dependencies=dependencies or []
        )

        workflow.validate()
        await self.workflow_repository.save(workflow)

        return workflow

    async def start_workflow(self, workflow_id: WorkflowId) -> Workflow:
        """Start a workflow execution."""
        workflow = await self.workflow_repository.find_by_id(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        workflow.start()
        await self.workflow_repository.save(workflow)

        # Create initial jobs for workflow steps
        for step in workflow.steps:
            job_id = JobId.generate()
            job = Job(
                id=job_id,
                workflow_id=str(workflow_id),
                name=f"{workflow.name} - {step.get('name', 'Step')}",
                status=JobStatus.QUEUED,
                payload=step
            )
            await self.job_repository.save(job)

        return workflow

    async def complete_workflow(
        self,
        workflow_id: WorkflowId,
        result: Optional[dict] = None
    ) -> Workflow:
        """Complete a workflow."""
        workflow = await self.workflow_repository.find_by_id(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        workflow.complete(result)
        await self.workflow_repository.save(workflow)

        return workflow

    async def fail_workflow(self, workflow_id: WorkflowId, error: str) -> Workflow:
        """Mark a workflow as failed."""
        workflow = await self.workflow_repository.find_by_id(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        workflow.fail(error)
        await self.workflow_repository.save(workflow)

        return workflow

    async def cancel_workflow(self, workflow_id: WorkflowId) -> Workflow:
        """Cancel a workflow."""
        workflow = await self.workflow_repository.find_by_id(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        workflow.cancel()
        await self.workflow_repository.save(workflow)

        return workflow

    async def get_workflow(self, workflow_id: WorkflowId) -> Optional[Workflow]:
        """Get a workflow by ID."""
        return await self.workflow_repository.find_by_id(workflow_id)

    async def get_workflows_by_status(self, status: WorkflowStatus) -> List[Workflow]:
        """Get workflows by status."""
        return await self.workflow_repository.find_by_status(status)

    async def get_all_workflows(self) -> List[Workflow]:
        """Get all workflows."""
        return await self.workflow_repository.find_all()

    async def validate_workflow_dependencies(self, workflow: Workflow) -> bool:
        """Validate that all workflow dependencies exist and are completed."""
        if not workflow.dependencies:
            return True

        for dep_id in workflow.dependencies:
            dep_workflow = await self.workflow_repository.find_by_id(WorkflowId(dep_id))
            if not dep_workflow:
                return False
            if not dep_workflow.is_completed():
                return False

        return True
