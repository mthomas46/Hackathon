# Meta-Orchestrator API Reference

Complete API documentation for the Meta-Orchestration Service, including all endpoints, request/response formats, and usage examples.

## 📋 Table of Contents

- [Authentication](#authentication)
- [Service Management](#service-management)
- [Configuration Management](#configuration-management)
- [Monitoring & Observability](#monitoring--observability)
- [Audit & Validation](#audit--validation)
- [Ecosystem Management](#ecosystem-management)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)

## 🔐 Authentication

### API Key Authentication

All API requests require authentication using an API key:

```bash
# Set API key in environment
export META_ORCHESTRATOR_API_KEY="your-secure-api-key"

# Or pass in request headers
curl -H "X-API-Key: your-secure-api-key" \
     http://localhost:8080/api/v1/services
```

### Authentication Headers

```http
X-API-Key: your-api-key-here
Authorization: Bearer your-jwt-token  # Future implementation
```

## 🏷️ Service Management

### List All Services

```http
GET /api/v1/services
```

**Response:**
```json
[
  {
    "name": "web-frontend",
    "status": "running",
    "image": "nginx:alpine",
    "ports": ["80:80", "443:443"],
    "health": "healthy",
    "uptime": "2h 15m",
    "cpu_usage": "5.2%",
    "memory_usage": "128MB / 512MB"
  }
]
```

### Get Service Details

```http
GET /api/v1/services/{service_name}
```

**Parameters:**
- `service_name` (path): Name of the service

**Response:**
```json
{
  "name": "web-frontend",
  "status": "running",
  "image": "nginx:alpine",
  "ports": ["80:80", "443:443"],
  "environment": ["NODE_ENV=production"],
  "volumes": ["/var/log/nginx:/var/log/nginx"],
  "health": "healthy",
  "uptime": "2h 15m 30s",
  "restart_count": 0,
  "created": "2024-01-15T10:00:00Z",
  "networks": ["web-network", "internal-network"]
}
```

### Start Service

```http
POST /api/v1/services/{service_name}/start
```

**Parameters:**
- `service_name` (path): Name of the service
- `profile` (query, optional): Docker Compose profile (default: "all")

**Response:**
```json
{
  "service_name": "web-frontend",
  "action": "start",
  "status": "success",
  "message": "Service started successfully",
  "timestamp": "2024-01-15T10:30:00Z",
  "duration": 15.5
}
```

### Stop Service

```http
POST /api/v1/services/{service_name}/stop
```

**Response:**
```json
{
  "service_name": "web-frontend",
  "action": "stop",
  "status": "success",
  "message": "Service stopped successfully",
  "timestamp": "2024-01-15T10:45:00Z",
  "duration": 8.2
}
```

### Restart Service

```http
POST /api/v1/services/{service_name}/restart
```

**Response:**
```json
{
  "service_name": "web-frontend",
  "action": "restart",
  "status": "success",
  "message": "Service restarted successfully",
  "timestamp": "2024-01-15T11:00:00Z",
  "duration": 22.8
}
```

### Get Service Logs

```http
GET /api/v1/services/{service_name}/logs
```

**Parameters:**
- `service_name` (path): Name of the service
- `lines` (query, optional): Number of log lines to retrieve (default: 100, max: 1000)

**Response:**
```json
{
  "service": "web-frontend",
  "logs": [
    "2024-01-15T10:30:00Z INFO: Server started on port 3000",
    "2024-01-15T10:30:05Z INFO: Connected to database",
    "2024-01-15T10:30:10Z WARN: High memory usage detected"
  ]
}
```

## ⚙️ Configuration Management

### Update Service Configuration

```http
PUT /api/v1/services/{service_name}/config
```

**Request Body:**
```json
{
  "environment": {
    "NODE_ENV": "production",
    "PORT": "8080"
  },
  "restart_policy": "unless-stopped",
  "network_mode": "bridge"
}
```

**Response:**
```json
{
  "service_name": "web-frontend",
  "status": "success",
  "changes_applied": [
    "Updated NODE_ENV=production",
    "Updated PORT=8080",
    "Changed restart policy to unless-stopped"
  ],
  "backup_created": "config_backup_20240115_103000",
  "requires_restart": true
}
```

### Rollback Configuration

```http
POST /api/v1/services/{service_name}/config/rollback
```

**Request Body:**
```json
{
  "rollback_to": "2024-01-15T10:00:00Z",
  "reason": "Configuration change caused issues"
}
```

### Get Current Configuration

```http
GET /api/v1/services/{service_name}/config/current
```

**Response:**
```json
{
  "service_name": "web-frontend",
  "config": {
    "environment": {
      "NODE_ENV": "production",
      "PORT": "8080"
    },
    "ports": ["8080:3000"],
    "volumes": ["/data:/app/data"],
    "restart_policy": "unless-stopped"
  },
  "timestamp": "2024-01-15T11:00:00Z",
  "source": "docker_compose"
}
```

### Validate Configuration

```http
POST /api/v1/services/config/validate
```

**Request Body:**
```json
{
  "service_name": "web-frontend",
  "config": {
    "environment": {"PORT": "8080"},
    "ports": ["8080:3000"]
  }
}
```

**Response:**
```json
{
  "valid": true,
  "warnings": [],
  "errors": [],
  "suggestions": [
    "Consider adding health check configuration"
  ]
}
```

## 📊 Monitoring & Observability

### Get Health Status

```http
GET /api/v1/monitoring/health
```

**Response:**
```json
{
  "health_status": {
    "web-frontend": {
      "status": "healthy",
      "response_time": 0.15,
      "last_check": "2024-01-15T11:00:00Z",
      "endpoint": "http://localhost:3000/health",
      "uptime": "2h 15m"
    },
    "api-backend": {
      "status": "degraded",
      "response_time": 2.5,
      "last_check": "2024-01-15T10:59:45Z",
      "endpoint": "http://localhost:8000/health",
      "error": "High response time"
    }
  }
}
```

### Get Configuration Drift

```http
GET /api/v1/monitoring/drift
```

**Response:**
```json
{
  "drift_status": {
    "total_unresolved": 3,
    "by_service": {
      "web-frontend": [
        {
          "type": "environment_mismatch",
          "severity": "medium",
          "description": "NODE_ENV differs between compose and runtime",
          "timestamp": "2024-01-15T10:25:00Z"
        }
      ]
    }
  }
}
```

### Get Active Alerts

```http
GET /api/v1/monitoring/alerts
```

**Parameters:**
- `service_name` (query, optional): Filter by service

**Response:**
```json
{
  "alerts": [
    {
      "id": 123,
      "type": "health_failure",
      "severity": "high",
      "service": "api-backend",
      "title": "Service Health Check Failed",
      "message": "api-backend health check failed 5 times in 10 minutes",
      "timestamp": "2024-01-15T10:25:00Z",
      "acknowledged": false
    }
  ]
}
```

### Acknowledge Alert

```http
POST /api/v1/monitoring/alerts/{alert_id}/acknowledge
```

**Parameters:**
- `alert_id` (path): Alert ID to acknowledge
- `user` (query, optional): User acknowledging the alert

### Get Analytics Report

```http
GET /api/v1/monitoring/analytics
```

**Response:**
```json
{
  "analytics_report": {
    "time_range": "7d",
    "overall_health_score": 87.5,
    "risk_level": "low",
    "total_services": 15,
    "healthy_services": 13,
    "drift_events": 5,
    "mtbf_hours": 168.5,
    "mttr_minutes": 12.3,
    "recommendations": [
      "Consider implementing auto-scaling for api-backend",
      "Review configuration management processes"
    ]
  }
}
```

## 🔍 Audit & Validation

### Validate Docker Compose

```http
POST /api/v1/audit/docker-compose/validate
```

**Parameters:**
- `compose_file` (query, optional): Path to compose file (default: "docker-compose.dev.yml")

**Response:**
```json
{
  "docker_compose_validation": {
    "success": true,
    "services_count": 15,
    "port_conflicts": 0,
    "issues": [
      {
        "service": "web-frontend",
        "type": "health_check",
        "severity": "warning",
        "description": "Missing start_period in health check",
        "can_auto_fix": true
      }
    ],
    "warnings": 1,
    "errors": 0
  }
}
```

### Detect Configuration Drift

```http
POST /api/v1/audit/config/drift-detect
```

**Parameters:**
- `dev_only` (query, optional): Skip cross-environment comparisons (default: true)

**Response:**
```json
{
  "configuration_drift": {
    "success": true,
    "total_issues": 3,
    "high_severity": 1,
    "medium_severity": 2,
    "low_severity": 0,
    "schema_validation_passed": true,
    "scanned_files": 25,
    "scanned_containers": 12,
    "issues": [
      {
        "type": "docker_vs_compose",
        "severity": "high",
        "description": "Port mapping mismatch for service 'api-gateway'",
        "field_path": "ports",
        "can_auto_fix": false
      }
    ]
  }
}
```

### Validate Production Readiness

```http
POST /api/v1/audit/production-readiness/validate
```

**Parameters:**
- `target_level` (query, optional): Readiness level to validate against
  - `development_ready` (default)
  - `testing_ready`
  - `production_ready`

**Response:**
```json
{
  "production_readiness": {
    "success": true,
    "overall_readiness": "development_ready",
    "overall_score": 0.85,
    "total_checks": 8,
    "passed_checks": 7,
    "failed_checks": 1,
    "critical_failures": 0,
    "results": [
      {
        "check_name": "service_config_validation",
        "success": true,
        "score": 1.0,
        "message": "All service configurations valid",
        "issues": [],
        "recommendations": []
      }
    ]
  }
}
```

### Standardize Service Configuration

```http
POST /api/v1/audit/config/standardize/service/{service_name}
```

**Parameters:**
- `service_name` (path): Service to standardize
- `mode` (query, optional): Standardization mode
  - `validate` - Only validate (default)
  - `dry_run` - Show changes without applying
  - `apply` - Apply standardization fixes

**Response:**
```json
{
  "config_standardization": {
    "service_name": "web-frontend",
    "success": true,
    "changes_made": [
      "Updated server.port from 3000 to 8080",
      "Standardized environment variable naming"
    ],
    "warnings": [
      "DRY RUN: Changes shown are hypothetical"
    ],
    "errors": [],
    "issues": [
      {
        "service": "web-frontend",
        "type": "port_standardization",
        "severity": "info",
        "description": "Port updated from 3000 to 8080",
        "can_auto_fix": true
      }
    ]
  }
}
```

### Standardize All Configurations

```http
POST /api/v1/audit/config/standardize/all
```

**Parameters:**
- `mode` (query, optional): Standardization mode (validate/dry_run/apply)

**Response:**
```json
{
  "config_standardization": {
    "services_processed": 8,
    "services_standardized": 6,
    "total_issues": 12,
    "fixes_applied": 9,
    "standardization_rate": 0.75,
    "results": [
      {
        "service_name": "web-frontend",
        "success": true,
        "changes_made": ["Port standardized", "Environment variables updated"],
        "warnings": [],
        "errors": []
      }
    ]
  }
}
```

### Standardize Docker Configurations

```http
POST /api/v1/audit/docker/standardize
```

**Parameters:**
- `mode` (query, optional): Standardization mode (validate/dry_run/apply)

**Response:**
```json
{
  "docker_standardization": {
    "success": true,
    "files_processed": 3,
    "files_modified": 1,
    "issues_found": 5,
    "issues_fixed": 3,
    "validation_errors": 0,
    "pydantic_validation_passed": true,
    "issues": [
      {
        "service": "api-backend",
        "type": "port_mapping",
        "severity": "warning",
        "description": "Service should expose standardized port 8000",
        "can_auto_fix": false
      }
    ]
  }
}
```

## 🌐 Ecosystem Management

### Start All Services

```http
POST /api/v1/ecosystem/start
```

**Parameters:**
- `profile` (query, optional): Docker Compose profile (default: "all")

**Response:**
```json
{
  "message": "Starting all services in profile 'all'",
  "status": "initiated",
  "profile": "all",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Get Ecosystem Status

```http
GET /api/v1/ecosystem/status
```

**Response:**
```json
{
  "ecosystem_status": {
    "overall_health": "healthy",
    "total_services": 15,
    "running_services": 14,
    "stopped_services": 1,
    "degraded_services": 0,
    "last_updated": "2024-01-15T11:00:00Z",
    "services": {
      "web-frontend": "running",
      "api-backend": "running",
      "database": "stopped"
    }
  }
}
```

## 🚨 Error Handling

### Common Error Responses

#### Service Not Found
```json
{
  "detail": "Service 'unknown-service' not found"
}
```

#### Service Unavailable
```json
{
  "detail": "Meta-orchestrator not initialized"
}
```

#### Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "environment", "PORT"],
      "msg": "Port must be a valid integer",
      "type": "value_error"
    }
  ]
}
```

#### Permission Denied
```json
{
  "detail": "Insufficient permissions for operation"
}
```

### HTTP Status Codes

- `200` - Success
- `201` - Created
- `400` - Bad Request (validation error)
- `401` - Unauthorized (invalid API key)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found (service/configuration doesn't exist)
- `409` - Conflict (operation would cause issues)
- `422` - Unprocessable Entity (validation failed)
- `500` - Internal Server Error
- `503` - Service Unavailable (orchestrator not ready)

## ⚡ Rate Limiting

### Default Limits

- **Authenticated requests**: 100 requests per minute
- **Anonymous requests**: 10 requests per minute
- **Service start/stop operations**: 5 operations per minute
- **Configuration updates**: 20 updates per minute

### Rate Limit Headers

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
X-RateLimit-Retry-After: 60  # When limit exceeded
```

### Burst Handling

The API implements burst handling for critical operations:
- Short bursts allowed for immediate response
- Gradual throttling as limits approach
- Automatic backoff for clients

## 🔧 SDK Examples

### Python Client

```python
import requests

class MetaOrchestratorClient:
    def __init__(self, base_url="http://localhost:8080", api_key=None):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({'X-API-Key': api_key})

    def list_services(self):
        response = self.session.get(f"{self.base_url}/api/v1/services")
        return response.json()

    def start_service(self, service_name, profile="all"):
        response = self.session.post(
            f"{self.base_url}/api/v1/services/{service_name}/start",
            params={"profile": profile}
        )
        return response.json()

    def update_config(self, service_name, config):
        response = self.session.put(
            f"{self.base_url}/api/v1/services/{service_name}/config",
            json=config
        )
        return response.json()
```

### JavaScript/TypeScript Client

```javascript
class MetaOrchestratorClient {
    constructor(baseUrl = 'http://localhost:8080', apiKey = null) {
        this.baseUrl = baseUrl.replace(/\/$/, '');
        this.apiKey = apiKey;
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const headers = { 'Content-Type': 'application/json' };

        if (this.apiKey) {
            headers['X-API-Key'] = this.apiKey;
        }

        const response = await fetch(url, {
            headers,
            ...options
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        return response.json();
    }

    async listServices() {
        return this.request('/api/v1/services');
    }

    async startService(serviceName, profile = 'all') {
        return this.request(`/api/v1/services/${serviceName}/start`, {
            method: 'POST'
        });
    }

    async updateConfig(serviceName, config) {
        return this.request(`/api/v1/services/${serviceName}/config`, {
            method: 'PUT',
            body: JSON.stringify(config)
        });
    }
}
```

## 📚 Additional Resources

- [API Interactive Documentation](http://localhost:8080/docs) - Swagger UI
- [OpenAPI Specification](http://localhost:8080/openapi.json) - Machine-readable API spec
- [Service Architecture](./ARCHITECTURE.md) - Deep dive into service design
- [Developer Guide](./DEVELOPER_GUIDE.md) - How to extend and modify the service
- [Deployment Guide](./DEPLOYMENT.md) - Production deployment instructions
