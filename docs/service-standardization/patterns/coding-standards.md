---
llm_metadata:
  document_type: guide
  content_focus: technical
  platform:
    primary: shared
    secondary: []
  status: active
  created_date: '2023-09-24'
  last_modified: '2025-10-07'
  topics:
  - domain_driven_design
  - fastapi
  - python
  - rag
  - testing
  - deployment
  - security
  - monitoring
  - documentation
  concepts: []
  technologies: []
  services_mentioned: []
  semantic_summary: Guide document about technical aspects of the shared platform
  archive_reason: n/a
  historical_value: current
  reference_value: high
semantic_embedding:
  model: text-embedding-ada-002
  embedding_date: '2025-10-07'
  embedding_checksum: pending
rag_metadata:
  chunk_strategy: semantic
  optimal_chunk_size: 512
  retrieval_priority: high
---

# 🏗️ Coding Standards & Architectural Patterns

## 📋 Overview

This document establishes comprehensive coding standards for the LLM Documentation Ecosystem, following Domain-Driven Design (DDD) principles, REST architectural patterns, and KISS (Keep It Simple Stupid) / DRY (Don't Repeat Yourself) principles. All services must adhere to these standards for consistency, maintainability, and scalability.

## 🏛️ Architecture Principles

### Domain-Driven Design (DDD) Standards

#### 1. Layered Architecture
```
Presentation Layer (API/Controllers)
├── Application Layer (Use Cases/Services)
├── Domain Layer (Entities/Value Objects/Domain Services)
└── Infrastructure Layer (Repositories/External Services)
```

**Requirements:**
- **Strict separation** of concerns between layers
- **Dependency inversion** - inner layers don't depend on outer layers
- **Domain layer independence** - business logic free from infrastructure concerns

#### 2. Domain Modeling Standards

**Entities:**
- Must have unique identity (`id` field)
- Contain business logic methods
- Use dataclasses with proper validation
- Implement `from_dict()` and `to_dict()` for serialization

```python
@dataclass
class Document(BaseEntity):
    """Document entity following DDD standards."""
    id: str
    content: str
    content_hash: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    correlation_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def validate_content(self) -> None:
        """Business rule validation."""
        if not self.content or len(self.content.strip()) == 0:
            raise ValueError("Document content cannot be empty")

    def calculate_hash(self) -> str:
        """Domain logic for content hashing."""
        return hashlib.sha256(self.content.encode()).hexdigest()
```

**Value Objects:**
- Immutable objects representing concepts
- No identity, equality based on values
- Used for validation and business rules

```python
@dataclass(frozen=True)
class EmailAddress:
    """Value object for email validation."""
    value: str

    def __post_init__(self):
        if not self._is_valid_email(self.value):
            raise ValueError(f"Invalid email address: {self.value}")

    @staticmethod
    def _is_valid_email(email: str) -> bool:
        # Email validation logic
        pass
```

**Domain Services:**
- Stateless services containing business logic
- Don't belong to any single entity
- Named with business meaning (not technical)

#### 3. Repository Pattern Standards

**Base Repository Interface:**
```python
class BaseRepository(ABC, Generic[T]):
    """Standardized repository interface."""

    @abstractmethod
    async def save(self, entity: T) -> None:
        pass

    @abstractmethod
    async def find_by_id(self, entity_id: str) -> Optional[T]:
        pass

    @abstractmethod
    async def find_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        pass

    @abstractmethod
    async def update(self, entity_id: str, data: Dict[str, Any]) -> bool:
        pass

    @abstractmethod
    async def delete(self, entity_id: str) -> bool:
        pass
```

**SQL Repository Implementation:**
- Use `aiosqlite` for async database operations
- Implement proper connection management
- Include SQL injection prevention
- Use parameterized queries

```python
class SqlRepository(BaseRepository[T]):
    """SQL-based repository with standardized patterns."""

    def __init__(self, entity_class: type, connection_string: str):
        self.entity_class = entity_class
        self.connection_string = connection_string
        self._validate_table_name()

    def _validate_table_name(self) -> None:
        """Prevent SQL injection in table names."""
        if not validate_sql_identifier(self.table_name):
            raise ValueError(f"Invalid table name: {self.table_name}")

    async def _execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Standardized query execution."""
        async with aiosqlite.connect(self.connection_string) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(query, params)
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
```

### REST API Design Standards

#### 1. Resource Naming
- Use nouns, not verbs: `/documents`, `/users`, `/analyses`
- Use plural forms: `/documents/123`, not `/document/123`
- Hierarchical relationships: `/documents/123/versions`

#### 2. HTTP Methods
```
GET    /documents      # List documents
GET    /documents/123  # Get specific document
POST   /documents      # Create new document
PUT    /documents/123  # Update document (full)
PATCH  /documents/123  # Update document (partial)
DELETE /documents/123  # Delete document
```

#### 3. HTTP Status Codes
- **200 OK**: Successful GET/PUT/PATCH
- **201 Created**: Successful POST
- **204 No Content**: Successful DELETE
- **400 Bad Request**: Invalid request data
- **401 Unauthorized**: Authentication required
- **403 Forbidden**: Authorization failed
- **404 Not Found**: Resource doesn't exist
- **409 Conflict**: Resource state conflict
- **422 Unprocessable Entity**: Validation errors
- **500 Internal Server Error**: Server errors

#### 4. Response Format Standards
```python
# Standardized response structure
{
    "success": bool,
    "data": Any,  # Response payload
    "message": str,  # Human-readable message
    "errors": Optional[List[Dict]],  # Error details
    "request_id": Optional[str],  # Correlation ID
    "timestamp": str  # ISO format timestamp
}
```

### KISS & DRY Principles

#### 1. Keep It Simple Stupid (KISS)
- **Simple solutions** over complex ones
- **Clear, readable code** over clever optimizations
- **One responsibility** per function/class
- **Avoid over-engineering**

#### 2. Don't Repeat Yourself (DRY)
- **Extract common logic** into shared utilities
- **Use base classes** for common patterns
- **Configuration over code** for variability
- **Templates and generators** for repetitive structures

## 📚 OpenAPI/Swagger Documentation Standards

### Controller Documentation Requirements

#### 1. Endpoint Documentation
```python
@router.post(
    "/documents",
    summary="Create a new document",
    description="""
    Create a new document in the system with content validation and metadata.

    **Business Rules:**
    - Content cannot be empty
    - Maximum size: 10MB
    - Content hash is automatically calculated
    """,
    response_model=DocumentResponse,
    responses={
        201: {"description": "Document created successfully"},
        400: {"description": "Invalid request data"},
        422: {"description": "Validation error"}
    },
    tags=["Documents"]
)
async def create_document(request: DocumentRequest) -> DocumentResponse:
    pass
```

#### 2. Parameter Documentation
```python
@router.get(
    "/documents",
    summary="List documents with pagination",
    parameters=[
        {
            "name": "limit",
            "in": "query",
            "schema": {"type": "integer", "minimum": 1, "maximum": 1000, "default": 50},
            "description": "Maximum number of documents to return"
        },
        {
            "name": "offset",
            "in": "query",
            "schema": {"type": "integer", "minimum": 0, "default": 0},
            "description": "Number of documents to skip"
        }
    ]
)
async def list_documents(limit: int = Query(50, ge=1, le=1000), offset: int = Query(0, ge=0)):
    pass
```

#### 3. Pydantic Model Documentation
```python
class DocumentRequest(BaseModel):
    """Request model for document creation."""

    content: str = Field(
        ...,
        min_length=1,
        max_length=10485760,  # 10MB
        description="The document content text",
        example="This is the content of my document..."
    )

    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Document title",
        example="My Important Document"
    )

    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional metadata for the document",
        example={"author": "John Doe", "tags": ["important", "draft"]}
    )

    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "content": "This is a sample document content...",
                "title": "Sample Document",
                "metadata": {"author": "Jane Smith", "priority": "high"}
            }
        }
```

#### 4. Response Model Documentation
```python
class DocumentResponse(BaseModel):
    """Response model for document operations."""

    id: str = Field(..., description="Unique document identifier")
    content: str = Field(..., description="Document content")
    title: str = Field(..., description="Document title")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    class Config:
        """Pydantic configuration."""
        json_encoders = {datetime: lambda v: v.isoformat()}
        schema_extra = {
            "example": {
                "id": "doc_12345",
                "content": "Document content here...",
                "title": "My Document",
                "metadata": {"author": "John Doe"},
                "created_at": "2023-09-24T10:30:00Z"
            }
        }
```

#### 5. Error Response Documentation
```python
class ErrorResponse(BaseModel):
    """Standardized error response."""

    success: bool = Field(default=False, description="Always false for errors")
    message: str = Field(..., description="Human-readable error message")
    errors: List[Dict[str, Any]] = Field(..., description="Detailed error information")
    request_id: Optional[str] = Field(None, description="Request correlation ID")
    timestamp: str = Field(..., description="Error timestamp")

    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "success": False,
                "message": "Validation failed",
                "errors": [
                    {"field": "content", "message": "Content cannot be empty"},
                    {"field": "title", "message": "Title is required"}
                ],
                "request_id": "req_abc123",
                "timestamp": "2023-09-24T10:30:00Z"
            }
        }
```

### API Documentation Standards

#### 1. Service-Level Documentation
```python
app = FastAPI(
    title="Document Store Service",
    description="""
    Advanced document storage and analysis service with comprehensive features.

    ## Features
    - Document storage with versioning
    - Content analysis and tagging
    - Full-text search capabilities
    - Metadata management
    - Audit trail and lifecycle management

    ## API Version
    This is version 1.0.0 of the Document Store API.
    """,
    version="1.0.0",
    contact={
        "name": "Document Store Team",
        "email": "docs@company.com",
        "url": "https://docs.company.com"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    }
)
```

#### 2. Tag Organization
```python
tags_metadata = [
    {
        "name": "Documents",
        "description": "Document management operations",
        "externalDocs": {
            "description": "Find out more",
            "url": "https://docs.company.com/documents"
        }
    },
    {
        "name": "Search",
        "description": "Search and filtering operations"
    },
    {
        "name": "Analytics",
        "description": "Document analytics and reporting"
    }
]

app = FastAPI(..., openapi_tags=tags_metadata)
```

#### 3. Security Documentation
```python
security_schemes = {
    "BearerAuth": {
        "type": "http",
        "scheme": "bearer",
        "description": "JWT token authentication"
    },
    "ApiKeyAuth": {
        "type": "apiKey",
        "in": "header",
        "name": "X-API-Key",
        "description": "API key authentication"
    }
}

app = FastAPI(..., openapi_components={"securitySchemes": security_schemes})
```

## 🧪 Testing Standards

### Unit Testing Requirements
- **Test coverage**: >90% for all services
- **Test naming**: `test_[function_name]_[scenario]`
- **Arrange-Act-Assert** pattern
- **Mock external dependencies**
- **Test edge cases and error conditions**

```python
class TestDocumentService:
    """Unit tests for DocumentService."""

    def test_create_document_success(self):
        """Test successful document creation."""
        # Arrange
        service = DocumentService()
        request = DocumentRequest(
            title="Test Document",
            content="Test content",
            metadata={"author": "Test User"}
        )

        # Act
        result = service.create_document(request)

        # Assert
        assert result.title == "Test Document"
        assert result.content.text == "Test content"
        assert result.metadata["author"] == "Test User"

    def test_create_document_validation_error(self):
        """Test document creation with validation error."""
        # Arrange
        service = DocumentService()
        request = DocumentRequest(
            title="",  # Invalid: empty title
            content="Test content"
        )

        # Act & Assert
        with pytest.raises(ValueError, match="Title cannot be empty"):
            service.create_document(request)
```

### Integration Testing Standards
- **Test real dependencies** where safe
- **Use test databases** for data persistence
- **Test complete workflows**
- **Verify side effects**

### Test Organization
```
tests/
├── unit/
│   ├── domain/
│   ├── infrastructure/
│   └── application/
├── integration/
│   ├── api/
│   └── services/
└── e2e/
    └── workflows/
```

## 🛠️ Code Quality Standards

### Naming Conventions
- **Classes**: `PascalCase` (e.g., `DocumentService`, `UserRepository`)
- **Functions/Methods**: `snake_case` (e.g., `create_document`, `validate_user`)
- **Variables**: `snake_case` (e.g., `user_id`, `document_list`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_FILE_SIZE`, `DEFAULT_TIMEOUT`)

### Code Structure Standards
- **Maximum line length**: 88 characters (Black formatter default)
- **Maximum function length**: 50 lines
- **Maximum class length**: 300 lines
- **One class per file** (except simple related classes)
- **Import organization**: Standard library, third-party, local imports

### Error Handling Standards
```python
# Use specific exceptions
class DocumentNotFoundError(ValueError):
    """Raised when a document cannot be found."""
    pass

class DocumentValidationError(ValueError):
    """Raised when document validation fails."""
    pass

# Consistent error handling pattern
try:
    document = await document_service.get_by_id(document_id)
    if not document:
        raise DocumentNotFoundError(f"Document {document_id} not found")
except DocumentNotFoundError:
    raise HTTPException(status_code=404, detail="Document not found")
except DocumentValidationError as e:
    raise HTTPException(status_code=422, detail=str(e))
```

## 🔧 Configuration Standards

### Environment-Based Configuration
```python
# Use pydantic-settings for configuration
from pydantic_settings import BaseSettings

class ServiceConfig(BaseSettings):
    """Service configuration with validation."""

    # Service identity
    service_name: str = Field(default="unknown-service")
    service_version: str = Field(default="1.0.0")

    # Database configuration
    database_url: str = Field(...)
    database_pool_size: int = Field(default=10, ge=1, le=100)

    # External service URLs
    discovery_agent_url: str = Field(...)
    orchestrator_url: str = Field(...)

    # Security settings
    secret_key: str = Field(default_factory=lambda: secrets.token_hex(32))
    jwt_expiration_hours: int = Field(default=24, ge=1, le=168)

    class Config:
        """Pydantic configuration."""
        env_prefix = "SERVICE_"
        case_sensitive = False
```

### Configuration Loading Pattern
```python
def load_service_config(service_type: str) -> ServiceConfig:
    """Load service configuration from multiple sources."""
    loader = ConfigLoader()
    loader.add_environment_source("SERVICE_")
    loader.add_file_source("./config.yaml")

    return loader.load(ServiceConfig)
```

## 📊 Performance Standards

### Response Time Targets
- **API endpoints**: <200ms 95th percentile
- **Database queries**: <50ms average
- **External API calls**: <500ms timeout
- **Service startup**: <30 seconds

### Resource Usage Limits
- **Memory per service**: <512MB
- **CPU usage**: <80% sustained
- **Database connections**: <20 per service
- **Concurrent requests**: Based on load testing

### Caching Standards
- **Cache frequently accessed data**
- **Use TTL (Time To Live) appropriately**
- **Implement cache invalidation strategies**
- **Monitor cache hit rates**

## 🔒 Security Standards

### Input Validation
- **Validate all inputs** at API boundaries
- **Use parameterized queries** for database operations
- **Sanitize user inputs** to prevent injection attacks
- **Implement rate limiting** on public endpoints

### Authentication & Authorization
- **JWT tokens** for API authentication
- **Role-based access control** (RBAC)
- **API key authentication** for service-to-service calls
- **Secure password hashing** (bcrypt/Argon2)

### Data Protection
- **Encrypt sensitive data** at rest and in transit
- **Implement audit logging** for sensitive operations
- **Use HTTPS** for all external communications
- **Regular security updates** of dependencies

## 📝 Documentation Standards

### Code Documentation
```python
def create_document(
    self,
    title: str,
    content: str,
    metadata: Optional[Dict[str, Any]] = None
) -> Document:
    """
    Create a new document with validation.

    Args:
        title: Document title (required, 1-200 characters)
        content: Document content (required, max 10MB)
        metadata: Optional metadata dictionary

    Returns:
        Created Document entity

    Raises:
        ValueError: If validation fails
        DocumentExistsError: If document with same content exists

    Example:
        >>> service = DocumentService()
        >>> doc = service.create_document(
        ...     title="My Document",
        ...     content="Document content...",
        ...     metadata={"author": "John Doe"}
        ... )
        >>> doc.title
        'My Document'
    """
```

### README Standards
Each service must have a comprehensive README with:
- Service overview and purpose
- Architecture diagram
- API documentation links
- Setup and deployment instructions
- Configuration options
- Testing instructions

## 🎯 Compliance Checklist

### Pre-Commit Checks
- [ ] All flake8 linting passes
- [ ] Black formatting applied
- [ ] isort import sorting correct
- [ ] Type hints present (mypy compatible)
- [ ] Test coverage >90%
- [ ] OpenAPI documentation complete
- [ ] Security scan passes

### Code Review Standards
- [ ] DDD principles followed
- [ ] REST conventions adhered to
- [ ] KISS/DRY principles applied
- [ ] Error handling comprehensive
- [ ] Logging appropriate
- [ ] Documentation complete
- [ ] Tests included and passing

### Deployment Readiness
- [ ] Configuration documented
- [ ] Environment variables specified
- [ ] Health checks implemented
- [ ] Monitoring configured
- [ ] Rollback plan documented

---

*These standards ensure consistency, maintainability, and scalability across all services in the LLM Documentation Ecosystem. All new code must comply with these standards, and existing code should be gradually migrated to meet these requirements.*