"""Create Finding Use Case."""

from dataclasses import dataclass

from ...domain.entities import Finding, DocumentId
from ...domain.services import FindingService
from ...domain.validation import FindingValidator
from ...domain.exceptions import DocumentNotFoundException
from ...infrastructure.repositories import FindingRepository, DocumentRepository
from ..dto import CreateFindingRequest, FindingResponse


@dataclass
class CreateFindingCommand:
    """Command for creating a finding."""
    document_id: str
    analysis_id: str
    title: str
    description: str
    severity: str
    category: str
    location: dict = None
    suggestion: str = None
    confidence: float = 0.8
    metadata: dict = None


@dataclass
class CreateFindingResult:
    """Result of finding creation."""
    finding: Finding
    is_valid: bool
    validation_errors: list[str]


class CreateFindingUseCase:
    """Use case for creating findings."""

    def __init__(self,
                 finding_service: FindingService,
                 finding_validator: FindingValidator,
                 finding_repository: FindingRepository,
                 document_repository: DocumentRepository):
        """Initialize use case with dependencies."""
        self.finding_service = finding_service
        self.finding_validator = finding_validator
        self.finding_repository = finding_repository
        self.document_repository = document_repository

    async def execute(self, command: CreateFindingCommand) -> CreateFindingResult:
        """Execute the create finding use case."""
        try:
            # Validate document exists
            document = await self.document_repository.get_by_id(command.document_id)
            if not document:
                raise DocumentNotFoundException(command.document_id)

            # Create finding entity
            finding = self.finding_service.create_finding(
                document_id=DocumentId(command.document_id),
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
                return CreateFindingResult(
                    finding=finding,
                    is_valid=False,
                    validation_errors=[error for error in validation_result.errors]
                )

            # Check business rules
            await self._validate_business_rules(finding)

            # Save finding
            await self.finding_repository.save(finding)

            return CreateFindingResult(
                finding=finding,
                is_valid=True,
                validation_errors=[]
            )

        except Exception as e:
            # Log error and re-raise
            print(f"Error creating finding: {e}")
            raise

    async def _validate_business_rules(self, finding: Finding) -> None:
        """Validate business rules for finding creation."""
        # Check for duplicate findings (simplified - in real app this would be more sophisticated)
        existing_findings = await self.finding_repository.get_by_document_id(finding.document_id.value)
        for existing in existing_findings:
            if (existing.title == finding.title and
                existing.category == finding.category and
                existing.analysis_id == finding.analysis_id):
                # Allow similar findings if they're from different analyses
                # This is a simplified rule - in practice, you'd have more sophisticated deduplication
                pass

        # Ensure confidence is reasonable for severity
        if finding.severity.value == 'critical' and finding.confidence < 0.9:
            print(f"Warning: Critical finding with low confidence: {finding.confidence}")

        if finding.severity.value == 'info' and finding.confidence > 0.9:
            print(f"Warning: Info finding with high confidence: {finding.confidence}")

    def to_response(self, result: CreateFindingResult) -> FindingResponse:
        """Convert result to response DTO."""
        return FindingResponse.from_domain(result.finding)
