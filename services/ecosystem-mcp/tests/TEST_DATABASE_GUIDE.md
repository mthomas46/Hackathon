# Test Database Guide

**Date:** October 23, 2025  
**Status:** Production-Ready Test Infrastructure  
**Coverage:** Isolated PostgreSQL, Redis, and ChromaDB for testing

---

## 🎯 Overview

This guide covers the test database infrastructure for running integration and E2E tests against isolated database containers.

## 🏗️ Architecture

```
┌─────────────────────────────────────┐
│   Test Infrastructure               │
├─────────────────────────────────────┤
│                                     │
│  ┌──────────────────────────────┐  │
│  │ PostgreSQL Test (Port 5433)  │  │
│  │  • In-memory (tmpfs)         │  │
│  │  • Fast performance          │  │
│  │  • Auto-cleanup              │  │
│  └──────────────────────────────┘  │
│                                     │
│  ┌──────────────────────────────┐  │
│  │ Redis Test (Port 6380)       │  │
│  │  • In-memory cache           │  │
│  │  • No persistence            │  │
│  └──────────────────────────────┘  │
│                                     │
│  ┌──────────────────────────────┐  │
│  │ ChromaDB Test (Port 8001)    │  │
│  │  • Vector store tests        │  │
│  │  • Optional                  │  │
│  └──────────────────────────────┘  │
│                                     │
└─────────────────────────────────────┘
```

## 🚀 Quick Start

### 1. Start Test Database

```bash
# Using helper script (recommended)
./scripts/test-db.sh start

# Or directly with docker-compose
docker-compose -f docker-compose.test.yml up -d
```

### 2. Verify Status

```bash
./scripts/test-db.sh status
```

Expected output:
```
✅ PostgreSQL: Healthy
✅ Redis: Healthy
✅ ChromaDB: Running
```

### 3. Run Tests

```bash
# Run all tests
pytest tests/

# Run only integration tests
pytest tests/integration/ -v

# Run with test database check
pytest tests/ --check-test-db
```

## 📋 Management Commands

### Start/Stop

```bash
# Start
./scripts/test-db.sh start

# Stop
./scripts/test-db.sh stop

# Restart
./scripts/test-db.sh restart
```

### Reset Database

```bash
# Clean all data (truncate tables, flush cache)
./scripts/test-db.sh clean

# Complete reset (destroy and recreate)
./scripts/test-db.sh reset
```

### Access Database

```bash
# PostgreSQL CLI
./scripts/test-db.sh psql

# Redis CLI
./scripts/test-db.sh redis
```

### Monitoring

```bash
# View logs
./scripts/test-db.sh logs

# Check status
./scripts/test-db.sh status
```

## 🔧 Configuration

### Connection Strings

```bash
# PostgreSQL
postgresql://test_user:test_password@localhost:5433/ecosystem_mcp_test

# Redis
redis://localhost:6380/0

# ChromaDB
http://localhost:8001
```

### Environment Variables

Create `.env.test` or set in your environment:

```bash
# Database
export DATABASE_URL="postgresql://test_user:test_password@localhost:5433/ecosystem_mcp_test"
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5433

# Redis
export REDIS_URL="redis://localhost:6380/0"
export REDIS_HOST=localhost
export REDIS_PORT=6380

# Test mode
export TEST_MODE=true
export TESTING=true
```

## 🧪 Writing Tests

### Integration Test Example

```python
import pytest
from fastapi.testclient import TestClient

@pytest.mark.integration
async def test_with_database(db_session):
    """Test that uses real database."""
    # Your test code here
    result = await some_database_operation()
    assert result is not None
```

### Using Fixtures

```python
@pytest.mark.integration
async def test_with_clean_db(db_session, clean_database):
    """Test with completely clean database."""
    # Database is truncated before this test
    pass

async def test_with_redis(redis_client):
    """Test with Redis."""
    await redis_client.set("key", "value")
    assert await redis_client.get("key") == "value"
```

## 🎯 Best Practices

### 1. Always Use Test Database

✅ **DO:**
```bash
# Start test database
./scripts/test-db.sh start

# Run tests
pytest tests/integration/
```

❌ **DON'T:**
```bash
# Don't test against production database!
DATABASE_URL=postgresql://prod/... pytest
```

### 2. Clean Between Test Runs

```bash
# Clean data but keep schema
./scripts/test-db.sh clean

# Full reset
./scripts/test-db.sh reset
```

### 3. Use Transactions

Tests automatically roll back transactions via `db_session` fixture:

```python
@pytest.mark.integration
async def test_creates_record(db_session):
    # Create record in transaction
    record = await create_record(db_session)
    
    # Test logic here
    
    # Automatic rollback after test
    # Record won't exist in next test
```

### 4. Skip If Database Unavailable

Pytest automatically skips integration tests if database isn't running:

```bash
# Tests will be skipped with helpful message
pytest tests/integration/

# Output:
# SKIPPED: Test database not running 
#          (use ./scripts/test-db.sh start)
```

## 🔄 CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Start test database
        run: |
          cd services/ecosystem-mcp
          docker-compose -f docker-compose.test.yml up -d
          sleep 10  # Wait for healthy
      
      - name: Run tests
        run: |
          cd services/ecosystem-mcp
          source venv/bin/activate
          pytest tests/ -v --cov
      
      - name: Stop test database
        run: |
          cd services/ecosystem-mcp
          docker-compose -f docker-compose.test.yml down
```

## ⚡ Performance Optimizations

The test database is optimized for speed:

1. **tmpfs** - All data in memory (no disk I/O)
2. **fsync disabled** - No disk synchronization
3. **No persistence** - Redis doesn't save to disk
4. **Fast healthchecks** - 5s intervals
5. **Minimal logging** - Only 5MB, 1 file

Result: **~10x faster** than production database!

## 🐛 Troubleshooting

### Database Won't Start

```bash
# Check port conflicts
lsof -i :5433
lsof -i :6380

# Stop conflicting services
./scripts/test-db.sh stop

# Reset completely
./scripts/test-db.sh reset
```

### Tests Can't Connect

```bash
# Verify database is healthy
./scripts/test-db.sh status

# Check connection
./scripts/test-db.sh psql
```

### Permission Errors

```bash
# Ensure script is executable
chmod +x scripts/test-db.sh

# Run with proper permissions
docker-compose -f docker-compose.test.yml up -d
```

## 📊 Test Database Schema

Schema is automatically created from migrations:

```bash
# Initialize schema
./scripts/test-db.sh init

# Or manually run migrations
export DATABASE_URL="postgresql://test_user:test_password@localhost:5433/ecosystem_mcp_test"
python -m src.storage.migrations.run_migrations
```

## 🎉 Benefits

1. ✅ **Isolated** - No impact on dev/prod
2. ✅ **Fast** - In-memory, optimized settings
3. ✅ **Reproducible** - Same setup everywhere
4. ✅ **Clean** - Easy reset between runs
5. ✅ **Parallel** - Multiple developers can test
6. ✅ **CI/CD Ready** - Works in automation

---

## 📚 Additional Resources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [PostgreSQL Testing Best Practices](https://www.postgresql.org/docs/current/regress.html)
- [pytest-asyncio Documentation](https://pytest-asyncio.readthedocs.io/)
- [Integration Testing Guide](./README.md)

---

**Last Updated:** October 23, 2025  
**Maintainer:** Ecosystem MCP Team

