---
title: "Embedding Service - Architecture Overview"
service: "ecosystem-mcp-embedding"
category: "architecture"
tags: ["architecture", "embeddings", "worker", "ollama"]
related: ["../api/ENDPOINTS.md", "../guides/QUICK_START.md"]
status: "current"
last_updated: "2025-10-28"
audience: "developer"
difficulty: "beginner"
---

# Embedding Service - Architecture Overview

**Dedicated worker for generating text embeddings at scale**

---

## 🎯 Purpose

The Embedding Service is a **specialized worker** that:

1. **Generates Embeddings**: Convert text to vector representations
2. **Batch Processing**: Process multiple texts efficiently
3. **Queue Integration**: Consume jobs from Redis Streams
4. **Fault Tolerance**: Retry failed operations
5. **Scalability**: Easy horizontal scaling for high throughput

---

## 🏗️ Architecture

### Component Diagram

```
Main Service (ecosystem-mcp)
         │
         │ (creates job)
         ▼
    Redis Stream
    "embedding_queue"
         │
         │ (consumes)
         ▼
  Embedding Worker
         │
         ├─> Ollama (local)
         ├─> Sentence Transformers
         │
         │ (stores result)
         ▼
     ChromaDB
```

---

## 🧩 Key Components

### 1. API Layer

**Endpoints**:

- `GET /health` - Health check
- `POST /embed` - Generate embeddings (sync)
- `GET /metrics` - Prometheus metrics

**Technology**: FastAPI

### 2. Worker Process

**Responsibilities**:
- Poll Redis Stream for new jobs
- Generate embeddings via models
- Store results in ChromaDB
- Handle errors and retries

**Technology**: Python asyncio

### 3. Embedding Models

**Supported Models**:

1. **Ollama (nomic-embed-text)**:
   - Dimensions: 768
   - Speed: ~1000 docs/second
   - Quality: High

2. **Sentence Transformers**:
   - Multiple model options
   - Fallback option

---

## 📊 Data Flow

### Embedding Generation Flow

```
1. Main service creates embedding job:
   XADD embedding_queue * text="..." document_id="..." metadata="..."

2. Embedding worker polls Redis:
   XREADGROUP GROUP embedding_workers worker1 COUNT 10 BLOCK 5000 STREAMS embedding_queue >

3. Worker processes batch:
   a. Extract texts from messages
   b. Generate embeddings via Ollama
   c. Store in ChromaDB
   d. ACK messages in Redis

4. Main service queries ChromaDB:
   Results available for semantic search
```

---

## 🔧 Configuration

**Environment Variables**:

```bash
# Redis
REDIS_URL=redis://redis:6379
REDIS_STREAM_NAME=embedding_queue
REDIS_CONSUMER_GROUP=embedding_workers

# Ollama
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_EMBEDDING_MODEL=nomic-embed-text

# ChromaDB
CHROMA_HOST=ecosystem-mcp-service
CHROMA_PORT=8000

# Worker Settings
BATCH_SIZE=100
MAX_RETRIES=3
POLL_INTERVAL_MS=1000
```

---

## 📈 Performance

### Throughput
- **Single Worker**: ~1000 docs/second
- **Horizontal Scaling**: Linear scaling with workers

### Latency
- **Batch of 100**: ~100ms
- **Single document**: ~1ms (via batch)

---

## 🛡️ Fault Tolerance

### Retry Logic
- Failed embeddings retry 3 times
- Exponential backoff (1s, 2s, 4s)
- Dead letter queue for permanent failures

### Health Checks
- Redis connectivity check
- Ollama availability check
- ChromaDB connectivity check

---

## 🔗 Related Documentation

- [API Reference](../api/ENDPOINTS.md)
- [Quick Start](../guides/QUICK_START.md)
- [Main Service](../../../ecosystem-mcp/docs/INDEX.md)

---

**Last Updated**: 2025-10-28
**Version**: 1.0.0
**Status**: Production-Ready

