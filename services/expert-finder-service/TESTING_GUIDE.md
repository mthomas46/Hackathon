# Testing Guide - expert-finder-service

**Version**: 1.0.0  
**Last Updated**: October 10, 2025  
**Coverage**: 77% (Target: 80%+)

---

## 📋 Overview

This guide provides comprehensive information on testing the expert-finder-service. The service uses a test pyramid approach with emphasis on unit tests, supported by integration and functional tests.

---

## 🎯 Testing Philosophy

### Test Pyramid

```
        /\
       /E2E\      10% - End-to-End (workflow tests)
      /------\
     /  INT   \   30% - Integration (cross-layer)
    /----------\
   /    UNIT    \ 60% - Unit (isolated components)
  /--------------\
```

**Focus**: Fast, reliable unit tests with strategic integration coverage

---

## 📊 Current Coverage

**Overall**: 77% (Target: 80%+)

| Layer | Coverage | Status |
|-------|----------|--------|
| **Domain** | 80%+ | ✅ Excellent |
| **Infrastructure/Config** | 93% | ✅ Excellent |
| **Application** | 71% | ⚠️ Good |
| **Presentation** | 89%+ | ✅ Excellent |
| **Infrastructure/Repos** | 20-44% | ⚠️ Basic |
| **Utils** | 27-45% | ⚠️ Basic |

---

## 🧪 Test Categories

### Unit Tests (`tests/unit/`)

**Purpose**: Test individual components in isolation

**Files**:
- `test_domain_expert.py` - Expert entity tests
- `test_domain_scoring_service.py` - Scoring algorithm tests
- `test_infrastructure_config.py` - Settings/configuration tests
- `test_infrastructure_repositories.py` - Repository initialization tests
- `test_application_use_cases.py` - Use case orchestration tests
- `test_presentation_routes.py` - API endpoint tests

**Total**: 57 tests (48 passing, 9 with mocking issues)

**Run Command**:
```bash
pytest tests/unit/ -v
```

---

### Integration Tests (`tests/integration/`)

**Purpose**: Test interactions between layers

**Status**: ⏳ Planned (Phase 4 enhancement)

**Planned Tests**:
- Repository HTTP integration tests
- Use case with real repositories
- Cross-service workflow tests

**Run Command**:
```bash
pytest tests/integration/ -v
```

---

### E2E Tests

**Purpose**: Test complete workflows

**Status**: ⏳ Planned (Phase 4 enhancement)

**Planned Tests**:
- Complete expert finding workflow
- SME identification flow
- Error handling scenarios

---

## 🚀 Running Tests

### Quick Start

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/unit/test_domain_expert.py -v

# Run specific test method
pytest tests/unit/test_domain_expert.py::TestExpertEntity::test_expert_creation -v
```

### Test Markers

Tests are marked for selective execution:

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only functional tests
pytest -m functional

# Skip slow tests
pytest -m "not slow"
```

**Available Markers**:
- `unit` - Unit tests
- `integration` - Integration tests
- `functional` - Functional tests
- `performance` - Performance/benchmark tests
- `security` - Security tests
- `contract` - API contract tests
- `e2e` - End-to-end tests
- `workflow` - Workflow tests

---

## 📝 Writing Tests

### Test Structure

```python
"""
Module docstring explaining what's being tested.
"""

import pytest
from module import ClassToTest


class TestClassName:
    """Group related tests in a class."""
    
    @pytest.fixture
    def test_fixture(self):
        """Create reusable test data."""
        return ClassToTest()
    
    def test_specific_behavior(self, test_fixture):
        """Test one specific behavior.
        
        Arrange: Set up test conditions
        Act: Execute the action
        Assert: Verify the result
        """
        # Arrange
        input_data = {"key": "value"}
        
        # Act
        result = test_fixture.method(input_data)
        
        # Assert
        assert result == expected_value
```

### Naming Conventions

- **Test Files**: `test_<module_name>.py`
- **Test Classes**: `Test<ClassName>`
- **Test Methods**: `test_<what_it_does>`

**Examples**:
- `test_expert_creation` ✅
- `test_user_creation` ❌ (too generic)
- `test_expert_creation_with_valid_data` ✅ (specific)

---

## 🎭 Mocking Guidelines

### When to Mock

✅ **DO mock**:
- External services (user-store, doc-store)
- Database connections
- File system operations
- Network calls
- Time-dependent operations

❌ **DON'T mock**:
- Domain logic
- Simple value objects
- Pure functions
- Code under test

### Mocking Examples

#### Mock External HTTP Calls

```python
from unittest.mock import AsyncMock

@pytest.fixture
def mock_user_repo():
    repo = AsyncMock()
    repo.get_users_by_role.return_value = [
        {"user_id": "1", "name": "Alice"}
    ]
    return repo
```

#### Mock Settings

```python
@pytest.fixture
def mock_settings(monkeypatch):
    monkeypatch.setenv("SERVICE_PORT", "9999")
    monkeypatch.setenv("DEBUG", "true")
    return Settings()
```

---

## 🔍 Testing Best Practices

### 1. Test One Thing

Each test should verify one specific behavior:

```python
# ✅ Good - Tests one behavior
def test_expert_has_role_returns_true_for_matching_role():
    expert = Expert(role="Backend Developer")
    assert expert.has_role("Backend")

# ❌ Bad - Tests multiple behaviors
def test_expert_operations():
    expert = Expert(role="Backend Developer", topics=["Python"])
    assert expert.has_role("Backend")
    assert expert.has_topic("Python")  # Separate test
```

### 2. Use Descriptive Names

```python
# ✅ Good - Clear what's being tested
def test_scoring_service_returns_zero_for_no_matches():
    ...

# ❌ Bad - Unclear what's expected
def test_scoring():
    ...
```

### 3. Arrange-Act-Assert Pattern

```python
def test_example():
    # Arrange - Set up test conditions
    expert = Expert(user_id="1", name="Alice")
    
    # Act - Execute the action
    result = expert.is_senior()
    
    # Assert - Verify the result
    assert result == False
```

### 4. Test Edge Cases

```python
def test_topic_match_with_empty_list():
    expert = Expert(topics=[])
    assert expert.topic_match_count([]) == 0

def test_topic_match_with_none():
    expert = Expert(topics=None)
    assert expert.topic_match_count(["Python"]) == 0
```

### 5. Use Fixtures for Reusability

```python
@pytest.fixture
def sample_expert():
    """Reusable expert for multiple tests."""
    return Expert(
        user_id="1",
        name="Alice",
        role="Backend Developer",
        topics=["Python", "FastAPI"]
    )

def test_expert_name(sample_expert):
    assert sample_expert.name == "Alice"

def test_expert_role(sample_expert):
    assert sample_expert.role == "Backend Developer"
```

---

## 📈 Coverage Goals

### Target Coverage by Layer

| Layer | Target | Current | Status |
|-------|--------|---------|--------|
| Domain | 80%+ | 80%+ | ✅ Met |
| Application | 80%+ | 71% | ⚠️ Close |
| Infrastructure | 60%+ | 40%+ | ⚠️ Basic |
| Presentation | 80%+ | 89%+ | ✅ Met |
| **Overall** | **80%+** | **77%** | ⚠️ **Close** |

### How to Improve Coverage

1. **Add more unit tests for utils**:
   - `validators.py` (current: 45%)
   - `transformers.py` (current: 27%)

2. **Add repository integration tests**:
   - Use mocked HTTP responses
   - Test error handling
   - Test retry logic

3. **Add use case integration tests**:
   - Test with real dependencies
   - Test failure scenarios
   - Test edge cases

---

## 🐛 Common Test Issues

### Issue: Tests Failing with Import Errors

**Solution**: Ensure service directory is in Python path

```bash
cd services/expert-finder-service
export PYTHONPATH="."
pytest
```

### Issue: Async Test Failures

**Solution**: Use `pytest-asyncio` and mark tests:

```python
@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result == expected
```

### Issue: Mocking Not Working

**Solution**: Mock at the right level:

```python
# ❌ Wrong - Mocks the import
@patch("module.function")

# ✅ Right - Mocks where it's used
@patch("tests.unit.test_module.function")
```

---

## ⚡ Performance Testing

### Benchmark Tests

```bash
pytest tests/performance/ --benchmark-only
```

### Coverage Performance

```bash
# Fast (no coverage)
pytest

# With coverage (slower)
pytest --cov=.

# With HTML report (slowest)
pytest --cov=. --cov-report=html
```

---

## 🔄 CI/CD Integration

### Pre-commit Checks

```bash
# Run before committing
pytest tests/unit/ --cov=. --cov-fail-under=75
```

### CI Pipeline

```yaml
test:
  script:
    - pip install -r requirements.txt
    - pip install -r requirements-test.txt
    - pytest --cov=. --cov-report=xml --cov-fail-under=75
```

---

## 📚 Resources

### Documentation
- [pytest documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)

### Internal Resources
- Service README: `README.md` (to be created)
- API Documentation: `GET /openapi.json`
- Phase 3 Validation: `PHASE_3_VALIDATION.md`
- Phase 7 Deployment: `PHASE_7_DEPLOYMENT_VALIDATION.md`

---

## ✅ Testing Checklist

Before marking a feature complete:

- [ ] Unit tests written (one per behavior)
- [ ] Edge cases covered
- [ ] Error cases tested
- [ ] Coverage target met (80%+)
- [ ] Tests pass locally
- [ ] Tests documented in this guide
- [ ] CI pipeline passes

---

## 🎯 Next Steps

### Short Term (Phase 5 Completion)
1. ✅ Create testing infrastructure
2. ✅ Add infrastructure tests (93% config coverage)
3. ✅ Add application tests (71% coverage)
4. ✅ Add presentation tests (89%+ coverage)
5. ✅ Create testing guide (this document)
6. ⏳ Fix 9 failing tests (mocking issues)
7. ⏳ Achieve 80%+ overall coverage

### Medium Term (Phase 6)
1. Add integration tests
2. Add repository HTTP tests
3. Add cross-service workflow tests

### Long Term (Future)
1. Add E2E tests
2. Add performance benchmarks
3. Add security tests
4. Add contract tests

---

**Maintained by**: Development Team  
**Questions**: Contact service maintainers  
**Last Review**: October 10, 2025

