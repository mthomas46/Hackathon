"""
LLM Router Status endpoint - Monitor 3-tier LLM routing system.

Tracks:
- Cursor IDE (Tier 1: Premium models for extreme complexity)
- Desktop Ollama (Tier 2: GPU for heavy workloads)
- Docker Ollama (Tier 3: CPU for simple queries)
"""

import logging
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...services.models.ollama_router import get_ollama_router, LLMInstance

logger = logging.getLogger(__name__)

router = APIRouter()


class LLMInstanceStatus(BaseModel):
    """Status of an LLM instance."""
    tier: int
    url: str | None = None
    available: bool | None = None
    model: str | None = None
    enabled: bool = True
    use_case: str | None = None
    fallback: bool | None = None


class LLMStatusResponse(BaseModel):
    """Response from LLM status endpoint (3-tier)."""
    routing: str
    complexity_threshold: float
    cursor: LLMInstanceStatus
    desktop: LLMInstanceStatus
    docker: LLMInstanceStatus


@router.get(
    "/llm/status",
    response_model=LLMStatusResponse,
    summary="Get 3-tier LLM router status",
    description="Check availability and configuration of all LLM instances (Cursor, Desktop, Docker)"
)
async def get_llm_status():
    """
    Get status of 3-tier LLM routing system.
    
    Returns information about:
    - Cursor IDE (Tier 1: Claude 4.5, premium)
    - Desktop Ollama (Tier 2: GPU acceleration)
    - Docker Ollama (Tier 3: CPU fallback)
    
    Example response:
    ```json
    {
        "routing": "3-tier",
        "complexity_threshold": 0.7,
        "cursor": {
            "tier": 1,
            "url": "http://localhost:3000",
            "available": true,
            "model": "claude-4.5-sonnet",
            "enabled": true,
            "use_case": "Extreme complexity (>0.7)",
            "fallback": true
        },
        "desktop": {
            "tier": 2,
            "url": "http://localhost:11435",
            "available": true,
            "model": "llama3.1:8b",
            "enabled": true,
            "use_case": "Heavy queries (complexity 0.4-0.7)"
        },
        "docker": {
            "tier": 3,
            "url": "http://localhost:11434",
            "available": true,
            "model": "llama3.2:3b",
            "use_case": "Simple queries (complexity < 0.4)"
        }
    }
    ```
    """
    try:
        router_instance = get_ollama_router()
        status = await router_instance.get_status()
        
        return LLMStatusResponse(
            routing=status["routing"],
            complexity_threshold=status["complexity_threshold"],
            cursor=LLMInstanceStatus(**status["cursor"]),
            desktop=LLMInstanceStatus(**status["desktop"]),
            docker=LLMInstanceStatus(**status["docker"])
        )
    except Exception as e:
        logger.error(f"Failed to get LLM status: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve LLM status: {str(e)}"
        )


@router.get(
    "/llm/models/{instance}",
    summary="List models on LLM instance",
    description="List available models on Cursor, Desktop, or Docker"
)
async def list_models(instance: str):
    """
    List available models on an LLM instance.
    
    Args:
        instance: Either 'cursor', 'desktop', or 'docker'
    
    Returns:
        List of model names
    """
    try:
        instance_lower = instance.lower()
        if instance_lower not in ['cursor', 'desktop', 'docker']:
            raise HTTPException(
                status_code=400,
                detail="Instance must be 'cursor', 'desktop', or 'docker'"
            )
        
        router_instance = get_ollama_router()
        
        # Map string to enum
        if instance_lower == 'cursor':
            llm_instance = LLMInstance.CURSOR
        elif instance_lower == 'desktop':
            llm_instance = LLMInstance.DESKTOP
        else:
            llm_instance = LLMInstance.DOCKER
        
        models = await router_instance.list_models(llm_instance)
        
        return {
            "instance": instance_lower,
            "models": models,
            "count": len(models)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list models on {instance}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list models: {str(e)}"
        )

