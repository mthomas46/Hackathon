---
title: "Ecosystem MCP Embedding Service - Documentation Index"
service: "ecosystem-mcp-embedding"
category: "index"
tags: ["index", "embeddings", "worker", "navigation"]
related: ["../../ecosystem-mcp/docs/INDEX.md"]
status: "current"
last_updated: "2025-10-28"
audience: "all"
---

# Ecosystem MCP Embedding Service Documentation

**Dedicated embedding generation worker for Ecosystem MCP**

---

## 📚 Quick Navigation

### Getting Started
- [Quick Start Guide](guides/QUICK_START.md) - Get the worker running
- [Configuration Guide](guides/CONFIGURATION.md) - Configure embedding service

### Architecture
- [System Overview](architecture/OVERVIEW.md) - Worker architecture
- [Integration](architecture/INTEGRATION.md) - How it connects to MCP service

### API Reference
- [Endpoints](api/ENDPOINTS.md) - Worker API endpoints

---

## 🎯 Service Overview

**Purpose**: Dedicated worker for generating text embeddings

**Technology Stack**:
- **Language**: Python 3.11+
- **Framework**: FastAPI
- **Embedding Models**: Ollama (nomic-embed-text), Sentence Transformers
- **Queue**: Redis Streams
- **Deployment**: Docker container

**Key Features**:
1. **Batch Processing**: Generate embeddings in batches for efficiency
2. **Queue Integration**: Consume jobs from Redis Streams
3. **Model Routing**: Support multiple embedding models
4. **Health Monitoring**: Health checks and metrics
5. **Graceful Scaling**: Easy horizontal scaling

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│       ECOSYSTEM MCP EMBEDDING SERVICE                │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌────────────────────────────────────────────┐    │
│  │          API Layer (FastAPI)                │    │
│  ├────────────────────────────────────────────┤    │
│  │  • Health check endpoint                    │    │
│  │  • Embedding generation endpoint            │    │
│  │  • Metrics endpoint                         │    │
│  └────────────────────────────────────────────┘    │
│                       ▼                              │
│  ┌────────────────────────────────────────────┐    │
│  │      Worker Process (Background)            │    │
│  ├────────────────────────────────────────────┤    │
│  │  • Consume from Redis Stream                │    │
│  │  • Generate embeddings                      │    │
│  │  • Batch processing                         │    │
│  │  • Error handling & retry                   │    │
│  └────────────────────────────────────────────┘    │
│                       ▼                              │
│  ┌────────────────────────────────────────────┐    │
│  │      Embedding Service Layer                │    │
│  ├────────────────────────────────────────────┤    │
│  │  • Model selection (Ollama, Transformers)   │    │
│  │  • Batch optimization                       │    │
│  │  • Result caching                           │    │
│  └────────────────────────────────────────────┘    │
│                       ▼                              │
│              Ollama / Local Models                   │
│                                                      │
└─────────────────────────────────────────────────────┘
```

---

## 🔗 Integration with Ecosystem MCP

**Communication Flow**:

1. **Job Creation**: Main service creates embedding job → Redis Stream
2. **Job Consumption**: Embedding worker picks up job from Redis
3. **Processing**: Worker generates embeddings via Ollama
4. **Result Storage**: Worker stores embeddings in ChromaDB
5. **Completion**: Worker marks job as complete in Redis

**Redis Streams**:
- **Queue**: `embedding_queue`
- **Consumer Group**: `embedding_workers`
- **Message Format**: `{text: str, document_id: str, metadata: dict}`

---

## 🏷️ Tags

#embeddings #worker #ollama #redis-streams #background-processing

---

## 🔗 Related Services

- [Ecosystem MCP Service](../../ecosystem-mcp/docs/INDEX.md) - Main backend service
- [Dashboard](../../ecosystem-mcp-dashboard/docs/INDEX.md) - Web interface

---

**Last Updated**: 2025-10-28  
**Version**: 1.0.0

