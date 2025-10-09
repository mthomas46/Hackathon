# Test Plan - code-analyzer

**Service**: code-analyzer  
**Date**: October 9, 2025  
**Phase**: 2.3 Test Planning  
**Target Coverage**: 80%+

---

## 🎯 Testing Strategy

### Testing Pyramid

```
        /\
       /  \
      /E2E \      10% - End-to-End Tests
     /------\
    /  INT   \    30% - Integration Tests
   /----------\
  /   UNIT     \  60% - Unit Tests
 /--------------\
```

**Coverage Goals**:
- Unit Tests: 60% of tests, targeting 85% code coverage
- Integration Tests: 30% of tests, covering service interactions
- E2E Tests: 10% of tests, covering critical workflows

---

## 🧪 Unit Tests (60% of effort)

### Domain Layer Tests

#### 1. CodeAnalysis Entity Tests
**File**: `tests/unit/domain/test_code_analysis.py`

**Test Cases**:
- ✅ Create CodeAnalysis with valid inputs
- ✅ Reject CodeAnalysis with empty code
- ✅ Reject CodeAnalysis with unsupported language
- ✅ Status transitions (PENDING → ANALYZING → COMPLETED)
- ✅ Cannot transition from COMPLETED to ANALYZING
- ✅ Failed status handling
- ✅ Immutability of results once COMPLETED

**Coverage Target**: 90%

---

#### 2. CodeStructure Entity Tests
**File**: `tests/unit/domain/test_code_structure.py`

**Test Cases**:
- ✅ Create function structure
- ✅ Create class structure with methods
- ✅ Validate line_start <= line_end
- ✅ Recursive structures (nested classes)
- ✅ Parameter parsing
- ✅ Docstring extraction

**Coverage Target**: 85%

---

#### 3. Value Object Tests
**File**: `tests/unit/domain/test_value_objects.py`

**Test Cases for Language**:
- ✅ Enum values
- ✅ File extension mapping
- ✅ Equality comparison
- ✅ Immutability

**Test Cases for ComplexityMetrics**:
- ✅ Non-negative constraints
- ✅ Maintainability index 0-100
- ✅ Comment ratio 0.0-1.0
- ✅ Calculation correctness

**Test Cases for AnalysisStatus**:
- ✅ Valid transitions
- ✅ Invalid transitions

**Coverage Target**: 95% (simpler code)

---

### Domain Service Tests

#### 4. CodeAnalyzer Service Tests
**File**: `tests/unit/domain/services/test_code_analyzer.py`

**Test Cases**:
- ✅ Analyze simple Python function
- ✅ Analyze Python class
- ✅ Analyze multi-file module
- ✅ Handle syntax errors gracefully
- ✅ Coordinate sub-analyzers correctly
- ✅ Aggregate results from all analyzers
- ✅ Apply business rules (complexity thresholds)

**Coverage Target**: 80%

---

#### 5. StructureExtractor Service Tests
**File**: `tests/unit/domain/services/test_structure_extractor.py`

**Test Cases**:
- ✅ Extract Python functions
- ✅ Extract Python classes
- ✅ Extract nested structures
- ✅ Handle decorators
- ✅ Extract method parameters
- ✅ Extract docstrings
- ✅ Handle malformed code

**Coverage Target**: 85%

---

#### 6. ComplexityCalculator Service Tests
**File**: `tests/unit/domain/services/test_complexity_calculator.py`

**Test Cases**:
- ✅ Calculate cyclomatic complexity
- ✅ Calculate cognitive complexity
- ✅ Calculate maintainability index
- ✅ Compute comment ratio
- ✅ Handle empty code
- ✅ Verify against known complexity values

**Coverage Target**: 90%

---

#### 7. SecurityScanner Service Tests
**File**: `tests/unit/domain/services/test_security_scanner.py`

**Test Cases**:
- ✅ Detect SQL injection patterns
- ✅ Detect XSS vulnerabilities
- ✅ Detect hardcoded secrets
- ✅ Detect insecure deserialization
- ✅ Detect command injection
- ✅ Severity classification
- ✅ False positive handling

**Coverage Target**: 75%

---

### Application Layer Tests

#### 8. Application Services Tests
**File**: `tests/unit/application/test_analysis_service.py`

**Test Cases**:
- ✅ Handle analyze request
- ✅ Validate input
- ✅ Call domain services
- ✅ Map to response DTOs
- ✅ Handle domain exceptions
- ✅ Transaction boundaries

**Coverage Target**: 80%

---

### Infrastructure Layer Tests

#### 9. API Tests (Presentation Layer)
**File**: `tests/unit/presentation/test_api_endpoints.py`

**Test Cases**:
- ✅ POST /api/v2/analyze endpoint
- ✅ POST /api/v2/analyze/structure endpoint
- ✅ POST /api/v2/analyze/complexity endpoint
- ✅ POST /api/v2/analyze/security endpoint
- ✅ GET /api/v2/health endpoint
- ✅ GET /api/v2/about-me endpoint
- ✅ GET /api/v2/endpoints endpoint
- ✅ GET /api/v2/provider-consumer endpoint
- ✅ Request validation
- ✅ Error handling
- ✅ Response formatting

**Coverage Target**: 90%

---

## 🔗 Integration Tests (30% of effort)

### Service Integration Tests

#### 10. Full Analysis Integration Test
**File**: `tests/integration/test_full_analysis.py`

**Test Cases**:
- ✅ End-to-end analysis flow (request → domain → response)
- ✅ All layers working together
- ✅ Real code samples (Python, JS, etc.)
- ✅ Performance benchmarks (< 2 seconds for typical code)

**Coverage Target**: Key workflows covered

---

#### 11. API Integration Tests
**File**: `tests/integration/test_api_integration.py`

**Test Cases**:
- ✅ Test actual HTTP requests
- ✅ Swagger UI accessible
- ✅ OpenAPI spec valid
- ✅ CORS handling
- ✅ Error responses properly formatted
- ✅ Standard endpoints functional

**Coverage Target**: All endpoints tested

---

#### 12. Shared Infrastructure Integration
**File**: `tests/integration/test_shared_infrastructure.py`

**Test Cases**:
- ✅ Health check integration
- ✅ Logging integration
- ✅ Middleware chain
- ✅ Config loading
- ✅ Error handling middleware

**Coverage Target**: Shared components verified

---

## 🌐 End-to-End Tests (10% of effort)

### Critical Workflow Tests

#### 13. Prompt Store Integration Test
**File**: `tests/e2e/test_prompt_store_workflow.py`

**Test Cases**:
- ✅ Prompt store requests code analysis
- ✅ Code analyzer processes request
- ✅ Results returned to prompt store
- ✅ Error handling across services

**Coverage Target**: Primary consumer workflow

---

## 🚀 Performance Tests

#### 14. Load Tests
**File**: `tests/performance/test_load.py`

**Test Cases**:
- ✅ 100 concurrent requests
- ✅ Large file analysis (10K+ lines)
- ✅ Response time < 2s for typical code
- ✅ Memory usage reasonable

**Coverage Target**: Performance benchmarks

---

## 🔒 Security Tests

#### 15. Security Tests
**File**: `tests/security/test_security.py`

**Test Cases**:
- ✅ Code injection prevention
- ✅ Input validation
- ✅ Rate limiting
- ✅ Authentication/authorization (if applicable)

**Coverage Target**: Security requirements validated

---

## 📊 Test Matrix

| Layer | Files | Unit Tests | Integration Tests | Coverage Target |
|-------|-------|------------|-------------------|-----------------|
| Domain Entities | 3 | 45 | - | 90% |
| Domain Services | 4 | 50 | - | 80% |
| Application | 1 | 20 | 10 | 80% |
| Infrastructure | 1 | 30 | 15 | 85% |
| Presentation | 1 | 40 | 10 | 90% |
| E2E | - | - | 5 | Workflows |
| **Total** | **10** | **185** | **40** | **80%+** |

---

## 🛠️ Testing Tools

### Required Tools
- `pytest` - Test framework
- `pytest-cov` - Coverage reporting
- `pytest-asyncio` - Async test support
- `httpx` - HTTP client for integration tests
- `faker` - Test data generation
- `factory-boy` - Object factories

### Code Quality Tools
- `mypy` - Type checking
- `pylint` - Linting
- `black` - Code formatting
- `radon` - Complexity metrics

---

## 🏃 Test Execution Plan

### Phase 3: TDD Implementation

**Red Phase** (Write Failing Tests):
1. Week 1: Domain entity tests (45 tests)
2. Week 2: Domain service tests (50 tests)
3. Week 3: Application + Infrastructure tests (50 tests)
4. Week 4: Presentation + Integration tests (50 tests)

**Green Phase** (Make Tests Pass):
1. Implement domain entities
2. Implement domain services
3. Implement application services
4. Implement API endpoints

**Refactor Phase** (Optimize):
1. Remove duplication
2. Improve naming
3. Optimize performance
4. Enhance error handling

---

## 📈 Coverage Strategy

### Minimum Coverage Requirements

**Overall**: 80% total coverage

**By Layer**:
- Domain: 85%+ (core business logic)
- Application: 80%+
- Infrastructure: 80%+
- Presentation: 85%+ (API surface)

**Excluded from Coverage**:
- Scaffolding/boilerplate
- Configuration files
- __init__.py files

---

## 🔄 Continuous Testing

### CI/CD Integration

**On Pull Request**:
```bash
pytest tests/unit --cov --cov-fail-under=80
pytest tests/integration
mypy services/code-analyzer
pylint services/code-analyzer
```

**On Merge to Main**:
```bash
pytest tests/ --cov --cov-report=html
pytest tests/e2e
```

**Nightly**:
```bash
pytest tests/performance
pytest tests/security
```

---

## ✅ Test Plan Acceptance Criteria

- [x] Unit test strategy defined (60% of tests)
- [x] Integration test strategy defined (30% of tests)
- [x] E2E test strategy defined (10% of tests)
- [x] 80%+ coverage target set
- [x] Test pyramid followed
- [x] All layers have test cases identified
- [x] Performance tests planned
- [x] Security tests planned
- [x] CI/CD integration planned
- [x] Tools identified

---

## 📝 Test Execution Checklist

**Before Starting TDD** (Phase 3):
- [ ] Install testing tools
- [ ] Configure pytest
- [ ] Set up coverage reporting
- [ ] Create test fixtures
- [ ] Set up test database (if needed)

**During TDD**:
- [ ] Write failing test
- [ ] Run test (should fail)
- [ ] Implement minimum code to pass
- [ ] Run test (should pass)
- [ ] Refactor if needed
- [ ] Commit

**After TDD**:
- [ ] Run full test suite
- [ ] Generate coverage report
- [ ] Review uncovered lines
- [ ] Add missing tests
- [ ] Verify 80%+ coverage achieved

---

**Test Plan Complete**  
**Ready for Phase 3: TDD Implementation**

**Total Planned Tests**: 225 (185 unit + 40 integration/e2e)  
**Target Coverage**: 80%+  
**Estimated Effort**: 4 weeks (Phase 3)

