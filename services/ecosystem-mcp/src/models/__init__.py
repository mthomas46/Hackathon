"""
Data models for Ecosystem MCP Service.

All models use Pydantic for validation and type safety.
"""

from .document import Document, DocumentMetadata, DocumentCreate, DocumentUpdate
from .embedding import Embedding, EmbeddingCreate, EmbeddingMetadata
from .git_commit import GitCommit, GitCommitMetadata, FileChange
from .ingestion import IngestionJob, IngestionMode, IngestionStatus, IngestionResult
from .model_request import ModelRequest, ModelType, TaskType
from .version import DocumentVersion, VersionDiff

__all__ = [
    # Document
    "Document",
    "DocumentMetadata",
    "DocumentCreate",
    "DocumentUpdate",
    # Embedding
    "Embedding",
    "EmbeddingCreate",
    "EmbeddingMetadata",
    # Git
    "GitCommit",
    "GitCommitMetadata",
    "FileChange",
    # Ingestion
    "IngestionJob",
    "IngestionMode",
    "IngestionStatus",
    "IngestionResult",
    # Model Request
    "ModelRequest",
    "ModelType",
    "TaskType",
    # Version
    "DocumentVersion",
    "VersionDiff",
]

