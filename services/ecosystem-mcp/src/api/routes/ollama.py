"""
Ollama direct query endpoints.

Provides direct access to Ollama for testing and validation.
"""

import logging
from typing import Optional, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ...services.models.ollama_client import get_ollama_client
from ...config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


class OllamaRequest(BaseModel):
    """Ollama generation request."""
    prompt: str = Field(..., description="Prompt text", min_length=1)
    model: Optional[str] = Field(None, description="Model name (uses default if None)")
    system: Optional[str] = Field(None, description="System prompt")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Temperature")
    max_tokens: int = Field(500, ge=1, le=4096, description="Maximum tokens")


class OllamaResponse(BaseModel):
    """Ollama generation response."""
    response: str
    model: str
    context_length: int
    eval_count: int
    eval_duration_ms: int


class OllamaModel(BaseModel):
    """Ollama model information."""
    name: str
    size: str
    modified: str


class OllamaStatus(BaseModel):
    """Ollama service status."""
    available: bool
    url: str
    models: List[str]


@router.get(
    "/status",
    response_model=OllamaStatus,
    summary="Get Ollama status",
    description="Check if Ollama is available and list models"
)
async def get_ollama_status():
    """
    Get Ollama service status.
    
    Returns:
        Ollama availability and available models
    """
    client = get_ollama_client()
    
    try:
        # Check if available
        is_available = await client.is_available()
        
        # Get model list
        models = []
        if is_available:
            try:
                model_list = await client.list_models()
                models = [m["name"] for m in model_list.get("models", [])]
            except:
                pass
        
        return OllamaStatus(
            available=is_available,
            url=settings.ollama_base_url,
            models=models
        )
    except Exception as e:
        logger.error(f"Failed to get Ollama status: {e}")
        raise HTTPException(status_code=503, detail=f"Ollama unavailable: {e}")


@router.post(
    "/generate",
    response_model=OllamaResponse,
    summary="Generate with Ollama",
    description="Generate text using Ollama"
)
async def generate_with_ollama(request: OllamaRequest):
    """
    Generate text using Ollama.
    
    Args:
        request: Generation request with prompt and parameters
    
    Returns:
        Generated text and metadata
    """
    client = get_ollama_client()
    
    # Check availability
    if not await client.is_available():
        raise HTTPException(
            status_code=503,
            detail="Ollama is not available. Check if service is running."
        )
    
    # Use default model if not specified
    model = request.model or settings.ollama_model_medium
    
    try:
        result = await client.generate(
            prompt=request.prompt,
            model=model,
            system=request.system,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        return OllamaResponse(
            response=result.get("response", ""),
            model=result.get("model", model),
            context_length=result.get("context", 0),
            eval_count=result.get("eval_count", 0),
            eval_duration_ms=result.get("eval_duration", 0) // 1000000  # ns to ms
        )
    except Exception as e:
        logger.error(f"Ollama generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Generation failed: {e}")


@router.get(
    "/models",
    summary="List Ollama models",
    description="List all available Ollama models"
)
async def list_ollama_models():
    """
    List all available Ollama models.
    
    Returns:
        List of models with metadata
    """
    client = get_ollama_client()
    
    if not await client.is_available():
        raise HTTPException(status_code=503, detail="Ollama is not available")
    
    try:
        models = await client.list_models()
        return models
    except Exception as e:
        logger.error(f"Failed to list models: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list models: {e}")


@router.post(
    "/pull",
    summary="Pull Ollama model",
    description="Pull a model from Ollama library"
)
async def pull_ollama_model(
    model: str = Field(..., description="Model name to pull")
):
    """
    Pull a model from Ollama library.
    
    Args:
        model: Model name (e.g., 'mistral', 'llama3.1')
    
    Returns:
        Pull status
    """
    client = get_ollama_client()
    
    if not await client.is_available():
        raise HTTPException(status_code=503, detail="Ollama is not available")
    
    try:
        # Note: This is a long-running operation
        # In production, this should be async/background task
        result = await client.pull_model(model)
        return {"status": "success", "model": model, "details": result}
    except Exception as e:
        logger.error(f"Failed to pull model: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to pull model: {e}")


@router.post(
    "/embed",
    summary="Generate embeddings",
    description="Generate embeddings using Ollama"
)
async def generate_embedding(
    text: str = Field(..., description="Text to embed"),
    model: Optional[str] = Field(None, description="Embedding model")
):
    """
    Generate embeddings using Ollama.
    
    Args:
        text: Text to embed
        model: Optional embedding model (uses default if None)
    
    Returns:
        Embedding vector
    """
    client = get_ollama_client()
    
    if not await client.is_available():
        raise HTTPException(status_code=503, detail="Ollama is not available")
    
    model = model or settings.ollama_embedding_model
    
    try:
        embedding = await client.generate_embedding(text, model)
        return {
            "model": model,
            "embedding": embedding,
            "dimensions": len(embedding)
        }
    except Exception as e:
        logger.error(f"Failed to generate embedding: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate embedding: {e}")

