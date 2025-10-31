---
title: "🔒 OLLAMA-ONLY MODE"
service: "ecosystem-mcp"
category: "api"
tags: ['api', 'background', 'config', 'configuration', 'deployment', 'docker', 'endpoints', 'ingestion', 'llm', 'ollama']
related: ['INDEX.md', 'architecture/OVERVIEW.md', 'CODE_REFERENCE.md', 'API_ENDPOINTS_COMPLETE.md']
status: "current"
last_updated: "2025-10-28"
audience: "developer"
difficulty: "intermediate"
semantic_keywords: ['api', 'background', 'config', 'configuration', 'deployment']
llm_search_hints: ['what is 🔒 ollama-only mode', 'how does 🔒 ollama-only mode work', 'guide to 🔒 ollama-only mode']
---

# 🔒 OLLAMA-ONLY MODE

**Purpose**: Run Ecosystem MCP with ONLY local Ollama (no external API calls)  
**Benefits**: Zero costs, complete privacy, offline capability  
**Status**: ✅ Fully Supported

---

## 🎯 OVERVIEW

Ollama-only mode configures the service to use **exclusively** the local Ollama instance for all LLM operations. No external API calls are made to Claude, OpenAI, or any other cloud service.

### **Perfect For**

- ✅ **Cost-conscious deployments** (zero API costs)
- ✅ **Privacy-focused organizations** (data never leaves your infrastructure)
- ✅ **Offline environments** (air-gapped or limited internet)
- ✅ **Development/testing** (no API keys required)
- ✅ **Compliance requirements** (GDPR, HIPAA, SOC2)

---

## 🚀 QUICK START

### **1. Configure Ollama-Only Mode**

Edit `.env`:

```bash
# Model Strategy
MODEL_STRATEGY=ollama-only

# Ollama Configuration
OLLAMA_HOST=ollama  # or localhost if not using Docker
OLLAMA_PORT=11434
OLLAMA_MODEL=mistral:latest
OLLAMA_EMBEDDING_MODEL=nomic-embed-text:latest

# Optional: Increase timeout for large models
OLLAMA_TIMEOUT=120
OLLAMA_CONTEXT_LENGTH=4096
```

### **2. Start Services**

```bash
# Start all services (including Ollama)
docker-compose up -d

# Wait for Ollama to be ready (~30 seconds)
docker-compose logs -f ollama
```

### **3. Pull Models**

```bash
# Pull the main LLM model
docker exec -it ecosystem-mcp-ollama ollama pull mistral:latest

# Pull the embedding model
docker exec -it ecosystem-mcp-ollama ollama pull nomic-embed-text:latest

# Verify models are available
docker exec -it ecosystem-mcp-ollama ollama list
```

### **4. Start Ecosystem MCP**

```bash
python -m src.server
```

You should see:
```
🔒 Running in OLLAMA-ONLY mode - no external API calls
Model router initialized (strategy: ollama-only)
```

---

## 📊 COMPARISON: OLLAMA-ONLY vs CLOUD

| Feature | Ollama-Only | Cloud (Claude/GPT) |
|---------|-------------|-------------------|
| **Cost** | $0 | $0.01-0.03 per 1K tokens |
| **Privacy** | 100% local | Data sent to cloud |
| **Latency** | Low (local) | Medium (network) |
| **Offline** | ✅ Yes | ❌ No |
| **Quality** | Good | Excellent |
| **Setup** | GPU recommended | API key only |
| **Limits** | Hardware only | Rate limits + costs |

---

## 🔧 CONFIGURATION OPTIONS

### **Model Strategy**

Set `MODEL_STRATEGY` in `.env`:

| Strategy | Behavior |
|----------|----------|
| `ollama-only` | **Only Ollama** - No external APIs |
| `auto` | Free-first, fallback to paid (default) |
| `cloud-first` | Prefer Claude/GPT, fallback to Ollama |

### **Ollama Models**

Recommended models for different use cases:

| Use Case | Model | Size | Performance |
|----------|-------|------|-------------|
| **General** | `mistral:latest` | 7B | Excellent |
| **Code** | `codellama:latest` | 7B-34B | Best for code |
| **Fast** | `phi:latest` | 3B | Very fast |
| **Quality** | `mixtral:latest` | 8x7B | Highest quality |
| **Embeddings** | `nomic-embed-text:latest` | - | Best embeddings |

### **Resource Limits**

```bash
# Maximum parallel workers
MAX_WORKERS=4  # Adjust based on CPU/RAM

# Ollama timeout (seconds)
OLLAMA_TIMEOUT=120  # Increase for large models

# Context window size
OLLAMA_CONTEXT_LENGTH=4096  # Model-dependent
```

---

## 🐳 DOCKER CONFIGURATION

### **Standard Setup (CPU)**

```yaml
ollama:
  image: ollama/ollama:latest
  ports:
    - "11434:11434"
  volumes:
    - ollama_data:/root/.ollama
```

### **GPU Setup (NVIDIA)**

```yaml
ollama:
  image: ollama/ollama:latest
  ports:
    - "11434:11434"
  volumes:
    - ollama_data:/root/.ollama
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
```

### **Apple Silicon (M1/M2/M3/M4)**

Ollama automatically uses Apple's Metal for GPU acceleration. No special configuration needed!

---

## 📈 PERFORMANCE OPTIMIZATION

### **1. Model Selection**

Choose based on your hardware:

**Low RAM (< 8GB)**:
```bash
docker exec -it ecosystem-mcp-ollama ollama pull phi:latest
```

**Medium RAM (8-16GB)**:
```bash
docker exec -it ecosystem-mcp-ollama ollama pull mistral:latest
```

**High RAM (16GB+) or GPU**:
```bash
docker exec -it ecosystem-mcp-ollama ollama pull mixtral:latest
```

### **2. Concurrent Requests**

Adjust based on your hardware:

```bash
# Conservative (4GB RAM)
MAX_WORKERS=1

# Moderate (8GB RAM)
MAX_WORKERS=2

# Aggressive (16GB+ RAM or GPU)
MAX_WORKERS=4
```

### **3. Context Length**

Balance between memory and capability:

```bash
# Smaller context (less memory)
OLLAMA_CONTEXT_LENGTH=2048

# Default
OLLAMA_CONTEXT_LENGTH=4096

# Larger context (more memory, better results)
OLLAMA_CONTEXT_LENGTH=8192
```

---

## 🔍 VERIFICATION

### **Check Ollama is Running**

```bash
# Via Docker
docker-compose ps ollama

# Via API
curl http://localhost:11434/api/tags
```

### **Test Model Generation**

```bash
curl http://localhost:11434/api/generate -d '{
  "model": "mistral",
  "prompt": "Why is the sky blue?",
  "stream": false
}'
```

### **Check Service is in Ollama-Only Mode**

Look for this in logs:
```
🔒 Running in OLLAMA-ONLY mode - no external API calls
```

---

## 💡 BEST PRACTICES

### **1. Pre-Pull Models**

Pull models before starting the service:

```bash
# Main model
docker exec -it ecosystem-mcp-ollama ollama pull mistral:latest

# Embedding model
docker exec -it ecosystem-mcp-ollama ollama pull nomic-embed-text:latest
```

### **2. Monitor Resources**

```bash
# Watch resource usage
docker stats ecosystem-mcp-ollama

# Watch logs
docker logs -f ecosystem-mcp-ollama
```

### **3. Optimize for Your Hardware**

**CPU-Only**:
- Use smaller models (phi, mistral 7B)
- Reduce MAX_WORKERS
- Lower OLLAMA_CONTEXT_LENGTH

**GPU (NVIDIA/AMD)**:
- Use larger models (mixtral, codellama 34B)
- Increase MAX_WORKERS
- Higher OLLAMA_CONTEXT_LENGTH

**Apple Silicon**:
- Excellent performance with Metal
- Can handle mixtral comfortably
- Good balance of speed and quality

---

## 🐛 TROUBLESHOOTING

### **Ollama Not Starting**

**Symptoms**:
```
❌ Ollama: Connection failed: Error 111
```

**Solutions**:
```bash
# Check if container is running
docker-compose ps ollama

# Start Ollama
docker-compose up -d ollama

# Check logs
docker logs ecosystem-mcp-ollama
```

### **Model Not Found**

**Symptoms**:
```
Error: model 'mistral' not found
```

**Solutions**:
```bash
# Pull the model
docker exec -it ecosystem-mcp-ollama ollama pull mistral

# Verify it's available
docker exec -it ecosystem-mcp-ollama ollama list
```

### **Slow Performance**

**Symptoms**:
- Requests timing out
- Long response times

**Solutions**:
1. **Use smaller model**:
   ```bash
   MODEL=phi:latest  # Instead of mixtral
   ```

2. **Reduce concurrency**:
   ```bash
   MAX_WORKERS=1  # One at a time
   ```

3. **Check resources**:
   ```bash
   docker stats ecosystem-mcp-ollama
   ```

### **Out of Memory**

**Symptoms**:
```
Error: failed to allocate memory
```

**Solutions**:
1. Use smaller model (phi instead of mixtral)
2. Reduce context length
3. Increase Docker memory limit
4. Close other applications

---

## 📊 COST ANALYSIS

### **Ollama-Only Costs**

| Item | Cost |
|------|------|
| **API Calls** | $0 |
| **Tokens** | $0 |
| **Storage** | Minimal (5-10GB for models) |
| **Compute** | Your hardware |

**Total**: $0 per month (after hardware)

### **Cloud Comparison**

For 1M tokens per month:

| Provider | Cost |
|----------|------|
| **Ollama** | $0 |
| **Claude Haiku** | $0.25 per 1M tokens |
| **Claude Sonnet** | $3 per 1M tokens |
| **GPT-3.5** | $0.50 per 1M tokens |
| **GPT-4** | $30 per 1M tokens |

**Savings**: 100% (infinite ROI) 🎉

---

## 🔐 PRIVACY & COMPLIANCE

### **Data Privacy**

In Ollama-only mode:
- ✅ **All data stays local** (never leaves your infrastructure)
- ✅ **No external API calls** (verified by logs)
- ✅ **Complete control** (audit, encrypt, delete)
- ✅ **GDPR compliant** (data minimization)

### **Compliance**

Suitable for:
- ✅ **GDPR** (EU data protection)
- ✅ **HIPAA** (healthcare data)
- ✅ **SOC2** (security controls)
- ✅ **FedRAMP** (government)

---

## 📚 ADDITIONAL RESOURCES

### **Ollama Documentation**

- [Ollama Models](https://ollama.ai/library)
- [Ollama API](https://github.com/ollama/ollama/blob/main/docs/api.md)
- [Ollama Docker](https://hub.docker.com/r/ollama/ollama)

### **Model Comparisons**

- [Model Benchmarks](https://github.com/ollama/ollama#model-library)
- [Hardware Requirements](https://github.com/ollama/ollama#hardware)

---

## ✅ CHECKLIST

Before deploying Ollama-only mode:

- [ ] Set `MODEL_STRATEGY=ollama-only` in `.env`
- [ ] Configure Ollama host and port
- [ ] Start Ollama container
- [ ] Pull required models (LLM + embeddings)
- [ ] Verify models are available
- [ ] Test generation endpoint
- [ ] Start Ecosystem MCP service
- [ ] Verify "OLLAMA-ONLY mode" in logs
- [ ] Test ingestion and search
- [ ] Monitor resource usage

---

## 🎉 BENEFITS SUMMARY

Using Ollama-only mode gives you:

1. **Zero Costs** - No API fees ever
2. **Complete Privacy** - Data never leaves your infrastructure
3. **Offline Capability** - Works without internet
4. **No Rate Limits** - Only limited by hardware
5. **Full Control** - Own your AI stack
6. **Compliance Ready** - GDPR, HIPAA, SOC2 compatible
7. **Predictable Performance** - No network variability
8. **Simple Billing** - No usage-based costs

**Perfect for organizations that value privacy, cost control, and data sovereignty!** 🔒

---

**Status**: ✅ Production-Ready  
**Cost**: $0/month  
**Privacy**: 100% Local  
**Recommended**: Yes (for most use cases)

