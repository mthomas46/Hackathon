"""Document Ingestion Integration for External Service Store.

This module provides integration utilities for the source agent to process
documents and automatically create bidirectional relationships between
documents and services in the external service store.

It demonstrates how document ingestion can be enhanced to automatically
detect and link services mentioned in document content.
"""

import asyncio
import httpx
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class DocumentIngestionRequest:
    """Request model for document ingestion with service relationship enhancement."""
    document_id: str
    content: str
    metadata: Dict[str, Any]
    document_type: str
    source: str  # confluence, jira, github_pr, etc.

    # Optional service hints
    explicit_service_ids: Optional[List[str]] = None
    tags: Optional[List[str]] = None


@dataclass
class DocumentIngestionResult:
    """Result model for document ingestion with relationship creation."""
    document_id: str
    document_stored: bool
    service_relationships_created: int
    detected_services: List[str]
    processing_time_ms: float
    errors: List[str]


class DocumentIngestionIntegrator:
    """Integration service for enhanced document ingestion with service relationships."""

    def __init__(
        self,
        external_service_store_url: str = "http://localhost:8010",
        document_store_url: str = "http://localhost:8002",
        timeout: float = 30.0
    ):
        """Initialize the integration service."""
        self.external_service_store_url = external_service_store_url.rstrip('/')
        self.document_store_url = document_store_url.rstrip('/')
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)

    async def process_document_with_relationships(
        self,
        request: DocumentIngestionRequest
    ) -> DocumentIngestionResult:
        """Process a document and create bidirectional relationships with detected services.

        This method:
        1. Stores the document in the document store
        2. Analyzes document content for service mentions
        3. Creates bidirectional relationships in the external service store
        4. Returns comprehensive processing results

        Args:
            request: Document ingestion request with content and metadata

        Returns:
            DocumentIngestionResult with processing details and relationship info
        """
        start_time = asyncio.get_event_loop().time()
        errors = []

        try:
            # Step 1: Store document in document store
            document_stored = await self._store_document_in_document_store(request)
            if not document_stored:
                errors.append("Failed to store document in document store")
                return DocumentIngestionResult(
                    document_id=request.document_id,
                    document_stored=False,
                    service_relationships_created=0,
                    detected_services=[],
                    processing_time_ms=(asyncio.get_event_loop().time() - start_time) * 1000,
                    errors=errors
                )

            # Step 2: Process document for service relationships
            relationship_result = await self._create_service_relationships(request)

            processing_time = (asyncio.get_event_loop().time() - start_time) * 1000

            return DocumentIngestionResult(
                document_id=request.document_id,
                document_stored=True,
                service_relationships_created=relationship_result.get('relationships_created', 0),
                detected_services=relationship_result.get('service_ids', []),
                processing_time_ms=processing_time,
                errors=errors
            )

        except Exception as e:
            self.logger.error(f"Error processing document {request.document_id}: {str(e)}")
            errors.append(f"Processing error: {str(e)}")

            return DocumentIngestionResult(
                document_id=request.document_id,
                document_stored=False,
                service_relationships_created=0,
                detected_services=[],
                processing_time_ms=(asyncio.get_event_loop().time() - start_time) * 1000,
                errors=errors
            )

    async def _store_document_in_document_store(self, request: DocumentIngestionRequest) -> bool:
        """Store document in the document store."""
        try:
            # Prepare document data for document store
            doc_data = {
                "id": request.document_id,
                "content": request.content,
                "metadata": request.metadata,
                "source": request.source,
                "document_type": request.document_type,
                "tags": request.tags or []
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # This would be the actual document store endpoint
                # For now, we'll simulate the call
                self.logger.info(f"Would store document {request.document_id} in document store")
                return True  # Simulate successful storage

        except Exception as e:
            self.logger.error(f"Error storing document {request.document_id}: {str(e)}")
            return False

    async def _create_service_relationships(self, request: DocumentIngestionRequest) -> Dict[str, Any]:
        """Create bidirectional relationships between document and detected services."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Call the external service store to process relationships
                url = f"{self.external_service_store_url}/documents/{request.document_id}/process-relationships"

                # Prepare form data
                form_data = {
                    "content": request.content,
                    "metadata": json.dumps(request.metadata),
                    "document_type": request.document_type
                }

                response = await client.post(url, data=form_data)
                response.raise_for_status()

                result = response.json()
                self.logger.info(f"Created {result.get('relationships_created', 0)} service relationships for document {request.document_id}")

                return result

        except httpx.HTTPError as e:
            self.logger.error(f"HTTP error creating service relationships: {str(e)}")
            return {"relationships_created": 0, "service_ids": [], "errors": [str(e)]}
        except Exception as e:
            self.logger.error(f"Error creating service relationships: {str(e)}")
            return {"relationships_created": 0, "service_ids": [], "errors": [str(e)]}

    async def bulk_process_documents(
        self,
        documents: List[DocumentIngestionRequest],
        batch_size: int = 10
    ) -> List[DocumentIngestionResult]:
        """Process multiple documents in batches for better performance."""
        results = []

        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]

            # Process batch concurrently
            tasks = [self.process_document_with_relationships(doc) for doc in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in batch_results:
                if isinstance(result, Exception):
                    # Handle exceptions in batch processing
                    self.logger.error(f"Batch processing error: {str(result)}")
                    # Create error result for failed document
                    error_result = DocumentIngestionResult(
                        document_id="unknown",
                        document_stored=False,
                        service_relationships_created=0,
                        detected_services=[],
                        processing_time_ms=0,
                        errors=[str(result)]
                    )
                    results.append(error_result)
                else:
                    results.append(result)

        return results

    async def get_document_service_relationships(self, document_id: str) -> Dict[str, Any]:
        """Get all service relationships for a document."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                url = f"{self.external_service_store_url}/documents/{document_id}/services"
                response = await client.get(url)
                response.raise_for_status()
                return response.json()

        except httpx.HTTPError as e:
            self.logger.error(f"Error getting document relationships: {str(e)}")
            return {"document_id": document_id, "services": [], "total": 0, "error": str(e)}

    async def sync_document_service_relationships(
        self,
        document_id: str,
        service_ids: List[str],
        document_type: str = "unknown"
    ) -> Dict[str, Any]:
        """Manually synchronize relationships between a document and services."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                url = f"{self.external_service_store_url}/documents/{document_id}/sync-relationships"

                form_data = {
                    "service_ids": ",".join(service_ids),
                    "document_type": document_type,
                    "relationship_type": "reference"
                }

                response = await client.post(url, data=form_data)
                response.raise_for_status()
                return response.json()

        except httpx.HTTPError as e:
            self.logger.error(f"Error syncing relationships: {str(e)}")
            return {"error": str(e)}

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on both services."""
        health_results = {
            "external_service_store": {"status": "unknown", "response_time_ms": 0},
            "document_store": {"status": "unknown", "response_time_ms": 0},
            "relationship_health": {"status": "unknown"}
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Check external service store
                start_time = asyncio.get_event_loop().time()
                response = await client.get(f"{self.external_service_store_url}/health")
                response_time = (asyncio.get_event_loop().time() - start_time) * 1000

                if response.status_code == 200:
                    health_results["external_service_store"] = {
                        "status": "healthy",
                        "response_time_ms": response_time
                    }
                else:
                    health_results["external_service_store"] = {
                        "status": "unhealthy",
                        "response_time_ms": response_time,
                        "error": f"Status code: {response.status_code}"
                    }

                # Check document store
                start_time = asyncio.get_event_loop().time()
                response = await client.get(f"{self.document_store_url}/health")
                response_time = (asyncio.get_event_loop().time() - start_time) * 1000

                if response.status_code == 200:
                    health_results["document_store"] = {
                        "status": "healthy",
                        "response_time_ms": response_time
                    }
                else:
                    health_results["document_store"] = {
                        "status": "unhealthy",
                        "response_time_ms": response_time,
                        "error": f"Status code: {response.status_code}"
                    }

                # Check relationship health
                response = await client.get(f"{self.external_service_store_url}/relationships/health")
                if response.status_code == 200:
                    health_data = response.json()
                    health_results["relationship_health"] = {
                        "status": "healthy",
                        "total_services": health_data.get("total_services", 0),
                        "total_relationships": health_data.get("total_document_relationships", 0),
                        "health_score": health_data.get("health_score", 0)
                    }
                else:
                    health_results["relationship_health"] = {
                        "status": "unhealthy",
                        "error": f"Status code: {response.status_code}"
                    }

        except Exception as e:
            self.logger.error(f"Health check error: {str(e)}")
            health_results["error"] = str(e)

        return health_results


# Example usage and integration point for source agent
async def example_document_ingestion():
    """Example of how the source agent would use the integration service."""

    integrator = DocumentIngestionIntegrator()

    # Example document from Confluence
    document_request = DocumentIngestionRequest(
        document_id="confluence:API_DOCS:USER_STORE",
        content="""
        # User Store API Documentation

        The User Store service provides comprehensive user management capabilities
        for the LLM Documentation Ecosystem.

        ## Service Dependencies

        The User Store depends on the following services:
        - document-store: For storing user profile documents
        - notification-service: For sending user notifications
        - external-service-store: For service registry integration

        ## API Endpoints

        ### GET /users
        Retrieve a list of users with optional filtering.

        ### POST /users
        Create a new user in the system.

        ## Configuration

        The service uses SQLite for data persistence and FastAPI for the web framework.
        """,
        metadata={
            "title": "User Store API Documentation",
            "author": "Dev Team",
            "last_modified": "2024-01-15",
            "space": "API Documentation",
            "labels": ["api", "documentation", "user-store"]
        },
        document_type="confluence",
        source="confluence",
        tags=["api", "documentation", "user-store", "user-management"]
    )

    # Process the document
    result = await integrator.process_document_with_relationships(document_request)

    print("Document Ingestion Result:")
    print(f"- Document ID: {result.document_id}")
    print(f"- Document Stored: {result.document_stored}")
    print(f"- Service Relationships Created: {result.service_relationships_created}")
    print(f"- Detected Services: {result.detected_services}")
    print(".2f")
    if result.errors:
        print(f"- Errors: {result.errors}")

    # Check the relationships that were created
    if result.service_relationships_created > 0:
        relationships = await integrator.get_document_service_relationships(result.document_id)
        print(f"\nCreated relationships: {relationships}")


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)

    # Run example
    asyncio.run(example_document_ingestion())

