# 🚀 Getting Started with Service Refactoring

**Quick start guide for developers beginning service refactoring**

---

## 📋 Prerequisites

Before starting, ensure you have:

- [x] Read the [Master Refactoring Plan](./MASTER_REFACTORING_PLAN.md)
- [x] Reviewed the [Naming Conventions & Standards](./NAMING_CONVENTIONS_STANDARDS.md)
- [x] Studied the reference implementation (`analysis-service`)
- [x] Python 3.11+ installed
- [x] Docker and Docker Compose installed
- [x] Git configured
- [x] Access to the Hackathon repository

---

## 🎯 Step-by-Step Process

### Step 1: Choose a Service

**Check availability in [Living Progress Tracker](./LIVING_PROGRESS_TRACKER.md)**

Start with services that:
- Have no dependencies (or dependencies already refactored)
- Match your expertise level
- Are in the current sprint tier

**Example**:
```bash
# Good first choices (Tier 1 - Foundation):
- redis (infrastructure, minimal dependencies)
- doc_store (core service, well-understood)
```

### Step 2: Run Automated Audit

**Use the audit script to gather metrics:**

```bash
cd /path/to/Hackathon
python3 scripts/refactoring/audit_service.py <service-name>
```

**Example**:
```bash
python3 scripts/refactoring/audit_service.py redis
```

**Output**:
- JSON report in `docs/refactoring/audits/<service>_audit.json`
- Summary displayed in terminal
- Automated checks for DDD structure, tests, docs, Docker

### Step 3: Complete Manual Audit

**Copy and fill out the Service Audit Template:**

```bash
cp docs/refactoring/SERVICE_AUDIT_TEMPLATE.md \
   docs/refactoring/audits/redis_audit.md
```

**Fill out all sections**:
1. Service Overview
2. Architecture Assessment
3. Dependencies Analysis
4. API Assessment
5. Code Quality Assessment
6. Testing Assessment
7. Configuration Management
8. Documentation Assessment
9. Docker & Deployment
10. Performance & Scalability
11. Security Assessment
12. Gap Analysis
13. Refactoring Plan
14. Risk Assessment
15. Recommendations

**Tip**: Use the JSON report from Step 2 to help fill out the template.

### Step 4: Create Refactoring Plan

**Based on your audit, create a detailed plan:**

1. **Identify Gaps**
   - Missing DDD layers
   - Insufficient tests
   - Poor documentation
   - Configuration issues

2. **Prioritize Work**
   - Critical issues first
   - High-impact, low-effort wins
   - Foundation before features

3. **Estimate Effort**
   - Phase 1: Audit (1-2 days) ✅
   - Phase 2: Design (1 day)
   - Phase 3: Implementation (3-5 days)
   - Phase 4: Integration (1-2 days)
   - Phase 5: Documentation (1 day)
   - Phase 6: Deployment (1 day)

4. **Document Risks**
   - Breaking changes
   - Dependent services
   - Data migration needs
   - Performance concerns

### Step 5: Set Up TDD Environment

**Copy the TDD checklist:**

```bash
cp docs/refactoring/TDD_CHECKLIST.md \
   docs/refactoring/checklists/redis_tdd.md
```

**Prepare test infrastructure:**

```bash
cd services/<service-name>

# Create tests directory structure
mkdir -p tests/{unit/{domain,application,infrastructure,presentation},integration,e2e}

# Create pytest configuration
cat > pytest.ini << EOF
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    --cov=.
    --cov-report=html
    --cov-report=term
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
EOF

# Create conftest.py for fixtures
touch tests/conftest.py
```

### Step 6: Design DDD Domain Model

**Create domain model diagram:**

1. **Identify Entities**
   - What are the core business objects?
   - What has identity and lifecycle?

2. **Define Value Objects**
   - What are immutable values?
   - What can be compared by value?

3. **Design Aggregates**
   - What are the consistency boundaries?
   - What is the aggregate root?

4. **Plan Domain Events**
   - What significant state changes occur?
   - What do other services need to know?

5. **Define Repository Interfaces**
   - What persistence operations are needed?
   - What queries will be common?

**Example for a simple service:**
```
Domain Model: Redis Service
===========================

Entities:
- CacheEntry (id, key, value, ttl, created_at)
- CacheNamespace (id, name, config)

Value Objects:
- TTL (seconds)
- CacheKey (namespace, key)
- CacheValue (data, encoding)

Aggregates:
- CacheEntry (root)
  └─ Metadata

Domain Events:
- CacheEntryCreated
- CacheEntryExpired
- CacheNamespaceConfigured

Repositories:
- CacheRepository (interface)
  - get(key)
  - set(key, value, ttl)
  - delete(key)
  - exists(key)
```

### Step 7: Implement Using TDD

**Follow the Red-Green-Refactor cycle:**

#### 🔴 RED Phase: Write Failing Tests

**Start with domain entities:**

```python
# tests/unit/domain/test_cache_entry.py

def test_create_cache_entry_with_valid_data_returns_entry():
    # Arrange
    key = "test:key"
    value = "test value"
    ttl = 3600
    
    # Act
    entry = CacheEntry(key=key, value=value, ttl=ttl)
    
    # Assert
    assert entry.key == key
    assert entry.value == value
    assert entry.ttl == ttl
    assert entry.id is not None

def test_create_cache_entry_with_empty_key_raises_error():
    # Arrange
    key = ""
    value = "test value"
    
    # Act & Assert
    with pytest.raises(ValueError, match="Key cannot be empty"):
        CacheEntry(key=key, value=value)
```

**Run tests - they should fail:**
```bash
pytest tests/unit/domain/test_cache_entry.py
# EXPECTED: FAIL - CacheEntry doesn't exist yet
```

#### 🟢 GREEN Phase: Make Tests Pass

**Implement minimal code:**

```python
# domain/entities/cache_entry.py

from dataclasses import dataclass
from typing import Optional
from datetime import datetime
import uuid

@dataclass
class CacheEntry:
    """A cache entry entity"""
    
    key: str
    value: str
    ttl: Optional[int] = None
    id: str = None
    created_at: datetime = None
    
    def __post_init__(self):
        if not self.key:
            raise ValueError("Key cannot be empty")
        
        if self.id is None:
            self.id = str(uuid.uuid4())
        
        if self.created_at is None:
            self.created_at = datetime.now()
```

**Run tests - they should pass:**
```bash
pytest tests/unit/domain/test_cache_entry.py
# EXPECTED: PASS
```

#### 🔄 REFACTOR Phase: Improve Code

**Now that tests pass, improve the code:**

1. Extract validation logic
2. Improve naming
3. Add type hints
4. Add docstrings
5. Remove duplication

**Refactored version:**

```python
# domain/entities/cache_entry.py

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
import uuid

from ..value_objects.cache_key import CacheKey
from ..value_objects.ttl import TTL
from ..exceptions import InvalidCacheKeyError

@dataclass
class CacheEntry:
    """
    Represents a cache entry in the system.
    
    A cache entry is an aggregate root that manages the lifecycle
    of cached data including expiration and metadata.
    
    Attributes:
        key: The unique cache key
        value: The cached value (serialized)
        ttl: Time-to-live in seconds (None = no expiration)
        id: Unique identifier for this entry
        created_at: Timestamp when entry was created
    """
    
    key: CacheKey
    value: str
    ttl: Optional[TTL] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate cache entry after initialization"""
        self._validate_key()
        self._validate_value()
    
    def _validate_key(self) -> None:
        """Validate cache key"""
        if not isinstance(self.key, CacheKey):
            raise TypeError("Key must be a CacheKey instance")
    
    def _validate_value(self) -> None:
        """Validate cache value"""
        if not self.value:
            raise ValueError("Value cannot be empty")
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        if self.ttl is None:
            return False
        
        age = (datetime.now() - self.created_at).total_seconds()
        return age > self.ttl.seconds
```

**Run tests again - should still pass:**
```bash
pytest tests/unit/domain/test_cache_entry.py
# EXPECTED: PASS (all green)
```

### Step 8: Implement All Layers

**Continue TDD through all layers:**

1. **Domain Layer** (Business Logic)
   - Entities
   - Value Objects
   - Domain Services
   - Domain Events
   - Repository Interfaces

2. **Application Layer** (Use Cases)
   - Commands (write operations)
   - Queries (read operations)
   - DTOs (data transfer)
   - Validators
   - Application Services

3. **Infrastructure Layer** (External Dependencies)
   - Repository Implementations
   - Database Connections
   - External Service Clients
   - Event Publishers
   - Configuration

4. **Presentation Layer** (API)
   - Controllers
   - Request/Response Models
   - Middleware
   - Error Handlers
   - OpenAPI Documentation

### Step 9: Integration Testing

**Test service integration:**

```bash
# Start dependencies
docker-compose up -d redis

# Run integration tests
pytest tests/integration/ -v

# Test Docker build
docker build -t hackathon/<service-name>:test .

# Test Docker Compose standalone
docker-compose -f services/<service-name>/docker-compose.yml up

# Test in ecosystem
docker-compose -f docker-compose.dev.yml up <service-name>
```

### Step 10: Quality Gates Check

**Run automated quality gates:**

```bash
python3 scripts/refactoring/check_quality_gates.py <service-name>
```

**Expected output:**
```
🚦 QUALITY GATES SUMMARY
============================================================
📊 Overall: 8/8 gates passed (100.0%)
   ✅ Architecture Review: 5/5
   ✅ Code Quality: 4/5
   ✅ Testing: 5/5
   ✅ Documentation: 5/5
   ✅ Docker & Deployment: 5/5
   ✅ Configuration: 4/5
   ✅ API Standards: 4/5
   ✅ Integration: 4/5

🎉 ALL QUALITY GATES PASSED! Service is ready.
```

**If gates fail**, address the issues and re-run.

### Step 11: Documentation

**Complete all documentation:**

1. **Update README.md**
   ```markdown
   # Service Name
   
   ## Overview
   [Purpose and key features]
   
   ## Quick Start
   [Installation and running]
   
   ## Architecture
   [DDD layers explanation]
   
   ## API Reference
   [Endpoints and examples]
   
   ## Configuration
   [Environment variables]
   
   ## Development
   [Local setup and testing]
   
   ## Integration
   [Dependencies and patterns]
   
   ## Troubleshooting
   [Common issues]
   ```

2. **Create Architecture Documentation**
   - Draw DDD layer diagram
   - Document domain model
   - Show data flows
   - Explain design decisions

3. **Complete OpenAPI Documentation**
   - Add operation descriptions
   - Include examples
   - Document error responses
   - Specify security requirements

### Step 12: Code Review

**Request code review:**

```bash
git checkout -b refactor/<service-name>
git add .
git commit -m "refactor: <service-name> - DDD implementation with comprehensive tests"
git push origin refactor/<service-name>
```

**Include in PR description:**
- Link to audit report
- Link to TDD checklist
- Quality gates results
- Breaking changes (if any)
- Migration guide (if needed)

### Step 13: Update Progress Tracker

**Update the Living Progress Tracker:**

1. Change service status to "Complete"
2. Mark all phases as done
3. Add completion date
4. Document lessons learned
5. Update metrics

### Step 14: Deploy

**Deploy to development:**

```bash
# Deploy service
docker-compose -f docker-compose.dev.yml up -d <service-name>

# Verify health
curl http://localhost:<port>/health

# Run smoke tests
./scripts/smoke_test_<service-name>.sh

# Monitor logs
docker-compose logs -f <service-name>
```

---

## 📚 Quick Reference

### Essential Commands

```bash
# Audit service
python3 scripts/refactoring/audit_service.py <service>

# Check quality gates
python3 scripts/refactoring/check_quality_gates.py <service>

# Run tests
pytest tests/ -v --cov

# Check code quality
radon cc . -a
pylint <service>
mypy <service>

# Build Docker image
docker build -t hackathon/<service>:dev .

# Run standalone
python3 main.py

# Run in Docker
docker-compose up
```

### Key Files

```
Service Structure:
├── domain/          # Business logic
├── application/     # Use cases
├── infrastructure/  # External deps
├── presentation/    # API layer
├── tests/          # Test suite
├── main.py         # Entry point
├── Dockerfile      # Docker config
└── README.md       # Documentation
```

---

## 🎯 Success Criteria

A service is complete when:

- ✅ All 8 quality gates passed
- ✅ Test coverage > 80%
- ✅ All documentation complete
- ✅ Runs standalone, in Docker, in ecosystem
- ✅ Code review approved
- ✅ Deployed to development
- ✅ Smoke tests passing

---

## 💡 Tips and Tricks

### Write Better Tests

1. **Use descriptive names**: `test_create_user_with_invalid_email_raises_validation_error()`
2. **Follow AAA pattern**: Arrange, Act, Assert
3. **One assertion per test** (when possible)
4. **Test behavior, not implementation**
5. **Use fixtures for common setup**

### Improve Code Quality

1. **Use type hints everywhere**
2. **Write docstrings for public APIs**
3. **Keep functions small** (< 20 lines)
4. **Keep complexity low** (< 10)
5. **Avoid deep nesting** (< 4 levels)

### Speed Up Development

1. **Copy from analysis-service** (reference implementation)
2. **Use templates and scripts**
3. **Run tests frequently** (TDD loop)
4. **Commit often** (small commits)
5. **Ask for help early**

---

## 🆘 Troubleshooting

### Common Issues

**Issue**: Tests are failing after refactoring  
**Solution**: Run tests one at a time to identify the failing test, then fix the code

**Issue**: Quality gates failing  
**Solution**: Run the quality gate script to see specific failures, address each one

**Issue**: Docker build failing  
**Solution**: Check Dockerfile syntax, ensure all dependencies in requirements.txt

**Issue**: Service won't start  
**Solution**: Check logs, verify environment variables, ensure dependencies are running

**Issue**: Low test coverage  
**Solution**: Add tests for uncovered branches, focus on business logic first

---

## 📞 Getting Help

- **Documentation**: Check the [Master Refactoring Plan](./MASTER_REFACTORING_PLAN.md)
- **Standards**: Reference [Naming Conventions](./NAMING_CONVENTIONS_STANDARDS.md)
- **Examples**: Study `services/analysis-service/`
- **Questions**: Ask in team chat or create an issue

---

## 🎉 Celebration

**After completing a service:**

1. Update progress tracker
2. Share with team
3. Document lessons learned
4. Take a break - you earned it!

Then pick the next service and repeat! 🚀

---

**Happy Refactoring!**

