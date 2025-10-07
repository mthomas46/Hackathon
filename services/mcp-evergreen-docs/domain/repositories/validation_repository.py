"""Validation Repository Interface."""

from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities.validation_result import ValidationResult


class ValidationRepository(ABC):
    """Abstract repository for ValidationResult entities."""
    
    @abstractmethod
    async def add(self, result: ValidationResult) -> None:
        """Add validation result."""
        pass
    
    @abstractmethod
    async def get_by_id(self, result_id: str) -> Optional[ValidationResult]:
        """Get validation result by ID."""
        pass
    
    @abstractmethod
    async def get_latest_by_doc(self, doc_id: str) -> Optional[ValidationResult]:
        """Get latest validation result for document."""
        pass
    
    @abstractmethod
    async def list_by_doc(self, doc_id: str) -> List[ValidationResult]:
        """List all validation results for document."""
        pass
    
    @abstractmethod
    async def delete(self, result_id: str) -> None:
        """Delete validation result."""
        pass
    
    @abstractmethod
    async def find_invalid_docs(self) -> List[str]:
        """Find document IDs with invalid validation results."""
        pass

