# Operational Runbook - Document Ingestion System

## 📚 Table of Contents
1. [System Overview](#system-overview)
2. [Service Architecture](#service-architecture)
3. [Monitoring & Health Checks](#monitoring--health-checks)
4. [Common Operations](#common-operations)
5. [Troubleshooting](#troubleshooting)
6. [Emergency Procedures](#emergency-procedures)
7. [Performance Tuning](#performance-tuning)

---

## System Overview

### Services
- **ecosystem-mcp-service**: Main API and worker
- **ecosystem-mcp-embedding**: FastEmbed service for embeddings
- **ecosystem-mcp-dashboard**: Streamlit dashboard
- **ecosystem-mcp-postgres**: Document and job storage
- **ecosystem-mcp-redis**: Job queue and caching
- **ecosystem-mcp-ollama**: LLM and embedding fallback

### Key Components
- **Ingestion Worker**: Background process for job execution
- **Job Processor**: Orchestrates document pipeline
- **Embedding Service**: Generates vector embeddings
- **ChromaDB**: Vector storage

---

## Service Architecture

### Worker Loop Flow
```
┌─────────────────────────────────────┐
│   Ingestion Worker Loop             │
│                                     │
│  1. Poll Redis stream (1s timeout) │
│  2. Get next job from queue        │
│  3. Process job with timeout       │
│  4. ACK message in Redis           │
│  5. Repeat (iterations #2, #3...)  │
└─────────────────────────────────────┘
```

### Job Processing Pipeline
```
Job → Git/Snapshot → Normalize → Embed → Store
      ↓               ↓           ↓       ↓
    Files          Markdown    Vectors  PostgreSQL
                                        ChromaDB
```

---

## Monitoring & Health Checks

### Service Health Endpoints

```bash
# Main service
curl http://localhost:8000/health
# Response: {"status": "healthy"}

# Embedding service  
curl http://localhost:8001/health
# Response: {"status": "healthy", "model": "BAAI/bge-base-en-v1.5"}

# Dashboard
curl http://localhost:8501/
# Response: 200 OK
```

### Worker Status

```bash
# Check if worker is running
docker logs ecosystem-mcp-service 2>&1 | grep "Worker loop iteration" | tail -10

# Should see:
# 🔄 Worker loop iteration #1
# 🔄 Worker loop iteration #2
# 🔄 Worker loop iteration #3
# ...

# ⚠️  If stuck at #1: Worker is blocked (see troubleshooting)
```

### Redis Stream Status

```bash
# Check job queue status
curl -s http://localhost:8000/api/v1/admin/redis/stream-status | jq '.'

# Key fields:
# - stream_length: Total jobs in queue
# - pending: Jobs claimed by workers but not ACK'd
```

### Database Health

```bash
# Check job counts by status
docker exec ecosystem-mcp-postgres psql -U ecosystem -d ecosystem_mcp -c \
  "SELECT status, COUNT(*) FROM ingestion_jobs GROUP BY status;"

# Check for hung jobs (processing >1 hour)
docker exec ecosystem-mcp-postgres psql -U ecosystem -d ecosystem_mcp -c \
  "SELECT id, status, started_at, 
   EXTRACT(EPOCH FROM (NOW() - started_at))/60 as minutes_running 
   FROM ingestion_jobs 
   WHERE status = 'processing' 
   AND started_at < NOW() - INTERVAL '1 hour';"
```

---

## Common Operations

### Starting Services

```bash
# Start all services
cd /Users/mykalthomas/Documents/work/Hackathon
docker-compose -f docker-compose.dev.yml up -d

# Verify all healthy
docker ps | grep ecosystem-mcp
docker logs ecosystem-mcp-service --tail 20
```

### Stopping Services

```bash
# Graceful stop
docker-compose -f docker-compose.dev.yml stop

# Force stop (if hung)
docker-compose -f docker-compose.dev.yml kill
```

### Restarting Specific Service

```bash
# Restart main service (includes worker)
docker restart ecosystem-mcp-service

# Restart embedding service
docker restart ecosystem-mcp-embedding

# Restart all
docker restart ecosystem-mcp-service ecosystem-mcp-embedding ecosystem-mcp-dashboard
```

### Submitting Ingestion Job

```bash
# Via API
curl -X POST http://localhost:8000/api/v1/admin/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "repo_path": "/host/services/ecosystem-mcp/src/utils",
    "mode": "snapshot"
  }'

# Response: {"job_id": "...", "status": "queued"}
```

### Monitoring Job Progress

```bash
# Get job status
JOB_ID="your-job-id-here"
docker exec ecosystem-mcp-postgres psql -U ecosystem -d ecosystem_mcp -c \
  "SELECT status, processed_documents, total_documents, embeddings_generated 
   FROM ingestion_jobs WHERE id = '$JOB_ID';"

# Watch logs in real-time
docker logs -f ecosystem-mcp-service
```

---

## Troubleshooting

### Problem: Worker Stuck at Iteration #1

**Symptoms:**
```bash
$ docker logs ecosystem-mcp-service | grep iteration
🔄 Worker loop iteration #1
[no iteration #2]
```

**Root Cause:** Event loop blocked by synchronous operations

**Solutions:**
1. Check if processing large directory (>10k files)
2. Verify async yielding is working
3. Check for hung jobs blocking queue

```bash
# Kill hung jobs
docker exec ecosystem-mcp-postgres psql -U ecosystem -d ecosystem_mcp -c \
  "UPDATE ingestion_jobs 
   SET status = 'failed', 
       error_message = 'Manually stopped - hung too long',
       completed_at = NOW()
   WHERE status = 'processing' 
   AND started_at < NOW() - INTERVAL '10 minutes';"

# Restart worker
docker restart ecosystem-mcp-service
```

---

### Problem: Jobs Stuck in "queued" Status

**Symptoms:**
- Jobs never move to "processing"
- Worker logs show iterations but no job processing

**Root Cause:** Redis stream issue or worker not consuming

**Solutions:**
```bash
# 1. Check Redis stream
curl -s http://localhost:8000/api/v1/admin/redis/stream-status | jq '.'

# 2. Check if jobs actually in stream
docker exec ecosystem-mcp-redis redis-cli XLEN ingestion_queue

# 3. Clear and restart if needed
docker exec ecosystem-mcp-redis redis-cli DEL ingestion_queue
docker restart ecosystem-mcp-service
```

---

### Problem: Embedding Service Unhealthy

**Symptoms:**
```bash
$ curl http://localhost:8001/health
{"status": "unhealthy", "model": "BAAI/bge-base-en-v1.5"}
```

**Root Cause:** Model auto-unloaded after 5 minutes inactivity

**Solution:**
```bash
# Restart to reload model
docker restart ecosystem-mcp-embedding

# Verify healthy
sleep 5
curl http://localhost:8001/health | jq '.status'
# Should return: "healthy"
```

---

### Problem: Ollama Returns 500 Errors

**Symptoms:**
```
HTTP Request: POST http://host.docker.internal:11434/api/embed 
"HTTP/1.1 500 Internal Server Error"
```

**Root Causes:**
1. Model not pulled to Docker Ollama
2. Ollama overloaded
3. Text too long

**Solutions:**
```bash
# 1. Check if model exists
curl http://localhost:11434/api/tags | jq '.models[] | select(.name | contains("nomic"))'

# 2. Pull model if missing
docker exec ecosystem-mcp-service curl -X POST http://host.docker.internal:11434/api/pull \
  -d '{"model": "nomic-embed-text:latest"}'

# 3. Restart Ollama if overloaded
docker restart ecosystem-mcp-ollama
```

---

### Problem: Circuit Breaker Open

**Symptoms:**
```
🔴 Circuit breaker open for generate_embedding
```

**Root Cause:** Too many consecutive failures

**Solution:**
```bash
# 1. Check service health
curl http://localhost:8001/health

# 2. Restart services
docker restart ecosystem-mcp-embedding ecosystem-mcp-ollama

# 3. Circuit breaker will auto-reset after services healthy
# Wait 2 minutes for automatic health check and reset
```

---

### Problem: Database Connection Errors

**Symptoms:**
```
asyncpg.exceptions.ConnectionDoesNotExistError
```

**Solution:**
```bash
# Restart PostgreSQL
docker restart ecosystem-mcp-postgres

# Check connections
docker exec ecosystem-mcp-postgres psql -U ecosystem -d ecosystem_mcp -c \
  "SELECT count(*) FROM pg_stat_activity WHERE datname = 'ecosystem_mcp';"
```

---

## Emergency Procedures

### Full System Reset

**When to use:** Complete system malfunction, stuck jobs everywhere

```bash
# 1. Stop all services
docker-compose -f docker-compose.dev.yml down

# 2. Clear hung jobs (DESTRUCTIVE!)
docker-compose -f docker-compose.dev.yml up -d ecosystem-mcp-postgres
sleep 5
docker exec ecosystem-mcp-postgres psql -U ecosystem -d ecosystem_mcp -c \
  "UPDATE ingestion_jobs 
   SET status = 'failed', 
       error_message = 'System reset',
       completed_at = NOW()
   WHERE status IN ('queued', 'processing');"

# 3. Clear Redis
docker-compose -f docker-compose.dev.yml up -d ecosystem-mcp-redis
sleep 5
docker exec ecosystem-mcp-redis redis-cli FLUSHDB

# 4. Restart all services
docker-compose -f docker-compose.dev.yml up -d

# 5. Verify health
sleep 15
curl http://localhost:8000/health
curl http://localhost:8001/health
```

### Database Backup

```bash
# Backup PostgreSQL
docker exec ecosystem-mcp-postgres pg_dump -U ecosystem ecosystem_mcp > \
  backup_$(date +%Y%m%d_%H%M%S).sql

# Backup ChromaDB (data directory)
docker exec ecosystem-mcp-service tar czf - /app/data/chroma_db > \
  chroma_backup_$(date +%Y%m%d_%H%M%S).tar.gz
```

### Database Restore

```bash
# Restore PostgreSQL
docker exec -i ecosystem-mcp-postgres psql -U ecosystem ecosystem_mcp < backup.sql

# Restore ChromaDB
docker cp chroma_backup.tar.gz ecosystem-mcp-service:/tmp/
docker exec ecosystem-mcp-service tar xzf /tmp/chroma_backup.tar.gz -C /
```

---

## Performance Tuning

### Worker Concurrency

**Default:** Auto-tuned (2× CPU cores, max 20)

**Adjust for your system:**
```python
# In job_processor.py
self.max_concurrent_commits = 10  # Lower for less powerful systems
```

### File Limit Per Job

**Default:** 10,000 files

**Adjust if needed:**
```python
# In job_processor.py _process_snapshot_mode()
MAX_FILES_PER_JOB = 5000  # Lower for faster jobs
MAX_FILES_PER_JOB = 20000  # Higher if you trust your paths
```

### Batch Size

**Default:** 50 files per batch

**Adjust:**
```python
# In job_processor.py _process_snapshot_mode()
batch_size = 100  # Larger batches = fewer DB commits
```

### Timeout Settings

**Job Timeout:** 10 minutes (600s)
```python
# In ingestion_worker.py
timeout=600  # Adjust based on typical job size
```

**Commit Timeout:** 10 minutes
```python
# In job_processor.py
self.commit_timeout_seconds = 300  # 5 minutes for faster failure
```

---

## Metrics & Dashboards

### Key Metrics to Monitor

1. **Worker Iteration Rate**
   - Target: >1 iteration/sec when jobs available
   - Alert if: Stuck at same iteration >30s

2. **Job Processing Time**
   - Target: <5 min for <1000 files
   - Alert if: >10 min for any job

3. **Job Failure Rate**
   - Target: <5%
   - Alert if: >10%

4. **Embedding Generation Rate**
   - Target: >10 embeddings/sec
   - Alert if: <1 embedding/sec

5. **Memory Usage**
   - Target: <2GB per service
   - Alert if: >4GB

### Dashboard Access

- **Main Dashboard:** http://localhost:8501
- **API Docs:** http://localhost:8000/docs
- **Embedding API:** http://localhost:8001/docs

---

## Contact & Escalation

### Debug Mode

```bash
# Enable debug logging
docker-compose -f docker-compose.dev.yml down
export LOG_LEVEL=DEBUG
docker-compose -f docker-compose.dev.yml up -d

# View debug logs
docker logs -f ecosystem-mcp-service
```

### Log Locations

- Service logs: `docker logs ecosystem-mcp-service`
- Database logs: `docker logs ecosystem-mcp-postgres`
- Redis logs: `docker logs ecosystem-mcp-redis`

---

## Known Issues & Limitations

### 1. Embedding Service Auto-Unload
**Issue:** Model unloads after 5 minutes inactivity
**Workaround:** Restart service or increase timeout
**Fix:** Disable auto-unload in production

### 2. Large Directory Scans
**Issue:** Scanning 125k+ files takes 5-10 minutes
**Workaround:** Use specific subdirectories
**Fix:** 10k file limit enforced

### 3. Git History Mode Slow
**Issue:** Processing full git history takes hours
**Workaround:** Use snapshot mode for speed
**Alternative:** Use "recent" mode (last 200 commits)

---

*Last Updated: October 22, 2025*
*Version: 1.0 (Post 7-hour debug session)*

