# 🧠 Ecosystem MCP Service

**Intelligent Refactoring Knowledge Base with Model Context Protocol Integration**

## 🎯 Overview

Ecosystem MCP is a production-grade MCP (Model Context Protocol) service that enables AI agents (like Claude in Cursor IDE) to access, analyze, and learn from your project's refactoring documentation. It provides semantic search, pattern recognition, and context-aware optimization suggestions based on your actual refactoring history.

### Key Features

- **🔌 MCP Integration**: Native integration with Cursor IDE and other MCP clients
- **🧠 Multi-Model Routing**: Intelligent routing between Ollama (local), Cursor free models, and Claude
- **📚 Document Versioning**: Git-integrated document history with time-travel capabilities
- **🔍 Semantic Search**: Vector-based search across all documentation
- **⚡ Parallel Processing**: Optimized ingestion pipeline with 8 parallel workers
- **💾 Persistent Storage**: PostgreSQL + ChromaDB + Redis for reliable data management
- **📊 Cost Tracking**: Monitor embedding and API costs in real-time
- **🔄 Resumable Ingestion**: Redis Streams enable fault-tolerant document processing

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    ECOSYSTEM MCP SERVICE                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  MCP Server (FastAPI)                                           │
│  ├── Tools: analyze, compare, search, suggest                   │
│  ├── Resources: docs/{service}, patterns/{name}                 │
│  └── Prompts: optimization guides                               │
│                           ▼                                      │
│  Model Router (Intelligent Task Distribution)                   │
│  ├── Ollama (M4 Max optimized) - Simple tasks                  │
│  ├── Cursor Free Models - Medium complexity                    │
│  └── Claude - Complex reasoning                                │
│                           ▼                                      │
│  Storage Layer                                                  │
│  ├── PostgreSQL: Metadata, versions, git commits               │
│  ├── ChromaDB: Embeddings, vector search                       │
│  └── Redis: Queues, cache, pub/sub                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- **Hardware**: Apple Silicon Mac (M1+) with 16GB+ RAM (M4 Max recommended)
- **Software**: Python 3.11+, Docker, Git
- **Services**: PostgreSQL, Redis, Ollama

### Installation

```bash
# Clone and navigate
cd services/ecosystem-mcp

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup Ollama (M4 Max optimized)
ollama pull llama3.1:8b-instruct-q8_0
ollama pull mistral:7b-instruct-q8_0
ollama pull nomic-embed-text:latest

# Start services
docker-compose up -d

# Run migrations
alembic upgrade head

# Start MCP server
python src/server.py
```

### Configure Cursor IDE

Add to your Cursor settings (`.cursor/config.json`):

```json
{
  "mcp": {
    "servers": {
      "ecosystem-mcp": {
        "command": "python",
        "args": ["/Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp/src/server.py"],
        "env": {
          "DATABASE_URL": "postgresql://ecosystem:password@localhost:5432/ecosystem_mcp",
          "REDIS_URL": "redis://localhost:6379",
          "CHROMA_PATH": "./data/chroma_db",
          "OLLAMA_BASE_URL": "http://localhost:11434"
        }
      }
    }
  }
}
```

---

## 📚 Ingestion Modes

### Mode 1: Quick Start (Current .md only)
```bash
python scripts/ingest.py --mode quick

Duration: ~1-2 minutes
Files: ~100-200 .md files
Cost: ~$0.10-0.20
Use Case: Immediate validation, quick start
```

### Mode 2: Standard (Current code + .md)
```bash
python scripts/ingest.py --mode standard

Duration: ~5-10 minutes
Files: All current files
Cost: ~$0.50-1.00
Use Case: Normal development work
```

### Mode 3: Historical Docs (Current + .md history)
```bash
python scripts/ingest.py --mode historical

Duration: ~15-30 minutes
Files: Current + all .md versions
Cost: ~$2-5
Use Case: Understanding doc evolution
```

### Mode 4: Full History (Everything)
```bash
python scripts/ingest.py --mode full

Duration: ~1-3 hours
Files: Complete git history
Cost: ~$10-50
Use Case: One-time complete analysis
```

---

## 🛠️ MCP Tools

### `analyze_service`
Analyze a service and provide refactoring recommendations.

```python
# Usage in Cursor
{
  "tool": "analyze_service",
  "arguments": {
    "service_name": "expert-finder-service",
    "focus_areas": ["testing", "documentation"]
  }
}
```

### `search_documentation`
Semantic search across all refactoring documentation.

```python
{
  "tool": "search_documentation",
  "arguments": {
    "query": "How to implement standard endpoints?",
    "service_filter": "expert-finder-service",
    "limit": 5
  }
}
```

### `compare_services`
Compare a service with similar refactored services.

```python
{
  "tool": "compare_services",
  "arguments": {
    "service_name": "doc-store",
    "compare_to": ["expert-finder-service", "code-analyzer"]
  }
}
```

### `suggest_optimizations`
Get optimization suggestions based on service analysis.

```python
{
  "tool": "suggest_optimizations",
  "arguments": {
    "service_name": "doc-store",
    "current_phase": "Phase 3"
  }
}
```

### `get_refactoring_pattern`
Get refactoring pattern with examples from similar services.

```python
{
  "tool": "get_refactoring_pattern",
  "arguments": {
    "pattern_name": "standard-endpoints",
    "service_context": "FastAPI service"
  }
}
```

---

## 📊 MCP Resources

- `ecosystem://docs/{service_name}` - Complete service documentation
- `ecosystem://patterns/{pattern_name}` - Refactoring patterns
- `ecosystem://metrics/overview` - Ecosystem metrics

---

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test suite
pytest tests/test_ingestion.py -v

# Test MCP integration
pytest tests/test_mcp.py -v
```

---

## 📈 Monitoring

### Health Check
```bash
curl http://localhost:8000/health
```

### Metrics (Prometheus)
```bash
curl http://localhost:8000/metrics
```

### Admin Dashboard
```bash
open http://localhost:8000/admin
```

---

## 🎯 Model Selection Strategy

| Task Type | Complexity | Model | Cost | Speed |
|-----------|------------|-------|------|-------|
| Metadata extraction | Low | Ollama Llama 3.1 8B | Free | Fast |
| Summarization | Low | Ollama Mistral 7B | Free | Fast |
| Code analysis | Medium | Cursor Free / Haiku | Free/Low | Medium |
| Pattern recognition | High | Claude Sonnet | Medium | Fast |
| Complex refactoring | Highest | Claude Opus | High | Medium |

---

## 📊 Performance Metrics

### Stage 1 (MVP):
- ✅ Mode 1 ingestion: < 2 minutes
- ✅ Mode 2 ingestion: < 10 minutes
- ✅ Search latency: < 500ms
- ✅ MCP response: < 2 seconds

### Stage 2 (Production):
- 🎯 Mode 3 ingestion: < 30 minutes
- 🎯 Mode 4 ingestion: < 3 hours
- 🎯 Search latency: < 100ms
- 🎯 Uptime: > 99%

---

## 🗂️ Project Structure

```
ecosystem-mcp/
├── src/
│   ├── server.py                  # MCP server entry point
│   ├── config.py                  # Configuration
│   ├── models/                    # Data models
│   │   ├── document.py
│   │   ├── embedding.py
│   │   └── git_commit.py
│   ├── services/                  # Business logic
│   │   ├── model_router.py
│   │   ├── ingestion_service.py
│   │   ├── search_service.py
│   │   └── git_service.py
│   ├── storage/                   # Database layer
│   │   ├── postgresql.py
│   │   ├── chromadb_client.py
│   │   └── redis_client.py
│   ├── ingestion/                 # Document processing
│   │   ├── pipeline.py
│   │   ├── parser.py
│   │   ├── normalizer.py
│   │   └── metadata_extractor.py
│   └── utils/                     # Utilities
│       ├── logging.py
│       └── monitoring.py
├── tests/                         # Test suite
├── docs/                          # Documentation
├── docker/                        # Docker configs
├── scripts/                       # CLI scripts
└── data/                          # Persistent data
```

---

## 🔧 Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://ecosystem:password@localhost:5432/ecosystem_mcp

# Redis
REDIS_URL=redis://localhost:6379

# ChromaDB
CHROMA_PATH=./data/chroma_db

# Ollama
OLLAMA_BASE_URL=http://localhost:11434

# API Keys (optional)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Monitoring
SENTRY_DSN=https://...

# Limits
MAX_WORKERS=8
EMBEDDING_DAILY_BUDGET_USD=10.0
MAX_SEARCH_RESULTS=50
```

---

## 📝 Documentation

- [Implementation Plan](./IMPLEMENTATION_PLAN.md) - Detailed development roadmap
- [Architecture](./docs/ARCHITECTURE.md) - System design and decisions
- [API Reference](./docs/API_REFERENCE.md) - Complete API documentation
- [Deployment Guide](./docs/DEPLOYMENT.md) - Production deployment
- [Fine-Tuning Framework](./docs/FINE_TUNING_FRAMEWORK.md) - Future capability

---

## 🎯 Roadmap

### ✅ Stage 1: Core MVP (Week 1-2)
- [x] Project structure
- [ ] Database setup
- [ ] Redis Streams
- [ ] Model router
- [ ] Basic ingestion (Mode 1 & 2)
- [ ] MCP server

### 🔄 Stage 2: Production-Ready (Week 3-4)
- [ ] Git history integration
- [ ] Document versioning
- [ ] Advanced ingestion (Mode 3 & 4)
- [ ] Monitoring & observability

### 🎯 Stage 3: Advanced Features (Week 5-6)
- [ ] Advanced RAG (reranking, hybrid search)
- [ ] Relationship graph
- [ ] Fine-tuning framework documentation
- [ ] Admin dashboard

---

## 💡 Design Decisions

### Why PostgreSQL over SQLite?
- ✅ True concurrent writes
- ✅ Better performance at scale
- ✅ JSONB for flexible metadata
- ✅ Production-ready

### Why ChromaDB?
- ✅ Embedded (no server)
- ✅ Good performance (< 100k docs)
- ✅ Simple API
- ✅ HNSW indexing

### Why Redis Streams over Kafka?
- ✅ Lightweight (< 100 MB RAM)
- ✅ Simple operations
- ✅ Persistent queues
- ✅ No ZooKeeper dependency

### Why Single Writer for ChromaDB?
- ⚠️ ChromaDB NOT designed for concurrent writes
- ✅ Prevents index corruption
- ✅ Sequential writes = data integrity
- ✅ Parallel API calls still fast

---

## 🐛 Troubleshooting

### Ollama not responding
```bash
# Check Ollama status
ollama list

# Restart Ollama
brew services restart ollama

# Check logs
tail -f ~/.ollama/logs/server.log
```

### ChromaDB slow searches
```bash
# Rebuild index
python scripts/rebuild_index.py

# Check collection stats
python scripts/check_chroma.py
```

### Redis queue backing up
```bash
# Check queue depth
redis-cli XLEN ingestion_queue

# Clear queue (careful!)
redis-cli XTRIM ingestion_queue MAXLEN 0
```

---

## 📄 License

MIT License - See LICENSE file for details

---

## 🤝 Contributing

This service is part of the Hackathon ecosystem refactoring project. See [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md) for development workflow.

---

## 📞 Support

- **Issues**: Create GitHub issue
- **Documentation**: See `/docs` directory
- **Implementation Plan**: See `IMPLEMENTATION_PLAN.md`

---

**Status**: 🟡 In Development (Stage 1 - Core MVP)  
**Version**: 0.1.0  
**Last Updated**: 2025-10-10

