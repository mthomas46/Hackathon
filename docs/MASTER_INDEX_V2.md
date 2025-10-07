---
llm_metadata:
  document_type: reference
  content_focus: technical
  platform:
    primary: both
    secondary: []
  status: active
  created_date: '2025-10-01'
  last_modified: '2025-10-07'
  topics:
  - python
  - redis
  - postgresql
  - docker
  - ollama
  - llm_orchestration
  - rag
  - 5_tier_system
  - testing
  - deployment
  concepts: []
  technologies: []
  services_mentioned: []
  semantic_summary: Reference document about technical aspects of the both platform
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

# 📚 Master Documentation Index v2.0

**Version:** 2.0.0  
**Last Updated:** October 7, 2025  
**Status:** Consolidated & Reorganized  
**Total Platforms:** 2  
**Total Services:** 30+ (15+ implemented, 17 documented)

---

## 🚀 **START HERE**

### New to This Project?
→ **[00-START-HERE.md](00-START-HERE.md)** - Primary entry point (5 min read)

### Confused About the Platforms?
→ **[PLATFORM_OVERVIEW.md](PLATFORM_OVERVIEW.md)** - Understand the two ecosystems (15 min read)

### Want to Know What's Built?
→ **[IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md)** - Implementation vs documentation (10 min read)

---

## 🎯 **Quick Navigation by Role**

### I'm a **Developer**
1. Read [Platform Overview](PLATFORM_OVERVIEW.md) - Understand the architecture
2. Choose platform: [Doc Analysis](#platform-1-document-analysis--planning) or [MCP](#platform-2-mcp-model-context-protocol)
3. Follow quickstart guide for your chosen platform
4. Deploy and start building

### I'm a **Product Manager**
1. Read [00-START-HERE](00-START-HERE.md) - Quick overview
2. Review [Implementation Status](IMPLEMENTATION_STATUS.md) - What's available
3. Check [Platform Comparison](PLATFORM_OVERVIEW.md#decision-matrix-which-platform) - Choose your platform
4. Run [Demo](#quick-demos) to see capabilities

### I'm an **Architect**
1. Study [Platform Overview](PLATFORM_OVERVIEW.md) - Complete architecture
2. Review [Documentation Consolidation Analysis](DOCUMENTATION_CONSOLIDATION_ANALYSIS.md) - Design decisions
3. Explore platform-specific architecture docs below
4. Plan integration strategy

### I'm an **Operations Engineer**
1. Check [Implementation Status](IMPLEMENTATION_STATUS.md) - Deployment readiness
2. Follow [Deployment Guide](shared/deployment/README.md) - Deploy services
3. Review [Operations Manual](shared/operations/README.md) - Day-to-day operations
4. Set up [Monitoring](shared/operations/MONITORING.md) - Health checks

---

## 📊 **Platform 1: Document Analysis & Planning**

**Status:** ✅ **Production Ready**  
**Services:** 15+ (all implemented)  
**Use Cases:** Documentation drift detection, planning reports, consistency analysis

### Core Documentation

| Document | Purpose | Read Time |
|----------|---------|-----------|
| **[Quickstart Guide](platform-document-analysis/QUICKSTART.md)** | Get started in 5 minutes | 5 min |
| **[Architecture Overview](architecture/ECOSYSTEM_ARCHITECTURE.md)** | System design & patterns | 20 min |
| **[Service Catalog](services/README_SERVICES.md)** | All 15+ services | 15 min |
| **[Business Pitch](business/PITCH.md)** | Business value & use cases | 10 min |

### Key Features

- ✅ **Multi-Source Ingestion**: GitHub, Jira, Confluence
- ✅ **Consistency Analysis**: Detect drift and contradictions
- ✅ **Planning Reports**: 6 comprehensive report types
- ✅ **User Intelligence**: SME identification & skill analysis
- ✅ **AI-Powered Analysis**: ML-based document analysis

### Essential Services

| Service | Port | Purpose | Status |
|---------|------|---------|--------|
| **orchestrator** | 5099 | Workflow coordination | ✅ Production |
| **doc_store** | 5087 | Document storage (90+ endpoints) | ✅ Production |
| **analysis-service** | 5020 | Document analysis | ✅ Production |
| **source-agent** | 5085 | Multi-source ingestion | ✅ Production |
| **llm-gateway** | 5055 | AI provider routing | ✅ Production |
| **frontend** | 3000 | Web interface | ✅ Production |

[View all services →](services/README_SERVICES.md)

### Quick Demo

```bash
# Start services (1 minute)
bash restart_ecosystem_clean.sh

# Run demo (5 minutes, generates 6 reports)
python3 demo_hyper_realistic_parameterized.py \
  --feature "User authentication" \
  --tickets 10 \
  --team 8 \
  --tech Python React \
  --output my_demo
  
# View results
open my_demo/reports/Executive_Dashboard.md
```

### Documentation

- **Architecture**: [ECOSYSTEM_ARCHITECTURE.md](architecture/ECOSYSTEM_ARCHITECTURE.md)
- **Services**: [README_SERVICES.md](services/README_SERVICES.md)
- **Workflows**: [workflow/](workflow/)
- **Deployment**: [shared/deployment/](shared/deployment/)

---

## 🧠 **Platform 2: MCP (Model Context Protocol)**

**Status:** 📋 **Extensively Documented** (Implementation Planned)  
**Services:** 17 (all documented, ready for implementation)  
**Use Cases:** Hierarchical LLM context, portable knowledge packages, advanced RAG

### Core Documentation

| Document | Purpose | Read Time |
|----------|---------|-----------|
| **[MCP Architecture Complete](architecture/MCP_ARCHITECTURE_COMPLETE.md)** | Complete system design | 30 min |
| **[Service Catalog](reference/SERVICE_CATALOG.md)** | All 17 MCP services | 20 min |
| **[5-Tier System Guide](guides/5_TIER_SYSTEM_GUIDE.md)** | Hierarchical context system | 15 min |
| **[Pattern Index](reference/MCP_PATTERNS_INDEX.md)** | 34 LLM patterns | 25 min |

### Key Concepts

- 📋 **5-Tier Hierarchy**: Client → Project → Team → Company → Ecosystem
- 📋 **Hierarchical Retrieval**: Smart context assembly from tiers
- 📋 **Context Pruning**: 4 strategies for token management
- 📋 **MCP Packages**: Portable .mcp files
- 📋 **34 LLM Patterns**: Production-ready implementations
- 📋 **Hot-Swapping**: Zero-downtime package updates

### MCP Services (Documented)

| Service | Port | Purpose | Documentation |
|---------|------|---------|---------------|
| **mcp-gateway** | 5000 | Unified API entry | ✅ Complete spec |
| **mcp-composer** | 5100 | Multi-MCP orchestration | ✅ Complete spec |
| **mcp-orchestrator** | 5200 | Pattern execution | ✅ Complete spec |
| **mcp-tier-manager** | 6200 | 5-tier system | ✅ Complete spec |
| **mcp-retrieval** | 6100 | Hierarchical retrieval | ✅ Complete spec |
| **mcp-package-manager** | 6300 | Package portability | ✅ Complete spec |

[View all MCP services →](reference/SERVICE_CATALOG.md)

### Implementation Guides

- **5-Tier System**: [5_TIER_SYSTEM_GUIDE.md](guides/5_TIER_SYSTEM_GUIDE.md)
- **Hierarchical Retrieval**: [HIERARCHICAL_RETRIEVAL_GUIDE.md](guides/HIERARCHICAL_RETRIEVAL_GUIDE.md)
- **Context Pruning**: [CONTEXT_PRUNING_GUIDE.md](guides/CONTEXT_PRUNING_GUIDE.md)
- **MCP Portability**: [MCP_PORTABILITY_GUIDE.md](guides/MCP_PORTABILITY_GUIDE.md)
- **Logs MCP**: [LOGS_MCP_GUIDE.md](guides/LOGS_MCP_GUIDE.md)
- **Local LLM**: [LOCAL_LLM_PLATFORM_GUIDE.md](guides/LOCAL_LLM_PLATFORM_GUIDE.md)

### 34 LLM Patterns

| Category | Patterns | Documentation |
|----------|----------|---------------|
| **Reasoning** | Chain-of-Thought, Tree-of-Thought, Graph-of-Thought, ReAct, Self-Consistency | ✅ Specs available |
| **Multi-Agent** | Debate, Collaboration, Voting | ✅ Specs available |
| **RAG & Knowledge** | Advanced RAG, Knowledge Graphs, Multi-Query RAG, Graph RAG | ✅ Specs available |
| **Self-Improvement** | Self-Critique, Constitutional AI, Iterative Refinement | ✅ Specs available |
| **Ensemble** | Orchestration, Analysis | ✅ Specs available |
| **Advanced** | HITL, Uncertainty-Aware, Context Pruning, Adaptive Selection, etc. | ✅ Specs available |

[View pattern index →](reference/MCP_PATTERNS_INDEX.md)

### Phase Tracker

- **Phase 1-7**: ✅ Foundational work complete
- **Phase 8**: ✅ Advanced features documented (5 sub-phases)
- **Phase 9-10**: 📋 Planned expansion phases

[View detailed progress →](reference/PHASE_TRACKER.md)

---

## 🔗 **Shared Infrastructure**

Both platforms share these components:

| Component | Purpose | Port | Documentation |
|-----------|---------|------|---------------|
| **Redis** | Caching, events | 6379 | [Infrastructure Guide](shared/infrastructure/REDIS.md) |
| **Ollama** | Local LLM | 11434 | [Local LLM Guide](guides/LOCAL_LLM_PLATFORM_GUIDE.md) |
| **PostgreSQL** | Database | 5432 | [Database Guide](shared/infrastructure/DATABASE.md) |
| **LLM Gateway** | AI routing | 5055 | [Service README](services/llm-gateway/README.md) |
| **Log Collector** | Logging | 5040 | [Service README](services/log-collector/README.md) |

### Shared Documentation

- **Deployment**: [shared/deployment/](shared/deployment/)
- **Infrastructure**: [shared/infrastructure/](shared/infrastructure/)
- **Operations**: [shared/operations/](shared/operations/)
- **Security**: [security/](security/)
- **Testing**: [shared/testing/](shared/testing/)

---

## 📖 **Documentation by Category**

### Getting Started
- [00-START-HERE](00-START-HERE.md) - Primary entry point
- [Platform Overview](PLATFORM_OVERVIEW.md) - Understand platforms
- [Implementation Status](IMPLEMENTATION_STATUS.md) - What's built
- [Quick Reference](QUICK_REFERENCE.md) - Common commands

### Architecture
- [ECOSYSTEM_ARCHITECTURE.md](architecture/ECOSYSTEM_ARCHITECTURE.md) - Document Analysis architecture
- [MCP_ARCHITECTURE_COMPLETE.md](architecture/MCP_ARCHITECTURE_COMPLETE.md) - MCP architecture
- [MCP_ECOSYSTEM_ARCHITECTURE.md](architecture/MCP_ECOSYSTEM_ARCHITECTURE.md) - MCP service map
- [FEATURES_AND_INTERACTIONS.md](architecture/FEATURES_AND_INTERACTIONS.md) - Service interactions

### Guides
- **Document Analysis**: [guides/](guides/) - Operational guides
- **MCP Specific**: [guides/5_TIER_SYSTEM_GUIDE.md](guides/5_TIER_SYSTEM_GUIDE.md), [guides/HIERARCHICAL_RETRIEVAL_GUIDE.md](guides/HIERARCHICAL_RETRIEVAL_GUIDE.md), etc.
- **Testing**: [TESTING_GUIDE.md](guides/TESTING_GUIDE.md)
- **Development**: [development/](development/)

### Reference
- [Service Catalog](reference/SERVICE_CATALOG.md) - MCP services
- [Services README](services/README_SERVICES.md) - Doc Analysis services
- [MCP Patterns Index](reference/MCP_PATTERNS_INDEX.md) - 34 patterns
- [Phase Tracker](reference/PHASE_TRACKER.md) - Implementation progress
- [API Reference](reference/API_REFERENCE.md) - API documentation

### Operations
- [Deployment Guide](shared/deployment/GUIDE.md) - How to deploy
- [Operations Manual](shared/operations/README.md) - Day-to-day ops
- [Troubleshooting](shared/operations/TROUBLESHOOTING.md) - Common issues
- [Health Checks](operations/HEALTH_CHECKS.md) - Monitoring

---

## 🎓 **Learning Paths**

### Path 1: Document Analysis Developer (2-3 hours)
1. [00-START-HERE](00-START-HERE.md) (5 min)
2. [Platform Overview](PLATFORM_OVERVIEW.md) - Focus on Platform 1 (10 min)
3. [Quickstart Guide](platform-document-analysis/QUICKSTART.md) (15 min)
4. Run demo and explore code (60 min)
5. [Architecture](architecture/ECOSYSTEM_ARCHITECTURE.md) - Deep dive (30 min)
6. [Service Catalog](services/README_SERVICES.md) - Study services (30 min)
7. Start building! (∞)

### Path 2: MCP Architect (3-4 hours)
1. [00-START-HERE](00-START-HERE.md) (5 min)
2. [Platform Overview](PLATFORM_OVERVIEW.md) - Focus on Platform 2 (15 min)
3. [MCP Architecture Complete](architecture/MCP_ARCHITECTURE_COMPLETE.md) (45 min)
4. [5-Tier System Guide](guides/5_TIER_SYSTEM_GUIDE.md) (30 min)
5. [Hierarchical Retrieval](guides/HIERARCHICAL_RETRIEVAL_GUIDE.md) (25 min)
6. [Pattern Index](reference/MCP_PATTERNS_INDEX.md) - Study patterns (45 min)
7. [Service Catalog](reference/SERVICE_CATALOG.md) - All services (30 min)
8. Plan implementation (∞)

### Path 3: Full Platform Understanding (1 day)
1. Morning: Complete Path 1 (Document Analysis)
2. Afternoon: Complete Path 2 (MCP)
3. Evening: [Documentation Consolidation Analysis](DOCUMENTATION_CONSOLIDATION_ANALYSIS.md) - Understand design decisions (30 min)

---

## 📊 **Project Statistics**

```
Total Documentation Files:    507
Total Services:               30+ (15+ implemented, 17 documented)
Total Endpoints:              200+ (implemented)
Test Coverage:                85%+
Lines of Code:                100,000+ (Doc Analysis)
Lines of Documentation:       150,000+
Docker Containers:            23
Reports Generated:            6 types
LLM Patterns:                 34 documented
```

---

## 🔍 **Search Guide**

### Can't Find Something?

1. **Search keywords**: Use your IDE's search across `/docs/`
2. **Check Cross-Reference**: [CROSS_REFERENCE_INDEX.md](CROSS_REFERENCE_INDEX.md)
3. **Service-specific**: Check individual service READMEs
4. **By topic**: Use category links above

### Common Searches

- **"How to deploy"** → [Deployment Guide](shared/deployment/GUIDE.md)
- **"Service ports"** → [QUICK_REFERENCE.md](QUICK_REFERENCE.md) or [Implementation Status](IMPLEMENTATION_STATUS.md)
- **"Testing"** → [TESTING_GUIDE.md](guides/TESTING_GUIDE.md)
- **"Architecture"** → [architecture/](architecture/)
- **"MCP patterns"** → [MCP_PATTERNS_INDEX.md](reference/MCP_PATTERNS_INDEX.md)

---

## 🆘 **Need Help?**

### Documentation Issues
- Can't find something? Check [Cross-Reference Index](CROSS_REFERENCE_INDEX.md)
- Unclear documentation? Open an issue
- Found an error? Submit a PR

### Technical Support
- Service not starting? [Troubleshooting Guide](shared/operations/TROUBLESHOOTING.md)
- Configuration issues? [Configuration Guide](guides/CONFIG_README.md)
- Deployment problems? [Deployment Guide](shared/deployment/GUIDE.md)

### Learning Resources
- [Developer Onboarding](guides/DEVELOPER_ONBOARDING.md)
- [Testing Guide](guides/TESTING_GUIDE.md)
- [Documentation Style Guide](guides/DOCUMENTATION_STYLE_GUIDE.md)

---

## 📝 **Documentation Updates**

### Recent Changes (October 2025)
- ✅ Complete consolidation and reorganization
- ✅ Clear separation of two platforms
- ✅ New primary entry point (00-START-HERE.md)
- ✅ Implementation status clarity
- ✅ Improved navigation structure

### Previous Documentation
- [Old Master Index](MASTER_INDEX.md) - Original version (archived reference)
- [Archive](archive/) - Historical documentation

---

## 🎉 **Quick Wins**

**In 5 minutes:**
- ✅ Understand the project
- ✅ Know which platform to use
- ✅ Run your first demo

**In 30 minutes:**
- ✅ Deploy Document Analysis Platform
- ✅ Generate your first planning report
- ✅ Understand the architecture

**In 2 hours:**
- ✅ Deep dive into one platform
- ✅ Customize for your needs
- ✅ Start building features

---

**Navigate with confidence. Every document is connected. Both platforms are well-documented.** 🚀

---

*Last Updated: October 7, 2025*  
*Version: 2.0.0*  
*Maintained by: Platform Architecture Team*  
*See [DOCUMENTATION_CONSOLIDATION_ANALYSIS.md](DOCUMENTATION_CONSOLIDATION_ANALYSIS.md) for methodology*

