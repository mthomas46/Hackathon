"""Workflow Execution Engine for Interpreter Service.

This module handles the execution, monitoring, and management of workflows through
deep integration with the orchestrator service. It provides intelligent workflow
execution, real-time monitoring, error handling, and result optimization.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from enum import Enum
from services.shared.clients import ServiceClients
from services.shared.constants_new import ServiceNames
from services.shared.logging import fire_and_forget

try:
    from .orchestrator_integration import orchestrator_integration
    from .conversation_memory import conversation_memory
    from .ecosystem_context import ecosystem_context
except ImportError:
    from orchestrator_integration import orchestrator_integration
    from conversation_memory import conversation_memory
    from ecosystem_context import ecosystem_context


class ExecutionStatus(Enum):
    """Workflow execution status enumeration."""
    PENDING = "pending"
    PREPARING = "preparing"
    EXECUTING = "executing"
    MONITORING = "monitoring"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class WorkflowExecutionEngine:
    """Advanced workflow execution engine with orchestrator integration."""

    def __init__(self):
        self.client = ServiceClients()
        self.orchestrator_url = "http://orchestrator:5099"
        
        # Active executions tracking
        self.active_executions = {}
        self.execution_history = []
        self.execution_callbacks = {}
        
        # Execution configuration
        self.max_concurrent_executions = 10
        self.default_timeout = timedelta(minutes=30)
        self.monitoring_interval = 5  # seconds
        
        # Performance metrics
        self.execution_metrics = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "average_execution_time": 0.0,
            "workflow_performance": {}
        }

    async def execute_workflow(self, execution_plan: Dict[str, Any], user_id: str = None,
                             callback: Callable = None, priority: str = "normal") -> Dict[str, Any]:
        """Execute a workflow with comprehensive monitoring and management."""
        try:
            # Generate execution ID
            execution_id = f"exec_{int(datetime.utcnow().timestamp())}_{user_id or 'anon'}"
            
            # Check execution limits
            if len(self.active_executions) >= self.max_concurrent_executions:
                return await self._handle_execution_queue_full(execution_plan, user_id)
            
            # Prepare execution context
            execution_context = await self._prepare_execution_context(
                execution_id, execution_plan, user_id, callback, priority
            )
            
            # Register execution
            self.active_executions[execution_id] = execution_context
            
            # Start execution
            execution_result = await self._execute_workflow_async(execution_context)
            
            # Cleanup and finalize
            await self._finalize_execution(execution_id, execution_result)
            
            return execution_result
            
        except Exception as e:
            error_result = {
                "status": "error",
                "execution_id": execution_id if 'execution_id' in locals() else None,
                "error": str(e),
                "error_type": type(e).__name__,
                "timestamp": datetime.utcnow().isoformat(),
                "recovery_suggestions": await self._generate_recovery_suggestions(execution_plan, str(e))
            }
            
            fire_and_forget(
                "workflow_execution_error",
                f"Workflow execution failed: {str(e)}",
                ServiceNames.INTERPRETER,
                {"execution_plan": execution_plan, "user_id": user_id, "error": str(e)}
            )
            
            return error_result

    async def _prepare_execution_context(self, execution_id: str, execution_plan: Dict[str, Any],
                                       user_id: str, callback: Callable, priority: str) -> Dict[str, Any]:
        """Prepare comprehensive execution context."""
        context = {
            "execution_id": execution_id,
            "execution_plan": execution_plan,
            "user_id": user_id,
            "callback": callback,
            "priority": priority,
            "status": ExecutionStatus.PENDING,
            "start_time": datetime.utcnow(),
            "timeout": datetime.utcnow() + self.default_timeout,
            "progress": {
                "current_step": 0,
                "total_steps": len(execution_plan.get("services_involved", [])),
                "completed_steps": [],
                "failed_steps": [],
                "step_details": {}
            },
            "resources": {
                "allocated_memory": 0,
                "estimated_duration": execution_plan.get("estimated_duration", "unknown"),
                "services_allocated": [],
                "dependencies_checked": False
            },
            "monitoring": {
                "last_heartbeat": datetime.utcnow(),
                "health_checks": [],
                "performance_metrics": {},
                "log_entries": []
            },
            "execution_metadata": {
                "workflow_name": execution_plan.get("workflow_name", "unknown"),
                "workflow_type": execution_plan.get("workflow_type", "unknown"),
                "orchestrator_endpoint": execution_plan.get("orchestrator_endpoint", ""),
                "execution_method": execution_plan.get("execution_method", "standard"),
                "parameters": execution_plan.get("parameters", {}),
                "interpreter_confidence": execution_plan.get("parameters", {}).get("interpreter_confidence", 0.0)
            }
        }
        
        return context

    async def _execute_workflow_async(self, execution_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute workflow asynchronously with monitoring."""
        execution_id = execution_context["execution_id"]
        execution_plan = execution_context["execution_plan"]
        
        try:
            # Update status to preparing
            execution_context["status"] = ExecutionStatus.PREPARING
            await self._log_execution_step(execution_id, "preparation_started", "Preparing workflow execution")
            
            # Pre-execution checks
            validation_result = await self._validate_execution_requirements(execution_context)
            if not validation_result["valid"]:
                return await self._handle_validation_failure(execution_context, validation_result)
            
            # Update status to executing
            execution_context["status"] = ExecutionStatus.EXECUTING
            await self._log_execution_step(execution_id, "execution_started", "Starting workflow execution")
            
            # Execute based on method
            execution_method = execution_plan.get("execution_method", "orchestrator_standard")
            
            if execution_method == "orchestrator_langgraph":
                result = await self._execute_langgraph_workflow(execution_context)
            else:
                result = await self._execute_standard_workflow(execution_context)
            
            # Update status to monitoring
            execution_context["status"] = ExecutionStatus.MONITORING
            await self._monitor_execution_completion(execution_context, result)
            
            # Enhance result with execution metadata
            enhanced_result = await self._enhance_execution_result(execution_context, result)
            
            # Update status to completed
            execution_context["status"] = ExecutionStatus.COMPLETED
            await self._log_execution_step(execution_id, "execution_completed", "Workflow execution completed successfully")
            
            return enhanced_result
            
        except asyncio.TimeoutError:
            execution_context["status"] = ExecutionStatus.TIMEOUT
            return await self._handle_execution_timeout(execution_context)
        except Exception as e:
            execution_context["status"] = ExecutionStatus.FAILED
            return await self._handle_execution_error(execution_context, e)

    async def _validate_execution_requirements(self, execution_context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate all requirements for workflow execution."""
        validation_result = {
            "valid": True,
            "issues": [],
            "warnings": [],
            "requirements_checked": []
        }
        
        execution_plan = execution_context["execution_plan"]
        
        # Check service availability
        services_involved = execution_plan.get("services_involved", [])
        for service in services_involved:
            try:
                # Quick health check for service
                service_health = await ecosystem_context.check_service_health(service)
                if not service_health.get("healthy", False):
                    validation_result["issues"].append(f"Service {service} is not healthy")
                    validation_result["valid"] = False
                else:
                    validation_result["requirements_checked"].append(f"{service}_health")
            except Exception as e:
                validation_result["warnings"].append(f"Could not verify {service} health: {str(e)}")
        
        # Check parameter completeness
        parameters = execution_plan.get("parameters", {})
        required_params = await self._get_required_parameters(execution_plan.get("workflow_name", ""))
        
        for param in required_params:
            if param not in parameters or not parameters[param]:
                validation_result["issues"].append(f"Required parameter '{param}' is missing or empty")
                validation_result["valid"] = False
            else:
                validation_result["requirements_checked"].append(f"parameter_{param}")
        
        # Check orchestrator availability
        try:
            orchestrator_health = await orchestrator_integration.check_orchestrator_health()
            if not orchestrator_health.get("healthy", False):
                validation_result["issues"].append("Orchestrator service is not available")
                validation_result["valid"] = False
            else:
                validation_result["requirements_checked"].append("orchestrator_health")
        except Exception as e:
            validation_result["issues"].append(f"Could not verify orchestrator health: {str(e)}")
            validation_result["valid"] = False
        
        # Check execution capacity
        if len(self.active_executions) >= self.max_concurrent_executions:
            validation_result["issues"].append("Maximum concurrent executions reached")
            validation_result["valid"] = False
        else:
            validation_result["requirements_checked"].append("execution_capacity")
        
        return validation_result

    async def _execute_langgraph_workflow(self, execution_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute LangGraph workflow through orchestrator."""
        execution_plan = execution_context["execution_plan"]
        user_id = execution_context["user_id"]
        
        workflow_type = execution_plan.get("workflow_type")
        parameters = execution_plan.get("parameters", {})
        
        # Add execution tracking to parameters
        parameters["execution_id"] = execution_context["execution_id"]
        parameters["interpreter_source"] = True
        
        # Execute through orchestrator integration
        result = await orchestrator_integration.execute_langgraph_workflow(
            workflow_type, parameters, user_id
        )
        
        # Track execution steps
        await self._log_execution_step(
            execution_context["execution_id"],
            "langgraph_execution",
            f"Executed LangGraph workflow: {workflow_type}"
        )
        
        return result

    async def _execute_standard_workflow(self, execution_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute standard workflow through orchestrator."""
        execution_plan = execution_context["execution_plan"]
        user_id = execution_context["user_id"]
        
        workflow_name = execution_plan.get("workflow_name")
        parameters = execution_plan.get("parameters", {})
        
        # Add execution tracking to parameters
        parameters["execution_id"] = execution_context["execution_id"]
        parameters["interpreter_source"] = True
        
        # Execute through orchestrator integration
        result = await orchestrator_integration.execute_workflow(
            workflow_name, parameters, user_id
        )
        
        # Track execution steps
        await self._log_execution_step(
            execution_context["execution_id"],
            "standard_execution",
            f"Executed standard workflow: {workflow_name}"
        )
        
        return result

    async def _monitor_execution_completion(self, execution_context: Dict[str, Any], 
                                          result: Dict[str, Any]):
        """Monitor workflow execution for completion."""
        execution_id = execution_context["execution_id"]
        
        # Check if the result indicates async execution
        if result.get("async_execution", False):
            workflow_execution_id = result.get("workflow_execution_id")
            if workflow_execution_id:
                # Monitor the workflow execution
                await self._monitor_async_workflow(execution_context, workflow_execution_id)
        
        # Update monitoring metrics
        execution_context["monitoring"]["last_heartbeat"] = datetime.utcnow()
        execution_context["monitoring"]["health_checks"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "status": result.get("status", "unknown"),
            "message": "Execution monitoring completed"
        })

    async def _monitor_async_workflow(self, execution_context: Dict[str, Any], 
                                    workflow_execution_id: str):
        """Monitor asynchronous workflow execution."""
        execution_id = execution_context["execution_id"]
        max_monitoring_time = timedelta(minutes=30)
        start_time = datetime.utcnow()
        
        while datetime.utcnow() - start_time < max_monitoring_time:
            try:
                # Check workflow status
                status_result = await orchestrator_integration.get_workflow_status(workflow_execution_id)
                
                if status_result.get("status") == "completed":
                    await self._log_execution_step(
                        execution_id, "async_completed", "Async workflow completed"
                    )
                    break
                elif status_result.get("status") == "failed":
                    await self._log_execution_step(
                        execution_id, "async_failed", "Async workflow failed"
                    )
                    break
                
                # Wait before next check
                await asyncio.sleep(self.monitoring_interval)
                
            except Exception as e:
                await self._log_execution_step(
                    execution_id, "monitoring_error", f"Monitoring error: {str(e)}"
                )
                break

    async def _enhance_execution_result(self, execution_context: Dict[str, Any], 
                                      result: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance execution result with comprehensive metadata."""
        execution_id = execution_context["execution_id"]
        start_time = execution_context["start_time"]
        end_time = datetime.utcnow()
        execution_duration = (end_time - start_time).total_seconds()
        
        enhanced_result = result.copy()
        
        # Add execution metadata
        enhanced_result["execution_metadata"] = {
            **execution_context["execution_metadata"],
            "execution_id": execution_id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "execution_duration_seconds": execution_duration,
            "execution_status": execution_context["status"].value,
            "progress": execution_context["progress"],
            "monitoring_data": execution_context["monitoring"]
        }
        
        # Add performance metrics
        enhanced_result["performance_metrics"] = {
            "execution_efficiency": await self._calculate_execution_efficiency(execution_context),
            "resource_utilization": await self._calculate_resource_utilization(execution_context),
            "workflow_score": await self._calculate_workflow_score(execution_context, result)
        }
        
        # Add follow-up recommendations
        enhanced_result["recommendations"] = await self._generate_execution_recommendations(
            execution_context, result
        )
        
        # Add conversation context updates
        if execution_context["user_id"]:
            enhanced_result["conversation_updates"] = await self._prepare_conversation_updates(
                execution_context, result
            )
        
        return enhanced_result

    async def _calculate_execution_efficiency(self, execution_context: Dict[str, Any]) -> float:
        """Calculate execution efficiency score."""
        start_time = execution_context["start_time"]
        end_time = datetime.utcnow()
        actual_duration = (end_time - start_time).total_seconds()
        
        # Get estimated duration
        estimated_duration_str = execution_context["execution_metadata"].get("estimated_duration", "5-10 minutes")
        estimated_seconds = await self._parse_duration_estimate(estimated_duration_str)
        
        if estimated_seconds <= 0:
            return 0.8  # Default efficiency if no estimate
        
        # Calculate efficiency (inverse of duration ratio, capped at 1.0)
        efficiency = min(estimated_seconds / actual_duration, 1.0)
        return max(efficiency, 0.1)  # Minimum efficiency of 0.1

    async def _calculate_resource_utilization(self, execution_context: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate resource utilization metrics."""
        services_involved = execution_context["execution_plan"].get("services_involved", [])
        
        return {
            "services_count": len(services_involved),
            "concurrent_executions": len(self.active_executions),
            "max_concurrent_capacity": self.max_concurrent_executions,
            "capacity_utilization": len(self.active_executions) / self.max_concurrent_executions,
            "services_utilized": services_involved
        }

    async def _calculate_workflow_score(self, execution_context: Dict[str, Any], 
                                      result: Dict[str, Any]) -> float:
        """Calculate overall workflow execution score."""
        score = 0.0
        
        # Success factor (50%)
        if result.get("status") == "success":
            score += 0.5
        elif result.get("status") == "partial_success":
            score += 0.3
        
        # Confidence factor (20%)
        interpreter_confidence = execution_context["execution_metadata"].get("interpreter_confidence", 0.0)
        score += interpreter_confidence * 0.2
        
        # Efficiency factor (20%)
        efficiency = await self._calculate_execution_efficiency(execution_context)
        score += efficiency * 0.2
        
        # User satisfaction factor (10%) - estimated based on result quality
        if result.get("data") and len(str(result.get("data", ""))) > 100:
            score += 0.1  # Assume good result if substantial data returned
        
        return min(score, 1.0)

    async def _generate_execution_recommendations(self, execution_context: Dict[str, Any],
                                                result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate recommendations based on execution results."""
        recommendations = []
        
        workflow_name = execution_context["execution_metadata"].get("workflow_name", "")
        execution_status = result.get("status", "unknown")
        
        # Success recommendations
        if execution_status == "success":
            recommendations.append({
                "type": "follow_up",
                "title": "Review Results",
                "description": "Review the workflow results and consider next steps",
                "priority": "medium",
                "action": "review_results"
            })
            
            if workflow_name in ["document_analysis", "code_documentation"]:
                recommendations.append({
                    "type": "automation",
                    "title": "Schedule Regular Runs",
                    "description": "Consider scheduling this workflow to run regularly",
                    "priority": "low",
                    "action": "schedule_workflow"
                })
        
        # Failure recommendations
        elif execution_status in ["failed", "error"]:
            recommendations.append({
                "type": "troubleshooting",
                "title": "Review Error Details",
                "description": "Check the error details and consider alternative approaches",
                "priority": "high",
                "action": "review_errors"
            })
            
            recommendations.append({
                "type": "retry",
                "title": "Retry with Modifications",
                "description": "Try running the workflow again with adjusted parameters",
                "priority": "medium",
                "action": "retry_modified"
            })
        
        # Performance recommendations
        efficiency = await self._calculate_execution_efficiency(execution_context)
        if efficiency < 0.5:
            recommendations.append({
                "type": "optimization",
                "title": "Optimize Workflow",
                "description": "This workflow took longer than expected. Consider optimization",
                "priority": "low",
                "action": "optimize_workflow"
            })
        
        return recommendations

    async def _prepare_conversation_updates(self, execution_context: Dict[str, Any],
                                          result: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare conversation context updates."""
        return {
            "workflow_completed": execution_context["execution_metadata"]["workflow_name"],
            "execution_status": result.get("status", "unknown"),
            "services_used": execution_context["execution_plan"].get("services_involved", []),
            "execution_duration": (datetime.utcnow() - execution_context["start_time"]).total_seconds(),
            "confidence_achieved": execution_context["execution_metadata"].get("interpreter_confidence", 0.0),
            "should_update_preferences": result.get("status") == "success"
        }

    async def _log_execution_step(self, execution_id: str, step_type: str, message: str):
        """Log execution step for monitoring."""
        if execution_id in self.active_executions:
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "step_type": step_type,
                "message": message,
                "execution_id": execution_id
            }
            
            self.active_executions[execution_id]["monitoring"]["log_entries"].append(log_entry)
            
            fire_and_forget(
                "workflow_execution_step",
                message,
                ServiceNames.INTERPRETER,
                {"execution_id": execution_id, "step_type": step_type}
            )

    async def _finalize_execution(self, execution_id: str, execution_result: Dict[str, Any]):
        """Finalize execution and cleanup."""
        if execution_id in self.active_executions:
            execution_context = self.active_executions[execution_id]
            
            # Update metrics
            self.execution_metrics["total_executions"] += 1
            if execution_result.get("status") == "success":
                self.execution_metrics["successful_executions"] += 1
            else:
                self.execution_metrics["failed_executions"] += 1
            
            # Update average execution time
            execution_duration = (datetime.utcnow() - execution_context["start_time"]).total_seconds()
            current_avg = self.execution_metrics["average_execution_time"]
            total_execs = self.execution_metrics["total_executions"]
            self.execution_metrics["average_execution_time"] = (
                (current_avg * (total_execs - 1) + execution_duration) / total_execs
            )
            
            # Update workflow-specific performance
            workflow_name = execution_context["execution_metadata"]["workflow_name"]
            if workflow_name not in self.execution_metrics["workflow_performance"]:
                self.execution_metrics["workflow_performance"][workflow_name] = {
                    "executions": 0,
                    "successes": 0,
                    "average_duration": 0.0
                }
            
            workflow_perf = self.execution_metrics["workflow_performance"][workflow_name]
            workflow_perf["executions"] += 1
            if execution_result.get("status") == "success":
                workflow_perf["successes"] += 1
            
            # Update workflow average duration
            workflow_avg = workflow_perf["average_duration"]
            workflow_execs = workflow_perf["executions"]
            workflow_perf["average_duration"] = (
                (workflow_avg * (workflow_execs - 1) + execution_duration) / workflow_execs
            )
            
            # Move to history and cleanup
            execution_context["final_result"] = execution_result
            execution_context["end_time"] = datetime.utcnow()
            self.execution_history.append(execution_context)
            
            # Keep only last 100 executions in history
            if len(self.execution_history) > 100:
                self.execution_history = self.execution_history[-100:]
            
            # Remove from active executions
            del self.active_executions[execution_id]
            
            # Execute callback if provided
            callback = execution_context.get("callback")
            if callback and callable(callback):
                try:
                    await callback(execution_id, execution_result)
                except Exception as e:
                    fire_and_forget(
                        "execution_callback_error",
                        f"Execution callback failed: {str(e)}",
                        ServiceNames.INTERPRETER,
                        {"execution_id": execution_id, "error": str(e)}
                    )

    async def _handle_execution_queue_full(self, execution_plan: Dict[str, Any], 
                                         user_id: str) -> Dict[str, Any]:
        """Handle case when execution queue is full."""
        return {
            "status": "queued",
            "message": "Execution queue is full. Your request has been queued.",
            "queue_position": len(self.active_executions) + 1,
            "estimated_wait_time": "5-10 minutes",
            "alternative_suggestions": [
                "Try a simpler workflow that requires fewer resources",
                "Wait a few minutes and try again",
                "Contact administrator if urgent"
            ]
        }

    async def _handle_validation_failure(self, execution_context: Dict[str, Any],
                                       validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Handle validation failure."""
        return {
            "status": "validation_failed",
            "execution_id": execution_context["execution_id"],
            "issues": validation_result["issues"],
            "warnings": validation_result["warnings"],
            "requirements_checked": validation_result["requirements_checked"],
            "recovery_suggestions": [
                "Check that all required services are running",
                "Verify that all required parameters are provided",
                "Try again in a few minutes",
                "Contact administrator if issues persist"
            ]
        }

    async def _handle_execution_timeout(self, execution_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle execution timeout."""
        return {
            "status": "timeout",
            "execution_id": execution_context["execution_id"],
            "message": "Workflow execution timed out",
            "timeout_duration": self.default_timeout.total_seconds(),
            "progress": execution_context["progress"],
            "recovery_suggestions": [
                "Try breaking the workflow into smaller steps",
                "Increase timeout if this is expected for this workflow type",
                "Check if any services are experiencing issues",
                "Retry with simplified parameters"
            ]
        }

    async def _handle_execution_error(self, execution_context: Dict[str, Any], 
                                    error: Exception) -> Dict[str, Any]:
        """Handle execution error."""
        return {
            "status": "failed",
            "execution_id": execution_context["execution_id"],
            "error": str(error),
            "error_type": type(error).__name__,
            "progress": execution_context["progress"],
            "recovery_suggestions": await self._generate_recovery_suggestions(
                execution_context["execution_plan"], str(error)
            )
        }

    async def _generate_recovery_suggestions(self, execution_plan: Dict[str, Any], 
                                           error_message: str) -> List[str]:
        """Generate recovery suggestions based on error."""
        suggestions = []
        
        error_lower = error_message.lower()
        
        if "connection" in error_lower or "network" in error_lower:
            suggestions.extend([
                "Check network connectivity to services",
                "Verify that all required services are running",
                "Try again in a few minutes"
            ])
        
        if "timeout" in error_lower:
            suggestions.extend([
                "Try breaking the workflow into smaller steps",
                "Check if services are experiencing high load",
                "Retry with a longer timeout"
            ])
        
        if "parameter" in error_lower or "argument" in error_lower:
            suggestions.extend([
                "Check that all required parameters are provided",
                "Verify parameter formats and values",
                "Review the workflow documentation"
            ])
        
        if "permission" in error_lower or "access" in error_lower:
            suggestions.extend([
                "Check user permissions for the requested operation",
                "Verify service authentication",
                "Contact administrator for access issues"
            ])
        
        # Default suggestions
        if not suggestions:
            suggestions.extend([
                "Review the error details and try again",
                "Simplify the request and retry",
                "Contact support if the issue persists"
            ])
        
        return suggestions

    async def _parse_duration_estimate(self, duration_str: str) -> float:
        """Parse duration estimate string to seconds."""
        try:
            # Extract numbers from string like "5-10 minutes"
            import re
            numbers = re.findall(r'\d+', duration_str)
            if numbers:
                # Take average if range, otherwise single number
                if len(numbers) >= 2:
                    avg_minutes = (int(numbers[0]) + int(numbers[1])) / 2
                else:
                    avg_minutes = int(numbers[0])
                
                # Convert to seconds
                if "hour" in duration_str.lower():
                    return avg_minutes * 3600
                elif "minute" in duration_str.lower():
                    return avg_minutes * 60
                else:
                    return avg_minutes  # Assume seconds if no unit
            
            return 300.0  # Default 5 minutes
        except Exception:
            return 300.0  # Default 5 minutes

    async def _get_required_parameters(self, workflow_name: str) -> List[str]:
        """Get required parameters for a workflow."""
        # This would typically come from workflow definitions
        required_params_map = {
            "document_analysis": ["doc_id"],
            "code_documentation": ["repo_url"],
            "security_audit": ["target_type"],
            "content_processing": ["content_source"],
            "data_ingestion": ["source_type", "source_url"],
            "prompt_optimization": ["prompt_id"],
            "quality_assurance": ["target_type"],
            "research_assistance": ["research_topic"]
        }
        
        return required_params_map.get(workflow_name, [])

    async def get_execution_status(self, execution_id: str) -> Dict[str, Any]:
        """Get current status of an execution."""
        if execution_id in self.active_executions:
            context = self.active_executions[execution_id]
            return {
                "execution_id": execution_id,
                "status": context["status"].value,
                "progress": context["progress"],
                "start_time": context["start_time"].isoformat(),
                "elapsed_time": (datetime.utcnow() - context["start_time"]).total_seconds(),
                "workflow_name": context["execution_metadata"]["workflow_name"],
                "user_id": context["user_id"],
                "monitoring": context["monitoring"]
            }
        
        # Check execution history
        for execution in self.execution_history:
            if execution["execution_id"] == execution_id:
                return {
                    "execution_id": execution_id,
                    "status": execution["status"].value,
                    "progress": execution["progress"],
                    "start_time": execution["start_time"].isoformat(),
                    "end_time": execution.get("end_time", datetime.utcnow()).isoformat(),
                    "final_result": execution.get("final_result", {}),
                    "workflow_name": execution["execution_metadata"]["workflow_name"]
                }
        
        return {
            "execution_id": execution_id,
            "status": "not_found",
            "message": "Execution not found in active or historical records"
        }

    async def cancel_execution(self, execution_id: str, user_id: str = None) -> Dict[str, Any]:
        """Cancel an active execution."""
        if execution_id not in self.active_executions:
            return {
                "status": "error",
                "message": "Execution not found or already completed"
            }
        
        context = self.active_executions[execution_id]
        
        # Check authorization
        if user_id and context["user_id"] != user_id:
            return {
                "status": "error",
                "message": "Not authorized to cancel this execution"
            }
        
        # Update status
        context["status"] = ExecutionStatus.CANCELLED
        context["end_time"] = datetime.utcnow()
        
        # Log cancellation
        await self._log_execution_step(execution_id, "execution_cancelled", "Execution cancelled by user")
        
        # Move to history
        self.execution_history.append(context)
        del self.active_executions[execution_id]
        
        return {
            "status": "success",
            "message": "Execution cancelled successfully",
            "execution_id": execution_id
        }

    async def get_execution_metrics(self) -> Dict[str, Any]:
        """Get execution engine metrics."""
        return {
            "execution_metrics": self.execution_metrics,
            "active_executions": len(self.active_executions),
            "max_concurrent_executions": self.max_concurrent_executions,
            "capacity_utilization": len(self.active_executions) / self.max_concurrent_executions,
            "execution_history_size": len(self.execution_history),
            "average_execution_time": self.execution_metrics["average_execution_time"],
            "success_rate": (
                self.execution_metrics["successful_executions"] / 
                max(self.execution_metrics["total_executions"], 1)
            )
        }


# Create singleton instance
workflow_execution_engine = WorkflowExecutionEngine()
