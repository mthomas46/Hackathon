"""Create Document Use Case."""

from typing import Optional
from dataclasses import dataclass

from ...domain.entities import Document, DocumentId
from ...domain.services import DocumentService
from ...domain.factories import DocumentFactory
from ...domain.validation import DocumentValidator
from ...domain.exceptions import DocumentValidationException
from ...infrastructure.repositories import DocumentRepository
from ..dto import CreateDocumentRequest, DocumentResponse


@dataclass
class CreateDocumentCommand:
    """Command for creating a document."""
    title: str
    content: str
    format: str = "markdown"
    author: Optional[str] = None
    tags: Optional[list] = None
    repository_id: Optional[str] = None


@dataclass
class CreateDocumentResult:
    """Result of document creation."""
    document: Document
    is_valid: bool
    validation_errors: list[str]


class CreateDocumentUseCase:
    """Use case for creating documents."""

    def __init__(self,
                 document_service: DocumentService,
                 document_factory: DocumentFactory,
                 document_validator: DocumentValidator,
                 document_repository: DocumentRepository):
        """Initialize use case with dependencies."""
        self.document_service = document_service
        self.document_factory = document_factory
        self.document_validator = document_validator
        self.document_repository = document_repository

    async def execute(self, command: CreateDocumentCommand) -> CreateDocumentResult:
        """Execute the create document use case."""
        try:
            # Create document from command
            document = self.document_factory.create_from_text(
                title=command.title,
                text=command.content,
                content_format=command.format,
                author=command.author,
                tags=command.tags,
                repository_id=command.repository_id
            )

            # Validate document
            validation_result = self.document_validator.validate(document)
            if not validation_result.is_valid:
                return CreateDocumentResult(
                    document=document,
                    is_valid=False,
                    validation_errors=[error for error in validation_result.errors]
                )

            # Validate for creation
            creation_validation = self.document_validator.validate_for_creation(document)
            if not creation_validation.is_valid:
                return CreateDocumentResult(
                    document=document,
                    is_valid=False,
                    validation_errors=[error for error in creation_validation.errors]
                )

            # Check business rules
            await self._validate_business_rules(document)

            # Save document
            await self.document_repository.save(document)

            return CreateDocumentResult(
                document=document,
                is_valid=True,
                validation_errors=[]
            )

        except Exception as e:
            # Log error and re-raise
            print(f"Error creating document: {e}")
            raise

    async def _validate_business_rules(self, document: Document) -> None:
        """Validate business rules for document creation."""
        # Check for duplicate titles (simplified - in real app this would be more sophisticated)
        existing_docs = await self.document_repository.get_all()
        for existing_doc in existing_docs:
            if (existing_doc.title.lower() == document.title.lower() and
                existing_doc.metadata.author == document.metadata.author):
                raise DocumentValidationException(
                    document.id.value,
                    ["Document with same title and author already exists"]
                )

        # Check repository exists if specified
        if document.repository_id:
            # In a real implementation, we would check if repository exists
            # For now, we'll skip this validation
            pass

    def to_response(self, result: CreateDocumentResult) -> DocumentResponse:
        """Convert result to response DTO."""
        return DocumentResponse.from_domain(result.document)
