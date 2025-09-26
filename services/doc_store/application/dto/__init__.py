"""Application DTOs for Doc Store service.

Data Transfer Objects for application layer communication.
"""

from .document_dto import (
    DocumentDTO,
    CreateDocumentDTO,
    UpdateDocumentDTO,
    DocumentListDTO
)

__all__ = [
    "DocumentDTO",
    "CreateDocumentDTO",
    "UpdateDocumentDTO",
    "DocumentListDTO",
]
