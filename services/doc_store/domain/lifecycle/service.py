"""Lifecycle management service for business logic operations.

Handles lifecycle policy evaluation and automated transitions.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from ...core.service import BaseService
from ...core.entities import LifecyclePolicy
from .repository import LifecycleRepository


class LifecycleService(BaseService[LifecyclePolicy]):
    """Service for lifecycle management business logic."""

    def __init__(self):
        super().__init__(LifecycleRepository())

    def _validate_entity(self, entity: LifecyclePolicy) -> None:
        """Validate lifecycle policy."""
        if not entity.name:
            raise ValueError("Policy name is required")

        if not entity.conditions:
            raise ValueError("Policy conditions are required")

        if not entity.actions:
            raise ValueError("Policy actions are required")

        # Validate conditions
        if "max_age_days" in entity.conditions:
            if not isinstance(entity.conditions["max_age_days"], int) or entity.conditions["max_age_days"] <= 0:
                raise ValueError("max_age_days must be a positive integer")

        # Validate actions
        valid_actions = ["archive", "delete", "retain"]
        for action in entity.actions.values():
            if action not in valid_actions:
                raise ValueError(f"Invalid action: {action}")

    def _create_entity_from_data(self, entity_id: str, data: Dict[str, Any]) -> LifecyclePolicy:
        """Create lifecycle policy from data."""
        return LifecyclePolicy(
            id=entity_id,
            name=data['name'],
            description=data.get('description', ''),
            conditions=data['conditions'],
            actions=data['actions'],
            priority=data.get('priority', 0),
            enabled=data.get('enabled', True)
        )

    def create_policy(self, name: str, description: str, conditions: Dict[str, Any],
                     actions: Dict[str, Any], priority: int = 0) -> LifecyclePolicy:
        """Create a new lifecycle policy."""
        data = {
            'name': name,
            'description': description,
            'conditions': conditions,
            'actions': actions,
            'priority': priority
        }
        return self.create_entity(data)

    def evaluate_document_policies(self, document: Dict[str, Any]) -> List[LifecyclePolicy]:
        """Evaluate which policies apply to a document."""
        return self.repository.get_policies_for_document(document)

    def apply_lifecycle_policies(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Apply appropriate lifecycle policies to a document."""
        policies = self.evaluate_document_policies(document)
        applied_policies = []

        for policy in policies:
            # Check if policy should trigger an action
            if self._should_apply_policy(policy, document):
                self._apply_policy_action(policy, document)
                applied_policies.append(policy.name)

                # Log the event
                self.repository.log_lifecycle_event(
                    document['id'],
                    'policy_applied',
                    {'policy_name': policy.name, 'actions': policy.actions}
                )

        # Update document lifecycle
        if applied_policies:
            self.repository.update_document_lifecycle(
                document['id'],
                'active',  # Start as active
                retention_days=365  # Default retention
            )

        return {
            "document_id": document['id'],
            "applied_policies": applied_policies,
            "policy_count": len(applied_policies)
        }

    def _should_apply_policy(self, policy: LifecyclePolicy, document: Dict[str, Any]) -> bool:
        """Determine if a policy should be applied to a document."""
        # Check age-based conditions
        if "max_age_days" in policy.conditions:
            created_at = datetime.fromisoformat(document["created_at"])
            age_days = (datetime.utcnow() - created_at).days

            if age_days >= policy.conditions["max_age_days"]:
                return True

        # Check other conditions as needed
        return False

    def _apply_policy_action(self, policy: LifecyclePolicy, document: Dict[str, Any]) -> None:
        """Apply a policy's actions to a document."""
        actions = policy.actions

        if "archive" in actions.values():
            # Mark for archival
            self.repository.update_document_lifecycle(document['id'], 'archival_pending')

        if "delete" in actions.values():
            # Mark for deletion
            self.repository.update_document_lifecycle(document['id'], 'deletion_pending')

        if "retain" in actions.values():
            # Set retention period
            retention_days = actions.get("retention_days", 365)
            self.repository.update_document_lifecycle(document['id'], 'retention', retention_days)

    def process_lifecycle_transitions(self) -> Dict[str, Any]:
        """Process pending lifecycle transitions."""
        processed = {"archived": 0, "deleted": 0, "errors": []}

        # Process archival transitions
        archival_docs = self.repository.get_documents_for_lifecycle_transition("archival")
        for doc in archival_docs:
            try:
                self.repository.update_document_lifecycle(doc['id'], 'archived')
                self.repository.log_lifecycle_event(doc['id'], 'archived')
                processed["archived"] += 1
            except Exception as e:
                processed["errors"].append(f"Failed to archive {doc['id']}: {str(e)}")

        # Process deletion transitions
        deletion_docs = self.repository.get_documents_for_lifecycle_transition("deletion")
        for doc in deletion_docs:
            try:
                # Actually delete the document
                from ...domain.documents.repository import DocumentRepository
                doc_repo = DocumentRepository()
                doc_repo.delete_by_id(doc['id'])

                self.repository.log_lifecycle_event(doc['id'], 'deleted')
                processed["deleted"] += 1
            except Exception as e:
                processed["errors"].append(f"Failed to delete {doc['id']}: {str(e)}")

        return processed

    def get_document_lifecycle(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get lifecycle information for a document."""
        row = self.repository.execute_query("""
            SELECT * FROM document_lifecycle WHERE document_id = ?
        """, (document_id,), fetch_one=True)

        if not row:
            return None

        return {
            "document_id": row['document_id'],
            "current_phase": row['current_phase'],
            "retention_period_days": row['retention_period_days'],
            "archival_date": row['archival_date'],
            "deletion_date": row['deletion_date'],
            "last_reviewed": row['last_reviewed'],
            "compliance_status": row['compliance_status'],
            "applied_policies": row['applied_policies']
        }

    def get_lifecycle_statistics(self) -> Dict[str, Any]:
        """Get comprehensive lifecycle statistics."""
        return self.repository.get_lifecycle_stats()

    def update_policy_status(self, policy_id: str, enabled: bool) -> None:
        """Enable or disable a lifecycle policy."""
        policy = self.repository.get_by_id(policy_id)
        if policy:
            policy.enabled = enabled
            self.repository.update(policy)
