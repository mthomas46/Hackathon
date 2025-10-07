# 📖 MCP Guides - Complete Navigation

**Quick Access Hub for All Guides**  
**Last Updated:** October 7, 2025

---

## 🚀 **Start Here**

### **New to MCP?**
→ [**Getting Started Guide**](GETTING_STARTED.md) - 5-minute quickstart

### **Need Something Specific?**
Use the categories below or `Ctrl+F` to search.

---

## 📚 **Guides by Category**

### **🏗️ Core System Guides**

#### [5-Tier Hierarchical System](5_TIER_SYSTEM_GUIDE.md)
**Purpose:** Multi-level context management (Client → Ecosystem)  
**Key Topics:** Tier creation, inheritance, progressive refinement  
**Prerequisites:** Basic MCP understanding  
**Related:** [Hierarchical Retrieval](#advanced-retrieval), [Architecture](../architecture/MCP_ARCHITECTURE_COMPLETE.md)

#### [Hierarchical Retrieval](HIERARCHICAL_RETRIEVAL_GUIDE.md)
**Purpose:** Retrieve context from multiple tiers efficiently  
**Key Topics:** Token budgets, tier weights, retrieval strategies  
**Prerequisites:** [5-Tier System](5_TIER_SYSTEM_GUIDE.md)  
**Related:** [Context Pruning](#context-pruning), [5-Tier Guide](5_TIER_SYSTEM_GUIDE.md)

#### [Context Pruning](CONTEXT_PRUNING_GUIDE.md)
**Purpose:** Dynamically reduce context to fit token limits  
**Key Topics:** 4 pruning strategies, relevance scoring, budget management  
**Prerequisites:** [Hierarchical Retrieval](#hierarchical-retrieval)  
**Related:** [Retrieval Service](../reference/SERVICE_CATALOG.md#mcp-retrieval)

---

### **🤖 AI & LLM Features**

#### [Local LLM Platform](LOCAL_LLM_PLATFORM_GUIDE.md)
**Purpose:** 100% local LLM inference with M4 Max optimization  
**Key Topics:** Ollama, embeddings, semantic search, zero-cost inference  
**Prerequisites:** None (optional: Ollama installed)  
**Related:** [Dashboard](../operations/DASHBOARD_GUIDE.md), [M4 Optimization](#performance)

#### [HITL Workflows (Human-in-the-Loop)](HITL_WORKFLOWS_GUIDE.md)
**Purpose:** Add human approval to AI decisions  
**Key Topics:** Approval requests, queues, audit trails  
**Prerequisites:** Basic MCP knowledge  
**Related:** [Retrieval Service](../reference/SERVICE_CATALOG.md#mcp-retrieval)

---

### **📦 Package & Deployment**

#### [MCP Portability](MCP_PORTABILITY_GUIDE.md)
**Purpose:** Export/import MCPs as portable packages  
**Key Topics:** .mcp files, hot-swapping, versioning, rollback  
**Prerequisites:** MCP provisioning knowledge  
**Related:** [Package Manager](../reference/SERVICE_CATALOG.md#mcp-package-manager), [MCP Store](../reference/SERVICE_CATALOG.md#mcp-store)

#### [Production Deployment](PRODUCTION_DEPLOYMENT_GUIDE.md)
**Purpose:** Deploy MCP ecosystem to production  
**Key Topics:** Docker, health checks, monitoring, configuration  
**Prerequisites:** [Getting Started](GETTING_STARTED.md)  
**Related:** [Service Startup](SERVICE_STARTUP_GUIDE.md), [Docker Guide](../docker/README.md)

#### [Service Startup Guide](SERVICE_STARTUP_GUIDE.md)
**Purpose:** Start/stop individual services  
**Key Topics:** Docker commands, debugging, service dependencies  
**Prerequisites:** Docker installed  
**Related:** [Service Catalog](../reference/SERVICE_CATALOG.md), [Production Deployment](#production-deployment)

---

### **🔍 Observability & Monitoring**

#### [Logs MCP System](LOGS_MCP_GUIDE.md)
**Purpose:** Transform logs into strategic intelligence  
**Key Topics:** Pattern detection, anomalies, root cause analysis, predictive maintenance  
**Prerequisites:** Basic logging knowledge  
**Related:** [Performance Monitoring](#performance), [Dashboard](../operations/DASHBOARD_GUIDE.md)

#### [Evergreen Documentation](EVERGREEN_DOCS_GUIDE.md)
**Purpose:** Self-healing, auto-updating documentation  
**Key Topics:** Bi-directional sync, Confluence integration, health scoring  
**Prerequisites:** Confluence access (optional)  
**Related:** [Documentation Best Practices](#documentation)

---

### **🔧 Development & Integration**

#### [Service Integration](SERVICE_INTEGRATION_GUIDE.md)
**Purpose:** Integrate services with resilience patterns  
**Key Topics:** HTTP clients, circuit breakers, retries, timeouts  
**Prerequisites:** Python/FastAPI knowledge  
**Related:** [Service Catalog](../reference/SERVICE_CATALOG.md), [Architecture](../architecture/MCP_ARCHITECTURE_COMPLETE.md)

#### [Testing Guide](TESTING_GUIDE.md)
**Purpose:** Comprehensive testing strategies  
**Key Topics:** Unit tests, integration tests, E2E tests, TDD  
**Prerequisites:** pytest knowledge  
**Related:** [Development Guide](../development/README.md), [CI/CD](../ci-cd/README.md)

#### [Demo CLI Guide](DEMO_CLI_GUIDE.md)
**Purpose:** Command-line demos and examples  
**Key Topics:** CLI usage, demo scripts, example workflows  
**Prerequisites:** [Getting Started](GETTING_STARTED.md)  
**Related:** [Demo Walkthrough](#demo-walkthrough)

#### [Demo Walkthrough](DEMO_WALKTHROUGH.md)
**Purpose:** Step-by-step demo scenarios  
**Key Topics:** Use cases, interactive demos, example outputs  
**Prerequisites:** Services running  
**Related:** [Demo CLI Guide](#demo-cli-guide), [Getting Started](GETTING_STARTED.md)

---

## 🎯 **Guides by Skill Level**

### **Beginner (Start Here)**
1. [Getting Started](GETTING_STARTED.md) - 5-min setup
2. [Service Startup Guide](SERVICE_STARTUP_GUIDE.md) - Basic operations
3. [Demo Walkthrough](DEMO_WALKTHROUGH.md) - See it in action

### **Intermediate**
1. [5-Tier System](5_TIER_SYSTEM_GUIDE.md) - Core architecture
2. [Hierarchical Retrieval](HIERARCHICAL_RETRIEVAL_GUIDE.md) - Advanced retrieval
3. [Context Pruning](CONTEXT_PRUNING_GUIDE.md) - Context management
4. [HITL Workflows](HITL_WORKFLOWS_GUIDE.md) - Human oversight

### **Advanced**
1. [MCP Portability](MCP_PORTABILITY_GUIDE.md) - Package management
2. [Local LLM Platform](LOCAL_LLM_PLATFORM_GUIDE.md) - Local inference
3. [Logs MCP System](LOGS_MCP_GUIDE.md) - Intelligent observability
4. [Service Integration](SERVICE_INTEGRATION_GUIDE.md) - Resilience patterns

### **Production/Ops**
1. [Production Deployment](PRODUCTION_DEPLOYMENT_GUIDE.md) - Deploy
2. [Testing Guide](TESTING_GUIDE.md) - Quality assurance
3. [Evergreen Documentation](EVERGREEN_DOCS_GUIDE.md) - Auto-docs

---

## 🔄 **Learning Paths**

### **Path 1: RAG Developer**
```
Getting Started → 5-Tier System → Hierarchical Retrieval 
→ Context Pruning → Production Deployment
```

### **Path 2: MLOps Engineer**
```
Getting Started → Service Integration → Testing Guide 
→ Production Deployment → Logs MCP
```

### **Path 3: AI Product Manager**
```
Getting Started → Demo Walkthrough → 5-Tier System 
→ HITL Workflows → Evergreen Docs
```

### **Path 4: Platform Engineer**
```
Getting Started → Service Startup → Service Integration 
→ MCP Portability → Production Deployment
```

---

## 🔗 **Quick Links by Task**

### **I want to...**

#### **...get started quickly**
→ [Getting Started Guide](GETTING_STARTED.md)

#### **...understand the architecture**
→ [5-Tier System](5_TIER_SYSTEM_GUIDE.md) + [Architecture Docs](../architecture/MCP_ARCHITECTURE_COMPLETE.md)

#### **...deploy to production**
→ [Production Deployment](PRODUCTION_DEPLOYMENT_GUIDE.md) + [Service Startup](SERVICE_STARTUP_GUIDE.md)

#### **...build a RAG system**
→ [Hierarchical Retrieval](HIERARCHICAL_RETRIEVAL_GUIDE.md) + [Context Pruning](CONTEXT_PRUNING_GUIDE.md)

#### **...run locally without APIs**
→ [Local LLM Platform](LOCAL_LLM_PLATFORM_GUIDE.md)

#### **...monitor my system**
→ [Logs MCP](LOGS_MCP_GUIDE.md) + [Dashboard Guide](../operations/DASHBOARD_GUIDE.md)

#### **...export/import MCPs**
→ [MCP Portability](MCP_PORTABILITY_GUIDE.md)

#### **...add human approval**
→ [HITL Workflows](HITL_WORKFLOWS_GUIDE.md)

#### **...test my implementation**
→ [Testing Guide](TESTING_GUIDE.md)

#### **...integrate services**
→ [Service Integration](SERVICE_INTEGRATION_GUIDE.md)

---

## 📊 **Guide Statistics**

```
Total Guides:                     12
Average Length:              ~250 LOC
Total Documentation:        ~3,000 LOC
Skill Levels Covered:              4
Learning Paths:                    4
Cross-References:               100+
```

---

## 🆘 **Can't Find What You Need?**

1. **Check the Master Index:** [MASTER_INDEX.md](../MASTER_INDEX.md)
2. **Browse Architecture:** [architecture/](../architecture/)
3. **Search Reference:** [reference/](../reference/)
4. **Explore Operations:** [operations/](../operations/)
5. **Ask the team:** Open an issue

---

## 📚 **Other Documentation**

- [Master Index](../MASTER_INDEX.md) - All documentation
- [Service Catalog](../reference/SERVICE_CATALOG.md) - All 17 services
- [Phase Tracker](../reference/PHASE_TRACKER.md) - Implementation progress
- [Architecture](../architecture/MCP_ARCHITECTURE_COMPLETE.md) - System design
- [Roadmap](../roadmap/PROJECT_ROADMAP_COMPLETE.md) - Future plans

---

## 🔄 **Recently Updated**

- **Oct 7, 2025:** Complete documentation reorganization
- **Oct 7, 2025:** Added Local LLM Platform Guide
- **Oct 7, 2025:** Added Evergreen Docs Guide
- **Oct 7, 2025:** Added Logs MCP Guide

---

**All guides are production-ready and actively maintained!** ✅

*Navigate with confidence.* 🚀
