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
  - docker
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

# 🔗 MCP Ecosystem - Cross-Reference Index

**Smart Navigation Through 465+ Documents**  
**Last Updated:** October 7, 2025

---

## 🎯 **How to Use This Index**

This index connects **related documents** across the entire documentation tree. Use it to:
- Find related resources quickly
- Understand document relationships
- Navigate complex topics
- Discover relevant guides

---

## 📊 **By Topic**

### **🏗️ Architecture & Design**

**Main Document:** [MCP Architecture Complete](architecture/MCP_ARCHITECTURE_COMPLETE.md)

**Related:**
- [Visual Architecture Diagrams](architecture/MCP_VISUAL_ARCHITECTURE.md) - 12+ diagrams
- [MCP Lifecycle Flows](architecture/MCP_LIFECYCLE_FLOWS.md) - Creation → Usage
- [MCP Ecosystem Architecture](architecture/MCP_ECOSYSTEM_ARCHITECTURE.md) - Original overview
- [Service Catalog](reference/SERVICE_CATALOG.md) - All 17 services
- [5-Tier System Guide](guides/5_TIER_SYSTEM_GUIDE.md) - Hierarchical design

**Supporting:**
- [Ecosystem Build Guide](ecosystem/ECOSYSTEM_BUILD_GUIDE.md)
- [Ecosystem Master Document](ecosystem/ECOSYSTEM_MASTER_LIVING_DOCUMENT.md)
- [Implementation Patterns](guides/ECOSYSTEM_INTEGRATION_PATTERNS.md)

---

### **🚀 Getting Started & Setup**

**Main Document:** [Getting Started Guide](guides/GETTING_STARTED.md)

**Related:**
- [Service Startup Guide](guides/SERVICE_STARTUP_GUIDE.md) - Start/stop services
- [Developer Onboarding](guides/DEVELOPER_ONBOARDING.md) - New developer guide
- [Infrastructure Setup](guides/INFRASTRUCTURE_SETUP.md) - Infrastructure config
- [Docker Guide](docker/README.md) - Container setup
- [Master Index](MASTER_INDEX.md) - Documentation hub

**Supporting:**
- [Demo Walkthrough](guides/DEMO_WALKTHROUGH.md) - Interactive demos
- [Demo CLI Guide](guides/DEMO_CLI_GUIDE.md) - Command-line demos
- [Troubleshooting Index](guides/TROUBLESHOOTING_INDEX.md) - Common issues

---

### **📦 Services & Components**

**Main Document:** [Service Catalog](reference/SERVICE_CATALOG.md)

**Related by Service:**

#### **Core Services:**
- [MCP Provisioner](../services/mcp-provisioner/README.md) → [Architecture](architecture/MCP_ARCHITECTURE_COMPLETE.md#mcp-provisioner)
- [MCP Composer](../services/mcp-composer/README.md) → [Pattern Composition](reference/MCP_PATTERNS_INDEX.md)
- [MCP Orchestrator](../services/mcp-orchestrator/README.md) → [Pattern Library](reference/MCP_PATTERNS_INDEX.md)
- [MCP Interpreter](../services/mcp-interpreter/README.md) → [Architecture](architecture/MCP_ARCHITECTURE_COMPLETE.md#interpreter)
- [MCP Gateway](../services/mcp-gateway/README.md) → [API Reference](reference/API_REFERENCE.md)

#### **Data Services:**
- [MCP Store](../services/mcp-store/README.md) → [Portability Guide](guides/MCP_PORTABILITY_GUIDE.md)
- [Performance Store](../services/mcp-performance-store/README.md) → [Logs MCP Guide](guides/LOGS_MCP_GUIDE.md)
- [MCP Registry](../services/mcp-registry/README.md) → [Service Catalog](reference/SERVICE_CATALOG.md)

#### **Advanced Services:**
- [MCP Retrieval](../services/mcp-retrieval/README.md) → [Hierarchical Retrieval Guide](guides/HIERARCHICAL_RETRIEVAL_GUIDE.md)
- [Tier Manager](../services/mcp_tier_manager/README.md) → [5-Tier System Guide](guides/5_TIER_SYSTEM_GUIDE.md)
- [Package Manager](../services/mcp_package_manager/README.md) → [MCP Portability Guide](guides/MCP_PORTABILITY_GUIDE.md)
- [Logs MCP](../services/mcp_logs/README.md) → [Logs MCP Guide](guides/LOGS_MCP_GUIDE.md)
- [Local LLM](../services/mcp_local_llm/README.md) → [Local LLM Guide](guides/LOCAL_LLM_PLATFORM_GUIDE.md)

**Supporting:**
- [Service Integration Guide](guides/SERVICE_INTEGRATION_GUIDE.md) - Integration patterns
- [Service Standardization](service-standardization/) - Standards & conventions

---

### **🧪 Testing & Quality**

**Main Document:** [Testing Guide](guides/TESTING_GUIDE.md)

**Related:**
- [Test Suite Documentation](guides/TEST_SUITE.md) - Test organization
- [Testing Recipes](guides/TESTING_RECIPES.md) - Common patterns
- [Test Datasets & Fixtures](guides/TEST_DATASETS_FIXTURES.md) - Test data
- [Ecosystem Testing](guides/ECOSYSTEM_TESTING_README.md) - E2E testing
- [E2E Secure Demo](guides/E2E_Secure_Summarization_Demo.md) - Demo test

**Supporting:**
- [Ecosystem Testing Capabilities](ecosystem/ECOSYSTEM_TESTING_CAPABILITIES.md)
- [CI/CD Documentation](ci-cd/) - Continuous integration

---

### **🔍 Retrieval & Context**

**Main Documents:**
- [Hierarchical Retrieval Guide](guides/HIERARCHICAL_RETRIEVAL_GUIDE.md)
- [Context Pruning Guide](guides/CONTEXT_PRUNING_GUIDE.md)

**Related:**
- [5-Tier System Guide](guides/5_TIER_SYSTEM_GUIDE.md) - Tier architecture
- [MCP Retrieval Service](../services/mcp-retrieval/README.md) - Implementation
- [Tier Manager Service](../services/mcp_tier_manager/README.md) - Tier management
- [HITL Workflows Guide](guides/HITL_WORKFLOWS_GUIDE.md) - Human approval

**Supporting:**
- [Architecture - 5-Tier Section](architecture/MCP_ARCHITECTURE_COMPLETE.md#5-tier-hierarchical-system)
- [Visual Architecture - Context Flow](architecture/MCP_VISUAL_ARCHITECTURE.md)

---

### **🤖 AI & LLM Features**

**Main Documents:**
- [Local LLM Platform Guide](guides/LOCAL_LLM_PLATFORM_GUIDE.md)
- [MCP Patterns Index](reference/MCP_PATTERNS_INDEX.md)

**Related:**
- [Pattern Library (34 patterns)](reference/MCP_PATTERNS_INDEX.md) - All LLM patterns
- [Local LLM Service](../services/mcp_local_llm/README.md) - Implementation
- [Orchestrator Service](../services/mcp-orchestrator/README.md) - Pattern execution
- [Composer Service](../services/mcp-composer/README.md) - Pattern composition

**Supporting:**
- [Pattern Decision Framework](archive/PATTERN_DECISION_FRAMEWORK_V2.md)
- [Multi-Agent Patterns](archive/MULTI_AGENT_CATEGORY_COMPLETE.md)

---

### **📊 Monitoring & Observability**

**Main Documents:**
- [Logs MCP Guide](guides/LOGS_MCP_GUIDE.md)
- [Production Deployment Guide](guides/PRODUCTION_DEPLOYMENT_GUIDE.md)

**Related:**
- [Logs MCP Service](../services/mcp_logs/README.md) - Implementation
- [Performance Store Service](../services/mcp-performance-store/README.md) - Metrics
- [Dashboard Service](../services/mcp-dashboard/README.md) - Visualization
- [Logging Service](../services/mcp-logging/README.md) - Log collection

**Supporting:**
- [Ecosystem Hardening](ecosystem/ECOSYSTEM_HARDENING_IMPLEMENTATION.md)
- [Operations Documentation](operations/) - Ops guides

---

### **📦 Package Management & Deployment**

**Main Documents:**
- [MCP Portability Guide](guides/MCP_PORTABILITY_GUIDE.md)
- [Production Deployment Guide](guides/PRODUCTION_DEPLOYMENT_GUIDE.md)

**Related:**
- [Package Manager Service](../services/mcp_package_manager/README.md) - Hot-swapping
- [MCP Store Service](../services/mcp-store/README.md) - Storage
- [Registry Service](../services/mcp-registry/README.md) - Versioning
- [Docker Documentation](docker/) - Container deployment

**Supporting:**
- [MCP Lifecycle Flows](architecture/MCP_LIFECYCLE_FLOWS.md) - Package lifecycle
- [Deployment Documentation](deployment/) - Deploy strategies

---

### **📚 Documentation & Processes**

**Main Documents:**
- [Evergreen Docs Guide](guides/EVERGREEN_DOCS_GUIDE.md)
- [Documentation Style Guide](guides/DOCUMENTATION_STYLE_GUIDE.md)

**Related:**
- [Evergreen Docs Service](../services/mcp_evergreen_docs/README.md) - Implementation
- [Master Index](MASTER_INDEX.md) - All documentation
- [Documentation Organization Summary](DOCUMENTATION_ORGANIZATION_SUMMARY.md) - Org structure

**Supporting:**
- [Documentation Audit](COMPREHENSIVE_DOCS_AUDIT_PLAN.md)
- [Audit Progress Status](AUDIT_PROGRESS_STATUS.md)

---

### **🗺️ Planning & Roadmap**

**Main Documents:**
- [Project Roadmap Complete](roadmap/PROJECT_ROADMAP_COMPLETE.md)
- [Phase Tracker](reference/PHASE_TRACKER.md)

**Related:**
- [Future Phases Plan](roadmap/FUTURE_PHASES_PLAN.md) - Phases 8.6-10
- [Implementation Plan](roadmap/IMPLEMENTATION_PLAN_PHASE_6_7_FUTURE.md) - Detailed plan
- [Session History](achievements/SESSION_HISTORY.md) - Past progress

**Supporting:**
- [Feature Development Roadmap](archive/FEATURE_DEVELOPMENT_ROADMAP_IMPLEMENTATION_PLAN.md)
- [MCP System Plan](mcp-system-plan/) - System planning docs

---

### **🎓 Learning & Onboarding**

**Main Documents:**
- [Getting Started Guide](guides/GETTING_STARTED.md)
- [Developer Onboarding](guides/DEVELOPER_ONBOARDING.md)

**Related:**
- [Demo Walkthrough](guides/DEMO_WALKTHROUGH.md) - Interactive demos
- [Quick Reference Guides](guides/QUICK_REFERENCE_GUIDES.md) - Cheat sheets
- [Troubleshooting Index](guides/TROUBLESHOOTING_INDEX.md) - Common issues
- [Guides README](guides/README.md) - All guides hub

**Supporting:**
- [Demo Enhancement Plan](guides/DEMO_ENHANCEMENT_PLAN.md)
- [CLI Guide](guides/DEMO_CLI_GUIDE.md)

---

## 🔍 **By Use Case**

### **I want to build a RAG system**

**Start:** [Hierarchical Retrieval Guide](guides/HIERARCHICAL_RETRIEVAL_GUIDE.md)

**Then:**
1. [5-Tier System](guides/5_TIER_SYSTEM_GUIDE.md) - Understand hierarchy
2. [Context Pruning](guides/CONTEXT_PRUNING_GUIDE.md) - Manage context
3. [MCP Patterns - RAG](reference/MCP_PATTERNS_INDEX.md#rag--knowledge) - RAG patterns
4. [Service Integration](guides/SERVICE_INTEGRATION_GUIDE.md) - Connect services

**Reference:**
- [Retrieval Service](../services/mcp-retrieval/README.md)
- [Architecture - RAG Flow](architecture/MCP_ARCHITECTURE_COMPLETE.md)

---

### **I want to deploy to production**

**Start:** [Production Deployment Guide](guides/PRODUCTION_DEPLOYMENT_GUIDE.md)

**Then:**
1. [Service Startup](guides/SERVICE_STARTUP_GUIDE.md) - Start services
2. [Docker Guide](docker/README.md) - Container setup
3. [Monitoring](guides/LOGS_MCP_GUIDE.md) - Set up monitoring
4. [Testing](guides/TESTING_GUIDE.md) - Validate deployment

**Reference:**
- [Service Catalog](reference/SERVICE_CATALOG.md) - All services
- [Health Checks](operations/) - Ops documentation

---

### **I want to understand the architecture**

**Start:** [MCP Architecture Complete](architecture/MCP_ARCHITECTURE_COMPLETE.md)

**Then:**
1. [Visual Diagrams](architecture/MCP_VISUAL_ARCHITECTURE.md) - See it visually
2. [Lifecycle Flows](architecture/MCP_LIFECYCLE_FLOWS.md) - Understand flows
3. [5-Tier System](guides/5_TIER_SYSTEM_GUIDE.md) - Core design
4. [Service Catalog](reference/SERVICE_CATALOG.md) - All components

**Reference:**
- [Ecosystem Architecture](architecture/MCP_ECOSYSTEM_ARCHITECTURE.md)
- [Pattern Library](reference/MCP_PATTERNS_INDEX.md)

---

### **I want to run everything locally**

**Start:** [Local LLM Platform Guide](guides/LOCAL_LLM_PLATFORM_GUIDE.md)

**Then:**
1. [Getting Started](guides/GETTING_STARTED.md) - Basic setup
2. [Service Startup](guides/SERVICE_STARTUP_GUIDE.md) - Start services
3. [Docker Guide](docker/README.md) - Local containers

**Reference:**
- [Local LLM Service](../services/mcp_local_llm/README.md)
- [Infrastructure Setup](guides/INFRASTRUCTURE_SETUP.md)

---

### **I want to contribute**

**Start:** [Developer Onboarding](guides/DEVELOPER_ONBOARDING.md)

**Then:**
1. [Documentation Style Guide](guides/DOCUMENTATION_STYLE_GUIDE.md) - Writing standards
2. [Testing Guide](guides/TESTING_GUIDE.md) - Test requirements
3. [Service Integration](guides/SERVICE_INTEGRATION_GUIDE.md) - Integration patterns

**Reference:**
- [Development Documentation](development/)
- [Service Standardization](service-standardization/)

---

## 📊 **Documentation Map**

```
docs/
├── MASTER_INDEX.md ⭐ Central hub
├── CROSS_REFERENCE_INDEX.md ⭐ This file
│
├── achievements/ → Session history & milestones
├── architecture/ → System design & diagrams
├── guides/ → User & developer guides
├── reference/ → Technical reference
├── roadmap/ → Future planning
│
├── operations/ → Ops & deployment
├── development/ → Dev guides & standards
├── ecosystem/ → Ecosystem docs
├── docker/ → Container docs
├── ci-cd/ → CI/CD pipelines
│
└── archive/ → Historical documents
```

---

## 🔗 **Quick Navigation**

| Topic | Main Document | Related Docs |
|-------|---------------|--------------|
| **Getting Started** | [Getting Started](guides/GETTING_STARTED.md) | [Demos](guides/DEMO_WALKTHROUGH.md), [Setup](guides/SERVICE_STARTUP_GUIDE.md) |
| **Architecture** | [Complete Architecture](architecture/MCP_ARCHITECTURE_COMPLETE.md) | [Visual](architecture/MCP_VISUAL_ARCHITECTURE.md), [Flows](architecture/MCP_LIFECYCLE_FLOWS.md) |
| **Services** | [Service Catalog](reference/SERVICE_CATALOG.md) | [Integration](guides/SERVICE_INTEGRATION_GUIDE.md), [Startup](guides/SERVICE_STARTUP_GUIDE.md) |
| **Testing** | [Testing Guide](guides/TESTING_GUIDE.md) | [Recipes](guides/TESTING_RECIPES.md), [Datasets](guides/TEST_DATASETS_FIXTURES.md) |
| **Deployment** | [Production Guide](guides/PRODUCTION_DEPLOYMENT_GUIDE.md) | [Docker](docker/README.md), [Ops](operations/) |
| **Monitoring** | [Logs MCP](guides/LOGS_MCP_GUIDE.md) | [Performance](../services/mcp-performance-store/README.md), [Dashboard](../services/mcp-dashboard/README.md) |
| **Development** | [Developer Onboarding](guides/DEVELOPER_ONBOARDING.md) | [Style Guide](guides/DOCUMENTATION_STYLE_GUIDE.md), [Testing](guides/TESTING_GUIDE.md) |
| **Roadmap** | [Project Roadmap](roadmap/PROJECT_ROADMAP_COMPLETE.md) | [Phases](reference/PHASE_TRACKER.md), [History](achievements/SESSION_HISTORY.md) |

---

## 🎯 **Most Referenced Documents**

1. **[Getting Started Guide](guides/GETTING_STARTED.md)** - Entry point for everyone
2. **[Service Catalog](reference/SERVICE_CATALOG.md)** - Service reference
3. **[MCP Architecture](architecture/MCP_ARCHITECTURE_COMPLETE.md)** - System design
4. **[Testing Guide](guides/TESTING_GUIDE.md)** - Quality assurance
5. **[Production Deployment](guides/PRODUCTION_DEPLOYMENT_GUIDE.md)** - Deploy guide

---

## 📚 **Documentation Statistics**

```
Total Documents:                465+
Main Guides:                     20+
Service READMEs:                 17
Architecture Docs:                4
Reference Docs:                  10+
Cross-References:              500+
```

---

**Use this index to navigate the ecosystem with confidence!** 🚀

*Every document is connected.* 🔗

