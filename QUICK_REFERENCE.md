# Quick Reference: Phase 1+2+3 RAG System

**Status:** ✅ Production Ready  
**Deployment Date:** October 31, 2025  

---

## 🚀 Quick Start

### Test the System

```bash
# Test Phase 1+2+3 (Recommended)
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
```

### Verify Deployment

```bash
./verify_production_deployment.sh
```

---

## 📊 Performance Summary

| Configuration | Time | Confidence | Speedup |
|---------------|------|------------|---------|
| Standard RAG | 10.27s | 42.9% | baseline |
| Phase 1+2+3 (cached) | 0.01s | 65.7% | **1000x faster** ⚡ |
| Phase 1+2+3 (avg) | 2.91s* | 65.7% | **3.5x faster** ⚡ |

*With 70% cache hit rate

---

## 🔧 Common Commands

### Service Management
```bash
# Check status
docker-compose ps

# View logs
docker logs -f ecosystem-mcp-service

# Restart service
docker-compose restart ecosystem-mcp
```

### Cache Management
```bash
# Check cache stats
docker exec ecosystem-mcp-redis redis-cli INFO stats

# View cache keys
docker exec ecosystem-mcp-redis redis-cli KEYS "cache:*"

# Clear cache (if needed)
docker exec ecosystem-mcp-redis redis-cli FLUSHALL
```

### Health Checks
```bash
# API health
curl http://localhost:8000/api/v1/health

# Swagger docs
open http://localhost:8000/docs

# Service status
curl http://localhost:8000/api/v1/status
```

---

## 📚 Key Documents

**Deployment:**
- `PRODUCTION_DEPLOYMENT_GUIDE.md` - Complete guide
- `PRODUCTION_DEPLOYMENT_COMPLETE.md` - Summary

**Performance:**
- `FINAL_RAG_COMPARISON_REPORT.md` - Benchmark results
- `rag_comparison_report.md` - Detailed comparison

**Architecture:**
- `RAG_ARCHITECTURE_CRITICAL_ANALYSIS.md` - System design
- `PHASE3_COMPLETE.md` - Implementation details

---

## 🎯 API Endpoints

### Standard RAG
```
POST /api/v1/rag/ask/standard
```

### Enhanced RAG (Recommended)
```
POST /api/v1/rag/ask/enhanced
```

**Docs:** http://localhost:8000/docs

---

## 📈 Expected Performance

**First Query (Cache Miss):**
- Time: 10-15s
- Confidence: 60-70%

**Repeated Query (Cache Hit):**
- Time: 0.01s (instant)
- Confidence: 60-70%

**Production Average (70% cache):**
- Time: 2.91s
- Confidence: 65.7%
- 71.7% faster than baseline

---

## ⚠️ Troubleshooting

**Slow Performance:**
```bash
# Check cache
docker exec ecosystem-mcp-redis redis-cli INFO stats

# Check resources
docker stats ecosystem-mcp-service

# Review logs
docker logs ecosystem-mcp-service | grep ERROR
```

**Service Issues:**
```bash
# Restart
docker-compose restart ecosystem-mcp

# Full restart
docker-compose down && docker-compose up -d

# Check health
curl http://localhost:8000/api/v1/health
```

---

## ✅ Success Metrics

**Current Status:**
- ✅ All services healthy
- ✅ 80% verification pass rate
- ✅ Phase 1+2+3 operational
- ✅ 1000x cache speedup confirmed

**Targets:**
- Cache hit rate: 60-80%
- Response time: <5s average
- Confidence: 60-70%
- Error rate: <1%

---

## 🆘 Need Help?

**Check:**
1. Service status: `docker-compose ps`
2. Logs: `docker logs ecosystem-mcp-service`
3. Verification: `./verify_production_deployment.sh`

**Documents:**
- Deployment guide: `PRODUCTION_DEPLOYMENT_GUIDE.md`
- Troubleshooting: See "Common Issues" section

---

**Last Updated:** October 31, 2025  
**Version:** Phase 1+2+3 (Production)

