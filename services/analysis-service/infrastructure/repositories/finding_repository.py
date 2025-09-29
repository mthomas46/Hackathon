"""Finding repository implementation."""

from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod

from ...domain.entities import Finding, FindingId, DocumentId


class FindingRepository(ABC):
    """Abstract repository for finding entities."""

    @abstractmethod
    async def save(self, finding: Finding) -> None:
        """Save a finding."""
        pass

    @abstractmethod
    async def get_by_id(self, finding_id: str) -> Optional[Finding]:
        """Get finding by ID."""
        pass

    @abstractmethod
    async def get_by_document_id(self, document_id: str) -> List[Finding]:
        """Get all findings for a document."""
        pass

    @abstractmethod
    async def get_all(self) -> List[Finding]:
        """Get all findings."""
        pass

    @abstractmethod
    async def get_by_category(self, category: str) -> List[Finding]:
        """Get findings by category."""
        pass

    @abstractmethod
    async def get_unresolved(self) -> List[Finding]:
        """Get all unresolved findings."""
        pass

    @abstractmethod
    async def delete(self, finding_id: str) -> bool:
        """Delete a finding."""
        pass


class InMemoryFindingRepository(FindingRepository):
    """In-memory implementation of finding repository."""

    def __init__(self):
        """Initialize repository with empty storage."""
        self._findings: Dict[str, Finding] = {}
        self._document_findings: Dict[str, List[str]] = {}

    async def save(self, finding: Finding) -> None:
        """Save a finding to memory."""
        finding_id = finding.id.value
        document_id = finding.document_id.value

        self._findings[finding_id] = finding

        # Update document index
        if document_id not in self._document_findings:
            self._document_findings[document_id] = []
        if finding_id not in self._document_findings[document_id]:
            self._document_findings[document_id].append(finding_id)

    async def get_by_id(self, finding_id: str) -> Optional[Finding]:
        """Get finding by ID from memory."""
        return self._findings.get(finding_id)

    async def get_by_document_id(self, document_id: str) -> List[Finding]:
        """Get all findings for a document from memory."""
        finding_ids = self._document_findings.get(document_id, [])
        return [self._findings[fid] for fid in finding_ids if fid in self._findings]

    async def get_all(self) -> List[Finding]:
        """Get all findings from memory."""
        return list(self._findings.values())

    async def get_by_category(self, category: str) -> List[Finding]:
        """Get findings by category from memory."""
        return [
            finding for finding in self._findings.values()
            if finding.category == category
        ]

    async def get_unresolved(self) -> List[Finding]:
        """Get all unresolved findings from memory."""
        return [
            finding for finding in self._findings.values()
            if not finding.is_resolved()
        ]

    async def delete(self, finding_id: str) -> bool:
        """Delete a finding from memory."""
        if finding_id in self._findings:
            finding = self._findings[finding_id]
            document_id = finding.document_id.value

            # Remove from main storage
            del self._findings[finding_id]

            # Remove from document index
            if document_id in self._document_findings:
                if finding_id in self._document_findings[document_id]:
                    self._document_findings[document_id].remove(finding_id)

            return True
        return False

    def clear(self) -> None:
        """Clear all findings (for testing)."""
        self._findings.clear()
        self._document_findings.clear()
