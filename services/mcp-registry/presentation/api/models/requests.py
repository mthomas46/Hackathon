"""Request models for API endpoints."""

from typing import Optional, List

from pydantic import BaseModel, Field


class ExportMCPRequestModel(BaseModel):
    """Request model for exporting an MCP."""
    
    mcp_id: str = Field(..., description="MCP ID to export", min_length=1)
    version: Optional[str] = Field(None, description="Version (null = latest)")
    export_format: str = Field("msgpack", description="Export format")
    storage_backend: str = Field("local_filesystem", description="Storage backend")
    compress: bool = Field(True, description="Enable compression")
    include_dependencies: bool = Field(False, description="Include dependencies")
    exported_by: str = Field("system", description="Exporter ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "mcp_id": "mcp-team-alpha",
                "version": "1.2.3",
                "export_format": "msgpack",
                "compress": True
            }
        }


class ImportMCPRequestModel(BaseModel):
    """Request model for importing an MCP."""
    
    export_format: str = Field(..., description="Export format")
    imported_by: str = Field("system", description="Importer ID")
    verify_integrity: bool = Field(True, description="Verify checksums")
    run_security_scan: bool = Field(True, description="Run security scan")
    auto_register: bool = Field(True, description="Auto-register in registry")
    make_public: bool = Field(False, description="Make publicly accessible")
    override_mcp_id: Optional[str] = Field(None, description="Override MCP ID")
    override_owner_id: Optional[str] = Field(None, description="Override owner")
    
    class Config:
        json_schema_extra = {
            "example": {
                "export_format": "msgpack",
                "verify_integrity": True,
                "auto_register": True,
                "make_public": False
            }
        }


class SearchRequestModel(BaseModel):
    """Request model for searching the registry."""
    
    query: str = Field(..., description="Search query", min_length=1)
    tier: Optional[int] = Field(None, ge=0, le=4, description="Filter by tier")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    limit: Optional[int] = Field(100, ge=1, le=1000, description="Result limit")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "team alpha",
                "tier": 2,
                "limit": 50
            }
        }

