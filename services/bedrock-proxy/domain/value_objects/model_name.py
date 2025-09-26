"""Model Name value object."""

import re
from typing import List


class ModelName:
    """Value object representing an AI model name."""

    # Valid AWS Bedrock model patterns
    VALID_PATTERNS = [
        r'amazon\.titan-.*',
        r'anthropic\.claude-.*',
        r'meta\.llama.*',
        r'ai21\.j2-.*',
        r'stability\.sd.*',
        r'cohere\.command-.*',
        r'mistral\..*'
    ]

    def __init__(self, value: str):
        """Initialize ModelName.

        Args:
            value: String representing the model name

        Raises:
            ValueError: If the model name is invalid
        """
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Model name must be a non-empty string")

        self._value = value.strip()

        # Validate against known patterns (but allow custom models)
        if not self._is_valid_pattern(self._value):
            # Log warning but allow - new models may not be in our list yet
            pass

    def _is_valid_pattern(self, name: str) -> bool:
        """Check if the model name matches known patterns."""
        for pattern in self.VALID_PATTERNS:
            if re.match(pattern, name, re.IGNORECASE):
                return True
        return False

    @property
    def value(self) -> str:
        """Get the model name value."""
        return self._value

    @property
    def provider(self) -> str:
        """Extract provider from model name."""
        parts = self._value.split('.')
        return parts[0] if len(parts) > 1 else 'unknown'

    @property
    def model_family(self) -> str:
        """Extract model family from model name."""
        if 'titan' in self._value.lower():
            return 'titan'
        elif 'claude' in self._value.lower():
            return 'claude'
        elif 'llama' in self._value.lower():
            return 'llama'
        elif 'j2' in self._value.lower():
            return 'j2'
        elif 'sd' in self._value.lower():
            return 'stable-diffusion'
        elif 'command' in self._value.lower():
            return 'command'
        elif 'mistral' in self._value.lower():
            return 'mistral'
        else:
            return 'unknown'

    def __str__(self) -> str:
        """String representation."""
        return self._value

    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"ModelName({self._value})"

    def __eq__(self, other) -> bool:
        """Check equality."""
        if not isinstance(other, ModelName):
            return False
        return self._value == other._value

    def __hash__(self) -> int:
        """Hash for use in sets and dictionaries."""
        return hash(self._value)

    @classmethod
    def from_provider_and_model(cls, provider: str, model: str) -> 'ModelName':
        """Create from provider and model parts."""
        return cls(f"{provider}.{model}")
