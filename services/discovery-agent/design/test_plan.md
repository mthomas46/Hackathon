# Test Plan - discovery-agent

**Service**: discovery-agent  
**Date**: October 9, 2025  
**Target Coverage**: 80%+  
**Total Tests Planned**: 110+

> **Detailed Plan**: See [PHASE_2_DESIGN_PLAN.md](../PHASE_2_DESIGN_PLAN.md#-phase-23-comprehensive-test-plan) for complete test specifications.

---

## 🎯 Test Strategy

### **Test Pyramid**

```
        E2E (10%)
       /    10 tests    \
      /                  \
     /  Integration (30%) \
    /      30 tests        \
   /________________________\
  /     Unit Tests (60%)     \
 /         60 tests           \
/______________________________\

Total: 110 tests targeting 80%+ coverage
```

---

## 📊 Test Suite Breakdown

### **Unit Tests** (60 tests, 60% of suite)

**Domain Layer** (30 tests):
- `test_entities.py` - 15 tests
  - Endpoint, Service, DiscoveryResult entities
  - CRUD operations, validation, serialization
- `test_value_objects.py` - 10 tests
  - All 5 value objects (DiscoverySpec, HttpMethod, ApiPath, etc.)
  - Validation, immutability, factory methods
- `test_domain_services.py` - 5 tests
  - Discovery orchestration, semantic analysis, tool generation

**Application Layer** (20 tests):
- `test_commands.py` - 5 tests
- `test_queries.py` - 5 tests
- `test_handlers.py` - 5 tests
- `test_events.py` - 5 tests

**Infrastructure Layer** (10 tests):
- `test_repositories.py` - 5 tests
- `test_external_services.py` - 5 tests

---

### **Integration Tests** (30 tests, 30% of suite)

- `test_discovery_workflow.py` - 10 tests
  - OpenAPI fetching and parsing
  - Endpoint extraction
  - Service registration
- `test_tool_generation_workflow.py` - 10 tests
  - Tool generation from OpenAPI
  - Tool categorization
  - Orchestrator registration
- `test_orchestrator_integration.py` - 5 tests
  - Communication with orchestrator
  - Error handling and retries
- `test_openapi_parsing.py` - 5 tests
  - Complex schema parsing
  - Multiple OpenAPI versions

---

### **E2E Tests** (10 tests, 10% of suite)

- `test_api_endpoints.py` - 6 tests
  - Test all API endpoints
  - Request/response validation
- `test_standard_endpoints.py` - 4 tests
  - Test 4 standard endpoints
  - Response schema validation

---

### **Workflow Tests** (10 tests)

- `test_service_discovery_scenarios.py` - 5 tests
  - Real-world discovery scenarios
  - Multiple services, dependencies
- `test_tool_discovery_scenarios.py` - 5 tests
  - Tool discovery workflows
  - Batch processing, filtering

---

## 🛠️ Test Infrastructure

### **Files to Create**

1. **pytest.ini** - Configuration with 10+ markers
2. **requirements-test.txt** - Test dependencies (pytest, httpx, faker, etc.)
3. **tests/conftest.py** - Shared fixtures
4. **tests/README.md** - Test documentation

### **Test Markers**

```ini
[pytest]
markers =
    unit: Unit tests (fast, isolated)
    integration: Integration tests
    e2e: End-to-end tests
    api: API tests
    domain: Domain layer tests
    application: Application tests
    infrastructure: Infrastructure tests
    discovery: Discovery tests
    tools: Tool tests
    slow: Slow tests
```

---

## ✅ Coverage Targets

| Layer | Target Coverage | Min Tests |
|-------|----------------|-----------|
| Domain | 90%+ | 30 tests |
| Application | 80%+ | 20 tests |
| Infrastructure | 70%+ | 10 tests |
| Presentation (API) | 90%+ | 10 tests |
| **Overall** | **80%+** | **110 tests** |

---

## 🧪 Test Scenarios

### **Critical Scenarios**

1. **Service Discovery Success** ✅
   - Fetch OpenAPI from URL
   - Parse specifications
   - Extract endpoints
   - Register with orchestrator

2. **Tool Generation Success** ✅
   - Convert endpoints to tools
   - Categorize operations
   - Generate descriptions
   - Register tools

3. **Error Handling** ✅
   - Invalid OpenAPI spec
   - Network timeouts
   - Orchestrator unreachable
   - Malformed requests

4. **Standard Endpoints** ✅
   - All 4 standard endpoints working
   - Correct response schemas
   - Consistent behavior

---

## 📝 Test Execution Plan

### **Phase 3.1: Setup** (30 min)
- Create pytest.ini
- Create conftest.py
- Set up test structure
- Install dependencies

### **Phase 3.2: Red Phase** (2 hours)
- Write all 110 tests (failing)
- Organize by layer
- Document test cases

### **Phase 3.3: Green Phase** (3 hours)
- Implement code to pass tests
- Focus on domain layer first
- Then application, infrastructure

### **Phase 3.4: Refactor** (1 hour)
- Improve code quality
- Remove duplication
- Enhance readability

### **Phase 3.5: Validate** (30 min)
- Run full test suite
- Check coverage (target 80%+)
- Validate logging integration

---

## 🎯 Success Criteria

- [ ] 110+ tests written
- [ ] All tests passing (100%)
- [ ] 80%+ code coverage achieved
- [ ] All layers tested
- [ ] Standard endpoints tested
- [ ] Integration with orchestrator tested
- [ ] Error scenarios covered
- [ ] Documentation complete

---

**Status**: ✅ Plan Approved  
**Ready for**: Phase 3 Implementation  
**Estimated Time**: 4-5 hours

