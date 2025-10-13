"""
Docker container management endpoints.

Provides API for managing Docker containers in the ecosystem.
Uses subprocess calls to docker CLI for reliability.
"""

import logging
import json
import subprocess
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, status, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

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


def run_docker_command(args: List[str], check: bool = True) -> subprocess.CompletedProcess:
    """
    Run a docker command using subprocess.
    
    Args:
        args: Docker command arguments (without 'docker' prefix)
        check: Whether to raise exception on non-zero exit code
    
    Returns:
        CompletedProcess result
    
    Raises:
        HTTPException: If Docker command fails
    """
    try:
        result = subprocess.run(
            ["docker"] + args,
            capture_output=True,
            text=True,
            check=check,
            timeout=30
        )
        return result
    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=504,
            detail="Docker command timed out"
        )
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.strip() if e.stderr else str(e)
        logger.error(f"Docker command failed: {error_msg}")
        raise HTTPException(
            status_code=503,
            detail=f"Docker command failed: {error_msg}"
        )
    except FileNotFoundError:
        raise HTTPException(
            status_code=503,
            detail="Docker CLI not found. Ensure Docker is installed."
        )
    except Exception as e:
        logger.error(f"Error running docker command: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error executing docker command: {str(e)}"
        )


@router.get(
    "/containers",
    response_model=ContainerListResponse,
    summary="List all Docker containers",
    description="Get list of all Docker containers (running and stopped)"
)
async def list_containers():
    """
    List all Docker containers using docker ps.
    
    Returns:
        List of containers with their status, names, and details.
    """
    try:
        # Use docker ps with JSON format for easy parsing
        result = run_docker_command([
            "ps", "-a",
            "--format", "{{json .}}",
            "--no-trunc"
        ])
        
        container_list = []
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            
            try:
                container_data = json.loads(line)
                
                # Get detailed info with docker inspect
                inspect_result = run_docker_command(["inspect", container_data.get("ID", container_data.get("Names", ""))])
                inspect_data = json.loads(inspect_result.stdout)
                
                if inspect_data:
                    container_info = inspect_data[0]
                    
                    # Parse ports
                    ports = {}
                    if container_info.get("NetworkSettings", {}).get("Ports"):
                        ports = container_info["NetworkSettings"]["Ports"]
                    
                    container_list.append({
                        "id": container_info["Id"][:12],
                        "name": container_info["Name"].lstrip("/"),
                        "short_id": container_info["Id"][:12],
                        "status": container_info["State"]["Status"],
                        "state": container_info["State"]["Status"],
                        "image": container_info["Config"]["Image"],
                        "created": container_info["Created"],
                        "ports": ports,
                        "labels": container_info["Config"].get("Labels", {}),
                        "network_mode": container_info["HostConfig"].get("NetworkMode", ""),
                    })
            
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse container JSON: {e}")
                continue
            except Exception as e:
                logger.warning(f"Error processing container: {e}")
                continue
        
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
    Get detailed information about a specific container using docker inspect.
    
    Args:
        container_name: Name or ID of the container
    
    Returns:
        Detailed container information.
    """
    try:
        # Get container details with docker inspect
        result = run_docker_command(["inspect", container_name])
        inspect_data = json.loads(result.stdout)
        
        if not inspect_data:
            raise HTTPException(
                status_code=404,
                detail=f"Container '{container_name}' not found"
            )
        
        container = inspect_data[0]
        
        # Build response
        details = {
            "id": container["Id"],
            "name": container["Name"].lstrip("/"),
            "short_id": container["Id"][:12],
            "status": container["State"]["Status"],
            "image": container["Config"]["Image"],
            "created": container["Created"],
            "started": container["State"].get("StartedAt"),
            "finished": container["State"].get("FinishedAt"),
            "ports": container["NetworkSettings"].get("Ports", {}),
            "environment": container["Config"].get("Env", []),
            "labels": container["Config"].get("Labels", {}),
            "mounts": container.get("Mounts", []),
            "network_settings": container.get("NetworkSettings", {}),
            "restart_count": container.get("RestartCount", 0),
        }
        
        # Get stats if running
        if container["State"]["Status"] == "running":
            try:
                stats_result = run_docker_command([
                    "stats", container_name,
                    "--no-stream", "--format", "{{json .}}"
                ])
                if stats_result.stdout.strip():
                    stats_data = json.loads(stats_result.stdout)
                    details["stats"] = stats_data
            except Exception as e:
                logger.warning(f"Could not get stats: {e}")
        
        return JSONResponse(content=details)
    
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
    Perform an action on a Docker container using docker CLI.
    
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
        logger.info(f"Performing '{action_request.action}' on container '{action_request.container_name}'")
        
        # Execute the docker command
        if action_request.action == "stop":
            # Add timeout for stop command
            run_docker_command(["stop", "-t", "10", action_request.container_name])
        elif action_request.action == "restart":
            # Add timeout for restart command
            run_docker_command(["restart", "-t", "10", action_request.container_name])
        else:
            # start, pause, unpause don't need timeout
            run_docker_command([action_request.action, action_request.container_name])
        
        message = f"Container '{action_request.container_name}' {action_request.action}ed successfully"
        
        return ContainerActionResponse(
            success=True,
            message=message,
            container_name=action_request.container_name,
            action=action_request.action,
            timestamp=datetime.now().isoformat()
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
    tail: int = Query(100, description="Number of lines to retrieve from the end"),
    since: Optional[str] = Query(None, description="Show logs since timestamp or relative time"),
    timestamps: bool = Query(True, description="Include timestamps in logs")
):
    """
    Get logs from a specific container using docker logs.
    
    Args:
        container_name: Name or ID of the container
        tail: Number of lines to retrieve from the end (default: 100)
        since: Show logs since timestamp (ISO format) or relative (e.g., "5m")
        timestamps: Include timestamps in logs
    
    Returns:
        Container logs as a list of lines.
    """
    try:
        # Build docker logs command
        cmd = ["logs", "--tail", str(tail)]
        
        if timestamps:
            cmd.append("--timestamps")
        
        if since:
            cmd.extend(["--since", since])
        
        cmd.append(container_name)
        
        result = run_docker_command(cmd)
        log_lines = result.stdout.split("\n")
        
        return JSONResponse(content={
            "container": container_name,
            "lines": len(log_lines),
            "logs": log_lines
        })
    
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
    Get real-time resource usage statistics for a container using docker stats.
    
    Args:
        container_name: Name or ID of the container
    
    Returns:
        Resource usage statistics (CPU, memory, network, disk I/O).
    """
    try:
        # Check if container is running first
        inspect_result = run_docker_command(["inspect", "-f", "{{.State.Status}}", container_name])
        status = inspect_result.stdout.strip()
        
        if status != "running":
            raise HTTPException(
                status_code=400,
                detail=f"Container '{container_name}' is not running (status: {status})"
            )
        
        # Get stats
        result = run_docker_command([
            "stats", container_name,
            "--no-stream",
            "--format", "{{json .}}"
        ])
        
        if not result.stdout.strip():
            raise HTTPException(
                status_code=500,
                detail="Failed to retrieve container stats"
            )
        
        stats_data = json.loads(result.stdout)
        
        # Parse memory usage
        mem_usage = stats_data.get("MemUsage", "0B / 0B")
        mem_percent = stats_data.get("MemPerc", "0.00%")
        
        # Try to extract memory values
        try:
            mem_parts = mem_usage.split(" / ")
            usage_str = mem_parts[0].strip()
            limit_str = mem_parts[1].strip() if len(mem_parts) > 1 else "0B"
            
            def parse_memory(s):
                """Parse memory string like '123.4MiB' to MB"""
                s = s.strip()
                if 'GiB' in s or 'GB' in s:
                    return float(s.replace('GiB', '').replace('GB', '')) * 1024
                elif 'MiB' in s or 'MB' in s:
                    return float(s.replace('MiB', '').replace('MB', ''))
                elif 'KiB' in s or 'KB' in s:
                    return float(s.replace('KiB', '').replace('KB', '')) / 1024
                else:
                    return float(s.replace('B', '')) / 1024 / 1024
            
            usage_mb = parse_memory(usage_str)
            limit_mb = parse_memory(limit_str)
            percent = float(mem_percent.rstrip('%'))
        except Exception as e:
            logger.warning(f"Failed to parse memory values: {e}")
            usage_mb = limit_mb = percent = 0.0
        
        parsed_stats = {
            "container": container_name,
            "timestamp": datetime.now().isoformat(),
            "memory": {
                "usage_mb": usage_mb,
                "limit_mb": limit_mb,
                "percent": percent
            },
            "cpu": {
                "percent": stats_data.get("CPUPerc", "0.00%"),
                "online_cpus": stats_data.get("CPUs", 0)
            },
            "network": {
                "input": stats_data.get("NetIO", "0B / 0B").split(" / ")[0],
                "output": stats_data.get("NetIO", "0B / 0B").split(" / ")[1] if " / " in stats_data.get("NetIO", "") else "0B"
            },
            "block_io": {
                "read": stats_data.get("BlockIO", "0B / 0B").split(" / ")[0],
                "write": stats_data.get("BlockIO", "0B / 0B").split(" / ")[1] if " / " in stats_data.get("BlockIO", "") else "0B"
            },
            "pids": stats_data.get("PIDs", 0)
        }
        
        return JSONResponse(content=parsed_stats)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting container stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get container stats: {str(e)}"
        )
