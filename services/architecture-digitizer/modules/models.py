"""Data models for the Architecture Digitizer service."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, field_validator
from services.shared.core.responses.responses import BaseResponse


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


class FileNormalizeRequest(BaseModel):
    """Request model for normalizing uploaded diagram files."""
    system: str  # miro, figjam, lucid, confluence
    file_format: str  # json, pdf, png, jpg, svg, xml, html

    @field_validator('system')
    @classmethod
    def validate_system(cls, v):
        valid_systems = ['miro', 'figjam', 'lucid', 'confluence']
        if v not in valid_systems:
            raise ValueError(f'System must be one of: {", ".join(valid_systems)}')
        return v

    @field_validator('file_format')
    @classmethod
    def validate_file_format(cls, v):
        valid_formats = ['json', 'pdf', 'png', 'jpg', 'jpeg', 'svg', 'xml', 'html']
        if v.lower() not in valid_formats:
            raise ValueError(f'File format must be one of: {", ".join(valid_formats)}')
        return v.lower()


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


class FileNormalizeResponse(BaseResponse):
    """Response model for file-based normalization."""
    system: str
    file_format: str
    filename: str
    data: NormalizedArchitectureData


class SupportedFileFormatsResponse(BaseResponse):
    """Response model for supported file formats by system."""
    system: str
    supported_formats: List[Dict[str, Any]]
    count: int


class SupportedSystemsResponse(BaseResponse):
    """Response model for supported systems list."""
    systems: List[SupportedSystemInfo]
    count: int
