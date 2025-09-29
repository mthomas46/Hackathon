"""Command handlers for CQRS pattern."""

from typing import Optional
from abc import ABC, abstractmethod

from .commands import (
    CreateDocumentCommand,
    UpdateDocumentCommand,
    DeleteDocumentCommand,
    PerformAnalysisCommand,
    CreateFindingCommand,
    UpdateFindingCommand,
    DeleteFindingCommand,
    CancelAnalysisCommand,
    RetryAnalysisCommand
)
from ..use_cases import (
    CreateDocumentUseCase,
    PerformAnalysisUseCase,
    CreateFindingUseCase
)
from ...domain.entities import Document
from ...infrastructure.repositories import DocumentRepository, AnalysisRepository, FindingRepository
from ...domain.services import DocumentService, AnalysisService, FindingService
from ...domain.factories import DocumentFactory, FindingFactory
from ...domain.validation import DocumentValidator, FindingValidator


class CommandHandler(ABC):
    """Base class for command handlers."""

    @abstractmethod
    async def handle(self, command):
        """Handle the command."""
        pass


class CreateDocumentCommandHandler(CommandHandler):
    """Handler for creating documents."""

    def __init__(self,
                 document_service: DocumentService,
                 document_factory: DocumentFactory,
                 document_validator: DocumentValidator,
                 document_repository: DocumentRepository):
        """Initialize handler with dependencies."""
        self.document_service = document_service
        self.document_factory = document_factory
        self.document_validator = document_validator
        self.document_repository = document_repository

    async def handle(self, command: CreateDocumentCommand) -> Document:
        """Handle create document command."""
        # Create document using factory
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
            raise ValueError(f"Document validation failed: {validation_result.errors}")

        # Validate for creation
        creation_validation = self.document_validator.validate_for_creation(document)
        if not creation_validation.is_valid:
            raise ValueError(f"Document creation validation failed: {creation_validation.errors}")

        # Save document
        await self.document_repository.save(document)

        return document


class UpdateDocumentCommandHandler(CommandHandler):
    """Handler for updating documents."""

    def __init__(self,
                 document_service: DocumentService,
                 document_validator: DocumentValidator,
                 document_repository: DocumentRepository):
        """Initialize handler with dependencies."""
        self.document_service = document_service
        self.document_validator = document_validator
        self.document_repository = document_repository

    async def handle(self, command: UpdateDocumentCommand) -> Optional[Document]:
        """Handle update document command."""
        # Get existing document
        document = await self.document_repository.get_by_id(command.document_id)
        if not document:
            raise ValueError(f"Document not found: {command.document_id}")

        # Apply updates
        if command.title is not None:
            # Note: In a real implementation, this would create a new document with updated title
            # For now, we'll create a new document with the updated content
            pass

        if command.content is not None:
            document.update_content(document.content.__class__(text=command.content, format=command.content.format))

        if command.metadata is not None:
            from datetime import datetime
            from ...domain.entities import Metadata
            new_metadata = Metadata(
                created_at=document.metadata.created_at,
                updated_at=datetime.now(),
                author=command.author or document.metadata.author,
                tags=command.tags or document.metadata.tags,
                properties={**document.metadata.properties, **(command.metadata or {})}
            )
            document.update_metadata(new_metadata)

        # Validate updated document
        validation_result = self.document_validator.validate(document)
        if not validation_result.is_valid:
            raise ValueError(f"Document validation failed: {validation_result.errors}")

        # Save updated document
        await self.document_repository.save(document)

        return document


class DeleteDocumentCommandHandler(CommandHandler):
    """Handler for deleting documents."""

    def __init__(self, document_repository: DocumentRepository):
        """Initialize handler with dependencies."""
        self.document_repository = document_repository

    async def handle(self, command: DeleteDocumentCommand) -> bool:
        """Handle delete document command."""
        # Check if document exists
        document = await self.document_repository.get_by_id(command.document_id)
        if not document:
            raise ValueError(f"Document not found: {command.document_id}")

        # Delete document
        return await self.document_repository.delete(command.document_id)


class PerformAnalysisCommandHandler(CommandHandler):
    """Handler for performing analysis."""

    def __init__(self,
                 analysis_service: AnalysisService,
                 document_repository: DocumentRepository,
                 analysis_repository: AnalysisRepository):
        """Initialize handler with dependencies."""
        self.analysis_service = analysis_service
        self.document_repository = document_repository
        self.analysis_repository = analysis_repository

    async def handle(self, command: PerformAnalysisCommand):
        """Handle perform analysis command."""
        # Get document
        document = await self.document_repository.get_by_id(command.document_id)
        if not document:
            raise ValueError(f"Document not found: {command.document_id}")

        # Create analysis configuration
        from ...domain.entities.value_objects import AnalysisConfiguration, AnalysisType
        config_dict = command.configuration or {}
        if command.timeout_seconds:
            config_dict['timeout_seconds'] = command.timeout_seconds
        config_dict['priority'] = command.priority

        analysis_config = AnalysisConfiguration(**config_dict)

        # Create analysis entity
        analysis = self.analysis_service.create_analysis(
            document=document,
            analysis_type=AnalysisType(command.analysis_type),
            configuration=analysis_config
        )

        # Save analysis
        await self.analysis_repository.save(analysis)

        # Start analysis (in a real implementation, this might be queued)
        analysis.start()
        await self.analysis_repository.save(analysis)

        # Execute analysis (simplified - in real implementation this might be async)
        try:
            result = self.analysis_service.execute_analysis(analysis)
            analysis.complete(result)
        except Exception as e:
            analysis.fail(str(e))

        # Save final analysis state
        await self.analysis_repository.save(analysis)

        return analysis


class CreateFindingCommandHandler(CommandHandler):
    """Handler for creating findings."""

    def __init__(self,
                 finding_service: FindingService,
                 finding_factory: FindingFactory,
                 finding_validator: FindingValidator,
                 finding_repository: FindingRepository,
                 document_repository: DocumentRepository):
        """Initialize handler with dependencies."""
        self.finding_service = finding_service
        self.finding_factory = finding_factory
        self.finding_validator = finding_validator
        self.finding_repository = finding_repository
        self.document_repository = document_repository

    async def handle(self, command: CreateFindingCommand):
        """Handle create finding command."""
        # Validate document exists
        document = await self.document_repository.get_by_id(command.document_id)
        if not document:
            raise ValueError(f"Document not found: {command.document_id}")

        # Create finding entity
        finding = self.finding_service.create_finding(
            document_id=document.id,
            analysis_id=command.analysis_id,
            title=command.title,
            description=command.description,
            severity=command.severity,
            category=command.category,
            confidence=command.confidence,
            location=command.location,
            suggestion=command.suggestion
        )

        # Validate finding
        validation_result = self.finding_validator.validate(finding)
        if not validation_result.is_valid:
            raise ValueError(f"Finding validation failed: {validation_result.errors}")

        # Save finding
        await self.finding_repository.save(finding)

        return finding


class UpdateFindingCommandHandler(CommandHandler):
    """Handler for updating findings."""

    def __init__(self,
                 finding_validator: FindingValidator,
                 finding_repository: FindingRepository):
        """Initialize handler with dependencies."""
        self.finding_validator = finding_validator
        self.finding_repository = finding_repository

    async def handle(self, command: UpdateFindingCommand):
        """Handle update finding command."""
        # Get existing finding
        finding = await self.finding_repository.get_by_id(command.finding_id)
        if not finding:
            raise ValueError(f"Finding not found: {command.finding_id}")

        # Apply updates (simplified - in real implementation, this would create a new finding)
        # For now, we'll just return the existing finding
        return finding


class DeleteFindingCommandHandler(CommandHandler):
    """Handler for deleting findings."""

    def __init__(self, finding_repository: FindingRepository):
        """Initialize handler with dependencies."""
        self.finding_repository = finding_repository

    async def handle(self, command: DeleteFindingCommand) -> bool:
        """Handle delete finding command."""
        # Check if finding exists
        finding = await self.finding_repository.get_by_id(command.finding_id)
        if not finding:
            raise ValueError(f"Finding not found: {command.finding_id}")

        # Delete finding
        return await self.finding_repository.delete(command.finding_id)


class CancelAnalysisCommandHandler(CommandHandler):
    """Handler for canceling analysis."""

    def __init__(self, analysis_repository: AnalysisRepository):
        """Initialize handler with dependencies."""
        self.analysis_repository = analysis_repository

    async def handle(self, command: CancelAnalysisCommand):
        """Handle cancel analysis command."""
        # Get analysis
        analysis = await self.analysis_repository.get_by_id(command.analysis_id)
        if not analysis:
            raise ValueError(f"Analysis not found: {command.analysis_id}")

        # Cancel analysis
        analysis.cancel()
        await self.analysis_repository.save(analysis)

        return analysis
