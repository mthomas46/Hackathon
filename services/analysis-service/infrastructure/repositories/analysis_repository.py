"""Analysis repository implementation."""

from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod

from ...domain.entities import Analysis, AnalysisId, DocumentId


class AnalysisRepository(ABC):
    """Abstract repository for analysis entities."""

    @abstractmethod
    async def save(self, analysis: Analysis) -> None:
        """Save an analysis."""
        pass

    @abstractmethod
    async def get_by_id(self, analysis_id: str) -> Optional[Analysis]:
        """Get analysis by ID."""
        pass

    @abstractmethod
    async def get_by_document_id(self, document_id: str) -> List[Analysis]:
        """Get all analyses for a document."""
        pass

    @abstractmethod
    async def get_all(self) -> List[Analysis]:
        """Get all analyses."""
        pass

    @abstractmethod
    async def get_by_status(self, status: str) -> List[Analysis]:
        """Get analyses by status."""
        pass

    @abstractmethod
    async def delete(self, analysis_id: str) -> bool:
        """Delete an analysis."""
        pass


class InMemoryAnalysisRepository(AnalysisRepository):
    """In-memory implementation of analysis repository."""

    def __init__(self):
        """Initialize repository with empty storage."""
        self._analyses: Dict[str, Analysis] = {}
        self._document_analyses: Dict[str, List[str]] = {}

    async def save(self, analysis: Analysis) -> None:
        """Save an analysis to memory."""
        analysis_id = analysis.id.value
        document_id = analysis.document_id.value

        self._analyses[analysis_id] = analysis

        # Update document index
        if document_id not in self._document_analyses:
            self._document_analyses[document_id] = []
        if analysis_id not in self._document_analyses[document_id]:
            self._document_analyses[document_id].append(analysis_id)

    async def get_by_id(self, analysis_id: str) -> Optional[Analysis]:
        """Get analysis by ID from memory."""
        return self._analyses.get(analysis_id)

    async def get_by_document_id(self, document_id: str) -> List[Analysis]:
        """Get all analyses for a document from memory."""
        analysis_ids = self._document_analyses.get(document_id, [])
        return [self._analyses[aid] for aid in analysis_ids if aid in self._analyses]

    async def get_all(self) -> List[Analysis]:
        """Get all analyses from memory."""
        return list(self._analyses.values())

    async def get_by_status(self, status: str) -> List[Analysis]:
        """Get analyses by status from memory."""
        return [
            analysis for analysis in self._analyses.values()
            if analysis.status.value == status
        ]

    async def delete(self, analysis_id: str) -> bool:
        """Delete an analysis from memory."""
        if analysis_id in self._analyses:
            analysis = self._analyses[analysis_id]
            document_id = analysis.document_id.value

            # Remove from main storage
            del self._analyses[analysis_id]

            # Remove from document index
            if document_id in self._document_analyses:
                if analysis_id in self._document_analyses[document_id]:
                    self._document_analyses[document_id].remove(analysis_id)

            return True
        return False

    def clear(self) -> None:
        """Clear all analyses (for testing)."""
        self._analyses.clear()
        self._document_analyses.clear()
