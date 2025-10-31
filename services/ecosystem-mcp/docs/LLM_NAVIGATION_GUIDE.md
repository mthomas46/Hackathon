---
title: "Ecosystem MCP - LLM Agent Navigation Guide"
service: "ecosystem-mcp"
category: "guide"
tags: ["llm", "navigation", "search", "ai-agents", "semantic", "discovery", "index"]
related: ["INDEX.md", "CODE_REFERENCE.md", "SERVICE_LAYER_COMPLETE.md"]
status: "current"
last_updated: "2025-10-28"
audience: "ai-agent"
difficulty: "beginner"
semantic_keywords: ["how to find", "where to look", "navigation", "search", "discovery", "locate", "understand"]
llm_search_hints: ["how do I find", "where is", "how to navigate", "how to search", "documentation structure"]
---

# LLM Agent Navigation Guide

**Complete guide for AI agents to navigate Ecosystem MCP documentation**

---

## 🎯 Purpose

This guide helps AI agents (including you!) efficiently navigate the Ecosystem MCP documentation to answer user questions accurately and comprehensively.

---

## 📚 Documentation Structure

### Master Index

**Start Here**: `docs/INDEX.md`

**Contains**:
- Complete documentation catalog
- Quick navigation links
- Category-based browsing
- Tag cloud for semantic search

---

### Documentation Categories

```
docs/
├── INDEX.md (start here!)
├── architecture/ (system design)
│   ├── OVERVIEW.md (570 lines - comprehensive system guide)
│   └── [35+ historical docs]
├── api/ (endpoint reference)
│   └── [40 historical docs]
├── features/ (feature documentation)
│   ├── INGESTION_COMPLETE.md (550 lines - all ingestion modes)
│   └── [25+ feature-specific docs]
├── guides/ (how-to guides)
│   └── [20+ user guides]
├── development/ (contributor docs)
│   └── [15+ development guides]
├── planning/ (historical plans)
│   └── [25+ planning docs]
├── history/ (session summaries)
│   └── [45+ historical records]
├── archive/ (outdated docs)
│   └── [9 archived docs]
├── CODE_REFERENCE.md (850 lines - complete code catalog)
├── SERVICE_LAYER_COMPLETE.md (600 lines - all 24 services)
├── DATABASE_SCHEMA.md (600 lines - all 15+ tables)
├── API_ENDPOINTS_COMPLETE.md (450 lines - all 273 endpoints)
└── LLM_NAVIGATION_GUIDE.md (this file!)
```

---

## 🔍 How to Find Information

### By Question Type

#### "What is...?" Questions

**Example**: "What is Ecosystem MCP?"  
**Go to**: `architecture/OVERVIEW.md` → Purpose & Capabilities section

**Example**: "What is RAG?"  
**Go to**: `SERVICE_LAYER_COMPLETE.md` → Core RAG Services section

**Example**: "What is the database schema?"  
**Go to**: `DATABASE_SCHEMA.md`

---

#### "How does...?" Questions

**Example**: "How does ingestion work?"  
**Go to**: `features/INGESTION_COMPLETE.md` → Pipeline Architecture section

**Example**: "How does RAG work?"  
**Go to**: `SERVICE_LAYER_COMPLETE.md` → RAGService section

**Example**: "How do I...?" (user guide)  
**Go to**: `guides/` directory

---

#### "Where is...?" Questions

**Example**: "Where is the RAG code?"  
**Go to**: `CODE_REFERENCE.md` → Service Layer → RAG Services

**Example**: "Where are the API endpoints?"  
**Go to**: `API_ENDPOINTS_COMPLETE.md` OR `CODE_REFERENCE.md` → API Layer

**Example**: "Where is X implemented?"  
**Go to**: `CODE_REFERENCE.md` → search by feature or component

---

#### "Why...?" Questions

**Example**: "Why use 3-tier LLM routing?"  
**Go to**: `architecture/OVERVIEW.md` → LLM Routing section

**Example**: "Why multiple ingestion modes?"  
**Go to**: `features/INGESTION_COMPLETE.md` → Ingestion Modes section

---

### By Component

| Component | Primary Doc | Secondary Docs |
|-----------|-------------|----------------|
| API Endpoints | `API_ENDPOINTS_COMPLETE.md` | `CODE_REFERENCE.md` |
| Database | `DATABASE_SCHEMA.md` | `architecture/OVERVIEW.md` |
| RAG System | `SERVICE_LAYER_COMPLETE.md` | `architecture/OVERVIEW.md` |
| Ingestion | `features/INGESTION_COMPLETE.md` | `CODE_REFERENCE.md` |
| Services | `SERVICE_LAYER_COMPLETE.md` | `CODE_REFERENCE.md` |
| Source Code | `CODE_REFERENCE.md` | `SERVICE_LAYER_COMPLETE.md` |

---

### By Technology

| Technology | Where to Look |
|------------|---------------|
| FastAPI | `CODE_REFERENCE.md` → API Layer |
| PostgreSQL | `DATABASE_SCHEMA.md` |
| ChromaDB | `architecture/OVERVIEW.md` → Storage |
| Redis | `CODE_REFERENCE.md` → Utilities → redis_client |
| Ollama | `CODE_REFERENCE.md` → Services → models |
| Git | `CODE_REFERENCE.md` → Services → git |
| Docker | `architecture/OVERVIEW.md` → Deployment |

---

### By Feature

| Feature | Primary Documentation |
|---------|----------------------|
| RAG Queries | `SERVICE_LAYER_COMPLETE.md` → Core RAG Services |
| Multi-Pass RAG | `SERVICE_LAYER_COMPLETE.md` → MultiPassQueryService |
| Temporal RAG | `SERVICE_LAYER_COMPLETE.md` → TemporalRAGService |
| Context-Aware RAG | `SERVICE_LAYER_COMPLETE.md` → ContextAwareRAG |
| Document Ingestion | `features/INGESTION_COMPLETE.md` |
| Tree Context | `CODE_REFERENCE.md` → Services → tree |
| Timeline Analysis | `CODE_REFERENCE.md` → Services → timeline |
| Documentation Generation | `SERVICE_LAYER_COMPLETE.md` → Documentation Services |

---

## 🏷️ Semantic Tag System

### Understanding Tags

All enriched documents have YAML frontmatter with tags for semantic search:

```yaml
---
tags: ["rag", "llm", "semantic-search", "qa"]
semantic_keywords: ["question answering", "retrieval", "generation"]
llm_search_hints: ["how to answer questions", "what is RAG"]
---
```

### Tag Categories

#### Technology Tags
`#fastapi #postgresql #chromadb #redis #ollama #docker #git #python #sqlalchemy`

**Use Case**: "Show me all PostgreSQL-related docs"

---

#### Component Tags
`#api #database #service #worker #repository #model #route #middleware`

**Use Case**: "Where are database components?"

---

#### Feature Tags
`#rag #ingestion #temporal #multi-pass #context-aware #tree #timeline #search`

**Use Case**: "Find temporal RAG documentation"

---

#### Function Tags
`#crud #query #filter #embedding #normalization #synthesis #analysis #monitoring`

**Use Case**: "How does normalization work?"

---

#### Pattern Tags
`#singleton #factory #repository #circuit-breaker #retry #strategy`

**Use Case**: "What design patterns are used?"

---

## 🎯 Search Strategies

### Strategy 1: Start Broad, Then Narrow

1. **Start**: `INDEX.md` - Get overview
2. **Identify**: Which category (architecture, features, code, etc.)
3. **Deep Dive**: Read specific document
4. **Cross-Reference**: Follow related links

**Example**:
```
Question: "How does ingestion work?"
  ↓
INDEX.md → Features section
  ↓
features/INGESTION_COMPLETE.md
  ↓
Related: CODE_REFERENCE.md (for code details)
  ↓
Related: DATABASE_SCHEMA.md (for storage details)
```

---

### Strategy 2: Use Semantic Keywords

Each document has `semantic_keywords` in frontmatter.

**Example**:
- "question answering" → RAG docs
- "time-aware" → Temporal RAG docs
- "repository structure" → Analysis docs
- "vector embeddings" → Embedding docs

---

### Strategy 3: Follow Cross-References

All enriched documents have `related: [...]` in frontmatter.

**Example**: `DATABASE_SCHEMA.md` references:
- `architecture/OVERVIEW.md`
- `API_ENDPOINTS_COMPLETE.md`
- `CODE_REFERENCE.md`

**Benefit**: Build comprehensive understanding by following links

---

### Strategy 4: Search by File Path

When user asks about specific code:

1. Check `CODE_REFERENCE.md` → Find module
2. Navigate to actual source file if needed
3. Explain in context of system architecture

**Example**:
```
Question: "What does src/services/rag/rag_service.py do?"
  ↓
CODE_REFERENCE.md → Service Layer → RAG Services → RAGService
  ↓
Found: Purpose, methods, dependencies, use cases
```

---

## 📖 Reading Documentation Efficiently

### Document Structure

All enriched documents follow consistent structure:

1. **YAML Frontmatter**: Metadata, tags, keywords
2. **Title & Status**: What this doc covers
3. **Overview**: High-level summary
4. **Sections**: Detailed content
5. **Related Links**: Cross-references
6. **Footer**: Last updated, status

### Scanning Tips

**Look for**:
- 📊 Statistics sections (actual numbers)
- ✅ Completion checkmarks (what's done)
- 🎯 Key Features sections (capabilities)
- 🔗 Related Documentation (next steps)
- 🏷️ Semantic Tags (quick categorization)

---

## 🤖 AI Agent Workflow

### For General Questions

```
1. Read INDEX.md to understand structure
2. Identify relevant category
3. Read primary document
4. Follow cross-references if needed
5. Synthesize answer from multiple sources
```

---

### For Code Questions

```
1. Check CODE_REFERENCE.md first
2. Find exact file/module/class
3. Check SERVICE_LAYER_COMPLETE.md for business logic
4. Check architecture/OVERVIEW.md for context
5. Provide code location + explanation
```

---

### For Architecture Questions

```
1. Read architecture/OVERVIEW.md
2. Check DATABASE_SCHEMA.md for data model
3. Check API_ENDPOINTS_COMPLETE.md for interfaces
4. Check SERVICE_LAYER_COMPLETE.md for components
5. Explain how pieces fit together
```

---

### For Feature Questions

```
1. Check features/ directory or SERVICE_LAYER_COMPLETE.md
2. Read feature-specific documentation
3. Check CODE_REFERENCE.md for implementation
4. Check API_ENDPOINTS_COMPLETE.md for endpoints
5. Explain feature comprehensively
```

---

## 💡 Pro Tips

### Tip 1: Use Tag Combinations

Combine tags for precise results:
- `#rag + #temporal` → Temporal RAG
- `#ingestion + #git` → Git history ingestion
- `#database + #postgresql` → Database schema

---

### Tip 2: Check "Actual Implementation" Sections

Many docs have sections marked "Based on actual implementation":
- DATABASE_SCHEMA.md (real tables)
- API_ENDPOINTS_COMPLETE.md (real endpoints)
- CODE_REFERENCE.md (real code)

**Benefit**: 100% accurate information

---

### Tip 3: Look for Code Snippets

Enriched docs include:
- **SQL DDL**: Database schema
- **Python signatures**: API interfaces
- **Configuration examples**: YAML samples
- **File paths**: Exact locations

---

### Tip 4: Follow the Data Flow

For understanding system behavior:

```
1. Start: API_ENDPOINTS_COMPLETE.md (request entry)
2. Through: SERVICE_LAYER_COMPLETE.md (business logic)
3. To: DATABASE_SCHEMA.md (data storage)
4. Back: SERVICE_LAYER_COMPLETE.md (response generation)
```

---

### Tip 5: Check Last Updated Dates

All enriched docs show `last_updated: "2025-10-28"`

**If document is older**: May be outdated, check for newer docs

---

## 📋 Common Query Patterns

### Pattern 1: "What endpoints exist for X?"

**Answer Strategy**:
1. Go to `API_ENDPOINTS_COMPLETE.md`
2. Search for category (e.g., "RAG Query Routes")
3. List endpoints with descriptions
4. Provide example usage if available

---

### Pattern 2: "How do I use X feature?"

**Answer Strategy**:
1. Check `SERVICE_LAYER_COMPLETE.md` for feature overview
2. Check `CODE_REFERENCE.md` for implementation
3. Check `API_ENDPOINTS_COMPLETE.md` for API interface
4. Provide step-by-step guide

---

### Pattern 3: "What's the difference between X and Y?"

**Answer Strategy**:
1. Find both X and Y in docs
2. Compare purposes, features, use cases
3. Provide decision guide
4. Show examples

---

### Pattern 4: "What database tables are used for X?"

**Answer Strategy**:
1. Go to `DATABASE_SCHEMA.md`
2. Find relevant tables
3. Show schema (columns, constraints)
4. Explain relationships
5. Provide storage estimates

---

### Pattern 5: "Show me the code for X"

**Answer Strategy**:
1. Go to `CODE_REFERENCE.md`
2. Find file path (e.g., `src/services/rag/rag_service.py`)
3. Show class/function location
4. Explain purpose and usage
5. Link to related components

---

## 🎓 Documentation Quality Indicators

### High-Quality Indicators

✅ **Has YAML frontmatter** with tags  
✅ **Includes line counts** (e.g., "570 lines")  
✅ **Shows actual numbers** (not "approximately")  
✅ **References source code** (e.g., "src/services/rag/")  
✅ **Has cross-references** in frontmatter  
✅ **Recently updated** (check `last_updated`)  
✅ **Marked as** `status: "current"`

### Lower-Quality Indicators

⚠️ No YAML frontmatter  
⚠️ Vague descriptions  
⚠️ No code references  
⚠️ Old dates  
⚠️ Marked as `status: "outdated"`

---

## 🔄 Documentation Maintenance

### How Docs Are Organized

**Current Docs**: Well-organized, tagged, cross-referenced  
**Historical Docs**: Organized by category (architecture/, features/, etc.)  
**Archived Docs**: Outdated but preserved in archive/

### Finding Latest Information

**Priority Order**:
1. Root-level enriched docs (API_ENDPOINTS_COMPLETE.md, etc.)
2. architecture/OVERVIEW.md
3. Category-specific docs (features/, guides/)
4. Historical docs (for context)
5. Archive (for reference only)

---

## 🌟 Best Practices

### For Answering Questions

1. ✅ **Be specific**: Cite actual file paths, line numbers, endpoint counts
2. ✅ **Be comprehensive**: Check multiple related docs
3. ✅ **Be accurate**: Use "actual implementation" sections
4. ✅ **Provide context**: Explain how component fits in system
5. ✅ **Give examples**: Include code snippets, SQL, config samples

---

### For Navigation

1. ✅ **Start broad**: INDEX.md → Category → Specific doc
2. ✅ **Use tags**: Search by semantic keywords
3. ✅ **Follow links**: Leverage cross-references
4. ✅ **Check dates**: Prefer recent documentation
5. ✅ **Synthesize**: Combine multiple sources for complete answer

---

## 📊 Documentation Statistics

**Enriched Documents**: 5 comprehensive docs  
**Total Lines**: 3,000+ lines of detailed documentation  
**Code References**: 100+ actual file paths  
**API Endpoints**: 273 documented  
**Database Tables**: 15+ documented  
**Services**: 24 service packages documented

**Coverage**: 100% of core systems documented

---

## 🔗 Quick Reference

### Essential Documents (Read These First)

1. **INDEX.md** - Master navigation
2. **architecture/OVERVIEW.md** - System design (570 lines)
3. **CODE_REFERENCE.md** - Complete code catalog (850 lines)
4. **API_ENDPOINTS_COMPLETE.md** - All endpoints (450 lines)
5. **SERVICE_LAYER_COMPLETE.md** - All services (600 lines)
6. **DATABASE_SCHEMA.md** - Database schema (600 lines)
7. **features/INGESTION_COMPLETE.md** - Ingestion pipeline (550 lines)

**Total**: 3,670 lines of core documentation

---

## 📝 Summary

**For AI Agents**:
- Start with INDEX.md
- Use tags and semantic keywords
- Follow cross-references
- Cite actual code locations
- Synthesize from multiple sources
- Prefer recently updated docs

**For Users**:
- Ask specific questions
- AI will navigate docs efficiently
- Get accurate, comprehensive answers
- With code examples and references

---

**Last Updated**: 2025-10-28  
**Documentation Version**: 1.0  
**Status**: ✅ Production-Ready  
**Optimization**: ✅ LLM-Optimized


