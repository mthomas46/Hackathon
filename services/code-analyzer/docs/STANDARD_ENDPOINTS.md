# Standard API Endpoints - code-analyzer

**Service**: code-analyzer  
**Version**: 1.0.0  
**Status**: Documentation Complete, Implementation Pending

---

## 📋 Overview

This document defines the four standard endpoints that all services in the ecosystem must implement. These endpoints provide consistent service discovery, health checking, and relationship mapping across the microservices architecture.

**Current Status**: ⏸️ **Documentation complete, implementation pending**

These endpoints should be implemented in the application/presentation layer (future work).

---

## 🔗 Standard Endpoints

### 1. `/health` - Health Check

**Purpose**: Check if the service is healthy and operational

**Method**: `GET`  
**Path**: `/health`  
**Authentication**: None required

**Response**: `200 OK`
```json
{
  "status": "healthy",
  "service": "code-analyzer",
  "version": "1.0.0",
  "timestamp": "2025-10-09T18:00:00Z",
  "uptime_seconds": 3600,
  "checks": {
    "domain_layer": "ok",
    "memory": "ok",
    "disk": "ok"
  }
}
```

**Response**: `503 Service Unavailable` (if unhealthy)
```json
{
  "status": "unhealthy",
  "service": "code-analyzer",
  "version": "1.0.0",
  "timestamp": "2025-10-09T18:00:00Z",
  "checks": {
    "domain_layer": "ok",
    "memory": "critical",
    "disk": "ok"
  },
  "errors": [
    "Memory usage above 90% threshold"
  ]
}
```

**Usage**:
```bash
curl http://localhost:6000/health
```

**Docker Integration**:
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:6000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
```

---

### 2. `/about-me` - Service Descriptor

**Purpose**: Describe the service capabilities and metadata

**Method**: `GET`  
**Path**: `/about-me`  
**Authentication**: None required

**Response**: `200 OK`
```json
{
  "service": "code-analyzer",
  "version": "1.0.0",
  "description": "Static code analysis service providing structure extraction, complexity analysis, security scanning, and style checking for Python code",
  "capabilities": [
    "structure_extraction",
    "complexity_analysis",
    "security_scanning",
    "style_checking"
  ],
  "features": {
    "languages": ["python"],
    "analysis_types": [
      "cyclomatic_complexity",
      "cognitive_complexity",
      "maintainability_index",
      "halstead_metrics"
    ],
    "security_checks": [
      "code_injection",
      "unsafe_deserialization",
      "sql_injection_patterns"
    ]
  },
  "ecosystem_role": "analysis",
  "tier": "Tier 3 - Analysis Services",
  "dependencies": {
    "external": [],
    "internal": []
  },
  "provides_to_ecosystem": [
    "Code structure analysis",
    "Complexity metrics",
    "Security vulnerability detection",
    "Code quality assessment"
  ],
  "architecture": {
    "pattern": "DDD (Domain-Driven Design)",
    "layers": ["domain", "application", "infrastructure", "presentation"],
    "aggregates": ["CodeAnalysis"],
    "value_objects": [
      "Language",
      "AnalysisStatus",
      "ComplexityMetrics",
      "Severity",
      "StyleIssue",
      "SecurityFinding"
    ]
  },
  "quality_metrics": {
    "test_coverage": "96.4%",
    "total_tests": 84,
    "code_quality": "A+"
  },
  "documentation": {
    "readme": "/README.md",
    "openapi": "/docs",
    "config": "/CONFIG.md"
  },
  "maintainer": "Hackathon Team",
  "repository": "https://github.com/hackathon/services/tree/main/code-analyzer",
  "license": "MIT"
}
```

**Usage**:
```bash
curl http://localhost:6000/about-me | jq
```

---

### 3. `/endpoints` - API Endpoint List

**Purpose**: List all available API endpoints

**Method**: `GET`  
**Path**: `/endpoints`  
**Authentication**: None required

**Response**: `200 OK`
```json
{
  "service": "code-analyzer",
  "version": "1.0.0",
  "base_url": "http://localhost:6000",
  "endpoints": [
    {
      "path": "/health",
      "methods": ["GET"],
      "description": "Health check endpoint",
      "authentication": false,
      "category": "standard"
    },
    {
      "path": "/about-me",
      "methods": ["GET"],
      "description": "Service descriptor",
      "authentication": false,
      "category": "standard"
    },
    {
      "path": "/endpoints",
      "methods": ["GET"],
      "description": "List all endpoints",
      "authentication": false,
      "category": "standard"
    },
    {
      "path": "/provider-consumer",
      "methods": ["GET"],
      "description": "Service relationships",
      "authentication": false,
      "category": "standard"
    },
    {
      "path": "/analyze",
      "methods": ["POST"],
      "description": "Analyze code (primary endpoint)",
      "authentication": false,
      "category": "core",
      "request_body": {
        "code": "string (required)",
        "language": "string (required, e.g., 'python')",
        "options": "object (optional)"
      },
      "response": {
        "analysis_id": "string",
        "status": "string",
        "results": "object"
      }
    },
    {
      "path": "/analyze/batch",
      "methods": ["POST"],
      "description": "Batch analyze multiple code samples",
      "authentication": false,
      "category": "core"
    },
    {
      "path": "/docs",
      "methods": ["GET"],
      "description": "OpenAPI/Swagger documentation",
      "authentication": false,
      "category": "documentation"
    }
  ],
  "total_endpoints": 8,
  "categories": {
    "standard": 4,
    "core": 2,
    "documentation": 2
  }
}
```

**Usage**:
```bash
curl http://localhost:6000/endpoints | jq
```

---

### 4. `/provider-consumer` - Service Relationships

**Purpose**: Document service dependencies and relationships

**Method**: `GET`  
**Path**: `/provider-consumer`  
**Authentication**: None required

**Response**: `200 OK`
```json
{
  "service": "code-analyzer",
  "version": "1.0.0",
  "relationships": {
    "providers": [],
    "consumers": [
      {
        "service": "analysis-service",
        "relationship": "consumer",
        "description": "Uses code-analyzer for code quality analysis in CI/CD pipelines",
        "endpoints_used": ["/analyze", "/analyze/batch"],
        "data_provided": [
          "complexity_metrics",
          "security_findings",
          "style_issues"
        ]
      },
      {
        "service": "orchestrator",
        "relationship": "consumer",
        "description": "Orchestrates code analysis workflows",
        "endpoints_used": ["/analyze", "/health"],
        "data_provided": ["analysis_results"]
      }
    ],
    "provide_consume": []
  },
  "dependencies": {
    "external_apis": [],
    "databases": [],
    "message_queues": [],
    "cache_systems": []
  },
  "provides_data_to": [
    "analysis-service",
    "orchestrator",
    "frontend",
    "cli"
  ],
  "consumes_data_from": [],
  "self_contained": true,
  "notes": "code-analyzer is a self-contained service with no external dependencies. It processes code strings provided via API calls and returns analysis results."
}
```

**Usage**:
```bash
curl http://localhost:6000/provider-consumer | jq
```

---

## 🔧 Implementation Guide

### Implementation Priority

1. **Phase 1 (Required)**: `/health`
   - Essential for Docker health checks
   - Required for deployment
   - Simple to implement

2. **Phase 1 (Required)**: `/about-me`
   - Provides service discovery
   - Documents capabilities
   - Moderate complexity

3. **Phase 2 (Recommended)**: `/endpoints`
   - API documentation
   - Developer experience
   - Can be auto-generated from routes

4. **Phase 2 (Recommended)**: `/provider-consumer`
   - Ecosystem mapping
   - Dependency visualization
   - Static configuration

### Technology Stack

**Recommended**: FastAPI (Python)

```python
# Example implementation structure
from fastapi import FastAPI

app = FastAPI(title="code-analyzer", version="1.0.0")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "code-analyzer",
        "version": "1.0.0"
    }

@app.get("/about-me")
async def about_me():
    """Service descriptor."""
    return {
        "service": "code-analyzer",
        "description": "...",
        # ... rest of response
    }

@app.get("/endpoints")
async def list_endpoints():
    """List all endpoints."""
    # Can auto-generate from app.routes
    return {"endpoints": [...]}

@app.get("/provider-consumer")
async def provider_consumer():
    """Service relationships."""
    return {"relationships": {...}}
```

### Testing

```python
# Example test structure
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    """Test health endpoint returns 200."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

@pytest.mark.asyncio
async def test_about_me_endpoint(client: AsyncClient):
    """Test about-me endpoint returns service info."""
    response = await client.get("/about-me")
    assert response.status_code == 200
    assert response.json()["service"] == "code-analyzer"

# ... more tests
```

### Docker Health Check

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:6000/health || exit 1
```

---

## 📊 Current Status

| Endpoint | Documentation | Implementation | Tests | Status |
|----------|---------------|----------------|-------|--------|
| `/health` | ✅ Complete | ⏸️ Pending | ⏸️ Pending | 33% |
| `/about-me` | ✅ Complete | ⏸️ Pending | ⏸️ Pending | 33% |
| `/endpoints` | ✅ Complete | ⏸️ Pending | ⏸️ Pending | 33% |
| `/provider-consumer` | ✅ Complete | ⏸️ Pending | ⏸️ Pending | 33% |

**Overall Standard Endpoints Progress**: 33% (Documentation only)

---

## 🎯 Next Steps

### Phase 6 (Deployment) Prerequisites

Before deployment, implement:
1. `/health` endpoint (required for Docker health checks)
2. Docker configuration
3. Health check tests

### Phase 7 (Enhancement) Recommendations

For full ecosystem integration:
1. Implement all 4 standard endpoints
2. Add comprehensive endpoint tests
3. Create API client examples
4. Add Swagger/OpenAPI UI

### Future Enhancements

- **Metrics**: Add `/metrics` endpoint for Prometheus
- **Debug**: Add `/debug` endpoint for troubleshooting (dev only)
- **Status**: Add `/status` endpoint for detailed status
- **Version**: Add `/version` endpoint for version info

---

## 📚 Related Documentation

- [Service README](../README.md) - Complete service documentation
- [CONFIG.md](../CONFIG.md) - Configuration guide
- [OpenAPI Specification](../design/openapi_v2.yaml) - API documentation
- [Master Configuration Registry](../../../docs/refactoring/MASTER_CONFIGURATION_REGISTRY.md) - Ecosystem config

---

**Status**: ✅ **Documentation Complete**  
**Next**: Implement in application/presentation layer  
**Priority**: `/health` is high priority for deployment

---

**Last Updated**: October 9, 2025  
**Maintained by**: Hackathon Team

