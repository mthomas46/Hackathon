"""Document handlers for API endpoints.

Handles HTTP requests and responses for document operations.
"""
from typing import Dict, Any, Optional
from services.shared.core.responses.responses import create_success_response, create_error_response
from services.shared.utilities import utc_now
from ...core.models import (
    DocumentRequest, DocumentResponse, DocumentListResponse,
    MetadataUpdateRequest, SearchRequest, SearchResponse, QualityResponse
)
from .service import DocumentService


class DocumentHandlers:
    """Handlers for document API endpoints."""

    def __init__(self):
        self.service = DocumentService()

    async def handle_create_document(self, request: DocumentRequest) -> Dict[str, Any]:
        """Handle document creation."""
        try:
            # Process metadata
            metadata = request.metadata if isinstance(request.metadata, dict) else {}

            # Create document
            document = self.service.create_document(
                content=request.content,
                metadata=metadata,
                document_id=request.id,
                correlation_id=request.correlation_id
            )

            # Create response
            response_data = DocumentResponse(
                id=document.id,
                content=document.content,
                content_hash=document.content_hash,
                metadata=document.metadata,
                created_at=document.created_at.isoformat()
            )

            return create_success_response(
                "Document created successfully",
                response_data.dict(),
                {"document_id": document.id}
            )

        except ValueError as e:
            return create_error_response(str(e), "VALIDATION_ERROR")
        except Exception as e:
            return create_error_response(f"Failed to create document: {str(e)}", "INTERNAL_ERROR")

    async def handle_get_document(self, document_id: str) -> Dict[str, Any]:
        """Handle document retrieval."""
        try:
            document = self.service.get_document(document_id)
            if not document:
                return create_error_response(f"Document {document_id} not found", "NOT_FOUND")

            response_data = DocumentResponse(
                id=document.id,
                content=document.content,
                content_hash=document.content_hash,
                metadata=document.metadata,
                created_at=document.created_at.isoformat()
            )

            return create_success_response(
                "Document retrieved successfully",
                response_data.dict(),
                {"document_id": document_id}
            )

        except Exception as e:
            return create_error_response(f"Failed to retrieve document: {str(e)}", "INTERNAL_ERROR")

    async def handle_list_documents(self, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """Handle document listing."""
        try:
            result = self.service.list_documents(limit, offset)

            # Return the raw result for FastAPI to validate against DocumentListResponse
            return result

        except Exception as e:
            # For errors, still use the shared response system
            return create_error_response(f"Failed to list documents: {str(e)}", "INTERNAL_ERROR")

    async def handle_update_metadata(self, document_id: str, request: MetadataUpdateRequest) -> Dict[str, Any]:
        """Handle metadata updates."""
        try:
            self.service.update_metadata(document_id, request.metadata)

            return create_success_response(
                "Document metadata updated successfully",
                {"document_id": document_id, "metadata": request.metadata},
                {"document_id": document_id}
            )

        except ValueError as e:
            return create_error_response(str(e), "VALIDATION_ERROR")
        except Exception as e:
            return create_error_response(f"Failed to update metadata: {str(e)}", "INTERNAL_ERROR")

    async def handle_search_documents(self, request: SearchRequest) -> Dict[str, Any]:
        """Handle document search."""
        try:
            result = self.service.search_documents(request.query, request.limit or 50)

            return create_success_response(
                "Documents searched successfully",
                result,
                {"query": request.query, "results_count": len(result["items"])}
            )

        except ValueError as e:
            return create_error_response(str(e), "VALIDATION_ERROR")
        except Exception as e:
            return create_error_response(f"Failed to search documents: {str(e)}", "INTERNAL_ERROR")

    async def handle_get_quality_metrics(self, limit: int = 1000) -> Dict[str, Any]:
        """Handle quality metrics retrieval."""
        try:
            result = self.service.get_quality_metrics(limit)

            return create_success_response(
                "Quality metrics retrieved successfully",
                result,
                {"documents_analyzed": len(result["items"])}
            )

        except Exception as e:
            return create_error_response(f"Failed to get quality metrics: {str(e)}", "INTERNAL_ERROR")

    async def handle_get_related_documents(self, correlation_id: str) -> Dict[str, Any]:
        """Handle related documents retrieval."""
        try:
            documents = self.service.get_related_documents(correlation_id)

            return create_success_response(
                "Related documents retrieved successfully",
                {"documents": documents, "correlation_id": correlation_id},
                {"correlation_id": correlation_id, "count": len(documents)}
            )

        except Exception as e:
            return create_error_response(f"Failed to get related documents: {str(e)}", "INTERNAL_ERROR")

    async def handle_delete_document(self, document_id: str) -> Dict[str, Any]:
        """Handle document deletion."""
        try:
            self.service.delete_document(document_id)

            return create_success_response(
                "Document deleted successfully",
                {"document_id": document_id},
                {"document_id": document_id}
            )

        except ValueError as e:
            return create_error_response(str(e), "VALIDATION_ERROR")
        except Exception as e:
            return create_error_response(f"Failed to delete document: {str(e)}", "INTERNAL_ERROR")


# Global instance for backward compatibility
document_handlers = DocumentHandlers()
