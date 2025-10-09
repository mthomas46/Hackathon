<!-- AI_READ_PRIORITY: 3 -->
<!-- AI_TAGS: api, rest, openapi, swagger, standard-endpoints -->
<!-- AI_KEY_SECTIONS: Standard Endpoints, OpenAPI Requirements, Implementation Guide -->

---
ai_metadata:
  purpose: api_guidance
  read_priority: 3
  context_level: tactical
  tags:
  - api
  - rest
  - openapi
  - swagger
  - standard-endpoints
  when_to_read: During Phase 5 (Documentation)
  key_sections:
  - Standard Endpoints
  - OpenAPI Requirements
  - Implementation Guide
  execution_relevance: phase-specific
  relevant_phases:
  - Phase 5
---

# 🔌 API Standardization Strategy - Required Endpoints & OpenAPI

**Version**: 1.0.0  
**Created**: October 9, 2025  
**Status**: Active

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Standard Endpoints](#standard-endpoints)
3. [OpenAPI Requirements](#openapi-requirements)
4. [Implementation Guide](#implementation-guide)
5. [Validation](#validation)
6. [Examples](#examples)

---

## 🎯 Overview

### Purpose

Every REST-based service must implement **standardized endpoints** that provide:

- **Health Monitoring**: Service health status
- **Service Discovery**: Service description and capabilities
- **Endpoint Discovery**: List of available endpoints
- **Relationship Discovery**: Service dependencies and connections

These endpoints enable:
- Automated service discovery
- Health monitoring and alerting
- Dependency mapping
- API documentation generation
- Integration testing

### Requirements

| Requirement | Description |
|-------------|-------------|
| **Standard Endpoints** | 4 required endpoints (health, about-me, endpoints, provider-consumer) |
| **OpenAPI/Swagger** | Complete API documentation with annotations |
| **Swagger UI** | Interactive API documentation page |
| **Response Format** | Standardized JSON responses |
| **HTTP Status Codes** | Proper status codes for all responses |

---

## 🔌 Standard Endpoints

### 1. Health Endpoint

**Purpose**: Service health status for monitoring

**Endpoint**: `GET /health`

**Response**: 200 OK (healthy) or 503 Service Unavailable (unhealthy)

**Response Format**:
```json
{
  "status": "healthy",
  "service": "doc-store",
  "version": "2.0.0",
  "timestamp": "2025-10-09T10:30:45.123Z",
  "uptime_seconds": 86400,
  "dependencies": {
    "redis": {
      "status": "healthy",
      "latency_ms": 2
    },
    "database": {
      "status": "healthy",
      "latency_ms": 5
    }
  },
  "metrics": {
    "requests_total": 12345,
    "requests_per_second": 15.2,
    "error_rate": 0.001
  }
}
```

**Unhealthy Response**:
```json
{
  "status": "unhealthy",
  "service": "doc-store",
  "version": "2.0.0",
  "timestamp": "2025-10-09T10:30:45.123Z",
  "uptime_seconds": 86400,
  "errors": [
    {
      "component": "redis",
      "error": "Connection timeout",
      "since": "2025-10-09T10:28:00.000Z"
    }
  ],
  "dependencies": {
    "redis": {
      "status": "unhealthy",
      "error": "Connection timeout"
    },
    "database": {
      "status": "healthy",
      "latency_ms": 5
    }
  }
}
```

**Implementation**:
```python
from fastapi import APIRouter, status
from datetime import datetime
import time

router = APIRouter()

start_time = time.time()

@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Health check endpoint
    
    Returns service health status including:
    - Overall health status
    - Dependency health
    - Basic metrics
    """
    # Check dependencies
    dependencies_health = await check_dependencies()
    
    # Determine overall status
    is_healthy = all(
        dep["status"] == "healthy" 
        for dep in dependencies_health.values()
    )
    
    response = {
        "status": "healthy" if is_healthy else "unhealthy",
        "service": "doc-store",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "uptime_seconds": int(time.time() - start_time),
        "dependencies": dependencies_health,
        "metrics": await get_metrics()
    }
    
    if not is_healthy:
        response["errors"] = get_errors()
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=response
        )
    
    return response
```

---

### 2. About-Me Endpoint

**Purpose**: Service descriptor and capabilities

**Endpoint**: `GET /about-me`

**Response**: 200 OK

**Response Format**:
```json
{
  "service_name": "doc-store",
  "display_name": "Document Store Service",
  "version": "2.0.0",
  "description": "Centralized document storage and retrieval service",
  "capabilities": {
    "solo": [
      "Store documents with metadata",
      "Retrieve documents by ID",
      "Search documents by content",
      "Version document changes",
      "Manage document lifecycle"
    ],
    "ecosystem": [
      "Provides document storage for all services",
      "Enables document versioning across ecosystem",
      "Supports cross-service document sharing",
      "Maintains document access audit trail"
    ]
  },
  "features": [
    "RESTful API with OpenAPI documentation",
    "Document versioning and history",
    "Full-text search",
    "Metadata tagging",
    "Access control",
    "Bulk operations",
    "Real-time notifications"
  ],
  "technology_stack": {
    "language": "Python 3.11",
    "framework": "FastAPI 0.104.0",
    "database": "PostgreSQL 15",
    "cache": "Redis 7.0",
    "architecture": "Domain-Driven Design (DDD)"
  },
  "architecture": {
    "pattern": "DDD (Domain-Driven Design)",
    "layers": ["Domain", "Application", "Infrastructure", "Presentation"],
    "bounded_context": "Document Management"
  },
  "contact": {
    "team": "Platform Team",
    "slack": "#platform-support",
    "repository": "https://github.com/org/hackathon/services/doc-store"
  },
  "links": {
    "documentation": "http://localhost:5001/docs",
    "openapi_spec": "http://localhost:5001/openapi.json",
    "health": "http://localhost:5001/health",
    "endpoints": "http://localhost:5001/endpoints",
    "relationships": "http://localhost:5001/provider-consumer"
  }
}
```

**Implementation**:
```python
@router.get("/about-me", status_code=status.HTTP_200_OK)
async def about_me():
    """
    Service descriptor endpoint
    
    Returns comprehensive information about:
    - Service identity and version
    - Capabilities (solo and ecosystem)
    - Features and technology stack
    - Architecture and design patterns
    - Contact information and links
    """
    return {
        "service_name": config.SERVICE_NAME,
        "display_name": config.DISPLAY_NAME,
        "version": config.VERSION,
        "description": config.DESCRIPTION,
        "capabilities": {
            "solo": config.SOLO_CAPABILITIES,
            "ecosystem": config.ECOSYSTEM_CAPABILITIES
        },
        "features": config.FEATURES,
        "technology_stack": {
            "language": "Python 3.11",
            "framework": "FastAPI 0.104.0",
            "database": config.DATABASE_TYPE,
            "cache": config.CACHE_TYPE,
            "architecture": "Domain-Driven Design (DDD)"
        },
        "architecture": {
            "pattern": "DDD",
            "layers": ["Domain", "Application", "Infrastructure", "Presentation"],
            "bounded_context": config.BOUNDED_CONTEXT
        },
        "contact": config.CONTACT_INFO,
        "links": {
            "documentation": f"http://localhost:{config.PORT}/docs",
            "openapi_spec": f"http://localhost:{config.PORT}/openapi.json",
            "health": f"http://localhost:{config.PORT}/health",
            "endpoints": f"http://localhost:{config.PORT}/endpoints",
            "relationships": f"http://localhost:{config.PORT}/provider-consumer"
        }
    }
```

---

### 3. Endpoints Listing

**Purpose**: Discoverable list of all available endpoints

**Endpoint**: `GET /endpoints`

**Response**: 200 OK

**Response Format**:
```json
{
  "service": "doc-store",
  "version": "2.0.0",
  "total_endpoints": 15,
  "categories": {
    "standard": 4,
    "business": 8,
    "admin": 3
  },
  "endpoints": [
    {
      "path": "/health",
      "method": "GET",
      "category": "standard",
      "description": "Service health check",
      "authentication": false,
      "rate_limit": "1000/minute"
    },
    {
      "path": "/about-me",
      "method": "GET",
      "category": "standard",
      "description": "Service descriptor",
      "authentication": false,
      "rate_limit": "100/minute"
    },
    {
      "path": "/endpoints",
      "method": "GET",
      "category": "standard",
      "description": "List all endpoints",
      "authentication": false,
      "rate_limit": "100/minute"
    },
    {
      "path": "/provider-consumer",
      "method": "GET",
      "category": "standard",
      "description": "Service relationships",
      "authentication": false,
      "rate_limit": "100/minute"
    },
    {
      "path": "/api/v2/documents",
      "method": "POST",
      "category": "business",
      "description": "Create new document",
      "authentication": true,
      "rate_limit": "100/minute",
      "request_body": {
        "content_type": "application/json",
        "schema": "$ref:CreateDocumentRequest"
      },
      "responses": {
        "201": "Document created successfully",
        "400": "Invalid request",
        "401": "Unauthorized",
        "422": "Validation error"
      }
    },
    {
      "path": "/api/v2/documents/{id}",
      "method": "GET",
      "category": "business",
      "description": "Retrieve document by ID",
      "authentication": true,
      "rate_limit": "1000/minute",
      "path_parameters": {
        "id": {
          "type": "string",
          "format": "uuid",
          "description": "Document ID"
        }
      },
      "responses": {
        "200": "Document retrieved successfully",
        "404": "Document not found",
        "401": "Unauthorized"
      }
    }
  ],
  "openapi_spec": "http://localhost:5001/openapi.json",
  "swagger_ui": "http://localhost:5001/docs"
}
```

**Implementation**:
```python
@router.get("/endpoints", status_code=status.HTTP_200_OK)
async def list_endpoints(request: Request):
    """
    List all available endpoints
    
    Returns comprehensive list of all API endpoints including:
    - Path and HTTP method
    - Category (standard/business/admin)
    - Description
    - Authentication requirements
    - Rate limits
    - Request/response schemas
    """
    app = request.app
    endpoints = []
    
    for route in app.routes:
        if hasattr(route, "methods"):
            for method in route.methods:
                if method in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                    endpoint_info = {
                        "path": route.path,
                        "method": method,
                        "category": get_category(route.path),
                        "description": get_description(route),
                        "authentication": requires_auth(route),
                        "rate_limit": get_rate_limit(route)
                    }
                    
                    # Add request/response details
                    if hasattr(route, "endpoint"):
                        endpoint_info.update(get_endpoint_details(route.endpoint))
                    
                    endpoints.append(endpoint_info)
    
    return {
        "service": config.SERVICE_NAME,
        "version": config.VERSION,
        "total_endpoints": len(endpoints),
        "categories": count_categories(endpoints),
        "endpoints": sorted(endpoints, key=lambda x: (x["category"], x["path"])),
        "openapi_spec": f"http://localhost:{config.PORT}/openapi.json",
        "swagger_ui": f"http://localhost:{config.PORT}/docs"
    }
```

---

### 4. Provider-Consumer Relationships

**Purpose**: Service dependency mapping

**Endpoint**: `GET /provider-consumer`

**Response**: 200 OK

**Response Format**:
```json
{
  "service_name": "doc-store",
  "version": "2.0.0",
  "port": 5001,
  "timestamp": "2025-10-09T10:30:45.123Z",
  "relationships": {
    "providers": [
      {
        "service": "redis",
        "type": "provider",
        "purpose": "Caching and pub/sub messaging",
        "connection_type": "direct",
        "endpoints_used": ["N/A (Redis protocol)"],
        "critical": true,
        "health_check": "redis://localhost:6379",
        "fallback_strategy": "none",
        "timeout_ms": 5000
      },
      {
        "service": "postgres",
        "type": "provider",
        "purpose": "Document persistence",
        "connection_type": "direct",
        "endpoints_used": ["N/A (SQL)"],
        "critical": true,
        "health_check": "postgresql://localhost:5432",
        "fallback_strategy": "none",
        "timeout_ms": 10000
      }
    ],
    "consumers": [
      {
        "service": "orchestrator",
        "type": "consumer",
        "purpose": "Document orchestration and workflows",
        "connection_type": "http",
        "endpoints_consumed": [
          "POST /api/v2/documents",
          "GET /api/v2/documents/{id}",
          "PUT /api/v2/documents/{id}",
          "DELETE /api/v2/documents/{id}"
        ],
        "critical": false,
        "request_volume": "high",
        "typical_requests_per_minute": 500
      },
      {
        "service": "analysis-service",
        "type": "consumer",
        "purpose": "Document retrieval for analysis",
        "connection_type": "http",
        "endpoints_consumed": [
          "GET /api/v2/documents/{id}",
          "GET /api/v2/documents?search={query}"
        ],
        "critical": false,
        "request_volume": "medium",
        "typical_requests_per_minute": 100
      },
      {
        "service": "notification-service",
        "type": "consumer",
        "purpose": "Document change notifications",
        "connection_type": "http",
        "endpoints_consumed": [
          "GET /api/v2/documents/{id}"
        ],
        "critical": false,
        "request_volume": "low",
        "typical_requests_per_minute": 20
      }
    ],
    "bidirectional": [
      {
        "service": "prompt-store",
        "type": "provide-consume",
        "purpose": "Document template exchange",
        "connection_type": "http",
        "provides": {
          "endpoints": [
            "GET /api/v2/documents/{id}"
          ],
          "purpose": "Provide document templates"
        },
        "consumes": {
          "endpoints": [
            "GET /api/v2/prompts/{id}"
          ],
          "purpose": "Retrieve prompt templates"
        },
        "critical": false,
        "request_volume": "low"
      }
    ]
  },
  "summary": {
    "total_connections": 6,
    "providers_count": 2,
    "consumers_count": 3,
    "bidirectional_count": 1,
    "scope": "core",
    "critical_dependencies": ["redis", "postgres"],
    "high_volume_consumers": ["orchestrator"]
  },
  "dependency_health": {
    "all_critical_healthy": true,
    "degraded_services": [],
    "unavailable_services": []
  }
}
```

**Scope Determination**:
```python
def get_scope(total_connections: int) -> str:
    """Determine relationship scope"""
    if total_connections < 4:
        return "standard"
    elif total_connections < len(ALL_SERVICES):
        return "core"
    else:
        return "all"
```

**Implementation**:
```python
@router.get("/provider-consumer", status_code=status.HTTP_200_OK)
async def provider_consumer_relationships():
    """
    Service relationship mapping
    
    Returns comprehensive dependency information:
    - Services we depend on (providers)
    - Services depending on us (consumers)
    - Bidirectional relationships
    - Connection details and health
    - Criticality and fallback strategies
    """
    # Load relationship configuration
    relationships = load_relationships_config()
    
    # Check dependency health
    dependency_health = await check_dependency_health(
        relationships["providers"]
    )
    
    # Calculate summary
    total_connections = (
        len(relationships["providers"]) +
        len(relationships["consumers"]) +
        len(relationships["bidirectional"])
    )
    
    return {
        "service_name": config.SERVICE_NAME,
        "version": config.VERSION,
        "port": config.PORT,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "relationships": relationships,
        "summary": {
            "total_connections": total_connections,
            "providers_count": len(relationships["providers"]),
            "consumers_count": len(relationships["consumers"]),
            "bidirectional_count": len(relationships["bidirectional"]),
            "scope": get_scope(total_connections),
            "critical_dependencies": get_critical_dependencies(relationships),
            "high_volume_consumers": get_high_volume_consumers(relationships)
        },
        "dependency_health": dependency_health
    }
```

---

## 📚 OpenAPI Requirements

### 1. Complete API Documentation

Every REST service must have **complete OpenAPI 3.0+ documentation** with:

- **API Metadata**: Title, description, version, contact
- **All Endpoints**: Complete path and operation documentation
- **Request Schemas**: All request body schemas defined
- **Response Schemas**: All response schemas defined
- **Error Responses**: All error codes documented
- **Authentication**: Security schemes defined
- **Examples**: Request/response examples for all endpoints

### 2. Swagger UI

Every service must provide **interactive Swagger UI** at `/docs`:

```python
from fastapi import FastAPI

app = FastAPI(
    title="Document Store Service",
    description="Centralized document storage and retrieval",
    version="2.0.0",
    contact={
        "name": "Platform Team",
        "email": "platform@example.com"
    },
    license_info={
        "name": "MIT"
    },
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc",  # ReDoc alternative
    openapi_url="/openapi.json"  # OpenAPI spec
)
```

### 3. OpenAPI Annotations

**All endpoints must have complete annotations**:

```python
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional

router = APIRouter()

class CreateDocumentRequest(BaseModel):
    """Request model for creating a document"""
    title: str = Field(..., description="Document title", min_length=1, max_length=255)
    content: str = Field(..., description="Document content", min_length=1)
    metadata: Optional[dict] = Field(None, description="Additional metadata")
    
    class Config:
        schema_extra = {
            "example": {
                "title": "My Document",
                "content": "Document content here",
                "metadata": {"author": "John Doe"}
            }
        }

class DocumentResponse(BaseModel):
    """Response model for document"""
    id: str = Field(..., description="Document ID")
    title: str = Field(..., description="Document title")
    content: str = Field(..., description="Document content")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "doc-123abc",
                "title": "My Document",
                "content": "Document content here",
                "created_at": "2025-10-09T10:30:45.123Z",
                "updated_at": "2025-10-09T10:30:45.123Z"
            }
        }

@router.post(
    "/api/v2/documents",
    status_code=status.HTTP_201_CREATED,
    response_model=DocumentResponse,
    summary="Create new document",
    description="Creates a new document with title, content, and optional metadata",
    response_description="The created document",
    tags=["Documents"],
    responses={
        201: {
            "description": "Document created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "doc-123abc",
                        "title": "My Document",
                        "content": "Document content here",
                        "created_at": "2025-10-09T10:30:45.123Z",
                        "updated_at": "2025-10-09T10:30:45.123Z"
                    }
                }
            }
        },
        400: {
            "description": "Invalid request",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Invalid document data"
                    }
                }
            }
        },
        401: {
            "description": "Unauthorized"
        },
        422: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["body", "title"],
                                "msg": "field required",
                                "type": "value_error.missing"
                            }
                        ]
                    }
                }
            }
        }
    }
)
async def create_document(request: CreateDocumentRequest):
    """
    Create a new document
    
    Args:
        request: Document creation request
        
    Returns:
        DocumentResponse: The created document
        
    Raises:
        HTTPException: 400 if validation fails
        HTTPException: 401 if not authenticated
    """
    # Implementation
    pass
```

### 4. Tags and Organization

Organize endpoints with tags:

```python
app = FastAPI(
    title="Document Store Service",
    openapi_tags=[
        {
            "name": "Standard",
            "description": "Standard endpoints (health, about-me, etc.)"
        },
        {
            "name": "Documents",
            "description": "Document CRUD operations"
        },
        {
            "name": "Search",
            "description": "Document search and filtering"
        },
        {
            "name": "Admin",
            "description": "Administrative operations"
        }
    ]
)
```

---

## 💻 Implementation Guide

### Step 1: Add Standard Endpoints

Create `presentation/api/standard/routes.py`:

```python
from fastapi import APIRouter
from .health import health_check
from .about_me import about_me
from .endpoints import list_endpoints
from .provider_consumer import provider_consumer_relationships

router = APIRouter()

router.add_api_route("/health", health_check, methods=["GET"], tags=["Standard"])
router.add_api_route("/about-me", about_me, methods=["GET"], tags=["Standard"])
router.add_api_route("/endpoints", list_endpoints, methods=["GET"], tags=["Standard"])
router.add_api_route("/provider-consumer", provider_consumer_relationships, methods=["GET"], tags=["Standard"])
```

### Step 2: Configure Service Metadata

Create `config/service_metadata.yaml`:

```yaml
service_name: doc-store
display_name: Document Store Service
version: 2.0.0
description: Centralized document storage and retrieval service

capabilities:
  solo:
    - Store documents with metadata
    - Retrieve documents by ID
    - Search documents by content
    - Version document changes
    - Manage document lifecycle
  
  ecosystem:
    - Provides document storage for all services
    - Enables document versioning across ecosystem
    - Supports cross-service document sharing
    - Maintains document access audit trail

features:
  - RESTful API with OpenAPI documentation
  - Document versioning and history
  - Full-text search
  - Metadata tagging
  - Access control
  - Bulk operations
  - Real-time notifications

technology_stack:
  language: Python 3.11
  framework: FastAPI 0.104.0
  database: PostgreSQL 15
  cache: Redis 7.0
  architecture: Domain-Driven Design (DDD)

contact:
  team: Platform Team
  slack: "#platform-support"
  repository: https://github.com/org/hackathon/services/doc-store
```

### Step 3: Configure Relationships

Create `config/service_relationships.yaml`:

```yaml
providers:
  - service: redis
    type: provider
    purpose: Caching and pub/sub messaging
    connection_type: direct
    critical: true
    health_check: redis://localhost:6379
    fallback_strategy: none
    timeout_ms: 5000
  
  - service: postgres
    type: provider
    purpose: Document persistence
    connection_type: direct
    critical: true
    health_check: postgresql://localhost:5432
    fallback_strategy: none
    timeout_ms: 10000

consumers:
  - service: orchestrator
    type: consumer
    purpose: Document orchestration and workflows
    connection_type: http
    endpoints_consumed:
      - POST /api/v2/documents
      - GET /api/v2/documents/{id}
      - PUT /api/v2/documents/{id}
      - DELETE /api/v2/documents/{id}
    critical: false
    request_volume: high
    typical_requests_per_minute: 500

bidirectional: []
```

### Step 4: Add OpenAPI Annotations

Update all endpoints with complete OpenAPI annotations (see examples above).

### Step 5: Test Standard Endpoints

```bash
# Health
curl http://localhost:5001/health

# About-me
curl http://localhost:5001/about-me

# Endpoints
curl http://localhost:5001/endpoints

# Provider-consumer
curl http://localhost:5001/provider-consumer

# Swagger UI
open http://localhost:5001/docs

# OpenAPI spec
curl http://localhost:5001/openapi.json
```

---

## ✅ Validation

### Checklist

**Standard Endpoints**:
- [ ] `/health` endpoint implemented
- [ ] `/about-me` endpoint implemented
- [ ] `/endpoints` endpoint implemented
- [ ] `/provider-consumer` endpoint implemented
- [ ] All endpoints return proper JSON
- [ ] All endpoints return correct HTTP status codes

**OpenAPI/Swagger**:
- [ ] OpenAPI spec available at `/openapi.json`
- [ ] Swagger UI available at `/docs`
- [ ] All endpoints documented
- [ ] All request schemas defined
- [ ] All response schemas defined
- [ ] All error responses documented
- [ ] Examples provided for all endpoints
- [ ] Tags used for organization

**Response Quality**:
- [ ] Health includes dependency status
- [ ] About-me includes all required fields
- [ ] Endpoints list is complete and accurate
- [ ] Provider-consumer relationships are accurate
- [ ] All timestamps in ISO 8601 format
- [ ] All IDs follow naming conventions

---

## 📚 Examples

See complete implementations in:
- `services/analysis-service/presentation/api/standard/`
- `services/doc-store/presentation/api/standard/`

---

**Document Control**  
**Version**: 1.0.0  
**Last Updated**: October 9, 2025  
**Next Review**: 2025-11-09  
**Owner**: Hackathon Team

