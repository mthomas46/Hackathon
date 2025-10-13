"""
Configuration viewer endpoints.

Provides API for viewing current configuration of services.
"""

import logging
import os
from typing import Dict, Any
from datetime import datetime

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ...config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/config/current",
    summary="Get current configuration",
    description="Get currently loaded configuration for all services"
)
async def get_current_config():
    """
    Get currently loaded configuration.
    
    Returns:
        Current configuration with sensitive values masked.
    """
    # Use the already imported settings
    config = {
        "timestamp": datetime.now().isoformat(),
        "environment": os.getenv("ENVIRONMENT", "unknown"),
        "database": {
            "url": _mask_sensitive(str(settings.database_url)),
            "pool_size": settings.database_pool_size,
            "max_overflow": settings.database_max_overflow,
        },
        "redis": {
            "url": _mask_sensitive(str(settings.redis_url)),
        },
        "chromadb": {
            "path": str(settings.chroma_path),
            "collection_name": settings.chroma_collection_name
        },
        "ollama": {
            "base_url": settings.ollama_base_url,
            "model_small": settings.ollama_model_small,
            "model_medium": settings.ollama_model_medium,
            "embedding_model": settings.ollama_embedding_model,
            "timeout": settings.ollama_timeout,
            "desktop_enabled": settings.ollama_desktop_enabled,
            "desktop_url": settings.ollama_desktop_url if settings.ollama_desktop_enabled else None,
            "desktop_model": settings.ollama_desktop_model if settings.ollama_desktop_enabled else None
        },
        "openai": {
            "api_key_set": bool(settings.openai_api_key),
            "embedding_model": settings.openai_embedding_model
        },
        "anthropic": {
            "api_key_set": bool(settings.anthropic_api_key)
        },
        "cursor": {
            "enabled": settings.cursor_enabled,
            "mcp_url": settings.cursor_mcp_url,
            "model": settings.cursor_model,
            "complexity_threshold": settings.cursor_complexity_threshold,
            "fallback_enabled": settings.cursor_fallback_enabled
        },
        "llm_strategy": {
            "model_strategy": settings.model_strategy
        },
        "ingestion": {
            "max_workers": settings.max_workers,
            "batch_size": settings.batch_size,
            "embedding_batch_size": settings.embedding_batch_size
        },
        "caching": {
            "cache_ttl_seconds": settings.cache_ttl_seconds
        },
        "performance": {
            "search_max_results": settings.search_max_results,
            "search_timeout_seconds": settings.search_timeout_seconds
        },
        "logging": {
            "log_level": settings.log_level
        }
    }
    
    return JSONResponse(content=config)


@router.get(
    "/config/environment",
    summary="Get environment variables",
    description="Get current environment variables (sensitive values masked)"
)
async def get_environment_variables():
    """
    Get current environment variables.
    
    Returns:
        Environment variables with sensitive values masked.
    """
    sensitive_keys = [
        "PASSWORD", "SECRET", "KEY", "TOKEN", "API_KEY",
        "POSTGRES_PASSWORD", "REDIS_PASSWORD", "DATABASE_URL"
    ]
    
    env_vars = {}
    for key, value in os.environ.items():
        # Mask sensitive values
        if any(sensitive in key.upper() for sensitive in sensitive_keys):
            env_vars[key] = _mask_sensitive(value)
        else:
            env_vars[key] = value
    
    return JSONResponse(content={
        "timestamp": datetime.now().isoformat(),
        "total_variables": len(env_vars),
        "variables": env_vars
    })


@router.get(
    "/config/docker",
    summary="Get Docker container info",
    description="Get Docker container configuration and metadata"
)
async def get_docker_config():
    """
    Get Docker container configuration.
    
    Returns:
        Docker container info and configuration.
    """
    config = {
        "timestamp": datetime.now().isoformat(),
        "container": {
            "hostname": os.getenv("HOSTNAME", "unknown"),
            "home": os.getenv("HOME", "unknown"),
            "user": os.getenv("USER", "unknown"),
            "pwd": os.getenv("PWD", "unknown")
        },
        "resources": {},
        "networking": {},
        "volumes": {}
    }
    
    # Try to get resource limits from cgroups
    try:
        # Memory limit
        try:
            with open("/sys/fs/cgroup/memory/memory.limit_in_bytes", "r") as f:
                memory_limit = int(f.read().strip())
                config["resources"]["memory_limit_bytes"] = memory_limit
                config["resources"]["memory_limit_mb"] = memory_limit / 1024 / 1024
        except:
            pass
        
        # CPU limit
        try:
            with open("/sys/fs/cgroup/cpu/cpu.cfs_quota_us", "r") as f:
                cpu_quota = int(f.read().strip())
            with open("/sys/fs/cgroup/cpu/cpu.cfs_period_us", "r") as f:
                cpu_period = int(f.read().strip())
            if cpu_quota > 0:
                config["resources"]["cpu_limit"] = cpu_quota / cpu_period
        except:
            pass
    except Exception as e:
        config["resources"]["error"] = str(e)
    
    # Network info
    try:
        import socket
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        config["networking"] = {
            "hostname": hostname,
            "ip_address": ip_address
        }
    except Exception as e:
        config["networking"]["error"] = str(e)
    
    # Volume mounts
    try:
        from pathlib import Path
        import psutil
        
        mounts = []
        for partition in psutil.disk_partitions():
            mounts.append({
                "device": partition.device,
                "mountpoint": partition.mountpoint,
                "fstype": partition.fstype
            })
        config["volumes"] = {"mounts": mounts}
    except Exception as e:
        config["volumes"]["error"] = str(e)
    
    return JSONResponse(content=config)


@router.get(
    "/config/system",
    summary="Get system information",
    description="Get system resource information"
)
async def get_system_info():
    """
    Get system information.
    
    Returns:
        System resource information (CPU, memory, disk).
    """
    try:
        import psutil
        import platform
        
        # CPU info
        cpu_info = {
            "count": psutil.cpu_count(logical=True),
            "physical_count": psutil.cpu_count(logical=False),
            "percent": psutil.cpu_percent(interval=0.1),
            "per_cpu": psutil.cpu_percent(interval=0.1, percpu=True)
        }
        
        # Memory info
        mem = psutil.virtual_memory()
        memory_info = {
            "total_bytes": mem.total,
            "total_mb": mem.total / 1024 / 1024,
            "total_gb": mem.total / 1024 / 1024 / 1024,
            "available_bytes": mem.available,
            "available_mb": mem.available / 1024 / 1024,
            "used_percent": mem.percent,
            "used_mb": mem.used / 1024 / 1024
        }
        
        # Disk info
        disk = psutil.disk_usage('/')
        disk_info = {
            "total_bytes": disk.total,
            "total_gb": disk.total / 1024 / 1024 / 1024,
            "used_bytes": disk.used,
            "used_gb": disk.used / 1024 / 1024 / 1024,
            "free_gb": disk.free / 1024 / 1024 / 1024,
            "percent": disk.percent
        }
        
        # Platform info
        platform_info = {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version()
        }
        
        return JSONResponse(content={
            "timestamp": datetime.now().isoformat(),
            "cpu": cpu_info,
            "memory": memory_info,
            "disk": disk_info,
            "platform": platform_info
        })
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


def _mask_sensitive(value: str) -> str:
    """Mask sensitive configuration values."""
    if not value or len(value) < 8:
        return "***"
    
    # For URLs, mask password and tokens
    if "://" in value:
        parts = value.split("://")
        if len(parts) == 2:
            protocol = parts[0]
            rest = parts[1]
            
            # Mask password in URL
            if "@" in rest:
                auth_and_host = rest.split("@")
                if len(auth_and_host) == 2:
                    auth = auth_and_host[0]
                    host = auth_and_host[1]
                    
                    if ":" in auth:
                        user, _ = auth.split(":", 1)
                        return f"{protocol}://{user}:***@{host}"
            
            return f"{protocol}://{rest[:10]}***"
    
    # For other values, show first 4 and last 4 characters
    return f"{value[:4]}{'*' * (len(value) - 8)}{value[-4:]}"

