# Phase 1: Audit & Analysis - expert-finder-service

**Date**: October 10, 2025  
**Service**: expert-finder-service  
**Current Version**: 1.0.0  
**Refactoring Plan**: v1.5.0

---

## 📊 Current State Assessment

### Service Overview
- **Purpose**: Intelligent user discovery and subject matter expert identification
- **Type**: REST API Service (FastAPI)
- **Port**: 5160
- **Architecture**: Monolithic (1,286-line main.py)
- **Dependencies**: user-store, doc-store, external-service-store

### File Structure
```
expert-finder-service/
├── main.py                 (1,286 lines) ⚠️ MONOLITHIC
├── domain/                 (empty) ⚠️
├── infrastructure/         (empty) ⚠️
├── README.md              (210 lines) ✅
├── requirements.txt        ✅
└── Dockerfile              ✅

❌ NO TESTS DIRECTORY
❌ NO TEST FILES
❌ NO CONFIG.md
❌ NO PHASE DOCUMENTS
```

---

## 🔍 Endpoint Inventory

### Current Endpoints (6)
1. **POST `/experts/find`** - Natural language expert search
2. **GET `/experts/by-topic/{topic}`** - Topic-based expert search
3. **GET `/experts/by-service/{service}`** - Service-based expert search
4. **GET `/experts/sme/{area}`** - Subject matter expert identification
5. **GET `/experts/teammates/{user_id}`** - Teammate discovery
6. **GET `/teams/{team_id}/expertise`** - Team expertise summary
7. **GET `/health`** - Health check

### Missing Standard Endpoints
- ❌ **GET `/about-me`** - Service descriptor
- ❌ **GET `/endpoints`** - Endpoint listing
- ❌ **GET `/provider-consumer`** - Service relationships
- ❌ **GET `/openapi.json`** - OpenAPI spec (FastAPI auto-generates this)
- ❌ **GET `/demos`** - Demo listing (NEW in v1.5.0)
- ❌ **POST `/run-demo`** - Demo execution (NEW in v1.5.0)

---

## 🏗️ Architecture Analysis

### Current Architecture: **MONOLITHIC**

**main.py contains everything**:
- FastAPI app initialization
- Pydantic models (7+ models)
- All 6 endpoint implementations
- Relevance scoring algorithm
- HTTP clients for external services
- Logging configuration
- CORS middleware

### Monolithic Issues
| Issue | Impact | Priority |
|-------|--------|----------|
| 1,286 lines in single file | Hard to navigate | High |
| No domain layer | Business logic mixed with API | High |
| No repository pattern | Direct HTTP calls in endpoints | Medium |
| No service layer | No abstraction | Medium |
| No value objects | Primitive obsession | Low |

---

## 🧪 Testing Analysis

### Current Test Coverage: **0%** ⚠️ CRITICAL

**Test Status**:
- ❌ No tests directory
- ❌ No unit tests
- ❌ No integration tests
- ❌ No test fixtures
- ❌ No test configuration

**Impact**:
- Cannot verify refactoring doesn't break functionality
- No safety net for changes
- Unknown code quality
- High risk of regressions

**Priority**: **CRITICAL** - Must create tests in Phase 3

---

## 📦 Dependencies

### External Service Dependencies
1. **user-store** (Primary, Required)
   - URL: `http://localhost:5150`
   - Purpose: User data source
   - Relationship: **Consumer** (queries user data)

2. **doc-store** (Optional)
   - URL: `http://localhost:5087`
   - Purpose: Document authorship verification
   - Relationship: **Consumer** (queries documents)

3. **external-service-store** (Optional)
   - URL: `http://localhost:5140`
   - Purpose: Service expertise validation
   - Relationship: **Consumer** (queries service data)

### Python Dependencies (from requirements.txt)
```python
fastapi>=0.104.1
uvicorn[standard]>=0.24.0
pydantic>=2.8.0
httpx>=0.25.2
# (need to verify full list)
```

---

## 🎯 Core Capabilities

### 1. Expert Search
**Relevance Scoring Algorithm** (Multi-factor):
- Role Matching (30% weight)
- Topic/Interest Matching (40% weight) - Strongest signal
- Service Subscriptions (20% weight)
- Document Relationships (10% weight)
- User Tags (bonus)
- Name Matching (bonus)

### 2. Query Types
- Natural language queries
- Topic-based search
- Service-based search
- SME identification (with document threshold)
- Teammate discovery
- Team expertise aggregation

### 3. Business Logic
- User relevance scoring (complex algorithm)
- Query parsing and matching
- Result ranking and filtering
- Metadata aggregation

---

## ⚠️ Gap Analysis

### Against DDD Standards

| Standard | Current | Gap | Priority |
|----------|---------|-----|----------|
| **Domain Layer** | ❌ Missing | No domain entities, value objects, or aggregates | High |
| **Application Layer** | ❌ Missing | No use cases or application services | High |
| **Infrastructure Layer** | ❌ Placeholder | No repositories or external service clients | High |
| **Presentation Layer** | ⚠️ Monolithic | All endpoints in main.py | High |
| **Separation of Concerns** | ❌ None | Business logic mixed with API | High |

### Against Testing Standards (Phase 5 NEW)

| Requirement | Current | Gap | Priority |
|-------------|---------|-----|----------|
| **Minimum 50% Coverage** | 0% | -50% | CRITICAL |
| **100% Happy-Path Coverage** | 0% | -100% | CRITICAL |
| **Edge Case Tests** | None | Missing | CRITICAL |
| **TESTING_GUIDE.md** | ❌ Missing | Not created | High |

### Against Documentation Standards

| Requirement | Current | Gap | Priority |
|-------------|---------|-----|----------|
| **CONFIG.md** | ❌ Missing | Not created | High |
| **Standard Endpoints** | 4/7 missing | `/about-me`, `/endpoints`, `/provider-consumer`, `/demos`, `/run-demo` | High |
| **Future Expansion Section** | ❌ Missing | Not in README | Medium |
| **Demo Endpoints** | ❌ Missing | NEW in v1.5.0 | Medium |

---

## 🔧 Configuration Analysis

### Current Configuration
- **Port**: 5160 (from environment or default)
- **Service URLs**: Environment variables
  - `USER_STORE_URL`: http://localhost:5150
  - `DOC_STORE_URL`: http://localhost:5087
  - `EXTERNAL_SERVICE_STORE_URL`: http://localhost:5140
  - `LLM_GATEWAY_URL`: http://localhost:8100 (future)

### Configuration Issues
- ❌ No CONFIG.md
- ❌ Configuration not centralized
- ⚠️ Hardcoded defaults in code
- ⚠️ No config validation

### Port Conflicts
- ✅ Port 5160 is unique (no conflicts found)

---

## 📈 Complexity Metrics

### File Complexity
| File | Lines | Complexity | Status |
|------|-------|------------|--------|
| **main.py** | 1,286 | Very High | ⚠️ **NEEDS REFACTORING** |

### Estimated Component Breakdown (from reading main.py)
- Models: ~150 lines (7+ Pydantic models)
- Endpoints: ~400 lines (6 endpoints + logic)
- Scoring Algorithm: ~200 lines
- HTTP Clients: ~100 lines
- Utilities: ~100 lines
- Configuration/Setup: ~100 lines
- Documentation: ~236 lines (docstrings)

**Target Structure** (after refactoring):
- Presentation Layer: ~300 lines (3-4 route modules)
- Domain Layer: ~400 lines (entities, value objects, services)
- Infrastructure Layer: ~200 lines (repositories, clients)
- Models: ~150 lines
- Tests: ~600 lines (50%+ coverage target)
- **Total**: ~1,650 lines (+28% for proper structure + tests)

---

## 🎯 Refactoring Scope

### High Priority (Must Do)
1. ✅ **Create Test Infrastructure** (Phase 3/5)
   - Create tests/ directory
   - Unit tests for scoring algorithm
   - Integration tests for endpoints
   - Test fixtures for sample data
   - Target: 50%+ coverage, 100% happy-path

2. ✅ **Extract Domain Layer** (Phase 3)
   - Expert entity
   - User value object
   - Relevance scoring service
   - Query value object

3. ✅ **Create Presentation Layer** (Phase 3)
   - expert_routes.py (expert search endpoints)
   - team_routes.py (team expertise endpoints)
   - standard_routes.py (health, about-me, endpoints, provider-consumer, demos)

4. ✅ **Add Standard Endpoints** (Phase 3/9)
   - GET `/about-me`
   - GET `/endpoints`
   - GET `/provider-consumer`
   - GET `/demos` (NEW)
   - POST `/run-demo` (NEW)

5. ✅ **Create Infrastructure Layer** (Phase 3)
   - UserStoreRepository
   - DocStoreRepository
   - ExternalServiceStoreRepository

6. ✅ **Documentation** (Phase 6/9)
   - CONFIG.md
   - TESTING_GUIDE.md (Phase 5 NEW)
   - Update README with Future Expansion
   - Phase completion documents

7. ✅ **Demo Implementation** (Phase 9 NEW)
   - 2-3 self-contained demos
   - 1-2 ecosystem demos
   - Demo data in demo_data/
   - Demo endpoints functional

### Medium Priority (Should Do)
- Configuration centralization
- Error handling improvements
- Logging standardization

### Low Priority (Nice to Have)
- LLM integration (future)
- Caching layer (future)
- GraphQL support (future)

---

## 📋 Proposed Structure (Post-Refactoring)

```
expert-finder-service/
├── main.py                          (reduced to ~150 lines)
├── domain/
│   ├── entities/
│   │   └── expert.py
│   ├── value_objects/
│   │   ├── query.py
│   │   └── relevance_score.py
│   └── services/
│       └── expert_finder_service.py (scoring algorithm)
├── infrastructure/
│   ├── repositories/
│   │   ├── user_store_repository.py
│   │   ├── doc_store_repository.py
│   │   └── external_service_repository.py
│   └── http_clients/
│       └── service_client.py
├── presentation/
│   ├── api/
│   │   └── models.py                (API models)
│   └── routes/
│       ├── expert_routes.py         (expert search endpoints)
│       ├── team_routes.py           (team expertise endpoints)
│       ├── standard_routes.py       (standard endpoints)
│       └── demo_routes.py           (NEW: demo endpoints)
├── tests/
│   ├── unit/
│   │   ├── test_scoring_algorithm.py
│   │   ├── test_expert_service.py
│   │   └── test_repositories.py
│   ├── integration/
│   │   ├── test_expert_endpoints.py
│   │   └── test_team_endpoints.py
│   └── fixtures/
│       └── sample_data.py
├── demo_data/                       (NEW: canned demo data)
│   ├── sample_users.json
│   ├── sample_query.json
│   └── expected_results.json
├── demo_artifacts/                  (NEW: generated demo artifacts)
├── CONFIG.md                        (NEW)
├── TESTING_GUIDE.md                 (NEW: Phase 5)
├── README.md                        (enhanced)
├── requirements.txt
└── Dockerfile
```

---

## 🚀 Phase 1 Deliverables

- [x] Service Audit Report (this document)
- [ ] Configuration Audit (port, credentials, profiles)
- [ ] Dependency Map (service interactions)
- [ ] Gap Analysis Document (vs DDD standards)
- [ ] Refactoring Scope Statement

---

## ⏱️ Estimated Timeline

| Phase | Duration | Priority |
|-------|----------|----------|
| Phase 1: Audit & Analysis | 2 hours | ✅ Current |
| Phase 2: Design & Planning | 2-3 hours | High |
| Phase 3: TDD Implementation | 6-8 hours | High |
| Phase 4: Integration Testing | 2 hours | High |
| Phase 5: Comprehensive Testing | 2-3 hours | MANDATORY (NEW) |
| Phase 6: Documentation | 2 hours | High |
| Phase 7: Deployment & Monitoring | 1 hour | High |
| Phase 8: Service Validation | 1 hour | MANDATORY |
| Phase 9: Future Expansion Planning | 2-4 hours | MANDATORY (NEW) |
| **Total** | **20-28 hours** | - |

---

## 🎯 Success Criteria

### Phase 1 Complete When:
- [x] Current state documented
- [ ] Dependencies mapped
- [ ] Gaps identified
- [ ] Refactoring scope defined
- [ ] Port conflicts checked
- [ ] Configuration documented

### Overall Refactoring Success Criteria:
- ✅ Monolithic main.py refactored into ~10 focused files
- ✅ Minimum 50% code coverage (Phase 5 NEW)
- ✅ 100% happy-path feature coverage (Phase 5 NEW)
- ✅ All standard endpoints implemented (including `/demos`, `/run-demo`)
- ✅ Zero breaking changes (backward compatible)
- ✅ All tests passing
- ✅ CONFIG.md and TESTING_GUIDE.md created
- ✅ 2-3 executable demos implemented (Phase 9 NEW)
- ✅ Service validated via Phase 8
- ✅ Future expansion documented (Phase 9 NEW)

---

## 🚨 Critical Issues

1. **❌ NO TESTS** (0% coverage)
   - **Priority**: CRITICAL
   - **Risk**: High chance of breaking changes during refactoring
   - **Mitigation**: Create comprehensive test suite in Phase 3/5

2. **⚠️ Monolithic Architecture** (1,286 lines)
   - **Priority**: High
   - **Impact**: Hard to maintain, test, and extend
   - **Mitigation**: Systematic refactoring in Phase 3

3. **❌ Missing Standard Endpoints**
   - **Priority**: High
   - **Impact**: Not ecosystem-compliant
   - **Mitigation**: Add in Phase 3

---

**Phase 1 Status**: IN PROGRESS  
**Next Step**: Complete dependency mapping and create Phase 2 design

*Document Version: 1.0*  
*Created: October 10, 2025*

