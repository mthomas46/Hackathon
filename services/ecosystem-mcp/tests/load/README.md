# Load Testing Guide

**Date**: 2025-10-12  
**Service**: ecosystem-mcp v0.1.0  
**Tool**: Locust

---

## Overview

This directory contains load testing infrastructure for the ecosystem-mcp service. Load tests validate performance, scalability, and resilience under various load conditions.

---

## Prerequisites

```bash
# Install locust
pip install locust

# Ensure service is running
make deploy  # Or: docker-compose up -d
```

---

## Test Scenarios

### 1. Baseline Test (1 user, 1 minute)

**Purpose**: Establish baseline performance metrics

```bash
locust -f tests/load/locustfile.py \
    --host=http://localhost:8000 \
    --users 1 \
    --spawn-rate 1 \
    --run-time 1m \
    --headless \
    --html tests/load/reports/baseline.html
```

**Expected Results**:
- Success rate: >99%
- Avg response time: <100ms (without cache), <10ms (with cache)
- Requests/sec: ~10

---

### 2. Sustained Load Test (100 users, 10 minutes)

**Purpose**: Validate performance under normal production load

```bash
locust -f tests/load/locustfile.py \
    --host=http://localhost:8000 \
    --users 100 \
    --spawn-rate 10 \
    --run-time 10m \
    --headless \
    --html tests/load/reports/sustained.html
```

**Expected Results**:
- Success rate: >95%
- Avg response time: <500ms
- Requests/sec: ~100-200
- CPU usage: <70%
- Memory usage: <80%

**What to watch**:
- Cache hit rate should increase over time
- Response times should stabilize
- No memory leaks (constant memory usage)
- Circuit breakers should remain CLOSED

---

### 3. Spike Test (500 users, 5 minutes)

**Purpose**: Test resilience to sudden traffic spikes

```bash
locust -f tests/load/locustfile.py \
    --host=http://localhost:8000 \
    --users 500 \
    --spawn-rate 50 \
    --run-time 5m \
    --headless \
    --html tests/load/reports/spike.html
```

**Expected Results**:
- Success rate: >90% (some failures acceptable)
- Avg response time: <1000ms
- Requests/sec: ~300-500
- CPU usage: <90%
- Memory usage: <90%

**What to watch**:
- Circuit breakers may OPEN temporarily (acceptable)
- Rate limiting may trigger
- Service should recover automatically
- No crashes or OOM errors

---

### 4. Soak Test (50 users, 1 hour)

**Purpose**: Detect memory leaks and long-term stability issues

```bash
locust -f tests/load/locustfile.py \
    --host=http://localhost:8000 \
    --users 50 \
    --spawn-rate 5 \
    --run-time 1h \
    --headless \
    --html tests/load/reports/soak.html
```

**Expected Results**:
- Success rate: >99%
- Avg response time: <300ms (stable over time)
- Requests/sec: ~50-100
- Memory usage: Stable (no continuous growth)
- CPU usage: <60%

**What to watch**:
- Memory should not increase continuously
- Response times should remain consistent
- No connection pool exhaustion
- Cache should remain stable

---

## Interpreting Results

### Success Metrics

| Metric | Baseline | Sustained | Spike | Soak |
|--------|----------|-----------|-------|------|
| **Success Rate** | >99% | >95% | >90% | >99% |
| **Avg Response** | <100ms | <500ms | <1000ms | <300ms |
| **P95 Response** | <200ms | <1000ms | <2000ms | <500ms |
| **P99 Response** | <500ms | <2000ms | <5000ms | <1000ms |
| **Requests/sec** | ~10 | ~100-200 | ~300-500 | ~50-100 |

### Key Performance Indicators (KPIs)

1. **Response Time Percentiles**
   - P50 (median): Most users experience this
   - P95: 95% of requests faster than this
   - P99: Worst-case for most users

2. **Throughput**
   - Requests per second (RPS)
   - Higher is better

3. **Error Rate**
   - Failures / Total requests
   - Lower is better

4. **Resource Usage**
   - CPU: Should be <80% under sustained load
   - Memory: Should be stable (no leaks)
   - Connections: Should not exhaust pool

---

## Analyzing Results

### 1. Check HTML Report

```bash
open tests/load/reports/sustained.html
```

**Look for**:
- Response time chart (should be stable)
- Requests per second (should be consistent)
- Failure rate (should be low)
- User count ramp-up

### 2. Check Service Logs

```bash
docker-compose logs -f ecosystem-mcp
```

**Look for**:
- Error messages
- Circuit breaker state changes
- Cache hit/miss ratios
- Database query times

### 3. Check Prometheus Metrics

```bash
curl http://localhost:8000/metrics
```

**Key metrics**:
- `http_requests_total` - Total requests
- `http_request_duration_seconds` - Response times
- `cache_hits_total` - Cache effectiveness
- `circuit_breaker_state` - Resilience

### 4. Check Database Performance

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U ecosystem_mcp

# Check connection count
SELECT count(*) FROM pg_stat_activity;

# Check slow queries
SELECT query, mean_exec_time 
FROM pg_stat_statements 
ORDER BY mean_exec_time DESC 
LIMIT 10;
```

---

## Common Issues and Solutions

### Issue: High Response Times

**Symptoms**:
- P95 > 2000ms
- Users experiencing slow responses

**Possible Causes**:
1. **Database bottleneck**
   - Check query performance
   - Add missing indexes
   - Increase connection pool

2. **Cache misses**
   - Check cache hit rate
   - Increase TTL if appropriate
   - Warm up cache before test

3. **External service slow**
   - Check Ollama response times
   - Check ChromaDB performance
   - Circuit breaker should help

**Solutions**:
```bash
# Check cache stats
curl http://localhost:8000/api/v1/admin/cache-stats

# Check circuit breakers
curl http://localhost:8000/api/v1/admin/circuit-breakers

# Warm up cache
for i in {1..100}; do
    curl -X POST http://localhost:8000/api/v1/query \
        -H "Content-Type: application/json" \
        -d '{"query": "test query", "limit": 5}'
done
```

---

### Issue: High Failure Rate

**Symptoms**:
- Success rate < 90%
- Many 500 errors

**Possible Causes**:
1. **Service overloaded**
   - Too many users
   - CPU at 100%
   - Memory exhausted

2. **Database connection pool exhausted**
   - Check `pg_stat_activity`
   - Increase pool size

3. **Circuit breakers tripping**
   - Ollama unavailable
   - ChromaDB slow
   - Check logs

**Solutions**:
```bash
# Reduce load
# In locustfile: decrease users or spawn-rate

# Increase connection pool
# In config/ecosystem-mcp.env:
DATABASE_POOL_SIZE=20  # Increase from 10

# Check circuit breaker states
curl http://localhost:8000/api/v1/admin/circuit-breakers
```

---

### Issue: Memory Leak

**Symptoms**:
- Memory usage increases continuously
- Eventually crashes with OOM

**Possible Causes**:
1. **Database connections not closed**
2. **Cache growing unbounded**
3. **Memory not released**

**Solutions**:
```bash
# Monitor memory during test
watch -n 5 'docker stats --no-stream ecosystem-mcp'

# Check for connection leaks
docker-compose exec postgres psql -U ecosystem_mcp -c \
    "SELECT count(*), state FROM pg_stat_activity GROUP BY state;"

# Clear cache if needed
curl -X POST http://localhost:8000/api/v1/admin/clear-all-cache
```

---

## Best Practices

1. **Run tests in isolation**
   - Don't run multiple tests simultaneously
   - Clean state between tests

2. **Warm up the service**
   - Run baseline test first
   - Populate cache with common queries

3. **Monitor during tests**
   - Watch logs in real-time
   - Monitor metrics
   - Track resource usage

4. **Document results**
   - Save HTML reports
   - Note any issues
   - Compare to previous runs

5. **Run tests regularly**
   - Before releases
   - After major changes
   - Weekly for regression testing

---

## Automation

### Run All Tests

```bash
#!/bin/bash
# tests/load/run_all.sh

# Ensure service is running
make deploy

# Wait for service to be ready
sleep 10

# Baseline
locust -f tests/load/locustfile.py \
    --host=http://localhost:8000 \
    --users 1 --spawn-rate 1 --run-time 1m --headless \
    --html tests/load/reports/baseline_$(date +%Y%m%d_%H%M%S).html

# Sustained
locust -f tests/load/locustfile.py \
    --host=http://localhost:8000 \
    --users 100 --spawn-rate 10 --run-time 10m --headless \
    --html tests/load/reports/sustained_$(date +%Y%m%d_%H%M%S).html

# Spike
locust -f tests/load/locustfile.py \
    --host=http://localhost:8000 \
    --users 500 --spawn-rate 50 --run-time 5m --headless \
    --html tests/load/reports/spike_$(date +%Y%m%d_%H%M%S).html

echo "Load tests complete! Check tests/load/reports/ for results."
```

---

## Integration with CI/CD

```yaml
# .github/workflows/load-test.yml
name: Load Testing

on:
  schedule:
    - cron: '0 2 * * 0'  # Weekly on Sunday at 2 AM
  workflow_dispatch:  # Manual trigger

jobs:
  load-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Start services
        run: docker-compose up -d
      
      - name: Wait for ready
        run: sleep 30
      
      - name: Install locust
        run: pip install locust
      
      - name: Run sustained load test
        run: |
          locust -f tests/load/locustfile.py \
            --host=http://localhost:8000 \
            --users 100 --spawn-rate 10 --run-time 10m \
            --headless --html report.html
      
      - name: Upload results
        uses: actions/upload-artifact@v2
        with:
          name: load-test-report
          path: report.html
```

---

## Conclusion

Load testing is crucial for production readiness. These tests validate:
- ✅ Performance under normal load
- ✅ Resilience to traffic spikes
- ✅ Long-term stability (no memory leaks)
- ✅ Circuit breaker effectiveness
- ✅ Caching effectiveness

**Run all tests before production deployment!**

---

**Next**: Security Audit

