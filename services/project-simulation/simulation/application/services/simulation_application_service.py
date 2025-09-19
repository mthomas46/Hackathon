"""Application Services - Use Case Orchestration.

This module provides application services that orchestrate domain services
to fulfill high-level use cases following CQRS and Clean Architecture patterns.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime

from ...domain.services.project_simulation_service import ProjectSimulationService
from ...infrastructure.logging import SimulationLogger
from ...presentation.websockets.simulation_websocket import (
    notify_simulation_progress,
    notify_simulation_event
)
from ...domain.value_objects import SimulationStatus
from ...domain.entities.simulation import SimulationType
from ...infrastructure.config.simulation_config_loader import (
    load_simulation_config, create_sample_simulation_config, SimulationConfigFile, get_simulation_config_loader
)


class SimulationApplicationService:
    """Application service for simulation use cases.

    This service orchestrates domain services to fulfill high-level
    business use cases while maintaining clean architecture principles.
    """

    def __init__(self,
                 domain_service,
                 project_repository,
                 timeline_repository,
                 team_repository,
                 simulation_repository,
                 monitoring_service,
                 logger):
        """Initialize application service."""
        self._domain_service = domain_service
        self._project_repository = project_repository
        self._timeline_repository = timeline_repository
        self._team_repository = team_repository
        self._simulation_repository = simulation_repository
        self._monitoring_service = monitoring_service
        self._logger = logger

    async def create_simulation(self, request: Dict[str, Any], correlation_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a new project simulation."""
        try:
            self._logger.info(
                "Creating new simulation",
                operation="create_simulation",
                project_name=request.get("name", "unknown")
            )

            start_time = datetime.now()

            # Create project first
            from ...domain.entities.project import Project, ProjectId
            from ...domain.entities.simulation import Simulation, SimulationId, SimulationConfiguration
            from ...domain.value_objects import ProjectType, ComplexityLevel

            project = Project(
                id=ProjectId(),
                name=request["name"],
                description=request.get("description", ""),
                type=ProjectType(request.get("type", "web_application")),
                team_size=request.get("team_size", 5),
                complexity=ComplexityLevel(request.get("complexity", "medium")),
                duration_weeks=request.get("duration_weeks", 8),
                budget=request.get("budget"),
                technologies=request.get("technologies", [])
            )

            # Save project
            await self._project_repository.save(project)

            # Create simulation
            simulation_config = SimulationConfiguration(
                simulation_type=SimulationType(request.get("simulation_type", "full_project")),
                include_document_generation=request.get("include_documents", True),
                include_workflow_execution=request.get("include_workflows", True),
                include_team_dynamics=request.get("include_team", True),
                real_time_progress=request.get("real_time", False),
                max_execution_time_minutes=request.get("max_time_minutes", 60),
                generate_realistic_delays=request.get("realistic_delays", True),
                capture_metrics=request.get("capture_metrics", True),
                enable_ecosystem_integration=request.get("ecosystem_integration", True)
            )

            simulation = Simulation(
                id=SimulationId(),
                project_id=str(project.id.value),
                configuration=simulation_config
            )

            # Create default timeline
            from ...domain.entities.timeline import Timeline, TimelineId, TimelinePhase
            from ...domain.value_objects import Duration
            from datetime import timedelta

            phases = []
            start_date = datetime.now()
            for i, phase_name in enumerate(["Planning", "Design", "Development", "Testing", "Deployment"]):
                phase_start = start_date + timedelta(weeks=i*2)
                phase_end = phase_start + timedelta(weeks=2)
                phases.append(TimelinePhase(
                    id=f"phase_{i+1}",
                    name=phase_name,
                    display_name=phase_name,
                    description=f"{phase_name} phase of the project",
                    planned_duration=Duration(weeks=2),
                    start_date=phase_start,
                    planned_end_date=phase_end,
                    status="pending" if i > 0 else "in_progress"
                ))

            timeline = Timeline(
                id=TimelineId(),
                project_id=str(project.id.value),
                phases=phases
            )

            # Save timeline
            await self._timeline_repository.save(timeline)

            # Create default team
            from ...domain.entities.team import Team, TeamId, TeamMemberEntity, TeamRole, ExpertiseLevel, CommunicationStyle, WorkStyle, MoraleLevel, BurnoutRisk

            team_members = []
            # Create common team roles
            product_manager = TeamRole(
                name="Product Manager",
                description="Manages product vision and requirements",
                required_expertise=ExpertiseLevel.ADVANCED
            )
            technical_lead = TeamRole(
                name="Technical Lead",
                description="Leads technical architecture and development",
                required_expertise=ExpertiseLevel.EXPERT
            )
            senior_developer = TeamRole(
                name="Senior Developer",
                description="Experienced software developer",
                required_expertise=ExpertiseLevel.ADVANCED
            )
            qa_engineer = TeamRole(
                name="QA Engineer",
                description="Quality assurance and testing specialist",
                required_expertise=ExpertiseLevel.INTERMEDIATE
            )

            roles = [product_manager, technical_lead, senior_developer, qa_engineer]
            for i, role in enumerate(roles):
                member = TeamMemberEntity(
                    id=f"member_{i+1}",
                    name=f"Team Member {i+1}",
                    email=f"member{i+1}@project.com",
                    role=role,
                    expertise_level=ExpertiseLevel.SENIOR,
                    communication_style=CommunicationStyle.COLLABORATIVE,
                    work_style=WorkStyle.TEAM_PLAYER,
                    productivity_multiplier=1.0 + (i * 0.1),
                    morale_level=MoraleLevel.HIGH,
                    burnout_risk=BurnoutRisk.LOW,
                    joined_at=datetime.now() - timedelta(days=30),
                    specialization=["Python", "FastAPI", "Testing"][:i+1] + ["Communication"]
                )
                team_members.append(member)

            team = Team(
                id=TeamId(),
                project_id=str(project.id.value),
                name=f"Team for {project.name}",
                members=team_members,
                max_size=6
            )

            # Save team
            await self._team_repository.save(team)

            # Save simulation
            await self._simulation_repository.save(simulation)

            simulation_id = str(simulation.id.value)

            duration = (datetime.now() - start_time).total_seconds()

            self._logger.log_performance(
                operation="create_simulation",
                duration=duration,
                simulation_id=simulation_id,
                correlation_id=correlation_id
            )

            # Notify WebSocket clients about new simulation
            try:
                await notify_simulation_progress(simulation_id, {
                    "progress_percentage": 0.0,
                    "current_phase": "Initialization",
                    "status": "created",
                    "message": "Simulation created successfully"
                })
            except Exception as ws_error:
                self._logger.warning(
                    "Failed to send WebSocket notification for simulation creation",
                    error=str(ws_error),
                    simulation_id=simulation_id
                )

            return {
                "success": True,
                "simulation_id": simulation_id,
                "message": "Simulation created successfully",
                "created_at": datetime.now().isoformat()
            }

        except Exception as e:
            self._logger.error(
                "Failed to create simulation",
                error=str(e),
                correlation_id=correlation_id
            )
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to create simulation"
            }

    async def link_document_to_simulation(self, simulation_id: str, document_id: str,
                                       document_type: str, doc_store_reference: str) -> None:
        """Link a document to a simulation in the repository."""
        await self._simulation_repository.link_document_to_simulation(
            simulation_id, document_id, document_type, doc_store_reference
        )

    async def link_prompt_to_simulation(self, simulation_id: str, prompt_id: str,
                                      prompt_type: str, prompt_store_reference: str) -> None:
        """Link a prompt to a simulation in the repository."""
        await self._simulation_repository.link_prompt_to_simulation(
            simulation_id, prompt_id, prompt_type, prompt_store_reference
        )

    async def get_simulation_documents(self, simulation_id: str) -> List[Dict[str, Any]]:
        """Get all documents linked to a simulation."""
        return await self._simulation_repository.get_simulation_documents(simulation_id)

    async def get_simulation_prompts(self, simulation_id: str) -> List[Dict[str, Any]]:
        """Get all prompts linked to a simulation."""
        return await self._simulation_repository.get_simulation_prompts(simulation_id)

    async def save_simulation_run_data(self, simulation_id: str, run_id: str, execution_data: Dict[str, Any]) -> None:
        """Save simulation run data to the repository."""
        await self._simulation_repository.save_simulation_run_data(simulation_id, run_id, execution_data)

    async def get_simulation_run_data(self, simulation_id: str, run_id: str) -> Optional[Dict[str, Any]]:
        """Get simulation run data from the repository."""
        return await self._simulation_repository.get_simulation_run_data(simulation_id, run_id)

    async def execute_simulation(self, simulation_id: str) -> Dict[str, Any]:
        """Execute a simulation."""
        correlation_id = getattr(self._logger, '_correlation_id', None) or 'unknown'

        try:
            self._logger.info(
                "Executing simulation",
                operation="execute_simulation",
                simulation_id=simulation_id,
                correlation_id=correlation_id
            )

            # Execute simulation using execution engine
            from ...infrastructure.execution.simulation_execution_engine import SimulationExecutionEngine
            from ...infrastructure.content.content_generation_pipeline import ContentGenerationPipeline
            from ...infrastructure.clients.ecosystem_clients import get_ecosystem_service_registry
            from ...infrastructure.workflows.workflow_orchestrator import SimulationWorkflowOrchestrator

            # Create execution engine
            execution_engine = SimulationExecutionEngine(
                content_pipeline=ContentGenerationPipeline(),
                ecosystem_clients=get_ecosystem_service_registry(),
                workflow_orchestrator=SimulationWorkflowOrchestrator(),
                logger=self._logger,
                monitoring_service=self._monitoring_service,
                simulation_repository=self._simulation_repository,
                project_repository=self._project_repository,
                timeline_repository=self._timeline_repository,
                team_repository=self._team_repository
            )

            # Execute simulation
            result = await execution_engine.execute_simulation(simulation_id)

            self._logger.info(
                "Simulation execution completed",
                operation="execute_simulation",
                simulation_id=simulation_id,
                success=result.get("success", False),
                duration=result.get("execution_time_seconds", 0),
                correlation_id=correlation_id
            )

            # Notify WebSocket clients about execution start
            try:
                await notify_simulation_progress(simulation_id, {
                    "progress_percentage": 10.0,
                    "current_phase": "Execution",
                    "status": "running",
                    "message": "Simulation execution started",
                    "execution_time_seconds": result.get("execution_time_seconds", 0)
                })
            except Exception as ws_error:
                self._logger.warning(
                    "Failed to send WebSocket notification for simulation execution",
                    error=str(ws_error),
                    simulation_id=simulation_id
                )

            return result

        except Exception as e:
            self._logger.error(
                "Failed to execute simulation",
                error=str(e),
                simulation_id=simulation_id,
                correlation_id=correlation_id
            )
            return {
                "success": False,
                "simulation_id": simulation_id,
                "error": str(e),
                "message": "Failed to execute simulation"
            }

    async def get_simulation_status(self, simulation_id: str) -> Dict[str, Any]:
        """Get simulation status."""
        correlation_id = getattr(self._logger, '_correlation_id', None) or 'unknown'

        try:
            self._logger.debug(
                "Getting simulation status",
                operation="get_simulation_status",
                simulation_id=simulation_id,
                correlation_id=correlation_id
            )

            # Get simulation from repository
            simulation = await self._simulation_repository.find_by_id(simulation_id)

            if not simulation:
                return {
                    "success": False,
                    "error": "Simulation not found",
                    "simulation_id": simulation_id
                }

            return {
                "success": True,
                "simulation_id": simulation_id,
                "status": simulation.status.value,
                "progress": simulation.get_progress_percentage(),
                "created_at": simulation.created_at.isoformat(),
                "started_at": simulation.started_at.isoformat() if simulation.started_at else None,
                "completed_at": simulation.completed_at.isoformat() if simulation.completed_at else None,
                "result": simulation.result.get_summary() if simulation.result else None
            }

        except Exception as e:
            self._logger.error(
                "Failed to get simulation status",
                error=str(e),
                simulation_id=simulation_id,
                correlation_id=correlation_id
            )
            return {
                "success": False,
                "simulation_id": simulation_id,
                "error": str(e)
            }

    async def list_simulations(self, status_filter: Optional[str] = None,
                              limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """List simulations with optional filtering."""
        correlation_id = getattr(self._logger, '_correlation_id', None) or 'unknown'

        try:
            self._logger.debug(
                "Listing simulations",
                operation="list_simulations",
                status_filter=status_filter,
                limit=limit,
                correlation_id=correlation_id
            )

            # Get simulations from repository
            from ...infrastructure.di_container import get_simulation_container
            simulation_repo = get_simulation_container().simulation_repository

            if status_filter:
                simulations = simulation_repo.find_by_status(status_filter)
            else:
                simulations = simulation_repo.find_recent(limit)

            # Convert to response format
            simulation_list = []
            for sim in simulations[:limit]:
                simulation_list.append({
                    "id": str(sim.id.value),
                    "project_id": sim.project_id,
                    "status": sim.status.value,
                    "progress": sim.get_progress_percentage(),
                    "created_at": sim.created_at.isoformat(),
                    "started_at": sim.started_at.isoformat() if sim.started_at else None,
                    "completed_at": sim.completed_at.isoformat() if sim.completed_at else None
                })

            return {
                "success": True,
                "simulations": simulation_list,
                "total": len(simulation_list),
                "filter": status_filter
            }

        except Exception as e:
            self._logger.error(
                "Failed to list simulations",
                error=str(e),
                status_filter=status_filter,
                correlation_id=correlation_id
            )
            return {
                "success": False,
                "error": str(e),
                "simulations": [],
                "total": 0
            }

    async def cancel_simulation(self, simulation_id: str) -> Dict[str, Any]:
        """Cancel a running simulation."""
        correlation_id = getattr(self._logger, '_correlation_id', None) or 'unknown'

        try:
            self._logger.info(
                "Cancelling simulation",
                operation="cancel_simulation",
                simulation_id=simulation_id,
                correlation_id=correlation_id
            )

            # Get simulation from repository
            from ...infrastructure.di_container import get_simulation_container
            simulation_repo = get_simulation_container().simulation_repository
            simulation = simulation_repo.find_by_id(simulation_id)

            if not simulation:
                return {
                    "success": False,
                    "error": "Simulation not found",
                    "simulation_id": simulation_id
                }

            if simulation.is_completed():
                return {
                    "success": False,
                    "error": "Simulation is already completed",
                    "simulation_id": simulation_id,
                    "status": simulation.status.value
                }

            # Cancel simulation
            simulation.cancel_simulation()
            simulation_repo.save(simulation)

            self._logger.info(
                "Simulation cancelled successfully",
                operation="cancel_simulation",
                simulation_id=simulation_id,
                correlation_id=correlation_id
            )

            return {
                "success": True,
                "simulation_id": simulation_id,
                "message": "Simulation cancelled successfully",
                "cancelled_at": datetime.now().isoformat()
            }

        except Exception as e:
            self._logger.error(
                "Failed to cancel simulation",
                error=str(e),
                simulation_id=simulation_id,
                correlation_id=correlation_id
            )
            return {
                "success": False,
                "simulation_id": simulation_id,
                "error": str(e)
            }

    async def get_simulation_results(self, simulation_id: str) -> Dict[str, Any]:
        """Get detailed simulation results."""
        correlation_id = getattr(self._logger, '_correlation_id', None) or 'unknown'

        try:
            self._logger.debug(
                "Getting simulation results",
                operation="get_simulation_results",
                simulation_id=simulation_id,
                correlation_id=correlation_id
            )

            # Get simulation from repository
            from ...infrastructure.di_container import get_simulation_container
            simulation_repo = get_simulation_container().simulation_repository
            simulation = simulation_repo.find_by_id(simulation_id)

            if not simulation:
                return {
                    "success": False,
                    "error": "Simulation not found",
                    "simulation_id": simulation_id
                }

            if not simulation.result:
                return {
                    "success": False,
                    "error": "Simulation has no results yet",
                    "simulation_id": simulation_id,
                    "status": simulation.status.value
                }

            return {
                "success": True,
                "simulation_id": simulation_id,
                "results": simulation.result.get_summary(),
                "documents_created": simulation.result.documents_created,
                "workflows_executed": simulation.result.workflows_executed,
                "insights": simulation.result.insights,
                "errors": simulation.result.errors,
                "warnings": simulation.result.warnings
            }

        except Exception as e:
            self._logger.error(
                "Failed to get simulation results",
                error=str(e),
                simulation_id=simulation_id,
                correlation_id=correlation_id
            )
            return {
                "success": False,
                "simulation_id": simulation_id,
                "error": str(e)
            }

    async def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status."""
        correlation_id = getattr(self._logger, '_correlation_id', None) or 'unknown'

        try:
            from ...infrastructure.di_container import get_simulation_container
            health_manager = get_simulation_container().health_manager

            health_status = await health_manager.simulation_health()

            return {
                "success": True,
                "health": health_status
            }

        except Exception as e:
            self._logger.error(
                "Failed to get health status",
                error=str(e),
                correlation_id=correlation_id
            )
            return {
                "success": False,
                "error": str(e)
            }

    async def create_simulation_from_config_file(self, config_file_path: str) -> Dict[str, Any]:
        """Create a simulation from a configuration file."""
        try:
            self._logger.info(
                "Creating simulation from configuration file",
                config_file_path=config_file_path
            )

            # Load configuration from file
            config = load_simulation_config(config_file_path)

            # Validate configuration
            issues = get_simulation_config_loader().validate_config(config)
            if issues:
                return {
                    "success": False,
                    "error": "Configuration validation failed",
                    "issues": issues,
                    "config_file_path": config_file_path
                }

            # Convert configuration to simulation request format
            simulation_request = self._convert_config_to_simulation_request(config)

            # Create simulation using existing method
            return await self.create_simulation(simulation_request)

        except Exception as e:
            self._logger.error(
                "Failed to create simulation from config file",
                error=str(e),
                config_file_path=config_file_path
            )
            return {
                "success": False,
                "error": str(e),
                "config_file_path": config_file_path
            }

    async def create_sample_config_file(self, file_path: str,
                                      project_name: str = "Sample E-commerce Platform") -> Dict[str, Any]:
        """Create a sample configuration file."""
        try:
            self._logger.info(
                "Creating sample configuration file",
                file_path=file_path,
                project_name=project_name
            )

            # Create sample configuration
            config = create_sample_simulation_config(file_path, project_name)

            return {
                "success": True,
                "message": "Sample configuration file created successfully",
                "file_path": file_path,
                "project_name": config.project_name,
                "simulation_type": config.simulation_type.value,
                "team_size": len(config.team_members),
                "timeline_phases": len(config.timeline_phases),
                "duration_weeks": config.duration_weeks
            }

        except Exception as e:
            self._logger.error(
                "Failed to create sample configuration file",
                error=str(e),
                file_path=file_path
            )
            return {
                "success": False,
                "error": str(e),
                "file_path": file_path
            }

    async def validate_config_file(self, config_file_path: str) -> Dict[str, Any]:
        """Validate a configuration file without creating a simulation."""
        try:
            self._logger.info(
                "Validating configuration file",
                config_file_path=config_file_path
            )

            # Load configuration from file
            config = load_simulation_config(config_file_path)

            # Validate configuration
            issues = get_simulation_config_loader().validate_config(config)

            return {
                "success": True,
                "valid": len(issues) == 0,
                "issues": issues,
                "config_file_path": config_file_path,
                "project_name": config.project_name,
                "simulation_type": config.simulation_type.value,
                "team_size": len(config.team_members),
                "timeline_phases": len(config.timeline_phases)
            }

        except Exception as e:
            self._logger.error(
                "Failed to validate configuration file",
                error=str(e),
                config_file_path=config_file_path
            )
            return {
                "success": False,
                "error": str(e),
                "config_file_path": config_file_path
            }

    def _convert_config_to_simulation_request(self, config: SimulationConfigFile) -> Dict[str, Any]:
        """Convert a configuration file object to a simulation creation request."""
        return {
            "name": config.project_name,
            "description": config.project_description,
            "type": config.project_type.value,
            "complexity": config.complexity_level.value,
            "duration_weeks": config.duration_weeks,
            "budget": config.budget,
            "team_size": len(config.team_members),
            "simulation_type": config.simulation_type.value,
            "include_documents": config.include_document_generation,
            "include_workflows": config.include_workflow_execution,
            "include_team": config.include_team_dynamics,
            "real_time": config.real_time_progress,
            "max_time_minutes": config.max_execution_time_minutes,
            "realistic_delays": config.generate_realistic_delays,
            "capture_metrics": config.capture_metrics,
            "ecosystem_integration": config.enable_ecosystem_integration,
            "technologies": ["Python", "FastAPI", "React", "PostgreSQL"]  # Default technologies
        }

    async def get_config_template(self) -> Dict[str, Any]:
        """Get a configuration template for creating custom simulation configs."""
        try:
            template = get_simulation_config_loader().get_config_template()

            return {
                "success": True,
                "template": template,
                "description": "Configuration template for creating custom simulation scenarios",
                "supported_formats": ["yaml", "yml", "json"],
                "example_usage": {
                    "yaml": "config/simulation_config.yaml",
                    "json": "config/simulation_config.json"
                }
            }

        except Exception as e:
            self._logger.error(
                "Failed to get configuration template",
                error=str(e)
            )
            return {
                "success": False,
                "error": str(e)
            }
