# ⚡ Quick Reference Guides - LLM Documentation Ecosystem

<!--
LLM Processing Metadata:
- document_type: "quick_reference_and_patterns"
- content_focus: "practical_task_guidance_and_patterns"
- key_concepts: ["quick_reference", "common_tasks", "deployment", "troubleshooting", "api_usage"]
- processing_hints: "Task-oriented quick reference for common operations and patterns"
- cross_references: ["ECOSYSTEM_MASTER_LIVING_DOCUMENT.md", "docs/deployment/DEPLOYMENT_GUIDE.md", "docs/guides/"]
- target_audience: ["developers", "operators", "integrators", "users"]
-->

## 🎯 **Quick Reference Overview**

**Fast access to common tasks, patterns, and operations** for the LLM Documentation Ecosystem. Designed for quick lookup during development, deployment, and operational activities.

**🔗 Related Guides**: [Deployment Guide](docs/deployment/DEPLOYMENT_GUIDE.md) | [Living Document](ECOSYSTEM_MASTER_LIVING_DOCUMENT.md) | [Documentation Index](docs/README.md)

---

## 🚀 **Deployment & Operations Quick Reference**

### **⚡ Rapid Service Startup**

#### **1. Complete Ecosystem Startup**
```bash
# Quick ecosystem deployment
docker-compose -f docker-compose.dev.yml up -d

# Check health status
./scripts/docker/health-check.sh

# View service logs
docker-compose logs [service-name]
```

#### **2. Individual Service Management**
```bash
# Start specific service
docker-compose up -d [service-name]

# Restart service
docker-compose restart [service-name]

# View service status
docker ps | grep [service-name]

# Access service logs
docker logs [container-name] --tail 50 -f
```

#### **3. Bulletproof System Management**
```bash
# Start with bulletproof protections
make -f Makefile.bulletproof start-bulletproof

# Health check all services
make -f Makefile.bulletproof health

# System healing
make -f Makefile.bulletproof heal
```

### **🔍 Health Monitoring Quick Commands**

| Command | Purpose | Output |
|---------|---------|---------|
| `./scripts/docker/health-check.sh` | Complete ecosystem health | Service status summary |
| `curl http://localhost:[port]/health` | Individual service health | JSON health response |
| `docker ps --format "table {{.Names}}\t{{.Status}}"` | Container status | Running containers |
| `make -f Makefile.bulletproof status` | Bulletproof system status | Enhanced system overview |

### **📊 Port Quick Reference**

#### **Core Services**
| Service | External Port | Internal Port | Health Check |
|---------|---------------|---------------|--------------|
| **Orchestrator** | 5099 | 5099 | `curl http://localhost:5099/health` |
| **LLM Gateway** | 5055 | 5055 | `curl http://localhost:5055/health` |
| **Discovery Agent** | 5045 | 5045 | `curl http://localhost:5045/health` |
| **Doc Store** | 5087 | 5010 | `curl http://localhost:5087/health` |
| **Analysis Service** | 5080 | 5020 | `curl http://localhost:5080/health` |

#### **Analysis & Intelligence**
| Service | External Port | Internal Port | Health Check |
|---------|---------------|---------------|--------------|
| **Code Analyzer** | 5025 | 5025 | `curl http://localhost:5025/health` |
| **Secure Analyzer** | 5100 | 5070 | `curl http://localhost:5100/health` |
| **Memory Agent** | 5090 | 5040 | `curl http://localhost:5090/health` |
| **Source Agent** | 5085 | 5085 | `curl http://localhost:5085/health` |
| **Interpreter** | 5120 | 5120 | `curl http://localhost:5120/health` |

#### **Integration & Operations**
| Service | External Port | Internal Port | Health Check |
|---------|---------------|---------------|--------------|
| **Frontend** | 3000 | 3000 | `curl http://localhost:3000/health` |
| **GitHub MCP** | 5030 | 5072 | `curl http://localhost:5030/health` |
| **Bedrock Proxy** | 5060 | 7090 | `curl http://localhost:5060/health` |
| **Log Collector** | 5040 | 5080 | `curl http://localhost:5040/health` |
| **Notification Service** | 5130 | 5130 | `curl http://localhost:5130/health` |

---

## 🔧 **Development Quick Reference**

### **🛠️ Service Development Patterns**

#### **1. New Service Creation Template**
```python
# Basic service structure
from fastapi import FastAPI
from shared.core.responses import SuccessResponse
from shared.monitoring.health import HealthManager

app = FastAPI(title="Service Name")
health_manager = HealthManager("service-name", "1.0.0")

@app.get("/health")
async def health_check():
    """Standard health check endpoint."""
    health_status = await health_manager.basic_health()
    return SuccessResponse(data=health_status.dict())

if __name__ == "__main__":
    import uvicorn
    import os
    
    port = int(os.environ.get('SERVICE_PORT', 5000))
    uvicorn.run(app, host="0.0.0.0", port=port)
```

#### **2. Standard Dockerfile Pattern**
```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000
ENV SERVICE_PORT=5000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

CMD ["python", "services/service-name/main.py"]
```

#### **3. Service Configuration Template**
```yaml
# config.yaml
service:
  name: "service-name"
  version: "1.0.0"
  port: 5000
  
dependencies:
  - "redis"
  - "doc-store"
  
environment:
  development:
    log_level: "DEBUG"
  production:
    log_level: "INFO"
```

### **📝 Function Documentation Pattern**
```markdown
**`ServiceClass.function_name()` - [Brief Purpose]**
- **Purpose**: [What this function does and why it exists]
- **Ecosystem Value**: [How this benefits the overall ecosystem]
- **Key Features**: [Major capabilities and features provided]
- **Integration Points**: [Services/components this function interacts with]
```

### **🧪 Testing Quick Commands**

| Task | Command | Purpose |
|------|---------|---------|
| **Run all tests** | `python -m pytest tests/` | Complete test suite |
| **Service tests** | `python -m pytest tests/unit/service-name/` | Specific service tests |
| **Integration tests** | `python -m pytest tests/integration/` | Cross-service tests |
| **API tests** | `python -m pytest tests/unit/service/test_api_endpoints.py` | API endpoint tests |
| **Coverage report** | `python -m pytest --cov=services/service-name tests/` | Test coverage |

---

## 🔌 **API Integration Quick Reference**

### **🌐 Common API Patterns**

#### **1. Orchestrator API - Workflow Management**
```python
# Create workflow
import httpx

workflow_data = {
    "name": "Document Analysis Workflow",
    "parameters": [{"name": "document_id", "type": "string", "required": True}],
    "actions": [
        {
            "action_id": "analyze_document",
            "action_type": "service_call",
            "config": {
                "service": "analysis-service",
                "endpoint": "/analyze",
                "method": "POST"
            }
        }
    ]
}

response = httpx.post("http://localhost:5099/workflows", json=workflow_data)
workflow = response.json()
```

#### **2. Doc Store API - Document Operations**
```python
# Store document
document_data = {
    "content": "Document content here",
    "metadata": {
        "title": "Document Title",
        "author": "Author Name",
        "category": "documentation"
    }
}

response = httpx.post("http://localhost:5087/api/v1/documents", json=document_data)
document = response.json()

# Retrieve document
doc_response = httpx.get(f"http://localhost:5087/api/v1/documents/{document['data']['id']}")
retrieved_doc = doc_response.json()
```

#### **3. LLM Gateway API - AI Processing**
```python
# Process with LLM
llm_request = {
    "prompt": "Analyze this document for key insights",
    "content": "Document content to analyze",
    "provider_preference": "ollama",  # or "openai", "anthropic", etc.
    "max_tokens": 1000
}

response = httpx.post("http://localhost:5055/process", json=llm_request)
ai_result = response.json()
```

#### **4. Analysis Service API - Document Analysis**
```python
# Comprehensive analysis
analysis_request = {
    "document_id": "doc-123",
    "analysis_types": ["quality", "semantic", "trend"],
    "options": {
        "include_metadata": True,
        "generate_summary": True
    }
}

response = httpx.post("http://localhost:5080/analyze/comprehensive", json=analysis_request)
analysis_results = response.json()
```

### **📊 API Response Patterns**

#### **Standard Success Response**
```json
{
  "success": true,
  "message": "Operation completed successfully",
  "data": {
    "id": "resource-id",
    "result": "operation result"
  },
  "timestamp": "2025-09-18T10:30:00Z",
  "request_id": "req-12345"
}
```

#### **Standard Error Response**
```json
{
  "success": false,
  "message": "Error description",
  "error_code": "VALIDATION_ERROR",
  "details": {
    "field": "error details"
  },
  "timestamp": "2025-09-18T10:30:00Z",
  "request_id": "req-12345"
}
```

---

## 🔧 **Configuration Quick Reference**

### **⚙️ Environment Variables**

#### **Core Service Configuration**
```bash
# Essential environment variables
export ENVIRONMENT=development
export DATABASE_URL=postgresql://user:pass@localhost:5432/db
export REDIS_URL=redis://localhost:6379
export SECRET_KEY=your-secret-key

# Service URLs
export ORCHESTRATOR_URL=http://localhost:5099
export DOC_STORE_URL=http://localhost:5087
export LLM_GATEWAY_URL=http://localhost:5055
export ANALYSIS_SERVICE_URL=http://localhost:5080
```

#### **AI Provider Configuration**
```bash
# LLM Gateway configuration
export OLLAMA_URL=http://localhost:11434
export OPENAI_API_KEY=your-openai-key
export ANTHROPIC_API_KEY=your-anthropic-key
export AWS_ACCESS_KEY_ID=your-aws-key
export AWS_SECRET_ACCESS_KEY=your-aws-secret
```

#### **Logging & Monitoring**
```bash
# Logging configuration
export LOG_LEVEL=INFO
export LOG_COLLECTOR_URL=http://localhost:5040
export CORRELATION_ID_HEADER=X-Correlation-ID

# Health check configuration
export HEALTH_CHECK_TIMEOUT=10s
export HEALTH_CHECK_INTERVAL=30s
```

### **🐳 Docker Configuration Patterns**

#### **Basic Service Docker Compose**
```yaml
version: '3.8'
services:
  service-name:
    build:
      context: .
      dockerfile: services/service-name/Dockerfile
    ports:
      - "5000:5000"
    environment:
      - SERVICE_PORT=5000
      - ENVIRONMENT=development
    volumes:
      - ./services/service-name:/app/services/service-name
      - ./services/shared:/app/services/shared
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

---

## 🔍 **Troubleshooting Quick Reference**

### **⚠️ Common Issues & Solutions**

#### **Service Startup Issues**

| Problem | Quick Check | Solution |
|---------|-------------|----------|
| **Port conflicts** | `netstat -tlnp \| grep :port` | Update port in config |
| **Import errors** | Check `PYTHONPATH` setting | Verify path configuration |
| **Missing dependencies** | Check `requirements.txt` | `pip install -r requirements.txt` |
| **Health check fails** | `curl http://localhost:port/health` | Check service logs |

#### **Docker Issues**

| Problem | Quick Check | Solution |
|---------|-------------|----------|
| **Container won't start** | `docker logs container-name` | Check logs for errors |
| **Port not accessible** | `docker port container-name` | Verify port mapping |
| **Image build fails** | Check Dockerfile syntax | Validate build context |
| **Volume mount issues** | Check file permissions | Verify volume paths |

#### **Network Connectivity**

| Problem | Quick Check | Solution |
|---------|-------------|----------|
| **Service unreachable** | `docker network ls` | Check network configuration |
| **DNS resolution** | `nslookup service-name` | Verify service discovery |
| **Inter-service communication** | Test direct API calls | Check service URLs |
| **Load balancer issues** | Check routing rules | Verify upstream configuration |

### **📊 Diagnostic Commands**

#### **System Health Checks**
```bash
# Complete ecosystem health
./scripts/docker/health-check.sh

# Individual service health
curl -f http://localhost:[port]/health

# Container resource usage
docker stats

# Service dependencies
docker-compose ps
```

#### **Log Analysis**
```bash
# Service logs
docker-compose logs [service-name] --tail 100 -f

# System logs
docker logs [container-name] --since 1h

# Error pattern search
docker logs [container-name] 2>&1 | grep -i error

# Performance logs
docker logs [container-name] 2>&1 | grep -i "slow\|timeout\|performance"
```

#### **Network Diagnostics**
```bash
# Container network info
docker inspect [container-name] | grep -A 10 "NetworkSettings"

# Port accessibility
curl -I http://localhost:[port]/health

# Service connectivity test
docker exec [container-name] curl -f http://service-name:port/health

# DNS resolution test
docker exec [container-name] nslookup service-name
```

---

## 📚 **Documentation Quick Reference**

### **📝 Document Lookup Patterns**

| Need | Document | Quick Link |
|------|----------|------------|
| **Service details** | Service README | `services/[service-name]/README.md` |
| **Function summaries** | Living Document | [Service sections](ECOSYSTEM_MASTER_LIVING_DOCUMENT.md) |
| **API reference** | Service documentation | Service README → API section |
| **Architecture** | Architecture docs | [Architecture overview](docs/architecture/ECOSYSTEM_ARCHITECTURE.md) |
| **Deployment** | Deployment guide | [Deployment instructions](docs/deployment/DEPLOYMENT_GUIDE.md) |
| **Testing** | Test documentation | [Testing guide](docs/guides/TESTING_GUIDE.md) |

### **🔍 Search Patterns**

#### **Find Service Information**
```bash
# Service by port
grep -r "port.*5099" docs/ services/

# Service by functionality
grep -r "document analysis" docs/ services/

# Configuration patterns
find . -name "config.yaml" -exec grep -l "service_name" {} \;
```

#### **Find API Endpoints**
```bash
# API routes
grep -r "@app\." services/[service-name]/

# Health check endpoints
grep -r "/health" services/

# Specific functionality
grep -r "workflow" services/orchestrator/
```

### **📋 Quick Navigation**

| Document Type | Location Pattern | Example |
|---------------|------------------|---------|
| **Service README** | `services/[name]/README.md` | `services/orchestrator/README.md` |
| **Configuration** | `services/[name]/config.yaml` | `services/llm-gateway/config.yaml` |
| **Tests** | `tests/unit/[name]/` | `tests/unit/doc_store/` |
| **Integration** | `tests/integration/` | `tests/integration/orchestrator/` |
| **Documentation** | `docs/[category]/` | `docs/architecture/` |

---

## 🎯 **Performance & Monitoring Quick Reference**

### **📊 Performance Metrics**

#### **Service Performance Checks**
```bash
# Response time testing
time curl -s http://localhost:5099/health

# Load testing (basic)
for i in {1..10}; do curl -s http://localhost:5099/health & done; wait

# Memory usage
docker stats --no-stream | grep service-name

# CPU usage
top -p $(docker inspect --format='{{.State.Pid}}' container-name)
```

#### **System Resource Monitoring**
```bash
# Container resource usage
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"

# Disk usage
df -h

# Network traffic
netstat -i

# Process monitoring
ps aux | grep python
```

### **🔍 Monitoring Quick Commands**

| Metric | Command | Purpose |
|--------|---------|---------|
| **Health Status** | `./scripts/docker/health-check.sh` | Complete system health |
| **Response Times** | `time curl http://localhost:port/health` | Individual service performance |
| **Resource Usage** | `docker stats` | Container resource consumption |
| **Log Analysis** | `docker logs container --since 1h \| grep ERROR` | Error pattern detection |
| **Network Status** | `docker network ls && docker port container` | Network connectivity |

---

*This quick reference guide provides fast access to common operations and patterns. For detailed information, refer to the complete documentation in the [Living Document](ECOSYSTEM_MASTER_LIVING_DOCUMENT.md) and [Documentation Index](docs/README.md).*
