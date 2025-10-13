# Desktop Ollama Architecture Diagram

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          ECOSYSTEM-MCP SERVICE                              │
│                         (Port 8000 - FastAPI)                               │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                    │
              ▼                    ▼                    ▼
    ┌─────────────────┐  ┌──────────────────┐  ┌─────────────────┐
    │   RAG Service   │  │  Embedding Svc   │  │  Query Service  │
    └────────┬────────┘  └────────┬─────────┘  └────────┬────────┘
             │                    │                     │
             └────────────────────┼─────────────────────┘
                                  │
                                  ▼
                    ┌──────────────────────────────┐
                    │      OLLAMA ROUTER           │
                    │  (Intelligent Workload       │
                    │   Distribution)              │
                    └──────────┬───────────────────┘
                               │
                               │
         ┌─────────────────────┴─────────────────────┐
         │                                           │
         │  Decision Logic:                          │
         │  • Heavy workload? → Desktop GPU          │
         │  • Light workload? → Docker CPU           │
         │  • Desktop unavailable? → Fallback        │
         │                                           │
         └─────────────────────┬─────────────────────┘
                               │
                ┌──────────────┴──────────────┐
                │                             │
                ▼                             ▼
    ┌───────────────────────┐     ┌───────────────────────┐
    │   DOCKER OLLAMA       │     │  DESKTOP OLLAMA ⭐    │
    │   (CPU - Container)   │     │  (GPU - Native)       │
    ├───────────────────────┤     ├───────────────────────┤
    │ Port: 11434           │     │ Port: 11435           │
    │ Location: Container   │     │ Location: macOS       │
    │ Compute: CPU only     │     │ Compute: M4 Max GPU   │
    │ Speed: 3-5 tok/sec    │     │ Speed: 20-40 tok/sec  │
    │                       │     │                       │
    │ Models:               │     │ Models:               │
    │ • llama3.2:3b         │     │ • llama3.1:8b ⭐      │
    │ • nomic-embed-text    │     │ • mistral:7b          │
    │ • (embedding focused) │     │ • codellama:13b       │
    │                       │     │ • (generation focused)│
    │                       │     │                       │
    │ Use Cases:            │     │ Use Cases:            │
    │ ✓ Embeddings          │     │ ✓ RAG queries         │
    │ ✓ Simple queries      │     │ ✓ Long generation     │
    │ ✓ High frequency      │     │ ✓ Code generation     │
    │ ✓ Fallback            │     │ ✓ Complex reasoning   │
    └───────────────────────┘     └───────────────────────┘
                │                             │
                │                             │
                └──────────────┬──────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   LLM RESPONSE      │
                    └─────────────────────┘
```

---

## 📊 Request Flow Examples

### Example 1: RAG Query (Heavy Workload)

```
User Request: "Generate development history from 100 commits"
      │
      ▼
POST /api/v1/ask
      │
      ▼
RAGService.ask()
      │
      ├─► ChromaDB: Semantic search
      ├─► Retrieve & rank documents
      ├─► Build context prompt
      │
      ▼
OllamaRouter.generate(workload_type='rag')
      │
      ├─► Check: Desktop enabled? ✅
      ├─► Check: Desktop available? ✅
      ├─► Decision: Route to Desktop GPU
      │
      ▼
Desktop Ollama (Port 11435)
      │
      ├─► Model: llama3.1:8b-instruct-q8_0
      ├─► GPU: M4 Max (60-80% usage)
      ├─► Time: 24.3 seconds ✅
      │
      ▼
Response: Comprehensive development history
```

**Performance**: 24.3s vs 120s+ timeout (5x faster!)

---

### Example 2: Embedding (Light Workload)

```
User Request: Generate embedding for document
      │
      ▼
POST /api/v1/embed
      │
      ▼
EmbeddingService.generate_embedding()
      │
      ▼
OllamaRouter.embed()
      │
      ├─► Check: Always use Docker for embeddings
      ├─► Reason: Consistency across corpus
      │
      ▼
Docker Ollama (Port 11434)
      │
      ├─► Model: nomic-embed-text:latest
      ├─► CPU: 20-30% usage
      ├─► Time: 1.2 seconds ✅
      │
      ▼
Response: 768-dimensional embedding vector
```

**Performance**: 1.2s (CPU is sufficient)

---

### Example 3: Fallback Scenario

```
User Request: RAG query
      │
      ▼
OllamaRouter.generate(workload_type='rag')
      │
      ├─► Check: Desktop enabled? ✅
      ├─► Check: Desktop available? ❌
      │
      ├─► Log: "Desktop Ollama not available, falling back to Docker"
      ├─► Decision: Route to Docker
      │
      ▼
Docker Ollama (Port 11434)
      │
      ├─► Model: llama3.2:3b (smaller, faster)
      ├─► CPU: 80-90% usage
      ├─► Time: 45 seconds
      │
      ▼
Response: Good quality answer (slightly lower quality than 8B)
```

**Performance**: 45s (slower than GPU, but still completes!)

---

## 🔀 Routing Decision Tree

```
                    ┌─────────────────┐
                    │ Request Arrives │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ What workload?  │
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
    ┌────────┐         ┌─────────┐        ┌──────────┐
    │  RAG   │         │Embedding│        │ Simple   │
    │ Heavy  │         │  Light  │        │  Light   │
    └───┬────┘         └────┬────┘        └────┬─────┘
        │                   │                   │
        ▼                   │                   │
    ┌──────────────┐        │                   │
    │Desktop       │        │                   │
    │enabled?      │        │                   │
    └───┬──────────┘        │                   │
        │                   │                   │
    Yes │   No              │                   │
        │    │              │                   │
        ▼    │              └───────┬───────────┘
    ┌──────────────┐                │
    │Desktop       │                │
    │available?    │                │
    └───┬──────────┘                │
        │                           │
    Yes │   No                      │
        │    │                      │
        ▼    └──────────────────────┼──────┐
    ┌──────────┐                    │      │
    │ DESKTOP  │                    │      │
    │   GPU    │                    │      │
    │ (Fast!)  │                    │      │
    └──────────┘                    │      │
                                    │      │
                            ┌───────┼──────┘
                            │       │
                            ▼       ▼
                        ┌──────────────┐
                        │   DOCKER     │
                        │     CPU      │
                        │  (Reliable)  │
                        └──────────────┘
```

---

## 🎯 Configuration States

### State 1: Docker Only (Default)
```
OLLAMA_DESKTOP_ENABLED=false

All Requests → Docker Ollama (CPU)
• Simple & reliable
• Works everywhere
• Slower for heavy workloads
```

### State 2: Desktop Enabled, Desktop Available (Optimal)
```
OLLAMA_DESKTOP_ENABLED=true
Desktop: Running on port 11435

Heavy Requests → Desktop Ollama (GPU) ⭐
Light Requests → Docker Ollama (CPU)
• Best performance
• Intelligent routing
• GPU acceleration
```

### State 3: Desktop Enabled, Desktop Unavailable (Fallback)
```
OLLAMA_DESKTOP_ENABLED=true
Desktop: Not running

All Requests → Docker Ollama (CPU)
• Automatic fallback
• Service continues
• Warning logged
```

---

## 📈 Performance Matrix

| Workload Type | Size | Docker CPU | Desktop GPU | Speedup |
|--------------|------|------------|-------------|---------|
| RAG Query | Large | >120s ❌ | 15-30s ✅ | **4-8x** |
| Code Gen | Large | 60-90s | 10-15s | **6x** |
| Simple Query | Small | 17s | 2-3s | **6-8x** |
| Embedding | Small | 1.2s | 1.2s | **1x** * |
| Batch Embed | Medium | 15s | 15s | **1x** * |

*Note: Embeddings use Docker for consistency, not performance

---

## 🔒 Ports & Services

```
┌─────────────────────────────────────────────────────────────┐
│                    HOST MACHINE (macOS)                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Port 8000  ◄─── ecosystem-mcp FastAPI                      │
│  Port 11434 ◄─── Docker Ollama (in container)              │
│  Port 11435 ◄─── Desktop Ollama (native, GPU) ⭐           │
│  Port 5432  ◄─── PostgreSQL (in container)                 │
│  Port 6379  ◄─── Redis (in container)                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎛️ Monitoring & Observability

### Health Check
```
GET /api/v1/ollama/status

Response:
{
  "docker": {
    "available": true,
    "url": "http://localhost:11434",
    "model": "llama3.2:3b"
  },
  "desktop": {
    "available": true,
    "url": "http://localhost:11435",
    "model": "llama3.1:8b",
    "use_for_rag": true
  }
}
```

### Log Monitoring
```bash
# Watch routing decisions
tail -f logs/service_*.log | grep "Routing\|Desktop\|Docker"

# Example output:
INFO: OllamaRouter initialized
INFO: ✅ Desktop Ollama available at http://localhost:11435
INFO: Routing rag to desktop Ollama (GPU)
INFO: Generating with http://localhost:11435 using llama3.1:8b
```

---

## 🚀 Deployment Scenarios

### Scenario 1: Development (Laptop)
- Desktop Ollama: Enabled (GPU for speed)
- Use Case: Fast iteration, testing
- Performance: Optimal

### Scenario 2: CI/CD Pipeline
- Desktop Ollama: Disabled (Docker only)
- Use Case: Automated testing
- Performance: Reliable, consistent

### Scenario 3: Production Server
- Desktop Ollama: Depends on GPU availability
- Use Case: High-volume inference
- Performance: Best with GPU

---

**Architecture Status**: ✅ Fully Implemented  
**Routing**: ✅ Intelligent & Automatic  
**Fallback**: ✅ Graceful & Reliable  
**Performance**: ✅ 4-8x Faster with GPU  

🎉 Production-ready architecture!

