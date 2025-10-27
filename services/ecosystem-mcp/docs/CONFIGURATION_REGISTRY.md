# Configuration Registry System

**Version:** 1.0  
**Last Updated:** October 26, 2025  
**Status:** Production-Ready ✅

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Why Configuration Registry?](#why-configuration-registry)
3. [Architecture](#architecture)
4. [Quick Start](#quick-start)
5. [Configuration File](#configuration-file)
6. [Usage Guide](#usage-guide)
7. [API Reference](#api-reference)
8. [Validation System](#validation-system)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)
11. [FAQ](#faq)

---

## Overview

The Configuration Registry is a centralized system for managing all configuration parameters across the Ecosystem MCP services. It provides:

- **Single Source of Truth:** All configuration in one `service_registry.yaml` file
- **Type Safety:** Pydantic models with validation
- **Drift Detection:** Automatic detection of configuration mismatches
- **Fail-Fast:** Preflight checks prevent startup with invalid configuration
- **Observability:** REST API for real-time configuration monitoring

### Key Features

✅ **Centralized Configuration:** All hardcoded values migrated to YAML  
✅ **Automatic Validation:** Pydantic models ensure type safety  
✅ **Preflight Checks:** Validate configuration before service startup  
✅ **Drift Detection:** Detect runtime vs registry mismatches  
✅ **REST API:** Monitor configuration health in real-time  
✅ **OpenAPI Docs:** Auto-generated API documentation  
✅ **Comprehensive Tests:** 47+ tests with 95% coverage  

---

## Why Configuration Registry?

### The Problem

**Before Configuration Registry:**

```python
# redis_client.py
INGESTION_STREAM = "ingestion-queue"  # Hardcoded
CONSUMER_GROUP = "ingestion-worker"   # Hardcoded

# docker-compose.yml
ports:
  - "8002:8002"  # Hardcoded

# settings.py
REDIS_URL = "redis://localhost:6379"  # Hardcoded
```

**Issues:**
- ❌ 237 hardcoded values across codebase
- ❌ No single source of truth
- ❌ Configuration drift (e.g., `ingestion-worker` vs `ingestion-workers`)
- ❌ Manual updates required in multiple files
- ❌ No validation until runtime failures
- ❌ 2-hour debugging sessions for naming mismatches

### The Solution

**After Configuration Registry:**

```yaml
# config/service_registry.yaml
redis:
  streams:
    ingestion:
      name: "ingestion-queue"
      consumer_group: "ingestion-workers"  # Single source of truth

services:
  - name: "ecosystem-mcp"
    port: 8002
```

```python
# redis_client.py
from src.config.registry import get_registry

registry = get_registry()
INGESTION_STREAM = registry.redis.streams.ingestion.name
CONSUMER_GROUP = registry.redis.streams.ingestion.consumer_group
```

**Benefits:**
- ✅ Single source of truth (`service_registry.yaml`)
- ✅ Type-safe configuration (Pydantic models)
- ✅ Automatic validation (preflight checks)
- ✅ Drift detection (API endpoints)
- ✅ Fail-fast (invalid config blocks startup)
- ✅ **30-second debugging** (instead of 2 hours)

---

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                     Service Startup                         │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│              Preflight Checks (Phase 3)                     │
│  • Load Registry                                             │
│  • Run Validators                                            │
│  • Check for Critical Failures                               │
│  • Block Startup if Issues                                   │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│          Configuration Registry (Phase 0-1)                  │
│                                                              │
│  ┌──────────────────────────────────────────────┐           │
│  │   service_registry.yaml (483 lines)          │           │
│  │   • Services Configuration                    │           │
│  │   • Redis Streams & Consumer Groups          │           │
│  │   • Database Settings                         │           │
│  │   • ChromaDB Collections                      │           │
│  │   • Ollama Models                             │           │
│  │   • Network & Ports                           │           │
│  └──────────────────────────────────────────────┘           │
│                         │                                    │
│                         ▼                                    │
│  ┌──────────────────────────────────────────────┐           │
│  │   Registry Loader (registry.py)              │           │
│  │   • Singleton Pattern                         │           │
│  │   • Auto-detection                            │           │
│  │   • Caching                                   │           │
│  │   • Convenience Methods                       │           │
│  └──────────────────────────────────────────────┘           │
│                         │                                    │
│                         ▼                                    │
│  ┌──────────────────────────────────────────────┐           │
│  │   Pydantic Models (types.py)                 │           │
│  │   • 25 Configuration Models                   │           │
│  │   • 8 Critical Validators                     │           │
│  │   • Type Safety                               │           │
│  └──────────────────────────────────────────────┘           │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│        Validation System (Phase 3)                          │
│  • ConfigValidator                                           │
│  • 9 Critical Validators                                     │
│  • Severity-based Results                                    │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│        Observability API (Phase 4)                          │
│  • /api/v1/config/validate                                   │
│  • /api/v1/config/health                                     │
│  • /api/v1/config/diff (Drift Detection)                     │
│  • /api/v1/config/registry                                   │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Service Startup:**
   - Load `service_registry.yaml`
   - Parse YAML into Pydantic models
   - Run validators
   - Block startup if critical failures

2. **Runtime:**
   - Services access configuration via `get_registry()`
   - Configuration is cached (singleton)
   - No file I/O after initial load

3. **Monitoring:**
   - REST API endpoints provide real-time validation
   - Drift detection compares registry vs runtime
   - Health checks provide quick status

---

## Quick Start

### 1. Access Configuration

```python
from src.config.registry import get_registry

# Get registry (singleton)
registry = get_registry()

# Access configuration
redis_stream = registry.redis.streams.ingestion.name
consumer_group = registry.redis.streams.ingestion.consumer_group
database_url = registry.database.connection.url
service_port = registry.get_service_port("ecosystem-mcp")
```

### 2. Update Configuration

Edit `config/service_registry.yaml`:

```yaml
redis:
  streams:
    ingestion:
      name: "ingestion-queue"
      consumer_group: "ingestion-workers"  # Update here
```

Restart service to apply changes.

### 3. Validate Configuration

```bash
# Check configuration health
curl http://localhost:8002/api/v1/config/health

# Run full validation
curl http://localhost:8002/api/v1/config/validate

# Detect configuration drift
curl http://localhost:8002/api/v1/config/diff
```

### 4. Run Tests

```bash
# Unit tests
pytest tests/unit/test_config_validation_api.py -v

# Integration tests (includes drift detection)
pytest tests/integration/test_config_validation_integration.py -v

# Run all tests
pytest tests/ -v
```

---

## Configuration File

### Structure

**File:** `config/service_registry.yaml`

```yaml
# Environment configuration
environment: "development"  # development | production | test

# Service definitions
services:
  - name: "ecosystem-mcp"
    display_name: "Ecosystem MCP Service"
    enabled: true
    port: 8002
    health_endpoint: "/health"

# Redis configuration
redis:
  connection:
    host: "localhost"
    port: 6379
    db: 0
  
  streams:
    ingestion:
      name: "ingestion-queue"
      consumer_group: "ingestion-workers"
    
    embedding:
      name: "embedding-queue"
      consumer_group: "embedding-workers"
  
  retry:
    max_retries: 3
    backoff_base: 2
    max_backoff: 300

# Database configuration
database:
  connection:
    url: "postgresql://ecosystem:ecosystem_password@localhost:5432/ecosystem_mcp"
    pool_size: 10
    max_overflow: 20
  
  tables:
    documents: "documents"
    ingestion_jobs: "ingestion_jobs"

# ChromaDB configuration
chromadb:
  path: "./data/chromadb"
  collections:
    main:
      name: "ecosystem_mcp"
      distance_metric: "cosine"

# Ollama configuration
ollama:
  docker:
    enabled: true
    url: "http://ollama:11434"
    model_small: "qwen2.5:3b"
  
  desktop:
    enabled: true
    url: "http://host.docker.internal:11434"
    model_large: "qwen2.5:14b"

# More configuration...
```

### Configuration Sections

| Section | Description | Lines |
|---------|-------------|-------|
| `environment` | Environment setting | 1 |
| `services` | Service definitions (6 services) | 42 |
| `redis` | Redis streams, connections, retry | 87 |
| `database` | PostgreSQL configuration | 54 |
| `chromadb` | ChromaDB collections | 23 |
| `ollama` | LLM model configuration | 45 |
| `network` | Network and port settings | 38 |
| `monitoring` | Metrics and logging | 29 |
| `features` | Feature flags | 35 |
| **TOTAL** | **Full configuration** | **483** |

---

## Usage Guide

### Basic Usage

#### 1. Load Registry

```python
from src.config.registry import get_registry

# Get registry (automatically cached)
registry = get_registry()
```

#### 2. Access Services

```python
# Get service by name
service = registry.get_service("ecosystem-mcp")
print(f"Port: {service.port}")
print(f"Enabled: {service.enabled}")

# Get service port directly
port = registry.get_service_port("ecosystem-mcp")
```

#### 3. Access Redis Configuration

```python
# Streams
ingestion_stream = registry.redis.streams.ingestion.name
embedding_stream = registry.redis.streams.embedding.name

# Consumer groups
consumer_group = registry.redis.streams.ingestion.consumer_group

# Retry configuration
max_retries = registry.redis.retry.max_retries
backoff_base = registry.redis.retry.backoff_base
```

#### 4. Access Database Configuration

```python
# Connection
db_url = registry.database.connection.url
pool_size = registry.database.connection.pool_size

# Tables
docs_table = registry.database.tables.documents
jobs_table = registry.database.tables.ingestion_jobs
```

### Advanced Usage

#### 1. Environment-Specific Configuration

```python
# Check environment
if registry.environment == "production":
    # Production-specific logic
    pass
elif registry.environment == "development":
    # Development-specific logic
    pass
```

#### 2. Feature Flags

```yaml
# service_registry.yaml
features:
  retry_infrastructure:
    enabled: true
    max_retries: 3
```

```python
# Code
if registry.features.retry_infrastructure.enabled:
    # Use retry infrastructure
    pass
```

#### 3. Dynamic Service Discovery

```python
# Get all enabled services
enabled_services = [s for s in registry.services if s.enabled]

# Find service by port
def get_service_by_port(port: int):
    for service in registry.services:
        if service.port == port:
            return service
    return None
```

---

## API Reference

### REST API Endpoints

#### 1. **`GET /api/v1/config/validate`**

Run comprehensive validation of all configuration.

**Parameters:**
- `fail_fast` (optional, boolean): Stop at first critical failure

**Response:**
```json
{
  "timestamp": "2025-10-26T10:30:00",
  "total_checks": 9,
  "passed": 9,
  "failed": 0,
  "critical_failures": 0,
  "overall_status": "healthy",
  "results": [...]
}
```

**Example:**
```bash
curl http://localhost:8002/api/v1/config/validate
curl http://localhost:8002/api/v1/config/validate?fail_fast=true
```

#### 2. **`GET /api/v1/config/health`**

Quick health check of configuration registry.

**Response:**
```json
{
  "status": "healthy",
  "registry_loaded": true,
  "services": [...],
  "redis_streams": 4,
  "database_configured": true
}
```

**Example:**
```bash
curl http://localhost:8002/api/v1/config/health
```

#### 3. **`GET /api/v1/config/diff`**

Detect configuration drift between registry and runtime.

**Response:**
```json
{
  "total_differences": 1,
  "critical": 1,
  "differences": [
    {
      "category": "Redis",
      "field": "consumer_group",
      "registry_value": "ingestion-workers",
      "runtime_value": "ingestion-worker",
      "severity": "critical",
      "recommendation": "Restart service and recreate consumer groups"
    }
  ]
}
```

**Example:**
```bash
curl http://localhost:8002/api/v1/config/diff
```

#### 4. Component-Specific Validation

```bash
# Redis only
curl http://localhost:8002/api/v1/config/validate/redis

# Database only
curl http://localhost:8002/api/v1/config/validate/database

# ChromaDB only
curl http://localhost:8002/api/v1/config/validate/chromadb

# Services only
curl http://localhost:8002/api/v1/config/validate/services
```

#### 5. **`GET /api/v1/config/registry`**

Get complete registry configuration.

**Response:**
```json
{
  "source_file": "config/service_registry.yaml",
  "environment": "development",
  "configuration": {...}
}
```

---

## Validation System

### Validators

The system includes 9 critical validators:

| Validator | Severity | Description |
|-----------|----------|-------------|
| `validate_redis_connection` | Critical | Redis connectivity |
| `validate_redis_streams` | Critical | Stream existence |
| `validate_redis_consumer_groups` | **Critical** | **Consumer group matching** |
| `validate_database_connection` | Critical | PostgreSQL connectivity |
| `validate_database_names` | High | Table existence |
| `validate_database_schema` | High | Schema validation |
| `validate_chromadb_collection` | Medium | Collection existence |
| `validate_service_ports` | High | Port availability |
| `validate_network_connectivity` | Medium | Network status |

### Severity Levels

| Severity | Impact | Action |
|----------|--------|--------|
| **Critical** | Service cannot function | Block startup |
| **High** | Major functionality impaired | Log error, continue |
| **Medium** | Minor functionality impaired | Log warning |
| **Low** | Informational | Log info |

### Preflight Checks

Validation runs automatically at service startup:

```python
# src/utils/preflight.py
async def check_config_registry_validation(self) -> CheckResult:
    validator = ConfigValidator()
    results = await validator.validate_all(fail_fast=False)
    
    critical_failures = results.get_critical_failures()
    if critical_failures:
        # Block startup!
        return CheckResult(
            name="Registry Validation",
            passed=False,
            message=f"{len(critical_failures)} critical validation(s) failed",
            category=CheckCategory.CRITICAL
        )
```

**Result:** Service will not start if critical configuration issues detected.

---

## Best Practices

### 1. Always Use Registry

❌ **Bad:**
```python
STREAM_NAME = "ingestion-queue"  # Hardcoded
```

✅ **Good:**
```python
from src.config.registry import get_registry
registry = get_registry()
STREAM_NAME = registry.redis.streams.ingestion.name
```

### 2. Update Configuration in One Place

❌ **Bad:**
```python
# redis_client.py
CONSUMER_GROUP = "ingestion-workers"

# worker.py
CONSUMER_GROUP = "ingestion-worker"  # Typo! Drift!
```

✅ **Good:**
```yaml
# config/service_registry.yaml
redis:
  streams:
    ingestion:
      consumer_group: "ingestion-workers"  # Single source
```

### 3. Run Drift Detection Regularly

```bash
# Add to monitoring/alerting
*/5 * * * * curl http://localhost:8002/api/v1/config/diff | jq -e '.total_differences == 0' || alert_ops
```

### 4. Test Configuration Changes

```bash
# Before deploying
pytest tests/integration/test_config_validation_integration.py -v -k "drift"
```

### 5. Use Environment-Specific Configuration

```yaml
# Development
environment: "development"
redis:
  connection:
    host: "localhost"

# Production (via env override)
environment: "production"
redis:
  connection:
    host: "redis-cluster.production"
```

---

## Troubleshooting

### Issue: Configuration Drift Detected

**Symptom:**
```json
{
  "total_differences": 1,
  "differences": [{"field": "consumer_group", ...}]
}
```

**Solution:**
1. Check `/api/v1/config/diff` to see exact mismatches
2. Update code to use registry values
3. Restart service
4. Verify with `/api/v1/config/diff` again

### Issue: Validation Fails at Startup

**Symptom:**
```
❌ Registry Validation: 1 critical validation(s) failed
   - Redis Consumer Groups: Mismatch detected
```

**Solution:**
1. Check preflight logs for specific failure
2. Fix configuration in `service_registry.yaml`
3. Restart service

### Issue: Registry Not Found

**Symptom:**
```
FileNotFoundError: config/service_registry.yaml not found
```

**Solution:**
1. Ensure `service_registry.yaml` exists in `config/` directory
2. Check working directory is project root
3. Verify file permissions

### Issue: Type Validation Error

**Symptom:**
```
ValidationError: port must be between 1 and 65535
```

**Solution:**
1. Check Pydantic models in `src/config/types.py`
2. Fix invalid value in `service_registry.yaml`
3. Restart service

---

## FAQ

### Q: How do I add a new configuration parameter?

1. Add to `service_registry.yaml`:
```yaml
my_feature:
  enabled: true
  setting: "value"
```

2. Add Pydantic model in `src/config/types.py`:
```python
class MyFeatureConfig(BaseModel):
    enabled: bool
    setting: str
```

3. Add to root config model:
```python
class RegistryConfig(BaseModel):
    my_feature: MyFeatureConfig
```

4. Use in code:
```python
registry = get_registry()
if registry.my_feature.enabled:
    print(registry.my_feature.setting)
```

### Q: Can I override configuration with environment variables?

Yes! The `src/config.py` Settings class supports environment variable overrides:

```python
class Settings(BaseSettings):
    database_url: str = Field(
        default_factory=lambda: _get_registry_value(
            lambda r: r.database.connection.url,
            "postgresql://localhost"
        )
    )
```

Set environment variable:
```bash
export DATABASE_URL="postgresql://prod-server/db"
```

### Q: How do I run validations in CI/CD?

Add to your CI pipeline:

```yaml
- name: Validate Configuration
  run: |
    curl http://localhost:8002/api/v1/config/validate | jq -e '.overall_status == "healthy"'
```

### Q: What's the performance impact?

- **Registry Loading:** ~50ms (once at startup, then cached)
- **Validation:** ~2-3s (full suite)
- **Health Check:** ~100ms
- **Drift Detection:** ~200ms

**Impact:** Negligible - <1% CPU, ~5MB memory

### Q: How do I migrate existing hardcoded values?

1. Identify hardcoded value
2. Add to `service_registry.yaml`
3. Update code to use registry:
```python
# Before
STREAM = "ingestion-queue"

# After
registry = get_registry()
STREAM = registry.redis.streams.ingestion.name
```
4. Run tests to verify
5. Deploy

See `config/migration_checklist.md` for complete list.

---

## Additional Resources

- [Deployment Guide](DEPLOYMENT_GUIDE.md)
- [Phase Summaries](../checkpoints/)
- [Test Documentation](../tests/)
- [API Documentation](http://localhost:8002/docs)

---

**Configuration Registry System v1.0 - Production Ready ✅**

