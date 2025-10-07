"""Change detection system for Evergreen Documentation."""

from typing import Dict, List, Optional, Set, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import hashlib
import difflib


class ChangeType(Enum):
    """Type of change detected."""
    ADDED = "added"
    MODIFIED = "modified"
    DELETED = "deleted"
    RENAMED = "renamed"
    MOVED = "moved"


class ChangeSeverity(Enum):
    """Severity of the change."""
    MINOR = "minor"          # Typos, formatting
    MODERATE = "moderate"    # Content updates
    MAJOR = "major"          # Structural changes
    CRITICAL = "critical"    # Breaking changes


@dataclass
class DocumentChange:
    """Represents a change to a document."""
    change_id: str
    document_id: str
    change_type: ChangeType
    severity: ChangeSeverity
    old_content: Optional[str]
    new_content: Optional[str]
    diff: Optional[str]
    metadata: Dict[str, Any]
    detected_at: datetime
    author: Optional[str] = None
    reason: Optional[str] = None


@dataclass
class ChangeDetectionResult:
    """Result of change detection."""
    total_changes: int
    changes_by_type: Dict[str, int]
    changes_by_severity: Dict[str, int]
    changes: List[DocumentChange]
    detected_at: datetime


class ChangeDetector:
    """
    Detects changes in documentation for Evergreen Documentation system.
    
    Provides:
    - Content change detection
    - Diff generation
    - Change severity classification
    - Change type identification
    """
    
    def __init__(self):
        """Initialize change detector."""
        self.known_documents: Dict[str, str] = {}  # doc_id -> content_hash
        self.document_content: Dict[str, str] = {}  # doc_id -> content
        self.change_history: List[DocumentChange] = []
    
    def register_document(self, document_id: str, content: str):
        """
        Register a document for change tracking.
        
        Args:
            document_id: Document identifier
            content: Document content
        """
        content_hash = self._compute_hash(content)
        self.known_documents[document_id] = content_hash
        self.document_content[document_id] = content
    
    def detect_changes(
        self,
        document_id: str,
        new_content: str,
        author: Optional[str] = None
    ) -> Optional[DocumentChange]:
        """
        Detect changes in a document.
        
        Args:
            document_id: Document identifier
            new_content: New document content
            author: Optional author of the change
        
        Returns:
            DocumentChange if changes detected, None otherwise
        """
        # Check if document is new
        if document_id not in self.known_documents:
            change = DocumentChange(
                change_id=self._generate_change_id(document_id),
                document_id=document_id,
                change_type=ChangeType.ADDED,
                severity=ChangeSeverity.MAJOR,
                old_content=None,
                new_content=new_content,
                diff=None,
                metadata={"lines": len(new_content.splitlines())},
                detected_at=datetime.now(),
                author=author,
                reason="New document created"
            )
            
            self.register_document(document_id, new_content)
            self.change_history.append(change)
            return change
        
        # Check if content changed
        old_content = self.document_content.get(document_id, "")
        new_hash = self._compute_hash(new_content)
        old_hash = self.known_documents[document_id]
        
        if new_hash == old_hash:
            return None  # No change
        
        # Generate diff
        diff = self._generate_diff(old_content, new_content)
        
        # Classify severity
        severity = self._classify_severity(old_content, new_content, diff)
        
        # Create change record
        change = DocumentChange(
            change_id=self._generate_change_id(document_id),
            document_id=document_id,
            change_type=ChangeType.MODIFIED,
            severity=severity,
            old_content=old_content,
            new_content=new_content,
            diff=diff,
            metadata={
                "old_lines": len(old_content.splitlines()),
                "new_lines": len(new_content.splitlines()),
                "additions": diff.count("\n+"),
                "deletions": diff.count("\n-")
            },
            detected_at=datetime.now(),
            author=author
        )
        
        # Update stored content
        self.register_document(document_id, new_content)
        self.change_history.append(change)
        
        return change
    
    def detect_deletion(
        self,
        document_id: str,
        author: Optional[str] = None
    ) -> Optional[DocumentChange]:
        """
        Detect document deletion.
        
        Args:
            document_id: Document identifier
            author: Optional author of the deletion
        
        Returns:
            DocumentChange for deletion
        """
        if document_id not in self.known_documents:
            return None  # Document not tracked
        
        old_content = self.document_content.get(document_id, "")
        
        change = DocumentChange(
            change_id=self._generate_change_id(document_id),
            document_id=document_id,
            change_type=ChangeType.DELETED,
            severity=ChangeSeverity.MAJOR,
            old_content=old_content,
            new_content=None,
            diff=None,
            metadata={"lines": len(old_content.splitlines())},
            detected_at=datetime.now(),
            author=author,
            reason="Document deleted"
        )
        
        # Remove from tracking
        del self.known_documents[document_id]
        del self.document_content[document_id]
        
        self.change_history.append(change)
        return change
    
    def detect_rename(
        self,
        old_document_id: str,
        new_document_id: str,
        author: Optional[str] = None
    ) -> Optional[DocumentChange]:
        """
        Detect document rename.
        
        Args:
            old_document_id: Old document identifier
            new_document_id: New document identifier
            author: Optional author of the rename
        
        Returns:
            DocumentChange for rename
        """
        if old_document_id not in self.known_documents:
            return None
        
        content = self.document_content.get(old_document_id, "")
        
        change = DocumentChange(
            change_id=self._generate_change_id(old_document_id),
            document_id=new_document_id,
            change_type=ChangeType.RENAMED,
            severity=ChangeSeverity.MODERATE,
            old_content=None,
            new_content=None,
            diff=None,
            metadata={
                "old_id": old_document_id,
                "new_id": new_document_id
            },
            detected_at=datetime.now(),
            author=author,
            reason=f"Renamed from {old_document_id}"
        )
        
        # Update tracking
        content_hash = self.known_documents[old_document_id]
        del self.known_documents[old_document_id]
        del self.document_content[old_document_id]
        
        self.known_documents[new_document_id] = content_hash
        self.document_content[new_document_id] = content
        
        self.change_history.append(change)
        return change
    
    def detect_batch_changes(
        self,
        documents: Dict[str, str],
        author: Optional[str] = None
    ) -> ChangeDetectionResult:
        """
        Detect changes across multiple documents.
        
        Args:
            documents: Dict of document_id -> content
            author: Optional author of changes
        
        Returns:
            ChangeDetectionResult with all detected changes
        """
        changes: List[DocumentChange] = []
        
        # Detect changes in provided documents
        for doc_id, content in documents.items():
            change = self.detect_changes(doc_id, content, author)
            if change:
                changes.append(change)
        
        # Detect deletions (documents that were tracked but not provided)
        tracked_ids = set(self.known_documents.keys())
        provided_ids = set(documents.keys())
        deleted_ids = tracked_ids - provided_ids
        
        for doc_id in deleted_ids:
            change = self.detect_deletion(doc_id, author)
            if change:
                changes.append(change)
        
        # Aggregate statistics
        changes_by_type = {}
        changes_by_severity = {}
        
        for change in changes:
            change_type = change.change_type.value
            severity = change.severity.value
            
            changes_by_type[change_type] = changes_by_type.get(change_type, 0) + 1
            changes_by_severity[severity] = changes_by_severity.get(severity, 0) + 1
        
        return ChangeDetectionResult(
            total_changes=len(changes),
            changes_by_type=changes_by_type,
            changes_by_severity=changes_by_severity,
            changes=changes,
            detected_at=datetime.now()
        )
    
    def get_change_history(
        self,
        document_id: Optional[str] = None,
        limit: int = 100
    ) -> List[DocumentChange]:
        """
        Get change history.
        
        Args:
            document_id: Optional document ID to filter by
            limit: Maximum number of changes to return
        
        Returns:
            List of changes
        """
        if document_id:
            history = [
                change for change in self.change_history
                if change.document_id == document_id
            ]
        else:
            history = self.change_history
        
        return history[-limit:]
    
    def _compute_hash(self, content: str) -> str:
        """
        Compute content hash.
        
        Args:
            content: Document content
        
        Returns:
            SHA-256 hash of content
        """
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def _generate_diff(self, old_content: str, new_content: str) -> str:
        """
        Generate unified diff.
        
        Args:
            old_content: Old content
            new_content: New content
        
        Returns:
            Unified diff string
        """
        old_lines = old_content.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            old_lines,
            new_lines,
            lineterm='',
            n=3  # Context lines
        )
        
        return ''.join(diff)
    
    def _classify_severity(
        self,
        old_content: str,
        new_content: str,
        diff: str
    ) -> ChangeSeverity:
        """
        Classify change severity.
        
        Args:
            old_content: Old content
            new_content: New content
            diff: Generated diff
        
        Returns:
            ChangeSeverity classification
        """
        # Count changes
        additions = diff.count("\n+")
        deletions = diff.count("\n-")
        total_changes = additions + deletions
        
        old_lines = len(old_content.splitlines())
        
        # Calculate change ratio
        if old_lines == 0:
            return ChangeSeverity.MAJOR
        
        change_ratio = total_changes / old_lines
        
        # Classify
        if change_ratio > 0.5:
            return ChangeSeverity.CRITICAL  # >50% changed
        elif change_ratio > 0.2:
            return ChangeSeverity.MAJOR     # >20% changed
        elif change_ratio > 0.05:
            return ChangeSeverity.MODERATE  # >5% changed
        else:
            return ChangeSeverity.MINOR     # <5% changed
    
    def _generate_change_id(self, document_id: str) -> str:
        """
        Generate unique change ID.
        
        Args:
            document_id: Document identifier
        
        Returns:
            Unique change ID
        """
        timestamp = datetime.now().isoformat()
        combined = f"{document_id}:{timestamp}"
        return hashlib.sha256(combined.encode('utf-8')).hexdigest()[:16]

