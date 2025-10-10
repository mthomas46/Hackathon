# Phase 2.7: Library Recommendations - expert-finder-service

**Date**: October 10, 2025  
**Duration**: 15 minutes  
**Status**: Complete

---

## 🎯 Recommendations Summary

| Priority | Libraries | Phase | Impact |
|----------|-----------|-------|--------|
| **HIGH** | httpx, tenacity, pydantic-settings | Phase 3 | ~80 lines eliminated |
| **MEDIUM** | structlog, faker, factory-boy | Phase 8 | Better observability + testing |
| **LOW** | cachetools | Phase 11 | Optional caching upgrade |
| **KEEP CUSTOM** | Relevance Scoring | N/A | Domain-specific |

---

## 🔥 High Priority (Implement in Phase 3)

### 1. Replace `requests` with `httpx`

**Current State**:
```python
import requests

def get_users():
    response = requests.get(f"{USER_STORE_URL}/users")
    return response.json()
```

**Issues**:
- Synchronous (blocking)
- No connection pooling
- No async support
- No HTTP/2

**Recommended Library**: **httpx** (v0.25+)

**Benefits**:
- ✅ Async/await support
- ✅ Connection pooling built-in
- ✅ HTTP/2 support
- ✅ Better timeout handling
- ✅ API compatible with `requests`
- ✅ Widely used across ecosystem

**Effort**: **LOW** (30 minutes - API is almost identical)

**Decision**: ✅ **Implement in Phase 3**

**After (with httpx)**:
```python
import httpx

# Create client with connection pooling
client = httpx.AsyncClient(
    timeout=30.0,
    limits=httpx.Limits(
        max_keepalive_connections=20,
        max_connections=100
    )
)

async def get_users():
    response = await client.get(f"{settings.user_store_url}/users")
    response.raise_for_status()
    return response.json()
```

**Lines Saved**: ~20 lines (no manual connection management)

---

### 2. Replace manual retry with `tenacity`

**Current State**:
```python
def retry_call(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)  # Simple exponential backoff
```

**Issues**:
- Custom implementation (~15 lines)
- Not configurable
- No jitter (thundering herd problem)
- Not battle-tested
- Difficult to customize per use case

**Recommended Library**: **tenacity** (v8.2+)

**Benefits**:
- ✅ Configurable retry strategies
- ✅ Exponential backoff with jitter
- ✅ Stop conditions (max attempts, max time)
- ✅ Wait strategies (fixed, exponential, random)
- ✅ Exception filtering
- ✅ Battle-tested by thousands of projects

**Effort**: **LOW** (30 minutes - drop-in replacement)

**Decision**: ✅ **Implement in Phase 3**

**After (with tenacity)**:
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10)
)
async def get_users():
    response = await client.get(f"{settings.user_store_url}/users")
    response.raise_for_status()
    return response.json()
```

**Lines Saved**: ~15 lines (custom retry function eliminated)

---

### 3. Replace manual env loading with `pydantic-settings`

**Current State**:
```python
import os

USER_STORE_URL = os.getenv("USER_STORE_URL", "http://localhost:5110")
DOC_STORE_URL = os.getenv("DOC_STORE_URL", "http://localhost:5100")
SERVICE_PORT = int(os.getenv("SERVICE_PORT", "5160"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
# ... scattered throughout code
```

**Issues**:
- No type safety
- No validation
- Scattered throughout code
- Manual type conversion
- No .env file support
- Default values not documented

**Recommended Library**: **pydantic-settings** (v2.1+)

**Benefits**:
- ✅ Type-safe configuration
- ✅ Automatic validation
- ✅ .env file support
- ✅ Centralized configuration
- ✅ Type conversion automatic
- ✅ IDE autocomplete support
- ✅ FastAPI integration

**Effort**: **LOW** (30 minutes - centralize all config)

**Decision**: ✅ **Implement in Phase 3**

**After (with pydantic-settings)**:
```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Service config
    service_name: str = "expert-finder-service"
    service_port: int = 5160
    environment: str = "development"
    
    # Dependencies (required)
    user_store_url: str  # Will raise error if not set
    
    # Dependencies (optional)
    doc_store_url: str | None = None
    external_service_store_url: str | None = None
    log_collector_url: str | None = None
    
    # HTTP client config
    http_timeout_seconds: int = 30
    http_pool_size: int = 10
    
    # Scoring weights (validated)
    scoring_role_weight: float = 0.30
    scoring_topic_weight: float = 0.40
    scoring_service_weight: float = 0.20
    scoring_document_weight: float = 0.10
    
    # Logging
    log_level: str = "INFO"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    def __post_init__(self):
        # Validate weights sum to 1.0
        total = (self.scoring_role_weight + self.scoring_topic_weight + 
                 self.scoring_service_weight + self.scoring_document_weight)
        if not (0.99 <= total <= 1.01):
            raise ValueError(f"Scoring weights must sum to 1.0, got {total}")

settings = Settings()
```

**Lines Saved**: ~30 lines (scattered env loading eliminated)

---

## ⚠️ Medium Priority (Implement in Phase 8)

### 4. Add `structlog` for structured logging

**Current State**:
```python
print(f"Searching for experts with topics: {topics}")
print(f"Found {len(results)} experts in {duration}ms")
print(f"Error fetching users: {error}")
```

**Issues**:
- Not structured (difficult to parse)
- No correlation IDs
- No log levels
- No log collector integration
- Difficult to search/filter

**Recommended Library**: **structlog** (v23.2+)

**Benefits**:
- ✅ Structured JSON logging
- ✅ Context preservation (correlation IDs)
- ✅ Fast performance
- ✅ Easy integration with log aggregators
- ✅ Better debugging (searchable logs)

**Effort**: **MEDIUM** (1-2 hours to add throughout codebase)

**Decision**: ⚠️ **Implement in Phase 8 (Optimization)**

**Rationale**: Not blocking for Phase 3 implementation, but important for production observability

**After (with structlog)**:
```python
import structlog

logger = structlog.get_logger()

logger.info(
    "expert_search_started",
    user_id="user-123",
    query_topics=["python", "fastapi"],
    query_services=["code-analyzer"]
)

logger.info(
    "expert_search_completed",
    results_found=5,
    duration_ms=45.2,
    top_expert="user-456"
)

logger.error(
    "user_fetch_failed",
    error=str(error),
    user_store_url=settings.user_store_url,
    retry_attempt=attempt
)
```

**Value**: Significant improvement in observability and debugging

---

### 5. Add `faker` for test data generation

**Current State**:
```python
def test_expert_search():
    # Hardcoded test data
    test_expert = {
        "user_id": "user-123",
        "name": "Test User",
        "email": "test@example.com",
        "role": "senior_developer",
        "topics": ["python", "fastapi"]
    }
```

**Issues**:
- Hardcoded data repeated across tests
- Not realistic
- Manual creation for each test
- Difficult to test edge cases

**Recommended Library**: **faker** (v20.1+)

**Benefits**:
- ✅ Realistic test data generation
- ✅ Reduces manual fixture creation
- ✅ Easy to generate edge cases
- ✅ Locale support (international names, etc.)

**Effort**: **MEDIUM** (1-2 hours to refactor all tests)

**Decision**: ⚠️ **Implement in Phase 8 (Optimization)**

**Rationale**: Not blocking for Phase 3, but improves test quality

**After (with faker)**:
```python
from faker import Faker

fake = Faker()

def test_expert_search():
    # Generate realistic test data
    test_expert = {
        "user_id": fake.uuid4(),
        "name": fake.name(),
        "email": fake.email(),
        "role": fake.random_element(["junior", "mid", "senior", "lead"]),
        "topics": [fake.word() for _ in range(3)]
    }
```

**Value**: Better test coverage with less boilerplate

---

### 6. Add `factory-boy` for test fixtures

**Current State**:
```python
# Repeated fixture creation in every test
def sample_expert_1():
    return Expert(user_id="user-1", name="Alice", ...)

def sample_expert_2():
    return Expert(user_id="user-2", name="Bob", ...)
```

**Recommended Library**: **factory-boy** (v3.3+)

**Benefits**:
- ✅ DRY test fixtures
- ✅ Easy to create variations
- ✅ Integrates with `faker`
- ✅ Reduces test boilerplate

**Effort**: **MEDIUM** (1-2 hours to create factories)

**Decision**: ⚠️ **Implement in Phase 8 (Optimization)**

**After (with factory-boy)**:
```python
from factory import Factory, Faker as FactoryFaker
from faker import Faker

class ExpertFactory(Factory):
    class Meta:
        model = Expert
    
    user_id = FactoryFaker('uuid4')
    name = FactoryFaker('name')
    email = FactoryFaker('email')
    role = FactoryFaker('random_element', elements=['junior', 'mid', 'senior'])
    topics = FactoryFaker('words', nb=3)

# Usage in tests
expert1 = ExpertFactory()
expert2 = ExpertFactory(role='senior')  # Override specific fields
experts = ExpertFactory.create_batch(10)  # Create multiple
```

**Value**: Cleaner, more maintainable tests

---

## ⏸️ Low Priority (Mark as Phase 11 Optional)

### 7. Consider `cachetools` for advanced caching

**Current State**: Simple `lru_cache` planned

**Recommended Library**: **cachetools** (v5.3+)

**Benefits**:
- ✅ TTL (time-to-live) caching
- ✅ Multiple eviction strategies (LRU, LFU, RR)
- ✅ Better than manual caching dictionaries

**Effort**: **LOW** (1 hour)

**Decision**: ⏸️ **Mark as Phase 11 (optional)**

**Rationale**: Simple `lru_cache` sufficient for initial implementation. Upgrade only if:
- Cache invalidation becomes important (need TTL)
- Different eviction strategies needed (LFU vs LRU)
- Cache statistics needed

**Example (if needed later)**:
```python
from cachetools import TTLCache, cached

# TTL cache (5 minute expiration)
user_cache = TTLCache(maxsize=100, ttl=300)

@cached(user_cache)
def get_user_data(user_id: str):
    # Automatically evicts after 5 minutes
    return fetch_from_api(user_id)
```

**Mark in Phase 11 Tracking**: "Optional: Upgrade to cachetools if TTL caching needed"

---

## ❌ Not Recommended (Keep Custom Code)

### 8. Relevance Scoring Algorithm

**Current State**: Multi-factor scoring algorithm
- Role matching: 30% weight
- Topic relevance: 40% weight
- Service contribution: 20% weight
- Document authorship: 10% weight

**Library Considered**: None (domain-specific)

**Decision**: ❌ **Keep custom code**

**Rationale**: This is **core domain logic** specific to this service's business requirements. No generic library can provide this exact scoring algorithm. This belongs in `domain/services/relevance_scoring_service.py` as custom implementation.

**Implementation**:
```python
# domain/services/relevance_scoring_service.py
class RelevanceScoringService:
    """
    Domain service for expert relevance scoring.
    
    Custom algorithm (not a library) because:
    - Business-specific weights (30/40/20/10)
    - Domain-specific matching rules
    - Custom scoring logic
    """
    
    def __init__(self, weights: ScoringWeights):
        self.weights = weights
    
    def calculate_relevance(self, expert: Expert, query: ExpertQuery) -> ExpertMatch:
        # Custom domain logic - DO NOT replace with library
        role_score = self._calculate_role_score(expert, query)
        topic_score = self._calculate_topic_score(expert, query)
        service_score = self._calculate_service_score(expert, query)
        document_score = self._calculate_document_score(expert, query)
        
        overall_score = (
            role_score * self.weights.role_weight +
            topic_score * self.weights.topic_weight +
            service_score * self.weights.service_weight +
            document_score * self.weights.document_weight
        )
        
        return ExpertMatch(...)
```

---

## 📦 Updated requirements.txt

```txt
# Web Framework
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0

# HTTP Client (Phase 3 - HIGH PRIORITY) ✅
httpx==0.25.2

# Retry & Resilience (Phase 3 - HIGH PRIORITY) ✅
tenacity==8.2.3

# Configuration (Phase 3 - HIGH PRIORITY) ✅
pydantic-settings==2.1.0
python-dotenv==1.0.0

# Logging (Phase 8 - MEDIUM PRIORITY) ⚠️
structlog==23.2.0

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0

# Test Data Generation (Phase 8 - MEDIUM PRIORITY) ⚠️
faker==20.1.0
factory-boy==3.3.0

# Optional (Phase 11) ⏸️
# cachetools==5.3.2  # Uncomment if TTL caching needed

# Note: NO requests library - using httpx instead
```

---

## 📊 Impact Summary

### Code Reduction
| Area | Before | After | Saved |
|------|--------|-------|-------|
| HTTP Client | ~30 lines | 0 (library) | 30 lines |
| Retry Logic | ~15 lines | 0 (library) | 15 lines |
| Config Loading | ~30 lines | 0 (library) | 30 lines |
| Manual Logging | ~20 lines | 0 (library) | 20 lines |
| Test Fixtures | ~50 lines | 0 (library) | 50 lines |
| **Total** | **~145 lines** | **0 lines** | **~145 lines** |

### Quality Improvements
- ✅ **Async/await throughout** (httpx)
- ✅ **Connection pooling** (httpx)
- ✅ **Configurable retry with backoff** (tenacity)
- ✅ **Type-safe configuration** (pydantic-settings)
- ✅ **Structured JSON logging** (structlog - Phase 8)
- ✅ **Realistic test data** (faker - Phase 8)
- ✅ **Battle-tested implementations** (all libraries widely used)

### Consistency with Ecosystem
- ✅ Matches `code-analyzer`, `discovery-agent`, `bedrock-proxy`
- ✅ Same HTTP client (`httpx`)
- ✅ Same retry mechanism (`tenacity`)
- ✅ Same config approach (`pydantic-settings`)
- ✅ Same logging (`structlog`)

---

## ✅ Quality Gates

- [x] All custom code identified and evaluated ✅
- [x] Library recommendations documented with effort estimates ✅
- [x] HIGH priority (LOW effort) libraries marked for Phase 3 ✅
- [x] MEDIUM priority (MEDIUM effort) libraries marked for Phase 8 ✅
- [x] LOW priority (HIGH effort) libraries marked for Phase 11 ✅
- [x] Domain-specific custom code marked to keep (with rationale) ✅
- [x] requirements.txt updated ✅

---

**Status**: Recommendations complete  
**Next**: Update MASTER_TECHNOLOGY_MATRIX.md with service entry  
**Implementation**: Begin Phase 3 with recommended libraries

