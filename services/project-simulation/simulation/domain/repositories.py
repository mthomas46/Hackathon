"""Repository Interfaces - Data Access Contracts.

This module defines repository interfaces following Domain Driven Design principles.
Repositories provide a consistent interface for data access while hiding
implementation details.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from .entities.project import Project
from .entities.simulation import Simulation
from .entities.team import Team
from .entities.timeline import Timeline


class IProjectRepository(ABC):
    """Repository interface for Project aggregate."""

    @abstractmethod
    def save(self, project: Project) -> None:
        """Save a project aggregate."""

    @abstractmethod
    def find_by_id(self, project_id: str) -> Optional[Project]:
        """Find a project by its ID."""

    @abstractmethod
    def find_by_name(self, name: str) -> Optional[Project]:
        """Find a project by its name."""

    @abstractmethod
    def find_all(self) -> List[Project]:
        """Find all projects."""

    @abstractmethod
    def find_by_status(self, status: str) -> List[Project]:
        """Find projects by status."""

    @abstractmethod
    def delete(self, project_id: str) -> bool:
        """Delete a project by ID."""


class ITimelineRepository(ABC):
    """Repository interface for Timeline aggregate."""

    @abstractmethod
    def save(self, timeline: Timeline) -> None:
        """Save a timeline aggregate."""

    @abstractmethod
    def find_by_id(self, timeline_id: str) -> Optional[Timeline]:
        """Find a timeline by its ID."""

    @abstractmethod
    def find_by_project_id(self, project_id: str) -> Optional[Timeline]:
        """Find a timeline by project ID."""

    @abstractmethod
    def find_all_for_project(self, project_id: str) -> List[Timeline]:
        """Find all timelines for a project."""

    @abstractmethod
    def delete(self, timeline_id: str) -> bool:
        """Delete a timeline by ID."""


class ITeamRepository(ABC):
    """Repository interface for Team aggregate."""

    @abstractmethod
    def save(self, team: Team) -> None:
        """Save a team aggregate."""

    @abstractmethod
    def find_by_id(self, team_id: str) -> Optional[Team]:
        """Find a team by its ID."""

    @abstractmethod
    def find_by_project_id(self, project_id: str) -> Optional[Team]:
        """Find a team by project ID."""

    @abstractmethod
    def find_by_name(self, name: str) -> Optional[Team]:
        """Find a team by name."""

    @abstractmethod
    def find_all_for_project(self, project_id: str) -> List[Team]:
        """Find all teams for a project."""

    @abstractmethod
    def delete(self, team_id: str) -> bool:
        """Delete a team by ID."""


class ISimulationRepository(ABC):
    """Repository interface for Simulation aggregate."""

    @abstractmethod
    def save(self, simulation: Simulation) -> None:
        """Save a simulation aggregate."""

    @abstractmethod
    def find_by_id(self, simulation_id: str) -> Optional[Simulation]:
        """Find a simulation by its ID."""

    @abstractmethod
    def find_by_project_id(self, project_id: str) -> List[Simulation]:
        """Find all simulations for a project."""

    @abstractmethod
    def find_by_status(self, status: str) -> List[Simulation]:
        """Find simulations by status."""

    @abstractmethod
    def find_recent(self, limit: int = 10) -> List[Simulation]:
        """Find recent simulations."""

    @abstractmethod
    def delete(self, simulation_id: str) -> bool:
        """Delete a simulation by ID."""


class IUnitOfWork(ABC):
    """Unit of Work interface for transactional operations."""

    @abstractmethod
    def begin(self) -> None:
        """Begin a transaction."""

    @abstractmethod
    def commit(self) -> None:
        """Commit the transaction."""

    @abstractmethod
    def rollback(self) -> None:
        """Rollback the transaction."""

    @abstractmethod
    def __enter__(self):
        """Context manager entry."""

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""

    @property
    @abstractmethod
    def projects(self) -> IProjectRepository:
        """Get project repository."""

    @property
    @abstractmethod
    def timelines(self) -> ITimelineRepository:
        """Get timeline repository."""

    @property
    @abstractmethod
    def teams(self) -> ITeamRepository:
        """Get team repository."""

    @property
    @abstractmethod
    def simulations(self) -> ISimulationRepository:
        """Get simulation repository."""
