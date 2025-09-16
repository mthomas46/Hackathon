# ============================================================================
# LIFECYCLE MANAGEMENT MODULE
# ============================================================================
"""
Document lifecycle management and automated policy enforcement for Doc Store service.

Provides comprehensive lifecycle management including:
- Policy-based retention and archival
- Automated lifecycle transitions
- Compliance monitoring and reporting
- Audit trails and event logging
- Configurable retention policies
"""

import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field

from services.shared.utilities import utc_now
from .shared_utils import execute_db_query


@dataclass
class LifecyclePolicy:
    """Document lifecycle policy definition."""
    id: str
    name: str
    description: str
    conditions: Dict[str, Any]
    actions: Dict[str, Any]
    priority: int = 0
    enabled: bool = True
    created_at: str = ""
    updated_at: str = ""

    def matches_document(self, document: Dict[str, Any], lifecycle: Dict[str, Any]) -> bool:
        """Check if this policy matches a document."""
        try:
            conditions = self.conditions

            # Check content type
            if "content_types" in conditions:
                doc_type = document.get("metadata", {}).get("type", "")
                if doc_type not in conditions["content_types"]:
                    return False

            # Check source type
            if "source_types" in conditions:
                source_type = document.get("metadata", {}).get("source_type", "")
                if source_type not in conditions["source_types"]:
                    return False

            # Check age
            if "max_age_days" in conditions:
                created_at = datetime.fromisoformat(document["created_at"])
                age_days = (datetime.now() - created_at).days
                if age_days < conditions["max_age_days"]:
                    return False

            # Check tags
            if "required_tags" in conditions:
                doc_tags = lifecycle.get("tags", [])
                required_tags = conditions["required_tags"]
                if not all(tag in doc_tags for tag in required_tags):
                    return False

            # Check analysis status
            if "has_analysis" in conditions:
                analysis_count = lifecycle.get("analysis_count", 0)
                if conditions["has_analysis"] and analysis_count == 0:
                    return False
                elif not conditions["has_analysis"] and analysis_count > 0:
                    return False

            return True

        except Exception:
            return False


@dataclass
class DocumentLifecycle:
    """Document lifecycle information."""
    id: str
    document_id: str
    current_phase: str = "active"
    retention_period_days: Optional[int] = None
    archival_date: Optional[str] = None
    deletion_date: Optional[str] = None
    last_reviewed: Optional[str] = None
    compliance_status: str = "compliant"
    applied_policies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""


class LifecycleManager:
    """Manages document lifecycle policies and enforcement."""

    def __init__(self):
        self.policies: Dict[str, LifecyclePolicy] = {}
        self._load_policies()

    def _load_policies(self):
        """Load lifecycle policies from database."""
        try:
            rows = execute_db_query(
                "SELECT id, name, description, conditions, actions, priority, enabled, created_at, updated_at FROM lifecycle_policies WHERE enabled = 1",
                fetch_all=True
            )

            for row in rows:
                policy = LifecyclePolicy(
                    id=row['id'],
                    name=row['name'],
                    description=row['description'],
                    conditions=json.loads(row['conditions'] or '{}'),
                    actions=json.loads(row['actions'] or '{}'),
                    priority=row['priority'],
                    enabled=bool(row['enabled']),
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                )
                self.policies[policy.id] = policy

        except Exception as e:
            print(f"Error loading lifecycle policies: {e}")

    def create_policy(self, name: str, description: str, conditions: Dict[str, Any],
                     actions: Dict[str, Any], priority: int = 0) -> str:
        """Create a new lifecycle policy."""
        try:
            policy_id = f"policy_{name.lower().replace(' ', '_')}"

            execute_db_query("""
                INSERT OR REPLACE INTO lifecycle_policies
                (id, name, description, conditions, actions, priority, enabled, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)
            """, (
                policy_id,
                name,
                description,
                json.dumps(conditions),
                json.dumps(actions),
                priority,
                utc_now().isoformat(),
                utc_now().isoformat()
            ))

            policy = LifecyclePolicy(
                id=policy_id,
                name=name,
                description=description,
                conditions=conditions,
                actions=actions,
                priority=priority,
                enabled=True,
                created_at=utc_now().isoformat(),
                updated_at=utc_now().isoformat()
            )
            self.policies[policy_id] = policy

            return policy_id

        except Exception as e:
            raise Exception(f"Failed to create policy: {str(e)}")

    def get_document_lifecycle(self, document_id: str) -> Optional[DocumentLifecycle]:
        """Get lifecycle information for a document."""
        try:
            row = execute_db_query("""
                SELECT id, document_id, current_phase, retention_period_days, archival_date,
                       deletion_date, last_reviewed, compliance_status, applied_policies,
                       metadata, created_at, updated_at
                FROM document_lifecycle WHERE document_id = ?
            """, (document_id,), fetch_one=True)

            if not row:
                return None

            return DocumentLifecycle(
                id=row['id'],
                document_id=row['document_id'],
                current_phase=row['current_phase'],
                retention_period_days=row['retention_period_days'],
                archival_date=row['archival_date'],
                deletion_date=row['deletion_date'],
                last_reviewed=row['last_reviewed'],
                compliance_status=row['compliance_status'],
                applied_policies=json.loads(row['applied_policies'] or '[]'),
                metadata=json.loads(row['metadata'] or '{}'),
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )

        except Exception:
            return None

    def initialize_document_lifecycle(self, document_id: str) -> str:
        """Initialize lifecycle tracking for a document."""
        try:
            lifecycle_id = f"lifecycle_{document_id}"

            # Apply matching policies
            applied_policies = self._evaluate_policies(document_id)

            # Calculate retention and dates
            retention_days = self._calculate_retention_period(applied_policies)
            archival_date = None
            deletion_date = None

            if retention_days:
                now = datetime.now()
                archival_date = (now + timedelta(days=retention_days//2)).isoformat()
                deletion_date = (now + timedelta(days=retention_days)).isoformat()

            execute_db_query("""
                INSERT OR REPLACE INTO document_lifecycle
                (id, document_id, current_phase, retention_period_days, archival_date,
                 deletion_date, applied_policies, created_at, updated_at)
                VALUES (?, ?, 'active', ?, ?, ?, ?, ?, ?)
            """, (
                lifecycle_id,
                document_id,
                retention_days,
                archival_date,
                deletion_date,
                json.dumps([p.id for p in applied_policies]),
                utc_now().isoformat(),
                utc_now().isoformat()
            ))

            # Log lifecycle initialization
            self._log_lifecycle_event(
                document_id=doc_id,
                event_type="initialized",
                details={"applied_policies": [p.name for p in applied_policies]}
            )

            return lifecycle_id

        except Exception as e:
            raise Exception(f"Failed to initialize document lifecycle: {str(e)}")

    def _evaluate_policies(self, document_id: str) -> List[LifecyclePolicy]:
        """Evaluate which policies apply to a document."""
        try:
            # Get document and lifecycle information
            document = execute_db_query(
                "SELECT id, metadata, created_at FROM documents WHERE id = ?",
                (document_id,),
                fetch_one=True
            )

            if not document:
                return []

            # Get analysis count and tags
            analysis_count = execute_db_query(
                "SELECT COUNT(*) FROM analyses WHERE document_id = ?",
                (document_id,),
                fetch_one=True
            )[0]

            tags = execute_db_query(
                "SELECT tag FROM document_tags WHERE document_id = ?",
                (document_id,),
                fetch_all=True
            )
            tag_list = [row['tag'] for row in tags]

            lifecycle_info = {
                "analysis_count": analysis_count,
                "tags": tag_list
            }

            # Evaluate policies
            matching_policies = []
            for policy in self.policies.values():
                if policy.matches_document(document, lifecycle_info):
                    matching_policies.append(policy)

            # Sort by priority
            matching_policies.sort(key=lambda p: p.priority, reverse=True)

            return matching_policies

        except Exception:
            return []

    def _calculate_retention_period(self, policies: List[LifecyclePolicy]) -> Optional[int]:
        """Calculate retention period based on applied policies."""
        if not policies:
            return None

        # Use the policy with highest retention requirement
        max_retention = 0
        for policy in policies:
            if "retention_days" in policy.actions:
                max_retention = max(max_retention, policy.actions["retention_days"])

        return max_retention if max_retention > 0 else None

    def process_lifecycle_transitions(self) -> Dict[str, Any]:
        """Process automatic lifecycle transitions for documents."""
        try:
            processed = {"archived": 0, "deleted": 0, "reviewed": 0}

            # Find documents ready for archival
            archival_candidates = execute_db_query("""
                SELECT dl.document_id, dl.archival_date, d.metadata
                FROM document_lifecycle dl
                JOIN documents d ON dl.document_id = d.id
                WHERE dl.current_phase = 'active'
                AND dl.archival_date IS NOT NULL
                AND dl.archival_date <= ?
            """, (utc_now().isoformat(),), fetch_all=True)

            for row in archival_candidates:
                self._transition_document_phase(
                    row['document_id'],
                    'active',
                    'archived',
                    f"Automatic archival based on retention policy"
                )
                processed["archived"] += 1

            # Find documents ready for deletion
            deletion_candidates = execute_db_query("""
                SELECT dl.document_id, dl.deletion_date, d.metadata
                FROM document_lifecycle dl
                JOIN documents d ON dl.document_id = d.id
                WHERE dl.current_phase = 'archived'
                AND dl.deletion_date IS NOT NULL
                AND dl.deletion_date <= ?
            """, (utc_now().isoformat(),), fetch_all=True)

            for row in deletion_candidates:
                # Actually delete the document (in a real system, this might move to cold storage)
                execute_db_query("DELETE FROM documents WHERE id = ?", (row['document_id'],))
                execute_db_query("DELETE FROM document_lifecycle WHERE document_id = ?", (row['document_id'],))

                self._log_lifecycle_event(
                    document_id=row['document_id'],
                    event_type="deleted",
                    details={"reason": "retention period expired"}
                )
                processed["deleted"] += 1

            return processed

        except Exception as e:
            return {"error": str(e)}

    def _transition_document_phase(self, document_id: str, old_phase: str, new_phase: str, reason: str):
        """Transition a document to a new lifecycle phase."""
        try:
            execute_db_query("""
                UPDATE document_lifecycle
                SET current_phase = ?, updated_at = ?
                WHERE document_id = ?
            """, (new_phase, utc_now().isoformat(), document_id))

            self._log_lifecycle_event(
                document_id=document_id,
                event_type="phase_transition",
                old_phase=old_phase,
                new_phase=new_phase,
                details={"reason": reason}
            )

        except Exception as e:
            print(f"Error transitioning document {document_id}: {e}")

    def _log_lifecycle_event(self, document_id: str, event_type: str, policy_id: Optional[str] = None,
                           old_phase: Optional[str] = None, new_phase: Optional[str] = None,
                           details: Optional[Dict[str, Any]] = None, performed_by: str = "system"):
        """Log a lifecycle event."""
        try:
            event_id = f"event_{document_id}_{int(datetime.now().timestamp())}"

            execute_db_query("""
                INSERT INTO lifecycle_events
                (id, document_id, event_type, policy_id, old_phase, new_phase, details, performed_by, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event_id,
                document_id,
                event_type,
                policy_id,
                old_phase,
                new_phase,
                json.dumps(details or {}),
                performed_by,
                utc_now().isoformat()
            ))

        except Exception as e:
            print(f"Error logging lifecycle event: {e}")

    def get_lifecycle_report(self, days_back: int = 30) -> Dict[str, Any]:
        """Generate a comprehensive lifecycle management report."""
        try:
            cutoff_date = (datetime.now() - timedelta(days=days_back)).isoformat()

            # Phase distribution
            phase_distribution = execute_db_query("""
                SELECT current_phase, COUNT(*) as count
                FROM document_lifecycle
                GROUP BY current_phase
            """, fetch_all=True)

            # Upcoming transitions
            upcoming_archivals = execute_db_query("""
                SELECT COUNT(*) FROM document_lifecycle
                WHERE current_phase = 'active'
                AND archival_date IS NOT NULL
                AND archival_date > ?
                AND archival_date <= ?
            """, (
                cutoff_date,
                (datetime.now() + timedelta(days=30)).isoformat()
            ), fetch_one=True)[0]

            upcoming_deletions = execute_db_query("""
                SELECT COUNT(*) FROM document_lifecycle
                WHERE current_phase = 'archived'
                AND deletion_date IS NOT NULL
                AND deletion_date > ?
                AND deletion_date <= ?
            """, (
                cutoff_date,
                (datetime.now() + timedelta(days=30)).isoformat()
            ), fetch_one=True)[0]

            # Recent events
            recent_events = execute_db_query("""
                SELECT document_id, event_type, old_phase, new_phase, created_at
                FROM lifecycle_events
                WHERE created_at > ?
                ORDER BY created_at DESC
                LIMIT 50
            """, (cutoff_date,), fetch_all=True)

            # Policy effectiveness
            policy_effectiveness = execute_db_query("""
                SELECT lp.name, COUNT(le.id) as events_count
                FROM lifecycle_policies lp
                LEFT JOIN lifecycle_events le ON lp.id = le.policy_id
                GROUP BY lp.id, lp.name
            """, fetch_all=True)

            return {
                "phase_distribution": [{"phase": row['current_phase'], "count": row['count']} for row in phase_distribution],
                "upcoming_transitions": {
                    "archivals_next_30_days": upcoming_archivals,
                    "deletions_next_30_days": upcoming_deletions
                },
                "recent_events": [
                    {
                        "document_id": row['document_id'],
                        "event_type": row['event_type'],
                        "old_phase": row['old_phase'],
                        "new_phase": row['new_phase'],
                        "timestamp": row['created_at']
                    } for row in recent_events
                ],
                "policy_effectiveness": [
                    {"policy_name": row['name'], "events_count": row['events_count']}
                    for row in policy_effectiveness
                ],
                "report_period_days": days_back
            }

        except Exception as e:
            return {"error": str(e)}


# Global lifecycle manager instance
lifecycle_manager = LifecycleManager()
