# Docker Compose - MCP Workflow Ecosystem

Complete orchestration of the MCP creation workflow with integrated observability.

## 🎯 Overview

This Docker Compose configuration provides:
- **6 NEW microservices** with full MCP logging integration
- **Infrastructure services** (Kafka, Redis, Ollama, Elasticsearch)
- **AMS network** for inter-service communication
- **Health checks** for all services
- **Profile support** for minimal/full deployments

---

## 📦 Services

### Infrastructure (6 services)
- **kafka** (port 9092) - Event streaming
- **zookeeper** (port 2181) - Kafka coordination
- **redis** (port 6379) - Caching & persistence
- **ollama** (port 11434) - Local LLM runtime
- **elasticsearch** (port 9200) - Log storage
- **mcp-logs** (port 8016) - Centralized logging ⭐

### MCP Workflow (5 NEW services)
- **kafka-ingestion-service** (port 5700) - Document event ingestion
- **llm-tagging-pipeline** (port 8021) - LLM metadata tagging
- **mcp-local-llm** (port 8014) - Local LLM inference
- **mcp-package-manager** (port 8103) - Package management
- **mcp-evergreen-docs** (port 8104) - Documentation sync

### Optional Services (profile: full)
- **mcp-training-coordinator** (port 8100)
- **mcp-store** (port 8101)
- **mcp-registry** (port 8102)
- **doc_store** (port 5087)

---

## 🚀 Quick Start

### Minimal Deployment (NEW services only)
```bash
# Start infrastructure + 5 new services
docker-compose -f docker-compose-mcp-ecosystem.yml up -d

# Check service health
docker-compose -f docker-compose-mcp-ecosystem.yml ps
```

### Full Deployment (All services)
```bash
# Start all services including existing MCP services
docker-compose -f docker-compose-mcp-ecosystem.yml --profile full up -d
```

### Build Services
```bash
# Build all new services
docker-compose -f docker-compose-mcp-ecosystem.yml build

# Build specific service
docker-compose -f docker-compose-mcp-ecosystem.yml build kafka-ingestion-service
```

### Stop Services
```bash
# Stop all services
docker-compose -f docker-compose-mcp-ecosystem.yml down

# Stop and remove volumes
docker-compose -f docker-compose-mcp-ecosystem.yml down -v
```

---

## 🔍 Observability

### Centralized Logging
All services send logs to `mcp-logs` (port 8016):
```bash
# View mcp-logs
curl http://localhost:8016/api/v1/logs

# View service-specific logs
curl "http://localhost:8016/api/v1/logs?service=kafka-ingestion"

# View logs by correlation ID
curl "http://localhost:8016/api/v1/logs?correlation_id=abc-123"
```

### Elasticsearch Queries
```bash
# Query Elasticsearch directly
curl http://localhost:9200/logs-*/_search?pretty

# Get log counts by service
curl -X GET "localhost:9200/logs-*/_search?pretty" -H 'Content-Type: application/json' -d'
{
  "aggs": {
    "by_service": {
      "terms": { "field": "service.keyword" }
    }
  },
  "size": 0
}'
```

### Health Checks
```bash
# Check all services
docker-compose -f docker-compose-mcp-ecosystem.yml ps

# Individual health endpoints
curl http://localhost:8016/health  # mcp-logs
curl http://localhost:5700/health  # kafka-ingestion
curl http://localhost:8021/health  # llm-tagging
curl http://localhost:8014/health  # mcp-local-llm
curl http://localhost:8103/health  # mcp-package-manager
curl http://localhost:8104/health  # mcp-evergreen-docs
```

---

## 🌐 Network Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      AMS Network (Bridge)                    │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Kafka      │  │    Redis     │  │  Ollama      │      │
│  │  :9092       │  │    :6379     │  │  :11434      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│           ▲                ▲                ▲                 │
│           │                │                │                 │
│  ┌────────┴────────────────┴────────────────┴──────┐        │
│  │                                                   │        │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐ │       │
│  │  │ kafka-ing  │→ │ llm-tagging│→ │ mcp-train  │ │       │
│  │  │  :5700     │  │   :8021    │  │  :8100     │ │       │
│  │  └────────────┘  └────────────┘  └────────────┘ │       │
│  │         │                │                │       │       │
│  │         └────────────────┴────────────────┘       │       │
│  │                         ▼                          │       │
│  │                  ┌────────────┐                    │       │
│  │                  │  mcp-logs  │◄───────────────────┘       │
│  │                  │   :8016    │                            │
│  │                  └─────┬──────┘                            │
│  │                        ▼                                   │
│  │                ┌────────────────┐                          │
│  │                │ Elasticsearch  │                          │
│  │                │     :9200      │                          │
│  │                └────────────────┘                          │
│  └───────────────────────────────────────────────────────────┘
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Service Dependencies

```
Startup Order (with health checks):
1. zookeeper → kafka
2. redis
3. ollama
4. elasticsearch → mcp-logs
5. kafka-ingestion-service (depends on: kafka, redis, mcp-logs)
6. llm-tagging-pipeline (depends on: ollama, mcp-logs)
7. mcp-local-llm (depends on: ollama, mcp-logs)
8. mcp-package-manager (depends on: redis, mcp-logs)
9. mcp-evergreen-docs (depends on: redis, mcp-logs)
```

---

## 🔧 Configuration

### Environment Variables

Each service can be configured via environment variables:

**kafka-ingestion-service:**
```bash
KAFKA_INGESTION_SERVICE_PORT=5700
KAFKA_INGESTION_KAFKA_BOOTSTRAP_SERVERS=kafka:29092
KAFKA_INGESTION_REDIS_URL=redis://redis:6379
KAFKA_INGESTION_MCP_LOGS_URL=http://mcp-logs:8016
```

**llm-tagging-pipeline:**
```bash
SERVICE_PORT=8021
OLLAMA_HOST=ollama
OLLAMA_PORT=11434
DEFAULT_MODEL=llama2
```

**mcp-local-llm:**
```bash
LOCAL_LLM_PORT=8014
LOCAL_LLM_OLLAMA_HOST=ollama
LOCAL_LLM_DEFAULT_MODEL=llama2
```

### Volumes

Persistent data volumes:
- `ollama-data` - Ollama models
- `es-data` - Elasticsearch indices
- `package-data` - MCP packages
- `mcp-store-data` - MCP storage
- `doc-store-data` - Document storage

---

## 🐛 Troubleshooting

### View Logs
```bash
# All services
docker-compose -f docker-compose-mcp-ecosystem.yml logs -f

# Specific service
docker-compose -f docker-compose-mcp-ecosystem.yml logs -f kafka-ingestion-service

# Last 100 lines
docker-compose -f docker-compose-mcp-ecosystem.yml logs --tail=100
```

### Restart Service
```bash
docker-compose -f docker-compose-mcp-ecosystem.yml restart kafka-ingestion-service
```

### Check Network
```bash
docker network inspect ams
```

### Health Check Issues
```bash
# Check container health status
docker ps --filter "health=unhealthy"

# Inspect specific container
docker inspect kafka-ingestion-service | grep -A 10 Health
```

---

## 📈 Performance

### Resource Requirements

**Minimal deployment:**
- CPU: 4 cores
- RAM: 8 GB
- Disk: 20 GB

**Full deployment:**
- CPU: 8 cores
- RAM: 16 GB
- Disk: 50 GB

### Scaling

Scale specific services:
```bash
docker-compose -f docker-compose-mcp-ecosystem.yml up -d --scale kafka-ingestion-service=3
```

---

## ✅ Verification

### Test Workflow
```bash
# 1. Check all services are healthy
docker-compose -f docker-compose-mcp-ecosystem.yml ps

# 2. Test kafka-ingestion endpoint
curl http://localhost:5700/health

# 3. Test LLM tagging
curl http://localhost:8021/health

# 4. Check centralized logs
curl http://localhost:8016/api/v1/logs | jq

# 5. Verify Elasticsearch
curl http://localhost:9200/_cluster/health?pretty
```

---

## 🎯 Next Steps

1. **Pull Ollama models**:
   ```bash
   docker exec ollama ollama pull llama2
   docker exec ollama ollama pull mistral
   ```

2. **Initialize Kafka topics**:
   ```bash
   docker exec kafka kafka-topics --create \
     --bootstrap-server localhost:9092 \
     --topic document-events \
     --partitions 3 \
     --replication-factor 1
   ```

3. **Test end-to-end workflow**:
   ```bash
   python demo_mcp_workflow_validation.py
   ```

---

**Status**: Production-ready ✅  
**Architecture**: Microservices with centralized observability  
**Network**: AMS bridge network  
**Logging**: Fully integrated with mcp-logs  

