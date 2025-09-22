"""Document Store Client - Client for Document Store Service.

This module provides a client for interacting with the Document Store service,
enabling browsing, uploading, and management of documents with advanced features.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
from infrastructure.config.config import get_config


class DocumentStoreClient:
    """Client for interacting with the Document Store service."""

    def __init__(self, base_url: Optional[str] = None, timeout: float = 30.0):
        """Initialize the document store client.

        Args:
            base_url: Base URL of the Document Store service
            timeout: Request timeout in seconds
        """
        self.config = get_config()
        self.base_url = base_url or self.config.document_service.base_url
        self.timeout = timeout

        # HTTP client setup
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
            headers={"Content-Type": "application/json", "User-Agent": "DataServicesDashboard/1.0"},
        )

        # Logging
        self.logger = logging.getLogger(__name__)

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def create_document(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new document."""
        try:
            response = await self.client.post("/api/v1/documents", json=request)
            return response.json()
        except Exception as e:
            self.logger.error(f"Failed to create document: {e}")
            return {"success": False, "error": str(e)}

    async def list_documents(
        self, skip: int = 0, limit: int = 50, search: Optional[str] = None, **filters
    ) -> Dict[str, Any]:
        """List documents with optional filtering."""
        try:
            params = {"skip": skip, "limit": limit}
            if search:
                params["search"] = search

            # Add any additional filters
            params.update(filters)

            response = await self.client.get("/api/v1/documents", params=params)
            return response.json()
        except Exception as e:
            self.logger.error(f"Failed to list documents: {e}")
            return {"success": False, "error": str(e), "documents": []}

    async def get_document(self, document_id: str) -> Dict[str, Any]:
        """Get a specific document by ID."""
        try:
            response = await self.client.get(f"/api/v1/documents/{document_id}")
            return response.json()
        except Exception as e:
            self.logger.error(f"Failed to get document {document_id}: {e}")
            return {"success": False, "error": str(e)}

    async def update_document(self, document_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update document metadata."""
        try:
            response = await self.client.put(f"/api/v1/documents/{document_id}", json=updates)
            return response.json()
        except Exception as e:
            self.logger.error(f"Failed to update document {document_id}: {e}")
            return {"success": False, "error": str(e)}

    async def delete_document(self, document_id: str) -> Dict[str, Any]:
        """Delete a document."""
        try:
            response = await self.client.delete(f"/api/v1/documents/{document_id}")
            return response.json() if response.status_code != 204 else {"success": True}
        except Exception as e:
            self.logger.error(f"Failed to delete document {document_id}: {e}")
            return {"success": False, "error": str(e)}

    async def search_documents(self, query: str, **filters) -> Dict[str, Any]:
        """Search documents using advanced search."""
        try:
            search_request = {"query": query, **filters}
            response = await self.client.post("/api/v1/documents/search", json=search_request)
            return response.json()
        except Exception as e:
            self.logger.error(f"Failed to search documents: {e}")
            return {"success": False, "error": str(e), "results": []}

    async def get_document_content(self, document_id: str) -> Dict[str, Any]:
        """Get document content."""
        try:
            response = await self.client.get(f"/api/v1/documents/{document_id}/content")
            return response.json()
        except Exception as e:
            self.logger.error(f"Failed to get content for document {document_id}: {e}")
            return {"success": False, "error": str(e)}

    async def get_document_quality(self, document_id: str) -> Dict[str, Any]:
        """Get document quality metrics."""
        try:
            response = await self.client.get(f"/api/v1/documents/{document_id}/quality")
            return response.json()
        except Exception as e:
            self.logger.error(f"Failed to get quality for document {document_id}: {e}")
            return {"success": False, "error": str(e)}

    async def add_document_tags(self, document_id: str, tags: List[str]) -> Dict[str, Any]:
        """Add tags to a document."""
        try:
            response = await self.client.post(f"/api/v1/documents/{document_id}/tags", json={"tags": tags})
            return response.json()
        except Exception as e:
            self.logger.error(f"Failed to add tags to document {document_id}: {e}")
            return {"success": False, "error": str(e)}

    async def remove_document_tags(self, document_id: str, tags: List[str]) -> Dict[str, Any]:
        """Remove tags from a document."""
        try:
            response = await self.client.delete(f"/api/v1/documents/{document_id}/tags", json={"tags": tags})
            return response.json()
        except Exception as e:
            self.logger.error(f"Failed to remove tags from document {document_id}: {e}")
            return {"success": False, "error": str(e)}

    async def get_document_tags(self, document_id: str) -> Dict[str, Any]:
        """Get tags for a document."""
        try:
            response = await self.client.get(f"/api/v1/documents/{document_id}/tags")
            return response.json()
        except Exception as e:
            self.logger.error(f"Failed to get tags for document {document_id}: {e}")
            return {"success": False, "error": str(e), "tags": []}

    async def get_document_version(self, document_id: str, version: int) -> Dict[str, Any]:
        """Get a specific version of a document."""
        try:
            response = await self.client.get(f"/api/v1/documents/{document_id}/versions/{version}")
            return response.json()
        except Exception as e:
            self.logger.error(f"Failed to get version {version} of document {document_id}: {e}")
            return {"success": False, "error": str(e)}

    async def list_document_versions(self, document_id: str) -> Dict[str, Any]:
        """List all versions of a document."""
        try:
            response = await self.client.get(f"/api/v1/documents/{document_id}/versions")
            return response.json()
        except Exception as e:
            self.logger.error(f"Failed to list versions for document {document_id}: {e}")
            return {"success": False, "error": str(e), "versions": []}

    async def restore_document_version(self, document_id: str, version: int) -> Dict[str, Any]:
        """Restore a document to a specific version."""
        try:
            response = await self.client.post(f"/api/v1/documents/{document_id}/versions/{version}/restore")
            return response.json()
        except Exception as e:
            self.logger.error(f"Failed to restore document {document_id} to version {version}: {e}")
            return {"success": False, "error": str(e)}

    async def get_document_relationships(self, document_id: str) -> Dict[str, Any]:
        """Get relationships for a document."""
        try:
            response = await self.client.get(f"/api/v1/documents/{document_id}/relationships")
            return response.json()
        except Exception as e:
            self.logger.error(f"Failed to get relationships for document {document_id}: {e}")
            return {"success": False, "error": str(e), "relationships": []}

    async def add_document_relationship(
        self, document_id: str, target_id: str, relationship_type: str
    ) -> Dict[str, Any]:
        """Add a relationship between documents."""
        try:
            request_data = {"target_id": target_id, "relationship_type": relationship_type}
            response = await self.client.post(f"/api/v1/documents/{document_id}/relationships", json=request_data)
            return response.json()
        except Exception as e:
            self.logger.error(f"Failed to add relationship to document {document_id}: {e}")
            return {"success": False, "error": str(e)}

    async def get_document_analytics(self) -> Dict[str, Any]:
        """Get document analytics."""
        try:
            response = await self.client.get("/api/v1/analytics/documents")
            return response.json()
        except Exception as e:
            self.logger.error(f"Failed to get document analytics: {e}")
            return {"success": False, "error": str(e)}

    async def get_document_lifecycle(self, document_id: str) -> Dict[str, Any]:
        """Get document lifecycle information."""
        try:
            response = await self.client.get(f"/api/v1/documents/{document_id}/lifecycle")
            return response.json()
        except Exception as e:
            self.logger.error(f"Failed to get lifecycle for document {document_id}: {e}")
            return {"success": False, "error": str(e)}

    async def update_document_lifecycle(self, document_id: str, action: str, **params) -> Dict[str, Any]:
        """Update document lifecycle."""
        try:
            request_data = {"action": action, **params}
            response = await self.client.put(f"/api/v1/documents/{document_id}/lifecycle", json=request_data)
            return response.json()
        except Exception as e:
            self.logger.error(f"Failed to update lifecycle for document {document_id}: {e}")
            return {"success": False, "error": str(e)}

    async def bulk_document_operation(self, operation: str, document_ids: List[str], **params) -> Dict[str, Any]:
        """Perform bulk operations on documents."""
        try:
            request_data = {"operation": operation, "document_ids": document_ids, **params}
            response = await self.client.post("/api/v1/bulk/documents", json=request_data)
            return response.json()
        except Exception as e:
            self.logger.error(f"Failed to perform bulk operation {operation}: {e}")
            return {"success": False, "error": str(e)}

    def format_document_for_display(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Format a document for display in the dashboard."""
        return {
            "id": document.get("id", ""),
            "title": document.get("title", ""),
            "content_type": document.get("content_type", ""),
            "size": document.get("size", 0),
            "tags": document.get("tags", []),
            "metadata": document.get("metadata", {}),
            "quality_score": document.get("quality_score", 0.0),
            "created_at": document.get("created_at", ""),
            "updated_at": document.get("updated_at", ""),
            "version": document.get("version", 1),
            "lifecycle_status": document.get("lifecycle_status", "active"),
            "content_preview": (
                document.get("content", "")[:300] + "..."
                if len(document.get("content", "")) > 300
                else document.get("content", "")
            ),
            "content_full": document.get("content", ""),
        }
