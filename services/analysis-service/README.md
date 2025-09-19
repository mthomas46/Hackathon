# 📊 Analysis Service - Comprehensive Document Intelligence

<!--
LLM Processing Metadata:
- document_type: "service_documentation"
- service_name: "analysis-service"
- port: 5080
- key_concepts: ["document_analysis", "ml_processing", "consistency_checking", "distributed_analysis"]
- architecture: "distributed_analysis_engine"
- processing_hints: "Advanced document analysis with ML-powered insights and distributed processing"
- cross_references: ["../../ECOSYSTEM_MASTER_LIVING_DOCUMENT.md", "../doc_store/README.md", "../../tests/unit/analysis_service/"]
- integration_points: ["doc_store", "source_agent", "prompt_store", "redis", "llm_gateway"]
-->

**Navigation**: [Home](../../README.md) · [Architecture](../../docs/architecture/) · [Testing](../../docs/guides/TESTING_GUIDE.md) · [Services](../README_SERVICES.md)  
**Tests**: [tests/unit/analysis_service](../../tests/unit/analysis_service)

**Status**: ✅ Production Ready  
**Port**: `5080` (External) → `5020` (Internal)  
**Version**: `2.0.0`  
**Last Updated**: September 18, 2025

**Dependencies**: Doc Store, Source Agent, Prompt Store (optional), Redis (optional)

## 🎯 **Overview & Purpose**

The **Analysis Service** is the **comprehensive document intelligence engine** that powers advanced analysis capabilities across the ecosystem. With ML-powered insights and distributed processing architecture, it provides deep analysis of document consistency, quality assessment, trend analysis, and intelligent findings generation.

**Core Mission**: Transform raw document content into actionable intelligence through sophisticated analysis algorithms, enabling data-driven decisions and maintaining high content quality standards across the ecosystem.

## 🚀 **Key Features & Capabilities**

### **🔍 Advanced Analysis Engine**
- **Consistency Analysis**: Deep document consistency checking and API/document drift detection
- **Quality Assessment**: Intelligent quality scoring with degradation detection using ML algorithms
- **Semantic Analysis**: AI-powered content understanding using embedding vectors and similarity calculations
- **Trend Analysis**: Performance trends and pattern analysis for proactive insights

### **📊 Intelligent Reporting**
- **Findings Management**: Comprehensive findings retrieval and categorization (summary, trends, lifecycle, PR confidence)
- **Report Generation**: Automated report generation including Confluence consolidation and Jira staleness reports
- **Owner Notification**: Intelligent owner resolution and automated notification system
- **Analytics Dashboard**: Real-time analytics and performance monitoring

### **🤖 AI-Powered Analysis**
- **Prompt Integration**: Advanced prompt-driven analysis through Prompt Store integration
- **Natural Language Processing**: Natural language query analysis via Interpreter service
- **ML Enhancement**: Machine learning algorithms for intelligent content assessment
- **Context-Aware Processing**: Intelligent analysis based on document context and relationships

### **⚡ Distributed Processing**
- **Scalable Architecture**: Distributed processing with worker scaling for enterprise loads
- **Performance Optimization**: Intelligent load balancing and resource optimization
- **Async Operations**: Non-blocking analysis operations for high-throughput processing
- **Queue Management**: Advanced queue management for reliable analysis processing

## 🏗️ **Architecture & Design**

### **🎯 Analysis Engine Architecture**
The Analysis Service employs a sophisticated, distributed analysis architecture designed for enterprise-scale document processing:

#### **Core Components**
- **Analysis Coordinator**: Central coordination of analysis workflows
- **Worker Pool**: Scalable worker processes for distributed analysis tasks
- **Quality Engine**: ML-powered quality assessment and scoring
- **Findings Aggregator**: Intelligent aggregation and correlation of analysis results

## 📡 **API Reference**

### **🔧 Core Analysis Endpoints**

| Method | Path | Description | Purpose |
|--------|------|-------------|---------|
| **POST** | `/analyze` | Analyze targets | Core document analysis with configurable analysis types |
| **POST** | `/analyze/generate-report` | Generate simulation reports | Comprehensive analysis reports for simulation service |
| **POST** | `/analyze/pull-request` | Analyze pull request | PR analysis with refactoring suggestions and health scoring |
| **GET** | `/findings` | List findings | Retrieve analysis findings with filtering (limit, severity, type) |
| **GET** | `/integration/health` | Integration health | Service integration health and dependency status |

### **📊 Report Generation Endpoints**

| Method | Path | Description | Output |
|--------|------|-------------|--------|
| **POST** | `/reports/generate` | Generate comprehensive reports | Summary, trends, lifecycle, PR confidence analysis |
| **GET** | `/reports/confluence/consolidation` | Confluence consolidation report | Cross-platform content consolidation analysis |
| **GET** | `/reports/jira/staleness` | Jira staleness report | Issue staleness and lifecycle analysis |
| **POST** | `/reports/findings/notify-owners` | Notify finding owners | Automated owner notification for identified issues |

### **🤖 AI Integration Endpoints**

| Method | Path | Description | Integration |
|--------|------|-------------|-------------|
| **POST** | `/integration/analyze-with-prompt` | Prompt-driven analysis | Prompt Store integration for AI-powered analysis |
| **POST** | `/integration/natural-language-analysis` | Natural language analysis | Interpreter service integration for query processing |
| **POST** | `/integration/log-analysis` | Analysis usage logging | Comprehensive usage tracking and analytics |

### **🔍 Analysis Request Example**
```bash
POST /analyze
Content-Type: application/json

{
  "targets": ["document-123", "document-456"],
  "analysis_types": ["consistency", "quality", "semantic"],
  "options": {
    "include_recommendations": true,
    "severity_threshold": "medium"
  }
}
```

## ⚙️ **Configuration**

### **🔧 Environment Variables**

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DOC_STORE_URL` | Doc Store service base URL | - | ✅ |
| `SOURCE_AGENT_URL` | Source Agent service base URL | - | ✅ |
| `ANALYSIS_SERVICE_URL` | Self base URL for internal calls | - | Optional |
| `REDIS_HOST` | Redis host for event processing | `redis` | Optional |
| `SERVICE_PORT` | Service port (internal) | `5020` | Optional |

### **🎯 Service Dependencies**

| Service | Purpose | Integration | Required |
|---------|---------|-------------|----------|
| **Doc Store** | Document storage and retrieval | Core analysis data source | ✅ |
| **Source Agent** | Content ingestion and processing | Content source integration | ✅ |
| **Prompt Store** | AI-powered analysis prompts | Enhanced analysis capabilities | Optional |
| **Interpreter** | Natural language query processing | Query understanding | Optional |
| **Redis** | Event streaming and coordination | Real-time updates | Optional |

### **🚀 Quick Start**
```bash
# Start the service locally
python services/analysis-service/main.py

# Using Docker Compose
docker-compose up analysis-service

# Health check
curl http://localhost:5080/integration/health
```

## 🔗 **Integration Points**

### **🎯 Ecosystem Integration**
- **Doc Store**: Primary data source for document analysis and findings storage
- **Source Agent**: Content ingestion integration for comprehensive analysis workflows
- **Prompt Store**: AI-powered analysis through intelligent prompt utilization
- **Interpreter**: Natural language query processing for user-friendly analysis requests
- **Orchestrator**: Workflow coordination for complex multi-service analysis operations

## 🧪 **Testing**

### **🔧 Test Coverage**
- **Unit Tests**: [tests/unit/analysis_service](../../tests/unit/analysis_service) - Comprehensive unit test suite
- **Integration Tests**: Cross-service communication and data flow validation
- **Performance Tests**: Load testing for high-volume analysis operations
- **AI Testing**: Validation of ML-powered analysis accuracy and performance

### **📊 Testing Strategies**
- **Envelope-Aware Assertions**: Support for both success envelopes and direct response validation
- **Mock Integration**: Comprehensive mocking of Doc Store and Source Agent with URL-based branching
- **Parameter Validation**: Query parameter handling and error path validation
- **Filter Behavior**: Strict validation of limits, severity filtering, and type-based filtering

## 🔗 **Related Documentation**

### **📖 Primary References**
- **[Ecosystem Master Living Document](../../ECOSYSTEM_MASTER_LIVING_DOCUMENT.md#analysis-service-port-5080---comprehensive-document-intelligence)** - Complete technical reference
- **[Doc Store Service](../doc_store/README.md)** - Document storage integration
- **[Prompt Store Service](../prompt_store/README.md)** - AI-powered analysis integration

### **🎯 Integration Guides**
- **[Interpreter Service](../interpreter/README.md)** - Natural language processing integration
- **[Architecture Overview](../../docs/architecture/ECOSYSTEM_ARCHITECTURE.md)** - System design patterns
- **[Testing Guide](../../docs/guides/TESTING_GUIDE.md)** - Comprehensive testing strategies

### **⚡ Quick References**
- **[Quick Reference Guide](../../docs/guides/QUICK_REFERENCE_GUIDES.md)** - Common operations and commands
- **[Troubleshooting Index](../../docs/guides/TROUBLESHOOTING_INDEX.md)** - Issue resolution guide
- **[Services Index](../README_SERVICES.md)** - Complete service catalog

---

**🎯 The Analysis Service serves as the intelligent analysis engine that transforms raw document content into actionable insights through sophisticated ML algorithms, distributed processing, and comprehensive reporting capabilities.**
