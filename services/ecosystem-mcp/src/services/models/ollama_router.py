"""
Ollama Router - 3-Tier Intelligent Routing System.

Routes requests to the optimal LLM instance based on:
- Query complexity (via ComplexityAnalyzer)
- Cursor IDE availability (Claude 4.5 Sonnet for extreme complexity)
- Desktop Ollama availability (GPU for heavy workloads)
- Docker Ollama (CPU fallback for light workloads)

Routing Priority:
1. Cursor IDE (Premium) → Extreme complexity (0.8-1.0)
2. Desktop Ollama (GPU) → Heavy complexity (0.4-0.8)
3. Docker Ollama (CPU) → Simple queries (0.0-0.4)
"""

import logging
from typing import Optional, Dict, Any
from enum import Enum

import httpx

from ...config import settings
from .ollama_client import OllamaClient
from .cursor_client import get_cursor_client
from .complexity_analyzer import get_complexity_analyzer

logger = logging.getLogger(__name__)


class LLMInstance(Enum):
    """Available LLM instances."""
    CURSOR = "cursor"    # Cursor IDE (Claude 4.5, premium)
    DESKTOP = "desktop"  # Desktop Ollama (GPU)
    DOCKER = "docker"    # Docker Ollama (CPU)


class OllamaRouter:
    """
    3-Tier Intelligent Router for LLM requests.
    
    Features:
    - Analyzes query complexity (0.0-1.0 scale)
    - Routes extreme complexity → Cursor IDE (Claude 4.5)
    - Routes heavy workloads → Desktop Ollama (GPU)
    - Routes light workloads → Docker Ollama (CPU)
    - Automatic fallback cascade
    - Health monitoring of all instances
    """
    
    def __init__(self):
        """Initialize 3-tier LLM router."""
        # Docker Ollama (always available)
        self.docker_client = OllamaClient(base_url=settings.ollama_base_url)
        
        # Desktop Ollama (optional, for heavy workloads)
        self.desktop_client = None
        self.desktop_available = False
        
        if settings.ollama_desktop_enabled:
            self.desktop_client = OllamaClient(base_url=settings.ollama_desktop_url)
        
        # Cursor IDE (optional, for extreme complexity)
        self.cursor_client = None
        self.cursor_available = False
        
        if settings.cursor_enabled:
            self.cursor_client = get_cursor_client()
        
        # Complexity analyzer
        self.complexity_analyzer = get_complexity_analyzer()
        
        logger.info(
            f"OllamaRouter initialized (3-tier): "
            f"Docker={settings.ollama_base_url}, "
            f"Desktop={'enabled' if settings.ollama_desktop_enabled else 'disabled'}, "
            f"Cursor={'enabled' if settings.cursor_enabled else 'disabled'}"
        )
    
    async def _check_desktop_availability(self) -> bool:
        """
        Check if desktop Ollama is available.
        
        Returns:
            True if desktop Ollama is accessible
        """
        if not self.desktop_client:
            return False
        
        try:
            self.desktop_available = await self.desktop_client.is_available()
            if self.desktop_available:
                logger.info(f"✅ Desktop Ollama available at {settings.ollama_desktop_url}")
            else:
                logger.warning(f"❌ Desktop Ollama not available at {settings.ollama_desktop_url}")
            return self.desktop_available
        except Exception as e:
            logger.warning(f"Desktop Ollama check failed: {e}")
            self.desktop_available = False
            return False
    
    async def _check_cursor_availability(self) -> bool:
        """
        Check if Cursor IDE is available.
        
        Returns:
            True if Cursor is accessible
        """
        if not self.cursor_client:
            return False
        
        try:
            self.cursor_available = await self.cursor_client.is_available()
            if self.cursor_available:
                logger.info(f"✅ Cursor IDE available at {settings.cursor_mcp_url}")
            else:
                logger.warning(f"❌ Cursor IDE not available at {settings.cursor_mcp_url}")
            return self.cursor_available
        except Exception as e:
            logger.warning(f"Cursor IDE check failed: {e}")
            self.cursor_available = False
            return False
    
    async def get_instance_for_complexity(
        self,
        complexity_score: float,
        prompt: str,
        workload_type: str = 'generation'
    ) -> tuple[Any, str, str]:
        """
        Get the appropriate LLM instance based on complexity score.
        
        Args:
            complexity_score: Complexity score (0.0-1.0)
            prompt: The query/prompt (for logging)
            workload_type: Type of workload ('rag', 'generation', etc.)
        
        Returns:
            Tuple of (client, model_name, instance_name)
        """
        # Refresh availability (cached, only checks periodically)
        if settings.cursor_enabled:
            await self._check_cursor_availability()
        if settings.ollama_desktop_enabled:
            await self._check_desktop_availability()
        
        # 🎯 SPECIAL CASE: RAG queries should prefer Desktop when available (for GPU acceleration)
        # RAG queries benefit significantly from GPU (3-5x faster) but may have low complexity scores
        if (workload_type == 'rag' and 
            settings.ollama_desktop_enabled and 
            settings.use_desktop_for_rag and
            self.desktop_available):
            
            logger.info(
                f"🎯 Routing RAG query to DESKTOP GPU (complexity={complexity_score:.2f}): "
                f"{prompt[:50]}..."
            )
            return self.desktop_client, settings.ollama_desktop_model, "desktop"
        
        # Tier 1: Extreme complexity → Cursor IDE (premium)
        if (settings.cursor_enabled and 
            self.cursor_available and 
            complexity_score >= settings.cursor_complexity_threshold):
            
            logger.info(
                f"🎯 Routing to CURSOR IDE (complexity={complexity_score:.2f}): "
                f"{prompt[:50]}..."
            )
            return self.cursor_client, settings.cursor_model, "cursor"
        
        # Tier 2: Heavy complexity → Desktop Ollama (GPU)
        if (settings.ollama_desktop_enabled and 
            self.desktop_available and 
            complexity_score >= 0.4):
            
            logger.info(
                f"🎯 Routing to DESKTOP GPU (complexity={complexity_score:.2f}): "
                f"{prompt[:50]}..."
            )
            return self.desktop_client, settings.ollama_desktop_model, "desktop"
        
        # Tier 3: Simple queries → Docker Ollama (CPU)
        logger.info(
            f"🎯 Routing to DOCKER CPU (complexity={complexity_score:.2f}): "
            f"{prompt[:50]}..."
        )
        return self.docker_client, settings.ollama_model_small, "docker"
    
    async def generate(
        self,
        prompt: str,
        workload_type: str = 'generation',
        model: Optional[str] = None,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        context: Optional[str] = None,
        context_docs: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Generate text using the optimal LLM instance.
        
        Args:
            prompt: The prompt to generate from
            workload_type: Type of workload ('rag', 'generation', 'embedding', etc.)
            model: Optional model override
            system: Optional system message
            temperature: LLM temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            context: Additional context for complexity analysis
            context_docs: Retrieved documents for complexity analysis
        
        Returns:
            Generated text and metadata
        """
        """
        Generate text using appropriate LLM instance based on complexity.
        
        Args:
            prompt: Input prompt
            workload_type: Type of workload ('rag', 'generation', etc.)
            model: Optional model override
            system: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            context: Optional context for complexity analysis
            context_docs: Optional documents for complexity analysis
        
        Returns:
            Generation response with 'response' key
        """
        # Analyze complexity
        complexity_score = self.complexity_analyzer.analyze(
            query=prompt,
            context=context,
            context_docs=context_docs,
            workload_type=workload_type
        )
        
        # Get appropriate instance
        client, default_model, instance_name = await self.get_instance_for_complexity(
            complexity_score, prompt, workload_type
        )
        model = model or default_model
        
        # Try primary instance
        try:
            response = await client.generate(
                prompt=prompt,
                model=model,
                system=system,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # Add routing metadata
            response["_routing"] = {
                "instance": instance_name,
                "complexity": complexity_score,
                "model": model
            }
            
            return response
            
        except Exception as e:
            logger.error(f"{instance_name.upper()} failed: {e}")
            
            # Cascade fallback: Cursor → Desktop → Docker
            if instance_name == "cursor" and settings.cursor_fallback_enabled:
                logger.warning("Falling back from Cursor to Desktop/Docker")
                if self.desktop_available:
                    return await self.desktop_client.generate(
                        prompt=prompt,
                        model=settings.ollama_desktop_model,
                        system=system,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                else:
                    return await self.docker_client.generate(
                        prompt=prompt,
                        model=settings.ollama_model_small,
                        system=system,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
            
            elif instance_name == "desktop":
                logger.warning("Falling back from Desktop to Docker")
                return await self.docker_client.generate(
                    prompt=prompt,
                    model=settings.ollama_model_small,
                    system=system,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
            
            else:
                # Docker failed, no fallback
                raise
    
    async def embed(
        self,
        text: str,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate embeddings (always uses Docker for consistency).
        
        Args:
            text: Text to embed
            model: Optional model override
        
        Returns:
            Embedding response
        """
        model = model or settings.ollama_embedding_model
        
        logger.debug(f"Generating embedding with Docker Ollama")
        
        return await self.docker_client.embed(
            text=text,
            model=model
        )
    
    async def get_status(self) -> Dict[str, Any]:
        """
        Get status of all LLM instances (3-tier).
        
        Returns:
            Status information for Docker, Desktop, and Cursor
        """
        status = {
            "routing": "3-tier",
            "complexity_threshold": settings.cursor_complexity_threshold,
            "docker": {
                "tier": 3,
                "url": settings.ollama_base_url,
                "available": await self.docker_client.is_available(),
                "model": settings.ollama_model_small,
                "use_case": "Simple queries (complexity < 0.4)"
            }
        }
        
        if settings.ollama_desktop_enabled:
            await self._check_desktop_availability()
            status["desktop"] = {
                "tier": 2,
                "url": settings.ollama_desktop_url,
                "available": self.desktop_available,
                "model": settings.ollama_desktop_model,
                "enabled": True,
                "use_case": f"Heavy queries (complexity 0.4-{settings.cursor_complexity_threshold})"
            }
        else:
            status["desktop"] = {
                "tier": 2,
                "enabled": False
            }
        
        if settings.cursor_enabled:
            await self._check_cursor_availability()
            status["cursor"] = {
                "tier": 1,
                "url": settings.cursor_mcp_url,
                "available": self.cursor_available,
                "model": settings.cursor_model,
                "enabled": True,
                "use_case": f"Extreme complexity (>{settings.cursor_complexity_threshold})",
                "fallback": settings.cursor_fallback_enabled
            }
        else:
            status["cursor"] = {
                "tier": 1,
                "enabled": False
            }
        
        return status
    
    async def list_models(self, instance: LLMInstance = LLMInstance.DOCKER) -> list[str]:
        """
        List available models on an instance.
        
        Args:
            instance: Which instance to query (CURSOR, DESKTOP, or DOCKER)
        
        Returns:
            List of model names
        """
        if instance == LLMInstance.CURSOR and self.cursor_client:
            try:
                return await self.cursor_client.get_models()
            except Exception as e:
                logger.error(f"Failed to list Cursor models: {e}")
                return []
        
        elif instance == LLMInstance.DESKTOP and self.desktop_client:
            try:
                return await self.desktop_client.list_models()
            except Exception as e:
                logger.error(f"Failed to list Desktop models: {e}")
                return []
        
        else:  # Docker or fallback
            try:
                return await self.docker_client.list_models()
            except Exception as e:
                logger.error(f"Failed to list Docker models: {e}")
                return []


# Singleton instance
_ollama_router: Optional[OllamaRouter] = None


def get_ollama_router() -> OllamaRouter:
    """
    Get the global Ollama router instance.
    
    Returns:
        OllamaRouter instance
    """
    global _ollama_router
    
    if _ollama_router is None:
        _ollama_router = OllamaRouter()
    
    return _ollama_router

