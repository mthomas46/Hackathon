# 🔄 API Versioning Strategy for Zero-Downtime Refactoring

**Version**: 1.0.0  
**Created**: October 8, 2025  
**Status**: Active

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Versioning Strategy](#versioning-strategy)
3. [Migration Approach](#migration-approach)
4. [Implementation Guide](#implementation-guide)
5. [Testing Strategy](#testing-strategy)
6. [Deprecation Process](#deprecation-process)
7. [Examples](#examples)

---

## 🎯 Overview

### Purpose

This document defines the API versioning strategy to enable **zero-downtime, no-breaking-change refactoring** of all services in the ecosystem. By using `/v2/` versioned endpoints during refactoring, we can:

- **Deploy incrementally** without breaking existing clients
- **Test thoroughly** with both old and new implementations running
- **Migrate gracefully** at our own pace
- **Roll back safely** if issues are discovered
- **Maintain compatibility** during the entire refactoring process

### Key Principles

1. **No Breaking Changes**: Existing `/v1/` or unversioned endpoints continue to work
2. **Parallel Deployment**: Old and new versions run side-by-side
3. **Gradual Migration**: Clients migrate to `/v2/` when ready
4. **Comprehensive Testing**: Both versions tested continuously
5. **Clear Deprecation**: Transparent timeline for `/v1/` sunset

---

## 🏗️ Versioning Strategy

### URL Path Versioning

**Format**: `/api/v{version}/{resource}`

**Examples**:
```
# Old (v1 or unversioned)
GET /documents/{id}
GET /api/v1/documents/{id}

# New (v2 - refactored with DDD)
GET /api/v2/documents/{id}
```

**Why Path Versioning?**
- ✅ Clear and visible
- ✅ Easy to route
- ✅ Simple to test
- ✅ Well understood by developers
- ✅ Works with all HTTP clients

### Version Lifecycle

```
Phase 1: Legacy (v1/unversioned)
├── Current production API
└── Status: Active, no changes

Phase 2: Development (v2 in parallel)
├── New DDD implementation
├── v1 continues to work
├── v2 under development
└── Status: Both active, testing v2

Phase 3: Migration (dual support)
├── v2 ready for production
├── v1 still supported
├── Clients gradually migrate
└── Status: Both active, v2 recommended

Phase 4: Deprecation (v1 marked deprecated)
├── v2 is primary
├── v1 marked deprecated with sunset date
├── Warning headers on v1 responses
└── Status: v2 active, v1 deprecated

Phase 5: Sunset (v1 removed)
├── v2 is only version
├── v1 endpoints return 410 Gone
└── Status: v2 active, v1 removed
```

### Version Support Timeline

| Phase | v1 | v2 | Duration | Notes |
|-------|----|----|----------|-------|
| Development | ✅ Active | 🚧 Building | Varies | v2 development |
| Testing | ✅ Active | 🧪 Testing | 2-4 weeks | Integration testing |
| Migration | ✅ Active | ✅ Active | 2-3 months | Gradual migration |
| Deprecation | ⚠️ Deprecated | ✅ Active | 3-6 months | With warnings |
| Sunset | ❌ Removed | ✅ Active | N/A | v1 gone |

---

## 🔄 Migration Approach

### Per-Service Migration Strategy

Each service refactoring follows this pattern:

```
1. Analyze Current API
   ├── Document all existing endpoints
   ├── Identify consumers/clients
   ├── Map data contracts
   └── Note any quirks or workarounds

2. Design v2 API
   ├── Apply REST standards
   ├── Implement DDD principles
   ├── Improve naming and structure
   └── Add comprehensive OpenAPI docs

3. Implement v2 (parallel to v1)
   ├── New DDD implementation
   ├── New endpoints at /api/v2/*
   ├── v1 endpoints unchanged
   └── Both versions active

4. Test Both Versions
   ├── Unit tests for v2
   ├── Integration tests for v2
   ├── Regression tests for v1
   └── Workflow tests for both

5. Deploy with Feature Flag
   ├── v2 behind feature flag initially
   ├── Gradually enable for testing
   ├── Monitor metrics
   └── Full rollout when stable

6. Migrate Clients
   ├── Update internal services first
   ├── Provide migration guide
   ├── Monitor adoption
   └── Support during transition

7. Deprecate v1
   ├── Add deprecation warnings
   ├── Set sunset date (6 months out)
   ├── Communication to stakeholders
   └── Monitor v1 usage decline

8. Remove v1
   ├── Final warning period (1 month)
   ├── Switch v1 to 410 Gone
   ├── Keep redirect to v2 (optional)
   └── Clean up old code
```

### Backward Compatibility Layer

For services with many consumers, create a compatibility adapter:

```python
# Legacy v1 endpoint (adapter pattern)
@router.get("/documents/{id}")
async def get_document_v1(id: str):
    """
    Legacy endpoint - redirects to v2 internally
    Deprecated: Use /api/v2/documents/{id}
    Sunset: 2026-04-01
    """
    # Add deprecation warning
    response = await get_document_v2(id)
    response.headers["X-API-Deprecation"] = "true"
    response.headers["X-API-Sunset-Date"] = "2026-04-01"
    response.headers["X-API-Upgrade-Path"] = f"/api/v2/documents/{id}"
    
    # Transform v2 response to v1 format if needed
    v1_data = adapt_v2_to_v1(response.data)
    return v1_data

# New v2 endpoint (DDD implementation)
@router.get("/api/v2/documents/{id}")
async def get_document_v2(id: str):
    """
    Get document by ID
    
    Uses new DDD architecture with proper domain modeling.
    """
    # New implementation
    pass
```

---

## 💻 Implementation Guide

### Step 1: Define v2 API Specification

**Create OpenAPI spec for v2:**

```yaml
# openapi_v2.yaml
openapi: 3.0.3
info:
  title: Document Service API
  version: 2.0.0
  description: |
    Refactored API with DDD architecture.
    
    Breaking changes from v1:
    - Resource names now plural
    - Consistent error format
    - Better field naming
    - Pagination standardized

servers:
  - url: http://localhost:5087/api/v2
    description: Development

paths:
  /documents:
    get:
      summary: List documents
      description: Get paginated list of documents
      parameters:
        - name: limit
          in: query
          schema:
            type: integer
            default: 10
        - name: offset
          in: query
          schema:
            type: integer
            default: 0
      responses:
        '200':
          description: Success
          content:
            application/json:
              schema:
                type: object
                properties:
                  data:
                    type: array
                    items:
                      $ref: '#/components/schemas/Document'
                  meta:
                    $ref: '#/components/schemas/PaginationMeta'
```

### Step 2: Implement v2 with DDD

**Directory structure:**

```
services/doc_store/
├── domain/
│   ├── entities/
│   │   └── document.py
│   ├── repositories/
│   │   └── document_repository.py  # Interface
│   └── value_objects/
│       └── document_id.py
├── application/
│   ├── commands/
│   │   └── create_document.py
│   └── queries/
│       └── get_document.py
├── infrastructure/
│   └── repositories/
│       └── sqlite_document_repository.py
├── presentation/
│   ├── api/
│   │   ├── v1/                    # Old implementation
│   │   │   └── routes.py          # Legacy endpoints
│   │   └── v2/                    # New implementation
│   │       ├── routes.py          # DDD-based endpoints
│   │       └── schemas.py         # Pydantic models
│   └── middleware/
│       └── version_router.py      # Routes to correct version
└── main.py
```

### Step 3: Create Version Router

**Automatic routing to correct version:**

```python
# presentation/middleware/version_router.py

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

def create_version_router():
    """
    Creates a router that handles version routing automatically
    """
    router = APIRouter()
    
    # Mount v1 (legacy)
    from ..api.v1 import routes as v1_routes
    router.include_router(
        v1_routes.router,
        tags=["v1 (deprecated)"]
    )
    
    # Mount v2 (new DDD)
    from ..api.v2 import routes as v2_routes
    router.include_router(
        v2_routes.router,
        prefix="/api/v2",
        tags=["v2"]
    )
    
    return router

# main.py
from fastapi import FastAPI
from presentation.middleware.version_router import create_version_router

app = FastAPI(
    title="Document Service",
    version="2.0.0",
    description="DDD-based document service with v1/v2 support"
)

# Add version router
app.include_router(create_version_router())

# Add deprecation middleware
@app.middleware("http")
async def add_deprecation_headers(request: Request, call_next):
    response = await call_next(request)
    
    # Add deprecation warning for v1 endpoints
    if not request.url.path.startswith("/api/v2"):
        response.headers["X-API-Deprecation"] = "true"
        response.headers["X-API-Sunset-Date"] = "2026-04-01"
        response.headers["X-API-Upgrade-Path"] = request.url.path.replace("/api/v1", "/api/v2")
        response.headers["Warning"] = '299 - "API v1 is deprecated. Migrate to v2."'
    
    return response
```

### Step 4: Implement Feature Flags

**Control v2 rollout:**

```python
# infrastructure/config/feature_flags.py

from typing import Dict
import os

class FeatureFlags:
    """Feature flags for gradual rollout"""
    
    def __init__(self):
        self.flags = {
            "v2_enabled": os.getenv("V2_ENABLED", "false").lower() == "true",
            "v2_percentage": int(os.getenv("V2_ROLLOUT_PERCENTAGE", "0")),
            "v2_allowed_clients": os.getenv("V2_ALLOWED_CLIENTS", "").split(","),
        }
    
    def is_v2_enabled(self, client_id: str = None) -> bool:
        """Check if v2 is enabled for this client"""
        if not self.flags["v2_enabled"]:
            return False
        
        # Specific clients can be allow-listed
        if client_id and client_id in self.flags["v2_allowed_clients"]:
            return True
        
        # Percentage-based rollout
        if self.flags["v2_percentage"] >= 100:
            return True
        
        # Use consistent hashing for percentage rollout
        if client_id:
            hash_val = hash(client_id) % 100
            return hash_val < self.flags["v2_percentage"]
        
        return False

# Usage in middleware
feature_flags = FeatureFlags()

@app.middleware("http")
async def route_to_version(request: Request, call_next):
    client_id = request.headers.get("X-Client-ID")
    
    # If v2 not enabled, use v1
    if not feature_flags.is_v2_enabled(client_id):
        if request.url.path.startswith("/api/v2"):
            return JSONResponse(
                status_code=503,
                content={"error": "v2 API not yet available for your client"}
            )
    
    return await call_next(request)
```

---

## 🧪 Testing Strategy

### Dual Testing Approach

**Test both versions in parallel:**

```python
# tests/integration/test_document_api_versions.py

import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
class TestDocumentAPIVersions:
    """Test both v1 and v2 APIs for compatibility"""
    
    async def test_v1_and_v2_return_same_data(self, client: AsyncClient):
        """Ensure v2 returns same data as v1 (backward compatible)"""
        # Create document via v2
        v2_response = await client.post(
            "/api/v2/documents",
            json={"title": "Test", "content": "Content"}
        )
        assert v2_response.status_code == 201
        doc_id = v2_response.json()["data"]["id"]
        
        # Get via v1
        v1_response = await client.get(f"/documents/{doc_id}")
        assert v1_response.status_code == 200
        v1_data = v1_response.json()
        
        # Get via v2
        v2_response = await client.get(f"/api/v2/documents/{doc_id}")
        assert v2_response.status_code == 200
        v2_data = v2_response.json()["data"]
        
        # Compare essential fields
        assert v1_data["id"] == v2_data["id"]
        assert v1_data["title"] == v2_data["title"]
        assert v1_data["content"] == v2_data["content"]
    
    async def test_v1_has_deprecation_headers(self, client: AsyncClient):
        """Ensure v1 responses include deprecation warnings"""
        response = await client.get("/documents")
        
        assert "X-API-Deprecation" in response.headers
        assert response.headers["X-API-Deprecation"] == "true"
        assert "X-API-Sunset-Date" in response.headers
        assert "X-API-Upgrade-Path" in response.headers
    
    async def test_v2_follows_standard_format(self, client: AsyncClient):
        """Ensure v2 follows new standard response format"""
        response = await client.get("/api/v2/documents")
        assert response.status_code == 200
        
        data = response.json()
        # v2 uses envelope format
        assert "data" in data
        assert "meta" in data
        assert "pagination" in data["meta"]
    
    async def test_v1_still_works_when_v2_fails(self, client: AsyncClient):
        """Ensure v1 is independent of v2 failures"""
        # This tests isolation between versions
        pass
```

### Workflow Testing

**Test complete workflows through both versions:**

```python
# tests/workflows/test_document_workflow.py

import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
class TestDocumentWorkflow:
    """Test complete document workflow through API versions"""
    
    async def test_create_analyze_retrieve_workflow_v2(self, client: AsyncClient):
        """
        Test: Create doc → Analyze → Retrieve results
        Version: v2
        Services: doc-store, analysis-service
        """
        # Step 1: Create document (doc-store v2)
        create_response = await client.post(
            "/api/v2/documents",
            json={
                "title": "Analysis Test Document",
                "content": "This is test content for analysis."
            }
        )
        assert create_response.status_code == 201
        doc_id = create_response.json()["data"]["id"]
        
        # Step 2: Trigger analysis (analysis-service v2)
        analysis_response = await client.post(
            "http://analysis-service:5020/api/v2/analyze",
            json={
                "targets": [doc_id],
                "analysis_types": ["quality", "semantic"]
            }
        )
        assert analysis_response.status_code == 200
        analysis_id = analysis_response.json()["data"]["id"]
        
        # Step 3: Wait for analysis completion
        import asyncio
        await asyncio.sleep(2)
        
        # Step 4: Retrieve analysis results
        results_response = await client.get(
            f"http://analysis-service:5020/api/v2/analyses/{analysis_id}"
        )
        assert results_response.status_code == 200
        results = results_response.json()["data"]
        
        assert results["status"] == "completed"
        assert "quality" in results["results"]
        assert "semantic" in results["results"]
        
        # Step 5: Retrieve document with analysis metadata
        doc_response = await client.get(
            f"/api/v2/documents/{doc_id}?include=analyses"
        )
        assert doc_response.status_code == 200
        doc_data = doc_response.json()["data"]
        
        assert len(doc_data["analyses"]) > 0
        assert doc_data["analyses"][0]["id"] == analysis_id
    
    async def test_cross_version_compatibility(self, client: AsyncClient):
        """
        Test: v1 doc-store → v2 analysis → v1 retrieval
        Ensures versions can interoperate
        """
        # Create via v1
        create_response = await client.post(
            "/documents",
            json={"title": "Test", "content": "Content"}
        )
        doc_id = create_response.json()["id"]
        
        # Analyze via v2
        analysis_response = await client.post(
            "http://analysis-service:5020/api/v2/analyze",
            json={"targets": [doc_id]}
        )
        assert analysis_response.status_code == 200
        
        # Retrieve via v1
        doc_response = await client.get(f"/documents/{doc_id}")
        assert doc_response.status_code == 200
```

---

## 📉 Deprecation Process

### Deprecation Timeline

**Standard deprecation period: 6 months**

```
Month 1-2: Announcement
├── Communication to all stakeholders
├── Migration guide published
├── v2 marked as stable
└── Deprecation warnings added to v1

Month 3-4: Active Migration
├── Support teams help clients migrate
├── Track migration progress
├── Address migration blockers
└── Monitor v1 usage decline

Month 5-6: Final Push
├── Sunset date announced
├── Final warnings sent
├── Last chance for migration
└── Prepare for v1 removal

Month 7: Sunset
├── v1 returns 410 Gone
├── Optional redirect to v2
├── Monitor for issues
└── Clean up v1 code
```

### Deprecation Headers

**Standard headers for deprecated endpoints:**

```
X-API-Deprecation: true
X-API-Sunset-Date: 2026-04-01
X-API-Upgrade-Path: /api/v2/documents/{id}
Warning: 299 - "API v1 is deprecated. Migrate to v2 by 2026-04-01"
Link: </api/v2/documents/{id}>; rel="successor-version"
```

### Sunset Response

**After sunset date:**

```json
HTTP/1.1 410 Gone
Content-Type: application/json

{
  "error": {
    "code": "API_VERSION_SUNSET",
    "message": "API v1 has been sunset. Please use v2.",
    "sunset_date": "2026-04-01",
    "upgrade_path": "/api/v2/documents/{id}",
    "documentation": "https://docs.example.com/migration-guide",
    "support": "support@example.com"
  }
}
```

---

## 📚 Examples

### Example 1: Simple Service Refactor

**Service**: `notification-service`  
**Complexity**: Low (few dependencies)

**v1 Endpoint** (legacy):
```python
@app.post("/notify")
async def send_notification(request: NotificationRequest):
    # Legacy implementation
    pass
```

**v2 Endpoint** (DDD):
```python
@router.post("/api/v2/notifications")
async def create_notification(
    command: CreateNotificationCommand,
    service: NotificationApplicationService = Depends()
):
    """
    Send a notification using DDD architecture
    
    - Uses command pattern
    - Proper domain modeling
    - Event sourcing for audit trail
    """
    result = await service.create_notification(command)
    return {"data": result, "meta": {"version": "2.0"}}
```

### Example 2: Complex Service with Many Consumers

**Service**: `doc-store`  
**Complexity**: High (15+ dependent services)

**Strategy**:
1. Create v2 with adapter for v1 compatibility
2. Gradual rollout with feature flags
3. Long deprecation period (9 months)

**Adapter Pattern**:
```python
# v1/routes.py (adapter to v2)
from ..v2.routes import DocumentController

v1_router = APIRouter()
v2_controller = DocumentController()

@v1_router.get("/documents/{id}")
async def get_document_v1(id: str):
    """Legacy endpoint - uses v2 internally"""
    # Use v2 implementation
    result = await v2_controller.get_document_v2(id)
    
    # Transform to v1 format
    v1_format = {
        "id": result["data"]["id"],
        "title": result["data"]["title"],
        # ... other v1 fields
    }
    
    return v1_format
```

### Example 3: Breaking Change Managed

**Scenario**: Changing document ID format from integer to UUID

**v1**: `GET /documents/123` (integer ID)  
**v2**: `GET /api/v2/documents/550e8400-e29b-41d4-a716-446655440000` (UUID)

**Solution**: Adapter that supports both:

```python
from uuid import UUID
from typing import Union

@router.get("/api/v2/documents/{id}")
async def get_document(id: str):
    # Try to parse as UUID
    try:
        document_id = UUID(id)
    except ValueError:
        # If not UUID, try as legacy integer ID
        try:
            legacy_id = int(id)
            # Look up UUID by legacy ID
            document_id = await get_uuid_from_legacy_id(legacy_id)
        except ValueError:
            raise HTTPException(400, "Invalid document ID format")
    
    # Use UUID in new implementation
    return await document_service.get_by_id(document_id)
```

---

## ✅ Checklist

### For Each Service Refactor

**Planning Phase**:
- [ ] Document all v1 endpoints
- [ ] Identify all consumers
- [ ] Design v2 API specification
- [ ] Plan migration strategy
- [ ] Set deprecation timeline

**Implementation Phase**:
- [ ] Implement v2 with DDD
- [ ] Create version router
- [ ] Add feature flags
- [ ] Implement backward compatibility
- [ ] Add deprecation headers

**Testing Phase**:
- [ ] Unit tests for v2
- [ ] Integration tests for both versions
- [ ] Workflow tests across versions
- [ ] Performance tests
- [ ] Backward compatibility tests

**Deployment Phase**:
- [ ] Deploy with v1 and v2 active
- [ ] Gradual rollout with feature flags
- [ ] Monitor metrics
- [ ] Address issues

**Migration Phase**:
- [ ] Publish migration guide
- [ ] Update internal services
- [ ] Support external clients
- [ ] Track migration progress

**Deprecation Phase**:
- [ ] Add deprecation warnings
- [ ] Communicate sunset date
- [ ] Monitor v1 usage
- [ ] Prepare for removal

**Sunset Phase**:
- [ ] Switch v1 to 410 Gone
- [ ] Monitor for issues
- [ ] Clean up v1 code
- [ ] Update documentation

---

## 📊 Monitoring

### Key Metrics to Track

```
API Version Usage:
├── v1 request count (declining)
├── v2 request count (growing)
├── Error rates per version
└── Response times per version

Migration Progress:
├── % of clients on v2
├── v1 usage by client
├── Migration blockers
└── Support tickets

Performance:
├── v1 vs v2 latency
├── Resource usage
├── Error rates
└── Success rates
```

---

**Document Control**  
**Version**: 1.0.0  
**Last Updated**: October 8, 2025  
**Next Review**: 2025-11-08  
**Owner**: Hackathon Team

