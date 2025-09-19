"""Orchestrator State Management - Reuse Orchestrator Patterns for State Management.

This module integrates with the orchestrator service patterns for consistent state
management, workflow coordination, and state transitions following existing ecosystem
conventions and leveraging the orchestrator's proven state management capabilities.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Type, Union
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import json

# Import from shared infrastructure
sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent / "services" / "shared"))

from simulation.infrastructure.logging import get_simulation_logger
from simulation.infrastructure.monitoring.simulation_monitoring import get_simulation_monitoring_service
from simulation.infrastructure.integration.service_clients import get_ecosystem_client

# Import orchestrator patterns (with fallbacks)
try:
    from services.orchestrator.state_manager import StateManager, StateTransition, WorkflowState
    from services.orchestrator.workflow_engine import WorkflowEngine, WorkflowDefinition
    from services.orchestrator.event_publisher import EventPublisher
except ImportError:
    # Fallback implementations
    class WorkflowState(str, Enum):
        CREATED = "created"
        RUNNING = "running"
        PAUSED = "paused"
        COMPLETED = "completed"
        FAILED = "failed"
        CANCELLED = "cancelled"

    class StateTransition:
        def __init__(self, from_state: WorkflowState, to_state: WorkflowState,
                     condition: Optional[Callable] = None, action: Optional[Callable] = None):
            self.from_state = from_state
            self.to_state = to_state
            self.condition = condition
            self.action = action

    class StateManager:
        def __init__(self):
            self.current_state: WorkflowState = WorkflowState.CREATED
            self.transitions: Dict[str, List[StateTransition]] = {}
            self.state_history: List[Dict[str, Any]] = []

        def add_transition(self, transition: StateTransition):
            key = f"{transition.from_state}_{transition.to_state}"
            if key not in self.transitions:
                self.transitions[key] = []
            self.transitions[key].append(transition)

        def can_transition(self, to_state: WorkflowState) -> bool:
            key = f"{self.current_state}_{to_state}"
            transitions = self.transitions.get(key, [])
            return any(t.condition() if t.condition else True for t in transitions)

        def transition_to(self, to_state: WorkflowState, **kwargs) -> bool:
            if not self.can_transition(to_state):
                return False

            old_state = self.current_state
            self.current_state = to_state

            # Record transition
            self.state_history.append({
                "from_state": old_state,
                "to_state": to_state,
                "timestamp": datetime.now(),
                "metadata": kwargs
            })

            # Execute transition actions
            key = f"{old_state}_{to_state}"
            for transition in self.transitions.get(key, []):
                if transition.action:
                    transition.action(**kwargs)

            return True

        def get_state_history(self) -> List[Dict[str, Any]]:
            return self.state_history.copy()

    class WorkflowEngine:
        def __init__(self):
            self.workflows: Dict[str, Dict[str, Any]] = {}

        def create_workflow(self, workflow_id: str, definition: Dict[str, Any]) -> str:
            self.workflows[workflow_id] = {
                "definition": definition,
                "state": WorkflowState.CREATED,
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            return workflow_id

        def execute_workflow(self, workflow_id: str) -> Dict[str, Any]:
            if workflow_id not in self.workflows:
                return {"success": False, "error": "Workflow not found"}

            workflow = self.workflows[workflow_id]
            workflow["state"] = WorkflowState.RUNNING
            workflow["updated_at"] = datetime.now()

            return {"success": True, "workflow_id": workflow_id}

    class EventPublisher:
        def __init__(self):
            self.subscribers: Dict[str, List[Callable]] = {}

        def subscribe(self, event_type: str, callback: Callable):
            if event_type not in self.subscribers:
                self.subscribers[event_type] = []
            self.subscribers[event_type].append(callback)

        def publish(self, event_type: str, **kwargs):
            if event_type in self.subscribers:
                for callback in self.subscribers[event_type]:
                    callback(**kwargs)


class OrchestratorStateManager:
    """State manager that reuses orchestrator patterns for simulation state management."""

    def __init__(self, orchestrator_client=None):
        """Initialize orchestrator state manager."""
        self.logger = get_simulation_logger()
        self.monitoring = get_simulation_monitoring_service()
        self.orchestrator_client = orchestrator_client or get_ecosystem_client("orchestrator")

        # Core state management components
        self.state_manager = StateManager()
        self.workflow_engine = WorkflowEngine()
        self.event_publisher = EventPublisher()

        # Simulation-specific state tracking
        self.simulation_states: Dict[str, Dict[str, Any]] = {}
        self.workflow_states: Dict[str, Dict[str, Any]] = {}

        # Setup state transitions
        self._setup_state_transitions()

        # Setup event subscriptions
        self._setup_event_subscriptions()

        self.logger.info("Orchestrator state manager initialized")

    def _setup_state_transitions(self):
        """Setup state transitions following orchestrator patterns."""
        # Simulation state transitions
        self.state_manager.add_transition(StateTransition(
            WorkflowState.CREATED, WorkflowState.RUNNING,
            condition=self._can_start_simulation,
            action=self._on_simulation_started
        ))

        self.state_manager.add_transition(StateTransition(
            WorkflowState.RUNNING, WorkflowState.COMPLETED,
            condition=self._can_complete_simulation,
            action=self._on_simulation_completed
        ))

        self.state_manager.add_transition(StateTransition(
            WorkflowState.RUNNING, WorkflowState.FAILED,
            condition=self._can_fail_simulation,
            action=self._on_simulation_failed
        ))

        self.state_manager.add_transition(StateTransition(
            WorkflowState.RUNNING, WorkflowState.PAUSED,
            action=self._on_simulation_paused
        ))

        self.state_manager.add_transition(StateTransition(
            WorkflowState.PAUSED, WorkflowState.RUNNING,
            action=self._on_simulation_resumed
        ))

        self.state_manager.add_transition(StateTransition(
            WorkflowState.RUNNING, WorkflowState.CANCELLED,
            action=self._on_simulation_cancelled
        ))

    def _setup_event_subscriptions(self):
        """Setup event subscriptions for state management."""
        self.event_publisher.subscribe("simulation_started", self._handle_simulation_started_event)
        self.event_publisher.subscribe("phase_completed", self._handle_phase_completed_event)
        self.event_publisher.subscribe("document_generated", self._handle_document_generated_event)
        self.event_publisher.subscribe("workflow_executed", self._handle_workflow_executed_event)

    async def create_simulation_workflow(self, simulation_id: str, config: Dict[str, Any]) -> str:
        """Create a simulation workflow using orchestrator patterns."""
        try:
            # Create workflow definition
            workflow_definition = {
                "name": f"simulation_{simulation_id}",
                "description": f"Simulation workflow for {simulation_id}",
                "steps": [
                    {"name": "initialize", "type": "init", "config": config},
                    {"name": "execute_phases", "type": "parallel", "config": {"phases": config.get("phases", [])}},
                    {"name": "generate_reports", "type": "report", "config": {}},
                    {"name": "cleanup", "type": "cleanup", "config": {}}
                ],
                "triggers": ["manual", "scheduled"],
                "timeout_seconds": config.get("timeout_seconds", 3600)
            }

            # Use orchestrator client to create workflow
            if hasattr(self.orchestrator_client, 'create_workflow'):
                workflow_id = await self.orchestrator_client.create_workflow(workflow_definition)
            else:
                # Fallback to local workflow engine
                workflow_id = self.workflow_engine.create_workflow(simulation_id, workflow_definition)

            # Track workflow state
            self.workflow_states[simulation_id] = {
                "workflow_id": workflow_id,
                "state": WorkflowState.CREATED,
                "created_at": datetime.now(),
                "config": config
            }

            self.logger.info("Simulation workflow created", simulation_id=simulation_id, workflow_id=workflow_id)
            return workflow_id

        except Exception as e:
            self.logger.error("Failed to create simulation workflow", simulation_id=simulation_id, error=str(e))
            raise

    async def execute_simulation_workflow(self, simulation_id: str) -> Dict[str, Any]:
        """Execute a simulation workflow using orchestrator patterns."""
        try:
            workflow_state = self.workflow_states.get(simulation_id)
            if not workflow_state:
                raise ValueError(f"No workflow found for simulation {simulation_id}")

            # Update simulation state
            self.state_manager.transition_to(WorkflowState.RUNNING, simulation_id=simulation_id)

            # Execute workflow
            if hasattr(self.orchestrator_client, 'execute_workflow'):
                result = await self.orchestrator_client.execute_workflow(workflow_state["workflow_id"], {})
            else:
                # Fallback to local workflow engine
                result = self.workflow_engine.execute_workflow(workflow_state["workflow_id"])

            # Track execution
            workflow_state["state"] = WorkflowState.RUNNING
            workflow_state["started_at"] = datetime.now()

            # Record monitoring event
            self.monitoring.record_simulation_event("workflow_started", simulation_id)

            self.logger.info("Simulation workflow execution started", simulation_id=simulation_id)
            return result

        except Exception as e:
            self.logger.error("Failed to execute simulation workflow", simulation_id=simulation_id, error=str(e))
            self.state_manager.transition_to(WorkflowState.FAILED, simulation_id=simulation_id, error=str(e))
            raise

    async def get_simulation_state(self, simulation_id: str) -> Dict[str, Any]:
        """Get comprehensive simulation state using orchestrator patterns."""
        try:
            # Get workflow state
            workflow_state = self.workflow_states.get(simulation_id, {})

            # Get simulation-specific state
            simulation_state = self.simulation_states.get(simulation_id, {})

            # Combine states
            combined_state = {
                "simulation_id": simulation_id,
                "current_state": self.state_manager.current_state.value,
                "workflow_state": workflow_state.get("state", WorkflowState.CREATED).value,
                "created_at": workflow_state.get("created_at"),
                "started_at": workflow_state.get("started_at"),
                "completed_at": workflow_state.get("completed_at"),
                "progress": simulation_state.get("progress", {}),
                "metrics": simulation_state.get("metrics", {}),
                "phase_states": simulation_state.get("phase_states", {}),
                "last_updated": datetime.now()
            }

            return combined_state

        except Exception as e:
            self.logger.error("Failed to get simulation state", simulation_id=simulation_id, error=str(e))
            return {
                "simulation_id": simulation_id,
                "error": str(e),
                "state": "unknown",
                "last_updated": datetime.now()
            }

    async def update_simulation_progress(self, simulation_id: str, phase_name: str, progress: float, details: Dict[str, Any] = None):
        """Update simulation progress using orchestrator state management."""
        try:
            if simulation_id not in self.simulation_states:
                self.simulation_states[simulation_id] = {
                    "progress": {},
                    "phase_states": {},
                    "metrics": {},
                    "created_at": datetime.now()
                }

            simulation_state = self.simulation_states[simulation_id]

            # Update phase progress
            simulation_state["progress"][phase_name] = progress
            simulation_state["phase_states"][phase_name] = {
                "progress": progress,
                "last_updated": datetime.now(),
                "details": details or {}
            }

            # Calculate overall progress
            overall_progress = sum(simulation_state["progress"].values()) / len(simulation_state["progress"])
            simulation_state["overall_progress"] = overall_progress

            # Update metrics
            simulation_state["metrics"].update(details.get("metrics", {}))
            simulation_state["last_updated"] = datetime.now()

            # Publish progress event
            self.event_publisher.publish("simulation_progress_updated",
                                       simulation_id=simulation_id,
                                       phase=phase_name,
                                       progress=progress)

            self.logger.debug("Simulation progress updated",
                            simulation_id=simulation_id,
                            phase=phase_name,
                            progress=progress)

        except Exception as e:
            self.logger.error("Failed to update simulation progress",
                            simulation_id=simulation_id, error=str(e))

    async def complete_simulation_phase(self, simulation_id: str, phase_name: str, results: Dict[str, Any]):
        """Complete a simulation phase using orchestrator patterns."""
        try:
            # Update phase state
            await self.update_simulation_progress(simulation_id, phase_name, 100.0, results)

            # Publish phase completion event
            self.event_publisher.publish("phase_completed",
                                       simulation_id=simulation_id,
                                       phase_name=phase_name,
                                       results=results)

            # Check if all phases are complete
            simulation_state = self.simulation_states.get(simulation_id, {})
            progress = simulation_state.get("progress", {})

            if all(p >= 100.0 for p in progress.values()):
                # All phases complete - transition to completed
                self.state_manager.transition_to(WorkflowState.COMPLETED,
                                              simulation_id=simulation_id,
                                              completion_time=datetime.now())

                # Update workflow state
                workflow_state = self.workflow_states.get(simulation_id, {})
                workflow_state["state"] = WorkflowState.COMPLETED
                workflow_state["completed_at"] = datetime.now()

                self.logger.info("Simulation completed", simulation_id=simulation_id)

            self.logger.info("Simulation phase completed",
                           simulation_id=simulation_id,
                           phase=phase_name)

        except Exception as e:
            self.logger.error("Failed to complete simulation phase",
                            simulation_id=simulation_id,
                            phase=phase_name,
                            error=str(e))

    def get_state_history(self, simulation_id: str) -> List[Dict[str, Any]]:
        """Get state history for a simulation."""
        return self.state_manager.get_state_history()

    def get_workflow_statistics(self) -> Dict[str, Any]:
        """Get workflow execution statistics."""
        total_workflows = len(self.workflow_states)
        active_workflows = sum(1 for w in self.workflow_states.values()
                             if w.get("state") == WorkflowState.RUNNING)
        completed_workflows = sum(1 for w in self.workflow_states.values()
                                if w.get("state") == WorkflowState.COMPLETED)
        failed_workflows = sum(1 for w in self.workflow_states.values()
                             if w.get("state") == WorkflowState.FAILED)

        return {
            "total_workflows": total_workflows,
            "active_workflows": active_workflows,
            "completed_workflows": completed_workflows,
            "failed_workflows": failed_workflows,
            "success_rate": completed_workflows / total_workflows if total_workflows > 0 else 0
        }

    # Transition condition methods
    def _can_start_simulation(self) -> bool:
        """Check if simulation can be started."""
        return self.state_manager.current_state == WorkflowState.CREATED

    def _can_complete_simulation(self) -> bool:
        """Check if simulation can be completed."""
        return self.state_manager.current_state == WorkflowState.RUNNING

    def _can_fail_simulation(self) -> bool:
        """Check if simulation can fail."""
        return self.state_manager.current_state in [WorkflowState.RUNNING, WorkflowState.PAUSED]

    # Transition action methods
    def _on_simulation_started(self, **kwargs):
        """Handle simulation started transition."""
        simulation_id = kwargs.get("simulation_id")
        if simulation_id:
            self.monitoring.record_simulation_event("simulation_started", simulation_id)

    def _on_simulation_completed(self, **kwargs):
        """Handle simulation completed transition."""
        simulation_id = kwargs.get("simulation_id")
        if simulation_id:
            self.monitoring.record_simulation_event("simulation_completed", simulation_id)

    def _on_simulation_failed(self, **kwargs):
        """Handle simulation failed transition."""
        simulation_id = kwargs.get("simulation_id")
        if simulation_id:
            self.monitoring.record_simulation_event("simulation_failed", simulation_id)

    def _on_simulation_paused(self, **kwargs):
        """Handle simulation paused transition."""
        simulation_id = kwargs.get("simulation_id")
        if simulation_id:
            self.monitoring.record_simulation_event("simulation_paused", simulation_id)

    def _on_simulation_resumed(self, **kwargs):
        """Handle simulation resumed transition."""
        simulation_id = kwargs.get("simulation_id")
        if simulation_id:
            self.monitoring.record_simulation_event("simulation_resumed", simulation_id)

    def _on_simulation_cancelled(self, **kwargs):
        """Handle simulation cancelled transition."""
        simulation_id = kwargs.get("simulation_id")
        if simulation_id:
            self.monitoring.record_simulation_event("simulation_cancelled", simulation_id)

    # Event handlers
    def _handle_simulation_started_event(self, **kwargs):
        """Handle simulation started event."""
        self.logger.info("Simulation started event received", **kwargs)

    def _handle_phase_completed_event(self, **kwargs):
        """Handle phase completed event."""
        self.logger.info("Phase completed event received", **kwargs)

    def _handle_document_generated_event(self, **kwargs):
        """Handle document generated event."""
        self.logger.debug("Document generated event received", **kwargs)

    def _handle_workflow_executed_event(self, **kwargs):
        """Handle workflow executed event."""
        self.logger.debug("Workflow executed event received", **kwargs)


# Global orchestrator state manager instance
_orchestrator_state_manager: Optional[OrchestratorStateManager] = None


def get_orchestrator_state_manager() -> OrchestratorStateManager:
    """Get the global orchestrator state manager instance."""
    global _orchestrator_state_manager
    if _orchestrator_state_manager is None:
        _orchestrator_state_manager = OrchestratorStateManager()
    return _orchestrator_state_manager


# Convenience functions for state management
async def create_simulation_workflow(simulation_id: str, config: Dict[str, Any]) -> str:
    """Create a simulation workflow."""
    manager = get_orchestrator_state_manager()
    return await manager.create_simulation_workflow(simulation_id, config)


async def execute_simulation_workflow(simulation_id: str) -> Dict[str, Any]:
    """Execute a simulation workflow."""
    manager = get_orchestrator_state_manager()
    return await manager.execute_simulation_workflow(simulation_id)


async def get_simulation_state(simulation_id: str) -> Dict[str, Any]:
    """Get simulation state."""
    manager = get_orchestrator_state_manager()
    return await manager.get_simulation_state(simulation_id)


async def update_simulation_progress(simulation_id: str, phase_name: str, progress: float, details: Dict[str, Any] = None):
    """Update simulation progress."""
    manager = get_orchestrator_state_manager()
    return await manager.update_simulation_progress(simulation_id, phase_name, progress, details)


async def complete_simulation_phase(simulation_id: str, phase_name: str, results: Dict[str, Any]):
    """Complete a simulation phase."""
    manager = get_orchestrator_state_manager()
    return await manager.complete_simulation_phase(simulation_id, phase_name, results)


__all__ = [
    'OrchestratorStateManager',
    'get_orchestrator_state_manager',
    'create_simulation_workflow',
    'execute_simulation_workflow',
    'get_simulation_state',
    'update_simulation_progress',
    'complete_simulation_phase'
]
