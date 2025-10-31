---
title: "Quick Start Guide - ecosystem-mcp RAG"
service: "ecosystem-mcp"
category: "guides"
tags: ['config', 'configuration', 'guide', 'howto', 'llm', 'ollama', 'optimization', 'performance', 'rag', 'retrieval']
related: ['INDEX.md', 'architecture/OVERVIEW.md', 'CODE_REFERENCE.md', 'API_ENDPOINTS_COMPLETE.md']
status: "current"
last_updated: "2025-10-28"
audience: "user"
difficulty: "beginner"
semantic_keywords: ['config', 'configuration', 'guide', 'howto', 'llm']
llm_search_hints: ['what is quick start guide - ecosystem-mcp rag', 'how does quick start guide - ecosystem-mcp rag work', 'guide to quick start guide - ecosystem-mcp rag']
---

# Quick Start Guide - ecosystem-mcp RAG

**Everything is configured and ready! Just follow these steps.**

---

## 🚀 START THE SERVICE

```bash
cd /Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp

# Ensure dependencies are running
docker-compose up -d postgres redis ollama

# Start the service
python3 -m uvicorn src.api.app:create_app --factory --host 0.0.0.0 --port 8000 &

# Wait for startup
sleep 30

# Verify health
curl http://localhost:8000/health
```

---

## 📝 GENERATE DEVELOPMENT HISTORY

```bash
# Option A: RAG with LLM (20-40 seconds with 3B model)
python3 generate_dev_history.py

# Option B: Search-only (5-10 seconds, already generated)
python3 generate_history_search_only.py
cat DEVELOPMENT_HISTORY_SEARCH.md
```

---

## 🧪 TEST RAG ENDPOINT DIRECTLY

```bash
curl -X POST http://localhost:8000/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is ecosystem-mcp?",
    "n_results": 5,
    "temperature": 0.7
  }'
```

---

## 🔍 CHECK AVAILABLE MODELS

```bash
curl http://localhost:11434/api/tags | python3 -m json.tool
```

**Current Models**:
- `llama3.2:3b` - Fast (configured for RAG)
- `llama3.1:8b-instruct-q8_0` - High quality but slow
- `codellama:7b-instruct` - Code-specific
- `mistral:7b-instruct-q8_0` - Alternative
- `nomic-embed-text:latest` - Embeddings

---

## 📊 VERIFY CONFIGURATION

```bash
./verify_docker_memory.sh
```

**Expected Output**:
```
✅ Docker Desktop: 31+ GB
✅ Ollama Container: 30 GB limit
✅ Service: Running
✅ Models: Available
✅ All checks passed!
```

---

## 🎯 WHAT'S CONFIGURED

✅ Docker: 31.29 GB memory  
✅ Ollama: 8 performance optimizations  
✅ Models: 5 models loaded (20.82 GB)  
✅ RAG: Complete with scoring & deduplication  
✅ Timeout: 120 seconds for complex queries  
✅ Model: `llama3.2:3b` (fast & efficient)  

---

## 📚 DOCUMENTATION

- `COMPLETE_IMPLEMENTATION_SUMMARY.md` - Full summary
- `OLLAMA_OPTIMIZATION_ANALYSIS.md` - Performance tuning details
- `DOCKER_MEMORY_INCREASE_GUIDE.md` - Docker setup guide
- `DEVELOPMENT_HISTORY_SEARCH.md` - Generated history document

---

## 🐛 TROUBLESHOOTING

### Service won't start
```bash
# Kill existing processes
pkill -9 -f uvicorn
lsof -ti:8000 | xargs kill -9

# Restart dependencies
docker-compose restart postgres redis ollama

# Start fresh
python3 -m uvicorn src.api.app:create_app --factory --host 0.0.0.0 --port 8000
```

### Models not responding
```bash
# Check Ollama
docker logs ecosystem-mcp-ollama --tail 50

# Restart Ollama
docker-compose restart ollama

# Verify
curl http://localhost:11434/api/tags
```

### Still timing out
```bash
# Check which model is configured
grep "ollama_model_small" src/config.py

# Should show: ollama_model_small: str = Field(default="llama3.2:3b")

# If showing 8B model, change to 3B for speed
```

---

**Status**: Ready to use! 🚀

*Last updated: 2025-10-12*

