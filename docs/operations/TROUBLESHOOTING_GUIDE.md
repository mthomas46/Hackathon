# Troubleshooting Guide - Document Ingestion System

## 🎯 Based on Real Production Issues

This guide documents actual issues encountered during development, testing, and the **7-hour debugging session** that uncovered the root cause of worker loop blocking.

---

## Table of Contents

1. [Quick Diagnosis](#quick-diagnosis)
2. [Worker Loop Issues](#worker-loop-issues)
3. [Job Processing Issues](#job-processing-issues)
4. [Embedding Service Issues](#embedding-service-issues)
5. [Database Issues](#database-issues)
6. [Performance Issues](#performance-issues)
7. [Lessons Learned](#lessons-learned)

---

## Quick Diagnosis

### Diagnostic Commands

Run these to quickly assess system state:

```bash
# 1. Check all service health
docker ps | grep ecosystem-mcp
docker logs ecosystem-mcp-service --tail 20
curl http://localhost:8000/health
curl http://localhost:8001/health

# 2. Check worker status
docker logs ecosystem-mcp-service 2>&1 | grep "Worker loop iteration" | tail -10

# 3. Check job queue
curl -s http://localhost:8000/api/v1/admin/redis/stream-status | jq '.'

# 4. Check for hung jobs
docker exec ecosystem-mcp-postgres psql -U ecosystem -d ecosystem_mcp -c \
  "SELECT id, status, started_at, 
   EXTRACT(EPOCH FROM (NOW() - started_at))/60 as minutes_running 
   FROM ingestion_jobs 
   WHERE status = 'processing' 
   ORDER BY started_at DESC 
   LIMIT 5;"
```

### Quick Health Check Script

```bash
#!/bin/bash
# save as: check_health.sh

echo "🏥 System Health Check"
echo "====================="

echo -e "\n📊 Services:"
docker ps --format "table {{.Names}}\t{{.Status}}" | grep ecosystem-mcp

echo -e "\n🔄 Worker Status:"
ITERATIONS=$(docker logs ecosystem-mcp-service 2>&1 | grep "Worker loop iteration" | tail -3)
if [ -z "$ITERATIONS" ]; then
    echo "❌ No worker iterations found!"
else
    echo "$ITERATIONS"
fi

echo -e "\n📬 Redis Queue:"
curl -s http://localhost:8000/api/v1/admin/redis/stream-status | \
  jq '{length: .status.ingestion_stream.length, pending: .status.pending_messages.count}'

echo -e "\n💾 Job Stats:"
docker exec ecosystem-mcp-postgres psql -U ecosystem -d ecosystem_mcp -t -c \
  "SELECT status, COUNT(*) FROM ingestion_jobs GROUP BY status;" | \
  grep -v "^$"

echo -e "\n✅ Health check complete"
```

---

## Worker Loop Issues

### Issue #1: Worker Stuck at Iteration #1

**Symptom:**
```
🔄 Worker loop iteration #1
[never reaches #2]
```

**Root Cause:** Event loop blocked by synchronous `os.walk()` scanning 125k+ files

**Investigation Steps:**
1. Check if large directory being scanned
2. Look for blocking operations in logs
3. Check if timeout protection triggered

**Solution:**
```bash
# 1. Identify hung job
docker exec ecosystem-mcp-postgres psql -U ecosystem -d ecosystem_mcp -c \
  "SELECT id, repo_path, started_at 
   FROM ingestion_jobs 
   WHERE status = 'processing';"

# 2. Kill hung job
docker exec ecosystem-mcp-postgres psql -U ecosystem -d ecosystem_mcp -c \
  "UPDATE ingestion_jobs 
   SET status = 'failed',
       error_message = 'Hung - manually stopped',
       completed_at = NOW()
   WHERE status = 'processing';"

# 3. Restart worker
docker restart ecosystem-mcp-service

# 4. Verify iterations resume
sleep 10
docker logs ecosystem-mcp-service 2>&1 | grep "iteration" | tail -5
```

**Prevention:**
- Use specific subdirectories, not root paths
- Check file count before submitting: `find /path -type f | wc -l`
- 10k file limit is enforced automatically

---

### Issue #2: Worker Not Starting

**Symptom:**
```
$ docker logs ecosystem-mcp-service | grep "Worker"
[no output]
```

**Root Cause:** Worker initialization failed

**Investigation:**
```bash
# Check for startup errors
docker logs ecosystem-mcp-service 2>&1 | grep -A 10 "ERROR"

# Check if lifespan completed
docker logs ecosystem-mcp-service 2>&1 | grep "Application startup complete"
```

**Solution:**
```bash
# Restart service
docker restart ecosystem-mcp-service

# If persists, check dependencies
docker logs ecosystem-mcp-redis --tail 20
docker logs ecosystem-mcp-postgres --tail 20
```

---

### Issue #3: Worker Crashes During Processing

**Symptom:**
```
Exception in worker loop: [error]
Worker loop stopped after 1 iterations
```

**Investigation:**
```bash
# Get full stack trace
docker logs ecosystem-mcp-service 2>&1 | grep -A 20 "Exception in worker loop"
```

**Common Causes:**
1. **Database connection lost**
   ```bash
   docker restart ecosystem-mcp-postgres
   docker restart ecosystem-mcp-service
   ```

2. **Redis connection lost**
   ```bash
   docker restart ecosystem-mcp-redis
   docker restart ecosystem-mcp-service
   ```

3. **Memory exhaustion**
   ```bash
   docker stats ecosystem-mcp-service
   # If memory >4GB, increase Docker memory or lower file limit
   ```

---

## Job Processing Issues

### Issue #4: Jobs Stuck in "queued"

**Symptom:**
Jobs never move from "queued" to "processing"

**Root Cause Checklist:**
- [ ] Worker not running
- [ ] Redis stream disconnected
- [ ] Job not actually in Redis
- [ ] Worker blocked on previous job

**Investigation:**
```bash
# 1. Check worker running
docker logs ecosystem-mcp-service 2>&1 | grep "iteration" | tail -5

# 2. Check Redis
curl -s http://localhost:8000/api/v1/admin/redis/stream-status | jq '.'

# 3. Check job in DB vs Redis
JOB_ID="your-job-id"
docker exec ecosystem-mcp-postgres psql -U ecosystem -d ecosystem_mcp -c \
  "SELECT id, status FROM ingestion_jobs WHERE id = '$JOB_ID';"

docker exec ecosystem-mcp-redis redis-cli XRANGE ingestion_queue - + | grep "$JOB_ID"
```

**Solution:**
```bash
# If job in DB but not Redis, re-queue it
curl -X POST http://localhost:8000/api/v1/admin/jobs/$JOB_ID/retry

# If Redis disconnected, restart
docker restart ecosystem-mcp-redis ecosystem-mcp-service
```

---

### Issue #5: Jobs Failing Immediately

**Symptom:**
Job goes from "queued" to "failed" instantly

**Common Causes:**

**1. Path Not Found**
```
Error: Repository path does not exist: /host/nonexistent
```
**Solution:** Verify path exists in container:
```bash
docker exec ecosystem-mcp-service ls -la /host/your/path
```

**2. Not a Git Repository** (git history modes only)
```
Error: Path is not in a git repository
```
**Solution:** Use `snapshot` mode instead:
```json
{"repo_path": "/host/path", "mode": "snapshot"}
```

**3. ChromaDB Import Error**
```
ModuleNotFoundError: No module named 'src.storage.chroma'
```
**Solution:** This was fixed in recent updates. Rebuild:
```bash
docker-compose build ecosystem-mcp-service
docker restart ecosystem-mcp-service
```

---

### Issue #6: Jobs Timeout After 10 Minutes

**Symptom:**
```
⏰ Job {id} timed out after 10 minutes!
```

**Root Causes:**
1. Processing too many files (>10k limit hit)
2. Embedding service slow/failing
3. Database operations slow

**Investigation:**
```bash
# Check how many files
docker logs ecosystem-mcp-service 2>&1 | grep "Found.*files to process"

# Check embedding errors
docker logs ecosystem-mcp-service 2>&1 | grep "embedding" | tail -20

# Check DB performance
docker exec ecosystem-mcp-postgres psql -U ecosystem -d ecosystem_mcp -c \
  "SELECT COUNT(*) as active_queries 
   FROM pg_stat_activity 
   WHERE state = 'active';"
```

**Solutions:**
- Use smaller directory (< 1000 files for testing)
- Increase timeout in code if justified
- Fix embedding service (see below)

---

## Embedding Service Issues

### Issue #7: Embedding Service "unhealthy"

**Symptom:**
```json
{"status": "unhealthy", "model": "BAAI/bge-base-en-v1.5"}
```

**Root Cause:** Model auto-unloaded after 5 min inactivity

**Solution:**
```bash
# Quick fix: Restart
docker restart ecosystem-mcp-embedding

# Verify
sleep 5
curl http://localhost:8001/health | jq '.status'
```

**Permanent Fix:**
Increase or disable auto-unload timeout in `fastembed_service.py`:
```python
auto_unload_timeout: int = 3600  # 1 hour instead of 5 min
# or
auto_unload_timeout: int = None  # Disable auto-unload
```

---

### Issue #8: Ollama Returns 500 Errors

**Symptom:**
```
HTTP/1.1 500 Internal Server Error
url: 'http://host.docker.internal:11434/api/embed'
```

**Root Causes & Solutions:**

**1. Model Not Pulled**
```bash
# Check model exists
curl http://localhost:11434/api/tags | jq '.models[].name' | grep nomic

# If missing, pull it
docker exec ecosystem-mcp-service curl -X POST http://host.docker.internal:11434/api/pull \
  -d '{"model": "nomic-embed-text:latest"}'
```

**2. Ollama Overloaded**
```bash
# Restart Ollama
docker restart ecosystem-mcp-ollama

# Wait for it to be ready
sleep 10
curl http://localhost:11434/api/tags
```

**3. Text Too Long**
```
# Ollama has token limits
# Check logs for text length
docker logs ecosystem-mcp-service 2>&1 | grep "Text too long"
```

---

### Issue #9: Circuit Breaker Open

**Symptom:**
```
🔴 Circuit breaker open for generate_embedding
⚠️  Circuit breaker OPEN for FastEmbed
```

**What It Means:**
Too many consecutive failures → circuit breaker prevents further attempts

**How to Reset:**
```bash
# 1. Fix underlying issue (restart services)
docker restart ecosystem-mcp-embedding ecosystem-mcp-ollama

# 2. Wait for automatic health check (2 minutes)
# OR manually reset via API (if implemented)

# 3. Verify services healthy
curl http://localhost:8001/health
curl http://localhost:11434/api/tags
```

**Circuit Breaker Settings:**
- Failure threshold: 15 consecutive failures
- Timeout: 120 seconds before retry
- Startup grace: 90 seconds (failures ignored)

---

## Database Issues

### Issue #10: Connection Pool Exhausted

**Symptom:**
```
asyncpg.exceptions.TooManyConnectionsError
```

**Solution:**
```bash
# Check active connections
docker exec ecosystem-mcp-postgres psql -U ecosystem -d ecosystem_mcp -c \
  "SELECT count(*), state FROM pg_stat_activity GROUP BY state;"

# Kill idle connections if needed
docker exec ecosystem-mcp-postgres psql -U ecosystem -d ecosystem_mcp -c \
  "SELECT pg_terminate_backend(pid) 
   FROM pg_stat_activity 
   WHERE state = 'idle' 
   AND state_change < NOW() - INTERVAL '5 minutes';"

# Restart service to reset pool
docker restart ecosystem-mcp-service
```

---

### Issue #11: Duplicate Key Errors

**Symptom:**
```
IntegrityError: duplicate key value violates unique constraint
```

**Root Cause:** Same document ingested twice

**This is Expected:** Duplicate detection working!

**Check Metrics:**
```bash
# See skipped documents count
docker exec ecosystem-mcp-postgres psql -U ecosystem -d ecosystem_mcp -c \
  "SELECT SUM(skipped_documents) as total_duplicates_skipped 
   FROM ingestion_jobs 
   WHERE status = 'completed';"
```

---

## Performance Issues

### Issue #12: Slow Job Processing

**Target:** <5 min for 1000 files

**Diagnosis:**
```bash
# Time a test job
time curl -X POST http://localhost:8000/api/v1/admin/ingest \
  -H "Content-Type: application/json" \
  -d '{"repo_path": "/host/tests", "mode": "snapshot"}'

# Monitor progress
JOB_ID="from-above"
watch -n 5 "docker exec ecosystem-mcp-postgres psql -U ecosystem -d ecosystem_mcp -t -c \
  \"SELECT processed_documents, total_documents FROM ingestion_jobs WHERE id = '$JOB_ID';\""
```

**Common Bottlenecks:**

**1. Embedding Generation Slow**
```bash
# Check embedding service logs
docker logs ecosystem-mcp-embedding --tail 50

# If slow, check CPU usage
docker stats ecosystem-mcp-embedding
```

**2. Database Writes Slow**
```bash
# Check DB performance
docker exec ecosystem-mcp-postgres psql -U ecosystem -d ecosystem_mcp -c \
  "SELECT schemaname, tablename, 
   pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) 
   FROM pg_tables 
   WHERE schemaname = 'public';"

# Consider VACUUM if table bloated
docker exec ecosystem-mcp-postgres psql -U ecosystem -d ecosystem_mcp -c \
  "VACUUM ANALYZE documents;"
```

**3. Too Much Parallelism**
```python
# Reduce in job_processor.py
self.max_concurrent_commits = 5  # Lower if CPU constrained
```

---

### Issue #13: High Memory Usage

**Symptom:**
```bash
$ docker stats ecosystem-mcp-service
CONTAINER  CPU %  MEM USAGE / LIMIT  MEM %
...        50%    4.5GB / 8GB         56%
```

**Solutions:**

**1. Lower File Limit**
```python
# In job_processor.py
MAX_FILES_PER_JOB = 5000  # From 10,000
```

**2. Reduce Batch Size**
```python
# In job_processor.py
batch_size = 25  # From 50
```

**3. Restart Service Periodically**
```bash
# For long-running operations
docker restart ecosystem-mcp-service
```

---

## Lessons Learned

### From 7-Hour Debug Session

**🔍 Issue:** Worker loop stopped at iteration #1, jobs hung for 40+ minutes

**Root Cause:** `os.walk()` blocked event loop scanning 125k+ files

**Key Learnings:**

1. **Async != Automatic**
   - `async def` doesn't make everything async
   - Synchronous I/O still blocks

2. **Always Yield in Loops**
   - Use `await asyncio.sleep(0)` in long loops
   - Allows timeout and other tasks to run

3. **Set Safety Limits**
   - Never process unbounded data
   - 10k file limit prevents runaway processing

4. **Test at Scale**
   - Testing with 60 files didn't catch the issue
   - 125k files exposed the blocking behavior

5. **Logging is Critical**
   - Without detailed logs, appeared as simple "hang"
   - 50+ log points revealed actual progress

---

### Common Mistakes

**❌ Don't:**
- Process entire filesystem (`/host`)
- Ignore worker iteration logs
- Let jobs run >1 hour without investigation
- Skip health checks

**✅ Do:**
- Use specific subdirectories
- Monitor worker iterations
- Set up alerts for stuck jobs
- Regular health checks (every 5 min)

---

### Debug Checklist

When things go wrong:

- [ ] Check all service health endpoints
- [ ] Verify worker iterations progressing
- [ ] Check for hung jobs (>10 min processing)
- [ ] Look for errors in all service logs
- [ ] Verify Redis stream status
- [ ] Check database connectivity
- [ ] Monitor memory/CPU usage
- [ ] Test with minimal job first

---

## Getting Help

### Collect Diagnostic Info

```bash
#!/bin/bash
# save as: collect_diagnostics.sh

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_DIR="diagnostics_$TIMESTAMP"
mkdir -p $OUTPUT_DIR

echo "Collecting diagnostics..."

# Service logs
docker logs ecosystem-mcp-service > $OUTPUT_DIR/service.log 2>&1
docker logs ecosystem-mcp-embedding > $OUTPUT_DIR/embedding.log 2>&1
docker logs ecosystem-mcp-postgres > $OUTPUT_DIR/postgres.log 2>&1
docker logs ecosystem-mcp-redis > $OUTPUT_DIR/redis.log 2>&1

# Service status
docker ps > $OUTPUT_DIR/docker_ps.txt

# Health checks
curl -s http://localhost:8000/health > $OUTPUT_DIR/service_health.json
curl -s http://localhost:8001/health > $OUTPUT_DIR/embedding_health.json

# Redis status
curl -s http://localhost:8000/api/v1/admin/redis/stream-status > $OUTPUT_DIR/redis_status.json

# Database queries
docker exec ecosystem-mcp-postgres psql -U ecosystem -d ecosystem_mcp -c \
  "SELECT * FROM ingestion_jobs ORDER BY started_at DESC LIMIT 10;" \
  > $OUTPUT_DIR/recent_jobs.txt

echo "Diagnostics saved to $OUTPUT_DIR/"
tar czf ${OUTPUT_DIR}.tar.gz $OUTPUT_DIR/
echo "Archive: ${OUTPUT_DIR}.tar.gz"
```

---

*Last Updated: October 22, 2025*
*Based on 7-hour production debugging session*
*Version: 1.0*

