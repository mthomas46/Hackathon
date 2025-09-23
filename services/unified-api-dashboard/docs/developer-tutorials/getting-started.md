# 🚀 Getting Started with Unified API Dashboard

## Overview

Welcome to the Unified API Dashboard! This tutorial will guide you through your first steps in exploring and managing your API ecosystem.

## Prerequisites

- Access to a running Unified API Dashboard instance
- API credentials (username/password)
- Basic understanding of REST APIs

## Step 1: Authentication

Before you can use the dashboard, you need to authenticate and obtain a JWT token.

### Using the Web Interface

1. Open your browser and navigate to the dashboard URL
2. Click "Login" in the top right corner
3. Enter your username and password
4. You'll be redirected to the main dashboard

### Using the REST API

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your-username",
    "password": "your-password"
  }'
```

**Response:**
```json
{
  "success": true,
  "data": {
    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "expires_at": "2024-01-01T12:00:00Z"
  }
}
```

Save the token for use in subsequent API calls:

```bash
TOKEN="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

## Step 2: Explore the API Catalog

### Discover Available Services

Let's see what services are available in your ecosystem:

```bash
curl -X GET http://localhost:8000/api/discovery/services \
  -H "Authorization: Bearer $TOKEN"
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "service_name": "user-service",
      "service_url": "http://user-service:8000",
      "status": "healthy"
    },
    {
      "service_name": "order-service",
      "service_url": "http://order-service:8000",
      "status": "healthy"
    }
  ]
}
```

### Browse API Endpoints

Now let's explore the available API endpoints:

```bash
curl -X GET "http://localhost:8000/api/catalog/endpoints" \
  -H "Authorization: Bearer $TOKEN"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "services": ["user-service", "order-service"],
    "endpoints": [
      {
        "service": "user-service",
        "path": "/users",
        "method": "GET",
        "summary": "List users"
      },
      {
        "service": "user-service",
        "path": "/users",
        "method": "POST",
        "summary": "Create user"
      }
    ],
    "total": 25
  }
}
```

### Search for Specific APIs

Search for user-related endpoints:

```bash
curl -X GET "http://localhost:8000/api/catalog/search?query=user" \
  -H "Authorization: Bearer $TOKEN"
```

## Step 3: Test API Endpoints

### Interactive Testing via Web UI

1. Navigate to the "API Testing" section in the dashboard
2. Select a service from the dropdown
3. Choose an endpoint from the list
4. Fill in any required parameters
5. Click "Send Request"
6. View the response, headers, and timing information

### Testing via REST API

Test the users endpoint:

```bash
curl -X GET "http://user-service:8000/users" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"
```

### Create a Test User

```bash
curl -X POST "http://user-service:8000/users" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe"
  }'
```

## Step 4: Monitor API Health

### Check Service Health

```bash
curl -X GET "http://localhost:8000/api/health/services" \
  -H "Authorization: Bearer $TOKEN"
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "service": "user-service",
      "status": "healthy",
      "response_time": 145,
      "uptime": 99.9,
      "last_check": "2024-01-01T10:30:00Z"
    }
  ]
}
```

### View Health Dashboard

In the web interface:
1. Go to the "Health Monitoring" section
2. View real-time health status of all services
3. Set up alerts for service degradation
4. Monitor response times and error rates

## Step 5: Analyze API Usage

### Get Usage Overview

```bash
curl -X GET "http://localhost:8000/api/analytics/usage/overview" \
  -H "Authorization: Bearer $TOKEN"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "total_requests": 15420,
    "unique_users": 234,
    "services_used": 12,
    "peak_usage_hour": 14,
    "top_endpoints": [
      {
        "endpoint": "/users",
        "service": "user-service",
        "requests": 2340
      }
    ]
  }
}
```

### View Analytics Dashboard

In the web interface:
1. Navigate to "Analytics & Insights"
2. View usage patterns and trends
3. Analyze performance metrics
4. Monitor error rates and types

## Step 6: Generate Client Code

### Generate Python Client

```bash
curl -X POST "http://localhost:8000/api/tools/generate-client" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "user-service",
    "language": "python"
  }'
```

**Response:**
```json
{
  "success": true,
  "data": {
    "language": "python",
    "client_code": "class UserServiceClient:\n    def __init__(self, base_url):\n        self.base_url = base_url\n        self.session = requests.Session()\n\n    def get_users(self, **params):\n        response = self.session.get(f'{self.base_url}/users', params=params)\n        return response.json()\n\n    def create_user(self, user_data):\n        response = self.session.post(f'{self.base_url}/users', json=user_data)\n        return response.json()",
    "filename": "user_service_client.py"
  }
}
```

### Using the Generated Client

Save the generated code to a file and use it:

```python
from user_service_client import UserServiceClient

# Initialize client
client = UserServiceClient("http://user-service:8000")

# Use the client
users = client.get_users(limit=10)
print(f"Found {len(users)} users")

# Create a new user
new_user = client.create_user({
    "username": "janedoe",
    "email": "jane@example.com",
    "first_name": "Jane",
    "last_name": "Doe"
})
print(f"Created user: {new_user}")
```

## Step 7: Validate API Specifications

### Validate OpenAPI Spec

```bash
curl -X POST "http://localhost:8000/api/tools/validate-spec" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "user-service",
    "openapi_spec": {
      "openapi": "3.0.0",
      "info": {"title": "User Service", "version": "1.0.0"},
      "paths": {
        "/users": {
          "get": {
            "summary": "List users",
            "responses": {
              "200": {
                "description": "Success",
                "content": {
                  "application/json": {
                    "schema": {"type": "array", "items": {"type": "object"}}
                  }
                }
              }
            }
          }
        }
      }
    }
  }'
```

**Response:**
```json
{
  "success": true,
  "data": {
    "valid": true,
    "errors": [],
    "warnings": ["Consider adding response schemas"],
    "compliance_score": 85,
    "recommendations": [
      "Add detailed response schemas",
      "Include authentication requirements"
    ]
  }
}
```

## Step 8: Explore Service Topology

### Get Topology Analysis

```bash
curl -X GET "http://localhost:8000/api/topology/analysis" \
  -H "Authorization: Bearer $TOKEN"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "services": ["api-gateway", "user-service", "order-service"],
    "relationships": [
      {
        "from": "api-gateway",
        "to": "user-service",
        "calls": 1500,
        "avg_response_time": 120
      }
    ],
    "clusters": [
      {
        "name": "user-management",
        "services": ["api-gateway", "user-service"],
        "centrality_score": 0.85
      }
    ],
    "health_score": 94.2
  }
}
```

### View Topology Visualization

In the web interface:
1. Go to "Service Topology" section
2. View interactive dependency graph
3. Explore service relationships
4. Identify bottlenecks and critical paths

## Step 9: Monitor Security & Compliance

### Check Audit Logs

```bash
curl -X GET "http://localhost:8000/api/audit/events?limit=10" \
  -H "Authorization: Bearer $TOKEN"
```

### View Compliance Status

```bash
curl -X GET "http://localhost:8000/api/audit/compliance" \
  -H "Authorization: Bearer $TOKEN"
```

### Monitor Security Threats

```bash
curl -X GET "http://localhost:8000/api/security/threats?limit=5" \
  -H "Authorization: Bearer $TOKEN"
```

## Next Steps

Now that you've completed the basics, you can:

1. **Set up monitoring alerts** for service health and performance
2. **Create custom dashboards** for your team's specific needs
3. **Integrate with CI/CD** pipelines for automated testing
4. **Explore advanced analytics** for usage patterns and optimization
5. **Set up automated client generation** for your development workflow

## Troubleshooting

### Common Issues

**Authentication Failed:**
- Check that your username/password is correct
- Ensure your account is active and not locked
- Verify token hasn't expired (refresh if needed)

**Service Unavailable:**
- Check service health status in the dashboard
- Verify network connectivity
- Contact system administrator if service is down

**Permission Denied:**
- Verify your user role has necessary permissions
- Check with administrator if you need additional access
- Some endpoints require elevated privileges

**Rate Limiting:**
- Wait for the reset period shown in error response
- Reduce request frequency
- Contact admin for higher rate limits if needed

### Getting Help

- **Documentation**: Check the full API reference
- **Support**: Contact your system administrator
- **Logs**: Check audit logs for detailed error information
- **Health Checks**: Use `/health` endpoint for system status

## Summary

You've successfully:
- ✅ Authenticated with the dashboard
- ✅ Explored available services and APIs
- ✅ Tested API endpoints
- ✅ Monitored service health
- ✅ Analyzed usage patterns
- ✅ Generated client code
- ✅ Validated API specifications
- ✅ Explored service topology
- ✅ Monitored security and compliance

The Unified API Dashboard is now your central hub for managing and monitoring your entire API ecosystem!
