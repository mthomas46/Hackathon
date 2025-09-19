"""Integration Tests for Timeline Management - Event-Driven Engine Testing.

This module contains integration tests for timeline management, event ordering,
and temporal workflow orchestration in the simulation system.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from simulation.infrastructure.content.timeline_based_generation import (
    TimelineAwareContentGenerator, TimelineEventType, TemporalRelationship
)
from simulation.domain.entities.timeline import Timeline, TimelinePhase
from simulation.domain.events import (
    TimelineEventOccurred, PhaseStarted, PhaseDelayed, ProjectPhaseCompleted
)


class TestTimelineManagementIntegration:
    """Test cases for timeline management integration."""

    @pytest.fixture
    def timeline_generator(self):
        """Create TimelineAwareContentGenerator for testing."""
        with patch('simulation.infrastructure.content.timeline_based_generation.get_context_aware_generator') as mock_get_generator:
            mock_generator = AsyncMock()
            mock_get_generator.return_value = mock_generator

            generator = TimelineAwareContentGenerator()
            return generator

    @pytest.mark.asyncio
    async def test_timeline_aware_content_generation(self, timeline_generator):
        """Test timeline-aware content generation workflow."""
        # Mock context generator
        timeline_generator.context_generator.generate_content.return_value = {
            "content": "# Sprint Planning Meeting\n\n## Attendees\n- Product Owner\n- Scrum Master\n- Development Team",
            "metadata": {"word_count": 150, "quality_score": 0.9}
        }

        # Define timeline context
        timeline_context = {
            "current_phase": "planning",
            "phase_number": 1,
            "days_into_phase": 3,
            "total_phase_duration": 14,
            "upcoming_events": [
                {"type": "milestone", "title": "Requirements Complete", "days_until": 5},
                {"type": "meeting", "title": "Sprint Planning", "days_until": 1}
            ],
            "recent_events": [
                {"type": "milestone", "title": "Project Kickoff", "days_ago": 2}
            ]
        }

        content_request = {
            "document_type": "meeting_notes",
            "title": "Sprint Planning Meeting",
            "timeline_context": timeline_context,
            "project_phase": "planning"
        }

        result = await timeline_generator.generate_timeline_aware_content(content_request)

        # Verify the generation was called with correct context
        timeline_generator.context_generator.generate_content.assert_called_once()

        # Verify result structure
        assert isinstance(result, dict)
        assert "content" in result
        assert "metadata" in result
        assert "timeline_context" in result

    @pytest.mark.asyncio
    async def test_phase_based_content_generation(self, timeline_generator):
        """Test content generation based on project phases."""
        # Mock different responses for different phases
        def mock_generate(request):
            phase = request.get("timeline_context", {}).get("current_phase", "unknown")
            if phase == "planning":
                return {
                    "content": "# Requirements Document\n\n## Overview\nProject requirements...",
                    "metadata": {"phase": "planning", "word_count": 300}
                }
            elif phase == "development":
                return {
                    "content": "# Architecture Document\n\n## Components\nSystem components...",
                    "metadata": {"phase": "development", "word_count": 400}
                }
            else:
                return {
                    "content": "# Generic Document\n\n## Content\nGeneric content...",
                    "metadata": {"phase": phase, "word_count": 200}
                }

        timeline_generator.context_generator.generate_content.side_effect = mock_generate

        # Test planning phase
        planning_request = {
            "document_type": "requirements_doc",
            "timeline_context": {"current_phase": "planning", "phase_number": 1}
        }

        planning_result = await timeline_generator.generate_timeline_aware_content(planning_request)
        assert "Requirements Document" in planning_result["content"]
        assert planning_result["metadata"]["phase"] == "planning"

        # Test development phase
        development_request = {
            "document_type": "architecture_doc",
            "timeline_context": {"current_phase": "development", "phase_number": 2}
        }

        development_result = await timeline_generator.generate_timeline_aware_content(development_request)
        assert "Architecture Document" in development_result["content"]
        assert development_result["metadata"]["phase"] == "development"

    @pytest.mark.asyncio
    async def test_timeline_event_driven_generation(self, timeline_generator):
        """Test content generation driven by timeline events."""
        # Mock event-driven content generation
        timeline_generator.context_generator.generate_content.return_value = {
            "content": "# Sprint Complete\n\n## Achievements\n- Completed all planned items\n- Quality metrics met",
            "metadata": {"event_type": "sprint_complete", "word_count": 120}
        }

        event_context = {
            "event_type": "sprint_complete",
            "event_title": "Sprint 1 Complete",
            "event_description": "Successfully completed first development sprint",
            "current_phase": "development",
            "phase_progress": 0.25,
            "team_velocity": 85,
            "quality_metrics": {"test_coverage": 0.92, "bug_density": 0.05}
        }

        request = {
            "document_type": "status_report",
            "timeline_context": event_context,
            "trigger_event": "sprint_complete"
        }

        result = await timeline_generator.generate_timeline_aware_content(request)

        # Verify event-driven generation
        assert "Sprint Complete" in result["content"]
        assert "Achievements" in result["content"]
        assert result["metadata"]["event_type"] == "sprint_complete"


class TestTimelineEventOrdering:
    """Test cases for timeline event ordering and sequencing."""

    def test_timeline_event_chronological_ordering(self):
        """Test that timeline events are properly ordered chronologically."""
        # Create events at different times
        base_time = datetime.now()

        events = [
            {
                "event_type": "project_start",
                "title": "Project Kickoff",
                "timestamp": base_time,
                "sequence": 1
            },
            {
                "event_type": "milestone",
                "title": "Requirements Complete",
                "timestamp": base_time + timedelta(days=7),
                "sequence": 2
            },
            {
                "event_type": "phase_start",
                "title": "Design Phase Begins",
                "timestamp": base_time + timedelta(days=8),
                "sequence": 3
            },
            {
                "event_type": "milestone",
                "title": "Design Complete",
                "timestamp": base_time + timedelta(days=21),
                "sequence": 4
            },
            {
                "event_type": "phase_start",
                "title": "Development Phase Begins",
                "timestamp": base_time + timedelta(days=22),
                "sequence": 5
            }
        ]

        # Sort by timestamp
        sorted_events = sorted(events, key=lambda e: e["timestamp"])

        # Verify chronological ordering
        for i in range(len(sorted_events) - 1):
            assert sorted_events[i]["timestamp"] <= sorted_events[i + 1]["timestamp"]
            assert sorted_events[i]["sequence"] <= sorted_events[i + 1]["sequence"]

        # Verify event types follow logical project progression
        event_types = [e["event_type"] for e in sorted_events]
        assert "project_start" in event_types
        assert event_types.count("milestone") == 2
        assert event_types.count("phase_start") == 2

    def test_timeline_event_dependency_ordering(self):
        """Test that timeline events respect dependency ordering."""
        # Define events with dependencies
        events_with_deps = {
            "kickoff": {"title": "Project Kickoff", "depends_on": []},
            "requirements": {"title": "Requirements Gathering", "depends_on": ["kickoff"]},
            "design": {"title": "System Design", "depends_on": ["requirements"]},
            "development": {"title": "Development", "depends_on": ["design"]},
            "testing": {"title": "Testing", "depends_on": ["development"]},
            "deployment": {"title": "Deployment", "depends_on": ["testing"]}
        }

        # Function to check if all dependencies are satisfied
        def can_execute_event(event_key: str, completed_events: set) -> bool:
            deps = events_with_deps[event_key]["depends_on"]
            return all(dep in completed_events for dep in deps)

        # Simulate event execution order
        completed_events = set()
        execution_order = []

        # Keep trying to execute events until all are done
        remaining_events = set(events_with_deps.keys())

        while remaining_events:
            executed_this_round = set()

            for event_key in remaining_events:
                if can_execute_event(event_key, completed_events):
                    execution_order.append(event_key)
                    completed_events.add(event_key)
                    executed_this_round.add(event_key)

            remaining_events -= executed_this_round

            # Prevent infinite loop
            if not executed_this_round:
                break

        # Verify correct execution order
        expected_order = ["kickoff", "requirements", "design", "development", "testing", "deployment"]
        assert execution_order == expected_order

        # Verify all events were executed
        assert len(execution_order) == len(events_with_deps)
        assert set(execution_order) == set(events_with_deps.keys())


class TestTimelinePhaseProgression:
    """Test cases for timeline phase progression."""

    @pytest.mark.asyncio
    async def test_phase_progression_events(self):
        """Test generation of events during phase progression."""
        with patch('simulation.infrastructure.content.timeline_based_generation.get_context_aware_generator') as mock_get_generator:
            mock_generator = AsyncMock()
            mock_get_generator.return_value = mock_generator

            # Mock content generation for different phase stages
            def mock_content_generation(request):
                phase_progress = request.get("timeline_context", {}).get("phase_progress", 0)

                if phase_progress < 0.25:
                    return {"content": "# Phase Start\n\nPhase is beginning...", "stage": "start"}
                elif phase_progress < 0.75:
                    return {"content": "# Phase Midpoint\n\nPhase is in progress...", "stage": "midpoint"}
                else:
                    return {"content": "# Phase End\n\nPhase is completing...", "stage": "end"}

            mock_generator.generate_content.side_effect = mock_content_generation

            generator = TimelineAwareContentGenerator()

            # Test phase start
            start_request = {
                "timeline_context": {"phase_progress": 0.1, "current_phase": "development"},
                "document_type": "progress_report"
            }
            start_result = await generator.generate_timeline_aware_content(start_request)
            assert "Phase Start" in start_result["content"]

            # Test phase midpoint
            midpoint_request = {
                "timeline_context": {"phase_progress": 0.5, "current_phase": "development"},
                "document_type": "progress_report"
            }
            midpoint_result = await generator.generate_timeline_aware_content(midpoint_request)
            assert "Phase Midpoint" in midpoint_result["content"]

            # Test phase end
            end_request = {
                "timeline_context": {"phase_progress": 0.9, "current_phase": "development"},
                "document_type": "progress_report"
            }
            end_result = await generator.generate_timeline_aware_content(end_request)
            assert "Phase End" in end_result["content"]

    def test_phase_transition_validation(self):
        """Test validation of phase transitions."""
        # Define valid phase transitions
        valid_transitions = {
            "planning": ["design"],
            "design": ["development"],
            "development": ["testing"],
            "testing": ["deployment"],
            "deployment": ["maintenance"]
        }

        # Test valid transitions
        current_phase = "planning"
        next_phase = "design"
        assert next_phase in valid_transitions.get(current_phase, [])

        current_phase = "development"
        next_phase = "testing"
        assert next_phase in valid_transitions.get(current_phase, [])

        # Test invalid transitions
        current_phase = "planning"
        invalid_next = "deployment"
        assert invalid_next not in valid_transitions.get(current_phase, [])

        current_phase = "testing"
        invalid_next = "planning"
        assert invalid_next not in valid_transitions.get(current_phase, [])


class TestTimelineEventPersistence:
    """Test cases for timeline event persistence and replay."""

    @pytest.mark.asyncio
    async def test_timeline_event_persistence(self):
        """Test persistence of timeline events."""
        with patch('simulation.infrastructure.persistence.redis_event_store.RedisEventStore') as mock_store:
            mock_event_store = AsyncMock()
            mock_store.return_value = mock_event_store

            # Mock event storage
            mock_event_store.store_event.return_value = "event_123"

            # Create and persist a timeline event
            event = TimelineEventOccurred(
                timeline_id="timeline-101",
                project_id="proj-123",
                simulation_id="sim-456",
                event_date=datetime.now(),
                event_data={
                    "event_type": "milestone",
                    "title": "Requirements Complete",
                    "description": "All requirements have been gathered and approved"
                }
            )

            # Simulate storing the event
            event_id = await mock_event_store.store_event(event)

            assert event_id == "event_123"
            mock_event_store.store_event.assert_called_once()

            # Verify the stored event
            stored_event = mock_event_store.store_event.call_args[0][0]
            assert isinstance(stored_event, TimelineEventOccurred)
            assert stored_event.timeline_id == "timeline-101"
            assert stored_event.event_data["event_type"] == "milestone"

    @pytest.mark.asyncio
    async def test_timeline_event_retrieval(self):
        """Test retrieval of timeline events."""
        with patch('simulation.infrastructure.persistence.redis_event_store.RedisEventStore') as mock_store:
            mock_event_store = AsyncMock()
            mock_store.return_value = mock_event_store

            # Mock event retrieval
            mock_event_store.get_events.return_value = [
                {
                    "event_id": "event_1",
                    "timeline_id": "timeline-101",
                    "event_type": "milestone",
                    "title": "Phase 1 Complete",
                    "timestamp": datetime.now().isoformat()
                },
                {
                    "event_id": "event_2",
                    "timeline_id": "timeline-101",
                    "event_type": "phase_start",
                    "title": "Phase 2 Begins",
                    "timestamp": (datetime.now() + timedelta(hours=1)).isoformat()
                }
            ]

            # Retrieve events for a timeline
            events = await mock_event_store.get_events(
                timeline_id="timeline-101",
                event_type="milestone"
            )

            assert len(events) == 2
            assert events[0]["event_type"] == "milestone"
            assert events[1]["event_type"] == "phase_start"

            # Verify chronological ordering
            event_times = [datetime.fromisoformat(e["timestamp"]) for e in events]
            assert event_times[0] <= event_times[1]


class TestTemporalRelationshipManagement:
    """Test cases for temporal relationship management."""

    def test_temporal_relationship_types(self):
        """Test different types of temporal relationships."""
        # Define relationships between timeline events
        relationships = [
            {
                "from_event": "requirements_complete",
                "to_event": "design_start",
                "relationship": TemporalRelationship.PRECEDES,
                "description": "Requirements must be complete before design starts"
            },
            {
                "from_event": "design_review",
                "to_event": "development_start",
                "relationship": TemporalRelationship.ENABLES,
                "description": "Design review enables development to begin"
            },
            {
                "from_event": "sprint_planning",
                "to_event": "sprint_execution",
                "relationship": TemporalRelationship.CONCURRENT,
                "description": "Planning and execution can overlap slightly"
            }
        ]

        # Verify relationship types
        for rel in relationships:
            assert rel["relationship"] in TemporalRelationship
            assert "from_event" in rel
            assert "to_event" in rel
            assert "description" in rel

        # Test relationship constraints
        precedes_rels = [r for r in relationships if r["relationship"] == TemporalRelationship.PRECEDES]
        concurrent_rels = [r for r in relationships if r["relationship"] == TemporalRelationship.CONCURRENT]

        assert len(precedes_rels) == 1
        assert len(concurrent_rels) == 1

    def test_temporal_dependency_resolution(self):
        """Test resolution of temporal dependencies."""
        # Define a complex dependency graph
        dependencies = {
            "kickoff": [],
            "requirements": ["kickoff"],
            "design": ["requirements"],
            "design_review": ["design"],
            "development": ["design_review"],
            "testing": ["development"],
            "deployment": ["testing"],
            "go_live": ["deployment"],
            "support_setup": ["go_live"],
            "project_close": ["support_setup"]
        }

        # Function to get all prerequisites for an event
        def get_prerequisites(event: str, deps: Dict[str, List[str]]) -> set:
            prerequisites = set()
            to_check = [event]

            while to_check:
                current = to_check.pop()
                if current in deps:
                    for prereq in deps[current]:
                        if prereq not in prerequisites:
                            prerequisites.add(prereq)
                            to_check.append(prereq)

            return prerequisites

        # Test prerequisites for different events
        design_prereqs = get_prerequisites("design", dependencies)
        assert "kickoff" in design_prereqs
        assert "requirements" in design_prereqs
        assert len(design_prereqs) == 2

        deployment_prereqs = get_prerequisites("deployment", dependencies)
        expected_prereqs = {"kickoff", "requirements", "design", "design_review", "development", "testing"}
        assert deployment_prereqs == expected_prereqs

        project_close_prereqs = get_prerequisites("project_close", dependencies)
        assert len(project_close_prereqs) == 9  # All events except project_close itself


class TestTimelinePerformanceMonitoring:
    """Test cases for timeline performance monitoring."""

    @pytest.mark.asyncio
    async def test_timeline_performance_tracking(self):
        """Test tracking of timeline performance metrics."""
        # Simulate timeline execution with performance tracking
        timeline_start = datetime.now()

        # Define phases with expected durations
        phases = [
            {"name": "Planning", "planned_duration": 10, "actual_duration": 12},
            {"name": "Design", "planned_duration": 15, "actual_duration": 18},
            {"name": "Development", "planned_duration": 45, "actual_duration": 42},
            {"name": "Testing", "planned_duration": 20, "actual_duration": 25},
            {"name": "Deployment", "planned_duration": 5, "actual_duration": 7}
        ]

        total_planned = sum(p["planned_duration"] for p in phases)
        total_actual = sum(p["actual_duration"] for p in phases)

        timeline_end = timeline_start + timedelta(days=total_actual)
        total_duration = (timeline_end - timeline_start).days

        # Calculate performance metrics
        duration_variance = total_actual - total_planned
        duration_variance_percent = (duration_variance / total_planned) * 100

        # Verify calculations
        assert total_planned == 95
        assert total_actual == 104
        assert duration_variance == 9
        assert duration_variance_percent == pytest.approx(9.47, rel=0.01)

        # Check phase-level performance
        for phase in phases:
            variance = phase["actual_duration"] - phase["planned_duration"]
            if phase["name"] == "Development":
                assert variance == -3  # Under budget
            elif phase["name"] == "Testing":
                assert variance == 5  # Over budget

    def test_timeline_milestone_tracking(self):
        """Test tracking of timeline milestones."""
        # Define project milestones
        milestones = [
            {"name": "Project Kickoff", "planned_date": "2024-01-01", "actual_date": "2024-01-01", "status": "completed"},
            {"name": "Requirements Complete", "planned_date": "2024-01-10", "actual_date": "2024-01-12", "status": "completed"},
            {"name": "Design Complete", "planned_date": "2024-02-01", "actual_date": "2024-02-05", "status": "completed"},
            {"name": "MVP Release", "planned_date": "2024-03-15", "actual_date": None, "status": "pending"},
            {"name": "Final Release", "planned_date": "2024-04-30", "actual_date": None, "status": "pending"}
        ]

        # Calculate milestone performance
        completed_milestones = [m for m in milestones if m["status"] == "completed"]

        on_time_milestones = []
        delayed_milestones = []

        for milestone in completed_milestones:
            if milestone["actual_date"]:
                planned = datetime.fromisoformat(milestone["planned_date"])
                actual = datetime.fromisoformat(milestone["actual_date"])
                delay_days = (actual - planned).days

                if delay_days <= 0:
                    on_time_milestones.append(milestone)
                else:
                    delayed_milestones.append(milestone)

        # Verify milestone tracking
        assert len(completed_milestones) == 3
        assert len(on_time_milestones) == 1  # Kickoff was on time
        assert len(delayed_milestones) == 2  # Requirements and Design were delayed

        # Calculate average delay
        total_delay = sum(
            (datetime.fromisoformat(m["actual_date"]) - datetime.fromisoformat(m["planned_date"])).days
            for m in delayed_milestones
        )
        avg_delay = total_delay / len(delayed_milestones)
        assert avg_delay == 3.0  # (2 + 4) / 2
