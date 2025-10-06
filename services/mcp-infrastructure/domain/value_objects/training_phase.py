"""Training Phase - Value Object.

Defines the phases of MCP training pipelines.
"""

from enum import Enum


class TrainingPhase(str, Enum):
    """
    Phases of MCP training pipeline.
    
    This enum represents the sequential stages of training
    an MCP instance from data extraction to deployment.
    """
    
    IDLE = "idle"                   # Not currently training
    EXTRACTION = "extraction"       # Extracting data from sources
    NORMALIZATION = "normalization" # Normalizing and cleaning data
    EMBEDDING = "embedding"         # Generating vector embeddings
    GRAPH_BUILD = "graph_build"     # Building knowledge graph
    VALIDATION = "validation"       # Validating training results
    DEPLOYMENT = "deployment"       # Deploying trained model
    COMPLETE = "complete"           # Training successfully completed
    FAILED = "failed"               # Training failed
    CANCELLED = "cancelled"         # Training was cancelled
    
    def __str__(self) -> str:
        """String representation of training phase."""
        return self.value
    
    @property
    def is_active(self) -> bool:
        """Check if this phase represents active training."""
        return self in [
            TrainingPhase.EXTRACTION,
            TrainingPhase.NORMALIZATION,
            TrainingPhase.EMBEDDING,
            TrainingPhase.GRAPH_BUILD,
            TrainingPhase.VALIDATION,
            TrainingPhase.DEPLOYMENT,
        ]
    
    @property
    def is_terminal(self) -> bool:
        """Check if this phase is a terminal state."""
        return self in [
            TrainingPhase.COMPLETE,
            TrainingPhase.FAILED,
            TrainingPhase.CANCELLED,
        ]
    
    @property
    def progress_percentage(self) -> float:
        """Get approximate progress percentage for this phase."""
        progress_map = {
            TrainingPhase.IDLE: 0.0,
            TrainingPhase.EXTRACTION: 0.15,
            TrainingPhase.NORMALIZATION: 0.35,
            TrainingPhase.EMBEDDING: 0.55,
            TrainingPhase.GRAPH_BUILD: 0.75,
            TrainingPhase.VALIDATION: 0.90,
            TrainingPhase.DEPLOYMENT: 0.95,
            TrainingPhase.COMPLETE: 1.0,
            TrainingPhase.FAILED: 0.0,
            TrainingPhase.CANCELLED: 0.0,
        }
        return progress_map.get(self, 0.0)

