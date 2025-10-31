---
title: "🎯 Enhanced Query System - Complete Implementation"
service: "ecosystem-mcp"
category: "architecture"
tags: ['architecture', 'cache', 'caching', 'config', 'configuration', 'design', 'ingestion', 'llm', 'ollama', 'optimization']
related: ['INDEX.md', 'architecture/OVERVIEW.md', 'CODE_REFERENCE.md', 'API_ENDPOINTS_COMPLETE.md']
status: "current"
last_updated: "2025-10-28"
audience: "developer"
difficulty: "advanced"
semantic_keywords: ['architecture', 'cache', 'caching', 'config', 'configuration']
llm_search_hints: ['what is 🎯 enhanced query system - complete implementation', 'how does 🎯 enhanced query system - complete implementation work', 'guide to 🎯 enhanced query system - complete implementation']
---

# 🎯 Enhanced Query System - Complete Implementation

## Overview

Added comprehensive query system with **3 query modes** and **manual tier selection** with automatic fallback protection.

## 🎨 Features Implemented

### 1. Three Query Modes

#### 🎯 RAG Mode (Full)
- **Retrieval**: Semantic search for relevant documents
- **Augmentation**: Build context from multiple sources
- **Generation**: LLM synthesizes comprehensive answer
- **Features**: Source citations, confidence scoring
- **Best For**: Complex questions requiring accurate, cited answers
- **Speed**: 3-10 seconds
- **Quality**: Highest

#### 📄 Contextual Mode
- **Retrieval**: Document search
- **Augmentation**: Simple context creation
- **Generation**: Basic LLM generation
- **Best For**: Quick answers with document context
- **Speed**: 1-3 seconds
- **Quality**: Medium

#### ⚡ Basic Mode (LLM Only)
- **No Retrieval**: Direct to LLM
- **No Augmentation**: Pure LLM knowledge
- **Generation**: Immediate response
- **Best For**: General questions, brainstorming, quick queries
- **Speed**: <1 second
- **Quality**: Depends on LLM knowledge

### 2. Manual Tier Selection

Users can now **manually select** which LLM tier to use:

#### 🤖 Auto (Recommended)
- Analyzes query complexity
- Automatically routes to best tier
- Guaranteed to work (always falls back to Docker)

#### 🥇 Tier 1: Cursor IDE
- **Model**: Claude 4.5 Sonnet
- **Use Case**: Extreme complexity (0.8-1.0)
- **Requires**: Cursor IDE running on port 3000
- **Fallback**: Desktop → Docker

#### 🥈 Tier 2: Desktop Ollama
- **Model**: llama3:latest (GPU)
- **Use Case**: Heavy workloads (0.4-0.8)
- **Requires**: Desktop Ollama on port 11435
- **Fallback**: Docker

#### 🥉 Tier 3: Docker Ollama
- **Model**: llama3.2:3b (CPU)
- **Use Case**: Simple queries (0.0-0.4)
- **Status**: Always available
- **Fallback**: None (base tier)

### 3. Automatic Fallback Protection

```
User selects Cursor → Cursor unavailable
  ↓
System tries Desktop → Desktop unavailable
  ↓
System uses Docker → Always works! ✅
```

**Retry Logic:**
- Configurable `max_retries` (0-5)
- Each tier checked in order
- Connection validation before use
- Graceful fallback on failure
- User notified which tier was actually used

### 4. Connection Validation

Each tier is validated before use:
- **Cursor**: HTTP health check to `http://host.docker.internal:3000`
- **Desktop**: HTTP health check to `http://host.docker.internal:11435`
- **Docker**: Always available (internal network)

If validation fails, automatically try next tier.

## 📁 Files Created/Modified

### API Side

#### Created: `src/api/routes/query_enhanced.py`
New endpoint with:
- `/api/v1/query/enhanced` - Enhanced query with mode and tier selection
- `/api/v1/query/modes` - List available modes and descriptions
- `/api/v1/query/tier-status` - Check tier availability

**Key Functions:**
- `_process_rag_query()` - Full RAG processing
- `_process_contextual_query()` - Contextual search
- `_process_basic_query()` - Basic LLM query
- `_get_tier_client()` - Tier selection with fallback
- Connection validation for each tier

#### Modified: `src/api/app.py`
- Registered new `query_enhanced` router
- Added to OpenAPI docs under "Enhanced Query" tag

### Dashboard Side

#### Created: `pages/query_enhanced.py`
New dashboard page with:
- Real-time tier availability status
- Mode selector with descriptions
- Tier selector with warnings
- Advanced settings (temperature, retries, n_results)
- Query submission and result display
- Source citations display
- Metadata viewer
- Comprehensive help section

## 🔌 API Endpoints

### POST `/api/v1/query/enhanced`

Enhanced query with full control.

**Request:**
```json
{
  "question": "How does caching work?",
  "mode": "rag",
  "tier": "desktop",
  "n_results": 10,
  "temperature": 0.7,
  "max_retries": 2
}
```

**Response:**
```json
{
  "answer": "Caching in this system works by...",
  "mode": "rag",
  "tier_used": "desktop",
  "tier_requested": "desktop",
  "sources": [
    {
      "file_path": "src/utils/cache_decorator.py",
      "service": "ecosystem-mcp",
      "score": 0.95,
      "content_preview": "..."
    }
  ],
  "metadata": {
    "confidence": 0.87,
    "documents_used": 10,
    "model": "llama3:latest"
  }
}
```

**Parameters:**
- `question` (required): Question to answer (3-1000 chars)
- `mode` (optional): Query mode - `rag`, `contextual`, or `basic` (default: `rag`)
- `tier` (optional): LLM tier - `auto`, `cursor`, `desktop`, or `docker` (default: `auto`)
- `n_results` (optional): Documents to retrieve 1-50 (default: 10, only for rag/contextual)
- `temperature` (optional): LLM temperature 0.0-1.0 (default: 0.7)
- `max_retries` (optional): Max retry attempts 0-5 (default: 2)

**Status Codes:**
- `200`: Success
- `400`: Invalid request
- `500`: Internal server error

### GET `/api/v1/query/modes`

List available query modes with descriptions.

**Response:**
```json
{
  "modes": {
    "rag": {
      "name": "Full RAG",
      "description": "Retrieval + Augmentation + Generation",
      "features": [...],
      "best_for": "Complex questions requiring accurate, cited answers",
      "speed": "Slower (3-10s)",
      "quality": "Highest"
    },
    "contextual": {...},
    "basic": {...}
  },
  "tiers": {
    "auto": "Automatic tier selection based on complexity",
    "cursor": "Cursor IDE (Claude 4.5 Sonnet) - Highest quality",
    "desktop": "Desktop Ollama (GPU) - Good performance",
    "docker": "Docker Ollama (CPU) - Always available"
  }
}
```

### GET `/api/v1/query/tier-status`

Check tier availability.

**Response:**
```json
{
  "tiers": {
    "cursor": {
      "tier": 1,
      "name": "Cursor IDE",
      "available": false,
      "model": "Claude 4.5 Sonnet",
      "use_case": "Extreme complexity queries"
    },
    "desktop": {
      "tier": 2,
      "name": "Desktop Ollama",
      "available": true,
      "model": "llama3:latest (GPU)",
      "use_case": "Heavy workloads"
    },
    "docker": {
      "tier": 3,
      "name": "Docker Ollama",
      "available": true,
      "model": "llama3.2:3b (CPU)",
      "use_case": "Simple queries (always available)"
    }
  },
  "recommendation": "desktop"
}
```

## 🚀 Usage Examples

### Example 1: Full RAG with Auto Tier

```bash
curl -X POST "http://localhost:8000/api/v1/query/enhanced" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How does the ingestion pipeline work?",
    "mode": "rag",
    "tier": "auto"
  }'
```

**Result:**
- System analyzes complexity
- Routes to appropriate tier
- Retrieves relevant documents
- Synthesizes comprehensive answer
- Provides source citations

### Example 2: Force Desktop Ollama

```bash
curl -X POST "http://localhost:8000/api/v1/query/enhanced" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Explain caching",
    "mode": "contextual",
    "tier": "desktop",
    "max_retries": 2
  }'
```

**Result:**
- Tries Desktop Ollama first
- If unavailable, falls back to Docker
- Response indicates which tier was used

### Example 3: Quick LLM Query

```bash
curl -X POST "http://localhost:8000/api/v1/query/enhanced" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is a circuit breaker?",
    "mode": "basic",
    "tier": "docker"
  }'
```

**Result:**
- No document retrieval
- Direct LLM query
- Fast response (<1s)
- Answer from LLM knowledge only

### Example 4: Check Tier Status

```bash
curl "http://localhost:8000/api/v1/query/tier-status"
```

**Result:**
```json
{
  "tiers": {
    "cursor": {"available": false, ...},
    "desktop": {"available": true, ...},
    "docker": {"available": true, ...}
  },
  "recommendation": "desktop"
}
```

## 🎨 Dashboard Usage

### Access the Enhanced Query Interface

1. **Open Dashboard**: http://localhost:8501/
2. **Navigate**: Sidebar → "🎯 Enhanced Query Interface"
3. **Check Status**: View real-time tier availability at top
4. **Read Mode Info**: Expand mode cards to see descriptions
5. **Submit Query**:
   - Enter your question
   - Select mode (RAG, Contextual, or Basic)
   - Select tier (Auto recommended)
   - Adjust settings (documents, temperature)
   - Click "Submit Query"
6. **View Results**:
   - See which tier was used
   - Read synthesized answer
   - Browse source citations
   - Check metadata

### Dashboard Features

- **🔌 Tier Status**: Real-time availability indicators
- **📋 Mode Cards**: Expandable cards with mode descriptions
- **🎛️ Controls**: Intuitive selectors for mode, tier, and settings
- **⚙️ Advanced Settings**: Retries, temperature control
- **📊 Results Display**: Answer, sources, metadata
- **⚠️ Fallback Warnings**: Notified if requested tier unavailable
- **❓ Help Section**: Comprehensive usage guide

## 🔧 Configuration

No additional configuration needed! The system uses existing Ollama hierarchy settings from `src/config.py`:

```python
# Ollama Desktop (Tier 2)
ollama_desktop_enabled: bool = True
ollama_desktop_url: str = "http://host.docker.internal:11435"
ollama_desktop_model: str = "llama3:latest"

# Cursor IDE (Tier 1)
cursor_enabled: bool = False  # Set to True to enable
cursor_mcp_url: str = "http://host.docker.internal:3000"
cursor_model: str = "claude-4.5-sonnet"

# Docker Ollama (Tier 3)
ollama_url: str = "http://ollama:11434"
ollama_model: str = "llama3.2:3b"
```

## 🧪 Testing

### Test Tier Status

```bash
curl http://localhost:8000/api/v1/query/tier-status | jq
```

### Test RAG Mode

```bash
curl -X POST "http://localhost:8000/api/v1/query/enhanced" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How does RAG work?",
    "mode": "rag",
    "tier": "auto"
  }' | jq
```

### Test Contextual Mode

```bash
curl -X POST "http://localhost:8000/api/v1/query/enhanced" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is ChromaDB?",
    "mode": "contextual",
    "tier": "docker"
  }' | jq
```

### Test Basic Mode

```bash
curl -X POST "http://localhost:8000/api/v1/query/enhanced" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is Python?",
    "mode": "basic",
    "tier": "auto"
  }' | jq
```

### Test Tier Fallback

```bash
# Request Cursor (likely unavailable) - should fall back
curl -X POST "http://localhost:8000/api/v1/query/enhanced" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Test query",
    "mode": "basic",
    "tier": "cursor",
    "max_retries": 2
  }' | jq .tier_used
```

Expected: `"desktop"` or `"docker (fallback)"`

## 🎯 Comparison: Modes

| Feature | RAG | Contextual | Basic |
|---------|-----|------------|-------|
| Document Retrieval | ✅ Yes (semantic) | ✅ Yes (semantic) | ❌ No |
| Context Building | ✅ Sophisticated | ⚡ Simple | ❌ None |
| LLM Synthesis | ✅ Advanced prompt | ⚡ Basic prompt | ⚡ Direct query |
| Source Citations | ✅ Full citations | ⚡ Simple list | ❌ None |
| Confidence Score | ✅ Yes | ❌ No | ❌ No |
| Speed | 🐢 3-10s | ⚡ 1-3s | 🚀 <1s |
| Quality | ⭐⭐⭐ Highest | ⭐⭐ Medium | ⭐ Depends on LLM |
| Best For | Technical questions | Quick lookups | General questions |

## 🎯 Comparison: Tiers

| Tier | Model | Speed | Quality | Availability |
|------|-------|-------|---------|--------------|
| 🥇 Cursor | Claude 4.5 Sonnet | Slow | Highest | Conditional |
| 🥈 Desktop | llama3:latest (GPU) | Fast | High | Conditional |
| 🥉 Docker | llama3.2:3b (CPU) | Medium | Good | Always |

## ✨ Benefits

1. **User Control**: Manual tier selection when needed
2. **Flexibility**: Three modes for different use cases
3. **Reliability**: Automatic fallback ensures queries never fail
4. **Transparency**: User sees which tier was actually used
5. **Efficiency**: Choose speed vs quality tradeoff
6. **Protection**: Retry logic and connection validation
7. **Performance**: Use GPU when available, CPU as fallback

## 🔄 Automatic Fallback Flow

```
┌─────────────────────┐
│ User Selects Tier   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐      ┌──────────────┐
│ Check Availability  │─────▶│ Available?   │
└─────────────────────┘      └──────┬───────┘
                                    │ Yes
                                    ▼
                             ┌──────────────┐
                             │ Use Tier ✅  │
                             └──────────────┘
                                    │ No
                                    ▼
                             ┌──────────────┐
                             │ Try Next     │──┐
                             │ Tier         │  │
                             └──────────────┘  │
                                    │          │
                                    │ Retries  │
                                    └──────────┘
                                    │ Exhausted
                                    ▼
                             ┌──────────────┐
                             │ Use Docker   │
                             │ (Always ✅)  │
                             └──────────────┘
```

## 🚀 Next Steps

1. **Rebuild API container** to apply changes:
   ```bash
   docker compose build ecosystem-mcp
   docker compose up -d ecosystem-mcp
   ```

2. **Access enhanced query**:
   - API: http://localhost:8000/docs → "Enhanced Query" section
   - Dashboard: http://localhost:8501/ → "🎯 Enhanced Query Interface"

3. **Check tier status**:
   ```bash
   curl http://localhost:8000/api/v1/query/tier-status
   ```

4. **Test all modes**:
   - RAG for technical questions
   - Contextual for quick lookups
   - Basic for general queries

5. **Enable desktop Ollama** (optional):
   ```bash
   OLLAMA_HOST=0.0.0.0:11435 ollama serve
   ```

## 📚 Documentation

All endpoints are documented in OpenAPI/Swagger:
- http://localhost:8000/docs
- Look for "Enhanced Query" tag
- Interactive testing available

## ✅ Status

- ✅ Three query modes implemented (RAG, Contextual, Basic)
- ✅ Manual tier selection with auto mode
- ✅ Automatic fallback protection
- ✅ Retry logic with connection validation
- ✅ Dashboard interface created
- ✅ API endpoints documented
- ✅ Ready to use!

## 🎉 Summary

Your RAG system now has:
- **3 query modes** for different use cases
- **Manual tier selection** with auto mode
- **Automatic fallback** to ensure queries always work
- **Connection validation** before tier use
- **Retry logic** with configurable max attempts
- **Beautiful dashboard** interface
- **Full API** documentation

**Try it now!** 🚀

