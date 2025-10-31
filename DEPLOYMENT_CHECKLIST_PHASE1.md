**Date:** October 28, 2025  
**Status:** Deployment Checklist for Phase 1  
**Target:** Production Deployment  

# Phase 1 Deployment Checklist

Complete checklist for deploying Phase 1 quick wins to production.

---

## 📋 Pre-Deployment

### 1. Validation
- [ ] Run validation script: `bash scripts/validate_phase1_implementation.sh`
- [ ] All 21 validation tests pass
- [ ] No linting errors in modified files
- [ ] Code review completed (if applicable)

### 2. Baseline Metrics
- [ ] Run baseline measurement: `bash scripts/measure_baseline_metrics.sh`
- [ ] Capture current performance metrics
- [ ] Document current error rates
- [ ] Record current resource usage

### 3. Database Migration Preparation
- [ ] Review migration file: `services/ecosystem-mcp/src/storage/migrations/013_add_temporal_rag_indexes.py`
- [ ] Verify CONCURRENTLY flag (no table locks)
- [ ] Estimate migration time (check table sizes)
- [ ] Prepare rollback plan

### 4. Testing Environment
- [ ] Deploy to staging environment
- [ ] Run integration tests
- [ ] Verify all 7 features work correctly
- [ ] Test rollback procedure

---

## 🚀 Deployment Steps

### Phase 1: Database Migration (No Downtime)

```bash
# Connect to database
psql -U ecosystem -d ecosystem_mcp

# Run migration (creates indexes with CONCURRENTLY - no locks)
cd services/ecosystem-mcp
python -m src.storage.migrations.013_add_temporal_rag_indexes

# Verify indexes created
\di idx_documents_*
\di idx_jobs_*

# Check index sizes
SELECT
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexname::regclass)) as size
FROM pg_indexes
WHERE indexname LIKE 'idx_documents_%'
   OR indexname LIKE 'idx_jobs_%';
```

**Estimated Time:** 5-15 minutes (depending on table size)  
**Downtime:** None (CONCURRENTLY flag)

- [ ] Migration started
- [ ] Migration completed successfully
- [ ] Indexes verified
- [ ] No errors in logs

---

### Phase 2: Service Deployment

#### Step 1: Build New Images

```bash
# Build all services
docker-compose -f docker-compose-mcp-ecosystem.yml build \
    ecosystem-mcp \
    ecosystem-mcp-embedding

# Verify builds
docker images | grep ecosystem-mcp
```

- [ ] Main service built
- [ ] Embedding service built
- [ ] Dashboard built (if changes)
- [ ] No build errors

#### Step 2: Deploy Services (Rolling Update)

```bash
# Stop services gracefully
docker-compose -f docker-compose-mcp-ecosystem.yml stop ecosystem-mcp
docker-compose -f docker-compose-mcp-ecosystem.yml stop ecosystem-mcp-embedding

# Start with new code
docker-compose -f docker-compose-mcp-ecosystem.yml up -d ecosystem-mcp
docker-compose -f docker-compose-mcp-ecosystem.yml up -d ecosystem-mcp-embedding

# Verify startup
docker-compose -f docker-compose-mcp-ecosystem.yml logs -f ecosystem-mcp | head -50
```

- [ ] Services stopped gracefully
- [ ] Services started successfully
- [ ] Health checks pass
- [ ] No errors in startup logs

#### Step 3: Verify Deployment

```bash
# Check service health
curl http://localhost:8000/health

# Check infrastructure health
curl http://localhost:8000/api/v1/infrastructure/health

# Verify Phase 1 features
docker logs ecosystem-mcp | grep "Database pool sizing"
docker logs ecosystem-mcp | grep "Creating Redis connection pool"
docker logs ecosystem-mcp-embedding | grep "Circuit breaker: enabled"
```

- [ ] Health endpoints respond
- [ ] Database pool sizing logged
- [ ] Redis connection pool created
- [ ] Circuit breaker initialized
- [ ] Lock monitoring active

---

### Phase 3: Feature Verification

#### Test 1.1: Database Pool Sizing

```bash
# Check logs for dynamic pool sizing
docker logs ecosystem-mcp 2>&1 | grep "Database pool sizing"

# Expected output:
# 📊 Database pool sizing: <size> + <overflow> overflow (workers=<count>, config_min=20)
```

- [ ] Dynamic pool sizing active
- [ ] Pool size scales with WORKER_COUNT
- [ ] Logging confirms configuration

#### Test 1.2: Redis Connection Pooling

```bash
# Check pool creation
docker logs ecosystem-mcp 2>&1 | grep "Creating Redis connection pool"

# Test pool stats endpoint (when implemented)
# curl http://localhost:8000/api/v1/diagnostics/redis-stats
```

- [ ] Connection pool created
- [ ] Pool reused across clients
- [ ] No connection errors

#### Test 1.3: Embedding Circuit Breaker

```bash
# Check circuit breaker initialization
docker logs ecosystem-mcp-embedding 2>&1 | grep "Circuit breaker"

# Test embedding generation
curl -X POST http://localhost:8001/api/v1/embeddings \
  -H "Content-Type: application/json" \
  -d '{"text": "test", "model": "fastembed"}'
```

- [ ] Circuit breaker initialized
- [ ] Embeddings generate successfully
- [ ] No ONNX runtime errors

#### Test 1.4: ChromaDB Lock Monitoring

```bash
# Trigger some writes to populate metrics
# Then check lock stats (when endpoint added)

# Check logs for lock monitoring
docker logs ecosystem-mcp 2>&1 | grep "lock monitoring"
```

- [ ] Lock monitoring initialized
- [ ] Metrics being collected
- [ ] No high contention alerts

#### Test 1.5: Request ID Propagation

```bash
# Make request with X-Request-ID
curl -H "X-Request-ID: test-123" http://localhost:8000/health

# Check logs for request ID
docker logs ecosystem-mcp 2>&1 | grep "test-123"
```

- [ ] Request IDs logged
- [ ] End-to-end tracing works
- [ ] Request IDs in all log statements

#### Test 1.6: Database Query Indexes

```bash
# Test temporal query performance
psql -U ecosystem -d ecosystem_mcp -c "
EXPLAIN ANALYZE
SELECT * FROM documents
WHERE git_date BETWEEN '2025-01-01' AND '2025-12-31'
LIMIT 100;
"

# Should show: Index Scan using idx_documents_git_date
```

- [ ] Indexes being used
- [ ] Query planner shows index scans
- [ ] Query performance improved

#### Test 1.7: Dashboard API Cache

```bash
# Load dashboard
# Open browser to http://localhost:8501

# Check for cache hits in logs
# Navigate multiple times to same page within 5 seconds
```

- [ ] Dashboard loads successfully
- [ ] API cache operational
- [ ] Cache hits logged
- [ ] No duplicate API calls

---

## 📊 Post-Deployment Validation

### 1. Measure Impact

```bash
# Run metrics measurement again
bash scripts/measure_baseline_metrics.sh

# Compare with baseline
# Expected improvements:
# - Redis operations: +200-400%
# - Temporal queries: +500-2000%
# - Dashboard API calls: -60%
```

- [ ] Post-deployment metrics captured
- [ ] Performance improvements confirmed
- [ ] No performance regressions
- [ ] Resource usage acceptable

### 2. Monitor for Issues

```bash
# Monitor logs for errors
docker-compose -f docker-compose-mcp-ecosystem.yml logs -f --tail=100

# Check error rates
# Check response times
# Check resource usage (CPU, memory, disk)
```

**Monitoring Period:** 1-4 hours

- [ ] No error spikes
- [ ] Response times improved
- [ ] Resource usage stable
- [ ] No memory leaks

### 3. User Acceptance

- [ ] Dashboard responsive
- [ ] RAG queries faster
- [ ] Ingestion stable
- [ ] No user-reported issues

---

## 🔄 Rollback Plan

### If Issues Occur:

#### Option 1: Code Rollback (5 minutes)

```bash
# Revert to previous images
docker-compose -f docker-compose-mcp-ecosystem.yml down
git checkout <previous-commit>
docker-compose -f docker-compose-mcp-ecosystem.yml up -d

# Verify rollback
curl http://localhost:8000/health
```

#### Option 2: Index Rollback (10 minutes)

```bash
# Remove indexes if causing issues
psql -U ecosystem -d ecosystem_mcp

DROP INDEX CONCURRENTLY IF EXISTS idx_documents_git_date;
DROP INDEX CONCURRENTLY IF EXISTS idx_documents_service_created;
DROP INDEX CONCURRENTLY IF EXISTS idx_jobs_status_created;
DROP INDEX CONCURRENTLY IF EXISTS idx_jobs_active;
DROP INDEX CONCURRENTLY IF EXISTS idx_documents_service_path;
```

#### Option 3: Full Rollback (15 minutes)

```bash
# Full system rollback
docker-compose -f docker-compose-mcp-ecosystem.yml down
git checkout <previous-commit>
# Run index rollback (above)
docker-compose -f docker-compose-mcp-ecosystem.yml up -d
```

---

## ✅ Deployment Complete

### Sign-off Checklist

- [ ] All deployment steps completed
- [ ] All verification tests pass
- [ ] Performance improvements confirmed
- [ ] No critical errors
- [ ] Monitoring in place
- [ ] Team notified
- [ ] Documentation updated

### Next Steps

- [ ] Monitor for 24-48 hours
- [ ] Collect performance data
- [ ] Gather user feedback
- [ ] Plan Phase 2 deployment

---

## 📞 Contacts & Support

**Deployment Lead:** _______________  
**Database Admin:** _______________  
**On-Call Engineer:** _______________  

**Rollback Decision Maker:** _______________

---

**Deployment Date:** _______________  
**Deployment Time:** _______________  
**Completed By:** _______________  
**Status:** ⬜ Success  ⬜ Partial  ⬜ Rollback  

---

**Notes:**


