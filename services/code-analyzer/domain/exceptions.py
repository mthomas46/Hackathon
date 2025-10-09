"""Domain exceptions for code-analyzer service."""


class DomainException(Exception):
    """Base exception for domain layer."""
    pass


class InvalidCodeError(DomainException):
    """Raised when code content is invalid."""
    pass


class UnsupportedLanguageError(DomainException):
    """Raised when language is not supported."""
    pass


class InvalidStatusTransitionError(DomainException):
    """Raised when attempting invalid status transition."""
    pass


class AnalysisImmutableError(DomainException):
    """Raised when attempting to modify completed analysis."""
    pass


class InvariantViolationError(DomainException):
    """Raised when domain invariant is violated."""
    pass


class InvalidValueError(DomainException):
    """Raised when value object receives invalid value."""
    pass

