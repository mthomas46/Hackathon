# 🐳 Docker Deployment Guide

## Overview

This guide covers containerized deployment of the Unified API Dashboard using Docker and related orchestration tools.

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- 4GB RAM minimum, 8GB recommended
- 10GB free disk space

## Quick Start with Docker Compose

### Basic Development Setup

```yaml
# docker-compose.yml
version: '3.8'

services:
  dashboard:
    build: .
    ports:
      - "8000:8000"
    environment:
      - SERVICE_NAME=unified-api-dashboard
      - SERVICE_PORT=8000
      - REDIS_HOST=redis
      - ENVIRONMENT=development
    depends_on:
      - redis
    volumes:
      - ./config.yml:/app/config.yml:ro
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  redis_data:
```

### Production Docker Compose

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  dashboard:
    build:
      context: .
      dockerfile: Dockerfile.prod
    ports:
      - "8000:8000"
    environment:
      - SERVICE_NAME=unified-api-dashboard
      - SERVICE_PORT=8000
      - REDIS_HOST=redis
      - ENVIRONMENT=production
      - LOG_LEVEL=INFO
      - METRICS_ENABLED=true
    depends_on:
      redis:
        condition: service_healthy
    volumes:
      - ./config.prod.yml:/app/config.yml:ro
      - ./ssl:/app/ssl:ro
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 40s
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/ssl/certs:ro
    depends_on:
      - dashboard
    restart: unless-stopped

volumes:
  redis_data:
    driver: local
```

## Dockerfile Configurations

### Development Dockerfile

```dockerfile
# Dockerfile.dev
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd --create-home --shell /bin/bash app

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Change ownership
RUN chown -R app:app /app

# Switch to app user
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

### Production Dockerfile

```dockerfile
# Dockerfile.prod
# Multi-stage build for production

# Build stage
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd --create-home --shell /bin/bash --uid 1000 app

# Copy virtual environment
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Create app directory
WORKDIR /app

# Copy application code
COPY --chown=app:app . .

# Switch to app user
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

## Docker Compose with Microservices

### Full Ecosystem Setup

```yaml
# docker-compose.full.yml
version: '3.8'

services:
  # API Dashboard
  dashboard:
    build:
      context: .
      dockerfile: Dockerfile.prod
    ports:
      - "8000:8000"
    environment:
      - SERVICE_NAME=unified-api-dashboard
      - SERVICE_PORT=8000
      - REDIS_HOST=redis
      - ENVIRONMENT=production
      - DISCOVERY_AGENT_URL=http://discovery-agent:8080
    depends_on:
      - redis
      - discovery-agent
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 5
    restart: unless-stopped

  # Discovery Agent
  discovery-agent:
    image: your-registry/discovery-agent:latest
    environment:
      - SERVICE_PORT=8080
      - REDIS_HOST=redis
    ports:
      - "8080:8080"
    depends_on:
      - redis
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  # Redis Cache
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  # Example Microservices
  user-service:
    image: your-registry/user-service:latest
    environment:
      - SERVICE_PORT=8081
      - REDIS_HOST=redis
    ports:
      - "8081:8081"
    depends_on:
      - redis
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8081/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  order-service:
    image: your-registry/order-service:latest
    environment:
      - SERVICE_PORT=8082
      - REDIS_HOST=redis
    ports:
      - "8082:8082"
    depends_on:
      - redis
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8082/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  # Monitoring Stack
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=200h'
      - '--web.enable-lifecycle'
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning:ro
    depends_on:
      - prometheus
    restart: unless-stopped

volumes:
  redis_data:
  prometheus_data:
  grafana_data:
```

## Kubernetes Deployment

### Namespace and RBAC

```yaml
# k8s/namespace.yml
apiVersion: v1
kind: Namespace
metadata:
  name: api-dashboard
  labels:
    name: api-dashboard

---
# k8s/rbac.yml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: api-dashboard
  name: api-dashboard-role
rules:
- apiGroups: [""]
  resources: ["pods", "services", "endpoints", "configmaps", "secrets"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets"]
  verbs: ["get", "list", "watch"]

---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  namespace: api-dashboard
  name: api-dashboard-rolebinding
subjects:
- kind: ServiceAccount
  name: api-dashboard-sa
  namespace: api-dashboard
roleRef:
  kind: Role
  name: api-dashboard-role
  apiGroup: rbac.authorization.k8s.io

---
apiVersion: v1
kind: ServiceAccount
metadata:
  namespace: api-dashboard
  name: api-dashboard-sa
```

### ConfigMap and Secrets

```yaml
# k8s/configmap.yml
apiVersion: v1
kind: ConfigMap
metadata:
  namespace: api-dashboard
  name: api-dashboard-config
data:
  config.yml: |
    service:
      name: unified-api-dashboard
      version: "1.0.0"
      port: 8000

    redis:
      host: redis-service
      port: 6379

    discovery_agent:
      url: http://discovery-agent-service:8080

    security:
      jwt_secret_key: ${JWT_SECRET}
      audit_secret_key: ${AUDIT_SECRET}

    logging:
      level: INFO
      format: json

---
# k8s/secret.yml
apiVersion: v1
kind: Secret
metadata:
  namespace: api-dashboard
  name: api-dashboard-secrets
type: Opaque
data:
  # Base64 encoded secrets
  jwt-secret: <base64-encoded-jwt-secret>
  audit-secret: <base64-encoded-audit-secret>
  redis-password: <base64-encoded-redis-password>
```

### Deployment and Service

```yaml
# k8s/deployment.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  namespace: api-dashboard
  name: api-dashboard
  labels:
    app: api-dashboard
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api-dashboard
  template:
    metadata:
      labels:
        app: api-dashboard
    spec:
      serviceAccountName: api-dashboard-sa
      containers:
      - name: api-dashboard
        image: your-registry/unified-api-dashboard:latest
        ports:
        - containerPort: 8000
          name: http
        env:
        - name: SERVICE_PORT
          value: "8000"
        - name: REDIS_HOST
          value: "redis-service"
        - name: ENVIRONMENT
          value: "production"
        envFrom:
        - secretRef:
            name: api-dashboard-secrets
        volumeMounts:
        - name: config
          mountPath: /app/config.yml
          subPath: config.yml
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: config
        configMap:
          name: api-dashboard-config

---
# k8s/service.yml
apiVersion: v1
kind: Service
metadata:
  namespace: api-dashboard
  name: api-dashboard-service
  labels:
    app: api-dashboard
spec:
  selector:
    app: api-dashboard
  ports:
  - name: http
    port: 80
    targetPort: 8000
  type: ClusterIP

---
# k8s/ingress.yml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  namespace: api-dashboard
  name: api-dashboard-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - api-dashboard.your-domain.com
    secretName: api-dashboard-tls
  rules:
  - host: api-dashboard.your-domain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api-dashboard-service
            port:
              number: 80
```

### Redis Deployment

```yaml
# k8s/redis.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  namespace: api-dashboard
  name: redis
  labels:
    app: redis
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
        env:
        - name: REDIS_PASSWORD
          valueFrom:
            secretKeyRef:
              name: api-dashboard-secrets
              key: redis-password
        command: ["redis-server", "--requirepass", "$(REDIS_PASSWORD)"]
        volumeMounts:
        - name: redis-data
          mountPath: /data
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
        livenessProbe:
          exec:
            command: ["redis-cli", "ping"]
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          exec:
            command: ["redis-cli", "ping"]
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: redis-data
        persistentVolumeClaim:
          claimName: redis-pvc

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  namespace: api-dashboard
  name: redis-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
```

### Horizontal Pod Autoscaling

```yaml
# k8s/hpa.yml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  namespace: api-dashboard
  name: api-dashboard-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api-dashboard
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
      - type: Pods
        value: 2
        periodSeconds: 60
```

## Monitoring and Logging

### Prometheus Metrics

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  # - "first_rules.yml"
  # - "second_rules.yml"

scrape_configs:
  - job_name: 'api-dashboard'
    static_configs:
      - targets: ['api-dashboard-service:8000']
    scrape_interval: 5s
    metrics_path: '/metrics'

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-service:6379']
    scrape_interval: 30s

  - job_name: 'kubernetes-pods'
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
        action: replace
        target_label: __metrics_path__
        regex: (.+)
      - source_labels: [__address__, __meta_kubernetes_pod_annotation_prometheus_io_port]
        action: replace
        regex: ([^:]+)(?::\d+)?;(\d+)
        replacement: $1:$2
        target_label: __address__
      - action: labelmap
        regex: __meta_kubernetes_pod_label_(.+)
      - source_labels: [__meta_kubernetes_namespace]
        action: replace
        target_label: kubernetes_namespace
      - source_labels: [__meta_kubernetes_pod_name]
        action: replace
        target_label: kubernetes_pod_name
```

### Grafana Dashboard

```json
// monitoring/grafana/dashboard.json
{
  "dashboard": {
    "title": "API Dashboard Metrics",
    "tags": ["api", "dashboard"],
    "timezone": "browser",
    "panels": [
      {
        "title": "API Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(api_request_duration_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "title": "API Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(api_requests_total[5m])",
            "legendFormat": "Requests per second"
          }
        ]
      },
      {
        "title": "Service Health",
        "type": "table",
        "targets": [
          {
            "expr": "api_service_health",
            "legendFormat": "{{service}}"
          }
        ]
      }
    ]
  }
}
```

## Deployment Commands

### Docker Compose

```bash
# Development
docker-compose up -d

# Production
docker-compose -f docker-compose.prod.yml up -d

# Full ecosystem
docker-compose -f docker-compose.full.yml up -d

# View logs
docker-compose logs -f dashboard

# Scale services
docker-compose up -d --scale dashboard=3
```

### Kubernetes

```bash
# Create namespace
kubectl apply -f k8s/namespace.yml

# Deploy RBAC
kubectl apply -f k8s/rbac.yml

# Deploy ConfigMap and Secrets
kubectl apply -f k8s/configmap.yml
kubectl apply -f k8s/secret.yml

# Deploy Redis
kubectl apply -f k8s/redis.yml

# Deploy API Dashboard
kubectl apply -f k8s/deployment.yml
kubectl apply -f k8s/service.yml

# Deploy Ingress
kubectl apply -f k8s/ingress.yml

# Deploy HPA
kubectl apply -f k8s/hpa.yml

# Check status
kubectl get pods -n api-dashboard
kubectl get services -n api-dashboard
kubectl get ingress -n api-dashboard
```

### Health Checks

```bash
# Docker health check
docker ps
docker-compose ps

# Kubernetes health check
kubectl get pods -n api-dashboard
kubectl describe pod <pod-name> -n api-dashboard
kubectl logs <pod-name> -n api-dashboard

# Application health check
curl http://localhost:8000/health
curl http://api-dashboard.your-domain.com/health
```

### Troubleshooting

**Common Issues:**

1. **Port conflicts**: Check if ports 8000, 6379 are available
2. **Redis connection**: Verify Redis is running and accessible
3. **Memory issues**: Increase Docker memory limit to 4GB+
4. **Network issues**: Check Docker network configuration
5. **Kubernetes issues**: Verify RBAC permissions and service accounts

**Logs:**

```bash
# Docker logs
docker-compose logs dashboard
docker logs <container-id>

# Kubernetes logs
kubectl logs <pod-name> -n api-dashboard -f
kubectl logs -l app=api-dashboard -n api-dashboard
```

**Debugging:**

```bash
# Enter container
docker exec -it <container-id> /bin/bash

# Check processes
ps aux

# Check network
netstat -tlnp
curl localhost:8000/health

# Check environment
env | grep -E "(SERVICE|REDIS|ENVIRONMENT)"
```

This deployment guide provides production-ready configurations for Docker and Kubernetes environments with monitoring, scaling, and high availability features.
