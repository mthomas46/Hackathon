# Test Suite - discovery-agent

**Service**: discovery-agent  
**Target Coverage**: 80%+  
**Total Tests Planned**: 110+

---

## 🎯 Test Organization

### **Directory Structure**

```
tests/
├── conftest.py                    # Shared fixtures (400+ lines)
├── README.md                      # This file
├── unit/                          # Unit tests (60 tests)
│   ├── domain/                    # Domain layer tests
│   │   ├── test_entities.py       # Entity tests (15 tests)
│   │   ├── test_value_objects.py  # Value object tests (10 tests)
│   │   └── test_domain_services.py # Domain service tests (5 tests)
│   ├── application/               # Application layer tests
│   │   ├── test_commands.py       # Command tests (5 tests)
│   │   ├── test_queries.py        # Query tests (5 tests)
│   │   ├── test_handlers.py       # Handler tests (5 tests)
│   │   └── test_events.py         # Event tests (5 tests)
│   └── infrastructure/            # Infrastructure tests
│       ├── test_repositories.py   # Repository tests (5 tests)
│       └── test_external_services.py # External service tests (5 tests)
├── integration/                   # Integration tests (30 tests)
│   ├── test_discovery_workflow.py
│   ├── test_tool_generation_workflow.py
│   ├── test_orchestrator_integration.py
│   └── test_openapi_parsing.py
├── e2e/                          # E2E tests (10 tests)
│   ├── test_api_endpoints.py
│   └── test_standard_endpoints.py
└── workflow/                     # Real-world scenarios (10 tests)
    ├── test_service_discovery_scenarios.py
    └── test_tool_discovery_scenarios.py
```

---

## 🧪 Running Tests

### **All Tests**
```bash
pytest tests/
```

### **By Layer**
```bash
pytest tests/unit/                 # Unit tests only
pytest tests/integration/          # Integration tests only
pytest tests/e2e/                  # E2E tests only
```

### **By Marker**
```bash
pytest -m unit                     # Unit tests
pytest -m integration              # Integration tests
pytest -m e2e                      # E2E tests
pytest -m api                      # API tests
pytest -m domain                   # Domain layer tests
pytest -m discovery                # Discovery tests
pytest -m tools                    # Tool generation tests
```

### **With Coverage**
```bash
pytest --cov=. --cov-report=html
```

### **Specific Test File**
```bash
pytest tests/unit/domain/test_entities.py
```

### **Specific Test**
```bash
pytest tests/unit/domain/test_entities.py::test_endpoint_creation
```

---

## 📊 Test Coverage Targets

| Layer | Target | Status |
|-------|--------|--------|
| Domain | 90%+ | 🎯 In Progress |
| Application | 80%+ | 🎯 In Progress |
| Infrastructure | 70%+ | 🎯 In Progress |
| Presentation | 90%+ | 🎯 In Progress |
| **Overall** | **80%+** | 🎯 **In Progress** |

---

## 🔧 Available Fixtures

See `conftest.py` for full list. Key fixtures:

### **Entities**
- `sample_endpoint` - Endpoint entity
- `sample_service` - Service entity
- `sample_service_with_endpoints` - Service with multiple endpoints
- `sample_discovery_result` - Discovery result

### **Value Objects**
- `sample_discovery_spec_url` - Discovery spec with URL
- `sample_discovery_spec_content` - Discovery spec with content
- `sample_http_method` - HTTP method
- `sample_api_path` - API path

### **OpenAPI Specs**
- `simple_openapi_spec` - Simple OpenAPI 3.0 spec
- `complex_openapi_spec` - Complex OpenAPI 3.0 spec

### **Mocks**
- `mock_orchestrator` - Mock orchestrator service
- `mock_http_client` - Mock HTTP client
- `mock_openapi_fetcher` - Mock OpenAPI fetcher

### **FastAPI**
- `test_client` - FastAPI test client
- `test_app` - FastAPI application

---

## ✅ Test Checklist

### **Phase 3.1: Testing Infrastructure** ✅
- [x] pytest.ini configured
- [x] requirements-test.txt created
- [x] conftest.py with comprehensive fixtures
- [x] tests/README.md created

### **Phase 3.2: Red Phase** (In Progress)
- [ ] Write 60 unit tests
- [ ] Write 30 integration tests
- [ ] Write 10 e2e tests
- [ ] Write 10 workflow tests

### **Phase 3.3: Green Phase** (Planned)
- [ ] Implement to pass unit tests
- [ ] Implement to pass integration tests
- [ ] Implement to pass e2e tests
- [ ] Implement to pass workflow tests

### **Phase 3.4: Refactor** (Planned)
- [ ] Improve code quality
- [ ] Remove duplication
- [ ] Enhance readability

### **Phase 3.5: Validate** (Planned)
- [ ] Achieve 80%+ coverage
- [ ] All tests passing
- [ ] Logging validated

---

**Status**: Infrastructure Complete ✅  
**Next**: Write tests (Red Phase)  
**Updated**: October 9, 2025

