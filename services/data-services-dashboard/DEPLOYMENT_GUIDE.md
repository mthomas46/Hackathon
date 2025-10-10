# Deployment Guide - Data Services Dashboard

**Service**: data-services-dashboard  
**Version**: 1.0.0  
**Last Updated**: October 9, 2025

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Local Development](#local-development)
4. [Docker Deployment](#docker-deployment)
5. [Production Deployment](#production-deployment)
6. [Health Checks](#health-checks)
7. [Monitoring](#monitoring)
8. [Troubleshooting](#troubleshooting)
9. [Rollback](#rollback)

---

## 🎯 Overview

This guide covers deploying the Data Services Dashboard in various environments:

- **Local Development** - For development and testing
- **Docker** - Containerized deployment
- **Production** - Production-ready deployment

**Deployment Model**: **Hybrid Service** (Streamlit UI + FastAPI REST API in single container)

---

## 📋 Prerequisites

### **System Requirements**

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **Python** | 3.12+ | 3.12+ |
| **RAM** | 512MB | 1GB |
| **CPU** | 1 core | 2 cores |
| **Disk** | 100MB | 500MB |

### **Dependencies**

#### **Required Services**

| Service | Port | Purpose | Criticality |
|---------|------|---------|-------------|
| **log-collector** | 8104 | Operation logs | **Critical** |

#### **Required Packages**

```bash
# Production dependencies
pip install -r requirements.txt

# Test dependencies (optional)
pip install -r requirements-test.txt
```

---

## 💻 Local Development

### **Quick Start**

```bash
# 1. Clone repository
cd /Users/mykalthomas/Documents/work/Hackathon/services/data-services-dashboard

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment (optional)
cp .env.example .env
# Edit .env with your settings

# 4. Run dashboard
streamlit run app.py
```

**Access**:
- **Streamlit UI**: http://localhost:8501
- **FastAPI API**: http://localhost:8080
- **API Docs**: http://localhost:8080/docs

### **Development with Live Reload**

Streamlit automatically reloads on code changes:

```bash
streamlit run app.py --server.runOnSave=true
```

### **Running Tests**

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=./ --cov-report=html

# Run specific test category
pytest -m unit
pytest -m integration
pytest -m api
```

---

## 🐳 Docker Deployment

### **Build Docker Image**

```bash
# Build image
docker build -t data-services-dashboard:1.0.0 .

# Tag for registry (optional)
docker tag data-services-dashboard:1.0.0 registry.example.com/data-services-dashboard:1.0.0
```

### **Run Container**

```bash
docker run -d \
  --name data-services-dashboard \
  -p 8501:8501 \
  -p 8080:8080 \
  -e DASHBOARD_LOG_COLLECTOR_URL=http://log-collector:8104 \
  -e DASHBOARD_CACHE_TTL=30 \
  -e DASHBOARD_ENVIRONMENT=production \
  data-services-dashboard:1.0.0
```

### **Docker Compose**

#### **Standalone**

```yaml
# docker-compose.yml
version: '3.8'

services:
  data-services-dashboard:
    build: .
    image: data-services-dashboard:1.0.0
    container_name: data-services-dashboard
    
    ports:
      - "8501:8501"  # Streamlit UI
      - "8080:8080"  # FastAPI API
    
    environment:
      DASHBOARD_UI_PORT: 8501
      DASHBOARD_API_PORT: 8080
      DASHBOARD_LOG_COLLECTOR_URL: http://log-collector:8104
      DASHBOARD_CACHE_TTL: 30
      DASHBOARD_ENVIRONMENT: production
      DASHBOARD_DEBUG: false
    
    volumes:
      - ./logs:/app/logs
    
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    
    restart: unless-stopped
    
    networks:
      - hackathon_default

networks:
  hackathon_default:
    driver: bridge
```

#### **With Dependencies**

```yaml
# docker-compose.yml
version: '3.8'

services:
  log-collector:
    image: log-collector:latest
    ports:
      - "8104:8104"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8104/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - hackathon_default

  data-services-dashboard:
    build: .
    image: data-services-dashboard:1.0.0
    container_name: data-services-dashboard
    
    ports:
      - "8501:8501"
      - "8080:8080"
    
    environment:
      DASHBOARD_LOG_COLLECTOR_URL: http://log-collector:8104
      DASHBOARD_ENVIRONMENT: production
    
    depends_on:
      log-collector:
        condition: service_healthy
    
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    
    restart: unless-stopped
    
    networks:
      - hackathon_default

networks:
  hackathon_default:
    driver: bridge
```

**Start Services**:

```bash
docker-compose up -d
```

**View Logs**:

```bash
docker-compose logs -f data-services-dashboard
```

**Stop Services**:

```bash
docker-compose down
```

---

## 🚀 Production Deployment

### **Deployment Checklist**

- [ ] **Environment Configuration**
  - [ ] Set `DASHBOARD_ENVIRONMENT=production`
  - [ ] Set `DASHBOARD_DEBUG=false`
  - [ ] Configure production URLs
  - [ ] Set optimal cache TTL (30-60s)

- [ ] **Security**
  - [ ] Use HTTPS for log-collector URL
  - [ ] Configure firewall rules
  - [ ] Set up network isolation
  - [ ] Implement API authentication (if needed)

- [ ] **Performance**
  - [ ] Set cache TTL based on load (30-60s)
  - [ ] Configure retry attempts (3-5)
  - [ ] Set appropriate timeouts
  - [ ] Enable connection pooling

- [ ] **Monitoring**
  - [ ] Set up health check monitoring
  - [ ] Configure log aggregation
  - [ ] Set up alerting
  - [ ] Monitor resource usage

- [ ] **Dependencies**
  - [ ] Verify log-collector is running
  - [ ] Test connectivity to all services
  - [ ] Verify network routing

### **Production Environment Variables**

```bash
# Production .env
DASHBOARD_SERVICE_NAME=data-services-dashboard
DASHBOARD_SERVICE_VERSION=1.0.0
DASHBOARD_ENVIRONMENT=production
DASHBOARD_DEBUG=false

# Ports
DASHBOARD_UI_PORT=8501
DASHBOARD_API_PORT=8080

# External Services (use HTTPS in production)
DASHBOARD_LOG_COLLECTOR_URL=https://log-collector.prod.internal:8104

# Performance
DASHBOARD_CACHE_TTL=30
DASHBOARD_HTTP_TIMEOUT=5.0

# Retry Logic (increase for production reliability)
DASHBOARD_MAX_RETRY_ATTEMPTS=5
DASHBOARD_RETRY_DELAY=2.0
DASHBOARD_RETRY_BACKOFF=2.0
```

### **Production Dockerfile**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY api/ ./api/
COPY data/ ./data/
COPY metrics/ ./metrics/
COPY visualization/ ./visualization/
COPY utils/ ./utils/
COPY app.py .
COPY config.py .

# Create directories
RUN mkdir -p /app/logs

# Set environment
ENV PYTHONPATH=/app
ENV DASHBOARD_ENVIRONMENT=production
ENV DASHBOARD_DEBUG=false

# Create non-root user
RUN useradd -m -u 1000 dashboard && chown -R dashboard:dashboard /app
USER dashboard

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Expose ports
EXPOSE 8501 8080

# Start command (hybrid: both Streamlit + FastAPI)
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### **Kubernetes Deployment** (Optional)

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: data-services-dashboard
  labels:
    app: data-services-dashboard
spec:
  replicas: 2
  selector:
    matchLabels:
      app: data-services-dashboard
  template:
    metadata:
      labels:
        app: data-services-dashboard
    spec:
      containers:
      - name: dashboard
        image: registry.example.com/data-services-dashboard:1.0.0
        ports:
        - containerPort: 8501
          name: ui
        - containerPort: 8080
          name: api
        env:
        - name: DASHBOARD_ENVIRONMENT
          value: "production"
        - name: DASHBOARD_LOG_COLLECTOR_URL
          value: "http://log-collector:8104"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 60
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 10
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"

---
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: data-services-dashboard
spec:
  selector:
    app: data-services-dashboard
  ports:
  - name: ui
    port: 8501
    targetPort: 8501
  - name: api
    port: 8080
    targetPort: 8080
  type: LoadBalancer
```

---

## ✅ Health Checks

### **Liveness Probe** (Is the service running?)

```bash
# Check API health
curl http://localhost:8080/health

# Expected response:
{
  "status": "healthy",
  "service": "data-services-dashboard",
  "uptime_seconds": 3600
}
```

### **Readiness Probe** (Is the service ready to accept traffic?)

```bash
# Check log-collector connectivity
curl http://localhost:8080/health | jq '.dependencies.log_collector'

# Should return "connected"
```

### **Startup Probe** (Has the service finished starting?)

```bash
# Wait for service to start
timeout 60 bash -c 'until curl -f http://localhost:8080/health; do sleep 2; done'
```

### **Health Check Script**

```bash
#!/bin/bash
# healthcheck.sh

UI_PORT=${DASHBOARD_UI_PORT:-8501}
API_PORT=${DASHBOARD_API_PORT:-8080}

# Check API
if ! curl -f http://localhost:$API_PORT/health > /dev/null 2>&1; then
  echo "❌ API health check failed"
  exit 1
fi

# Check log-collector connectivity
LOG_COLLECTOR_STATUS=$(curl -s http://localhost:$API_PORT/health | jq -r '.dependencies.log_collector')
if [ "$LOG_COLLECTOR_STATUS" != "connected" ]; then
  echo "⚠️  Log-collector disconnected"
  # Don't fail - dashboard continues to work
fi

echo "✅ Health check passed"
exit 0
```

---

## 📊 Monitoring

### **Metrics to Monitor**

| Metric | Endpoint | Threshold | Action |
|--------|----------|-----------|--------|
| **Health Status** | `/health` | `status != "healthy"` | Alert & investigate |
| **Uptime** | `/health` | `uptime_seconds` | Track availability |
| **Log-Collector** | `/health` | `dependencies.log_collector != "connected"` | Check log-collector |
| **Response Time** | All endpoints | `> 5s` | Investigate performance |

### **Monitoring Script**

```bash
#!/bin/bash
# monitor.sh

API_URL="http://localhost:8080"

while true; do
  # Get health status
  HEALTH=$(curl -s $API_URL/health)
  STATUS=$(echo $HEALTH | jq -r '.status')
  UPTIME=$(echo $HEALTH | jq -r '.uptime_seconds')
  LOG_COLLECTOR=$(echo $HEALTH | jq -r '.dependencies.log_collector')
  
  echo "[$(date)] Status: $STATUS, Uptime: ${UPTIME}s, Log-Collector: $LOG_COLLECTOR"
  
  # Alert if unhealthy
  if [ "$STATUS" != "healthy" ]; then
    echo "❌ ALERT: Dashboard is unhealthy!"
    # Send alert (e.g., PagerDuty, Slack, email)
  fi
  
  sleep 60  # Check every minute
done
```

### **Log Monitoring**

```bash
# View logs
docker logs -f data-services-dashboard

# Filter errors
docker logs data-services-dashboard 2>&1 | grep ERROR

# View last 100 lines
docker logs --tail 100 data-services-dashboard
```

---

## 🐛 Troubleshooting

### **Service Won't Start**

**Symptoms**: Container exits immediately

**Diagnosis**:
```bash
docker logs data-services-dashboard
```

**Common Causes**:
1. Port already in use
2. Missing dependencies
3. Configuration errors

**Solutions**:
```bash
# Check port availability
lsof -i :8501
lsof -i :8080

# Check configuration
docker exec data-services-dashboard python -c "from config import config; print(config.model_dump())"

# Restart with verbose logging
docker-compose up data-services-dashboard
```

### **Can't Connect to Log-Collector**

**Symptoms**: Dashboard shows "Log Collector: Disconnected"

**Diagnosis**:
```bash
# Check log-collector is running
docker ps | grep log-collector

# Check connectivity
docker exec data-services-dashboard curl http://log-collector:8104/health
```

**Solutions**:
```bash
# Verify log-collector URL
echo $DASHBOARD_LOG_COLLECTOR_URL

# Check Docker network
docker network inspect hackathon_default

# Restart log-collector
docker-compose restart log-collector
```

### **Slow Dashboard Performance**

**Symptoms**: Dashboard takes > 5s to load

**Diagnosis**:
```bash
# Check cache TTL
docker exec data-services-dashboard env | grep CACHE_TTL

# Check log volume
curl http://localhost:8104/logs?limit=1000
```

**Solutions**:
```bash
# Increase cache TTL
export DASHBOARD_CACHE_TTL=60

# Reduce time range in dashboard
# Use "Last 100 operations" instead of "Last 1000"

# Check log-collector performance
curl http://localhost:8104/health
```

---

## 🔄 Rollback

### **Rollback to Previous Version**

```bash
# Stop current version
docker-compose down

# Deploy previous version
docker run -d \
  --name data-services-dashboard \
  -p 8501:8501 \
  -p 8080:8080 \
  data-services-dashboard:0.9.0

# Verify health
curl http://localhost:8080/health
```

### **Database/State Rollback**

The dashboard is **stateless** - no database or persistent state to roll back.

---

## 📚 Additional Resources

- **[README.md](./README.md)** - Service overview
- **[CONFIG.md](./CONFIG.md)** - Configuration reference
- **[Master Refactoring Plan](../../docs/refactoring/MASTER_REFACTORING_PLAN.md)** - Ecosystem standards

---

**Deployment Guide Version**: 1.0.0  
**Last Updated**: October 9, 2025  
**Status**: Production Ready

