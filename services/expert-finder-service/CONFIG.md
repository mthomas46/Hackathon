# Configuration Guide - expert-finder-service

**Service**: expert-finder-service  
**Version**: 2.0.0 (DDD Refactored)  
**Port**: 5160 (HTTP)  
**Last Updated**: October 10, 2025

---

## 📋 Table of Contents

1. [Port Configuration](#port-configuration)
2. [Environment Variables](#environment-variables)
3. [Configuration Profiles](#configuration-profiles)
4. [Dependencies](#dependencies)
5. [Credentials & Secrets](#credentials--secrets)
6. [Docker Configuration](#docker-configuration)
7. [Validation](#validation)
8. [Troubleshooting](#troubleshooting)

---

## 🔌 Port Configuration

### Assigned Ports

| Purpose | Port | Protocol | Notes |
|---------|------|----------|-------|
| HTTP API | 5160 | HTTP | Main REST API |

### Port Conflict Check

**Status**: ✅ No conflicts (verified October 10, 2025)

Port 5160 is unique and does not conflict with other services. Verified against:
- [MASTER_CONFIGURATION_REGISTRY.md](../../docs/refactoring/MASTER_CONFIGURATION_REGISTRY.md)

---

## 🔐 Environment Variables

### Required Variables

| Variable | Default | Description | Required |
|----------|---------|-------------|----------|
| `SERVICE_NAME` | expert-finder-service | Service identifier | No |
| `SERVICE_PORT` | 5160 | HTTP port | No |
| `USER_STORE_URL` | http://localhost:5110 | user-store service URL | **Yes** ⚠️ |

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ENVIRONMENT` | development | Environment (development, test, staging, production) |
| `DOC_STORE_URL` | http://localhost:5100 | doc-store service URL (optional) |
| `EXTERNAL_SERVICE_STORE_URL` | http://localhost:5150 | external-service-store URL (optional) |
| `LOG_COLLECTOR_URL` | http://localhost:5140 | log-collector service URL |
| `LOG_LEVEL` | INFO | Logging level (DEBUG, INFO, WARNING, ERROR) |

### Scoring Algorithm Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `SCORING_ROLE_WEIGHT` | 0.30 | Weight for role matching (0-1) |
| `SCORING_TOPIC_WEIGHT` | 0.40 | Weight for topic relevance (0-1) |
| `SCORING_SERVICE_WEIGHT` | 0.20 | Weight for service contribution (0-1) |
| `SCORING_DOCUMENT_WEIGHT` | 0.10 | Weight for document authorship (0-1) |

**Note**: Weights must sum to 1.0

### HTTP Client Configuration

| Variable | Default (Dev) | Default (Prod) | Description |
|----------|---------------|----------------|-------------|
| `HTTP_TIMEOUT_SECONDS` | 30 | 60 | Timeout for external API calls |
| `HTTP_MAX_RETRIES` | 3 | 5 | Max retry attempts for failed calls |
| `HTTP_POOL_SIZE` | 10 | 50 | Connection pool size |
| `HTTP_RETRY_BACKOFF_SECONDS` | 1 | 2 | Initial backoff time for retries |

### Performance Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `CACHE_TTL_SECONDS` | 300 | Cache time-to-live (5 minutes) |
| `MAX_RESULTS` | 100 | Maximum search results to return |

---

## 🎛️ Configuration Profiles

### Development Profile

**Use Case**: Local development, debugging

**Configuration**:
```bash
ENVIRONMENT=development
SERVICE_PORT=5160
USER_STORE_URL=http://localhost:5110
LOG_LEVEL=DEBUG
HTTP_TIMEOUT_SECONDS=30
HTTP_POOL_SIZE=10
CACHE_TTL_SECONDS=60  # Short cache for development
```

**Features**:
- Debug logging enabled
- Short cache TTL (1 minute)
- Small connection pools
- Detailed error messages (including stack traces)
- Optional mock mode for external services

---

### Test Profile

**Use Case**: Automated testing, CI/CD

**Configuration**:
```bash
ENVIRONMENT=test
SERVICE_PORT=5160
USER_STORE_URL=http://localhost:5110  # Or mock server
LOG_LEVEL=WARNING
HTTP_TIMEOUT_SECONDS=10  # Faster timeouts
HTTP_POOL_SIZE=5
CACHE_TTL_SECONDS=0  # No caching in tests
```

**Features**:
- Minimal logging (warnings and errors only)
- No caching (predictable tests)
- Fast timeouts
- Mock external services (optional)

---

### Staging Profile

**Use Case**: Pre-production validation

**Configuration**:
```bash
ENVIRONMENT=staging
SERVICE_PORT=5160
USER_STORE_URL=http://user-store-staging:5110
DOC_STORE_URL=http://doc-store-staging:5100
EXTERNAL_SERVICE_STORE_URL=http://external-service-store-staging:5150
LOG_LEVEL=INFO
HTTP_TIMEOUT_SECONDS=60
HTTP_POOL_SIZE=50
CACHE_TTL_SECONDS=300  # 5 minutes
```

**Features**:
- Production-like configuration
- Real external services (staging environment)
- Full caching enabled
- Standard logging
- Sanitized error messages

---

### Production Profile

**Use Case**: Production deployment

**Configuration**:
```bash
ENVIRONMENT=production
SERVICE_PORT=5160
USER_STORE_URL=https://user-store.company.com
DOC_STORE_URL=https://doc-store.company.com
EXTERNAL_SERVICE_STORE_URL=https://external-service-store.company.com
LOG_COLLECTOR_URL=https://log-collector.company.com
LOG_LEVEL=INFO
HTTP_TIMEOUT_SECONDS=60
HTTP_MAX_RETRIES=5
HTTP_POOL_SIZE=50
HTTP_RETRY_BACKOFF_SECONDS=2
CACHE_TTL_SECONDS=300  # 5 minutes
MAX_RESULTS=100
```

**Features**:
- Info logging (no debug)
- Real external services with HTTPS
- Large connection pools (50 connections)
- Longer timeouts (60s)
- More retries (5 attempts)
- Sanitized error messages (no stack traces to clients)
- Full caching (5 min TTL)
- Performance monitoring enabled
- Request ID tracking

**Security**:
- No secrets in code
- All URLs use HTTPS
- Error details hidden from clients
- Rate limiting enabled

---

## 🔗 Dependencies

### Required Services

| Service | Purpose | URL (Dev) | URL (Prod) | Status |
|---------|---------|-----------|------------|--------|
| `user-store` | User/expert data | http://localhost:5110 | https://user-store.company.com | **REQUIRED** ⚠️ |

**Impact if Unavailable**: Service cannot function (expert data source)

### Optional Services

| Service | Purpose | URL (Dev) | URL (Prod) | Graceful Degradation |
|---------|---------|-----------|------------|----------------------|
| `doc-store` | Document authorship | http://localhost:5100 | https://doc-store.company.com | Document scoring disabled |
| `external-service-store` | Service contribution | http://localhost:5150 | https://external-service-store.company.com | Service scoring reduced |
| `log-collector` | Centralized logging | http://localhost:5140 | https://log-collector.company.com | Falls back to stdout |

---

## 🔑 Credentials & Secrets

### API Keys

**Currently**: No API keys required

**Future**: If authentication is added:
- `USER_STORE_API_KEY` (required)
- `DOC_STORE_API_KEY` (optional)

### Secrets Management

- **Development**: `.env` file (not committed)
- **Test**: Environment variables in CI
- **Staging**: Kubernetes Secrets or AWS Secrets Manager
- **Production**: Kubernetes Secrets or AWS Secrets Manager

**Never commit secrets to Git!** ⚠️

---

## 🐳 Docker Configuration

### Dockerfile

**Base Image**: `python:3.11-slim`  
**Working Directory**: `/app`  
**Exposed Port**: `5160`  
**Health Check**: `GET /health` (every 30s)

### Build Command

```bash
docker build -t expert-finder-service:2.0.0 .
```

### Run Command (Development)

```bash
docker run -d \
  --name expert-finder-service \
  -p 5160:5160 \
  -e USER_STORE_URL=http://host.docker.internal:5110 \
  -e LOG_LEVEL=DEBUG \
  expert-finder-service:2.0.0
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  expert-finder-service:
    build: .
    container_name: expert-finder-service
    ports:
      - "5160:5160"
    environment:
      - SERVICE_PORT=5160
      - USER_STORE_URL=http://user-store:5110
      - DOC_STORE_URL=http://doc-store:5100
      - EXTERNAL_SERVICE_STORE_URL=http://external-service-store:5150
      - LOG_COLLECTOR_URL=http://log-collector:5140
      - ENVIRONMENT=development
      - LOG_LEVEL=INFO
    depends_on:
      - user-store
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5160/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    networks:
      - microservices

networks:
  microservices:
    external: true
```

---

## ✅ Validation

### Preflight Checks

Run before deployment:

```bash
# Check port conflicts
make check-port-conflicts

# Validate configuration
make validate-config

# Validate YAML syntax
make validate-yaml

# Validate Dockerfile
make validate-docker

# Run all preflight checks
make preflight
```

### Health Check

```bash
curl http://localhost:5160/health
```

**Expected Response**:
```json
{
  "status": "healthy",
  "service": "expert-finder-service",
  "version": "2.0.0",
  "uptime_seconds": 123.45,
  "timestamp": "2025-10-10T12:00:00Z",
  "dependencies": {
    "user-store": "connected",
    "doc-store": "connected",
    "external-service-store": "connected"
  }
}
```

### Configuration Validation

```python
# Validate weights sum to 1.0
from domain.value_objects.scoring_weights import ScoringWeights

weights = ScoringWeights(
    role_weight=float(os.getenv("SCORING_ROLE_WEIGHT", "0.30")),
    topic_weight=float(os.getenv("SCORING_TOPIC_WEIGHT", "0.40")),
    service_weight=float(os.getenv("SCORING_SERVICE_WEIGHT", "0.20")),
    document_weight=float(os.getenv("SCORING_DOCUMENT_WEIGHT", "0.10"))
)
# Raises ValueError if weights don't sum to 1.0
```

---

## 🔧 Troubleshooting

### Issue: Service won't start

**Symptoms**: Container exits immediately

**Possible Causes**:
1. Port 5160 already in use
2. Missing required `USER_STORE_URL` environment variable
3. Invalid scoring weights (don't sum to 1.0)

**Solutions**:
```bash
# Check port
lsof -i :5160

# Check environment variables
docker exec expert-finder-service env | grep USER_STORE

# Check logs
docker logs expert-finder-service
```

---

### Issue: "Cannot connect to user-store"

**Symptoms**: Health check fails, API returns 503

**Possible Causes**:
1. user-store service is down
2. Incorrect `USER_STORE_URL`
3. Network connectivity issues

**Solutions**:
```bash
# Check user-store health
curl http://localhost:5110/health

# Check network connectivity from container
docker exec expert-finder-service curl http://user-store:5110/health

# Check DNS resolution
docker exec expert-finder-service nslookup user-store
```

---

### Issue: Slow search responses

**Symptoms**: Search takes > 1 second

**Possible Causes**:
1. Cache not working (check `CACHE_TTL_SECONDS`)
2. user-store is slow
3. Connection pool too small

**Solutions**:
```bash
# Check cache configuration
docker exec expert-finder-service env | grep CACHE

# Increase connection pool
# Set HTTP_POOL_SIZE=50 (default production value)

# Check user-store performance
curl -w "@curl-format.txt" http://localhost:5110/users
```

---

### Issue: "Weights must sum to 1.0" error

**Symptoms**: Service crashes on startup

**Cause**: Scoring weights misconfigured

**Solution**:
```bash
# Verify weights sum to 1.0
# SCORING_ROLE_WEIGHT + SCORING_TOPIC_WEIGHT + 
# SCORING_SERVICE_WEIGHT + SCORING_DOCUMENT_WEIGHT = 1.0

# Example: Default values (correct)
SCORING_ROLE_WEIGHT=0.30
SCORING_TOPIC_WEIGHT=0.40
SCORING_SERVICE_WEIGHT=0.20
SCORING_DOCUMENT_WEIGHT=0.10
# Sum: 0.30 + 0.40 + 0.20 + 0.10 = 1.0 ✅
```

---

## 📊 Configuration Summary

### Quick Reference

| Configuration | Development | Test | Staging | Production |
|---------------|-------------|------|---------|------------|
| **Port** | 5160 | 5160 | 5160 | 5160 |
| **Log Level** | DEBUG | WARNING | INFO | INFO |
| **Timeout** | 30s | 10s | 60s | 60s |
| **Pool Size** | 10 | 5 | 50 | 50 |
| **Cache TTL** | 60s | 0s | 300s | 300s |
| **Retries** | 3 | 1 | 5 | 5 |

---

**Last Updated**: October 10, 2025  
**Maintainer**: Hackathon Team  
**Questions**: See [README.md](./README.md) or contact team

