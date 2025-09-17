"""DTOs for Service Registry API"""

from pydantic import BaseModel, Field, field_validator
from typing import Dict, Any, Optional, List
from datetime import datetime


class ServiceRegistrationRequest(BaseModel):
    """Request to register a service."""
    service_name: str = Field(..., min_length=1, max_length=255)
    service_url: str = Field(..., min_length=1, max_length=2000)
    capabilities: List[str] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = None

    @field_validator('service_name')
    @classmethod
    def validate_service_name(cls, v):
        if not v.strip():
            raise ValueError('Service name cannot be empty')
        return v.strip()

    @field_validator('capabilities')
    @classmethod
    def validate_capabilities(cls, v):
        if len(v) > 100:
            raise ValueError('Too many capabilities (max 100)')
        return v


class ServiceUnregistrationRequest(BaseModel):
    """Request to unregister a service."""
    service_name: str = Field(..., min_length=1, max_length=255)

    @field_validator('service_name')
    @classmethod
    def validate_service_name(cls, v):
        if not v.strip():
            raise ValueError('Service name cannot be empty')
        return v.strip()


class PollOpenAPIRequest(BaseModel):
    """Request to poll OpenAPI specs from services."""
    service_urls: List[str] = Field(..., min_items=1)
    force_refresh: bool = False

    @field_validator('service_urls')
    @classmethod
    def validate_service_urls(cls, v):
        if len(v) > 50:
            raise ValueError('Too many service URLs (max 50)')
        return v


class ServiceInfoResponse(BaseModel):
    """Response containing service information."""
    name: str
    description: str
    category: str
    capabilities: List[str]
    endpoints: List[str]
    status: str = "unknown"
    version: Optional[str] = None

    class Config:
        from_attributes = True


class RegistryEntryResponse(BaseModel):
    """Response containing service registry entry."""
    service_name: str
    service_url: str
    capabilities: List[str]
    status: str
    last_seen: str
    metadata: Dict[str, Any]

    class Config:
        from_attributes = True


class ServiceListResponse(BaseModel):
    """Response containing list of services."""
    services: List[RegistryEntryResponse]
    total: int

    class Config:
        from_attributes = True
