"""CodeAnalysis entity - Aggregate root for code analysis domain."""

import uuid
from datetime import datetime
from typing import Optional

from domain.value_objects import Language, AnalysisStatus
from domain.exceptions import (
    InvalidCodeError,
    UnsupportedLanguageError,
    InvalidStatusTransitionError,
    AnalysisImmutableError,
    InvariantViolationError
)


class CodeAnalysis:
    """
    CodeAnalysis entity (Aggregate Root).
    
    Represents a code analysis operation with its lifecycle and results.
    Enforces domain invariants and business rules.
    """
    
    def __init__(self, code_content: str, language: Language):
        """
        Create a new CodeAnalysis.
        
        Args:
            code_content: Source code to analyze
            language: Programming language
            
        Raises:
            InvalidCodeError: If code is invalid
            UnsupportedLanguageError: If language not supported
        """
        # Validate code content
        if code_content is None:
            raise InvalidCodeError("Code content cannot be None")
        
        if not isinstance(code_content, str):
            raise InvalidCodeError("Code content must be a string")
        
        if not code_content or not code_content.strip():
            raise InvalidCodeError("Code content cannot be empty or whitespace")
        
        # Validate language
        if not isinstance(language, Language):
            raise UnsupportedLanguageError(f"Unsupported language: {language}")
        
        # Initialize entity
        self._analysis_id = str(uuid.uuid4())
        self._code_content = code_content
        self._language = language
        self._status = AnalysisStatus.PENDING
        self._timestamp = datetime.now()
        self._results: Optional['AnalysisResults'] = None
        self._error_message: Optional[str] = None
    
    @property
    def analysis_id(self) -> str:
        """Get analysis ID (immutable)."""
        return self._analysis_id
    
    @property
    def code_content(self) -> str:
        """Get code content (immutable)."""
        return self._code_content
    
    @property
    def language(self) -> Language:
        """Get language (immutable)."""
        return self._language
    
    @property
    def status(self) -> AnalysisStatus:
        """Get current status."""
        return self._status
    
    @property
    def timestamp(self) -> datetime:
        """Get creation timestamp (immutable)."""
        return self._timestamp
    
    @property
    def results(self) -> Optional['AnalysisResults']:
        """Get analysis results."""
        return self._results
    
    @property
    def error_message(self) -> Optional[str]:
        """Get error message if failed."""
        return self._error_message
    
    def start_analysis(self):
        """
        Start the analysis process.
        
        Raises:
            InvalidStatusTransitionError: If cannot transition to ANALYZING
        """
        if not self._status.can_transition_to(AnalysisStatus.ANALYZING):
            raise InvalidStatusTransitionError(
                f"Cannot start analysis from status {self._status.name}"
            )
        
        self._status = AnalysisStatus.ANALYZING
    
    def complete_analysis(self):
        """
        Mark analysis as completed.
        
        Raises:
            InvalidStatusTransitionError: If cannot transition to COMPLETED
            InvariantViolationError: If results not set
        """
        # Business rule: completed analysis must have results
        if self._results is None:
            raise InvariantViolationError(
                "Cannot complete analysis without results"
            )
        
        if not self._status.can_transition_to(AnalysisStatus.COMPLETED):
            raise InvalidStatusTransitionError(
                f"Cannot complete analysis from status {self._status.name}"
            )
        
        self._status = AnalysisStatus.COMPLETED
    
    def mark_failed(self, error_message: Optional[str]):
        """
        Mark analysis as failed.
        
        Args:
            error_message: Description of failure
            
        Raises:
            InvalidStatusTransitionError: If cannot transition to FAILED
            InvariantViolationError: If error message invalid
        """
        # Business rule: failed analysis must have error message
        if not error_message or not error_message.strip():
            raise InvariantViolationError(
                "Failed analysis must have an error message"
            )
        
        if not self._status.can_transition_to(AnalysisStatus.FAILED):
            raise InvalidStatusTransitionError(
                f"Cannot mark as failed from status {self._status.name}"
            )
        
        self._error_message = error_message
        self._status = AnalysisStatus.FAILED
    
    def set_results(self, results: 'AnalysisResults'):
        """
        Set analysis results.
        
        Args:
            results: Analysis results to set
            
        Raises:
            AnalysisImmutableError: If analysis already completed
        """
        # Business rule: cannot modify results after completion
        if self._status == AnalysisStatus.COMPLETED:
            raise AnalysisImmutableError(
                "Cannot modify results of completed analysis"
            )
        
        self._results = results
    
    def __eq__(self, other) -> bool:
        """Equality based on analysis ID."""
        if not isinstance(other, CodeAnalysis):
            return False
        return self._analysis_id == other._analysis_id
    
    def __ne__(self, other) -> bool:
        """Inequality based on analysis ID."""
        return not self.__eq__(other)
    
    def __hash__(self) -> int:
        """Hash based on analysis ID."""
        return hash(self._analysis_id)
    
    def __repr__(self) -> str:
        """String representation."""
        return (
            f"CodeAnalysis("
            f"id={self._analysis_id[:8]}..., "
            f"language={self._language.name}, "
            f"status={self._status.name})"
        )

