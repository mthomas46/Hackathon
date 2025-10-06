"""Worker Type Value Object."""

from enum import Enum


class WorkerType(str, Enum):
    """
    Type of worker in the training pipeline.
    
    Each worker type handles a specific stage of MCP training.
    """
    
    EXTRACTION = "extraction"
    """Extracts raw data from sources (GitHub, Jira, Confluence, etc.)."""
    
    NORMALIZATION = "normalization"
    """Normalizes extracted data (markdown conversion, scope classification)."""
    
    EMBEDDING = "embedding"
    """Generates embeddings, tags, and entity extraction."""
    
    STORAGE = "storage"
    """Stores processed data to vector/graph databases."""
    
    VALIDATION = "validation"
    """Validates job inputs and configuration."""
    
    @property
    def stage_order(self) -> int:
        """Get execution order in pipeline."""
        stage_orders = {
            WorkerType.VALIDATION: 0,
            WorkerType.EXTRACTION: 1,
            WorkerType.NORMALIZATION: 2,
            WorkerType.EMBEDDING: 3,
            WorkerType.STORAGE: 4,
        }
        return stage_orders[self]
    
    @property
    def next_stage(self) -> "WorkerType":
        """Get next stage in pipeline."""
        next_stages = {
            WorkerType.VALIDATION: WorkerType.EXTRACTION,
            WorkerType.EXTRACTION: WorkerType.NORMALIZATION,
            WorkerType.NORMALIZATION: WorkerType.EMBEDDING,
            WorkerType.EMBEDDING: WorkerType.STORAGE,
        }
        return next_stages.get(self)
    
    @property
    def is_final_stage(self) -> bool:
        """Check if this is the final stage."""
        return self == WorkerType.STORAGE

