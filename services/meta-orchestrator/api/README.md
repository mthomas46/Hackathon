# Meta-Orchestrator API Layer

The REST API layer provides the primary interface for interacting with the Meta-Orchestration Service, built with FastAPI for high performance and automatic OpenAPI documentation generation.

## 📋 Overview

This directory contains all the REST API endpoints, request/response models, and routing logic for the Meta-Orchestrator service.

## 📁 Structure

```
api/
├── __init__.py          # API package initialization
└── routes.py           # All API endpoint definitions
```

## 🚀 Key Components

### Routes Module (`routes.py`)

The `routes.py` file contains all API endpoints organized by functional areas:

#### Service Management Endpoints
- `GET /api/v1/services` - List all services with status
- `GET /api/v1/services/{service_name}` - Get detailed service information
- `POST /api/v1/services/{service_name}/start` - Start a specific service
- `POST /api/v1/services/{service_name}/stop` - Stop a specific service
- `POST /api/v1/services/{service_name}/restart` - Restart a specific service
- `GET /api/v1/services/{service_name}/logs` - Retrieve service logs

#### Ecosystem Management Endpoints
- `POST /api/v1/ecosystem/start` - Start all services in the ecosystem
- `GET /api/v1/ecosystem/status` - Get overall ecosystem health status

#### Configuration Management Endpoints
- `GET /api/v1/monitoring/config/port-conflicts` - Detect port conflicts
- `POST /api/v1/monitoring/config/resolve-port-conflicts` - Resolve conflicts
- `GET /api/v1/monitoring/config/inconsistencies` - Find config issues
- `POST /api/v1/monitoring/config/resolve-inconsistencies` - Fix issues
- `POST /api/v1/monitoring/config/sync` - Sync configurations
- `GET /api/v1/monitoring/config/{service_name}` - Get service config
- `GET /api/v1/monitoring/config/{service_name}/export` - Export config
- `GET /api/v1/monitoring/config/{service_name}/compare` - Compare configs
- `GET /api/v1/monitoring/config/{service_name}/history` - Config history

#### Monitoring Endpoints
- `GET /api/v1/monitoring/health` - Service health status
- `GET /api/v1/monitoring/drift` - Configuration drift detection
- `GET /api/v1/monitoring/alerts` - Active alerts
- `POST /api/v1/monitoring/alerts/{alert_id}/acknowledge` - Acknowledge alerts
- `GET /api/v1/monitoring/analytics` - System analytics

#### Audit & Validation Endpoints
- `POST /api/v1/audit/docker-compose/validate` - Validate compose files
- `POST /api/v1/audit/config/drift-detect` - Detect configuration drift
- `POST /api/v1/audit/production-readiness/validate` - Production readiness
- `POST /api/v1/audit/config/standardize/service/{service_name}` - Standardize service
- `POST /api/v1/audit/config/standardize/all` - Standardize all services
- `POST /api/v1/audit/docker/standardize` - Standardize Docker configs

## 🔧 API Design Patterns

### Consistent Response Format

All endpoints follow a consistent response structure:

```python
# Success Response
{
    "status": "success",
    "data": {...},  # Endpoint-specific data
    "timestamp": "2024-01-15T10:30:00Z"
}

# Error Response
{
    "detail": "Error description",
    "status_code": 400
}
```

### Error Handling

The API implements comprehensive error handling:

- **Validation Errors** (422): Input validation failures
- **Not Found** (404): Resources that don't exist
- **Forbidden** (403): Authorization failures
- **Service Unavailable** (503): Orchestrator not initialized
- **Internal Server Error** (500): Unexpected errors

### Authentication & Authorization

```python
# API Key Authentication
headers = {"X-API-Key": "your-api-key"}

# Rate Limiting
# - 100 requests/minute for authenticated users
# - 10 requests/minute for anonymous users
# - Special limits for service operations
```

## 📊 Request/Response Models

### Pydantic Models

All request/response data is validated using Pydantic models:

```python
from pydantic import BaseModel, Field
from typing import Optional, List

class ServiceInfo(BaseModel):
    name: str = Field(..., description="Service name")
    status: str = Field(..., description="Current status")
    image: str = Field(..., description="Docker image")
    ports: List[str] = Field(default_factory=list, description="Port mappings")

class ServiceListResponse(BaseModel):
    services: List[ServiceInfo]
    total_count: int
    timestamp: datetime
```

## 🔄 Async Operations

All endpoints are async by default for high performance:

```python
@app.get("/services")
async def list_services() -> ServiceListResponse:
    """List all services asynchronously"""
    services = await orchestrator.get_services()
    return ServiceListResponse(services=services)
```

## 📋 OpenAPI Documentation

The API automatically generates comprehensive OpenAPI/Swagger documentation:

- **Interactive Documentation**: `http://localhost:8080/docs`
- **OpenAPI Schema**: `http://localhost:8080/openapi.json`
- **Alternative UI**: `http://localhost:8080/redoc`

## 🧪 Testing

### Unit Tests for API Endpoints

```python
import pytest
from fastapi.testclient import TestClient
from main import app

def test_list_services():
    client = TestClient(app)
    response = client.get("/api/v1/services")
    assert response.status_code == 200
    data = response.json()
    assert "services" in data

def test_service_not_found():
    client = TestClient(app)
    response = client.get("/api/v1/services/nonexistent")
    assert response.status_code == 404
```

### Integration Tests

```python
async def test_service_lifecycle(client, orchestrator_mock):
    # Start service
    response = client.post("/api/v1/services/test-service/start")
    assert response.status_code == 200

    # Check status
    response = client.get("/api/v1/services/test-service")
    assert response.status_code == 200
    assert response.json()["status"] == "running"
```

## 🔒 Security Features

### Input Validation
- All inputs validated with Pydantic models
- SQL injection prevention
- XSS protection
- Path traversal protection

### Rate Limiting
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimited, _rate_limit_exceeded_handler)
```

### CORS Configuration
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://your-domain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

## 📈 Performance Optimization

### Response Caching
```python
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis.asyncio import Redis

# Redis caching for frequently accessed data
redis = Redis.from_url("redis://localhost:6379")
FastAPICache.init(RedisBackend(redis), prefix="meta-orchestrator")
```

### Database Connection Pooling
```python
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Async database connections
engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/db")
async_session = sessionmaker(engine, class_=AsyncSession)
```

### Background Task Processing
```python
from fastapi import BackgroundTasks

@app.post("/services/{service_name}/restart")
async def restart_service(service_name: str, background_tasks: BackgroundTasks):
    # Immediate response
    background_tasks.add_task(orchestrator.restart_service, service_name)
    return {"message": "Restart initiated", "status": "accepted"}
```

## 🚨 Error Monitoring

### Structured Logging
```python
import structlog

logger = structlog.get_logger()

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(
        "Unhandled exception",
        exc_info=exc,
        path=request.url.path,
        method=request.method,
        user_agent=request.headers.get("user-agent")
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )
```

## 📚 Usage Examples

### Python Client
```python
import httpx

async def get_services():
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8080/api/v1/services",
            headers={"X-API-Key": "your-key"}
        )
        return response.json()
```

### cURL Examples
```bash
# List services
curl -H "X-API-Key: your-key" http://localhost:8080/api/v1/services

# Start service
curl -X POST -H "X-API-Key: your-key" \
     http://localhost:8080/api/v1/services/web-frontend/start

# Get service logs
curl -H "X-API-Key: your-key" \
     "http://localhost:8080/api/v1/services/web-frontend/logs?lines=100"
```

This API layer provides a robust, scalable, and well-documented interface for managing the entire Hackathon ecosystem through a single, unified REST API.
