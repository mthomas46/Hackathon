"""Pydantic models for configuration management API"""

from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field, field_validator, ConfigDict


class ServiceConfigUpdate(BaseModel):
    """Request model for service configuration updates"""
    environment: Optional[Union[Dict[str, str], List[str]]] = Field(None, description="Environment variables")
    ports: Optional[List[str]] = Field(None, description="Port mappings (e.g., ['8080:3000'])")
    volumes: Optional[List[str]] = Field(None, description="Volume mounts")
    depends_on: Optional[Union[List[str], Dict[str, Any]]] = Field(None, description="Service dependencies")
    restart: Optional[str] = Field(None, description="Restart policy")
    networks: Optional[List[str]] = Field(None, description="Network configurations")
    image: Optional[str] = Field(None, description="Docker image")
    build: Optional[Union[str, Dict[str, Any]]] = Field(None, description="Build configuration")
    restart_after_change: Optional[bool] = Field(True, description="Restart service after changes")

    @field_validator('ports')
    @classmethod
    def validate_ports(cls, v):
        if v is not None:
            for port_spec in v:
                if ':' not in port_spec:
                    raise ValueError(f"Invalid port specification: {port_spec}. Must be in format 'external:internal'")
                try:
                    external, internal = port_spec.split(':', 1)
                    int(external), int(internal)
                except ValueError:
                    raise ValueError(f"Invalid port numbers in: {port_spec}")
        return v

    @field_validator('restart')
    @classmethod
    def validate_restart(cls, v):
        if v is not None:
            valid_policies = ["no", "always", "on-failure", "unless-stopped"]
            if v not in valid_policies:
                raise ValueError(f"Invalid restart policy: {v}. Must be one of {valid_policies}")
        return v

    @field_validator('environment')
    @classmethod
    def validate_environment(cls, v):
        if v is not None:
            if isinstance(v, list):
                for env_item in v:
                    if '=' not in str(env_item):
                        raise ValueError(f"Invalid environment variable format: {env_item}. Must be 'KEY=VALUE'")
            elif isinstance(v, dict):
                # Dict format is valid
                pass
            else:
                raise ValueError("Environment must be a list of 'KEY=VALUE' strings or a dictionary")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "environment": {"DEBUG": "true", "LOG_LEVEL": "INFO"},
                "ports": ["8080:3000", "8443:443"],
                "volumes": ["./data:/app/data", "logs:/app/logs"],
                "restart": "unless-stopped",
                "restart_after_change": True
            }
        }
    )


class BatchConfigUpdate(BaseModel):
    """Request model for batch configuration updates"""
    services: Dict[str, ServiceConfigUpdate] = Field(..., description="Service configurations to update")
    rollback_on_failure: Optional[bool] = Field(False, description="Rollback all changes if any service fails")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "services": {
                    "web-frontend": {
                        "environment": {"NODE_ENV": "production"},
                        "restart": "always"
                    },
                    "api-backend": {
                        "ports": ["3001:3000"],
                        "volumes": ["./config:/app/config"]
                    }
                },
                "rollback_on_failure": True
            }
        }
    )


class ConfigValidationRequest(BaseModel):
    """Request model for configuration validation"""
    services: Dict[str, ServiceConfigUpdate] = Field(..., description="Service configurations to validate")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "services": {
                    "user-store": {
                        "environment": {"DATABASE_URL": "postgresql://..."},
                        "ports": ["5433:5432"]
                    }
                }
            }
        }
    )


class ConfigRollbackRequest(BaseModel):
    """Request model for configuration rollback"""
    original_config: Dict[str, Any] = Field(..., description="Original configuration to restore")
    restart_after_rollback: Optional[bool] = Field(True, description="Restart service after rollback")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "original_config": {
                    "environment": {"DEBUG": "false"},
                    "restart": "unless-stopped"
                },
                "restart_after_rollback": True
            }
        }
    )


class ConfigExportRequest(BaseModel):
    """Request model for configuration export"""
    format: Optional[str] = Field("json", description="Export format: 'json' or 'yaml'")

    @field_validator('format')
    @classmethod
    def validate_format(cls, v):
        if v not in ["json", "yaml"]:
            raise ValueError(f"Invalid format: {v}. Must be 'json' or 'yaml'")
        return v


# Response Models

class ConfigModificationResult(BaseModel):
    """Response model for configuration modification results"""
    success: bool = Field(..., description="Whether the modification was successful")
    service_name: str = Field(..., description="Name of the service modified")
    changes_applied: List[str] = Field(..., description="List of configuration keys that were changed")
    original_config: Optional[Dict[str, Any]] = Field(None, description="Original configuration before changes")
    persistence_result: Optional[Dict[str, Any]] = Field(None, description="File persistence results")
    restart_result: Optional[Dict[str, Any]] = Field(None, description="Service restart results")
    message: str = Field(..., description="Human-readable result message")


class BatchConfigModificationResult(BaseModel):
    """Response model for batch configuration modification results"""
    total_services: int = Field(..., description="Total number of services in the batch")
    successful_modifications: int = Field(..., description="Number of successful modifications")
    failed_modifications: int = Field(..., description="Number of failed modifications")
    results: Dict[str, Any] = Field(..., description="Detailed results for each service")


class ConfigValidationResult(BaseModel):
    """Response model for configuration validation results"""
    overall_valid: bool = Field(..., description="Whether all configurations are valid")
    services_validated: int = Field(..., description="Number of services validated")
    services_valid: int = Field(..., description="Number of valid services")
    services_invalid: int = Field(..., description="Number of invalid services")
    service_results: Dict[str, Dict[str, Any]] = Field(..., description="Detailed results for each service")


class ServiceConfigInfo(BaseModel):
    """Response model for service configuration information"""
    service_name: str = Field(..., description="Name of the service")
    config_hash: str = Field(..., description="Hash of the configuration for change detection")
    config_data: Dict[str, Any] = Field(..., description="Configuration data")
    timestamp: str = Field(..., description="Timestamp of the configuration")
    source: str = Field(..., description="Source of the configuration")


class CurrentConfigResponse(BaseModel):
    """Response model for current service configuration"""
    current_config: Dict[str, Any] = Field(..., description="Current configuration from docker-compose.yml")


class ConfigExportResponse(BaseModel):
    """Response model for configuration export"""
    service_name: str = Field(..., description="Name of the service")
    format: str = Field(..., description="Export format")
    content: str = Field(..., description="Exported configuration content")


class BulkConfigExportResponse(BaseModel):
    """Response model for bulk configuration export"""
    export_result: Dict[str, Any] = Field(..., description="Export results")


class PortConflictInfo(BaseModel):
    """Response model for port conflict information"""
    port: str = Field(..., description="Conflicting port number")
    services: List[str] = Field(..., description="Services using the conflicting port")
    severity: str = Field(..., description="Severity level: 'low', 'medium', 'high', 'critical'")


class ConfigInconsistencyInfo(BaseModel):
    """Response model for configuration inconsistency information"""
    service_name: str = Field(..., description="Name of the service with inconsistency")
    inconsistency_type: str = Field(..., description="Type of inconsistency")
    description: str = Field(..., description="Description of the issue")
    severity: str = Field(..., description="Severity level")
    suggested_fix: Dict[str, Any] = Field(..., description="Suggested fix for the inconsistency")


class ConfigSyncResult(BaseModel):
    """Response model for configuration synchronization results"""
    total_services: int = Field(..., description="Total number of services")
    successful_syncs: int = Field(..., description="Number of successful synchronizations")
    failed_syncs: int = Field(..., description="Number of failed synchronizations")
    service_results: Dict[str, Dict[str, Any]] = Field(..., description="Results for each service")


class ConfigComparisonResult(BaseModel):
    """Response model for configuration comparison results"""
    status: str = Field(..., description="Comparison status")
    changes_detected: Optional[bool] = Field(None, description="Whether changes were detected")
    change_count: Optional[int] = Field(None, description="Number of changes detected")
    changes: Optional[List[Dict[str, Any]]] = Field(None, description="Detailed change information")
    current_version: Optional[str] = Field(None, description="Current configuration version")
    previous_version: Optional[str] = Field(None, description="Previous configuration version")


class ConfigHistoryResponse(BaseModel):
    """Response model for configuration history"""
    config_history: List[Dict[str, Any]] = Field(..., description="List of historical configurations")


# Error Response Models

class ValidationErrorDetail(BaseModel):
    """Detailed validation error information"""
    field: str = Field(..., description="Field that failed validation")
    message: str = Field(..., description="Error message")
    value: Optional[Any] = Field(None, description="Invalid value that was provided")


class ErrorResponse(BaseModel):
    """Generic error response"""
    error: str = Field(..., description="Error type or code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[List[ValidationErrorDetail]] = Field(None, description="Detailed validation errors")
