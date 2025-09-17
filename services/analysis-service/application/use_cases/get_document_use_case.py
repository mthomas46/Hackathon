"""Get Document Use Case."""

from typing import Optional
from dataclasses import dataclass

from ...domain.entities import Document
from ...domain.exceptions import DocumentNotFoundException
from ...infrastructure.repositories import DocumentRepository
from ..dto import GetDocumentsRequest, DocumentResponse, DocumentListResponse


@dataclass
class GetDocumentQuery:
    """Query for getting a single document."""
    document_id: str


@dataclass
class GetDocumentsQuery:
    """Query for getting multiple documents."""
    author: Optional[str] = None
    tags: Optional[list] = None
    repository_id: Optional[str] = None
    limit: int = 50
    offset: int = 0


@dataclass
class DocumentQueryResult:
    """Result of document query."""
    documents: list[Document]
    total_count: int
    has_more: bool


class GetDocumentUseCase:
    """Use case for retrieving documents."""

    def __init__(self, document_repository: DocumentRepository):
        """Initialize use case with dependencies."""
        self.document_repository = document_repository

    async def get_by_id(self, query: GetDocumentQuery) -> Document:
        """Get a single document by ID."""
        document = await self.document_repository.get_by_id(query.document_id)
        if not document:
            raise DocumentNotFoundException(query.document_id)
        return document

    async def get_list(self, query: GetDocumentsQuery) -> DocumentQueryResult:
        """Get a list of documents with filtering."""
        # Get all documents (in a real implementation, this would be filtered in the repository)
        all_documents = await self.document_repository.get_all()

        # Apply filters
        filtered_documents = self._apply_filters(all_documents, query)

        # Apply pagination
        total_count = len(filtered_documents)
        start_idx = query.offset
        end_idx = start_idx + query.limit
        paginated_documents = filtered_documents[start_idx:end_idx]

        has_more = end_idx < total_count

        return DocumentQueryResult(
            documents=paginated_documents,
            total_count=total_count,
            has_more=has_more
        )

    def _apply_filters(self, documents: list[Document], query: GetDocumentsQuery) -> list[Document]:
        """Apply filters to document list."""
        filtered = documents

        if query.author:
            filtered = [d for d in filtered if d.metadata.author and
                       query.author.lower() in d.metadata.author.lower()]

        if query.tags:
            filtered = [d for d in filtered if any(tag in d.metadata.tags for tag in query.tags)]

        if query.repository_id:
            filtered = [d for d in filtered if d.repository_id == query.repository_id]

        return filtered

    def to_response(self, document: Document) -> DocumentResponse:
        """Convert document to response DTO."""
        return DocumentResponse.from_domain(document)

    def to_list_response(self, result: DocumentQueryResult, query: GetDocumentsQuery) -> DocumentListResponse:
        """Convert query result to list response DTO."""
        document_responses = [DocumentResponse.from_domain(doc) for doc in result.documents]

        filters = {
            'author': query.author,
            'tags': query.tags,
            'repository_id': query.repository_id
        }

        return DocumentListResponse.create(
            documents=document_responses,
            total=result.total_count,
            page=(query.offset // query.limit) + 1,
            page_size=query.limit,
            filters=filters
        )
