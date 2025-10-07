---
llm_metadata:
  document_type: reference
  content_focus: historical
  platform:
    primary: mcp
    secondary: []
  status: archived
  created_date: '2024-09-01'
  archived_date: '2025-10-07'
  topics:
  - redis
  - postgresql
  - docker
  - ollama
  - llm_orchestration
  - rag
  - 5_tier_system
  concepts: []
  technologies: []
  services_mentioned: []
  semantic_summary: Reference document about historical aspects of the mcp platform
  archive_reason: consolidated
  historical_value: medium
  reference_value: medium
semantic_embedding:
  model: text-embedding-ada-002
  embedding_date: '2025-10-07'
  embedding_checksum: pending
rag_metadata:
  chunk_strategy: semantic
  optimal_chunk_size: 512
  retrieval_priority: medium
---

# ⚡ MCP Ecosystem - Quick Reference

**Fast Access to Common Information**  
**Last Updated:** October 7, 2025

---

## 🚀 **Essential Commands**

### **Start/Stop Services**
```bash
# Start all services
docker-compose -f docker-compose.dev.yml up -d

# Stop all services
docker-compose -f docker-compose.dev.yml down

# Restart specific service
docker-compose -f docker-compose.dev.yml restart mcp-provisioner

# View logs
docker-compose -f docker-compose.dev.yml logs -f mcp-provisioner
```

### **Health Checks**
```bash
# Gateway
curl http://localhost:5000/health

# Provisioner
curl http://localhost:5400/health

# All services (loop)
for port in 5000 5100 5200 5300 5400 5500 5600 5700 5800 5900 6000; do
  echo "Port $port:" && curl -s http://localhost:$port/health | jq '.status' || echo "N/A"
done
```

---

## 🏢 **Service Ports Reference**

| Service | Port | Purpose |
|---------|------|---------|
| **mcp-gateway** | 5000 | Unified API entry |
| **mcp-composer** | 5100 | Multi-MCP orchestration |
| **mcp-orchestrator** | 5200 | Pattern execution |
| **mcp-interpreter** | 5300 | NLU → intents |
| **mcp-provisioner** | 5400 | MCP lifecycle |
| **mcp-infrastructure** | 5500 | Infrastructure mgmt |
| **mcp-training-coordinator** | 5600 | Training pipelines |
| **mcp-logging** | 5700 | Log collection |
| **mcp-store** | 5800 | Package storage |
| **mcp-performance-store** | 5900 | Metrics & analytics |
| **mcp-registry** | 6000 | Package registry |
| **mcp-retrieval** | 6100 | Hierarchical retrieval |
| **mcp-tier-manager** | 6200 | 5-Tier system |
| **mcp-package-manager** | 6300 | Package portability |
| **mcp_logs** | 6400 | Intelligent observability |
| **mcp_evergreen_docs** | 6500 | Self-healing docs |
| **mcp_local_llm** | 6600 | Local LLM platform |
| **mcp-dashboard** | 8015 | Web dashboard |

---

## 📚 **Common API Endpoints**

### **MCP Provisioner (5400)**
```bash
# List MCPs
curl http://localhost:5400/api/v1/mcps

# Create MCP
curl -X POST http://localhost:5400/api/v1/mcps \
  -H "Content-Type: application/json" \
  -d '{"name":"test-mcp","description":"Test"}'

# Get MCP details
curl http://localhost:5400/api/v1/mcps/{mcp_id}

# Delete MCP
curl -X DELETE http://localhost:5400/api/v1/mcps/{mcp_id}
```

### **Gateway (5000)**
```bash
# Query via Gateway
curl -X POST http://localhost:5000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query":"What is ML?","mcp_id":"test-mcp"}'
```

### **Performance Store (5900)**
```bash
# Get executions
curl http://localhost:5900/api/v1/executions

# Get analytics
curl http://localhost:5900/api/v1/analytics/trends?pattern=rag

# Check anomalies
curl http://localhost:5900/api/v1/analytics/anomalies
```

### **MCP Store (5800)**
```bash
# List packages
curl http://localhost:5800/api/v1/packages

# Get package
curl http://localhost:5800/api/v1/packages/{package_id}

# Export package
curl -X POST http://localhost:5800/api/v1/packages/{package_id}/export
```

---

## 🔗 **Quick Links**

### **Getting Started**
- [5-Minute Setup](guides/GETTING_STARTED.md#quick-start)
- [Demo Walkthrough](guides/DEMO_WALKTHROUGH.md)
- [Troubleshooting](guides/TROUBLESHOOTING_INDEX.md)

### **Architecture**
- [System Overview](architecture/MCP_ARCHITECTURE_COMPLETE.md)
- [Visual Diagrams](architecture/MCP_VISUAL_ARCHITECTURE.md)
- [Service Catalog](reference/SERVICE_CATALOG.md)

### **Development**
- [Testing Guide](guides/TESTING_GUIDE.md)
- [Service Integration](guides/SERVICE_INTEGRATION_GUIDE.md)
- [Developer Onboarding](guides/DEVELOPER_ONBOARDING.md)

### **Operations**
- [Production Deployment](guides/PRODUCTION_DEPLOYMENT_GUIDE.md)
- [Service Startup](guides/SERVICE_STARTUP_GUIDE.md)
- [Monitoring](guides/LOGS_MCP_GUIDE.md)

---

## 🐛 **Common Issues & Solutions**

### **Port Already in Use**
```bash
# Find process using port
lsof -i :5000

# Kill process
kill -9 <PID>

# Or change port in docker-compose.dev.yml
```

### **Container Won't Start**
```bash
# Check logs
docker-compose -f docker-compose.dev.yml logs service-name

# Rebuild
docker-compose -f docker-compose.dev.yml build service-name

# Force recreate
docker-compose -f docker-compose.dev.yml up -d --force-recreate service-name
```

### **Database Connection Issues**
```bash
# Check if database is running
docker-compose -f docker-compose.dev.yml ps | grep postgres

# Restart database
docker-compose -f docker-compose.dev.yml restart postgres

# Check connectivity
docker-compose -f docker-compose.dev.yml exec service-name ping postgres
```

### **Out of Memory**
```bash
# Check Docker stats
docker stats

# Increase Docker memory (Docker Desktop)
# Settings → Resources → Memory → 8GB+

# Restart Docker
```

---

## 🎯 **Environment Variables**

### **Core Services**
```bash
# Gateway
GATEWAY_PORT=5000

# Redis
REDIS_URL=redis://redis:6379

# PostgreSQL
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=mcpuser
POSTGRES_PASSWORD=mcppass

# MinIO
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
```

### **Optional Services**
```bash
# Ollama (Local LLM)
OLLAMA_HOST=http://localhost:11434

# Confluence (Evergreen Docs)
CONFLUENCE_URL=https://your-org.atlassian.net
CONFLUENCE_USER=your-email@example.com
CONFLUENCE_API_TOKEN=your-token
```

---

## 📊 **Key Metrics**

### **System Health**
```bash
# Check all health endpoints
curl http://localhost:5000/health  # Gateway
curl http://localhost:5100/health  # Composer
curl http://localhost:5200/health  # Orchestrator
curl http://localhost:5300/health  # Interpreter
curl http://localhost:5400/health  # Provisioner
```

### **Performance**
```bash
# View performance metrics
curl http://localhost:5900/api/v1/executions | jq '.[] | {pattern, duration, status}'

# Check anomalies
curl http://localhost:5900/api/v1/analytics/anomalies | jq
```

---

## 🔐 **Default Credentials**

### **MinIO Console**
- URL: `http://localhost:9001`
- Username: `minioadmin`
- Password: `minioadmin`

### **PostgreSQL**
- Host: `localhost:5432`
- Database: `mcpdb`
- Username: `mcpuser`
- Password: `mcppass`

### **Redis**
- Host: `localhost:6379`
- No password (dev environment)

---

## 📁 **Important File Locations**

```
/Users/mykalthomas/Documents/work/Hackathon/
├── docker-compose.dev.yml    # Main compose file
├── services/                  # All service code
│   ├── mcp-provisioner/
│   ├── mcp-composer/
│   └── ...
├── docs/                      # Documentation
│   ├── MASTER_INDEX.md       # Doc hub
│   ├── guides/               # User guides
│   └── architecture/         # Architecture docs
└── tests/                     # Test suites
    ├── unit/
    ├── integration/
    └── e2e/
```

---

## 🧪 **Quick Tests**

### **Smoke Test**
```bash
# Test basic functionality
./scripts/smoke_test.sh
```

### **Health Check All**
```bash
# Check all services
./scripts/health_check_all.sh
```

### **Run Tests**
```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# E2E tests
pytest tests/e2e/

# All tests with coverage
pytest --cov=services --cov-report=html
```

---

## 🎓 **Learning Paths (Time Estimates)**

### **Quick Start (15 min)**
1. [Getting Started](guides/GETTING_STARTED.md) - 10 min
2. [Demo Walkthrough](guides/DEMO_WALKTHROUGH.md) - 5 min

### **Developer Onboarding (2 hours)**
1. [Getting Started](guides/GETTING_STARTED.md) - 15 min
2. [Architecture Overview](architecture/MCP_ARCHITECTURE_COMPLETE.md) - 30 min
3. [Service Catalog](reference/SERVICE_CATALOG.md) - 30 min
4. [Testing Guide](guides/TESTING_GUIDE.md) - 30 min
5. [Developer Onboarding](guides/DEVELOPER_ONBOARDING.md) - 15 min

### **Production Deployment (4 hours)**
1. [Getting Started](guides/GETTING_STARTED.md) - 15 min
2. [Production Deployment](guides/PRODUCTION_DEPLOYMENT_GUIDE.md) - 1 hour
3. [Docker Guide](docker/README.md) - 30 min
4. [Service Startup](guides/SERVICE_STARTUP_GUIDE.md) - 30 min
5. [Monitoring Setup](guides/LOGS_MCP_GUIDE.md) - 1 hour
6. Testing & validation - 45 min

---

## 📞 **Getting Help**

### **Documentation**
- [Master Index](MASTER_INDEX.md) - All docs
- [Troubleshooting](guides/TROUBLESHOOTING_INDEX.md) - Common issues
- [Cross-Reference Index](CROSS_REFERENCE_INDEX.md) - Related docs

### **Support**
- Open an issue on GitHub
- Check existing issues
- Contact the team

---

## 🔄 **Recently Updated**

- **Oct 7, 2025:** Complete documentation reorganization
- **Oct 7, 2025:** Phase 8.5 complete (Local LLM Platform)
- **Oct 7, 2025:** Phase 8.4 complete (Evergreen Docs)
- **Oct 7, 2025:** Phase 8.3 complete (Logs MCP)

---

**Bookmark this page for quick reference!** ⚡

*[← Back to Master Index](MASTER_INDEX.md)*

