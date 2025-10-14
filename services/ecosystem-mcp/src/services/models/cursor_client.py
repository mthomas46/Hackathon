"""
Cursor IDE Client - Communicates with Cursor via MCP for premium model access.

Enables ecosystem-mcp to leverage Cursor IDE's Claude 4.5 Sonnet and other
premium models for the most complex queries.
"""

import logging
from typing import Dict, Any, Optional
import httpx

from ...config import settings

logger = logging.getLogger(__name__)


class CursorClient:
    """
    Client for Cursor IDE integration via MCP.
    
    Features:
    - Access to Claude 4.5 Sonnet and other premium models
    - Uses user's Cursor credentials
    - Highest quality responses for most complex queries
    - Automatic fallback if unavailable
    """
    
    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize Cursor client.
        
        Args:
            base_url: Optional override for Cursor MCP URL
        """
        self.base_url = base_url or settings.cursor_mcp_url
        self.model = settings.cursor_model
        self.timeout = settings.ollama_timeout  # Reuse timeout setting
        self._available = None  # Cached availability status
        
        logger.info(f"CursorClient initialized: {self.base_url}, model={self.model}")
    
    async def is_available(self) -> bool:
        """
        Check if Cursor integration is configured.
        
        Note: Cursor IDE calls ecosystem-mcp via MCP (inbound), 
        not the other way around. This check only verifies if 
        the integration is enabled in config.
        
        Returns:
            True if Cursor integration is enabled
        """
        # Cursor IDE doesn't host an HTTP server that we can check.
        # The MCP integration allows Cursor to call US, not us calling Cursor.
        # So we can only check if the feature is enabled in config.
        from ...config import settings
        
        is_enabled = settings.cursor_enabled
        self._available = is_enabled
        
        if is_enabled:
            logger.info("✅ Cursor MCP integration enabled (Cursor can call ecosystem-mcp via MCP)")
        else:
            logger.debug("ℹ️ Cursor MCP integration disabled")
        
        return is_enabled
    
    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate text using Cursor IDE's model.
        
        Args:
            prompt: Input prompt
            model: Optional model override
            system: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
        
        Returns:
            Response dict with 'response' key
        
        Raises:
            httpx.HTTPError: If request fails
        """
        model = model or self.model
        
        logger.info(f"Generating with Cursor: model={model}, temp={temperature}")
        
        # Build request payload (MCP format)
        payload = {
            "model": model,
            "prompt": prompt,
            "temperature": temperature,
            "stream": False
        }
        
        if system:
            payload["system"] = system
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload
                )
                response.raise_for_status()
                
                data = response.json()
                
                logger.info(
                    f"Cursor response received: {len(data.get('response', ''))} chars"
                )
                
                return data
        
        except httpx.HTTPError as e:
            logger.error(f"Cursor request failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error with Cursor: {e}", exc_info=True)
            raise
    
    async def chat(
        self,
        messages: list[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Chat with Cursor IDE's model (conversational format).
        
        Args:
            messages: List of {"role": "user/assistant", "content": "..."}
            model: Optional model override
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
        
        Returns:
            Response dict with 'message' key
        """
        model = model or self.model
        
        logger.info(f"Chat with Cursor: {len(messages)} messages")
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": False
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload
                )
                response.raise_for_status()
                
                return response.json()
        
        except httpx.HTTPError as e:
            logger.error(f"Cursor chat failed: {e}")
            raise
    
    async def get_models(self) -> list[str]:
        """
        Get list of available models in Cursor.
        
        Returns:
            List of model names
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/api/models")
                response.raise_for_status()
                
                data = response.json()
                models = [model.get("name") for model in data.get("models", [])]
                
                logger.info(f"Cursor models: {models}")
                
                return models
        
        except Exception as e:
            logger.error(f"Failed to get Cursor models: {e}")
            return []


# Singleton instance
_cursor_client: Optional[CursorClient] = None


def get_cursor_client() -> CursorClient:
    """
    Get the global Cursor client instance.
    
    Returns:
        CursorClient instance
    """
    global _cursor_client
    
    if _cursor_client is None:
        _cursor_client = CursorClient()
    
    return _cursor_client

