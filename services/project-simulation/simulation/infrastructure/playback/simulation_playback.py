"""Simulation playback infrastructure.

This module provides functionality to replay simulations using stored data,
retrieving documents and prompts that were used during the original simulation.
"""

import asyncio
import json
from typing import Dict, Any, List, Optional, AsyncGenerator
from datetime import datetime
from dataclasses import dataclass

from ...application.services.simulation_application_service import SimulationApplicationService
from ...domain.entities.simulation import Simulation, SimulationId
from ...infrastructure.logging import SimulationLogger


@dataclass
class PlaybackEvent:
    """Represents an event in the simulation playback."""
    timestamp: datetime
    event_type: str
    simulation_id: str
    data: Dict[str, Any]
    sequence_number: int


@dataclass
class PlaybackSession:
    """Represents a simulation playback session."""
    session_id: str
    simulation_id: str
    start_time: datetime
    status: str
    current_position: int = 0
    total_events: int = 0
    playback_speed: float = 1.0


class SimulationPlaybackEngine:
    """Engine for replaying simulations using stored data."""

    def __init__(self, application_service: SimulationApplicationService, logger: SimulationLogger):
        self.application_service = application_service
        self.logger = logger
        self.active_sessions: Dict[str, PlaybackSession] = {}

    async def start_playback(self, simulation_id: str, run_id: str,
                           playback_speed: float = 1.0) -> str:
        """Start a new playback session for a simulation run."""
        session_id = f"playback_{simulation_id}_{run_id}_{int(datetime.now().timestamp())}"

        # Get run data
        run_data = await self.application_service.get_simulation_run_data(simulation_id, run_id)
        if not run_data:
            raise ValueError(f"Run data not found for simulation {simulation_id}, run {run_id}")

        # Create playback session
        session = PlaybackSession(
            session_id=session_id,
            simulation_id=simulation_id,
            start_time=datetime.now(),
            status="initializing",
            playback_speed=playback_speed
        )

        self.active_sessions[session_id] = session
        self.logger.info("Started simulation playback session", session_id=session_id, simulation_id=simulation_id)

        return session_id

    async def get_playback_events(self, simulation_id: str, run_id: str) -> List[PlaybackEvent]:
        """Get all events for a simulation run playback."""
        # Get run data
        run_data = await self.application_service.get_simulation_run_data(simulation_id, run_id)
        if not run_data:
            return []

        events = []

        # Convert run data to playback events
        sequence = 0

        # Start event
        if "start_time" in run_data:
            events.append(PlaybackEvent(
                timestamp=datetime.fromisoformat(run_data["start_time"]),
                event_type="simulation_started",
                simulation_id=simulation_id,
                data={"run_id": run_id},
                sequence_number=sequence
            ))
            sequence += 1

        # Document generation events
        documents = await self.application_service.get_simulation_documents(simulation_id)
        for doc in documents:
            events.append(PlaybackEvent(
                timestamp=datetime.fromisoformat(doc["created_at"]),
                event_type="document_generated",
                simulation_id=simulation_id,
                data={
                    "document_id": doc["document_id"],
                    "document_type": doc["document_type"],
                    "doc_store_reference": doc["doc_store_reference"]
                },
                sequence_number=sequence
            ))
            sequence += 1

        # Prompt usage events
        prompts = await self.application_service.get_simulation_prompts(simulation_id)
        for prompt in prompts:
            events.append(PlaybackEvent(
                timestamp=datetime.fromisoformat(prompt["created_at"]),
                event_type="prompt_used",
                simulation_id=simulation_id,
                data={
                    "prompt_id": prompt["prompt_id"],
                    "prompt_type": prompt["prompt_type"],
                    "prompt_store_reference": prompt["prompt_store_reference"]
                },
                sequence_number=sequence
            ))
            sequence += 1

        # Completion event
        if "end_time" in run_data:
            events.append(PlaybackEvent(
                timestamp=datetime.fromisoformat(run_data.get("end_time", run_data["start_time"])),
                event_type="simulation_completed",
                simulation_id=simulation_id,
                data={"run_id": run_id, "final_status": run_data.get("status", "completed")},
                sequence_number=sequence
            ))

        # Sort events by timestamp
        events.sort(key=lambda e: e.timestamp)

        return events

    async def play_events(self, session_id: str) -> AsyncGenerator[PlaybackEvent, None]:
        """Play back events for a session."""
        if session_id not in self.active_sessions:
            raise ValueError(f"Playback session {session_id} not found")

        session = self.active_sessions[session_id]

        # Get simulation ID and run ID from session
        parts = session_id.split("_")
        if len(parts) < 3:
            raise ValueError(f"Invalid session ID format: {session_id}")

        simulation_id = parts[1]
        run_id = parts[2]

        # Get all events
        events = await self.get_playback_events(simulation_id, run_id)
        session.total_events = len(events)
        session.status = "playing"

        # Play events with timing
        last_timestamp = None

        for event in events:
            if last_timestamp:
                # Calculate delay based on playback speed
                time_diff = (event.timestamp - last_timestamp).total_seconds()
                delay = time_diff / session.playback_speed

                if delay > 0:
                    await asyncio.sleep(delay)

            session.current_position += 1
            yield event
            last_timestamp = event.timestamp

        session.status = "completed"

    async def pause_playback(self, session_id: str) -> None:
        """Pause a playback session."""
        if session_id in self.active_sessions:
            self.active_sessions[session_id].status = "paused"

    async def resume_playback(self, session_id: str) -> None:
        """Resume a playback session."""
        if session_id in self.active_sessions:
            self.active_sessions[session_id].status = "playing"

    async def stop_playback(self, session_id: str) -> None:
        """Stop a playback session."""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session.status = "stopped"
            del self.active_sessions[session_id]

    async def get_session_status(self, session_id: str) -> Optional[PlaybackSession]:
        """Get the status of a playback session."""
        return self.active_sessions.get(session_id)

    async def get_available_runs(self, simulation_id: str) -> List[Dict[str, Any]]:
        """Get all available runs for a simulation."""
        # This would need to be implemented to query the database for all runs
        # For now, return a placeholder
        return [
            {
                "run_id": "run_001",
                "start_time": datetime.now().isoformat(),
                "status": "completed",
                "duration_seconds": 120.5
            }
        ]


class SimulationReconstructor:
    """Reconstructs simulation state from stored data."""

    def __init__(self, application_service: SimulationApplicationService, logger: SimulationLogger):
        self.application_service = application_service
        self.logger = logger

    async def reconstruct_simulation(self, simulation_id: str, run_id: str) -> Dict[str, Any]:
        """Reconstruct the complete simulation state from stored data."""
        # Get simulation
        simulation = await self.application_service._simulation_repository.find_by_id(simulation_id)
        if not simulation:
            raise ValueError(f"Simulation {simulation_id} not found")

        # Get run data
        run_data = await self.application_service.get_simulation_run_data(simulation_id, run_id)

        # Get documents
        documents = await self.application_service.get_simulation_documents(simulation_id)

        # Get prompts
        prompts = await self.application_service.get_simulation_prompts(simulation_id)

        # Reconstruct state
        reconstructed_state = {
            "simulation": {
                "id": simulation.id.value,
                "project_id": simulation.project_id,
                "status": simulation.status.value,
                "configuration": {
                    "simulation_type": simulation.configuration.simulation_type.value,
                    "include_document_generation": simulation.configuration.include_document_generation,
                    "include_workflow_execution": simulation.configuration.include_workflow_execution,
                    "include_team_dynamics": simulation.configuration.include_team_dynamics,
                    "real_time_progress": simulation.configuration.real_time_progress,
                    "max_execution_time_minutes": simulation.configuration.max_execution_time_minutes,
                    "generate_realistic_delays": simulation.configuration.generate_realistic_delays,
                    "capture_metrics": simulation.configuration.capture_metrics,
                    "enable_ecosystem_integration": simulation.configuration.enable_ecosystem_integration
                }
            },
            "run_data": run_data or {},
            "documents": documents,
            "prompts": prompts,
            "reconstructed_at": datetime.now().isoformat(),
            "total_documents": len(documents),
            "total_prompts": len(prompts)
        }

        return reconstructed_state

    async def get_document_content(self, simulation_id: str, document_id: str) -> Optional[Dict[str, Any]]:
        """Get document content from doc-store via simulation linkage."""
        documents = await self.application_service.get_simulation_documents(simulation_id)
        doc_info = next((doc for doc in documents if doc["document_id"] == document_id), None)

        if not doc_info:
            return None

        # In a real implementation, this would call the doc-store API
        # For now, return mock content
        return {
            "document_id": document_id,
            "simulation_id": simulation_id,
            "content": f"Mock content for document {document_id}",
            "metadata": {
                "type": doc_info["document_type"],
                "created_at": doc_info["created_at"],
                "doc_store_reference": doc_info["doc_store_reference"]
            }
        }

    async def get_prompt_content(self, simulation_id: str, prompt_id: str) -> Optional[Dict[str, Any]]:
        """Get prompt content from prompt-store via simulation linkage."""
        prompts = await self.application_service.get_simulation_prompts(simulation_id)
        prompt_info = next((prompt for prompt in prompts if prompt["prompt_id"] == prompt_id), None)

        if not prompt_info:
            return None

        # In a real implementation, this would call the prompt-store API
        # For now, return mock content
        return {
            "prompt_id": prompt_id,
            "simulation_id": simulation_id,
            "content": f"Mock content for prompt {prompt_id}",
            "metadata": {
                "type": prompt_info["prompt_type"],
                "created_at": prompt_info["created_at"],
                "prompt_store_reference": prompt_info["prompt_store_reference"]
            }
        }


# Factory functions
def create_simulation_playback_engine(application_service: SimulationApplicationService,
                                    logger: SimulationLogger) -> SimulationPlaybackEngine:
    """Create a simulation playback engine."""
    return SimulationPlaybackEngine(application_service, logger)


def create_simulation_reconstructor(application_service: SimulationApplicationService,
                                  logger: SimulationLogger) -> SimulationReconstructor:
    """Create a simulation reconstructor."""
    return SimulationReconstructor(application_service, logger)
