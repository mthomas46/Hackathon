# 🌐 Unified API Dashboard - API Guides

## Overview

The Unified API Dashboard provides comprehensive REST APIs for API discovery, testing, monitoring, analytics, and management across your entire API ecosystem.

## Authentication

All API endpoints require authentication using JWT tokens. Include the token in the `Authorization` header:

```
Authorization: Bearer <your-jwt-token>
```

### Login

**Endpoint:** `POST /api/auth/login`

**Request Body:**
```json
{
  "username": "your-username",
  "password": "your-password"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user_id": "user123",
    "username": "your-username",
    "role": "developer",
    "permissions": ["api_catalog:read", "analytics:read"],
    "expires_at": "2024-01-01T12:00:00Z"
  },
  "message": "Login successful",
  "timestamp": "2024-01-01T11:00:00Z"
}
```

### Token Refresh

**Endpoint:** `POST /api/auth/refresh`

**Headers:**
```
Authorization: Bearer <current-valid-token>
```

**Response:**
```json
{
  "success": true,
  "data": {
    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "expires_at": "2024-01-01T13:00:00Z"
  },
  "message": "Token refreshed successfully"
}
```

## API Discovery

### Get Discovered Services

**Endpoint:** `GET /api/discovery/services`

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "service_name": "user-service",
      "service_url": "http://user-service:8000",
      "health_endpoint": "/health",
      "last_discovered": "2024-01-01T10:00:00Z",
      "status": "healthy"
    }
  ]
}
```

### Trigger Discovery Scan

**Endpoint:** `POST /api/discovery/scan`

**Response:**
```json
{
  "success": true,
  "data": {
    "scan_id": "scan_123",
    "services_discovered": 15,
    "apis_found": 127
  },
  "message": "Discovery scan completed"
}
```

## API Catalog

### Get API Catalog

**Endpoint:** `GET /api/catalog/endpoints`

**Query Parameters:**
- `service` (optional): Filter by service name
- `search` (optional): Search in endpoint descriptions
- `limit` (optional): Maximum results (default: 50)
- `offset` (optional): Pagination offset (default: 0)

**Response:**
```json
{
  "success": true,
  "data": {
    "services": ["user-service", "auth-service"],
    "endpoints": [
      {
        "service": "user-service",
        "path": "/users",
        "method": "GET",
        "summary": "List users",
        "description": "Retrieve a paginated list of users"
      }
    ],
    "total": 25,
    "limit": 50,
    "offset": 0
  }
}
```

### Search APIs

**Endpoint:** `GET /api/catalog/search`

**Query Parameters:**
- `query`: Search term
- `service` (optional): Filter by service
- `method` (optional): Filter by HTTP method

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "service": "user-service",
      "endpoint": "/users/{id}",
      "method": "GET",
      "summary": "Get user by ID",
      "relevance_score": 0.95
    }
  ]
}
```

## API Testing

### Execute API Test

**Endpoint:** `POST /api/testing/execute`

**Request Body:**
```json
{
  "service_name": "user-service",
  "endpoint_path": "/users",
  "method": "GET",
  "headers": {
    "Authorization": "Bearer test-token"
  },
  "params": {
    "limit": 10,
    "offset": 0
  },
  "body": null
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "test_id": "test_123",
    "status": "completed",
    "request": {
      "url": "http://user-service:8000/users",
      "method": "GET",
      "headers": {"Authorization": "Bearer test-token"}
    },
    "response": {
      "status_code": 200,
      "headers": {"content-type": "application/json"},
      "body": {"users": [], "total": 0},
      "response_time": 145
    }
  }
}
```

### Get Test History

**Endpoint:** `GET /api/testing/history`

**Query Parameters:**
- `service` (optional): Filter by service
- `status` (optional): Filter by test status
- `limit` (optional): Maximum results (default: 50)

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "test_id": "test_123",
      "service": "user-service",
      "endpoint": "/users",
      "method": "GET",
      "status": "passed",
      "response_time": 145,
      "status_code": 200,
      "timestamp": "2024-01-01T10:30:00Z"
    }
  ]
}
```

## Analytics

### Usage Overview

**Endpoint:** `GET /api/analytics/usage/overview`

**Response:**
```json
{
  "success": true,
  "data": {
    "total_requests": 15420,
    "unique_users": 234,
    "services_used": 12,
    "peak_usage_hour": 14,
    "avg_requests_per_hour": 642,
    "top_endpoints": [
      {
        "endpoint": "/users",
        "service": "user-service",
        "requests": 2340,
        "avg_response_time": 145
      }
    ]
  }
}
```

### Performance Insights

**Endpoint:** `GET /api/analytics/performance/insights`

**Response:**
```json
{
  "success": true,
  "data": {
    "avg_response_time": 145,
    "p95_response_time": 320,
    "p99_response_time": 450,
    "error_rate": 0.023,
    "throughput_rps": 12.5,
    "bottlenecks": [
      {
        "service": "data-service",
        "endpoint": "/query",
        "avg_response_time": 890,
        "recommendation": "Consider adding database indexes"
      }
    ]
  }
}
```

### Error Analytics

**Endpoint:** `GET /api/analytics/errors/overview`

**Response:**
```json
{
  "success": true,
  "data": {
    "total_errors": 356,
    "error_rate": 0.023,
    "errors_by_type": {
      "validation_error": 145,
      "authentication_error": 89,
      "server_error": 67,
      "not_found": 55
    },
    "errors_by_service": {
      "user-service": 156,
      "auth-service": 89,
      "data-service": 111
    },
    "recent_errors": [
      {
        "timestamp": "2024-01-01T10:45:00Z",
        "service": "user-service",
        "endpoint": "/users/123",
        "error_type": "not_found",
        "message": "User not found",
        "status_code": 404
      }
    ]
  }
}
```

## Developer Tools

### Generate Client Code

**Endpoint:** `POST /api/tools/generate-client`

**Request Body:**
```json
{
  "service_name": "user-service",
  "language": "python"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "language": "python",
    "client_code": "class UserServiceClient:\n    def __init__(self, base_url):\n        self.base_url = base_url\n\n    def get_users(self):\n        # Generated method\n        pass\n\n    def create_user(self, user_data):\n        # Generated method\n        pass",
    "filename": "user_service_client.py"
  }
}
```

### Validate API Specification

**Endpoint:** `POST /api/tools/validate-spec`

**Request Body:**
```json
{
  "service_name": "user-service",
  "openapi_spec": {
    "openapi": "3.0.0",
    "info": {"title": "User Service", "version": "1.0.0"},
    "paths": {
      "/users": {
        "get": {
          "responses": {"200": {"description": "OK"}}
        }
      }
    }
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "valid": true,
    "errors": [],
    "warnings": [
      "Consider adding response schemas",
      "Add security definitions"
    ],
    "compliance_score": 85,
    "recommendations": [
      "Add detailed response schemas",
      "Include authentication requirements",
      "Add rate limiting information"
    ]
  }
}
```

### Run Integration Test

**Endpoint:** `POST /api/tools/run-integration-test`

**Request Body:**
```json
{
  "service_name": "user-service",
  "test_type": "functional",
  "config": {
    "concurrent_users": 5,
    "duration_seconds": 60,
    "endpoints": ["/users", "/users/123"]
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "test_suite_id": "suite_123",
    "status": "completed",
    "total_tests": 10,
    "passed_tests": 9,
    "failed_tests": 1,
    "execution_time": 65.2,
    "results": [
      {
        "endpoint": "/users",
        "method": "GET",
        "status": "passed",
        "response_time": 145,
        "status_code": 200
      }
    ]
  }
}
```

## Security & Audit

### Get Audit Events

**Endpoint:** `GET /api/audit/events`

**Query Parameters:**
- `user_id` (optional): Filter by user
- `event_type` (optional): Filter by event type
- `start_date` (optional): Start date (ISO format)
- `end_date` (optional): End date (ISO format)
- `limit` (optional): Maximum results (default: 100)

**Response:**
```json
{
  "success": true,
  "data": {
    "events": [
      {
        "event_id": "evt_123",
        "event_type": "api.access",
        "user_id": "user123",
        "username": "johndoe",
        "timestamp": "2024-01-01T10:30:00Z",
        "resource": "GET /api/users",
        "action": "access_granted",
        "details": {"ip_address": "192.168.1.100"}
      }
    ],
    "total": 1
  }
}
```

### Get Compliance Status

**Endpoint:** `GET /api/audit/compliance`

**Response:**
```json
{
  "success": true,
  "data": {
    "gdpr": {
      "status": "compliant",
      "violations": 0,
      "last_checked": "2024-01-01T10:00:00Z"
    },
    "hipaa": {
      "status": "compliant",
      "violations": 0,
      "last_checked": "2024-01-01T10:00:00Z"
    },
    "sox": {
      "status": "compliant",
      "violations": 0,
      "last_checked": "2024-01-01T10:00:00Z"
    }
  }
}
```

### Get Security Threats

**Endpoint:** `GET /api/security/threats`

**Query Parameters:**
- `threat_type` (optional): Filter by threat type
- `severity` (optional): Filter by severity
- `limit` (optional): Maximum results (default: 100)

**Response:**
```json
{
  "success": true,
  "data": {
    "threats": [
      {
        "event_id": "threat_123",
        "threat_type": "suspicious_traffic",
        "threat_level": "medium",
        "source_ip": "192.168.1.100",
        "user_id": "user123",
        "description": "High volume of API calls detected",
        "timestamp": "2024-01-01T10:45:00Z",
        "confidence_score": 0.85,
        "mitigated": false
      }
    ],
    "total": 1
  }
}
```

## Service Topology

### Get Topology Analysis

**Endpoint:** `GET /api/topology/analysis`

**Response:**
```json
{
  "success": true,
  "data": {
    "services": ["api-gateway", "user-service", "auth-service"],
    "relationships": [
      {
        "from": "api-gateway",
        "to": "user-service",
        "calls": 1500,
        "avg_response_time": 120,
        "error_rate": 0.01
      }
    ],
    "clusters": [
      {
        "name": "authentication-cluster",
        "services": ["api-gateway", "auth-service"],
        "centrality_score": 0.85
      }
    ],
    "critical_paths": [
      {
        "path": ["api-gateway", "auth-service", "user-service"],
        "total_calls": 2100,
        "bottlenecks": ["user-service"]
      }
    ],
    "health_score": 92.5
  }
}
```

### Get Topology Visualization

**Endpoint:** `GET /api/topology/visualization`

**Query Parameters:**
- `format` (optional): Output format (default: "cytoscape")
- `include_health` (optional): Include health status (default: true)

**Response:**
```json
{
  "success": true,
  "data": {
    "format": "cytoscape",
    "elements": {
      "nodes": [
        {
          "id": "api-gateway",
          "label": "API Gateway",
          "health": "healthy",
          "load": 0.75
        }
      ],
      "edges": [
        {
          "source": "api-gateway",
          "target": "user-service",
          "calls": 1500,
          "avg_response_time": 120
        }
      ]
    },
    "metadata": {
      "generated_at": "2024-01-01T11:00:00Z",
      "total_services": 12,
      "total_relationships": 28
    }
  }
}
```

## Error Handling

All API endpoints follow consistent error handling patterns:

**Standard Error Response:**
```json
{
  "success": false,
  "error": "Error message",
  "error_code": "ERROR_CODE",
  "details": {
    "field": "additional error details"
  },
  "timestamp": "2024-01-01T10:00:00Z",
  "request_id": "req_123"
}
```

### Common Error Codes

- `AUTHENTICATION_FAILED`: Invalid credentials or token
- `AUTHORIZATION_DENIED`: Insufficient permissions
- `VALIDATION_ERROR`: Invalid request data
- `NOT_FOUND`: Resource not found
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `SERVICE_UNAVAILABLE`: Service temporarily unavailable
- `INTERNAL_ERROR`: Unexpected server error

### Rate Limiting

API endpoints are rate limited. When limits are exceeded:

```json
{
  "success": false,
  "error": "Rate limit exceeded",
  "error_code": "RATE_LIMIT_EXCEEDED",
  "details": {
    "retry_after": 60,
    "limit": 100,
    "remaining": 0,
    "reset_time": "2024-01-01T11:00:00Z"
  }
}
```

## Pagination

List endpoints support pagination:

**Request:**
```
GET /api/catalog/endpoints?limit=25&offset=50
```

**Response:**
```json
{
  "success": true,
  "data": {
    "items": [...],
    "total": 150,
    "limit": 25,
    "offset": 50,
    "has_more": true
  }
}
```

## WebSocket Support

Real-time updates are available via WebSocket:

**Endpoint:** `ws://localhost:8000/ws/analytics`

**Message Types:**
- `usage_update`: Real-time usage metrics
- `health_alert`: Service health changes
- `security_alert`: Security events
- `topology_change`: Service topology updates

## Versioning

API versioning follows semantic versioning:

- **Breaking changes**: New major version (e.g., `/api/v2/`)
- **Additions**: New minor version (e.g., `/api/v1.1/`)
- **Bug fixes**: Patch versions (backward compatible)

Current version: `v1.0`

## SDKs and Libraries

Generated client SDKs are available for:

- **Python**: `pip install unified-api-client`
- **JavaScript/TypeScript**: `npm install @unified-api/client`
- **Java**: Maven/Gradle dependency
- **Go**: `go get github.com/unified-api/go-client`
- **C#**: NuGet package

## Support

For API support and questions:

- **Documentation**: https://docs.unified-api.local
- **API Reference**: https://api.unified-api.local/docs
- **Support**: support@unified-api.local
- **GitHub Issues**: https://github.com/unified-api/dashboard/issues
