"""Generation parameters value object."""

from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class GenerationParams:
    """
    Immutable value object for text generation parameters.
    
    Attributes:
        temperature: Sampling temperature (0.0-2.0)
        top_p: Nucleus sampling parameter (0.0-1.0)
        top_k: Top-k sampling parameter (positive integer)
        repeat_penalty: Repetition penalty (typically 1.0-1.5)
        max_tokens: Maximum tokens to generate
        stop_sequences: List of stop sequences
        seed: Random seed for reproducibility
    """
    
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40
    repeat_penalty: float = 1.1
    max_tokens: int = 512
    stop_sequences: List[str] = None
    seed: Optional[int] = None
    
    def __post_init__(self):
        """Validate generation parameters."""
        # Use object.__setattr__ for frozen dataclass
        if self.stop_sequences is None:
            object.__setattr__(self, 'stop_sequences', [])
        
        if not (0.0 <= self.temperature <= 2.0):
            raise ValueError("Temperature must be between 0.0 and 2.0")
        
        if not (0.0 <= self.top_p <= 1.0):
            raise ValueError("Top-p must be between 0.0 and 1.0")
        
        if self.top_k <= 0:
            raise ValueError("Top-k must be positive")
        
        if self.repeat_penalty < 1.0:
            raise ValueError("Repeat penalty must be >= 1.0")
        
        if self.max_tokens <= 0:
            raise ValueError("Max tokens must be positive")
    
    @classmethod
    def default(cls) -> "GenerationParams":
        """Create default generation parameters."""
        return cls()
    
    @classmethod
    def creative(cls) -> "GenerationParams":
        """Create parameters for creative generation."""
        return cls(
            temperature=0.9,
            top_p=0.95,
            top_k=50,
            repeat_penalty=1.0,
            max_tokens=1024,
        )
    
    @classmethod
    def precise(cls) -> "GenerationParams":
        """Create parameters for precise/deterministic generation."""
        return cls(
            temperature=0.2,
            top_p=0.8,
            top_k=20,
            repeat_penalty=1.2,
            max_tokens=512,
        )
    
    @classmethod
    def balanced(cls) -> "GenerationParams":
        """Create balanced parameters."""
        return cls(
            temperature=0.5,
            top_p=0.85,
            top_k=30,
            repeat_penalty=1.15,
            max_tokens=768,
        )
    
    def to_dict(self):
        """Convert to dictionary for API serialization."""
        return {
            "temperature": self.temperature,
            "top_p": self.top_p,
            "top_k": self.top_k,
            "repeat_penalty": self.repeat_penalty,
            "max_tokens": self.max_tokens,
            "stop_sequences": self.stop_sequences,
            "seed": self.seed,
        }

