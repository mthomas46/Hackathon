<!-- AI_READ_PRIORITY: 1 -->
<!-- AI_TAGS: strategy, methodology, phases, quality-gates, overview -->
<!-- AI_KEY_SECTIONS: Goals and Objectives, Refactoring Methodology, Quality Gates, Service Categories -->

---
ai_metadata:
  purpose: primary_strategy
  read_priority: 1
  context_level: strategic
  tags:
  - strategy
  - methodology
  - phases
  - quality-gates
  - overview
  when_to_read: Before starting any refactoring work
  key_sections:
  - Goals and Objectives
  - Refactoring Methodology
  - Quality Gates
  - Service Categories
  execution_relevance: critical
---

# 🏗️ Master Refactoring and Standardization Plan

**Version**: 1.7.0  
**Created**: October 8, 2025  
**Last Updated**: October 10, 2025  
**Status**: Active  
**Owner**: Hackathon Team

## 📝 Changelog

### v1.7.0 (October 10, 2025)
- 📚 **NEW: Phase 2.7 - Library Consolidation Analysis** (MANDATORY, 20-30 min)
  - Systematic identification of library opportunities
  - Decision framework for custom code vs libraries
  - Replace custom retry, HTTP, config, logging with standard libraries
  - Document recommendations by priority (Phase 3, 8, or 11)
- 📊 **NEW: MASTER_TECHNOLOGY_MATRIX.md** - Living document tracking all Python libraries
  - Tracks libraries across all services
  - Standardizes library choices
  - Identifies consolidation opportunities
  - Provides recommendations by use case
- 🎯 **Library Standards Defined**:
  - HTTP Client: `httpx` (replaces `requests`)
  - Retry: `tenacity` (replaces custom retry)
  - Config: `pydantic-settings` (replaces manual env loading)
  - Logging: `structlog` (replaces print/basic logging)
  - Testing: `pytest` + `faker` + `factory-boy`
- 🔧 **Phase 3 Impact**: Services now implemented with standard libraries from the start
- 📚 **Documentation**: See [LIBRARY_CONSOLIDATION_ENHANCEMENT.md](./LIBRARY_CONSOLIDATION_ENHANCEMENT.md)
- 📈 **Goal**: 90%+ services using standard libraries after refactoring

### v1.6.0 (October 10, 2025)
- ⚡ **MAJOR: Added Optimization & Tuning to ALL Phases** - Iterative improvement at every step
  - **Phase-Level Optimization** added to Phases 1-7 (15-30 min per phase)
  - Critical evaluation of work completed in each phase
  - Service-specific optimization based on service characteristics
  - Hardening (error handling, validation, logging)
  - Iteration and improvement before moving forward
- 🔧 **NEW: Phase 8 - Service Optimization & Hardening** (MANDATORY, 2-4 hours)
  - Configuration optimization (externalize all hardcoded values)
  - Quick wins implementation (3-5 per service: caching, retry, metrics)
  - Service-specific optimization strategies
  - Production hardening (validation, error handling, security)
  - Regression protection (test all optimizations)
  - Performance benchmarking (before/after)
- 🎯 **NEW: Phase 10 - Future Expansion Planning** (MANDATORY, from v1.5.0)
  - Workflow planning with E2E test plans
  - Functional demo plans with canned data
  - Demo endpoints (`/demos`, `/run-demo`)
  - MASTER_SERVICE_MATRIX.md updates
- 📊 **Phase Renumbering**:
  - Phase 5: Added Comprehensive Testing & Coverage (from v1.5.0)
  - Phase 8: Service Optimization & Hardening (NEW)
  - Phase 9: Service Validation (was Phase 7, still MANDATORY)
  - Phase 10: Future Expansion Planning (NEW, MANDATORY)
  - Phase 11: Enhancement & Optional Work (was Phase 8, still optional)
- ⏱️ **Timeline Updated**: 12-20 hours per service (was 10-16h)
  - +2-4h for phase-level optimizations
  - +2-4h for Phase 8 (Service Optimization)
- 📚 **Documentation**: See [OPTIMIZATION_AND_TUNING_ENHANCEMENT.md](./OPTIMIZATION_AND_TUNING_ENHANCEMENT.md)
- 🎁 **20+ Quick Wins Library** with code examples
- 🏗️ **ROI**: Additional time pays for itself through fewer production issues, better performance

### v1.5.0 (October 10, 2025)
- 🧪 **Added Phase 5: Comprehensive Testing & Coverage** (MANDATORY)
  - 50%+ code coverage required (target 80%+)
  - 100% happy-path coverage
  - Common edge cases covered
  - Service-specific TESTING_GUIDE.md
- 🚀 **Added Phase 9: Future Expansion Planning** (MANDATORY)
  - Audit MASTER_SERVICE_MATRIX.md
  - Plan workflows with E2E testing
  - Plan functional demos
  - Update service README with future expansion section
- 🎬 **Added Demo Endpoints** - Services must implement:
  - `GET /demos` - List executable demos
  - `POST /run-demo` - Execute demos programmatically
  - 3 demo types: self-contained, ecosystem, hybrid
- 📊 **Created MASTER_SERVICE_MATRIX.md** - Living document tracking all services
- 📚 **Documentation**: See [PLAN_ENRICHMENT_TESTING_AND_FUTURE_EXPANSION.md](./PLAN_ENRICHMENT_TESTING_AND_FUTURE_EXPANSION.md)
- 📚 **Documentation**: See [DEMO_ENDPOINTS_ENHANCEMENT.md](./DEMO_ENDPOINTS_ENHANCEMENT.md)

### v1.4.0 (October 10, 2025)
- 🚨 **CRITICAL: Added Mandatory Phase 7 - Service Validation** - Prevents shipping broken services
  - **Phase 7 is now MANDATORY** before marking any service complete
  - Comprehensive validation: Docker build, container startup, endpoint testing, full test suite
  - Quality gates: All tests must pass, coverage must be >= 80% (measured with pytest --cov)
  - Discovered in real execution: data-services-dashboard would have shipped broken without this
  - Based on critical audit of 3 service refactorings (see MASTER_PLAN_CRITICAL_AUDIT_AND_ENRICHMENT.md)
  - **Service is NOT complete until Phase 7 passes!**
- 📊 Renamed previous "Phase 7: Enhancement & Optional Work" to **Phase 8** (still optional)
- 📈 Updated methodology from 6-phase (+ optional 7) to 7-phase (+ optional 8)
- 🎯 Updated effort estimates: 8-12 hours per service (was 6-8h)
- ⚠️ Identified and fixed 10 critical flaws in previous plan
- 🏗️ Added architecture-specific guidance (DDD, Modular, Hybrid)
- ✅ Enhanced quality gates with measurable criteria
- 🔍 Validation catches: non-functional APIs, test failures, coverage gaps, Docker issues

### v1.3.0 (October 9, 2025)
- 🔀 **Integrated Git Checkpoints into All Phases** - Mandatory commits at phase boundaries
  - Added **Git Checkpoint** steps after each phase (1-6)
  - Detailed commit message templates for each phase
  - Alternative commit strategies for Phase 3 (split into 2 commits for large services)
  - Enforcement: AI agents MUST commit after each phase
  - Recovery: Git commits create rollback points
  - Quality: Meaningful, tangible commits (not micro-commits)
- 📋 Updated Git Commit Strategy enforcement
- ✅ Validated: 4 commits made for code-analyzer (recovered from 0)
- 🎯 Prevents data loss and enables rollback

### v1.2.0 (October 9, 2025)
- 🔧 **Added Configuration Management System** - Comprehensive config tracking and validation
  - Created [MASTER_CONFIGURATION_REGISTRY.md](./MASTER_CONFIGURATION_REGISTRY.md) - Living registry for all configs
  - Added Master Port & Network Matrix (prevents port conflicts)
  - Added Credentials & API Keys Registry
  - Standardized configuration files (.yml, .env, docker, docker-compose)
  - Defined service config profiles (dev, test, staging, prod)
  - Automated validation scripts (`check_port_conflicts.py`)
  - Per-service CONFIG.md template
  - AI agent integration for config management
- 📋 Integrated config management into Phase 1.1, 2.2, 5.1, and 6.1
- ✅ Automated preflight checks via Makefiles
- See [CONFIGURATION_MANAGEMENT_ENHANCEMENT.md](./CONFIGURATION_MANAGEMENT_ENHANCEMENT.md) for details

### v1.1.0 (October 9, 2025)
- ✨ **Added Phase 7: Enhancement & Optional Work** - Captures optional/skipped work for later enhancement
- 📖 Updated methodology from 6-phase to 7-phase (with Phase 7 being optional)
- 🎯 Based on real-world execution experience with `code-analyzer` service
- 📊 Enables 20-25% time savings by deferring non-critical work
- See [PHASE_7_ENHANCEMENT_ADDITION.md](./PHASE_7_ENHANCEMENT_ADDITION.md) for details

### v1.0.0 (October 8, 2025)
- 🎉 Initial comprehensive refactoring plan
- 📋 Defined 6-phase per-service methodology
- 🏗️ Established DDD and REST architecture standards
- ✅ Created quality gates and success metrics

---

## 📋 Table of Contents

1. [Changelog](#-changelog)
2. [Executive Summary](#executive-summary)
3. [Goals and Objectives](#goals-and-objectives)
4. [Guiding Principles](#guiding-principles)
5. [Architecture Standards](#architecture-standards)
6. [Refactoring Methodology](#refactoring-methodology)
7. [Service Categories](#service-categories)
8. [Refactoring Phases](#refactoring-phases)
9. [Quality Gates](#quality-gates)
10. [Documentation Requirements](#documentation-requirements)
11. [Success Metrics](#success-metrics)

---

## 🎯 Executive Summary

This document outlines a comprehensive, methodical approach to refactor and standardize all microservices in the Hackathon ecosystem. The plan follows Domain-Driven Design (DDD) principles, REST architecture, and Test-Driven Development (TDD) practices to transform the current services into a cohesive, maintainable, and scalable microservices architecture.

### Current State
- **50+ Services** with varying levels of standardization
- Mixed architectural patterns and naming conventions
- Inconsistent configuration management
- Varying levels of documentation
- Scripts and demos scattered across directories
- Suboptimal configurations (hardcoded values, no profiles)
- Missing quick wins (caching, retry, monitoring)

### Target State
- **Unified Architecture**: All services following DDD and REST principles
- **Consistent Standards**: Shared naming conventions and directory structures
- **High Quality**: Comprehensive test coverage with TDD approach + optimization at every phase
- **Well Documented**: Standardized documentation across all services
- **Organized Codebase**: Scripts integrated as utilities, demos as dedicated services
- **Production-Ready**: Fully optimized, hardened, and validated services
- **Observable**: Request tracking, metrics, comprehensive logging
- **Resilient**: Retry logic, circuit breakers, graceful degradation
- **Future-Proof**: Workflow planning, E2E tests, executable demos

---

## ⭐ v6.3 Update: Practical Learnings

**Status**: Plan has been tested and refined (October 9, 2025)

### What Works (Proven)
- ✅ **All 20+ automation scripts smoke tested** - 100% functional
- ✅ **Rollback safety** - Backup branches before destructive operations
- ✅ **Step definitions** - Centralized acceptance criteria in YAML
- ✅ **Basic integration tests** - Core workflows validated
- ✅ **Validation enforcement** - Cannot complete steps without passing checks

### Critical Protections in Place
1. **Auto-checkpointing** - Every 2 hours + phase boundaries
2. **Reality validation** - Prevents hallucinated step completion
3. **Context drift detection** - Monitors execution health
4. **Safe rollback** - Can recover from mistakes
5. **Stuck detection** - Alerts after 4 hours no progress

### Before Starting ANY Service
```bash
# 1. Smoke test all scripts (verify they work)
bash scripts/refactoring/test_smoke.sh

# 2. Run integration tests (verify workflows)
python3 tests/refactoring/test_integration_basic.py

# Both should pass before proceeding
```

### Execution Confidence: 70%
- **Risk Level**: 🟡 MEDIUM (down from 🔴 HIGH)
- **Production Ready**: ⚠️ Yes, with manual supervision
- **Recommended**: Pilot on one service first, then scale

**See**: `docs/refactoring/IMPLEMENTATION_COMPLETE_v6.3.md` for full details

---

## 🎯 Goals and Objectives

### Primary Goals

1. **Architectural Consistency**
   - Implement DDD architecture across all services
   - Ensure clean separation of concerns (Domain, Application, Infrastructure, Presentation)
   - Establish clear bounded contexts

2. **Code Quality**
   - Achieve 80%+ test coverage across all services
   - Reduce code complexity (cyclomatic complexity < 10)
   - Eliminate code duplication (DRY principle)

3. **Standardization**
   - Unified naming conventions
   - Consistent directory structures
   - Standardized configuration management
   - Uniform API patterns and documentation

4. **Operational Excellence**
   - Services run independently in terminal
   - Services run solo in Docker containers
   - Services integrate seamlessly in ecosystem
   - Comprehensive health checks and monitoring

5. **Documentation**
   - Complete API documentation with OpenAPI/Swagger
   - Service README with architecture diagrams
   - Integration guides and examples
   - Troubleshooting guides

### Secondary Goals

- Migrate scripts to appropriate service utilities
- Convert demos to dedicated demo services
- Organize shared/common resources
- Establish CI/CD standards
- Create development workflow documentation

---

## 🧭 Guiding Principles

### KISS (Keep It Simple, Stupid)
- Favor simplicity over cleverness
- Clear, readable code over concise but cryptic code
- Straightforward solutions over over-engineered ones
- Simple interfaces over complex abstractions

### TDD (Test-Driven Development)
- Write tests before implementation
- Red-Green-Refactor cycle for all features
- Tests as living documentation
- Continuous integration and testing

### DRY (Don't Repeat Yourself)
- Identify and eliminate code duplication
- Extract common functionality to shared libraries
- Use composition over inheritance
- Create reusable components

### SOLID Principles
- **S**ingle Responsibility Principle
- **O**pen/Closed Principle
- **L**iskov Substitution Principle
- **I**nterface Segregation Principle
- **D**ependency Inversion Principle

---

## 🏛️ Architecture Standards

### Domain-Driven Design (DDD) Structure

Every service must follow this layered architecture:

```
service-name/
├── domain/                    # Business logic layer
│   ├── entities/             # Core business entities
│   ├── value_objects/        # Immutable value objects
│   ├── aggregates/           # Aggregate roots
│   ├── services/             # Domain services
│   ├── events/               # Domain events
│   ├── repositories/         # Repository interfaces
│   └── exceptions/           # Domain-specific exceptions
├── application/              # Application logic layer
│   ├── use_cases/           # Business use cases (commands/queries)
│   ├── commands/            # CQRS commands
│   ├── queries/             # CQRS queries
│   ├── dtos/                # Data transfer objects
│   ├── services/            # Application services
│   └── validators/          # Input/business rule validators
├── infrastructure/          # External dependencies layer
│   ├── repositories/        # Repository implementations
│   ├── persistence/         # Database connections
│   ├── external_services/   # Third-party integrations
│   ├── messaging/           # Event bus, queues
│   └── config/              # Configuration management
├── presentation/            # API/Interface layer
│   ├── api/                 # REST API controllers
│   │   ├── routes/         # Route definitions
│   │   ├── controllers/    # Controller implementations
│   │   ├── middleware/     # API middleware
│   │   └── schemas/        # Request/response schemas
│   └── cli/                 # CLI commands (if applicable)
├── tests/                   # Test suite
│   ├── unit/               # Unit tests (per layer)
│   │   ├── domain/
│   │   ├── application/
│   │   ├── infrastructure/
│   │   └── presentation/
│   ├── integration/        # Integration tests
│   └── e2e/               # End-to-end tests
├── config/                  # Configuration files
│   ├── config.yaml         # Base configuration
│   ├── config.development.yaml
│   ├── config.production.yaml
│   └── config.test.yaml
├── docs/                    # Service documentation
│   ├── architecture.md     # Architecture diagrams
│   ├── api.md             # API documentation
│   ├── integration.md     # Integration guide
│   └── troubleshooting.md
├── utilities/              # Service-specific utilities
├── main.py                 # Application entry point
├── Dockerfile             # Docker configuration
├── docker-compose.yml     # Standalone compose file
├── requirements.txt       # Python dependencies
├── pytest.ini            # Test configuration
├── README.md             # Service documentation
└── .env.example          # Environment variable template
```

### REST API Standards

#### Endpoint Naming Conventions
```
GET    /resources              # List resources (with pagination)
GET    /resources/{id}         # Get single resource
POST   /resources              # Create new resource
PUT    /resources/{id}         # Update entire resource
PATCH  /resources/{id}         # Partial update
DELETE /resources/{id}         # Delete resource
GET    /resources/{id}/sub     # Get nested resources
POST   /resources/{id}/action  # Resource-specific action
```

#### HTTP Status Codes
- `200 OK` - Successful GET, PUT, PATCH, DELETE
- `201 Created` - Successful POST
- `204 No Content` - Successful DELETE with no response body
- `400 Bad Request` - Invalid input
- `401 Unauthorized` - Missing/invalid authentication
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `409 Conflict` - Resource conflict
- `422 Unprocessable Entity` - Validation errors
- `500 Internal Server Error` - Server error
- `503 Service Unavailable` - Service temporarily unavailable

#### OpenAPI/Swagger Annotations

All endpoints must have comprehensive OpenAPI documentation:

```python
from fastapi import APIRouter, Path, Query
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1", tags=["resources"])

class ResourceCreate(BaseModel):
    """Schema for creating a resource"""
    name: str
    description: str
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Example Resource",
                "description": "A sample resource"
            }
        }

@router.post(
    "/resources",
    response_model=ResourceResponse,
    status_code=201,
    summary="Create a new resource",
    description="Creates a new resource with the provided details",
    responses={
        201: {"description": "Resource created successfully"},
        400: {"description": "Invalid input"},
        409: {"description": "Resource already exists"}
    },
    tags=["resources"]
)
async def create_resource(resource: ResourceCreate):
    """
    Create a new resource with the following information:
    
    - **name**: The resource name (required)
    - **description**: A description of the resource (required)
    
    Returns the created resource with its assigned ID.
    """
    pass
```

---

## 📋 Refactoring Methodology

### Phase-Based Approach

Each service refactoring follows an **11-phase methodology** with:
- **Phases 1-10**: MANDATORY (cannot skip)
- **Phase 11**: OPTIONAL (enhancements)

**Key Features**:
- ⚡ **Optimization at Every Phase** (Phases 1-7): Critical evaluation, service-specific tuning, hardening
- 🔧 **Dedicated Optimization Phase** (Phase 8): Configuration optimization, quick wins, production hardening
- ✅ **Comprehensive Validation** (Phase 9): Docker + endpoint + test validation before marking complete
- 🚀 **Future Planning** (Phase 10): Workflow planning, E2E tests, executable demos

**Timeline**: 12-20 hours per service (10 mandatory phases + 1 optional)

#### Phase 1: Audit & Analysis (1-2 days)
**Objective**: Understand current state and dependencies

**Activities**:
1. **Service Audit**
   - Document current architecture
   - Identify all endpoints and functionality
   - Map dependencies (services it calls, services that call it)
   - Review current tests
   - Identify technical debt

2. **Configuration Audit** 🔧 *New in v1.2*
   - **READ** [MASTER_CONFIGURATION_REGISTRY.md](./MASTER_CONFIGURATION_REGISTRY.md)
   - Document current ports (HTTP, internal, gRPC, admin)
   - Check for port conflicts with other services
   - Identify credentials/API keys required
   - Review existing config files (.env, config.yaml, docker-compose.yml)
   - Document current profiles (dev, test, prod)
   - Note configuration issues or inconsistencies

3. **Dependency Analysis**
   - Map service interactions
   - Identify shared resources
   - Document data flows
   - Identify circular dependencies

4. **Gap Analysis**
   - Compare against DDD standards
   - Identify missing tests
   - Document configuration issues
   - Note documentation gaps

**Deliverables**:
- Service Audit Report
- Configuration Audit (ports, credentials, profiles)
- Dependency Map
- Gap Analysis Document
- Refactoring Scope Statement

---

### 1.N: Phase 1 Optimization & Critical Evaluation ⚡

**Duration**: 15-30 minutes

**Objective**: Ensure audit is complete and accurate

**Critical Questions**:
- [ ] Have we identified ALL dependencies (including hidden ones)?
- [ ] Have we checked for port conflicts thoroughly?
- [ ] Is the complexity assessment accurate?
- [ ] Are there hidden configuration files we missed?
- [ ] Is the refactoring scope realistic?

**Service-Specific Optimization**:
- **Data-Intensive Services**: Check database connections, query patterns, indexes
- **API Services**: Check rate limiting, timeout configurations, circuit breakers
- **Integration Services**: Check retry logic, fallback mechanisms, error handling
- **Real-Time Services**: Check WebSocket configurations, latency requirements
- **Background Workers**: Check queue configurations, batch sizes, worker pools

**Hardening**:
- Double-check all configuration sources (env vars, config files, Docker)
- Verify port conflicts with [MASTER_CONFIGURATION_REGISTRY.md](./MASTER_CONFIGURATION_REGISTRY.md)
- Re-scan codebase for missed dependencies
- Identify service-specific risks (data loss, security, performance)

**Iteration**:
- Update audit with any missed items
- Refine complexity assessment if needed
- Adjust refactoring scope based on findings
- Document service-specific considerations

**Quality Gate**: Audit is comprehensive, accurate, and service-specific

**Reference**: [OPTIMIZATION_AND_TUNING_ENHANCEMENT.md - Phase 1 Optimization](./OPTIMIZATION_AND_TUNING_ENHANCEMENT.md#phase-1-optimization-audit--analysis)

---

**Git Checkpoint** 🔀 *Required*:
```bash
# AI Agent MUST commit after Phase 1 completion
git add services/<service>/{audit_report,dependency_map,gap_analysis}.{md,json}
git commit -m "feat(<service>): Complete Phase 1 - Audit & Analysis

- Service structure audit
- Configuration audit (ports, credentials)
- Dependency mapping (providers/consumers)
- Gap analysis vs DDD standards
- Refactoring scope defined

Deliverables: 5
Status: Phase 1 complete"
```

---

#### Phase 2: Design & Planning (1 day)
**Objective**: Create detailed refactoring plan

**Activities**:
1. **Domain Modeling**
   - Identify domain entities
   - Define value objects
   - Map aggregates
   - Design domain events

2. **API Design & Configuration** 🔧 *Enhanced in v1.2*
   - Define REST endpoints
   - Create OpenAPI specification
   - Design request/response schemas
   - Plan versioning strategy
   - **Port Allocation:**
     - **READ** [MASTER_CONFIGURATION_REGISTRY.md](./MASTER_CONFIGURATION_REGISTRY.md)
     - Check port availability (run `check_port_conflicts.py`)
     - Allocate HTTP, internal, gRPC, admin ports
     - **UPDATE** registry with new port assignments
   - **Configuration Planning:**
     - Define required credentials/API keys
     - **UPDATE** credentials registry
     - Plan config profiles (dev, test, staging, prod)
     - Design environment variables
   - **Generate Service Configs:**
     - Create CONFIG.md from template
     - Create .env.template
     - Create config.yaml
     - Create/update docker-compose.yml entry
   - **Create Validation:**
     - Add Makefile with `validate-config` target
     - Add preflight checks
   - **RUN Preflight Checks:**
     - Execute `make validate-config`
     - Fix any configuration issues
     - **REQUIRED**: Must pass before completing step

3. **Test Planning**
   - Define test scenarios
   - Plan unit test structure
   - Design integration tests
   - Create E2E test cases

4. **Migration Strategy**
   - Plan backward compatibility
   - Define feature flags
   - Create rollback plan
   - Schedule deployment windows

**Deliverables**:
- Domain Model Diagram
- OpenAPI Specification
- **Service CONFIG.md** (generated from template) 🔧 *New*
- **Updated MASTER_CONFIGURATION_REGISTRY.md** 🔧 *New*
- **Service Makefile with validation** 🔧 *New*
- Test Plan Document
- Migration Strategy Document

---

### 2.7: Library Consolidation Analysis ⚡ **NEW in v1.7.0**

**Duration**: 20-30 minutes

**Objective**: Identify opportunities to simplify code by leveraging Python libraries instead of custom implementations

**Note**: This step was added in v1.7.0 to systematically identify where well-tested libraries can replace custom code, reducing maintenance burden and improving code quality.

**Activities**:

#### Step 1: Read MASTER_TECHNOLOGY_MATRIX.md

**Action**:
```bash
# AI Agent: Read the technology matrix
READ: docs/refactoring/MASTER_TECHNOLOGY_MATRIX.md
```

**Purpose**:
- Understand standard library choices across ecosystem
- Learn what other services are using
- See consolidation opportunities already identified

#### Step 2: Audit Current Service Technology

**For Existing Services**:
- Review `requirements.txt` or `pyproject.toml`
- Identify custom implementations:
  - Retry logic
  - Configuration loading
  - HTTP clients
  - Caching mechanisms
  - Logging
- Note use of outdated libraries (`requests` vs `httpx`)

**For New Services**:
- List planned functionality
- Check if libraries exist for each area

**Document in**: `PHASE_2_LIBRARY_AUDIT.md`

#### Step 3: Apply Decision Framework

**For each functionality, ask**:

1. **Is there custom code?**
   - NO → Check if using standard library ✅
   - YES → Continue to #2

2. **Is it domain-specific?**
   - YES → Keep custom code ✅ (e.g., scoring algorithms, normalizers)
   - NO → Continue to #3

3. **Does a good library exist?**
   - NO → Keep custom code, document why
   - YES → Continue to #4

4. **Is the library**:
   - Well-maintained? (updates within 6 months)
   - Widely used? (high downloads, active community)
   - Better than custom code? (features, performance, testing)
   
   **ALL YES** → Recommend library
   **ANY NO** → Keep custom code

5. **What's the migration effort?**
   - **LOW** (< 1 hour) → Implement in Phase 3
   - **MEDIUM** (1-4 hours) → Implement in Phase 8
   - **HIGH** (> 4 hours) → Mark as Phase 11 (optional)

**Common Categories**:

| Functionality | Custom Code | Standard Library | Effort |
|---------------|-------------|------------------|--------|
| HTTP Client | Manual `requests` | `httpx.AsyncClient` | LOW |
| Retry Logic | Custom decorators | `tenacity.retry` | LOW |
| Configuration | Manual `os.getenv()` | `pydantic-settings` | LOW |
| Logging | `print`, basic `logging` | `structlog` | MEDIUM |
| Caching | Manual dicts | `lru_cache`, `cachetools` | LOW |
| Validation | Manual checks | `pydantic.BaseModel` | LOW |
| Test Data | Hardcoded | `faker`, `factory-boy` | MEDIUM |

#### Step 4: Document Recommendations

**Create**: `PHASE_2_LIBRARY_RECOMMENDATIONS.md`

**Format for each recommendation**:
```markdown
### [Priority Level]: [Custom Code] → [Library Name]

**Current State**: [What exists now]

**Recommended Library**: [Library name + version]

**Benefits**:
- [Benefit 1]
- [Benefit 2]
- [Benefit 3]

**Effort**: [LOW/MEDIUM/HIGH] ([time estimate])

**Decision**: 
- ✅ Implement in Phase 3 (if LOW effort)
- ⚠️ Implement in Phase 8 (if MEDIUM effort)
- ⏸️ Mark as Phase 11 optional (if HIGH effort)
- ❌ Keep custom code (if domain-specific)

**Rationale**: [Why this decision]

**Code Example**: [Before/After code snippet]
```

#### Step 5: Update Requirements

**Action**: Update `requirements.txt` with recommended libraries

**Example additions**:
```txt
# Standard Libraries (Phase 2.7 recommendations)
httpx==0.25.2          # Async HTTP client (replaces requests)
tenacity==8.2.3        # Retry with backoff (replaces custom retry)
pydantic-settings==2.1.0  # Config management (replaces manual env loading)
structlog==23.2.0      # Structured logging (replaces print statements)
faker==20.1.0          # Test data generation (Phase 8)
factory-boy==3.3.0     # Test fixtures (Phase 8)
```

#### Step 6: Update MASTER_TECHNOLOGY_MATRIX.md

**Action**: Add service entry to technology matrix

**Example**:
```markdown
### Service: {service-name}

| Category | Technology | Version | Purpose | Consolidation Opportunity |
|----------|-----------|---------|---------|---------------------------|
| Framework | FastAPI | 0.104+ | REST API | ✅ Standard |
| HTTP Client | httpx | 0.25+ | External calls | ✅ Standard (new) |
| Validation | Pydantic | 2.4+ | Data validation | ✅ Standard |
| Config | pydantic-settings | 2.0+ | Configuration | ✅ Standard (new) |
| Retry | tenacity | 8.2+ | Retry logic | ✅ Standard (new) |
| Logging | structlog | 23.2+ | JSON logging | ✅ Standard (new) |
| Testing | pytest + faker | 7.4+ | Tests | ✅ Standard |
| Domain Logic | Custom | N/A | [Description] | ✅ Appropriate (domain-specific) |

**Custom Code to Consolidate**: [List any remaining custom code]

**Library Opportunities**: [Note any Phase 11 opportunities]
```

**Deliverables**:
1. ✅ `PHASE_2_LIBRARY_AUDIT.md` - Current technology audit
2. ✅ `PHASE_2_LIBRARY_RECOMMENDATIONS.md` - Library recommendations with decisions
3. ✅ Updated `requirements.txt` - With new libraries added
4. ✅ Updated `MASTER_TECHNOLOGY_MATRIX.md` - Service entry added

**Quality Gates**:
- [ ] All custom code identified and evaluated
- [ ] Library recommendations documented with effort estimates
- [ ] HIGH priority (LOW effort) libraries marked for Phase 3
- [ ] MEDIUM priority (MEDIUM effort) libraries marked for Phase 8
- [ ] LOW priority (HIGH effort) libraries marked for Phase 11
- [ ] Domain-specific custom code marked to keep (with rationale)
- [ ] MASTER_TECHNOLOGY_MATRIX.md updated

**Reference**: [LIBRARY_CONSOLIDATION_ENHANCEMENT.md](./LIBRARY_CONSOLIDATION_ENHANCEMENT.md)

---

### 2.N: Phase 2 Optimization & Critical Evaluation ⚡

**Duration**: 15-30 minutes

**Objective**: Ensure design is optimal for THIS specific service

**Critical Questions**:
- [ ] Is this the best architecture for THIS service's needs?
- [ ] Are we over-engineering or under-engineering?
- [ ] Does the design leverage the service's strengths?
- [ ] Are there simpler approaches we're missing?
- [ ] Have we considered performance implications?
- [ ] Is the API design optimal for expected use cases?

**Service-Specific Optimization**:
- **Stateless Services**: Optimize for horizontal scaling, minimal per-request state
- **Stateful Services**: Design proper state management, persistence strategies
- **Heavy I/O Services**: Design for async/await patterns, connection pooling
- **Compute-Heavy Services**: Consider worker pools, batch processing
- **Real-Time Services**: Optimize for low latency, WebSocket design
- **Integration Services**: Plan circuit breakers, retry strategies, fallbacks

**Hardening**:
- Review domain model for simplicity (avoid over-abstraction)
- Validate repository patterns match service needs
- Optimize API design for service's primary use cases
- Identify potential performance bottlenecks in design
- Ensure error handling strategy is comprehensive

**Iteration**:
- Simplify domain model if over-complex
- Refine API design based on use cases
- Optimize config strategy for service needs
- Update test plan to cover identified risks
- Adjust migration strategy if needed

**Quality Gate**: Design is optimal, simple, and service-specific

**Reference**: [OPTIMIZATION_AND_TUNING_ENHANCEMENT.md - Phase 2 Optimization](./OPTIMIZATION_AND_TUNING_ENHANCEMENT.md#phase-2-optimization-design--planning)

---

**Git Checkpoint** 🔀 *Required*:
```bash
# AI Agent MUST commit after Phase 2 completion
git add services/<service>/design/ services/<service>/CONFIG.md
git commit -m "feat(<service>): Complete Phase 2 - Design & Planning

- Domain model with DDD architecture
- OpenAPI specification
- Configuration planning (ports, profiles, secrets)
- Service CONFIG.md generated
- Test plan defined
- Migration strategy documented

Config: Ports allocated, validated
Registry: Updated with service
Deliverables: 6
Status: Phase 2 complete"
```

---

#### Phase 3: TDD Implementation (3-5 days)
**Objective**: Implement refactored service following TDD

**Activities**:
1. **Red Phase - Write Failing Tests**
   - Domain entity tests
   - Use case tests
   - Repository tests
   - API endpoint tests
   - **Target**: 80%+ coverage of core features
   - **Reference**: [Comprehensive Testing Strategy](./COMPREHENSIVE_TESTING_STRATEGY.md)

2. **Green Phase - Implement Features**
   - Domain layer implementation
   - Application layer implementation
   - Infrastructure layer implementation
   - Presentation layer implementation
   - **Implement standardized logging** for all core features
   - **Reference**: [Standardized Logging Strategy](./STANDARDIZED_LOGGING_STRATEGY.md)

3. **Refactor Phase - Optimize Code**
   - Remove duplication
   - Improve naming
   - Optimize performance
   - Enhance readability

4. **Testing & Logging Validation**
   - Verify 80%+ test coverage achieved
   - Validate logging integration with log-collector
   - Check structured logging format compliance
   - Ensure all core features have comprehensive tests

**Deliverables**:
- Refactored service code
- Comprehensive test suite (80%+ coverage)
- Integrated structured logging
- Updated configuration
- Migration scripts (if needed)
- Test coverage report
- Logging validation report

---

### 3.N: Phase 3 Optimization & Critical Evaluation ⚡

**Duration**: 15-30 minutes

**Objective**: Ensure code quality and performance are optimal

**Critical Questions**:
- [ ] Is the code as simple as possible (KISS)?
- [ ] Are there unnecessary abstractions?
- [ ] Is error handling comprehensive?
- [ ] Are there performance issues in hot paths?
- [ ] Is the code testable and maintainable?
- [ ] Are we following SOLID principles?

**Service-Specific Optimization**:
- **API Services**: Optimize request/response handling, middleware chains
- **Background Workers**: Optimize batch processing, queue management
- **Real-Time Services**: Optimize for low latency, minimize blocking operations
- **Data Services**: Optimize query patterns, caching strategies
- **Integration Services**: Optimize external API calls, connection pooling

**Hardening**:
- Refactor complex functions (> 50 lines or cyclomatic complexity > 10)
- Remove unnecessary abstractions (premature optimization)
- Add comprehensive error handling (try/except, custom exceptions)
- Optimize hot paths (profile and fix bottlenecks)
- Improve logging for debugging (add context, correlation IDs)
- Validate all inputs at boundaries

**Iteration**:
- Run profiler on key operations
- Identify and fix performance bottlenecks
- Add missing error handling
- Improve test coverage for edge cases
- Enhance logging messages with context
- Re-run tests to ensure no regressions

**Quality Gate**: Code is simple, performant, well-tested, and maintainable

**Reference**: [OPTIMIZATION_AND_TUNING_ENHANCEMENT.md - Phase 3 Optimization](./OPTIMIZATION_AND_TUNING_ENHANCEMENT.md#phase-3-optimization-tdd-implementation)

---

**Git Checkpoint** 🔀 *Required*:
```bash
# AI Agent MUST commit after Phase 3 completion
# Note: Phase 3 is long - consider 2 commits:
#   Commit 3a: After Green Phase (domain layer complete)
#   Commit 3b: After Refactor Phase (code quality improved)

# Commit after full Phase 3 (recommended):
git add services/<service>/domain/ \
        services/<service>/tests/ \
        services/<service>/pytest.ini \
        services/<service>/requirements-test.txt

git commit -m "feat(<service>): Complete Phase 3 - TDD Implementation

Phase 3.1: Testing Infrastructure
- pytest configuration with custom markers
- Test fixtures and conftest
- requirements-test.txt

Phase 3.2: Red Phase
- XX unit tests written (TDD Red)
- Test coverage structure defined

Phase 3.3: Green Phase
- Complete domain layer implementation
- Entities, value objects, services
- Domain exceptions
- All tests passing

Phase 3.4: Refactor Phase
- Code quality improvements (DRY, KISS, SOLID)
- Reduced duplication
- Enhanced maintainability

Phase 3.5: Validation
- Logging integration validated
- Test coverage XX% (target: 80%+)

Tests: XX/XX passing (100%)
Coverage: XX%
Status: Domain layer complete, production-ready"
```

**Alternative: Split Phase 3 into 2 Commits** (for very large services):
```bash
# Commit 3a: After Green Phase
git add services/<service>/domain/ services/<service>/tests/unit/
git commit -m "feat(<service>): Complete Phase 3.3 - Domain Layer (TDD Green)

- Complete domain layer with XX tests passing
- Entities, value objects, domain services

Tests: XX/XX passing
Coverage: XX%"

# Commit 3b: After Refactor Phase  
git add services/<service>/domain/ services/<service>/tests/
git commit -m "refactor(<service>): Complete Phase 3.4 - Code Quality

- Improved code quality (DRY, KISS, SOLID)
- Enhanced test suite
- Validated logging

Tests: XX/XX passing
Coverage: XX%"
```

---

#### Phase 4: Integration Testing (1-2 days)
**Objective**: Ensure service integrates with ecosystem

**Activities**:
1. **Service Integration Tests**
   - Test service-to-service communication
   - Verify data flows
   - Test error handling
   - Validate event publishing/subscription

2. **Docker Testing**
   - Test standalone Docker run
   - Verify Docker Compose integration
   - Test health checks
   - Validate environment variables

3. **Ecosystem Testing**
   - Test in full ecosystem
   - Verify dependent services
   - Test backward compatibility
   - Load testing

**Deliverables**:
- Integration test results
- Docker validation report
- Ecosystem compatibility report
- Performance benchmarks

---

### 4.N: Phase 4 Optimization & Critical Evaluation ⚡

**Duration**: 15-30 minutes

**Objective**: Ensure integration tests are comprehensive and fast

**Critical Questions**:
- [ ] Do tests cover all integration points?
- [ ] Are tests fast enough (< 5 minutes total)?
- [ ] Are mocks realistic?
- [ ] Do we test failure scenarios?
- [ ] Are tests maintainable?
- [ ] Do tests catch real integration issues?

**Service-Specific Optimization**:
- **Services with Many Dependencies**: Test each integration separately
- **Services with External APIs**: Mock API responses realistically
- **Services with Databases**: Use test databases or efficient mocks
- **Services with Message Queues**: Test message handling thoroughly
- **Services with File I/O**: Test with temporary files/directories

**Hardening**:
- Optimize test fixtures (reduce setup time)
- Parallelize tests where possible
- Add missing integration test cases (failure scenarios)
- Improve test clarity and maintainability
- Add timeout assertions for async operations
- Test retry logic and circuit breakers

**Iteration**:
- Profile test suite to find slow tests
- Optimize or parallelize slow tests
- Add tests for error conditions
- Improve test documentation
- Verify Docker configuration works correctly
- Test with real dependencies (if safe)

**Quality Gate**: Fast, comprehensive integration tests that catch real issues

**Reference**: [OPTIMIZATION_AND_TUNING_ENHANCEMENT.md - Phase 4 Optimization](./OPTIMIZATION_AND_TUNING_ENHANCEMENT.md#phase-4-optimization-integration-testing)

---

**Git Checkpoint** 🔀 *Required*:
```bash
# AI Agent MUST commit after Phase 4 completion
git add services/<service>/tests/integration/ \
        services/<service>/tests/workflows/

git commit -m "test(<service>): Complete Phase 4 - Integration Testing

- XX integration tests (100% passing)
- XX workflow tests (real-world scenarios)
- Docker integration validated
- Ecosystem compatibility confirmed
- Performance benchmarks established

Tests: XX total (100% passing)
  - XX unit tests
  - XX integration tests
  - XX workflow tests
Coverage: XX%
Performance: Within targets
Status: Integration complete"
```

---

#### Phase 5: Comprehensive Testing & Coverage (2-3 hours) **MANDATORY** 🧪

**Objective**: Achieve comprehensive test coverage with quality, not just quantity

**Note**: This phase was added in v1.5.0 to address insufficient testing standards. Services MUST achieve 50%+ coverage (target 80%+) with 100% happy-path coverage before proceeding.

**Activities**:
1. **Coverage Analysis**
   - Run coverage report: `pytest --cov=./ --cov-report=html --cov-report=term-missing`
   - Identify untested code paths
   - Prioritize critical paths (business logic, error handling)
   - Target: 50% minimum, 80% ideal

2. **Happy-Path Testing (100% Coverage)**
   - Test ALL primary use cases
   - Test ALL API endpoints (basic success case)
   - Test ALL domain operations (core business logic)
   - Verify ALL expected outputs

3. **Edge Case Testing**
   - Boundary conditions (min/max values, empty inputs)
   - Error conditions (invalid inputs, missing data)
   - Concurrent operations (if applicable)
   - State transitions (if stateful)
   - Network failures (timeouts, retries)

4. **Test Quality Review**
   - Tests are meaningful (not just hitting lines)
   - Tests catch real bugs
   - Tests are maintainable
   - Test code quality is good
   - Tests run fast (< 5 minutes total)

5. **Create TESTING_GUIDE.md**
   - Service-specific testing strategy
   - How to run tests (unit, integration, E2E)
   - How to add new tests
   - Test fixtures and helpers
   - Common testing patterns
   - Troubleshooting test failures

**Deliverables**:
- Test coverage >= 50% (measured with pytest --cov)
- 100% happy-path coverage
- Edge cases covered for critical paths
- TESTING_GUIDE.md created
- Coverage report (HTML + XML)
- All tests passing

**Quality Gates**:
- [ ] Coverage >= 50% (target 80%+)
- [ ] All happy paths tested
- [ ] All API endpoints tested
- [ ] Critical edge cases covered
- [ ] TESTING_GUIDE.md complete
- [ ] All tests passing (0 failures)
- [ ] Test suite runs in < 5 minutes

---

### 5.N: Phase 5 Optimization & Critical Evaluation ⚡

**Duration**: 15-30 minutes

**Objective**: Maximize test quality, not just coverage percentage

**Critical Questions**:
- [ ] Are tests meaningful or just hitting lines?
- [ ] Do tests catch real bugs?
- [ ] Are edge cases well-covered?
- [ ] Is test code quality good?
- [ ] Are tests maintainable?
- [ ] Are tests fast enough?

**Service-Specific Optimization**:
- **Services with Complex Logic**: Focus on logic tests, decision tables
- **Services with Many States**: Test state transitions thoroughly
- **Services with Concurrency**: Test race conditions, deadlocks
- **Services with External APIs**: Test failure modes, retries
- **Services with Data Processing**: Test data transformations, validation

**Hardening**:
- Review tests for quality (not just coverage)
- Add mutation testing (if applicable)
- Optimize test performance (parallelize, optimize fixtures)
- Improve test documentation (docstrings, comments)
- Add property-based tests for complex logic (hypothesis)
- Test error messages are helpful

**Iteration**:
- Add tests for critical uncovered paths
- Refactor duplicated test code
- Optimize slow tests
- Improve test clarity
- Add missing edge cases
- Verify tests actually fail when code breaks

**Quality Gate**: High-quality, comprehensive test suite that catches real bugs

**Reference**: [OPTIMIZATION_AND_TUNING_ENHANCEMENT.md - Phase 5 Optimization](./OPTIMIZATION_AND_TUNING_ENHANCEMENT.md#phase-5-optimization-comprehensive-testing--coverage)

---

**Git Checkpoint** 🔀 *Required*:
```bash
# AI Agent MUST commit after Phase 5 completion
git add services/<service>/tests/ \
        services/<service>/TESTING_GUIDE.md \
        services/<service>/pytest.ini \
        services/<service>/htmlcov/

git commit -m "test(<service>): Complete Phase 5 - Comprehensive Testing & Coverage

- Test coverage: XX% (target: 50%+ minimum, 80%+ ideal)
- Happy-path coverage: 100% ✅
- Edge cases: Common scenarios covered
- TESTING_GUIDE.md created

Test Breakdown:
- XX unit tests (domain, application, infrastructure, presentation)
- XX integration tests
- XX E2E tests

Coverage Highlights:
- Business logic: XX%
- API endpoints: XX%
- Error handling: XX%

All tests passing: XX/XX (100%)
Test execution time: X.XXs

Status: Comprehensive testing complete"
```

---

#### Phase 6: Documentation (1 day)
**Objective**: Complete comprehensive documentation with AI optimization

**Activities**:
1. **Service Documentation** ⭐
   - Create comprehensive README (solo + ecosystem capabilities)
   - Add architecture diagrams (ecosystem, data flow, workflows)
   - Document major libraries and dependencies
   - Document all service relationships (provider/consumer)
   - **Reference**: [Service Documentation Strategy](./SERVICE_DOCUMENTATION_STRATEGY.md)

2. **Configuration Documentation** 🔧 *New in v1.2*
   - **UPDATE** CONFIG.md with complete details:
     - All ports and networking
     - All credentials and secrets
     - All configuration files
     - All environment variables
     - All profiles (dev, test, staging, prod)
     - Docker configuration
     - Validation commands
     - Troubleshooting guide
   - **UPDATE** [MASTER_CONFIGURATION_REGISTRY.md](./MASTER_CONFIGURATION_REGISTRY.md)
   - Verify all config files are documented
   - Ensure .env.template is complete
   - Document deployment configurations

3. **API Documentation** ⭐
   - Complete OpenAPI annotations on all endpoints
   - Implement standard endpoints (health, about-me, endpoints, provider-consumer)
   - Ensure Swagger UI available at `/docs`
   - Document all request/response schemas
   - **Reference**: [API Standardization Strategy](./API_STANDARDIZATION_STRATEGY.md)

4. **Visual Documentation** ⭐
   - Ecosystem architecture diagram (how service fits in ecosystem)
   - Data flow diagram (how data flows through service)
   - Workflow diagrams (participation in multi-service workflows)

5. **Developer Guides**
   - Local development setup
   - Testing guide
   - Troubleshooting guide
   - Contributing guidelines

6. **AI Agent Documentation Enrichment** ⭐ NEW
   - Add AI metadata tags to service documentation
   - Add navigation markers for AI discoverability
   - Add semantic tags for key sections
   - Add cross-references between documents
   - Generate AI-optimized index
   - **Script**: `python3 scripts/refactoring/enrich_service_documentation.py {service}`
   - **Validation**: Documentation is AI-agent friendly

**Deliverables**:
- Comprehensive README.md with all required sections
- Architecture, data flow, and workflow diagrams
- Complete OpenAPI/Swagger documentation
- Standard endpoints implemented and documented
- Service relationship mapping (JSON format)
- Integration guides
- AI-enriched documentation with metadata and tags ⭐

---

### 6.N: Phase 6 Optimization & Critical Evaluation ⚡

**Duration**: 15-30 minutes

**Objective**: Ensure documentation is clear, complete, and helpful

**Critical Questions**:
- [ ] Is documentation clear and accurate?
- [ ] Are examples realistic and helpful?
- [ ] Is configuration well-documented?
- [ ] Are common issues addressed?
- [ ] Is documentation discoverable?
- [ ] Are diagrams up-to-date and clear?

**Service-Specific Optimization**:
- **Public-Facing Services**: Focus on API docs, usage examples
- **Internal Services**: Focus on integration docs, dependencies
- **Complex Services**: Add architecture diagrams, sequence diagrams
- **Data Services**: Document data models, query patterns
- **Integration Services**: Document external API contracts

**Hardening**:
- Review documentation for clarity (remove jargon)
- Add missing examples (common use cases)
- Improve troubleshooting section (common errors)
- Add diagrams where helpful (architecture, data flow)
- Verify all links work (internal and external)
- Ensure API examples are tested and work
- Check spelling and grammar

**Iteration**:
- Read documentation from user perspective
- Add missing sections (found during review)
- Improve confusing explanations
- Add more examples for complex features
- Update diagrams if outdated
- Verify OpenAPI spec matches implementation
- Test all code examples

**Quality Gate**: Documentation is clear, comprehensive, and user-friendly

**Reference**: [OPTIMIZATION_AND_TUNING_ENHANCEMENT.md - Phase 6 Optimization](./OPTIMIZATION_AND_TUNING_ENHANCEMENT.md#phase-6-optimization-documentation)

---

**Git Checkpoint** 🔀 *Required*:
```bash
# AI Agent MUST commit after Phase 6 completion
git add services/<service>/README.md \
        services/<service>/CONFIG.md \
        services/<service>/docs/ \
        services/<service>/*.md

git commit -m "docs(<service>): Complete Phase 6 - Documentation

- Comprehensive README (XXX+ lines)
  * Service overview and features
  * Architecture diagrams
  * Installation and usage
  * Testing guide
  * API reference
  * Troubleshooting
- Complete CONFIG.md
  * Ports, credentials, profiles
  * Configuration files
  * Validation commands
- API documentation (OpenAPI/Swagger)
- Visual documentation (diagrams)
- AI-enriched with metadata and tags

Documentation: Production-ready
Status: Phase 6 complete"
```

---

#### Phase 7: Deployment & Monitoring (1 day)
**Objective**: Deploy and validate in target environment

**Activities**:
1. **Pre-Deployment Configuration Validation** 🔧 *New in v1.2*
   - **READ** [MASTER_CONFIGURATION_REGISTRY.md](./MASTER_CONFIGURATION_REGISTRY.md)
   - **RUN** preflight checks:
     - `make check-port-conflicts` (ecosystem-level)
     - `make validate-config` (service-level)
     - `make validate-yaml` (YAML syntax)
     - `make validate-docker` (Dockerfile best practices)
   - Verify all credentials are configured (production secrets)
   - Confirm correct profile selected (staging/production)
   - Check network configuration
   - **REQUIRED**: All validations must pass before deployment

2. **Deployment**
   - Deploy to development/staging/production
   - Validate health checks (`/health` endpoint)
   - Monitor logs (structured JSON logging)
   - Verify metrics (Prometheus endpoints)
   - Verify service discovery (DNS resolution)
   - Test inter-service communication

3. **Validation**
   - Run smoke tests
   - Validate integrations with dependent services
   - Check performance benchmarks
   - Review logs for errors
   - Verify configuration profiles active
   - Test standard endpoints (health, about-me, endpoints)

4. **Monitoring Setup**
   - Configure alerts (port, health, errors)
   - Set up dashboards (include config metrics)
   - Enable tracing
   - Document runbooks
   - Monitor configuration drift

**Deliverables**:
- **Configuration validation report** 🔧 *New*
- Deployment checklist
- Monitoring configuration
- Alert definitions
- Runbook documentation

---

### 7.N: Phase 7 Optimization & Critical Evaluation ⚡

**Duration**: 15-30 minutes

**Objective**: Ensure deployment is smooth and monitoring is effective

**Critical Questions**:
- [ ] Is deployment automated?
- [ ] Are rollback procedures clear?
- [ ] Is monitoring comprehensive?
- [ ] Are alerts actionable?
- [ ] Are logs useful for debugging?
- [ ] Are health checks responsive?

**Service-Specific Optimization**:
- **Critical Services**: Add health checks, circuit breakers, redundancy
- **High-Traffic Services**: Add performance monitoring, rate limiting
- **Stateful Services**: Add data validation, backup procedures
- **Integration Services**: Add dependency health checks
- **Background Workers**: Add queue monitoring, worker health

**Hardening**:
- Optimize health check response time (< 100ms)
- Add missing metrics (request count, latency, errors)
- Improve log messages for debugging (add context, IDs)
- Test deployment procedure (dry run)
- Document rollback process (step-by-step)
- Verify alerts fire correctly (test alert conditions)
- Check monitoring dashboard usability

**Iteration**:
- Run deployment in staging environment
- Test rollback procedure
- Verify alerts trigger on real issues
- Improve runbook based on deployment
- Add missing monitoring metrics
- Test health check under load
- Verify logs are searchable and useful

**Quality Gate**: Production-ready deployment with comprehensive monitoring

**Reference**: [OPTIMIZATION_AND_TUNING_ENHANCEMENT.md - Phase 7 Optimization](./OPTIMIZATION_AND_TUNING_ENHANCEMENT.md#phase-7-optimization-deployment--monitoring)

---

**Git Checkpoint** 🔀 *Required*:
```bash
# AI Agent MUST commit after Phase 7 completion
git add services/<service>/docker-compose.yml \
        services/<service>/Dockerfile \
        services/<service>/.github/ \
        services/<service>/Makefile

git commit -m "deploy(<service>): Complete Phase 7 - Deployment & Monitoring

- Pre-deployment validation passed
  * Port conflicts: None
  * Configuration validated
  * YAML syntax validated
  * Docker best practices confirmed
- Deployed to [environment]
- Health checks validated
- Monitoring configured
- Alerts established
- Runbook documented

Deployment: Successful
Health: Passing
Monitoring: Active
Status: Service deployed and operational"
```

**⚠️ DO NOT MARK COMPLETE YET! Proceed to Phase 8 (Service Optimization & Hardening) then Phase 9 (Service Validation).**

---

#### Phase 8: Service Optimization & Hardening (2-4 hours) ⚠️ **MANDATORY** 🔧

**Objective**: Holistically optimize service configuration, implement quick wins, and harden for production

**Note**: This phase was added in v1.6.0 to ensure all services are fully optimized and production-ready before validation. This phase takes all learnings from Phases 1-7 and applies comprehensive optimization.

**Duration**: 2-4 hours

**Key Focus Areas**:
1. Configuration optimization (externalize hardcoded values)
2. Quick wins implementation (3-5 per service)
3. Service-specific optimization
4. Production hardening
5. Regression protection
6. Performance benchmarking

**For complete Phase 8 specification**, see [OPTIMIZATION_AND_TUNING_ENHANCEMENT.md - Phase 8](./OPTIMIZATION_AND_TUNING_ENHANCEMENT.md#phase-8-service-optimization--hardening-new)

**Activities Summary**:

### 8.1: Configuration Optimization
- Externalize all hardcoded values to environment variables
- Create configuration profiles (dev, test, staging, prod)
- Add sensible defaults
- Document all configuration options in CONFIG.md
- Add configuration validation

### 8.2: Quick Wins Implementation (3-5 Required)

**Quick Win Categories**:
- **Performance**: Caching, connection pooling, compression
- **Reliability**: Retry logic, circuit breakers, timeouts
- **Observability**: Request ID tracking, metrics, enhanced logging
- **Security**: Input validation, rate limiting, error sanitization
- **Developer Experience**: Better errors, debug endpoints

**Examples**:
```python
# Quick Win 1: Connection pooling
client = httpx.AsyncClient(
    limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
)

# Quick Win 2: Retry with backoff
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
async def call_external_api():
    ...

# Quick Win 3: Request ID tracking
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))
    request_id_var.set(request_id)
    response = await call_next(request)
    response.headers['X-Request-ID'] = request_id
    return response
```

### 8.3: Service-Specific Optimization

**By Service Type**:
- **Stateless APIs**: Horizontal scaling, connection pooling, caching
- **Data-Intensive**: Query optimization, caching, batch operations
- **Integration Services**: Circuit breakers, retry strategies, fallbacks
- **Real-Time Services**: Low latency optimization, WebSockets
- **Background Workers**: Batch sizes, worker pools, queue management

### 8.4: Hardening & Error Handling

**Checklist**:
- [ ] All endpoints validate input
- [ ] All exceptions caught appropriately
- [ ] All external calls have timeouts
- [ ] Retry logic for transient failures
- [ ] Circuit breakers for failing services
- [ ] Request size limits enforced
- [ ] Rate limiting configured
- [ ] Security headers set
- [ ] Secrets not in code

### 8.5: Regression Protection

**Required**:
- Run full test suite after each optimization
- Add tests for new functionality (caching, retry, etc.)
- Verify performance improvements (benchmark)
- Integration testing
- Smoke testing all endpoints
- Configuration testing (different profiles)

### 8.6: Update CONFIG.md

**Add sections**:
- Configuration Options (with defaults and production values)
- Configuration Profiles (dev vs prod settings)
- Quick Wins Implemented (list with impact)
- Optimizations Applied (performance, reliability, observability)
- Performance Metrics (before/after)

**Deliverables**:
1. ✅ Configuration fully optimized and externalized
2. ✅ 3-5 quick wins implemented and tested
3. ✅ Service-specific optimizations applied
4. ✅ Service hardened (validation, error handling, security)
5. ✅ All tests passing (regression protected)
6. ✅ CONFIG.md updated with optimizations
7. ✅ Performance benchmarks (before/after measurements)

**Quality Gates**:
- [ ] All configuration externalized (no hardcoded values)
- [ ] Minimum 3 quick wins implemented
- [ ] Service-specific optimizations applied
- [ ] All tests passing (0 failures)
- [ ] No performance regressions
- [ ] CONFIG.md comprehensive and up-to-date

**Git Checkpoint** 🔀 *Required*:
```bash
# AI Agent MUST commit after Phase 8 completion
git add services/<service>/ \
        services/<service>/CONFIG.md

git commit -m "optimize(<service>): Complete Phase 8 - Service Optimization & Hardening

🔧 Configuration Optimization:
- Externalized X hardcoded values → env vars
- Created config profiles (dev, test, staging, prod)
- Added configuration validation
- Documented all options in CONFIG.md

⚡ Quick Wins Implemented:
1. [Quick win 1] - [Impact description]
2. [Quick win 2] - [Impact description]
3. [Quick win 3] - [Impact description]
4. [Quick win 4] - [Impact description] (optional)
5. [Quick win 5] - [Impact description] (optional)

🎯 Service-Specific Optimizations:
- [Optimization 1 specific to service type]
- [Optimization 2 specific to service type]

🛡️ Hardening:
- Input validation enhanced
- Error handling comprehensive
- Timeouts and retries configured
- Security checks implemented
- Resource limits set

📊 Performance Metrics:
- Before: X req/s, Y ms avg latency
- After: X req/s (+Z%), Y ms avg latency (-Z%)
- Memory: X MB → Y MB
- [Other relevant metrics]

✅ Regression Protection:
- All tests passing: XX/XX (100%)
- Coverage maintained: XX%
- Integration tests: PASSING
- Performance: NO REGRESSIONS

Status: Phase 8 complete, service optimized and hardened"
```

**⚠️ DO NOT MARK COMPLETE YET! Proceed to Phase 9 (Service Validation).**

---

#### Phase 9: Service Validation ⚠️ **MANDATORY** (1-2 hours)

**Objective**: **Validate that the refactored service actually works** before marking it complete.

**Critical Importance**: This phase was added after discovering that `data-services-dashboard` was marked "100% Complete" despite having:
- ❌ Non-functional REST API (FastAPI didn't start)
- ❌ 4 failing tests
- ❌ 45% actual coverage (not the claimed 80%)
- ❌ Docker configuration issues

**Without Phase 7, broken services ship to production!** 🚨

---

**7.1: Build Docker Image** (5 minutes)

**AI Agent Instructions**:
1. Navigate to service directory
2. Build Docker image with proper tagging
3. Verify build completes without errors
4. Check for any warnings or issues

```bash
# Build Docker image
cd services/<service-name>
docker build -t <service-name>:<version> .

# Expected output:
# - No syntax errors
# - All layers build successfully
# - Image created and tagged
# - Reasonable image size (< 1GB for most services)
```

**Success Criteria**:
- ✅ Build completes without errors
- ✅ No syntax errors in Dockerfile
- ✅ All dependencies installed
- ✅ Image tagged correctly

**Common Issues**:
- Inline comments in EXPOSE directive (use comment above instead)
- .dockerignore excluding code directories
- Missing COPY directives for required files
- Base image not available

**If Build Fails**: Stop immediately, fix the issue, commit the fix, and restart Phase 7.

---

**7.2: Start Container** (5 minutes)

**AI Agent Instructions**:
1. Start container with all required environment variables
2. Wait for initialization (15-30 seconds)
3. Check logs for successful startup
4. Verify no critical errors

```bash
# Start container (adjust ports and env vars as needed)
docker run -d --name <service>-validation \\
  -p <port>:<port> \\
  -e REQUIRED_ENV_VAR=value \\
  <service-name>:<version>

# Wait for startup
sleep 15

# Check logs
docker logs <service>-validation

# Expected output:
# - Service initialized
# - No critical errors
# - Listening on configured port
```

**Success Criteria**:
- ✅ Container starts without crashing
- ✅ Logs show successful initialization
- ✅ No critical errors in logs
- ✅ Process running and listening

**Common Issues**:
- Missing environment variables
- Port already in use
- Dependency services not available
- Configuration errors

**If Startup Fails**: Stop container, fix the issue, rebuild if needed, and restart Phase 7.

---

**7.3: Test Health Endpoint** (5 minutes)

**AI Agent Instructions**:
1. Wait for service to be fully ready
2. Test the `/health` endpoint
3. Verify response format and status
4. Check response time

```bash
# Test health endpoint
curl -s http://localhost:<port>/health | python3 -m json.tool

# Expected response:
{
  "status": "healthy",
  "service": "<service-name>",
  "version": "X.Y.Z",
  "uptime_seconds": <number>,
  "timestamp": "<iso-timestamp>"
}

# Success: Returns 200 OK with valid JSON
```

**Success Criteria**:
- ✅ Returns HTTP 200 OK
- ✅ JSON response is valid
- ✅ Status is "healthy"
- ✅ Response time < 1 second
- ✅ All required fields present

**Common Issues**:
- API not starting (e.g., FastAPI in background thread)
- Port not exposed correctly
- Health endpoint not implemented
- Incorrect routing

**If Health Check Fails**: This is **CRITICAL**. The service is broken. Stop, investigate logs, fix the root cause, and restart Phase 7.

---

**7.4: Test About-Me Endpoint** (5 minutes)

**AI Agent Instructions**:
1. Test the `/about-me` endpoint
2. Verify comprehensive service metadata
3. Check all required sections present

```bash
# Test about-me endpoint
curl -s http://localhost:<port>/about-me | python3 -m json.tool

# Expected response (comprehensive):
{
  "service": "<service-name>",
  "version": "X.Y.Z",
  "description": "...",
  "capabilities": [...],
  "architecture": {...},
  "ecosystem_role": "...",
  "dependencies": {
    "providers": [...],
    "consumers": [...]
  },
  "api": {
    "version": "v1",
    "documentation": "http://...",
    "openapi_spec": "http://..."
  }
}
```

**Success Criteria**:
- ✅ Returns HTTP 200 OK
- ✅ JSON response is valid
- ✅ Contains service metadata
- ✅ Lists capabilities
- ✅ Lists dependencies (providers/consumers)
- ✅ Includes API information

**If About-Me Fails**: Implement missing sections, update endpoint, and restart Phase 7.

---

**7.5: Test All Standard Endpoints** (10 minutes)

**AI Agent Instructions**:
1. Test all 5 standard endpoints
2. Verify each returns valid responses
3. Check OpenAPI spec validates

```bash
# Test all standard endpoints
curl -s http://localhost:<port>/health
curl -s http://localhost:<port>/about-me
curl -s http://localhost:<port>/endpoints
curl -s http://localhost:<port>/provider-consumer
curl -s http://localhost:<port>/openapi.json

# For hybrid architectures (UI + API), test both ports:
# - Streamlit UI: http://localhost:8501
# - FastAPI API: http://localhost:8080
```

**Success Criteria**:
- ✅ All 5 endpoints return HTTP 200 OK
- ✅ All return valid JSON
- ✅ `/endpoints` lists all available endpoints
- ✅ `/provider-consumer` shows service relationships
- ✅ `/openapi.json` validates as valid OpenAPI 3.0+ spec
- ✅ For hybrid: Both UI and API ports accessible

**Common Issues**:
- Missing endpoints (need to implement)
- Incorrect routing
- Invalid JSON responses
- OpenAPI spec errors

**If Any Endpoint Fails**: Implement or fix the endpoint and restart Phase 7.

---

**7.6: Container Teardown** (2 minutes)

**AI Agent Instructions**:
1. Stop the container gracefully
2. Remove the container
3. Verify clean shutdown

```bash
# Stop and remove container
docker stop <service>-validation
docker rm <service>-validation

# Verify removal
docker ps -a | grep <service>-validation  # Should be empty
```

**Success Criteria**:
- ✅ Container stops gracefully (no force kill needed)
- ✅ No hanging processes
- ✅ Clean shutdown in logs
- ✅ Container removed successfully

---

**7.7: Run Full Test Suite** (10-15 minutes)

**AI Agent Instructions**:
1. Run **ALL** tests with coverage measurement
2. Verify **0 test failures**
3. Verify **coverage >= 80%** (measured, not estimated!)
4. Save test results and coverage report

```bash
# Run full test suite with coverage
cd services/<service-name>
pytest tests/ -v --cov=./ --cov-report=term-missing --cov-report=html --cov-report=xml

# Expected output:
# ===== X passed in Y.XXs =====
# Coverage >= 80%

# Save results
mkdir -p validation_results/
cp htmlcov/ validation_results/ -r
cp coverage.xml validation_results/
pytest tests/ -v > validation_results/test_results.txt 2>&1
```

**Success Criteria**:
- ✅ **ALL tests pass** (0 failures, 0 errors)
- ✅ **Coverage >= 80%** (measured with `pytest --cov`)
- ✅ No test warnings (except deprecation)
- ✅ Test execution time reasonable (< 5 minutes for most services)
- ✅ Coverage report saved

**Common Test Failures**:
- Pydantic validation errors (models don't match tests)
- Calculation errors (percentiles, metrics off by small amounts)
- String formatting errors (truncation, padding)
- Mock/fixture issues

**If ANY Test Fails**: **STOP IMMEDIATELY**. Do NOT mark service complete. Fix the failing test(s), re-run tests until all pass, and restart Phase 7 validation.

**If Coverage < 80%**: Write more tests to reach 80%+, then restart Phase 7.

---

**7.8: Integration Test (If Applicable)** (10 minutes)

**AI Agent Instructions**:
1. If service has dependencies, test integration
2. Use docker-compose to start all required services
3. Test actual data flow between services

```bash
# For services with dependencies (e.g., dashboard -> log-collector)
docker-compose up -d

# Wait for all services to be healthy
sleep 30

# Test integration
# Example: Dashboard should fetch logs from log-collector
curl -s http://localhost:<dashboard-port>/health
curl -s http://localhost:<log-collector-port>/health

# Verify data flows correctly
# (service-specific validation)

# Teardown
docker-compose down
```

**Success Criteria**:
- ✅ All dependency services start
- ✅ Service connects to dependencies
- ✅ Data flows correctly
- ✅ Error handling works (graceful degradation if dependency unavailable)

**If Integration Fails**: Fix connectivity, error handling, or configuration issues, and restart Phase 7.

---

**7.9: Create Validation Report** (10 minutes)

**AI Agent Instructions**:
1. Document all validation steps executed
2. Record pass/fail status for each
3. Note any issues discovered and fixes applied
4. Save final validation result

Create `PHASE_7_VALIDATION_REPORT.md` in the service directory:

```markdown
# Phase 7: Service Validation Report

**Service**: <service-name>
**Version**: <version>
**Date**: <date>
**Validation Status**: ✅ PASSED / ❌ FAILED

---

## Validation Steps

### 7.1: Build Docker Image
**Status**: ✅ PASSED
**Duration**: X minutes
**Notes**: Built successfully, image size: XXX MB

### 7.2: Start Container
**Status**: ✅ PASSED
**Duration**: X seconds
**Notes**: Started without errors

### 7.3: Test Health Endpoint
**Status**: ✅ PASSED
**Response Time**: XXX ms
**Notes**: Returns 200 OK with valid JSON

### 7.4: Test About-Me Endpoint
**Status**: ✅ PASSED
**Response Time**: XXX ms
**Notes**: Comprehensive metadata returned

### 7.5: Test All Standard Endpoints
**Status**: ✅ PASSED
**Endpoints Tested**: 5/5
**Notes**: All endpoints functional

### 7.6: Container Teardown
**Status**: ✅ PASSED
**Notes**: Clean shutdown

### 7.7: Run Full Test Suite
**Status**: ✅ PASSED
**Tests Run**: XXX
**Tests Passed**: XXX
**Tests Failed**: 0
**Coverage**: XX.X%
**Notes**: All tests passing, coverage above threshold

### 7.8: Integration Test
**Status**: ✅ PASSED / N/A (if no dependencies)
**Notes**: Integration with <dependencies> successful

---

## Issues Discovered
- Issue 1: <description>
  - Fix: <what was done>
- Issue 2: <description>
  - Fix: <what was done>

---

## Final Validation Result

**Overall Status**: ✅ **PASSED**

The service has been validated and is confirmed to be:
- ✅ Builds successfully
- ✅ Starts and runs correctly
- ✅ All endpoints functional
- ✅ All tests passing
- ✅ Coverage >= 80%
- ✅ Integration working (if applicable)

**Service is PRODUCTION-READY!** 🎉
```

---

**9.10: Git Commit** 🔀 *Required*

**AI Agent Instructions**:
1. Stage all validation-related files
2. Commit with clear message indicating validation passed
3. Include validation results in commit

```bash
# AI Agent MUST commit after Phase 9 completion
git add services/<service>/PHASE_9_VALIDATION_REPORT.md \\
        services/<service>/validation_results/ \\
        services/<service>/ # Any fixes made during validation

git commit -m "validate(<service>): Complete Phase 9 - Service Validation ✅

Phase 9: Service Validation - PASSED
================================================================================

✅ 9.1: Build Docker Image - PASSED
✅ 9.2: Start Container - PASSED
✅ 9.3: Test Health Endpoint - PASSED (XXX ms)
✅ 9.4: Test About-Me Endpoint - PASSED (XXX ms)
✅ 9.5: Test All Standard Endpoints - PASSED (5/5)
✅ 9.6: Container Teardown - PASSED
✅ 9.7: Run Full Test Suite - PASSED (XXX tests, XX.X% coverage)
✅ 9.8: Integration Test - PASSED / N/A

Issues Fixed During Validation:
- [List any issues discovered and fixed]

Final Result: ✅ PRODUCTION-READY

All validation steps passed successfully!
Service is confirmed working and ready for deployment."
```

---

**Deliverables**:
- ✅ **PHASE_9_VALIDATION_REPORT.md** - Comprehensive validation report
- ✅ **validation_results/** - Test results, coverage reports, logs
- ✅ **Working service** - Confirmed functional in Docker container
- ✅ **Passing tests** - 0 failures, >= 80% coverage (measured)
- ✅ **Git commit** - Validation results committed

---

**⚠️ CRITICAL: Validation Decision Tree**

```
┌─────────────────────────────────────┐
│  All Validation Steps Pass?        │
└──────────┬──────────────────────────┘
           │
    ┌──────┴──────┐
    │             │
   YES           NO
    │             │
    ▼             ▼
┌────────────┐   ┌─────────────────────────┐
│ PROCEED    │   │ STOP IMMEDIATELY        │
│ Mark       │   │ DO NOT MARK COMPLETE    │
│ Service    │   │                         │
│ Complete   │   │ 1. Document issue       │
│            │   │ 2. Fix root cause       │
│ ✅ READY   │   │ 3. Commit fix           │
│ FOR PROD   │   │ 4. Restart Phase 7      │
└────────────┘   │                         │
                 │ Repeat until ALL pass   │
                 └─────────────────────────┘
```

**DO NOT skip this phase!**
**DO NOT mark service complete without passing validation!**
**DO NOT estimate - measure actual results!**

---

**Service Validation Complete!** ✅

**Only after Phase 9 (Service Validation) passes**, proceed to Phase 10.

**⚠️ DO NOT SKIP Phase 10! It is MANDATORY.**

---

#### Phase 10: Future Expansion Planning (2-4 hours) ⚠️ **MANDATORY** 🚀

**Objective**: Plan workflows, E2E tests, and executable demos for future ecosystem integration

**Note**: This phase was added in v1.5.0 to ensure services are not just working in isolation but are planned for ecosystem-wide workflows and have executable demos for validation.

**Duration**: 2-4 hours

**Key Focus Areas**:
1. Audit MASTER_SERVICE_MATRIX.md
2. Plan workflows involving this service
3. Create E2E test plans for workflows
4. Plan functional demos with canned data
5. Implement demo endpoints (`/demos`, `/run-demo`)
6. Update service README with future expansion section
7. Update MASTER_SERVICE_MATRIX.md

**For complete Phase 10 specification**, see [PLAN_ENRICHMENT_TESTING_AND_FUTURE_EXPANSION.md - Phase 9](./PLAN_ENRICHMENT_TESTING_AND_FUTURE_EXPANSION.md)

**Activities Summary**:

### 10.1: Audit MASTER_SERVICE_MATRIX.md

**Objective**: Understand the ecosystem and this service's role

**Activities**:
- Read [MASTER_SERVICE_MATRIX.md](./MASTER_SERVICE_MATRIX.md)
- Identify services this service depends on (providers)
- Identify services that depend on this service (consumers)
- Understand current ecosystem workflows
- Identify gaps where this service could participate

### 10.2: Plan Workflows Involving This Service

**Objective**: Design realistic workflows that leverage this service

**Activities**:
- Identify 3-5 workflows that involve this service
- For each workflow:
  - Document participating services
  - Document data flow
  - Document expected outcomes
  - Document failure scenarios
- Prioritize workflows by business value

**Example Workflows**:
- **Code Analysis Workflow**: `code-analyzer` → `doc-store` → `llm-gateway` → `prompt-store`
- **Expert Finding Workflow**: `expert-finder-service` → `user-store` → `doc-store`
- **Architecture Digitization Workflow**: `architecture-digitizer` → `doc-store` → `analysis-service`

### 10.3: Create E2E Test Plans

**Objective**: Plan comprehensive E2E tests for each workflow

**Activities**:
- For each workflow planned in 10.2:
  - Define test scenarios (happy path + failure modes)
  - Define test data requirements
  - Define expected outcomes
  - Define validation criteria
  - Document test automation strategy

**Deliverable**: `E2E_TEST_PLAN.md` in service directory

### 10.4: Plan Functional Demos

**Objective**: Design executable demos that showcase service capabilities

**Activities**:
- Plan 3-5 demos (mix of self-contained and ecosystem-based)
- For each demo:
  - Define demo objective
  - Define required canned data
  - Define service interactions
  - Define expected output/reports
  - Document demo execution steps

**Demo Types**:
1. **Self-Contained**: Service operates independently with mock data
2. **Ecosystem**: Service interacts with real ecosystem services
3. **Hybrid**: Service uses mix of real and mock services

**Deliverable**: `DEMO_PLAN.md` in service directory

### 10.5: Implement Demo Endpoints

**Objective**: Add `/demos` and `/run-demo` endpoints to service

**Note**: Required for all services (not dashboards), per [DEMO_ENDPOINTS_ENHANCEMENT.md](./DEMO_ENDPOINTS_ENHANCEMENT.md)

**Implementation**:
```python
# GET /demos - List available demos
@app.get("/demos")
async def list_demos():
    return {
        "demos": [
            {
                "id": "demo-1",
                "name": "Basic Analysis Demo",
                "description": "Analyzes sample code and returns metrics",
                "type": "self-contained",
                "estimated_duration_seconds": 30
            },
            # ... more demos
        ]
    }

# POST /run-demo - Execute demo
@app.post("/run-demo")
async def run_demo(demo_id: str):
    # Execute demo, return results
    pass
```

**Deliverable**: Endpoints implemented and tested

### 10.6: Update Service README

**Objective**: Document future expansion plans

**Activities**:
- Add "Future Expansion" section to README.md
- Document planned workflows
- Document E2E test plans
- Document planned demos
- Document potential enhancements

**Example Section**:
```markdown
## Future Expansion

### Planned Workflows
1. **Code Analysis Workflow** - Integration with doc-store and llm-gateway
2. **Expert Recommendation** - Enhanced team formation recommendations

### E2E Testing Plans
- See [E2E_TEST_PLAN.md](./E2E_TEST_PLAN.md) for comprehensive test scenarios

### Executable Demos
- Basic Analysis Demo (self-contained)
- Ecosystem Integration Demo
- Performance Benchmark Demo

See `/demos` endpoint for full list of executable demos.

### Potential Enhancements
- Real-time analysis streaming
- Multi-language support expansion
- Integration with CI/CD pipelines
```

### 10.7: Update MASTER_SERVICE_MATRIX.md

**Objective**: Record this service's capabilities and workflows

**Activities**:
- Add service to matrix (if not already there)
- Update "Refactor Status" to "Phase 10 Complete"
- List key capabilities
- List planned workflows
- List available demos

**Deliverables**:
1. ✅ MASTER_SERVICE_MATRIX.md audited
2. ✅ 3-5 workflows planned and documented
3. ✅ E2E_TEST_PLAN.md created
4. ✅ DEMO_PLAN.md created
5. ✅ Demo endpoints implemented (`/demos`, `/run-demo`)
6. ✅ README.md updated with Future Expansion section
7. ✅ MASTER_SERVICE_MATRIX.md updated

**Quality Gates**:
- [ ] At least 3 workflows planned
- [ ] E2E test plan comprehensive (happy path + failures)
- [ ] At least 3 demos planned (mix of types)
- [ ] Demo endpoints functional and tested
- [ ] README Future Expansion section complete
- [ ] MASTER_SERVICE_MATRIX.md updated

**Git Checkpoint** 🔀 *Required*:
```bash
# AI Agent MUST commit after Phase 10 completion
git add services/<service>/E2E_TEST_PLAN.md \
        services/<service>/DEMO_PLAN.md \
        services/<service>/README.md \
        services/<service>/main.py \
        docs/refactoring/MASTER_SERVICE_MATRIX.md

git commit -m "plan(<service>): Complete Phase 10 - Future Expansion Planning

🚀 Workflow Planning:
- Workflow 1: [Name] - [Brief description]
- Workflow 2: [Name] - [Brief description]
- Workflow 3: [Name] - [Brief description]
- [Additional workflows...]

🧪 E2E Test Planning:
- Created E2E_TEST_PLAN.md
- X test scenarios defined
- Happy path + failure modes covered

🎬 Demo Planning:
- Created DEMO_PLAN.md
- X demos planned (self-contained, ecosystem, hybrid)
- Demo endpoints implemented: /demos, /run-demo

📊 Demos Available:
1. [Demo 1] - [Type] - [Duration]
2. [Demo 2] - [Type] - [Duration]
3. [Demo 3] - [Type] - [Duration]
- [Additional demos...]

📖 Documentation:
- README.md: Added Future Expansion section
- MASTER_SERVICE_MATRIX.md: Updated service entry

Status: Phase 10 complete, service future-ready"
```

---

**Service Refactoring Complete!** 🎉

**After completing Phase 10**, the service is now:
- ✅ Deployed and operational
- ✅ Fully tested (80%+ coverage **measured**)
- ✅ Comprehensively documented
- ✅ Monitored and observable
- ✅ **Optimized and hardened**
- ✅ **Validated and confirmed working**
- ✅ **Workflows planned with E2E tests**
- ✅ **Executable demos available**
- ✅ **Production-ready and future-proof**

**Next**: Optionally proceed to Phase 11 for enhancements, or move to the next service.

---

#### Phase 11: Enhancement & Optional Work (1-2 days, as needed)
**Objective**: Complete optional/skipped steps and enhancements

**Note**: This phase is **optional** and can be performed at any time after Phase 10, or even after multiple services are complete. It captures work that was skipped during initial phases because it was non-critical or time could be better spent moving to the next service.

**When to Use**:
- After completing initial 10 mandatory phases for a service
- When returning to polish a "complete" service
- During maintenance/enhancement sprints
- When resources are available for optimization

**Activities**:

1. **Skipped Testing Work**
   - Docker testing (if skipped in Phase 4.2)
     - Test standalone Docker run
     - Verify Docker Compose integration
     - Test health checks in containers
     - Validate environment variables
   - Ecosystem testing (if skipped in Phase 4.3)
     - Full ecosystem integration tests
     - Load testing with real traffic
     - Chaos engineering tests
     - Performance benchmarking
   - Additional test coverage
     - Edge cases not covered in initial TDD
     - Property-based testing
     - Mutation testing
     - Stress testing

2. **Enhanced Documentation**
   - Additional architecture diagrams (if minimal in Phase 5)
     - Sequence diagrams for complex workflows
     - State machine diagrams
     - Data flow diagrams
     - Component interaction diagrams
   - Advanced usage examples
     - Complex workflow examples
     - Integration patterns
     - Troubleshooting scenarios
   - Video tutorials or demos
   - API usage guides for specific use cases

3. **Performance Optimization**
   - Profiling and bottleneck identification
   - Caching strategy implementation
   - Database query optimization
   - Memory usage optimization
   - Async/parallel processing opportunities

4. **Security Hardening**
   - Security audit (beyond basic checks)
   - Penetration testing
   - Input validation hardening
   - Rate limiting implementation
   - Security headers and best practices

5. **Developer Experience**
   - Local development setup improvements
   - Debug tooling
   - Mock/stub services for testing
   - Developer documentation enhancements
   - IDE configuration examples

6. **Monitoring & Observability**
   - Enhanced metrics collection
   - Distributed tracing setup
   - Custom dashboards
   - Alerting refinement
   - Log aggregation optimization

7. **Technical Debt Paydown**
   - Code cleanup identified but deferred
   - Refactoring opportunities noted during TDD
   - Configuration simplification
   - Dependency updates
   - Dead code removal

**Deliverables** (as applicable):
- Enhanced test suite
- Additional documentation
- Performance optimization report
- Security audit results
- Developer tooling improvements
- Enhanced monitoring setup
- Technical debt reduction report

**Decision Criteria for Skipping**:
Skip Phase 11 initially if:
- ✅ Phases 1-10 are complete and validated
- ✅ Service is production-ready for core features
- ✅ Moving to next service provides more value
- ✅ No critical issues identified

Return to Phase 11 later if:
- ⏸️ Performance issues arise in production
- ⏸️ Security concerns identified
- ⏸️ Developer friction with service
- ⏸️ Maintenance burden is high
- ⏸️ Planning enhancement sprint for multiple services

---

## 🗂️ Service Categories

Services are categorized to prioritize refactoring and manage dependencies:

### Tier 1: Foundation Services (Refactor First)
**Critical infrastructure services with many dependents**

1. **redis** - Caching and messaging infrastructure
2. **doc_store** - Document storage service
3. **orchestrator** - Central coordination hub
4. **llm-gateway** - AI provider routing

**Rationale**: These services are dependencies for many others. Refactoring them first establishes patterns and ensures stability.

### Tier 2: Core Services (Refactor Second)
**Essential business logic services**

5. **analysis-service** ✅ (Already refactored - use as template)
6. **prompt_store** - Prompt management
7. **source-agent** - Data ingestion
8. **discovery-agent** - Service discovery
9. **memory-agent** - Context memory

**Rationale**: Core business services that implement primary functionality. Many services depend on these.

### Tier 3: Integration Services (Refactor Third)
**Services that integrate with external systems**

10. **github-mcp** - GitHub integration
11. **bedrock-proxy** - AWS Bedrock proxy
12. **interpreter** - Natural language interface
13. **log-collector** - Centralized logging
14. **notification-service** - Multi-channel notifications

**Rationale**: Integration services that connect ecosystem to external systems.

### Tier 4: Analysis & Processing (Refactor Fourth)
**Specialized analysis and processing services**

15. **code-analyzer** - Code analysis
16. **secure-analyzer** - Security analysis
17. **architecture-digitizer** - Architecture analysis
18. **summarizer-hub** - Content summarization
19. **mock-data-generator** - Test data generation

**Rationale**: Specialized services with focused functionality.

### Tier 5: User-Facing Services (Refactor Fifth)
**Frontend and user interface services**

20. **frontend** - Web interface
21. **cli** - Command-line interface
22. **unified-api-dashboard** - API dashboard
23. **simulation-dashboard** - Simulation interface
24. **data-services-dashboard** - Data services UI

**Rationale**: User-facing services that depend on backend services.

### Tier 6: MCP Services (Refactor Sixth)
**Model Context Protocol ecosystem services**

25. **mcp-provisioner** - MCP provisioning
26. **mcp-infrastructure** - MCP infrastructure
27. **mcp-gateway** - MCP gateway
28. **mcp-orchestrator** - MCP orchestration
29. **mcp-interpreter** - MCP interpretation
30. **mcp-registry** - MCP registry
31. **mcp-training-coordinator** - Training coordination
32. **mcp-dashboard** - MCP dashboard
33. **mcp-composer** - MCP composition
34. **mcp-store** - MCP storage
35. **mcp-package-manager** - Package management
36. **mcp-logs** - MCP logging
37. **mcp-performance-store** - Performance metrics

**Rationale**: Specialized MCP ecosystem with internal dependencies.

### Tier 7: Supporting Services (Refactor Last)
**Supporting and utility services**

38. **project-planning-service** - Project planning
39. **project-simulation** - Project simulation
40. **user-store** - User management
41. **external-service-store** - External service tracking
42. **expert-finder-service** - Expert identification
43. **meta-orchestrator** - Meta orchestration

**Rationale**: Supporting services with specific use cases.

---

## 📅 Refactoring Phases

### Phase 1: Foundation (Weeks 1-4)
**Focus**: Establish patterns and refactor foundation services

**Services**: redis, doc_store, orchestrator, llm-gateway

**Goals**:
- Establish refactoring patterns
- Create reusable components
- Set up testing infrastructure
- Document standards

### Phase 2: Core (Weeks 5-8)
**Focus**: Refactor core business services

**Services**: analysis-service ✅, prompt_store, source-agent, discovery-agent, memory-agent

**Goals**:
- Apply established patterns
- Build common libraries
- Enhance testing frameworks
- Create integration tests

### Phase 3: Integration (Weeks 9-11)
**Focus**: Refactor integration services

**Services**: github-mcp, bedrock-proxy, interpreter, log-collector, notification-service

**Goals**:
- Standardize external integrations
- Create integration patterns
- Enhance error handling
- Improve resilience

### Phase 4: Analysis (Weeks 12-14)
**Focus**: Refactor analysis and processing services

**Services**: code-analyzer, secure-analyzer, architecture-digitizer, summarizer-hub, mock-data-generator

**Goals**:
- Optimize analysis workflows
- Improve performance
- Enhance accuracy
- Create analysis patterns

### Phase 5: User-Facing (Weeks 15-17)
**Focus**: Refactor user interface services

**Services**: frontend, cli, unified-api-dashboard, simulation-dashboard, data-services-dashboard

**Goals**:
- Improve user experience
- Enhance error messages
- Optimize performance
- Create UI patterns

### Phase 6: MCP Ecosystem (Weeks 18-22)
**Focus**: Refactor MCP services

**Services**: All MCP services (13 services)

**Goals**:
- Standardize MCP patterns
- Improve interoperability
- Enhance performance
- Create MCP patterns

### Phase 7: Supporting (Weeks 23-25)
**Focus**: Refactor remaining services

**Services**: project-planning-service, project-simulation, user-store, etc.

**Goals**:
- Complete standardization
- Final integration testing
- Performance optimization
- Documentation completion

---

## ✅ Quality Gates

Each service must pass these quality gates before moving to the next service:

### Gate 1: Architecture Review
- [ ] Follows DDD structure
- [ ] Clear layer separation
- [ ] Proper dependency injection
- [ ] No circular dependencies
- [ ] Bounded contexts defined

### Gate 2: Code Quality
- [ ] Cyclomatic complexity < 10
- [ ] No code duplication
- [ ] Follows naming conventions
- [ ] Proper error handling
- [ ] Type hints on all public APIs

### Gate 3: Testing
- [ ] Unit test coverage > 80% (per [Comprehensive Testing Strategy](./COMPREHENSIVE_TESTING_STRATEGY.md))
- [ ] Integration tests pass
- [ ] Functional tests cover all core features (80%+ coverage)
- [ ] E2E tests for critical workflows
- [ ] Performance tests pass
- [ ] All tests documented
- [ ] Test pyramid followed (60% unit, 30% integration, 10% E2E)
- [ ] Tests run in < 5 minutes

### Gate 4: Documentation
- [ ] Comprehensive README complete (per [Service Documentation Strategy](./SERVICE_DOCUMENTATION_STRATEGY.md))
- [ ] Solo capabilities documented
- [ ] Ecosystem contributions documented
- [ ] Major libraries documented (with versions and purposes)
- [ ] Service relationships documented (providers/consumers)
- [ ] Architecture diagrams present (ecosystem + data flow + workflows)
- [ ] Visual elements clear and up-to-date
- [ ] OpenAPI documentation complete
- [ ] Integration guide written
- [ ] Troubleshooting guide complete

### Gate 5: Docker & Deployment
- [ ] Runs standalone in terminal
- [ ] Docker container builds
- [ ] Docker Compose standalone works
- [ ] Ecosystem integration works
- [ ] Health checks functional

### Gate 6: Configuration
- [ ] Configuration standardized
- [ ] Environment variables documented
- [ ] Config validation present
- [ ] Default values provided
- [ ] Example config included

### Gate 7: API Standards
- [ ] REST principles followed
- [ ] Swagger annotations complete (per [API Standardization Strategy](./API_STANDARDIZATION_STRATEGY.md))
- [ ] Swagger UI available at `/docs`
- [ ] OpenAPI spec available at `/openapi.json`
- [ ] Standard endpoints implemented:
  - [ ] `GET /health` (service health check)
  - [ ] `GET /about-me` (service descriptor with capabilities)
  - [ ] `GET /endpoints` (list of all endpoints)
  - [ ] `GET /provider-consumer` (service relationships)
- [ ] Error responses standardized
- [ ] Versioning implemented
- [ ] Rate limiting configured

### Gate 8: Integration
- [ ] Service discovery registered
- [ ] Event publishing works
- [ ] Dependency injection works
- [ ] Circuit breakers configured
- [ ] Retry logic implemented

### Gate 9: Logging & Observability
- [ ] Structured logging implemented (per [Standardized Logging Strategy](./STANDARDIZED_LOGGING_STRATEGY.md))
- [ ] All core features logged
- [ ] Log-collector integration working
- [ ] Correlation IDs tracked
- [ ] Performance metrics logged (duration_ms)
- [ ] Error logging comprehensive
- [ ] No sensitive data in logs
- [ ] Log levels appropriate
- [ ] JSON format validated

---

## 📚 Documentation Requirements

### Service README Template
Each service must have a comprehensive README covering:

1. **Overview**
   - Service purpose and responsibilities
   - Key features
   - Architecture diagram

2. **Quick Start**
   - Installation instructions
   - Configuration steps
   - Running locally
   - Running in Docker

3. **Architecture**
   - DDD layers explanation
   - Component diagrams
   - Data flow diagrams
   - Dependency map

4. **API Documentation**
   - Endpoint list
   - Request/response examples
   - Authentication requirements
   - Rate limiting info

5. **Configuration**
   - Environment variables
   - Configuration files
   - Feature flags
   - Secrets management

6. **Development**
   - Local setup guide
   - Testing guide
   - Debugging tips
   - Contributing guidelines

7. **Integration**
   - Dependencies
   - Integration patterns
   - Event contracts
   - Example usage

8. **Troubleshooting**
   - Common issues
   - Error codes
   - Debugging guide
   - Support contacts

### OpenAPI Documentation
- Complete operation descriptions
- Request/response schemas
- Example requests
- Error responses
- Security requirements

---

## 📊 Success Metrics

### Code Quality Metrics
- **Test Coverage**: > 80% across all services
- **Code Complexity**: Average cyclomatic complexity < 8
- **Duplication**: < 3% code duplication
- **Technical Debt**: < 10% of total development time

### Performance Metrics
- **Response Time**: P95 < 200ms for API calls
- **Throughput**: > 100 requests/second per service
- **Error Rate**: < 0.1% error rate
- **Availability**: > 99.9% uptime

### Documentation Metrics
- **API Coverage**: 100% of endpoints documented
- **README Quality**: All sections complete
- **Code Comments**: All public APIs documented
- **Architecture Docs**: Up-to-date diagrams

### Standardization Metrics
- **DDD Compliance**: 100% of services follow DDD structure
- **REST Compliance**: 100% of APIs follow REST principles
- **Config Standards**: 100% of services use standard config
- **Naming Consistency**: 100% follow naming conventions

---

## 🔄 Continuous Improvement

### Regular Reviews
- Weekly: Progress review and planning
- Bi-weekly: Architecture review and pattern assessment
- Monthly: Comprehensive metrics review
- Quarterly: Standards and patterns update

### Feedback Loops
- Developer feedback on patterns
- Team retrospectives after each tier
- Architecture decision record (ADR) updates
- Pattern library maintenance

### Living Documentation
- Refactoring plan updates
- Progress tracker maintenance
- Standards document evolution
- Lessons learned capture

---

## 📖 Related Documents

- [Living Progress Tracker](./LIVING_PROGRESS_TRACKER.md) - Track refactoring progress
- [Naming Conventions & Standards](./NAMING_CONVENTIONS_STANDARDS.md) - Coding standards
- [Service Audit Template](./SERVICE_AUDIT_TEMPLATE.md) - Audit checklist
- [TDD Checklist](./TDD_CHECKLIST.md) - Test-driven development guide

---

**Document Control**  
**Version History**:
- v1.0.0 (2025-10-08): Initial creation

**Next Review**: 2025-10-22  
**Owner**: Hackathon Team  
**Stakeholders**: All developers

