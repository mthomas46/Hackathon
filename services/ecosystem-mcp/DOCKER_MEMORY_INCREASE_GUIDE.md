# Docker Desktop Memory Increase Guide

**Issue**: Ollama container requires 30GB to run multiple LLaMA models, but Docker Desktop is currently allocated only 7.65GB.

**Solution**: Increase Docker Desktop memory allocation to 32GB+

---

## 🎯 Current Status

```
Docker Desktop Total Memory: 7.653 GiB
Ollama Container Limit:      30 GB (configured)
LLaMA 3.1 8B Required:       8.8 GiB
Status:                      ❌ Insufficient memory
```

**Error**: `model requires more system memory (8.8 GiB) than is available (7.4 GiB)`

---

## 📋 Step-by-Step Instructions

### 1. Open Docker Desktop Settings

1. **Open Docker Desktop** application
2. Click on the **⚙️ Settings** icon (gear icon in top-right)
3. Navigate to **Resources** → **Advanced**

### 2. Increase Memory Allocation

**Current Setting**: 7.65 GB  
**Recommended Setting**: **32 GB** (minimum)

This allows:
- 30 GB for Ollama container
- 2 GB for other containers (PostgreSQL, Redis, etc.)

**If you have more RAM available:**
- **64 GB system RAM**: Allocate 48 GB to Docker
- **32 GB system RAM**: Allocate 24-28 GB to Docker
- **16 GB system RAM**: Allocate 12-14 GB to Docker (may limit model size)

### 3. Adjust Other Resources (Optional but Recommended)

While you're in the Resources settings:

**CPUs**: 
- Current: (check your setting)
- Recommended: 8-12 CPUs for M4 Max
- This enables faster LLM inference

**Swap**: 
- Recommended: 4 GB minimum
- Helps when multiple models are loaded

**Disk Image Size**:
- Recommended: 100 GB minimum
- Multiple LLaMA models can take 20-50 GB

### 4. Apply and Restart

1. Click **Apply & Restart** at the bottom
2. Docker Desktop will restart (takes 1-2 minutes)
3. Wait for Docker to fully start

---

## ✅ Verification

After restarting Docker Desktop, run this verification script:

```bash
cd /Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp
./verify_docker_memory.sh
```

Or manually verify:

```bash
# Check Docker Desktop memory
docker info | grep "Total Memory"

# Check Ollama container limit
docker inspect ecosystem-mcp-ollama | grep -A 2 "Memory"

# Test LLaMA 3.1 8B model
curl -s -X POST http://localhost:11434/api/generate \
  -d '{"model":"llama3.1:8b-instruct-q8_0","prompt":"Hello","stream":false}' \
  | python3 -m json.tool
```

**Expected Output:**
```
Total Memory: 32GiB (or higher)
✅ Model loads successfully
✅ Response generated
```

---

## 🚀 After Memory Increase

Once Docker Desktop is restarted with increased memory:

### 1. Restart Services

```bash
cd /Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp
docker-compose restart ollama
sleep 10
```

### 2. Test RAG with Better Model

```bash
# Test basic generation
curl -X POST http://localhost:11434/api/generate \
  -d '{"model":"llama3.1:8b-instruct-q8_0","prompt":"Test","stream":false}'

# Restart MCP service with new model
pkill -9 -f uvicorn
export OLLAMA_MODEL_SMALL=llama3.1:8b-instruct-q8_0
python3 -m uvicorn src.api.app:create_app --factory --host 0.0.0.0 --port 8000 &

# Test RAG endpoint
sleep 20
python3 generate_dev_history.py
```

### 3. Load Multiple Models

With 30GB available, you can pre-load multiple models:

```bash
# LLaMA 3.1 8B (8.8 GB) - Better quality
docker exec ecosystem-mcp-ollama ollama pull llama3.1:8b-instruct-q8_0

# LLaMA 3.2 3B (2 GB) - Faster responses  
docker exec ecosystem-mcp-ollama ollama pull llama3.2:3b

# Mistral 7B (8 GB) - Alternative model
docker exec ecosystem-mcp-ollama ollama pull mistral:7b-instruct-q8_0

# Check loaded models
curl -s http://localhost:11434/api/tags | python3 -m json.tool
```

---

## 💡 Benefits of 30GB Allocation

### Multiple Model Support
- **LLaMA 3.1 8B** (8.8 GB): High-quality responses
- **LLaMA 3.2 3B** (2 GB): Fast, lightweight
- **Mistral 7B** (8 GB): Alternative reasoning
- **Llama 2 13B** (13 GB): Advanced tasks (if needed)

### Better RAG Performance
- More sophisticated answer generation
- Better context understanding
- Improved multi-document synthesis
- Higher quality summaries

### Concurrent Model Loading
- Keep multiple models in memory
- Switch between models instantly
- No reload delays
- Better for production use

---

## 🔧 Troubleshooting

### Issue: Docker Desktop won't start after memory increase

**Cause**: System doesn't have enough RAM  
**Solution**: Reduce Docker memory allocation to 16-20 GB

### Issue: "Cannot allocate memory" error

**Cause**: macOS memory pressure  
**Solution**: 
1. Close other applications
2. Restart your Mac
3. Try a lower Docker memory allocation (20-24 GB)

### Issue: Ollama still reports insufficient memory

**Causes:**
1. Docker Desktop not restarted properly
2. Ollama container not restarted
3. Settings not applied

**Solutions:**
```bash
# Stop all containers
docker-compose down

# Restart Docker Desktop (via UI)

# Start containers
docker-compose up -d

# Verify
docker info | grep "Total Memory"
docker inspect ecosystem-mcp-ollama | grep "Memory"
```

### Issue: Model loads but runs very slowly

**Cause**: Not enough system RAM remaining  
**Solution**: Close other applications or reduce Docker allocation slightly

---

## 📊 Memory Allocation Recommendations

| System RAM | Docker Allocation | Ollama Models Supported |
|------------|-------------------|-------------------------|
| 16 GB | 12 GB | 1x 8B model |
| 32 GB | 24 GB | 2x 8B models |
| 64 GB | 48 GB | Multiple 8B + 13B models |
| 96 GB+ | 64 GB+ | Multiple large models |

**Current System**: Apple M4 Max (likely 36-96 GB unified memory)  
**Recommended**: 32-48 GB to Docker

---

## ✅ Expected Results After Increase

### Before (7.6 GB):
```
❌ llama3.1:8b-instruct-q8_0: FAILED (needs 8.8 GB)
✅ llama3.2:3b: Works (2 GB)
```

### After (32 GB):
```
✅ llama3.1:8b-instruct-q8_0: Works (8.8 GB)
✅ llama3.2:3b: Works (2 GB) 
✅ mistral:7b-instruct-q8_0: Works (8 GB)
✅ Multiple models simultaneously
✅ Better RAG quality
✅ Faster model switching
```

---

## 📝 Next Steps

1. ✅ Update Docker Desktop memory to 32+ GB
2. ✅ Restart Docker Desktop
3. ✅ Run verification script
4. ✅ Restart Ollama container
5. ✅ Test LLaMA 3.1 8B model
6. ✅ Restart MCP service
7. ✅ Test RAG endpoint
8. ✅ Generate development history with better quality

---

**Status**: ⏳ Awaiting Docker Desktop memory increase  
**Documentation**: This guide  
**Verification Script**: `verify_docker_memory.sh`

*Generated: 2025-10-12*

