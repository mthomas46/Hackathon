# Phase 2: Design & Planning - discovery-agent

**Service**: discovery-agent  
**Phase**: 2 - Design & Planning  
**Date**: October 9, 2025  
**Status**: ✅ Complete

---

## 🎯 Executive Summary

Phase 2 reviews the existing well-structured DDD architecture and plans comprehensive improvements. The service already has a solid domain model with proper entities, value objects, and services. This phase focuses on planning test infrastructure, standard endpoints implementation, and configuration standardization.

```
╔════════════════════════════════════════════════════════╗
║                                                        ║
║  Existing Architecture: Strong DDD Foundation          ║
║  Plan: Incremental Improvements                        ║
║  Focus: Testing, Standards, Configuration              ║
║                                                        ║
╚════════════════════════════════════════════════════════╝
```

---

## 🏗️ Phase 2.1: Domain Model Review

### **Current Domain Model** ✅ EXCELLENT

The discovery-agent service already has a well-designed DDD architecture:

#### **Entities** (3 entities)

| Entity | Purpose | Quality | Notes |
|--------|---------|---------|-------|
| **Endpoint** | Represents discovered API endpoint | ✅ Excellent | Has proper methods, validation, serialization |
| **Service** | Represents discovered service with endpoints | ✅ Excellent | Aggregate root, manages endpoints |
| **DiscoveryResult** | Result of discovery operation | ✅ Excellent | Proper encapsulation |

**Entity Review**:
- ✅ Proper encapsulation
- ✅ Business logic in entities
- ✅ Immutability where appropriate
- ✅ Serialization methods (to_dict, from_dict)
- ✅ Inherits from BaseEntity (shared infrastructure)
- ⚠️  Uses `datetime.utcnow()` (deprecated in Python 3.12+, should use `datetime.now(timezone.utc)`)

#### **Value Objects** (5 value objects)

| Value Object | Purpose | Quality | Notes |
|--------------|---------|---------|-------|
| **DiscoverySpec** | OpenAPI specification representation | ✅ Excellent | Immutable, validated |
| **EndpointMetadata** | Endpoint metadata from OpenAPI | ✅ Excellent | Factory method included |
| **ServiceMetadata** | Service metadata from OpenAPI info | ✅ Excellent | Factory method included |
| **HttpMethod** | HTTP method validation | ✅ Excellent | Validation, helper methods |
| **ApiPath** | API path validation | ✅ Excellent | Validation, path parsing |

**Value Object Review**:
- ✅ Immutable (frozen dataclasses)
- ✅ Validation in `__post_init__`
- ✅ No identity (compared by value)
- ✅ Rich behavior (helper properties)
- ✅ Factory methods for complex construction

#### **Domain Services** (5 services)

| Service | Purpose | Status |
|---------|---------|--------|
| **discovery_service.py** | Core discovery orchestration | ✅ Implemented |
| **semantic_analyzer.py** | Semantic analysis of endpoints | ✅ Implemented |
| **tool_discovery.py** | LangGraph tool generation | ⚠️  Partial (has placeholder) |
| **tool_registry.py** | Tool registry management | ✅ Implemented |
| **shared_utils.py** | Shared domain utilities | ⚠️  Should refactor to helpers |

**Domain Service Review**:
- ✅ Proper separation of concerns
- ✅ Orchestration logic in services
- ✅ No infrastructure concerns in domain
- ⚠️  `shared_utils.py` should be refactored to `helpers/` or individual services
- ⚠️  `tool_discovery.py` has placeholder code (needs completion)

### **Domain Model Refinements Needed**

| Issue | Priority | Action |
|-------|----------|--------|
| Deprecated datetime | 🟡 Medium | Replace `datetime.utcnow()` with `datetime.now(timezone.utc)` |
| shared_utils.py | 🟡 Medium | Refactor to domain/helpers/ or specific services |
| tool_discovery.py placeholders | 🟢 Low | Complete implementation (or mark as future work) |

**Overall Domain Model Score**: **9/10** (Excellent, minor refinements needed)

---

## 📡 Phase 2.2: API Design & Configuration

### **Current API Endpoints Review**

| Endpoint | Method | Status | Notes |
|----------|--------|--------|-------|
| `/health` | GET | ✅ Exists | Standard health check |
| `/api/v1/discover` | POST | ✅ Exists | Core discovery |
| `/api/v1/discover/tools` | POST | ✅ Exists | Tool discovery |
| `/docs` | GET | ✅ Exists | Swagger UI |
| `/redoc` | GET | ✅ Exists | ReDoc |

**API Review**:
- ✅ RESTful design
- ✅ Version prefix (`/api/v1/`)
- ✅ OpenAPI/Swagger auto-generation
- ✅ Clear endpoint naming
- ❌ **Missing 3 standard endpoints**

### **Standard Endpoints to Implement** 🔴 CRITICAL

#### 1. `/about-me` Endpoint

**Purpose**: Service descriptor for ecosystem integration

**Response Schema**:
```json
{
  "service": "discovery-agent",
  "version": "1.0.0",
  "description": "Automated service discovery engine...",
  "capabilities": [
    "service_discovery",
    "tool_generation",
    "openapi_analysis"
  ],
  "features": {
    "discovery_types": ["openapi", "health_check"],
    "tool_formats": ["langgraph"],
    "analysis": ["semantic", "endpoint_extraction"]
  },
  "ecosystem_role": "integration",
  "tier": 3,
  "dependencies": {
    "providers": ["orchestrator", "log-collector"],
    "consumers": ["orchestrator", "all-services"]
  },
  "architecture": {
    "pattern": "DDD",
    "layers": 4,
    "patterns": ["CQRS", "Event-Driven"]
  },
  "quality_metrics": {
    "test_coverage": "TBD",
    "total_tests": "TBD"
  }
}
```

#### 2. `/endpoints` Endpoint

**Purpose**: List all available API endpoints

**Response Schema**:
```json
{
  "service": "discovery-agent",
  "version": "1.0.0",
  "base_url": "http://localhost:5050",
  "endpoints": [
    {
      "path": "/health",
      "methods": ["GET"],
      "description": "Health check",
      "authentication": false,
      "category": "standard"
    },
    {
      "path": "/about-me",
      "methods": ["GET"],
      "description": "Service descriptor",
      "authentication": false,
      "category": "standard"
    },
    {
      "path": "/endpoints",
      "methods": ["GET"],
      "description": "API endpoint list",
      "authentication": false,
      "category": "standard"
    },
    {
      "path": "/provider-consumer",
      "methods": ["GET"],
      "description": "Service relationships",
      "authentication": false,
      "category": "standard"
    },
    {
      "path": "/api/v1/discover",
      "methods": ["POST"],
      "description": "Discover service and extract endpoints",
      "authentication": false,
      "category": "core"
    },
    {
      "path": "/api/v1/discover/tools",
      "methods": ["POST"],
      "description": "Discover LangGraph tools",
      "authentication": false,
      "category": "core"
    }
  ],
  "total_endpoints": 6,
  "categories": {
    "standard": 4,
    "core": 2
  }
}
```

#### 3. `/provider-consumer` Endpoint

**Purpose**: Document service dependencies and relationships

**Response Schema**:
```json
{
  "service": "discovery-agent",
  "version": "1.0.0",
  "relationships": {
    "providers": [
      {
        "service": "orchestrator",
        "relationship": "provider",
        "purpose": "Service registration and tool registry",
        "endpoints_used": [
          "POST /registry/services",
          "POST /tools/register"
        ],
        "data_consumed": []
      },
      {
        "service": "log-collector",
        "relationship": "provider",
        "purpose": "Structured logging",
        "endpoints_used": ["POST /logs"],
        "required": false
      },
      {
        "service": "target-services",
        "relationship": "provider",
        "purpose": "Services to discover",
        "endpoints_used": [
          "GET /openapi.json",
          "GET /health"
        ]
      }
    ],
    "consumers": [
      {
        "service": "orchestrator",
        "relationship": "consumer",
        "purpose": "Receives discovered services and tools",
        "data_consumed": [
          "service_metadata",
          "tool_definitions",
          "endpoint_catalog"
        ],
        "endpoints_provided": [
          "POST /api/v1/discover",
          "POST /api/v1/discover/tools"
        ]
      },
      {
        "service": "all-services",
        "relationship": "consumer",
        "purpose": "Self-registration capability",
        "data_consumed": [],
        "endpoints_provided": [
          "POST /api/v1/discover"
        ],
        "notes": "Any service can use discovery-agent for self-registration"
      }
    ]
  },
  "dependencies": {
    "external_apis": [],
    "databases": [],
    "message_queues": [],
    "cache_systems": ["redis (optional)"]
  },
  "provides_data_to": [
    "orchestrator",
    "all-services"
  ],
  "consumes_data_from": [
    "orchestrator",
    "target-services"
  ],
  "self_contained": false,
  "notes": "Requires orchestrator for service registration"
}
```

### **Port Configuration Plan** 🔴 CRITICAL

**Current Configuration**:
- HTTP: **5045** (config.yaml)
- Internal: **Not configured**

**Target Configuration** (per MASTER_CONFIGURATION_REGISTRY.md):
- HTTP: **5050**
- Internal: **5051**

**Actions Required**:
1. Update `config.yaml` server.port: 5045 → 5050
2. Add internal port configuration: 5051
3. Update environment variable defaults
4. Update docker-compose.yml ports
5. Update README.md port references
6. Update MASTER_CONFIGURATION_REGISTRY.md status

**Files to Update**:
- `config.yaml`
- `config.development.yaml`
- `config.production.yaml`
- `main.py` (DEFAULT_API_PORT)
- `docker-compose.yml`
- `README.md`
- `../../docs/refactoring/MASTER_CONFIGURATION_REGISTRY.md`

---

## 🧪 Phase 2.3: Comprehensive Test Plan

### **Test Coverage Target**: 80%+ (100+ tests)

### **Test Infrastructure Setup**

**Files to Create**:
1. `pytest.ini` - pytest configuration with markers
2. `requirements-test.txt` - test dependencies
3. `tests/conftest.py` - shared fixtures
4. `tests/README.md` - test documentation

**Test Markers** (in pytest.ini):
```ini
markers =
    unit: Unit tests (fast, isolated)
    integration: Integration tests (with dependencies)
    e2e: End-to-end tests (full workflow)
    api: API endpoint tests
    domain: Domain layer tests
    application: Application layer tests
    infrastructure: Infrastructure layer tests
    discovery: Discovery operation tests
    tools: Tool generation tests
    slow: Tests that take significant time
```

### **Test Suite Structure**

```
tests/
├── conftest.py                    # Shared fixtures
├── README.md                      # Test documentation
├── unit/                          # Unit tests (60% of suite)
│   ├── domain/                    # Domain layer tests
│   │   ├── test_entities.py       # Endpoint, Service, DiscoveryResult
│   │   ├── test_value_objects.py  # ✅ EXISTS (expand)
│   │   ├── test_discovery_service.py
│   │   ├── test_semantic_analyzer.py
│   │   ├── test_tool_discovery.py
│   │   └── test_tool_registry.py
│   ├── application/               # Application layer tests
│   │   ├── test_commands.py
│   │   ├── test_queries.py
│   │   ├── test_handlers.py
│   │   └── test_events.py
│   └── infrastructure/            # Infrastructure tests
│       ├── test_repositories.py
│       └── test_external_services.py
├── integration/                   # Integration tests (30%)
│   ├── test_discovery_workflow.py
│   ├── test_tool_generation_workflow.py
│   ├── test_orchestrator_integration.py
│   └── test_openapi_parsing.py
├── e2e/                          # E2E tests (10%)
│   ├── test_api_endpoints.py
│   ├── test_standard_endpoints.py
│   └── test_full_discovery_flow.py
└── workflow/                     # Real-world scenarios
    ├── test_service_discovery_scenarios.py
    └── test_tool_discovery_scenarios.py
```

### **Detailed Test Plan**

#### **Unit Tests (60 tests, 60% coverage)**

**Domain Layer (30 tests)**:

1. **test_entities.py** (15 tests)
   - `test_endpoint_creation`
   - `test_endpoint_operation_id_generation`
   - `test_endpoint_serialization_deserialization`
   - `test_service_creation`
   - `test_service_add_endpoint`
   - `test_service_remove_endpoint`
   - `test_service_health_url`
   - `test_service_endpoint_count`
   - `test_service_serialization_deserialization`
   - `test_discovery_result_success`
   - `test_discovery_result_failure`
   - `test_discovery_result_endpoint_count`
   - `test_entity_timestamps`
   - `test_entity_id_generation`
   - `test_entity_update_tracking`

2. **test_value_objects.py** (10 tests) - ✅ Expand existing
   - `test_discovery_spec_with_url`
   - `test_discovery_spec_with_content`
   - `test_discovery_spec_validation`
   - `test_http_method_validation`
   - `test_http_method_safe_idempotent`
   - `test_api_path_validation`
   - `test_api_path_parameters`
   - `test_endpoint_metadata_from_openapi`
   - `test_service_metadata_from_openapi`
   - `test_value_object_immutability`

3. **test_domain_services.py** (5 tests)
   - `test_discovery_service_orchestration`
   - `test_semantic_analyzer_categorization`
   - `test_tool_discovery_generation`
   - `test_tool_registry_operations`
   - `test_domain_service_error_handling`

**Application Layer (20 tests)**:

4. **test_commands.py** (5 tests)
   - `test_discover_service_command`
   - `test_discover_tools_command`
   - `test_register_service_command`
   - `test_command_validation`
   - `test_command_execution`

5. **test_queries.py** (5 tests)
   - `test_get_service_query`
   - `test_list_services_query`
   - `test_get_tools_query`
   - `test_query_validation`
   - `test_query_execution`

6. **test_handlers.py** (5 tests)
   - `test_discovery_handler`
   - `test_service_handler`
   - `test_ai_tool_selector`
   - `test_orchestrator_integration_handler`
   - `test_handler_error_handling`

7. **test_events.py** (5 tests)
   - `test_discovery_completed_event`
   - `test_service_registered_event`
   - `test_tool_generated_event`
   - `test_event_creation`
   - `test_event_serialization`

**Infrastructure Layer (10 tests)**:

8. **test_repositories.py** (5 tests)
   - `test_service_repository_save`
   - `test_service_repository_find`
   - `test_service_repository_list`
   - `test_service_repository_delete`
   - `test_repository_error_handling`

9. **test_external_services.py** (5 tests)
   - `test_http_client_get`
   - `test_http_client_post`
   - `test_http_client_timeout`
   - `test_http_client_error_handling`
   - `test_langgraph_integration`

#### **Integration Tests (30 tests, 30% coverage)**

10. **test_discovery_workflow.py** (10 tests)
    - `test_discover_service_from_openapi_url`
    - `test_discover_service_from_inline_spec`
    - `test_discover_service_endpoint_extraction`
    - `test_discover_service_metadata_extraction`
    - `test_discover_service_with_orchestrator`
    - `test_discover_service_error_handling`
    - `test_discover_service_timeout_handling`
    - `test_discover_service_invalid_spec`
    - `test_discover_service_version_detection`
    - `test_discover_service_health_check`

11. **test_tool_generation_workflow.py** (10 tests)
    - `test_generate_tools_from_openapi`
    - `test_tool_categorization`
    - `test_tool_parameter_extraction`
    - `test_tool_description_generation`
    - `test_tool_registration_with_orchestrator`
    - `test_tool_generation_dry_run`
    - `test_tool_generation_filtering`
    - `test_tool_generation_error_handling`
    - `test_tool_generation_batch_processing`
    - `test_tool_generation_validation`

12. **test_orchestrator_integration.py** (5 tests)
    - `test_register_service_with_orchestrator`
    - `test_register_tools_with_orchestrator`
    - `test_orchestrator_communication_retry`
    - `test_orchestrator_communication_timeout`
    - `test_orchestrator_error_response_handling`

13. **test_openapi_parsing.py** (5 tests)
    - `test_parse_openapi_v3`
    - `test_parse_paths`
    - `test_parse_parameters`
    - `test_parse_responses`
    - `test_parse_complex_schemas`

#### **E2E Tests (10 tests, 10% coverage)**

14. **test_api_endpoints.py** (6 tests)
    - `test_discover_endpoint_success`
    - `test_discover_endpoint_validation`
    - `test_discover_tools_endpoint_success`
    - `test_discover_tools_endpoint_dry_run`
    - `test_health_endpoint`
    - `test_openapi_docs_available`

15. **test_standard_endpoints.py** (4 tests)
    - `test_about_me_endpoint`
    - `test_endpoints_list_endpoint`
    - `test_provider_consumer_endpoint`
    - `test_standard_endpoints_consistency`

#### **Workflow Tests (10+ tests)**

16. **test_service_discovery_scenarios.py** (5 tests)
    - `test_discover_multiple_services`
    - `test_discover_service_with_dependencies`
    - `test_discover_service_incremental_updates`
    - `test_discover_service_failure_recovery`
    - `test_discover_service_concurrent_requests`

17. **test_tool_discovery_scenarios.py** (5 tests)
    - `test_tool_discovery_full_workflow`
    - `test_tool_discovery_with_filtering`
    - `test_tool_discovery_batch_processing`
    - `test_tool_discovery_iterative_refinement`
    - `test_tool_discovery_performance`

**Total Tests**: **110 tests**

---

## 🔄 Phase 2.4: Migration Strategy

### **API Versioning Strategy**

**Current**: `/api/v1/` prefix exists

**Strategy**: No breaking changes needed
- Keep existing `/api/v1/` endpoints unchanged
- Add standard endpoints at root level (`/about-me`, etc.)
- Maintain backward compatibility

### **Port Migration Strategy**

**Current**: Service running on port 5045

**Target**: Port 5050-5051

**Migration Plan**:
1. **Development**: Update immediately (no impact)
2. **Staging**: Deploy with new ports (coordinate with orchestrator)
3. **Production**: Rolling update strategy
   - Update orchestrator configuration first
   - Deploy discovery-agent with new ports
   - Verify connectivity
   - Decommission old port

**Rollback Plan**:
- Keep old configuration files as `.backup`
- Document original port settings
- Test rollback procedure in development

### **Feature Flags**

Not needed for this refactoring (no feature changes, only improvements)

### **Database Migrations**

Not applicable (no database schema changes)

### **Backward Compatibility**

✅ **100% backward compatible**
- Existing API endpoints unchanged
- Only adding new standard endpoints
- Port change coordinated with orchestrator
- No breaking changes to request/response schemas

---

## 📋 Phase 2 Deliverables Summary

| Deliverable | Status | Notes |
|-------------|--------|-------|
| **Domain Model Review** | ✅ Complete | Excellent foundation (9/10) |
| **API Design Plan** | ✅ Complete | 3 standard endpoints to add |
| **Port Configuration Plan** | ✅ Complete | 5045 → 5050-5051 |
| **Test Plan** | ✅ Complete | 110 tests planned |
| **Migration Strategy** | ✅ Complete | Backward compatible |
| **PHASE_2_DESIGN_PLAN.md** | ✅ Complete | This document |

---

## 🎯 Key Decisions Made

### **1. Domain Model** ✅ Keep Existing

**Decision**: Keep existing domain model with minor refinements

**Rationale**:
- Excellent DDD structure already in place
- Proper entities, value objects, and services
- Only minor improvements needed (datetime deprecation)
- Would waste time rebuilding what's already good

**Actions**:
- Replace `datetime.utcnow()` with `datetime.now(timezone.utc)` during refactoring
- Refactor `shared_utils.py` to proper structure
- Complete `tool_discovery.py` placeholders

### **2. API Design** ✅ Add Standard Endpoints

**Decision**: Add 3 standard endpoints while keeping existing API

**Rationale**:
- Existing API is well-designed (RESTful, versioned)
- Standard endpoints required for ecosystem integration
- No breaking changes needed
- Backward compatible

**Actions**:
- Implement `/about-me`
- Implement `/endpoints`
- Implement `/provider-consumer`
- Test all endpoints comprehensively

### **3. Port Configuration** ✅ Update to Registry Standard

**Decision**: Update ports from 5045 to 5050-5051

**Rationale**:
- Align with ecosystem standard (MASTER_CONFIGURATION_REGISTRY.md)
- Prevent conflicts
- Enable internal communication on separate port
- Coordinate with orchestrator

**Actions**:
- Update all configuration files
- Coordinate with orchestrator team
- Test port changes
- Document migration

### **4. Testing Strategy** ✅ Comprehensive TDD

**Decision**: Implement comprehensive test suite (110+ tests, 80%+ coverage)

**Rationale**:
- Current coverage ~5% (1 test file)
- Cannot safely refactor without tests
- Need confidence in changes
- Follow test pyramid (60/30/10)

**Actions**:
- Set up test infrastructure (pytest.ini, conftest.py)
- Write 110+ tests following TDD
- Achieve 80%+ coverage
- Document testing approach

### **5. Migration Approach** ✅ Incremental, Backward Compatible

**Decision**: Incremental improvements, no breaking changes

**Rationale**:
- Service is functional and in use
- Breaking changes would impact ecosystem
- Incremental approach reduces risk
- Can deploy progressively

**Actions**:
- Keep existing API unchanged
- Add features incrementally
- Coordinate port changes
- Test thoroughly before deployment

---

## 📊 Phase 2 Metrics

| Metric | Value |
|--------|-------|
| **Domain Model Quality** | 9/10 |
| **APIs to Keep** | 5 |
| **APIs to Add** | 3 |
| **Tests Planned** | 110+ |
| **Target Coverage** | 80%+ |
| **Port Changes** | 2 (HTTP, Internal) |
| **Breaking Changes** | 0 |
| **Backward Compatible** | ✅ Yes |
| **Estimated Implementation Time** | 8-10 hours |

---

## ✅ Phase 2 Completion Checklist

- [x] Domain model reviewed and assessed (9/10)
- [x] Entities analyzed (3 entities, excellent quality)
- [x] Value objects analyzed (5 VOs, excellent quality)
- [x] Domain services reviewed (5 services, good separation)
- [x] API endpoints reviewed (5 existing, 3 to add)
- [x] Standard endpoints designed (schemas defined)
- [x] Port configuration plan created (5045 → 5050-5051)
- [x] Comprehensive test plan created (110+ tests)
- [x] Test infrastructure planned (pytest.ini, conftest.py)
- [x] Migration strategy defined (backward compatible)
- [x] Feature flags assessed (not needed)
- [x] Rollback plan documented
- [x] Key decisions documented and rationalized

---

## 🚀 Next Phase: Phase 3 - TDD Implementation

**Estimated Time**: 4-5 hours

**Focus**:
1. Set up testing infrastructure
2. Write 110+ tests (TDD Red/Green/Refactor)
3. Achieve 80%+ test coverage
4. Implement standard endpoints
5. Update port configuration
6. Validate all changes

**Key Activities**:
- Phase 3.1: Set up testing infrastructure
- Phase 3.2: Red Phase (write failing tests)
- Phase 3.3: Green Phase (implement to pass tests)
- Phase 3.4: Refactor Phase (improve code quality)
- Phase 3.5: Validate (coverage, logging)

---

**Phase 2 Status**: ✅ **COMPLETE**  
**Ready for**: Phase 3 (TDD Implementation)  
**Confidence**: **HIGH** (strong foundation, clear plan)

---

**Document Version**: 1.0  
**Last Updated**: October 9, 2025  
**Created By**: AI Agent

