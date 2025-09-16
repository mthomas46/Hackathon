"""Lifecycle management repository.

Handles data access operations for prompt lifecycle transitions and status management.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from services.prompt_store.db.queries import execute_query
from services.prompt_store.core.entities import Prompt
from services.shared.utilities import utc_now


class LifecycleRepository:
    """Repository for prompt lifecycle management operations."""

    VALID_STATUSES = {"draft", "published", "deprecated", "archived"}
    VALID_TRANSITIONS = {
        "draft": ["published", "archived"],
        "published": ["deprecated", "archived"],
        "deprecated": ["archived", "published"],  # Allow reactivation
        "archived": ["published"]  # Allow reactivation from archive
    }

    def __init__(self):
        super().__init__()
        self.table_name = "prompts"

    def get_entity(self, entity_id: str) -> Optional[Prompt]:
        """Get a prompt by ID with lifecycle information."""
        query = f"""
            SELECT id, name, category, content, variables, description,
                   lifecycle_status, version, created_by, created_at,
                   updated_at, tags, metadata
            FROM {self.table_name}
            WHERE id = ?
        """
        row = execute_query(query, (entity_id,), fetch_one=True)
        if not row:
            return None

        # Convert row to Prompt entity
        return Prompt.from_dict(row)

    def update_lifecycle_status(self, prompt_id: str, new_status: str,
                               reason: str = "", updated_by: str = "system") -> bool:
        """Update the lifecycle status of a prompt."""
        if new_status not in self.VALID_STATUSES:
            raise ValueError(f"Invalid lifecycle status: {new_status}")

        # Get current status to validate transition
        current_prompt = self.get_entity(prompt_id)
        if not current_prompt:
            raise ValueError(f"Prompt {prompt_id} not found")

        # Validate transition
        if new_status not in self.VALID_TRANSITIONS.get(current_prompt.lifecycle_status, []):
            raise ValueError(
                f"Invalid transition from '{current_prompt.lifecycle_status}' to '{new_status}'"
            )

        # Update the status
        update_query = f"""
            UPDATE {self.table_name}
            SET lifecycle_status = ?, updated_at = ?, updated_by = ?
            WHERE id = ?
        """

        metadata = current_prompt.metadata or {}
        if "lifecycle_history" not in metadata:
            metadata["lifecycle_history"] = []

        # Add to lifecycle history
        history_entry = {
            "timestamp": utc_now().isoformat(),
            "from_status": current_prompt.lifecycle_status,
            "to_status": new_status,
            "reason": reason,
            "updated_by": updated_by
        }
        metadata["lifecycle_history"].append(history_entry)

        # Update metadata with history
        metadata_query = f"""
            UPDATE {self.table_name}
            SET metadata = ?
            WHERE id = ?
        """

        try:
            execute_query(update_query, (new_status, utc_now(), updated_by, prompt_id))
            execute_query(metadata_query, (str(metadata), prompt_id))
            return True
        except Exception as e:
            raise Exception(f"Failed to update lifecycle status: {str(e)}")

    def get_prompts_by_status(self, status: str, limit: int = 50,
                             offset: int = 0) -> List[Prompt]:
        """Get prompts by lifecycle status."""
        if status not in self.VALID_STATUSES:
            raise ValueError(f"Invalid lifecycle status: {status}")

        query = f"""
            SELECT id, name, category, content, variables, description,
                   lifecycle_status, version, created_by, created_at,
                   updated_at, tags, metadata
            FROM {self.table_name}
            WHERE lifecycle_status = ?
            ORDER BY updated_at DESC
            LIMIT ? OFFSET ?
        """

        rows = execute_query(query, (status, limit, offset))
        return [Prompt.from_dict(dict(row)) for row in rows]

    def get_lifecycle_history(self, prompt_id: str) -> List[Dict[str, Any]]:
        """Get the lifecycle transition history for a prompt."""
        prompt = self.get_entity(prompt_id)
        if not prompt:
            return []

        metadata = prompt.metadata or {}
        return metadata.get("lifecycle_history", [])

    def get_status_counts(self) -> Dict[str, int]:
        """Get count of prompts in each lifecycle status."""
        query = f"""
            SELECT lifecycle_status, COUNT(*) as count
            FROM {self.table_name}
            GROUP BY lifecycle_status
        """

        rows = execute_query(query, fetch_all=True)
        counts = {status: 0 for status in self.VALID_STATUSES}
        counts.update({row["lifecycle_status"]: row["count"] for row in rows})
        return counts

    def validate_transition(self, from_status: str, to_status: str) -> bool:
        """Validate if a lifecycle transition is allowed."""
        return to_status in self.VALID_TRANSITIONS.get(from_status, [])

    def get_transition_rules(self) -> Dict[str, List[str]]:
        """Get all valid lifecycle transition rules."""
        return self.VALID_TRANSITIONS.copy()
