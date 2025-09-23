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
- **Multi-Dimensional Analysis**: Comprehensive analysis across consistency, quality, semantic similarity, sentiment, tone, and risk factors
- **Quality Degradation Detection**: ML-powered detection of documentation quality degradation over time
- **Semantic Similarity Analysis**: AI-powered content understanding using embedding vectors and similarity calculations
- **Trend Analysis & Forecasting**: Performance trends, predictive analytics, and maintenance forecasting
- **Risk Assessment**: Comprehensive risk factor analysis for documentation drift and quality issues

### **📊 Intelligent Reporting & Findings**
- **Comprehensive Findings Management**: Advanced categorization (summary, trends, lifecycle, PR confidence, maintenance forecasts)
- **Automated Report Generation**: Multi-format reports including Confluence consolidation, Jira staleness, and cross-repository analysis
- **Owner Resolution & Notification**: Intelligent owner identification and automated notification workflows
- **Real-time Analytics Dashboard**: Live monitoring with performance metrics and health scoring

### **🤖 AI-Powered Analysis Suite**
- **Prompt-Driven Analysis**: Advanced integration with Prompt Store for customizable AI analysis workflows
- **Natural Language Processing**: Interpreter service integration for natural language query processing
- **Sentiment & Tone Analysis**: ML algorithms for content sentiment, tone patterns, and writing style assessment
- **Context-Aware Processing**: Intelligent analysis considering document relationships and ecosystem context

### **⚡ Enterprise Distributed Processing**
- **Scalable Worker Architecture**: Dynamic worker scaling with intelligent load balancing strategies
- **High-Throughput Processing**: Async operations with advanced queue management for enterprise workloads
- **Cross-Repository Analysis**: Multi-repository connectivity analysis and dependency mapping
- **Automated Remediation**: AI-powered automated fixes for detected documentation issues

## 🏗️ **Architecture & Design**

### **🎯 Analysis Engine Architecture**
The Analysis Service employs a sophisticated, modular architecture designed for enterprise-scale document processing with extensive analysis capabilities:

#### **Core Architectural Components**
- **Analysis Coordinator**: Central orchestration of analysis workflows and distributed task management
- **Distributed Processor**: Scalable worker pool with intelligent load balancing and queue management
- **Analysis Handler Framework**: Modular handler system for different analysis types (semantic, quality, risk, trend, etc.)
- **Automated Remediation Engine**: AI-powered automated fixes and remediation workflows
- **Cross-Repository Analyzer**: Multi-repository analysis and dependency mapping capabilities

#### **Analysis Modules & Capabilities**
- **Semantic Analysis**: Embedding-based similarity analysis and content understanding
- **Quality Assessment**: ML-powered quality scoring with degradation detection
- **Risk Assessment**: Comprehensive risk factor analysis and predictive modeling
- **Trend Analysis**: Performance trends and predictive maintenance forecasting
- **Sentiment Analysis**: Content sentiment, tone, and writing style assessment
- **Change Impact Analysis**: Impact assessment for documentation changes across portfolios

#### **Enterprise Features**
- **Workflow Integration**: Event-driven analysis workflows with webhook support
- **Maintenance Forecasting**: Predictive maintenance scheduling and lifecycle management
- **Repository Connectivity**: Cross-platform repository analysis and dependency mapping
- **Real-time Monitoring**: Live analytics dashboard with performance metrics

## 📡 **API Reference**

### **🔍 Analysis Endpoints**

| Method | Path | Description | Analysis Type |
|--------|------|-------------|---------------|
| **POST** | `/analyze` | Core document analysis | Configurable multi-type analysis |
| **POST** | `/analyze/semantic-similarity` | Semantic similarity analysis | Embedding-based content similarity |
| **POST** | `/analyze/sentiment` | Sentiment analysis | Content sentiment and tone assessment |
| **POST** | `/analyze/tone` | Tone analysis | Writing style and tone patterns |
| **POST** | `/analyze/quality` | Quality assessment | Comprehensive quality scoring |
| **POST** | `/analyze/trends` | Trend analysis | Performance trends and predictions |
| **POST** | `/analyze/trends/portfolio` | Portfolio trend analysis | Cross-document trend analysis |
| **POST** | `/analyze/risk` | Risk assessment | Documentation risk factor analysis |
| **POST** | `/analyze/risk/portfolio` | Portfolio risk assessment | Cross-document risk analysis |
| **POST** | `/analyze/maintenance/forecast` | Maintenance forecasting | Predictive maintenance scheduling |
| **POST** | `/analyze/maintenance/forecast/portfolio` | Portfolio maintenance forecast | Cross-document maintenance planning |
| **POST** | `/analyze/quality/degradation` | Quality degradation detection | Time-based quality monitoring |
| **POST** | `/analyze/quality/degradation/portfolio` | Portfolio quality monitoring | Cross-document quality trends |
| **POST** | `/analyze/change/impact` | Change impact analysis | Impact assessment for documentation changes |
| **POST** | `/analyze/change/impact/portfolio` | Portfolio change impact | Cross-document change analysis |

### **🔧 Remediation & Workflow Endpoints**

| Method | Path | Description | Function |
|--------|------|-------------|----------|
| **POST** | `/remediate` | Apply automated fixes | Execute remediation workflows |
| **POST** | `/remediate/preview` | Preview remediation changes | Dry-run remediation without execution |
| **POST** | `/workflows/events` | Process workflow events | Event-driven analysis triggering |
| **GET** | `/workflows/{workflow_id}` | Get workflow status | Workflow execution monitoring |
| **GET** | `/workflows/queue/status` | Get queue status | Workflow queue monitoring |
| **POST** | `/workflows/webhook/config` | Configure webhooks | Workflow integration setup |

### **🏢 Repository & Cross-Platform Analysis**

| Method | Path | Description | Scope |
|--------|------|-------------|-------|
| **POST** | `/repositories/analyze` | Multi-repository analysis | Cross-repository documentation analysis |
| **POST** | `/repositories/connectivity` | Connectivity analysis | Repository dependency mapping |
| **POST** | `/repositories/connectors/config` | Configure connectors | External system integration setup |
| **GET** | `/repositories/connectors` | List connectors | Available repository connectors |
| **GET** | `/repositories/frameworks` | Analysis frameworks | Cross-repository analysis frameworks |

### **⚡ Distributed Processing Endpoints**

| Method | Path | Description | Management |
|--------|------|-------------|------------|
| **POST** | `/distributed/tasks` | Submit distributed task | Single task distributed processing |
| **POST** | `/distributed/tasks/batch` | Submit batch tasks | Multiple tasks batch processing |
| **GET** | `/distributed/tasks/{task_id}` | Get task status | Task execution monitoring |
| **DELETE** | `/distributed/tasks/{task_id}` | Cancel distributed task | Task cancellation |
| **GET** | `/distributed/workers` | Get worker status | Worker pool monitoring |
| **GET** | `/distributed/stats` | Get processing stats | Distributed system statistics |
| **POST** | `/distributed/workers/scale` | Scale workers | Dynamic worker scaling |
| **POST** | `/distributed/start` | Start distributed system | System initialization |
| **PUT** | `/distributed/load-balancing/strategy` | Configure load balancing | Load distribution strategy |
| **GET** | `/distributed/queue/status` | Get queue status | Processing queue monitoring |
| **PUT** | `/distributed/load-balancing/config` | Configure load balancing | Advanced load balancing settings |
| **GET** | `/distributed/load-balancing/config` | Get load balancing config | Current load balancing configuration |

### **📊 Reporting & Findings Management**

| Method | Path | Description | Output |
|--------|------|-------------|--------|
| **GET** | `/findings` | List findings | Filtered findings retrieval |
| **GET** | `/detectors` | List analysis detectors | Available analysis capabilities |
| **POST** | `/reports/generate` | Generate reports | Multi-format report generation |
| **GET** | `/reports/confluence/consolidation` | Confluence consolidation | Content consolidation analysis |
| **GET** | `/reports/jira/staleness` | Jira staleness analysis | Issue lifecycle analysis |
| **POST** | `/reports/findings/notify-owners` | Notify owners | Automated owner notifications |

### **🔗 Integration & Health Endpoints**

| Method | Path | Description | Integration |
|--------|------|-------------|-------------|
| **GET** | `/integration/health` | Integration health check | Service dependency status |
| **POST** | `/integration/analyze-with-prompt` | Prompt-driven analysis | Prompt Store AI integration |
| **POST** | `/integration/natural-language-analysis` | Natural language analysis | Interpreter NLP integration |
| **POST** | `/integration/log-analysis` | Analysis usage logging | Usage tracking and analytics |

### **🔍 Analysis Request Examples**

#### **Multi-Type Document Analysis**
```bash
POST /analyze
Content-Type: application/json

{
  "targets": ["document-123", "document-456"],
  "analysis_types": ["consistency", "quality", "semantic"],
  "options": {
    "include_recommendations": true,
    "severity_threshold": "medium",
    "context_window": 1000
  }
}
```

#### **Semantic Similarity Analysis**
```bash
POST /analyze/semantic-similarity
Content-Type: application/json

{
  "documents": ["doc-1", "doc-2", "doc-3"],
  "similarity_threshold": 0.8,
  "embedding_model": "text-embedding-ada-002",
  "analysis_scope": "content_and_metadata"
}
```

#### **Quality Degradation Analysis**
```bash
POST /analyze/quality/degradation
Content-Type: application/json

{
  "document_id": "doc-123",
  "time_range": {
    "start": "2024-01-01T00:00:00Z",
    "end": "2024-12-31T23:59:59Z"
  },
  "degradation_metrics": ["completeness", "accuracy", "consistency"],
  "alert_threshold": 0.1
}
```

#### **Risk Assessment Portfolio Analysis**
```bash
POST /analyze/risk/portfolio
Content-Type: application/json

{
  "portfolio_scope": {
    "repositories": ["repo-1", "repo-2"],
    "document_types": ["api_docs", "user_guides"],
    "tags": ["critical", "public"]
  },
  "risk_factors": ["drift", "staleness", "inconsistency"],
  "prediction_window_days": 90,
  "risk_threshold": "high"
}
```

#### **Distributed Task Processing**
```bash
POST /distributed/tasks/batch
Content-Type: application/json

{
  "tasks": [
    {
      "type": "semantic_analysis",
      "document_ids": ["doc-1", "doc-2"],
      "priority": "high"
    },
    {
      "type": "quality_assessment",
      "document_ids": ["doc-3", "doc-4"],
      "priority": "medium"
    }
  ],
  "load_balancing_strategy": "adaptive",
  "completion_callback": "http://callback-service/notify"
}
```

#### **Automated Remediation**
```bash
POST /remediate
Content-Type: application/json

{
  "findings": ["finding-123", "finding-456"],
  "remediation_strategy": "conservative",
  "preview_only": false,
  "backup_original": true,
  "owner_approval_required": true
}
```

## ⚙️ **Configuration**

### **🔧 Environment Variables**

#### **Core Service Configuration**
| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SERVICE_PORT` | Service port (internal) | `5020` | Optional |
| `HOST` | Service host binding | `0.0.0.0` | Optional |
| `ENVIRONMENT` | Deployment environment | `development` | Optional |
| `DEBUG` | Enable debug logging | `false` | Optional |
| `LOG_LEVEL` | Logging level | `INFO` | Optional |
| `TESTING` | Enable testing mode | `false` | Optional |

#### **Database & Caching Configuration**
| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `ANALYSIS_DB_PATH` | Analysis database path | `./data/analysis.db` | Optional |
| `ENABLE_CACHING` | Enable caching layer | `true` | Optional |
| `CACHE_MAX_MEMORY` | Cache memory limit (MB) | `512` | Optional |
| `CACHE_DEFAULT_TTL` | Default cache TTL (seconds) | `3600` | Optional |
| `CACHE_CONNECTION_TIMEOUT` | Cache connection timeout | `5` | Optional |
| `CACHE_ENABLE_COMPRESSION` | Enable cache compression | `true` | Optional |
| `CACHE_MAX_RETRIES` | Maximum cache retry attempts | `3` | Optional |
| `CACHE_POOL_SIZE` | Cache connection pool size | `10` | Optional |

#### **Distributed Processing Configuration**
| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `MAX_CONCURRENT_REQUESTS` | Maximum concurrent requests | `100` | Optional |
| `REQUEST_TIMEOUT` | Request timeout (seconds) | `30` | Optional |
| `EXTERNAL_MAX_RETRIES` | External service retry attempts | `3` | Optional |
| `EXTERNAL_REQUEST_TIMEOUT` | External request timeout | `10` | Optional |
| `EXTERNAL_RETRY_DELAY` | Retry delay between attempts | `1` | Optional |

#### **AI/ML Model Configuration**
| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `OPENAI_MODEL` | OpenAI model for analysis | `gpt-4` | Optional |
| `OPENAI_MAX_TOKENS` | Maximum tokens per request | `4096` | Optional |
| `OPENAI_TEMPERATURE` | Model temperature setting | `0.3` | Optional |
| `SENTIMENT_MODEL` | Sentiment analysis model | `cardiffnlp/twitter-roberta-base-sentiment` | Optional |
| `SENTIMENT_CONFIDENCE_THRESHOLD` | Sentiment confidence threshold | `0.6` | Optional |
| `SEMANTIC_SIMILARITY_THRESHOLD` | Semantic similarity threshold | `0.8` | Optional |
| `SEMANTIC_BATCH_SIZE` | Batch size for semantic processing | `10` | Optional |

#### **External Service Integration**
| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `REDIS_HOST` | Redis host for event processing | `redis` | Optional |
| `REDIS_PORT` | Redis port | `6379` | Optional |
| `REDIS_DB` | Redis database number | `0` | Optional |
| `REDIS_SSL` | Enable Redis SSL | `false` | Optional |
| `POSTGRES_PORT` | PostgreSQL port (if used) | `5432` | Optional |

#### **Observability & Monitoring**
| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `ENABLE_METRICS` | Enable metrics collection | `true` | Optional |
| `ENABLE_TRACING` | Enable distributed tracing | `false` | Optional |

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
- **Analysis Algorithm Tests**: Validation of semantic, sentiment, quality, risk, and trend analysis algorithms
- **Distributed Processing Tests**: Worker scaling, load balancing, and task queue management validation
- **Integration Tests**: Cross-service communication with Doc Store, Prompt Store, and Interpreter services
- **Remediation Tests**: Automated fix validation and preview functionality testing
- **Repository Analysis Tests**: Cross-repository connectivity and dependency mapping validation
- **Performance Tests**: High-volume analysis operations and distributed processing load testing
- **AI/ML Model Tests**: ML-powered analysis accuracy and model performance validation

### **📊 Test Classes & Methods**

| Test Class | Methods | Coverage |
|------------|---------|----------|
| `TestAnalysisAlgorithms` | 15+ methods | Core analysis types (semantic, quality, risk, trend) |
| `TestDistributedProcessing` | 10+ methods | Worker management, load balancing, task queues |
| `TestRemediationEngine` | 8+ methods | Automated fixes, preview mode, backup validation |
| `TestRepositoryAnalysis` | 6+ methods | Cross-repo analysis, connectivity mapping |
| `TestIntegrationEndpoints` | 12+ methods | Service integrations, API compatibility |
| `TestPerformanceBenchmarks` | 5+ methods | Load testing, throughput, latency validation |

### **📊 Testing Strategies**
- **Algorithm Validation**: ML model accuracy testing with known datasets and edge cases
- **Distributed Scaling**: Worker pool scaling, load distribution, and failure recovery testing
- **Integration Mocking**: Comprehensive service mocking with realistic response simulation
- **Performance Benchmarking**: Measurable throughput, latency, and resource utilization testing
- **Error Path Coverage**: Comprehensive error handling and graceful degradation validation
- **Cross-Service Compatibility**: End-to-end workflow testing across service boundaries

### **🔄 Performance Testing**
- **Analysis Throughput**: High-volume document processing performance and scalability validation
- **Distributed Efficiency**: Worker utilization, queue management, and load balancing effectiveness
- **Memory Management**: Large dataset processing and garbage collection efficiency
- **Concurrent Workloads**: Multi-tenant analysis operations and resource contention handling
- **AI Model Performance**: ML inference speed, batch processing optimization, and model accuracy

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
