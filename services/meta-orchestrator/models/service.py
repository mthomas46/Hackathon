"""Service-related models"""

from enum import Enum
from typing import Dict, List, Any, Optional
from pydantic import BaseModel


class ServiceStatus(str, Enum):
    """Service status enumeration"""
    RUNNING = "running"
    STOPPED = "stopped"
    STARTING = "starting"
    STOPPING = "stopping"
    ERROR = "error"
    UNKNOWN = "unknown"


class ServiceInfo(BaseModel):
    """Information about a service"""
    name: str
    status: ServiceStatus
    config: Dict[str, Any]
    container_id: Optional[str] = None
    ports: List[str] = []
    environment: Dict[str, Any] = {}
    depends_on: List[str] = []
    health_check_url: Optional[str] = None
    last_health_check: Optional[float] = None


class ServiceAction(BaseModel):
    """Result of a service action"""
    service_name: str
    action: str  # start, stop, restart, update_config
    success: bool
    message: str
    timestamp: float
