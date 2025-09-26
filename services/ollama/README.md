# 🦙 Ollama - Local LLM Runtime

<!--
LLM Processing Metadata:
- document_type: "service_documentation"
- service_name: "ollama"
- port: 11434
- key_concepts: ["local_llm", "ollama", "ai_models", "inference", "containerized_ai"]
- architecture: "containerized_ai_service"
- processing_hints: "Containerized Ollama service for local LLM inference and model management"
- cross_references: ["../../ECOSYSTEM_MASTER_LIVING_DOCUMENT.md", "../llm-gateway/README.md"]
- integration_points: ["llm_gateway", "external_ai_services"]
-->

**Navigation**: [Home](../../README.md) · [Architecture](../../docs/architecture/) · [Testing](../../docs/guides/TESTING_GUIDE.md) · [Services](../README_SERVICES.md)

**Status**: ✅ Production Ready  
**Port**: `11434` (External) → `11434` (Internal)  
**Version**: `0.1.0`  
**Last Updated**: September 26, 2025

## 🎯 **Overview & Purpose**

The **Ollama service** provides **local Large Language Model (LLM) inference capabilities** through a containerized Ollama runtime. It enables offline AI processing and model management for scenarios requiring local AI computation without external API dependencies.

**Core Mission**: Provide reliable, containerized LLM inference capabilities for local AI processing, model management, and offline AI workflows within the ecosystem.

## 🚀 **Key Features & Capabilities**

### **🦙 Ollama Integration**
- **Model Management**: Download, manage, and serve multiple LLM models locally
- **Inference API**: RESTful API for text generation and completion tasks
- **Model Compatibility**: Support for various open-source LLM architectures
- **Resource Optimization**: Efficient model loading and memory management

### **🐳 Containerized Deployment**
- **Isolated Runtime**: Self-contained container environment for AI processing
- **Resource Management**: Configurable CPU and memory allocation
- **Volume Persistence**: Model storage and caching persistence
- **Network Isolation**: Controlled network access for security

### **⚡ Performance Optimization**
- **GPU Support**: Optional GPU acceleration for compatible hardware
- **Model Caching**: Intelligent model loading and caching strategies
- **Batch Processing**: Efficient batch inference capabilities
- **Memory Management**: Optimized memory usage for large models

## 📡 **API Reference**

### **🔧 Core Endpoints**

| Method | Path | Description | Purpose |
|--------|------|-------------|---------|
| **GET** | `/api/tags` | List available models | Model inventory and status |
| **POST** | `/api/generate` | Text generation | AI-powered text generation |
| **POST** | `/api/chat` | Chat completion | Conversational AI interactions |
| **POST** | `/api/pull` | Pull model | Download and install models |
| **DELETE** | `/api/delete` | Delete model | Remove installed models |

### **📊 Model Management**
```bash
# List available models
GET /api/tags

# Pull a model
POST /api/pull
{
  "name": "llama2:7b"
}

# Generate text
POST /api/generate
{
  "model": "llama2:7b",
  "prompt": "Hello, how are you?",
  "stream": false
}
```

## 🏗️ **Architecture & Design**

### **🎯 Container Architecture**
The Ollama service runs as a containerized application with persistent model storage:

#### **Container Structure**
- **Base Image**: Official Ollama container image
- **Volume Mounts**: Persistent storage for models and cache
- **Port Mapping**: Standard Ollama API port (11434)
- **Resource Limits**: Configurable CPU and memory constraints

## ⚙️ **Configuration**

### **🐳 Docker Configuration**
```yaml
# docker-compose.yml
ollama:
  image: ollama/ollama:latest
  ports:
    - "11434:11434"
  volumes:
    - ollama_data:/root/.ollama
  environment:
    - OLLAMA_HOST=0.0.0.0
  restart: unless-stopped
```

### **🔧 Environment Variables**
| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `OLLAMA_HOST` | API bind address | `0.0.0.0` | Optional |
| `OLLAMA_PORT` | API port | `11434` | Optional |
| `OLLAMA_MAX_LOADED_MODELS` | Max loaded models | `3` | Optional |

## 📋 **Requirements**

### **🔧 System Requirements**
- **Docker**: Container runtime for service deployment
- **Storage**: 10GB+ for model storage and cache
- **Memory**: 4GB+ RAM minimum, 16GB+ recommended
- **CPU**: Multi-core processor for inference performance

### **🎯 Hardware Recommendations**
- **GPU**: NVIDIA GPU with CUDA support (optional, for acceleration)
- **Storage**: SSD storage for faster model loading
- **Network**: Stable internet connection for model downloads

## 🏗️ **Infrastructure**

### **🐳 Container Deployment**
- **Docker Compose**: Multi-service orchestration
- **Volume Management**: Persistent model storage
- **Network Configuration**: Service mesh integration
- **Health Monitoring**: Container health checks

### **☸️ Kubernetes Support**
- **Helm Charts**: Production deployment templates
- **Persistent Volumes**: Model data persistence
- **Resource Quotas**: CPU and memory management
- **Auto-scaling**: Load-based scaling capabilities

## 🌐 **Ecosystem Integration**

### **🎯 Primary Integrations**
- **LLM Gateway**: AI model coordination and routing
- **Mock Data Generator**: Local AI content generation
- **Analysis Service**: Offline document analysis capabilities

### **🔄 Integration Patterns**
- **Direct API Access**: RESTful communication with Ollama API
- **Model Management**: Automated model downloading and updates
- **Fallback Processing**: Local AI processing when cloud services unavailable
- **Offline Capabilities**: Full offline AI processing support

## 🧪 **Testing**

### **🔧 Test Coverage**
- **API Integration Tests**: Ollama API communication validation
- **Model Management Tests**: Model download and loading verification
- **Performance Tests**: Inference speed and resource utilization testing
- **Container Tests**: Docker deployment and configuration testing

## 🚀 **Deployment & Operations**

### **🐳 Quick Start**
```bash
# Start Ollama service
docker run -d -p 11434:11434 --name ollama ollama/ollama

# Pull a model
docker exec ollama ollama pull llama2:7b

# Test the API
curl http://localhost:11434/api/tags
```

### **📦 Model Management**
```bash
# List models
ollama list

# Pull specific model
ollama pull llama2:13b

# Remove model
ollama rm llama2:7b
```

## 🔗 **Related Documentation**

### **📖 Primary References**
- **[Ecosystem Master Living Document](../../ECOSYSTEM_MASTER_LIVING_DOCUMENT.md#ollama-service-port-11434---local-llm-runtime)** - Complete technical reference
- **[LLM Gateway Service](../llm-gateway/README.md)** - AI model coordination
- **[Ollama Documentation](https://github.com/ollama/ollama)** - Official Ollama documentation

### **🎯 Integration Guides**
- **[Local AI Setup](../../docs/guides/LOCAL_AI_SETUP.md)** - Local AI deployment guide
- **[Model Management](../../docs/guides/MODEL_MANAGEMENT.md)** - AI model management best practices
- **[Offline Processing](../../docs/guides/OFFLINE_PROCESSING.md)** - Offline AI capabilities

---

**🎯 The Ollama service provides containerized local LLM capabilities, enabling offline AI processing and model management within the ecosystem.**
