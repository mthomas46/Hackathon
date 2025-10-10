# Architecture Digitizer Service - Configuration Guide

## 📋 **Table of Contents**
- [Service Overview](#service-overview)
- [Port & Network Configuration](#port--network-configuration)
- [Environment Variables](#environment-variables)
- [Configuration Files](#configuration-files)
- [External API Configuration](#external-api-configuration)
- [Dependencies](#dependencies)
- [Docker Configuration](#docker-configuration)
- [Deployment Profiles](#deployment-profiles)

---

## 🎯 **Service Overview**

| Property | Value |
|----------|-------|
| **Service Name** | `architecture-digitizer` |
| **Service Title** | Architecture Digitizer |
| **Version** | 1.0.0 |
| **Default Port** | 5105 |
| **Protocol** | HTTP/REST |
| **Framework** | FastAPI |

---

## 🌐 **Port & Network Configuration**

### Primary Service Port
```yaml
Default Port: 5105
Environment Variable: SERVICE_API_PORT
Protocol: HTTP
Binding: 0.0.0.0:5105
```

### Port Conflicts
- ✅ No known conflicts with other ecosystem services
- Port 5105 is unique to `architecture-digitizer`

### Network Dependencies
| Service | Dependency Type | Purpose |
|---------|----------------|---------|
| **Miro API** | External Provider | Fetch Miro boards |
| **Figma API** | External Provider | Fetch FigJam files |
| **Lucid API** | External Provider | Fetch Lucid documents |
| **Confluence API** | External Provider | Fetch Confluence pages |
| **doc-store** | Internal Consumer | Store normalized diagrams (optional) |
| **log-collector-service** | Internal Consumer | Centralized logging (future) |

---

## 🔐 **Environment Variables**

### Core Service Configuration
```bash
# Service Identity
SERVICE_NAME=architecture-digitizer
SERVICE_VERSION=1.0.0
SERVICE_API_PORT=5105

# API Timeout & Retry Settings
API_TIMEOUT_SECONDS=30
MAX_RETRIES=3
RETRY_BACKOFF_SECONDS=1

# Rate Limiting
RATE_LIMIT_REQUESTS_PER_MINUTE=60

# Caching
CACHE_ENABLED=true
CACHE_TTL_SECONDS=300
```

### External API Tokens (Required for API-based normalization)
```bash
# Miro Integration
MIRO_TOKEN=your_miro_api_token_here
MIRO_BASE_URL=https://api.miro.com/v2

# Figma/FigJam Integration
FIGMA_TOKEN=your_figma_api_token_here
FIGMA_BASE_URL=https://api.figma.com/v1

# Lucidchart Integration
LUCID_TOKEN=your_lucid_api_token_here
LUCID_BASE_URL=https://lucid.app/api

# Confluence Integration
CONFLUENCE_TOKEN=your_confluence_api_token_here
CONFLUENCE_BASE_URL_TEMPLATE=https://{domain}.atlassian.net/wiki/rest/api
CONFLUENCE_DOMAIN=your-company
```

### Optional Configuration
```bash
# Default component type for unmapped diagram elements
DEFAULT_COMPONENT_TYPE=service

# Supported systems (comma-separated)
SUPAPI_PORTED_SYSTEMS=miro,figjam,lucid,confluence

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

---

## 📁 **Configuration Files**

### 1. `config.yaml` (Base Configuration)
```yaml
server:
  port: 5105

architecture_digitizer:
  supported_systems: ${SUPAPI_PORTED_SYSTEMS:-miro,figjam,lucid,confluence}
  api_timeout_seconds: ${API_TIMEOUT_SECONDS:-30}
  max_retries: ${MAX_RETRIES:-3}
  retry_backoff_seconds: ${RETRY_BACKOFF_SECONDS:-1}
  rate_limit_requests_per_minute: ${RATE_LIMIT_REQUESTS_PER_MINUTE:-60}
  default_component_type: ${DEFAULT_COMPONENT_TYPE:-service}
  cache_enabled: ${CACHE_ENABLED:-true}
  cache_ttl_seconds: ${CACHE_TTL_SECONDS:-300}

external_apis:
  miro:
    base_url: ${MIRO_BASE_URL:-https://api.miro.com/v2}
    token_env_var: MIRO_TOKEN
  figjam:
    base_url: ${FIGMA_BASE_URL:-https://api.figma.com/v1}
    token_env_var: FIGMA_TOKEN
  lucid:
    base_url: ${LUCID_BASE_URL:-https://lucid.app/api}
    token_env_var: LUCID_TOKEN
  confluence:
    base_url_template: ${CONFLUENCE_BASE_URL_TEMPLATE:-https://{domain}.atlassian.net/wiki/rest/api}
    token_env_var: CONFLUENCE_TOKEN
```

### 2. `config.development.yaml` (Development Overrides)
- Extends `config.yaml`
- Lower timeouts for faster local testing
- Debug logging enabled
- Mock external APIs (optional)

### 3. `config.production.yaml` (Production Overrides)
- Extends `config.yaml`
- Production-grade timeouts
- Enhanced error handling
- Metrics enabled
- Real external API connections

---

## 🔌 **External API Configuration**

### Miro API
```yaml
Base URL: https://api.miro.com/v2
Authentication: Bearer Token
Token Header: Authorization: Bearer {MIRO_TOKEN}
Documentation: https://developers.miro.com/docs/rest-api-reference
Rate Limit: 60 requests/minute (default)
```

**Required Scopes:**
- `boards:read` - Read board data

### Figma API (FigJam)
```yaml
Base URL: https://api.figma.com/v1
Authentication: Personal Access Token
Token Header: X-FIGMA-TOKEN: {FIGMA_TOKEN}
Documentation: https://www.figma.com/developers/api
Rate Limit: 60 requests/minute (default)
```

**Required Scopes:**
- `file:read` - Read file data

### Lucidchart API
```yaml
Base URL: https://lucid.app/api
Authentication: Bearer Token
Token Header: Authorization: Bearer {LUCID_TOKEN}
Documentation: https://developer.lucid.co/
Rate Limit: 60 requests/minute (default)
```

**Required Scopes:**
- `documents:read` - Read document data

### Confluence API
```yaml
Base URL: https://{domain}.atlassian.net/wiki/rest/api
Authentication: Bearer Token or API Token
Token Header: Authorization: Bearer {CONFLUENCE_TOKEN}
Documentation: https://developer.atlassian.com/cloud/confluence/rest/v1/intro/
Rate Limit: Variable (Atlassian Cloud limits)
```

**Required Scopes:**
- `read:confluence-content.summary` - Read page content

---

## 📦 **Dependencies**

### Core Dependencies
```txt
fastapi>=0.104.1          # Web framework
uvicorn[standard]>=0.24.0 # ASGI server
pydantic>=2.8.0           # Data validation
httpx>=0.25.2             # Async HTTP client
```

### External Integration
```txt
aiohttp>=3.12.0           # Alternative HTTP client
requests>=2.32.0          # Sync HTTP client
```

### Monitoring & Observability
```txt
prometheus-client>=0.20.0 # Metrics
psutil>=5.9.0             # System metrics
structlog>=23.0.0         # Structured logging
```

### Configuration & Utilities
```txt
pyyaml>=6.0.0             # YAML parsing
python-dotenv>=1.0.0      # Environment variables
```

### Data Processing
```txt
pandas>=2.0.0             # Data manipulation (optional)
numpy>=1.24.0             # Numerical operations (optional)
```

### Testing
```txt
pytest>=7.4.0             # Test framework
pytest-asyncio>=0.21.0    # Async testing
pytest-mock>=3.12.0       # Mocking
```

---

## 🐳 **Docker Configuration**

### Dockerfile
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5105
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5105"]
```

### docker-compose.yml
```yaml
services:
  architecture-digitizer:
    build: .
    container_name: architecture-digitizer
    ports:
      - "5105:5105"
    environment:
      - SERVICE_NAME=architecture-digitizer
      - SERVICE_API_PORT=5105
      - MIRO_TOKEN=${MIRO_TOKEN}
      - FIGMA_TOKEN=${FIGMA_TOKEN}
      - LUCID_TOKEN=${LUCID_TOKEN}
      - CONFLUENCE_TOKEN=${CONFLUENCE_TOKEN}
    networks:
      - ecosystem-network
    restart: unless-stopped

networks:
  ecosystem-network:
    external: true
```

---

## 🎭 **Deployment Profiles**

### Development Profile
```bash
# Characteristics:
- Local execution
- Mock external APIs (optional)
- Debug logging enabled
- Hot reload enabled
- No authentication required

# Run Command:
uvicorn main:app --reload --host 0.0.0.0 --port 5105
```

### Testing Profile
```bash
# Characteristics:
- Test database/cache
- Isolated network
- Comprehensive logging
- Metrics enabled

# Run Command:
docker-compose -f docker-compose.test.yml up
```

### Staging Profile
```bash
# Characteristics:
- Production-like environment
- Real external APIs
- Full monitoring
- Rate limiting enabled

# Run Command:
docker-compose -f docker-compose.staging.yml up
```

### Production Profile
```bash
# Characteristics:
- High availability
- Load balancing
- Full security hardening
- Performance monitoring
- Auto-scaling enabled

# Run Command:
docker-compose -f docker-compose.prod.yml up
```

---

## 🔍 **Health Check Configuration**

### Health Endpoint
```yaml
Endpoint: GET /health
Response: {"service": "architecture-digitizer", "status": "healthy"}
Interval: 30s
Timeout: 10s
Retries: 3
```

### Readiness Check
```yaml
Endpoint: GET /health
Expected Status: 200
Criteria:
  - Service is running
  - Configuration is loaded
  - Network is accessible
```

### Liveness Check
```yaml
Endpoint: GET /health
Expected Status: 200
Criteria:
  - Process is responsive
  - No deadlocks
```

---

## 📊 **Metrics Configuration**

### Prometheus Metrics
```yaml
Endpoint: GET /metrics
Format: Prometheus exposition format

Metrics:
  - architecture_digitizer_requests_total
  - architecture_digitizer_request_duration_seconds
  - architecture_digitizer_api_failures_total
  - architecture_digitizer_file_uploads_total
  - architecture_digitizer_cache_hits_total
  - architecture_digitizer_cache_misses_total
```

---

## 🔧 **Configuration Validation**

### Pre-flight Checks
```bash
# Validate configuration files
python -m yamllint config.yaml

# Check environment variables
python -c "from main import app; print('✅ Configuration valid')"

# Test external API connectivity
python scripts/test_api_connections.py
```

### Common Issues
1. **Missing API Tokens**: Ensure all required tokens are set
2. **Port Conflicts**: Verify port 5105 is available
3. **Network Issues**: Check firewall rules for external APIs
4. **Invalid Config**: Validate YAML syntax

---

## 🚀 **Quick Start**

```bash
# 1. Clone repository
git clone <repo-url>
cd services/architecture-digitizer

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set environment variables
export SERVICE_API_PORT=5105
export MIRO_TOKEN=your_token_here

# 4. Run service
uvicorn main:app --host 0.0.0.0 --port 5105

# 5. Verify
curl http://localhost:5105/health
```

---

## 📚 **Additional Resources**

- [Service README](./README.md) - Full service documentation
- [API Reference](http://localhost:5105/docs) - Swagger/OpenAPI docs
- [Master Refactoring Plan](../../docs/refactoring/MASTER_REFACTORING_PLAN.md)
- [Ecosystem Overview](../../docs-evergreen/01_ECOSYSTEM_OVERVIEW.md)

---

*Last Updated: October 10, 2025*
*Service: architecture-digitizer v1.0.0*
*Configuration Version: 1.0*

