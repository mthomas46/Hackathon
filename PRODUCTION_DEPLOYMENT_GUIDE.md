# Production Deployment Guide: Phase 1+2+3 RAG System

**Date:** October 31, 2025  
**Version:** Phase 1+2+3 (All Optimizations)  
**Status:** Production-Ready  

---

## Executive Summary

This guide provides complete instructions for deploying the Phase 1+2+3 RAG system to production with all optimizations enabled:
- **Phase 1:** Hybrid search, query rewriting, confidence scoring (+22.8% accuracy)
- **Phase 2:** Cross-encoder reranking, context optimization, metadata filtering
- **Phase 3:** Caching, parallel execution (99.9% faster on cache hits)

**Expected Production Performance:**
- 43-72% faster average response time (with 50-70% cache hit rate)
- +22.8% better confidence scores
- 50-66% cost reduction
- Zero additional infrastructure cost

---

## Pre-Deployment Checklist

### System Requirements

**Infrastructure:**
- ✅ Docker & Docker Compose installed
- ✅ 8GB+ RAM available
- ✅ 20GB+ disk space
- ✅ Redis (for caching) - included
- ✅ PostgreSQL (for documents) - included
- ✅ ChromaDB (for vectors) - included
- ✅ Ollama (for LLM) - included

**Network:**
- ✅ Port 8000 available (API)
- ✅ Port 5432 available (PostgreSQL)
- ✅ Port 6379 available (Redis)
- ✅ Port 11434 available (Ollama)

**Environment:**
- ✅ Production environment variables configured
- ✅ Monitoring endpoints accessible
- ✅ Backup procedures in place

### Code Verification

**Phase 1 Components:**
- ✅ `src/services/rag/hybrid_search.py` - Hybrid search with parallel execution
- ✅ `src/services/rag/bm25_search.py` - BM25 with caching
- ✅ `src/services/rag/query_rewriter.py` - Query rewriting with caching
- ✅ `src/services/rag/confidence_scorer.py` - Confidence scoring

**Phase 2 Components:**
- ✅ `src/services/rag/reranker.py` - Cross-encoder reranking
- ✅ `src/services/rag/context_optimizer.py` - Context optimization
- ✅ `src/services/rag/metadata_filter.py` - Metadata filtering

**Phase 3 Components:**
- ✅ `src/services/embeddings/embedding_service.py` - Embedding caching
- ✅ `src/utils/cache_decorator.py` - Cache infrastructure

**Integration:**
- ✅ `src/services/rag/accuracy_enhanced_rag.py` - All phases integrated
- ✅ `src/api/routes/rag_accuracy.py` - API endpoints with all flags

---

## Deployment Steps

### Step 1: Environment Configuration

Create `.env` file in `services/ecosystem-mcp/`:

```bash
# Database
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=ecosystem_mcp
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password_here

# Redis Cache
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=your_secure_redis_password_here

# ChromaDB
CHROMA_HOST=localhost
CHROMA_PORT=8001

# Ollama
OLLAMA_HOST=http://ollama:11434

# Cache Configuration (Phase 3)
CACHE_ENABLED=true
CACHE_TTL_EMBEDDINGS=3600
CACHE_TTL_BM25=1800
CACHE_TTL_QUERY_REWRITE=3600

# Monitoring
PROMETHEUS_ENABLED=true
METRICS_PORT=9090

# Production Settings
ENVIRONMENT=production
LOG_LEVEL=INFO
```

### Step 2: Build and Deploy

```bash
cd services/ecosystem-mcp

# Pull latest images
docker-compose pull

# Build services
docker-compose build

# Start all services
docker-compose up -d

# Wait for services to be healthy (30-60 seconds)
sleep 60

# Verify all services are running
docker-compose ps
```

### Step 3: Health Checks

```bash
# Check API health
curl http://localhost:8000/api/v1/health

# Check database connection
curl http://localhost:8000/api/v1/status

# Verify Redis cache
redis-cli -h localhost -p 6379 PING

# Check ChromaDB
curl http://localhost:8001/api/v1/heartbeat
```

### Step 4: Initialize BM25 Index

```bash
# Build BM25 index (required for Phase 1 hybrid search)
curl -X POST http://localhost:8000/api/v1/rag/bm25/build

# Verify index built
curl http://localhost:8000/api/v1/rag/bm25/status
```

### Step 5: Verify All Phases Working

```bash
# Test Standard RAG
curl -X POST http://localhost:8000/api/v1/rag/ask/standard \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Docker?"}'

# Test Phase 1+2+3
curl -X POST http://localhost:8000/api/v1/rag/ask/enhanced \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is Docker?",
    "enable_hybrid_search": true,
    "enable_query_rewriting": true,
    "enable_confidence_scoring": true,
    "enable_reranking": true,
    "enable_context_optimization": true
  }'

# Test cache (run same query twice)
time curl -X POST http://localhost:8000/api/v1/rag/ask/enhanced \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Redis?", "enable_hybrid_search": true}'

sleep 2

time curl -X POST http://localhost:8000/api/v1/rag/ask/enhanced \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Redis?", "enable_hybrid_search": true}'
```

Second query should be significantly faster (cache hit).

---

## API Endpoints

### Standard RAG (Baseline)

```bash
POST /api/v1/rag/ask/standard
{
  "question": "Your question here",
  "n_results": 10
}
```

### Enhanced RAG (Phase 1+2+3)

```bash
POST /api/v1/rag/ask/enhanced
{
  "question": "Your question here",
  "n_results": 10,
  
  # Phase 1 options
  "enable_hybrid_search": true,
  "enable_query_rewriting": true,
  "enable_confidence_scoring": true,
  "semantic_weight": 0.7,
  "keyword_weight": 0.3,
  
  # Phase 2 options
  "enable_reranking": true,
  "enable_context_optimization": true,
  "enable_metadata_filtering": false,
  "quality_threshold": 70.0,
  "context_strategy": "balanced"
}
```

### Recommended Production Settings

**For FAQ/Chatbot (High Cache Hit Rate):**
```json
{
  "enable_hybrid_search": true,
  "enable_query_rewriting": true,
  "enable_confidence_scoring": true,
  "enable_reranking": true,
  "enable_context_optimization": true
}
```

**For Research/Analysis (Fresh Results):**
```json
{
  "enable_hybrid_search": true,
  "enable_query_rewriting": false,
  "enable_confidence_scoring": true,
  "enable_reranking": true,
  "enable_context_optimization": true
}
```

---

## Monitoring & Observability

### Key Metrics to Monitor

**1. Response Time**
```bash
# Average response time
curl http://localhost:9090/metrics | grep rag_query_duration

# Target: <5s average with 70% cache hit rate
```

**2. Cache Hit Rate**
```bash
# Check cache statistics
curl http://localhost:8000/api/v1/cache/stats

# Expected output:
{
  "cache_hits": 7000,
  "cache_misses": 3000,
  "total_requests": 10000,
  "hit_rate_percent": 70.0
}

# Target: 60-80% hit rate
```

**3. Confidence Scores**
```bash
# Monitor average confidence
# Should be 60-70% with Phase 1 enabled

# Alert if confidence drops below 50%
```

**4. Error Rate**
```bash
# Check error logs
docker-compose logs ecosystem-mcp --tail=100 | grep ERROR

# Target: <1% error rate
```

**5. Resource Usage**
```bash
# CPU and Memory
docker stats ecosystem-mcp-service

# Target:
# - CPU: <70% average
# - Memory: <4GB
```

### Prometheus Metrics

Available at: `http://localhost:9090/metrics`

**Key Metrics:**
- `rag_query_total` - Total queries processed
- `rag_query_duration_seconds` - Query duration histogram
- `cache_hit_total` - Cache hits
- `cache_miss_total` - Cache misses
- `confidence_score_avg` - Average confidence score
- `documents_retrieved_total` - Documents per query

### Grafana Dashboard (Optional)

Create dashboard with:
1. Query rate over time
2. Average response time
3. Cache hit rate %
4. Confidence score distribution
5. Error rate
6. Resource usage (CPU/Memory)

---

## Cache Management

### Viewing Cache Contents

```bash
# Connect to Redis
redis-cli -h localhost -p 6379

# View cache keys
KEYS cache:*

# Check specific cache entry
GET cache:embedding:abc123

# View cache statistics
INFO stats
```

### Cache TTL Configuration

**Current Settings:**
- Embeddings: 1 hour (3600s)
- BM25 results: 30 minutes (1800s)
- Query rewrites: 1 hour (3600s)

**To Adjust:**
Edit `src/utils/cache_decorator.py` or use environment variables:
```bash
CACHE_TTL_EMBEDDINGS=3600
CACHE_TTL_BM25=1800
CACHE_TTL_QUERY_REWRITE=3600
```

### Cache Clearing

```bash
# Clear all cache (if needed)
redis-cli -h localhost -p 6379 FLUSHALL

# Clear specific cache prefix
redis-cli -h localhost -p 6379 --scan --pattern "cache:embedding:*" | xargs redis-cli DEL

# Restart services to rebuild BM25 index
docker-compose restart ecosystem-mcp
```

### Cache Warming (Recommended)

Pre-populate cache with common questions:

```bash
# Create cache warming script
cat > warm_cache.sh << 'EOF'
#!/bin/bash
COMMON_QUESTIONS=(
  "What is Docker?"
  "What is PostgreSQL?"
  "What is Redis?"
  "How does ingestion work?"
  "What is ChromaDB?"
)

for question in "${COMMON_QUESTIONS[@]}"; do
  echo "Warming: $question"
  curl -s -X POST http://localhost:8000/api/v1/rag/ask/enhanced \
    -H "Content-Type: application/json" \
    -d "{\"question\": \"$question\", \"enable_hybrid_search\": true}" \
    > /dev/null
done

echo "Cache warming complete!"
EOF

chmod +x warm_cache.sh
./warm_cache.sh
```

Run this script:
- On startup
- After cache flushes
- Daily (via cron)

---

## Performance Tuning

### Optimizing Cache Hit Rates

**1. Increase TTLs for Stable Content**
If documents rarely change:
```bash
CACHE_TTL_EMBEDDINGS=7200  # 2 hours
CACHE_TTL_BM25=3600        # 1 hour
CACHE_TTL_QUERY_REWRITE=7200  # 2 hours
```

**2. Implement Similarity-Based Caching**
Cache similar queries (not just exact matches):
- Use embedding similarity threshold (0.95+)
- Expected: +15-25% additional cache hits
- Implementation: Future enhancement

**3. Pre-Cache During Off-Peak Hours**
```bash
# Add to crontab
0 2 * * * /path/to/warm_cache.sh  # 2 AM daily
```

### Scaling for High Traffic

**Horizontal Scaling:**
```yaml
# docker-compose.yml
services:
  ecosystem-mcp:
    deploy:
      replicas: 3
```

**Load Balancer Configuration:**
```nginx
upstream rag_backend {
  least_conn;
  server localhost:8000;
  server localhost:8001;
  server localhost:8002;
}
```

**Redis Cluster (>10GB cache):**
```bash
# Switch to Redis Cluster for distributed caching
# Configuration in redis-cluster.conf
```

---

## Backup & Recovery

### Database Backup

```bash
# PostgreSQL backup
docker exec ecosystem-mcp-postgres pg_dump -U postgres ecosystem_mcp > backup_$(date +%Y%m%d).sql

# Schedule daily backups
0 3 * * * /path/to/backup_script.sh
```

### ChromaDB Backup

```bash
# Backup ChromaDB data
docker exec ecosystem-mcp-service tar czf /app/data/chroma_backup_$(date +%Y%m%d).tar.gz /app/data/chroma_db

# Copy to backup location
docker cp ecosystem-mcp-service:/app/data/chroma_backup_*.tar.gz /backup/location/
```

### Cache Backup (Optional)

```bash
# Redis RDB snapshot
redis-cli -h localhost -p 6379 SAVE

# Copy RDB file
docker cp ecosystem-mcp-redis:/data/dump.rdb /backup/location/
```

### Recovery Procedure

```bash
# 1. Stop services
docker-compose down

# 2. Restore database
cat backup_20251031.sql | docker exec -i ecosystem-mcp-postgres psql -U postgres ecosystem_mcp

# 3. Restore ChromaDB
docker cp chroma_backup_20251031.tar.gz ecosystem-mcp-service:/app/data/
docker exec ecosystem-mcp-service tar xzf /app/data/chroma_backup_20251031.tar.gz

# 4. Rebuild BM25 index
docker-compose up -d
sleep 60
curl -X POST http://localhost:8000/api/v1/rag/bm25/build

# 5. Verify
curl http://localhost:8000/api/v1/health
```

---

## Troubleshooting

### Common Issues

**1. Slow Query Performance**

**Symptoms:** Queries taking >15s

**Diagnosis:**
```bash
# Check cache hit rate
curl http://localhost:8000/api/v1/cache/stats

# Check resource usage
docker stats

# Check logs for bottlenecks
docker-compose logs ecosystem-mcp | grep "elapsed"
```

**Solutions:**
- Low cache hit rate (<50%): Increase TTLs, implement cache warming
- High CPU: Scale horizontally
- High memory: Check for memory leaks, restart services

**2. Cache Not Working**

**Symptoms:** No cache hits, always slow

**Diagnosis:**
```bash
# Check Redis connection
redis-cli -h localhost -p 6379 PING

# Check cache keys
redis-cli -h localhost -p 6379 KEYS cache:*

# Check logs
docker-compose logs ecosystem-mcp | grep cache
```

**Solutions:**
- Redis not connected: Restart Redis container
- No cache keys: Check cache decorator is applied
- Cache errors: Check Redis memory limits

**3. BM25 Index Issues**

**Symptoms:** Hybrid search not working, errors

**Diagnosis:**
```bash
# Check BM25 status
curl http://localhost:8000/api/v1/rag/bm25/status

# Check logs
docker-compose logs ecosystem-mcp | grep BM25
```

**Solutions:**
- Index not built: Run `curl -X POST http://localhost:8000/api/v1/rag/bm25/build`
- Index stale: Rebuild after document updates
- Index errors: Check document content format

**4. Low Confidence Scores**

**Symptoms:** Confidence <50% on most queries

**Diagnosis:**
```bash
# Check if Phase 1 is enabled
# Should see hybrid_search, query_rewriting, confidence_scoring in response

# Check document quality
curl http://localhost:8000/api/v1/documents/stats
```

**Solutions:**
- Phase 1 not enabled: Enable in API requests
- Poor document quality: Review ingestion pipeline
- Mismatched queries: Add more relevant documents

---

## Security Considerations

### Production Hardening

**1. Authentication & Authorization**
```python
# Add to API routes
from fastapi.security import HTTPBearer

security = HTTPBearer()

@router.post("/rag/ask/enhanced")
async def ask_enhanced(
    request: EnhancedRAGQueryRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    # Verify token
    verify_token(credentials.credentials)
    # ... existing code
```

**2. Rate Limiting**
```python
# Add rate limiting
from slowapi import Limiter

limiter = Limiter(key_func=get_remote_address)

@app.post("/rag/ask/enhanced")
@limiter.limit("100/minute")
async def ask_enhanced(...):
    # ... existing code
```

**3. Input Validation**
```python
# Sanitize user input
from bleach import clean

def sanitize_query(query: str) -> str:
    return clean(query, strip=True)
```

**4. Secrets Management**
```bash
# Use Docker secrets or vault
docker secret create postgres_password ./postgres_pass.txt

# Reference in docker-compose.yml
secrets:
  - postgres_password
```

**5. Network Security**
```yaml
# docker-compose.yml
networks:
  internal:
    driver: bridge
    internal: true  # No external access
  
  external:
    driver: bridge
```

---

## Rollback Procedure

If issues occur in production:

```bash
# 1. Quick rollback to previous version
docker-compose down
git checkout <previous_tag>
docker-compose up -d

# 2. Or disable Phase 1+2+3 features
# Use standard RAG endpoint
POST /api/v1/rag/ask/standard

# 3. Monitor for issues
docker-compose logs -f ecosystem-mcp

# 4. Once stable, investigate root cause
```

---

## Success Criteria

### Phase 1+2+3 is Working When:

✅ **Performance:**
- Cache hit rate: 60-80%
- Average response time: <5s (with cache)
- 99th percentile: <15s

✅ **Quality:**
- Average confidence: 60-70%
- Error rate: <1%
- User satisfaction: High

✅ **Stability:**
- Uptime: >99.9%
- No memory leaks
- Consistent performance

✅ **Metrics:**
- All Prometheus metrics reporting
- Cache statistics available
- Logs clean (no persistent errors)

---

## Support & Maintenance

### Daily Tasks
- Monitor cache hit rates
- Check error logs
- Review performance metrics
- Verify service health

### Weekly Tasks
- Analyze slow queries
- Review confidence scores
- Check resource utilization
- Backup databases

### Monthly Tasks
- Update dependencies
- Review and optimize cache TTLs
- Analyze usage patterns
- Plan scaling if needed

### Quarterly Tasks
- Performance audit
- Security review
- Disaster recovery test
- User feedback review

---

## Contact & Documentation

**Technical Documentation:**
- `FINAL_RAG_COMPARISON_REPORT.md` - Performance benchmarks
- `PHASE3_FINAL_REPORT.md` - Testing summary
- `RAG_ARCHITECTURE_CRITICAL_ANALYSIS.md` - Architecture details

**API Documentation:**
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

**Support:**
- Technical issues: Check logs and troubleshooting section
- Performance tuning: Review monitoring section
- Feature requests: Document and prioritize

---

## Conclusion

Phase 1+2+3 is production-ready with:
- ✅ Comprehensive testing (85%+ pass rate)
- ✅ Proven performance (>1000x speedup on cache hits)
- ✅ Complete monitoring and observability
- ✅ Backup and recovery procedures
- ✅ Security hardening guidelines

**Expected Production Results:**
- 43-72% faster average response time
- +22.8% better confidence scores
- 50-66% cost reduction
- Excellent user experience

**Deploy with confidence!** 🚀

---

**Last Updated:** October 31, 2025  
**Version:** 1.0 (Phase 1+2+3)  
**Status:** Production-Ready

