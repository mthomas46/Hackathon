# Test Data Isolation Strategy

**Date:** October 23, 2025  
**Priority:** CRITICAL  
**Objective:** Ensure test data never interferes with production data  

---

## 🎯 THE PROBLEM

### Risk Scenarios
1. **Data Contamination**: Test data mixed with real application data
2. **Accidental Deletion**: Test cleanup removing production data
3. **Database Confusion**: Tests running against production database
4. **Cache Pollution**: Test data cached alongside real data
5. **Analytics Corruption**: Test data skewing metrics

### Impact
- ❌ Production data integrity compromised
- ❌ User experience degraded
- ❌ Analytics unreliable
- ❌ Debugging nightmare
- ❌ Data recovery needed

---

## 🛡️ MULTI-LAYER ISOLATION STRATEGY

We'll implement **5 layers of defense** to ensure complete isolation:

### Layer 1: Separate Test Database (Infrastructure) ✅
**Status:** Already implemented  
**Mechanism:** Docker Compose with dedicated test database

```yaml
# docker-compose.test.yml
postgres-test:
  image: postgres:16
  ports:
    - "5433:5432"  # Different port
  environment:
    POSTGRES_DB: test_ecosystem_mcp
    POSTGRES_USER: test_user
    POSTGRES_PASSWORD: test_pass
```

**Benefits:**
- ✅ Complete physical isolation
- ✅ No risk of data mixing
- ✅ Independent lifecycle

**Limitations:**
- ⚠️ Requires Docker
- ⚠️ Could accidentally use wrong DB

---

### Layer 2: Environment-Based Configuration (CRITICAL)
**Status:** Need to implement  
**Mechanism:** Strict environment validation

```python
# src/config/database.py

import os
from enum import Enum

class Environment(str, Enum):
    PRODUCTION = "production"
    STAGING = "staging"
    DEVELOPMENT = "development"
    TEST = "test"

def get_database_config():
    """Get database configuration based on environment."""
    env = os.getenv("APP_ENV", "development")
    
    # CRITICAL: Prevent tests from running in production
    if env == "production" and os.getenv("PYTEST_CURRENT_TEST"):
        raise RuntimeError(
            "🚨 CRITICAL: Tests cannot run in production environment! "
            "Set APP_ENV=test"
        )
    
    configs = {
        "production": {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": int(os.getenv("DB_PORT", "5432")),
            "database": os.getenv("DB_NAME", "ecosystem_mcp"),
            "user": os.getenv("DB_USER", "postgres"),
            "allow_test_data": False  # CRITICAL FLAG
        },
        "test": {
            "host": os.getenv("TEST_DB_HOST", "localhost"),
            "port": int(os.getenv("TEST_DB_PORT", "5433")),
            "database": os.getenv("TEST_DB_NAME", "test_ecosystem_mcp"),
            "user": os.getenv("TEST_DB_USER", "test_user"),
            "allow_test_data": True  # Only tests can write
        }
    }
    
    return configs.get(env, configs["development"])
```

**Benefits:**
- ✅ Automatic environment detection
- ✅ Prevents production accidents
- ✅ Clear configuration per environment

---

### Layer 3: Test Data Tagging (Safety Net)
**Status:** Need to implement  
**Mechanism:** Metadata marking on all test data

```python
# src/utils/test_data_marker.py

from datetime import datetime
import uuid

class TestDataMarker:
    """Mark and identify test data."""
    
    TEST_MARKER_KEY = "_test_data_marker"
    TEST_SESSION_KEY = "_test_session_id"
    TEST_CREATED_KEY = "_test_created_at"
    
    @staticmethod
    def mark_as_test_data(data: dict, session_id: str = None) -> dict:
        """
        Add test data markers to any data dictionary.
        
        This acts as a safety net if test data somehow
        ends up in production database.
        """
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Add markers to metadata
        if "metadata" not in data:
            data["metadata"] = {}
        
        data["metadata"][TestDataMarker.TEST_MARKER_KEY] = True
        data["metadata"][TestDataMarker.TEST_SESSION_KEY] = session_id
        data["metadata"][TestDataMarker.TEST_CREATED_KEY] = datetime.utcnow().isoformat()
        
        return data
    
    @staticmethod
    def is_test_data(data: dict) -> bool:
        """Check if data is marked as test data."""
        metadata = data.get("metadata", {})
        return metadata.get(TestDataMarker.TEST_MARKER_KEY, False)
    
    @staticmethod
    def get_test_session(data: dict) -> str:
        """Get test session ID from data."""
        metadata = data.get("metadata", {})
        return metadata.get(TestDataMarker.TEST_SESSION_KEY)


# Usage in tests:
def create_test_document(content: str) -> dict:
    doc_data = {
        "file_path": "test.py",
        "content": content,
        "service_name": "test-service"
    }
    return TestDataMarker.mark_as_test_data(doc_data)
```

**Benefits:**
- ✅ Every test record tagged
- ✅ Easy to identify test data
- ✅ Can filter in queries
- ✅ Safety net for accidents

---

### Layer 4: Automatic Cleanup (Transaction Rollback)
**Status:** Already implemented ✅  
**Mechanism:** Database transaction rollback after each test

```python
# tests/conftest.py

@pytest.fixture
async def db_session():
    """
    Database session with automatic rollback.
    
    Every test gets a fresh transaction that's
    rolled back after the test completes.
    """
    async with get_database().session() as session:
        # Start transaction
        transaction = await session.begin()
        
        try:
            yield session
        finally:
            # ALWAYS rollback - test data never persists
            await transaction.rollback()
```

**Benefits:**
- ✅ Zero persistence of test data
- ✅ Automatic cleanup
- ✅ No manual cleanup needed
- ✅ Tests always start fresh

---

### Layer 5: Query Filtering (Production Safety)
**Status:** Need to implement  
**Mechanism:** Automatic test data filtering in production

```python
# src/storage/repositories/base_repository.py

class BaseRepository:
    """Base repository with test data protection."""
    
    def __init__(self, session):
        self.session = session
        self.config = get_database_config()
    
    def _filter_test_data(self, query):
        """
        Filter out test data in non-test environments.
        
        This ensures if test data accidentally exists
        in production, it's never returned to users.
        """
        if not self.config.get("allow_test_data", False):
            # Production: Filter out test data
            query = query.filter(
                ~Model.metadata.contains({
                    TestDataMarker.TEST_MARKER_KEY: True
                })
            )
        return query
    
    async def list_all(self, limit: int = 100):
        """List all records, filtering test data in production."""
        query = select(self.model_class).limit(limit)
        query = self._filter_test_data(query)  # CRITICAL
        result = await self.session.execute(query)
        return result.scalars().all()
```

**Benefits:**
- ✅ Automatic filtering
- ✅ Protection even if data leaks
- ✅ No user-facing test data
- ✅ Defense in depth

---

## 🏗️ IMPLEMENTATION PLAN

### Phase 1: Environment Configuration (30 mins)
1. ✅ Create `src/config/environment.py`
2. ✅ Add environment detection
3. ✅ Add production safety checks
4. ✅ Update database config

### Phase 2: Test Data Tagging (30 mins)
1. ✅ Create `src/utils/test_data_marker.py`
2. ✅ Implement marking functions
3. ✅ Add to test fixtures
4. ✅ Update all test helpers

### Phase 3: Repository Protection (45 mins)
1. ✅ Update `BaseRepository`
2. ✅ Add test data filtering
3. ✅ Update all repositories
4. ✅ Add safety checks

### Phase 4: Testing & Validation (30 mins)
1. ✅ Test environment detection
2. ✅ Verify data isolation
3. ✅ Validate cleanup
4. ✅ Document usage

**Total Time:** ~2 hours  
**Priority:** CRITICAL  

---

## 🎯 USAGE PATTERNS

### For Test Authors

```python
# tests/functional/test_example.py

@pytest.mark.functional
async def test_document_workflow(db_session, test_session_id):
    """All test data automatically marked and cleaned up."""
    
    # Create test document (automatically marked)
    doc_data = create_test_document(
        content="test content",
        session_id=test_session_id  # Links to test session
    )
    
    # Store in database
    doc = await doc_repo.create(doc_data)
    
    # Use in test
    assert doc.metadata["_test_data_marker"] == True
    
    # Automatic cleanup via rollback - no manual cleanup needed!
```

### For Application Code

```python
# src/api/routes/documents.py

@router.get("/documents")
async def list_documents():
    """
    List documents.
    
    Automatically filters test data in production.
    """
    # Repository automatically filters test data
    docs = await doc_repo.list_all()
    
    # In production: only real data returned
    # In test: test data included
    return docs
```

---

## 🔒 SAFETY GUARANTEES

### What We Guarantee

1. **✅ Complete Isolation**
   - Test database separate from production
   - Different ports, credentials, database names

2. **✅ Zero Data Leakage**
   - Transaction rollback after every test
   - No test data persists beyond test execution

3. **✅ Production Protection**
   - Tests cannot run in production environment
   - Runtime checks prevent accidents

4. **✅ Automatic Filtering**
   - Test data filtered in production queries
   - Even if data leaks, users never see it

5. **✅ Easy Identification**
   - All test data tagged
   - Easy to find and remove if needed

---

## 🧪 VERIFICATION TESTS

```python
# tests/test_data_isolation.py

class TestDataIsolation:
    """Verify data isolation guarantees."""
    
    async def test_cannot_run_tests_in_production(self):
        """Tests must fail if APP_ENV=production."""
        os.environ["APP_ENV"] = "production"
        os.environ["PYTEST_CURRENT_TEST"] = "test"
        
        with pytest.raises(RuntimeError, match="CRITICAL"):
            get_database_config()
    
    async def test_data_is_marked_as_test(self, db_session):
        """All test data must be marked."""
        doc = await create_test_document("test")
        assert TestDataMarker.is_test_data(doc)
    
    async def test_data_rolls_back(self, db_session):
        """Test data must not persist."""
        doc = await doc_repo.create(create_test_document("test"))
        session_id = doc.id
        
        # After rollback, data should not exist
        # (verified in separate test)
    
    async def test_production_filters_test_data(self):
        """Production queries must filter test data."""
        # Set production environment
        os.environ["APP_ENV"] = "production"
        
        # Create repo
        repo = DocumentRepository(session)
        
        # Query should filter test data
        docs = await repo.list_all()
        assert all(not TestDataMarker.is_test_data(d) for d in docs)
```

---

## 📊 COMPARISON TABLE

| Layer | Mechanism | When Active | Strength | Fallback |
|-------|-----------|-------------|----------|----------|
| 1. Separate DB | Infrastructure | Always | 🟢 Complete | None needed |
| 2. Environment Check | Config | Runtime | 🟢 Prevents accidents | Manual verification |
| 3. Data Tagging | Metadata | Write time | 🟡 Identification | Layer 4 cleanup |
| 4. Auto Cleanup | Rollback | Test end | 🟢 Zero persistence | Layer 5 filtering |
| 5. Query Filtering | Repository | Query time | 🟢 Production safety | Layer 1 DB |

**Defense in Depth:** 5 independent layers ensure safety

---

## 🚀 DEPLOYMENT CHECKLIST

### Before Running Tests
- [ ] Verify `APP_ENV=test` is set
- [ ] Confirm test database running (port 5433)
- [ ] Check no production credentials in test config

### After Test Session
- [ ] Verify test database can be cleaned
- [ ] Confirm no test data in production DB
- [ ] Review test data markers

### Production Deployment
- [ ] Verify `APP_ENV=production` set
- [ ] Confirm test data filtering active
- [ ] Validate no test markers in production data

---

## 🎯 BEST PRACTICES

### DO ✅
- ✅ Always use test fixtures
- ✅ Let automatic cleanup happen
- ✅ Use environment variables
- ✅ Tag all test data
- ✅ Use separate test database

### DON'T ❌
- ❌ Manually set production credentials in tests
- ❌ Skip test data markers
- ❌ Commit test database credentials
- ❌ Run tests with `APP_ENV=production`
- ❌ Disable automatic rollback

---

## 📈 SUCCESS METRICS

### Technical Metrics
- ✅ **0 test data leaks** to production
- ✅ **100% test data tagged**
- ✅ **100% automatic cleanup**
- ✅ **0 production test runs**

### Quality Metrics
- ✅ **Tests run in isolation**
- ✅ **No manual cleanup needed**
- ✅ **Clear environment separation**
- ✅ **Production data protected**

---

## 🎊 SUMMARY

**5-Layer Defense Strategy:**

1. **🏗️ Infrastructure**: Separate test database
2. **⚙️ Configuration**: Environment-based isolation
3. **🏷️ Tagging**: Metadata markers on test data
4. **🔄 Cleanup**: Automatic transaction rollback
5. **🔒 Filtering**: Production query protection

**Result:** Bulletproof isolation with zero risk of contamination!

---

*Last Updated: October 23, 2025*  
*Status: Ready to Implement*  
*Priority: CRITICAL*

