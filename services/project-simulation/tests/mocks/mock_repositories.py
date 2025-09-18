"""Mock Repositories - Repository mocking for testing.

Provides mock implementations of all repository interfaces used in the
Project Simulation Service, following ecosystem patterns for consistent
test behavior and reliable data isolation.
"""

import asyncio
from typing import Dict, Any, List, Optional, Union
from unittest.mock import MagicMock
from datetime import datetime

from services.project_simulation.simulation.domain.entities.project import Project
from services.project_simulation.simulation.domain.value_objects import (
    ProjectType, ComplexityLevel, ProjectStatus
)


class MockProjectRepository:
    """Mock project repository with configurable behavior."""

    def __init__(self):
        self.projects: Dict[str, Any] = {}
        self.save_calls = []
        self.get_calls = []
        self.list_calls = []
        self.should_fail = False
        self.delay_seconds = 0

    async def save(self, project: Any) -> None:
        """Mock save operation."""
        if self.delay_seconds > 0:
            await asyncio.sleep(self.delay_seconds)

        if self.should_fail:
            raise Exception("Mock repository save failure")

        self.projects[project.project_id] = project
        self.save_calls.append({
            "project_id": project.project_id,
            "project_name": project.name,
            "timestamp": datetime.now()
        })

    async def get(self, project_id: str) -> Optional[Any]:
        """Mock get operation."""
        if self.delay_seconds > 0:
            await asyncio.sleep(self.delay_seconds)

        if self.should_fail:
            raise Exception("Mock repository get failure")

        self.get_calls.append({
            "project_id": project_id,
            "timestamp": datetime.now()
        })

        return self.projects.get(project_id)

    async def list(self, filters: Optional[Dict[str, Any]] = None) -> List[Any]:
        """Mock list operation."""
        if self.delay_seconds > 0:
            await asyncio.sleep(self.delay_seconds)

        if self.should_fail:
            raise Exception("Mock repository list failure")

        filters = filters or {}
        self.list_calls.append({
            "filters": filters,
            "timestamp": datetime.now()
        })

        projects = list(self.projects.values())

        # Apply filters
        if filters:
            filtered_projects = []
            for project in projects:
                match = True
                for key, value in filters.items():
                    if hasattr(project, key):
                        if getattr(project, key) != value:
                            match = False
                            break
                    else:
                        match = False
                        break
                if match:
                    filtered_projects.append(project)
            return filtered_projects

        return projects

    async def delete(self, project_id: str) -> bool:
        """Mock delete operation."""
        if self.delay_seconds > 0:
            await asyncio.sleep(self.delay_seconds)

        if self.should_fail:
            raise Exception("Mock repository delete failure")

        if project_id in self.projects:
            del self.projects[project_id]
            return True
        return False

    async def exists(self, project_id: str) -> bool:
        """Mock exists operation."""
        if self.delay_seconds > 0:
            await asyncio.sleep(self.delay_seconds)

        return project_id in self.projects

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Mock count operation."""
        if self.delay_seconds > 0:
            await asyncio.sleep(self.delay_seconds)

        projects = await self.list(filters)
        return len(projects)

    def reset(self):
        """Reset mock state."""
        self.projects.clear()
        self.save_calls.clear()
        self.get_calls.clear()
        self.list_calls.clear()
        self.should_fail = False
        self.delay_seconds = 0

    def add_project(self, project: Any):
        """Helper to add project to mock repository."""
        self.projects[project.project_id] = project


class MockSimulationRepository:
    """Mock simulation repository with configurable behavior."""

    def __init__(self):
        self.simulations: Dict[str, Any] = {}
        self.save_calls = []
        self.get_calls = []
        self.update_calls = []
        self.should_fail = False
        self.delay_seconds = 0

    async def save(self, simulation: Any) -> None:
        """Mock save operation."""
        if self.delay_seconds > 0:
            await asyncio.sleep(self.delay_seconds)

        if self.should_fail:
            raise Exception("Mock simulation repository save failure")

        self.simulations[simulation.id] = simulation
        self.save_calls.append({
            "simulation_id": simulation.id,
            "status": getattr(simulation, 'status', 'unknown'),
            "timestamp": datetime.now()
        })

    async def get(self, simulation_id: str) -> Optional[Any]:
        """Mock get operation."""
        if self.delay_seconds > 0:
            await asyncio.sleep(self.delay_seconds)

        if self.should_fail:
            raise Exception("Mock simulation repository get failure")

        self.get_calls.append({
            "simulation_id": simulation_id,
            "timestamp": datetime.now()
        })

        return self.simulations.get(simulation_id)

    async def update(self, simulation_id: str, updates: Dict[str, Any]) -> bool:
        """Mock update operation."""
        if self.delay_seconds > 0:
            await asyncio.sleep(self.delay_seconds)

        if self.should_fail:
            raise Exception("Mock simulation repository update failure")

        if simulation_id in self.simulations:
            simulation = self.simulations[simulation_id]
            for key, value in updates.items():
                if hasattr(simulation, key):
                    setattr(simulation, key, value)

            self.update_calls.append({
                "simulation_id": simulation_id,
                "updates": updates,
                "timestamp": datetime.now()
            })
            return True
        return False

    async def delete(self, simulation_id: str) -> bool:
        """Mock delete operation."""
        if self.delay_seconds > 0:
            await asyncio.sleep(self.delay_seconds)

        if simulation_id in self.simulations:
            del self.simulations[simulation_id]
            return True
        return False

    async def list_by_status(self, status: str) -> List[Any]:
        """Mock list by status operation."""
        if self.delay_seconds > 0:
            await asyncio.sleep(self.delay_seconds)

        simulations = []
        for simulation in self.simulations.values():
            if getattr(simulation, 'status', None) == status:
                simulations.append(simulation)
        return simulations

    async def get_by_project(self, project_id: str) -> List[Any]:
        """Mock get by project operation."""
        if self.delay_seconds > 0:
            await asyncio.sleep(self.delay_seconds)

        simulations = []
        for simulation in self.simulations.values():
            if getattr(simulation, 'project_id', None) == project_id:
                simulations.append(simulation)
        return simulations

    def reset(self):
        """Reset mock state."""
        self.simulations.clear()
        self.save_calls.clear()
        self.get_calls.clear()
        self.update_calls.clear()
        self.should_fail = False
        self.delay_seconds = 0

    def add_simulation(self, simulation: Any):
        """Helper to add simulation to mock repository."""
        self.simulations[simulation.id] = simulation


class MockTimelineRepository:
    """Mock timeline repository with configurable behavior."""

    def __init__(self):
        self.timelines: Dict[str, Any] = {}
        self.save_calls = []
        self.get_calls = []
        self.should_fail = False
        self.delay_seconds = 0

    async def save(self, timeline: Any) -> None:
        """Mock save operation."""
        if self.delay_seconds > 0:
            await asyncio.sleep(self.delay_seconds)

        if self.should_fail:
            raise Exception("Mock timeline repository save failure")

        timeline_id = getattr(timeline, 'id', getattr(timeline, 'timeline_id', 'default'))
        self.timelines[timeline_id] = timeline
        self.save_calls.append({
            "timeline_id": timeline_id,
            "phases_count": len(getattr(timeline, 'phases', [])),
            "timestamp": datetime.now()
        })

    async def get(self, timeline_id: str) -> Optional[Any]:
        """Mock get operation."""
        if self.delay_seconds > 0:
            await asyncio.sleep(self.delay_seconds)

        if self.should_fail:
            raise Exception("Mock timeline repository get failure")

        self.get_calls.append({
            "timeline_id": timeline_id,
            "timestamp": datetime.now()
        })

        return self.timelines.get(timeline_id)

    async def get_by_project(self, project_id: str) -> Optional[Any]:
        """Mock get by project operation."""
        if self.delay_seconds > 0:
            await asyncio.sleep(self.delay_seconds)

        for timeline in self.timelines.values():
            if getattr(timeline, 'project_id', None) == project_id:
                return timeline
        return None

    async def update_phase(self, timeline_id: str, phase_index: int, updates: Dict[str, Any]) -> bool:
        """Mock update phase operation."""
        if self.delay_seconds > 0:
            await asyncio.sleep(self.delay_seconds)

        if timeline_id in self.timelines:
            timeline = self.timelines[timeline_id]
            if hasattr(timeline, 'phases') and phase_index < len(timeline.phases):
                phase = timeline.phases[phase_index]
                for key, value in updates.items():
                    if hasattr(phase, key):
                        setattr(phase, key, value)
                return True
        return False

    def reset(self):
        """Reset mock state."""
        self.timelines.clear()
        self.save_calls.clear()
        self.get_calls.clear()
        self.should_fail = False
        self.delay_seconds = 0

    def add_timeline(self, timeline: Any):
        """Helper to add timeline to mock repository."""
        timeline_id = getattr(timeline, 'id', getattr(timeline, 'timeline_id', 'default'))
        self.timelines[timeline_id] = timeline


class MockTeamRepository:
    """Mock team repository with configurable behavior."""

    def __init__(self):
        self.teams: Dict[str, Any] = {}
        self.save_calls = []
        self.get_calls = []
        self.should_fail = False
        self.delay_seconds = 0

    async def save(self, team: Any) -> None:
        """Mock save operation."""
        if self.delay_seconds > 0:
            await asyncio.sleep(self.delay_seconds)

        if self.should_fail:
            raise Exception("Mock team repository save failure")

        team_id = getattr(team, 'id', getattr(team, 'team_id', 'default'))
        self.teams[team_id] = team
        self.save_calls.append({
            "team_id": team_id,
            "members_count": len(getattr(team, 'members', [])),
            "timestamp": datetime.now()
        })

    async def get(self, team_id: str) -> Optional[Any]:
        """Mock get operation."""
        if self.delay_seconds > 0:
            await asyncio.sleep(self.delay_seconds)

        if self.should_fail:
            raise Exception("Mock team repository get failure")

        self.get_calls.append({
            "team_id": team_id,
            "timestamp": datetime.now()
        })

        return self.teams.get(team_id)

    async def get_by_project(self, project_id: str) -> Optional[Any]:
        """Mock get by project operation."""
        if self.delay_seconds > 0:
            await asyncio.sleep(self.delay_seconds)

        for team in self.teams.values():
            if getattr(team, 'project_id', None) == project_id:
                return team
        return None

    async def add_member(self, team_id: str, member: Any) -> bool:
        """Mock add member operation."""
        if self.delay_seconds > 0:
            await asyncio.sleep(self.delay_seconds)

        if team_id in self.teams:
            team = self.teams[team_id]
            if not hasattr(team, 'members'):
                team.members = []
            team.members.append(member)
            return True
        return False

    async def remove_member(self, team_id: str, member_id: str) -> bool:
        """Mock remove member operation."""
        if self.delay_seconds > 0:
            await asyncio.sleep(self.delay_seconds)

        if team_id in self.teams:
            team = self.teams[team_id]
            if hasattr(team, 'members'):
                team.members = [m for m in team.members if getattr(m, 'member_id', None) != member_id]
                return True
        return False

    def reset(self):
        """Reset mock state."""
        self.teams.clear()
        self.save_calls.clear()
        self.get_calls.clear()
        self.should_fail = False
        self.delay_seconds = 0

    def add_team(self, team: Any):
        """Helper to add team to mock repository."""
        team_id = getattr(team, 'id', getattr(team, 'team_id', 'default'))
        self.teams[team_id] = team


# Factory functions for easy mock creation
def create_mock_project_repository(**kwargs) -> MockProjectRepository:
    """Create configured mock project repository."""
    repo = MockProjectRepository()

    for key, value in kwargs.items():
        if hasattr(repo, key):
            setattr(repo, key, value)

    return repo


def create_mock_simulation_repository(**kwargs) -> MockSimulationRepository:
    """Create configured mock simulation repository."""
    repo = MockSimulationRepository()

    for key, value in kwargs.items():
        if hasattr(repo, key):
            setattr(repo, key, value)

    return repo


def create_mock_timeline_repository(**kwargs) -> MockTimelineRepository:
    """Create configured mock timeline repository."""
    repo = MockTimelineRepository()

    for key, value in kwargs.items():
        if hasattr(repo, key):
            setattr(repo, key, value)

    return repo


def create_mock_team_repository(**kwargs) -> MockTeamRepository:
    """Create configured mock team repository."""
    repo = MockTeamRepository()

    for key, value in kwargs.items():
        if hasattr(repo, key):
            setattr(repo, key, value)

    return repo


# Bulk repository creation
def create_mock_repositories(**kwargs) -> Dict[str, Any]:
    """Create all mock repositories with shared configuration."""
    return {
        'project': create_mock_project_repository(**kwargs),
        'simulation': create_mock_simulation_repository(**kwargs),
        'timeline': create_mock_timeline_repository(**kwargs),
        'team': create_mock_team_repository(**kwargs)
    }


__all__ = [
    'MockProjectRepository',
    'MockSimulationRepository',
    'MockTimelineRepository',
    'MockTeamRepository',
    'create_mock_project_repository',
    'create_mock_simulation_repository',
    'create_mock_timeline_repository',
    'create_mock_team_repository',
    'create_mock_repositories'
]
