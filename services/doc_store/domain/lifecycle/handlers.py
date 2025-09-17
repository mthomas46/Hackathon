"""Lifecycle management handlers for API endpoints.

Handles lifecycle policy and transition-related HTTP requests.
"""
from typing import Dict, Any, Optional
from ...core.handler import BaseHandler
from .service import LifecycleService


class LifecycleHandlers(BaseHandler):
    """Handlers for lifecycle management API endpoints."""

    def __init__(self):
        super().__init__(LifecycleService())

    async def handle_create_policy(self, name: str, description: str,
                                 conditions: Dict[str, Any], actions: Dict[str, Any],
                                 priority: int = 0) -> Dict[str, Any]:
        """Handle lifecycle policy creation."""
        self._validate_request_data({
            'name': name,
            'conditions': conditions,
            'actions': actions
        }, ['name', 'conditions', 'actions'])

        policy = self.service.create_policy(name, description, conditions, actions, priority)

        return await self._handle_request(
            lambda: policy.to_dict(),
            operation="create_lifecycle_policy",
            policy_name=name
        )

    async def handle_get_policy(self, policy_id: str) -> Dict[str, Any]:
        """Handle policy retrieval."""
        return await self.handle_get(policy_id)

    async def handle_list_policies(self) -> Dict[str, Any]:
        """Handle policy listing."""
        return await self.handle_list()

    async def handle_update_policy(self, policy_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Handle policy updates."""
        return await self.handle_update(policy_id, updates)

    async def handle_delete_policy(self, policy_id: str) -> Dict[str, Any]:
        """Handle policy deletion."""
        return await self.handle_delete(policy_id)

    async def handle_evaluate_document_policies(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Handle document policy evaluation."""
        policies = self.service.evaluate_document_policies(document)

        return await self._handle_request(
            lambda: {
                "document_id": document.get('id'),
                "matching_policies": [p.to_dict() for p in policies],
                "policy_count": len(policies)
            },
            operation="evaluate_document_policies",
            document_id=document.get('id'),
            matching_policies=len(policies)
        )

    async def handle_apply_lifecycle_policies(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Handle policy application to document."""
        result = self.service.apply_lifecycle_policies(document)

        return await self._handle_request(
            lambda: result,
            operation="apply_lifecycle_policies",
            document_id=document.get('id'),
            applied_policies=len(result['applied_policies'])
        )

    async def handle_process_lifecycle_transitions(self) -> Dict[str, Any]:
        """Handle lifecycle transition processing."""
        result = self.service.process_lifecycle_transitions()

        return await self._handle_request(
            lambda: result,
            operation="process_lifecycle_transitions",
            documents_processed=result['archived'] + result['deleted'],
            errors=len(result['errors'])
        )

    async def handle_get_document_lifecycle(self, document_id: str) -> Dict[str, Any]:
        """Handle document lifecycle retrieval."""
        lifecycle = self.service.get_document_lifecycle(document_id)

        if not lifecycle:
            return await self._handle_request(lambda: (_ for _ in ()).throw(ValueError("Document lifecycle not found")))

        return await self._handle_request(
            lambda: lifecycle,
            operation="get_document_lifecycle",
            document_id=document_id
        )

    async def handle_get_lifecycle_statistics(self) -> Dict[str, Any]:
        """Handle lifecycle statistics request."""
        stats = self.service.get_lifecycle_statistics()

        return await self._handle_request(
            lambda: stats,
            operation="get_lifecycle_statistics"
        )

    async def handle_update_policy_status(self, policy_id: str, enabled: bool) -> Dict[str, Any]:
        """Handle policy status update."""
        self.service.update_policy_status(policy_id, enabled)

        return await self._handle_request(
            lambda: {"policy_id": policy_id, "enabled": enabled},
            operation="update_policy_status",
            policy_id=policy_id,
            enabled=enabled
        )
