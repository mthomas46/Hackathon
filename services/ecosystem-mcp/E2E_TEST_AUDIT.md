# E2E Testing Audit & Plan

## Objective
Create comprehensive E2E tests that validate all major workflows and catch integration errors before deployment.

---

## 1. MAJOR CODEPATHS IDENTIFIED

### 1.1 Application Startup & Shutdown
- **Critical Path**: Lifespan management
- **Components**:
  - Database initialization
  - Redis initialization
  - ChromaDB initialization
  - Ollama client initialization
  - Ingestion worker startup/shutdown
  - Signal handlers
  - Graceful shutdown
- **Recent Errors**:
  - ❌ Missing `get_ingestion_worker` export
  - ❌ Worker not starting during lifespan
  - ❌ Missing `worker_id` attribute

### 1.2 Ingestion Pipeline
- **Critical Path**: Document ingestion from Git commits
- **Components**:
  - `IngestionWorker` (polling Redis streams)
  - `JobProcessor` (orchestrating pipeline)
  - `GitService` (fetching commits/files)
  - `NormalizerFactory` + normalizers (processing documents)
  - `EmbeddingService` (generating embeddings)
  - `DocumentRepository` + `EmbeddingRepository` (storage)
  - Redis streams (job queue)
- **Recent Errors**:
  - ❌ `BaseRepository.create()` parameter mismatch
  - ❌ Wrong parameter order in `super().__init__()`
  - ❌ Missing `read_stream` → should be `read_from_stream`
  - ❌ Missing `consumer_name` parameter
  - ❌ Missing `worker_id` attribute

### 1.3 Search & Query
- **Critical Path**: Semantic search across documents
- **Components**:
  - Search endpoint (`/api/v1/search`)
  - Ollama embedding generation
  - ChromaDB vector search
  - Result ranking and filtering
  - Caching layer
- **Recent Errors**:
  - ❌ Missing `cache` import in `ollama_client.py`
  - ❌ Cache decorator not properly imported

### 1.4 Admin & Monitoring
- **Critical Path**: Service management and observability
- **Components**:
  - Admin endpoints (`/api/v1/admin/*`)
  - Health checks
  - Metrics (Prometheus)
  - Queue status
  - Circuit breakers
  - Cache statistics
- **Recent Errors**: None (but untested)

### 1.5 Repository Pattern
- **Critical Path**: Database operations
- **Components**:
  - `BaseRepository` (generic CRUD)
  - `DocumentRepository`
  - `EmbeddingRepository`
  - `IngestionJobRepository`
- **Recent Errors**:
  - ❌ Parameter order mismatch
  - ❌ `create()` expects entity, not kwargs

---

## 2. E2E TEST REQUIREMENTS

### Test 1: Full Application Lifecycle
**Purpose**: Catch startup/shutdown integration errors
- ✅ Application starts successfully
- ✅ All components initialize
- ✅ Worker starts and runs
- ✅ Graceful shutdown works
- ✅ No orphaned processes/connections

### Test 2: Complete Ingestion Workflow
**Purpose**: Validate end-to-end document ingestion
- ✅ Create ingestion job via API
- ✅ Worker picks up job from Redis
- ✅ Fetches files from Git
- ✅ Normalizes documents (MD, PY, YAML, JSON)
- ✅ Generates embeddings
- ✅ Stores in database + ChromaDB
- ✅ Job status updates correctly
- ✅ Stats reflect new documents

### Test 3: Search Workflow
**Purpose**: Validate search pipeline
- ✅ Ingest documents
- ✅ Search by keyword
- ✅ Search by service filter
- ✅ Results are relevant
- ✅ Caching works
- ✅ Rate limiting works

### Test 4: Repository Operations
**Purpose**: Catch database integration errors
- ✅ Create entities
- ✅ Read entities
- ✅ Update entities
- ✅ Bulk operations
- ✅ Transactions
- ✅ Query filtering

### Test 5: Redis Streams
**Purpose**: Validate queue operations
- ✅ Add jobs to stream
- ✅ Read from stream with consumer group
- ✅ Acknowledge messages
- ✅ Handle stream errors
- ✅ Dead letter queue

### Test 6: Circuit Breakers & Resilience
**Purpose**: Validate failure handling
- ✅ Circuit breaker opens on failures
- ✅ Circuit breaker recovers
- ✅ Graceful degradation
- ✅ Retry logic

### Test 7: Import Validation
**Purpose**: Catch import/export errors at test time
- ✅ All `__init__.py` exports are valid
- ✅ All imports resolve
- ✅ No circular dependencies
- ✅ All singletons work

---

## 3. TEST INFRASTRUCTURE

### 3.1 Test Fixtures
- Clean database (reset between tests)
- Clean Redis (flush streams)
- Clean ChromaDB (empty collection)
- Test Git repository
- Mock Ollama (optional)

### 3.2 Test Utilities
- Service starter/stopper
- Data generators (test documents, commits)
- Assertion helpers
- Async test support

### 3.3 Test Coverage Goals
- **Critical paths**: 100%
- **Happy paths**: 100%
- **Error paths**: 80%
- **Edge cases**: 60%

---

## 4. IMPLEMENTATION PLAN

### Phase 1: Infrastructure (1h)
- Set up pytest fixtures
- Create test helpers
- Create test data generators

### Phase 2: Core Tests (2h)
- Test 1: Application lifecycle
- Test 2: Ingestion workflow
- Test 7: Import validation

### Phase 3: Feature Tests (1.5h)
- Test 3: Search workflow
- Test 4: Repository operations
- Test 5: Redis streams

### Phase 4: Resilience Tests (1h)
- Test 6: Circuit breakers
- Error handling tests
- Recovery tests

### Phase 5: Integration (0.5h)
- Run full test suite
- Fix discovered issues
- Document coverage

**Total Estimated Time**: 6 hours

---

## 5. ERRORS THAT WOULD HAVE BEEN CAUGHT

### Import/Export Errors
- ❌ Missing `cache` import → **Test 7** would catch
- ❌ Missing `get_ingestion_worker` export → **Test 1** would catch
- ❌ Missing circuit breaker imports → **Test 7** would catch

### Integration Errors
- ❌ Worker not starting → **Test 1** would catch
- ❌ Wrong Redis method name → **Test 2** would catch
- ❌ Missing parameters → **Test 2** would catch
- ❌ Repository parameter mismatch → **Test 4** would catch

### Runtime Errors
- ❌ Missing `worker_id` attribute → **Test 2** would catch
- ❌ Database schema mismatch → **Test 4** would catch

---

## 6. SUCCESS CRITERIA

✅ All 7 test suites pass
✅ No import errors
✅ No integration errors
✅ Service starts/stops cleanly
✅ Full ingestion workflow works
✅ Search works end-to-end
✅ All repositories work correctly
✅ Redis streams work correctly
✅ Circuit breakers work correctly

---

## 7. CONTINUOUS INTEGRATION

### Pre-commit Hook
- Run import validation
- Run quick tests (<30s)

### CI Pipeline
- Run full E2E suite
- Generate coverage report
- Block on failures

### Deployment Validation
- Run E2E tests against staging
- Validate all endpoints
- Check metrics/logs

