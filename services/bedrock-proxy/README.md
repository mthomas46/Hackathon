# 🌩️ Bedrock Proxy - AWS Bedrock Integration Gateway

<!--
LLM Processing Metadata:
- document_type: "service_documentation"
- service_name: "bedrock-proxy"
- port: 5060
- key_concepts: ["aws_bedrock", "llm_proxy", "ai_integration", "summarization", "template_engine"]
- architecture: "ai_gateway_proxy"
- processing_hints: "AWS Bedrock integration proxy with template-driven responses and development/production modes"
- cross_references: ["../../ECOSYSTEM_MASTER_LIVING_DOCUMENT.md", "../summarizer-hub/README.md", "../../tests/unit/bedrock_proxy/"]
- integration_points: ["summarizer_hub", "llm_gateway", "aws_bedrock", "ai_providers"]
-->

**Navigation**: [Home](../../README.md) · [Architecture](../../docs/architecture/) · [Testing](../../docs/guides/TESTING_GUIDE.md) · [Services](../README_SERVICES.md)  
**Tests**: [tests/unit/bedrock_proxy](../../tests/unit/bedrock_proxy)

**Status**: ✅ Production Ready  
**Port**: `5060` (External) → `7090` (Internal)  
**Version**: `1.7.0`  
**Last Updated**: September 18, 2025

## 🎯 **Overview & Purpose**

The **Bedrock Proxy** is a **AWS Bedrock integration gateway** that provides seamless Amazon Bedrock AI model access with intelligent template-driven responses, development mocking capabilities, and production-ready AI integration. It serves as the bridge between ecosystem services and AWS Bedrock foundation models.

**Core Mission**: Enable reliable, cost-effective access to AWS Bedrock foundation models while providing comprehensive development and testing capabilities through intelligent mocking, template systems, and production-grade proxy features.

## 🚀 **Key Features & Capabilities**

### **🌩️ AWS Bedrock Integration**
- **Foundation Model Access**: Direct integration with AWS Bedrock foundation models (Claude, Titan, etc.)
- **Multi-Model Support**: Support for various Bedrock models with intelligent routing and fallback
- **Authentication Management**: Secure AWS credential handling and authentication
- **Cost Optimization**: Usage tracking and cost management for Bedrock API calls

### **🎭 Development & Testing**
- **Mock-First Design**: Comprehensive mocking capabilities for development without AWS dependencies
- **Template-Driven Responses**: Intelligent template system for consistent, deterministic outputs
- **Offline Compatibility**: Complete offline operation for development and CI/CD environments
- **Development Acceleration**: Rapid development cycles without cloud dependencies or costs

### **📋 Template Engine**
- **Multiple Templates**: Support for summary, risks, decisions, PR confidence, and lifecycle templates
- **Format Flexibility**: Multi-format output support (Markdown, Text, JSON) with consistent structure
- **Configurable Responses**: Customizable template responses for different use cases
- **Deterministic Output**: Consistent, predictable responses for testing and validation

### **🔧 Production Features**
- **Health Monitoring**: Comprehensive health checks and service status reporting
- **Request Logging**: Detailed logging for debugging and operational monitoring
- **Error Handling**: Robust error handling with fallback and retry mechanisms
- **Performance Metrics**: Detailed metrics on request latency, success rates, and usage patterns

## 📡 **API Reference**

### **🔧 Core Proxy Endpoints**

| Method | Path | Description | Purpose |
|--------|------|-------------|---------|
| **GET** | `/health` | Service health check | System monitoring and availability verification |
| **POST** | `/invoke` | Bedrock model invocation | AI model processing and response generation |

### **📋 Template System**

| Template | Purpose | Format Support | Use Case |
|----------|---------|----------------|----------|
| `summary` | Document summarization | md, txt, json | Content summarization and key points |
| `risks` | Risk analysis | md, txt, json | Risk assessment and mitigation planning |
| `decisions` | Decision documentation | md, txt, json | Decision tracking and rationale |
| `pr_confidence` | PR confidence scoring | md, txt, json | Code review confidence assessment |
| `life_of_ticket` | Ticket lifecycle analysis | md, txt, json | Issue tracking and lifecycle management |

### **🔍 Request Parameters**

| Parameter | Type | Description | Required | Default |
|-----------|------|-------------|----------|---------|
| `prompt` | string | Input text for processing | ✅ | - |
| `model` | string | Bedrock model identifier | Optional | Auto-selected |
| `region` | string | AWS region for Bedrock | Optional | `us-east-1` |
| `template` | string | Response template type | Optional | `summary` |
| `format` | string | Output format (md/txt/json) | Optional | `md` |
| `title` | string | Title for structured responses | Optional | Auto-generated |

### **🌩️ Usage Examples**

#### **Document Summarization (Markdown)**
```bash
POST /invoke
Content-Type: application/json

{
  "prompt": "Summarize: Feature adds GET /hello endpoint with comprehensive tests and documentation",
  "template": "summary",
  "format": "md",
  "title": "Feature Summary"
}
```

#### **Risk Analysis (JSON)**
```bash
POST /invoke
Content-Type: application/json

{
  "prompt": "Analyze risks for deploying new authentication system with OAuth integration",
  "template": "risks", 
  "format": "json"
}
```

#### **PR Confidence Assessment**
```bash
POST /invoke
Content-Type: application/json

{
  "prompt": "PR #42 implements /hello endpoint per HELLO-2 with unit tests and documentation",
  "template": "pr_confidence",
  "format": "json"
}
```

### **📊 Response Formats**

#### **Markdown/Text Response**
```json
{
  "output": "## Summary\n\n- Key feature implementation\n- Comprehensive testing\n- Documentation updates",
  "model": "anthropic.claude-3-sonnet-20240229-v1:0",
  "region": "us-east-1"
}
```

#### **JSON Structured Response**
```json
{
  "title": "Feature Analysis",
  "model": "anthropic.claude-3-sonnet-20240229-v1:0", 
  "region": "us-east-1",
  "sections": {
    "Key Features": ["GET /hello endpoint", "Comprehensive testing"],
    "Benefits": ["Improved API coverage", "Enhanced documentation"]
  }
}
```

## 🏗️ **Architecture & Design**

### **🎯 Proxy Architecture**
The Bedrock Proxy employs a sophisticated gateway architecture designed for both development and production environments:

#### **Core Components**
- **Request Router**: Intelligent routing between mock and production Bedrock endpoints
- **Template Engine**: Advanced template processing with multi-format output generation
- **Authentication Manager**: Secure AWS credential handling and token management
- **Response Processor**: Intelligent response formatting and validation

#### **Integration Patterns**
- **Mock/Production Switching**: Environment-based switching between stub and real AWS Bedrock
- **Template Processing**: Advanced template system for consistent, structured responses
- **Format Transformation**: Multi-format output generation with validation
- **Error Handling**: Comprehensive error handling with fallback and retry mechanisms

## ⚙️ **Configuration**

### **🔧 Environment Variables**

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SERVICE_PORT` | Service port (internal) | `7090` | Optional |
| `AWS_ACCESS_KEY_ID` | AWS access key for Bedrock | - | Production |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key for Bedrock | - | Production |
| `AWS_REGION` | AWS region for Bedrock services | `us-east-1` | Optional |
| `BEDROCK_MOCK_MODE` | Enable mock responses | `true` | Optional |

### **🎯 Service Dependencies**

| Service | Purpose | Integration | Required |
|---------|---------|-------------|----------|
| **Summarizer Hub** | Primary AI processing client | Template-driven summarization | ✅ |
| **LLM Gateway** | AI model coordination | Bedrock provider integration | Integration |
| **AWS Bedrock** | Foundation model access | Production AI processing | Production |

### **📋 Development Setup**
```bash
# Install dependencies
pip install -r services/bedrock-proxy/requirements.txt

# Start development server
uvicorn services.bedrock-proxy.main:app --host 0.0.0.0 --port 7090

# Configure Summarizer Hub integration
export BEDROCK_ENDPOINT=http://localhost:7090/invoke
```

### **🌩️ Production Configuration**
```yaml
# services/summarizer-hub/config.yaml
providers:
  bedrock:
    endpoint: http://bedrock-proxy:7090/invoke
    model: anthropic.claude-3-sonnet-20240229-v1:0
    region: us-east-1
```

## 🔗 **Integration Points**

### **🎯 Ecosystem Integration**
- **Summarizer Hub**: Primary integration for AI-powered content processing and analysis
- **LLM Gateway**: Provider coordination and intelligent routing for AI operations
- **Template System**: Consistent response formatting for downstream service consumption
- **Development Tools**: Comprehensive mocking capabilities for development and testing

### **🌩️ AWS Bedrock Integration**
- **Foundation Models**: Access to Claude, Titan, and other AWS Bedrock foundation models
- **Cost Management**: Usage tracking and cost optimization for large-scale deployments
- **Authentication**: Secure credential handling and AWS service integration
- **Performance Optimization**: Caching and request optimization for high-volume scenarios

## 🧪 **Testing**

### **🔧 Test Coverage**
- **Unit Tests**: [tests/unit/bedrock_proxy](../../tests/unit/bedrock_proxy) - Comprehensive unit test suite
- **Template Validation**: Comprehensive testing of template processing and format generation
- **Integration Tests**: AWS Bedrock integration and authentication validation
- **Mock Validation**: Development mocking capabilities and response consistency

### **📊 Testing Strategies**
- **Template Response Validation**: Format-driven response shape and structure checks
- **Multi-Format Testing**: Markdown, text, and JSON output validation across all templates
- **Authentication Testing**: AWS credential handling and security validation
- **Performance Testing**: High-volume request processing and response time validation

### **🔄 Mock vs Production Testing**
- **Mock Mode**: Comprehensive template-driven response validation for development
- **Production Mode**: Real AWS Bedrock integration testing with controlled environments
- **Switching Validation**: Environment-based mode switching and configuration testing
- **Error Simulation**: Network failures, authentication errors, and service unavailability

## 🚀 **Deployment & Operations**

### **🔧 Development Deployment**
- **Local Development**: Standalone operation with comprehensive mocking capabilities
- **CI/CD Integration**: Deterministic responses for automated testing and validation
- **Template Development**: Interactive template development and testing environment
- **Cost-Free Development**: Complete development capabilities without AWS charges

### **🌩️ Production Deployment**
- **AWS Integration**: Full AWS Bedrock foundation model access and processing
- **Scalability**: High-performance proxy for large-scale AI processing workloads
- **Monitoring**: Comprehensive monitoring and observability for production operations
- **Security**: Enterprise-grade security with credential management and access control

## 🔗 **Related Documentation**

### **📖 Primary References**
- **[Ecosystem Master Living Document](../../ECOSYSTEM_MASTER_LIVING_DOCUMENT.md#bedrock-proxy-service-port-5060---aws-bedrock-integration)** - Complete technical reference
- **[Summarizer Hub Service](../summarizer-hub/README.md)** - Primary integration and AI processing client
- **[LLM Gateway Service](../llm-gateway/README.md)** - AI provider coordination and routing

### **🎯 Integration Guides**
- **[AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)** - Official AWS Bedrock documentation
- **[Architecture Overview](../../docs/architecture/ECOSYSTEM_ARCHITECTURE.md)** - System design patterns
- **[Testing Guide](../../docs/guides/TESTING_GUIDE.md)** - Comprehensive testing strategies

### **⚡ Quick References**
- **[Quick Reference Guide](../../docs/guides/QUICK_REFERENCE_GUIDES.md)** - Common operations and commands
- **[Troubleshooting Index](../../docs/guides/TROUBLESHOOTING_INDEX.md)** - Issue resolution guide
- **[Shared Utilities](../shared/README.md)** - Common infrastructure components

---

**🎯 The Bedrock Proxy provides seamless AWS Bedrock integration with intelligent template processing, enabling both cost-effective development through comprehensive mocking and production-ready AI processing capabilities.**
