"""In-Memory Repositories - Development and Testing Infrastructure.

This module provides in-memory implementations of repositories for development
and testing purposes, allowing the service to run without external dependencies.
"""

from typing import Dict, List, Optional
from datetime import datetime

from ...domain.entities.project import Project, ProjectId, TeamMember
from ...domain.entities.timeline import Timeline, TimelineId
from ...domain.entities.team import Team, TeamId
from ...domain.entities.simulation import Simulation, SimulationId
from ...domain.repositories import (
    IProjectRepository, ITimelineRepository, ITeamRepository, ISimulationRepository
)


class InMemoryProjectRepository(IProjectRepository):
    """In-memory implementation of project repository for development/testing."""

    def __init__(self):
        self._projects: Dict[str, Project] = {}

    async def save(self, project: Project) -> None:
        """Save a project."""
        self._projects[str(project.id.value)] = project

    async def find_by_id(self, project_id: str) -> Optional[Project]:
        """Find project by ID."""
        return self._projects.get(project_id)

    def find_by_name(self, name: str) -> Optional[Project]:
        """Find project by name."""
        for project in self._projects.values():
            if project.name == name:
                return project
        return None

    def find_all(self) -> List[Project]:
        """Find all projects."""
        return list(self._projects.values())

    def find_by_status(self, status: str) -> List[Project]:
        """Find projects by status."""
        return [p for p in self._projects.values() if p.status.value == status]

    def delete(self, project_id: str) -> bool:
        """Delete a project."""
        if project_id in self._projects:
            del self._projects[project_id]
            return True
        return False


class InMemoryTimelineRepository(ITimelineRepository):
    """In-memory implementation of timeline repository for development/testing."""

    def __init__(self):
        self._timelines: Dict[str, Timeline] = {}

    async def save(self, timeline: Timeline) -> None:
        """Save a timeline."""
        self._timelines[str(timeline.id.value)] = timeline

    async def find_by_id(self, timeline_id: str) -> Optional[Timeline]:
        """Find timeline by ID."""
        return self._timelines.get(timeline_id)

    async def find_by_project_id(self, project_id: str) -> Optional[Timeline]:
        """Find timeline by project ID."""
        for timeline in self._timelines.values():
            if timeline.project_id == project_id:
                return timeline
        return None

    def find_all_for_project(self, project_id: str) -> List[Timeline]:
        """Find all timelines for a project."""
        return [t for t in self._timelines.values() if t.project_id == project_id]

    def delete(self, timeline_id: str) -> bool:
        """Delete a timeline."""
        if timeline_id in self._timelines:
            del self._timelines[timeline_id]
            return True
        return False


class InMemoryTeamRepository(ITeamRepository):
    """In-memory implementation of team repository for development/testing."""

    def __init__(self):
        self._teams: Dict[str, Team] = {}

    async def save(self, team: Team) -> None:
        """Save a team."""
        self._teams[str(team.id.value)] = team

    async def find_by_id(self, team_id: str) -> Optional[Team]:
        """Find team by ID."""
        return self._teams.get(team_id)

    async def find_by_project_id(self, project_id: str) -> Optional[Team]:
        """Find team by project ID."""
        for team in self._teams.values():
            if team.project_id == project_id:
                return team
        return None

    def find_by_name(self, name: str) -> Optional[Team]:
        """Find team by name."""
        for team in self._teams.values():
            if team.name == name:
                return team
        return None

    def find_all_for_project(self, project_id: str) -> List[Team]:
        """Find all teams for a project."""
        return [t for t in self._teams.values() if t.project_id == project_id]

    def delete(self, team_id: str) -> bool:
        """Delete a team."""
        if team_id in self._teams:
            del self._teams[team_id]
            return True
        return False


class InMemorySimulationRepository(ISimulationRepository):
    """In-memory implementation of simulation repository for development/testing."""

    def __init__(self):
        self._simulations: Dict[str, Simulation] = {}

    async def save(self, simulation: Simulation) -> None:
        """Save a simulation."""
        self._simulations[str(simulation.id.value)] = simulation

    async def find_by_id(self, simulation_id: str) -> Optional[Simulation]:
        """Find simulation by ID."""
        return self._simulations.get(simulation_id)

    def find_by_project_id(self, project_id: str) -> List[Simulation]:
        """Find simulations by project ID."""
        return [s for s in self._simulations.values() if s.project_id == project_id]

    def find_by_status(self, status: str) -> List[Simulation]:
        """Find simulations by status."""
        return [s for s in self._simulations.values() if s.status.value == status]

    def find_recent(self, limit: int = 10) -> List[Simulation]:
        """Find recent simulations."""
        sorted_simulations = sorted(
            self._simulations.values(),
            key=lambda s: s.created_at,
            reverse=True
        )
        return sorted_simulations[:limit]

    def delete(self, simulation_id: str) -> bool:
        """Delete a simulation."""
        if simulation_id in self._simulations:
            del self._simulations[simulation_id]
            return True
        return False


# Factory functions for creating repositories
def create_in_memory_repositories():
    """Create a complete set of in-memory repositories."""
    return {
        "projects": InMemoryProjectRepository(),
        "timelines": InMemoryTimelineRepository(),
        "teams": InMemoryTeamRepository(),
        "simulations": InMemorySimulationRepository()
    }


# Repository registry for easy access
class RepositoryRegistry:
    """Registry for managing repository instances."""

    def __init__(self):
        self._repositories = create_in_memory_repositories()

    @property
    def projects(self) -> IProjectRepository:
        """Get project repository."""
        return self._repositories["projects"]

    @property
    def timelines(self) -> ITimelineRepository:
        """Get timeline repository."""
        return self._repositories["timelines"]

    @property
    def teams(self) -> ITeamRepository:
        """Get team repository."""
        return self._repositories["teams"]

    @property
    def simulations(self) -> ISimulationRepository:
        """Get simulation repository."""
        return self._repositories["simulations"]

    def reset_all(self) -> None:
        """Reset all repositories (useful for testing)."""
        self._repositories = create_in_memory_repositories()


# Global repository registry instance
_repository_registry: Optional[RepositoryRegistry] = None


def get_repository_registry() -> RepositoryRegistry:
    """Get the global repository registry instance."""
    global _repository_registry
    if _repository_registry is None:
        _repository_registry = RepositoryRegistry()
    return _repository_registry


# Convenience functions
def get_project_repository() -> IProjectRepository:
    """Get project repository."""
    return get_repository_registry().projects

def get_timeline_repository() -> ITimelineRepository:
    """Get timeline repository."""
    return get_repository_registry().timelines

def get_team_repository() -> ITeamRepository:
    """Get team repository."""
    return get_repository_registry().teams

def get_simulation_repository() -> ISimulationRepository:
    """Get simulation repository."""
    return get_repository_registry().simulations


__all__ = [
    'InMemoryProjectRepository',
    'InMemoryTimelineRepository',
    'InMemoryTeamRepository',
    'InMemorySimulationRepository',
    'RepositoryRegistry',
    'get_repository_registry',
    'get_project_repository',
    'get_timeline_repository',
    'get_team_repository',
    'get_simulation_repository'
]
