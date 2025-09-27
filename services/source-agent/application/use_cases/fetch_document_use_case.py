"""Fetch document use case."""

from typing import Dict, Any, Optional
from dataclasses import dataclass

from ...domain.entities.document import Document
from ...domain.entities.ingestion_result import IngestionResult
from ...domain.services.intelligent_ingestion import IntelligentIngestionService
from ...domain.services.fetch_handler import FetchHandler


@dataclass
class FetchDocumentRequest:
    """Request DTO for fetching documents."""
    source_type: str
    source_id: str
    scope: Optional[Dict[str, Any]] = None
    include_metadata: bool = True
    timeout_seconds: int = 300


@dataclass
class FetchDocumentResponse:
    """Response DTO for document fetching."""
    success: bool
    documents: list[Document]
    ingestion_result: IngestionResult
    message: str
    processing_time_seconds: float


class FetchDocumentUseCase:
    """Use case for fetching documents from source systems.

    Orchestrates the process of connecting to source systems,
    fetching documents, and processing them for ingestion.
    """

    def __init__(
        self,
        fetch_handler: FetchHandler,
        intelligent_ingestion_service: IntelligentIngestionService
    ):
        """Initialize use case with dependencies."""
        self._fetch_handler = fetch_handler
        self._intelligent_ingestion_service = intelligent_ingestion_service

    async def execute(self, request: FetchDocumentRequest) -> FetchDocumentResponse:
        """Execute the fetch document use case.

        Args:
            request: The fetch document request

        Returns:
            Response containing fetched documents and processing results
        """
        import time
        start_time = time.time()

        try:
            # Create ingestion result to track the operation
            ingestion_result = IngestionResult(
                source_id=request.source_id,
                source_type=request.source_type,
                operation_type="fetch"
            )

            # Fetch documents from the source
            documents_data = await self._fetch_handler.fetch_documents(
                source_type=request.source_type,
                source_id=request.source_id,
                scope=request.scope,
                timeout=request.timeout_seconds
            )

            documents = []
            for doc_data in documents_data:
                try:
                    # Create domain document entity
                    document = Document(
                        source_type=request.source_type,
                        source_id=request.source_id,
                        title=doc_data.get("title", ""),
                        content=doc_data.get("content", ""),
                        metadata=doc_data.get("metadata", {}) if request.include_metadata else {},
                        tags=doc_data.get("tags", []),
                        version=doc_data.get("version"),
                        author=doc_data.get("author")
                    )

                    documents.append(document)
                    ingestion_result.record_success(document.id, len(document.content))

                except Exception as e:
                    ingestion_result.record_failure(
                        doc_data.get("id", "unknown"),
                        f"Failed to create document entity: {str(e)}"
                    )

            # Process documents with intelligent ingestion if needed
            if documents:
                try:
                    processed_docs = await self._intelligent_ingestion_service.process_documents(
                        documents, ingestion_result
                    )
                    documents = processed_docs
                except Exception as e:
                    ingestion_result.add_warning(f"Intelligent processing failed: {str(e)}")

            # Complete the operation
            ingestion_result.complete_successfully()

            processing_time = time.time() - start_time

            return FetchDocumentResponse(
                success=True,
                documents=documents,
                ingestion_result=ingestion_result,
                message=f"Successfully fetched {len(documents)} documents from {request.source_type}",
                processing_time_seconds=processing_time
            )

        except Exception as e:
            processing_time = time.time() - start_time

            # Create failed ingestion result
            ingestion_result = IngestionResult(
                source_id=request.source_id,
                source_type=request.source_type,
                operation_type="fetch"
            )
            ingestion_result.complete_with_failure(str(e))

            return FetchDocumentResponse(
                success=False,
                documents=[],
                ingestion_result=ingestion_result,
                message=f"Failed to fetch documents: {str(e)}",
                processing_time_seconds=processing_time
            )
