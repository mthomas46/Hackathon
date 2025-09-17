#!/usr/bin/env python3
"""
Integration Tests for Event-Driven Orchestration

Comprehensive integration test suite covering:
- Event store persistence and retrieval
- CQRS command and query operations
- Event correlation and pattern detection
- Reactive workflow management
- Event-driven workflow execution
- Cross-service event integration
"""

import asyncio
import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch, call
import pytest
from datetime import datetime, timedelta

# Add services to path for testing
import sys
from pathlib import Path
services_path = Path(__file__).parent.parent.parent.parent / "services"
if str(services_path) not in sys.path:
    sys.path.insert(0, str(services_path))

from services.orchestrator.modules.event_driven_orchestration import (
    initialize_event_driven_orchestration,
    event_store,
    cqrs_handler,
    event_driven_engine,
    reactive_manager,
    WorkflowEvent,
    EventType,
    EventStore,
    CQRSHandler,
    EventDrivenWorkflowEngine,
    ReactiveWorkflowManager
)

from services.shared.constants_new import ServiceNames
from services.shared.logging import fire_and_forget


class TestEventDrivenOrchestrationIntegration:
    """Integration tests for the complete event-driven orchestration system."""

    @pytest.fixture
    async def setup_event_system(self):
        """Setup the event system for testing."""
        # Initialize with mocked Redis
        with patch('redis.asyncio.from_url') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client

            # Initialize the event system
            await initialize_event_driven_orchestration()

            yield {
                'redis_client': mock_client,
                'event_store': event_store,
                'cqrs_handler': cqrs_handler,
                'event_engine': event_driven_engine,
                'reactive_manager': reactive_manager
            }

    @pytest.mark.asyncio
    async def test_event_store_persistence_and_retrieval(self, setup_event_system):
        """Test event persistence and retrieval across the system."""
        components = setup_event_system

        # Create test workflow events
        workflow_id = "test-workflow-" + str(uuid.uuid4())

        events = [
            WorkflowEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.WORKFLOW_STARTED,
                workflow_id=workflow_id,
                aggregate_id=workflow_id,
                correlation_id="corr-1",
                payload={"action": "started", "parameters": {"input": "test"}},
                metadata={"source": "test", "version": "1.0"},
                user_id="user-123"
            ),
            WorkflowEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.STEP_COMPLETED,
                workflow_id=workflow_id,
                aggregate_id=workflow_id,
                correlation_id="corr-2",
                payload={"step_id": "step-1", "step_name": "Initialize", "result": "success"},
                metadata={"source": "test", "version": "1.0"},
                user_id="user-123"
            ),
            WorkflowEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.WORKFLOW_COMPLETED,
                workflow_id=workflow_id,
                aggregate_id=workflow_id,
                correlation_id="corr-3",
                payload={"action": "completed", "result": {"output": "done"}, "duration": 2.5},
                metadata={"source": "test", "version": "1.0"},
                user_id="user-123"
            )
        ]

        # Store events
        stored_results = []
        for event in events:
            result = await components['event_store'].store_event(event)
            stored_results.append(result)
            assert result is True

        # Verify events were stored
        assert all(stored_results)

        # Retrieve events by aggregate
        retrieved_events = await components['event_store'].get_aggregate_events(workflow_id, "workflow")
        assert len(retrieved_events) == 3

        # Verify event order and content
        assert retrieved_events[0].event_type == EventType.WORKFLOW_STARTED
        assert retrieved_events[1].event_type == EventType.STEP_COMPLETED
        assert retrieved_events[2].event_type == EventType.WORKFLOW_COMPLETED

        # Verify payloads
        assert retrieved_events[0].payload["action"] == "started"
        assert retrieved_events[1].payload["step_name"] == "Initialize"
        assert retrieved_events[2].payload["duration"] == 2.5

    @pytest.mark.asyncio
    async def test_event_correlation_and_pattern_detection(self, setup_event_system):
        """Test event correlation and complex pattern detection."""
        components = setup_event_system

        # Create correlated events across multiple workflows
        base_correlation_id = "correlation-" + str(uuid.uuid4())

        workflow_1 = "workflow-1-" + str(uuid.uuid4())
        workflow_2 = "workflow-2-" + str(uuid.uuid4())

        # Workflow 1 events
        events_1 = [
            WorkflowEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.WORKFLOW_STARTED,
                workflow_id=workflow_1,
                aggregate_id=workflow_1,
                correlation_id=base_correlation_id,
                payload={"workflow": "analysis", "priority": "high"},
                metadata={"source": "orchestrator"},
                user_id="user-123"
            ),
            WorkflowEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.STEP_COMPLETED,
                workflow_id=workflow_1,
                aggregate_id=workflow_1,
                correlation_id=base_correlation_id,
                payload={"step": "data_ingestion", "records_processed": 1000},
                metadata={"source": "source_agent"},
                user_id="user-123"
            )
        ]

        # Workflow 2 events (correlated)
        events_2 = [
            WorkflowEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.WORKFLOW_STARTED,
                workflow_id=workflow_2,
                aggregate_id=workflow_2,
                correlation_id=base_correlation_id,
                payload={"workflow": "reporting", "depends_on": workflow_1},
                metadata={"source": "orchestrator"},
                user_id="user-123"
            ),
            WorkflowEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.STEP_COMPLETED,
                workflow_id=workflow_2,
                aggregate_id=workflow_2,
                correlation_id=base_correlation_id,
                payload={"step": "report_generation", "source_workflow": workflow_1},
                metadata={"source": "analysis_service"},
                user_id="user-123"
            )
        ]

        # Store all events
        all_events = events_1 + events_2
        for event in all_events:
            await components['event_store'].store_event(event)

        # Test correlation by base correlation ID
        correlated_events = await components['event_store'].get_correlated_events(base_correlation_id)
        assert len(correlated_events) == 4

        # Verify events are from both workflows but same correlation
        workflow_ids = set(event.workflow_id for event in correlated_events)
        assert workflow_ids == {workflow_1, workflow_2}

        correlation_ids = set(event.correlation_id for event in correlated_events)
        assert correlation_ids == {base_correlation_id}

        # Test pattern detection - workflow dependency chain
        dependency_pattern = await components['event_store'].detect_pattern(
            base_correlation_id,
            "workflow_dependency"
        )
        assert dependency_pattern is not None
        assert len(dependency_pattern['chain']) == 2

    @pytest.mark.asyncio
    async def test_cqrs_command_query_separation(self, setup_event_system):
        """Test CQRS pattern with command and query separation."""
        components = setup_event_system

        # Test command side - create workflow
        command_result = await components['cqrs_handler'].handle_command({
            "command_type": "create_workflow",
            "aggregate_id": "workflow-123",
            "payload": {
                "name": "CQRS Test Workflow",
                "description": "Testing CQRS pattern",
                "actions": ["analyze", "report"]
            },
            "user_id": "user-456"
        })

        assert command_result["success"] is True
        assert command_result["aggregate_id"] == "workflow-123"

        # Test query side - get workflow state
        query_result = await components['cqrs_handler'].handle_query({
            "query_type": "get_workflow_state",
            "aggregate_id": "workflow-123"
        })

        assert query_result["found"] is True
        assert query_result["state"]["name"] == "CQRS Test Workflow"
        assert query_result["state"]["status"] == "created"

        # Test command side - update workflow
        update_command = await components['cqrs_handler'].handle_command({
            "command_type": "update_workflow_status",
            "aggregate_id": "workflow-123",
            "payload": {"status": "active"},
            "user_id": "user-456"
        })

        assert update_command["success"] is True

        # Verify query reflects the update
        updated_query = await components['cqrs_handler'].handle_query({
            "query_type": "get_workflow_state",
            "aggregate_id": "workflow-123"
        })

        assert updated_query["state"]["status"] == "active"

    @pytest.mark.asyncio
    async def test_event_driven_workflow_engine(self, setup_event_system):
        """Test event-driven workflow engine functionality."""
        components = setup_event_system

        # Register a test workflow
        async def test_workflow_logic(state):
            """Test workflow that processes events."""
            if state.get("trigger_event") == "workflow_started":
                state["processed"] = True
                state["result"] = "workflow_processed"
                return state
            return state

        workflow_id = "test-event-driven-workflow"
        components['event_engine'].register_workflow(workflow_id, test_workflow_logic)

        # Create initial state
        initial_state = {
            "workflow_id": workflow_id,
            "trigger_event": "workflow_started",
            "correlation_id": "test-correlation-123",
            "parameters": {"input": "test_data"}
        }

        # Execute workflow
        result = await components['event_engine'].execute_workflow(workflow_id, initial_state)

        assert result["processed"] is True
        assert result["result"] == "workflow_processed"
        assert result["correlation_id"] == "test-correlation-123"

        # Test event processing pipeline
        workflow_event = WorkflowEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.WORKFLOW_STARTED,
            workflow_id=workflow_id,
            aggregate_id=workflow_id,
            correlation_id="event-test-456",
            payload={"action": "started"},
            metadata={"source": "test"},
            user_id="user-789"
        )

        # Process event through engine
        processed = await components['event_engine'].process_event(workflow_event)
        assert processed is True

    @pytest.mark.asyncio
    async def test_reactive_workflow_management(self, setup_event_system):
        """Test reactive workflow management and event reactions."""
        components = setup_event_system

        # Setup reactive rules
        reaction_called = False

        async def test_reaction(event):
            nonlocal reaction_called
            reaction_called = True
            return {"reaction": "executed", "event_type": event.event_type.value}

        # Register reaction for workflow failure events
        components['reactive_manager'].register_reaction(
            EventType.WORKFLOW_FAILED,
            test_reaction
        )

        # Create and process a workflow failure event
        failure_event = WorkflowEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.WORKFLOW_FAILED,
            workflow_id="failed-workflow-123",
            aggregate_id="failed-workflow-123",
            correlation_id="failure-test-789",
            payload={"error": "Test failure", "reason": "simulated_error"},
            metadata={"source": "test"},
            user_id="user-999"
        )

        # Trigger reactive processing
        await components['reactive_manager'].process_reaction(failure_event)

        # Verify reaction was executed
        assert reaction_called is True

        # Test reaction chain - failure triggers recovery workflow
        recovery_triggered = False

        async def recovery_reaction(event):
            nonlocal recovery_triggered
            recovery_triggered = True
            # Simulate starting recovery workflow
            return {"recovery_workflow": "started", "original_workflow": event.workflow_id}

        components['reactive_manager'].register_reaction(
            EventType.WORKFLOW_FAILED,
            recovery_reaction
        )

        # Process another failure event
        another_failure = WorkflowEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.WORKFLOW_FAILED,
            workflow_id="another-failed-workflow",
            aggregate_id="another-failed-workflow",
            correlation_id="recovery-test-999",
            payload={"error": "Another failure"},
            metadata={"source": "test"},
            user_id="user-999"
        )

        await components['reactive_manager'].process_reaction(another_failure)

        assert recovery_triggered is True

    @pytest.mark.asyncio
    async def test_event_replay_and_state_reconstruction(self, setup_event_system):
        """Test event replay for state reconstruction."""
        components = setup_event_system

        workflow_id = "replay-test-" + str(uuid.uuid4())

        # Create a sequence of events that tell a story
        events = [
            WorkflowEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.WORKFLOW_STARTED,
                workflow_id=workflow_id,
                aggregate_id=workflow_id,
                correlation_id="replay-test-1",
                payload={"action": "started", "initial_state": "created"},
                metadata={"source": "orchestrator"},
                user_id="user-123"
            ),
            WorkflowEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.STEP_STARTED,
                workflow_id=workflow_id,
                aggregate_id=workflow_id,
                correlation_id="replay-test-1",
                payload={"step": "validation", "status": "in_progress"},
                metadata={"source": "validation_service"},
                user_id="user-123"
            ),
            WorkflowEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.STEP_COMPLETED,
                workflow_id=workflow_id,
                aggregate_id=workflow_id,
                correlation_id="replay-test-1",
                payload={"step": "validation", "status": "completed", "result": "valid"},
                metadata={"source": "validation_service"},
                user_id="user-123"
            ),
            WorkflowEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.STEP_STARTED,
                workflow_id=workflow_id,
                aggregate_id=workflow_id,
                correlation_id="replay-test-1",
                payload={"step": "processing", "status": "in_progress"},
                metadata={"source": "processing_service"},
                user_id="user-123"
            ),
            WorkflowEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.WORKFLOW_COMPLETED,
                workflow_id=workflow_id,
                aggregate_id=workflow_id,
                correlation_id="replay-test-1",
                payload={"action": "completed", "final_result": "success", "duration": 5.2},
                metadata={"source": "orchestrator"},
                user_id="user-123"
            )
        ]

        # Store events
        for event in events:
            await components['event_store'].store_event(event)

        # Replay events to reconstruct state
        reconstructed_state = await components['event_store'].replay_events(workflow_id, "workflow")

        # Verify reconstructed state
        assert reconstructed_state["aggregate_id"] == workflow_id
        assert reconstructed_state["aggregate_type"] == "workflow"
        assert reconstructed_state["current_state"] == "completed"
        assert reconstructed_state["event_count"] == 5
        assert reconstructed_state["started_at"] is not None
        assert reconstructed_state["completed_at"] is not None
        assert reconstructed_state["final_result"] == "success"
        assert reconstructed_state["duration"] == 5.2

        # Verify step progression
        assert len(reconstructed_state["steps"]) == 2
        assert reconstructed_state["steps"]["validation"] == "completed"
        assert reconstructed_state["steps"]["processing"] == "started"

    @pytest.mark.asyncio
    async def test_cross_service_event_integration(self, setup_event_system):
        """Test cross-service event integration and communication."""
        components = setup_event_system

        # Simulate events from different services in a workflow
        workflow_id = "cross-service-" + str(uuid.uuid4())
        correlation_id = "cross-service-test-" + str(uuid.uuid4())

        # Source Agent events
        source_events = [
            WorkflowEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.STEP_STARTED,
                workflow_id=workflow_id,
                aggregate_id=workflow_id,
                correlation_id=correlation_id,
                payload={"step": "data_ingestion", "service": "source_agent", "files": ["doc1.pdf", "doc2.pdf"]},
                metadata={"source": "source_agent", "version": "1.0"},
                user_id="user-123"
            ),
            WorkflowEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.STEP_COMPLETED,
                workflow_id=workflow_id,
                aggregate_id=workflow_id,
                correlation_id=correlation_id,
                payload={"step": "data_ingestion", "service": "source_agent", "records_ingested": 150},
                metadata={"source": "source_agent", "version": "1.0"},
                user_id="user-123"
            )
        ]

        # Analysis Service events
        analysis_events = [
            WorkflowEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.STEP_STARTED,
                workflow_id=workflow_id,
                aggregate_id=workflow_id,
                correlation_id=correlation_id,
                payload={"step": "analysis", "service": "analysis_service", "analysis_type": "consistency"},
                metadata={"source": "analysis_service", "version": "2.1"},
                user_id="user-123"
            ),
            WorkflowEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.STEP_COMPLETED,
                workflow_id=workflow_id,
                aggregate_id=workflow_id,
                correlation_id=correlation_id,
                payload={"step": "analysis", "service": "analysis_service", "issues_found": 3, "score": 0.85},
                metadata={"source": "analysis_service", "version": "2.1"},
                user_id="user-123"
            )
        ]

        # Notification Service events
        notification_events = [
            WorkflowEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.STEP_STARTED,
                workflow_id=workflow_id,
                aggregate_id=workflow_id,
                correlation_id=correlation_id,
                payload={"step": "notification", "service": "notification_service", "recipients": ["user@company.com"]},
                metadata={"source": "notification_service", "version": "1.5"},
                user_id="user-123"
            )
        ]

        # Store all cross-service events
        all_events = source_events + analysis_events + notification_events
        for event in all_events:
            await components['event_store'].store_event(event)

        # Verify cross-service event correlation
        correlated_events = await components['event_store'].get_correlated_events(correlation_id)
        assert len(correlated_events) == 5

        # Verify events from different services
        services_involved = set()
        for event in correlated_events:
            services_involved.add(event.metadata["source"])

        assert "source_agent" in services_involved
        assert "analysis_service" in services_involved
        assert "notification_service" in services_involved

        # Test service interaction patterns
        ingestion_completed = False
        analysis_started = False

        for event in correlated_events:
            if (event.payload.get("step") == "data_ingestion" and
                event.event_type == EventType.STEP_COMPLETED):
                ingestion_completed = True
            if (event.payload.get("step") == "analysis" and
                event.event_type == EventType.STEP_STARTED):
                analysis_started = True

        assert ingestion_completed is True
        assert analysis_started is True

        # Verify workflow progression across services
        workflow_state = await components['event_store'].replay_events(workflow_id, "workflow")
        assert workflow_state["current_state"] == "in_progress"  # Notification step not completed
        assert workflow_state["services_involved"] == 3

    @pytest.mark.asyncio
    async def test_event_system_resilience_and_error_handling(self, setup_event_system):
        """Test event system resilience and error handling."""
        components = setup_event_system

        # Test with Redis connection failure
        original_redis_client = components['redis_client']

        # Simulate Redis connection failure
        with patch.object(original_redis_client, 'set', side_effect=Exception("Redis connection lost")):
            # Try to store event - should handle gracefully
            event = WorkflowEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.WORKFLOW_STARTED,
                workflow_id="resilience-test",
                aggregate_id="resilience-test",
                correlation_id="resilience-test",
                payload={"test": "resilience"},
                metadata={"source": "test"},
                user_id="user-test"
            )

            # Event storage should handle Redis failure gracefully
            result = await components['event_store'].store_event(event)
            # In real implementation, this might still succeed with fallback storage
            # For test, we verify the error handling doesn't crash the system

        # Test with malformed events
        malformed_event = WorkflowEvent(
            event_id=None,  # Invalid
            event_type=EventType.WORKFLOW_STARTED,
            workflow_id="malformed-test",
            aggregate_id="malformed-test",
            correlation_id="malformed-test",
            payload={"test": "malformed"},
            metadata={"source": "test"},
            user_id="user-test"
        )

        # System should handle malformed events gracefully
        result = await components['event_store'].store_event(malformed_event)
        # Should either succeed (with ID generation) or fail gracefully

        # Test event retrieval with non-existent workflow
        non_existent_events = await components['event_store'].get_aggregate_events("non-existent-workflow", "workflow")
        assert len(non_existent_events) == 0

        # Test correlation with non-existent correlation ID
        correlated_events = await components['event_store'].get_correlated_events("non-existent-correlation")
        assert len(correlated_events) == 0

    @pytest.mark.asyncio
    async def test_performance_and_scalability(self, setup_event_system):
        """Test event system performance and scalability."""
        components = setup_event_system

        # Create multiple workflows with events
        num_workflows = 10
        events_per_workflow = 5

        workflows_data = []

        for i in range(num_workflows):
            workflow_id = f"perf-test-workflow-{i}"
            correlation_id = f"perf-test-correlation-{i}"

            workflow_events = []
            for j in range(events_per_workflow):
                event = WorkflowEvent(
                    event_id=str(uuid.uuid4()),
                    event_type=EventType.WORKFLOW_STARTED if j == 0 else EventType.STEP_COMPLETED,
                    workflow_id=workflow_id,
                    aggregate_id=workflow_id,
                    correlation_id=correlation_id,
                    payload={"step": j, "data": f"test_data_{j}"},
                    metadata={"source": "performance_test"},
                    user_id=f"user-{i}"
                )
                workflow_events.append(event)

            workflows_data.append({
                "workflow_id": workflow_id,
                "correlation_id": correlation_id,
                "events": workflow_events
            })

        # Store all events concurrently
        store_tasks = []
        for workflow_data in workflows_data:
            for event in workflow_data["events"]:
                task = components['event_store'].store_event(event)
                store_tasks.append(task)

        # Execute all storage operations
        store_results = await asyncio.gather(*store_tasks, return_exceptions=True)

        # Verify all events were stored successfully
        successful_stores = sum(1 for result in store_results if result is True)
        assert successful_stores == (num_workflows * events_per_workflow)

        # Test concurrent retrieval
        retrieval_tasks = []
        for workflow_data in workflows_data:
            task = components['event_store'].get_aggregate_events(
                workflow_data["workflow_id"], "workflow"
            )
            retrieval_tasks.append(task)

        # Execute all retrieval operations
        retrieval_results = await asyncio.gather(*retrieval_tasks)

        # Verify all events were retrieved
        for i, events in enumerate(retrieval_results):
            assert len(events) == events_per_workflow
            assert events[0].workflow_id == workflows_data[i]["workflow_id"]

        # Test concurrent correlation queries
        correlation_tasks = []
        for workflow_data in workflows_data:
            task = components['event_store'].get_correlated_events(
                workflow_data["correlation_id"]
            )
            correlation_tasks.append(task)

        correlation_results = await asyncio.gather(*correlation_tasks)

        # Verify correlation results
        for i, correlated_events in enumerate(correlation_results):
            assert len(correlated_events) == events_per_workflow
            # Verify all events have the same correlation ID
            correlation_ids = set(event.correlation_id for event in correlated_events)
            assert len(correlation_ids) == 1
            assert list(correlation_ids)[0] == workflows_data[i]["correlation_id"]


if __name__ == "__main__":
    pytest.main([__file__])
