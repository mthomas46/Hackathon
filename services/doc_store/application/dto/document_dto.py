"""Document DTOs for Doc Store application layer.

Data Transfer Objects for document operations.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class DocumentDTO:
    """DTO for document data transfer."""

    id: str
    content: str
    metadata: Optional[Dict[str, str]] = None
    tags: Optional[List[str]] = None
    created_at: Optional[float] = None
    updated_at: Optional[float] = None


@dataclass
class CreateDocumentDTO:
    """DTO for document creation requests."""

    content: str
    metadata: Optional[Dict[str, str]] = None
    tags: Optional[List[str]] = None


@dataclass
class UpdateDocumentDTO:
    """DTO for document update requests."""

    content: Optional[str] = None
    metadata: Optional[Dict[str, str]] = None
    tags: Optional[List[str]] = None


@dataclass
class DocumentListDTO:
    """DTO for paginated document lists."""

    documents: List[DocumentDTO]
    total_count: int
    limit: int
    offset: int
