"""Lifecycle management repository for data access operations.

Handles lifecycle policy and document lifecycle data operations.
"""
import json
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from ...core.repository import BaseRepository
from ...db.queries import execute_query
from ...core.entities import LifecyclePolicy


class LifecycleRepository(BaseRepository[LifecyclePolicy]):
    """Repository for lifecycle management data access."""

    def __init__(self):
        super().__init__("lifecycle_policies")

    def _row_to_entity(self, row: Dict[str, Any]) -> LifecyclePolicy:
        """Convert database row to LifecyclePolicy entity."""
        return LifecyclePolicy(
            id=row['id'],
            name=row['name'],
            description=row['description'],
            conditions=json.loads(row['conditions'] or '{}'),
            actions=json.loads(row['actions'] or '{}'),
            priority=row.get('priority', 0),
            enabled=row.get('enabled', True),
            created_at=row['created_at'],
            updated_at=row.get('updated_at')
        )

    def _entity_to_row(self, entity: LifecyclePolicy) -> Dict[str, Any]:
        """Convert LifecyclePolicy entity to database row."""
        return {
            'id': entity.id,
            'name': entity.name,
            'description': entity.description,
            'conditions': json.dumps(entity.conditions),
            'actions': json.dumps(entity.actions),
            'priority': entity.priority,
            'enabled': entity.enabled,
            'created_at': entity.created_at.isoformat(),
            'updated_at': entity.updated_at.isoformat() if entity.updated_at else None
        }

    def get_enabled_policies(self) -> List[LifecyclePolicy]:
        """Get all enabled policies ordered by priority."""
        rows = execute_query(
            f"SELECT * FROM {self.table_name} WHERE enabled = 1 ORDER BY priority DESC, created_at ASC",
            fetch_all=True
        )
        return [self._row_to_entity(row) for row in rows]

    def get_policies_for_document(self, document: Dict[str, Any]) -> List[LifecyclePolicy]:
        """Get policies that match a specific document."""
        policies = self.get_enabled_policies()
        matching_policies = []

        for policy in policies:
            if self._policy_matches_document(policy, document):
                matching_policies.append(policy)

        return matching_policies

    def _policy_matches_document(self, policy: LifecyclePolicy, document: Dict[str, Any]) -> bool:
        """Check if a policy matches a document."""
        try:
            conditions = policy.conditions
            metadata = document.get("metadata", {})

            # Check content type
            if "content_types" in conditions:
                doc_type = metadata.get("type", "")
                if doc_type not in conditions["content_types"]:
                    return False

            # Check source type
            if "source_types" in conditions:
                source_type = metadata.get("source_type", "")
                if source_type not in conditions["source_types"]:
                    return False

            # Check age (days since creation)
            if "max_age_days" in conditions:
                created_at = datetime.fromisoformat(document["created_at"])
                age_days = (datetime.utcnow() - created_at).days
                if age_days < conditions["max_age_days"]:
                    return False

            # Check tags
            if "required_tags" in conditions:
                required_tags = conditions["required_tags"]
                # This would need document tags - simplified for now
                if not any(tag in str(metadata) for tag in required_tags):
                    return False

            return True

        except Exception:
            return False

    def get_documents_for_lifecycle_transition(self, transition_type: str) -> List[Dict[str, Any]]:
        """Get documents that need lifecycle transitions."""
        # Get all documents with their lifecycle info
        cutoff_date = (datetime.utcnow() - timedelta(days=1)).isoformat()

        if transition_type == "archival":
            # Documents older than archival threshold
            rows = execute_query("""
                SELECT d.*, lc.retention_period_days, lc.archival_date
                FROM documents d
                LEFT JOIN document_lifecycle lc ON d.id = lc.document_id
                WHERE lc.archival_date < ?
                AND lc.current_phase = 'active'
            """, (cutoff_date,), fetch_all=True)

        elif transition_type == "deletion":
            # Documents older than deletion threshold
            rows = execute_query("""
                SELECT d.*, lc.deletion_date
                FROM documents d
                LEFT JOIN document_lifecycle lc ON d.id = lc.document_id
                WHERE lc.deletion_date < ?
                AND lc.current_phase IN ('archived', 'retention')
            """, (cutoff_date,), fetch_all=True)

        else:
            rows = []

        return rows

    def update_document_lifecycle(self, document_id: str, phase: str,
                                retention_days: int = None) -> None:
        """Update document lifecycle information."""
        now = datetime.utcnow()

        if retention_days:
            archival_date = now + timedelta(days=retention_days)
            deletion_date = archival_date + timedelta(days=365)  # Default 1 year retention
        else:
            archival_date = None
            deletion_date = None

        # Insert or update lifecycle record
        execute_query("""
            INSERT OR REPLACE INTO document_lifecycle
            (document_id, current_phase, retention_period_days, archival_date, deletion_date,
             last_reviewed, compliance_status, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            document_id,
            phase,
            retention_days,
            archival_date.isoformat() if archival_date else None,
            deletion_date.isoformat() if deletion_date else None,
            now.isoformat(),
            'compliant',
            now.isoformat()
        ))

    def get_lifecycle_stats(self) -> Dict[str, Any]:
        """Get lifecycle management statistics."""
        # Document phase distribution
        phase_rows = execute_query("""
            SELECT current_phase, COUNT(*) as count
            FROM document_lifecycle
            GROUP BY current_phase
        """, fetch_all=True)

        phase_stats = {row['current_phase']: row['count'] for row in phase_rows}

        # Policy application stats
        policy_rows = execute_query("""
            SELECT COUNT(DISTINCT document_id) as docs_with_policies
            FROM document_lifecycle
            WHERE applied_policies IS NOT NULL
        """, fetch_one=True)

        policy_count = policy_rows['docs_with_policies'] if policy_rows else 0

        # Compliance stats
        compliance_rows = execute_query("""
            SELECT compliance_status, COUNT(*) as count
            FROM document_lifecycle
            GROUP BY compliance_status
        """, fetch_all=True)

        compliance_stats = {row['compliance_status']: row['count'] for row in compliance_rows}

        return {
            "phase_distribution": phase_stats,
            "documents_with_policies": policy_count,
            "compliance_stats": compliance_stats
        }

    def log_lifecycle_event(self, document_id: str, event_type: str,
                          details: Dict[str, Any] = None) -> None:
        """Log a lifecycle event."""
        execute_query("""
            INSERT INTO lifecycle_events
            (document_id, event_type, details, created_at)
            VALUES (?, ?, ?, ?)
        """, (
            document_id,
            event_type,
            json.dumps(details or {}),
            datetime.utcnow().isoformat()
        ))
