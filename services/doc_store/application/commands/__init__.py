"""Application commands for Doc Store service.

Commands represent write operations and business actions.
"""

from .document_commands import (
    CreateDocumentCommand,
    UpdateDocumentCommand,
    DeleteDocumentCommand,
    TagDocumentCommand
)

__all__ = [
    "CreateDocumentCommand",
    "UpdateDocumentCommand",
    "DeleteDocumentCommand",
    "TagDocumentCommand",
]
