# 🔧 Code Analyzer - Intelligent Code Analysis

<!--
LLM Processing Metadata:
- document_type: "service_documentation"
- service_name: "code-analyzer"
- port: 5025
- key_concepts: ["code_analysis", "endpoint_extraction", "security_scanning", "ai_enhancement"]
- architecture: "intelligent_code_analysis_engine"
- processing_hints: "Code analysis with API discovery, security scanning, and AI-enhanced analysis"
- cross_references: ["../../ECOSYSTEM_MASTER_LIVING_DOCUMENT.md", "../doc_store/README.md", "../../tests/unit/code_analyzer/"]
- integration_points: ["doc_store", "github_mcp", "redis", "llm_gateway"]
-->

**Navigation**: [Home](../../README.md) · [Architecture](../../docs/architecture/) · [Testing](../../docs/guides/TESTING_GUIDE.md) · [Services](../README_SERVICES.md)  
**Tests**: [tests/unit/code_analyzer](../../tests/unit/code_analyzer)

**Status**: ✅ Production Ready  
**Port**: `5025` (External) → `5025` (Internal)  
**Version**: `1.5.0`  
**Last Updated**: September 18, 2025

## 🎯 **Overview & Purpose**

The **Code Analyzer** is an **intelligent code analysis engine** that extracts API endpoints, performs security scanning, and provides AI-enhanced code understanding across multiple programming languages and frameworks. It serves as a critical component for code-aware analysis throughout the ecosystem.

**Core Mission**: Transform raw code into structured intelligence by extracting API endpoints, detecting security vulnerabilities, and providing comprehensive code analysis for enhanced ecosystem understanding.

## 🚀 **Key Features & Capabilities**

### **🔍 API Endpoint Extraction**
- **Multi-Framework Support**: Intelligent extraction from FastAPI, Flask, Express, and other popular frameworks
- **Language Agnostic**: Lightweight path-based detection adaptable to multiple programming languages
- **Golden Testing**: Comprehensive test coverage ensuring reliable endpoint detection
- **AST Integration Ready**: Extensible architecture for future AST and LLM-powered enhancements

### **🔒 Security Scanning**
- **Sensitive Pattern Detection**: Advanced scanning for PII, credentials, and security vulnerabilities
- **Secure Signal Extraction**: Identification of potential security risks in code repositories
- **Pattern Matching**: Configurable patterns for different types of sensitive information
- **Compliance Integration**: Security scanning aligned with enterprise compliance requirements

### **📊 Style Analysis & Examples**
- **Code Style Management**: Intelligent style example collection and categorization
- **Language-Specific Patterns**: Style analysis tailored to different programming languages
- **Example Persistence**: Integration with Doc Store for style example storage and retrieval
- **Best Practice Detection**: Identification of coding patterns and best practices

### **🤖 AI-Enhanced Analysis**
- **LLM Integration**: Ready for advanced AI-powered code understanding
- **Pattern Recognition**: Intelligent detection of code patterns and structures
- **Context Awareness**: Code analysis with understanding of broader application context
- **Future-Ready Architecture**: Designed for integration with advanced AI models

## 📡 **API Reference**

### **🔧 Core Analysis Endpoints**

| Method | Path | Description | Purpose |
|--------|------|-------------|---------|
| **GET** | `/health` | Service health check | System monitoring and availability verification |
| **POST** | `/analyze/text` | Analyze text for endpoints | Extract API endpoints from code text |
| **POST** | `/analyze/files` | Analyze multiple files | Batch analysis of multiple code files |
| **POST** | `/analyze/patch` | Analyze code patch | Analysis of code patches and diffs |

### **🔒 Security Analysis Endpoints**

| Method | Path | Description | Security Focus |
|--------|------|-------------|----------------|
| **POST** | `/scan/secure` | Secure scan for sensitive patterns | PII, credentials, and security vulnerability detection |

### **📊 Style Management Endpoints**

| Method | Path | Description | Purpose |
|--------|------|-------------|---------|
| **POST** | `/style/examples` | Save style examples | Store code style examples for future reference |
| **GET** | `/style/examples` | List style examples | Retrieve style examples filtered by programming language |

### **🔍 Analysis Request Examples**

#### **Text Analysis**
```bash
POST /analyze/text
Content-Type: application/json

{
  "content": "@app.get(\"/items\")\ndef get_items():\n    return {\"items\": []}",
  "language": "python"
}
```

#### **File Analysis**
```bash
POST /analyze/files
Content-Type: application/json

{
  "files": [
    {"path": "api/main.py", "content": "..."},
    {"path": "routes/users.py", "content": "..."}
  ],
  "options": {
    "extract_endpoints": true,
    "analyze_security": true
  }
}
```

## 🏗️ **Architecture & Design**

### **🎯 Analysis Engine Architecture**
The Code Analyzer employs a modular, extensible architecture designed for accurate code analysis and future enhancement:

#### **Core Components**
- **Endpoint Extractor**: Language-agnostic endpoint detection using pattern matching
- **Security Scanner**: Advanced pattern-based security vulnerability detection
- **Style Analyzer**: Code style analysis and best practice identification
- **Document Envelope Generator**: Standardized output formatting for ecosystem integration

#### **Integration Patterns**
- **Doc Store Integration**: Automatic persistence of analysis results and style examples
- **Event Broadcasting**: Redis-based event emission for real-time ecosystem updates
- **Standardized Output**: DocumentEnvelope format for consistent cross-service communication

### **🔧 Response Format**
All analysis endpoints return a `DocumentEnvelope` with:
- **Normalized Document**: Structured endpoint summary in `content`
- **Content Hash**: Unique hash for deduplication and caching
- **Source Metadata**: Original source information and analysis context
- **Style Examples**: Referenced style examples used in analysis (if applicable)

## ⚙️ **Configuration**

### **🔧 Environment Variables**

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `REDIS_HOST` | Redis host for event publishing | - | Optional |
| `DOC_STORE_URL` | Doc Store base URL for style examples | - | Optional |
| `RATE_LIMIT_ENABLED` | Enable rate limiting on heavy endpoints | `false` | Optional |
| `SERVICE_PORT` | Service port (internal) | `5025` | Optional |

### **🎯 Service Dependencies**

| Service | Purpose | Integration | Required |
|---------|---------|-------------|----------|
| **Doc Store** | Style example storage and retrieval | Enhanced analysis capabilities | Optional |
| **Redis** | Event publishing and coordination | Real-time updates | Optional |
| **GitHub MCP** | Source code integration | Code repository analysis | Integration |

## 🔗 **Integration Points**

### **🎯 Ecosystem Integration**
- **Event Emission**: Emits `docs.ingested.code` events with `DocumentEnvelope` for real-time processing
- **GitHub Integration**: Called by `github-agent` for repository analysis when `CODE_ANALYZER_URL` is configured
- **Consistency Engine**: Integrated with consistency-engine for comprehensive code analysis workflows
- **Doc Store Persistence**: Automatic storage of style examples and analysis results

### **📊 Style Example Management**
- **Doc Store Integration**: When `DOC_STORE_URL` is configured, style examples are persisted as `type=style_example`
- **Intelligent Retrieval**: GET `/style/examples` prefers doc_store index when available
- **Language Filtering**: Style examples can be filtered by programming language for relevant analysis

## 🧪 **Testing**

### **🔧 Test Coverage**
- **Unit Tests**: [tests/unit/code_analyzer](../../tests/unit/code_analyzer) - Comprehensive unit test suite
- **Golden Tests**: Validated endpoint extraction across multiple frameworks
- **Integration Tests**: Cross-service communication and event publishing validation
- **Security Testing**: Comprehensive validation of security scanning capabilities

### **📊 Testing Strategies**
- **Multi-Format Analysis**: Testing text, files, and patch analysis with normalized envelope validation
- **Framework Coverage**: Comprehensive testing across FastAPI, Flask, Express, and other frameworks
- **Security Pattern Validation**: Extensive testing of PII and credential detection patterns
- **Performance Testing**: Load testing for high-volume code analysis operations

## 🔗 **Related Documentation**

### **📖 Primary References**
- **[Ecosystem Master Living Document](../../ECOSYSTEM_MASTER_LIVING_DOCUMENT.md#code-analyzer-service-port-5025---intelligent-code-analysis)** - Complete technical reference
- **[Doc Store Service](../doc_store/README.md)** - Style example storage integration
- **[GitHub MCP Service](../github-mcp/README.md)** - Source code repository integration

### **🎯 Integration Guides**
- **[Architecture Overview](../../docs/architecture/ECOSYSTEM_ARCHITECTURE.md)** - System design patterns
- **[Testing Guide](../../docs/guides/TESTING_GUIDE.md)** - Comprehensive testing strategies
- **[Security Guide](../../docs/guides/SECURITY_GUIDE.md)** - Security scanning best practices

### **⚡ Quick References**
- **[Quick Reference Guide](../../docs/guides/QUICK_REFERENCE_GUIDES.md)** - Common operations and commands
- **[Troubleshooting Index](../../docs/guides/TROUBLESHOOTING_INDEX.md)** - Issue resolution guide
- **[Shared Utilities](../shared/README.md)** - Common infrastructure components

---

**🎯 The Code Analyzer provides intelligent code understanding capabilities, enabling comprehensive analysis, security scanning, and API discovery across multiple programming languages and frameworks to enhance ecosystem intelligence.**

