"""Document handlers for API endpoints.

Handles HTTP requests and responses for document operations.
"""
from typing import Dict, Any, Optional
from fastapi import HTTPException
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

    async def handle_create_document(self, request: DocumentRequest) -> DocumentResponse:
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

            # Return direct DocumentResponse without wrapper
            return DocumentResponse(
                id=document.id,
                content=document.content,
                content_hash=document.content_hash,
                metadata=document.metadata,
                created_at=document.created_at.isoformat()
            )

        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
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
                created_at=document.created_at.isoformat()
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
                items=result.get("items", []),
                total=result.get("total", 0),
                has_more=result.get("has_more", False)
            )

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")

    async def handle_update_metadata(self, document_id: str, request: MetadataUpdateRequest) -> Dict[str, Any]:
        """Handle metadata updates."""
        try:
            self.service.update_entity(document_id, {"metadata": request.metadata})

            # Return simple success response
            return {
                "success": True,
                "message": "Document metadata updated successfully",
                "document_id": document_id
            }

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
                search_time=result.get("search_time", 0.0)
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
                items=result["items"]
            )

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get quality metrics: {str(e)}")

    async def handle_get_related_documents(self, correlation_id: str) -> Dict[str, Any]:
        """Handle related documents retrieval."""
        try:
            documents = self.service.get_related_documents(correlation_id)

            return {
                "success": True,
                "documents": documents,
                "correlation_id": correlation_id,
                "count": len(documents)
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get related documents: {str(e)}")

    async def handle_delete_document(self, document_id: str) -> Dict[str, Any]:
        """Handle document deletion."""
        try:
            self.service.delete_entity(document_id)

            return {
                "success": True,
                "message": "Document deleted successfully",
                "document_id": document_id
            }

        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")


# Global instance for backward compatibility
document_handlers = DocumentHandlers()
