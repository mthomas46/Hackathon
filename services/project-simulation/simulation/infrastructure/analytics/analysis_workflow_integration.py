"""Analysis Workflow Integration - Advanced Workflow Orchestration.

This module implements sophisticated analysis workflow integration that leverages
existing analysis_service workflows, adapts them for project simulation contexts,
and orchestrates complex multi-step analysis processes with intelligent routing
and result aggregation.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Set, Tuple
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import json

# Import from shared infrastructure
sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent / "services" / "shared"))

from simulation.infrastructure.logging import get_simulation_logger
from simulation.infrastructure.analytics.analytics_integration import (
    AnalyticsIntegrationManager, AnalysisType, AnalysisInsight,
    get_analytics_integration_manager
)


class WorkflowExecutionStatus(Enum):
    """Status of workflow execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class WorkflowStep:
    """Represents a step in an analysis workflow."""

    def __init__(self,
                 step_id: str,
                 name: str,
                 analysis_type: AnalysisType,
                 dependencies: List[str] = None,
                 parameters: Dict[str, Any] = None,
                 timeout_seconds: int = 300):
        """Initialize workflow step."""
        self.step_id = step_id
        self.name = name
        self.analysis_type = analysis_type
        self.dependencies = dependencies or []
        self.parameters = parameters or {}
        self.timeout_seconds = timeout_seconds

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "step_id": self.step_id,
            "name": self.name,
            "analysis_type": self.analysis_type.value,
            "dependencies": self.dependencies,
            "parameters": self.parameters,
            "timeout_seconds": self.timeout_seconds
        }


class WorkflowExecution:
    """Represents the execution of an analysis workflow."""

    def __init__(self,
                 execution_id: str,
                 workflow_id: str,
                 context: Dict[str, Any],
                 steps: List[WorkflowStep]):
        """Initialize workflow execution."""
        self.execution_id = execution_id
        self.workflow_id = workflow_id
        self.context = context
        self.steps = steps
        self.status = WorkflowExecutionStatus.PENDING
        self.step_results: Dict[str, Any] = {}
        self.step_status: Dict[str, WorkflowExecutionStatus] = {}
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.errors: List[str] = []

        # Initialize step status
        for step in steps:
            self.step_status[step.step_id] = WorkflowExecutionStatus.PENDING

    def start(self):
        """Start workflow execution."""
        self.started_at = datetime.now()
        self.status = WorkflowExecutionStatus.RUNNING

    def complete_step(self, step_id: str, result: Any):
        """Mark a step as completed with result."""
        self.step_results[step_id] = result
        self.step_status[step_id] = WorkflowExecutionStatus.COMPLETED

    def fail_step(self, step_id: str, error: str):
        """Mark a step as failed with error."""
        self.step_status[step_id] = WorkflowExecutionStatus.FAILED
        self.errors.append(f"Step {step_id}: {error}")

    def complete(self):
        """Mark workflow as completed."""
        self.completed_at = datetime.now()
        self.status = WorkflowExecutionStatus.COMPLETED

    def fail(self, error: str):
        """Mark workflow as failed."""
        self.completed_at = datetime.now()
        self.status = WorkflowExecutionStatus.FAILED
        self.errors.append(f"Workflow failed: {error}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "execution_id": self.execution_id,
            "workflow_id": self.workflow_id,
            "status": self.status.value,
            "context": self.context,
            "step_results": self.step_results,
            "step_status": {k: v.value for k, v in self.step_status.items()},
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "errors": self.errors,
            "execution_time_seconds": (
                (self.completed_at - self.started_at).total_seconds()
                if self.started_at and self.completed_at else None
            )
        }


class AnalysisWorkflowOrchestrator:
    """Orchestrates complex analysis workflows with dependency management."""

    def __init__(self):
        """Initialize workflow orchestrator."""
        self.logger = get_simulation_logger()
        self.analytics_manager = get_analytics_integration_manager()

        # Workflow definitions
        self.workflows: Dict[str, List[WorkflowStep]] = self._define_workflows()

        # Active executions
        self.active_executions: Dict[str, WorkflowExecution] = {}

        # Execution history
        self.execution_history: List[WorkflowExecution] = []

    def _define_workflows(self) -> Dict[str, List[WorkflowStep]]:
        """Define comprehensive analysis workflows."""
        workflows = {}

        # Comprehensive Project Analysis Workflow
        workflows["comprehensive_project_analysis"] = [
            WorkflowStep(
                step_id="initial_assessment",
                name="Initial Project Assessment",
                analysis_type=AnalysisType.DOCUMENT_QUALITY,
                dependencies=[],
                parameters={"assessment_type": "initial"}
            ),
            WorkflowStep(
                step_id="risk_analysis",
                name="Project Risk Analysis",
                analysis_type=AnalysisType.PROJECT_RISKS,
                dependencies=["initial_assessment"],
                parameters={"risk_categories": ["timeline", "team", "technical"]}
            ),
            WorkflowStep(
                step_id="team_productivity",
                name="Team Productivity Analysis",
                analysis_type=AnalysisType.TEAM_PRODUCTIVITY,
                dependencies=["initial_assessment"],
                parameters={"metrics": ["efficiency", "collaboration", "output"]}
            ),
            WorkflowStep(
                step_id="requirement_coverage",
                name="Requirement Coverage Analysis",
                analysis_type=AnalysisType.REQUIREMENT_COVERAGE,
                dependencies=["initial_assessment", "risk_analysis"],
                parameters={"coverage_types": ["functional", "non_functional", "business"]}
            ),
            WorkflowStep(
                step_id="architecture_compliance",
                name="Architecture Compliance Check",
                analysis_type=AnalysisType.ARCHITECTURE_COMPLIANCE,
                dependencies=["requirement_coverage"],
                parameters={"standards": ["security", "scalability", "maintainability"]}
            ),
            WorkflowStep(
                step_id="test_coverage",
                name="Test Coverage Analysis",
                analysis_type=AnalysisType.TEST_COVERAGE,
                dependencies=["requirement_coverage", "architecture_compliance"],
                parameters={"coverage_levels": ["unit", "integration", "system"]}
            ),
            WorkflowStep(
                step_id="final_synthesis",
                name="Analysis Synthesis and Recommendations",
                analysis_type=AnalysisType.PERFORMANCE_METRICS,
                dependencies=["risk_analysis", "team_productivity", "test_coverage"],
                parameters={"synthesis_type": "comprehensive"}
            )
        ]

        # Agile Sprint Analysis Workflow
        workflows["agile_sprint_analysis"] = [
            WorkflowStep(
                step_id="sprint_backlog_analysis",
                name="Sprint Backlog Analysis",
                analysis_type=AnalysisType.REQUIREMENT_COVERAGE,
                dependencies=[],
                parameters={"analysis_scope": "sprint"}
            ),
            WorkflowStep(
                step_id="velocity_analysis",
                name="Team Velocity Analysis",
                analysis_type=AnalysisType.TEAM_PRODUCTIVITY,
                dependencies=["sprint_backlog_analysis"],
                parameters={"timeframe": "sprint"}
            ),
            WorkflowStep(
                step_id="burndown_analysis",
                name="Burndown Chart Analysis",
                analysis_type=AnalysisType.PROJECT_RISKS,
                dependencies=["velocity_analysis"],
                parameters={"analysis_type": "burndown"}
            ),
            WorkflowStep(
                step_id="sprint_retrospective",
                name="Sprint Retrospective Insights",
                analysis_type=AnalysisType.PERFORMANCE_METRICS,
                dependencies=["burndown_analysis"],
                parameters={"focus": "retrospective"}
            )
        ]

        # Code Quality Analysis Workflow
        workflows["code_quality_analysis"] = [
            WorkflowStep(
                step_id="code_complexity",
                name="Code Complexity Analysis",
                analysis_type=AnalysisType.CODE_COMPLEXITY,
                dependencies=[],
                parameters={"metrics": ["cyclomatic", "cognitive", "maintainability"]}
            ),
            WorkflowStep(
                step_id="security_analysis",
                name="Security Vulnerability Analysis",
                analysis_type=AnalysisType.SECURITY_ANALYSIS,
                dependencies=["code_complexity"],
                parameters={"scan_types": ["static", "dependency", "container"]}
            ),
            WorkflowStep(
                step_id="performance_analysis",
                name="Performance Analysis",
                analysis_type=AnalysisType.PERFORMANCE_METRICS,
                dependencies=["code_complexity"],
                parameters={"performance_indicators": ["response_time", "throughput", "resource_usage"]}
            ),
            WorkflowStep(
                step_id="quality_synthesis",
                name="Code Quality Synthesis",
                analysis_type=AnalysisType.DOCUMENT_QUALITY,
                dependencies=["security_analysis", "performance_analysis"],
                parameters={"synthesis_focus": "code_quality"}
            )
        ]

        return workflows

    async def execute_workflow(self,
                             workflow_id: str,
                             context: Dict[str, Any],
                             execution_id: Optional[str] = None) -> Dict[str, Any]:
        """Execute a complete analysis workflow."""
        try:
            if workflow_id not in self.workflows:
                raise ValueError(f"Workflow {workflow_id} not found")

            # Generate execution ID
            if execution_id is None:
                execution_id = f"{workflow_id}_{datetime.now().timestamp()}"

            # Create workflow execution
            steps = self.workflows[workflow_id]
            execution = WorkflowExecution(execution_id, workflow_id, context, steps)

            # Register execution
            self.active_executions[execution_id] = execution

            self.logger.info("Starting workflow execution",
                           execution_id=execution_id, workflow_id=workflow_id)

            # Execute workflow
            execution.start()
            result = await self._execute_workflow_steps(execution)

            # Clean up
            self.execution_history.append(execution)
            del self.active_executions[execution_id]

            return result

        except Exception as e:
            self.logger.error("Workflow execution failed",
                            workflow_id=workflow_id, error=str(e))
            raise

    async def _execute_workflow_steps(self, execution: WorkflowExecution) -> Dict[str, Any]:
        """Execute workflow steps in dependency order."""
        try:
            # Build dependency graph
            dependency_graph = self._build_dependency_graph(execution.steps)

            # Execute steps in topological order
            execution_order = self._get_execution_order(dependency_graph)

            for step_id in execution_order:
                step = next(s for s in execution.steps if s.step_id == step_id)

                # Check if dependencies are satisfied
                if not self._are_dependencies_satisfied(step, execution):
                    execution.fail(f"Dependencies not satisfied for step {step_id}")
                    break

                # Execute step
                try:
                    result = await self._execute_workflow_step(step, execution.context)
                    execution.complete_step(step_id, result)

                    self.logger.info("Workflow step completed",
                                   execution_id=execution.execution_id,
                                   step_id=step_id)

                except Exception as e:
                    execution.fail_step(step_id, str(e))
                    self.logger.error("Workflow step failed",
                                    execution_id=execution.execution_id,
                                    step_id=step_id, error=str(e))
                    break

            # Complete execution
            if execution.status == WorkflowExecutionStatus.RUNNING:
                execution.complete()
                self.logger.info("Workflow execution completed",
                               execution_id=execution.execution_id)

            return execution.to_dict()

        except Exception as e:
            execution.fail(str(e))
            raise

    async def _execute_workflow_step(self,
                                   step: WorkflowStep,
                                   context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single workflow step."""
        try:
            # Prepare step inputs
            step_inputs = self._prepare_step_inputs(step, context)

            # Execute analysis component
            result = await self.analytics_manager._execute_analysis_component(
                step.analysis_type, step_inputs, None  # Context not needed for this call
            )

            # Post-process results
            processed_result = self._post_process_step_result(step, result)

            return processed_result

        except Exception as e:
            self.logger.error("Step execution failed",
                            step_id=step.step_id, error=str(e))
            raise

    def _prepare_step_inputs(self,
                           step: WorkflowStep,
                           context: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare inputs for step execution."""
        inputs = step.parameters.copy()

        # Add context data based on step type
        if step.analysis_type == AnalysisType.DOCUMENT_QUALITY:
            inputs["documents"] = context.get("documents", [])
            inputs["quality_criteria"] = context.get("quality_criteria", [])

        elif step.analysis_type == AnalysisType.PROJECT_RISKS:
            inputs["project_config"] = context.get("project_config", {})
            inputs["team_data"] = context.get("team_data", {})
            inputs["timeline_data"] = context.get("timeline_data", {})

        elif step.analysis_type == AnalysisType.TEAM_PRODUCTIVITY:
            inputs["team_members"] = context.get("team_members", [])
            inputs["performance_data"] = context.get("performance_data", {})

        # Add any additional context
        inputs.update(context.get("additional_inputs", {}))

        return inputs

    def _post_process_step_result(self,
                                step: WorkflowStep,
                                result: Dict[str, Any]) -> Dict[str, Any]:
        """Post-process step execution result."""
        processed = result.copy()

        # Add step metadata
        processed["step_id"] = step.step_id
        processed["step_name"] = step.name
        processed["analysis_type"] = step.analysis_type.value
        processed["processed_at"] = datetime.now().isoformat()

        # Add confidence scoring
        processed["confidence_score"] = self._calculate_result_confidence(result)

        # Add recommendations if not present
        if "recommendations" not in processed:
            processed["recommendations"] = self._generate_step_recommendations(step, result)

        return processed

    def _calculate_result_confidence(self, result: Dict[str, Any]) -> float:
        """Calculate confidence score for result."""
        # Base confidence
        confidence = 0.5

        # Adjust based on result completeness
        if "status" in result and result["status"] == "error":
            confidence -= 0.3

        # Adjust based on data availability
        if "issues" in result:
            confidence += min(0.2, len(result["issues"]) * 0.05)

        if "recommendations" in result:
            confidence += min(0.2, len(result["recommendations"]) * 0.05)

        return max(0.0, min(1.0, confidence))

    def _generate_step_recommendations(self,
                                     step: WorkflowStep,
                                     result: Dict[str, Any]) -> List[str]:
        """Generate recommendations for step result."""
        recommendations = []

        if step.analysis_type == AnalysisType.DOCUMENT_QUALITY:
            if result.get("quality_score", 0) < 0.7:
                recommendations.append("Improve document clarity and completeness")
                recommendations.append("Add missing sections or details")

        elif step.analysis_type == AnalysisType.PROJECT_RISKS:
            if result.get("risk_score", 0) > 0.6:
                recommendations.append("Implement risk mitigation strategies")
                recommendations.append("Increase monitoring and oversight")

        elif step.analysis_type == AnalysisType.TEAM_PRODUCTIVITY:
            if result.get("productivity_score", 0) < 0.7:
                recommendations.append("Optimize team processes and workflows")
                recommendations.append("Provide additional training or resources")

        return recommendations

    def _build_dependency_graph(self, steps: List[WorkflowStep]) -> Dict[str, List[str]]:
        """Build dependency graph for workflow steps."""
        graph = {}

        for step in steps:
            graph[step.step_id] = step.dependencies.copy()

        return graph

    def _get_execution_order(self, dependency_graph: Dict[str, List[str]]) -> List[str]:
        """Get execution order respecting dependencies."""
        # Simple topological sort implementation
        order = []
        visited = set()
        visiting = set()

        def visit(node):
            if node in visiting:
                raise ValueError(f"Circular dependency detected at {node}")
            if node in visited:
                return

            visiting.add(node)

            for dependency in dependency_graph.get(node, []):
                visit(dependency)

            visiting.remove(node)
            visited.add(node)
            order.append(node)

        # Visit all nodes
        for node in dependency_graph:
            if node not in visited:
                visit(node)

        return order

    def _are_dependencies_satisfied(self,
                                  step: WorkflowStep,
                                  execution: WorkflowExecution) -> bool:
        """Check if step dependencies are satisfied."""
        for dependency_id in step.dependencies:
            if execution.step_status.get(dependency_id) != WorkflowExecutionStatus.COMPLETED:
                return False
        return True

    def get_workflow_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get status of workflow execution."""
        if execution_id in self.active_executions:
            return self.active_executions[execution_id].to_dict()

        # Check history
        for execution in self.execution_history:
            if execution.execution_id == execution_id:
                return execution.to_dict()

        return None

    def cancel_workflow(self, execution_id: str) -> bool:
        """Cancel a running workflow."""
        if execution_id in self.active_executions:
            execution = self.active_executions[execution_id]
            execution.status = WorkflowExecutionStatus.CANCELLED
            execution.completed_at = datetime.now()
            return True

        return False

    def get_available_workflows(self) -> Dict[str, Any]:
        """Get list of available workflows."""
        return {
            workflow_id: {
                "steps": len(steps),
                "description": self._get_workflow_description(workflow_id),
                "analysis_types": list(set(step.analysis_type.value for step in steps))
            }
            for workflow_id, steps in self.workflows.items()
        }

    def _get_workflow_description(self, workflow_id: str) -> str:
        """Get description for workflow."""
        descriptions = {
            "comprehensive_project_analysis": "Complete project analysis covering quality, risks, productivity, and compliance",
            "agile_sprint_analysis": "Agile sprint analysis focusing on velocity, burndown, and retrospective insights",
            "code_quality_analysis": "Code quality analysis covering complexity, security, and performance"
        }

        return descriptions.get(workflow_id, f"Analysis workflow: {workflow_id}")

    def get_execution_history(self,
                            workflow_id: Optional[str] = None,
                            limit: int = 10) -> List[Dict[str, Any]]:
        """Get execution history."""
        history = self.execution_history

        if workflow_id:
            history = [exec for exec in history if exec.workflow_id == workflow_id]

        # Sort by completion time (most recent first)
        history.sort(key=lambda x: x.completed_at or datetime.min, reverse=True)

        return [exec.to_dict() for exec in history[:limit]]

    async def execute_parallel_workflows(self,
                                       workflow_configs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute multiple workflows in parallel."""
        tasks = []

        for config in workflow_configs:
            workflow_id = config["workflow_id"]
            context = config.get("context", {})
            execution_id = config.get("execution_id")

            task = self.execute_workflow(workflow_id, context, execution_id)
            tasks.append(task)

        # Execute all workflows concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "workflow_config": workflow_configs[i],
                    "status": "error",
                    "error": str(result)
                })
            else:
                processed_results.append(result)

        return processed_results


# Global workflow orchestrator instance
_workflow_orchestrator: Optional[AnalysisWorkflowOrchestrator] = None


def get_workflow_orchestrator() -> AnalysisWorkflowOrchestrator:
    """Get the global workflow orchestrator instance."""
    global _workflow_orchestrator
    if _workflow_orchestrator is None:
        _workflow_orchestrator = AnalysisWorkflowOrchestrator()
    return _workflow_orchestrator


__all__ = [
    'WorkflowExecutionStatus',
    'WorkflowStep',
    'WorkflowExecution',
    'AnalysisWorkflowOrchestrator',
    'get_workflow_orchestrator'
]
