#!/usr/bin/env python3
"""
Workflow Management Service

Business logic layer for workflow operations including creation, validation, and execution.
"""

import asyncio
import json
import uuid
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta

from services.orchestrator.modules.workflow_management.models import (
    WorkflowDefinition, WorkflowExecution, WorkflowParameter, WorkflowAction,
    ActionType, WorkflowStatus, WorkflowExecutionStatus, ParameterType,
    create_workflow_from_template
)
from services.orchestrator.modules.workflow_management.repository import WorkflowRepository

# Import event bridge for workflow events
try:
    from services.orchestrator.modules.workflow_event_bridge import (
        emit_workflow_created_event,
        emit_workflow_started_event,
        emit_workflow_completed_event,
        emit_workflow_failed_event,
        emit_step_event
    )
    EVENT_BRIDGE_AVAILABLE = True
except ImportError:
    EVENT_BRIDGE_AVAILABLE = False

from services.shared.constants_new import ServiceNames
from services.shared.logging import fire_and_forget


class WorkflowManagementService:
    """Service for managing workflows and their executions."""

    def __init__(self):
        self.repository = WorkflowRepository()
        self.active_executions: Dict[str, WorkflowExecution] = {}
        self.execution_tasks: Dict[str, asyncio.Task] = {}

    # Workflow Definition Operations

    async def create_workflow(self, workflow_data: Dict[str, Any], created_by: str) -> Tuple[bool, str, Optional[WorkflowDefinition]]:
        """Create a new workflow definition."""
        try:
            # Validate input data
            if not workflow_data.get("name"):
                return False, "Workflow name is required", None

            # Create workflow definition
            workflow = WorkflowDefinition(
                name=workflow_data["name"],
                description=workflow_data.get("description", ""),
                created_by=created_by,
                tags=workflow_data.get("tags", [])
            )

            # Add parameters
            for param_data in workflow_data.get("parameters", []):
                param = WorkflowParameter(
                    name=param_data["name"],
                    type=ParameterType(param_data["type"]),
                    description=param_data.get("description", ""),
                    required=param_data.get("required", True),
                    default_value=param_data.get("default_value"),
                    validation_rules=param_data.get("validation_rules", {}),
                    allowed_values=param_data.get("allowed_values")
                )
                workflow.add_parameter(param)

            # Add actions
            for action_data in workflow_data.get("actions", []):
                action = WorkflowAction(
                    action_type=ActionType(action_data["action_type"]),
                    name=action_data["name"],
                    description=action_data.get("description", ""),
                    config=action_data["config"],
                    depends_on=action_data.get("depends_on", []),
                    retry_count=action_data.get("retry_count", 0),
                    timeout_seconds=action_data.get("timeout_seconds", 30)
                )
                workflow.add_action(action)

            # Validate workflow
            is_valid, validation_errors = self._validate_workflow(workflow)
            if not is_valid:
                return False, f"Workflow validation failed: {', '.join(validation_errors)}", None

            # Save workflow
            if self.repository.save_workflow_definition(workflow):
                fire_and_forget("info", f"Created workflow: {workflow.workflow_id}", ServiceNames.ORCHESTRATOR)

                # Emit workflow created event
                if EVENT_BRIDGE_AVAILABLE:
                    try:
                        await emit_workflow_created_event(
                            workflow.workflow_id,
                            workflow_data,
                            created_by
                        )
                    except Exception as e:
                        fire_and_forget("warning", f"Failed to emit workflow created event: {e}", ServiceNames.ORCHESTRATOR)

                return True, "Workflow created successfully", workflow
            else:
                return False, "Failed to save workflow", None

        except Exception as e:
            fire_and_forget("error", f"Failed to create workflow: {e}", ServiceNames.ORCHESTRATOR)
            return False, f"Failed to create workflow: {str(e)}", None

    async def create_workflow_from_template(self, template_name: str, customizations: Dict[str, Any],
                                          created_by: str) -> Tuple[bool, str, Optional[WorkflowDefinition]]:
        """Create a workflow from a predefined template."""
        try:
            # Create workflow from template
            workflow = create_workflow_from_template(template_name, customizations)
            workflow.created_by = created_by

            # Validate workflow
            is_valid, validation_errors = self._validate_workflow(workflow)
            if not is_valid:
                return False, f"Workflow validation failed: {', '.join(validation_errors)}", None

            # Save workflow
            if self.repository.save_workflow_definition(workflow):
                fire_and_forget("info", f"Created workflow from template '{template_name}': {workflow.workflow_id}", ServiceNames.ORCHESTRATOR)
                return True, "Workflow created from template successfully", workflow
            else:
                return False, "Failed to save workflow", None

        except Exception as e:
            fire_and_forget("error", f"Failed to create workflow from template: {e}", ServiceNames.ORCHESTRATOR)
            return False, f"Failed to create workflow from template: {str(e)}", None

    async def get_workflow(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        """Get a workflow definition by ID."""
        return self.repository.get_workflow_definition(workflow_id)

    async def list_workflows(self, filters: Dict[str, Any] = None) -> List[WorkflowDefinition]:
        """List workflow definitions with optional filters."""
        return self.repository.list_workflow_definitions(filters)

    async def search_workflows(self, query: str, limit: int = 50) -> List[WorkflowDefinition]:
        """Search workflows by name, description, or tags."""
        return self.repository.search_workflow_definitions(query, limit)

    async def update_workflow(self, workflow_id: str, updates: Dict[str, Any],
                            updated_by: str) -> Tuple[bool, str]:
        """Update an existing workflow definition."""
        try:
            workflow = await self.get_workflow(workflow_id)
            if not workflow:
                return False, "Workflow not found"

            # Check if workflow is active and has executions
            if workflow.status == WorkflowStatus.ACTIVE and workflow.total_executions > 0:
                # Create a new version instead of updating
                new_workflow = WorkflowDefinition(
                    name=updates.get("name", workflow.name),
                    description=updates.get("description", workflow.description),
                    version=self._increment_version(workflow.version),
                    created_by=updated_by,
                    tags=updates.get("tags", workflow.tags)
                )

                # Copy parameters and actions
                for param in workflow.parameters:
                    new_workflow.add_parameter(param)
                for action in workflow.actions:
                    new_workflow.add_action(action)

                # Apply updates
                if "parameters" in updates:
                    new_workflow.parameters = []
                    for param_data in updates["parameters"]:
                        new_workflow.add_parameter(WorkflowParameter(**param_data))

                if "actions" in updates:
                    new_workflow.actions = []
                    for action_data in updates["actions"]:
                        new_workflow.add_action(WorkflowAction(**action_data))

                # Validate and save new version
                is_valid, validation_errors = self._validate_workflow(new_workflow)
                if not is_valid:
                    return False, f"Workflow validation failed: {', '.join(validation_errors)}"

                if self.repository.save_workflow_definition(new_workflow):
                    fire_and_forget("info", f"Created new version of workflow: {new_workflow.workflow_id}", ServiceNames.ORCHESTRATOR)
                    return True, f"New workflow version created: {new_workflow.workflow_id}"
                else:
                    return False, "Failed to save new workflow version"

            else:
                # Update existing workflow
                if "name" in updates:
                    workflow.name = updates["name"]
                if "description" in updates:
                    workflow.description = updates["description"]
                if "tags" in updates:
                    workflow.tags = updates["tags"]
                if "status" in updates:
                    workflow.status = WorkflowStatus(updates["status"])

                # Update parameters and actions if provided
                if "parameters" in updates:
                    workflow.parameters = []
                    for param_data in updates["parameters"]:
                        workflow.add_parameter(WorkflowParameter(**param_data))

                if "actions" in updates:
                    workflow.actions = []
                    for action_data in updates["actions"]:
                        workflow.add_action(WorkflowAction(**action_data))

                workflow.updated_at = datetime.now()

                # Validate and save
                is_valid, validation_errors = self._validate_workflow(workflow)
                if not is_valid:
                    return False, f"Workflow validation failed: {', '.join(validation_errors)}"

                if self.repository.save_workflow_definition(workflow):
                    fire_and_forget("info", f"Updated workflow: {workflow_id}", ServiceNames.ORCHESTRATOR)
                    return True, "Workflow updated successfully"
                else:
                    return False, "Failed to update workflow"

        except Exception as e:
            fire_and_forget("error", f"Failed to update workflow: {e}", ServiceNames.ORCHESTRATOR)
            return False, f"Failed to update workflow: {str(e)}"

    async def delete_workflow(self, workflow_id: str) -> Tuple[bool, str]:
        """Delete a workflow definition."""
        try:
            workflow = await self.get_workflow(workflow_id)
            if not workflow:
                return False, "Workflow not found"

            # Check if workflow has active executions
            active_executions = [eid for eid, exec in self.active_executions.items()
                               if exec.workflow_id == workflow_id and exec.status == WorkflowExecutionStatus.RUNNING]

            if active_executions:
                return False, f"Cannot delete workflow with {len(active_executions)} active executions"

            if self.repository.delete_workflow_definition(workflow_id):
                fire_and_forget("info", f"Deleted workflow: {workflow_id}", ServiceNames.ORCHESTRATOR)
                return True, "Workflow deleted successfully"
            else:
                return False, "Failed to delete workflow"

        except Exception as e:
            fire_and_forget("error", f"Failed to delete workflow: {e}", ServiceNames.ORCHESTRATOR)
            return False, f"Failed to delete workflow: {str(e)}"

    # Workflow Execution Operations

    async def execute_workflow(self, workflow_id: str, input_parameters: Dict[str, Any],
                             initiated_by: str) -> Tuple[bool, str, Optional[WorkflowExecution]]:
        """Execute a workflow with given parameters."""
        try:
            # Get workflow definition
            workflow = await self.get_workflow(workflow_id)
            if not workflow:
                return False, "Workflow not found", None

            if workflow.status != WorkflowStatus.ACTIVE:
                return False, f"Workflow is not active (status: {workflow.status.value})", None

            # Validate input parameters
            is_valid, validation_errors = workflow.validate_parameters(input_parameters)
            if not is_valid:
                return False, f"Parameter validation failed: {'; '.join(validation_errors)}", None

            # Create execution instance
            execution = WorkflowExecution(
                workflow_id=workflow_id,
                initiated_by=initiated_by,
                input_parameters=input_parameters
            )

            # Save execution to database
            if not self.repository.save_workflow_execution(execution):
                return False, "Failed to save workflow execution", None

            # Start execution asynchronously
            execution.start_execution()
            self.active_executions[execution.execution_id] = execution

            # Update workflow execution stats
            workflow.update_execution_stats(False, 0)  # Will be updated when execution completes
            self.repository.save_workflow_definition(workflow)

            # Start execution task
            execution_task = asyncio.create_task(self._execute_workflow_async(execution, workflow))
            self.execution_tasks[execution.execution_id] = execution_task

            fire_and_forget("info", f"Started workflow execution: {execution.execution_id}", ServiceNames.ORCHESTRATOR)

            # Emit workflow started event
            if EVENT_BRIDGE_AVAILABLE:
                try:
                    await emit_workflow_started_event(
                        workflow_id,
                        execution.execution_id,
                        input_parameters,
                        initiated_by
                    )
                except Exception as e:
                    fire_and_forget("warning", f"Failed to emit workflow started event: {e}", ServiceNames.ORCHESTRATOR)

            return True, "Workflow execution started", execution

        except Exception as e:
            fire_and_forget("error", f"Failed to execute workflow: {e}", ServiceNames.ORCHESTRATOR)
            return False, f"Failed to execute workflow: {str(e)}", None

    async def get_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get a workflow execution by ID."""
        # Check active executions first
        if execution_id in self.active_executions:
            return self.active_executions[execution_id]

        # Check database
        return self.repository.get_workflow_execution(execution_id)

    async def list_executions(self, workflow_id: str = None, status: WorkflowExecutionStatus = None,
                            limit: int = 100) -> List[WorkflowExecution]:
        """List workflow executions with optional filters."""
        return self.repository.list_workflow_executions(workflow_id, status, limit)

    async def cancel_execution(self, execution_id: str, cancelled_by: str) -> Tuple[bool, str]:
        """Cancel a running workflow execution."""
        try:
            execution = self.active_executions.get(execution_id)
            if not execution:
                return False, "Execution not found or already completed"

            if execution.status != WorkflowExecutionStatus.RUNNING:
                return False, f"Cannot cancel execution with status: {execution.status.value}"

            # Cancel the execution task
            if execution_id in self.execution_tasks:
                self.execution_tasks[execution_id].cancel()

                # Mark execution as cancelled
                execution.status = WorkflowExecutionStatus.CANCELLED
                execution.completed_at = datetime.now()
                execution.execution_time_seconds = (execution.completed_at - (execution.started_at or execution.completed_at)).total_seconds()

                # Save updated execution
                self.repository.save_workflow_execution(execution)

                # Remove from active executions
                del self.active_executions[execution_id]
                del self.execution_tasks[execution_id]

                fire_and_forget("info", f"Cancelled workflow execution: {execution_id}", ServiceNames.ORCHESTRATOR)
                return True, "Workflow execution cancelled successfully"

            return False, "Execution task not found"

        except Exception as e:
            fire_and_forget("error", f"Failed to cancel execution: {e}", ServiceNames.ORCHESTRATOR)
            return False, f"Failed to cancel execution: {str(e)}"

    # Internal execution methods

    async def _execute_workflow_async(self, execution: WorkflowExecution, workflow: WorkflowDefinition):
        """Execute a workflow asynchronously."""
        try:
            start_time = datetime.now()

            # Execute workflow actions
            success, output_data, error_message = await self._execute_workflow_actions(execution, workflow)

            # Complete execution
            execution_time = (datetime.now() - start_time).total_seconds()
            execution.complete_execution(success, output_data)

            if not success and error_message:
                execution.fail_execution(error_message)

            # Update workflow statistics
            workflow.update_execution_stats(success, execution_time)
            self.repository.save_workflow_definition(workflow)

            # Save execution results
            self.repository.save_workflow_execution(execution)

            # Remove from active executions
            if execution.execution_id in self.active_executions:
                del self.active_executions[execution.execution_id]

            if execution.execution_id in self.execution_tasks:
                del self.execution_tasks[execution.execution_id]

            fire_and_forget("info", f"Completed workflow execution: {execution.execution_id} (success: {success})", ServiceNames.ORCHESTRATOR)

            # Emit workflow completion event
            if EVENT_BRIDGE_AVAILABLE:
                try:
                    if success:
                        await emit_workflow_completed_event(
                            execution.workflow_id,
                            execution.execution_id,
                            output_data or {},
                            execution_time,
                            execution.initiated_by
                        )
                    else:
                        await emit_workflow_failed_event(
                            execution.workflow_id,
                            execution.execution_id,
                            error_message or "Unknown error",
                            execution_time,
                            execution.initiated_by
                        )
                except Exception as e:
                    fire_and_forget("warning", f"Failed to emit workflow completion event: {e}", ServiceNames.ORCHESTRATOR)

        except Exception as e:
            # Handle execution errors
            execution.fail_execution(f"Execution failed: {str(e)}")
            self.repository.save_workflow_execution(execution)

            # Cleanup
            if execution.execution_id in self.active_executions:
                del self.active_executions[execution.execution_id]
            if execution.execution_id in self.execution_tasks:
                del self.execution_tasks[execution.execution_id]

            fire_and_forget("error", f"Workflow execution failed: {execution.execution_id} - {e}", ServiceNames.ORCHESTRATOR)

            # Emit workflow failure event for exceptions
            if EVENT_BRIDGE_AVAILABLE:
                try:
                    execution_time = (datetime.now() - start_time).total_seconds() if 'start_time' in locals() else 0
                    await emit_workflow_failed_event(
                        execution.workflow_id,
                        execution.execution_id,
                        f"Execution exception: {str(e)}",
                        execution_time,
                        execution.initiated_by
                    )
                except Exception as event_error:
                    fire_and_forget("warning", f"Failed to emit workflow failure event: {event_error}", ServiceNames.ORCHESTRATOR)

    async def _execute_workflow_actions(self, execution: WorkflowExecution,
                                      workflow: WorkflowDefinition) -> Tuple[bool, Dict[str, Any], Optional[str]]:
        """Execute workflow actions according to dependencies."""
        # Get execution plan
        execution_plan = workflow.get_execution_plan()

        # Context for storing action results
        context = {
            "execution_id": execution.execution_id,
            "workflow_id": workflow.workflow_id,
            "input_parameters": execution.input_parameters.copy(),
            "action_results": {},
            "global_variables": {}
        }

        try:
            # Execute actions level by level
            for level_actions in execution_plan:
                # Execute actions in this level concurrently
                level_tasks = []

                for action_id in level_actions:
                    action = workflow.get_action(action_id)
                    if action:
                        task = asyncio.create_task(self._execute_action(action, context, execution))
                        level_tasks.append((action_id, task))

                # Wait for all actions in this level to complete
                for action_id, task in level_tasks:
                    try:
                        result = await task
                        execution.update_action_result(action_id, result)
                        context["action_results"][action_id] = result

                        if not result.get("success", False):
                            return False, {}, f"Action {action_id} failed: {result.get('error', 'Unknown error')}"

                    except Exception as e:
                        error_result = {
                            "success": False,
                            "error": str(e),
                            "execution_time": 0.0
                        }
                        execution.update_action_result(action_id, error_result)
                        return False, {}, f"Action {action_id} failed: {str(e)}"

            return True, context.get("global_variables", {}), None

        except Exception as e:
            return False, {}, f"Workflow execution failed: {str(e)}"

    async def _execute_action(self, action: WorkflowAction, context: Dict[str, Any],
                            execution: WorkflowExecution) -> Dict[str, Any]:
        """Execute a single workflow action."""
        start_time = datetime.now()

        try:
            # Check conditional execution
            if action.condition and not self._evaluate_condition(action.condition, context):
                return {
                    "success": True,
                    "skipped": True,
                    "reason": "Condition not met",
                    "execution_time": 0.0
                }

            execution.current_action = action.action_id

            # Execute based on action type
            if action.action_type == ActionType.SERVICE_CALL:
                result = await self._execute_service_call(action, context)
            elif action.action_type == ActionType.PROMPT_EXECUTION:
                result = await self._execute_prompt_execution(action, context)
            elif action.action_type == ActionType.TRANSFORM_DATA:
                result = await self._execute_data_transformation(action, context)
            elif action.action_type == ActionType.WAIT:
                result = await self._execute_wait(action, context)
            elif action.action_type == ActionType.NOTIFICATION:
                result = await self._execute_notification(action, context)
            else:
                result = {
                    "success": False,
                    "error": f"Unsupported action type: {action.action_type.value}"
                }

            execution_time = (datetime.now() - start_time).total_seconds()
            result["execution_time"] = execution_time

            return result

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return {
                "success": False,
                "error": str(e),
                "execution_time": execution_time
            }

    async def _execute_service_call(self, action: WorkflowAction, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a service call action."""
        config = action.config

        # Resolve parameter references
        resolved_params = self._resolve_parameters(config.get("parameters", {}), context)

        # Here you would make actual service calls
        # For now, simulate based on service type
        service = config.get("service", "")
        endpoint = config.get("endpoint", "")
        method = config.get("method", "GET")

        # Simulate service call
        await asyncio.sleep(0.1)  # Simulate network delay

        # Mock response based on service
        if service == "analysis_service":
            response = {
                "quality_score": 0.85,
                "findings": ["Issue 1", "Issue 2"],
                "recommendations": ["Fix 1", "Fix 2"]
            }
        elif service == "summarizer_hub":
            response = {
                "summary": "This is a generated summary of the provided content.",
                "key_points": ["Point 1", "Point 2"]
            }
        else:
            response = {"message": f"Mock response from {service}"}

        return {
            "success": True,
            "service": service,
            "endpoint": endpoint,
            "method": method,
            "response": response
        }

    async def _execute_prompt_execution(self, action: WorkflowAction, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a prompt execution action."""
        config = action.config

        # Resolve parameter references
        resolved_params = self._resolve_parameters(config, context)

        # Simulate prompt execution
        await asyncio.sleep(0.2)  # Simulate LLM processing time

        prompt_template = resolved_params.get("prompt_template", "")
        model = resolved_params.get("model", "gpt-3.5-turbo")

        # Mock LLM response
        response = {
            "model": model,
            "prompt": prompt_template,
            "response": f"This is a mock response from {model} for the given prompt.",
            "tokens_used": len(prompt_template.split()) * 2
        }

        return {
            "success": True,
            "type": "prompt_execution",
            "response": response
        }

    async def _execute_data_transformation(self, action: WorkflowAction, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a data transformation action."""
        config = action.config

        # Simple data transformation simulation
        transformation_type = config.get("transformation_type", "copy")
        input_data = self._resolve_parameters(config.get("input_data", {}), context)

        if transformation_type == "filter":
            # Simple filtering
            filtered_data = {k: v for k, v in input_data.items() if config.get("filter_condition", lambda x: True)(v)}
            result = filtered_data
        elif transformation_type == "map":
            # Simple mapping
            mapping_function = config.get("mapping_function", lambda x: x)
            result = {k: mapping_function(v) for k, v in input_data.items()}
        else:
            result = input_data

        return {
            "success": True,
            "transformation_type": transformation_type,
            "result": result
        }

    async def _execute_wait(self, action: WorkflowAction, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a wait action."""
        config = action.config
        wait_seconds = config.get("seconds", 1)

        await asyncio.sleep(wait_seconds)

        return {
            "success": True,
            "waited_seconds": wait_seconds
        }

    async def _execute_notification(self, action: WorkflowAction, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a notification action."""
        config = action.config

        # Resolve message template
        message = self._resolve_parameters(config.get("message", ""), context)
        channels = config.get("channels", ["console"])

        # Send notifications (simulate)
        for channel in channels:
            if channel == "console":
                print(f"NOTIFICATION: {message}")
            elif channel == "email":
                print(f"EMAIL NOTIFICATION: {message}")
            elif channel == "slack":
                print(f"SLACK NOTIFICATION: {message}")

        return {
            "success": True,
            "message": message,
            "channels": channels
        }

    def _resolve_parameters(self, data: Any, context: Dict[str, Any]) -> Any:
        """Resolve parameter references in action configuration."""
        if isinstance(data, str):
            # Replace parameter references like {{param_name}} or {{action_id.result}}
            import re

            def replace_param(match):
                param_path = match.group(1).strip()

                # Check input parameters
                if param_path in context["input_parameters"]:
                    return str(context["input_parameters"][param_path])

                # Check action results
                if "." in param_path:
                    action_id, result_key = param_path.split(".", 1)
                    if action_id in context["action_results"]:
                        action_result = context["action_results"][action_id]
                        if "response" in action_result and result_key in action_result["response"]:
                            return str(action_result["response"][result_key])
                        elif result_key in action_result:
                            return str(action_result[result_key])

                return f"{{{param_path}}}"  # Return original if not found

            return re.sub(r'\{\{([^}]+)\}\}', replace_param, data)

        elif isinstance(data, dict):
            return {k: self._resolve_parameters(v, context) for k, v in data.items()}

        elif isinstance(data, list):
            return [self._resolve_parameters(item, context) for item in data]

        else:
            return data

    def _evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """Evaluate a conditional expression."""
        try:
            # Safe evaluation of simple conditions
            # In production, you'd want a more robust expression evaluator
            safe_context = {
                "input": context["input_parameters"],
                "results": context["action_results"],
                "vars": context["global_variables"]
            }

            # Simple variable substitution
            eval_condition = condition
            for key, value in safe_context.items():
                if isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        eval_condition = eval_condition.replace(f"{key}.{sub_key}", repr(sub_value))
                else:
                    eval_condition = eval_condition.replace(key, repr(value))

            # Evaluate the condition
            return bool(eval(eval_condition, {"__builtins__": {}}))

        except Exception:
            return False

    def _validate_workflow(self, workflow: WorkflowDefinition) -> Tuple[bool, List[str]]:
        """Validate a workflow definition."""
        errors = []

        # Check basic requirements
        if not workflow.name:
            errors.append("Workflow name is required")

        if not workflow.actions:
            errors.append("Workflow must have at least one action")

        # Check action dependencies
        action_ids = {action.action_id for action in workflow.actions}

        for action in workflow.actions:
            for dep in action.depends_on:
                if dep not in action_ids:
                    errors.append(f"Action {action.action_id} depends on unknown action {dep}")

        # Check for circular dependencies
        if self._has_circular_dependencies(workflow):
            errors.append("Workflow contains circular dependencies")

        # Check parameter references in actions
        for action in workflow.actions:
            param_errors = self._validate_action_parameters(action, workflow)
            errors.extend(param_errors)

        return len(errors) == 0, errors

    def _has_circular_dependencies(self, workflow: WorkflowDefinition) -> bool:
        """Check for circular dependencies in workflow actions."""
        # Simple cycle detection using DFS
        visited = set()
        recursion_stack = set()

        def has_cycle(action_id: str) -> bool:
            visited.add(action_id)
            recursion_stack.add(action_id)

            action = workflow.get_action(action_id)
            if action:
                for dep in action.depends_on:
                    if dep not in visited:
                        if has_cycle(dep):
                            return True
                    elif dep in recursion_stack:
                        return True

            recursion_stack.remove(action_id)
            return False

        for action in workflow.actions:
            if action.action_id not in visited:
                if has_cycle(action.action_id):
                    return True

        return False

    def _validate_action_parameters(self, action: WorkflowAction, workflow: WorkflowDefinition) -> List[str]:
        """Validate parameter references in action configuration."""
        errors = []
        param_names = {p.name for p in workflow.parameters}

        def check_param_references(data: Any) -> List[str]:
            refs = []

            if isinstance(data, str):
                # Find parameter references
                import re
                matches = re.findall(r'\{\{([^}]+)\}\}', data)
                refs.extend(matches)

            elif isinstance(data, dict):
                for value in data.values():
                    refs.extend(check_param_references(value))

            elif isinstance(data, list):
                for item in data:
                    refs.extend(check_param_references(item))

            return refs

        # Check parameter references
        all_refs = check_param_references(action.config)

        for ref in all_refs:
            if "." not in ref:  # Simple parameter reference
                if ref not in param_names:
                    errors.append(f"Action {action.action_id} references unknown parameter '{ref}'")
            else:  # Action result reference
                action_id, _ = ref.split(".", 1)
                if not workflow.get_action(action_id):
                    errors.append(f"Action {action.action_id} references unknown action '{action_id}'")

        return errors

    def _increment_version(self, version: str) -> str:
        """Increment version number."""
        try:
            parts = version.split(".")
            parts[-1] = str(int(parts[-1]) + 1)
            return ".".join(parts)
        except (ValueError, IndexError):
            return "1.0.1"

    # Statistics and monitoring

    def get_workflow_statistics(self) -> Dict[str, Any]:
        """Get comprehensive workflow statistics."""
        return self.repository.get_workflow_statistics()

    def get_recent_activity(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent workflow activity."""
        return self.repository.get_recent_activity(limit)

    async def cleanup_completed_executions(self, max_age_hours: int = 24):
        """Clean up old completed executions."""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)

        executions_to_cleanup = []
        for execution_id, execution in self.active_executions.items():
            if (execution.status in [WorkflowExecutionStatus.COMPLETED, WorkflowExecutionStatus.FAILED] and
                execution.completed_at and execution.completed_at < cutoff_time):
                executions_to_cleanup.append(execution_id)

        for execution_id in executions_to_cleanup:
            del self.active_executions[execution_id]
            if execution_id in self.execution_tasks:
                del self.execution_tasks[execution_id]

        fire_and_forget("info", f"Cleaned up {len(executions_to_cleanup)} old executions", ServiceNames.ORCHESTRATOR)
