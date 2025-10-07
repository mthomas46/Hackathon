"""Model entity - represents a local LLM model."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from uuid import UUID, uuid4


class ModelStatus(str, Enum):
    """Model lifecycle status."""
    UNLOADED = "unloaded"
    LOADING = "loading"
    READY = "ready"
    UNLOADING = "unloading"
    ERROR = "error"


@dataclass
class Model:
    """
    Domain entity representing a local LLM model.
    
    Attributes:
        id: Unique model identifier
        name: Model name (e.g., "llama2:7b")
        family: Model family (e.g., "llama", "mistral")
        size_bytes: Model size in bytes
        parameter_count: Number of parameters
        quantization: Quantization type (e.g., "Q4_0", "FP16")
        status: Current model status
        loaded_at: Timestamp when model was loaded
        last_used: Timestamp of last inference request
        memory_usage_mb: Current memory usage in MB
        gpu_layers: Number of layers loaded on GPU
        context_window: Maximum context window size
        metadata: Additional model metadata
    """
    
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    family: str = ""
    size_bytes: int = 0
    parameter_count: int = 0
    quantization: str = ""
    status: ModelStatus = ModelStatus.UNLOADED
    loaded_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    memory_usage_mb: float = 0.0
    gpu_layers: int = 0
    context_window: int = 2048
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate model entity after initialization."""
        if not self.name:
            raise ValueError("Model name cannot be empty")
        
        if self.parameter_count < 0:
            raise ValueError("Parameter count must be non-negative")
        
        if self.context_window <= 0:
            raise ValueError("Context window must be positive")
    
    def load(self, gpu_layers: int = 35) -> None:
        """
        Load the model into memory.
        
        Args:
            gpu_layers: Number of layers to load on GPU
            
        Raises:
            ValueError: If model is already loaded or loading
        """
        if self.status in (ModelStatus.READY, ModelStatus.LOADING):
            raise ValueError(f"Model is already {self.status.value}")
        
        self.status = ModelStatus.LOADING
        self.gpu_layers = gpu_layers
        self.loaded_at = datetime.utcnow()
    
    def mark_ready(self, memory_usage_mb: float) -> None:
        """
        Mark model as ready for inference.
        
        Args:
            memory_usage_mb: Memory usage after loading
        """
        if self.status != ModelStatus.LOADING:
            raise ValueError(f"Cannot mark model as ready from status: {self.status.value}")
        
        self.status = ModelStatus.READY
        self.memory_usage_mb = memory_usage_mb
    
    def unload(self) -> None:
        """Unload the model from memory."""
        if self.status != ModelStatus.READY:
            raise ValueError(f"Cannot unload model with status: {self.status.value}")
        
        self.status = ModelStatus.UNLOADING
    
    def mark_unloaded(self) -> None:
        """Mark model as unloaded."""
        self.status = ModelStatus.UNLOADED
        self.memory_usage_mb = 0.0
        self.gpu_layers = 0
        self.loaded_at = None
    
    def mark_error(self, error_message: str) -> None:
        """
        Mark model as error state.
        
        Args:
            error_message: Error description
        """
        self.status = ModelStatus.ERROR
        self.metadata["last_error"] = error_message
        self.metadata["error_timestamp"] = datetime.utcnow().isoformat()
    
    def update_usage(self) -> None:
        """Update last used timestamp."""
        self.last_used = datetime.utcnow()
    
    def is_loaded(self) -> bool:
        """Check if model is loaded and ready."""
        return self.status == ModelStatus.READY
    
    def can_handle_context(self, context_length: int) -> bool:
        """
        Check if model can handle given context length.
        
        Args:
            context_length: Required context length
            
        Returns:
            True if model can handle the context
        """
        return context_length <= self.context_window
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary representation."""
        return {
            "id": str(self.id),
            "name": self.name,
            "family": self.family,
            "size_bytes": self.size_bytes,
            "parameter_count": self.parameter_count,
            "quantization": self.quantization,
            "status": self.status.value,
            "loaded_at": self.loaded_at.isoformat() if self.loaded_at else None,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "memory_usage_mb": self.memory_usage_mb,
            "gpu_layers": self.gpu_layers,
            "context_window": self.context_window,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Model":
        """
        Create model from dictionary.
        
        Args:
            data: Dictionary representation
            
        Returns:
            Model instance
        """
        return cls(
            id=UUID(data["id"]) if "id" in data else uuid4(),
            name=data["name"],
            family=data.get("family", ""),
            size_bytes=data.get("size_bytes", 0),
            parameter_count=data.get("parameter_count", 0),
            quantization=data.get("quantization", ""),
            status=ModelStatus(data.get("status", "unloaded")),
            loaded_at=datetime.fromisoformat(data["loaded_at"]) if data.get("loaded_at") else None,
            last_used=datetime.fromisoformat(data["last_used"]) if data.get("last_used") else None,
            memory_usage_mb=data.get("memory_usage_mb", 0.0),
            gpu_layers=data.get("gpu_layers", 0),
            context_window=data.get("context_window", 2048),
            metadata=data.get("metadata", {}),
        )

