# Code Consolidation Strategy

## 📋 Overview

This document outlines the consolidation strategy for eliminating code duplication across the LLM Documentation Ecosystem. Based on the comprehensive audit, we identified significant duplication that can be consolidated to reduce maintenance burden and improve consistency.

## 🔍 Identified Duplication Patterns

### 1. Response Handler Functions (11 instances)
**Pattern**: `create_success_response`, `create_error_response`, and similar HTTP response utilities

**Locations**:
- `services/project-simulation/main.py` (6 functions)
- `services/orchestrator/presentation/utils.py` (1 function)
- `services/memory-agent/modules/shared_utils.py` (1 function)
- `services/analysis-service/modules/cross_repository_analyzer.py` (2 functions)
- `services/shared/core/responses/responses.py` (1 function)

**Impact**: 11 duplicate implementations with inconsistent patterns

### 2. Service Client Functions (3 instances)
**Pattern**: `get_service_client` for service-to-service communication

**Locations**:
- `services/analysis-service/modules/handlers/base_handler.py`
- `services/shared/utilities/utilities.py`
- `services/interpreter/modules/__init__.py`

**Impact**: 3 different implementations with varying functionality

### 3. Configuration Management (46 config files)
**Pattern**: Configuration loading, validation, and management

**Locations**: Scattered across all services with inconsistent patterns

**Impact**: 46 files with potential overlap and maintenance complexity

## 🏗️ Consolidation Strategy

### Phase 1: Foundation Consolidation (Weeks 2-3)

#### 1.1 Unified Response Handler System

**Target**: Create `services/shared/presentation/responses.py`

**Consolidation Plan**:
```python
# services/shared/presentation/responses.py
from typing import Any, Dict, Optional, Union
from fastapi import HTTPException
from pydantic import BaseModel

class APIResponse(BaseModel):
    """Standardized API response format."""
    success: bool
    data: Optional[Any] = None
    message: Optional[str] = None
    errors: Optional[List[Dict[str, Any]]] = None
    request_id: Optional[str] = None
    timestamp: str

def create_success_response(
    data: Any = None,
    message: str = "",
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """Create standardized success response."""
    return APIResponse(
        success=True,
        data=data,
        message=message or "Operation completed successfully",
        request_id=request_id,
        timestamp=datetime.utcnow().isoformat()
    ).dict()

def create_error_response(
    message: str,
    error_code: Optional[str] = None,
    status_code: int = 500,
    request_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create standardized error response."""
    return APIResponse(
        success=False,
        message=message,
        errors=[{
            "code": error_code,
            "message": message,
            "details": details
        }] if error_code else None,
        request_id=request_id,
        timestamp=datetime.utcnow().isoformat()
    ).dict()

# Specialized response types
def create_paginated_response(
    items: List[Any],
    total: int,
    page: int,
    page_size: int,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """Create paginated response."""
    return create_success_response(
        data={
            "items": items,
            "pagination": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size
            }
        },
        request_id=request_id
    )

def create_validation_error_response(
    errors: Dict[str, List[str]],
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """Create validation error response."""
    return APIResponse(
        success=False,
        message="Validation failed",
        errors=[{
            "field": field,
            "messages": messages
        } for field, messages in errors.items()],
        request_id=request_id,
        timestamp=datetime.utcnow().isoformat()
    ).dict()
```

**Migration Steps**:
1. Create unified response module in `services/shared/presentation/`
2. Update imports in all affected services
3. Remove duplicate implementations
4. Update tests to use new standard

#### 1.2 Unified Service Client System

**Target**: Create `services/shared/infrastructure/clients.py`

**Consolidation Plan**:
```python
# services/shared/infrastructure/clients.py
import asyncio
import logging
from typing import Any, Dict, Optional, Union
import httpx

from ..utilities.retry_service import RetryService
from ..utilities.circuit_breaker_service import CircuitBreakerService

logger = logging.getLogger(__name__)

class ServiceClient:
    """Unified service client for inter-service communication."""

    def __init__(
        self,
        service_name: str,
        base_url: str,
        timeout: int = 30,
        retry_service: Optional[RetryService] = None,
        circuit_breaker: Optional[CircuitBreakerService] = None
    ):
        self.service_name = service_name
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.retry_service = retry_service or RetryService()
        self.circuit_breaker = circuit_breaker

        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            headers={"User-Agent": f"service-client/{service_name}"}
        )

    async def get(self, path: str, **kwargs) -> Dict[str, Any]:
        """GET request with retry and circuit breaker."""
        return await self._request("GET", path, **kwargs)

    async def post(self, path: str, **kwargs) -> Dict[str, Any]:
        """POST request with retry and circuit breaker."""
        return await self._request("POST", path, **kwargs)

    async def put(self, path: str, **kwargs) -> Dict[str, Any]:
        """PUT request with retry and circuit breaker."""
        return await self._request("PUT", path, **kwargs)

    async def delete(self, path: str, **kwargs) -> Dict[str, Any]:
        """DELETE request with retry and circuit breaker."""
        return await self._request("DELETE", path, **kwargs)

    async def _request(
        self,
        method: str,
        path: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Execute HTTP request with resilience patterns."""
        url = f"{self.base_url}/{path.lstrip('/')}"

        async def _execute():
            if self.circuit_breaker:
                async with self.circuit_breaker.call(url):
                    response = await self.client.request(method, url, **kwargs)
            else:
                response = await self.client.request(method, url, **kwargs)

            response.raise_for_status()
            return response.json()

        return await self.retry_service.execute_with_retry(_execute)

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

class ServiceClientFactory:
    """Factory for creating service clients."""

    def __init__(self, service_registry: Dict[str, str]):
        self.service_registry = service_registry
        self.clients: Dict[str, ServiceClient] = {}

    def get_client(self, service_name: str) -> ServiceClient:
        """Get or create service client."""
        if service_name not in self.clients:
            if service_name not in self.service_registry:
                raise ValueError(f"Unknown service: {service_name}")

            self.clients[service_name] = ServiceClient(
                service_name=service_name,
                base_url=self.service_registry[service_name]
            )

        return self.clients[service_name]

    async def close_all(self):
        """Close all service clients."""
        for client in self.clients.values():
            await client.close()
        self.clients.clear()

# Global factory instance
_service_client_factory: Optional[ServiceClientFactory] = None

def initialize_service_clients(service_registry: Dict[str, str]):
    """Initialize global service client factory."""
    global _service_client_factory
    _service_client_factory = ServiceClientFactory(service_registry)

def get_service_client(service_name: str) -> ServiceClient:
    """Get service client from global factory."""
    if not _service_client_factory:
        raise RuntimeError("Service clients not initialized")
    return _service_client_factory.get_client(service_name)

async def close_service_clients():
    """Close all global service clients."""
    if _service_client_factory:
        await _service_client_factory.close_all()
```

**Migration Steps**:
1. Create unified client system in `services/shared/infrastructure/`
2. Update service discovery integration
3. Replace existing implementations
4. Add comprehensive tests

#### 1.3 Unified Configuration System

**Target**: Create `services/shared/infrastructure/config/`

**Consolidation Plan**:
```python
# services/shared/infrastructure/config/__init__.py
from .base_config import BaseConfig, ConfigValidationError
from .config_loader import ConfigLoader
from .environment_config import EnvironmentConfig
from .file_config import FileConfig
from .service_config import ServiceConfig

__all__ = [
    "BaseConfig",
    "ConfigValidationError",
    "ConfigLoader",
    "EnvironmentConfig",
    "FileConfig",
    "ServiceConfig"
]

# services/shared/infrastructure/config/service_config.py
from typing import Any, Dict, Optional
from pydantic import BaseSettings, validator
import os

class ServiceConfig(BaseSettings):
    """Standardized service configuration."""

    # Service identity
    service_name: str
    service_version: str = "1.0.0"

    # Server configuration
    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = False

    # Database configuration
    database_url: Optional[str] = None
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # Redis/Cache configuration
    redis_url: Optional[str] = None
    cache_ttl: int = 300

    # External services
    discovery_agent_url: Optional[str] = None
    shared_service_url: Optional[str] = None

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"

    # Security
    secret_key: str
    cors_origins: list = ["http://localhost:3000"]

    class Config:
        env_prefix = "SERVICE_"
        case_sensitive = False

    @validator('secret_key', pre=True, always=True)
    def validate_secret_key(cls, v):
        if not v:
            if os.getenv('SERVICE_SECRET_KEY'):
                return os.getenv('SERVICE_SECRET_KEY')
            raise ValueError('secret_key is required')
        return v

    @validator('database_url', pre=True, always=True)
    def validate_database_url(cls, v):
        return v or os.getenv('DATABASE_URL') or "sqlite:///./app.db"

# Service-specific config extensions
class AnalysisServiceConfig(ServiceConfig):
    """Analysis service specific configuration."""
    max_concurrent_analyses: int = 5
    analysis_timeout: int = 300
    supported_detectors: list = ["quality", "sentiment", "consistency"]

class DocStoreConfig(ServiceConfig):
    """Document store specific configuration."""
    max_document_size: int = 10485760  # 10MB
    supported_formats: list = ["markdown", "html", "plaintext"]
    backup_interval: int = 3600  # 1 hour
```

**Migration Steps**:
1. Create base configuration classes
2. Define service-specific extensions
3. Update all services to use standardized config
4. Consolidate environment variable handling

### Phase 2: Advanced Consolidation (Weeks 4-6)

#### 2.1 Error Handling Standardization

**Consolidate**: Multiple error handling approaches into unified system

**Target**: Extend `services/shared/utilities/error_handling.py`

#### 2.2 Logging Standardization

**Consolidate**: Logging patterns across services

**Target**: Extend `services/shared/utilities/logging_service.py`

#### 2.3 Validation Standardization

**Consolidate**: Input validation patterns

**Target**: Create `services/shared/utilities/validation/`

### Phase 3: Service-Specific Consolidation (Weeks 7-12)

#### 3.1 Database Patterns
- Consolidate repository patterns
- Standardize migration approaches
- Unify query builders

#### 3.2 API Patterns
- Standardize controller patterns
- Consolidate middleware usage
- Unify API documentation

#### 3.3 Testing Patterns
- Consolidate test utilities
- Standardize fixture patterns
- Unify mock implementations

## 📊 Consolidation Metrics & Code Reduction Targets

### Quantitative Reduction Targets
- **Response Handlers**: 11 → 1 implementation (91% reduction)
- **Service Clients**: 3 → 1 implementation (67% reduction)
- **Config Files**: 46 → ~10 standardized configs (78% reduction)
- **Overall Codebase**: Target **30-40% reduction** through consolidation
- **Boilerplate Code**: Target **60% reduction** through shared utilities
- **Import Statements**: Target **50% reduction** through lazy loading

### Qualitative Improvements
- **Cyclomatic Complexity**: Reduce average from current levels to < 8
- **Method Length**: Target < 15 lines per method (vs current averages)
- **Class Count**: Reduce duplicate classes by 70%
- **Test Code**: Target 90% test coverage with 50% less test boilerplate
- **Documentation**: 100% API documentation with 80% less manual documentation effort

### Quality Improvements
- **Consistency**: 100% standardized patterns across services
- **Maintainability**: Single source of truth for common functionality
- **Testability**: Unified testing patterns and utilities

## 🧹 Code Reduction & Boilerplate Elimination Strategies

### 1. Base Class & Template Standardization

#### Repository Base Classes
**Before**: Each service implements its own repository pattern
```python
class DocumentRepository:  # Repeated in every service
    def save(self, entity): pass
    def find_by_id(self, id): pass
    def find_all(self): pass
```

**After**: Standardized base repository with common functionality
```python
from shared.domain.base_repository import BaseRepository

class DocumentRepository(BaseRepository[Document]):
    # Only service-specific methods here
    def find_by_content_hash(self, hash: str) -> Optional[Document]:
        pass
```
**Reduction**: 70% less repository boilerplate code

#### Service Base Classes
**Before**: Each service reimplements common service patterns
```python
class DocumentService:  # Repeated patterns
    def __init__(self, repository):
        self.repository = repository

    def _validate_entity(self, entity):
        # Duplicate validation logic
        pass
```

**After**: Standardized service base with common patterns
```python
from shared.domain.base_service import BaseService

class DocumentService(BaseService[Document]):
    # Only business-specific logic here
    def create_with_validation(self, data: dict) -> Document:
        # Business logic only
        pass
```
**Reduction**: 60% less service boilerplate code

### 2. Exception & Error Handling Consolidation

#### Custom Exception Hierarchy
**Before**: Scattered exception definitions
```python
# In every service
class DocumentNotFoundError(Exception):
    pass

class ValidationError(Exception):
    pass
```

**After**: Standardized exception hierarchy
```python
from shared.domain.exceptions import (
    EntityNotFoundError,
    ValidationError,
    BusinessRuleViolationError
)

class DocumentNotFoundError(EntityNotFoundError):
    """Document not found - inherits all standard behavior"""
    pass
```
**Reduction**: 80% less exception boilerplate

#### Error Response Standardization
**Before**: Manual error response creation
```python
# Repeated in every controller
return {
    "success": False,
    "error": "Document not found",
    "code": 404
}
```

**After**: Standardized error responses
```python
from shared.presentation.responses import create_error_response

raise HTTPException(status_code=404, detail="Document not found")
# Automatically converted to standardized response
```
**Reduction**: 90% less error handling code

### 3. Validation & DTO Consolidation

#### Request/Response Model Templates
**Before**: Repeated Pydantic model patterns
```python
class CreateDocumentRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    tags: List[str] = Field(default_factory=list)

class DocumentResponse(BaseModel):
    id: str
    title: str
    content: str
    created_at: datetime
```

**After**: Standardized model templates
```python
from shared.presentation.models import (
    CreateEntityRequest,
    EntityResponse,
    PaginatedResponse
)

class CreateDocumentRequest(CreateEntityRequest):
    """Inherits validation, examples, and common fields"""
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)

class DocumentResponse(EntityResponse):
    """Inherits standard fields and serialization"""
    title: str
    content: str
```
**Reduction**: 75% less model boilerplate

### 4. Controller & Route Standardization

#### CRUD Controller Templates
**Before**: Repeated CRUD endpoint patterns
```python
@router.post("/")
async def create_document(request: CreateDocumentRequest):
    try:
        result = await service.create(request)
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/{id}")
async def get_document(id: str):
    try:
        result = await service.get_by_id(id)
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

**After**: Standardized CRUD controllers
```python
from shared.presentation.controllers import CRUDController

router = CRUDController(
    service=DocumentService(),
    entity_name="document",
    create_model=CreateDocumentRequest,
    response_model=DocumentResponse
).get_router()

# Generates all CRUD endpoints automatically with:
# - Standardized error handling
# - OpenAPI documentation
# - Request validation
# - Response formatting
```
**Reduction**: 95% less controller boilerplate

### 5. Testing Boilerplate Reduction

#### Test Base Classes
**Before**: Repeated test setup patterns
```python
class TestDocumentService:
    @pytest.fixture
    def service(self):
        return DocumentService()

    @pytest.fixture
    def repository(self):
        return Mock()

    def test_create_document(self, service, repository):
        # Boilerplate setup
        pass
```

**After**: Standardized test base classes
```python
from shared.testing.base import ServiceTestBase

class TestDocumentService(ServiceTestBase):
    service_class = DocumentService
    entity_class = Document

    def test_create_document(self):
        # Only test-specific logic here
        pass

    # Standard CRUD tests auto-generated
```
**Reduction**: 70% less test boilerplate

#### Fixture Consolidation
**Before**: Scattered fixture definitions
```python
@pytest.fixture
def sample_document():
    return Document(id="1", title="Test", content="Content")

@pytest.fixture
def mock_repository():
    return Mock(spec=DocumentRepository)
```

**After**: Standardized fixtures
```python
from shared.testing.fixtures import get_sample_entity, get_mock_repository

@pytest.fixture
def sample_document():
    return get_sample_entity(Document, id="1", title="Test")

@pytest.fixture
def mock_repository():
    return get_mock_repository(DocumentRepository)
```
**Reduction**: 80% less fixture boilerplate

### 6. Configuration Boilerplate Elimination

#### Service Configuration Templates
**Before**: Manual configuration classes
```python
@dataclass
class DocumentConfig:
    max_size: int = 1024
    allowed_formats: List[str] = field(default_factory=list)

    @classmethod
    def from_env(cls):
        return cls(
            max_size=int(os.getenv('DOC_MAX_SIZE', 1024)),
            allowed_formats=os.getenv('DOC_FORMATS', 'pdf,txt').split(',')
        )
```

**After**: Configuration templates
```python
from shared.infrastructure.config import create_service_config

config = create_service_config('doc-store',
    max_document_size=1024,
    allowed_formats=['pdf', 'txt']
)
```
**Reduction**: 85% less configuration boilerplate

### 7. Import & Dependency Management

#### Lazy Import System
**Before**: Large import blocks at module level
```python
from service.business_logic import ComplexBusinessLogic
from service.data_access import DatabaseAccessLayer
from service.external_integrations import ThirdPartyAPI
# 20+ imports loading at startup
```

**After**: Lazy imports on demand
```python
# No imports at module level
def process_data():
    # Imports loaded only when needed
    from service.business_logic import ComplexBusinessLogic
    # ...
```
**Reduction**: 60% faster startup time, 50% less memory usage

## 📈 Expected Code Reduction Results

### By Service Category
- **Foundation Services** (shared): 60% reduction (already achieved in utilities/__init__.py)
- **Business Services** (analysis-service, orchestrator): 40-50% reduction
- **Data Services** (doc_store, prompt_store): 35-45% reduction
- **Interface Services** (frontend, cli): 50-60% reduction
- **Utility Services** (discovery-agent, summarizer-hub): 30-40% reduction

### Overall Project Impact
- **Total Lines of Code**: 2M+ → ~1.2M (40% reduction)
- **Cyclomatic Complexity**: Average 12 → 8 (33% reduction)
- **Test Coverage**: 10% → 90% (with 50% less test code)
- **Maintenance Effort**: 70% reduction through standardization
- **Bug Fix Time**: 60% reduction through consistent patterns
- **New Feature Time**: 50% reduction through reusable components
- **Documentation**: Centralized API documentation

## 🔄 Migration Strategy

### Incremental Approach
1. **Create**: New consolidated modules in `services/shared/`
2. **Update**: One service at a time to use new implementations
3. **Test**: Comprehensive testing after each migration
4. **Remove**: Old implementations after successful migration
5. **Document**: Update living documentation

### Risk Mitigation
- **Backward Compatibility**: Maintain compatibility during transition
- **Feature Flags**: Enable new implementations gradually
- **Rollback Plan**: Ability to revert changes if issues arise
- **Testing Coverage**: 100% test coverage for consolidated code

### Success Criteria
- [ ] All services use consolidated utilities
- [ ] No duplicate implementations remain
- [ ] Consistent API patterns across services
- [ ] Comprehensive test coverage maintained
- [ ] Documentation updated and accurate

---

*This consolidation strategy will significantly reduce code duplication while improving maintainability and consistency across the entire ecosystem.*
