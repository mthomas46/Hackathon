"""Mock Data Generators - Test data generation utilities.

Provides comprehensive test data generation utilities for the Project
Simulation Service, following ecosystem patterns for consistent and
realistic test data across all test layers.
"""

import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from unittest.mock import MagicMock

from services.project_simulation.simulation.domain.entities.project import Project
from services.project_simulation.simulation.domain.value_objects import (
    ProjectType, ComplexityLevel, ProjectStatus, TeamMember, Phase, Milestone
)


class MockDataGenerator:
    """Comprehensive mock data generator for testing."""

    def __init__(self, seed: Optional[int] = None):
        """Initialize mock data generator with optional seed for reproducibility."""
        self.seed = seed
        self._id_counter = 0

    def generate_id(self, prefix: str = "mock") -> str:
        """Generate a unique ID with prefix."""
        self._id_counter += 1
        return f"{prefix}_{self._id_counter}_{uuid.uuid4().hex[:8]}"

    def generate_project(self, **overrides) -> Project:
        """Generate a mock project entity."""
        project_data = {
            "project_id": self.generate_id("project"),
            "name": f"Mock Project {self._id_counter}",
            "description": "A comprehensive mock project for testing",
            "project_type": ProjectType.WEB_APPLICATION,
            "complexity": ComplexityLevel.MEDIUM,
            "duration_weeks": 8,
            "budget": 100000,
            "status": ProjectStatus.PLANNING
        }
        project_data.update(overrides)

        project = Project(**project_data)

        # Add some mock events
        project.events = [MagicMock() for _ in range(2)]

        return project

    def generate_team_member(self, **overrides) -> TeamMember:
        """Generate a mock team member."""
        member_data = {
            "member_id": self.generate_id("member"),
            "name": f"Mock Team Member {self._id_counter}",
            "role": "developer",
            "email": f"member{self._id_counter}@mock.com",
            "experience_years": 3,
            "skills": ["Python", "FastAPI", "Testing"],
            "productivity_factor": 1.0
        }
        member_data.update(overrides)

        return TeamMember(**member_data)

    def generate_phase(self, **overrides) -> Phase:
        """Generate a mock project phase."""
        phase_data = {
            "phase_id": self.generate_id("phase"),
            "name": f"Mock Phase {self._id_counter}",
            "description": "A mock project phase for testing",
            "start_date": datetime.now(),
            "end_date": datetime.now() + timedelta(days=14),
            "duration_days": 14,
            "status": "pending"
        }
        phase_data.update(overrides)

        return Phase(**phase_data)

    def generate_milestone(self, **overrides) -> Milestone:
        """Generate a mock project milestone."""
        milestone_data = {
            "milestone_id": self.generate_id("milestone"),
            "name": f"Mock Milestone {self._id_counter}",
            "description": "A mock project milestone for testing",
            "due_date": datetime.now() + timedelta(days=30),
            "status": "upcoming"
        }
        milestone_data.update(overrides)

        return Milestone(**milestone_data)

    def generate_simulation(self, **overrides) -> Dict[str, Any]:
        """Generate mock simulation data."""
        simulation_data = {
            "id": self.generate_id("simulation"),
            "project_id": self.generate_id("project"),
            "status": "created",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "results": None,
            "progress": 0.0,
            "estimated_completion": datetime.now() + timedelta(hours=2)
        }
        simulation_data.update(overrides)

        return simulation_data

    def generate_timeline(self, **overrides) -> Dict[str, Any]:
        """Generate mock timeline data."""
        timeline_data = {
            "id": self.generate_id("timeline"),
            "project_id": self.generate_id("project"),
            "phases": [
                self.generate_phase(),
                self.generate_phase(
                    name="Development",
                    start_date=datetime.now() + timedelta(days=15),
                    end_date=datetime.now() + timedelta(days=60)
                ),
                self.generate_phase(
                    name="Testing",
                    start_date=datetime.now() + timedelta(days=61),
                    end_date=datetime.now() + timedelta(days=75)
                )
            ],
            "milestones": [
                self.generate_milestone(),
                self.generate_milestone(
                    name="MVP Release",
                    due_date=datetime.now() + timedelta(days=45)
                )
            ],
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        timeline_data.update(overrides)

        return timeline_data

    def generate_team(self, **overrides) -> Dict[str, Any]:
        """Generate mock team data."""
        team_data = {
            "id": self.generate_id("team"),
            "project_id": self.generate_id("project"),
            "members": [
                self.generate_team_member(role="developer"),
                self.generate_team_member(role="qa_engineer"),
                self.generate_team_member(role="product_owner")
            ],
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        team_data.update(overrides)

        return team_data

    def generate_document(self, **overrides) -> Dict[str, Any]:
        """Generate mock document data."""
        document_data = {
            "id": self.generate_id("doc"),
            "title": f"Mock Document {self._id_counter}",
            "content": "This is mock document content for testing purposes.",
            "type": "technical_document",
            "project_id": self.generate_id("project"),
            "author": f"mock_author_{self._id_counter}",
            "version": "1.0.0",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "quality_score": 0.85,
            "tags": ["mock", "test", "documentation"]
        }
        document_data.update(overrides)

        return document_data

    def generate_analysis_result(self, **overrides) -> Dict[str, Any]:
        """Generate mock analysis result."""
        analysis_data = {
            "analysis_id": self.generate_id("analysis"),
            "target_id": self.generate_id("doc"),
            "analysis_type": "quality",
            "overall_score": 0.82,
            "issues": [
                {
                    "severity": "medium",
                    "description": "Mock analysis issue",
                    "suggestion": "Fix mock issue"
                }
            ],
            "recommendations": [
                "Improve mock documentation",
                "Add more mock tests"
            ],
            "created_at": datetime.now(),
            "processing_time_seconds": 1.5
        }
        analysis_data.update(overrides)

        return analysis_data

    def generate_workflow_execution(self, **overrides) -> Dict[str, Any]:
        """Generate mock workflow execution data."""
        workflow_data = {
            "workflow_id": self.generate_id("workflow"),
            "name": "Mock Analysis Workflow",
            "status": "completed",
            "steps": [
                {
                    "name": "Document Analysis",
                    "status": "completed",
                    "duration_seconds": 2.5,
                    "result": {"quality_score": 0.85}
                },
                {
                    "name": "Content Generation",
                    "status": "completed",
                    "duration_seconds": 3.2,
                    "result": {"content_length": 1500}
                }
            ],
            "total_duration_seconds": 5.7,
            "created_at": datetime.now(),
            "completed_at": datetime.now() + timedelta(seconds=6)
        }
        workflow_data.update(overrides)

        return workflow_data

    def generate_api_request(self, **overrides) -> Dict[str, Any]:
        """Generate mock API request data."""
        request_data = {
            "name": f"Mock API Project {self._id_counter}",
            "description": "Mock project created via API for testing",
            "type": ProjectType.WEB_APPLICATION.value,
            "team_size": 4,
            "complexity": ComplexityLevel.MEDIUM.value,
            "duration_weeks": 6,
            "team_members": [
                {
                    "member_id": self.generate_id("member"),
                    "name": f"API Member {i+1}",
                    "role": "developer" if i < 3 else "qa_engineer",
                    "experience_years": 2 + i,
                    "skills": ["Python", "FastAPI", "Testing"][:i+1]
                } for i in range(4)
            ],
            "phases": [
                {
                    "name": "Planning",
                    "start_date": "2024-01-01",
                    "end_date": "2024-01-10",
                    "duration_days": 10
                },
                {
                    "name": "Development",
                    "start_date": "2024-01-11",
                    "end_date": "2024-02-10",
                    "duration_days": 30
                }
            ]
        }
        request_data.update(overrides)

        return request_data

    def generate_api_response(self, **overrides) -> Dict[str, Any]:
        """Generate mock API response data."""
        response_data = {
            "success": True,
            "message": "Operation completed successfully",
            "data": {
                "id": self.generate_id("response"),
                "created_at": datetime.now().isoformat(),
                "status": "active"
            },
            "request_id": f"req_{uuid.uuid4().hex[:8]}",
            "timestamp": datetime.now().isoformat(),
            "_links": {
                "self": {"href": f"/api/v1/resource/{self.generate_id()}", "method": "GET"},
                "update": {"href": f"/api/v1/resource/{self.generate_id()}", "method": "PUT"},
                "delete": {"href": f"/api/v1/resource/{self.generate_id()}", "method": "DELETE"}
            }
        }
        response_data.update(overrides)

        return response_data


# Convenience functions for common mock data generation
def generate_mock_project(**kwargs) -> Project:
    """Generate a single mock project."""
    generator = MockDataGenerator()
    return generator.generate_project(**kwargs)


def generate_mock_team(size: int = 3, **kwargs) -> List[TeamMember]:
    """Generate a mock team of specified size."""
    generator = MockDataGenerator()
    return [generator.generate_team_member(**kwargs) for _ in range(size)]


def generate_mock_timeline(phases_count: int = 4, **kwargs) -> Dict[str, Any]:
    """Generate a mock timeline with specified number of phases."""
    generator = MockDataGenerator()
    return generator.generate_timeline(**kwargs)


def generate_mock_simulation(**kwargs) -> Dict[str, Any]:
    """Generate a single mock simulation."""
    generator = MockDataGenerator()
    return generator.generate_simulation(**kwargs)


def generate_mock_document(**kwargs) -> Dict[str, Any]:
    """Generate a single mock document."""
    generator = MockDataGenerator()
    return generator.generate_document(**kwargs)


def generate_bulk_mock_data(count: int, data_type: str, **kwargs) -> List[Any]:
    """Generate bulk mock data of specified type."""
    generator = MockDataGenerator()

    if data_type == "projects":
        return [generator.generate_project(**kwargs) for _ in range(count)]
    elif data_type == "documents":
        return [generator.generate_document(**kwargs) for _ in range(count)]
    elif data_type == "simulations":
        return [generator.generate_simulation(**kwargs) for _ in range(count)]
    else:
        raise ValueError(f"Unknown data type: {data_type}")


# Pre-defined test scenarios
TEST_SCENARIOS = {
    "simple_project": {
        "project": {
            "name": "Simple Web App",
            "type": ProjectType.WEB_APPLICATION,
            "complexity": ComplexityLevel.SIMPLE,
            "duration_weeks": 4
        },
        "team": [
            {"role": "developer", "experience_years": 2},
            {"role": "qa_engineer", "experience_years": 1}
        ]
    },
    "complex_enterprise": {
        "project": {
            "name": "Enterprise E-commerce Platform",
            "type": ProjectType.WEB_APPLICATION,
            "complexity": ComplexityLevel.COMPLEX,
            "duration_weeks": 16,
            "budget": 500000
        },
        "team": [
            {"role": "developer", "experience_years": 5},
            {"role": "architect", "experience_years": 8},
            {"role": "qa_engineer", "experience_years": 4},
            {"role": "product_owner", "experience_years": 6},
            {"role": "devops_engineer", "experience_years": 3}
        ]
    },
    "api_microservice": {
        "project": {
            "name": "User Management API",
            "type": ProjectType.API_SERVICE,
            "complexity": ComplexityLevel.MEDIUM,
            "duration_weeks": 6
        },
        "team": [
            {"role": "developer", "experience_years": 4},
            {"role": "qa_engineer", "experience_years": 3}
        ]
    }
}


def create_test_scenario(scenario_name: str) -> Dict[str, Any]:
    """Create a complete test scenario with all related data."""
    if scenario_name not in TEST_SCENARIOS:
        raise ValueError(f"Unknown test scenario: {scenario_name}")

    generator = MockDataGenerator()
    scenario = TEST_SCENARIOS[scenario_name]

    # Generate core data
    project = generator.generate_project(**scenario["project"])
    team_members = [
        generator.generate_team_member(**member)
        for member in scenario["team"]
    ]

    # Create timeline
    timeline = generator.generate_timeline(project_id=project.project_id)

    # Create simulation
    simulation = generator.generate_simulation(project_id=project.project_id)

    return {
        "project": project,
        "team": team_members,
        "timeline": timeline,
        "simulation": simulation
    }


__all__ = [
    'MockDataGenerator',
    'generate_mock_project',
    'generate_mock_team',
    'generate_mock_timeline',
    'generate_mock_simulation',
    'generate_mock_document',
    'generate_bulk_mock_data',
    'TEST_SCENARIOS',
    'create_test_scenario'
]
