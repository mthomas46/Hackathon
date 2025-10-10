# Configuration Reference - Data Services Dashboard

**Service**: data-services-dashboard  
**Version**: 1.0.0  
**Last Updated**: October 9, 2025

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Environment Variables](#environment-variables)
3. [Configuration File](#configuration-file)
4. [Port Configuration](#port-configuration)
5. [Dependency Configuration](#dependency-configuration)
6. [Performance Tuning](#performance-tuning)
7. [Security Configuration](#security-configuration)
8. [Environment Profiles](#environment-profiles)
9. [Docker Configuration](#docker-configuration)
10. [Validation & Preflight Checks](#validation--preflight-checks)

---

## 🎯 Overview

The Data Services Dashboard uses **Pydantic Settings** for type-safe configuration management. All configuration can be provided via:

1. **Environment variables** (recommended for production)
2. **`.env` file** (for local development)
3. **Default values** (fallbacks)

**Configuration Prefix**: All environment variables use `DASHBOARD_` prefix.

---

## 🔧 Environment Variables

### **Service Identity**

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `DASHBOARD_SERVICE_NAME` | string | `data-services-dashboard` | Service name |
| `DASHBOARD_SERVICE_VERSION` | string | `1.0.0` | Service version |

### **Network Ports**

| Variable | Type | Default | Range | Description |
|----------|------|---------|-------|-------------|
| `DASHBOARD_UI_PORT` | int | `8501` | 1024-65535 | Streamlit UI port |
| `DASHBOARD_API_PORT` | int | `8080` | 1024-65535 | FastAPI REST API port |

### **External Services**

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `DASHBOARD_LOG_COLLECTOR_URL` | string | `http://localhost:8104` | Log-collector service URL |

### **Services to Monitor**

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `DASHBOARD_DEFAULT_SERVICES` | list | `["All", "doc_store", ...]` | Default services to monitor |

### **Time Ranges**

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `DASHBOARD_TIME_RANGES` | list | `["Last 100 operations", ...]` | Available time range options |

### **Performance & Caching**

| Variable | Type | Default | Range | Description |
|----------|------|---------|-------|-------------|
| `DASHBOARD_CACHE_TTL` | int | `5` | 0-300 | Cache TTL in seconds (0 = disabled) |
| `DASHBOARD_HTTP_TIMEOUT` | float | `5.0` | 1.0-30.0 | HTTP request timeout (seconds) |

### **Retry Logic**

| Variable | Type | Default | Range | Description |
|----------|------|---------|-------|-------------|
| `DASHBOARD_MAX_RETRY_ATTEMPTS` | int | `3` | 1-10 | Maximum retry attempts for HTTP requests |
| `DASHBOARD_RETRY_DELAY` | float | `1.0` | 0.1-10.0 | Initial retry delay (seconds) |
| `DASHBOARD_RETRY_BACKOFF` | float | `2.0` | 1.0-5.0 | Retry backoff multiplier |

### **Environment**

| Variable | Type | Default | Options | Description |
|----------|------|---------|---------|-------------|
| `DASHBOARD_ENVIRONMENT` | string | `development` | `development`, `staging`, `production` | Runtime environment |
| `DASHBOARD_DEBUG` | bool | `false` | `true`, `false` | Enable debug mode |

---

## 📄 Configuration File

### **`.env` File Example**

Create a `.env` file in the service directory:

```env
# Service Identity
DASHBOARD_SERVICE_NAME=data-services-dashboard
DASHBOARD_SERVICE_VERSION=1.0.0

# Ports
DASHBOARD_UI_PORT=8501
DASHBOARD_API_PORT=8080

# External Services
DASHBOARD_LOG_COLLECTOR_URL=http://log-collector:8104

# Services to Monitor
DASHBOARD_DEFAULT_SERVICES=All,doc_store,prompt_store,external-service-store,memory-agent

# Performance
DASHBOARD_CACHE_TTL=10
DASHBOARD_HTTP_TIMEOUT=5.0

# Retry Logic
DASHBOARD_MAX_RETRY_ATTEMPTS=3
DASHBOARD_RETRY_DELAY=1.0
DASHBOARD_RETRY_BACKOFF=2.0

# Environment
DASHBOARD_ENVIRONMENT=production
DASHBOARD_DEBUG=false
```

### **Loading Configuration**

Configuration is automatically loaded via Pydantic Settings:

```python
from config import config

# Access configuration
print(config.ui_port)  # 8501
print(config.log_collector_url)  # http://log-collector:8104
```

---

## 🔌 Port Configuration

### **Port Registry**

| Service Component | Port | Protocol | Purpose |
|-------------------|------|----------|---------|
| **Streamlit UI** | 8501 | HTTP | Web interface for humans |
| **FastAPI REST API** | 8080 | HTTP | REST API for systems |

### **Port Conflicts**

If ports are already in use, update via environment variables:

```bash
export DASHBOARD_UI_PORT=8502
export DASHBOARD_API_PORT=8081
```

### **Docker Port Mapping**

```yaml
# docker-compose.yml
services:
  data-services-dashboard:
    ports:
      - "8501:8501"  # Streamlit UI
      - "8080:8080"  # FastAPI API
```

---

## 🔗 Dependency Configuration

### **Log-Collector**

**Required**: Yes (Critical)

**Configuration**:
```env
DASHBOARD_LOG_COLLECTOR_URL=http://log-collector:8104
```

**Health Check**:
```bash
curl http://log-collector:8104/health
```

**Fallback Behavior**:
- Dashboard continues to function
- Shows "Log Collector: Disconnected" in sidebar
- Displays empty state or cached data

### **Connection Settings**

**Connection Pooling**:
```python
# Automatically configured
http_client = httpx.Client(
    limits=httpx.Limits(
        max_connections=10,
        max_keepalive_connections=5
    ),
    timeout=config.http_timeout
)
```

**Retry Configuration**:
- **Attempts**: 3 (configurable)
- **Delay**: 1s initial, 2s, 4s (exponential backoff)
- **Timeout**: 5s per request

---

## ⚡ Performance Tuning

### **Cache Configuration**

**Streamlit Cache**:
```env
# Cache TTL (seconds)
DASHBOARD_CACHE_TTL=5  # Default: 5s

# Recommended values:
# - Development: 0 (no cache)
# - Production: 10-30 (balance freshness vs load)
# - Heavy load: 60+ (reduce log-collector requests)
```

**Cache Behavior**:
- Caches log fetching per `(service, limit)` combination
- Automatically expires after TTL
- Disabled if `DASHBOARD_CACHE_TTL=0`

### **Request Optimization**

**Timeout Tuning**:
```env
# HTTP timeout (seconds)
DASHBOARD_HTTP_TIMEOUT=5.0

# Recommended values:
# - Fast network: 3.0
# - Normal network: 5.0
# - Slow network: 10.0
```

**Retry Tuning**:
```env
# Reduce retries for faster failure
DASHBOARD_MAX_RETRY_ATTEMPTS=2
DASHBOARD_RETRY_DELAY=0.5
DASHBOARD_RETRY_BACKOFF=1.5

# Increase for unreliable networks
DASHBOARD_MAX_RETRY_ATTEMPTS=5
DASHBOARD_RETRY_DELAY=2.0
DASHBOARD_RETRY_BACKOFF=3.0
```

### **Data Volume Optimization**

**Time Range Limits**:
```python
# Fetch fewer logs for better performance
time_ranges = [
    "Last 100 operations",   # Fast
    "Last 500 operations",   # Moderate
    "Last 1000 operations"   # Slower
]
```

**Service Filtering**:
- Filter by specific service reduces data volume
- Use "All" sparingly in production

---

## 🔒 Security Configuration

### **Production Hardening**

```env
# Disable debug mode
DASHBOARD_DEBUG=false

# Use production environment
DASHBOARD_ENVIRONMENT=production

# Use secure URLs (HTTPS)
DASHBOARD_LOG_COLLECTOR_URL=https://log-collector.internal:8104
```

### **Network Security**

**Firewall Rules**:
```bash
# Allow only internal network access to API
iptables -A INPUT -p tcp --dport 8080 -s 10.0.0.0/8 -j ACCEPT
iptables -A INPUT -p tcp --dport 8080 -j DROP

# Allow browser access to UI
iptables -A INPUT -p tcp --dport 8501 -j ACCEPT
```

**Docker Network Isolation**:
```yaml
# docker-compose.yml
networks:
  internal:
    internal: true  # No external access
  external:
    driver: bridge

services:
  data-services-dashboard:
    networks:
      - internal  # Can access log-collector
      - external  # Can be accessed from outside
```

### **API Access Control**

Currently, the API is open. For production, consider:

1. **API Key Authentication**
2. **Rate Limiting**
3. **IP Whitelisting**
4. **OAuth2/JWT Tokens**

---

## 🌍 Environment Profiles

### **Development Profile**

```env
# .env.development
DASHBOARD_ENVIRONMENT=development
DASHBOARD_DEBUG=true
DASHBOARD_CACHE_TTL=0
DASHBOARD_LOG_COLLECTOR_URL=http://localhost:8104
DASHBOARD_UI_PORT=8501
DASHBOARD_API_PORT=8080
```

### **Staging Profile**

```env
# .env.staging
DASHBOARD_ENVIRONMENT=staging
DASHBOARD_DEBUG=false
DASHBOARD_CACHE_TTL=10
DASHBOARD_LOG_COLLECTOR_URL=http://log-collector-staging:8104
DASHBOARD_UI_PORT=8501
DASHBOARD_API_PORT=8080
```

### **Production Profile**

```env
# .env.production
DASHBOARD_ENVIRONMENT=production
DASHBOARD_DEBUG=false
DASHBOARD_CACHE_TTL=30
DASHBOARD_LOG_COLLECTOR_URL=https://log-collector.prod.internal:8104
DASHBOARD_UI_PORT=8501
DASHBOARD_API_PORT=8080
DASHBOARD_MAX_RETRY_ATTEMPTS=5
DASHBOARD_RETRY_DELAY=2.0
```

### **Loading Profiles**

```bash
# Development
cp .env.development .env
streamlit run app.py

# Production
cp .env.production .env
docker-compose up -d
```

---

## 🐳 Docker Configuration

### **Environment Variables in Docker**

```yaml
# docker-compose.yml
services:
  data-services-dashboard:
    image: data-services-dashboard:1.0.0
    environment:
      DASHBOARD_UI_PORT: 8501
      DASHBOARD_API_PORT: 8080
      DASHBOARD_LOG_COLLECTOR_URL: http://log-collector:8104
      DASHBOARD_CACHE_TTL: 30
      DASHBOARD_ENVIRONMENT: production
    ports:
      - "8501:8501"
      - "8080:8080"
    depends_on:
      log-collector:
        condition: service_healthy
```

### **Dockerfile Configuration**

```dockerfile
# Set environment variables
ENV DASHBOARD_UI_PORT=8501
ENV DASHBOARD_API_PORT=8080
ENV DASHBOARD_LOG_COLLECTOR_URL=http://log-collector:8104
ENV DASHBOARD_CACHE_TTL=30
ENV DASHBOARD_ENVIRONMENT=production
```

---

## ✅ Validation & Preflight Checks

### **Configuration Validation**

Pydantic automatically validates configuration on load:

```python
# config.py
class DashboardConfig(BaseSettings):
    ui_port: int = Field(ge=1024, le=65535)  # Valid port range
    cache_ttl: int = Field(ge=0, le=300)     # 0-300 seconds
```

### **Preflight Checks**

Run preflight checks before starting:

```bash
# Check configuration
python -c "from config import config; print(config.model_dump())"

# Check log-collector connectivity
curl http://localhost:8104/health

# Check ports are available
lsof -i :8501
lsof -i :8080
```

### **Health Check After Startup**

```bash
# Wait for service to start
sleep 10

# Check Streamlit UI
curl http://localhost:8501

# Check FastAPI API
curl http://localhost:8080/health

# Check API documentation
curl http://localhost:8080/docs
```

---

## 🔧 Advanced Configuration

### **Custom Service List**

```python
# Programmatically update config
from config import config

config.default_services = ["All", "custom-service-1", "custom-service-2"]
```

### **Dynamic Configuration Reload**

Configuration is loaded once at startup. To reload:

1. Update `.env` file
2. Restart service: `streamlit run app.py` or `docker-compose restart`

---

## 📚 Related Documentation

- [README.md](./README.md) - Service overview
- [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) - Deployment instructions
- [Master Configuration Registry](../../docs/refactoring/MASTER_CONFIGURATION_REGISTRY.md) - Ecosystem-wide config

---

**Configuration Version**: 1.0.0  
**Last Updated**: October 9, 2025  
**Status**: Production Ready

