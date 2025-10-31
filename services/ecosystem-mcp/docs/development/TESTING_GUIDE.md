---
title: "🧪 ECOSYSTEM MCP - TESTING GUIDE"
service: "ecosystem-mcp"
category: "development"
tags: ['config', 'configuration', 'database', 'debugging', 'development', 'ingestion', 'llm', 'ollama', 'optimization', 'performance']
related: ['INDEX.md', 'architecture/OVERVIEW.md', 'CODE_REFERENCE.md', 'API_ENDPOINTS_COMPLETE.md']
status: "current"
last_updated: "2025-10-28"
audience: "developer"
difficulty: "beginner"
semantic_keywords: ['config', 'configuration', 'database', 'debugging', 'development']
llm_search_hints: ['what is 🧪 ecosystem mcp - testing guide', 'how does 🧪 ecosystem mcp - testing guide work', 'guide to 🧪 ecosystem mcp - testing guide']
---

# 🧪 ECOSYSTEM MCP - TESTING GUIDE

**Coverage Target**: 70-80%  
**Test Types**: Unit, Integration, Functional/E2E  
**Status**: ✅ Comprehensive Test Suite

---

## 📊 OVERVIEW

Comprehensive testing strategy for Ecosystem MCP Service with three test levels:

1. **Unit Tests** - Fast, isolated component tests
2. **Integration Tests** - Multi-component workflow tests
3. **Functional/E2E Tests** - Complete end-to-end scenarios

**Target Coverage**: 70-80% of codebase

---

## 🚀 QUICK START

### **Run All Tests**

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=src --cov-report=html

# Run specific test type
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m e2e           # E2E tests only
```

### **Run Tests in Parallel**

```bash
# Use multiple CPU cores
pytest -n auto
```

### **Run Specific Tests**

```bash
# Run specific file
pytest tests/unit/test_parser.py

# Run specific test
pytest tests/unit/test_parser.py::test_parse_markdown

# Run by pattern
pytest -k "test_parse"
```

---

## 📁 TEST STRUCTURE

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures
├── unit/                    # Unit tests (60% coverage target)
│   ├── test_parser.py
│   ├── test_normalizer.py
│   ├── test_metadata_extractor.py
│   ├── test_model_router.py
│   ├── test_query_routes.py
│   └── test_ollama_routes.py
├── integration/             # Integration tests (30% coverage target)
│   ├── test_ingestion_pipeline.py
│   └── test_api_endpoints.py
└── functional/              # E2E tests (10% coverage target)
    └── test_end_to_end.py
```

---

## 🎯 TEST COVERAGE

### **Current Coverage**

| Component | Target | Status |
|-----------|--------|--------|
| **Ingestion** | 80% | ✅ Complete |
| **API Routes** | 70% | ✅ Complete |
| **Model Router** | 75% | ✅ Complete |
| **Storage** | 70% | 🔄 In Progress |
| **Utilities** | 70% | 🔄 In Progress |
| **Overall** | 70-80% | 🎯 Target |

### **View Coverage Report**

```bash
# Generate HTML report
pytest --cov=src --cov-report=html

# Open in browser
open htmlcov/index.html
```

---

## 📝 WRITING TESTS

### **Unit Test Example**

```python
"""Unit tests for document parser."""

import pytest
from pathlib import Path
from src.ingestion.parser import DocumentParser


@pytest.fixture
def parser():
    """Create parser instance."""
    return DocumentParser()


def test_parse_markdown(parser, sample_markdown, tmp_path):
    """Test markdown parsing."""
    # Create temp file
    file_path = tmp_path / "test.md"
    file_path.write_text(sample_markdown)
    
    # Parse
    result = parser.parse(file_path)
    
    # Verify
    assert result["format"] == "markdown"
    assert result["content"] == sample_markdown
    assert "metadata" in result
```

### **Integration Test Example**

```python
"""Integration tests for full pipeline."""

import pytest
from src.ingestion.scanner import DocumentScanner
from src.ingestion.parser import DocumentParser
from src.ingestion.normalizer import DocumentNormalizer


def test_full_ingestion_flow(test_repo):
    """Test complete ingestion pipeline."""
    scanner = DocumentScanner(str(test_repo))
    parser = DocumentParser()
    normalizer = DocumentNormalizer()
    
    # Scan
    files = scanner.scan_all_supported()
    assert len(files) > 0
    
    # Process each file
    for file_path in files:
        parsed = parser.parse(file_path)
        normalized = normalizer.normalize(parsed)
        
        assert isinstance(normalized, str)
        assert len(normalized) > 0
```

### **E2E Test Example**

```python
"""End-to-end functional tests."""

import pytest
from httpx import AsyncClient


@pytest.mark.e2e
async def test_document_lifecycle(async_client):
    """Test complete document lifecycle."""
    # 1. Ingest document
    response = await async_client.post("/api/v1/admin/ingest", json={
        "mode": "quick"
    })
    assert response.status_code == 200
    
    # 2. Query for document
    response = await async_client.post("/api/v1/query/query", json={
        "service_name": "test-service",
        "limit": 10
    })
    assert response.status_code == 200
    
    documents = response.json()["documents"]
    assert len(documents) > 0
    
    # 3. Validate document
    doc_id = documents[0]["id"]
    response = await async_client.post(f"/api/v1/query/validate/{doc_id}")
    assert response.status_code == 200
```

---

## 🏷️ TEST MARKERS

Use markers to categorize tests:

```python
@pytest.mark.unit
def test_fast_operation():
    """Fast isolated test."""
    pass


@pytest.mark.integration
def test_multi_component():
    """Test multiple components."""
    pass


@pytest.mark.e2e
def test_full_workflow():
    """Test complete workflow."""
    pass


@pytest.mark.slow
def test_long_running():
    """Test that takes > 1 second."""
    pass


@pytest.mark.requires_ollama
def test_with_ollama():
    """Test that requires Ollama."""
    pass


@pytest.mark.requires_db
def test_with_database():
    """Test that requires PostgreSQL."""
    pass
```

### **Run by Marker**

```bash
# Run unit tests only
pytest -m unit

# Run integration tests
pytest -m integration

# Run E2E tests
pytest -m e2e

# Skip slow tests
pytest -m "not slow"

# Run tests that require Ollama
pytest -m requires_ollama
```

---

## 🔧 FIXTURES

### **Built-in Fixtures** (in `conftest.py`)

```python
@pytest.fixture
def sample_markdown():
    """Sample markdown content."""
    return """# Test Document
    
This is a test.
"""


@pytest.fixture
def sample_python():
    """Sample Python content."""
    return '''"""Module docstring."""

def hello():
    """Say hello."""
    return "Hello"
'''


@pytest.fixture
def test_repo(tmp_path):
    """Create test repository."""
    # Create test structure
    service_dir = tmp_path / "services" / "test-service"
    service_dir.mkdir(parents=True)
    
    (service_dir / "README.md").write_text("# Test")
    
    return tmp_path
```

---

## 📊 COVERAGE CONFIGURATION

### **pytest.ini**

```ini
[pytest]
testpaths = tests
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Slow tests
    requires_ollama: Requires Ollama
    requires_db: Requires PostgreSQL
    requires_redis: Requires Redis

addopts =
    -v
    --strict-markers
    --tb=short
    --cov=src
    --cov-report=term-missing
    --cov-report=html
    --cov-fail-under=70
```

### **Coverage Options**

```bash
# Terminal report with missing lines
pytest --cov=src --cov-report=term-missing

# HTML report
pytest --cov=src --cov-report=html

# XML report (for CI)
pytest --cov=src --cov-report=xml

# Fail if coverage below 70%
pytest --cov=src --cov-fail-under=70
```

---

## 🎯 TESTING BEST PRACTICES

### **1. Test Naming**

```python
# Good: Descriptive names
def test_parse_markdown_extracts_metadata():
    pass

def test_normalizer_handles_empty_content():
    pass

# Bad: Vague names
def test_parser():
    pass

def test_stuff():
    pass
```

### **2. Arrange-Act-Assert Pattern**

```python
def test_document_parsing():
    # Arrange: Set up test data
    parser = DocumentParser()
    file_path = Path("test.md")
    
    # Act: Perform action
    result = parser.parse(file_path)
    
    # Assert: Verify results
    assert result["format"] == "markdown"
```

### **3. One Assert Per Test (When Possible)**

```python
# Good: Focused test
def test_parser_returns_markdown_format():
    result = parser.parse(md_file)
    assert result["format"] == "markdown"

def test_parser_returns_content():
    result = parser.parse(md_file)
    assert result["content"] is not None

# Acceptable: Related assertions
def test_parser_result_structure():
    result = parser.parse(md_file)
    assert "format" in result
    assert "content" in result
    assert "metadata" in result
```

### **4. Use Fixtures for Shared Setup**

```python
@pytest.fixture
def parser():
    return DocumentParser()

@pytest.fixture
def sample_file(tmp_path):
    file_path = tmp_path / "test.md"
    file_path.write_text("# Test")
    return file_path

def test_with_fixtures(parser, sample_file):
    result = parser.parse(sample_file)
    assert result is not None
```

### **5. Test Edge Cases**

```python
def test_parser_handles_empty_file():
    """Test parser with empty file."""
    pass

def test_parser_handles_binary_file():
    """Test parser with binary file."""
    pass

def test_parser_handles_very_large_file():
    """Test parser with large file (>1MB)."""
    pass

def test_parser_handles_unicode():
    """Test parser with unicode characters."""
    pass
```

---

## 🚨 CONTINUOUS INTEGRATION

### **Run Tests in CI**

```bash
#!/bin/bash
# .github/workflows/test.yml

# Install dependencies
pip install -r requirements.txt

# Run tests with coverage
pytest --cov=src --cov-report=xml --cov-fail-under=70

# Upload coverage to Codecov (optional)
codecov --file coverage.xml
```

### **Pre-commit Hook**

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Run unit tests before commit
pytest -m unit

if [ $? -ne 0 ]; then
    echo "Unit tests failed. Commit aborted."
    exit 1
fi
```

---

## 📈 IMPROVING COVERAGE

### **Find Untested Code**

```bash
# Show missing lines
pytest --cov=src --cov-report=term-missing

# Generate HTML report for detailed view
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

### **Coverage By Module**

```bash
# Coverage for specific module
pytest --cov=src.ingestion --cov-report=term-missing

# Coverage for specific file
pytest --cov=src.ingestion.parser --cov-report=term-missing
```

---

## 🎬 DEMO TESTS

### **Run Demo Tests**

```bash
# Test document ingestion
pytest tests/integration/test_ingestion_pipeline.py -v

# Test API endpoints
pytest tests/integration/test_api_endpoints.py -v

# Test Ollama integration
pytest tests/unit/test_ollama_routes.py -v -m requires_ollama
```

---

## 🐛 DEBUGGING TESTS

### **Verbose Output**

```bash
# More verbose
pytest -v

# Even more verbose
pytest -vv

# Show print statements
pytest -s
```

### **Stop on First Failure**

```bash
# Stop at first failure
pytest -x

# Stop after N failures
pytest --maxfail=3
```

### **Run Last Failed Tests**

```bash
# Run only tests that failed last time
pytest --lf

# Run failed tests first, then others
pytest --ff
```

### **Debug with PDB**

```python
def test_something():
    result = complex_function()
    
    # Drop into debugger
    import pdb; pdb.set_trace()
    
    assert result == expected
```

---

## 📊 PERFORMANCE TESTING

### **Benchmark Tests**

```python
def test_parser_performance(benchmark):
    """Benchmark parser performance."""
    parser = DocumentParser()
    file_path = Path("large_file.md")
    
    result = benchmark(parser.parse, file_path)
    
    assert result is not None
```

```bash
# Run benchmark tests
pytest tests/ --benchmark-only
```

---

## ✅ CHECKLIST

Before considering tests complete:

- [ ] Unit tests cover all major functions
- [ ] Integration tests cover main workflows
- [ ] E2E tests cover critical user journeys
- [ ] Edge cases are tested
- [ ] Error handling is tested
- [ ] Coverage is 70%+
- [ ] All tests pass in CI
- [ ] Tests are well-documented
- [ ] Fixtures are reusable
- [ ] Tests are fast (< 1s for unit tests)

---

## 📚 ADDITIONAL RESOURCES

- [Pytest Documentation](https://docs.pytest.org/)
- [Coverage.py](https://coverage.readthedocs.io/)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)

---

**Status**: ✅ Comprehensive Test Suite  
**Coverage**: 70-80% Target  
**Test Count**: 20+ tests  
**Quality**: Production-Ready

