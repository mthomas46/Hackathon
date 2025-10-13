# Infrastructure Protections & Circuit Breakers

## Summary

Added comprehensive infrastructure protections to prevent cascading failures and provide clear diagnostics for infrastructure issues.

## What Was Added

### 1. Enhanced Preflight Checks ✅

**File**: `src/utils/preflight.py`

**Enhancements**:
- ✅ **Database Existence Validation**: Verifies correct database is connected
- ✅ **Schema Validation**: Checks if tables exist
- ✅ **Specific Error Detection**: Detects "database does not exist" vs "connection refused"
- ✅ **Actionable Suggestions**: Provides exact commands to fix issues

**Example Output**:
```
❌ PostgreSQL: Database does not exist: FATAL database "ecosystem" does not exist
   Suggestion: Create database: docker exec <postgres-container> psql -U <user> -c 'CREATE DATABASE ecosystem_mcp;'
```

### 2. Circuit Breaker Pattern ✅

**File**: `src/utils/circuit_breaker.py`

**Features**:
- **States**: CLOSED → OPEN → HALF_OPEN → CLOSED
- **Automatic Recovery**: Tests if service recovered after timeout
- **Fail Fast**: Prevents wasting time on known-bad connections
- **Statistics Tracking**: Tracks failures, successes, state transitions

**How It Works**:
```python
# Create circuit breaker
breaker = CircuitBreaker(
    name="database",
    failure_threshold=5,      # Open after 5 failures
    success_threshold=2,      # Close after 2 successes
    timeout=30.0              # Try again after 30 seconds
)

# Use as decorator
@breaker
async def query_database():
    return await db.query()
```

**States**:
1. **CLOSED** (Normal): All requests go through
2. **OPEN** (Failing): Fail fast without trying (saves time)
3. **HALF_OPEN** (Testing): Testing if service recovered

### 3. Infrastructure Health Monitoring ✅

**File**: `src/api/routes/infrastructure.py`

**New Endpoints**:

#### GET `/api/v1/infrastructure/health`
Detailed health status of all components:
```json
{
  "status": "healthy",
  "components": {
    "database": {
      "status": "healthy",
      "type": "postgresql",
      "pool_size": 20
    },
    "redis": {
      "status": "healthy",
      "connected_clients": 3
    },
    "chromadb": {
      "status": "healthy",
      "collections": 1
    }
  },
  "circuit_breakers": {
    "database": {
      "state": "closed",
      "total_failures": 0,
      "total_successes": 127
    }
  }
}
```

#### GET `/api/v1/infrastructure/diagnostics`
Comprehensive diagnostics for troubleshooting:
```json
{
  "database": {
    "healthy": true,
    "host": "localhost",
    "port": 5432,
    "database": "ecosystem_mcp",
    "tables": 8
  },
  "redis": {
    "healthy": true,
    "version": "7.2.4",
    "used_memory_human": "1.2M"
  },
  "chromadb": {
    "healthy": true,
    "collection_count": 1,
    "total_documents": 45
  },
  "recommendations": [
    {
      "component": "all",
      "issue": "none",
      "actions": ["All systems operational ✅"]
    }
  ]
}
```

#### POST `/api/v1/infrastructure/circuit-breakers/{name}/reset`
Manually reset a circuit breaker:
```bash
curl -X POST http://localhost:8000/api/v1/infrastructure/circuit-breakers/database/reset
```

### 4. Database Circuit Breaker Integration ✅

**File**: `src/storage/database.py`

**Changes**:
- Added circuit breaker to `health_check()` method
- Prevents repeated failed connection attempts
- Graceful degradation when database is down

**Before**:
```python
async def health_check():
    # Always tries, even if database is known to be down
    await db.query("SELECT 1")
```

**After**:
```python
@_db_breaker  # Circuit breaker protection
async def health_check():
    # Fails fast if circuit is open
    await db.query("SELECT 1")
```

## How It Protects Against Your Issue

### The Issue You Experienced:
```
FATAL: database "ecosystem" does not exist
```
Repeated every 10 seconds, flooding logs.

### How Protections Help:

1. **Preflight Checks** (Startup):
   ```
   ❌ PostgreSQL: Database does not exist
   Suggestion: docker exec ecosystem-mcp-postgres psql -U ecosystem -c 'CREATE DATABASE ecosystem;'
   ```
   - Detects issue at startup
   - Provides exact fix command
   - Service won't start with broken config

2. **Circuit Breaker** (Runtime):
   ```
   ⚠️ Circuit breaker 'database': CLOSED → OPEN (5 consecutive failures)
   ```
   - After 5 failures, stops trying
   - Waits 30 seconds before testing recovery
   - Prevents log spam

3. **Health Monitoring** (Diagnostics):
   ```bash
   curl http://localhost:8000/api/v1/infrastructure/diagnostics
   ```
   - Shows exactly what's wrong
   - Provides actionable recommendations
   - No need to dig through logs

## Usage Examples

### 1. Check Infrastructure Health
```bash
curl http://localhost:8000/api/v1/infrastructure/health
```

### 2. Get Detailed Diagnostics
```bash
curl http://localhost:8000/api/v1/infrastructure/diagnostics
```

### 3. Check Circuit Breaker Status
```bash
curl http://localhost:8000/api/v1/infrastructure/circuit-breakers
```

### 4. Reset a Circuit Breaker
```bash
curl -X POST http://localhost:8000/api/v1/infrastructure/circuit-breakers/database/reset
```

### 5. Monitor Circuit Breakers in Real-Time
```bash
watch -n 1 'curl -s http://localhost:8000/api/v1/infrastructure/circuit-breakers | jq'
```

## Configuration

### Circuit Breaker Settings

**Database**:
- Failure Threshold: 5 consecutive failures
- Timeout: 30 seconds before retry
- Success Threshold: 2 successes to close

**Customize**:
```python
from src.utils.circuit_breaker import get_circuit_breaker

breaker = get_circuit_breaker(
    name="my_service",
    failure_threshold=10,  # More tolerant
    timeout=60.0           # Wait longer
)
```

### Preflight Check Modes

**Strict Mode** (Default):
```bash
PREFLIGHT_MODE=strict python -m src.server
# Fails fast if critical checks fail
```

**Lenient Mode** (Development):
```bash
PREFLIGHT_MODE=lenient python -m src.server
# Warns but continues anyway
```

## Benefits

### 1. Fail Fast
- Detect issues at startup, not at runtime
- Clear error messages with suggestions
- No mystery failures

### 2. Prevent Cascading Failures
- Circuit breakers stop repeated failures
- Graceful degradation
- Automatic recovery testing

### 3. Clear Diagnostics
- Detailed health status
- Actionable recommendations
- No log diving required

### 4. Production Ready
- Monitors circuit breaker state
- Tracks failure rates
- Manual override capability

## Testing

### Test Preflight Checks
```bash
# Stop PostgreSQL
docker stop ecosystem-mcp-postgres

# Start service - will fail with clear message
python -m src.server
```

### Test Circuit Breaker
```python
from src.utils.circuit_breaker import CircuitBreaker

breaker = CircuitBreaker(name="test", failure_threshold=3)

@breaker
async def flaky_function():
    raise Exception("Simulated failure")

# After 3 failures, circuit opens
# Future calls fail fast without trying
```

### Test Infrastructure Monitoring
```bash
# Start service
python -m src.server

# Check health
curl http://localhost:8000/api/v1/infrastructure/health

# Stop Redis
docker stop ecosystem-mcp-redis

# Check diagnostics - will show Redis issue
curl http://localhost:8000/api/v1/infrastructure/diagnostics
```

## Future Enhancements

Potential additions:
- [ ] Email alerts when circuit breakers open
- [ ] Metrics export (Prometheus)
- [ ] Dashboard visualization
- [ ] Auto-remediation scripts
- [ ] Circuit breaker for Redis operations
- [ ] Circuit breaker for ChromaDB operations
- [ ] Circuit breaker for Ollama API calls

## Files Modified

1. ✅ `src/utils/preflight.py` - Enhanced PostgreSQL checks
2. ✅ `src/utils/circuit_breaker.py` - New circuit breaker implementation
3. ✅ `src/api/routes/infrastructure.py` - New monitoring endpoints
4. ✅ `src/storage/database.py` - Circuit breaker integration
5. ✅ `src/api/app.py` - Register infrastructure routes

## Documentation

- Circuit Breaker Pattern: https://martinfowler.com/bliki/CircuitBreaker.html
- Preflight Checks: Pre-startup validation to fail fast
- Health Checks: Runtime monitoring of service dependencies

## Summary

You now have:
- ✅ **Database existence validation** at startup
- ✅ **Circuit breaker protection** against cascading failures
- ✅ **Comprehensive health monitoring** endpoints
- ✅ **Actionable diagnostics** with fix suggestions
- ✅ **Graceful degradation** when dependencies fail

The "database does not exist" error will now:
1. Be detected at startup with clear fix instructions
2. Trigger circuit breaker after 5 failures
3. Stop spamming logs
4. Auto-recover when fixed

