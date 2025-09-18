"""Simulation Execution Engine - Core Business Logic Integration.

This module provides the core simulation execution engine that integrates
the domain layer (DDD aggregates) with the actual simulation execution logic,
connecting the FastAPI endpoints to the domain services and orchestrating
the complete simulation workflow.

Key Responsibilities:
- Execute simulations using domain models and aggregates
- Integrate with content generation pipeline for document creation
- Coordinate with ecosystem services for comprehensive execution
- Provide real-time progress updates and event broadcasting
- Handle simulation lifecycle management and error recovery
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional, List, AsyncGenerator
from datetime import datetime, timedelta
from uuid import uuid4
import asyncio
import json

# Import from shared infrastructure
sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent / "services" / "shared"))

from simulation.infrastructure.logging import get_simulation_logger
from simulation.infrastructure.monitoring.simulation_monitoring import SimulationMonitoringService
from simulation.infrastructure.content.content_generation_pipeline import ContentGenerationPipeline
from simulation.infrastructure.clients.ecosystem_clients import EcosystemServiceRegistry
from simulation.infrastructure.workflows.workflow_orchestrator import SimulationWorkflowOrchestrator
from simulation.domain.entities.simulation import Simulation, SimulationId, SimulationConfiguration, SimulationProgress
from simulation.domain.entities.project import Project
from simulation.domain.entities.timeline import Timeline
from simulation.domain.entities.team import Team
from simulation.domain.value_objects import SimulationStatus, SimulationMetrics, DocumentType
from simulation.domain.events import SimulationStarted, SimulationCompleted, SimulationFailed, DocumentGenerated, WorkflowExecuted
from simulation.domain.repositories import SimulationRepository, ProjectRepository, TimelineRepository, TeamRepository
from simulation.domain.services.project_simulation_service import ProjectSimulationService


class SimulationExecutionEngine:
    """Core simulation execution engine that orchestrates domain logic and ecosystem integration."""

    def __init__(self,
                 content_pipeline: ContentGenerationPipeline,
                 ecosystem_clients: EcosystemServiceRegistry,
                 workflow_orchestrator: SimulationWorkflowOrchestrator,
                 logger,
                 monitoring_service: SimulationMonitoringService,
                 simulation_repository: Optional[SimulationRepository] = None,
                 project_repository: Optional[ProjectRepository] = None,
                 timeline_repository: Optional[TimelineRepository] = None,
                 team_repository: Optional[TeamRepository] = None):
        """Initialize the simulation execution engine."""
        self.content_pipeline = content_pipeline
        self.ecosystem_clients = ecosystem_clients
        self.workflow_orchestrator = workflow_orchestrator
        self.logger = logger
        self.monitoring_service = monitoring_service

        # Repository dependencies (will be injected)
        self.simulation_repository = simulation_repository
        self.project_repository = project_repository
        self.timeline_repository = timeline_repository
        self.team_repository = team_repository

        # Active simulations tracking
        self.active_simulations: Dict[str, Simulation] = {}
        self.execution_tasks: Dict[str, asyncio.Task] = {}

    async def execute_simulation(self, simulation_id: str) -> Dict[str, Any]:
        """Execute a simulation using the domain model and ecosystem integration."""
        try:
            self.logger.info(f"Starting simulation execution", simulation_id=simulation_id)

            # Load simulation from repository
            simulation = await self._load_simulation(simulation_id)
            if not simulation:
                raise ValueError(f"Simulation {simulation_id} not found")

            # Start execution in background task
            execution_task = asyncio.create_task(self._execute_simulation_async(simulation))
            self.execution_tasks[simulation_id] = execution_task

            # Wait for completion or return status
            try:
                result = await asyncio.wait_for(execution_task, timeout=300)  # 5 minute timeout
                return result
            except asyncio.TimeoutError:
                return {
                    "success": False,
                    "status": "running",
                    "message": "Simulation is running in background",
                    "simulation_id": simulation_id
                }

        except Exception as e:
            self.logger.error(f"Failed to execute simulation", error=str(e), simulation_id=simulation_id)
            return {
                "success": False,
                "error": str(e),
                "simulation_id": simulation_id
            }

    async def _load_simulation(self, simulation_id: str) -> Optional[Simulation]:
        """Load simulation from repository."""
        if self.simulation_repository:
            return self.simulation_repository.find_by_id(simulation_id)
        return None

    async def _execute_simulation_async(self, simulation: Simulation) -> Dict[str, Any]:
        """Execute simulation asynchronously using domain logic."""
        simulation_id = str(simulation.id.value)

        try:
            self.logger.info(f"Executing simulation phases", simulation_id=simulation_id)

            # Mark simulation as running
            simulation.start_simulation()
            await self._save_simulation(simulation)

            # Publish simulation started event
            await self._publish_simulation_event(simulation, "simulation_started", {
                "project_name": "Unknown",  # This would come from project entity
                "estimated_duration": simulation.configuration.get_max_execution_time().total_seconds(),
                "simulation_type": simulation.configuration.simulation_type.value
            })

            # Execute simulation phases
            await self._execute_simulation_phases(simulation)

        # Run final analysis
        await self._run_final_analysis(simulation)

        # Run document quality analysis
        await self._run_document_quality_analysis(simulation)

            # Complete simulation
            metrics = await self._calculate_simulation_metrics(simulation)
            simulation.complete_simulation(True, 0.0, metrics)
            await self._save_simulation(simulation)

            # Publish simulation completion event
            await self._publish_simulation_event(simulation, "simulation_completed", {
                "total_documents": metrics.total_documents,
                "total_workflows": metrics.total_workflows,
                "execution_time_seconds": 0.0,
                "success": True
            })

            self.logger.info(f"Simulation completed successfully", simulation_id=simulation_id)

            return {
                "success": True,
                "simulation_id": simulation_id,
                "status": "completed",
                "execution_time": 0.0,
                "documents_generated": len(simulation.progress.documents_generated) if hasattr(simulation.progress, 'documents_generated') else 0,
                "workflows_executed": len(simulation.progress.workflows_executed) if hasattr(simulation.progress, 'workflows_executed') else 0
            }

        except Exception as e:
            self.logger.error(f"Simulation execution failed", error=str(e), simulation_id=simulation_id)
            simulation.fail_simulation(str(e))
            await self._save_simulation(simulation)

            # Publish simulation failure event
            await self._publish_simulation_event(simulation, "simulation_failed", {
                "error_message": str(e),
                "failure_time": datetime.now().isoformat()
            })

            return {
                "success": False,
                "simulation_id": simulation_id,
                "status": "failed",
                "error": str(e)
            }

    async def _execute_simulation_phases(self, simulation: Simulation) -> None:
        """Execute all phases of the simulation."""
        # Load related entities
        project = await self._load_project(simulation.project_id)
        timeline = await self._load_timeline(simulation.project_id)
        team = await self._load_team(simulation.project_id)

        if not project or not timeline:
            raise ValueError("Project or timeline not found")

        # Execute each timeline phase
        for phase in timeline.phases:
            await self._execute_phase(simulation, phase, project, team)

    async def _execute_phase(self, simulation: Simulation, phase: Any, project: Project, team: Team) -> None:
        """Execute a single simulation phase."""
        phase_name = getattr(phase, 'name', str(phase))
        simulation_id = str(simulation.id.value)

        self.logger.info(f"Executing phase: {phase_name}", simulation_id=simulation_id)

        # Generate documents for this phase using timeline-based generation
        from ..content.timeline_based_generation import TimelineAwareContentGenerator

        timeline_generator = TimelineAwareContentGenerator()

        # Create timeline context for this phase
        timeline_context = {
            "phase_name": phase_name,
            "current_phase": phase,
            "project_timeline": [],  # This would come from the timeline entity
            "project_config": {
                "name": project.name,
                "type": project.type.value,
                "complexity": project.complexity.value,
                "technologies": project.technologies
            },
            "team_config": {
                "size": len(team.members) if team else 0,
                "members": [
                    {
                        "id": str(member.id),
                        "name": member.name,
                        "role": member.role.value if hasattr(member.role, 'value') else str(member.role),
                        "expertise_level": member.expertise_level.value if hasattr(member.expertise_level, 'value') else str(member.expertise_level),
                        "communication_style": member.communication_style.value if hasattr(member.communication_style, 'value') else str(member.communication_style),
                        "productivity_multiplier": member.productivity_multiplier
                    } for member in team.members
                ] if team else []
            } if team else {},
            "simulation_config": simulation.configuration.__dict__
        }

        # Generate timeline-aware content
        timeline_content = await timeline_generator.generate_timeline_aware_content(
            document_type="comprehensive",
            project_config=timeline_context["project_config"],
            team_members=timeline_context.get("team_config", {}).get("members", []),
            timeline={"phases": [timeline_context]},
            current_phase=phase_name
        )

        # Convert timeline content to document format
        documents = [{
            "type": "timeline_aware_document",
            "title": f"Timeline-Aware Content - {phase_name}",
            "content": timeline_content.get("content", ""),
            "metadata": {
                "document_type": "timeline",
                "phase": phase_name,
                "timeline_awareness_score": timeline_content.get("temporal_metadata", {}).get("timeline_awareness_score", 0),
                "temporal_relationships": timeline_content.get("temporal_metadata", {}).get("temporal_relationships", 0)
            }
        }]

        # Also generate using content pipeline for additional documents
        phase_config = {
            "phase_name": phase_name,
            "project_config": {
                "name": project.name,
                "type": project.type.value,
                "complexity": project.complexity.value,
                "technologies": project.technologies
            },
            "team_config": team.__dict__ if team else {},
            "simulation_config": simulation.configuration.__dict__
        }

        additional_documents = await self.content_pipeline.execute_document_generation(phase_config)
        documents.extend(additional_documents)

        # Store documents in ecosystem and broadcast events
        for doc in documents:
            doc_id = await self._store_document(doc)

            # Determine document type
            doc_type = DocumentType.CONFLUENCE_DOC
            if "jira" in doc.get("type", "").lower():
                doc_type = DocumentType.JIRA_TICKET
            elif "github" in doc.get("type", "").lower():
                doc_type = DocumentType.GITHUB_PR

            simulation.record_document_generation(
                doc_type,
                doc.get("title", "Untitled"),
                len(doc.get("content", ""))
            )

            # Publish document generation event
            await self._publish_simulation_event(simulation, "document_generated", {
                "document_title": doc.get("title", "Untitled"),
                "document_type": doc_type.value,
                "word_count": len(doc.get("content", "")),
                "phase": phase_name
            })

        # Execute workflows for this phase
        workflow_config = {
            "phase": phase_name,
            "documents": documents,
            "project": project.to_dict(),
            "team": team.to_dict() if team else {}
        }

        workflow_result = await self.workflow_orchestrator.execute_phase_workflow(workflow_config)

        # Record workflow execution
        simulation.record_workflow_execution(
            f"{phase_name}_workflow",
            workflow_result.get("execution_time", 0.0),
            workflow_result.get("success", False)
        )

        # Publish workflow execution event
        await self._publish_simulation_event(simulation, "workflow_executed", {
            "workflow_name": f"{phase_name}_workflow",
            "execution_time": workflow_result.get("execution_time", 0.0),
            "success": workflow_result.get("success", False),
            "phase": phase_name
        })

        # Run phase-specific analysis
        if documents and len(documents) > 0:
            await self._run_phase_analysis(simulation, phase_name, documents)

        # Update progress
        simulation.update_progress(phase_name, len(documents), 1, True)

        # Publish phase completion event
        await self._publish_simulation_event(simulation, "phase_completed", {
            "phase_name": phase_name,
            "documents_generated": len(documents),
            "workflows_executed": 1,
            "phase_duration_seconds": 0  # This would be calculated
        })

        # Publish progress event
        await self._publish_progress_event(simulation)

    async def _run_phase_analysis(self, simulation: Simulation, phase_name: str, documents: List[Dict[str, Any]]) -> None:
        """Run analysis on documents generated in a specific phase."""
        simulation_id = str(simulation.id.value)

        try:
            self.logger.info(f"Running phase analysis for {phase_name}", simulation_id=simulation_id)

            # Analyze phase documents for quality and consistency
            if self.workflow_orchestrator:
                phase_analysis = await self.workflow_orchestrator.run_analysis_workflow({
                    "simulation_id": simulation_id,
                    "documents": documents,
                    "analysis_types": ["quality", "consistency"],
                    "phase_context": phase_name
                })

                # Store phase analysis results
                phase_analysis_doc = {
                    "type": "phase_analysis_report",
                    "title": f"Phase Analysis - {phase_name} - {simulation_id}",
                    "content": json.dumps(phase_analysis, indent=2),
                    "metadata": {
                        "document_type": "analysis",
                        "simulation_id": simulation_id,
                        "phase": phase_name,
                        "analysis_type": "phase_assessment",
                        "documents_analyzed": len(documents),
                        "analysis_timestamp": datetime.now().isoformat()
                    }
                }

                await self._store_document(phase_analysis_doc)

                # Record phase analysis workflow
                simulation.record_workflow_execution(
                    f"{phase_name}_analysis",
                    phase_analysis.get("execution_time", 0.0),
                    phase_analysis.get("success", True)
                )

                self.logger.info(f"Phase analysis completed for {phase_name}", simulation_id=simulation_id)

        except Exception as e:
            self.logger.error(f"Phase analysis failed for {phase_name}", error=str(e), simulation_id=simulation_id)

    async def _run_final_analysis(self, simulation: Simulation) -> Dict[str, Any]:
        """Run final analysis on the completed simulation."""
        simulation_id = str(simulation.id.value)

        self.logger.info(f"Running final analysis", simulation_id=simulation_id)

        # Get all documents from ecosystem
        documents = await self._get_all_simulation_documents(simulation_id)

        # Run analysis through ecosystem
        analysis_result = await self.workflow_orchestrator.run_analysis_workflow({
            "simulation_id": simulation_id,
            "documents": documents,
            "analysis_types": ["consistency", "quality", "insights"]
        })

            return analysis_result

    async def _run_document_quality_analysis(self, simulation: Simulation) -> None:
        """Run comprehensive document quality analysis on generated content."""
        simulation_id = str(simulation.id.value)

        try:
            self.logger.info(f"Running document quality analysis", simulation_id=simulation_id)

            # Get all simulation documents
            documents = await self._get_all_simulation_documents(simulation_id)

            if not documents:
                self.logger.warning(f"No documents found for quality analysis", simulation_id=simulation_id)
                return

            # Analyze document quality using analysis service
            if self.workflow_orchestrator:
                quality_analysis = await self.workflow_orchestrator.run_analysis_workflow({
                    "simulation_id": simulation_id,
                    "documents": documents,
                    "analysis_types": ["quality", "consistency", "insights", "patterns"]
                })

                # Store analysis results
                analysis_doc = {
                    "type": "analysis_report",
                    "title": f"Document Quality Analysis - {simulation_id}",
                    "content": json.dumps(quality_analysis, indent=2),
                    "metadata": {
                        "document_type": "analysis",
                        "simulation_id": simulation_id,
                        "analysis_type": "quality_assessment",
                        "documents_analyzed": len(documents),
                        "analysis_timestamp": datetime.now().isoformat()
                    }
                }

                await self._store_document(analysis_doc)

                # Record analysis workflow execution
                simulation.record_workflow_execution(
                    "document_quality_analysis",
                    quality_analysis.get("execution_time", 0.0),
                    quality_analysis.get("success", True)
                )

                # Publish analysis completion event
                await self._publish_simulation_event(simulation, "analysis_completed", {
                    "analysis_type": "document_quality",
                    "documents_analyzed": len(documents),
                    "quality_score": quality_analysis.get("analysis_result", {}).get("quality_score", 0),
                    "issues_found": len(quality_analysis.get("analysis_result", {}).get("issues", []))
                })

                self.logger.info(f"Document quality analysis completed", simulation_id=simulation_id)

        except Exception as e:
            self.logger.error(f"Document quality analysis failed", error=str(e), simulation_id=simulation_id)

    async def _calculate_simulation_metrics(self, simulation: Simulation) -> SimulationMetrics:
        """Calculate comprehensive simulation metrics."""
        # This would calculate actual metrics based on simulation results
        return SimulationMetrics(
            total_documents=simulation.progress.documents_generated if hasattr(simulation.progress, 'documents_generated') else 0,
            total_workflows=simulation.progress.workflows_executed if hasattr(simulation.progress, 'workflows_executed') else 0,
            execution_time_seconds=0.0,
            success_rate=1.0 if simulation.status == SimulationStatus.COMPLETED else 0.0,
            average_response_time=0.0,
            ecosystem_services_used=5,  # Mock value
            data_processed_mb=0.0
        )

    async def _load_project(self, project_id: str) -> Optional[Project]:
        """Load project from repository."""
        if self.project_repository:
            return await self.project_repository.find_by_id(project_id)
        return None

    async def _load_timeline(self, project_id: str) -> Optional[Timeline]:
        """Load timeline from repository."""
        if self.timeline_repository:
            return await self.timeline_repository.find_by_project_id(project_id)
        return None

    async def _load_team(self, project_id: str) -> Optional[Team]:
        """Load team from repository."""
        if self.team_repository:
            return await self.team_repository.find_by_project_id(project_id)
        return None

    async def _save_simulation(self, simulation: Simulation) -> None:
        """Save simulation to repository."""
        if self.simulation_repository:
            await self.simulation_repository.save(simulation)

    async def _store_document(self, document: Dict[str, Any]) -> Optional[str]:
        """Store document in ecosystem."""
        try:
            doc_store = self.ecosystem_clients.get_client("doc_store")
            if doc_store:
                return await doc_store.store_document(
                    document.get("title", "Untitled"),
                    document.get("content", ""),
                    document.get("metadata", {})
                )
        except Exception as e:
            self.logger.error(f"Failed to store document", error=str(e))
        return None

    async def _get_all_simulation_documents(self, simulation_id: str) -> List[Dict[str, Any]]:
        """Get all documents for a simulation."""
        try:
            doc_store = self.ecosystem_clients.get_client("doc_store")
            if doc_store:
                # This would need to be implemented based on how documents are tagged
                return await doc_store.search_documents(f"simulation:{simulation_id}")
        except Exception as e:
            self.logger.error(f"Failed to get simulation documents", error=str(e))
        return []

    async def _publish_progress_event(self, simulation: Simulation) -> None:
        """Publish simulation progress event."""
        try:
            # Publish to WebSocket if available
            from simulation.presentation.websockets.simulation_websocket import notify_simulation_progress

            progress_data = {
                "simulation_id": str(simulation.id.value),
                "progress_percentage": simulation.get_progress_percentage(),
                "current_phase": simulation.progress.current_phase if hasattr(simulation.progress, 'current_phase') else None,
                "status": simulation.status.value,
                "documents_generated": getattr(simulation.progress, 'documents_generated', 0),
                "workflows_executed": getattr(simulation.progress, 'workflows_executed', 0),
                "timestamp": datetime.now().isoformat()
            }

            await notify_simulation_progress(str(simulation.id.value), progress_data)

        except Exception as e:
            self.logger.error(f"Failed to publish progress event", error=str(e))

    async def _publish_simulation_event(self, simulation: Simulation, event_type: str, event_data: Dict[str, Any] = None) -> None:
        """Publish simulation-specific event."""
        try:
            from simulation.presentation.websockets.simulation_websocket import notify_simulation_event_dict

            event_payload = {
                "simulation_id": str(simulation.id.value),
                "event_type": event_type,
                "timestamp": datetime.now().isoformat(),
                "data": event_data or {},
                "simulation_status": simulation.status.value,
                "progress_percentage": simulation.get_progress_percentage()
            }

            await notify_simulation_event_dict(str(simulation.id.value), event_payload)

        except Exception as e:
            self.logger.error(f"Failed to publish simulation event", error=str(e), event_type=event_type)

    async def get_simulation_status(self, simulation_id: str) -> Optional[Dict[str, Any]]:
        """Get current simulation status."""
        simulation = self.active_simulations.get(simulation_id)
        if simulation:
            return simulation.get_simulation_summary()

        # Try to load from repository
        simulation = await self._load_simulation(simulation_id)
        if simulation:
            return simulation.get_simulation_summary()

        return None

    async def cancel_simulation(self, simulation_id: str) -> bool:
        """Cancel a running simulation."""
        if simulation_id in self.execution_tasks:
            self.execution_tasks[simulation_id].cancel()
            del self.execution_tasks[simulation_id]

        simulation = await self._load_simulation(simulation_id)
        if simulation and simulation.is_running():
            simulation.cancel_simulation()
            await self._save_simulation(simulation)
            return True

        return False

    async def pause_simulation(self, simulation_id: str) -> bool:
        """Pause a running simulation."""
        simulation = await self._load_simulation(simulation_id)
        if simulation and simulation.is_running():
            simulation.pause_simulation()
            await self._save_simulation(simulation)
            return True

        return False

    async def resume_simulation(self, simulation_id: str) -> bool:
        """Resume a paused simulation."""
        simulation = await self._load_simulation(simulation_id)
        if simulation and simulation.status.value == "paused":
            simulation.resume_simulation()
            await self._save_simulation(simulation)
            return True

        return False
