# Comprehensive Feature Test Plan - Phases 1-10
## Testing All Major Features Using Snapshot Mode Ingestion

**Date:** October 22, 2025  
**Based On:** 7-hour debugging session + Implementation plans + Chat history  
**Test Mode:** Snapshot (fastest, most reliable after async fix)

---

## 🎯 Test Strategy

### Why Snapshot Mode?
Based on our investigation:
- ✅ **Fastest:** No git history processing
- ✅ **Most Stable:** Async yielding fix validated
- ✅ **Recently Fixed:** All blocking issues resolved
- ✅ **Production Ready:** Worker loop verified working

### Test Target
Use `/Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp` as test repository:
- **Real-world complexity:** Actual production codebase
- **Known file count:** ~500 files
- **Multiple languages:** Python, YAML, JSON, Markdown
- **Good size:** Large enough to test, small enough to complete quickly

---

## 📋 Test Categories

### Phase 1-4: Core Pipeline (Foundation)
1. Basic Ingestion
2. Document Normalization
3. Embedding Generation
4. Vector Storage
5. Duplicate Detection
6. Job Recovery

### Phase 5-7: Intelligence & Analysis
7. Multi-Format Support
8. Code Analysis
9. Context Generation
10. RAG Querying

### Phase 8-10: Scale & Production
11. Async Yielding (CRITICAL - our fix)
12. Timeout Protection
13. Circuit Breakers
14. Progress Tracking
15. Documentation Generation

---

## 🧪 TEST SUITE

### Test 1: Basic Snapshot Ingestion ✅ (Core Pipeline)

**What We're Testing:**
- File scanning with async yielding
- 10k file limit enforcement
- Directory exclusions
- Worker loop iteration continuity

**Command:**
```bash
curl -X POST http://localhost:8000/api/v1/admin/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "repo_path": "/host/services/ecosystem-mcp",
    "mode": "snapshot"
  }' | jq '{job_id, status}'
```

**Expected Results:**
- Job created with ID
- Status: "queued"
- Worker picks up within 5 seconds
- Completes in 2-5 minutes
- Processed documents: 400-600
- Skipped documents: > 0 (duplicates)
- Worker reaches iteration #2+

**Validation:**
```bash
# Monitor progress
JOB_ID="<from-above>"
watch -n 5 "docker exec ecosystem-mcp-postgres psql -U ecosystem -d ecosystem_mcp -t -c \
  \"SELECT status, processed_documents, total_documents, skipped_documents, embeddings_generated \
   FROM ingestion_jobs WHERE id = '$JOB_ID';\""

# Verify worker iterations
docker logs ecosystem-mcp-service 2>&1 | grep "iteration" | tail -10
```

---

### Test 2: Document Normalization (Phase 1)

**What We're Testing:**
- Multi-format normalization (Python, YAML, JSON, MD)
- Content extraction
- Metadata preservation

**Validation:**
```sql
-- Check document types processed
SELECT 
  original_format,
  COUNT(*) as count
FROM documents
WHERE ingestion_mode = 'snapshot'
GROUP BY original_format
ORDER BY count DESC;

-- Sample normalized content
SELECT 
  file_path,
  LEFT(normalized_content, 200) as preview
FROM documents
WHERE ingestion_mode = 'snapshot'
LIMIT 5;
```

**Expected Results:**
- Multiple formats: .py, .yaml, .json, .md
- Normalized content in markdown format
- File paths preserved

---

### Test 3: Embedding Generation (Phase 2)

**What We're Testing:**
- FastEmbed service integration
- Ollama fallback
- Circuit breaker behavior
- Cache hit rates

**Pre-Test:** Ensure embedding service healthy
```bash
docker restart ecosystem-mcp-embedding
sleep 5
curl http://localhost:8001/health | jq '.status'
```

**Validation:**
```sql
-- Check embedding coverage
SELECT 
  COUNT(*) as total_docs,
  COUNT(embedding_id) as docs_with_embeddings,
  ROUND(COUNT(embedding_id) * 100.0 / COUNT(*), 2) as coverage_pct
FROM documents
WHERE ingestion_mode = 'snapshot';

-- Check embedding service used
SELECT 
  doc_metadata->>'embedding_backend' as backend,
  COUNT(*) as count
FROM documents
WHERE ingestion_mode = 'snapshot'
  AND embedding_id IS NOT NULL
GROUP BY backend;
```

**Expected Results:**
- Coverage: >80% (some files may skip)
- Backend: "fastembed" preferred
- No circuit breaker open errors in logs

---

### Test 4: Duplicate Detection (Phase 3)

**What We're Testing:**
- Content hash-based detection
- Bloom filter efficiency
- Skipped vs Failed distinction

**Test:** Run same ingestion twice
```bash
# First run
curl -X POST http://localhost:8000/api/v1/admin/ingest \
  -H "Content-Type: application/json" \
  -d '{"repo_path": "/host/services/ecosystem-mcp/src/utils", "mode": "snapshot"}'

# Wait for completion, then run again
curl -X POST http://localhost:8000/api/v1/admin/ingest \
  -H "Content-Type: application/json" \
  -d '{"repo_path": "/host/services/ecosystem-mcp/src/utils", "mode": "snapshot"}'
```

**Validation:**
```sql
-- Check duplicate detection
SELECT 
  job.id,
  job.processed_documents,
  job.skipped_documents,
  job.failed_documents
FROM ingestion_jobs job
WHERE job.repo_path LIKE '%/utils'
  AND job.mode = 'snapshot'
ORDER BY job.started_at DESC
LIMIT 2;
```

**Expected Results:**
- First run: processed >0, skipped low
- Second run: processed 0, skipped high (all duplicates)
- Failed: 0 (duplicates not failures)

---

### Test 5: Async Yielding & Timeout (Phase 8 - CRITICAL FIX)

**What We're Testing:**
- Event loop yields during large scans
- Worker continues to iteration #2+
- Timeout protection functional
- No blocking on os.walk()

**Test:** Large directory scan
```bash
curl -X POST http://localhost:8000/api/v1/admin/ingest \
  -H "Content-Type: application/json" \
  -d '{"repo_path": "/host/services", "mode": "snapshot"}'
```

**Monitor in Real-Time:**
```bash
# Watch worker iterations (should keep increasing)
docker logs -f ecosystem-mcp-service 2>&1 | grep "iteration"

# Watch file scanning progress
docker logs -f ecosystem-mcp-service 2>&1 | grep "Scanned.*files"
```

**Validation:**
```bash
# Check iterations continued
ITERATIONS=$(docker logs ecosystem-mcp-service 2>&1 | grep "Worker loop iteration" | wc -l)
echo "Total iterations: $ITERATIONS"
# Should be >5

# Check no timeout fired
docker logs ecosystem-mcp-service 2>&1 | grep "timed out"
# Should be empty for valid job

# Check yielding occurred
docker logs ecosystem-mcp-service 2>&1 | grep "Scanned.*files"
# Should see periodic progress
```

**Expected Results:**
- Worker reaches iterations #2, #3, #4+
- Job completes without timeout
- Periodic "Scanned X files" logs
- File limit warning if >10k files found

---

### Test 6: Circuit Breaker & Fallback (Phase 8)

**What We're Testing:**
- Circuit breaker protects services
- Fallback to Ollama when FastEmbed fails
- Smart retry with health checks
- Startup grace period

**Test:** Simulate embedding service failure
```bash
# 1. Start job
curl -X POST http://localhost:8000/api/v1/admin/ingest \
  -H "Content-Type: application/json" \
  -d '{"repo_path": "/host/services/ecosystem-mcp/src/api", "mode": "snapshot"}'

# 2. Stop embedding service mid-job
sleep 10
docker stop ecosystem-mcp-embedding

# 3. Monitor fallback behavior
docker logs -f ecosystem-mcp-service 2>&1 | grep -E "Circuit breaker|Fallback|Ollama"

# 4. Restart embedding service
docker start ecosystem-mcp-embedding
```

**Validation:**
```bash
# Check for circuit breaker activation
docker logs ecosystem-mcp-service 2>&1 | grep "Circuit breaker" | tail -10

# Check fallback occurred
docker logs ecosystem-mcp-service 2>&1 | grep "falling back to Ollama"

# Check smart retry
docker logs ecosystem-mcp-service 2>&1 | grep "Smart retry successful"
```

**Expected Results:**
- Circuit breaker opens after failures
- Automatic fallback to Ollama
- Job completes despite service failure
- Circuit breaker resets when service returns

---

### Test 7: Progress Tracking (Phase 4)

**What We're Testing:**
- Real-time progress updates
- Redis pub/sub
- Accurate metrics
- Dashboard updates

**Test:**
```bash
# Start job
JOB_ID=$(curl -X POST http://localhost:8000/api/v1/admin/ingest \
  -H "Content-Type: application/json" \
  -d '{"repo_path": "/host/services/ecosystem-mcp", "mode": "snapshot"}' | \
  jq -r '.job_id')

# Monitor progress via API
while true; do
  curl -s "http://localhost:8000/api/v1/admin/jobs/$JOB_ID" | \
    jq '{status, processed, total, progress_pct}'
  sleep 5
done
```

**Dashboard Check:**
Open http://localhost:8501 and verify:
- Job appears in list
- Progress bar updates
- Metrics update in real-time

**Expected Results:**
- Progress increases steadily
- Metrics accurate
- Dashboard responsive
- Final metrics match DB

---

### Test 8: Context Generation (Phase 9)

**What We're Testing:**
- Repository context creation
- Technology detection
- Service identification
- Metadata extraction

**Validation:**
```sql
-- Check if context generated
SELECT 
  COUNT(*) as docs_with_service,
  doc_metadata->>'service_name' as service_name
FROM documents
WHERE ingestion_mode = 'snapshot'
  AND doc_metadata->>'service_name' IS NOT NULL
GROUP BY service_name;

-- Check technology detection
SELECT DISTINCT
  doc_metadata->>'technologies' as techs
FROM documents
WHERE ingestion_mode = 'snapshot'
  AND doc_metadata->>'technologies' IS NOT NULL
LIMIT 10;
```

**Expected Results:**
- Service name: "ecosystem-mcp" detected
- Technologies: Python, FastAPI, AsyncIO detected
- File classifications present

---

### Test 9: RAG Query (Phase 5)

**What We're Testing:**
- Vector search working
- Context filtering
- Embedding retrieval
- Response generation

**Pre-Test:** Wait for embeddings to complete

**Test Query:**
```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How does the worker loop handle job processing?",
    "n_results": 5
  }' | jq '.'
```

**Expected Results:**
- Results returned (5 documents)
- Relevant to worker loop
- Documents from ingested repo
- Similarity scores present

---

### Test 10: Multi-Pass Documentation (Phase 10)

**What We're Testing:**
- Documentation generation
- Multi-pass refinement
- Context awareness
- Output quality

**Test:**
```bash
curl -X POST http://localhost:8000/api/v1/documentation/generate \
  -H "Content-Type: application/json" \
  -d '{
    "target_path": "/host/services/ecosystem-mcp/src/services/ingestion",
    "passes": 3,
    "output_format": "markdown"
  }' | jq '{job_id, status}'
```

**Validation:**
Check generated documentation quality:
- Architecture overview present
- Key components documented
- Code examples included
- Cross-references working

---

## 🎯 Master Test Script

Create automated test runner:

```bash
#!/bin/bash
# save as: run_comprehensive_tests.sh

set -e

echo "🧪 Comprehensive Feature Test Suite"
echo "===================================="
echo ""

# Pre-flight checks
echo "✈️  Pre-flight checks..."
./check_health.sh || exit 1
echo ""

# Test 1: Basic Ingestion
echo "📝 Test 1: Basic Snapshot Ingestion"
JOB1=$(curl -s -X POST http://localhost:8000/api/v1/admin/ingest \
  -H "Content-Type: application/json" \
  -d '{"repo_path": "/host/services/ecosystem-mcp/src/utils", "mode": "snapshot"}' | \
  jq -r '.job_id')

echo "Job ID: $JOB1"
echo "Waiting for completion..."

# Wait for job to complete (max 5 min)
for i in {1..60}; do
  STATUS=$(docker exec ecosystem-mcp-postgres psql -U ecosystem -d ecosystem_mcp -t -c \
    "SELECT status FROM ingestion_jobs WHERE id = '$JOB1';" | tr -d ' \n')
  
  if [ "$STATUS" == "completed" ] || [ "$STATUS" == "failed" ]; then
    break
  fi
  sleep 5
done

# Check results
docker exec ecosystem-mcp-postgres psql -U ecosystem -d ecosystem_mcp -c \
  "SELECT status, processed_documents, skipped_documents, embeddings_generated \
   FROM ingestion_jobs WHERE id = '$JOB1';"

if [ "$STATUS" == "completed" ]; then
  echo "✅ Test 1 PASSED"
else
  echo "❌ Test 1 FAILED"
  exit 1
fi
echo ""

# Test 2: Duplicate Detection
echo "📝 Test 2: Duplicate Detection"
JOB2=$(curl -s -X POST http://localhost:8000/api/v1/admin/ingest \
  -H "Content-Type: application/json" \
  -d '{"repo_path": "/host/services/ecosystem-mcp/src/utils", "mode": "snapshot"}' | \
  jq -r '.job_id')

echo "Job ID: $JOB2 (should skip all)"
sleep 30

# Check high skip rate
SKIPPED=$(docker exec ecosystem-mcp-postgres psql -U ecosystem -d ecosystem_mcp -t -c \
  "SELECT skipped_documents FROM ingestion_jobs WHERE id = '$JOB2';" | tr -d ' \n')

if [ "$SKIPPED" -gt "50" ]; then
  echo "✅ Test 2 PASSED (Skipped: $SKIPPED)"
else
  echo "❌ Test 2 FAILED (Skipped: $SKIPPED)"
fi
echo ""

# Test 3: Worker Iterations
echo "📝 Test 3: Worker Loop Iterations"
ITERATIONS=$(docker logs ecosystem-mcp-service 2>&1 | grep "Worker loop iteration" | wc -l)

if [ "$ITERATIONS" -gt "5" ]; then
  echo "✅ Test 3 PASSED (Iterations: $ITERATIONS)"
else
  echo "❌ Test 3 FAILED (Iterations: $ITERATIONS)"
fi
echo ""

# Test 4: Embedding Coverage
echo "📝 Test 4: Embedding Generation"
COVERAGE=$(docker exec ecosystem-mcp-postgres psql -U ecosystem -d ecosystem_mcp -t -c \
  "SELECT ROUND(COUNT(embedding_id) * 100.0 / COUNT(*), 2) \
   FROM documents WHERE ingestion_mode = 'snapshot';" | tr -d ' \n')

echo "Embedding Coverage: $COVERAGE%"
if (( $(echo "$COVERAGE > 50" | bc -l) )); then
  echo "✅ Test 4 PASSED"
else
  echo "⚠️  Test 4 WARNING (Coverage low)"
fi
echo ""

# Test 5: RAG Query
echo "📝 Test 5: RAG Query"
RESULTS=$(curl -s -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "worker loop", "n_results": 3}' | jq '.results | length')

if [ "$RESULTS" -gt "0" ]; then
  echo "✅ Test 5 PASSED (Results: $RESULTS)"
else
  echo "❌ Test 5 FAILED"
fi
echo ""

echo "🎉 Test Suite Complete!"
echo ""
echo "Summary:"
docker exec ecosystem-mcp-postgres psql -U ecosystem -d ecosystem_mcp -c \
  "SELECT 
     COUNT(*) as total_jobs,
     SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
     SUM(processed_documents) as total_processed,
     SUM(skipped_documents) as total_skipped,
     SUM(embeddings_generated) as total_embeddings
   FROM ingestion_jobs
   WHERE mode = 'snapshot';"
```

---

## 📊 Success Criteria

### Must Pass
- ✅ All jobs complete successfully
- ✅ Worker reaches iteration #2+
- ✅ No timeout on valid jobs
- ✅ Duplicate detection working
- ✅ Embedding coverage >50%

### Should Pass
- ✅ Embedding coverage >80%
- ✅ Circuit breakers activate appropriately
- ✅ Fallback mechanisms work
- ✅ Progress tracking accurate
- ✅ RAG queries return results

### Nice to Have
- ✅ Documentation generation works
- ✅ Context detection accurate
- ✅ Dashboard updates in real-time
- ✅ Performance within targets

---

## 🚀 Execution Plan

### Step 1: Environment Preparation
```bash
# Ensure services healthy
docker-compose -f docker-compose.dev.yml ps
./check_health.sh

# Clear old test data if needed
docker exec ecosystem-mcp-postgres psql -U ecosystem -d ecosystem_mcp -c \
  "DELETE FROM documents WHERE ingestion_mode = 'snapshot';"
  
docker exec ecosystem-mcp-postgres psql -U ecosystem -d ecosystem_mcp -c \
  "DELETE FROM ingestion_jobs WHERE mode = 'snapshot';"
```

### Step 2: Run Tests
```bash
chmod +x run_comprehensive_tests.sh
./run_comprehensive_tests.sh 2>&1 | tee test_results.log
```

### Step 3: Analyze Results
```bash
# Check for failures
grep "FAILED" test_results.log

# View summary
tail -20 test_results.log

# Check worker health
docker logs ecosystem-mcp-service 2>&1 | grep "iteration" | tail -20
```

---

## 📝 Test Results Template

```
# Test Results - [Date]

## Environment
- Services: All Healthy ✅
- Worker: Running ✅
- Embedding Service: Healthy ✅

## Test Results

### Test 1: Basic Ingestion
- Status: ✅ PASSED
- Job ID: xxx
- Processed: 60 docs
- Time: 45s

### Test 2: Duplicate Detection
- Status: ✅ PASSED
- Skipped: 60/60 docs (100%)

### Test 3: Worker Iterations
- Status: ✅ PASSED
- Iterations: 8

### Test 4: Embedding Coverage
- Status: ✅ PASSED
- Coverage: 85%

### Test 5: RAG Query
- Status: ✅ PASSED
- Results: 5 relevant docs

## Summary
- Tests Passed: 5/5
- System Status: ✅ PRODUCTION READY
- Next Steps: Deploy to production

## Notes
- Async yielding fix validated ✅
- Worker loop stable ✅
- All major features operational ✅
```

---

*Test plan based on 7-hour debugging session learnings and comprehensive implementation plans*

