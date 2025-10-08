# 🚀 RAG Quick Reference Card

## One-Line Summary
**RAG** = Semantic Search → Context Building → LLM Generation → Cited Answer

---

## Quick Commands

### Generate Embeddings (First Time Setup)
```bash
curl -X POST "http://localhost:5087/api/v1/embeddings/generate-batch?limit=100"
```

### Check Coverage
```bash
curl "http://localhost:5087/api/v1/embeddings/stats" | jq
```

### Semantic Search
```bash
curl -X POST "http://localhost:5087/api/v1/search/semantic" \
  -G --data-urlencode "query=your question" \
  --data-urlencode "limit=10" | jq
```

### RAG Answer (THE MAIN ONE!)
```bash
curl -X POST "http://localhost:5087/api/v1/synthesis/generate" \
  -G --data-urlencode "query=What is the Horus Heresy?" \
  --data-urlencode "temperature=0.3" \
  --data-urlencode "max_tokens=500" | jq
```

---

## Response Format

```json
{
  "success": true,
  "data": {
    "answer": "The Horus Heresy was...",
    "query": "What is the Horus Heresy?",
    "sources": ["doc-1", "doc-2"],
    "model": "llama3.2:3b",
    "synthesis_method": "rag",
    "context_documents_used": 5
  }
}
```

---

## Configuration Presets

### 📖 **Documentation Q&A** (Recommended)
```bash
temperature=0.3  semantic_weight=0.7  max_tokens=500
```

### 🎯 **Precise Factual**
```bash
temperature=0.1  semantic_weight=0.8  max_tokens=300
```

### 💬 **Conversational**
```bash
temperature=0.5  semantic_weight=0.6  max_tokens=800
```

---

## Architecture

```
Query → Embed → Search (hybrid) → Top 5 docs → LLM → Answer + Sources
  ↓        ↓         ↓              ↓            ↓         ↓
 Text   Vector   Similarity    Context      Generate  Verify
        [384d]   0.3-1.0      ~4000 chars    3-5s     Cited
```

---

## Key Metrics

| Operation | Time | Notes |
|-----------|------|-------|
| Embed query | ~50ms | One-time per query |
| Semantic search | ~150ms | Depends on doc count |
| LLM generation | ~3-5s | Main bottleneck |
| **Total** | **~3-6s** | Acceptable for Q&A |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| No results | Check embeddings: `/embeddings/stats` |
| Generic answers | Lower `min_similarity` to 0.2 |
| Slow | Reduce `max_tokens` or use GPU |
| Hallucination | RAG doesn't hallucinate (grounded) |

---

## Full Documentation
- Technical: `docs/VECTORIZATION_IMPLEMENTATION_SUMMARY.md`
- User Guide: `horus_heresy_demo/reports/VECTORIZATION_GUIDE.md`
- Examples: `RAG_DEMO_SHOWCASE.md`

