"""Domain Services - Cross-Aggregate Business Logic.

This module defines domain services that contain business logic spanning
multiple aggregates in the project simulation domain.
"""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Protocol
from abc import ABC, abstractmethod

from ..entities.project import Project
from ..entities.timeline import Timeline
from ..entities.team import Team
from ..entities.simulation import Simulation, SimulationConfiguration, SimulationType
from ..value_objects import SimulationMetrics, Percentage, Duration


class IProjectRepository(Protocol):
    """Repository interface for Project aggregate."""
    def save(self, project: Project) -> None: ...
    def find_by_id(self, project_id: str) -> Optional[Project]: ...
    def find_all(self) -> List[Project]: ...


class ITimelineRepository(Protocol):
    """Repository interface for Timeline aggregate."""
    def save(self, timeline: Timeline) -> None: ...
    def find_by_project_id(self, project_id: str) -> Optional[Timeline]: ...


class ITeamRepository(Protocol):
    """Repository interface for Team aggregate."""
    def save(self, team: Team) -> None: ...
    def find_by_project_id(self, project_id: str) -> Optional[Team]: ...


class ISimulationRepository(Protocol):
    """Repository interface for Simulation aggregate."""
    def save(self, simulation: Simulation) -> None: ...
    def find_by_id(self, simulation_id: str) -> Optional[Simulation]: ...
    def find_by_project_id(self, project_id: str) -> List[Simulation]: ...


class IDocumentGenerationService(Protocol):
    """Service interface for document generation."""
    async def generate_project_documents(self, project: Project) -> List[Dict[str, Any]]: ...
    async def generate_phase_documents(self, project: Project, phase_name: str) -> List[Dict[str, Any]]: ...


class IWorkflowExecutionService(Protocol):
    """Service interface for workflow execution."""
    async def execute_document_analysis_workflow(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]: ...
    async def execute_team_dynamics_workflow(self, team: Team) -> Dict[str, Any]: ...


@dataclass
class ProjectSimulationService:
    """Domain service for project simulation business logic.

    This service orchestrates complex business operations that span
    multiple aggregates and enforce domain rules.
    """

    project_repository: IProjectRepository
    timeline_repository: ITimelineRepository
    team_repository: ITeamRepository
    simulation_repository: ISimulationRepository
    document_generation_service: IDocumentGenerationService
    workflow_execution_service: IWorkflowExecutionService

    async def create_project_simulation(self, project_config: Dict[str, Any]) -> str:
        """Create a complete project simulation with all aggregates."""
        # Create Project aggregate
        project = self._create_project_from_config(project_config)

        # Create Timeline aggregate
        timeline = self._create_timeline_from_config(project_config, project.id)

        # Create Team aggregate
        team = self._create_team_from_config(project_config, project.id)

        # Create Simulation aggregate
        simulation_config = SimulationConfiguration(
            simulation_type=SimulationType.FULL_PROJECT,
            include_document_generation=True,
            include_workflow_execution=True,
            include_team_dynamics=True,
            real_time_progress=True
        )
        simulation = Simulation(
            id=None,  # Will be auto-generated
            project_id=str(project.id.value),
            configuration=simulation_config
        )

        # Save all aggregates
        self.project_repository.save(project)
        self.timeline_repository.save(timeline)
        self.team_repository.save(team)
        self.simulation_repository.save(simulation)

        return str(simulation.id.value)

    async def execute_simulation(self, simulation_id: str) -> Dict[str, Any]:
        """Execute a simulation with full orchestration."""
        # Retrieve aggregates
        simulation = self.simulation_repository.find_by_id(simulation_id)
        if not simulation:
            raise ValueError(f"Simulation {simulation_id} not found")

        project = self.project_repository.find_by_id(simulation.project_id)
        timeline = self.timeline_repository.find_by_project_id(simulation.project_id)
        team = self.team_repository.find_by_project_id(simulation.project_id)

        if not project or not timeline or not team:
            raise ValueError("Required aggregates not found")

        # Start simulation
        simulation.start_simulation()

        start_time = datetime.now()
        results = {
            "documents_generated": [],
            "workflows_executed": [],
            "errors": [],
            "insights": []
        }

        try:
            # Execute simulation phases
            for phase in timeline.phases:
                await self._execute_simulation_phase(
                    simulation, project, timeline, team, phase, results
                )

            # Calculate final metrics
            execution_time = (datetime.now() - start_time).total_seconds()
            metrics = SimulationMetrics(
                total_documents=len(results["documents_generated"]),
                total_tickets=0,  # Would be populated from JIRA simulation
                total_prs=0,      # Would be populated from GitHub simulation
                total_workflows=len(results["workflows_executed"]),
                execution_time_seconds=execution_time,
                average_response_time_ms=100.0,  # Mock value
                error_count=len(results["errors"]),
                success_rate=Percentage(95.0) if len(results["errors"]) == 0 else Percentage(80.0)
            )

            # Complete simulation
            simulation.complete_simulation(True, execution_time, metrics)

            return {
                "simulation_id": simulation_id,
                "success": True,
                "execution_time_seconds": execution_time,
                "results": results,
                "metrics": metrics
            }

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            simulation.fail_simulation(str(e))
            return {
                "simulation_id": simulation_id,
                "success": False,
                "execution_time_seconds": execution_time,
                "error": str(e)
            }

        finally:
            # Save final state
            self.simulation_repository.save(simulation)

    async def _execute_simulation_phase(self, simulation: Simulation, project: Project,
                                      timeline: Timeline, team: Team, phase: Any,
                                      results: Dict[str, Any]) -> None:
        """Execute a single simulation phase."""
        # Start phase
        simulation.update_progress(phase.name, completed=False)

        # Generate documents for this phase
        if simulation.configuration.should_generate_documents():
            try:
                documents = await self.document_generation_service.generate_phase_documents(
                    project, phase.name
                )
                results["documents_generated"].extend(documents)

                for doc in documents:
                    simulation.record_document_generation(
                        doc.get("type", "unknown"),
                        doc.get("title", "Untitled"),
                        doc.get("word_count", 0)
                    )
            except Exception as e:
                results["errors"].append(f"Document generation failed for phase {phase.name}: {str(e)}")

        # Execute workflows
        if simulation.configuration.should_execute_workflows():
            try:
                # Document analysis workflow
                if results["documents_generated"]:
                    workflow_result = await self.workflow_execution_service.execute_document_analysis_workflow(
                        results["documents_generated"]
                    )
                    results["workflows_executed"].append(workflow_result)
                    simulation.record_workflow_execution(
                        "document_analysis",
                        workflow_result.get("execution_time", 0),
                        workflow_result.get("success", True)
                    )

                # Team dynamics workflow
                if simulation.configuration.should_simulate_team_dynamics():
                    workflow_result = await self.workflow_execution_service.execute_team_dynamics_workflow(team)
                    results["workflows_executed"].append(workflow_result)
                    simulation.record_workflow_execution(
                        "team_dynamics",
                        workflow_result.get("execution_time", 0),
                        workflow_result.get("success", True)
                    )
            except Exception as e:
                results["errors"].append(f"Workflow execution failed for phase {phase.name}: {str(e)}")

        # Complete phase
        simulation.update_progress(phase.name, completed=True)

    def _create_project_from_config(self, config: Dict[str, Any]) -> Project:
        """Create Project aggregate from configuration."""
        from ..entities.project import Project, ProjectId, TeamMember

        project = Project(
            id=ProjectId(),
            name=config["name"],
            description=config.get("description", ""),
            type=config["type"],
            team_size=config["team_size"],
            complexity=config["complexity"],
            duration_weeks=config["duration_weeks"]
        )

        # Add team members if provided
        if "team_members" in config:
            for member_config in config["team_members"]:
                member = TeamMember(
                    id=member_config["id"],
                    name=member_config["name"],
                    role=member_config["role"],
                    expertise_level=member_config["expertise_level"],
                    communication_style=member_config["communication_style"],
                    work_style=member_config["work_style"],
                    specialization=member_config.get("specialization", [])
                )
                project.add_team_member(member)

        return project

    def _create_timeline_from_config(self, config: Dict[str, Any], project_id: str) -> Timeline:
        """Create Timeline aggregate from configuration."""
        from ..entities.timeline import Timeline, TimelineId, TimelinePhase, Milestone

        timeline = Timeline(
            id=TimelineId(),
            project_id=str(project_id.value)
        )

        # Add phases if provided
        if "phases" in config:
            for phase_config in config["phases"]:
                phase = TimelinePhase(
                    id=phase_config["id"],
                    name=phase_config["name"],
                    display_name=phase_config["display_name"],
                    description=phase_config["description"],
                    planned_duration=Duration(
                        weeks=phase_config["duration_weeks"],
                        days=phase_config.get("duration_days", 0)
                    ),
                    dependencies=phase_config.get("dependencies", []),
                    team_allocation=phase_config.get("team_allocation", {})
                )
                timeline.add_phase(phase)

        return timeline

    def _create_team_from_config(self, config: Dict[str, Any], project_id: str) -> Team:
        """Create Team aggregate from configuration."""
        from ..entities.team import Team, TeamId, TeamMemberEntity, ExpertiseLevel, CommunicationStyle, WorkStyle

        team = Team(
            id=TeamId(),
            project_id=str(project_id.value),
            name=config.get("team_name", "Project Team"),
            max_size=config["team_size"]
        )

        # Add team members if provided
        if "team_members" in config:
            for member_config in config["team_members"]:
                member = TeamMemberEntity(
                    id=member_config["id"],
                    name=member_config["name"],
                    email=member_config["email"],
                    role=member_config["role"],
                    expertise_level=ExpertiseLevel(member_config["expertise_level"]),
                    communication_style=CommunicationStyle(member_config["communication_style"]),
                    work_style=WorkStyle(member_config["work_style"]),
                    specialization=member_config.get("specialization", [])
                )
                team.add_member(member)

        return team
