"""Document handlers for API endpoints.

Handles HTTP requests and responses for document operations.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from fastapi import HTTPException

from ...presentation.dto.models import (
    DocumentListResponse,
    DocumentRequest,
    DocumentResponse,
    MetadataUpdateRequest,
    QualityResponse,
    SearchRequest,
    SearchResponse,
)
from ...domain.exceptions import (
    DocumentNotFoundException,
    DocumentValidationException,
    DocumentSizeExceededException,
)
from .service import DocumentService


class AbstractDocumentHandlers(ABC):
    """Abstract base class for document handlers - enables dependency injection."""

    @abstractmethod
    async def handle_create_document(
        self, request: DocumentRequest
    ) -> DocumentResponse:
        """Handle document creation."""
        pass

    @abstractmethod
    async def handle_get_document(self, document_id: str) -> DocumentResponse:
        """Handle document retrieval."""
        pass

    @abstractmethod
    async def handle_list_documents(
        self, limit: int = 10, offset: int = 0
    ) -> DocumentListResponse:
        """Handle document listing."""
        pass

    @abstractmethod
    async def handle_update_metadata(
        self, document_id: str, request: MetadataUpdateRequest
    ) -> DocumentResponse:
        """Handle metadata updates."""
        pass

    @abstractmethod
    async def handle_delete_document(self, document_id: str) -> Dict[str, Any]:
        """Handle document deletion."""
        pass

    @abstractmethod
    async def handle_search_documents(self, request: SearchRequest) -> SearchResponse:
        """Handle document search."""
        pass

    @abstractmethod
    async def handle_get_quality_metrics(self, limit: int = 10) -> QualityResponse:
        """Handle quality metrics retrieval."""
        pass


class DocumentHandlers(AbstractDocumentHandlers):
    """Handlers for document API endpoints with dependency injection."""

    def __init__(self, service: Optional[DocumentService] = None):
        """Initialize with injected service dependency."""
        self.service = service or DocumentService()

    async def handle_create_document(
        self, request: DocumentRequest
    ) -> DocumentResponse:
        """Handle document creation."""
        try:
            # Validate input
            if not request.content or not request.content.strip():
                raise DocumentValidationException(
                    "Document content cannot be empty",
                    ["content"]
                )

            # Check document size (example: 10MB limit)
            content_size = len(request.content.encode('utf-8'))
            max_size = 10 * 1024 * 1024  # 10MB
            if content_size > max_size:
                raise DocumentSizeExceededException(content_size, max_size)

            # Process metadata
            metadata = request.metadata if isinstance(request.metadata, dict) else {}
            
            # Process tags (extract from request)
            tags = request.tags if hasattr(request, 'tags') and request.tags is not None else []
            
            # 🔍 DEBUG: Write to file for visibility
            with open("/tmp/tags_debug.log", "a") as f:
                f.write(f"[{request.id}] request.tags: {getattr(request, 'tags', 'NO ATTR')}\n")
                f.write(f"[{request.id}] processed tags: {tags}\n")
                f.flush()
            
            # 🔍 DEBUG: Print tags (CRITICAL FIX LOCATION)
            print(f"[TAGS DEBUG] DOMAIN Handler - request.tags: {getattr(request, 'tags', 'NO ATTR')}", flush=True)
            print(f"[TAGS DEBUG] DOMAIN Handler - processed tags: {tags}", flush=True)

            # Create document using BaseService.create() method
            document = await self.service.create({
                "id": request.id,
                "content": request.content,
                "metadata": metadata,
                "tags": tags,  # ✅ CRITICAL FIX: Pass tags to service!
                "correlation_id": request.correlation_id,
            })
            
            # 🔍 DEBUG: Write to file after creation
            with open("/tmp/tags_debug.log", "a") as f:
                f.write(f"[{request.id}] document.tags after create: {document.tags}\n")
                f.flush()
            
            # 🔍 DEBUG: Print document after creation
            print(f"[TAGS DEBUG] Document created - tags: {document.tags}", flush=True)

            # Return direct DocumentResponse without wrapper
            return DocumentResponse(
                id=document.id,
                content=document.content,
                content_hash=document.content_hash,
                metadata=document.metadata,
                tags=document.tags,  # ✅ CRITICAL FIX: Include tags in response
                created_at=document.created_at.isoformat(),
            )

        except DocumentValidationException:
            raise  # Let global exception handler deal with it
        except DocumentSizeExceededException:
            raise  # Let global exception handler deal with it
        except ValueError as e:
            raise DocumentValidationException(str(e))
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to create document: {str(e)}"
            )

    async def handle_get_document(self, document_id: str) -> DocumentResponse:
        """Handle document retrieval."""
        try:
            document = self.service.get_entity(document_id)
            if not document:
                raise DocumentNotFoundException(document_id)

            return DocumentResponse(
                id=document.id,
                content=document.content,
                content_hash=document.content_hash,
                metadata=document.metadata,
                tags=document.tags,  # ✅ CRITICAL FIX: Include tags in response
                created_at=document.created_at.isoformat(),
            )

        except DocumentNotFoundException:
            raise  # Let the global exception handler deal with it
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to retrieve document: {str(e)}"
            )

    async def handle_list_documents(
        self, limit: int = 50, offset: int = 0
    ) -> DocumentListResponse:
        """Handle document listing."""
        try:
            result = await self.service.list_entities(limit, offset)

            # Return DocumentListResponse directly
            return DocumentListResponse(
                items=result.get("items", []),
                total=result.get("total", 0),
                has_more=result.get("has_more", False),
            )

        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to list documents: {str(e)}"
            )

    async def handle_update_metadata(
        self, document_id: str, request: MetadataUpdateRequest
    ) -> Dict[str, Any]:
        """Handle metadata updates."""
        try:
            self.service.update_entity(document_id, {"metadata": request.metadata})

            # Return simple success response
            return {
                "success": True,
                "message": "Document metadata updated successfully",
                "document_id": document_id,
            }

        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to update metadata: {str(e)}"
            )

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
            raise HTTPException(
                status_code=500, detail=f"Failed to search documents: {str(e)}"
            )

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
            raise HTTPException(
                status_code=500, detail=f"Failed to get quality metrics: {str(e)}"
            )

    async def handle_get_related_documents(self, correlation_id: str) -> Dict[str, Any]:
        """Handle related documents retrieval."""
        try:
            documents = self.service.get_related_documents(correlation_id)

            return {
                "success": True,
                "documents": documents,
                "correlation_id": correlation_id,
                "count": len(documents),
            }

        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to get related documents: {str(e)}"
            )

    async def handle_delete_document(self, document_id: str) -> Dict[str, Any]:
        """Handle document deletion."""
        try:
            self.service.delete_entity(document_id)

            return {
                "success": True,
                "message": "Document deleted successfully",
                "document_id": document_id,
            }

        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to delete document: {str(e)}"
            )


# Global instance for backward compatibility
document_handlers = DocumentHandlers()
