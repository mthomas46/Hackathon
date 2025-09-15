"""Data models for the Architecture Digitizer service."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, field_validator
from services.shared.models import BaseResponse


class ArchitectureComponent(BaseModel):
    """Represents a component in an architectural diagram."""
    id: str
    type: str  # service, database, queue, ui, gateway, function, storage, other
    name: str
    description: Optional[str] = None

    @field_validator('type')
    @classmethod
    def validate_component_type(cls, v):
        valid_types = ['service', 'database', 'queue', 'ui', 'gateway', 'function', 'storage', 'other']
        if v not in valid_types:
            raise ValueError(f'Component type must be one of: {", ".join(valid_types)}')
        return v


class ArchitectureConnection(BaseModel):
    """Represents a connection between architectural components."""
    from_id: str
    to_id: str
    label: Optional[str] = None


class NormalizedArchitectureData(BaseModel):
    """The normalized architecture data following the standard schema."""
    components: List[ArchitectureComponent]
    connections: List[ArchitectureConnection]
    metadata: Optional[Dict[str, Any]] = None


class NormalizeRequest(BaseModel):
    """Request model for normalizing architectural diagrams."""
    system: str  # miro, figjam, lucid, confluence
    board_id: str
    token: str

    @field_validator('system')
    @classmethod
    def validate_system(cls, v):
        valid_systems = ['miro', 'figjam', 'lucid', 'confluence']
        if v not in valid_systems:
            raise ValueError(f'System must be one of: {", ".join(valid_systems)}')
        return v


class NormalizeResponse(BaseResponse):
    """Response model for normalized architecture data."""
    system: str
    board_id: str
    data: NormalizedArchitectureData


class SupportedSystemInfo(BaseModel):
    """Information about a supported diagram system."""
    name: str
    description: str
    auth_type: str  # Bearer token, API key, etc.
    supported: bool


class SupportedSystemsResponse(BaseResponse):
    """Response model for supported systems list."""
    systems: List[SupportedSystemInfo]
    count: int
