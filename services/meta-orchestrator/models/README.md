# Meta-Orchestrator Data Models

Pydantic models and data structures for the Meta-Orchestration Service, providing type-safe data validation and serialization.

## 📋 Overview

The models package defines all the data structures used throughout the Meta-Orchestrator service, ensuring type safety, validation, and consistent data handling.

## 📁 Structure

```
models/
├── __init__.py          # Models package initialization
├── service.py           # Service-related data models
├── container.py         # Docker container models
├── result.py            # Operation result models
└── config_api.py        # Configuration API models
```

## 🔧 Core Data Models

### Service Models (`service.py`)

Models representing services in the ecosystem:

```python
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Any
from enum import Enum

class ServiceStatus(str, Enum):
    """Service status enumeration"""
    RUNNING = "running"
    STOPPED = "stopped"
    STARTING = "starting"
    STOPPING = "stopping"
    RESTARTING = "restarting"
    NOT_DEPLOYED = "not_deployed"
    UNHEALTHY = "unhealthy"
    CRASHED = "crashed"

class ServiceInfo(BaseModel):
    """Complete service information"""
    name: str = Field(..., description="Service name")
    image: str = Field(..., description="Docker image")
    status: ServiceStatus = Field(default=ServiceStatus.NOT_DEPLOYED,
                                  description="Current service status")
    ports: List[str] = Field(default_factory=list,
                            description="Port mappings (host:container)")
    environment: Dict[str, str] = Field(default_factory=dict,
                                       description="Environment variables")
    volumes: List[str] = Field(default_factory=list,
                              description="Volume mounts")
    depends_on: List[str] = Field(default_factory=list,
                                 description="Service dependencies")
    restart_policy: str = Field(default="no",
                               description="Restart policy")
    networks: List[str] = Field(default_factory=list,
                               description="Docker networks")
    labels: Dict[str, str] = Field(default_factory=dict,
                                  description="Docker labels")
    health_endpoint: Optional[str] = Field(default=None,
                                          description="Health check endpoint")
    config_endpoint: Optional[str] = Field(default=None,
                                          description="Configuration endpoint")

    @validator('name')
    def validate_service_name(cls, v):
        """Validate service name format"""
        if not v or not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('Service name must be alphanumeric with dashes/underscores')
        return v

    @validator('ports')
    def validate_ports(cls, v):
        """Validate port mapping format"""
        import re
        for port in v:
            if not re.match(r'^\d+(:\d+)?$', port):
                raise ValueError(f'Invalid port format: {port}')
        return v

    class Config:
        """Pydantic configuration"""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ServiceSummary(BaseModel):
    """Condensed service information for listings"""
    name: str
    status: ServiceStatus
    image: str
    ports: List[str]
    uptime: Optional[str] = None
    cpu_usage: Optional[str] = None
    memory_usage: Optional[str] = None

class ServiceConfig(BaseModel):
    """Service configuration structure"""
    environment: Dict[str, str] = Field(default_factory=dict)
    ports: List[str] = Field(default_factory=list)
    volumes: List[str] = Field(default_factory=list)
    restart_policy: str = Field(default="no")
    network_mode: Optional[str] = None
    networks: List[str] = Field(default_factory=list)
    labels: Dict[str, str] = Field(default_factory=dict)
    command: Optional[str] = None
    entrypoint: Optional[str] = None
    working_dir: Optional[str] = None
    user: Optional[str] = None
    privileged: bool = Field(default=False)
    cap_add: List[str] = Field(default_factory=list)
    cap_drop: List[str] = Field(default_factory=list)
```

### Container Models (`container.py`)

Models for Docker container operations:

```python
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime

class ContainerInfo(BaseModel):
    """Docker container information"""
    id: str = Field(..., description="Container ID")
    name: str = Field(..., description="Container name")
    image: str = Field(..., description="Docker image")
    status: str = Field(..., description="Container status")
    ports: Dict[str, List[Dict[str, str]]] = Field(default_factory=dict,
                                                  description="Port mappings")
    created: datetime = Field(..., description="Creation timestamp")
    started_at: Optional[datetime] = Field(default=None,
                                          description="Start timestamp")
    finished_at: Optional[datetime] = Field(default=None,
                                           description="Finish timestamp")
    exit_code: Optional[int] = Field(default=None,
                                    description="Exit code")
    labels: Dict[str, str] = Field(default_factory=dict,
                                  description="Container labels")
    env: List[str] = Field(default_factory=list,
                          description="Environment variables")
    mounts: List[Dict[str, Any]] = Field(default_factory=list,
                                        description="Volume mounts")
    networks: Dict[str, Any] = Field(default_factory=dict,
                                    description="Network settings")

class ContainerStats(BaseModel):
    """Container resource statistics"""
    cpu_usage: float = Field(..., description="CPU usage percentage")
    memory_usage: int = Field(..., description="Memory usage in bytes")
    memory_limit: int = Field(..., description="Memory limit in bytes")
    memory_percentage: float = Field(..., description="Memory usage percentage")
    network_rx: int = Field(..., description="Network received bytes")
    network_tx: int = Field(..., description="Network transmitted bytes")
    block_read: int = Field(..., description="Block device read bytes")
    block_write: int = Field(..., description="Block device write bytes")
    pids: int = Field(..., description="Number of processes")

class ContainerLog(BaseModel):
    """Container log entry"""
    timestamp: datetime
    stream: str  # 'stdout' or 'stderr'
    content: str
    container_id: str
    container_name: str

class ContainerOperation(BaseModel):
    """Container operation request/result"""
    container_name: str
    operation: str  # 'start', 'stop', 'restart', 'remove'
    success: bool
    message: str
    timestamp: datetime
    duration: Optional[float] = None
    error_details: Optional[str] = None
```

### Result Models (`result.py`)

Models for operation results and responses:

```python
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any, Union
from enum import Enum

class OperationStatus(str, Enum):
    """Operation status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"

class OperationResult(BaseModel):
    """Generic operation result"""
    operation_id: str = Field(..., description="Unique operation identifier")
    status: OperationStatus = Field(..., description="Operation status")
    success: bool = Field(..., description="Whether operation succeeded")
    message: str = Field(..., description="Human-readable message")
    timestamp: datetime = Field(default_factory=datetime.utcnow,
                               description="Operation timestamp")
    duration: Optional[float] = Field(default=None,
                                     description="Operation duration in seconds")
    details: Dict[str, Any] = Field(default_factory=dict,
                                   description="Additional operation details")
    error_code: Optional[str] = Field(default=None,
                                     description="Error code if failed")
    error_details: Optional[str] = Field(default=None,
                                        description="Detailed error information")

class BatchOperationResult(BaseModel):
    """Result for batch operations"""
    total_operations: int = Field(..., description="Total number of operations")
    successful_operations: int = Field(..., description="Number of successful operations")
    failed_operations: int = Field(..., description="Number of failed operations")
    results: List[OperationResult] = Field(default_factory=list,
                                          description="Individual operation results")
    summary: Dict[str, Any] = Field(default_factory=dict,
                                   description="Batch operation summary")

class HealthResult(BaseModel):
    """Health check result"""
    service_name: str
    healthy: bool
    response_time: Optional[float] = None
    status_code: Optional[int] = None
    endpoint: Optional[str] = None
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    checks: List[Dict[str, Any]] = Field(default_factory=list,
                                        description="Individual health checks")

class ValidationResult(BaseModel):
    """Configuration validation result"""
    service_name: Optional[str] = None
    success: bool = Field(..., description="Whether validation passed")
    issues: List[Dict[str, Any]] = Field(default_factory=list,
                                        description="Validation issues found")
    warnings: List[str] = Field(default_factory=list,
                               description="Validation warnings")
    errors: List[str] = Field(default_factory=list,
                             description="Validation errors")
    validator_name: str = Field(..., description="Name of the validator")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class DriftIssue(BaseModel):
    """Configuration drift issue"""
    issue_type: str = Field(..., description="Type of drift issue")
    severity: str = Field(..., description="Issue severity: low, medium, high, critical")
    description: str = Field(..., description="Human-readable description")
    field_path: str = Field(..., description="Configuration field path")
    source_a: str = Field(..., description="First configuration source")
    source_b: str = Field(..., description="Second configuration source")
    old_value: Optional[Any] = Field(default=None,
                                    description="Previous value")
    new_value: Optional[Any] = Field(default=None,
                                    description="New value")
    can_auto_fix: bool = Field(default=False,
                              description="Whether issue can be auto-fixed")
    suggested_fix: Optional[str] = Field(default=None,
                                        description="Suggested fix")
```

### Configuration API Models (`config_api.py`)

Models for configuration management API:

```python
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Any
from enum import Enum

class ConfigFormat(str, Enum):
    """Configuration format enumeration"""
    JSON = "json"
    YAML = "yaml"
    ENV = "env"
    DOCKER = "docker"

class ConfigUpdateRequest(BaseModel):
    """Request to update service configuration"""
    service_name: str = Field(..., description="Name of service to update")
    config: Dict[str, Any] = Field(..., description="New configuration values")
    validate_only: bool = Field(default=False,
                               description="Only validate, don't apply")
    backup: bool = Field(default=True,
                        description="Create backup before applying")
    restart_required: Optional[bool] = Field(default=None,
                                            description="Force restart after update")

    @validator('config')
    def validate_config_structure(cls, v):
        """Validate configuration has valid structure"""
        if not isinstance(v, dict):
            raise ValueError('Configuration must be a dictionary')

        # Validate known configuration keys
        valid_keys = {
            'environment', 'ports', 'volumes', 'restart_policy',
            'network_mode', 'networks', 'labels', 'command'
        }

        for key in v.keys():
            if key not in valid_keys:
                raise ValueError(f'Unknown configuration key: {key}')

        return v

class ConfigUpdateResponse(BaseModel):
    """Response from configuration update"""
    service_name: str
    success: bool
    changes_applied: List[str] = Field(default_factory=list)
    backup_created: Optional[str] = None
    validation_errors: List[str] = Field(default_factory=list)
    requires_restart: bool = Field(default=False)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ConfigValidationRequest(BaseModel):
    """Request to validate configuration"""
    service_name: str
    config: Dict[str, Any]
    strict: bool = Field(default=False,
                        description="Strict validation mode")

class ConfigValidationResponse(BaseModel):
    """Response from configuration validation"""
    valid: bool
    issues: List[Dict[str, Any]] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ConfigExportRequest(BaseModel):
    """Request to export configuration"""
    service_name: str
    format: ConfigFormat = Field(default=ConfigFormat.JSON)
    include_metadata: bool = Field(default=True,
                                  description="Include export metadata")

class ConfigExportResponse(BaseModel):
    """Response from configuration export"""
    service_name: str
    format: ConfigFormat
    content: str
    metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ConfigHistoryEntry(BaseModel):
    """Configuration history entry"""
    id: int
    service_name: str
    config_hash: str
    config_data: Dict[str, Any]
    created_at: datetime
    created_by: Optional[str] = None
    change_reason: Optional[str] = None
    backup_path: Optional[str] = None

class ConfigComparisonRequest(BaseModel):
    """Request to compare configurations"""
    service_name: str
    compare_with: str = Field(..., description="'previous', 'current', or timestamp")
    format: ConfigFormat = Field(default=ConfigFormat.JSON)

class ConfigComparisonResponse(BaseModel):
    """Response from configuration comparison"""
    service_name: str
    differences: List[Dict[str, Any]] = Field(default_factory=list)
    added: List[str] = Field(default_factory=list)
    removed: List[str] = Field(default_factory=list)
    modified: List[str] = Field(default_factory=list)
    summary: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
```

## 🔄 Model Relationships

### Service Lifecycle Models

```
ServiceInfo (static config)
    ↓
ContainerInfo (runtime state)
    ↓
ServiceSummary (condensed view)
```

### Configuration Models

```
ConfigUpdateRequest → ConfigValidationRequest → ConfigUpdateResponse
    ↓
ConfigExportRequest → ConfigExportResponse
    ↓
ConfigComparisonRequest → ConfigComparisonResponse
```

### Operation Models

```
OperationResult (base)
    ↓
BatchOperationResult (multiple operations)
    ↓
HealthResult (health checks)
    ↓
ValidationResult (configuration validation)
```

## ✅ Validation & Type Safety

### Built-in Validators

```python
class PortMapping(BaseModel):
    """Port mapping with validation"""
    host_port: int = Field(..., ge=1, le=65535, description="Host port")
    container_port: int = Field(..., ge=1, le=65535, description="Container port")
    protocol: str = Field(default="tcp", regex="^(tcp|udp)$")

    @validator('host_port', 'container_port')
    def validate_port_range(cls, v):
        """Validate port is in valid range"""
        if not (1 <= v <= 65535):
            raise ValueError(f'Port {v} is not in valid range (1-65535)')
        return v

class EnvironmentVariable(BaseModel):
    """Environment variable with validation"""
    name: str = Field(..., regex=r'^[A-Z_][A-Z0-9_]*$',
                     description="Environment variable name")
    value: str = Field(..., description="Environment variable value")

    @validator('name')
    def validate_env_name(cls, v):
        """Validate environment variable name format"""
        import re
        if not re.match(r'^[A-Z_][A-Z0-9_]*$', v):
            raise ValueError(f'Invalid environment variable name: {v}')
        return v
```

### Custom Field Types

```python
from pydantic import BaseModel, Field
from typing import Annotated

# Custom field types for better validation
ServiceName = Annotated[str, Field(min_length=1, max_length=63,
                                  regex=r'^[a-zA-Z0-9][a-zA-Z0-9\-_]*$')]
PortNumber = Annotated[int, Field(ge=1, le=65535)]
MemorySize = Annotated[str, Field(regex=r'^\d+[kmgt]?b?$')]
CpuShares = Annotated[float, Field(ge=0.0, le=1.0)]

class AdvancedServiceConfig(BaseModel):
    """Service configuration with custom field types"""
    name: ServiceName
    ports: List[PortNumber] = Field(default_factory=list)
    memory_limit: Optional[MemorySize] = None
    cpu_limit: Optional[CpuShares] = None
```

## 🔄 Serialization & Deserialization

### JSON Serialization

```python
# Custom JSON encoders for complex types
from pydantic.json import custom_pydantic_encoder

class CustomBaseModel(BaseModel):
    """Base model with custom JSON serialization"""

    class Config:
        """Pydantic configuration"""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Path: lambda v: str(v),
            Enum: lambda v: v.value,
            bytes: lambda v: v.decode('utf-8'),
        }

        # Allow population by field name
        allow_population_by_field_name = True

        # Validate field assignment
        validate_assignment = True

        # Extra fields not allowed
        extra = 'forbid'
```

### YAML Support

```python
import yaml
from pydantic import BaseModel

class YamlSerializable(BaseModel):
    """Model that can be serialized to/from YAML"""

    @classmethod
    def from_yaml(cls, yaml_str: str) -> 'YamlSerializable':
        """Create instance from YAML string"""
        data = yaml.safe_load(yaml_str)
        return cls(**data)

    def to_yaml(self) -> str:
        """Serialize to YAML string"""
        return yaml.dump(
            self.dict(),
            default_flow_style=False,
            sort_keys=False,
            indent=2
        )
```

## 🚨 Error Models

### API Error Models

```python
class APIError(BaseModel):
    """Standard API error response"""
    error_code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(default=None,
                                             description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = Field(default=None,
                                     description="Request correlation ID")

class ValidationErrorDetail(BaseModel):
    """Detailed validation error"""
    field: str = Field(..., description="Field that failed validation")
    value: Any = Field(..., description="Invalid value provided")
    error_type: str = Field(..., description="Type of validation error")
    message: str = Field(..., description="Validation error message")

class ValidationErrorResponse(APIError):
    """Response for validation errors"""
    validation_errors: List[ValidationErrorDetail] = Field(default_factory=list)
```

## 📊 Model Usage Patterns

### Builder Pattern for Complex Models

```python
class ServiceConfigBuilder:
    """Builder pattern for complex service configurations"""

    def __init__(self):
        self.config = ServiceConfig()

    def with_environment(self, **env_vars):
        """Add environment variables"""
        self.config.environment.update(env_vars)
        return self

    def with_ports(self, *ports):
        """Add port mappings"""
        self.config.ports.extend(ports)
        return self

    def with_volumes(self, *volumes):
        """Add volume mounts"""
        self.config.volumes.extend(volumes)
        return self

    def with_restart_policy(self, policy: str):
        """Set restart policy"""
        self.config.restart_policy = policy
        return self

    def build(self) -> ServiceConfig:
        """Build the final configuration"""
        return self.config

# Usage
config = (ServiceConfigBuilder()
         .with_environment(NODE_ENV="production", PORT="8080")
         .with_ports("8080:3000", "8443:443")
         .with_volumes("/data:/app/data")
         .with_restart_policy("unless-stopped")
         .build())
```

### Factory Pattern for Model Creation

```python
class ModelFactory:
    """Factory for creating model instances"""

    @staticmethod
    def create_service_info(name: str, image: str, **kwargs) -> ServiceInfo:
        """Create ServiceInfo with validation"""
        return ServiceInfo(name=name, image=image, **kwargs)

    @staticmethod
    def create_operation_result(operation_id: str, success: bool,
                              message: str, **kwargs) -> OperationResult:
        """Create OperationResult with defaults"""
        return OperationResult(
            operation_id=operation_id,
            success=success,
            message=message,
            **kwargs
        )

    @staticmethod
    def create_health_result(service_name: str, healthy: bool,
                           response_time: float = None) -> HealthResult:
        """Create HealthResult with common defaults"""
        return HealthResult(
            service_name=service_name,
            healthy=healthy,
            response_time=response_time,
            endpoint=f"http://localhost/health"
        )
```

This models package provides a robust, type-safe foundation for all data handling in the Meta-Orchestrator service, ensuring consistency, validation, and maintainability across the entire codebase.
