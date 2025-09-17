"""Use Cases for Workflow Management"""

from typing import Optional, List, Tuple
from abc import ABC, abstractmethod

from .commands import *
from .queries import *
from ...domain.workflow_management import (
    Workflow, WorkflowExecution, WorkflowParameter, WorkflowAction,
    WorkflowId, ExecutionId, ParameterType, ActionType,
    WorkflowValidator, ParameterResolver, WorkflowExecutor
)


class UseCase(ABC):
    """Base class for all use cases."""

    @abstractmethod
    async def execute(self, *args, **kwargs):
        """Execute the use case."""
        pass


class CreateWorkflowUseCase(UseCase):
    """Use case for creating workflows."""

    def __init__(self, workflow_repository):
        self.workflow_repository = workflow_repository

    async def execute(self, command: CreateWorkflowCommand) -> Tuple[bool, str, Optional[Workflow]]:
        """Execute the create workflow use case."""
        try:
            # Create workflow entity
            workflow = Workflow(
                name=command.name,
                description=command.description,
                created_by=command.created_by,
                tags=command.tags
            )

            # Add parameters
            for param_data in command.parameters:
                param = WorkflowParameter(
                    name=param_data["name"],
                    param_type=ParameterType(param_data["type"]),
                    description=param_data.get("description", ""),
                    required=param_data.get("required", True),
                    default_value=param_data.get("default_value"),
                    validation_rules=param_data.get("validation_rules", {}),
                    allowed_values=param_data.get("allowed_values")
                )
                workflow.add_parameter(param)

            # Add actions
            for action_data in command.actions:
                action = WorkflowAction(
                    name=action_data["name"],
                    description=action_data.get("description", ""),
                    action_type=ActionType(action_data["action_type"]),
                    config=action_data["config"],
                    depends_on=action_data.get("depends_on", []),
                    retry_count=action_data.get("retry_count", 0),
                    timeout_seconds=action_data.get("timeout_seconds", 30)
                )
                workflow.add_action(action)

            # Validate workflow
            is_valid, validation_errors = WorkflowValidator.validate_workflow(workflow)
            if not is_valid:
                return False, f"Workflow validation failed: {', '.join(validation_errors)}", None

            # Save workflow
            if self.workflow_repository.save_workflow(workflow):
                return True, "Workflow created successfully", workflow
            else:
                return False, "Failed to save workflow", None

        except Exception as e:
            return False, f"Failed to create workflow: {str(e)}", None


class ExecuteWorkflowUseCase(UseCase):
    """Use case for executing workflows."""

    def __init__(self, workflow_repository, execution_repository, workflow_executor):
        self.workflow_repository = workflow_repository
        self.execution_repository = execution_repository
        self.workflow_executor = workflow_executor

    async def execute(self, command: ExecuteWorkflowCommand) -> Tuple[bool, str, Optional[WorkflowExecution]]:
        """Execute the workflow execution use case."""
        try:
            # Get workflow
            workflow = self.workflow_repository.get_workflow(command.workflow_id)
            if not workflow:
                return False, f"Workflow {command.workflow_id.value} not found", None

            # Validate parameters
            valid, error = workflow.validate_parameters(command.parameters)
            if not valid:
                return False, f"Parameter validation failed: {error}", None

            # Create execution
            execution = WorkflowExecution(
                workflow_id=command.workflow_id,
                correlation_id=command.correlation_id,
                trace_id=command.trace_id
            )

            # Start execution
            execution.start(
                parameters=command.parameters,
                correlation_id=command.correlation_id,
                trace_id=command.trace_id
            )

            # Save execution
            if not self.execution_repository.save_execution(execution):
                return False, "Failed to save execution", None

            # Execute workflow asynchronously
            # In a real implementation, this would be handled by a background task
            # For now, we'll execute synchronously
            executed_execution = await self.workflow_executor.execute_workflow(workflow, execution)

            # Update execution in repository
            self.execution_repository.update_execution(executed_execution)

            return True, "Workflow execution completed", executed_execution

        except Exception as e:
            return False, f"Failed to execute workflow: {str(e)}", None


class GetWorkflowUseCase(UseCase):
    """Use case for getting a workflow."""

    def __init__(self, workflow_repository):
        self.workflow_repository = workflow_repository

    async def execute(self, query: GetWorkflowQuery) -> Optional[Workflow]:
        """Execute the get workflow use case."""
        return self.workflow_repository.get_workflow(query.workflow_id)


class ListWorkflowsUseCase(UseCase):
    """Use case for listing workflows."""

    def __init__(self, workflow_repository):
        self.workflow_repository = workflow_repository

    async def execute(self, query: ListWorkflowsQuery) -> List[Workflow]:
        """Execute the list workflows use case."""
        return self.workflow_repository.list_workflows(
            name_filter=query.name_filter,
            tag_filter=query.tag_filter,
            status_filter=query.status_filter,
            created_by_filter=query.created_by_filter,
            limit=query.limit,
            offset=query.offset
        )
