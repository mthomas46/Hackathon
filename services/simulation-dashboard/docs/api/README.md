# Intelligent Project Simulation Dashboard - REST API

**Enterprise-Grade REST API** for the Intelligent Project Simulation Dashboard Service, providing programmatic access to dashboard functionality, real-time monitoring, AI-powered insights, and ecosystem management.

## 🏗️ API Architecture

### Core Principles
- **RESTful Design**: Standard HTTP methods with resource-based URLs
- **OpenAPI 3.0**: Comprehensive API specification with interactive documentation
- **Type Safety**: Pydantic models for request/response validation
- **Error Handling**: Standardized error responses with detailed information
- **Rate Limiting**: Intelligent rate limiting with configurable thresholds
- **Versioning**: Semantic versioning with backward compatibility

### Technology Stack
- **Framework**: FastAPI with automatic OpenAPI generation
- **Validation**: Pydantic for type-safe request/response models
- **Documentation**: Interactive Swagger UI and ReDoc
- **Authentication**: API key authentication (configurable)
- **CORS**: Cross-origin resource sharing support
- **Logging**: Structured logging with request tracing

## 🚀 Quick Start

### Development Server
```bash
# Install dependencies
pip install -r requirements.txt
pip install fastapi uvicorn

# Start API server
python -m services.simulation_dashboard.api.main

# API will be available at:
# - Interactive Docs: http://localhost:8502/docs
# - Alternative Docs: http://localhost:8502/redoc
# - OpenAPI Schema: http://localhost:8502/openapi.json
```

### Docker Deployment
```bash
# Build and run with Docker
docker build -f services/simulation-dashboard/Dockerfile.api -t dashboard-api .
docker run -p 8502:8502 dashboard-api
```

### Ecosystem Integration
```bash
# Run with full ecosystem
cd /path/to/hackathon
docker-compose --profile simulation --profile ai_services up dashboard-api
```

## 📋 API Endpoints

### Core Resources

#### 🏥 Health & Monitoring
- `GET /health` - Service health check
- `GET /api/v1/ecosystem/health` - Ecosystem-wide health status
- `GET /api/v1/ecosystem/services/{service_name}/health` - Individual service health

#### 🎯 Simulations Management
- `GET /api/v1/simulations` - List simulations with filtering
- `POST /api/v1/simulations` - Create new simulation
- `GET /api/v1/simulations/{simulation_id}` - Get simulation details
- `PUT /api/v1/simulations/{simulation_id}` - Update simulation
- `DELETE /api/v1/simulations/{simulation_id}` - Delete simulation
- `POST /api/v1/simulations/{simulation_id}/execute` - Execute simulation
- `GET /api/v1/simulations/{simulation_id}/status` - Get execution status
- `GET /api/v1/simulations/{simulation_id}/metrics` - Get performance metrics
- `GET /api/v1/simulations/{simulation_id}/logs` - Get simulation logs

#### 📊 Dashboard Analytics
- `GET /api/v1/dashboard/metrics` - Dashboard performance metrics
- `GET /api/v1/dashboard/ai-metrics` - AI-powered feature metrics
- `GET /api/v1/dashboard/performance-metrics` - System performance metrics
- `GET /api/v1/dashboard/config` - Current configuration
- `GET /api/v1/dashboard/analytics/summary` - Analytics summary
- `GET /api/v1/dashboard/system/info` - System information

#### 🤖 Autonomous Operations
- `POST /api/v1/dashboard/actions/autonomous` - Trigger autonomous action
- `GET /api/v1/dashboard/actions/autonomous` - List autonomous actions
- `GET /api/v1/dashboard/actions/autonomous/{action_id}` - Get action details

#### 🌐 Ecosystem Management
- `GET /api/v1/ecosystem/services` - Discover available services
- `GET /api/v1/ecosystem/metrics/cross-service` - Cross-service analytics
- `GET /api/v1/ecosystem/alerts` - Ecosystem alerts
- `POST /api/v1/ecosystem/alerts/{alert_id}/acknowledge` - Acknowledge alert
- `GET /api/v1/ecosystem/topology` - Service dependency topology

## 🔐 Authentication & Security

### API Key Authentication
```bash
# Include API key in request header
curl -H "X-API-Key: your-api-key" http://localhost:8502/api/v1/simulations
```

### Rate Limiting
- **Default Limits**: 1000 requests per hour per API key
- **Burst Limits**: 100 requests per minute
- **Headers**: Rate limit information included in responses
  - `X-RateLimit-Limit`: Total requests allowed per hour
  - `X-RateLimit-Remaining`: Remaining requests
  - `X-RateLimit-Reset`: Time until reset (Unix timestamp)

### Security Features
- **Input Validation**: All requests validated with Pydantic models
- **SQL Injection Protection**: Parameterized queries
- **XSS Protection**: Output sanitization
- **CORS Configuration**: Configurable cross-origin policies
- **Request Tracing**: Unique request IDs for debugging

## 📊 Request/Response Format

### Standard Response Format
```json
{
  "data": {...},
  "message": "Optional success message",
  "metadata": {
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2024-01-01T12:00:00Z",
    "version": "1.0.0"
  }
}
```

### Error Response Format
```json
{
  "error": "ERROR_CODE",
  "message": "Human-readable error message",
  "details": {
    "field": "specific_field_error",
    "constraint": "validation_rule"
  },
  "timestamp": "2024-01-01T12:00:00Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Pagination
```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "per_page": 50,
    "total": 150,
    "total_pages": 3,
    "has_next": true,
    "has_prev": false
  }
}
```

## 🧪 Testing the API

### Using curl
```bash
# Health check
curl http://localhost:8502/health

# List simulations
curl "http://localhost:8502/api/v1/simulations?limit=5"

# Create simulation
curl -X POST "http://localhost:8502/api/v1/simulations" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Simulation",
    "type": "software_development",
    "complexity": "medium",
    "team_size": 5,
    "duration_weeks": 8
  }'

# Get dashboard metrics
curl http://localhost:8502/api/v1/dashboard/metrics

# Get ecosystem health
curl http://localhost:8502/api/v1/ecosystem/health
```

### Using Python
```python
import httpx

async with httpx.AsyncClient(base_url="http://localhost:8502") as client:
    # Health check
    response = await client.get("/health")
    print(response.json())

    # List simulations
    response = await client.get("/api/v1/simulations", params={"limit": 10})
    simulations = response.json()

    # Create simulation
    simulation_data = {
        "name": "API Test Simulation",
        "type": "data_pipeline",
        "complexity": "high",
        "team_size": 8,
        "duration_weeks": 12
    }
    response = await client.post("/api/v1/simulations", json=simulation_data)
    new_simulation = response.json()
```

### Using JavaScript/Node.js
```javascript
const axios = require('axios');

const api = axios.create({
  baseURL: 'http://localhost:8502',
  timeout: 10000
});

// Health check
api.get('/health')
  .then(response => console.log(response.data))
  .catch(error => console.error(error));

// List simulations
api.get('/api/v1/simulations', { params: { limit: 5 } })
  .then(response => console.log(response.data))
  .catch(error => console.error(error));
```

## 📈 Performance Characteristics

### Response Times
- **Health Check**: < 10ms
- **Simple Queries**: < 50ms
- **Complex Analytics**: < 200ms
- **AI Insights Generation**: < 2s
- **Large Dataset Operations**: < 5s

### Throughput
- **Read Operations**: 1000+ requests/second
- **Write Operations**: 500+ requests/second
- **Concurrent Users**: 100+ simultaneous connections
- **WebSocket Connections**: 500+ concurrent streams

### Resource Usage
- **Memory**: < 500MB baseline, < 2GB under load
- **CPU**: < 20% average, < 80% peak
- **Network**: < 100Mbps average traffic
- **Storage**: < 10GB for logs and cache

## 🔄 API Evolution

### Versioning Strategy
- **URL Versioning**: `/api/v1/`, `/api/v2/`, etc.
- **Backward Compatibility**: Maintain support for 2 major versions
- **Deprecation Notices**: 6-month deprecation periods
- **Migration Guides**: Provided for breaking changes

### Change Management
- **Semantic Versioning**: MAJOR.MINOR.PATCH
- **Breaking Changes**: Major version increments
- **Additive Changes**: Minor version increments
- **Bug Fixes**: Patch version increments

### Roadmap (v2.0)
- **GraphQL Support**: Alternative query interface
- **Webhook Integration**: Real-time event streaming
- **Bulk Operations**: Batch API operations
- **Advanced Filtering**: Complex query capabilities
- **API Analytics**: Usage metrics and insights

## 🐛 Troubleshooting

### Common Issues

#### Connection Refused
```bash
# Check if API server is running
curl http://localhost:8502/health

# Check Docker containers
docker ps | grep dashboard

# View API logs
docker logs dashboard-api
```

#### Authentication Errors
```bash
# Verify API key
curl -H "X-API-Key: your-key" http://localhost:8502/api/v1/simulations

# Check API key validity
curl -H "X-API-Key: invalid-key" http://localhost:8502/api/v1/simulations
# Should return 401 Unauthorized
```

#### Rate Limiting
```bash
# Check rate limit headers
curl -v http://localhost:8502/api/v1/simulations

# Response headers should include:
# X-RateLimit-Limit: 1000
# X-RateLimit-Remaining: 999
# X-RateLimit-Reset: 1640995200
```

#### Performance Issues
```bash
# Monitor API performance
curl http://localhost:8502/api/v1/dashboard/performance-metrics

# Check system resources
docker stats dashboard-api

# Review slow queries in logs
docker logs dashboard-api | grep "slow\|timeout"
```

### Debug Mode
Enable detailed logging for troubleshooting:
```bash
export DASHBOARD_API_DEBUG=true
export DASHBOARD_LOG_LEVEL=DEBUG
python -m services.simulation_dashboard.api.main
```

## 📚 Additional Resources

### Documentation
- [OpenAPI Specification](./openapi.yaml) - Complete API specification
- [Interactive API Docs](http://localhost:8502/docs) - Swagger UI documentation
- [Alternative Docs](http://localhost:8502/redoc) - ReDoc documentation

### Related Services
- [Project Simulation Service](../project-simulation/README.md)
- [LLM Gateway Service](../llm-gateway/README.md)
- [Analysis Service](../analysis-service/README.md)
- [Log Collector Service](../log-collector/README.md)

### Development
- [API Development Guide](../developer/api-development.md)
- [Testing Guidelines](../developer/testing.md)
- [Deployment Guide](../deployment/api-deployment.md)

---

**🎯 Enterprise-Grade API**: This REST API provides comprehensive, type-safe, and performant access to all Intelligent Project Simulation Dashboard capabilities, enabling seamless integration with external systems and programmatic automation of complex simulation workflows.
