"""
Model request models for Ecosystem MCP Service.

Tracks requests to AI models for cost and performance monitoring.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ModelType(str, Enum):
    """
    AI model types.
    """
    # Ollama (local)
    OLLAMA_LLAMA3_8B = "ollama_llama3_8b"
    OLLAMA_MISTRAL_7B = "ollama_mistral_7b"
    OLLAMA_EMBED = "ollama_embed"
    
    # OpenAI
    OPENAI_EMBED_SMALL = "openai_embed_small"
    OPENAI_EMBED_LARGE = "openai_embed_large"
    
    # Anthropic
    CLAUDE_HAIKU = "claude_haiku"
    CLAUDE_SONNET = "claude_sonnet"
    CLAUDE_OPUS = "claude_opus"
    
    # Cursor (free models)
    CURSOR_FREE_FAST = "cursor_free_fast"
    CURSOR_FREE_SMART = "cursor_free_smart"


class TaskType(str, Enum):
    """
    Task types for model requests.
    """
    METADATA_EXTRACTION = "metadata_extraction"
    SUMMARIZATION = "summarization"
    CODE_ANALYSIS = "code_analysis"
    PATTERN_RECOGNITION = "pattern_recognition"
    REFACTORING_SUGGESTION = "refactoring_suggestion"
    EMBEDDING_GENERATION = "embedding_generation"
    SEARCH_QUERY = "search_query"
    COMPARISON = "comparison"


class ModelRequest(BaseModel):
    """
    Model request tracking.
    
    Records every request to an AI model for cost and performance monitoring.
    """
    
    id: UUID = Field(
        default_factory=uuid4,
        description="Unique request identifier"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When request was made"
    )
    
    model: ModelType = Field(
        description="Model used"
    )
    
    task_type: TaskType = Field(
        description="Type of task"
    )
    
    input_tokens: int = Field(
        ge=0,
        description="Number of input tokens"
    )
    
    output_tokens: int = Field(
        ge=0,
        description="Number of output tokens"
    )
    
    cost_usd: float = Field(
        ge=0.0,
        description="Cost in USD"
    )
    
    latency_ms: int = Field(
        ge=0,
        description="Request latency in milliseconds"
    )
    
    success: bool = Field(
        description="Whether request succeeded"
    )
    
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if failed"
    )
    
    document_id: Optional[UUID] = Field(
        default=None,
        description="Related document if applicable"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "model": "claude_sonnet",
                "task_type": "pattern_recognition",
                "input_tokens": 5000,
                "output_tokens": 1000,
                "cost_usd": 0.018,
                "latency_ms": 2500,
                "success": True
            }
        }
    
    @property
    def total_tokens(self) -> int:
        """Calculate total tokens."""
        return self.input_tokens + self.output_tokens
    
    @property
    def cost_per_token(self) -> float:
        """Calculate cost per token."""
        if self.total_tokens > 0:
            return self.cost_usd / self.total_tokens
        return 0.0
    
    @property
    def is_free(self) -> bool:
        """Check if request was free."""
        return self.cost_usd == 0.0

