"""Document handlers for API endpoints.

Handles HTTP requests and responses for document operations.
"""

import time
from typing import Any, Dict, Optional

from fastapi import HTTPException

from services.shared.core.constants_new import ServiceNames
from services.shared.core.responses.responses import create_error_response, create_success_response
from services.shared.utilities import utc_now
from services.shared.utilities.logging_client import get_log_collector_client

from ...core.models import (
    DocumentListResponse,
    DocumentRequest,
    DocumentResponse,
    MetadataUpdateRequest,
    QualityResponse,
    SearchRequest,
    SearchResponse,
)
from .service import DocumentService

# Global logger client instance
logger_client = None


async def get_logger_client():
    """Get or initialize the logger client."""
    global logger_client
    if logger_client is None:
        try:
            logger_client = await get_log_collector_client(ServiceNames.DOC_STORE)
        except Exception:
            pass  # Fallback to no logging if client unavailable
    return logger_client


class DocumentHandlers:
    """Handlers for document API endpoints."""

    def __init__(self):
        self.service = DocumentService()

    async def handle_create_document(self, request: DocumentRequest) -> DocumentResponse:
        """Handle document creation."""
        start_time = time.time()
        request_id = f"doc_create_{int(time.time() * 1000)}"
        logger = await get_logger_client()

        try:
            # Process metadata
            metadata = request.metadata if isinstance(request.metadata, dict) else {}

            # Log document creation start
            if logger:
                await logger.log_business_event(
                    "document_creation_started",
                    {
                        "request_id": request_id,
                        "content_type": request.content_type,
                        "content_length": len(request.content) if request.content else 0,
                        "has_metadata": bool(metadata),
                        "metadata_keys": list(metadata.keys()) if metadata else [],
                        "has_tags": bool(request.tags),
                    },
                )

                await logger.log_info(
                    "Creating new document",
                    {
                        "request_id": request_id,
                        "content_type": request.content_type,
                        "content_length": len(request.content) if request.content else 0,
                        "metadata_count": len(metadata),
                    },
                )

            # Create document
            document = self.service.create_document(
                content=request.content,
                metadata=metadata,
                document_id=request.id,
                correlation_id=request.correlation_id,
            )

            # Calculate response time
            response_time = time.time() - start_time

            # Log successful creation
            if logger:
                await logger.log_business_event(
                    "document_created",
                    {
                        "request_id": request_id,
                        "document_id": document.id,
                        "content_type": request.content_type,
                        "content_length": len(document.content) if document.content else 0,
                        "response_time_seconds": response_time,
                        "success": True,
                    },
                )

                await logger.log_performance_metric(
                    "document_creation",
                    response_time,
                    {
                        "request_id": request_id,
                        "document_id": document.id,
                        "content_type": request.content_type,
                        "creation_success": True,
                    },
                )

            # Return direct DocumentResponse without wrapper
            return DocumentResponse(
                id=document.id,
                content=document.content,
                content_hash=document.content_hash,
                metadata=document.metadata,
                created_at=document.created_at.isoformat(),
            )

        except ValueError as e:
            error_time = time.time() - start_time

            # Log validation error
            if logger:
                await logger.log_error(
                    f"Document creation validation failed: {str(e)}",
                    {
                        "request_id": request_id,
                        "content_type": request.content_type,
                        "error_type": "validation_error",
                        "response_time_seconds": error_time,
                    },
                    error=e,
                )

                await logger.log_business_event(
                    "document_creation_validation_failed",
                    {
                        "request_id": request_id,
                        "content_type": request.content_type,
                        "error_message": str(e),
                        "response_time_seconds": error_time,
                    },
                )

            raise HTTPException(status_code=400, detail=str(e))

        except Exception as e:
            error_time = time.time() - start_time

            # Log internal error
            if logger:
                await logger.log_error(
                    f"Document creation failed: {str(e)}",
                    {
                        "request_id": request_id,
                        "content_type": request.content_type,
                        "error_type": type(e).__name__,
                        "response_time_seconds": error_time,
                    },
                    error=e,
                )

                await logger.log_business_event(
                    "document_creation_failed",
                    {
                        "request_id": request_id,
                        "content_type": request.content_type,
                        "error_type": type(e).__name__,
                        "error_message": str(e),
                        "response_time_seconds": error_time,
                    },
                )

            raise HTTPException(status_code=500, detail=f"Failed to create document: {str(e)}")

    async def handle_get_document(self, document_id: str) -> DocumentResponse:
        """Handle document retrieval."""
        try:
            document = self.service.get_entity(document_id)
            if not document:
                raise HTTPException(status_code=404, detail=f"Document {document_id} not found")

            return DocumentResponse(
                id=document.id,
                content=document.content,
                content_hash=document.content_hash,
                metadata=document.metadata,
                created_at=document.created_at.isoformat(),
            )

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to retrieve document: {str(e)}")

    async def handle_list_documents(self, limit: int = 50, offset: int = 0) -> DocumentListResponse:
        """Handle document listing."""
        try:
            result = self.service.list_entities(limit, offset)

            # Return DocumentListResponse directly
            return DocumentListResponse(
                items=result.get("items", []), total=result.get("total", 0), has_more=result.get("has_more", False)
            )

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")

    async def handle_update_metadata(self, document_id: str, request: MetadataUpdateRequest) -> Dict[str, Any]:
        """Handle metadata updates."""
        try:
            self.service.update_entity(document_id, {"metadata": request.metadata})

            # Return simple success response
            return {"success": True, "message": "Document metadata updated successfully", "document_id": document_id}

        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to update metadata: {str(e)}")

    async def handle_search_documents(self, request: SearchRequest) -> SearchResponse:
        """Handle document search."""
        try:
            result = self.service.search_documents(request.query, request.limit or 50)

            return SearchResponse(
                query=request.query,
                items=result["items"],
                total=result["total"],
                has_more=result["has_more"],
                search_time=result.get("search_time", 0.0),
            )

        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to search documents: {str(e)}")

    async def handle_get_quality_metrics(self, limit: int = 1000) -> QualityResponse:
        """Handle quality metrics retrieval."""
        try:
            result = self.service.get_quality_metrics(limit)

            return QualityResponse(
                total_documents=result["total_documents"],
                average_quality_score=result["average_quality_score"],
                quality_distribution=result["quality_distribution"],
                items=result["items"],
            )

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get quality metrics: {str(e)}")

    async def handle_get_related_documents(self, correlation_id: str) -> Dict[str, Any]:
        """Handle related documents retrieval."""
        try:
            documents = self.service.get_related_documents(correlation_id)

            return {"success": True, "documents": documents, "correlation_id": correlation_id, "count": len(documents)}

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get related documents: {str(e)}")

    async def handle_delete_document(self, document_id: str) -> Dict[str, Any]:
        """Handle document deletion."""
        try:
            self.service.delete_entity(document_id)

            return {"success": True, "message": "Document deleted successfully", "document_id": document_id}

        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")


# Global instance for backward compatibility
document_handlers = DocumentHandlers()
