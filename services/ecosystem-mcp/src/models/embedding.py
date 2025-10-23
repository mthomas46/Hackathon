"""
Embedding models for Ecosystem MCP Service.

Represents vector embeddings generated from documents,
with cost tracking and model information.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class EmbeddingMetadata(BaseModel):
    """
    Metadata about the embedding generation.
    """
    
    model_config = {"protected_namespaces": ()}  # Allow 'model_' prefix
    
    model_name: str = Field(
        description="Model used to generate embedding"
    )
    
    model_version: Optional[str] = Field(
        default=None,
        description="Model version"
    )
    
    dimensions: int = Field(
        ge=1,
        description="Embedding dimension count"
    )
    
    token_count: int = Field(
        ge=0,
        description="Number of tokens in input"
    )
    
    cost_usd: float = Field(
        ge=0.0,
        description="Cost in USD to generate embedding"
    )
    
    generation_time_ms: Optional[int] = Field(
        default=None,
        ge=0,
        description="Time taken to generate embedding (ms)"
    )


class Embedding(BaseModel):
    """
    Embedding model.
    
    Represents a vector embedding for a document,
    stored in ChromaDB with metadata in PostgreSQL.
    """
    
    id: UUID = Field(
        default_factory=uuid4,
        description="Unique embedding identifier"
    )
    
    document_id: UUID = Field(
        description="Reference to source document"
    )
    
    chroma_id: str = Field(
        description="ID in ChromaDB collection",
        min_length=1
    )
    
    model: str = Field(
        description="Model used for embedding",
        min_length=1,
        max_length=100
    )
    
    dimensions: int = Field(
        ge=1,
        description="Embedding dimension count"
    )
    
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When embedding was created"
    )
    
    token_count: int = Field(
        ge=0,
        description="Number of tokens embedded"
    )
    
    cost_usd: float = Field(
        ge=0.0,
        description="Cost to generate embedding"
    )
    
    metadata: Optional[EmbeddingMetadata] = Field(
        default=None,
        description="Additional metadata"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "document_id": "987fcdeb-51a2-43d1-b789-123456789abc",
                "chroma_id": "doc_12345",
                "model": "text-embedding-3-small",
                "dimensions": 1536,
                "token_count": 1500,
                "cost_usd": 0.0002
            }
        }


class EmbeddingCreate(BaseModel):
    """
    Model for creating a new embedding.
    """
    
    document_id: UUID
    chroma_id: str = Field(min_length=1)
    model: str = Field(min_length=1, max_length=100)
    dimensions: int = Field(ge=1)
    token_count: int = Field(ge=0)
    cost_usd: float = Field(ge=0.0)
    metadata: Optional[EmbeddingMetadata] = None

