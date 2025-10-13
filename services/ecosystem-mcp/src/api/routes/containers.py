"""
Docker container management endpoints.

Provides API for managing Docker containers in the ecosystem.
"""

import logging
from typing import Dict, Any, List
from datetime import datetime

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

try:
    import docker
    from docker.errors import DockerException, NotFound, APIError
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False

logger = logging.getLogger(__name__)

router = APIRouter()


class ContainerAction(BaseModel):
    """Request model for container actions."""
    action: str = Field(..., description="Action to perform: start, stop, restart, pause, unpause")
    container_name: str = Field(..., description="Name or ID of container")


class ContainerListResponse(BaseModel):
    """Response model for container list."""
    containers: List[Dict[str, Any]]
    total: int


class ContainerActionResponse(BaseModel):
    """Response model for container actions."""
    success: bool
    message: str
    container_name: str
    action: str
    timestamp: str


def get_docker_client():
    """Get Docker client with error handling."""
    if not DOCKER_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Docker SDK not available. Install docker-py to use this feature."
        )
    
    try:
        client = docker.from_env()
        client.ping()
        return client
    except DockerException as e:
        raise HTTPException(
            status_code=503,
            detail=f"Cannot connect to Docker daemon: {str(e)}"
        )


@router.get(
    "/containers",
    response_model=ContainerListResponse,
    summary="List all Docker containers",
    description="Get list of all Docker containers (running and stopped)"
)
async def list_containers():
    """
    List all Docker containers.
    
    Returns:
        List of containers with their status, names, and details.
    """
    try:
        client = get_docker_client()
        containers = client.containers.list(all=True)
        
        container_list = []
        for container in containers:
            try:
                stats = container.stats(stream=False) if container.status == "running" else {}
                
                container_info = {
                    "id": container.id[:12],
                    "name": container.name,
                    "short_id": container.short_id,
                    "status": container.status,
                    "state": container.attrs.get("State", {}).get("Status", "unknown"),
                    "image": container.image.tags[0] if container.image.tags else container.image.id[:12],
                    "created": container.attrs.get("Created", ""),
                    "ports": container.ports,
                    "labels": container.labels,
                    "network_mode": container.attrs.get("HostConfig", {}).get("NetworkMode", ""),
                }
                
                # Add resource usage if running
                if container.status == "running" and stats:
                    memory_stats = stats.get("memory_stats", {})
                    cpu_stats = stats.get("cpu_stats", {})
                    
                    if memory_stats and "usage" in memory_stats:
                        container_info["memory_usage_mb"] = memory_stats["usage"] / 1024 / 1024
                        if "limit" in memory_stats:
                            container_info["memory_limit_mb"] = memory_stats["limit"] / 1024 / 1024
                            container_info["memory_percent"] = (memory_stats["usage"] / memory_stats["limit"]) * 100
                
                container_list.append(container_info)
            
            except Exception as e:
                logger.warning(f"Error getting stats for container {container.name}: {e}")
                container_list.append({
                    "id": container.id[:12],
                    "name": container.name,
                    "status": container.status,
                    "error": str(e)
                })
        
        return ContainerListResponse(
            containers=container_list,
            total=len(container_list)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing containers: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list containers: {str(e)}"
        )


@router.get(
    "/containers/{container_name}",
    summary="Get container details",
    description="Get detailed information about a specific container"
)
async def get_container(container_name: str):
    """
    Get detailed information about a specific container.
    
    Args:
        container_name: Name or ID of the container
    
    Returns:
        Detailed container information including logs, stats, and configuration.
    """
    try:
        client = get_docker_client()
        container = client.containers.get(container_name)
        
        # Get container details
        details = {
            "id": container.id,
            "name": container.name,
            "short_id": container.short_id,
            "status": container.status,
            "image": container.image.tags[0] if container.image.tags else container.image.id,
            "created": container.attrs.get("Created"),
            "started": container.attrs.get("State", {}).get("StartedAt"),
            "finished": container.attrs.get("State", {}).get("FinishedAt"),
            "ports": container.ports,
            "environment": container.attrs.get("Config", {}).get("Env", []),
            "labels": container.labels,
            "mounts": [m for m in container.attrs.get("Mounts", [])],
            "network_settings": container.attrs.get("NetworkSettings", {}),
            "restart_count": container.attrs.get("RestartCount", 0),
        }
        
        # Get stats if running
        if container.status == "running":
            try:
                stats = container.stats(stream=False)
                details["stats"] = {
                    "memory": stats.get("memory_stats", {}),
                    "cpu": stats.get("cpu_stats", {}),
                    "networks": stats.get("networks", {}),
                }
            except Exception as e:
                logger.warning(f"Could not get stats: {e}")
        
        # Get recent logs (last 100 lines)
        try:
            logs = container.logs(tail=100, timestamps=True).decode("utf-8", errors="ignore")
            details["recent_logs"] = logs.split("\n")[-100:]
        except Exception as e:
            logger.warning(f"Could not get logs: {e}")
            details["recent_logs"] = []
        
        return JSONResponse(content=details)
    
    except NotFound:
        raise HTTPException(
            status_code=404,
            detail=f"Container '{container_name}' not found"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting container details: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get container details: {str(e)}"
        )


@router.post(
    "/containers/action",
    response_model=ContainerActionResponse,
    summary="Perform action on container",
    description="Start, stop, restart, pause, or unpause a container"
)
async def container_action(action_request: ContainerAction):
    """
    Perform an action on a Docker container.
    
    Supported actions:
    - start: Start a stopped container
    - stop: Stop a running container
    - restart: Restart a container
    - pause: Pause a running container
    - unpause: Unpause a paused container
    
    Args:
        action_request: Action details (action type and container name)
    
    Returns:
        Result of the action with success status and message.
    """
    valid_actions = ["start", "stop", "restart", "pause", "unpause"]
    
    if action_request.action not in valid_actions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid action '{action_request.action}'. Must be one of: {', '.join(valid_actions)}"
        )
    
    try:
        client = get_docker_client()
        container = client.containers.get(action_request.container_name)
        
        logger.info(f"Performing '{action_request.action}' on container '{container.name}'")
        
        # Perform the action
        if action_request.action == "start":
            container.start()
            message = f"Container '{container.name}' started successfully"
        
        elif action_request.action == "stop":
            container.stop(timeout=10)
            message = f"Container '{container.name}' stopped successfully"
        
        elif action_request.action == "restart":
            container.restart(timeout=10)
            message = f"Container '{container.name}' restarted successfully"
        
        elif action_request.action == "pause":
            container.pause()
            message = f"Container '{container.name}' paused successfully"
        
        elif action_request.action == "unpause":
            container.unpause()
            message = f"Container '{container.name}' unpaused successfully"
        
        return ContainerActionResponse(
            success=True,
            message=message,
            container_name=container.name,
            action=action_request.action,
            timestamp=datetime.now().isoformat()
        )
    
    except NotFound:
        raise HTTPException(
            status_code=404,
            detail=f"Container '{action_request.container_name}' not found"
        )
    except APIError as e:
        logger.error(f"Docker API error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Docker operation failed: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error performing container action: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to perform action: {str(e)}"
        )


@router.get(
    "/containers/{container_name}/logs",
    summary="Get container logs",
    description="Get logs from a specific container"
)
async def get_container_logs(
    container_name: str,
    tail: int = 100,
    since: str = None,
    timestamps: bool = True
):
    """
    Get logs from a specific container.
    
    Args:
        container_name: Name or ID of the container
        tail: Number of lines to retrieve from the end (default: 100)
        since: Show logs since timestamp (ISO format) or relative (e.g., "5m")
        timestamps: Include timestamps in logs
    
    Returns:
        Container logs as a list of lines.
    """
    try:
        client = get_docker_client()
        container = client.containers.get(container_name)
        
        log_kwargs = {
            "tail": tail,
            "timestamps": timestamps
        }
        
        if since:
            log_kwargs["since"] = since
        
        logs = container.logs(**log_kwargs).decode("utf-8", errors="ignore")
        log_lines = logs.split("\n")
        
        return JSONResponse(content={
            "container": container.name,
            "lines": len(log_lines),
            "logs": log_lines
        })
    
    except NotFound:
        raise HTTPException(
            status_code=404,
            detail=f"Container '{container_name}' not found"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting container logs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get container logs: {str(e)}"
        )


@router.get(
    "/containers/{container_name}/stats",
    summary="Get container resource stats",
    description="Get real-time resource usage statistics for a container"
)
async def get_container_stats(container_name: str):
    """
    Get real-time resource usage statistics for a container.
    
    Args:
        container_name: Name or ID of the container
    
    Returns:
        Resource usage statistics (CPU, memory, network, disk I/O).
    """
    try:
        client = get_docker_client()
        container = client.containers.get(container_name)
        
        if container.status != "running":
            raise HTTPException(
                status_code=400,
                detail=f"Container '{container_name}' is not running (status: {container.status})"
            )
        
        stats = container.stats(stream=False)
        
        # Parse stats
        memory_stats = stats.get("memory_stats", {})
        cpu_stats = stats.get("cpu_stats", {})
        precpu_stats = stats.get("precpu_stats", {})
        
        parsed_stats = {
            "container": container.name,
            "timestamp": datetime.now().isoformat(),
            "memory": {
                "usage_bytes": memory_stats.get("usage", 0),
                "usage_mb": memory_stats.get("usage", 0) / 1024 / 1024,
                "limit_bytes": memory_stats.get("limit", 0),
                "limit_mb": memory_stats.get("limit", 0) / 1024 / 1024,
                "percent": (memory_stats.get("usage", 0) / memory_stats.get("limit", 1)) * 100 if memory_stats.get("limit") else 0
            },
            "cpu": {
                "total_usage": cpu_stats.get("cpu_usage", {}).get("total_usage", 0),
                "system_cpu_usage": cpu_stats.get("system_cpu_usage", 0),
                "online_cpus": cpu_stats.get("online_cpus", 0)
            },
            "network": stats.get("networks", {}),
            "blkio": stats.get("blkio_stats", {})
        }
        
        return JSONResponse(content=parsed_stats)
    
    except NotFound:
        raise HTTPException(
            status_code=404,
            detail=f"Container '{container_name}' not found"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting container stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get container stats: {str(e)}"
        )

