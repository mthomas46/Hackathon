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
  - domain_driven_design
  - python
  - redis
  - postgresql
  - docker
  - ollama
  - llm_orchestration
  - context_management
  - rag
  - 5_tier_system
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

# 🌟 Platform Overview - Understanding the Dual Ecosystem

**Version:** 2.0.0  
**Last Updated:** October 7, 2025  
**Status:** Comprehensive Platform Guide

---

## 🎯 Executive Summary

This project consists of **TWO DISTINCT but COMPLEMENTARY PLATFORMS** sharing common infrastructure:

1. **Document Analysis & Planning Platform** (✅ Production Ready)
2. **MCP (Model Context Protocol) Platform** (📋 Extensively Documented)

Both platforms leverage shared services (Redis, Ollama, LLM Gateway) but serve fundamentally different purposes.

---

## 🏗️ Platform 1: Document Analysis & Planning

### Purpose & Mission

**Primary Goal:** Maintain documentation quality, detect drift, and generate intelligent planning reports.

**Problem Solved:** Organizations struggle with documentation that drifts from reality—READMEs don't match OpenAPI specs, Jira tickets contradict Confluence pages, and expertise is lost when people leave.

**Solution:** Automated multi-source ingestion, consistency checking, drift detection, and AI-powered intelligence extraction.

### Core Capabilities

| Capability | Description | Business Value |
|------------|-------------|----------------|
| **Multi-Source Ingestion** | GitHub, Jira, Confluence integration | Centralize all documentation sources |
| **Consistency Analysis** | Detect drift and contradictions | Maintain trustworthy documentation |
| **User Intelligence** | Extract team expertise from history | Preserve organizational knowledge |
| **Planning Reports** | 6 comprehensive report types | Data-driven project planning |
| **Drift Detection** | README vs OpenAPI mismatches | Catch errors before release |
| **SME Identification** | Find experts automatically | Speed up resource allocation |

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│           Document Analysis & Planning Platform             │
└─────────────────────────────────────────────────────────────┘

        ┌──────────────┐
        │  Frontend    │  User Interface (Port 3000)
        │  (React)     │
        └──────┬───────┘
               │
        ┌──────▼───────┐
        │ Orchestrator │  Central Coordination (Port 5099)
        │  (DDD)       │  • Workflow management
        └──────┬───────┘  • Service registry
               │          • Event streaming
               │
     ┌─────────┼─────────┬─────────┬─────────┐
     │         │         │         │         │
┌────▼───┐ ┌──▼───┐ ┌──▼───┐ ┌──▼───┐ ┌───▼────┐
│Source  │ │Doc   │ │Analy-│ │LLM   │ │Prompt  │
│Agent   │ │Store │ │sis   │ │Gate- │ │Store   │
│(5085)  │ │(5087)│ │(5020)│ │way   │ │(5110)  │
└────────┘ └──────┘ └──────┘ │(5055)│ └────────┘
                              └───┬───┘
                                  │
               ┌──────────────────┼──────────────────┐
               │                  │                  │
          ┌────▼────┐      ┌──────▼────┐     ┌──────▼────┐
          │ Ollama  │      │  OpenAI   │     │ Anthropic │
          │ (Local) │      │  (Cloud)  │     │  (Cloud)  │
          └─────────┘      └───────────┘     └───────────┘
```

### Key Services (All Implemented)

| Service | Port | Purpose | Status |
|---------|------|---------|--------|
| **orchestrator** | 5099 | Workflow coordination, DDD architecture | ✅ Production |
| **doc_store** | 5087 | Document storage with 90+ endpoints | ✅ Production |
| **analysis-service** | 5020 | Document analysis & consistency checking | ✅ Production |
| **source-agent** | 5085 | GitHub/Jira/Confluence integration | ✅ Production |
| **llm-gateway** | 5055 | Multi-provider AI routing | ✅ Production |
| **prompt_store** | 5110 | Prompt management & A/B testing | ✅ Production |
| **interpreter** | 5120 | Natural language query processing | ✅ Production |
| **memory-agent** | 5090 | Context memory management | ✅ Production |
| **frontend** | 3000 | Web interface | ✅ Production |
| **code-analyzer** | 5025 | Code analysis | ✅ Production |
| **secure-analyzer** | 5100 | Security-aware analysis | ✅ Production |
| **notification-service** | 5130 | Multi-channel notifications | ✅ Production |
| **log-collector** | 5040 | Centralized logging | ✅ Production |
| **bedrock-proxy** | 5060 | AWS Bedrock integration | ✅ Production |

### Typical Workflows

#### Workflow 1: Document Consistency Check
```
1. User requests consistency analysis via frontend
2. Interpreter parses natural language query
3. Orchestrator coordinates workflow:
   - Source Agent fetches from GitHub/Jira/Confluence
   - Doc Store indexes documents
   - Analysis Service detects drift and contradictions
4. Findings generated and stored
5. Notification Service alerts owners
6. Frontend displays results
```

#### Workflow 2: Planning Report Generation
```
1. User configures feature parameters (tickets, team size, tech stack)
2. Mock Data Generator creates realistic historical data
3. User Intelligence Extraction:
   - Extract users from historical documents
   - Identify SMEs using sophisticated scoring algorithm
   - Build collaboration networks
4. Service Discovery:
   - Discover relevant services
   - Extract dependencies
5. Planning Service generates comprehensive reports:
   - Executive Dashboard (GO/NO-GO decision)
   - Planning Report (timeline, resources, risks)
   - User & Team Report (skills, SMEs, gaps)
   - Behind-the-Scenes (workflow execution details)
   - Ecosystem Validation (service health)
   - Data Architecture (schemas, relationships)
```

### Use Cases

**Primary Use Cases:**
- ✅ Detect documentation drift before release
- ✅ Generate planning reports with historical intelligence
- ✅ Maintain docs/API consistency across organization
- ✅ Preserve expertise through automated SME identification
- ✅ Cross-platform content consolidation (GitHub + Jira + Confluence)
- ✅ Automated owner notification for documentation issues

**Demo:** `python3 demo_hyper_realistic_parameterized.py --feature "Your Feature" --tickets 10 --team 8`

---

## 🧠 Platform 2: MCP (Model Context Protocol)

### Purpose & Mission

**Primary Goal:** Intelligent management of LLM contexts across organizational hierarchies with portable knowledge packages.

**Problem Solved:** LLMs need context, but managing context across teams, projects, and organizational tiers is complex. How do you maintain client-specific, project-specific, and company-wide knowledge efficiently?

**Solution:** 5-tier hierarchical context system with intelligent retrieval, context pruning, and portable .mcp packages.

### Core Concepts

| Concept | Description | Value Proposition |
|---------|-------------|-------------------|
| **5-Tier Hierarchy** | Client → Project → Team → Company → Ecosystem | Organize context by scope |
| **Hierarchical Retrieval** | Smart context assembly from tiers | Relevant context, token budget aware |
| **Context Pruning** | 4 strategies (relevance, recency, importance, hybrid) | Fit within token limits |
| **MCP Packages** | Portable .mcp files | Deploy knowledge anywhere |
| **34 LLM Patterns** | Chain-of-Thought, RAG, ReAct, etc. | Production-ready patterns |
| **Hot-Swapping** | Zero-downtime package updates | Continuous operation |

### 5-Tier Hierarchical System

```
┌─────────────────────────────────────────┐
│         ECOSYSTEM TIER                  │  ← Company-wide knowledge
│    (Company-wide policies)              │
└──────────────────┬──────────────────────┘
                   │
         ┌─────────▼─────────┐
         │   COMPANY TIER    │              ← Organizational knowledge
         │ (Org standards)   │
         └─────────┬─────────┘
                   │
         ┌─────────▼─────────┐
         │     TEAM TIER     │              ← Team-specific practices
         │  (Team practices) │
         └─────────┬─────────┘
                   │
         ┌─────────▼─────────┐
         │   PROJECT TIER    │              ← Project context
         │ (Project context) │
         └─────────┬─────────┘
                   │
         ┌─────────▼─────────┐
         │   CLIENT TIER     │              ← User-specific customization
         │  (User-specific)  │
         └───────────────────┘
```

**Progressive Context Refinement Strategies:**
- **Bottom-Up**: Start specific (Client), progressively add broader context
- **Top-Down**: Start broad (Ecosystem), narrow to specific context
- **Hybrid**: Combine both based on query type and token budget

### Architecture Overview (Documented)

```
┌─────────────────────────────────────────────────────────────┐
│            MCP (Model Context Protocol) Platform            │
└─────────────────────────────────────────────────────────────┘

        ┌──────────────┐
        │ MCP Gateway  │  Unified API Entry (Port 5000)
        │              │  • Authentication
        └──────┬───────┘  • Rate limiting
               │
        ┌──────▼───────────┐
        │ MCP Interpreter  │  NLU → Structured Intents (5300)
        └──────┬───────────┘
               │
        ┌──────▼───────────┐
        │ MCP Composer     │  Multi-MCP Orchestration (5100)
        └──────┬───────────┘  • Conflict resolution
               │              • Routing strategies
               │
        ┌──────▼───────────┐
        │ MCP Orchestrator │  Pattern Execution (5200)
        │                  │  • 34 LLM patterns
        └──────┬───────────┘  • Workflow coordination
               │
     ┌─────────┼─────────────┬─────────┬─────────┐
     │         │             │         │         │
┌────▼───┐ ┌──▼───┐ ┌───────▼───┐ ┌──▼───┐ ┌───▼────┐
│MCP     │ │MCP   │ │MCP Tier   │ │MCP   │ │Package │
│Store   │ │Regis-│ │Manager    │ │Retri-│ │Manager │
│(5800)  │ │try   │ │(6200)     │ │eval  │ │(6300)  │
└────────┘ │(6000)│ └───────────┘ │(6100)│ └────────┘
           └──────┘                └──────┘
```

### MCP Services (Extensively Documented)

| Service | Port | Purpose | Status |
|---------|------|---------|--------|
| **mcp-gateway** | 5000 | Unified API entry point | 📋 Documented |
| **mcp-composer** | 5100 | Multi-MCP orchestration | 📋 Documented |
| **mcp-orchestrator** | 5200 | Pattern execution engine | 📋 Documented |
| **mcp-interpreter** | 5300 | NLU → structured intents | 📋 Documented |
| **mcp-provisioner** | 5400 | MCP lifecycle management | 📋 Documented |
| **mcp-store** | 5800 | Package storage ("Docker for Knowledge") | 📋 Documented |
| **mcp-registry** | 6000 | Package catalog | 📋 Documented |
| **mcp-retrieval** | 6100 | Hierarchical retrieval | 📋 Documented |
| **mcp-tier-manager** | 6200 | 5-tier system management | 📋 Documented |
| **mcp-package-manager** | 6300 | Package portability | 📋 Documented |
| **mcp_logs** | 6400 | Intelligent observability | 📋 Documented |
| **mcp_evergreen_docs** | 6500 | Self-healing docs | 📋 Documented |
| **mcp_local_llm** | 6600 | Local LLM platform | 📋 Documented |
| **mcp-dashboard** | 8015 | Web dashboard | 📋 Documented |

**Note:** MCP services are extensively documented with guides, architecture diagrams, and implementation specifications, but actual service implementations were not found during validation. This represents a planned/designed system rather than deployed services.

### 34 LLM Patterns

| Category | Patterns | Example Use Cases |
|----------|----------|-------------------|
| **Reasoning** (5) | Chain-of-Thought, Tree-of-Thought, Graph-of-Thought, ReAct, Self-Consistency | Logical problems, strategic planning |
| **Multi-Agent** (3) | Debate, Collaboration, Voting | Complex decisions, team problem-solving |
| **Self-Improvement** (3) | Self-Critique, Constitutional AI, Iterative Refinement | High-quality outputs, compliance |
| **RAG & Knowledge** (8) | Advanced RAG, Knowledge Graphs, Multi-Query RAG, Graph RAG | Question answering, knowledge retrieval |
| **Ensemble** (2) | Ensemble Orchestration, Ensemble Analysis | Multi-faceted problems, robustness |
| **Advanced** (10) | HITL, Uncertainty-Aware, Fallback Cascade, Context Pruning, etc. | Production systems, critical decisions |

### Typical Workflows (Conceptual)

#### Workflow 1: Hierarchical Context Retrieval
```
1. User submits query
2. MCP Gateway authenticates and routes
3. MCP Interpreter parses intent
4. MCP Tier Manager identifies relevant tiers
5. MCP Retrieval assembles context:
   - Query Client tier (user-specific)
   - Add Project tier (project context)
   - Add Team tier (team practices)
   - Add Company tier if needed
   - Include Ecosystem tier if relevant
6. Context Pruning applied (stay within token budget)
7. MCP Orchestrator executes selected pattern
8. Response returned with context provenance
```

#### Workflow 2: MCP Package Deployment
```
1. Developer creates MCP with knowledge
2. MCP Provisioner initializes package
3. MCP Store saves to SQLite + MinIO
4. MCP Registry registers version
5. Export .mcp file (TAR archive)
6. Transfer to target environment
7. MCP Package Manager imports
8. Hot-swap (zero downtime) deployment
9. Rollback capability if needed
```

### Use Cases (Conceptual)

**Primary Use Cases:**
- 📋 Hierarchical LLM context management
- 📋 Portable knowledge deployment (.mcp packages)
- 📋 Advanced RAG with 5-tier retrieval
- 📋 34 production-ready LLM patterns
- 📋 Progressive context refinement
- 📋 Zero-downtime knowledge updates

**Documentation:** Extensive guides available in `/docs/platform-mcp/`

---

## 🔗 Platform Relationship

### Shared Infrastructure

Both platforms share these components:

| Component | Purpose | Shared By |
|-----------|---------|-----------|
| **Redis** | Caching, event streaming, coordination | Both platforms |
| **Ollama** | Local LLM inference | Both platforms |
| **PostgreSQL** | Database storage | Both platforms |
| **LLM Gateway** | AI provider routing | Both platforms |
| **Log Collector** | Centralized logging | Both platforms |

### Independent Operation

Each platform has:
- **Own Orchestrator**: Document Analysis uses `orchestrator` (5099), MCP uses `mcp-orchestrator` (5200)
- **Own Services**: Distinct service sets with different responsibilities
- **Own Workflows**: Different use cases and workflows
- **Own Documentation**: Separate guide sets

### Complementary Relationship

```
┌─────────────────────────────────────────────────────────┐
│                    Shared Infrastructure                 │
│         Redis · Ollama · PostgreSQL · Monitoring        │
└─────────────────────────────────────────────────────────┘
             │                              │
    ┌────────▼────────┐          ┌─────────▼─────────┐
    │  Doc Analysis   │          │   MCP Platform    │
    │    Platform     │          │                   │
    │                 │          │   (Documented)    │
    │ (Production)    │          │                   │
    └─────────────────┘          └───────────────────┘
         Today                        Future/Concepts
```

**Strategy:**
1. **Phase 1 (Current)**: Production Document Analysis Platform
2. **Phase 2 (Future)**: Implement MCP services based on extensive documentation
3. **Phase 3 (Integration)**: Full integration of both platforms

---

## 📊 Decision Matrix: Which Platform?

| Your Need | Recommended Platform | Why |
|-----------|---------------------|-----|
| Documentation drift detection | Document Analysis | ✅ Production-ready now |
| Planning report generation | Document Analysis | ✅ Proven workflow |
| GitHub/Jira/Confluence integration | Document Analysis | ✅ Full multi-source support |
| User intelligence extraction | Document Analysis | ✅ SME identification algorithm |
| Hierarchical LLM context | MCP | 📋 Concepts available |
| Advanced RAG patterns | MCP | 📋 34 patterns documented |
| Portable knowledge packages | MCP | 📋 .mcp format spec available |
| 5-tier organizational context | MCP | 📋 Tier management documented |

---

## 🎯 Implementation Status

### Document Analysis Platform: ✅ Production Ready

**Fully Implemented:**
- All 15+ services deployed
- 200+ API endpoints
- 6 report generation workflows
- Multi-source ingestion (GitHub, Jira, Confluence)
- User intelligence extraction
- Comprehensive testing

**Deployment:** `bash restart_ecosystem_clean.sh`

### MCP Platform: 📋 Extensively Documented

**Available:**
- Complete architecture documentation
- 17 service specifications
- 34 LLM pattern implementations
- 12+ implementation guides
- API specifications
- Design patterns

**Status:** Documented and ready for implementation

---

## 🚀 Getting Started

### For Document Analysis Platform
1. Read [Quickstart](platform-document-analysis/QUICKSTART.md)
2. Deploy services: `bash restart_ecosystem_clean.sh`
3. Run demo: `python3 demo_hyper_realistic_parameterized.py`
4. View results in generated reports folder

### For MCP Platform
1. Read [MCP Architecture](platform-mcp/architecture/README.md)
2. Study [5-Tier System](platform-mcp/guides/5_TIER_SYSTEM_GUIDE.md)
3. Review [Pattern Index](platform-mcp/patterns/INDEX.md)
4. Plan implementation based on documentation

---

## 📚 Further Reading

### Document Analysis Platform
- [Architecture Guide](platform-document-analysis/architecture/README.md)
- [Service Catalog](platform-document-analysis/services/README.md)
- [Workflow Documentation](platform-document-analysis/workflows/README.md)

### MCP Platform
- [MCP Architecture Complete](platform-mcp/architecture/MCP_ARCHITECTURE_COMPLETE.md)
- [MCP Patterns Index](platform-mcp/patterns/MCP_PATTERNS_INDEX.md)
- [Hierarchical Retrieval Guide](platform-mcp/guides/HIERARCHICAL_RETRIEVAL_GUIDE.md)

### Shared Resources
- [Deployment Guide](shared/deployment/GUIDE.md)
- [Operations Manual](shared/operations/README.md)
- [Testing Strategy](shared/testing/README.md)

---

**This is a living document. Both platforms continue to evolve based on user needs and emerging patterns.**

---

*Last Updated: October 7, 2025*  
*Version: 2.0.0*  
*Maintained by: Platform Architecture Team*

