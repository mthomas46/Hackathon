---
llm_metadata:
  document_type: guide
  content_focus: technical
  platform:
    primary: mcp
    secondary: []
  status: active
  created_date: '2025-10-01'
  last_modified: '2025-10-07'
  topics:
  - microservices
  - python
  - redis
  - postgresql
  - docker
  - ollama
  - llm_orchestration
  - rag
  - embeddings
  - 5_tier_system
  concepts: []
  technologies: []
  services_mentioned: []
  semantic_summary: Guide document about technical aspects of the mcp platform
  archive_reason: n/a
  historical_value: current
  reference_value: high
semantic_embedding:
  model: text-embedding-ada-002
  embedding_date: '2025-10-07'
  embedding_checksum: pending
rag_metadata:
  chunk_strategy: semantic
  optimal_chunk_size: 512
  retrieval_priority: high
---

# 🚀 MCP Ecosystem - Getting Started Guide

**Version:** 1.0  
**Last Updated:** October 7, 2025  
**Difficulty:** Beginner-Friendly

---

## 📖 **Welcome to MCP!**

This guide will help you get the MCP Ecosystem up and running in **under 15 minutes**.

---

## 📋 **Prerequisites**

### **Required:**
- Docker & Docker Compose (v2.0+)
- Python 3.9+ (for local development)
- 8GB+ RAM
- 20GB+ disk space

### **Optional:**
- Ollama (for local LLM features)
- PostgreSQL client (for direct DB access)
- Redis client (for cache inspection)

---

## ⚡ **Quick Start** (5 Minutes)

### **Step 1: Clone Repository**

```bash
git clone https://github.com/your-org/mcp-ecosystem.git
cd mcp-ecosystem
```

### **Step 2: Start All Services**

```bash
# Start all services in detached mode
docker-compose -f docker-compose.dev.yml up -d

# Check status
docker-compose -f docker-compose.dev.yml ps
```

### **Step 3: Verify Health**

```bash
# Check Gateway health
curl http://localhost:5000/health

# Expected: {"status": "healthy"}
```

### **Step 4: Access Dashboard**

Open your browser:
```
http://localhost:8015
```

**🎉 That's it! You're running the MCP Ecosystem!**

---

## 🧪 **Testing Your Installation**

### **Test 1: Provision an MCP**

```bash
curl -X POST http://localhost:5400/api/v1/mcps \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test-mcp",
    "description": "My first MCP",
    "config": {}
  }'
```

### **Test 2: Query via Gateway**

```bash
curl -X POST http://localhost:5000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is machine learning?",
    "mcp_id": "test-mcp"
  }'
```

### **Test 3: Check Performance Metrics**

```bash
curl http://localhost:5900/api/v1/executions
```

---

## 📚 **Core Concepts**

### **What is an MCP?**

An **MCP (Model Context Protocol)** is a managed context environment for LLMs:
- **Knowledge Base:** Documents, embeddings, metadata
- **Configuration:** Behavior, constraints, policies
- **Lifecycle:** Provision → Train → Use → Archive

### **Service Architecture**

```
User → Gateway → Interpreter → Composer → Orchestrator → MCPs
         ↓
    Performance Metrics, Logs, Storage
```

See: [Architecture Overview](../architecture/MCP_ARCHITECTURE_COMPLETE.md)

---

## 🎯 **Common Use Cases**

### **Use Case 1: RAG System**

```python
# 1. Create MCP
mcp_id = create_mcp("rag-system")

# 2. Upload documents
upload_documents(mcp_id, ["doc1.pdf", "doc2.pdf"])

# 3. Train (embed documents)
train_mcp(mcp_id)

# 4. Query
response = query_mcp(mcp_id, "What does the documentation say about X?")
```

### **Use Case 2: Multi-MCP Orchestration**

```yaml
# composition.yaml
name: "multi-mcp-research"
mcps:
  - id: "technical-mcp"
    weight: 0.6
  - id: "business-mcp"
    weight: 0.4

routing: "parallel"
conflict_resolution: "vote"
```

### **Use Case 3: Hierarchical Context**

```python
# 5-Tier setup
create_tier("client", data=user_preferences)
create_tier("project", data=project_docs, parent="client")
create_tier("team", data=team_practices, parent="project")
create_tier("company", data=company_policies, parent="team")
create_tier("ecosystem", data=industry_knowledge, parent="company")

# Query with full hierarchy
response = hierarchical_query(
    query="How should we implement feature X?",
    tier_id="client"
)
```

---

## 🛠️ **Service-Specific Setup**

### **Local LLM Platform (Optional)**

If you want to use local LLMs:

```bash
# Install Ollama
brew install ollama

# Start Ollama
ollama serve

# Pull a model
ollama pull llama2:7b

# Test
curl http://localhost:11434/api/tags
```

See: [Local LLM Platform Guide](LOCAL_LLM_PLATFORM_GUIDE.md)

---

### **Evergreen Documentation (Optional)**

To sync with Confluence:

```bash
# Set environment variables
export CONFLUENCE_URL=https://your-org.atlassian.net
export CONFLUENCE_USER=your-email@example.com
export CONFLUENCE_API_TOKEN=your-api-token
export CONFLUENCE_SPACE=MCP

# Restart service
docker-compose -f docker-compose.dev.yml restart mcp_evergreen_docs
```

See: [Evergreen Docs Guide](EVERGREEN_DOCS_GUIDE.md)

---

## 📊 **Dashboard Features**

Access at `http://localhost:8015`:

### **Main Pages:**
1. **Home** - System overview & status
2. **MCP Management** - Create, list, delete MCPs
3. **Training** - Job management & worker status
4. **Query Interface** - Interactive querying
5. **Package Manager** - Export/import .mcp files
6. **Performance** - Metrics & analytics
7. **Logs MCP** - Intelligent observability
8. **Local LLM** - Model management & inference

---

## 🔧 **Configuration**

### **Environment Variables**

Key variables in `docker-compose.dev.yml`:

```yaml
# Gateway
GATEWAY_PORT=5000

# Redis
REDIS_URL=redis://redis:6379

# MinIO (S3-compatible storage)
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin

# TimescaleDB
TIMESCALE_HOST=timescaledb
TIMESCALE_PORT=5432
```

### **Customization**

Edit `docker-compose.dev.yml` to:
- Change ports
- Adjust resource limits
- Enable/disable services
- Add environment variables

---

## 📖 **Next Steps**

### **Beginner:**
1. ✅ Complete Quick Start (above)
2. 📚 Read [Architecture Overview](../architecture/MCP_ARCHITECTURE_COMPLETE.md)
3. 🧪 Try [Testing Guide](TESTING_GUIDE.md) examples
4. 📦 Explore [Service Catalog](../reference/SERVICE_CATALOG.md)

### **Intermediate:**
1. 🏗️ Study [5-Tier System](5_TIER_SYSTEM_GUIDE.md)
2. 🔄 Learn [Hierarchical Retrieval](HIERARCHICAL_RETRIEVAL_GUIDE.md)
3. ✂️ Understand [Context Pruning](CONTEXT_PRUNING_GUIDE.md)
4. 📝 Configure [HITL Workflows](HITL_WORKFLOWS_GUIDE.md)

### **Advanced:**
1. 📦 Master [MCP Portability](MCP_PORTABILITY_GUIDE.md)
2. 🔍 Implement [Logs MCP](LOGS_MCP_GUIDE.md) strategies
3. 🤖 Optimize [Local LLM Platform](LOCAL_LLM_PLATFORM_GUIDE.md)
4. 🚀 Deploy to [Production](PRODUCTION_DEPLOYMENT_GUIDE.md)

---

## 🐛 **Troubleshooting**

### **Issue: Services not starting**

```bash
# Check logs
docker-compose -f docker-compose.dev.yml logs

# Restart specific service
docker-compose -f docker-compose.dev.yml restart mcp-provisioner
```

### **Issue: Port conflicts**

```bash
# Check what's using port 5000
lsof -i :5000

# Kill process or change port in docker-compose.dev.yml
```

### **Issue: Out of memory**

```bash
# Check Docker memory
docker stats

# Increase Docker memory allocation (Docker Desktop)
# Settings → Resources → Memory → 8GB+
```

### **Issue: Can't access dashboard**

```bash
# Check if dashboard is running
docker-compose -f docker-compose.dev.yml ps mcp-dashboard

# Check dashboard logs
docker-compose -f docker-compose.dev.yml logs mcp-dashboard

# Restart dashboard
docker-compose -f docker-compose.dev.yml restart mcp-dashboard
```

---

## 📚 **Additional Resources**

### **Documentation**
- [Master Documentation Index](../MASTER_INDEX.md)
- [Service Catalog](../reference/SERVICE_CATALOG.md) - All 17 services
- [Phase Tracker](../reference/PHASE_TRACKER.md) - Implementation status

### **Architecture**
- [Complete Architecture](../architecture/MCP_ARCHITECTURE_COMPLETE.md)
- [Visual Diagrams](../architecture/MCP_VISUAL_ARCHITECTURE.md)
- [Lifecycle Flows](../architecture/MCP_LIFECYCLE_FLOWS.md)

### **Guides**
- [Testing Guide](TESTING_GUIDE.md)
- [Service Integration](SERVICE_INTEGRATION_GUIDE.md)
- [Production Deployment](PRODUCTION_DEPLOYMENT_GUIDE.md)

---

## 💡 **Tips & Tricks**

### **Development Workflow**

```bash
# Watch logs for all services
docker-compose -f docker-compose.dev.yml logs -f

# Watch logs for specific service
docker-compose -f docker-compose.dev.yml logs -f mcp-provisioner

# Execute command in service
docker-compose -f docker-compose.dev.yml exec mcp-provisioner bash

# Rebuild specific service
docker-compose -f docker-compose.dev.yml build mcp-provisioner
docker-compose -f docker-compose.dev.yml up -d mcp-provisioner
```

### **Database Access**

```bash
# Access TimescaleDB
docker-compose -f docker-compose.dev.yml exec timescaledb psql -U mcpuser -d mcp_performance

# Access MinIO console
# Browser: http://localhost:9001
# Username: minioadmin
# Password: minioadmin

# Access Redis
docker-compose -f docker-compose.dev.yml exec redis redis-cli
```

---

## 🎉 **You're Ready!**

You now have:
- ✅ MCP Ecosystem running
- ✅ All 17 services operational
- ✅ Dashboard accessible
- ✅ Understanding of core concepts

**Next:** Pick a use case and start building! 🚀

---

## 🆘 **Need Help?**

- 📖 Check [Master Index](../MASTER_INDEX.md)
- 🐛 Review [Troubleshooting](#troubleshooting) section
- 💬 Open an issue on GitHub
- 📧 Contact the team

---

**Happy Building!** 🎊

*The MCP Team*
