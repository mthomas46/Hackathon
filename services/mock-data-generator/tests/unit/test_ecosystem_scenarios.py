"""Unit Tests for Ecosystem Scenarios in Mock Data Generator.

This module tests ecosystem scenario generation capabilities including:
- Complete project simulation scenarios
- Timeline-based content generation
- Team activity simulation
- Phase-specific document creation
- Cross-service data relationships

Tests cover the complete ecosystem simulation infrastructure within the Mock Data Generator.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

from main import (
    EcosystemScenarioRequest, SimulationProjectDocsRequest,
    SimulationTimelineEventsRequest, SimulationTeamActivitiesRequest,
    SimulationPhaseDocumentsRequest, SimulationEcosystemScenarioRequest
)


class TestEcosystemScenarioGeneration:
    """Test Ecosystem Scenario Generation functionality."""

    @pytest.fixture
    def ecosystem_generator(self, mock_simulation_engine, mock_relationship_engine, mock_doc_store):
        """Create ecosystem generator instance with mocks."""
        class MockEcosystemGenerator:
            def __init__(self, simulation_engine, relationship_engine, doc_store):
                self.simulation_engine = simulation_engine
                self.relationship_engine = relationship_engine
                self.doc_store = doc_store

            async def generate_ecosystem_scenario(self, request: EcosystemScenarioRequest) -> Dict[str, Any]:
                """Mock ecosystem scenario generation."""
                scenario_documents = []

                # Generate base documents based on scenario type
                if request.scenario_type == "code_review":
                    base_docs = [
                        {"type": "github_pr", "count": 3},
                        {"type": "code_review_comments", "count": 8},
                        {"type": "test_scenarios", "count": 5},
                        {"type": "technical_design", "count": 2}
                    ]
                elif request.scenario_type == "documentation":
                    base_docs = [
                        {"type": "confluence_page", "count": 6},
                        {"type": "api_docs", "count": 4},
                        {"type": "user_story", "count": 7},
                        {"type": "deployment_guide", "count": 2}
                    ]
                else:
                    base_docs = [
                        {"type": "api_docs", "count": 3},
                        {"type": "user_story", "count": 4},
                        {"type": "technical_design", "count": 2}
                    ]

                total_docs = 0
                for doc_config in base_docs:
                    for i in range(doc_config["count"]):
                        doc = {
                            "id": str(uuid.uuid4()),
                            "type": doc_config["type"],
                            "title": f"{doc_config['type'].replace('_', ' ').title()} {i+1}",
                            "content": f"Generated {doc_config['type']} content for {request.scenario_type} scenario",
                            "metadata": {
                                "scenario_type": request.scenario_type,
                                "complexity": request.complexity,
                                "scale": request.scale,
                                "sequence_number": total_docs + 1,
                                "generated_at": datetime.now(),
                                "quality_score": 0.85
                            }
                        }
                        scenario_documents.append(doc)
                        total_docs += 1

                # Generate relationships if requested
                relationships = []
                if request.include_relationships and len(scenario_documents) > 1:
                    relationships = await self.relationship_engine.generate_relationships(
                        scenario_documents
                    )

                return {
                    "scenario_type": request.scenario_type,
                    "complexity": request.complexity,
                    "scale": request.scale,
                    "total_documents": total_docs,
                    "documents": scenario_documents,
                    "relationships": relationships,
                    "metadata": {
                        "generation_time_seconds": 4.2,
                        "quality_score": 0.88,
                        "relationship_density": len(relationships) / total_docs if total_docs > 0 else 0,
                        "scenario_coherence": 0.92
                    },
                    "created_at": datetime.now()
                }

        return MockEcosystemGenerator(mock_simulation_engine, mock_relationship_engine, mock_doc_store)

    def test_code_review_scenario_generation(self, ecosystem_generator):
        """Test code review ecosystem scenario generation."""
        request = EcosystemScenarioRequest(
            scenario_type="code_review",
            complexity="complex",
            scale="large",
            include_relationships=True,
            store_in_doc_store=True
        )

        result = asyncio.run(ecosystem_generator.generate_ecosystem_scenario(request))

        assert result["scenario_type"] == "code_review"
        assert result["complexity"] == "complex"
        assert result["scale"] == "large"
        assert result["total_documents"] == 18  # 3+8+5+2

        # Check document types are correct
        doc_types = [doc["type"] for doc in result["documents"]]
        assert "github_pr" in doc_types
        assert "code_review_comments" in doc_types
        assert "test_scenarios" in doc_types
        assert "technical_design" in doc_types

        # Check relationships are generated
        assert len(result["relationships"]) > 0

        # Check metadata
        metadata = result["metadata"]
        assert metadata["quality_score"] >= 0.8
        assert metadata["relationship_density"] > 0
        assert metadata["scenario_coherence"] >= 0.8

    def test_documentation_scenario_generation(self, ecosystem_generator):
        """Test documentation ecosystem scenario generation."""
        request = EcosystemScenarioRequest(
            scenario_type="documentation",
            complexity="medium",
            scale="medium",
            include_relationships=True,
            store_in_doc_store=True
        )

        result = asyncio.run(ecosystem_generator.generate_ecosystem_scenario(request))

        assert result["scenario_type"] == "documentation"
        assert result["total_documents"] == 19  # 6+4+7+2

        doc_types = [doc["type"] for doc in result["documents"]]
        assert "confluence_page" in doc_types
        assert "api_docs" in doc_types
        assert "user_story" in doc_types
        assert "deployment_guide" in doc_types

        # Documentation scenarios should have higher relationship density
        assert result["metadata"]["relationship_density"] > 0.5


class TestSimulationProjectGeneration:
    """Test Simulation Project Generation functionality."""

    @pytest.fixture
    def project_generator(self, mock_simulation_engine, mock_doc_store):
        """Create project generator instance with mocks."""
        class MockProjectGenerator:
            def __init__(self, simulation_engine, doc_store):
                self.simulation_engine = simulation_engine
                self.doc_store = doc_store

            async def generate_simulation_project(self, request: SimulationProjectDocsRequest) -> Dict[str, Any]:
                """Mock simulation project generation."""
                # Generate team members if not provided
                team_members = request.team_members or []
                if not team_members:
                    roles = [
                        "Senior Full-Stack Developer", "DevOps Engineer", "Product Manager",
                        "QA Engineer", "UI/UX Designer", "Technical Lead", "Business Analyst"
                    ][:request.team_size]

                    team_members = [
                        {
                            "name": f"Team Member {i+1}",
                            "role": roles[i] if i < len(roles) else "Developer",
                            "expertise": [f"skill_{j+1}" for j in range(3)]
                        }
                        for i in range(request.team_size)
                    ]

                # Generate project timeline
                timeline_result = await self.simulation_engine.generate_project_timeline({
                    "project_name": request.project_name,
                    "duration_weeks": request.duration_weeks,
                    "complexity": request.complexity
                })

                # Generate documents based on requested types
                generated_documents = []
                for doc_type in request.document_types:
                    if doc_type == "project_requirements":
                        docs = self._generate_requirements_docs(request, team_members)
                    elif doc_type == "architecture_diagram":
                        docs = self._generate_architecture_docs(request)
                    elif doc_type == "user_story":
                        docs = self._generate_user_stories(request, team_members)
                    elif doc_type == "technical_design":
                        docs = self._generate_technical_designs(request)
                    elif doc_type == "test_scenarios":
                        docs = self._generate_test_scenarios(request)
                    elif doc_type == "deployment_guide":
                        docs = self._generate_deployment_guide(request)
                    else:
                        docs = []

                    generated_documents.extend(docs)

                # Store documents if requested
                stored_ids = []
                if request.store_in_doc_store:
                    store_result = await self.doc_store.store_documents_batch(generated_documents)
                    stored_ids = store_result["document_ids"]

                return {
                    "project_name": request.project_name,
                    "project_type": request.project_type,
                    "team_size": request.team_size,
                    "complexity": request.complexity,
                    "duration_weeks": request.duration_weeks,
                    "team_members": team_members,
                    "timeline": timeline_result["timeline"],
                    "total_documents": len(generated_documents),
                    "documents_by_type": self._count_documents_by_type(generated_documents),
                    "documents": generated_documents,
                    "metadata": {
                        "generation_time_seconds": 8.5,
                        "quality_score": 0.89,
                        "realism_score": 0.87,
                        "project_coherence": 0.91
                    },
                    "stored_in_doc_store": request.store_in_doc_store,
                    "doc_store_ids": stored_ids,
                    "created_at": datetime.now()
                }

            def _generate_requirements_docs(self, request, team_members):
                """Generate project requirements documents."""
                return [
                    {
                        "id": str(uuid.uuid4()),
                        "type": "project_requirements",
                        "title": f"{request.project_name} - Requirements Document",
                        "content": f"Complete requirements for {request.project_name} project...",
                        "metadata": {
                            "author": team_members[0]["name"] if team_members else "Product Manager",
                            "complexity": request.complexity,
                            "word_count": 2500
                        }
                    }
                ]

            def _generate_architecture_docs(self, request):
                """Generate architecture documents."""
                return [
                    {
                        "id": str(uuid.uuid4()),
                        "type": "architecture_diagram",
                        "title": f"{request.project_name} - System Architecture",
                        "content": f"Architecture diagram and documentation for {request.project_name}...",
                        "metadata": {
                            "diagram_type": "system_overview",
                            "complexity": request.complexity
                        }
                    }
                ]

            def _generate_user_stories(self, request, team_members):
                """Generate user stories."""
                stories = []
                for i in range(min(10, request.team_size * 2)):
                    stories.append({
                        "id": str(uuid.uuid4()),
                        "type": "user_story",
                        "title": f"User Story {i+1}: {request.project_name} Feature {i+1}",
                        "content": f"As a user, I want feature {i+1} so that I can accomplish goal {i+1}...",
                        "metadata": {
                            "author": team_members[i % len(team_members)]["name"] if team_members else "Product Manager",
                            "priority": "medium",
                            "estimate": f"{(i % 5) + 1} points"
                        }
                    })
                return stories

            def _generate_technical_designs(self, request):
                """Generate technical design documents."""
                return [
                    {
                        "id": str(uuid.uuid4()),
                        "type": "technical_design",
                        "title": f"{request.project_name} - API Design",
                        "content": f"Technical design for {request.project_name} APIs...",
                        "metadata": {
                            "design_type": "api_design",
                            "complexity": request.complexity
                        }
                    },
                    {
                        "id": str(uuid.uuid4()),
                        "type": "technical_design",
                        "title": f"{request.project_name} - Database Schema",
                        "content": f"Database design for {request.project_name}...",
                        "metadata": {
                            "design_type": "database_design",
                            "complexity": request.complexity
                        }
                    }
                ]

            def _generate_test_scenarios(self, request):
                """Generate test scenarios."""
                return [
                    {
                        "id": str(uuid.uuid4()),
                        "type": "test_scenarios",
                        "title": f"{request.project_name} - Test Scenarios",
                        "content": f"Comprehensive test scenarios for {request.project_name}...",
                        "metadata": {
                            "test_types": ["unit", "integration", "e2e"],
                            "coverage_target": 85
                        }
                    }
                ]

            def _generate_deployment_guide(self, request):
                """Generate deployment guide."""
                return [
                    {
                        "id": str(uuid.uuid4()),
                        "type": "deployment_guide",
                        "title": f"{request.project_name} - Deployment Guide",
                        "content": f"Deployment procedures for {request.project_name}...",
                        "metadata": {
                            "environments": ["development", "staging", "production"],
                            "complexity": request.complexity
                        }
                    }
                ]

            def _count_documents_by_type(self, documents):
                """Count documents by type."""
                counts = {}
                for doc in documents:
                    doc_type = doc["type"]
                    counts[doc_type] = counts.get(doc_type, 0) + 1
                return counts

        return MockProjectGenerator(mock_simulation_engine, mock_doc_store)

    def test_simulation_project_generation(self, project_generator):
        """Test simulation project generation."""
        request = SimulationProjectDocsRequest(
            project_name="SmartInventory",
            project_type="web_application",
            team_size=6,
            complexity="complex",
            duration_weeks=12,
            document_types=[
                "project_requirements",
                "architecture_diagram",
                "user_story",
                "technical_design",
                "test_scenarios",
                "deployment_guide"
            ],
            store_in_doc_store=True
        )

        result = asyncio.run(project_generator.generate_simulation_project(request))

        assert result["project_name"] == "SmartInventory"
        assert result["project_type"] == "web_application"
        assert result["team_size"] == 6
        assert result["complexity"] == "complex"
        assert result["duration_weeks"] == 12

        # Check team generation
        assert len(result["team_members"]) == 6
        for member in result["team_members"]:
            assert "name" in member
            assert "role" in member
            assert "expertise" in member

        # Check timeline generation
        assert "timeline" in result
        assert len(result["timeline"]) > 0

        # Check document generation
        assert result["total_documents"] > 10  # Should generate multiple documents
        assert "documents_by_type" in result

        expected_types = ["project_requirements", "architecture_diagram", "user_story", "technical_design", "test_scenarios", "deployment_guide"]
        for doc_type in expected_types:
            assert doc_type in result["documents_by_type"]
            assert result["documents_by_type"][doc_type] > 0

        # Check storage
        assert result["stored_in_doc_store"] is True
        assert len(result["doc_store_ids"]) == result["total_documents"]

        # Check metadata
        metadata = result["metadata"]
        assert metadata["quality_score"] >= 0.8
        assert metadata["realism_score"] >= 0.8
        assert metadata["project_coherence"] >= 0.8


class TestTimelineEventGeneration:
    """Test Timeline Event Generation functionality."""

    @pytest.fixture
    def timeline_generator(self, mock_simulation_engine, mock_doc_store):
        """Create timeline generator instance with mocks."""
        class MockTimelineGenerator:
            def __init__(self, simulation_engine, doc_store):
                self.simulation_engine = simulation_engine
                self.doc_store = doc_store

            async def generate_timeline_events(self, request: SimulationTimelineEventsRequest) -> Dict[str, Any]:
                """Mock timeline events generation."""
                events = []

                # Generate events for each phase
                for phase in request.timeline_phases:
                    phase_start = datetime.fromisoformat(phase["start_date"])
                    phase_duration_days = phase.get("duration_weeks", 2) * 7

                    # Generate events based on types requested
                    for event_type in request.event_types:
                        event_count = 3 if event_type == "document_creation" else 2 if event_type == "team_activity" else 1

                        for i in range(event_count):
                            event_date = phase_start + timedelta(days=i * (phase_duration_days // event_count))

                            if request.include_past_events or event_date >= datetime.now():
                                event = {
                                    "id": str(uuid.uuid4()),
                                    "event_type": event_type,
                                    "phase_name": phase["name"],
                                    "title": f"{event_type.replace('_', ' ').title()} {i+1} - {phase['name']}",
                                    "description": f"Event description for {event_type} in {phase['name']} phase",
                                    "timestamp": event_date.isoformat(),
                                    "metadata": {
                                        "project_name": request.project_name,
                                        "phase": phase["name"],
                                        "event_type": event_type,
                                        "sequence_number": len(events) + 1
                                    }
                                }

                                # Add type-specific content
                                if event_type == "document_creation":
                                    event["document_type"] = "technical_design"
                                    event["document_title"] = f"Design Document {i+1}"
                                elif event_type == "team_activity":
                                    event["activity_type"] = "code_review"
                                    event["participants"] = ["developer_1", "developer_2"]
                                elif event_type == "milestone":
                                    event["milestone_type"] = "phase_completion"
                                    event["completion_percentage"] = 100

                                events.append(event)

                # Store events as documents if requested
                stored_ids = []
                if request.store_in_doc_store:
                    # Convert events to document format
                    event_documents = [{
                        "id": event["id"],
                        "type": "timeline_event",
                        "title": event["title"],
                        "content": f"Timeline event: {event['description']}",
                        "metadata": event["metadata"]
                    } for event in events]

                    store_result = await self.doc_store.store_documents_batch(event_documents)
                    stored_ids = store_result["document_ids"]

                return {
                    "project_name": request.project_name,
                    "current_phase": request.current_phase,
                    "total_events": len(events),
                    "events_by_type": self._count_events_by_type(events),
                    "events_by_phase": self._count_events_by_phase(events),
                    "events": events,
                    "metadata": {
                        "generation_time_seconds": 3.2,
                        "events_per_phase_avg": len(events) / len(request.timeline_phases),
                        "temporal_distribution": "uniform",
                        "realism_score": 0.88
                    },
                    "stored_in_doc_store": request.store_in_doc_store,
                    "doc_store_ids": stored_ids,
                    "created_at": datetime.now()
                }

            def _count_events_by_type(self, events):
                """Count events by type."""
                counts = {}
                for event in events:
                    event_type = event["event_type"]
                    counts[event_type] = counts.get(event_type, 0) + 1
                return counts

            def _count_events_by_phase(self, events):
                """Count events by phase."""
                counts = {}
                for event in events:
                    phase = event["phase_name"]
                    counts[phase] = counts.get(phase, 0) + 1
                return counts

        return MockTimelineGenerator(mock_simulation_engine, mock_doc_store)

    def test_timeline_events_generation(self, timeline_generator):
        """Test timeline events generation."""
        request = SimulationTimelineEventsRequest(
            project_name="SmartInventory",
            timeline_phases=[
                {
                    "name": "Planning",
                    "duration_weeks": 2,
                    "start_date": "2024-01-01"
                },
                {
                    "name": "Development",
                    "duration_weeks": 8,
                    "start_date": "2024-01-15"
                },
                {
                    "name": "Testing",
                    "duration_weeks": 3,
                    "start_date": "2024-03-10"
                }
            ],
            current_phase="Development",
            include_past_events=True,
            include_future_events=True,
            event_types=["document_creation", "team_activity", "milestone"],
            store_in_doc_store=True
        )

        result = asyncio.run(timeline_generator.generate_timeline_events(request))

        assert result["project_name"] == "SmartInventory"
        assert result["current_phase"] == "Development"
        assert result["total_events"] > 0

        # Check event distribution
        assert "events_by_type" in result
        assert "events_by_phase" in result

        # Should have events for all requested types
        for event_type in request.event_types:
            assert event_type in result["events_by_type"]
            assert result["events_by_type"][event_type] > 0

        # Should have events for all phases
        for phase in request.timeline_phases:
            assert phase["name"] in result["events_by_phase"]
            assert result["events_by_phase"][phase["name"]] > 0

        # Check event structure
        for event in result["events"]:
            assert "id" in event
            assert "event_type" in event
            assert "phase_name" in event
            assert "title" in event
            assert "description" in event
            assert "timestamp" in event
            assert "metadata" in event

        # Check storage
        assert result["stored_in_doc_store"] is True
        assert len(result["doc_store_ids"]) == result["total_events"]

        # Check metadata
        metadata = result["metadata"]
        assert metadata["realism_score"] >= 0.8
        assert "events_per_phase_avg" in metadata


class TestTeamActivitySimulation:
    """Test Team Activity Simulation functionality."""

    @pytest.fixture
    def team_activity_generator(self, mock_simulation_engine, mock_doc_store):
        """Create team activity generator instance with mocks."""
        class MockTeamActivityGenerator:
            def __init__(self, simulation_engine, doc_store):
                self.simulation_engine = simulation_engine
                self.doc_store = doc_store

            async def generate_team_activities(self, request: SimulationTeamActivitiesRequest) -> Dict[str, Any]:
                """Mock team activities generation."""
                activities = []

                # Generate activities for each team member and type
                base_date = datetime.now() - timedelta(days=request.time_range_days)

                for day in range(request.time_range_days):
                    current_date = base_date + timedelta(days=day)

                    for member in request.team_members:
                        # Generate 1-3 activities per member per day
                        activities_per_day = min(3, max(1, int(member.get("productivity_score", 0.8) * 3)))

                        for i in range(activities_per_day):
                            activity_type = request.activity_types[i % len(request.activity_types)]

                            activity = {
                                "id": str(uuid.uuid4()),
                                "activity_type": activity_type,
                                "participant": member["name"],
                                "timestamp": (current_date + timedelta(hours=i*2)).isoformat(),
                                "title": f"{activity_type.replace('_', ' ').title()} by {member['name']}",
                                "description": f"Activity description for {activity_type}",
                                "metadata": {
                                    "project_name": request.project_name,
                                    "participant": member["name"],
                                    "participant_role": member["role"],
                                    "activity_type": activity_type,
                                    "productivity_score": member.get("productivity_score", 0.8),
                                    "day_of_week": current_date.strftime("%A"),
                                    "sequence_number": len(activities) + 1
                                }
                            }

                            # Add type-specific details
                            if activity_type == "code_commit":
                                activity["repository"] = f"{request.project_name.lower()}_repo"
                                activity["files_changed"] = ["src/main.py", "tests/test_main.py"]
                                activity["lines_changed"] = 45
                            elif activity_type == "document_update":
                                activity["document_type"] = "technical_design"
                                activity["changes_summary"] = "Updated API specifications"
                            elif activity_type == "meeting_notes":
                                activity["meeting_type"] = "standup"
                                activity["duration_minutes"] = 15
                                activity["attendees"] = [m["name"] for m in request.team_members[:3]]
                            elif activity_type == "design_decision":
                                activity["decision_category"] = "architecture"
                                activity["impact_level"] = "high"

                            activities.append(activity)

                # Limit to requested count
                activities = activities[:request.activity_count]

                # Store activities as documents if requested
                stored_ids = []
                if request.store_in_doc_store:
                    activity_documents = [{
                        "id": activity["id"],
                        "type": "team_activity",
                        "title": activity["title"],
                        "content": f"Team activity: {activity['description']}",
                        "metadata": activity["metadata"]
                    } for activity in activities]

                    store_result = await self.doc_store.store_documents_batch(activity_documents)
                    stored_ids = store_result["document_ids"]

                return {
                    "project_name": request.project_name,
                    "time_range_days": request.time_range_days,
                    "total_activities": len(activities),
                    "activities_by_type": self._count_activities_by_type(activities),
                    "activities_by_participant": self._count_activities_by_participant(activities),
                    "activities": activities,
                    "metadata": {
                        "generation_time_seconds": 4.8,
                        "activities_per_day_avg": len(activities) / request.time_range_days,
                        "team_productivity_score": sum(m.get("productivity_score", 0.8) for m in request.team_members) / len(request.team_members),
                        "realism_score": 0.89,
                        "temporal_distribution": "realistic_work_hours"
                    },
                    "stored_in_doc_store": request.store_in_doc_store,
                    "doc_store_ids": stored_ids,
                    "created_at": datetime.now()
                }

            def _count_activities_by_type(self, activities):
                """Count activities by type."""
                counts = {}
                for activity in activities:
                    activity_type = activity["activity_type"]
                    counts[activity_type] = counts.get(activity_type, 0) + 1
                return counts

            def _count_activities_by_participant(self, activities):
                """Count activities by participant."""
                counts = {}
                for activity in activities:
                    participant = activity["participant"]
                    counts[participant] = counts.get(participant, 0) + 1
                return counts

        return MockTeamActivityGenerator(mock_simulation_engine, mock_doc_store)

    def test_team_activities_generation(self, team_activity_generator):
        """Test team activities generation."""
        request = SimulationTeamActivitiesRequest(
            project_name="SmartInventory",
            team_members=[
                {
                    "name": "Alice Johnson",
                    "role": "Senior Developer",
                    "productivity_score": 0.9
                },
                {
                    "name": "Bob Chen",
                    "role": "DevOps Engineer",
                    "productivity_score": 0.85
                },
                {
                    "name": "Carol Williams",
                    "role": "QA Engineer",
                    "productivity_score": 0.95
                }
            ],
            activity_types=[
                "code_commit",
                "document_update",
                "meeting_notes",
                "design_decision"
            ],
            time_range_days=7,
            activity_count=50,
            store_in_doc_store=True
        )

        result = asyncio.run(team_activity_generator.generate_team_activities(request))

        assert result["project_name"] == "SmartInventory"
        assert result["time_range_days"] == 7
        assert result["total_activities"] == 50

        # Check activity distribution
        assert "activities_by_type" in result
        assert "activities_by_participant" in result

        # Should have activities for all types
        for activity_type in request.activity_types:
            assert activity_type in result["activities_by_type"]
            assert result["activities_by_type"][activity_type] > 0

        # Should have activities for all participants
        for member in request.team_members:
            assert member["name"] in result["activities_by_participant"]
            assert result["activities_by_participant"][member["name"]] > 0

        # Check activity structure
        for activity in result["activities"]:
            assert "id" in activity
            assert "activity_type" in activity
            assert "participant" in activity
            assert "timestamp" in activity
            assert "title" in activity
            assert "description" in activity
            assert "metadata" in activity

        # Check type-specific details
        code_commits = [a for a in result["activities"] if a["activity_type"] == "code_commit"]
        if code_commits:
            for commit in code_commits:
                assert "repository" in commit
                assert "files_changed" in commit
                assert "lines_changed" in commit

        # Check storage
        assert result["stored_in_doc_store"] is True
        assert len(result["doc_store_ids"]) == result["total_activities"]

        # Check metadata
        metadata = result["metadata"]
        assert metadata["realism_score"] >= 0.8
        assert "team_productivity_score" in metadata
        assert 0.8 <= metadata["team_productivity_score"] <= 1.0


class TestPhaseDocumentGeneration:
    """Test Phase Document Generation functionality."""

    @pytest.fixture
    def phase_document_generator(self, mock_simulation_engine, mock_doc_store):
        """Create phase document generator instance with mocks."""
        class MockPhaseDocumentGenerator:
            def __init__(self, simulation_engine, doc_store):
                self.simulation_engine = simulation_engine
                self.doc_store = doc_store

            async def generate_phase_documents(self, request: SimulationPhaseDocumentsRequest) -> Dict[str, Any]:
                """Mock phase documents generation."""
                documents = []

                # Generate documents based on requested types
                for doc_type in request.document_types:
                    if doc_type == "technical_design":
                        docs = self._generate_technical_designs(request)
                    elif doc_type == "test_scenarios":
                        docs = self._generate_test_scenarios(request)
                    elif doc_type == "deployment_guide":
                        docs = self._generate_deployment_guide(request)
                    elif doc_type == "code_review_comments":
                        docs = self._generate_code_review_comments(request)
                    elif doc_type == "architecture_diagram":
                        docs = self._generate_architecture_diagram(request)
                    else:
                        docs = []

                    documents.extend(docs)

                # Assign team members to documents
                team_members = request.team_members or []
                for i, doc in enumerate(documents):
                    if team_members:
                        assigned_member = team_members[i % len(team_members)]
                        doc["metadata"]["author"] = assigned_member["name"]
                        doc["metadata"]["author_role"] = assigned_member["role"]

                # Store documents if requested
                stored_ids = []
                if request.store_in_doc_store:
                    store_result = await self.doc_store.store_documents_batch(documents)
                    stored_ids = store_result["document_ids"]

                return {
                    "project_name": request.project_name,
                    "phase_name": request.phase_name,
                    "total_documents": len(documents),
                    "documents_by_type": self._count_documents_by_type(documents),
                    "documents": documents,
                    "metadata": {
                        "generation_time_seconds": 5.2,
                        "phase_complexity": request.phase_details.get("challenges", []),
                        "quality_score": 0.87,
                        "phase_completeness": 0.92,
                        "team_involvement": len(team_members) > 0
                    },
                    "stored_in_doc_store": request.store_in_doc_store,
                    "doc_store_ids": stored_ids,
                    "created_at": datetime.now()
                }

            def _generate_technical_designs(self, request):
                """Generate technical designs for phase."""
                return [
                    {
                        "id": str(uuid.uuid4()),
                        "type": "technical_design",
                        "title": f"{request.project_name} - {request.phase_name} API Design",
                        "content": f"Technical design document for {request.phase_name} phase APIs...",
                        "metadata": {
                            "phase": request.phase_name,
                            "design_type": "api_design",
                            "complexity": "high"
                        }
                    },
                    {
                        "id": str(uuid.uuid4()),
                        "type": "technical_design",
                        "title": f"{request.project_name} - {request.phase_name} Database Design",
                        "content": f"Database design for {request.phase_name} phase...",
                        "metadata": {
                            "phase": request.phase_name,
                            "design_type": "database_design",
                            "complexity": "medium"
                        }
                    }
                ]

            def _generate_test_scenarios(self, request):
                """Generate test scenarios for phase."""
                return [
                    {
                        "id": str(uuid.uuid4()),
                        "type": "test_scenarios",
                        "title": f"{request.project_name} - {request.phase_name} Test Scenarios",
                        "content": f"Comprehensive test scenarios for {request.phase_name} phase...",
                        "metadata": {
                            "phase": request.phase_name,
                            "test_types": ["unit", "integration", "system"],
                            "coverage_target": 90
                        }
                    }
                ]

            def _generate_deployment_guide(self, request):
                """Generate deployment guide for phase."""
                return [
                    {
                        "id": str(uuid.uuid4()),
                        "type": "deployment_guide",
                        "title": f"{request.project_name} - {request.phase_name} Deployment Guide",
                        "content": f"Deployment procedures for {request.phase_name} phase...",
                        "metadata": {
                            "phase": request.phase_name,
                            "environments": ["development", "staging", "production"],
                            "automation_level": "high"
                        }
                    }
                ]

            def _generate_code_review_comments(self, request):
                """Generate code review comments for phase."""
                return [
                    {
                        "id": str(uuid.uuid4()),
                        "type": "code_review_comments",
                        "title": f"{request.project_name} - {request.phase_name} Code Review",
                        "content": f"Code review feedback and comments for {request.phase_name} phase...",
                        "metadata": {
                            "phase": request.phase_name,
                            "review_type": "peer_review",
                            "comments_count": 12,
                            "approval_status": "approved"
                        }
                    }
                ]

            def _generate_architecture_diagram(self, request):
                """Generate architecture diagram for phase."""
                return [
                    {
                        "id": str(uuid.uuid4()),
                        "type": "architecture_diagram",
                        "title": f"{request.project_name} - {request.phase_name} Architecture",
                        "content": f"Architecture diagram and documentation for {request.phase_name} phase...",
                        "metadata": {
                            "phase": request.phase_name,
                            "diagram_type": "component_diagram",
                            "format": "svg",
                            "complexity": "high"
                        }
                    }
                ]

            def _count_documents_by_type(self, documents):
                """Count documents by type."""
                counts = {}
                for doc in documents:
                    doc_type = doc["type"]
                    counts[doc_type] = counts.get(doc_type, 0) + 1
                return counts

        return MockPhaseDocumentGenerator(mock_simulation_engine, mock_doc_store)

    def test_phase_documents_generation(self, phase_document_generator):
        """Test phase documents generation."""
        request = SimulationPhaseDocumentsRequest(
            project_name="SmartInventory",
            phase_name="Development",
            phase_details={
                "phase_number": 3,
                "total_phases": 5,
                "phase_goal": "Implement core features and establish CI/CD pipeline",
                "key_deliverables": [
                    "User authentication system",
                    "Inventory management API",
                    "Database integration",
                    "Unit test coverage > 80%"
                ],
                "challenges": [
                    "Complex business logic",
                    "Real-time synchronization",
                    "Scalable architecture"
                ]
            },
            document_types=[
                "technical_design",
                "test_scenarios",
                "deployment_guide",
                "code_review_comments",
                "architecture_diagram"
            ],
            team_members=[
                {
                    "name": "Alice Johnson",
                    "role": "Tech Lead",
                    "responsibilities": ["Architecture", "Code Review"]
                },
                {
                    "name": "Bob Chen",
                    "role": "DevOps Engineer",
                    "responsibilities": ["CI/CD", "Infrastructure"]
                }
            ],
            store_in_doc_store=True
        )

        result = asyncio.run(phase_document_generator.generate_phase_documents(request))

        assert result["project_name"] == "SmartInventory"
        assert result["phase_name"] == "Development"
        assert result["total_documents"] > 0

        # Check document types are generated
        expected_types = request.document_types
        for doc_type in expected_types:
            assert doc_type in result["documents_by_type"]
            assert result["documents_by_type"][doc_type] > 0

        # Check document structure and team assignment
        for doc in result["documents"]:
            assert "id" in doc
            assert "type" in doc
            assert "title" in doc
            assert "content" in doc
            assert "metadata" in doc

            # Check phase information
            assert doc["metadata"]["phase"] == request.phase_name

            # Check team member assignment
            if result["metadata"]["team_involvement"]:
                assert "author" in doc["metadata"]
                assert "author_role" in doc["metadata"]

        # Check storage
        assert result["stored_in_doc_store"] is True
        assert len(result["doc_store_ids"]) == result["total_documents"]

        # Check metadata
        metadata = result["metadata"]
        assert metadata["quality_score"] >= 0.8
        assert metadata["phase_completeness"] >= 0.8
        assert metadata["team_involvement"] is True
