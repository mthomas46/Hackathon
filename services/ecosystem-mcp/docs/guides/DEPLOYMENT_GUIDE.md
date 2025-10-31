---
title: "🚀 ECOSYSTEM MCP - DEPLOYMENT GUIDE"
service: "ecosystem-mcp"
category: "guides"
tags: ['background', 'cache', 'caching', 'config', 'configuration', 'database', 'deployment', 'docker', 'guide', 'health']
related: ['INDEX.md', 'architecture/OVERVIEW.md', 'CODE_REFERENCE.md', 'API_ENDPOINTS_COMPLETE.md']
status: "current"
last_updated: "2025-10-28"
audience: "user"
difficulty: "beginner"
semantic_keywords: ['background', 'cache', 'caching', 'config', 'configuration']
llm_search_hints: ['what is 🚀 ecosystem mcp - deployment guide', 'how does 🚀 ecosystem mcp - deployment guide work', 'guide to 🚀 ecosystem mcp - deployment guide']
---

# 🚀 ECOSYSTEM MCP - DEPLOYMENT GUIDE

**Version**: 0.1.0  
**Date**: October 2025  
**Status**: Production-Ready

---

## 📋 PREREQUISITES

### Required

- **Docker** & **Docker Compose** (v2+)
- **Python** 3.11+
- **PostgreSQL** 14+ (or use Docker)
- **Redis** 7+ (or use Docker)
- **Git** repository access

### Optional

- **Ollama** (for local LLM)
- **Claude API Key** (for advanced features)
- **Cursor IDE** (for MCP integration)

---

## 🔧 QUICK START

### 1. Clone and Setup

```bash
cd services/ecosystem-mcp
cp env.template .env
# Edit .env with your configuration
```

### 2. Start Dependencies

```bash
make up
# Starts PostgreSQL + Redis via Docker Compose
```

### 3. Initialize Database

```bash
make migrate
# Run Alembic migrations
```

### 4. Install Dependencies

```bash
make install
# Install Python packages
```

### 5. Start Service

```bash
make dev
# Starts service in development mode
```

### 6. Verify

```bash
curl http://localhost:8000/health
# Should return {"status": "healthy"}
```

---

## 📊 INGESTION MODES

### Mode 1: Quick (Recommended for testing)

```bash
# Via CLI
python -m src.cli ingest --mode quick

# Via API
curl -X POST http://localhost:8000/api/v1/admin/ingest \
  -H "Content-Type: application/json" \
  -d '{"mode": "quick"}'
```

**Duration**: ~1-2 minutes  
**Files**: Current .md only  
**Cost**: ~$0.10-0.20

### Mode 2: Standard (Recommended for first run)

```bash
python -m src.cli ingest --mode standard
```

**Duration**: ~5-10 minutes  
**Files**: All current files  
**Cost**: ~$0.50-1.00

### Mode 3: Historical (For documentation history)

```bash
python -m src.cli ingest --mode historical
```

**Duration**: ~15-30 minutes  
**Files**: Current + .md history  
**Cost**: ~$2-5

### Mode 4: Full (⚠️ Run once only)

```bash
python -m src.cli ingest --mode full
```

**Duration**: ~1-3 hours  
**Files**: Complete git history  
**Cost**: ~$10-50

---

## 🔍 API ENDPOINTS

### Health Checks

```bash
GET /health              # Full health check
GET /health/live         # Liveness (K8s)
GET /health/ready        # Readiness (K8s)
```

### Admin

```bash
GET  /api/v1/admin/stats          # System statistics
GET  /api/v1/admin/queue-status   # Queue depths
POST /api/v1/admin/clear-cache    # Clear cache
POST /api/v1/admin/rebuild-index  # Rebuild index
```

### Search

```bash
POST /api/v1/search
{
  "query": "How do I implement authentication?",
  "service_filter": "auth-service",
  "limit": 10
}
```

### Documents

```bash
GET /api/v1/documents               # List all
GET /api/v1/documents?service=auth  # Filter by service
GET /api/v1/documents/{id}          # Get specific
```

### Documentation

```bash
GET /docs        # Interactive Swagger UI
GET /redoc       # ReDoc documentation
GET /openapi.json  # OpenAPI schema
```

---

## 🐳 DOCKER DEPLOYMENT

### Build Image

```bash
docker build -t ecosystem-mcp:latest .
```

### Run Container

```bash
docker run -d \
  --name ecosystem-mcp \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:pass@db/ecosystem_mcp \
  -e REDIS_HOST=redis \
  -e REDIS_PORT=6379 \
  ecosystem-mcp:latest
```

### Using Docker Compose (Recommended)

```bash
docker-compose up -d
```

---

## ☸️ KUBERNETES DEPLOYMENT

### Create Namespace

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: ecosystem-mcp
```

### Deploy Service

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ecosystem-mcp
  namespace: ecosystem-mcp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ecosystem-mcp
  template:
    metadata:
      labels:
        app: ecosystem-mcp
    spec:
      containers:
      - name: ecosystem-mcp
        image: ecosystem-mcp:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: ecosystem-mcp-secrets
              key: database-url
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
```

---

## 🔐 SECURITY

### API Keys

Store sensitive keys in environment variables:

```bash
export CLAUDE_API_KEY="your-key-here"
export CURSOR_API_KEY="your-key-here"
```

Or use secrets management:
- **Docker**: Docker Secrets
- **Kubernetes**: Secrets
- **Cloud**: AWS Secrets Manager, GCP Secret Manager

### Network Security

```yaml
# Restrict access to admin endpoints
- path: /api/v1/admin/*
  require_auth: true
  allowed_ips:
    - 10.0.0.0/8  # Internal only
```

### Database

- Use SSL/TLS for PostgreSQL connections
- Rotate credentials regularly
- Limit database user permissions

---

## 📈 MONITORING

### Health Checks

```bash
# Check service status
curl http://localhost:8000/health

# Check queue depths
curl http://localhost:8000/api/v1/admin/queue-status

# Get statistics
curl http://localhost:8000/api/v1/admin/stats
```

### Logs

```bash
# Docker
docker logs -f ecosystem-mcp

# Kubernetes
kubectl logs -f deployment/ecosystem-mcp -n ecosystem-mcp

# Local
tail -f logs/ecosystem-mcp.log
```

### Metrics

Prometheus metrics available at `/metrics` (if enabled).

Key metrics:
- `ingestion_documents_total`: Total documents processed
- `ingestion_duration_seconds`: Ingestion time
- `api_requests_total`: API request count
- `api_request_duration_seconds`: API latency

---

## 🔄 MAINTENANCE

### Backup Database

```bash
make backup
# or
pg_dump -h localhost -U postgres ecosystem_mcp > backup.sql
```

### Update Dependencies

```bash
make update
pip list --outdated
```

### Clear Queue

```bash
curl -X POST http://localhost:8000/api/v1/admin/clear-queue
```

### Rebuild Index

```bash
curl -X POST http://localhost:8000/api/v1/admin/rebuild-index
```

---

## 🐛 TROUBLESHOOTING

### Service Won't Start

1. Check database connection:
   ```bash
   psql $DATABASE_URL
   ```

2. Check Redis connection:
   ```bash
   redis-cli ping
   ```

3. Check logs:
   ```bash
   tail -f logs/*.log
   ```

### Ingestion Fails

1. Check queue status:
   ```bash
   curl http://localhost:8000/api/v1/admin/queue-status
   ```

2. Check failed queue:
   ```bash
   redis-cli XLEN ecosystem-mcp:failed
   ```

3. Retry failed documents:
   ```bash
   python -m src.cli retry-failed
   ```

### Search Returns No Results

1. Check document count:
   ```bash
   curl http://localhost:8000/api/v1/admin/stats
   ```

2. Rebuild index:
   ```bash
   curl -X POST http://localhost:8000/api/v1/admin/rebuild-index
   ```

---

## 🎯 BEST PRACTICES

### First Deployment

1. Start with **Mode 1** (quick) to test
2. Scale to **Mode 2** (standard) once validated
3. Only use **Mode 3/4** if you need history
4. Monitor costs and queue depths

### Ongoing Operations

1. Run **incremental ingestion** daily
2. Monitor queue depths (alert if > 1000)
3. Backup database weekly
4. Review cost reports monthly

### Performance

1. Use **connection pooling** for database
2. Cache frequently accessed documents
3. Scale workers based on queue depth
4. Monitor embedding costs

---

## 📞 SUPPORT

### Documentation

- **Main README**: `/README.md`
- **API Docs**: `http://localhost:8000/docs`
- **Implementation Plan**: `/IMPLEMENTATION_PLAN.md`

### Logs

- **Application**: `logs/ecosystem-mcp.log`
- **Errors**: `logs/errors.log`
- **Ingestion**: `logs/ingestion.log`

---

## ✅ DEPLOYMENT CHECKLIST

- [ ] Environment variables configured
- [ ] Database initialized (migrations run)
- [ ] Redis accessible
- [ ] Health check passes
- [ ] Initial ingestion complete (Mode 1/2)
- [ ] API endpoints tested
- [ ] Monitoring configured
- [ ] Backups scheduled
- [ ] Security hardened
- [ ] Documentation reviewed

---

**Status**: ✅ Production-Ready  
**Support**: See `/ENTERPRISE_CASE_STUDY.md` for methodology

