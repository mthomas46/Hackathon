"""
Path Resolver API Routes

Endpoints for resolving and validating host paths for ingestion.
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ...utils.host_path_resolver import (
    HostPathResolver,
    validate_ingestion_path,
    resolve_host_path
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Models
# ============================================================================

class PathResolveRequest(BaseModel):
    """Request to resolve a path."""
    path: str = Field(..., description="Path to resolve (host or container)")


class PathResolveResponse(BaseModel):
    """Response from path resolution."""
    original_path: str
    normalized_path: str
    container_path: str
    git_root: str | None
    is_git_repo: bool
    is_host_mount: bool
    relative_to_git: str | None
    mount_suggestion: str | None


class PathValidateResponse(BaseModel):
    """Response from path validation."""
    is_valid: bool
    message: str
    resolved_path: PathResolveResponse | None


# ============================================================================
# Endpoints
# ============================================================================

@router.post(
    "/resolve",
    response_model=PathResolveResponse,
    summary="Resolve host path",
    description="Resolve a host machine path to container-accessible path with git root detection"
)
async def resolve_path(request: PathResolveRequest):
    """
    Resolve a path from host machine to container format.
    
    Automatically detects:
    - Git repository root
    - Required mount points
    - Container-accessible paths
    
    Args:
        request: Path to resolve
    
    Returns:
        Resolved path information
    """
    try:
        resolved = resolve_host_path(request.path)
        
        # Get mount suggestion if needed
        mount_suggestion = None
        if resolved.is_host_mount:
            resolver = HostPathResolver()
            mount_suggestion = resolver.suggest_mount_config(request.path)
        
        return PathResolveResponse(
            original_path=resolved.original_path,
            normalized_path=resolved.normalized_path,
            container_path=resolved.container_path,
            git_root=resolved.git_root,
            is_git_repo=resolved.is_git_repo,
            is_host_mount=resolved.is_host_mount,
            relative_to_git=resolved.relative_to_git,
            mount_suggestion=mount_suggestion
        )
    
    except Exception as e:
        logger.error(f"Error resolving path: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/validate",
    response_model=PathValidateResponse,
    summary="Validate path for ingestion",
    description="Validate that a path is suitable for ingestion (git repo, accessible, secure)"
)
async def validate_path(request: PathResolveRequest):
    """
    Validate a path for ingestion.
    
    Checks:
    - Path exists and is accessible
    - Path is in a git repository
    - Path has required permissions
    - Path is not a sensitive system directory
    
    Args:
        request: Path to validate
    
    Returns:
        Validation result with details
    """
    try:
        is_valid, message, resolved = validate_ingestion_path(request.path)
        
        resolved_response = None
        if resolved:
            resolver = HostPathResolver()
            mount_suggestion = None
            if resolved.is_host_mount:
                mount_suggestion = resolver.suggest_mount_config(request.path)
            
            resolved_response = PathResolveResponse(
                original_path=resolved.original_path,
                normalized_path=resolved.normalized_path,
                container_path=resolved.container_path,
                git_root=resolved.git_root,
                is_git_repo=resolved.is_git_repo,
                is_host_mount=resolved.is_host_mount,
                relative_to_git=resolved.relative_to_git,
                mount_suggestion=mount_suggestion
            )
        
        return PathValidateResponse(
            is_valid=is_valid,
            message=message,
            resolved_path=resolved_response
        )
    
    except Exception as e:
        logger.error(f"Error validating path: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/mounts",
    response_model=Dict[str, Any],
    summary="Get configured mount points",
    description="Get list of configured host mount points"
)
async def get_mount_points():
    """
    Get configured mount points.
    
    Returns:
        Dictionary of container paths to host paths
    """
    try:
        resolver = HostPathResolver()
        
        return {
            "mount_points": resolver.host_mounts,
            "count": len(resolver.host_mounts)
        }
    
    except Exception as e:
        logger.error(f"Error getting mount points: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/suggest-mount",
    response_model=Dict[str, Any],
    summary="Get mount configuration suggestion",
    description="Get docker-compose mount configuration for a host path"
)
async def suggest_mount(request: PathResolveRequest):
    """
    Suggest docker-compose mount configuration for a path.
    
    Args:
        request: Path to get mount suggestion for
    
    Returns:
        Suggested docker-compose configuration
    """
    try:
        resolver = HostPathResolver()
        resolved = resolve_host_path(request.path)
        
        if not resolved.is_host_mount:
            return {
                "needs_mount": False,
                "message": "Path is already accessible in container",
                "container_path": resolved.container_path
            }
        
        mount_config = resolver.suggest_mount_config(request.path)
        
        return {
            "needs_mount": True,
            "git_root": resolved.git_root,
            "container_path": resolved.container_path,
            "mount_config": mount_config,
            "instructions": "Add the suggested volume mount to docker-compose.yml and restart the service"
        }
    
    except Exception as e:
        logger.error(f"Error suggesting mount: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

