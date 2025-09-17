"""Base validation infrastructure for application layer."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum


class ValidationSeverity(Enum):
    """Severity levels for validation errors."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationError:
    """Represents a validation error."""
    field: Optional[str]
    message: str
    code: str
    severity: ValidationSeverity = ValidationSeverity.ERROR
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'field': self.field,
            'message': self.message,
            'code': self.code,
            'severity': self.severity.value,
            'metadata': self.metadata or {}
        }


@dataclass
class ValidationResult:
    """Result of a validation operation."""
    is_valid: bool
    errors: List[ValidationError]
    warnings: List[ValidationError]
    metadata: Optional[Dict[str, Any]] = None

    @classmethod
    def success(cls, metadata: Optional[Dict[str, Any]] = None) -> 'ValidationResult':
        """Create a successful validation result."""
        return cls(
            is_valid=True,
            errors=[],
            warnings=[],
            metadata=metadata
        )

    @classmethod
    def failure(
        cls,
        errors: List[ValidationError],
        warnings: Optional[List[ValidationError]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> 'ValidationResult':
        """Create a failed validation result."""
        return cls(
            is_valid=False,
            errors=errors,
            warnings=warnings or [],
            metadata=metadata
        )

    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return len(self.errors) > 0

    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return len(self.warnings) > 0

    def get_all_issues(self) -> List[ValidationError]:
        """Get all validation issues (errors and warnings)."""
        return self.errors + self.warnings

    def get_errors_by_severity(self, severity: ValidationSeverity) -> List[ValidationError]:
        """Get errors by severity level."""
        return [error for error in self.errors if error.severity == severity]

    def get_warnings_by_severity(self, severity: ValidationSeverity) -> List[ValidationError]:
        """Get warnings by severity level."""
        return [warning for warning in self.warnings if warning.severity == severity]


class BaseValidator(ABC):
    """Abstract base class for all validators."""

    def __init__(self, name: Optional[str] = None):
        """Initialize validator."""
        self.name = name or self.__class__.__name__

    @abstractmethod
    async def validate(self, data: Any) -> ValidationResult:
        """Validate the given data."""
        pass

    async def validate_field(self, field_name: str, field_value: Any) -> List[ValidationError]:
        """Validate a specific field. Override in subclasses as needed."""
        return []

    def create_error(
        self,
        message: str,
        code: str,
        field: Optional[str] = None,
        severity: ValidationSeverity = ValidationSeverity.ERROR,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ValidationError:
        """Create a validation error."""
        return ValidationError(
            field=field,
            message=message,
            code=code,
            severity=severity,
            metadata=metadata
        )

    def create_warning(
        self,
        message: str,
        code: str,
        field: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ValidationError:
        """Create a validation warning."""
        return ValidationError(
            field=field,
            message=message,
            code=code,
            severity=ValidationSeverity.WARNING,
            metadata=metadata
        )


class CompositeValidator(BaseValidator):
    """Validator that combines multiple validators."""

    def __init__(self, validators: List[BaseValidator], name: Optional[str] = None):
        """Initialize composite validator."""
        super().__init__(name)
        self.validators = validators

    async def validate(self, data: Any) -> ValidationResult:
        """Validate using all child validators."""
        all_errors = []
        all_warnings = []
        all_metadata = {}

        for validator in self.validators:
            result = await validator.validate(data)
            all_errors.extend(result.errors)
            all_warnings.extend(result.warnings)

            if result.metadata:
                all_metadata.update(result.metadata)

        if all_errors:
            return ValidationResult.failure(
                errors=all_errors,
                warnings=all_warnings,
                metadata=all_metadata
            )

        return ValidationResult.success(metadata=all_metadata)


class ConditionalValidator(BaseValidator):
    """Validator that only validates if a condition is met."""

    def __init__(
        self,
        validator: BaseValidator,
        condition_func: callable,
        name: Optional[str] = None
    ):
        """Initialize conditional validator."""
        super().__init__(name)
        self.validator = validator
        self.condition_func = condition_func

    async def validate(self, data: Any) -> ValidationResult:
        """Validate only if condition is met."""
        if await self.condition_func(data):
            return await self.validator.validate(data)

        # Condition not met, return success
        return ValidationResult.success()


class ValidationException(Exception):
    """Exception raised when validation fails."""

    def __init__(self, result: ValidationResult):
        """Initialize validation exception."""
        self.result = result
        super().__init__(f"Validation failed: {len(result.errors)} errors, {len(result.warnings)} warnings")

    def get_errors(self) -> List[ValidationError]:
        """Get validation errors."""
        return self.result.errors

    def get_warnings(self) -> List[ValidationError]:
        """Get validation warnings."""
        return self.result.warnings


class ValidationContext:
    """Context for validation operations."""

    def __init__(
        self,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Initialize validation context."""
        self.user_id = user_id
        self.session_id = session_id
        self.correlation_id = correlation_id
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'user_id': self.user_id,
            'session_id': self.session_id,
            'correlation_id': self.correlation_id,
            'metadata': self.metadata
        }
