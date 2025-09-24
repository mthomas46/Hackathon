# Coding Standards & Patterns

## 📋 Overview

This document establishes the coding standards and architectural patterns for the LLM Documentation Ecosystem service standardization initiative. These standards are derived from the analysis of well-implemented services (analysis-service, orchestrator, doc_store, prompt_store) that follow Domain-Driven Design (DDD) principles.

## 🏗️ Architectural Patterns

### 1. Domain-Driven Design (DDD) Structure

#### Standard Layer Organization
```
services/{service-name}/
├── domain/                    # Business logic layer
│   ├── entities/             # Domain entities (dataclasses)
│   ├── value_objects/        # Value objects (immutable dataclasses)
│   ├── services/             # Domain services (business logic)
│   ├── events/               # Domain events
│   ├── factories/            # Entity factories
│   ├── repositories/         # Repository interfaces
│   ├── exceptions/           # Domain-specific exceptions
│   └── validation/           # Domain validation rules
├── application/               # Application layer
│   ├── use_cases/           # Use cases (business workflows)
│   ├── commands/            # CQRS commands
│   ├── queries/             # CQRS queries
│   ├── handlers/            # Command/query handlers
│   ├── services/            # Application services
│   ├── events/              # Application events
│   ├── dto/                 # Data transfer objects
│   └── validators/          # Input validation
├── infrastructure/           # Infrastructure layer
│   ├── repositories/        # Repository implementations
│   ├── config/              # Configuration management
│   ├── connections/         # External service connections
│   ├── events/              # Event publishing/infrastructure
│   └── migrations/          # Database migrations
├── presentation/             # Presentation layer
│   ├── controllers/         # HTTP controllers
│   ├── middleware/          # HTTP middleware
│   ├── models/              # API models (Pydantic)
│   └── api/                 # API routes
├── tests/                    # Test layer
│   ├── unit/                # Unit tests
│   ├── integration/         # Integration tests
│   ├── e2e/                 # End-to-end tests
│   └── fixtures/            # Test data
├── config.yaml              # Service configuration
├── main.py                  # Application entry point
├── Dockerfile               # Container definition
└── README.md               # Service documentation
```

#### CQRS Pattern (When Applicable)
For complex services with distinct read/write patterns:
```
application/
├── cqrs/
│   ├── command_bus.py       # Command dispatching
│   ├── query_bus.py         # Query dispatching
│   ├── commands.py          # Command definitions
│   └── queries.py           # Query definitions
└── handlers/
    ├── command_handlers.py  # Command processors
    └── query_handlers.py    # Query processors
```

### 2. Clean Architecture Principles

#### Dependency Rule
- Inner layers (domain) should not depend on outer layers
- Dependencies point inward only
- Use dependency injection for cross-layer communication

#### Layer Responsibilities
- **Domain Layer**: Business rules, entities, pure logic
- **Application Layer**: Use cases, orchestration, coordination
- **Infrastructure Layer**: External concerns (DB, APIs, frameworks)
- **Presentation Layer**: HTTP, UI, external interfaces

## 📝 Coding Standards

### 1. Python Language Standards

#### Imports
```python
# Standard library imports (alphabetical)
import logging
from typing import Any, Dict, List, Optional

# Third-party imports (alphabetical)
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

# Local imports (relative, by layer)
from ..domain.entities import Document
from ..domain.repositories import DocumentRepository
from ..infrastructure.config import DatabaseConfig
```

#### Type Hints
```python
# Always use type hints
from typing import Any, Dict, List, Optional, Union

def process_document(
    document_id: str,
    content: str,
    metadata: Optional[Dict[str, Any]] = None
) -> Document:
    """Process a document with optional metadata."""
    pass

# Use Union for multiple possible types
def validate_input(value: Union[str, int, float]) -> bool:
    pass
```

#### Naming Conventions
```python
# Classes: PascalCase
class DocumentService:
    pass

class DocumentRepository:
    pass

# Functions/Methods: snake_case
def create_document():
    pass

def validate_document():
    pass

# Constants: UPPER_SNAKE_CASE
MAX_DOCUMENT_SIZE = 1048576  # 1MB
DEFAULT_TIMEOUT = 30

# Private members: _leading_underscore
class DocumentService:
    def _validate_internal(self):
        pass
```

### 2. Domain Layer Standards

#### Entities (DataClasses)
```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

@dataclass(frozen=True)  # Immutable by default
class DocumentId:
    """Value object for document identifier."""
    value: str

    def __post_init__(self):
        if not self.value or not isinstance(self.value, str):
            raise ValueError("Document ID must be a non-empty string")

@dataclass(frozen=True)
class Document:
    """Document domain entity."""
    id: DocumentId
    title: str
    content: str
    created_at: datetime
    updated_at: datetime
    tags: List[str] = field(default_factory=list)

    def update_content(self, new_content: str) -> 'Document':
        """Create new version with updated content."""
        return Document(
            id=self.id,
            title=self.title,
            content=new_content,
            created_at=self.created_at,
            updated_at=datetime.utcnow(),
            tags=self.tags
        )
```

#### Value Objects
```python
@dataclass(frozen=True)
class EmailAddress:
    """Email address value object."""
    value: str

    def __post_init__(self):
        # Validation logic here
        if '@' not in self.value:
            raise ValueError("Invalid email address")

    @property
    def domain(self) -> str:
        return self.value.split('@')[1]
```

#### Domain Services
```python
class DocumentAnalysisService:
    """Domain service for document analysis logic."""

    def analyze_document_quality(
        self,
        document: Document,
        criteria: AnalysisCriteria
    ) -> AnalysisResult:
        """Analyze document quality against given criteria."""
        # Pure business logic here
        pass
```

#### Repository Interfaces
```python
from abc import ABC, abstractmethod
from typing import List, Optional

class DocumentRepository(ABC):
    """Repository interface for document persistence."""

    @abstractmethod
    async def save(self, document: Document) -> None:
        """Save a document."""
        pass

    @abstractmethod
    async def find_by_id(self, document_id: DocumentId) -> Optional[Document]:
        """Find document by ID."""
        pass

    @abstractmethod
    async def find_all(self, limit: int = 100) -> List[Document]:
        """Find all documents with limit."""
        pass
```

### 3. Application Layer Standards

#### Use Cases
```python
from ..domain.entities import Document, DocumentId
from ..domain.repositories import DocumentRepository
from ..domain.services import DocumentAnalysisService

class AnalyzeDocumentUseCase:
    """Use case for analyzing a document."""

    def __init__(
        self,
        repository: DocumentRepository,
        analysis_service: DocumentAnalysisService
    ):
        self.repository = repository
        self.analysis_service = analysis_service

    async def execute(self, document_id: str) -> AnalysisResult:
        """Execute the document analysis use case."""
        # Input validation
        doc_id = DocumentId(document_id)

        # Retrieve domain object
        document = await self.repository.find_by_id(doc_id)
        if not document:
            raise DocumentNotFoundError(doc_id)

        # Execute business logic
        return await self.analysis_service.analyze_document_quality(
            document,
            AnalysisCriteria.default()
        )
```

#### CQRS Commands/Queries
```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class CreateDocumentCommand:
    """Command to create a new document."""
    title: str
    content: str
    author_id: Optional[str] = None
    command_id: str = field(default_factory=lambda: str(uuid4()))

@dataclass
class GetDocumentQuery:
    """Query to retrieve a document."""
    document_id: str
    include_metadata: bool = False
```

### 4. Infrastructure Layer Standards

#### Repository Implementations
```python
import aiosqlite
from typing import List, Optional

from ..domain.entities import Document, DocumentId
from ..domain.repositories import DocumentRepository

class SQLiteDocumentRepository(DocumentRepository):
    """SQLite implementation of document repository."""

    def __init__(self, connection_string: str):
        self.connection_string = connection_string

    async def save(self, document: Document) -> None:
        async with aiosqlite.connect(self.connection_string) as conn:
            await conn.execute("""
                INSERT OR REPLACE INTO documents
                (id, title, content, created_at, updated_at, tags)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                document.id.value,
                document.title,
                document.content,
                document.created_at.isoformat(),
                document.updated_at.isoformat(),
                ','.join(document.tags)
            ))
            await conn.commit()

    async def find_by_id(self, document_id: DocumentId) -> Optional[Document]:
        async with aiosqlite.connect(self.connection_string) as conn:
            cursor = await conn.execute("""
                SELECT id, title, content, created_at, updated_at, tags
                FROM documents WHERE id = ?
            """, (document_id.value,))

            row = await cursor.fetchone()
            if row:
                return Document(
                    id=DocumentId(row[0]),
                    title=row[1],
                    content=row[2],
                    created_at=datetime.fromisoformat(row[3]),
                    updated_at=datetime.fromisoformat(row[4]),
                    tags=row[5].split(',') if row[5] else []
                )
        return None
```

### 5. Presentation Layer Standards

#### Controllers with OpenAPI/Swagger Annotations
```python
from fastapi import APIRouter, Depends, HTTPException, Path, Body
from typing import Optional

from ..application.use_cases import AnalyzeDocumentUseCase
from ..presentation.models import AnalyzeDocumentRequest, AnalysisResponse

router = APIRouter(prefix="/documents", tags=["Documents"])

@router.post(
    "/{document_id}/analyze",
    response_model=AnalysisResponse,
    summary="Analyze Document Quality",
    description="""
    Perform comprehensive quality analysis on a document.

    This endpoint analyzes the document for:
    - Content quality and readability
    - Structural issues and formatting problems
    - Consistency with organizational standards
    - Potential improvements and recommendations

    **Required Permissions:** documents:read, analysis:execute

    **Rate Limit:** 10 requests per minute
    """,
    responses={
        200: {
            "description": "Analysis completed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "document_id": "doc-123",
                        "quality_score": 0.85,
                        "issues": ["Minor formatting issue on line 42"],
                        "recommendations": ["Consider adding more descriptive headings"],
                        "analyzed_at": "2024-01-15T10:30:00Z"
                    }
                }
            }
        },
        400: {
            "description": "Invalid request parameters or document content",
            "content": {
                "application/json": {
                    "example": {"detail": "Document ID must be a valid UUID format"}
                }
            }
        },
        404: {
            "description": "Document not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Document with ID 'doc-123' not found"}
                }
            }
        },
        422: {
            "description": "Validation error in request data",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {"field": "criteria.min_score", "message": "Must be between 0.0 and 1.0"}
                        ]
                    }
                }
            }
        },
        429: {
            "description": "Rate limit exceeded",
            "content": {
                "application/json": {
                    "example": {"detail": "Too many requests. Try again in 60 seconds"}
                }
            }
        },
        500: {
            "description": "Internal server error",
            "content": {
                "application/json": {
                    "example": {"detail": "Analysis service temporarily unavailable"}
                }
            }
        }
    },
    tags=["Analysis"]
)
async def analyze_document(
    document_id: str = Path(
        ...,
        description="Unique identifier of the document to analyze",
        example="doc-123",
        min_length=1,
        max_length=100
    ),
    request: AnalyzeDocumentRequest = Body(
        ...,
        description="Analysis configuration and criteria",
        example={
            "criteria": {
                "min_score": 0.7,
                "check_formatting": True,
                "check_consistency": True
            },
            "include_recommendations": True
        }
    ),
    use_case: AnalyzeDocumentUseCase = Depends(get_analyze_use_case)
):
    """Analyze a document for quality and issues.

    Performs automated analysis using configured detectors and returns
    detailed quality metrics, identified issues, and improvement recommendations.
    """
    try:
        result = await use_case.execute(document_id, request.criteria)
        return AnalysisResponse.from_domain(result)
    except DocumentNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Document with ID '{document_id}' not found"
        )
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except AnalysisTimeoutError:
        raise HTTPException(
            status_code=408,
            detail="Analysis request timed out. Please try again."
        )
```

### 6. OpenAPI/Swagger Documentation Standards

#### API Documentation Requirements
All REST endpoints MUST include comprehensive OpenAPI/Swagger documentation:

1. **Summary and Description**: Clear, concise endpoint purpose and detailed description
2. **Response Models**: Proper Pydantic schemas for all responses
3. **Request Models**: Validated request bodies with examples
4. **Status Codes**: All possible HTTP status codes documented
5. **Parameter Documentation**: Path, query, and body parameters fully described
6. **Authentication**: Security requirements clearly specified
7. **Examples**: Realistic request/response examples
8. **Tags**: Logical grouping for API organization

#### Router Configuration
```python
from fastapi import APIRouter

# Use descriptive tags for API organization
router = APIRouter(
    prefix="/api/v1/documents",
    tags=["Documents"],
    responses={
        401: {"description": "Unauthorized - Invalid or missing authentication"},
        403: {"description": "Forbidden - Insufficient permissions"},
        500: {"description": "Internal Server Error"}
    }
)
```

#### Parameter Documentation
```python
from fastapi import Query, Path, Body
from pydantic import Field

@router.get("/{document_id}")
async def get_document(
    document_id: str = Path(
        ...,
        description="Unique identifier of the document",
        example="doc-12345",
        min_length=1,
        max_length=100,
        regex=r"^[a-zA-Z0-9_-]+$"  # Custom validation
    ),
    include_metadata: bool = Query(
        False,
        description="Whether to include full metadata in response",
        example=True
    ),
    version: Optional[str] = Query(
        None,
        description="Specific version to retrieve",
        example="v1.2.0",
        min_length=1,
        max_length=20
    )
):
    """Retrieve a document by ID with optional version and metadata inclusion."""
    pass
```

#### Pydantic Models with OpenAPI Annotations
```python
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class DocumentResponse(BaseModel):
    """Response model for document data with comprehensive OpenAPI documentation."""

    id: str = Field(
        ...,
        description="Unique identifier for the document",
        example="doc-12345",
        min_length=1,
        max_length=100
    )

    title: str = Field(
        ...,
        description="Document title or headline",
        example="API Design Guidelines",
        min_length=1,
        max_length=200
    )

    content: str = Field(
        ...,
        description="Full document content in markdown format",
        example="# Introduction\n\nThis document covers API design best practices...",
        min_length=1
    )

    status: str = Field(
        "draft",
        description="Current document status",
        example="published",
        enum=["draft", "review", "published", "archived"]
    )

    created_at: datetime = Field(
        ...,
        description="Timestamp when document was first created",
        example="2024-01-15T10:30:00Z"
    )

    updated_at: datetime = Field(
        ...,
        description="Timestamp of last modification",
        example="2024-01-20T14:22:00Z"
    )

    tags: List[str] = Field(
        default_factory=list,
        description="List of tags associated with the document",
        example=["api", "documentation", "guidelines"],
        max_items=50
    )

    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional metadata key-value pairs",
        example={"author": "John Doe", "department": "Engineering"}
    )

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "id": "doc-12345",
                "title": "API Design Guidelines",
                "content": "# Introduction\n\nThis document covers API design best practices...",
                "status": "published",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-20T14:22:00Z",
                "tags": ["api", "documentation", "guidelines"],
                "metadata": {
                    "author": "John Doe",
                    "department": "Engineering",
                    "word_count": 1250
                }
            }
        }

    @classmethod
    def from_domain(cls, document: Document) -> 'DocumentResponse':
        """Create response from domain entity."""
        return cls(
            id=document.id.value,
            title=document.title,
            content=document.content,
            status=document.status,
            created_at=document.created_at,
            updated_at=document.updated_at,
            tags=document.tags,
            metadata=document.metadata
        )
```

#### Error Response Documentation
```python
@router.post(
    "/documents",
    response_model=DocumentResponse,
    responses={
        201: {
            "description": "Document created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "doc-12345",
                        "title": "New Document",
                        "status": "draft",
                        "created_at": "2024-01-15T10:30:00Z"
                    }
                }
            }
        },
        400: {
            "description": "Invalid request data",
            "content": {
                "application/json": {
                    "example": {
                        "type": "validation_error",
                        "message": "Request validation failed",
                        "errors": [
                            {"field": "title", "message": "Title is required"},
                            {"field": "content", "message": "Content cannot be empty"}
                        ]
                    }
                }
            }
        },
        409: {
            "description": "Document with this title already exists",
            "content": {
                "application/json": {
                    "example": {
                        "type": "conflict_error",
                        "message": "A document with this title already exists",
                        "existing_id": "doc-67890"
                    }
                }
            }
        }
    }
)
async def create_document(request: CreateDocumentRequest):
    """Create a new document."""
    pass
```

#### API Versioning and Deprecation
```python
@router.get(
    "/documents/{document_id}",
    deprecated=True,
    summary="Get Document (Deprecated)",
    description="""
    ⚠️ **DEPRECATED**: Use `/api/v2/documents/{document_id}` instead.

    This endpoint is deprecated and will be removed in version 3.0.0.
    Please migrate to the new version which includes additional metadata fields.
    """,
    responses={
        200: {"description": "Document retrieved (deprecated format)"},
        410: {"description": "Endpoint permanently removed - use v2 API"}
    }
)
async def get_document_v1(document_id: str):
    """Get document using deprecated format."""
    pass

@router.get(
    "/v2/documents/{document_id}",
    summary="Get Document v2",
    description="Retrieve a document with enhanced metadata support.",
    response_model=DocumentResponseV2
)
async def get_document_v2(document_id: str):
    """Get document using current format."""
    pass
```

#### Tag Organization
Use consistent tag naming for API organization:
- **Core Resources**: `Documents`, `Users`, `Projects`
- **Operations**: `Analysis`, `Search`, `Import/Export`
- **Management**: `Administration`, `Monitoring`, `Configuration`
- **Specialized**: `Authentication`, `Webhooks`, `Bulk Operations`

#### FastAPI Application Configuration
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Document Service API",
    description="""
    Comprehensive document management and analysis service.

    ## Features
    - Document CRUD operations with versioning
    - Quality analysis and automated improvements
    - Full-text search with advanced filtering
    - Bulk operations and batch processing
    - Webhook integrations and notifications

    ## Authentication
    All endpoints require Bearer token authentication.
    Include `Authorization: Bearer <token>` header in requests.
    """,
    version="2.1.0",
    contact={
        "name": "API Support",
        "email": "api-support@company.com",
        "url": "https://docs.company.com/support"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    },
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.company.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
```

### 6. Testing Standards

#### Unit Test Structure
```python
import pytest
from unittest.mock import AsyncMock, Mock
from ..domain.entities import Document, DocumentId
from ..domain.services import DocumentAnalysisService

class TestDocumentAnalysisService:
    """Test cases for document analysis service."""

    @pytest.fixture
    def analysis_service(self):
        return DocumentAnalysisService()

    @pytest.fixture
    def sample_document(self):
        return Document(
            id=DocumentId("test-doc-123"),
            title="Test Document",
            content="This is test content.",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

    def test_analyze_quality_high_score(self, analysis_service, sample_document):
        """Test quality analysis returns high score for good content."""
        result = analysis_service.analyze_document_quality(
            sample_document,
            AnalysisCriteria.default()
        )

        assert result.score >= 0.8
        assert len(result.issues) == 0
```

#### Integration Test Structure
```python
import pytest
from httpx import AsyncClient
from ..main import app

@pytest.mark.asyncio
class TestDocumentAPI:
    """Integration tests for document API."""

    async def test_create_and_retrieve_document(self, client: AsyncClient):
        """Test creating and retrieving a document."""
        # Create document
        create_response = await client.post(
            "/documents",
            json={
                "title": "Integration Test Document",
                "content": "Test content for integration testing."
            }
        )
        assert create_response.status_code == 201
        document_data = create_response.json()

        # Retrieve document
        doc_id = document_data["id"]
        get_response = await client.get(f"/documents/{doc_id}")
        assert get_response.status_code == 200

        retrieved = get_response.json()
        assert retrieved["title"] == "Integration Test Document"
```

## 🔧 Development Practices

### 1. Code Organization
- One responsibility per class/function
- Small, focused methods (< 20 lines)
- Clear separation of concerns
- Dependency injection over direct instantiation

### 2. Error Handling
```python
# Domain exceptions
class DocumentNotFoundError(ValueError):
    """Raised when document is not found."""
    pass

class ValidationError(ValueError):
    """Raised when validation fails."""
    pass

# Application error handling
try:
    result = await use_case.execute(document_id)
except DocumentNotFoundError:
    # Handle domain error
    raise HTTPException(status_code=404, detail="Document not found")
except ValidationError as e:
    # Handle validation error
    raise HTTPException(status_code=400, detail=str(e))
```

### 3. Async/Await Patterns
```python
# Always use async for I/O operations
async def create_document(self, document: Document) -> None:
    async with self.connection_pool.get_connection() as conn:
        await conn.execute("INSERT INTO documents ...", document.values())

# Use sync for pure computation
def calculate_score(self, content: str) -> float:
    return len(content.split()) / 100.0  # Pure function
```

### 4. Logging Standards
```python
import logging

logger = logging.getLogger(__name__)

class DocumentService:
    async def process_document(self, document_id: str):
        logger.info("Processing document", extra={
            "document_id": document_id,
            "operation": "process_document",
            "service": "DocumentService"
        })

        try:
            # Business logic
            result = await self._process(document_id)

            logger.info("Document processed successfully", extra={
                "document_id": document_id,
                "result": result.status,
                "duration_ms": result.duration
            })

        except Exception as e:
            logger.error("Failed to process document", extra={
                "document_id": document_id,
                "error": str(e),
                "error_type": type(e).__name__
            }, exc_info=True)
            raise
```

## 📊 Quality Metrics

### Code Quality Targets
- **Cyclomatic Complexity**: < 10 per method
- **Method Length**: < 20 lines
- **Class Length**: < 200 lines
- **Test Coverage**: > 90%
- **Type Hint Coverage**: 100%

### Documentation Standards
- All public methods documented with docstrings
- Complex business logic explained
- API endpoints documented with examples
- Error conditions documented

---

*These standards will be enforced through code reviews and automated tooling. All new services must follow these patterns, and existing services will be refactored to comply.*
