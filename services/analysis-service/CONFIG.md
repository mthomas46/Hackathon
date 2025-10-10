# analysis-service: Configuration Guide

**Service**: analysis-service  
**Version**: 1.0.0  
**Type**: Core Analysis Engine  
**Tier**: 1 (Critical)  

---

## 📋 **Table of Contents**

1. [Service Overview](#service-overview)
2. [Configuration Files](#configuration-files)
3. [Environment Variables](#environment-variables)
4. [Port Configuration](#port-configuration)
5. [Dependencies & Services](#dependencies--services)
6. [API Keys & Credentials](#api-keys--credentials)
7. [Configuration Profiles](#configuration-profiles)
8. [Docker Configuration](#docker-configuration)
9. [CI/CD & Deployment](#cicd--deployment)
10. [Scripts & Makefiles](#scripts--makefiles)
11. [Validation & Testing](#validation--testing)

---

## 🎯 **Service Overview**

The **analysis-service** is the core analysis engine of the LLM Documentation Ecosystem, providing comprehensive document analysis, consistency checking, quality assessment, and trend analysis capabilities.

### Key Capabilities:
- Document consistency analysis
- Semantic similarity detection
- Sentiment and tone analysis
- Content quality assessment
- Trend analysis and forecasting
- Risk assessment
- Automated remediation
- Distributed processing
- Report generation

---

## 📁 **Configuration Files**

### Primary Configuration:
```
services/analysis-service/
├── .env                    # Environment variables (not in repo)
├── .env.example            # Example environment variables
├── config.yaml             # Service-specific configuration
├── docker-compose.yml      # Docker Compose for local dev
├── Dockerfile              # Container image definition
└── requirements.txt        # Python dependencies
```

### Configuration Priority (highest to lowest):
1. Environment variables (`.env`)
2. Config files (`config.yaml`)
3. Default values (hardcoded)

---

## 🔧 **Environment Variables**

### Required:
```bash
# Service Configuration
SERVICE_NAME=analysis-service
SERVICE_VERSION=1.0.0
SERVICE_PORT=8003
SERVICE_HOST=0.0.0.0

# Redis (Required for distributed processing)
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

# Doc Store (Required)
DOC_STORE_URL=http://doc-store:8001
```

### Optional:
```bash
# Prompt Store
PROMPT_STORE_URL=http://prompt-store:8002

# Interpreter
INTERPRETER_URL=http://interpreter:8004

# Source Agent
SOURCE_AGENT_URL=http://source-agent:8005

# Orchestrator
ORCHESTRATOR_URL=http://orchestrator:8006

# Log Collector
LOG_COLLECTOR_URL=http://log-collector:8010
LOG_LEVEL=INFO

# AWS Bedrock (Optional - for AI-powered analysis)
AWS_ACCESS_KEY_ID=your_key_id
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0

# Analysis Configuration
MAX_WORKERS=4
ENABLE_DISTRIBUTED=true
ENABLE_AUTO_SCALING=true
MAX_QUEUE_SIZE=1000
ANALYSIS_TIMEOUT=300

# Feature Flags
ENABLE_SEMANTIC_SIMILARITY=true
ENABLE_AI_ANALYSIS=false
ENABLE_AUTOMATED_REMEDIATION=true
ENABLE_WORKFLOW_INTEGRATION=true

# Performance Tuning
CACHE_TTL=3600
MAX_CONCURRENT_ANALYSES=10
BATCH_SIZE=50
```

---

## 🌐 **Port Configuration**

### Service Ports:

| Service | Port | Purpose | Status |
|---------|------|---------|--------|
| analysis-service | 8003 | Main HTTP API | Primary |
| Redis | 6379 | Cache & Queue | Required |
| doc-store | 8001 | Document storage | Required |
| prompt-store | 8002 | Prompt templates | Optional |
| interpreter | 8004 | NL queries | Optional |
| source-agent | 8005 | Source code | Optional |
| orchestrator | 8006 | Workflow coord | Optional |
| log-collector | 8010 | Centralized logs | Optional |

### Port Conflict Resolution:
If port 8003 is in use, set `SERVICE_PORT` environment variable:
```bash
SERVICE_PORT=8103 python main.py
```

---

## 🔗 **Dependencies & Services**

### Critical Dependencies (Required):
1. **Redis**
   - Purpose: Distributed task queue, caching
   - Configuration: `REDIS_HOST`, `REDIS_PORT`
   - Startup: Must be available before service starts
   - Health check: `redis-cli ping`

2. **doc-store**
   - Purpose: Document storage and retrieval
   - Configuration: `DOC_STORE_URL`
   - Startup: Required for most analysis operations
   - Health check: `GET {DOC_STORE_URL}/health`

### Optional Dependencies:
3. **prompt-store** - Prompt template management
4. **interpreter** - Natural language query processing
5. **source-agent** - Source code and repository data
6. **orchestrator** - Workflow coordination
7. **log-collector** - Centralized logging
8. **AWS Bedrock** - AI-powered analysis features

### Dependency Startup Order:
```
1. Redis (required)
2. doc-store (required)
3. analysis-service
4. Other services (optional)
```

---

## 🔐 **API Keys & Credentials**

### AWS Bedrock (Optional):
```bash
# Required for AI-powered analysis features
AWS_ACCESS_KEY_ID=your_access_key_id
AWS_SECRET_ACCESS_KEY=your_secret_access_key
AWS_DEFAULT_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
```

**Note**: AI-powered features are optional and the service runs fully without AWS credentials.

### Service Authentication:
The analysis-service does not require authentication by default. To enable:
```bash
ENABLE_AUTH=true
AUTH_TOKEN_SECRET=your_secret_key
```

---

## 🎛️ **Configuration Profiles**

### Development Profile:
```yaml
# config.dev.yaml
service:
  name: analysis-service
  port: 8003
  debug: true
  log_level: DEBUG

analysis:
  max_workers: 2
  enable_distributed: false
  cache_ttl: 60

features:
  enable_ai_analysis: false
  enable_distributed: false
```

### Test Profile:
```yaml
# config.test.yaml
service:
  name: analysis-service-test
  port: 8103
  log_level: WARNING

analysis:
  max_workers: 1
  enable_distributed: false
  use_mock_data: true
```

### Staging Profile:
```yaml
# config.staging.yaml
service:
  name: analysis-service
  port: 8003
  log_level: INFO

analysis:
  max_workers: 4
  enable_distributed: true
  enable_auto_scaling: true
  max_queue_size: 500
```

### Production Profile:
```yaml
# config.prod.yaml
service:
  name: analysis-service
  port: 8003
  log_level: INFO

analysis:
  max_workers: 8
  enable_distributed: true
  enable_auto_scaling: true
  max_queue_size: 2000
  cache_ttl: 3600

features:
  enable_ai_analysis: true
  enable_distributed: true
  enable_monitoring: true
```

---

## 🐳 **Docker Configuration**

### Dockerfile Best Practices:
```dockerfile
# Multi-stage build for smaller images
FROM python:3.11-slim as builder
# Build dependencies...

FROM python:3.11-slim
# Runtime image
COPY --from=builder ...
```

### Docker Compose:
```yaml
version: '3.8'

services:
  analysis-service:
    build: .
    ports:
      - "8003:8003"
    environment:
      - SERVICE_PORT=8003
      - REDIS_HOST=redis
      - DOC_STORE_URL=http://doc-store:8001
    depends_on:
      - redis
      - doc-store
    networks:
      - ecosystem-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8003/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Docker Profiles:
```bash
# Development
docker-compose --profile dev up analysis-service

# Testing
docker-compose --profile test up analysis-service

# Production
docker-compose --profile prod up analysis-service
```

---

## 🚀 **CI/CD & Deployment**

### CI Pipeline (GitHub Actions):
```yaml
name: analysis-service CI/CD

on:
  push:
    branches: [main, develop]
    paths:
      - 'services/analysis-service/**'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: |
          cd services/analysis-service
          pip install -r requirements.txt
          pytest tests/ --cov=. --cov-report=term

  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run linters
        run: |
          cd services/analysis-service
          black --check .
          pylint **/*.py
          mypy .

  build:
    runs-on: ubuntu-latest
    needs: [test, lint]
    steps:
      - uses: actions/checkout@v2
      - name: Build Docker image
        run: docker build -t analysis-service:latest services/analysis-service/

  deploy:
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Deploy to production
        run: |
          # Deployment steps...
```

### Deployment Strategies:

**1. Blue-Green Deployment:**
```bash
# Deploy new version (green)
docker-compose up -d analysis-service-green

# Switch traffic
# Update load balancer to green

# Decommission old (blue)
docker-compose down analysis-service-blue
```

**2. Rolling Update:**
```bash
# Update workers one at a time
for worker in worker-1 worker-2 worker-3 worker-4; do
  docker-compose up -d --no-deps --scale $worker=0
  sleep 30
  docker-compose up -d --no-deps --scale $worker=1
done
```

**3. Canary Deployment:**
```bash
# Deploy canary (10% traffic)
docker-compose up -d analysis-service-canary

# Monitor metrics
# If successful, full deployment
docker-compose up -d analysis-service
```

---

## 🛠️ **Scripts & Makefiles**

### Makefile Commands:
```makefile
# Development
make dev          # Run in development mode
make test         # Run all tests
make lint         # Run linters
make format       # Format code

# Docker
make build        # Build Docker image
make up           # Start services
make down         # Stop services
make logs         # View logs

# Database
make db-migrate   # Run migrations
make db-seed      # Seed test data

# Deployment
make deploy-dev   # Deploy to development
make deploy-prod  # Deploy to production
```

### Common Scripts:
```bash
# scripts/start.sh - Start service
./scripts/start.sh --env=dev

# scripts/test.sh - Run tests
./scripts/test.sh --coverage

# scripts/validate-config.sh - Validate configuration
./scripts/validate-config.sh config.yaml

# scripts/health-check.sh - Health check
./scripts/health-check.sh http://localhost:8003
```

---

## ✅ **Validation & Testing**

### Preflight Checks:
```bash
# 1. Validate configuration
python -m pytest tests/test_config.py

# 2. Check dependencies
./scripts/check-dependencies.sh

# 3. Validate Docker setup
docker-compose config

# 4. Run health checks
curl http://localhost:8003/health

# 5. Test standard endpoints
curl http://localhost:8003/about-me
curl http://localhost:8003/endpoints
curl http://localhost:8003/provider-consumer
```

### Configuration Validation:
```python
# tests/test_config.py
def test_required_env_vars():
    assert os.getenv('SERVICE_PORT')
    assert os.getenv('REDIS_HOST')
    assert os.getenv('DOC_STORE_URL')

def test_port_available():
    port = int(os.getenv('SERVICE_PORT', 8003))
    assert is_port_available(port)

def test_redis_connection():
    redis_client = redis.Redis(
        host=os.getenv('REDIS_HOST'),
        port=int(os.getenv('REDIS_PORT', 6379))
    )
    assert redis_client.ping()
```

---

## 📊 **Configuration Matrix**

| Config Item | Dev | Test | Staging | Prod |
|-------------|-----|------|---------|------|
| Log Level | DEBUG | WARN | INFO | INFO |
| Workers | 2 | 1 | 4 | 8 |
| Distributed | No | No | Yes | Yes |
| Auto-scale | No | No | Yes | Yes |
| Cache TTL | 60s | 0s | 600s | 3600s |
| AI Features | No | Mock | Yes | Yes |
| Monitoring | Basic | None | Full | Full |

---

## 🔍 **Troubleshooting**

### Common Issues:

**1. Port Already in Use:**
```bash
# Check what's using the port
lsof -i :8003

# Use different port
SERVICE_PORT=8103 python main.py
```

**2. Redis Connection Failed:**
```bash
# Check Redis is running
docker-compose ps redis

# Test connection
redis-cli -h redis -p 6379 ping
```

**3. Import Errors:**
```bash
# Ensure PYTHONPATH is set
export PYTHONPATH=/app:$PYTHONPATH
```

**4. Memory Issues:**
```bash
# Reduce workers
MAX_WORKERS=2 python main.py
```

---

## 📝 **Configuration Checklist**

Before deployment:
- [ ] All required environment variables set
- [ ] Redis is accessible
- [ ] doc-store is accessible
- [ ] Port is available
- [ ] Docker image builds successfully
- [ ] Health endpoint returns 200
- [ ] All tests pass
- [ ] Configuration validated
- [ ] Logs are being collected
- [ ] Monitoring is configured

---

## 📚 **Related Documentation**

- [README.md](README.md) - Service overview and quickstart
- [PHASE_2_COMPLETE.md](PHASE_2_COMPLETE.md) - Refactoring details
- [Master Refactoring Plan](../../docs/refactoring/MASTER_REFACTORING_PLAN.md)

---

**Last Updated**: 2025-10-10  
**Maintainer**: DevOps Team  
**Status**: Production-Ready ✅

