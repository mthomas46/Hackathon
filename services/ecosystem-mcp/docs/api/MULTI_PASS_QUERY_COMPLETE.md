---
title: "🔬 Multi-Pass Query System - COMPLETE"
service: "ecosystem-mcp"
category: "api"
tags: ['api', 'cache', 'caching', 'config', 'configuration', 'endpoints', 'ingestion', 'optimization', 'performance', 'pipeline']
related: ['INDEX.md', 'architecture/OVERVIEW.md', 'CODE_REFERENCE.md', 'API_ENDPOINTS_COMPLETE.md']
status: "current"
last_updated: "2025-10-28"
audience: "developer"
difficulty: "intermediate"
semantic_keywords: ['api', 'cache', 'caching', 'config', 'configuration']
llm_search_hints: ['what is 🔬 multi-pass query system - complete', 'how does 🔬 multi-pass query system - complete work', 'guide to 🔬 multi-pass query system - complete']
---

# 🔬 Multi-Pass Query System - COMPLETE

## Overview

A sophisticated **multi-pass query processing system** inspired by the deep docs generation workflow. Enables complex queries to be decomposed into sections with secondary questions for comprehensive, in-depth analysis.

## 🎯 What It Does

The Multi-Pass Query System:
1. **Decomposes** your complex query into N major concepts/sections
2. **Generates** M secondary questions for each section
3. **Executes** RAG for all questions (N×M total queries)
4. **Synthes**izes section-level answers
5. **Creates** a final comprehensive answer

## 📁 Implementation Complete

### API Side ✅

**Created:**
- `src/services/rag/multi_pass_query.py` - Multi-pass service with decomposition and synthesis
- `src/api/routes/multi_pass.py` - API endpoints with progress tracking

**Modified:**
- `src/services/rag/__init__.py` - Export multi-pass service
- `src/api/app.py` - Register multi-pass router
- `src/api/middleware/timeout.py` - Added 900s timeout (15 minutes)

### Frontend Integration 🚧

**Status:** API ready, frontend integration pending

The RAG Query page can be enhanced to include multi-pass functionality. For now, use:
- **API directly** (curl, httpx, requests)
- **Python test script** (provided below)
- **Swagger UI** at http://localhost:8000/docs

## 🔌 API Endpoints

### POST `/api/v1/query/multi-pass`

Process a complex query using multi-pass decomposition.

**Request:**
```json
{
  "query": "How does the caching system work and what are the best practices?",
  "num_passes": 3,
  "num_secondary_questions": 3,
  "n_results": 10,
  "temperature": 0.7,
  "stream": false
}
```

**Parameters:**
- `query` (required): Main query to analyze (10-2000 chars)
- `num_passes` (optional): Number of sections (1-10, default: 3)
- `num_secondary_questions` (optional): Questions per section (1-10, default: 3)
- `n_results` (optional): Documents per question (1-50, default: 10)
- `temperature` (optional): LLM temperature (0.0-1.0, default: 0.7)
- `stream` (optional): Stream progress updates via SSE (default: false)

**Response:**
```json
{
  "original_query": "...",
  "num_passes": 3,
  "num_secondary_questions": 3,
  "sections": [
    {
      "section_index": 0,
      "section_name": "Core Concepts",
      "section_description": "...",
      "synthesis": "...",
      "duration_seconds": 12.5,
      "questions": [
        {
          "question": "...",
          "answer": "...",
          "sources": [...],
          "confidence": 0.87,
          "duration_seconds": 4.2
        }
      ]
    }
  ],
  "section_summaries": [...],
  "final_synthesis": "...",
  "total_duration_seconds": 45.3,
  "total_questions_asked": 9,
  "total_sources_used": 42,
  "timestamp": "2025-10-13T23:00:00",
  "metadata": {...}
}
```

### GET `/api/v1/query/multi-pass/info`

Get information about multi-pass query processing.

**Response:**
```json
{
  "description": "Multi-pass query processing for complex analysis",
  "workflow": {
    "step_1": "Decompose query into N major concepts/sections",
    "step_2": "Generate M secondary questions per section",
    "step_3": "Execute RAG for each question (N×M total)",
    "step_4": "Synthesize section-level answers",
    "step_5": "Create final comprehensive synthesis"
  },
  "parameters": {...},
  "example_usage": {...}
}
```

## 🚀 Usage Examples

### Example 1: Simple Multi-Pass Query

```bash
curl -X POST "http://localhost:8000/api/v1/query/multi-pass" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How does the RAG system work?",
    "num_passes": 3,
    "num_secondary_questions": 3
  }' | jq '.final_synthesis'
```

**What this does:**
- Decomposes into 3 sections (e.g., Core Concepts, Implementation, Usage)
- Generates 3 questions per section (9 total)
- Executes 9 RAG queries
- Synthesizes answers for each section
- Creates final comprehensive answer

### Example 2: Deep Analysis

```bash
curl -X POST "http://localhost:8000/api/v1/query/multi-pass" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Explain the caching system architecture, implementation, and best practices",
    "num_passes": 5,
    "num_secondary_questions": 4,
    "n_results": 15
  }' | jq '{
    sections: .sections | length,
    total_questions: .total_questions_asked,
    total_sources: .total_sources_used,
    duration: .total_duration_seconds
  }'
```

**What this does:**
- Decomposes into 5 sections
- Generates 4 questions per section (20 total)
- Retrieves 15 documents per question
- Provides very comprehensive analysis

### Example 3: Quick Multi-Pass

```bash
curl -X POST "http://localhost:8000/api/v1/query/multi-pass" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is ChromaDB and how do we use it?",
    "num_passes": 2,
    "num_secondary_questions": 2
  }' | jq '.section_summaries'
```

**What this does:**
- Decomposes into 2 sections
- Generates 2 questions per section (4 total)
- Faster but still comprehensive

## 🐍 Python Test Script

```python
#!/usr/bin/env python3
"""Test multi-pass query system."""

import httpx
import json
from datetime import datetime

def test_multi_pass_query():
    """Test multi-pass query processing."""
    
    query_request = {
        "query": "How does the caching system work and what are the best practices?",
        "num_passes": 3,
        "num_secondary_questions": 3,
        "n_results": 10,
        "temperature": 0.7,
        "stream": False
    }
    
    print(f"🔬 Testing Multi-Pass Query System")
    print(f"Query: {query_request['query']}")
    print(f"Configuration: {query_request['num_passes']} passes × {query_request['num_secondary_questions']} questions")
    print(f"=" * 80)
    
    start_time = datetime.now()
    
    try:
        response = httpx.post(
            "http://localhost:8000/api/v1/query/multi-pass",
            json=query_request,
            timeout=900.0  # 15 minutes
        )
        
        duration = (datetime.now() - start_time).total_seconds()
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"\n✅ Multi-Pass Query Complete!")
            print(f"Duration: {duration:.2f}s")
            print(f"\nSections ({len(result['sections'])}):")
            
            for section in result['sections']:
                print(f"\n  📂 Section {section['section_index'] + 1}: {section['section_name']}")
                print(f"     Description: {section['section_description']}")
                print(f"     Questions: {len(section['questions'])}")
                print(f"     Synthesis Length: {len(section['synthesis'])} chars")
                print(f"     Duration: {section['duration_seconds']:.2f}s")
            
            print(f"\n📊 Statistics:")
            print(f"   Total Questions Asked: {result['total_questions_asked']}")
            print(f"   Total Sources Used: {result['total_sources_used']}")
            print(f"   Total Duration: {result['total_duration_seconds']:.2f}s")
            
            print(f"\n📝 Final Synthesis Preview:")
            synthesis = result['final_synthesis']
            preview = synthesis[:500] + "..." if len(synthesis) > 500 else synthesis
            print(f"{preview}")
            
            # Save full result
            output_file = f"multi_pass_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
            
            print(f"\n💾 Full result saved to: {output_file}")
            
        else:
            print(f"❌ Query failed: HTTP {response.status_code}")
            print(response.text)
    
    except httpx.TimeoutException:
        print(f"❌ Query timed out after {duration:.2f}s")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_multi_pass_query()
```

**Save as:** `test_multi_pass.py`

**Run:**
```bash
cd /Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp
python test_multi_pass.py
```

## 🎨 Workflow Visualization

```
┌──────────────────────────────────────────────────────────────┐
│  User Query: "How does the caching system work?"             │
└───────────────────────────┬──────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│  STEP 1: Query Decomposition                                 │
│  ────────────────────────────────────────────────────────    │
│  LLM analyzes query and decomposes into N sections:          │
│    • Section 1: Core Concepts                                │
│    • Section 2: Implementation Details                       │
│    • Section 3: Best Practices                               │
└───────────────────────────┬──────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│  STEP 2: Secondary Question Generation                       │
│  ────────────────────────────────────────────────────────    │
│  For each section, generate M specific questions:            │
│                                                               │
│  Section 1 (Core Concepts):                                  │
│    • Q1: What is caching?                                    │
│    • Q2: Why do we use caching?                              │
│    • Q3: What are the key components?                        │
│                                                               │
│  Section 2 (Implementation):                                 │
│    • Q1: How is Redis configured?                            │
│    • Q2: What caching strategies are used?                   │
│    • Q3: How are cache keys generated?                       │
│                                                               │
│  Section 3 (Best Practices):                                 │
│    • Q1: When to use caching?                                │
│    • Q2: How to invalidate cache?                            │
│    • Q3: What are common pitfalls?                           │
│                                                               │
│  Total: 3 sections × 3 questions = 9 questions               │
└───────────────────────────┬──────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│  STEP 3: RAG Execution (For Each Question)                   │
│  ────────────────────────────────────────────────────────    │
│  Execute full RAG for each question:                         │
│    1. Semantic search (retrieve documents)                   │
│    2. Build context (augmentation)                           │
│    3. Generate answer (synthesis)                            │
│                                                               │
│  Progress: [████████████░░░░░░░░░░] 6/9 questions complete   │
└───────────────────────────┬──────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│  STEP 4: Section Synthesis                                   │
│  ────────────────────────────────────────────────────────    │
│  For each section, synthesize all Q&A:                       │
│                                                               │
│  Section 1 Synthesis:                                        │
│    "Caching is a technique for storing frequently accessed   │
│     data in memory... Based on Q1-Q3 analysis..."            │
│                                                               │
│  Section 2 Synthesis:                                        │
│    "Our caching implementation uses Redis with... As shown   │
│     in Q1-Q3, the key strategies are..."                     │
│                                                               │
│  Section 3 Synthesis:                                        │
│    "Best practices include... Based on our analysis of       │
│     Q1-Q3, the recommendations are..."                       │
└───────────────────────────┬──────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│  STEP 5: Final Comprehensive Synthesis                       │
│  ────────────────────────────────────────────────────────    │
│  Integrate all section syntheses into final answer:          │
│                                                               │
│  "The caching system works by... [Section 1 insights]        │
│   Implementation details show... [Section 2 insights]        │
│   Following best practices... [Section 3 insights]           │
│                                                               │
│   In summary, the caching system provides..."                │
└───────────────────────────┬──────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│  RESULT: Comprehensive Answer with Sources                   │
│  ────────────────────────────────────────────────────────    │
│  • Final synthesis (integrated answer)                       │
│  • All section analyses                                      │
│  • All Q&A pairs with sources                                │
│  • Confidence scores                                         │
│  • Metrics and timing                                        │
└──────────────────────────────────────────────────────────────┘
```

## 🎯 Use Cases

### 1. Complex Technical Questions
```json
{
  "query": "Explain the complete architecture of the RAG system including storage, retrieval, and generation",
  "num_passes": 4,
  "num_secondary_questions": 4
}
```

### 2. Research Queries
```json
{
  "query": "What are all the different types of caching we use and when should each be used?",
  "num_passes": 3,
  "num_secondary_questions": 5
}
```

### 3. Documentation Generation
```json
{
  "query": "Document the complete ingestion pipeline from source to vector storage",
  "num_passes": 5,
  "num_secondary_questions": 3
}
```

### 4. System Understanding
```json
{
  "query": "How do all the microservices communicate and what patterns are used?",
  "num_passes": 6,
  "num_secondary_questions": 4
}
```

## 📊 Performance Characteristics

### Time Estimates

**Formula:** `Time ≈ (num_passes × num_secondary_questions × 2-3s) + synthesis_time`

**Examples:**
- `3 passes × 3 questions = 9 queries`: ~20-30 seconds
- `5 passes × 4 questions = 20 queries`: ~50-70 seconds
- `10 passes × 5 questions = 50 queries`: ~120-150 seconds

### Quality vs Speed Trade-offs

| Configuration | Questions | Time | Quality | Best For |
|---------------|-----------|------|---------|----------|
| 2×2 | 4 | ~10s | ⭐⭐ | Quick overview |
| 3×3 | 9 | ~25s | ⭐⭐⭐ | Standard analysis |
| 4×4 | 16 | ~45s | ⭐⭐⭐⭐ | Deep dive |
| 5×5 | 25 | ~70s | ⭐⭐⭐⭐⭐ | Comprehensive research |
| 10×5 | 50 | ~150s | ⭐⭐⭐⭐⭐ | Maximum depth |

## 🔧 Configuration Guidelines

### Recommended Configurations

**Quick Analysis (10-30s):**
```json
{
  "num_passes": 2,
  "num_secondary_questions": 2,
  "n_results": 5
}
```

**Standard Analysis (20-60s):**
```json
{
  "num_passes": 3,
  "num_secondary_questions": 3,
  "n_results": 10
}
```

**Deep Analysis (60-180s):**
```json
{
  "num_passes": 5,
  "num_secondary_questions": 4,
  "n_results": 15
}
```

**Comprehensive Research (3-5min):**
```json
{
  "num_passes": 8,
  "num_secondary_questions": 5,
  "n_results": 20
}
```

## 🐛 Troubleshooting

### Query Takes Too Long
- **Reduce `num_passes`**: Fewer sections = faster
- **Reduce `num_secondary_questions`**: Fewer questions per section
- **Reduce `n_results`**: Fewer documents per query

### Not Enough Detail
- **Increase `num_passes`**: More section coverage
- **Increase `num_secondary_questions`**: More depth per section
- **Increase `n_results`**: More document context

### Timeout Errors
- Maximum timeout is 900s (15 minutes)
- Reduce total questions if hitting timeout
- Consider breaking into multiple smaller queries

## 📚 API Documentation

Full API documentation available at:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

Look for the **"Multi-Pass Query"** section.

## ✅ Status

- ✅ Service layer implemented
- ✅ API endpoints created
- ✅ Progress tracking supported
- ✅ Streaming SSE available
- ✅ Documentation complete
- ✅ Container deployed
- ✅ Testing script provided
- 🚧 Frontend integration pending

## 🔮 Next Steps

### To Integrate into RAG Query Page:

1. Add query type selector (Standard vs Multi-Pass)
2. Add multi-pass form with:
   - `num_passes` slider (1-10)
   - `num_secondary_questions` slider (1-10)
3. Show progress bar during processing
4. Display section results in expandable cards
5. Show final synthesis at top

### To Enable Streaming:

1. Use Server-Sent Events (SSE)
2. Update progress bar in real-time
3. Show sections as they complete
4. Display total progress percentage

## 🎉 Summary

You now have a powerful **multi-pass query system** that can:

✨ **Decompose** complex queries into manageable sections  
✨ **Generate** targeted secondary questions automatically  
✨ **Execute** comprehensive RAG analysis  
✨ **Synthesize** integrated, authoritative answers  
✨ **Track** progress and provide detailed metrics  
✨ **Scale** from quick queries to deep research  

**Try it now:**
```bash
python test_multi_pass.py
```

Or via API:
```bash
curl -X POST "http://localhost:8000/api/v1/query/multi-pass" \
  -H "Content-Type: application/json" \
  -d '{"query": "How does our system work?", "num_passes": 3, "num_secondary_questions": 3}' | jq
```

🚀 **Your multi-pass query system is ready for complex analysis!**

