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
  - microservices
  - domain_driven_design
  - cqrs
  - event_sourcing
  - service_mesh
  - api_gateway
  - bounded_contexts
  - redis
  - langgraph
  - ollama
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

# 🚀 LLM Documentation Ecosystem - Complete API Index

**Total Services**: 17  
**Total API Endpoints**: 350+  
**Architecture**: Domain-Driven Design with Microservices  
**Last Updated**: September 18, 2025

---

## 📊 **API Overview by Service**

| Service | Endpoints | Port | Health | Documentation | Primary Function |
|---------|-----------|------|--------|---------------|------------------|
| **Frontend** | 120+ | 3000 | ✅ | ✅ [README](services/frontend/README.md) | Complete UI & Dashboard |
| **Prompt Store** | 101+ | 5110 | ✅ | ✅ [README](services/prompt_store/README.md) | Advanced Prompt Management |
| **Analysis Service** | 53+ | 5020 | ✅ | ✅ [README](services/analysis-service/README.md) | Document Analysis & DDD |
| **Interpreter** | 18+ | 5120 | ✅ | ✅ [README](services/interpreter/README.md) | Natural Language Processing |
| **LLM Gateway** | 15+ | 5055 | ✅ | ✅ [README](services/llm-gateway/README.md) | AI Provider Management |
| **Summarizer Hub** | 9+ | 5100 | ✅ | ✅ [README](services/summarizer-hub/README.md) | Multi-Provider Summarization |
| **Discovery Agent** | 5+ | 5045 | ✅ | ✅ [README](services/discovery-agent/README.md) | Service Discovery |
| **Log Collector** | 5+ | 5080 | ✅ | ✅ [README](services/log-collector/README.md) | Event Monitoring |
| **Notification Service** | 5+ | 5095 | ✅ | ✅ [README](services/notification-service/README.md) | Messaging & Alerts |
| **Source Agent** | 5+ | 5000 | ✅ | ✅ [README](services/source-agent/README.md) | Data Ingestion |
| **Architecture Digitizer** | 4+ | 5105 | ✅ | ✅ [README](services/architecture-digitizer/README.md) | Architecture Analysis |
| **GitHub MCP** | 4+ | 5072 | ✅ | ✅ [README](services/github-mcp/README.md) | GitHub Integration |
| **Mock Data Generator** | 4+ | 5065 | ✅ | ⚠️ Basic | LLM Data Generation |
| **Secure Analyzer** | 4+ | 5070 | ✅ | ✅ [README](services/secure-analyzer/README.md) | Security Analysis |
| **Memory Agent** | 3+ | 5040 | ✅ | ✅ [README](services/memory-agent/README.md) | Context Management |
| **Orchestrator** | 3+ | 5099 | ✅ | ✅ [README](services/orchestrator/README.md) | Workflow Coordination |
| **Doc Store** | 2+ | 5087 | ✅ | ✅ [README](services/doc_store/README.md) | Document Storage |
| **Bedrock Proxy** | 2+ | 7090 | ✅ | ✅ [README](services/bedrock-proxy/README.md) | AWS AI Access |
| **Code Analyzer** | 2+ | 5130 | ✅ | ✅ [README](services/code-analyzer/README.md) | Code Quality |

---

## 🎯 **Core API Categories**

### **🔧 Management & Operations (200+ endpoints)**

#### **Frontend Service** - Complete Ecosystem UI
**Port**: `3000` | **Endpoints**: `120+` | **Status**: ✅ Production Ready

**Key Capabilities**:
- Complete dashboard for all 17 services
- Interactive service monitoring and health checks
- Data browsing for doc store and prompt store
- CLI terminal interface and command execution
- Comprehensive reporting and analytics dashboards

**Major Endpoint Groups**:
```bash
# UI Pages (30+ endpoints)
GET /                          # Main dashboard
GET /findings                  # Analysis findings
GET /report                    # Comprehensive reports
GET /services/overview         # Services dashboard
GET /cli/terminal             # CLI interface

# API Endpoints (90+ endpoints)  
GET /api/services/overview/{service}  # Service details
POST /api/cli/execute               # CLI command execution
GET /api/workflows/jobs/status      # Workflow monitoring
```

#### **Prompt Store Service** - Enterprise Prompt Management
**Port**: `5110` | **Endpoints**: `101+` | **Status**: ✅ Enterprise Grade

**Domain-Driven Architecture** with 11 bounded contexts:
- **Prompt Management**: CRUD, versioning, content validation
- **A/B Testing**: Automated prompt optimization and testing
- **Analytics**: Performance metrics and cost optimization
- **Orchestration**: Workflow integration and chains
- **Intelligence**: AI-powered prompt generation and analysis

**Key Endpoint Categories**:
```bash
# Core Management (15 endpoints)
POST /api/v1/prompts                    # Create prompt
GET /api/v1/prompts/{id}                # Get prompt
PUT /api/v1/prompts/{id}                # Update prompt
GET /api/v1/prompts                     # List prompts

# A/B Testing & Optimization (12 endpoints)
POST /api/v1/optimization/ab-tests      # Create A/B test
GET /api/v1/ab-tests/{id}/results       # Test results
POST /api/v1/optimization/variations    # Generate variations

# Analytics & Intelligence (17 endpoints)
GET /api/v1/analytics/dashboard         # Performance dashboard
POST /api/v1/intelligence/code/generate # AI generation
POST /api/v1/validation/bias-detect     # Bias detection
```

### **🤖 AI & Processing Services (50+ endpoints)**

#### **LLM Gateway** - Unified AI Access
**Port**: `5055` | **Endpoints**: `15+` | **Status**: ✅ Enterprise Ready

**Multi-Provider Support**: Ollama, OpenAI, Anthropic, AWS Bedrock, Grok

```bash
# Core LLM Operations
POST /query                    # Execute LLM query with routing
POST /chat                     # Conversational interactions
POST /embeddings               # Text embedding generation
POST /stream                   # Streaming responses

# Provider Management
GET /providers                 # List providers and status
GET /models                    # Available models
POST /batch                    # Batch query execution

# Operations
GET /cache/stats              # Cache performance
POST /cache/clear             # Cache management
GET /metrics                  # Usage metrics
```

#### **Interpreter Service** - Natural Language Processing
**Port**: `5120` | **Endpoints**: `18+` | **Status**: ✅ Document Persistence Ready

**End-to-End Workflow Processing** with document persistence:

```bash
# Query Processing
POST /execute-query                    # Natural language to workflow
POST /interpret-query                  # Query interpretation
GET /intents                          # Supported intents
GET /ecosystem/capabilities           # Service capabilities

# Workflow Execution  
POST /workflows/execute-direct         # Direct workflow execution
GET /workflows/templates               # Available templates
GET /workflows/{id}/trace             # Execution traces

# Document Persistence
GET /documents/{id}/download           # Download generated documents
GET /documents/{id}/provenance         # Document provenance
GET /documents/by-workflow/{name}      # Find documents by workflow

# Output Management
GET /outputs/formats                   # Supported formats
GET /execution/{id}/status            # Execution status
```

#### **Analysis Service** - Advanced Document Analysis
**Port**: `5020` | **Endpoints**: `53+` | **Status**: ✅ Complete DDD Implementation

**Comprehensive Analysis Capabilities**:

```bash
# Core Analysis
POST /analyze                         # Document consistency analysis
POST /analyze/semantic-similarity     # Semantic analysis
POST /analyze/sentiment               # Sentiment analysis
POST /analyze/quality                 # Quality assessment

# Advanced Features
POST /analyze/trends                  # Trend analysis
POST /analyze/risk                    # Risk assessment
POST /analyze/maintenance/forecast    # Maintenance forecasting
POST /remediate                       # Automated fixes

# Enterprise Features
POST /distributed/tasks               # Distributed processing
POST /repositories/analyze            # Multi-repo analysis
POST /workflows/events               # Workflow integration
```

### **🔗 Integration & Data Services (40+ endpoints)**

#### **Orchestrator Service** - Workflow Coordination
**Port**: `5099` | **Endpoints**: `3+` | **Status**: ✅ LangGraph Integrated

**6 Bounded Contexts** for complete workflow management:

```bash
# Core Orchestration
GET /health                           # Service health
POST /workflows/execute               # Execute workflows
GET /services/registry               # Service registry
```

#### **Doc Store** - Document Management
**Port**: `5087` | **Endpoints**: `2+` | **Status**: ✅ DDD Implementation

```bash
# Document Operations
GET /health                           # Service health
POST /documents                       # Store documents
GET /documents/{id}                   # Retrieve documents
```

#### **Discovery Agent** - Service Discovery
**Port**: `5045` | **Endpoints**: `5+` | **Status**: ✅ Enhanced Implementation

```bash
# Service Discovery
GET /health                           # Service health
POST /discover                       # Discover services
GET /tools                           # Available tools
POST /bulk-discovery                 # Bulk discovery
GET /network-config                  # Network configuration
```

### **🛡️ Security & Monitoring Services (20+ endpoints)**

#### **Secure Analyzer** - Security Analysis
**Port**: `5070` | **Endpoints**: `4+` | **Status**: ✅ Complete

```bash
# Security Operations
GET /health                           # Service health
POST /detect                         # Security detection
POST /suggest                        # Security suggestions
POST /summarize                      # Secure summaries
```

#### **Log Collector** - Event Monitoring
**Port**: `5080` | **Endpoints**: `5+` | **Status**: ✅ Complete

```bash
# Monitoring Operations
GET /health                           # Service health
POST /events                         # Log events
GET /metrics                         # System metrics
POST /alerts                         # Alert management
```

### **🔌 External Integration Services (30+ endpoints)**

#### **Source Agent** - Data Ingestion
**Port**: `5000` | **Endpoints**: `5+` | **Status**: ✅ Complete Integration

```bash
# Data Ingestion
GET /health                           # Service health
POST /fetch                          # Fetch data
POST /normalize                      # Normalize data
POST /analyze                        # Analyze sources
```

#### **GitHub MCP** - GitHub Integration
**Port**: `5072` | **Endpoints**: `4+` | **Status**: ✅ Complete

```bash
# GitHub Operations
GET /health                           # Service health
GET /tools                           # Available tools
POST /invoke                         # Invoke GitHub operations
```

---

## 🏗️ **Architecture Patterns**

### **Domain-Driven Design (DDD) Services**
- **Prompt Store**: 11 domain modules, complete CQRS
- **Analysis Service**: 4-layer architecture, 6 bounded contexts
- **Orchestrator**: 6 bounded contexts, event sourcing
- **Doc Store**: Document domain with versioning and relationships

### **Microservices Excellence**
- **Service Mesh**: 17 services with clear boundaries
- **Event-Driven**: Redis-based asynchronous communication
- **Health Monitoring**: Comprehensive health checks
- **API Gateway**: LLM Gateway for AI operations

### **Enterprise Patterns**
- **CQRS**: Command and query responsibility separation
- **Event Sourcing**: Complete audit trails
- **Dependency Injection**: Shared infrastructure
- **Cache Management**: Multi-level Redis caching

---

## 🚀 **Quick Start Guide**

### **Health Check All Services**
```bash
# Check all services
for port in 3000 5000 5020 5040 5045 5055 5065 5070 5072 5080 5087 5095 5099 5100 5105 5110 5120 5130 7090; do
  echo "Port $port: $(curl -s --max-time 3 http://localhost:$port/health | jq -r '.status // "ERROR"')"
done
```

### **Core API Testing**
```bash
# Test LLM Gateway
curl -X POST http://localhost:5055/query \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello world", "provider": "ollama"}'

# Test Interpreter
curl -X POST http://localhost:5120/execute-query \
  -H "Content-Type: application/json" \
  -d '{"query": "Generate a test document", "format": "json"}'

# Test Prompt Store
curl http://localhost:5110/api/v1/prompts?limit=5
```

### **Monitoring & Analytics**
```bash
# Service Overview
curl http://localhost:3000/api/services/overview

# LLM Gateway Metrics
curl http://localhost:5055/metrics

# Analysis Service Status
curl http://localhost:5020/health
```

---

## 📊 **API Statistics**

### **Endpoint Distribution**
- **Frontend**: 120+ endpoints (34% of total)
- **Prompt Store**: 101+ endpoints (29% of total)
- **Analysis Service**: 53+ endpoints (15% of total)
- **Other Services**: 76+ endpoints (22% of total)

### **Architecture Maturity**
- **Enterprise DDD**: 4 services (Prompt Store, Analysis, Orchestrator, Doc Store)
- **Complete Implementation**: 13 services
- **Professional Documentation**: 16/17 services (94%)
- **Health Monitoring**: 17/17 services (100%)

### **Business Value**
- **AI-First Capabilities**: Complete LLM infrastructure
- **Enterprise Patterns**: DDD, CQRS, Event Sourcing
- **Developer Experience**: Comprehensive APIs and documentation
- **Operational Excellence**: 100% service health and monitoring

---

**🎯 The LLM Documentation Ecosystem provides a comprehensive API surface with 350+ endpoints across 17 services, demonstrating enterprise-grade architecture with complete AI-first capabilities and professional documentation standards.**

**Next Steps**: [Service Integration Guide](docs/architecture/) | [API Testing Guide](docs/guides/TESTING_GUIDE.md) | [Developer Onboarding](DEVELOPER_ONBOARDING.md)
