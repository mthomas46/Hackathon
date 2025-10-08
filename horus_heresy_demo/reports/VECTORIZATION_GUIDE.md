# 🔬 Vectorization & Semantic Search Guide

**MCP Knowledge Base Ecosystem - Advanced Capabilities**

---

## 📖 Table of Contents

1. [Introduction](#introduction)
2. [What is Vectorization?](#what-is-vectorization)
3. [Why Semantic Search?](#why-semantic-search)
4. [How It Works](#how-it-works)
5. [Using the APIs](#using-the-apis)
6. [Performance & Scaling](#performance--scaling)
7. [Best Practices](#best-practices)

---

## Introduction

The MCP ecosystem now includes advanced vectorization and semantic search capabilities,
enabling intelligent document retrieval and answer synthesis that goes beyond simple keyword matching.

**Key Benefits:**
- 🎯 Find documents by meaning, not just keywords
- 🤖 Generate intelligent answers from multiple sources (RAG)
- 🔄 Hybrid search combining keyword + semantic approaches
- ⚡ Sub-second search across thousands of documents

---

## What is Vectorization?

### The Concept

**Vectorization** converts text into numerical vectors (arrays of numbers) that capture semantic meaning.

```
"Machine learning algorithms" → [0.23, -0.15, 0.67, ..., 0.42] (384 dimensions)
"AI and neural networks"     → [0.25, -0.14, 0.65, ..., 0.40] (384 dimensions)
```

Similar concepts have similar vectors, enabling **semantic similarity search**.

### The Model

- **Model:** sentence-transformers/all-MiniLM-L6-v2
- **Dimensions:** 384
- **Training:** Millions of sentence pairs
- **Use Case:** General-purpose semantic similarity

---

## Why Semantic Search?

### Traditional Keyword Search Limitations

**Keyword Search:**
```
Query: "machine learning"
✓ Finds: "machine learning algorithms"
✗ Misses: "AI models", "neural networks", "deep learning"
```

**Problem:** Different words, same meaning.

### Semantic Search Advantages

**Semantic Search:**
```
Query: "machine learning"
✓ Finds: "machine learning algorithms" (0.95 similarity)
✓ Finds: "AI models and algorithms" (0.82 similarity)
✓ Finds: "neural network training" (0.76 similarity)
```

**Solution:** Understands meaning and context.

---

## How It Works

### 1. Embedding Generation

```
Document → Sentence Transformer → 384D Vector → Database
```

**Process:**
1. Document text passed to model
2. Model generates 384-dimensional embedding
3. Embedding stored in `document_vectors` table
4. Indexed by document ID for fast retrieval

### 2. Semantic Search

```
Query → Embed Query → Compare to All Docs → Rank by Similarity → Return Top K
```

**Similarity Calculation:**
```python
cosine_similarity = dot(query_vector, doc_vector) / (norm(query_vector) * norm(doc_vector))
```

Range: 0.0 (unrelated) to 1.0 (identical)

### 3. Hybrid Search

```
Keyword Search Results  ┐
                        ├──→ Weighted Merge → Ranked Results
Semantic Search Results ┘
```

**Scoring:**
```
combined_score = (1 - w) * keyword_score + w * semantic_score
```

Where `w` = semantic weight (default 0.7)

### 4. RAG (Retrieval-Augmented Generation)

```
1. Query → 2. Hybrid Search → 3. Top K Docs → 4. LLM Generation → 5. Answer + Sources
```

**Advantages:**
- Answers grounded in actual documents
- Source citations for verification
- No hallucination (only uses retrieved context)

---

## Using the APIs

### 1. Generate Embeddings

**Single Document:**
```bash
curl -X POST "http://localhost:5010/api/v1/embeddings/generate?document_id=doc-123"
```

**Batch (Auto-mode):**
```bash
# Automatically embeds documents without vectors
curl -X POST "http://localhost:5010/api/v1/embeddings/generate-batch?limit=100"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "total": 50,
    "successful": 48,
    "failed": 2
  }
}
```

### 2. Check Coverage

```bash
curl -X GET "http://localhost:5010/api/v1/embeddings/stats"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "total_documents": 100,
    "vectorized_documents": 95,
    "coverage_percentage": 95.0
  }
}
```

### 3. Semantic Search

```bash
curl -X POST "http://localhost:5010/api/v1/search/semantic" \
  -G \
  --data-urlencode "query=machine learning algorithms" \
  --data-urlencode "limit=10" \
  --data-urlencode "min_similarity=0.3"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "query": "machine learning algorithms",
    "total_results": 8,
    "results": [
      {
        "id": "doc-123",
        "semantic_similarity": 0.87,
        "content": "...",
        "metadata": {}
      }
    ]
  }
}
```

### 4. Hybrid Search

```bash
curl -X POST "http://localhost:5010/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "machine learning", "limit": 10}' \
  -G \
  --data-urlencode "use_semantic=true" \
  --data-urlencode "semantic_weight=0.7"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "query": "machine learning",
    "search_mode": "hybrid",
    "total_results": 15,
    "results": [
      {
        "id": "doc-123",
        "score": 0.92,           ← Combined score
        "semantic_similarity": 0.87,
        "keyword_score": 0.95,
        "content": "..."
      }
    ]
  }
}
```

### 5. RAG Synthesis

```bash
curl -X POST "http://localhost:5010/api/v1/synthesis/generate" \
  -G \
  --data-urlencode "query=What is the Horus Heresy?" \
  --data-urlencode "semantic_weight=0.7" \
  --data-urlencode "temperature=0.3" \
  --data-urlencode "max_tokens=500"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "answer": "The Horus Heresy was a galaxy-spanning civil war...",
    "query": "What is the Horus Heresy?",
    "context_documents_used": 5,
    "model": "llama3.2:3b",
    "sources": ["doc-1", "doc-2", "doc-3"],
    "synthesis_method": "rag"
  }
}
```

---

## Performance & Scaling

### Current Performance

**Embedding Generation:**
- Single: ~50-100ms
- Batch (32): ~10ms per document
- 1000 docs: ~10 seconds

**Semantic Search:**
- 100 docs: < 100ms
- 1000 docs: < 500ms
- 10,000 docs: < 5 seconds

**RAG Synthesis:**
- Total: ~2-6 seconds

### Scaling Strategies

#### For <10K Documents (Current)
✅ **Linear scan with cosine similarity** (works great!)

#### For 10K-100K Documents
**Recommendation:** Add FAISS/Annoy for approximate nearest neighbor
```python
# FAISS example
import faiss
index = faiss.IndexFlatIP(384)  # Inner product (cosine)
index.add(embeddings)
distances, indices = index.search(query_embedding, k=10)
```

**Benefits:**
- Sub-linear search O(log n)
- 10-100x faster
- Scales to millions

#### For >100K Documents
**Recommendation:** Dedicated vector database
- **Qdrant:** High-performance vector search engine
- **Weaviate:** GraphQL vector database
- **Pinecone:** Managed vector database service

---

## Best Practices

### 1. Embedding Coverage

**Target:** >90% coverage for best results

**Check regularly:**
```bash
curl -X GET "http://localhost:5010/api/v1/embeddings/stats"
```

**Auto-generate on ingestion:**
```bash
# After ingesting new documents
curl -X POST "http://localhost:5010/api/v1/embeddings/generate-batch?limit=100"
```

### 2. Search Strategy

**Use case-specific approaches:**

| Use Case | Recommended Approach |
|----------|---------------------|
| Known keywords | Keyword search (`semantic_weight=0.0`) |
| Conceptual search | Semantic search (`semantic_weight=1.0`) |
| General search | Hybrid search (`semantic_weight=0.5-0.7`) |
| Q&A / RAG | RAG synthesis endpoint |

### 3. Similarity Thresholds

**Guidelines:**
- `0.8-1.0`: Very similar (paraphrases, exact matches)
- `0.6-0.8`: Related (same topic, different aspects)
- `0.4-0.6`: Somewhat related
- `0.0-0.4`: Unrelated

**Recommended minimums:**
- Strict search: `min_similarity=0.7`
- Balanced: `min_similarity=0.5`
- Exploratory: `min_similarity=0.3`

### 4. RAG Configuration

**Temperature:**
- `0.0-0.3`: Factual, deterministic
- `0.4-0.7`: Balanced
- `0.8-1.0`: Creative (not recommended for facts)

**Max Tokens:**
- Short answer: 200-300
- Detailed: 500-800
- Comprehensive: 1000+

### 5. Performance Optimization

**Batch Processing:**
```bash
# Good: Batch embed 100 documents
curl -X POST ".../embeddings/generate-batch?limit=100"

# Bad: 100 individual requests
for i in {1..100}; do
  curl -X POST ".../embeddings/generate?document_id=doc-$i"
done
```

**Caching:**
- Cache common query embeddings
- Cache RAG responses for FAQ

**Async Processing:**
- Use background workers for large batches
- Don't block user requests

---

## Troubleshooting

### "No embeddings found"

**Problem:** Documents not vectorized yet.

**Solution:**
```bash
curl -X POST "http://localhost:5010/api/v1/embeddings/generate-batch?limit=1000"
```

### "Semantic search returns no results"

**Problem:** Similarity threshold too high.

**Solution:** Lower `min_similarity`:
```bash
curl -X POST ".../search/semantic?query=...&min_similarity=0.2"
```

### "RAG answers are generic"

**Problem:** Not enough relevant context documents.

**Solutions:**
1. Check embedding coverage
2. Lower similarity threshold
3. Increase context documents (modify service config)

### "Slow search performance"

**Problem:** Too many documents for linear scan.

**Solutions:**
1. Implement FAISS/Annoy (>10K docs)
2. Use vector database (>100K docs)
3. Add result caching

---

## Example Workflows

### Workflow 1: Initial Setup

```bash
# 1. Ingest documents
curl -X POST "http://localhost:5700/api/v1/ingest" -d @documents.json

# 2. Generate embeddings
curl -X POST "http://localhost:5010/api/v1/embeddings/generate-batch?limit=1000"

# 3. Check coverage
curl -X GET "http://localhost:5010/api/v1/embeddings/stats"

# 4. Test search
curl -X POST "http://localhost:5010/api/v1/search/semantic?query=test"
```

### Workflow 2: Q&A System

```bash
# Use RAG for intelligent answers
curl -X POST "http://localhost:5010/api/v1/synthesis/generate" \
  -G \
  --data-urlencode "query=What is the main topic?" \
  --data-urlencode "temperature=0.3" \
  --data-urlencode "max_tokens=500"
```

### Workflow 3: Similar Document Finder

```bash
# Find documents similar to a known document
# 1. Get document embedding
# 2. Search with that embedding
curl -X POST "http://localhost:5010/api/v1/search/semantic" \
  -G \
  --data-urlencode "query=<document_content>" \
  --data-urlencode "limit=10"
```

---

## Resources

### Documentation
- Full implementation: `/docs/VECTORIZATION_IMPLEMENTATION_SUMMARY.md`
- Test suite: `/tests/unit/doc_store/test_*embedding*`
- Integration tests: `/tests/integration/test_semantic_search_workflow.py`

### Further Reading
- [Sentence Transformers Documentation](https://www.sbert.net/)
- [FAISS Documentation](https://github.com/facebookresearch/faiss)
- [RAG Paper](https://arxiv.org/abs/2005.11401)

---

**System:** MCP Knowledge Base Ecosystem  
**Feature:** Vectorization & Semantic Search  
**Status:** ✅ Production-Ready  
**TDD Coverage:** 120+ Tests  

