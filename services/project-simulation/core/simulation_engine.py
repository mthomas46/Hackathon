"""Simulation Engine - Core Coordinator for Project Simulations.

This module provides the main SimulationEngine class that coordinates all aspects
of project simulation, including document generation, workflow execution,
analysis integration, and progress tracking.
"""

import asyncio
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, AsyncGenerator
from concurrent.futures import ThreadPoolExecutor

from ..models.configuration import (
    ProjectConfiguration, SimulationParameters, SimulationProgress,
    SimulationEvent, EventType, SimulationResult, DocumentMetadata,
    TicketMetadata, PRMetadata
)

from .timeline_engine import TimelineEngine
from .event_system import EventSystem
from .progress_tracker import ProgressTracker

from ..integrations.doc_store_client import DocStoreClient
from ..integrations.prompt_store_client import PromptStoreClient
from ..integrations.orchestrator_client import OrchestratorClient
from ..integrations.analysis_client import AnalysisClient
from ..integrations.llm_client import LLMClient

from ..generators.document_generator import DocumentGenerator
from ..generators.jira_generator import JIRAGenerator
from ..generators.github_generator import GitHubGenerator
from ..generators.user_generator import UserGenerator


class SimulationEngine:
    """Main simulation coordinator that orchestrates all simulation activities."""

    def __init__(self, event_system: EventSystem):
        """Initialize the simulation engine."""
        self.event_system = event_system
        self.timeline_engine = TimelineEngine()
        self.progress_tracker = ProgressTracker(event_system)

        # Service clients (initialized during startup)
        self.doc_store_client: Optional[DocStoreClient] = None
        self.prompt_store_client: Optional[PromptStoreClient] = None
        self.orchestrator_client: Optional[OrchestratorClient] = None
        self.analysis_client: Optional[AnalysisClient] = None
        self.llm_client: Optional[LLMClient] = None

        # Content generators
        self.document_generator = DocumentGenerator()
        self.jira_generator = JIRAGenerator()
        self.github_generator = GitHubGenerator()
        self.user_generator = UserGenerator()

        # Thread pool for CPU-intensive operations
        self.executor = ThreadPoolExecutor(max_workers=4)

        # Active simulations tracking
        self.active_simulations: Dict[str, Dict[str, Any]] = {}

    async def initialize(self):
        """Initialize the simulation engine and all components."""
        print("🔧 Initializing Simulation Engine...")

        # Initialize generators
        await self.document_generator.initialize(self.llm_client)
        await self.jira_generator.initialize(self.llm_client)
        await self.github_generator.initialize(self.llm_client)
        await self.user_generator.initialize()

        # Initialize integrations
        if self.doc_store_client:
            await self.doc_store_client.initialize()
        if self.prompt_store_client:
            await self.prompt_store_client.initialize()
        if self.orchestrator_client:
            await self.orchestrator_client.initialize()
        if self.analysis_client:
            await self.analysis_client.initialize()

        print("✅ Simulation Engine initialized successfully!")

    async def shutdown(self):
        """Shutdown the simulation engine and cleanup resources."""
        print("🛑 Shutting down Simulation Engine...")

        # Cancel all active simulations
        for sim_id in list(self.active_simulations.keys()):
            await self.cancel_simulation(sim_id)

        # Shutdown components
        if self.doc_store_client:
            await self.doc_store_client.close()
        if self.prompt_store_client:
            await self.prompt_store_client.close()
        if self.orchestrator_client:
            await self.orchestrator_client.close()
        if self.analysis_client:
            await self.analysis_client.close()

        # Shutdown thread pool
        self.executor.shutdown(wait=True)

        print("✅ Simulation Engine shut down successfully!")

    async def run_simulation(
        self,
        project_config: ProjectConfiguration,
        simulation_params: SimulationParameters,
        simulation_id: str
    ) -> SimulationResult:
        """Run a complete project simulation."""
        start_time = time.time()

        # Initialize simulation tracking
        self.active_simulations[simulation_id] = {
            "config": project_config,
            "params": simulation_params,
            "start_time": datetime.now(),
            "status": "running",
            "progress": SimulationProgress(
                simulation_id=simulation_id,
                status="running",
                start_time=datetime.now()
            )
        }

        try:
            # Publish simulation started event
            await self.event_system.publish_event(SimulationEvent(
                type=EventType.SIMULATION_STARTED,
                details={"project_name": project_config.name}
            ))

            # Generate team profiles if needed
            if not project_config.team_members:
                project_config.team_members = await self.user_generator.generate_team_profiles(
                    project_config.team_size,
                    project_config.type
                )

            # Initialize progress tracking
            await self.progress_tracker.initialize_simulation(simulation_id, project_config)

            # Run simulation phases
            documents_created = []
            tickets_created = []
            prs_created = []
            workflows_executed = []

            # Execute each timeline phase
            for phase in project_config.timeline_phases:
                await self._execute_phase(
                    simulation_id,
                    phase,
                    project_config,
                    simulation_params,
                    documents_created,
                    tickets_created,
                    prs_created,
                    workflows_executed
                )

            # Run final analysis if enabled
            analysis_results = {}
            if simulation_params.enable_analysis and self.analysis_client:
                analysis_results = await self._run_final_analysis(
                    simulation_id, project_config, documents_created, tickets_created, prs_created
                )

            # Calculate benefits and inconsistencies
            benefits_demonstrated = await self._calculate_benefits(project_config, documents_created, workflows_executed)
            inconsistencies_found = await self._identify_inconsistencies(documents_created, tickets_created)

            # Create simulation result
            result = SimulationResult(
                simulation_id=simulation_id,
                project_config=project_config,
                execution_time=time.time() - start_time,
                total_events=len(await self.event_system.get_simulation_events(simulation_id)),
                documents_created=documents_created,
                tickets_created=tickets_created,
                prs_created=prs_created,
                workflows_executed=workflows_executed,
                analysis_results=analysis_results,
                benefits_demonstrated=benefits_demonstrated,
                inconsistencies_found=inconsistencies_found
            )

            # Publish completion event
            await self.event_system.publish_event(SimulationEvent(
                type=EventType.SIMULATION_COMPLETED,
                details={
                    "execution_time": result.execution_time,
                    "documents_created": len(documents_created),
                    "tickets_created": len(tickets_created),
                    "prs_created": len(prs_created)
                }
            ))

            return result

        except Exception as e:
            # Publish error event
            await self.event_system.publish_event(SimulationEvent(
                type=EventType.ERROR_OCCURRED,
                details={"error": str(e)}
            ))
            raise

        finally:
            # Cleanup
            if simulation_id in self.active_simulations:
                self.active_simulations[simulation_id]["status"] = "completed"
                self.active_simulations[simulation_id]["end_time"] = datetime.now()

    async def _execute_phase(
        self,
        simulation_id: str,
        phase: Any,
        project_config: ProjectConfiguration,
        simulation_params: SimulationParameters,
        documents_created: List[DocumentMetadata],
        tickets_created: List[TicketMetadata],
        prs_created: List[PRMetadata],
        workflows_executed: List[Dict[str, Any]]
    ):
        """Execute a single timeline phase."""
        # Publish phase started event
        await self.event_system.publish_event(SimulationEvent(
            type=EventType.PHASE_STARTED,
            phase=phase.name,
            details={"duration_days": phase.duration_days}
        ))

        # Generate documents for this phase
        phase_documents = await self.document_generator.generate_phase_documents(
            phase, project_config, simulation_params
        )

        # Store documents in doc store
        for doc in phase_documents:
            if self.doc_store_client:
                doc_id = await self.doc_store_client.store_document(doc)
                doc.id = doc_id

        documents_created.extend(phase_documents)

        # Generate JIRA tickets for this phase
        if phase.name.lower() in ["development", "testing"]:
            phase_tickets = await self.jira_generator.generate_phase_tickets(
                phase, project_config, simulation_params
            )

            # Store tickets (in a real implementation, this might go to a ticket system)
            tickets_created.extend(phase_tickets)

        # Generate GitHub PRs for development phases
        if phase.name.lower() == "development":
            phase_prs = await self.github_generator.generate_phase_prs(
                phase, project_config, simulation_params
            )

            # Store PRs (in a real implementation, this might integrate with GitHub)
            prs_created.extend(phase_prs)

        # Execute analysis workflows if enabled
        if simulation_params.enable_analysis and self.orchestrator_client:
            phase_workflows = await self.orchestrator_client.execute_phase_workflows(
                phase, project_config, documents_created[-len(phase_documents):]
            )
            workflows_executed.extend(phase_workflows)

        # Update progress
        await self.progress_tracker.update_phase_progress(
            simulation_id, phase.name, len(phase_documents), len(phase_tickets), len(phase_prs)
        )

        # Apply speed multiplier for simulation timing
        if simulation_params.speed_multiplier != 1.0:
            delay = phase.duration_days / simulation_params.speed_multiplier
            await asyncio.sleep(min(delay, 1.0))  # Cap at 1 second for responsiveness

        # Publish phase completed event
        await self.event_system.publish_event(SimulationEvent(
            type=EventType.PHASE_COMPLETED,
            phase=phase.name,
            details={
                "documents_created": len(phase_documents),
                "tickets_created": len(phase_tickets) if 'phase_tickets' in locals() else 0,
                "prs_created": len(phase_prs) if 'phase_prs' in locals() else 0
            }
        ))

    async def _run_final_analysis(
        self,
        simulation_id: str,
        project_config: ProjectConfiguration,
        documents_created: List[DocumentMetadata],
        tickets_created: List[TicketMetadata],
        prs_created: List[PRMetadata]
    ) -> Dict[str, Any]:
        """Run final comprehensive analysis on the simulation results."""
        analysis_results = {}

        if not self.analysis_client:
            return analysis_results

        try:
            # Run document analysis
            if documents_created:
                doc_analysis = await self.analysis_client.analyze_documents(documents_created)
                analysis_results["document_analysis"] = doc_analysis

            # Run PR confidence analysis
            if prs_created:
                pr_analysis = await self.analysis_client.analyze_prs(prs_created)
                analysis_results["pr_analysis"] = pr_analysis

            # Run cross-repository analysis
            if documents_created and tickets_created:
                cross_analysis = await self.analysis_client.analyze_cross_repository(
                    documents_created, tickets_created
                )
                analysis_results["cross_repository_analysis"] = cross_analysis

            # Publish analysis completion event
            await self.event_system.publish_event(SimulationEvent(
                type=EventType.ANALYSIS_COMPLETED,
                details={
                    "document_analysis": bool(documents_created),
                    "pr_analysis": bool(prs_created),
                    "cross_repository_analysis": bool(documents_created and tickets_created)
                }
            ))

        except Exception as e:
            print(f"Warning: Final analysis failed: {e}")
            analysis_results["error"] = str(e)

        return analysis_results

    async def _calculate_benefits(
        self,
        project_config: ProjectConfiguration,
        documents_created: List[DocumentMetadata],
        workflows_executed: List[Dict[str, Any]]
    ) -> List[str]:
        """Calculate the benefits demonstrated by the ecosystem."""
        benefits = []

        # Document management benefits
        if len(documents_created) > 0:
            benefits.append(f"Automated creation of {len(documents_created)} professional documents")
            benefits.append("Consistent document formatting and structure")
            benefits.append("AI-powered content generation for realistic documentation")

        # Workflow orchestration benefits
        if len(workflows_executed) > 0:
            benefits.append(f"Executed {len(workflows_executed)} automated analysis workflows")
            benefits.append("Cross-service integration and data flow")
            benefits.append("Intelligent workflow orchestration and scheduling")

        # Analysis capabilities
        if any(doc.complexity_score > 0 for doc in documents_created):
            benefits.append("Automated document quality and complexity assessment")
            benefits.append("Content analysis and improvement suggestions")

        # Ecosystem integration benefits
        benefits.append("Seamless integration across 9+ microservices")
        benefits.append("Real-time event streaming and progress monitoring")
        benefits.append("Enterprise-grade reliability and error handling")

        return benefits

    async def _identify_inconsistencies(
        self,
        documents_created: List[DocumentMetadata],
        tickets_created: List[TicketMetadata]
    ) -> List[str]:
        """Identify inconsistencies and issues in the generated content."""
        inconsistencies = []

        # Check for missing documentation
        doc_types = {doc.type.value for doc in documents_created}
        if "api_specification" not in doc_types:
            inconsistencies.append("Missing API specification documentation")
        if "architecture_diagram" not in doc_types:
            inconsistencies.append("Missing architecture diagram documentation")

        # Check for ticket-document alignment
        if tickets_created:
            ticket_titles = {ticket.title.lower() for ticket in tickets_created}
            doc_titles = {doc.title.lower() for doc in documents_created}

            # Look for tickets without corresponding documentation
            for ticket_title in ticket_titles:
                if not any(ticket_title in doc_title or doc_title in ticket_title
                          for doc_title in doc_titles):
                    inconsistencies.append(f"Ticket '{ticket_title}' lacks corresponding documentation")

        # Check for naming inconsistencies
        if len(documents_created) > 1:
            titles = [doc.title for doc in documents_created]
            if len(set(titles)) != len(titles):
                inconsistencies.append("Duplicate document titles found")

        return inconsistencies

    async def cancel_simulation(self, simulation_id: str):
        """Cancel a running simulation."""
        if simulation_id in self.active_simulations:
            self.active_simulations[simulation_id]["status"] = "cancelled"

            # Publish cancellation event
            await self.event_system.publish_event(SimulationEvent(
                type=EventType.SIMULATION_COMPLETED,
                details={"cancelled": True}
            ))

    async def get_simulation_status(self, simulation_id: str) -> Optional[SimulationProgress]:
        """Get the current status of a simulation."""
        if simulation_id in self.active_simulations:
            return self.active_simulations[simulation_id].get("progress")
        return None

    async def get_simulation_events(self, simulation_id: str) -> List[SimulationEvent]:
        """Get all events for a simulation."""
        return await self.event_system.get_simulation_events(simulation_id)

    async def get_active_simulations(self) -> List[Dict[str, Any]]:
        """Get list of all active simulations."""
        return [
            {
                "simulation_id": sim_id,
                "status": info["status"],
                "start_time": info["start_time"],
                "project_name": info["config"].name,
                "progress": info.get("progress")
            }
            for sim_id, info in self.active_simulations.items()
        ]
