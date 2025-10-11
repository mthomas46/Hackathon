# Integration Checklist - Ecosystem MCP Hardening

**Status**: 🟡 **INTEGRATION REQUIRED**  
**Code Complete**: ✅ 100%  
**Integration Complete**: ⚠️ 40%  
**Production Ready**: ❌ NO (70%, need 95%)

---

## 📋 **Integration Tasks**

### 🔴 **High Priority - Must Complete Before Deployment**

#### 1. **Integrate Structured Logging** ⏳
**File**: `src/api/app.py`  
**Estimate**: 30 minutes  
**Status**: ❌ NOT DONE

**Changes Required**:
```python
# At top of app.py
from ..utils.logging_config import configure_structured_logging

# In lifespan function, BEFORE other initializations
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    
    # Configure structured logging FIRST
    json_logs = settings.environment != "development"
    configure_structured_logging(
        log_level=settings.log_level,
        json_logs=json_logs,
        include_timestamp=True
    )
    logger.info("✅ Structured logging configured")
    
    # ... rest of startup
```

**Verification**:
- [ ] Service starts successfully
- [ ] Logs show JSON format in production mode
- [ ] Logs show console format in development mode
- [ ] Test: `LOG_LEVEL=INFO python -m src.api.app`

---

#### 2. **Add Request ID Middleware** ⏳
**File**: `src/api/app.py`  
**Estimate**: 15 minutes  
**Status**: ❌ NOT DONE

**Changes Required**:
```python
# At top of app.py
from .middleware import RequestIDMiddleware

# After app creation, before routes
app = FastAPI(
    title="Ecosystem MCP",
    # ... config
)

# Add middleware
app.add_middleware(RequestIDMiddleware)

# ... rest of app setup
```

**Verification**:
- [ ] Service starts successfully
- [ ] GET /health returns X-Request-ID header
- [ ] Test: `curl -I http://localhost:8000/health | grep X-Request-ID`
- [ ] Test with existing ID: `curl -H "X-Request-ID: test-123" http://localhost:8000/health`

---

#### 3. **Integrate Environment Validation** ⏳
**File**: `src/config.py` OR `src/utils/preflight.py`  
**Estimate**: 15 minutes  
**Status**: ❌ NOT DONE

**Option A: In config.py (recommended)**:
```python
# In Settings class __init__ or validator
from .utils.environment import validate_environment, get_environment_config

class Settings(BaseSettings):
    environment: str = Field(default="development")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Validate environment on initialization
        validate_environment(self.environment)
```

**Option B: In preflight checks**:
```python
# In PreflightChecker class
from ..utils.environment import validate_environment

async def check_environment(self) -> CheckResult:
    """Check environment is valid."""
    try:
        validate_environment(settings.environment)
        return CheckResult(
            name="Environment",
            passed=True,
            message=f"Valid environment: {settings.environment}",
            category=CheckCategory.HIGH
        )
    except ValueError as e:
        return CheckResult(
            name="Environment",
            passed=False,
            message=str(e),
            category=CheckCategory.HIGH
        )
```

**Verification**:
- [ ] Service starts with valid environment (dev/staging/prod/test)
- [ ] Service fails with invalid environment
- [ ] Test: `ENVIRONMENT=invalid python -m src.api.app` → should fail
- [ ] Test: `ENVIRONMENT=production python -m src.api.app` → should work

---

#### 4. **Configure Log Rotation** ⏳
**File**: `src/utils/logging_config.py` OR `src/api/app.py`  
**Estimate**: 20 minutes  
**Status**: ❌ NOT DONE

**Changes Required**:
```python
# Option A: In logging_config.py configure_structured_logging()
from .log_rotation import setup_log_rotation
from pathlib import Path

def configure_structured_logging(
    log_level: str = "INFO",
    json_logs: bool = True,
    include_timestamp: bool = True,
    log_file: str | None = None,  # NEW
):
    # ... existing config
    
    # Add file handler with rotation if log_file specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = setup_log_rotation(
            log_file=log_path,
            max_bytes=10 * 1024 * 1024,  # 10MB
            backup_count=5,
            log_level=log_level
        )
        
        # Add to root logger
        logging.getLogger().addHandler(file_handler)

# In app.py lifespan:
configure_structured_logging(
    log_level=settings.log_level,
    json_logs=json_logs,
    include_timestamp=True,
    log_file="logs/mcp.log"  # NEW
)
```

**Verification**:
- [ ] Service starts successfully
- [ ] `logs/` directory is created
- [ ] `logs/mcp.log` file is created
- [ ] Log file rotates at 10MB
- [ ] Test: Run service, check `ls -lh logs/`

---

#### 5. **Use Custom Exception Hierarchy** ⏳
**Files**: Multiple (`src/storage/*.py`, `src/api/routes/*.py`)  
**Estimate**: 1 hour  
**Status**: ❌ NOT DONE

**Changes Required** (examples):
```python
# In src/storage/__init__.py
from ..utils.exceptions import DatabaseError

async def init_database():
    try:
        # ... create tables
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise DatabaseError(f"Failed to initialize database: {e}") from e

# In src/utils/preflight.py
from .exceptions import ConfigurationError, ValidationError

def check_config(self) -> CheckResult:
    if not config_valid:
        raise ConfigurationError("Invalid configuration")

# In deployment_manager.py
from src.utils.exceptions import ServiceStartError, ServiceStopError

def start_service(self):
    try:
        # ... start logic
    except Exception as e:
        raise ServiceStartError(f"Failed to start service: {e}") from e
```

**Files to Update**:
- [ ] `src/storage/__init__.py` → DatabaseError
- [ ] `src/storage/database.py` → DatabaseError
- [ ] `src/utils/preflight.py` → ConfigurationError, ValidationError
- [ ] `deployment_manager.py` → ServiceStartError, ServiceStopError
- [ ] `src/api/routes/health.py` → HealthCheckError

**Verification**:
- [ ] All exception usages replaced
- [ ] Service still works (no breaking changes)
- [ ] Errors are more specific and helpful

---

### 🟡 **Medium Priority - Verify & Test**

#### 6. **Verify PID Locking Integration** ⏳
**File**: `deployment_manager.py`  
**Estimate**: 30 minutes  
**Status**: ⚠️ PARTIAL (needs verification)

**Verification Needed**:
```bash
# Check if acquire_lock is called in start_service
grep -A 10 "def start_service" deployment_manager.py | grep "acquire_lock"

# Check if write_pid is used instead of write_text
grep "write_pid" deployment_manager.py

# Check if release_lock is called in stop_service
grep -A 10 "def stop_service" deployment_manager.py | grep "release_lock"
```

**Manual Test**:
- [ ] Start service: `make deploy`
- [ ] Try to start again (should fail with lock error): `make deploy`
- [ ] Stop service: `make teardown`
- [ ] Verify PID file is removed
- [ ] Start service again (should work)

**If Missing**: Add integration points per HONEST_EVALUATION.md

---

#### 7. **Verify Retry Logic in Service** ⏳
**Files**: `src/storage/*.py`, `src/api/routes/*.py`  
**Estimate**: 1 hour  
**Status**: ⚠️ PARTIAL (deployment_manager only)

**Changes Recommended**:
```python
# In src/storage/database.py
from ..utils.retry import retry_database_operation

@retry_database_operation
async def execute_query(self, query: str):
    """Execute query with retry logic."""
    # ... implementation

# In src/api/routes/ollama.py
from ...utils.retry import retry_external_call

@retry_external_call
async def call_ollama(self, endpoint: str):
    """Call Ollama with retry logic."""
    # ... implementation
```

**Verification**:
- [ ] Database operations retry on connection errors
- [ ] External API calls retry on network errors
- [ ] Logs show retry attempts
- [ ] Test: Temporarily stop database, verify retry + recovery

---

### 🟢 **Low Priority - Nice to Have**

#### 8. **Add Integration Tests** ⏳
**File**: `tests/integration/test_hardening.py` (new)  
**Estimate**: 2 hours  
**Status**: ❌ NOT DONE

**Tests Needed**:
```python
# tests/integration/test_hardening.py

def test_structured_logging_json_format():
    """Test logs are JSON in production mode."""
    # ... implementation

def test_request_id_propagation():
    """Test X-Request-ID header is added."""
    response = client.get("/health")
    assert "X-Request-ID" in response.headers

def test_environment_validation_rejects_invalid():
    """Test service rejects invalid environments."""
    # ... implementation

def test_health_check_shows_degraded():
    """Test health check shows DEGRADED when ChromaDB down."""
    # ... implementation

def test_pid_locking_prevents_double_start():
    """Test PID locking prevents simultaneous starts."""
    # ... implementation

def test_retry_logic_on_transient_failure():
    """Test retry logic recovers from transient failures."""
    # ... implementation
```

**Coverage Target**: 80% for hardening features

---

## 🎯 **Integration Phases**

### **Phase 1: Critical Integration** (2 hours)
1. ✅ Structured logging (30m)
2. ✅ Request ID middleware (15m)
3. ✅ Environment validation (15m)
4. ✅ Log rotation (20m)
5. ✅ Verify PID locking (30m)

**Goal**: All utilities integrated and callable

---

### **Phase 2: Validation** (1 hour)
1. Deploy service with all changes
2. Manual test each feature:
   - JSON logs in production
   - X-Request-ID headers
   - Environment validation errors
   - Log file rotation
   - PID locking prevents double-start
3. Fix any issues discovered
4. Re-deploy and re-test

**Goal**: All features working in deployed service

---

### **Phase 3: Testing** (2 hours)
1. Write integration tests for each feature
2. Run full test suite
3. Measure code coverage
4. Fix failing tests
5. Document test results

**Goal**: 80% test coverage for hardening features

---

## 📊 **Success Criteria**

### **Before Deployment**
- [ ] All 5 critical integrations complete
- [ ] Service deploys successfully
- [ ] All features verified manually
- [ ] No regressions in existing functionality

### **Production Ready**
- [ ] Integration tests pass
- [ ] Code coverage ≥ 70%
- [ ] Health check shows accurate status
- [ ] Structured logs working
- [ ] Request tracing functional
- [ ] PID locking prevents races

### **Metrics**
- **Current**: 70% production ready
- **Target**: 95% production ready
- **Gap**: 25% (requires integration + testing)

---

## 🚀 **Quick Start**

```bash
# 1. Review this checklist
cat INTEGRATION_CHECKLIST.md

# 2. Start with critical integrations (Phase 1)
#    Work through items 1-5 above

# 3. Deploy and validate (Phase 2)
make teardown
make deploy
make status
make logs

# 4. Test each feature manually
curl -I http://localhost:8000/health  # Check X-Request-ID
cat logs/mcp.log  # Check structured logs
ENVIRONMENT=invalid make deploy  # Should fail

# 5. Write integration tests (Phase 3)
#    See tests/integration/test_hardening.py

# 6. Run full test suite
make test

# 7. Update HARDENING_PROGRESS.md with actual results
```

---

**Status**: 🔴 **INTEGRATION REQUIRED**  
**Estimated Time**: 5 hours total  
**Blocking Deployment**: YES

**Once complete**: Update to 95% production ready ✅

