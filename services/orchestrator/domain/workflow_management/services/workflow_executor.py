"""Workflow Executor Domain Service"""

import asyncio
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime

from ..entities.workflow import Workflow
from ..entities.workflow_execution import WorkflowExecution
from ..entities.workflow_action import WorkflowAction
from ..value_objects.action_result import ActionResult, ActionStatus


class WorkflowExecutor:
    """Domain service for executing workflows."""

    def __init__(self, action_executor_factory: Callable = None):
        """Initialize with optional action executor factory."""
        self.action_executor_factory = action_executor_factory or self._default_action_executor

    async def execute_workflow(
        self,
        workflow: Workflow,
        execution: WorkflowExecution,
        external_services: Optional[Dict[str, Any]] = None
    ) -> WorkflowExecution:
        """Execute a workflow and update the execution entity."""
        try:
            # Execute actions in dependency order
            action_results = await self._execute_actions(workflow, execution.parameters, external_services)

            # Update execution with results
            for result in action_results.values():
                execution.add_action_result(result)

            # Check if execution was successful
            failed_actions = [r for r in action_results.values() if r.has_error]
            if failed_actions:
                error_msg = f"Actions failed: {', '.join(r.action_id for r in failed_actions)}"
                execution.fail(error_msg)
            else:
                execution.complete()

        except Exception as e:
            execution.fail(str(e))

        return execution

    async def _execute_actions(
        self,
        workflow: Workflow,
        parameters: Dict[str, Any],
        external_services: Optional[Dict[str, Any]] = None
    ) -> Dict[str, ActionResult]:
        """Execute all actions in the workflow."""
        results = {}
        pending_actions = {action.action_id: action for action in workflow.actions}

        # Execute actions in topological order
        while pending_actions:
            # Find actions that can be executed (no pending dependencies)
            executable_actions = self._get_executable_actions(pending_actions, results)

            if not executable_actions:
                # Circular dependency or dependency issue
                remaining_ids = list(pending_actions.keys())
                for action_id in remaining_ids:
                    results[action_id] = ActionResult.skipped(action_id)
                break

            # Execute actions concurrently
            execution_tasks = []
            for action in executable_actions:
                task = asyncio.create_task(
                    self._execute_action(action, parameters, results, external_services)
                )
                execution_tasks.append((action.action_id, task))

            # Wait for all to complete
            for action_id, task in execution_tasks:
                try:
                    result = await task
                    results[action_id] = result
                except Exception as e:
                    results[action_id] = ActionResult.failure(
                        action_id,
                        f"Execution failed: {str(e)}",
                        0
                    )
                finally:
                    del pending_actions[action_id]

        return results

    def _get_executable_actions(
        self,
        pending_actions: Dict[str, WorkflowAction],
        results: Dict[str, ActionResult]
    ) -> List[WorkflowAction]:
        """Get actions that can be executed (all dependencies satisfied)."""
        executable = []

        for action in pending_actions.values():
            can_execute = True

            # Check dependencies
            for dep_id in action.depends_on:
                if dep_id not in results:
                    can_execute = False
                    break
                dep_result = results[dep_id]
                if not dep_result.is_successful:
                    can_execute = False
                    break

            if can_execute:
                executable.append(action)

        return executable

    async def _execute_action(
        self,
        action: WorkflowAction,
        parameters: Dict[str, Any],
        previous_results: Dict[str, ActionResult],
        external_services: Optional[Dict[str, Any]] = None
    ) -> ActionResult:
        """Execute a single action."""
        start_time = datetime.utcnow()

        try:
            # Check if action should be skipped based on condition
            if not action.can_execute({k: v.output for k, v in previous_results.items()}):
                return ActionResult.skipped(action.action_id)

            # Execute the action
            result = await self.action_executor_factory(action, parameters, external_services)

            execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            return ActionResult.success(action.action_id, result, execution_time)

        except Exception as e:
            execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            return ActionResult.failure(action.action_id, str(e), execution_time)

    async def _default_action_executor(
        self,
        action: WorkflowAction,
        parameters: Dict[str, Any],
        external_services: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Default action executor - should be replaced with proper implementation."""
        # This is a placeholder - in real implementation, this would delegate
        # to specific executors based on action type
        if action.action_type.value == "service_call":
            return await self._execute_service_call(action, parameters, external_services)
        elif action.action_type.value == "prompt_execution":
            return await self._execute_prompt(action, parameters, external_services)
        else:
            raise NotImplementedError(f"Action type {action.action_type.value} not implemented")

    async def _execute_service_call(
        self,
        action: WorkflowAction,
        parameters: Dict[str, Any],
        external_services: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Execute a service call action."""
        # Placeholder implementation
        service_name = action.config.get("service")
        endpoint = action.config.get("endpoint")

        if external_services and service_name in external_services:
            service_client = external_services[service_name]
            # Make actual service call here
            return {"status": "success", "service": service_name, "endpoint": endpoint}

        return {"status": "mock_success", "service": service_name, "endpoint": endpoint}

    async def _execute_prompt(
        self,
        action: WorkflowAction,
        parameters: Dict[str, Any],
        external_services: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Execute a prompt action."""
        # Placeholder implementation
        prompt_id = action.config.get("prompt_id")

        return {"status": "success", "prompt_id": prompt_id, "output": "Mock prompt response"}
