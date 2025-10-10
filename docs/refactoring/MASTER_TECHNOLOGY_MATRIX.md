<!-- AI_READ_PRIORITY: 2 -->
<!-- AI_TAGS: technology, libraries, dependencies, standardization, consolidation -->
<!-- AI_KEY_SECTIONS: Common Libraries, Service Technology Audit, Consolidation Opportunities -->

---
ai_metadata:
  purpose: technology_and_library_tracking
  read_priority: 2
  context_level: strategic
  tags:
  - technology
  - libraries
  - dependencies
  - standardization
  - consolidation
  - python-ecosystem
  when_to_read: During Phase 2 (Design) to identify library opportunities
  key_sections:
  - Common Python Libraries
  - Service Technology Audit Matrix
  - Consolidation Opportunities
  - Library Recommendations
  execution_relevance: high
---

# Master Technology & Library Matrix

**Version**: 1.0.0  
**Created**: October 10, 2025  
**Status**: Living Document  
**Purpose**: Track Python libraries, technologies, and dependencies across all services to identify standardization and consolidation opportunities

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Common Python Libraries](#common-python-libraries)
3. [Service Technology Audit Matrix](#service-technology-audit-matrix)
4. [Technology Categories](#technology-categories)
5. [Consolidation Opportunities](#consolidation-opportunities)
6. [Library Recommendations](#library-recommendations)
7. [Standards & Best Practices](#standards--best-practices)

---

## 🎯 Overview

### Purpose

This living document tracks:
- **Python libraries** used across all services
- **Technologies** and frameworks (FastAPI, Streamlit, LangGraph, etc.)
- **Dependency patterns** and version consistency
- **Consolidation opportunities** where libraries can replace custom code
- **Standardization recommendations** for common functionality

### When to Use This Document

1. **Phase 2 (Design & Planning)**: Review matrix to identify libraries that can simplify design
2. **Phase 3 (Implementation)**: Use recommended libraries instead of custom code
3. **Phase 8 (Optimization)**: Identify quick wins through library adoption
4. **Phase 11 (Optional Work)**: Implement deferred library migrations

### AI Agent Usage

**During Phase 2**:
1. Read this document
2. Check if service's planned functionality matches existing libraries
3. Recommend libraries for adoption
4. Document library recommendations in service's Phase 2 design
5. Mark complex library migrations as optional work (Phase 11)

---

## 📚 Common Python Libraries

### Web Frameworks

| Library | Version | Purpose | Services Using | Adoption Level |
|---------|---------|---------|----------------|----------------|
| **FastAPI** | 0.104+ | REST API framework | Most services | ⭐⭐⭐⭐⭐ STANDARD |
| **Streamlit** | 1.28+ | Dashboard/UI framework | Dashboards | ⭐⭐⭐⭐ RECOMMENDED |
| **Uvicorn** | 0.24+ | ASGI server | All FastAPI services | ⭐⭐⭐⭐⭐ STANDARD |

### HTTP Clients

| Library | Version | Purpose | Services Using | Adoption Level |
|---------|---------|---------|----------------|----------------|
| **httpx** | 0.25+ | Async HTTP client | Most services | ⭐⭐⭐⭐⭐ STANDARD |
| **requests** | 2.31+ | Sync HTTP client (legacy) | Some services | ⭐⭐ DEPRECATED |

**Recommendation**: Migrate all services to `httpx` for:
- Async/await support
- HTTP/2 support
- Connection pooling
- Better timeout handling

### Data Validation & Serialization

| Library | Version | Purpose | Services Using | Adoption Level |
|---------|---------|---------|----------------|----------------|
| **Pydantic** | 2.4+ | Data validation & serialization | Most services | ⭐⭐⭐⭐⭐ STANDARD |
| **marshmallow** | 3.20+ | Serialization (legacy) | Few services | ⭐ DEPRECATED |

**Recommendation**: Standardize on Pydantic v2 for all services

### Configuration Management

| Library | Version | Purpose | Services Using | Adoption Level |
|---------|---------|---------|----------------|----------------|
| **pydantic-settings** | 2.0+ | Environment-based config | Some services | ⭐⭐⭐⭐⭐ STANDARD |
| **python-dotenv** | 1.0+ | .env file loading | Most services | ⭐⭐⭐⭐ RECOMMENDED |
| **dynaconf** | 3.2+ | Advanced config management | Few services | ⭐⭐⭐ OPTIONAL |

**Recommendation**: Use `pydantic-settings.BaseSettings` for all config

### Retry & Resilience

| Library | Version | Purpose | Services Using | Adoption Level |
|---------|---------|---------|----------------|----------------|
| **tenacity** | 8.2+ | Retry with backoff | Some services | ⭐⭐⭐⭐⭐ STANDARD |
| **backoff** | 2.2+ | Alternative retry library | Few services | ⭐⭐ ALTERNATIVE |

**Recommendation**: Standardize on `tenacity` for all retry logic

### Caching

| Library | Version | Purpose | Services Using | Adoption Level |
|---------|---------|---------|----------------|----------------|
| **functools.lru_cache** | Built-in | In-memory caching | Most services | ⭐⭐⭐⭐⭐ STANDARD |
| **cachetools** | 5.3+ | Advanced caching strategies | Some services | ⭐⭐⭐⭐ RECOMMENDED |
| **redis** | 5.0+ | Distributed caching | Few services | ⭐⭐⭐⭐ RECOMMENDED |

### Logging

| Library | Version | Purpose | Services Using | Adoption Level |
|---------|---------|---------|----------------|----------------|
| **structlog** | 23.2+ | Structured logging | Some services | ⭐⭐⭐⭐⭐ STANDARD |
| **loguru** | 0.7+ | Simplified logging | Few services | ⭐⭐⭐ ALTERNATIVE |
| **logging** | Built-in | Standard logging | Most services | ⭐⭐⭐ LEGACY |

**Recommendation**: Standardize on `structlog` for JSON logging

### Testing

| Library | Version | Purpose | Services Using | Adoption Level |
|---------|---------|---------|----------------|----------------|
| **pytest** | 7.4+ | Test framework | All services | ⭐⭐⭐⭐⭐ STANDARD |
| **pytest-asyncio** | 0.21+ | Async test support | Most services | ⭐⭐⭐⭐⭐ STANDARD |
| **pytest-cov** | 4.1+ | Coverage measurement | All services | ⭐⭐⭐⭐⭐ STANDARD |
| **faker** | 20.0+ | Test data generation | Some services | ⭐⭐⭐⭐ RECOMMENDED |
| **factory-boy** | 3.3+ | Test fixture factories | Few services | ⭐⭐⭐⭐ RECOMMENDED |
| **hypothesis** | 6.92+ | Property-based testing | Few services | ⭐⭐⭐ OPTIONAL |

### AI/LLM Integration

| Library | Version | Purpose | Services Using | Adoption Level |
|---------|---------|---------|----------------|----------------|
| **LangChain** | 0.1+ | LLM orchestration | Some services | ⭐⭐⭐⭐ RECOMMENDED |
| **LangGraph** | 0.0.20+ | Stateful LLM workflows | discovery-agent | ⭐⭐⭐⭐ RECOMMENDED |
| **openai** | 1.3+ | OpenAI API client | Some services | ⭐⭐⭐⭐ RECOMMENDED |
| **boto3** | 1.29+ | AWS SDK (Bedrock) | bedrock-proxy | ⭐⭐⭐⭐ RECOMMENDED |

### Data Processing

| Library | Version | Purpose | Services Using | Adoption Level |
|---------|---------|---------|----------------|----------------|
| **pandas** | 2.1+ | Data analysis | Dashboards, analysis | ⭐⭐⭐⭐⭐ STANDARD |
| **numpy** | 1.26+ | Numerical computing | Data services | ⭐⭐⭐⭐ RECOMMENDED |
| **plotly** | 5.18+ | Interactive visualizations | Dashboards | ⭐⭐⭐⭐⭐ STANDARD |

### Code Analysis

| Library | Version | Purpose | Services Using | Adoption Level |
|---------|---------|---------|----------------|----------------|
| **ast** | Built-in | Python AST parsing | code-analyzer | ⭐⭐⭐⭐⭐ STANDARD |
| **radon** | 6.0+ | Complexity metrics | code-analyzer | ⭐⭐⭐⭐ RECOMMENDED |
| **bandit** | 1.7+ | Security linting | secure-analyzer | ⭐⭐⭐⭐ RECOMMENDED |
| **pylint** | 3.0+ | Code linting | Some services | ⭐⭐⭐⭐ RECOMMENDED |
| **mypy** | 1.7+ | Type checking | Some services | ⭐⭐⭐⭐ RECOMMENDED |

### Database & Storage

| Library | Version | Purpose | Services Using | Adoption Level |
|---------|---------|---------|----------------|----------------|
| **redis** | 5.0+ | Key-value store | Many services | ⭐⭐⭐⭐⭐ STANDARD |
| **pymongo** | 4.6+ | MongoDB client | doc-store | ⭐⭐⭐⭐ RECOMMENDED |
| **SQLAlchemy** | 2.0+ | SQL ORM | Few services | ⭐⭐⭐⭐ RECOMMENDED |

### Utilities

| Library | Version | Purpose | Services Using | Adoption Level |
|---------|---------|---------|----------------|----------------|
| **uuid** | Built-in | Unique identifiers | Most services | ⭐⭐⭐⭐⭐ STANDARD |
| **datetime** | Built-in | Date/time handling | All services | ⭐⭐⭐⭐⭐ STANDARD |
| **pathlib** | Built-in | Path manipulation | Most services | ⭐⭐⭐⭐⭐ STANDARD |
| **dataclasses** | Built-in | Data structures | Most services | ⭐⭐⭐⭐⭐ STANDARD |
| **enum** | Built-in | Enumerations | Most services | ⭐⭐⭐⭐⭐ STANDARD |

---

## 🔍 Service Technology Audit Matrix

### Service: code-analyzer

| Category | Technology | Version | Purpose | Consolidation Opportunity |
|----------|-----------|---------|---------|---------------------------|
| Framework | FastAPI | 0.104+ | REST API | ✅ Standard |
| HTTP Client | httpx | 0.25+ | External calls | ✅ Standard |
| Validation | Pydantic | 2.4+ | Data validation | ✅ Standard |
| Config | pydantic-settings | 2.0+ | Configuration | ✅ Standard |
| Retry | tenacity | 8.2+ | Retry logic | ✅ Standard |
| Logging | structlog | 23.2+ | JSON logging | ✅ Standard |
| Testing | pytest | 7.4+ | Unit/integration tests | ✅ Standard |
| Code Analysis | ast | Built-in | AST parsing | ✅ Standard |
| Metrics | radon | 6.0+ | Complexity metrics | ✅ Standard |

**Custom Code to Consolidate**: None identified (already well-structured)

**Library Opportunities**: None (already using best practices)

---

### Service: discovery-agent

| Category | Technology | Version | Purpose | Consolidation Opportunity |
|----------|-----------|---------|---------|---------------------------|
| Framework | FastAPI | 0.104+ | REST API | ✅ Standard |
| HTTP Client | httpx | 0.25+ | External calls | ✅ Standard |
| Validation | Pydantic | 2.4+ | Data validation | ✅ Standard |
| AI/LLM | LangGraph | 0.0.20+ | Stateful workflows | ✅ Standard |
| AI/LLM | LangChain | 0.1+ | LLM orchestration | ✅ Standard |
| Retry | tenacity | 8.2+ | Retry logic | ✅ Standard |
| Testing | pytest | 7.4+ | Tests | ✅ Standard |

**Custom Code to Consolidate**: None identified

**Library Opportunities**: Consider `langchain-community` for additional integrations

---

### Service: bedrock-proxy

| Category | Technology | Version | Purpose | Consolidation Opportunity |
|----------|-----------|---------|---------|---------------------------|
| Framework | FastAPI | 0.104+ | REST API | ✅ Standard |
| HTTP Client | httpx | 0.25+ | External calls | ✅ Standard |
| Validation | Pydantic | 2.4+ | Data validation | ✅ Standard |
| AWS SDK | boto3 | 1.29+ | Bedrock integration | ✅ Standard |
| Retry | tenacity | 8.2+ | Retry logic | ✅ Standard |
| Testing | pytest | 7.4+ | Tests | ✅ Standard |

**Custom Code to Consolidate**: None identified

**Library Opportunities**: Consider `langchain-aws` for Bedrock abstractions

---

### Service: analysis-service

| Category | Technology | Version | Purpose | Consolidation Opportunity |
|----------|-----------|---------|---------|---------------------------|
| Framework | FastAPI | 0.104+ | REST API | ✅ Standard |
| HTTP Client | httpx | 0.25+ | External calls | ✅ Standard |
| Validation | Pydantic | 2.4+ | Data validation | ✅ Standard |
| Config | pydantic-settings | 2.0+ | Configuration | ✅ Standard |
| Event Bus | Custom | N/A | CQRS event bus | ⚠️ Consider `pyee` or `blinker` |
| Testing | pytest | 7.4+ | Tests | ✅ Standard |

**Custom Code to Consolidate**:
- ⚠️ Custom event bus implementation → Consider `pyee` or `blinker` for event handling
- ⚠️ Custom distributed processing → Consider `Celery` or `dramatiq` if scaling needed

**Library Opportunities**:
- `pyee` (event emitter) - Could simplify event bus
- `blinker` (signals) - Alternative for pub/sub patterns
- `Celery` (task queue) - If distributed processing grows

**Recommendation**: Keep custom event bus for now (simple, fits needs), consider libraries if complexity grows (mark as Phase 11 optional work)

---

### Service: architecture-digitizer

| Category | Technology | Version | Purpose | Consolidation Opportunity |
|----------|-----------|---------|---------|---------------------------|
| Framework | FastAPI | 0.104+ | REST API | ✅ Standard |
| HTTP Client | httpx | 0.25+ | External calls | ✅ Standard |
| Validation | Pydantic | 2.4+ | Data validation | ✅ Standard |
| Testing | pytest | 7.4+ | Tests | ✅ Standard |
| Normalizers | Custom | N/A | Format normalization | ✅ Appropriate (domain-specific) |

**Custom Code to Consolidate**: None identified (normalizers are domain-specific)

**Library Opportunities**: None (custom logic is appropriate for this domain)

---

### Service: data-services-dashboard

| Category | Technology | Version | Purpose | Consolidation Opportunity |
|----------|-----------|---------|---------|---------------------------|
| UI Framework | Streamlit | 1.28+ | Dashboard UI | ✅ Standard |
| API Framework | FastAPI | 0.104+ | REST API | ✅ Standard |
| HTTP Client | httpx | 0.25+ | External calls | ✅ Standard |
| Data Processing | pandas | 2.1+ | Data analysis | ✅ Standard |
| Visualization | plotly | 5.18+ | Charts | ✅ Standard |
| Retry | Custom | N/A | Retry decorator | ⚠️ Use `tenacity` |
| Testing | pytest | 7.4+ | Tests | ✅ Standard |

**Custom Code to Consolidate**:
- ⚠️ `@with_retry` decorator → Replace with `tenacity.retry`

**Library Opportunities**:
- `tenacity` - Replace custom retry logic (mark as Phase 11 optional work)

---

### Service: expert-finder-service

| Category | Technology | Version | Purpose | Consolidation Opportunity |
|----------|-----------|---------|---------|---------------------------|
| Framework | FastAPI | 0.104+ | REST API (planned) | ✅ Standard |
| HTTP Client | httpx | 0.25+ | External calls (planned) | ✅ Standard |
| Validation | Pydantic | 2.4+ | Data validation (planned) | ✅ Standard |
| Config | pydantic-settings | 2.0+ | Configuration (planned) | ✅ Standard |
| Retry | tenacity | 8.2+ | Retry logic (planned) | ✅ Standard |
| Caching | lru_cache | Built-in | In-memory cache (planned) | ✅ Standard |
| Testing | pytest | 7.4+ | Tests (planned) | ✅ Standard |
| Scoring | Custom | N/A | Relevance scoring | ✅ Appropriate (domain-specific) |

**Current State**: Monolithic 1,286-line `main.py` with custom implementations

**Custom Code to Consolidate**:
- ⚠️ Manual retry logic → Use `tenacity.retry`
- ⚠️ Custom HTTP calls → Use `httpx.AsyncClient` with connection pooling
- ⚠️ Manual config loading → Use `pydantic-settings.BaseSettings`
- ⚠️ Print statements → Use `structlog` for structured logging

**Library Opportunities**:
1. **tenacity** - Replace manual retry logic with exponential backoff
2. **httpx** - Replace `requests` with async HTTP client
3. **pydantic-settings** - Replace manual env var loading
4. **structlog** - Replace print statements with structured JSON logs
5. **cachetools** - Consider for advanced caching strategies (LRU, TTL)
6. **faker** + **factory-boy** - For generating test data

**Recommendation**: 
- **Phase 3**: Implement with `httpx`, `pydantic-settings`, `tenacity`, `structlog` from the start
- **Phase 11**: Consider `cachetools` for advanced caching (if simple `lru_cache` insufficient)

---

## 📊 Technology Categories

### 1. Web Framework (REST APIs)

**Standard**: FastAPI + Uvicorn

**Why**:
- Modern async/await support
- Automatic OpenAPI generation
- Pydantic integration
- Type hints for validation
- High performance

**Alternatives Considered**:
- Flask (synchronous, older)
- Django REST Framework (heavier, monolithic)

**Recommendation**: Use FastAPI for all new REST API services

---

### 2. HTTP Client

**Standard**: httpx

**Why**:
- Async/await support
- HTTP/2 support
- Connection pooling built-in
- Better timeout handling than `requests`
- Compatible with `requests` API

**Migration Path**: Replace `requests` with `httpx` in all services

**Example**:
```python
# Before (requests)
import requests
response = requests.get(url)

# After (httpx)
import httpx
async with httpx.AsyncClient() as client:
    response = await client.get(url)

# With connection pooling
client = httpx.AsyncClient(
    limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
)
```

---

### 3. Data Validation & Serialization

**Standard**: Pydantic v2

**Why**:
- Type hints for validation
- Automatic serialization/deserialization
- FastAPI integration
- Better error messages
- Performance (Pydantic v2 is 10x faster)

**Migration Path**: Replace `marshmallow` with Pydantic in all services

---

### 4. Configuration Management

**Standard**: pydantic-settings.BaseSettings

**Why**:
- Type-safe configuration
- Environment variable loading
- .env file support
- Validation on startup
- Seamless FastAPI integration

**Example**:
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    service_name: str = "my-service"
    service_port: int = 5000
    user_store_url: str
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
```

---

### 5. Retry & Resilience

**Standard**: tenacity

**Why**:
- Configurable retry strategies
- Exponential backoff support
- Stop conditions (max attempts, max time)
- Wait strategies (fixed, exponential, random)
- Better than custom retry logic

**Example**:
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10)
)
async def call_external_api():
    async with httpx.AsyncClient() as client:
        return await client.get(url)
```

---

### 6. Logging

**Standard**: structlog

**Why**:
- Structured JSON logging
- Context preservation
- Fast performance
- Easy to integrate with log aggregators
- Better than print statements or basic logging

**Example**:
```python
import structlog

logger = structlog.get_logger()

logger.info(
    "user_search_completed",
    user_id="user-123",
    query="python expert",
    results_count=5,
    duration_ms=45.2
)
```

---

### 7. Caching

**Standard**: functools.lru_cache (simple) or cachetools (advanced)

**Why**:
- `lru_cache`: Built-in, simple, fast
- `cachetools`: Advanced strategies (TTL, LRU, LFU, RR)
- Better than manual caching dictionaries

**Example**:
```python
from functools import lru_cache
from cachetools import TTLCache, cached

# Simple LRU cache
@lru_cache(maxsize=128)
def expensive_computation(x):
    return x ** 2

# TTL cache (time-based expiration)
cache = TTLCache(maxsize=100, ttl=300)  # 5 minutes

@cached(cache)
def get_user_data(user_id: str):
    return fetch_from_api(user_id)
```

---

### 8. Testing

**Standard**: pytest + pytest-asyncio + pytest-cov

**Recommended Add-ons**:
- **faker**: Realistic test data generation
- **factory-boy**: Test fixture factories
- **hypothesis**: Property-based testing

**Example**:
```python
import pytest
from faker import Faker
from factory import Factory, Faker as FactoryFaker

# Using faker
fake = Faker()
test_email = fake.email()
test_name = fake.name()

# Using factory-boy
class UserFactory(Factory):
    class Meta:
        model = User
    
    name = FactoryFaker('name')
    email = FactoryFaker('email')
    role = 'developer'

# In tests
@pytest.fixture
def sample_user():
    return UserFactory()

def test_user_creation(sample_user):
    assert sample_user.email
    assert sample_user.name
```

---

## 🔗 Consolidation Opportunities

### High Priority (Implement in Phase 3)

1. **Replace `requests` with `httpx`**
   - **Services Affected**: Any using `requests`
   - **Effort**: Low (API compatible)
   - **Benefit**: Async support, better performance
   - **Action**: Use `httpx` in all new services

2. **Replace manual retry logic with `tenacity`**
   - **Services Affected**: Any with custom retry decorators
   - **Effort**: Low (drop-in replacement)
   - **Benefit**: Configurable, tested, exponential backoff
   - **Action**: Use `tenacity` in all new services

3. **Replace manual env loading with `pydantic-settings`**
   - **Services Affected**: Any manually loading env vars
   - **Effort**: Low (Pydantic integration)
   - **Benefit**: Type-safe, validated, .env support
   - **Action**: Use in all new services

4. **Replace print statements with `structlog`**
   - **Services Affected**: Any using print or basic logging
   - **Effort**: Medium
   - **Benefit**: Structured JSON logs, better observability
   - **Action**: Standardize on `structlog`

---

### Medium Priority (Phase 8 or Phase 11)

1. **Replace custom event bus with `pyee` or `blinker`**
   - **Services Affected**: analysis-service
   - **Effort**: Medium (requires refactoring)
   - **Benefit**: Tested library vs custom code
   - **Action**: Evaluate if custom event bus grows complex
   - **Decision**: Mark as Phase 11 (optional) for now

2. **Replace custom retry decorator with `tenacity`**
   - **Services Affected**: data-services-dashboard
   - **Effort**: Low
   - **Benefit**: Better tested, more features
   - **Action**: Mark as Phase 11 (optional)

3. **Add `faker` + `factory-boy` for test data**
   - **Services Affected**: All services
   - **Effort**: Low per service
   - **Benefit**: Realistic test data, less manual fixture creation
   - **Action**: Add to new services in Phase 3

---

### Low Priority (Future Consideration)

1. **Distributed task queue (Celery/dramatiq)**
   - **Services Affected**: analysis-service (if scaling needed)
   - **Effort**: High (infrastructure required)
   - **Benefit**: Horizontal scaling of background tasks
   - **Action**: Only if distributed processing grows

2. **Advanced caching (Redis)**
   - **Services Affected**: High-traffic services
   - **Effort**: Medium (Redis infrastructure required)
   - **Benefit**: Distributed caching, persistence
   - **Action**: Only if in-memory caching insufficient

---

## 💡 Library Recommendations by Use Case

### Use Case: External API Integration

**Recommended Stack**:
- `httpx.AsyncClient` - HTTP client with connection pooling
- `tenacity.retry` - Retry with exponential backoff
- `pydantic.BaseModel` - Response validation
- `structlog` - Request/response logging

**Example**:
```python
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from pydantic import BaseModel
import structlog

logger = structlog.get_logger()

class UserResponse(BaseModel):
    user_id: str
    name: str
    email: str

client = httpx.AsyncClient(
    timeout=30.0,
    limits=httpx.Limits(max_keepalive_connections=20)
)

@retry(stop=stop_after_attempt(3), wait=wait_exponential())
async def fetch_user(user_id: str) -> UserResponse:
    logger.info("fetching_user", user_id=user_id)
    response = await client.get(f"{USER_STORE_URL}/users/{user_id}")
    response.raise_for_status()
    return UserResponse(**response.json())
```

---

### Use Case: Configuration Management

**Recommended Stack**:
- `pydantic-settings.BaseSettings` - Type-safe config
- `python-dotenv` - .env file loading (included in pydantic-settings)

**Example**:
```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Service config
    service_name: str = "my-service"
    service_port: int = 5000
    environment: str = "development"
    
    # Dependencies (required)
    user_store_url: str
    
    # Dependencies (optional)
    doc_store_url: str | None = None
    
    # HTTP client config
    http_timeout_seconds: int = 30
    http_pool_size: int = 10
    
    # Caching
    cache_ttl_seconds: int = 300
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

settings = Settings()
```

---

### Use Case: Structured Logging

**Recommended Stack**:
- `structlog` - Structured JSON logging
- Log collector client (custom or library)

**Example**:
```python
import structlog
import logging

# Configure structlog
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.BoundLogger,
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)

logger = structlog.get_logger()

# Usage
logger.info(
    "expert_search",
    user_id="user-123",
    query_topics=["python", "fastapi"],
    results_found=5,
    duration_ms=45.2
)
```

---

### Use Case: Testing

**Recommended Stack**:
- `pytest` - Test framework
- `pytest-asyncio` - Async test support
- `pytest-cov` - Coverage measurement
- `faker` - Realistic test data
- `factory-boy` - Test fixture factories
- `httpx` - HTTP client testing

**Example**:
```python
import pytest
from faker import Faker
from factory import Factory, Faker as FactoryFaker

fake = Faker()

class ExpertFactory(Factory):
    class Meta:
        model = Expert
    
    user_id = FactoryFaker('uuid4')
    name = FactoryFaker('name')
    email = FactoryFaker('email')
    role = 'senior_developer'
    skills = ['python', 'fastapi', 'docker']

@pytest.fixture
def sample_expert():
    return ExpertFactory()

@pytest.mark.asyncio
async def test_expert_search(sample_expert):
    query = ExpertQuery(topics=["python"], limit=10)
    results = await search_experts(query)
    assert len(results.experts) > 0
```

---

## 📋 Standards & Best Practices

### Standard Library Choices

| Category | Standard Library | Alternative (Avoid) |
|----------|------------------|---------------------|
| Web Framework | FastAPI | Flask, Django REST |
| HTTP Client | httpx | requests |
| Validation | Pydantic v2 | marshmallow |
| Config | pydantic-settings | os.getenv, ConfigParser |
| Retry | tenacity | Custom decorators |
| Logging | structlog | print, logging |
| Testing | pytest | unittest |
| Async HTTP | httpx.AsyncClient | aiohttp |
| Caching | lru_cache, cachetools | Manual dicts |

### When to Use Custom Code vs Libraries

**Use Libraries When**:
- ✅ Well-established problem (HTTP, retry, validation)
- ✅ Library is well-maintained and widely used
- ✅ Library reduces code complexity
- ✅ Library provides better features than custom code

**Use Custom Code When**:
- ✅ Domain-specific logic (scoring algorithms, normalizers)
- ✅ Simple functionality (< 50 lines)
- ✅ No good library exists
- ✅ Library adds unnecessary complexity

**Example Good Custom Code**:
- `RelevanceScoringService` (expert-finder) - Domain-specific algorithm
- Format normalizers (architecture-digitizer) - Domain-specific transformations
- CQRS event bus (analysis-service) - Simple, fits needs

**Example Bad Custom Code** (use libraries instead):
- Manual retry logic → Use `tenacity`
- Custom HTTP client → Use `httpx`
- Manual env var loading → Use `pydantic-settings`
- Print statements → Use `structlog`

---

## 🔄 Update Frequency

This document should be updated:
- **Phase 2** of each service refactoring (add service to matrix)
- **Phase 8** of each service refactoring (note consolidation opportunities)
- **Monthly**: Review for new libraries or version updates
- **As needed**: When new patterns or technologies emerge

---

**Last Updated**: October 10, 2025  
**Next Review**: November 10, 2025  
**Maintainer**: Hackathon Team

