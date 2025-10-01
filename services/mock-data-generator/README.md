# 🎭 Mock Data Generator - Intelligent Content Synthesis

<!--
LLM Processing Metadata:
- document_type: "service_documentation"
- service_name: "mock-data-generator"
- port: 5070
- key_concepts: ["data_generation", "content_synthesis", "ai_content", "testing_data", "realistic_scenarios"]
- architecture: "ai_powered_generator"
- processing_hints: "AI-powered mock data generation service with LLM integration for realistic content synthesis"
- cross_references: ["../../ECOSYSTEM_MASTER_LIVING_DOCUMENT.md", "../llm-gateway/README.md", "../../tests/unit/mock_data_generator/"]
- integration_points: ["llm_gateway", "doc_store", "analysis_service", "testing_frameworks"]
-->

**Navigation**: [Home](../../README.md) · [Architecture](../../docs/architecture/) · [Testing](../../docs/guides/TESTING_GUIDE.md) · [Services](../README_SERVICES.md)  
**Tests**: [tests/unit/mock_data_generator](../../tests/unit/mock_data_generator)

**Status**: ✅ Production Ready  
**Port**: `5070` (External) → `5020` (Internal)  
**Version**: `2.1.0`  
**Last Updated**: September 26, 2025

## 🎯 **Overview & Purpose**

The **Mock Data Generator** is the **AI-powered content synthesis engine** that generates realistic, intelligent mock data for testing and development across the LLM Documentation Ecosystem. It leverages advanced AI models to create contextually appropriate, high-quality synthetic content that closely mimics real-world documentation and data patterns.

**Core Mission**: Enable comprehensive testing and development workflows by providing AI-generated, realistic mock data that eliminates dependency on external data sources while maintaining content quality and contextual relevance.

## 🚀 **Key Features & Capabilities**

### **🤖 AI-Powered Content Generation**
- **LLM Integration**: Direct integration with LLM Gateway for intelligent content synthesis
- **Context Awareness**: Generates content that matches specific domains and contexts
- **Quality Assurance**: AI-driven quality checks and content validation
- **Multi-Format Support**: Generates content in various formats (Markdown, JSON, XML, etc.)

### **📄 Document Synthesis**
- **Comprehensive Types**: Supports 20+ document types including requirements, specifications, and reports
- **Structured Content**: Generates properly structured documents with consistent formatting
- **Metadata Enrichment**: Adds realistic metadata and properties to generated content
- **Relationship Modeling**: Creates interconnected content with proper references and links

### **🎯 Testing & Development Support**
- **Realistic Scenarios**: Generates data that closely mimics production environments
- **Configurable Complexity**: Adjustable content complexity and detail levels
- **Batch Generation**: High-volume content generation for performance testing
- **Deterministic Output**: Consistent results for reliable testing scenarios

### **🔄 Integration & Compatibility**
- **Service Integration**: Seamless integration with Doc Store and Analysis Service
- **API Compliance**: Generated content follows ecosystem API standards
- **Event Generation**: Creates realistic event streams and activity logs
- **Performance Optimization**: Efficient generation algorithms for high-throughput scenarios

## 📡 **API Reference**

### **🔧 Core Generation Endpoints**

| Method | Path | Description | Purpose |
|--------|------|-------------|---------|
| **GET** | `/health` | Service health check | System monitoring and availability verification |
| **POST** | `/generate/document` | Generate single document | Individual document creation with specific parameters |
| **POST** | `/generate/batch` | Batch document generation | High-volume document generation |
| **GET** | `/types` | Available document types | List all supported document types and templates |
| **GET** | `/templates/{type}` | Template details | Detailed information about specific document templates |

### **📊 Content Types**

| Category | Document Types | Use Cases |
|----------|----------------|-----------|
| **Requirements** | `requirements`, `user_stories`, `acceptance_criteria` | Product definition and validation |
| **Technical** | `api_specs`, `architecture_docs`, `design_docs` | Technical specification and design |
| **Process** | `workflows`, `procedures`, `guidelines` | Operational and process documentation |
| **Reports** | `status_reports`, `analysis_reports`, `metrics` | Progress tracking and analysis |

### **🔍 Generation Parameters**

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| `type` | string | Document type to generate | ✅ |
| `context` | object | Generation context and parameters | Optional |
| `complexity` | string | Content complexity level | Optional |
| `format` | string | Output format (markdown, json, etc.) | Optional |
| `metadata` | object | Additional metadata to include | Optional |

## 🏗️ **Architecture & Design**

### **🎯 AI-First Architecture**
The Mock Data Generator employs an AI-first architecture designed for intelligent content synthesis:

#### **Core Components**
- **AI Engine**: LLM Gateway integration for content generation
- **Template System**: Configurable templates for different document types
- **Quality Validator**: AI-powered content quality assessment
- **Batch Processor**: High-performance batch generation capabilities

#### **Generation Pipeline**
```
📝 Content Request → 🎯 Template Selection → 🤖 AI Generation → ✅ Quality Validation → 📤 Formatted Output
```

## ⚙️ **Configuration**

### **🔧 Environment Variables**

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SERVICE_API_PORT` | Service port (internal) | `5020` | Optional |
| `LLM_GATEWAY_URL` | LLM Gateway service URL | `http://llm-gateway:5055` | ✅ |
| `GENERATION_TIMEOUT` | AI generation timeout (seconds) | `30` | Optional |
| `MAX_BATCH_SIZE` | Maximum batch generation size | `100` | Optional |

### **🎯 Service Dependencies**

| Service | Purpose | Integration | Required |
|---------|---------|-------------|----------|
| **LLM Gateway** | AI content generation | Primary generation engine | ✅ |
| **Doc Store** | Content storage and retrieval | Generated content persistence | Optional |
| **Analysis Service** | Content quality assessment | Generation quality validation | Optional |

## 📋 **Requirements**

### **🔧 System Requirements**
- **Python**: 3.9+ with async support
- **Memory**: 1GB+ RAM for AI processing
- **Network**: Stable connectivity to LLM Gateway
- **Storage**: 500MB+ for templates and cache

### **📦 Dependencies**
- **FastAPI**: Web framework for API endpoints
- **httpx**: HTTP client for service communication
- **pydantic**: Data validation and serialization
- **LLM Gateway**: AI content generation service

## 🏗️ **Infrastructure**

### **🐳 Containerization**
- **Docker Images**: Multi-stage builds for optimized images
- **Volume Management**: Cache and template persistence
- **Resource Limits**: Configurable CPU and memory limits
- **Health Checks**: Automated container health monitoring

### **☸️ Orchestration**
- **Kubernetes**: Deployment manifests and Helm charts
- **Service Mesh**: Istio integration for traffic management
- **Auto-scaling**: Horizontal pod autoscaling based on load
- **Config Management**: Kubernetes ConfigMaps and Secrets

## 🌐 **Ecosystem Integration**

### **🎯 Primary Integrations**
- **LLM Gateway**: Core AI content generation capabilities
- **Doc Store**: Storage and retrieval of generated content
- **Analysis Service**: Quality assessment and validation
- **Project Simulation**: Realistic content for simulation scenarios

### **🔄 Integration Patterns**
- **Direct API Calls**: RESTful integration with ecosystem services
- **Event-driven Generation**: Trigger-based content generation
- **Batch Processing**: High-volume content generation workflows
- **Quality Feedback Loop**: Continuous improvement through analysis feedback

## 🧪 **Testing**

### **🔧 Test Coverage**
- **Unit Tests**: Template and generation logic validation
- **Integration Tests**: LLM Gateway and service integration testing
- **Performance Tests**: High-volume generation capacity testing
- **Quality Tests**: Generated content quality and accuracy validation

### **📊 Testing Strategies**
- **Template Validation**: Comprehensive template testing across all types
- **AI Integration Testing**: LLM Gateway communication and error handling
- **Content Quality Assessment**: Automated quality scoring and validation
- **Performance Benchmarking**: Generation speed and resource utilization testing

## 🚀 **Deployment & Operations**

### **📦 Quick Start**
```bash
# Install dependencies
pip install -r requirements.txt

# Start the service
python main.py

# Generate a sample document
curl -X POST http://localhost:5070/generate/document \
  -H "Content-Type: application/json" \
  -d '{"type": "requirements", "context": {"project": "Sample Project"}}'
```

### **🐳 Docker Deployment**
```bash
# Build and run
docker build -t mock-data-generator .
docker run -p 5070:5020 mock-data-generator
```

## 🔗 **Related Documentation**

### **📖 Primary References**
- **[Ecosystem Master Living Document](../../ECOSYSTEM_MASTER_LIVING_DOCUMENT.md#mock-data-generator-service-port-5070---intelligent-content-synthesis)** - Complete technical reference
- **[LLM Gateway Service](../llm-gateway/README.md)** - AI content generation integration
- **[Doc Store Service](../doc_store/README.md)** - Content storage integration

### **🎯 Integration Guides**
- **[Content Generation Guide](../../docs/guides/CONTENT_GENERATION.md)** - Content generation best practices
- **[AI Integration Patterns](../../docs/guides/AI_INTEGRATION.md)** - AI service integration patterns
- **[Testing with Mock Data](../../docs/guides/TESTING_MOCK_DATA.md)** - Mock data usage in testing

---

**🎯 The Mock Data Generator provides AI-powered content synthesis capabilities that enable comprehensive testing and development workflows across the entire ecosystem.**
