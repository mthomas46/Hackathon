# ============================================================================
# LIFECYCLE HANDLERS MODULE
# ============================================================================
"""
Lifecycle management handlers for Doc Store service.

Provides endpoints for lifecycle policy management, compliance monitoring,
and automated lifecycle operations.
"""

from typing import Dict, Any, Optional, List
from .lifecycle_management import lifecycle_manager, LifecyclePolicy
from .shared_utils import (
    build_doc_store_context,
    create_doc_store_success_response,
    handle_doc_store_error
)
from .models import (
    LifecyclePolicyRequest,
    LifecycleStatusResponse,
    LifecycleReportResponse,
    LifecycleTransitionRequest
)


class LifecycleHandlers:
    """Handles lifecycle management operations."""

    @staticmethod
    async def handle_create_policy(req: LifecyclePolicyRequest) -> Dict[str, Any]:
        """Create a new lifecycle policy."""
        try:
            policy_id = lifecycle_manager.create_policy(
                name=req.name,
                description=req.description,
                conditions=req.conditions,
                actions=req.actions,
                priority=req.priority
            )

            context = build_doc_store_context("policy_creation", policy_name=req.name)
            return create_doc_store_success_response("lifecycle policy created", {
                "policy_id": policy_id,
                "name": req.name,
                "description": req.description
            }, **context)

        except Exception as e:
            context = build_doc_store_context("policy_creation", policy_name=req.name)
            return handle_doc_store_error("create lifecycle policy", e, **context)

    @staticmethod
    async def handle_get_policies() -> Dict[str, Any]:
        """Get all lifecycle policies."""
        try:
            policies = []
            for policy_id, policy in lifecycle_manager.policies.items():
                policies.append({
                    "id": policy.id,
                    "name": policy.name,
                    "description": policy.description,
                    "conditions": policy.conditions,
                    "actions": policy.actions,
                    "priority": policy.priority,
                    "enabled": policy.enabled,
                    "created_at": policy.created_at,
                    "updated_at": policy.updated_at
                })

            context = build_doc_store_context("policies_retrieval", count=len(policies))
            return create_doc_store_success_response("lifecycle policies retrieved", {
                "policies": policies,
                "total": len(policies)
            }, **context)

        except Exception as e:
            context = build_doc_store_context("policies_retrieval")
            return handle_doc_store_error("get lifecycle policies", e, **context)

    @staticmethod
    async def handle_get_document_lifecycle(document_id: str) -> Dict[str, Any]:
        """Get lifecycle information for a document."""
        try:
            lifecycle = lifecycle_manager.get_document_lifecycle(document_id)

            if not lifecycle:
                return handle_doc_store_error("get document lifecycle", f"No lifecycle information found for document {document_id}")

            context = build_doc_store_context("lifecycle_retrieval", document_id=document_id)
            return create_doc_store_success_response("document lifecycle retrieved", {
                "id": lifecycle.id,
                "document_id": lifecycle.document_id,
                "current_phase": lifecycle.current_phase,
                "retention_period_days": lifecycle.retention_period_days,
                "archival_date": lifecycle.archival_date,
                "deletion_date": lifecycle.deletion_date,
                "last_reviewed": lifecycle.last_reviewed,
                "compliance_status": lifecycle.compliance_status,
                "applied_policies": lifecycle.applied_policies,
                "metadata": lifecycle.metadata,
                "created_at": lifecycle.created_at,
                "updated_at": lifecycle.updated_at
            }, **context)

        except Exception as e:
            context = build_doc_store_context("lifecycle_retrieval", document_id=document_id)
            return handle_doc_store_error("get document lifecycle", e, **context)

    @staticmethod
    async def handle_initialize_document_lifecycle(document_id: str) -> Dict[str, Any]:
        """Initialize lifecycle tracking for a document."""
        try:
            lifecycle_id = lifecycle_manager.initialize_document_lifecycle(document_id)

            context = build_doc_store_context("lifecycle_initialization", document_id=document_id)
            return create_doc_store_success_response("document lifecycle initialized", {
                "lifecycle_id": lifecycle_id,
                "document_id": document_id
            }, **context)

        except Exception as e:
            context = build_doc_store_context("lifecycle_initialization", document_id=document_id)
            return handle_doc_store_error("initialize document lifecycle", e, **context)

    @staticmethod
    async def handle_process_lifecycle_transitions() -> Dict[str, Any]:
        """Process automatic lifecycle transitions."""
        try:
            result = lifecycle_manager.process_lifecycle_transitions()

            context = build_doc_store_context("lifecycle_transitions", processed=result)
            return create_doc_store_success_response("lifecycle transitions processed", result, **context)

        except Exception as e:
            context = build_doc_store_context("lifecycle_transitions")
            return handle_doc_store_error("process lifecycle transitions", e, **context)

    @staticmethod
    async def handle_get_lifecycle_report(days_back: int = 30) -> Dict[str, Any]:
        """Get comprehensive lifecycle management report."""
        try:
            report = lifecycle_manager.get_lifecycle_report(days_back)

            context = build_doc_store_context("lifecycle_report", days_back=days_back)
            return create_doc_store_success_response("lifecycle report generated", report, **context)

        except Exception as e:
            context = build_doc_store_context("lifecycle_report", days_back=days_back)
            return handle_doc_store_error("generate lifecycle report", e, **context)

    @staticmethod
    async def handle_transition_document_phase(document_id: str, req: LifecycleTransitionRequest) -> Dict[str, Any]:
        """Manually transition a document to a new lifecycle phase."""
        try:
            # Get current lifecycle
            current_lifecycle = lifecycle_manager.get_document_lifecycle(document_id)
            if not current_lifecycle:
                return handle_doc_store_error("transition document phase", f"No lifecycle information found for document {document_id}")

            # Perform transition
            lifecycle_manager._transition_document_phase(
                document_id=document_id,
                old_phase=current_lifecycle.current_phase,
                new_phase=req.new_phase,
                reason=req.reason or "Manual transition"
            )

            # Update lifecycle record
            from .shared_utils import execute_db_query
            from services.shared.utilities import utc_now
            execute_db_query("""
                UPDATE document_lifecycle
                SET current_phase = ?, updated_at = ?
                WHERE document_id = ?
            """, (req.new_phase, utc_now().isoformat(), document_id))

            context = build_doc_store_context(
                "phase_transition",
                document_id=document_id,
                old_phase=current_lifecycle.current_phase,
                new_phase=req.new_phase
            )
            return create_doc_store_success_response("document phase transitioned", {
                "document_id": document_id,
                "old_phase": current_lifecycle.current_phase,
                "new_phase": req.new_phase,
                "reason": req.reason
            }, **context)

        except Exception as e:
            context = build_doc_store_context("phase_transition", document_id=document_id)
            return handle_doc_store_error("transition document phase", e, **context)
