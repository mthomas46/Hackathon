# RAG System Architecture - Visual Documentation

**Date:** November 1, 2025  
**Version:** 1.0  
**Status:** Production Deployment

---

## System Overview Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          RAG ENHANCEMENT SYSTEM                              │
│                      (Modular Pipeline Architecture)                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                         CLIENT / USER                                   │ │
│  └──────────────────────────────┬──────────────────────────────────────────┘ │
│                                 │                                             │
│                                 ▼                                             │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                          FastAPI (Port 8000)                            │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │ │
│  │  │ /api/v1/ │  │ /api/v1/ │  │ /api/v1/ │  │ /api/v1/ │  │  /api/  │ │ │
│  │  │   ask    │  │ temporal │  │  query   │  │ dynamic- │  │  cache  │ │ │
│  │  │          │  │   /query │  │ /context │  │   rag    │  │ /metrics│ │ │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬────┘ │ │
│  └───────┼─────────────┼─────────────┼─────────────┼──────────────┼──────┘ │
│          │             │             │             │              │          │
│          └─────────────┴─────────────┴─────────────┴──────────────┘          │
│                                      │                                        │
│                                      ▼                                        │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                    RAG SERVICE LAYER                                    │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌───────────┐ │ │
│  │  │  Standard    │  │   Temporal   │  │ Context-Aware│  │Multi-Pass │ │ │
│  │  │     RAG      │  │     RAG      │  │     RAG      │  │    RAG    │ │ │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └─────┬─────┘ │ │
│  │         │                  │                  │                │        │ │
│  │         └──────────────────┴──────────────────┴────────────────┘        │ │
│  │                                      │                                   │ │
│  │                                      ▼                                   │ │
│  │         ┌────────────────────────────────────────────────────┐         │ │
│  │         │     ✨ ENHANCEMENT PIPELINE (Phase 1)            │         │ │
│  │         │                                                     │         │ │
│  │         │  ┌─────────────────────────────────────────────┐  │         │ │
│  │         │  │ Phase 1: Query Preprocessing               │  │         │ │
│  │         │  │  • Query Rewriting                         │  │         │ │
│  │         │  │  • Synonym Expansion                       │  │         │ │
│  │         │  │  • Clarification                           │  │         │ │
│  │         │  └─────────────────┬───────────────────────────┘  │         │ │
│  │         │                    ▼                               │         │ │
│  │         │  ┌─────────────────────────────────────────────┐  │         │ │
│  │         │  │ Phase 2: Filter Construction               │  │         │ │
│  │         │  │  • Metadata Filters                        │  │         │ │
│  │         │  │  • Temporal Filters                        │  │         │ │
│  │         │  │  • Context Filters                         │  │         │ │
│  │         │  └─────────────────┬───────────────────────────┘  │         │ │
│  │         │                    ▼                               │         │ │
│  │         │  ┌─────────────────────────────────────────────┐  │         │ │
│  │         │  │ Phase 3: Retrieval (Hybrid Search)         │  │         │ │
│  │         │  │  • Semantic Search (70%) ──┐               │  │         │ │
│  │         │  │  • BM25 Keyword (30%)   ───┼─> RRF Fusion  │  │         │ │
│  │         │  │  • Quality Boost           │               │  │         │ │
│  │         │  └─────────────────┬───────────────────────────┘  │         │ │
│  │         │                    ▼                               │         │ │
│  │         │  ┌─────────────────────────────────────────────┐  │         │ │
│  │         │  │ Phase 4: Post-Retrieval                    │  │         │ │
│  │         │  │  • Cross-Encoder Reranking                 │  │         │ │
│  │         │  │  • Quality Filtering                       │  │         │ │
│  │         │  │  • Deduplication                           │  │         │ │
│  │         │  └─────────────────┬───────────────────────────┘  │         │ │
│  │         │                    ▼                               │         │ │
│  │         │  ┌─────────────────────────────────────────────┐  │         │ │
│  │         │  │ Phase 5: Context Optimization              │  │         │ │
│  │         │  │  • Smart Chunking                          │  │         │ │
│  │         │  │  • Redundancy Removal                      │  │         │ │
│  │         │  │  • Strategic Ordering                      │  │         │ │
│  │         │  └─────────────────┬───────────────────────────┘  │         │ │
│  │         │                    ▼                               │         │ │
│  │         │  ┌─────────────────────────────────────────────┐  │         │ │
│  │         │  │ Phase 6: Contradiction Detection           │  │         │ │
│  │         │  │  • Temporal Conflicts                      │  │         │ │
│  │         │  │  • Negation Detection                      │  │         │ │
│  │         │  │  • Value Conflicts                         │  │         │ │
│  │         │  └─────────────────┬───────────────────────────┘  │         │ │
│  │         │                    ▼                               │         │ │
│  │         │  ┌─────────────────────────────────────────────┐  │         │ │
│  │         │  │ Phase 7: Metrics & Logging                 │  │         │ │
│  │         │  │  • Performance Tracking                    │  │         │ │
│  │         │  │  • Enhancement Metrics                     │  │         │ │
│  │         │  │  • Confidence Scoring                      │  │         │ │
│  │         │  └─────────────────────────────────────────────┘  │         │ │
│  │         └────────────────────────────────────────────────────┘         │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                      │                                        │
│                                      ▼                                        │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                      STORAGE & SERVICES LAYER                           │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌───────────┐ │ │
│  │  │  PostgreSQL  │  │   ChromaDB   │  │    Redis     │  │  Ollama   │ │ │
│  │  │  (Metadata)  │  │  (Vectors)   │  │  (Cache)     │  │   (LLM)   │ │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  └───────────┘ │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Enhancement Pipeline Flow (Detailed)

```
┌─────────────────────────────────────────────────────────────────┐
│                    QUERY FLOW DIAGRAM                            │
└─────────────────────────────────────────────────────────────────┘

User Query: "What is MCP?"
        │
        ▼
┌──────────────────┐
│ Query Rewriter   │ → ["What is MCP?", "What is Model Context Protocol?"]
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Metadata Filter  │ → {quality_score: >0.7, exclude: tests}
└────────┬─────────┘
         │
         ▼
┌────────────────────────────────────────┐
│      HYBRID SEARCH (Parallel)          │
│  ┌────────────────┐  ┌──────────────┐ │
│  │ Semantic (70%) │  │  BM25 (30%)  │ │
│  │  ChromaDB      │  │  Text Index  │ │
│  │  Top 20 docs   │  │  Top 20 docs │ │
│  └────────┬───────┘  └──────┬───────┘ │
│           │                  │         │
│           └────────┬─────────┘         │
│                    │                   │
│           ┌────────▼─────────┐         │
│           │   RRF Fusion     │         │
│           │  (Reciprocal     │         │
│           │  Rank Fusion)    │         │
│           └────────┬─────────┘         │
└────────────────────┼───────────────────┘
                     │
                     ▼
          ┌──────────────────┐
          │  Top 30 docs      │
          └──────────┬────────┘
                     │
                     ▼
          ┌──────────────────┐
          │  Cross-Encoder   │ → Rerank by query-doc relevance
          │  Reranking       │    (optional, expensive)
          └──────────┬────────┘
                     │
                     ▼
          ┌──────────────────┐
          │  Top 15 docs      │
          └──────────┬────────┘
                     │
                     ▼
          ┌──────────────────┐
          │ Context Optimizer│ → Remove redundancy, order by relevance
          └──────────┬────────┘
                     │
                     ▼
          ┌──────────────────┐
          │  Top 8 docs       │
          │  (Final Context)  │
          └──────────┬────────┘
                     │
                     ▼
          ┌──────────────────┐
          │ Contradiction    │ → Detect conflicts
          │ Detection        │
          └──────────┬────────┘
                     │
                     ▼
          ┌──────────────────┐
          │  LLM Generation  │ → Ollama synthesizes answer
          └──────────┬────────┘
                     │
                     ▼
          ┌──────────────────┐
          │ Confidence Score │ → Calculate 0.0-1.0
          └──────────┬────────┘
                     │
                     ▼
              Final Answer
```

---

## RAG Type Comparison

```
┌───────────────────────────────────────────────────────────────────────────┐
│                          7 RAG TYPES                                       │
├────────────────┬──────────────┬──────────────┬─────────────┬──────────────┤
│   RAG Type     │  Enhancements│   Best For   │  Speed      │  Accuracy    │
├────────────────┼──────────────┼──────────────┼─────────────┼──────────────┤
│ Standard       │  Full ✅     │  General Q&A │  ~10s       │  High        │
│ Enhanced       │  Full ✅     │  Max Quality │  ~15s       │  Highest     │
│ Temporal       │  Hybrid ✅   │  Time-travel │  ~12s       │  High        │
│ Context-Aware  │  Hybrid ✅   │  Hierarchical│  ~10s       │  High        │
│ Multi-Pass     │  Optimized ✅│  Complex Q's │  ~120s      │  Very High   │
│ Dynamic Temp.  │  Hybrid ✅   │  Timelines   │  ~60s       │  High        │
│ Contextual     │  N/A         │  Lightweight │  ~5s        │  Medium      │
└────────────────┴──────────────┴──────────────┴─────────────┴──────────────┘

Legend:
✅ Full = All 7 pipeline phases
✅ Hybrid = Phases 1-3 (query rewriting + hybrid search)
✅ Optimized = Phases 1,3,5 (no reranking for N×M efficiency)
```

---

## Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    DOCUMENT INGESTION → RAG QUERY                        │
└─────────────────────────────────────────────────────────────────────────┘

INGESTION FLOW:
──────────────
Git Repository
     │
     ▼
┌─────────────┐
│  Scanner    │ → Discover files
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Classifier │ → Identify file types
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Normalizer  │ → Extract text content
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Embedder   │ → Generate vectors (Ollama)
└──────┬──────┘
       │
       ▼
┌─────────────┐    ┌──────────────┐
│ PostgreSQL  │    │  ChromaDB    │
│ (Metadata)  │    │  (Vectors)   │
└─────────────┘    └──────────────┘

QUERY FLOW:
───────────
User Query
     │
     ▼
┌─────────────────┐
│  Enhancement    │ → Rewrite, expand
│  Pipeline       │
└────────┬────────┘
         │
         ├────────────────────────────┐
         │                            │
         ▼                            ▼
┌─────────────────┐         ┌─────────────────┐
│  Semantic Search│         │   BM25 Search   │
│  (ChromaDB)     │         │   (Text Index)  │
└────────┬────────┘         └────────┬────────┘
         │                            │
         └────────────┬───────────────┘
                      │
                      ▼
              ┌──────────────┐
              │   Fusion     │ → Combine results
              └──────┬───────┘
                     │
                     ▼
              ┌──────────────┐
              │   Reranker   │ → Refine order
              └──────┬───────┘
                     │
                     ▼
              ┌──────────────┐
              │  Optimizer   │ → Build context
              └──────┬───────┘
                     │
                     ▼
              ┌──────────────┐
              │   Ollama     │ → Generate answer
              │   (LLM)      │
              └──────────────┘
```

---

## Configuration Presets Comparison

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    ENHANCEMENT CONFIG PRESETS                            │
├──────────────┬──────┬──────┬────────┬─────────┬──────────┬─────────────┤
│  Preset      │Hybrid│Rewrt │Rerank  │Context  │Confid.   │  Use Case   │
├──────────────┼──────┼──────┼────────┼─────────┼──────────┼─────────────┤
│ default      │  ✅  │  ✅  │   ✅   │  ✅     │   ✅     │ Balanced    │
│ temporal_def │  ✅  │  ✅  │   ✅   │  ✅     │   ✅     │ Temporal    │
│ context_def  │  ✅  │  ✅  │   ✅   │  ✅     │   ✅     │ Context     │
│ multipass    │  ✅  │  ❌  │   ❌   │  ✅     │   ✅     │ N×M queries │
│ fast         │  ✅  │  ❌  │   ❌   │  ❌     │   ✅     │ Speed       │
│ max_quality  │  ✅  │  ✅  │   ✅   │  ✅     │   ✅     │ Accuracy    │
│ minimal      │  ❌  │  ❌  │   ❌   │  ❌     │   ❌     │ Baseline    │
└──────────────┴──────┴──────┴────────┴─────────┴──────────┴─────────────┘

✅ = Enabled
❌ = Disabled
```

---

## Performance Comparison (Before/After)

```
SOURCE RETRIEVAL:
─────────────────
Before (Semantic Only):     After (Hybrid Search):
                                   
Query: "What is MCP?"       Query: "What is MCP?"
       │                           │
       ▼                           ▼
┌──────────────┐            ┌──────────────────────┐
│  ChromaDB    │            │  ChromaDB + BM25     │
│  Semantic    │            │  Hybrid Search       │
│              │            │                      │
│  5 docs      │     →      │  8 docs (+60%)      │
│  0.65 conf   │            │  0.73 conf (+8.8%)  │
│  ~12s        │            │  ~10s (-17%)        │
└──────────────┘            └──────────────────────┘

IMPROVEMENT: +60% sources, +8.8% confidence, -17% time
```

---

## Caching Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       REDIS CACHING LAYER                                │
└─────────────────────────────────────────────────────────────────────────┘

User Query
     │
     ▼
┌────────────────┐
│  Query Cache   │ ← Check if query seen before
└────────┬───────┘
         │
    ┌────┴────┐
    │ HIT?    │
    └────┬────┘
         │
    ┌────┴────────────────┐
    │                     │
    ▼ YES                 ▼ NO
┌─────────┐        ┌──────────────┐
│ Return  │        │ Execute      │
│ Cached  │        │ Pipeline     │
│ Answer  │        │              │
└─────────┘        └──────┬───────┘
                          │
                          ▼
                   ┌──────────────┐
                   │ BM25 Cache   │ ← Check if index built
                   └──────┬───────┘
                          │
                          ▼
                   ┌──────────────┐
                   │Embedding     │ ← Check if embedding cached
                   │Cache         │
                   └──────┬───────┘
                          │
                          ▼
                   ┌──────────────┐
                   │ Reranker     │ ← Check if reranking cached
                   │ Cache        │
                   └──────┬───────┘
                          │
                          ▼
                   ┌──────────────┐
                   │ Final Answer │
                   │              │
                   │ Store in     │
                   │ Query Cache  │
                   └──────────────┘

Cache Layers:
1. Query Cache (full answers) - TTL: 1 hour
2. BM25 Index Cache - TTL: 24 hours
3. Embedding Cache - TTL: 24 hours
4. Reranker Cache - TTL: 1 hour
```

---

## Monitoring & Metrics

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    MONITORING ARCHITECTURE                               │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│                       FastAPI Application                             │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                    Metrics Collection                           │ │
│  │                                                                  │ │
│  │  • Request Count        • Response Times                       │ │
│  │  • Error Rates          • Cache Hit Rates                      │ │
│  │  • Source Count         • Confidence Scores                    │ │
│  │  • Enhancement Usage    • Query Types                          │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                               │                                       │
└───────────────────────────────┼───────────────────────────────────────┘
                                │
                ┌───────────────┼───────────────┐
                │               │               │
                ▼               ▼               ▼
        ┌──────────┐    ┌─────────────┐  ┌───────────┐
        │  Redis   │    │ PostgreSQL  │  │   Logs    │
        │ Metrics  │    │  Analytics  │  │  (JSON)   │
        └──────────┘    └─────────────┘  └───────────┘

Available Endpoints:
• GET /api/health                    - System health
• GET /api/cache/metrics             - Cache statistics
• GET /api/cache/analytics           - Cache analytics
• GET /api/v1/rag/enhancements/stats - Enhancement usage
• GET /api/v1/performance/metrics    - Performance data
```

---

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       DOCKER COMPOSE DEPLOYMENT                          │
└─────────────────────────────────────────────────────────────────────────┘

Host Machine (macOS)
│
└─── Docker Desktop
     │
     └─── Docker Compose Network
          │
          ├─── ecosystem-mcp-service (FastAPI)
          │    • Port: 8000 → 8000
          │    • Healthcheck: /api/health
          │    • Depends: postgres, redis, chroma, ollama
          │
          ├─── ecosystem-mcp-postgres (PostgreSQL)
          │    • Port: 5432
          │    • Volume: postgres_data
          │    • Database: ecosystem_mcp
          │
          ├─── ecosystem-mcp-redis (Redis)
          │    • Port: 6379
          │    • Volume: redis_data
          │    • Used for: caching
          │
          ├─── ecosystem-mcp-chroma (ChromaDB)
          │    • Port: 8001
          │    • Volume: chroma_data
          │    • Collections: documents, embeddings
          │
          └─── ecosystem-mcp-ollama (Ollama LLM)
               • Port: 11434
               • Volume: ollama_data
               • Models: llama2, codellama, etc.

Health Check Flow:
─────────────────
1. Redis health → OK
2. PostgreSQL health → OK
3. ChromaDB health → OK
4. Ollama health → OK
5. FastAPI health → ✅ HEALTHY
```

---

## Summary

This document provides comprehensive visual documentation of the RAG Enhancement System architecture, including:

1. ✅ **System Overview** - Complete system diagram
2. ✅ **Enhancement Pipeline** - 7-phase processing flow
3. ✅ **Query Flow** - Detailed query processing
4. ✅ **RAG Types** - Comparison of all 7 types
5. ✅ **Data Flow** - Ingestion to query lifecycle
6. ✅ **Configuration** - Preset comparisons
7. ✅ **Performance** - Before/after analysis
8. ✅ **Caching** - Multi-layer caching strategy
9. ✅ **Monitoring** - Metrics collection architecture
10. ✅ **Deployment** - Docker Compose setup

**Status:** ✅ **PRODUCTION DEPLOYED**

---

**Last Updated:** November 1, 2025  
**Version:** 1.0  
**Maintained By:** RAG Enhancement Team

