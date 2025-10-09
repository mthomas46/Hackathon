<!-- AI_READ_PRIORITY: 3 -->
<!-- AI_TAGS: configuration, code-analyzer, ports, profiles -->
<!-- AI_KEY_SECTIONS: Ports, Profiles, Validation -->

---
ai_metadata:
  purpose: service_configuration
  read_priority: 3
  context_level: service
  service: code-analyzer
  tags:
  - configuration
  - code-analyzer
  - ports
  - profiles
  when_to_read: Before running service, during deployment
  key_sections:
  - Ports & Networking
  - Configuration Profiles
  - Validation
  execution_relevance: operational
---

# code-analyzer Configuration

**Service**: code-analyzer  
**Version**: 1.0.0  
**Last Updated**: October 9, 2025  
**Status**: Production Ready

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Ports & Networking](#ports--networking)
3. [Credentials & Secrets](#credentials--secrets)
4. [Configuration Files](#configuration-files)
5. [Environment Variables](#environment-variables)
6. [Configuration Profiles](#configuration-profiles)
7. [Docker Configuration](#docker-configuration)
8. [Validation](#validation)
9. [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

The code-analyzer service provides static code analysis capabilities including:
- Structure extraction (functions, classes, methods)
- Complexity analysis (cyclomatic, cognitive, maintainability)
- Security scanning (code injection, unsafe deserialization)
- Style checking (PEP 8 compliance, line length)

**Configuration managed by**: [MASTER_CONFIGURATION_REGISTRY.md](../../docs/refactoring/MASTER_CONFIGURATION_REGISTRY.md)

**Self-Contained**: This service has no external dependencies and requires no credentials.

---

## 🌐 Ports & Networking

### Assigned Ports

| Port Type | Port Number | Purpose | External Access |
|-----------|-------------|---------|-----------------|
| HTTP | 6000 | REST API endpoints | Yes (via proxy) |
| Internal | 6001 | Inter-service communication | No |
| gRPC | - | Not used | No |
| Admin | - | Not used | No |

### Network Configuration

**Docker Network**: `hackathon_analysis`

**Service Discovery**:
- DNS Name: `code-analyzer`
- Internal URL: `http://code-analyzer:6000`
- External URL: `http://localhost:6000` (development)

### Health Check

**Endpoint**: `GET /health`  
**Expected Response**: `200 OK`

```bash
# Check service health
curl http://localhost:6000/health
```

**Response**:
```json
{
  "status": "healthy",
  "service": "code-analyzer",
  "version": "1.0.0",
  "timestamp": "2025-10-09T18:00:00Z"
}
```

---

## 🔑 Credentials & Secrets

**No credentials required** - This service is self-contained and does not require:
- API keys
- Database credentials
- External service credentials
- Authentication tokens

**Rationale**: code-analyzer operates entirely on provided code strings and uses only the Python AST module, which requires no external access.

---

## 📄 Configuration Files

### File Structure

```
code-analyzer/
├── .env                    # Environment variables (optional)
├── .env.template           # Template for .env
├── config.yaml             # Application configuration (future)
├── docker-compose.yml      # Docker Compose config (future)
├── Dockerfile              # Production image (future)
├── Dockerfile.dev          # Development image (future)
├── pytest.ini              # Test configuration
├── requirements.txt        # Production dependencies
├── requirements-test.txt   # Test dependencies
└── Makefile                # Common commands (future)
```

### pytest.ini

**Location**: `./pytest.ini`

```ini
[pytest]
python_files = test_*.py
python_classes = Test*
python_functions = test_*
testpaths = tests

addopts =
    --verbose
    --strict-markers
    --tb=short
    --cov=.
    --cov-report=term-missing
    --cov-report=html:htmlcov
    --cov-fail-under=80
    -ra

markers =
    unit: Unit tests (fast, isolated)
    integration: Integration tests (slower, with dependencies)
    e2e: End-to-end tests (slowest, full workflow)
    performance: Performance and load tests
    security: Security tests
    slow: Tests that take significant time
    workflow: Workflow tests (real-world usage scenarios)
    domain: Domain layer tests
    application: Application layer tests
    infrastructure: Infrastructure layer tests
    presentation: Presentation/API layer tests
```

### .env Template (Future)

**Location**: `./.env.template`

```bash
# Service: code-analyzer
# Copy to .env and fill in values

# === Core Configuration ===
SERVICE_NAME=code-analyzer
SERVICE_PORT=6000
LOG_LEVEL=info

# === Feature Flags ===
ENABLE_METRICS=true
ENABLE_TRACING=false
ENABLE_SWAGGER=true

# === Performance ===
WORKERS=4
TIMEOUT=30
```

---

## 🔧 Environment Variables

### Core Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SERVICE_NAME` | Service name | code-analyzer | No |
| `SERVICE_PORT` | HTTP port | 6000 | No |
| `LOG_LEVEL` | Logging level | `info` | No |
| `WORKERS` | Worker processes | `4` | No |

### Feature Flags

| Variable | Description | Default | Type |
|----------|-------------|---------|------|
| `ENABLE_METRICS` | Enable Prometheus metrics | `true` | Boolean |
| `ENABLE_TRACING` | Enable distributed tracing | `false` | Boolean |
| `ENABLE_SWAGGER` | Enable Swagger UI | `true` | Boolean |

### Performance Tuning

| Variable | Description | Default | Range |
|----------|-------------|---------|-------|
| `WORKERS` | Number of worker processes | `4` | 1-16 |
| `TIMEOUT` | Request timeout (seconds) | `30` | 10-300 |
| `MAX_CODE_SIZE` | Maximum code size (bytes) | `1048576` (1MB) | 1KB-10MB |

---

## 🎛️ Configuration Profiles

### Available Profiles

#### Development Profile

**Purpose**: Local development with debug features

**Activation**:
```bash
export PROFILE=development
python main.py
```

**Features**:
- Debug logging enabled
- Swagger UI accessible at `/docs`
- Hot reload enabled (if using uvicorn --reload)
- Sample/test data available
- Longer timeouts for debugging
- Detailed error messages

**Configuration**:
```yaml
profile: development
log_level: debug
features:
  - swagger_ui
  - debug_endpoints
  - sample_data
performance:
  workers: 2
  timeout: 300  # 5 minutes for debugging
  max_code_size: 10485760  # 10MB
```

#### Testing Profile

**Purpose**: Automated testing

**Activation**:
```bash
export PROFILE=testing
pytest tests/
```

**Features**:
- Minimal logging (errors only)
- In-memory processing
- Test fixtures enabled
- Fast timeouts
- Deterministic behavior

**Configuration**:
```yaml
profile: testing
log_level: error
features:
  - test_mode
  - fixtures
performance:
  workers: 1
  timeout: 10
  max_code_size: 524288  # 512KB
```

#### Production Profile

**Purpose**: Production deployment

**Activation**:
```bash
export PROFILE=production
docker-compose --profile prod up code-analyzer
```

**Features**:
- Optimized logging (info level)
- Metrics and tracing enabled
- Rate limiting
- Security hardening
- Performance optimized

**Configuration**:
```yaml
profile: production
log_level: info
features:
  - metrics
  - tracing
  - rate_limiting
  - security_headers
performance:
  workers: 4
  timeout: 30
  max_code_size: 1048576  # 1MB
```

---

## 🐳 Docker Configuration

### Dockerfile (Future)

**Location**: `./Dockerfile`

**Build**:
```bash
docker build -t code-analyzer:latest .
```

**Run**:
```bash
docker run -p 6000:6000 code-analyzer:latest
```

### Docker Compose (Future)

**Location**: `./docker-compose.yml`

**Run standalone**:
```bash
docker-compose up code-analyzer
```

**Run with ecosystem**:
```bash
# From root directory
docker-compose --profile analysis up
```

### Docker Profiles

| Profile | Purpose | Command |
|---------|---------|---------|
| `dev` | Development | `docker-compose --profile dev up` |
| `prod` | Production | `docker-compose --profile prod up` |
| `analysis` | Analysis services | `docker-compose --profile analysis up` |

---

## ✅ Validation

### Preflight Checks (Future)

Run validation before starting service:

```bash
# Validate all configuration
make validate-config

# Check port availability
make check-ports

# Validate Python syntax
make validate-syntax

# Run tests
make test
```

### Manual Validation

```bash
# Check port conflicts
python ../../scripts/validation/check_port_conflicts.py code-analyzer 6000

# Check if port is available
lsof -i :6000

# Validate pytest configuration
pytest --collect-only

# Run tests
pytest tests/ -v
```

### Health Checks

```bash
# Service health (future)
curl http://localhost:6000/health

# Service info (future)
curl http://localhost:6000/about-me

# Available endpoints (future)
curl http://localhost:6000/endpoints

# Service relationships (future)
curl http://localhost:6000/provider-consumer
```

---

## 🔧 Troubleshooting

### Common Issues

#### Port Already in Use

**Error**: `Address already in use: 6000`

**Solution**:
```bash
# Find process using port
lsof -i :6000

# Kill process (if safe)
kill -9 <PID>

# Or change port
export SERVICE_PORT=6010
```

#### Import Errors

**Error**: `ModuleNotFoundError: No module named 'domain'`

**Solution**:
```bash
# Ensure you're in service directory
cd services/code-analyzer

# Install dependencies
pip install -r requirements.txt

# Add service to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

#### Tests Failing

**Error**: Tests fail unexpectedly

**Steps**:
1. Check test dependencies: `pip install -r requirements-test.txt`
2. Clear cache: `pytest --cache-clear`
3. Run specific test: `pytest tests/unit/domain/test_code_analysis.py -v`
4. Check coverage: `pytest --cov=. --cov-report=html`
5. Review coverage report: `open htmlcov/index.html`

#### AST Parsing Errors

**Error**: `SyntaxError: invalid syntax`

**Solution**:
```python
# This is expected for invalid code
# code-analyzer gracefully handles syntax errors
# Check analysis.status == AnalysisStatus.FAILED

from domain.entities.code_analysis import CodeAnalysis
from domain.value_objects import Language

analysis = CodeAnalysis(
    code_content="def broken(:",  # Invalid syntax
    language=Language.PYTHON
)
analysis.start_analysis()

# Result: analysis.status will be FAILED
# analysis.error will contain the syntax error message
```

### Debug Mode

**Enable debug logging**:
```bash
export LOG_LEVEL=debug
python main.py  # When main.py exists
```

**Or in tests**:
```bash
pytest tests/ -v --log-cli-level=DEBUG
```

### Performance Issues

**Symptom**: Analysis takes too long

**Solutions**:
1. Check code size: `len(code_content)` should be < 1MB
2. Reduce complexity: Break large files into smaller functions
3. Disable features: Set `options.include_complexity=False` to skip expensive calculations
4. Increase timeout: `export TIMEOUT=60`

---

## 📚 Related Documentation

- [Service README](./README.md) - Complete service documentation
- [Master Configuration Registry](../../docs/refactoring/MASTER_CONFIGURATION_REGISTRY.md) - Ecosystem configuration
- [Test Documentation](./tests/README.md) - Test suite details
- [Domain Model](./design/domain_model.md) - DDD architecture
- [OpenAPI Specification](./design/openapi_v2.yaml) - API documentation

---

## 📊 Current Configuration Status

**Ports**: ✅ Allocated (6000, 6001)  
**Credentials**: ✅ None required  
**Profiles**: ✅ Defined (dev, test, prod)  
**Docker**: ⏸️ Future (Dockerfile pending)  
**Validation**: ⏸️ Future (Makefile pending)  
**Deployment**: ⏸️ Future (Phase 6)

---

**Last Updated**: October 9, 2025  
**Maintained by**: Hackathon Team  
**Questions?**: See [Troubleshooting](#troubleshooting) or consult [README.md](./README.md)

