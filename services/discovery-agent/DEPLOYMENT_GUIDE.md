# Discovery Agent - Deployment Guide

**Service**: discovery-agent v2.0.0  
**Date**: October 9, 2025  
**Architecture**: DDD + Clean Architecture  
**Quality**: A+  
**Test Coverage**: 80%+

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Configuration](#configuration)
3. [Docker Deployment](#docker-deployment)
4. [Docker Compose Deployment](#docker-compose-deployment)
5. [Local Development](#local-development)
6. [Health Checks](#health-checks)
7. [Troubleshooting](#troubleshooting)
8. [Monitoring](#monitoring)

---

## 🎯 Prerequisites

### **System Requirements**

- **Docker**: 20.10+ (recommended)
- **Docker Compose**: 2.0+ (for multi-service)
- **Python**: 3.11+ (for local development)
- **curl**: For health checks

### **Network Requirements**

| Port | Purpose | Required |
|------|---------|----------|
| 5050 | HTTP API | ✅ Yes |
| 5051 | Internal | Optional |

### **Service Dependencies**

| Service | Required | Purpose |
|---------|----------|---------|
| orchestrator (5099) | ✅ Critical | Service/tool registration |
| log-collector (5060) | ⚠️  Optional | Centralized logging |
| Target services | Per request | Services to discover |

---

## ⚙️ Configuration

### **Environment Variables**

Create a `.env` file:

```bash
# Service Configuration
SERVICE_NAME=discovery-agent
SERVICE_API_PORT=5050
SERVICE_INTERNAL_PORT=5051
SERVER_API_HOST=0.0.0.0
ENVIRONMENT=production

# External Services
ORCHESTRATOR_URL=http://orchestrator:5099
LOG_COLLECTOR_URL=http://log-collector:5060

# Timeouts (seconds)
SERVICE_DISCOVERY_TIMEOUT=30.0
HEALTH_CHECK_TIMEOUT=5.0
TOOL_REGISTRATION_TIMEOUT=3.0
ENDPOINT_VALIDATION_TIMEOUT=3.0

# Python Configuration
PYTHONPATH=/app
PYTHONUNBUFFERED=1
```

### **config.yaml**

The service uses `config.yaml` for configuration:

```yaml
server:
  port: 5050
  internal_port: 5051
  host: 0.0.0.0

orchestrator:
  url: ${ORCHESTRATOR_URL:-http://orchestrator:5099}

timeouts:
  service_discovery: ${SERVICE_DISCOVERY_TIMEOUT:-30.0}
  health_check: ${HEALTH_CHECK_TIMEOUT:-5.0}
  tool_registration: ${TOOL_REGISTRATION_TIMEOUT:-3.0}
  endpoint_validation: ${ENDPOINT_VALIDATION_TIMEOUT:-3.0}
```

---

## 🐳 Docker Deployment

### **Step 1: Build the Image**

```bash
cd services/discovery-agent

# Build the image
docker build -t discovery-agent:2.0.0 .

# Verify build
docker images | grep discovery-agent
```

### **Step 2: Run the Container**

```bash
# Run with default configuration
docker run -d \
  --name discovery-agent \
  -p 5050:5050 \
  -p 5051:5051 \
  -e ORCHESTRATOR_URL=http://orchestrator:5099 \
  -e LOG_COLLECTOR_URL=http://log-collector:5060 \
  discovery-agent:2.0.0

# Run with environment file
docker run -d \
  --name discovery-agent \
  -p 5050:5050 \
  -p 5051:5051 \
  --env-file .env \
  discovery-agent:2.0.0
```

### **Step 3: Verify Deployment**

```bash
# Check container status
docker ps | grep discovery-agent

# Check logs
docker logs discovery-agent

# Check health
curl http://localhost:5050/health
```

### **Step 4: Stop and Remove**

```bash
# Stop container
docker stop discovery-agent

# Remove container
docker rm discovery-agent

# Remove image (if needed)
docker rmi discovery-agent:2.0.0
```

---

## 🚀 Docker Compose Deployment

### **Step 1: Review docker-compose.yml**

The `docker-compose.yml` includes:
- Discovery-agent service
- Orchestrator dependency
- Log-collector (optional)
- Network configuration
- Health checks
- Resource limits

### **Step 2: Deploy with Docker Compose**

```bash
# Start all services
docker-compose up -d

# Start specific service
docker-compose up -d discovery-agent

# View logs
docker-compose logs -f discovery-agent

# Check status
docker-compose ps
```

### **Step 3: Verify Deployment**

```bash
# Health check
curl http://localhost:5050/health

# Service info
curl http://localhost:5050/about-me

# Endpoints
curl http://localhost:5050/endpoints

# Interactive docs
open http://localhost:5050/docs
```

### **Step 4: Stop Services**

```bash
# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Stop but keep volumes
docker-compose stop
```

---

## 💻 Local Development

### **Step 1: Install Dependencies**

```bash
cd services/discovery-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install production dependencies
pip install -r requirements.txt

# Install test dependencies
pip install -r requirements-test.txt
```

### **Step 2: Run the Service**

```bash
# Option 1: Run with uvicorn
uvicorn main:app --host 0.0.0.0 --port 5050 --reload

# Option 2: Run with Python
python main.py

# Option 3: Run with specific config
SERVICE_API_PORT=5050 python main.py
```

### **Step 3: Run Tests**

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html --cov-report=term-missing

# Run specific test categories
pytest tests/unit/ -v           # Unit tests
pytest tests/integration/ -v    # Integration tests
pytest tests/e2e/ -v            # E2E tests
pytest tests/workflow/ -v       # Workflow tests

# Run by marker
pytest -m unit -v               # Unit tests
pytest -m api -v                # API tests
pytest -m discovery -v          # Discovery tests
```

### **Step 4: Development Workflow**

```bash
# Code quality checks
black domain/ application/ infrastructure/ presentation/
pylint domain/ application/ infrastructure/ presentation/
mypy domain/ application/ infrastructure/ presentation/

# Run linting
flake8 domain/ application/ infrastructure/ presentation/

# Security check
bandit -r domain/ application/ infrastructure/ presentation/
```

---

## 🏥 Health Checks

### **Standard Health Check**

```bash
# Basic health check
curl http://localhost:5050/health

# Expected response:
{
  "status": "healthy",
  "service": "discovery-agent",
  "version": "2.0.0",
  "timestamp": "2025-10-09T12:00:00+00:00",
  "uptime_seconds": 3600
}
```

### **Comprehensive Status Check**

```bash
# Service info
curl http://localhost:5050/about-me | jq .

# All endpoints
curl http://localhost:5050/endpoints | jq .

# Provider-consumer relationships
curl http://localhost:5050/provider-consumer | jq .
```

### **Automated Health Monitoring**

```bash
# Health check script
#!/bin/bash
while true; do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5050/health)
  if [ $STATUS -eq 200 ]; then
    echo "✅ Service healthy"
  else
    echo "❌ Service unhealthy (HTTP $STATUS)"
  fi
  sleep 30
done
```

---

## 🔧 Troubleshooting

### **Common Issues**

#### **Issue 1: Port Already in Use**

```bash
# Check what's using the port
lsof -i :5050

# Kill the process
kill -9 <PID>

# Or use different port
SERVICE_API_PORT=5052 python main.py
```

#### **Issue 2: Orchestrator Not Reachable**

```bash
# Check orchestrator status
curl http://orchestrator:5099/health

# Check network connectivity
docker network ls
docker network inspect hackathon_network

# Verify environment variable
echo $ORCHESTRATOR_URL
```

#### **Issue 3: Container Fails Health Check**

```bash
# Check logs
docker logs discovery-agent

# Check health check endpoint
docker exec discovery-agent curl http://localhost:5050/health

# Increase start_period in docker-compose.yml
healthcheck:
  start_period: 60s  # Increase if needed
```

#### **Issue 4: Import Errors**

```bash
# Verify Python path
docker exec discovery-agent env | grep PYTHONPATH

# Check if files exist
docker exec discovery-agent ls -la /app

# Reinstall dependencies
docker exec discovery-agent pip install -r requirements.txt
```

### **Debug Mode**

```bash
# Run with debug logging
docker run -d \
  --name discovery-agent \
  -p 5050:5050 \
  -e LOG_LEVEL=DEBUG \
  discovery-agent:2.0.0

# Or for local development
uvicorn main:app --host 0.0.0.0 --port 5050 --log-level debug
```

### **Logs Analysis**

```bash
# View logs
docker logs discovery-agent

# Follow logs
docker logs -f discovery-agent

# Last 100 lines
docker logs --tail 100 discovery-agent

# With timestamps
docker logs -t discovery-agent
```

---

## 📊 Monitoring

### **Metrics Endpoints**

```bash
# Service health
curl http://localhost:5050/health

# Service metrics
curl http://localhost:5050/about-me

# Endpoint catalog
curl http://localhost:5050/endpoints
```

### **Resource Monitoring**

```bash
# Docker stats
docker stats discovery-agent

# Container inspect
docker inspect discovery-agent

# Resource usage
docker exec discovery-agent ps aux
docker exec discovery-agent df -h
```

### **Log Monitoring**

Logs are sent to log-collector service:
```bash
# Check log-collector
curl http://log-collector:5060/api/v1/logs?service=discovery-agent
```

---

## 🚀 Production Deployment Checklist

### **Pre-Deployment**

- [ ] All tests passing (133 tests)
- [ ] Code quality checks passed
- [ ] Documentation up-to-date
- [ ] Environment variables configured
- [ ] Orchestrator service available
- [ ] Port 5050-5051 available
- [ ] Docker image built and tagged

### **Deployment**

- [ ] Deploy orchestrator first
- [ ] Deploy discovery-agent
- [ ] Verify health checks
- [ ] Check service registration
- [ ] Validate discovery functionality
- [ ] Check logs for errors

### **Post-Deployment**

- [ ] Monitor health endpoint
- [ ] Check log-collector integration
- [ ] Verify orchestrator registration
- [ ] Test discovery endpoints
- [ ] Monitor resource usage
- [ ] Set up alerting

---

## 📚 Additional Resources

- [README.md](./README.md) - Service documentation
- [CONFIG.md](./CONFIG.md) - Configuration guide
- [tests/README.md](./tests/README.md) - Test documentation
- [API Docs](http://localhost:5050/docs) - Interactive API documentation

---

## 🆘 Support

### **Getting Help**

1. Check logs: `docker logs discovery-agent`
2. Review troubleshooting section above
3. Check health endpoint: `curl http://localhost:5050/health`
4. Review service documentation

### **Common Commands Quick Reference**

```bash
# Start service
docker-compose up -d discovery-agent

# Stop service
docker-compose stop discovery-agent

# Restart service
docker-compose restart discovery-agent

# View logs
docker-compose logs -f discovery-agent

# Health check
curl http://localhost:5050/health

# Interactive docs
open http://localhost:5050/docs
```

---

**Last Updated**: October 9, 2025  
**Version**: 2.0.0  
**Status**: Production Ready  
**Quality**: A+

