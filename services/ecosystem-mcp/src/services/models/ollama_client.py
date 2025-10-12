"""
Ollama client for local LLM inference.

Optimized for Apple M4 Max with unified memory architecture.
"""

import asyncio
import logging
from typing import Optional, Dict, Any

import httpx

from ...config import settings

logger = logging.getLogger(__name__)


class OllamaClient:
    """
    Ollama client for local LLM inference.
    
    Optimized for M4 Max with fast inference on device.
    """
    
    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize Ollama client.
        
        Args:
            base_url: Ollama API base URL (uses settings if None)
        """
        self.base_url = base_url or settings.ollama_base_url
        self.timeout = settings.ollama_timeout
        self._available = None
        
        logger.info(f"Ollama client initialized: {self.base_url}")
    
    async def is_available(self) -> bool:
        """
        Check if Ollama is available.
        
        Returns:
            True if Ollama is accessible
        """
        if self._available is not None:
            return self._available
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                self._available = response.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama not available: {e}")
            self._available = False
        
        return self._available
    
    async def generate(
        self,
        prompt: str,
        model: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate text using Ollama model.
        
        Args:
            prompt: Input prompt
            model: Model name (e.g., "llama3.1:8b-instruct-q8_0")
            system: Optional system prompt
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
        
        Returns:
            Response dict with 'response', 'model', 'tokens', etc.
        """
        if not await self.is_available():
            from ...utils.exceptions import ModelError
            raise ModelError("Ollama is not available")
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
            }
        }
        
        if system:
            payload["system"] = system
        
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json=payload
            )
            response.raise_for_status()
            return response.json()
    
    @cache(ttl=3600, key_prefix="embedding")
    async def embed(
        self,
        text: str,
        model: Optional[str] = None
    ) -> list[float]:
        """
        Generate embeddings using Ollama (CACHED: 1 hour TTL).
        
        Embeddings are expensive to compute but deterministic,
        so we cache them aggressively with a 1-hour TTL.
        
        Args:
            text: Text to embed
            model: Embedding model (uses settings default if None)
        
        Returns:
            Embedding vector (cached if available)
        """
        if not await self.is_available():
            raise RuntimeError("Ollama is not available")
        
        embedding_model = model or settings.ollama_embedding_model
        
        payload = {
            "model": embedding_model,
            "input": text  # Fixed: Ollama embed API uses "input" not "prompt"
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/embed",
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            # Ollama returns "embeddings" (plural) array - get first one
            embeddings = data.get("embeddings", [])
            if not embeddings:
                raise RuntimeError(f"No embeddings returned for text: {text[:50]}...")
            return embeddings[0]
    
    async def list_models(self) -> list[str]:
        """
        List available models.
        
        Returns:
            List of model names
        """
        if not await self.is_available():
            return []
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            data = response.json()
            return [model["name"] for model in data.get("models", [])]


# Global instance
_ollama_client: Optional[OllamaClient] = None


def get_ollama_client() -> OllamaClient:
    """Get global Ollama client instance."""
    global _ollama_client
    if _ollama_client is None:
        _ollama_client = OllamaClient()
    return _ollama_client

