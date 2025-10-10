"""
Claude (Anthropic) client for high-quality AI responses.

Used for complex reasoning tasks that require the best model.
"""

import logging
from typing import Optional, Dict, Any

from ...config import settings

logger = logging.getLogger(__name__)


class ClaudeClient:
    """
    Claude API client.
    
    Used for complex tasks requiring advanced reasoning.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Claude client.
        
        Args:
            api_key: Anthropic API key (uses settings if None)
        """
        self.api_key = api_key or settings.anthropic_api_key
        self._available = bool(self.api_key)
        
        if self._available:
            # Lazy import to avoid dependency if not using Claude
            try:
                import anthropic
                self.client = anthropic.AsyncAnthropic(api_key=self.api_key)
            except ImportError:
                logger.warning("anthropic package not installed")
                self._available = False
        
        logger.info(f"Claude client initialized: {'available' if self._available else 'not available'}")
    
    def is_available(self) -> bool:
        """Check if Claude is available."""
        return self._available
    
    async def generate(
        self,
        prompt: str,
        model: str = "claude-3-5-sonnet-20241022",
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        """
        Generate text using Claude.
        
        Args:
            prompt: Input prompt
            model: Claude model name
            system: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
        
        Returns:
            Response dict with 'content', 'usage', etc.
        """
        if not self.is_available():
            raise RuntimeError("Claude is not available (no API key)")
        
        messages = [{"role": "user", "content": prompt}]
        
        kwargs = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        
        if system:
            kwargs["system"] = system
        
        response = await self.client.messages.create(**kwargs)
        
        return {
            "content": response.content[0].text,
            "model": response.model,
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
            "stop_reason": response.stop_reason,
        }
    
    def calculate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        model: str = "claude-3-5-sonnet-20241022"
    ) -> float:
        """
        Calculate cost for Claude API call.
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            model: Model name
        
        Returns:
            Cost in USD
        """
        # Pricing as of 2024 (per million tokens)
        pricing = {
            "claude-opus": {"input": 15.0, "output": 75.0},
            "claude-sonnet": {"input": 3.0, "output": 15.0},
            "claude-haiku": {"input": 0.25, "output": 1.25},
        }
        
        # Map full model names to pricing keys
        if "opus" in model.lower():
            key = "claude-opus"
        elif "sonnet" in model.lower():
            key = "claude-sonnet"
        elif "haiku" in model.lower():
            key = "claude-haiku"
        else:
            key = "claude-sonnet"  # Default
        
        rates = pricing[key]
        input_cost = (input_tokens / 1_000_000) * rates["input"]
        output_cost = (output_tokens / 1_000_000) * rates["output"]
        
        return input_cost + output_cost


# Global instance
_claude_client: Optional[ClaudeClient] = None


def get_claude_client() -> ClaudeClient:
    """Get global Claude client instance."""
    global _claude_client
    if _claude_client is None:
        _claude_client = ClaudeClient()
    return _claude_client

