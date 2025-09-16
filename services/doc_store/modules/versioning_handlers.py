# ============================================================================
# VERSIONING HANDLERS MODULE
# ============================================================================
"""
Versioning handlers for Doc Store service.

Provides comprehensive version control operations including:
- Version history retrieval
- Version comparison
- Rollback operations
- Version cleanup and management
"""

from typing import Dict, Any, Optional
from .versioning import (
    get_document_versions,
    get_document_version,
    compare_document_versions,
    rollback_document_to_version,
    cleanup_old_versions
)
from .shared_utils import (
    build_doc_store_context,
    create_doc_store_success_response,
    handle_doc_store_error
)
from .models import (
    DocumentVersionsResponse,
    DocumentVersionDetail,
    VersionComparison,
    VersionRollbackRequest,
    VersionCleanupRequest
)


class VersioningHandlers:
    """Handles document versioning operations."""

    @staticmethod
    async def handle_get_document_versions(
        document_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get version history for a document."""
        try:
            result = get_document_versions(document_id, limit, offset)

            context = build_doc_store_context("version_history_retrieval", document_id=document_id)
            return create_doc_store_success_response("version history retrieved", result, **context)

        except Exception as e:
            context = build_doc_store_context("version_history_retrieval", document_id=document_id)
            return handle_doc_store_error("retrieve document versions", e, **context)

    @staticmethod
    async def handle_get_document_version(document_id: str, version_number: int) -> Dict[str, Any]:
        """Get a specific version of a document."""
        try:
            result = get_document_version(document_id, version_number)

            context = build_doc_store_context(
                "version_retrieval",
                document_id=document_id,
                version_number=version_number
            )
            return create_doc_store_success_response("document version retrieved", result, **context)

        except Exception as e:
            context = build_doc_store_context(
                "version_retrieval",
                document_id=document_id,
                version_number=version_number
            )
            return handle_doc_store_error("retrieve document version", e, **context)

    @staticmethod
    async def handle_compare_versions(document_id: str, version_a: int, version_b: int) -> Dict[str, Any]:
        """Compare two versions of a document."""
        try:
            result = compare_document_versions(document_id, version_a, version_b)

            context = build_doc_store_context(
                "version_comparison",
                document_id=document_id,
                version_a=version_a,
                version_b=version_b
            )
            return create_doc_store_success_response("versions compared", result, **context)

        except Exception as e:
            context = build_doc_store_context(
                "version_comparison",
                document_id=document_id,
                version_a=version_a,
                version_b=version_b
            )
            return handle_doc_store_error("compare document versions", e, **context)

    @staticmethod
    async def handle_rollback_version(document_id: str, req: VersionRollbackRequest) -> Dict[str, Any]:
        """Rollback a document to a previous version."""
        try:
            result = rollback_document_to_version(
                document_id=document_id,
                version_number=req.version_number,
                changed_by=req.changed_by
            )

            context = build_doc_store_context(
                "version_rollback",
                document_id=document_id,
                rolled_back_to_version=req.version_number
            )
            return create_doc_store_success_response("document rolled back to previous version", result, **context)

        except Exception as e:
            context = build_doc_store_context(
                "version_rollback",
                document_id=document_id,
                target_version=req.version_number
            )
            return handle_doc_store_error("rollback document version", e, **context)

    @staticmethod
    async def handle_cleanup_versions(document_id: str, req: VersionCleanupRequest) -> Dict[str, Any]:
        """Clean up old versions of a document."""
        try:
            result = cleanup_old_versions(document_id, req.keep_versions)

            context = build_doc_store_context(
                "version_cleanup",
                document_id=document_id,
                versions_kept=req.keep_versions
            )
            return create_doc_store_success_response("old versions cleaned up", result, **context)

        except Exception as e:
            context = build_doc_store_context(
                "version_cleanup",
                document_id=document_id,
                keep_versions=req.keep_versions
            )
            return handle_doc_store_error("cleanup document versions", e, **context)
