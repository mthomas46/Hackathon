"""Model configuration value object."""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass(frozen=True)
class ModelConfig:
    """
    Immutable value object for model configuration.
    
    Attributes:
        gpu_layers: Number of layers to load on GPU
        context_window: Maximum context window size
        num_threads: Number of CPU threads to use
        batch_size: Batch size for processing
        use_mmap: Use memory-mapped files
        use_mlock: Lock model in memory
        rope_freq_base: RoPE frequency base
        rope_freq_scale: RoPE frequency scale
    """
    
    gpu_layers: int = 35
    context_window: int = 2048
    num_threads: int = 8
    batch_size: int = 512
    use_mmap: bool = True
    use_mlock: bool = False
    rope_freq_base: float = 10000.0
    rope_freq_scale: float = 1.0
    
    def __post_init__(self):
        """Validate model configuration."""
        if self.gpu_layers < 0:
            raise ValueError("GPU layers must be non-negative")
        
        if self.context_window <= 0:
            raise ValueError("Context window must be positive")
        
        if self.num_threads <= 0:
            raise ValueError("Number of threads must be positive")
        
        if self.batch_size <= 0:
            raise ValueError("Batch size must be positive")
        
        if self.rope_freq_base <= 0:
            raise ValueError("RoPE frequency base must be positive")
        
        if self.rope_freq_scale <= 0:
            raise ValueError("RoPE frequency scale must be positive")
    
    @classmethod
    def for_gpu(cls, gpu_layers: int = 35) -> "ModelConfig":
        """Create configuration optimized for GPU inference."""
        return cls(
            gpu_layers=gpu_layers,
            context_window=4096,
            num_threads=4,
            batch_size=512,
            use_mmap=True,
            use_mlock=False,
        )
    
    @classmethod
    def for_cpu(cls) -> "ModelConfig":
        """Create configuration optimized for CPU inference."""
        return cls(
            gpu_layers=0,
            context_window=2048,
            num_threads=8,
            batch_size=256,
            use_mmap=True,
            use_mlock=False,
        )
    
    @classmethod
    def for_low_memory(cls) -> "ModelConfig":
        """Create configuration for low-memory systems."""
        return cls(
            gpu_layers=10,
            context_window=1024,
            num_threads=4,
            batch_size=128,
            use_mmap=True,
            use_mlock=False,
        )
    
    def to_ollama_options(self) -> Dict[str, Any]:
        """Convert to Ollama API options format."""
        return {
            "num_gpu": self.gpu_layers,
            "num_ctx": self.context_window,
            "num_thread": self.num_threads,
            "num_batch": self.batch_size,
            "use_mmap": self.use_mmap,
            "use_mlock": self.use_mlock,
            "rope_frequency_base": self.rope_freq_base,
            "rope_frequency_scale": self.rope_freq_scale,
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "gpu_layers": self.gpu_layers,
            "context_window": self.context_window,
            "num_threads": self.num_threads,
            "batch_size": self.batch_size,
            "use_mmap": self.use_mmap,
            "use_mlock": self.use_mlock,
            "rope_freq_base": self.rope_freq_base,
            "rope_freq_scale": self.rope_freq_scale,
        }

