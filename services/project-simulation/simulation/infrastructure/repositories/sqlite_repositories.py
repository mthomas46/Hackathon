"""SQLite-based repositories for persistent data storage.

This module provides SQLite implementations of the repository interfaces,
ensuring data persistence across application restarts and test runs.
"""

import sqlite3
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

from ...domain.repositories import ISimulationRepository
from ...domain.entities.simulation import Simulation, SimulationId, SimulationConfiguration
from ...domain.value_objects import SimulationStatus


class SQLiteSimulationRepository(ISimulationRepository):
    """SQLite implementation of the simulation repository."""

    def __init__(self, db_path: str = None):
        """Initialize the SQLite repository.

        Args:
            db_path: Path to the SQLite database file (optional, defaults to project data dir)
        """
        if db_path is None:
            # Use absolute path based on project root
            from pathlib import Path
            # __file__ is: services/project-simulation/simulation/infrastructure/repositories/sqlite_repositories.py
            # We want: services/project-simulation/data/simulation.db
            current_file = Path(__file__)
            project_sim_root = current_file.parent.parent.parent.parent
            db_path = str(project_sim_root / "data" / "simulation.db")

        self.db_path = db_path
        self._ensure_db_exists()

    def _ensure_db_exists(self):
        """Ensure the database and tables exist."""
        # Create data directory if it doesn't exist
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            # Main simulations table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS simulations (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    configuration TEXT NOT NULL,  -- JSON
                    recommendations_report_id TEXT,  -- Link to recommendations report
                    recommendations_report_timestamp TEXT,  -- When report was generated
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            # Simulation run data table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS simulation_runs (
                    id TEXT PRIMARY KEY,
                    simulation_id TEXT NOT NULL,
                    run_id TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    status TEXT NOT NULL,
                    execution_data TEXT,  -- JSON: execution logs, metrics, etc.
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (simulation_id) REFERENCES simulations (id)
                )
            """)

            # Document-simulation linkage table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS simulation_documents (
                    id TEXT PRIMARY KEY,
                    simulation_id TEXT NOT NULL,
                    document_id TEXT NOT NULL,
                    document_type TEXT NOT NULL,
                    doc_store_reference TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (simulation_id) REFERENCES simulations (id)
                )
            """)

            # Prompt-simulation linkage table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS simulation_prompts (
                    id TEXT PRIMARY KEY,
                    simulation_id TEXT NOT NULL,
                    prompt_id TEXT NOT NULL,
                    prompt_type TEXT NOT NULL,
                    prompt_store_reference TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (simulation_id) REFERENCES simulations (id)
                )
            """)

            conn.commit()

    async def save(self, simulation: Simulation) -> None:
        """Save a simulation to the database."""
        simulation_dict = simulation.get_simulation_summary()

        with sqlite3.connect(self.db_path) as conn:
            # Convert configuration to JSON
            config_dict = {
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

            now = datetime.now().isoformat()

            conn.execute("""
                INSERT OR REPLACE INTO simulations
                (id, project_id, status, configuration, recommendations_report_id, recommendations_report_timestamp, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                simulation_dict["id"],
                simulation_dict["project_id"],
                simulation_dict["status"],
                json.dumps(config_dict),
                getattr(simulation, 'recommendations_report_id', None),
                getattr(simulation, 'recommendations_report_timestamp', None),
                now,  # For new records, use current time
                now   # Always update timestamp
            ))
            conn.commit()

    async def find_by_id(self, simulation_id: str) -> Optional[Simulation]:
        """Find a simulation by its ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT id, project_id, status, configuration, recommendations_report_id, recommendations_report_timestamp, created_at, updated_at
                FROM simulations
                WHERE id = ?
            """, (simulation_id,))

            row = cursor.fetchone()
            if row:
                return self._row_to_simulation(row)
            return None

    async def find_by_project_id(self, project_id: str) -> List[Simulation]:
        """Find all simulations for a project."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT id, project_id, status, configuration, recommendations_report_id, recommendations_report_timestamp, created_at, updated_at
                FROM simulations
                WHERE project_id = ?
                ORDER BY created_at DESC
            """, (project_id,))

            simulations = []
            for row in cursor.fetchall():
                simulation = self._row_to_simulation(row)
                if simulation:
                    simulations.append(simulation)

            return simulations

    async def find_all(self) -> List[Simulation]:
        """Find all simulations."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT id, project_id, status, configuration, recommendations_report_id, recommendations_report_timestamp, created_at, updated_at
                FROM simulations
                ORDER BY created_at DESC
            """)

            simulations = []
            for row in cursor.fetchall():
                simulation = self._row_to_simulation(row)
                if simulation:
                    simulations.append(simulation)

            return simulations

    async def find_by_status(self, status: str) -> List[Simulation]:
        """Find simulations by status."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT id, project_id, status, configuration, recommendations_report_id, recommendations_report_timestamp, created_at, updated_at
                FROM simulations
                WHERE status = ?
                ORDER BY created_at DESC
            """, (status,))

            simulations = []
            for row in cursor.fetchall():
                simulation = self._row_to_simulation(row)
                if simulation:
                    simulations.append(simulation)

            return simulations

    async def find_recent(self, limit: int = 10) -> List[Simulation]:
        """Find recent simulations."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT id, project_id, status, configuration, created_at, updated_at
                FROM simulations
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))

            simulations = []
            for row in cursor.fetchall():
                simulation = self._row_to_simulation(row)
                if simulation:
                    simulations.append(simulation)

            return simulations

    async def save_simulation_run(self, simulation_id: str, run_id: str, execution_data: Dict[str, Any]) -> None:
        """Save simulation run data."""
        now = datetime.now().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO simulation_runs
                (id, simulation_id, run_id, start_time, status, execution_data, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                f"{simulation_id}_{run_id}",
                simulation_id,
                run_id,
                execution_data.get("start_time", now),
                execution_data.get("status", "running"),
                json.dumps(execution_data),
                now,
                now
            ))
            conn.commit()

    async def link_document_to_simulation(self, simulation_id: str, document_id: str,
                                        document_type: str, doc_store_reference: str) -> None:
        """Link a document to a simulation."""
        now = datetime.now().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO simulation_documents
                (id, simulation_id, document_id, document_type, doc_store_reference, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                f"{simulation_id}_{document_id}",
                simulation_id,
                document_id,
                document_type,
                doc_store_reference,
                now
            ))
            conn.commit()

    async def link_prompt_to_simulation(self, simulation_id: str, prompt_id: str,
                                      prompt_type: str, prompt_store_reference: str) -> None:
        """Link a prompt to a simulation."""
        now = datetime.now().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO simulation_prompts
                (id, simulation_id, prompt_id, prompt_type, prompt_store_reference, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                f"{simulation_id}_{prompt_id}",
                simulation_id,
                prompt_id,
                prompt_type,
                prompt_store_reference,
                now
            ))
            conn.commit()

    async def get_simulation_run_data(self, simulation_id: str, run_id: str) -> Optional[Dict[str, Any]]:
        """Get simulation run data."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT execution_data FROM simulation_runs
                WHERE simulation_id = ? AND run_id = ?
            """, (simulation_id, run_id))

            row = cursor.fetchone()
            if row:
                return json.loads(row[0])
            return None

    async def get_simulation_documents(self, simulation_id: str) -> List[Dict[str, Any]]:
        """Get all documents linked to a simulation."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT document_id, document_type, doc_store_reference, created_at
                FROM simulation_documents
                WHERE simulation_id = ?
                ORDER BY created_at DESC
            """, (simulation_id,))

            documents = []
            for row in cursor.fetchall():
                documents.append({
                    "document_id": row[0],
                    "document_type": row[1],
                    "doc_store_reference": row[2],
                    "created_at": row[3]
                })
            return documents

    async def get_simulation_prompts(self, simulation_id: str) -> List[Dict[str, Any]]:
        """Get all prompts linked to a simulation."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT prompt_id, prompt_type, prompt_store_reference, created_at
                FROM simulation_prompts
                WHERE simulation_id = ?
                ORDER BY created_at DESC
            """, (simulation_id,))

            prompts = []
            for row in cursor.fetchall():
                prompts.append({
                    "prompt_id": row[0],
                    "prompt_type": row[1],
                    "prompt_store_reference": row[2],
                    "created_at": row[3]
                })
            return prompts

    async def delete(self, simulation_id: str) -> bool:
        """Delete a simulation by its ID."""
        with sqlite3.connect(self.db_path) as conn:
            # Delete related data first (due to foreign key constraints)
            conn.execute("DELETE FROM simulation_runs WHERE simulation_id = ?", (simulation_id,))
            conn.execute("DELETE FROM simulation_documents WHERE simulation_id = ?", (simulation_id,))
            conn.execute("DELETE FROM simulation_prompts WHERE simulation_id = ?", (simulation_id,))

            # Delete the simulation
            cursor = conn.execute("DELETE FROM simulations WHERE id = ?", (simulation_id,))
            conn.commit()
            return cursor.rowcount > 0

    def _row_to_simulation(self, row) -> Optional[Simulation]:
        """Convert a database row to a Simulation object."""
        try:
            id_str, project_id, status_str, config_json, recommendations_report_id, recommendations_report_timestamp, created_at, updated_at = row

            # Parse configuration
            config_dict = json.loads(config_json)

            # Create configuration object
            from ...domain.entities.simulation import SimulationType
            configuration = SimulationConfiguration(
                simulation_type=SimulationType(config_dict["simulation_type"]),
                include_document_generation=config_dict.get("include_document_generation", True),
                include_workflow_execution=config_dict.get("include_workflow_execution", True),
                include_team_dynamics=config_dict.get("include_team_dynamics", True),
                real_time_progress=config_dict.get("real_time_progress", False),
                max_execution_time_minutes=config_dict.get("max_execution_time_minutes", 60),
                generate_realistic_delays=config_dict.get("generate_realistic_delays", True),
                capture_metrics=config_dict.get("capture_metrics", True),
                enable_ecosystem_integration=config_dict.get("enable_ecosystem_integration", True)
            )

            # Create simulation object
            simulation = Simulation(
                id=SimulationId(id_str),
                project_id=project_id,
                configuration=configuration
            )

            # Set status if different from default
            if status_str != "created":
                simulation.status = SimulationStatus(status_str)

            # Set recommendations report linkage if present
            if recommendations_report_id:
                simulation.recommendations_report_id = recommendations_report_id
                simulation.recommendations_report_timestamp = recommendations_report_timestamp

            return simulation

        except Exception as e:
            print(f"Error converting row to simulation: {e}")
            return None


def get_sqlite_simulation_repository() -> ISimulationRepository:
    """Factory function for SQLite simulation repository."""
    return SQLiteSimulationRepository()
