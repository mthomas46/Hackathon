# Meta-Orchestrator Deployment Guide

Complete deployment instructions for the Meta-Orchestration Service across different environments.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Local Development](#local-development)
- [Docker Deployment](#docker-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [AWS Deployment](#aws-deployment)
- [Production Checklist](#production-checklist)
- [Monitoring & Observability](#monitoring--observability)
- [Backup & Recovery](#backup--recovery)
- [Troubleshooting](#troubleshooting)

## 📋 Prerequisites

### System Requirements

| Component | Minimum | Recommended | Production |
|-----------|---------|-------------|------------|
| CPU | 2 cores | 4 cores | 8+ cores |
| RAM | 4GB | 8GB | 16GB+ |
| Disk | 20GB | 50GB | 100GB+ SSD |
| Network | 100Mbps | 1Gbps | 10Gbps |

### Software Dependencies

```bash
# Required software versions
Docker >= 20.10.0
Docker Compose >= 2.0.0
Python >= 3.11.0
SQLite >= 3.35.0 (or PostgreSQL for production)

# Optional but recommended
Redis >= 6.0.0
Nginx >= 1.20.0 (reverse proxy)
Prometheus >= 2.30.0 (monitoring)
Grafana >= 8.0.0 (dashboards)
```

### Network Requirements

- **Inbound Ports**: 80, 443 (HTTP/HTTPS), 22 (SSH)
- **Outbound**: Docker registry access, external APIs
- **Internal**: Docker daemon socket access
- **Database**: Persistent storage for monitoring data

## 🏠 Local Development

### Quick Start with Docker Compose

```bash
# Clone repository
git clone <repository-url>
cd hackathon

# Start development environment
docker-compose -f docker-compose.dev.yml up -d

# Verify deployment
curl http://localhost:8080/api/v1/services
curl http://localhost:8080/health

# View logs
docker-compose logs meta-orchestrator

# Stop environment
docker-compose down
```

### Manual Development Setup

```bash
# Create virtual environment
cd services/meta-orchestrator
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DOCKER_HOST=unix:///var/run/docker.sock
export DEBUG=true
export LOG_LEVEL=DEBUG

# Run service
uvicorn main:app --reload --host 0.0.0.0 --port 8080
```

### Development Configuration

```yaml
# config/local/docker-compose.dev.yml
version: '3.8'
services:
  meta-orchestrator:
    build:
      context: ../../..
      dockerfile: services/meta-orchestrator/Dockerfile
    ports:
      - "8080:8080"
    environment:
      - DEBUG=true
      - LOG_LEVEL=DEBUG
      - DOCKER_HOST=unix:///var/run/docker.sock
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./data:/app/data
    networks:
      - dev-network

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - dev-network

networks:
  dev-network:
    driver: bridge

volumes:
  redis_data:
```

## 🐳 Docker Deployment

### Single Container Deployment

```dockerfile
# services/meta-orchestrator/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    docker.io \
    docker-compose \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p /app/data

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### Docker Compose Production

```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  meta-orchestrator:
    image: meta-orchestrator:latest
    ports:
      - "8080:8080"
    environment:
      - DEBUG=false
      - LOG_LEVEL=INFO
      - DOCKER_HOST=unix:///var/run/docker.sock
      - ENABLE_AUTH=true
      - API_KEY=${META_ORCHESTRATOR_KEY}
      - DATABASE_URL=postgresql://user:pass@db:5432/meta_orchestrator
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./data:/app/data
      - ./logs:/app/logs
    depends_on:
      - db
      - redis
    networks:
      - app-network
    restart: unless-stopped
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=meta_orchestrator
      - POSTGRES_USER=meta_orchestrator
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - app-network
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    networks:
      - app-network
    restart: unless-stopped
    command: redis-server --appendonly yes

networks:
  app-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16

volumes:
  postgres_data:
  redis_data:
```

### Multi-Stage Docker Build

```dockerfile
# Optimized Dockerfile with multi-stage build
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    docker.io \
    docker-compose \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && mkdir -p /app/data /app/logs \
    && chown -R app:app /app

USER app
WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /home/app/.local
ENV PATH=/home/app/.local/bin:$PATH

# Copy application code
COPY --chown=app:app . .

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "4"]
```

## ☸️ Kubernetes Deployment

### Basic Deployment

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: meta-orchestrator
  namespace: meta-orchestrator
spec:
  replicas: 2
  selector:
    matchLabels:
      app: meta-orchestrator
  template:
    metadata:
      labels:
        app: meta-orchestrator
    spec:
      containers:
      - name: meta-orchestrator
        image: meta-orchestrator:latest
        ports:
        - containerPort: 8080
          name: http
        env:
        - name: DEBUG
          value: "false"
        - name: LOG_LEVEL
          value: "INFO"
        - name: DOCKER_HOST
          value: "unix:///var/run/docker.sock"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: meta-orchestrator-secrets
              key: database-url
        volumeMounts:
        - name: docker-socket
          mountPath: /var/run/docker.sock
        - name: data
          mountPath: /app/data
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: docker-socket
        hostPath:
          path: /var/run/docker.sock
      - name: data
        persistentVolumeClaim:
          claimName: meta-orchestrator-data
```

### Service Configuration

```yaml
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: meta-orchestrator
  namespace: meta-orchestrator
spec:
  selector:
    app: meta-orchestrator
  ports:
  - port: 80
    targetPort: 8080
    protocol: TCP
    name: http
  type: ClusterIP
```

### Ingress Configuration

```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: meta-orchestrator
  namespace: meta-orchestrator
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - meta-orchestrator.example.com
    secretName: meta-orchestrator-tls
  rules:
  - host: meta-orchestrator.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: meta-orchestrator
            port:
              number: 80
```

### ConfigMap and Secrets

```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: meta-orchestrator-config
  namespace: meta-orchestrator
data:
  LOG_LEVEL: "INFO"
  DEBUG: "false"
  ENABLE_AUTH: "true"

---
# k8s/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: meta-orchestrator-secrets
  namespace: meta-orchestrator
type: Opaque
data:
  # Base64 encoded values
  api-key: <base64-encoded-api-key>
  database-url: <base64-encoded-database-url>
  redis-url: <base64-encoded-redis-url>
```

### Horizontal Pod Autoscaling

```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: meta-orchestrator
  namespace: meta-orchestrator
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: meta-orchestrator
  minReplicas: 2
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
```

## ☁️ AWS Deployment

### ECS Fargate Deployment

```hcl
# terraform/main.tf
resource "aws_ecs_cluster" "meta_orchestrator" {
  name = "meta-orchestrator-cluster"
}

resource "aws_ecs_task_definition" "meta_orchestrator" {
  family                   = "meta-orchestrator"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "1024"
  memory                   = "2048"

  container_definitions = jsonencode([{
    name  = "meta-orchestrator"
    image = "meta-orchestrator:latest"

    portMappings = [{
      containerPort = 8080
      hostPort      = 8080
      protocol      = "tcp"
    }]

    environment = [
      { name = "DEBUG", value = "false" },
      { name = "LOG_LEVEL", value = "INFO" },
      { name = "ENABLE_AUTH", value = "true" }
    ]

    secrets = [
      {
        name      = "API_KEY"
        valueFrom = aws_secretsmanager_secret_version.api_key.arn
      },
      {
        name      = "DATABASE_URL"
        valueFrom = aws_secretsmanager_secret_version.database_url.arn
      }
    ]

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        awslogs-group         = "/ecs/meta-orchestrator"
        awslogs-region        = var.aws_region
        awslogs-stream-prefix = "ecs"
      }
    }

    healthCheck = {
      command = ["CMD-SHELL", "curl -f http://localhost:8080/health || exit 1"]
      interval = 30
      timeout = 5
      retries = 3
    }
  }])
}

resource "aws_ecs_service" "meta_orchestrator" {
  name            = "meta-orchestrator"
  cluster         = aws_ecs_cluster.meta_orchestrator.id
  task_definition = aws_ecs_task_definition.meta_orchestrator.arn
  desired_count   = 2

  network_configuration {
    subnets         = aws_subnet.private[*].id
    security_groups = [aws_security_group.meta_orchestrator.id]
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.meta_orchestrator.arn
    container_name   = "meta-orchestrator"
    container_port   = 8080
  }

  lifecycle {
    ignore_changes = [desired_count]
  }
}
```

### Application Load Balancer

```hcl
resource "aws_lb" "meta_orchestrator" {
  name               = "meta-orchestrator-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets           = aws_subnet.public[*].id
}

resource "aws_lb_target_group" "meta_orchestrator" {
  name        = "meta-orchestrator-tg"
  port        = 8080
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 2
  }
}

resource "aws_lb_listener" "meta_orchestrator" {
  load_balancer_arn = aws_lb.meta_orchestrator.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELB-SSL-Negotiation-Policy-2015-05"
  certificate_arn   = aws_acm_certificate.meta_orchestrator.arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.meta_orchestrator.arn
  }
}
```

### RDS Database Setup

```hcl
resource "aws_db_instance" "meta_orchestrator" {
  identifier             = "meta-orchestrator-db"
  engine                 = "postgres"
  engine_version         = "15.3"
  instance_class         = "db.t3.micro"
  allocated_storage      = 20
  max_allocated_storage  = 100

  db_name  = "meta_orchestrator"
  username = "meta_orchestrator"
  password = random_password.db_password.result
  port     = 5432

  vpc_security_group_ids = [aws_security_group.database.id]
  db_subnet_group_name   = aws_db_subnet_group.meta_orchestrator.name

  backup_retention_period = 7
  backup_window           = "03:00-04:00"
  maintenance_window      = "sun:04:00-sun:05:00"

  skip_final_snapshot = true
}
```

### ElastiCache Redis Setup

```hcl
resource "aws_elasticache_cluster" "meta_orchestrator" {
  cluster_id           = "meta-orchestrator-cache"
  engine               = "redis"
  node_type            = "cache.t3.micro"
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  port                 = 6379

  subnet_group_name = aws_elasticache_subnet_group.meta_orchestrator.name
  security_group_ids = [aws_security_group.cache.id]
}
```

## ✅ Production Checklist

### Security Configuration

- [ ] **Network Security**
  - [ ] Deploy in private subnets
  - [ ] Configure security groups for minimal access
  - [ ] Enable VPC endpoints for AWS services
  - [ ] Configure network ACLs

- [ ] **Authentication & Authorization**
  - [ ] Enable API key authentication
  - [ ] Configure JWT tokens for user sessions
  - [ ] Implement role-based access control
  - [ ] Set up audit logging for all operations

- [ ] **Data Protection**
  - [ ] Enable TLS/SSL for all communications
  - [ ] Encrypt sensitive data at rest
  - [ ] Use secure secrets management (AWS Secrets Manager, HashiCorp Vault)
  - [ ] Implement data backup encryption

### Performance Optimization

- [ ] **Resource Allocation**
  - [ ] Configure appropriate CPU/memory limits
  - [ ] Set up horizontal pod autoscaling
  - [ ] Configure database connection pooling
  - [ ] Implement Redis caching for frequently accessed data

- [ ] **Monitoring & Alerting**
  - [ ] Set up comprehensive health checks
  - [ ] Configure application performance monitoring
  - [ ] Implement log aggregation and analysis
  - [ ] Set up alerting for critical issues

### Reliability & Resilience

- [ ] **High Availability**
  - [ ] Deploy across multiple availability zones
  - [ ] Configure load balancing
  - [ ] Implement database replication
  - [ ] Set up Redis cluster for caching

- [ ] **Backup & Recovery**
  - [ ] Configure automated database backups
  - [ ] Implement configuration backup strategy
  - [ ] Set up disaster recovery procedures
  - [ ] Test backup restoration processes

### Operational Readiness

- [ ] **Logging & Observability**
  - [ ] Configure structured logging
  - [ ] Set up log aggregation (ELK stack, CloudWatch)
  - [ ] Implement distributed tracing
  - [ ] Configure metrics collection

- [ ] **Documentation**
  - [ ] Update runbooks and procedures
  - [ ] Document troubleshooting procedures
  - [ ] Create incident response playbooks
  - [ ] Update monitoring dashboards

## 📊 Monitoring & Observability

### Prometheus Metrics

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'meta-orchestrator'
    static_configs:
      - targets: ['meta-orchestrator:8080']
    metrics_path: '/metrics'
    scrape_interval: 15s

  - job_name: 'docker'
    static_configs:
      - targets: ['docker-exporter:9323']
```

### Grafana Dashboards

```json
// Dashboard configuration for Meta-Orchestrator monitoring
{
  "dashboard": {
    "title": "Meta-Orchestrator Overview",
    "panels": [
      {
        "title": "Service Health Status",
        "type": "stat",
        "targets": [
          {
            "expr": "meta_orchestrator_service_health_status",
            "legendFormat": "{{service_name}}"
          }
        ]
      },
      {
        "title": "API Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(meta_orchestrator_api_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ]
      }
    ]
  }
}
```

### Health Check Endpoints

```python
# main.py - Health check endpoints
@app.get("/health")
async def health_check():
    """Basic health check"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check including dependencies"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "checks": {
            "database": await check_database_health(),
            "redis": await check_redis_health(),
            "docker": await check_docker_health(),
            "services": await check_services_health()
        }
    }

    # Determine overall health
    if any(not check.get("healthy", True) for check in health_status["checks"].values()):
        health_status["status"] = "unhealthy"

    return health_status
```

## 💾 Backup & Recovery

### Automated Backups

```bash
#!/bin/bash
# backup.sh - Automated backup script

BACKUP_DIR="/opt/meta-orchestrator/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Database backup
docker exec meta-orchestrator-db pg_dump -U meta_orchestrator meta_orchestrator > ${BACKUP_DIR}/db_${TIMESTAMP}.sql

# Configuration backup
kubectl get configmaps -n meta-orchestrator -o yaml > ${BACKUP_DIR}/config_${TIMESTAMP}.yaml
kubectl get secrets -n meta-orchestrator -o yaml > ${BACKUP_DIR}/secrets_${TIMESTAMP}.yaml

# Application data backup
docker run --rm -v meta-orchestrator-data:/data -v ${BACKUP_DIR}:/backup alpine tar czf /backup/data_${TIMESTAMP}.tar.gz -C /data .

# Clean up old backups (keep last 30 days)
find ${BACKUP_DIR} -name "*.sql" -mtime +30 -delete
find ${BACKUP_DIR} -name "*.yaml" -mtime +30 -delete
find ${BACKUP_DIR} -name "*.tar.gz" -mtime +30 -delete
```

### Recovery Procedures

```bash
#!/bin/bash
# recovery.sh - Disaster recovery script

BACKUP_TIMESTAMP="20240115_020000"

# Restore database
docker exec -i meta-orchestrator-db psql -U meta_orchestrator meta_orchestrator < /opt/backups/db_${BACKUP_TIMESTAMP}.sql

# Restore configuration
kubectl apply -f /opt/backups/config_${BACKUP_TIMESTAMP}.yaml
kubectl apply -f /opt/backups/secrets_${BACKUP_TIMESTAMP}.yaml

# Restore application data
docker run --rm -v meta-orchestrator-data:/data -v /opt/backups:/backup alpine sh -c "cd /data && tar xzf /backup/data_${BACKUP_TIMESTAMP}.tar.gz"

# Restart services
kubectl rollout restart deployment/meta-orchestrator -n meta-orchestrator
```

## 🔧 Troubleshooting

### Common Deployment Issues

#### Container Won't Start

```bash
# Check container logs
docker logs meta-orchestrator

# Check container status
docker ps -a | grep meta-orchestrator

# Verify Docker socket permissions
ls -la /var/run/docker.sock
```

#### Database Connection Issues

```bash
# Test database connectivity
docker exec -it meta-orchestrator-db psql -U meta_orchestrator -d meta_orchestrator -c "SELECT 1;"

# Check database logs
docker logs meta-orchestrator-db

# Verify connection string
echo $DATABASE_URL
```

#### API Authentication Failures

```bash
# Test API without authentication
curl http://localhost:8080/api/v1/services

# Test with API key
curl -H "X-API-Key: your-api-key" http://localhost:8080/api/v1/services

# Check API key configuration
docker exec meta-orchestrator env | grep API_KEY
```

#### Service Discovery Problems

```bash
# Check Docker networks
docker network ls

# Inspect service connectivity
docker exec meta-orchestrator nslookup other-service

# Verify service dependencies
docker-compose config
```

### Performance Issues

#### High CPU Usage

```bash
# Monitor container resources
docker stats meta-orchestrator

# Check application metrics
curl http://localhost:8080/metrics

# Profile Python application
docker exec meta-orchestrator python -m cProfile /app/main.py
```

#### Memory Leaks

```bash
# Monitor memory usage
docker exec meta-orchestrator ps aux --sort -rss

# Check for memory leaks in Python
docker exec meta-orchestrator python -c "import tracemalloc; tracemalloc.start(); # memory analysis code"
```

#### Slow API Responses

```bash
# Test API response times
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8080/api/v1/services

# Check database query performance
docker exec meta-orchestrator-db psql -U meta_orchestrator -d meta_orchestrator -c "EXPLAIN ANALYZE SELECT * FROM service_health LIMIT 10;"
```

### Log Analysis

#### Application Logs

```bash
# View recent logs
docker logs --tail 100 meta-orchestrator

# Follow logs in real-time
docker logs -f meta-orchestrator

# Search for specific errors
docker logs meta-orchestrator 2>&1 | grep ERROR
```

#### Database Logs

```bash
# PostgreSQL logs
docker logs meta-orchestrator-db

# Query slow queries
docker exec meta-orchestrator-db psql -U meta_orchestrator -d meta_orchestrator -c "SELECT * FROM pg_stat_activity WHERE state = 'active';"
```

#### System Logs

```bash
# Docker daemon logs
docker system events --since "1h ago"

# System resource usage
docker system df

# Container events
docker events --since "1h ago"
```

### Emergency Procedures

#### Service Outage Response

1. **Assess the Situation**
   ```bash
   # Check service status
   curl -f http://localhost:8080/health || echo "Service down"

   # Check container status
   docker ps | grep meta-orchestrator
   ```

2. **Restart Service**
   ```bash
   # Restart container
   docker restart meta-orchestrator

   # Or redeploy
   docker-compose up -d meta-orchestrator
   ```

3. **Check Dependencies**
   ```bash
   # Verify database connectivity
   docker exec meta-orchestrator-db pg_isready -U meta_orchestrator

   # Check Redis connectivity
   docker exec meta-orchestrator-redis redis-cli ping
   ```

4. **Rollback if Necessary**
   ```bash
   # Revert to previous version
   docker tag meta-orchestrator:v1 meta-orchestrator:latest
   docker-compose up -d meta-orchestrator
   ```

This deployment guide provides comprehensive instructions for deploying the Meta-Orchestration Service across different environments, from local development to production Kubernetes clusters and cloud platforms. Follow the appropriate section based on your target environment and ensure all production checklist items are completed before going live.
