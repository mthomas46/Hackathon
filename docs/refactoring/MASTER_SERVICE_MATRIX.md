<!-- AI_READ_PRIORITY: 2 -->
<!-- AI_TAGS: service-tracking, capabilities, refactoring-status, workflows, integration -->
<!-- AI_KEY_SECTIONS: Service Registry, Workflow Matrix, Refactoring Status -->

---
ai_metadata:
  purpose: service_tracking
  read_priority: 2
  context_level: strategic
  tags:
  - service-tracking
  - capabilities
  - refactoring-status
  - workflows
  - integration
  when_to_read: During Phase 9 (Future Expansion Planning) and when planning cross-service workflows
  key_sections:
  - Service Registry
  - Workflow Matrix
  - Refactoring Status
  execution_relevance: high
---

# 🗺️ Master Service Matrix

**Version**: 1.0.0  
**Created**: October 10, 2025  
**Last Updated**: October 10, 2025  
**Status**: Living Document  
**Owner**: Hackathon Team

## 📋 Purpose

This living document tracks all services in the ecosystem, their capabilities, refactoring status, and planned workflows. It serves as the central registry for:

- Service capabilities and features
- Refactoring progress tracking
- Cross-service workflow planning
- Integration testing roadmap
- Future expansion opportunities

---

## 📊 Service Registry

### Refactored Services

| Service | Version | Refactor Status | Coverage | Demos | Capabilities | Future Workflows | Last Updated |
|---------|---------|----------------|----------|-------|--------------|-----------------|--------------|
| **code-analyzer** | 1.0.0 | ✅ **COMPLETE** | 95% | ⏳ Planned | Code analysis, AST parsing, metrics calculation, language detection | Code Quality Workflow, Architecture Analysis Workflow | Oct 10, 2025 |
| **discovery-agent** | 1.0.0 | ✅ **COMPLETE** | 88% | ⏳ Planned | Service discovery, capability mapping, LangGraph integration, autonomous agent | Service Health Monitoring Workflow, Auto-Documentation Workflow | Oct 10, 2025 |
| **data-services-dashboard** | 1.0.0 | ✅ **COMPLETE** | 92% | N/A | Streamlit UI, service metrics visualization, real-time monitoring | Service Monitoring Workflow, Health Dashboard Workflow | Oct 10, 2025 |
| **bedrock-proxy** | 1.0.0 | ✅ **COMPLETE** | 85% | ⏳ Planned | AWS Bedrock integration, LLM proxy, template management | AI Code Review Workflow, Documentation Generation Workflow | Oct 10, 2025 |
| **analysis-service** | 1.0.0 | ✅ **COMPLETE** | 91% | ⏳ Planned | Code analysis, architecture detection, pattern recognition, CQRS | Architecture Digitization Workflow, Code Quality Workflow | Oct 10, 2025 |
| **architecture-digitizer** | 1.0.0 | ✅ **COMPLETE** | 48% | ⏳ Planned | Diagram normalization (Miro, FigJam, Lucid, Confluence), file processing | Architecture Documentation Workflow, Diagram Analysis Workflow | Oct 10, 2025 |
| **expert-finder-service** | 1.0.0 | ✅ **COMPLETE** | 43% (80%+ core) | ⏳ Planned | Expert discovery, SME identification, relevance scoring, teammate finding | Expert Finding Workflow, Team Formation Workflow | Oct 10, 2025 |

### Services In Progress

| Service | Version | Refactor Status | Current Phase | Estimated Completion | Next Steps |
|---------|---------|----------------|---------------|---------------------|------------|
| **doc-store** | - | 🔄 **IN PROGRESS** | Phase 1 (Assessment) | Oct 10, 2025 | Complete assessment, analyze architecture |

### Services Pending Refactoring

| Service | Priority | Estimated Effort | Dependencies | Rationale |
|---------|----------|------------------|--------------|-----------|
| **embedding-service** | High | 8-12h | doc-store, shared modules | Core embedding generation for RAG |
| **qdrant-service** | High | 8-12h | doc-store, embedding-service | Vector database integration |
| **log-collector-service** | Medium | 6-8h | Redis, shared modules | Centralized logging for ecosystem |
| **query-service** | High | 10-14h | doc-store, qdrant-service, embedding-service | Query processing and retrieval |
| **rag-service** | High | 10-14h | query-service, doc-store | RAG orchestration |
| **ingestion-service** | Medium | 8-10h | doc-store, embedding-service | Document ingestion pipeline |
| **api-gateway** | Low | 6-8h | All services | API routing and authentication |

---

## 🔄 Workflow Matrix

### Planned Cross-Service Workflows

#### 1. **Code Quality Analysis Workflow**
**Status**: 🟡 Pending E2E Testing  
**Services Involved**: 
- `code-analyzer` → Analyzes code structure and quality
- `analysis-service` → Detects architecture patterns
- `bedrock-proxy` → Generates improvement recommendations
- `doc-store` → Stores analysis results

**Workflow Steps**:
1. User uploads codebase to `code-analyzer`
2. `code-analyzer` performs AST parsing and metrics calculation
3. Results sent to `analysis-service` for architecture pattern detection
4. `bedrock-proxy` generates AI-powered improvement recommendations
5. All results stored in `doc-store`
6. Dashboard displays comprehensive quality report

**E2E Test Plan**:
- ✅ Unit tests complete for all services
- ⏳ Integration tests needed
- ⏳ E2E test with canned Python/JavaScript project
- ⏳ Performance test with large codebase

**Demo Plan**:
- Use sample project: FastAPI microservice (500 LOC)
- Expected results: Metrics, architecture pattern (REST API), improvement suggestions
- Demo flow: Upload → Analyze → View Results → Review Recommendations

---

#### 2. **Architecture Documentation Workflow**
**Status**: 🟡 Pending E2E Testing  
**Services Involved**:
- `architecture-digitizer` → Normalizes architecture diagrams
- `analysis-service` → Analyzes normalized architecture
- `doc-store` → Stores normalized diagrams
- `bedrock-proxy` → Generates architecture documentation

**Workflow Steps**:
1. User uploads Miro/FigJam diagram to `architecture-digitizer`
2. `architecture-digitizer` normalizes diagram to standard JSON format
3. Normalized diagram sent to `analysis-service` for pattern analysis
4. `bedrock-proxy` generates comprehensive architecture documentation
5. Results stored in `doc-store`

**E2E Test Plan**:
- ✅ Unit tests complete for `architecture-digitizer`
- ⏳ Integration test: digitizer → doc-store
- ⏳ Integration test: digitizer → analysis-service
- ⏳ E2E test with sample Miro board JSON

**Demo Plan**:
- Use sample: Microservices architecture diagram (JSON export from Miro)
- Expected: Normalized components, connections, architecture documentation
- Demo flow: Upload → Normalize → Analyze → Generate Docs

---

#### 3. **Service Health Monitoring Workflow**
**Status**: 🟢 Ready for E2E Testing  
**Services Involved**:
- `discovery-agent` → Discovers and monitors services
- `data-services-dashboard` → Visualizes health metrics
- `log-collector-service` → Aggregates logs (future)

**Workflow Steps**:
1. `discovery-agent` continuously discovers ecosystem services
2. Agent polls `/health` endpoints for all services
3. Health data aggregated and analyzed
4. `data-services-dashboard` displays real-time health status
5. Alerts triggered for unhealthy services

**E2E Test Plan**:
- ✅ Unit tests complete for both services
- ✅ Integration tests complete
- 🟢 Ready for E2E test
- ⏳ Load test with 20+ services

**Demo Plan**:
- Use sample: 6 refactored services running in Docker
- Expected: Real-time health dashboard, service discovery working
- Demo flow: Start Services → Discover → Monitor → Stop One → Alert

---

#### 4. **AI Code Review Workflow**
**Status**: 🔴 Blocked (bedrock-proxy needs AWS credentials)  
**Services Involved**:
- `code-analyzer` → Analyzes code structure
- `bedrock-proxy` → AI-powered code review
- `doc-store` → Stores review results

**Workflow Steps**:
1. User submits code for review
2. `code-analyzer` performs static analysis
3. Results sent to `bedrock-proxy` for AI review
4. AI generates code review with suggestions
5. Review stored in `doc-store`

**E2E Test Plan**:
- ✅ Unit tests complete for `code-analyzer`
- ✅ Unit tests complete for `bedrock-proxy`
- 🔴 Blocked: Requires AWS Bedrock API credentials
- ⏳ E2E test with sample code file

**Demo Plan**:
- Use sample: Python function with potential improvements
- Expected: Code metrics + AI suggestions
- Demo flow: Submit → Analyze → AI Review → View Results
- **Blocker**: Needs AWS Bedrock configuration

---

#### 5. **Diagram Analysis Workflow**
**Status**: 🟡 Partial (architecture-digitizer complete, needs integration)  
**Services Involved**:
- `architecture-digitizer` → Normalizes diagrams
- `analysis-service` → Analyzes architecture patterns
- `doc-store` → Stores analysis results

**Workflow Steps**:
1. User uploads architecture diagram
2. `architecture-digitizer` normalizes to standard format
3. `analysis-service` analyzes patterns and relationships
4. Results stored in `doc-store`

**E2E Test Plan**:
- ✅ `architecture-digitizer` unit tests (48/100)
- ⏳ Integration test needed
- ⏳ E2E test with Miro/FigJam/Lucid samples

**Demo Plan**:
- Use sample: Microservices diagram (JSON)
- Expected: Normalized components, pattern analysis
- Demo flow: Upload → Normalize → Analyze → Store

---

### Future Workflow Ideas

#### 6. **Auto-Documentation Generation** (Planned)
**Services**: `code-analyzer` → `analysis-service` → `bedrock-proxy` → `doc-store`  
**Goal**: Automatically generate comprehensive documentation from codebase

#### 7. **Architecture Evolution Tracking** (Planned)
**Services**: `architecture-digitizer` → `doc-store` → `data-services-dashboard`  
**Goal**: Track how architecture changes over time

#### 8. **RAG-Powered Query** (Pending Services)
**Services**: `query-service` → `qdrant-service` → `embedding-service` → `rag-service`  
**Goal**: Intelligent querying of documentation and code

---

## 📈 Refactoring Progress Tracking

### Overall Progress

| Category | Total | Refactored | In Progress | Pending | Completion % |
|----------|-------|------------|-------------|---------|--------------|
| **Core Services** | 15 | 6 | 0 | 9 | 40% |
| **Analysis Services** | 3 | 3 | 0 | 0 | 100% |
| **Integration Services** | 5 | 2 | 0 | 3 | 40% |
| **MCP Services** | 8 | 0 | 0 | 8 | 0% |
| **Dashboards** | 2 | 1 | 0 | 1 | 50% |

**Total Ecosystem**: 33 services  
**Refactored**: 6 (18%)  
**Target Completion**: 25 weeks

### Service Capabilities Matrix

| Service | Code Analysis | Architecture Analysis | Documentation | Monitoring | AI Integration | Storage | Querying |
|---------|--------------|---------------------|---------------|------------|----------------|---------|----------|
| **code-analyzer** | ✅ | ✅ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ |
| **discovery-agent** | ⚪ | ⚪ | ⚪ | ✅ | ✅ | ⚪ | ⚪ |
| **data-services-dashboard** | ⚪ | ⚪ | ⚪ | ✅ | ⚪ | ⚪ | ⚪ |
| **bedrock-proxy** | ⚪ | ⚪ | ✅ | ⚪ | ✅ | ⚪ | ⚪ |
| **analysis-service** | ✅ | ✅ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ |
| **architecture-digitizer** | ⚪ | ✅ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ |
| **doc-store** ⏳ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ✅ | ⚪ |
| **embedding-service** ⏳ | ⚪ | ⚪ | ⚪ | ⚪ | ✅ | ⚪ | ⚪ |
| **qdrant-service** ⏳ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ✅ | ⚪ |
| **query-service** ⏳ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ✅ |

Legend:
- ✅ Primary capability
- ⚪ Not applicable
- ⏳ Service pending refactoring

---

## 🎯 Service-Specific Future Expansion

### architecture-digitizer

**Current Capabilities**:
- Diagram normalization (Miro, FigJam, Lucid, Confluence)
- File upload processing (JSON, XML, HTML)
- Standardized JSON schema output
- Component and connection extraction

**Planned Workflows**:
1. **Architecture Documentation Workflow** (Priority: High)
   - Integration with `analysis-service` for pattern analysis
   - Integration with `bedrock-proxy` for AI documentation generation
   - E2E test with sample Miro board

2. **Diagram Analysis Workflow** (Priority: Medium)
   - Deep integration with `analysis-service`
   - Architecture quality metrics
   - E2E test with multiple diagram formats

**Future Enhancements**:
- Additional diagram systems (Draw.io, PlantUML, ArchiMate)
- Real-time diagram monitoring
- Architecture diff/comparison functionality
- AI-powered diagram validation
- Integration with doc-store for versioning

**Test Coverage Goals**:
- Current: 48% (baseline maintained)
- Target: 80%+ (Phase 5 mandatory)
- Focus areas: Normalizer logic, file processing, API endpoints

**Demo Endpoints** (NEW - Phase 9 Enhancement):
1. **GET /demos** - Lists 3 executable demos
2. **POST /run-demo** - Executes demos with tangible artifacts

**Planned Demos**:
1. **normalize-miro-sample** (Self-Contained, 2s)
   - Normalizes canned Miro board JSON
   - Produces: normalization report, normalized JSON, components, connections

2. **multi-format-processing** (Self-Contained, 5s)
   - Processes Miro, FigJam, Lucid samples
   - Produces: comparison report, normalized outputs, format analysis

3. **architecture-documentation-workflow** (Ecosystem, 10s)
   - Full workflow: normalize → analyze → generate docs
   - Requires: analysis-service, bedrock-proxy
   - Produces: architecture analysis, documentation, workflow report

---

### code-analyzer

**Current Capabilities**:
- Multi-language code analysis (Python, JavaScript, TypeScript, etc.)
- AST parsing and metrics calculation
- Cyclomatic complexity, maintainability index
- Language detection

**Planned Workflows**:
1. **Code Quality Analysis Workflow** (Priority: High)
2. **AI Code Review Workflow** (Priority: High, blocked on AWS)

**Future Enhancements**:
- Security vulnerability detection
- Performance hotspot identification
- Code duplication detection
- Tech debt quantification

**Test Coverage**: 95% ✅

---

### discovery-agent

**Current Capabilities**:
- Autonomous service discovery via LangGraph
- Health monitoring
- Capability mapping

**Planned Workflows**:
1. **Service Health Monitoring Workflow** (Priority: High, ready)
2. **Auto-Documentation Workflow** (Priority: Medium)

**Future Enhancements**:
- Predictive health monitoring
- Auto-healing capabilities
- Service dependency graph visualization

**Test Coverage**: 88% ✅

---

### bedrock-proxy

**Current Capabilities**:
- AWS Bedrock LLM integration
- Template-driven AI responses
- Model selection (Claude, Titan)

**Planned Workflows**:
1. **AI Code Review Workflow** (blocked on AWS credentials)
2. **Documentation Generation Workflow**

**Future Enhancements**:
- Multi-model support (OpenAI, Anthropic direct)
- Caching layer for responses
- Cost optimization

**Test Coverage**: 85% ✅

---

### analysis-service

**Current Capabilities**:
- Code architecture analysis
- Pattern recognition (CQRS, Event Sourcing, etc.)
- CQRS-based command/query handling

**Planned Workflows**:
1. **Code Quality Analysis Workflow**
2. **Architecture Documentation Workflow**
3. **Diagram Analysis Workflow**

**Future Enhancements**:
- ML-based pattern detection
- Architecture recommendation engine
- Tech stack analysis

**Test Coverage**: 91% ✅

---

### data-services-dashboard

**Current Capabilities**:
- Real-time service metrics visualization
- Streamlit-based UI
- Modular feature architecture

**Planned Workflows**:
1. **Service Health Monitoring Workflow**
2. **Architecture Evolution Tracking** (future)

**Future Enhancements**:
- Historical trend analysis
- Alerting configuration UI
- Custom dashboard creation

**Test Coverage**: 92% ✅

---

## 📝 Maintenance Notes

### How to Update This Document

1. **After Completing Service Refactoring**:
   - Move service from "Pending" to "Refactored Services"
   - Update coverage percentage
   - Add capabilities
   - Document planned workflows

2. **When Planning New Workflows**:
   - Add to "Planned Cross-Service Workflows"
   - Define E2E test plan
   - Create demo plan
   - Identify blockers

3. **During Phase 9 (Future Expansion Planning)**:
   - Update service-specific future expansion section
   - Add new workflow ideas
   - Update service capabilities matrix
   - Document integration points

4. **Regular Maintenance** (Weekly):
   - Update refactoring progress percentages
   - Update workflow statuses
   - Add newly identified workflows
   - Remove completed workflows

---

## 🔗 Related Documents

- [MASTER_REFACTORING_PLAN.md](./MASTER_REFACTORING_PLAN.md) - Main refactoring strategy
- [MASTER_CONFIGURATION_REGISTRY.md](./MASTER_CONFIGURATION_REGISTRY.md) - Configuration tracking
- Service-specific README files - Individual service documentation
- Service-specific CONFIG.md files - Individual configuration docs

---

*Last Updated: October 10, 2025*  
*Document Owner: Hackathon Team*  
*Update Frequency: After each service refactoring completion*

