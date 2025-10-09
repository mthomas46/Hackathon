<!-- AI_READ_PRIORITY: 2 -->
<!-- AI_TAGS: standards, naming, conventions, patterns -->
<!-- AI_KEY_SECTIONS: Service Naming, Directory Structure, Python Conventions, API Conventions -->

---
ai_metadata:
  purpose: coding_standards
  read_priority: 2
  context_level: reference
  tags:
  - standards
  - naming
  - conventions
  - patterns
  when_to_read: During implementation (Phase 3)
  key_sections:
  - Service Naming
  - Directory Structure
  - Python Conventions
  - API Conventions
  execution_relevance: high
  reference_type: continuous
---

# 📏 Naming Conventions & Standards

**Version**: 1.0.0  
**Last Updated**: October 8, 2025  
**Status**: Active

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Service Naming](#service-naming)
3. [Directory Structure](#directory-structure)
4. [Python Code Conventions](#python-code-conventions)
5. [API Conventions](#api-conventions)
6. [Database Conventions](#database-conventions)
7. [Configuration Conventions](#configuration-conventions)
8. [Documentation Conventions](#documentation-conventions)
9. [Testing Conventions](#testing-conventions)
10. [Docker Conventions](#docker-conventions)

---

## 🎯 Overview

This document defines the naming conventions and coding standards for all services in the Hackathon ecosystem. Consistency in naming and structure improves:

- **Readability**: Code is easier to understand
- **Maintainability**: Changes are easier to implement
- **Collaboration**: Team members can navigate unfamiliar code
- **Automation**: Tools can parse and analyze code effectively

### Guiding Principles

1. **Clarity over brevity**: Prefer descriptive names over short ones
2. **Consistency**: Same patterns across all services
3. **Pythonic**: Follow Python community standards (PEP 8)
4. **Domain-focused**: Names reflect business concepts
5. **No abbreviations**: Unless widely accepted (e.g., API, URL, ID)

---

## 🏢 Service Naming

### Service Names

**Format**: `lowercase-with-hyphens`

**Pattern**: `<domain>-<function>` or `<function>-<type>`

**Examples**:
```
✅ Good:
- doc-store
- llm-gateway
- analysis-service
- memory-agent
- github-mcp
- mcp-orchestrator

❌ Bad:
- DocStore (use lowercase)
- llm_gateway (use hyphens, not underscores)
- analysissvc (avoid abbreviations)
- mem-agt (avoid abbreviations)
```

### Port Assignment

**Pattern**: Services use consistent port ranges

```
5000-5099: Core Infrastructure
  5020: analysis-service
  5055: llm-gateway
  5087: doc-store
  5099: orchestrator

5100-5199: Analysis & Processing
  5100: secure-analyzer
  5105: architecture-digitizer
  5110: prompt-store
  5120: interpreter
  
5200-5299: MCP Services
  5200: mcp-orchestrator
  5300: mcp-gateway

5300-5399: Integration Services
  5300: github-mcp

5400-5499: Supporting Services
  5400: mcp-provisioner

8000-8999: External/Public Ports (Docker mapped)
```

### Container Names

**Format**: `hackathon-<service-name>`

**Examples**:
```
hackathon-doc-store
hackathon-llm-gateway
hackathon-analysis-service
```

---

## 📁 Directory Structure

### Service Root Structure

```
service-name/
├── domain/              # Business logic (PascalCase classes)
├── application/         # Use cases (PascalCase classes)
├── infrastructure/      # External deps (snake_case files)
├── presentation/        # API layer (snake_case files)
├── tests/              # Test suite (test_*.py)
├── config/             # Configuration files
├── docs/               # Documentation
├── utilities/          # Service utilities
├── main.py            # Entry point
├── Dockerfile         # Docker config
├── requirements.txt   # Dependencies
└── README.md          # Service docs
```

### File Naming

**Python Files**: `snake_case.py`
```
✅ Good:
- user_repository.py
- analysis_service.py
- create_document_command.py

❌ Bad:
- UserRepository.py (use snake_case)
- analysisService.py (no camelCase)
- CreateDocumentCommand.py (use snake_case)
```

**Test Files**: `test_<module_name>.py`
```
✅ Good:
- test_user_repository.py
- test_analysis_service.py
- test_create_document_command.py
```

**Configuration Files**: `config.<env>.yaml`
```
config.yaml
config.development.yaml
config.production.yaml
config.test.yaml
```

---

## 🐍 Python Code Conventions

### Class Names

**Format**: `PascalCase`

**Domain Entities**: `<Entity>` (noun)
```python
class Document:
    pass

class Analysis:
    pass

class Finding:
    pass
```

**Value Objects**: `<Value>` (descriptive noun)
```python
class DocumentId:
    pass

class AnalysisType:
    pass

class Confidence:
    pass
```

**Services**: `<Domain>Service`
```python
class DocumentService:
    pass

class AnalysisService:
    pass
```

**Repositories**: `<Entity>Repository` and `<Implementation><Entity>Repository`
```python
# Interface
class DocumentRepository(ABC):
    pass

# Implementation
class SQLiteDocumentRepository(DocumentRepository):
    pass

class PostgreSQLDocumentRepository(DocumentRepository):
    pass
```

**Commands/Queries**: `<Action><Entity>Command/Query`
```python
class CreateDocumentCommand:
    pass

class GetDocumentQuery:
    pass

class UpdateAnalysisCommand:
    pass
```

**DTOs**: `<Entity><RequestType>`
```python
class DocumentCreateRequest:
    pass

class DocumentResponse:
    pass

class AnalysisResultDTO:
    pass
```

### Function Names

**Format**: `snake_case`

**Pattern**: Verb phrase describing action

```python
✅ Good:
def create_document(document_data: dict) -> Document:
    pass

def analyze_content(content: str) -> Analysis:
    pass

def get_findings_by_severity(severity: str) -> List[Finding]:
    pass

❌ Bad:
def CreateDocument(documentData):  # Use snake_case
    pass

def analyze(c):  # Be specific
    pass

def getFindings():  # Use snake_case
    pass
```

### Variable Names

**Format**: `snake_case`

**Pattern**: Descriptive nouns

```python
✅ Good:
document_id = "doc-123"
analysis_result = perform_analysis(document)
findings_list = repository.get_all_findings()
max_retries = 3

❌ Bad:
docId = "doc-123"  # No camelCase
ar = perform_analysis(document)  # No abbreviations
findingsLst = repository.get_all_findings()  # No abbreviations
MAX_RETRIES = 3  # Constants use UPPER_SNAKE_CASE
```

### Constants

**Format**: `UPPER_SNAKE_CASE`

```python
MAX_RETRY_ATTEMPTS = 3
DEFAULT_TIMEOUT_SECONDS = 30
API_VERSION = "v1"
BASE_URL = "http://localhost:5000"
```

### Private Members

**Format**: Prefix with single underscore `_`

```python
class DocumentService:
    def __init__(self):
        self._repository = None  # Private attribute
    
    def _validate_document(self, doc):  # Private method
        pass
```

### Type Hints

**Always use type hints for public APIs**

```python
from typing import List, Optional, Dict, Any

def create_document(
    title: str,
    content: str,
    metadata: Optional[Dict[str, Any]] = None
) -> Document:
    pass

def get_documents(
    limit: int = 10,
    offset: int = 0
) -> List[Document]:
    pass
```

---

## 🌐 API Conventions

### Endpoint Naming

**Format**: `/api/v{version}/{resource}[/{id}][/{sub-resource}][/{action}]`

**Resources**: Plural nouns, lowercase with hyphens

```
✅ Good:
GET    /api/v1/documents
GET    /api/v1/documents/{id}
POST   /api/v1/documents
PUT    /api/v1/documents/{id}
DELETE /api/v1/documents/{id}
GET    /api/v1/documents/{id}/analyses
POST   /api/v1/documents/{id}/analyze

❌ Bad:
GET    /api/v1/document (use plural)
GET    /api/v1/getDocuments (no verbs, use HTTP method)
POST   /api/v1/documents/create (no action in URL)
GET    /api/v1/documents/{id}/getAnalyses (no verbs)
```

### HTTP Methods

```
GET    - Retrieve resource(s)
POST   - Create new resource
PUT    - Update entire resource
PATCH  - Partial update
DELETE - Remove resource
```

### Query Parameters

**Format**: `snake_case`

```python
✅ Good:
GET /api/v1/documents?limit=10&offset=20&sort_by=created_at&order=desc

❌ Bad:
GET /api/v1/documents?limit=10&offset=20&sortBy=created_at  # No camelCase
```

### Request/Response Bodies

**Format**: `snake_case` for JSON keys

```json
✅ Good:
{
  "document_id": "doc-123",
  "title": "My Document",
  "created_at": "2025-10-08T10:00:00Z",
  "analysis_results": [
    {
      "analysis_type": "consistency",
      "score": 0.95
    }
  ]
}

❌ Bad:
{
  "documentId": "doc-123",  // No camelCase
  "Title": "My Document",   // No PascalCase
  "createdAt": "2025-10-08T10:00:00Z"
}
```

### HTTP Status Codes

**Standard Usage**:
```
200 OK              - Successful GET, PUT, PATCH, DELETE
201 Created         - Successful POST
204 No Content      - Successful DELETE (no body)
400 Bad Request     - Invalid input
401 Unauthorized    - Missing/invalid authentication
403 Forbidden       - Insufficient permissions
404 Not Found       - Resource not found
409 Conflict        - Resource conflict (e.g., duplicate)
422 Unprocessable   - Validation errors
500 Server Error    - Internal error
503 Unavailable     - Service temporarily unavailable
```

### Error Response Format

**Standard structure for all errors**:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Document title is required",
    "details": [
      {
        "field": "title",
        "message": "Field is required"
      }
    ],
    "timestamp": "2025-10-08T10:00:00Z",
    "request_id": "req-123"
  }
}
```

---

## 🗄️ Database Conventions

### Table Names

**Format**: `snake_case`, plural

```sql
✅ Good:
documents
analyses
findings
analysis_results

❌ Bad:
Document (use lowercase and plural)
analysis (use plural)
AnalysisResults (use snake_case)
```

### Column Names

**Format**: `snake_case`

```sql
✅ Good:
document_id
title
content
created_at
updated_at
analysis_type
confidence_score

❌ Bad:
documentId (no camelCase)
DocumentTitle (no PascalCase)
analysistype (use underscores)
```

### Primary Keys

**Format**: `id` (integer) or `<table>_id` (UUID)

```sql
-- Auto-increment integer
CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ...
);

-- UUID
CREATE TABLE documents (
    document_id TEXT PRIMARY KEY,
    ...
);
```

### Foreign Keys

**Format**: `<referenced_table>_id`

```sql
CREATE TABLE analyses (
    id INTEGER PRIMARY KEY,
    document_id INTEGER,
    FOREIGN KEY (document_id) REFERENCES documents(id)
);
```

### Indexes

**Format**: `idx_<table>_<columns>`

```sql
CREATE INDEX idx_documents_created_at ON documents(created_at);
CREATE INDEX idx_analyses_document_id_type ON analyses(document_id, analysis_type);
```

---

## ⚙️ Configuration Conventions

### Environment Variables

**Format**: `UPPER_SNAKE_CASE`

**Pattern**: `<SERVICE>_<CATEGORY>_<NAME>`

```bash
✅ Good:
SERVICE_NAME=analysis-service
SERVICE_API_PORT=5020
DOC_STORE_URL=http://doc-store:5087
REDIS_API_HOST=redis
REDIS_API_PORT=6379
DATABASE_CONNECTION_POOL_SIZE=10
LLM_GATEWAY_TIMEOUT=30

❌ Bad:
serviceName=analysis-service (no camelCase)
service-name=analysis-service (no hyphens)
DocStoreUrl=http://doc-store:5087 (no PascalCase)
redis-host=redis (use UPPER_SNAKE_CASE)
```

### Configuration File Keys

**Format**: `snake_case` (YAML) or `camelCase` (minimal use)

```yaml
✅ Good YAML:
service:
  name: analysis-service
  port: 5020
  
database:
  connection_pool_size: 10
  timeout: 30
  
external_services:
  doc_store:
    url: http://doc-store:5087
    timeout: 30
```

---

## 📖 Documentation Conventions

### File Names

```
README.md              - Service overview
ARCHITECTURE.md        - Architecture details
API.md                 - API documentation
INTEGRATION.md         - Integration guide
TROUBLESHOOTING.md     - Common issues
CHANGELOG.md           - Version history
```

### Docstring Format

**Use Google-style docstrings**:

```python
def create_document(
    title: str,
    content: str,
    metadata: Optional[Dict[str, Any]] = None
) -> Document:
    """Create a new document with the given information.
    
    This function creates a new document in the system with the provided
    title, content, and optional metadata. The document is validated before
    creation and stored in the repository.
    
    Args:
        title: The title of the document. Must not be empty.
        content: The content of the document. Must not be empty.
        metadata: Optional metadata as key-value pairs. Defaults to None.
    
    Returns:
        A Document object representing the created document with an assigned ID.
    
    Raises:
        ValidationError: If title or content is empty.
        DuplicateError: If a document with the same title already exists.
        StorageError: If there's an error storing the document.
    
    Example:
        >>> doc = create_document(
        ...     title="My Document",
        ...     content="Document content",
        ...     metadata={"author": "John Doe"}
        ... )
        >>> print(doc.id)
        'doc-123'
    """
    pass
```

### README Structure

```markdown
# Service Name

Brief description

## Overview
Purpose and key features

## Quick Start
Installation and running instructions

## Architecture
DDD layers and components

## API Reference
Endpoints and examples

## Configuration
Environment variables and config files

## Development
Local setup and testing

## Integration
Dependencies and integration patterns

## Troubleshooting
Common issues and solutions
```

---

## 🧪 Testing Conventions

### Test File Names

**Format**: `test_<module_under_test>.py`

```
✅ Good:
test_document_repository.py
test_analysis_service.py
test_create_document_command.py
test_document_controller.py
```

### Test Function Names

**Format**: `test_<scenario>_<expected_behavior>`

```python
✅ Good:
def test_create_document_with_valid_data_returns_document():
    pass

def test_create_document_with_empty_title_raises_validation_error():
    pass

def test_get_document_with_nonexistent_id_returns_none():
    pass

❌ Bad:
def test_create_document():  # Be specific about scenario
    pass

def testCreateDocument():  # Use snake_case
    pass

def test1():  # Use descriptive names
    pass
```

### Test Structure

**Use Arrange-Act-Assert (AAA) pattern**:

```python
def test_create_document_with_valid_data_returns_document():
    # Arrange
    title = "Test Document"
    content = "Test content"
    repository = InMemoryDocumentRepository()
    service = DocumentService(repository)
    
    # Act
    result = service.create_document(title, content)
    
    # Assert
    assert result is not None
    assert result.title == title
    assert result.content == content
    assert result.id is not None
```

### Fixture Names

**Format**: `snake_case`, descriptive

```python
import pytest

@pytest.fixture
def document_repository():
    return InMemoryDocumentRepository()

@pytest.fixture
def sample_document():
    return Document(
        id="doc-123",
        title="Sample Document",
        content="Sample content"
    )

@pytest.fixture
def document_service(document_repository):
    return DocumentService(document_repository)
```

---

## 🐳 Docker Conventions

### Dockerfile Naming

```
Dockerfile                    - Main Dockerfile
Dockerfile.development        - Development variant
Dockerfile.production         - Production variant
Dockerfile.test              - Testing variant
```

### Image Names

**Format**: `<registry>/<service-name>:<tag>`

```
✅ Good:
hackathon/analysis-service:latest
hackathon/doc-store:v1.2.3
hackathon/llm-gateway:dev

❌ Bad:
analysis-service (no registry prefix)
AnalysisService:latest (use lowercase)
analysis_service:latest (use hyphens)
```

### Docker Compose Service Names

**Match service directory names**:

```yaml
services:
  analysis-service:  # Matches services/analysis-service/
    build: ./services/analysis-service
    
  doc-store:         # Matches services/doc_store/
    build: ./services/doc_store
```

### Volume Names

**Format**: `<service>_<purpose>`

```yaml
volumes:
  doc_store_data:
  prompt_store_data:
  redis_data:
  mcp_registry_data:
```

---

## 📊 Examples Summary

### Quick Reference Table

| Item | Convention | Example |
|------|-----------|---------|
| Service Names | lowercase-with-hyphens | `analysis-service` |
| Python Files | snake_case.py | `document_service.py` |
| Classes | PascalCase | `DocumentService` |
| Functions | snake_case | `create_document()` |
| Variables | snake_case | `document_id` |
| Constants | UPPER_SNAKE_CASE | `MAX_RETRIES` |
| API Endpoints | /resource/action | `/api/v1/documents` |
| Query Params | snake_case | `?limit=10&sort_by=date` |
| JSON Keys | snake_case | `{"document_id": "123"}` |
| DB Tables | snake_case, plural | `documents` |
| DB Columns | snake_case | `document_id` |
| Env Vars | UPPER_SNAKE_CASE | `SERVICE_NAME` |
| Config Keys | snake_case | `connection_pool_size` |
| Test Files | test_*.py | `test_document_service.py` |
| Test Functions | test_scenario_result | `test_create_returns_document` |

---

## 🔄 Enforcement

### Pre-commit Hooks

Use pre-commit hooks to enforce standards:
- `black` for code formatting
- `flake8` for linting
- `mypy` for type checking
- `pylint` for code quality

### Code Review Checklist

- [ ] Naming follows conventions
- [ ] Type hints on public APIs
- [ ] Docstrings on all public functions
- [ ] Tests follow naming conventions
- [ ] API endpoints follow REST principles
- [ ] Configuration uses standard patterns

### CI/CD Validation

- Automated linting checks
- Type checking validation
- Test naming validation
- Documentation generation

---

**Document Control**  
**Version**: 1.0.0  
**Last Updated**: October 8, 2025  
**Next Review**: 2025-11-08  
**Owner**: Hackathon Team

