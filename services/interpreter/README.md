# Interpreter Service

Navigation: [Home](../../README.md) · [Architecture](../../docs/architecture/) · [Testing](../../docs/guides/TESTING_GUIDE.md) · [Services](../README_SERVICES.md)

**🧠 Enterprise-Grade Natural Language Processing & Workflow Orchestration Platform**

The Interpreter service is the **intelligent gateway** to the LLM Documentation Ecosystem, providing advanced natural language understanding, multi-service orchestration, and AI-powered workflow generation capabilities.

- **🔌 Port**: 5120
- **🏗️ Architecture**: Modular microservice with ecosystem-wide integration
- **🤖 AI Integration**: LangGraph workflows, LLM Gateway, and intelligent prompt engineering
- **🔄 Orchestration**: Multi-service coordination with real-time context awareness
- **📊 Endpoints**: 9 comprehensive API endpoints for natural language processing
- **🧪 Testing**: Complete test suite with 50+ integration tests covering all features

## 🎯 Key Features

### 🧠 **Ecosystem-Aware NLP Processing**
- **Advanced Natural Language Understanding**: Context-aware interpretation with domain-specific knowledge
- **Intent Recognition**: Multi-intent detection with confidence scoring and entity extraction
- **Query Classification**: Automatic categorization and routing to appropriate services
- **Contextual Awareness**: Real-time understanding of available services and capabilities
- **Multi-Modal Processing**: Support for text, structured data, and mixed input formats

### 🔗 **Intelligent Service Orchestration**
- **Dynamic Service Discovery**: Automatic detection and mapping of ecosystem services
- **Workflow Generation**: AI-powered creation of complex multi-step workflows
- **Load Balancing**: Intelligent distribution of requests across available services
- **Error Recovery**: Automatic fallback and retry mechanisms with graceful degradation
- **Context Propagation**: Seamless context passing between services with correlation tracking

### 🎯 **LangGraph Integration & AI Workflows**
- **AI-Powered Workflows**: Automatic discovery and execution of LangGraph workflows
- **Intelligent Routing**: Context-aware selection of appropriate AI models and workflows
- **Dynamic Adaptation**: Real-time workflow modification based on execution results
- **Performance Optimization**: Intelligent caching and execution planning
- **Cost Management**: Budget-aware model selection and execution optimization

### ⚡ **Advanced Prompt Engineering**
- **Natural Language Translation**: Intelligent conversion of natural language to structured prompts
- **Prompt Optimization**: Automatic prompt enhancement for better results
- **Template Management**: Dynamic prompt template selection and customization
- **Version Control**: Prompt versioning and A/B testing capabilities
- **Performance Analytics**: Prompt effectiveness tracking and optimization recommendations

### 🌐 **Multi-Service Coordination**
- **Service Mesh Integration**: Enterprise-grade service-to-service communication
- **Event-Driven Processing**: Real-time event handling and workflow triggering
- **Cross-Service Transactions**: Distributed transaction management with rollback capabilities
- **Resource Management**: Intelligent resource allocation and optimization
- **Monitoring & Observability**: Comprehensive tracking of all service interactions

### 🎭 **Enterprise Reliability Features**
- **Intelligent Fallbacks**: Contextual suggestions and alternative execution paths
- **Circuit Breaker Protection**: Automatic service degradation on repeated failures
- **Rate Limiting**: Service-level protection with configurable thresholds
- **Health Monitoring**: Continuous service health checking and automatic recovery
- **Security Integration**: Enterprise-grade authentication and authorization

## Overview and role in the ecosystem
- **🆕 Enhanced Entry Point**: Advanced natural language interface to the entire LLM Documentation Ecosystem
- **🔄 Full Ecosystem Integration**: Works with ALL services (Prompt Store, Analysis Service, Doc Store, Source Agent, Code Analyzer, Summarizer Hub, Notification Service, Secure Analyzer, Orchestrator)
- **🎯 Intelligent Workflow Mapping**: Automatically maps natural language queries to appropriate workflows
- **🚀 LangGraph Orchestration**: Seamless integration with LangGraph for AI-powered workflow execution
- **💬 Conversational Interface**: Enables natural language interaction with the entire platform

## 🏗️ Architecture

### 🧠 **Intelligent Processing Pipeline**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Natural       │    │  Ecosystem      │    │   Service       │
│   Language      │───▶│  Context        │───▶│   Orchestration │
│   Query         │    │  Analysis       │    │   Engine        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Intent        │    │   LangGraph     │    │   Workflow      │
│   Recognition   │    │   Integration   │    │   Execution     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Ecosystem Services                       │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │ Prompt      │ │ Analysis    │ │ Document    │ ...      │
│  │ Store       │ │ Service     │ │ Store       │          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

### 🎯 **Core Processing Modules**

#### **1. Advanced NLP Engine** (`advanced_nlp_engine.py`)
- **Intent Recognition**: Multi-intent detection with confidence scoring
- **Entity Extraction**: Named entity recognition and context understanding
- **Sentiment Analysis**: Emotional context detection and processing
- **Domain Classification**: Automatic categorization of query domains
- **Query Expansion**: Intelligent query enhancement and disambiguation

#### **2. Ecosystem Context** (`ecosystem_context.py`)
- **Service Discovery**: Dynamic detection of available ecosystem services
- **Capability Mapping**: Real-time capability analysis and routing
- **Context Awareness**: User context, session state, and preference tracking
- **Workflow Discovery**: Automatic identification of relevant workflows
- **Resource Management**: Intelligent resource allocation and optimization

#### **3. LangGraph Integration** (`langgraph_integration.py`)
- **Workflow Discovery**: Automatic discovery of LangGraph workflows
- **AI-Powered Orchestration**: Intelligent workflow selection and execution
- **Dynamic Adaptation**: Real-time workflow modification based on context
- **Performance Optimization**: Intelligent caching and execution planning
- **Error Handling**: Comprehensive error recovery and fallback mechanisms

### 📚 **API Reference**

#### **Base URL**
```
http://localhost:5120
```

#### **Authentication**
All API endpoints support enterprise-grade authentication via headers:
```
Authorization: Bearer <token>
X-User-ID: <user_id>
X-Correlation-ID: <correlation_id>
X-Request-ID: <request_id>
```

#### **Request/Response Format**

**Standard Response Envelope**:
```json
{
  "success": true,
  "data": {},
  "message": "Operation completed successfully",
  "correlation_id": "req_abc123def456",
  "request_id": "req_abc123def456",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0",
  "metadata": {
    "processing_time_ms": 150,
    "service_version": "2.1.0",
    "ai_confidence": 0.92
  }
}
```

**Error Response Format**:
```json
{
  "success": false,
  "error": {
    "code": "NLP_PROCESSING_ERROR",
    "message": "Failed to process natural language query",
    "details": {
      "reason": "Ambiguous intent detected",
      "suggestions": ["Please be more specific about the document type"]
    },
    "correlation_id": "req_abc123def456",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

### 🔌 **Core Endpoints**

#### **Health & System Information**
| Method | Path       | Description |
|--------|------------|-------------|
| GET    | `/health`    | Health check with service status |
| GET    | `/intents`   | List supported intents and capabilities |

#### **Legacy Endpoints** (Deprecated)
| Method | Path         | Description |
|--------|--------------|-------------|
| POST   | `/interpret` | Interpret natural language query |
| POST   | `/execute`   | Interpret and execute workflow |

#### **🧠 Enhanced Natural Language Endpoints**
| Method | Path                        | Description |
|--------|-----------------------------|-------------|
| POST   | `/natural-query`           | Process natural language with full ecosystem context |
| POST   | `/execute-natural-workflow`| Execute natural language as complete workflow |
| GET    | `/ecosystem/capabilities`  | Get comprehensive ecosystem capabilities |
| POST   | `/workflows/discover`      | Discover all available workflows |
| POST   | `/prompt/translate`        | Translate natural language to workflow prompt |

### 🔌 **Detailed API Documentation**

#### **🧠 Natural Language Query Processing**
**Endpoint**: `POST /natural-query`

**Purpose**: Process natural language queries with full ecosystem context awareness and intelligent routing.

**Request Body**:
```json
{
  "query": "analyze this document for quality issues and generate a comprehensive summary report",
  "user_id": "user123",
  "context": {
    "domain": "documentation",
    "priority": "high",
    "output_format": "json",
    "include_metadata": true,
    "max_processing_time": 300
  },
  "preferences": {
    "language": "en",
    "detail_level": "comprehensive",
    "include_suggestions": true
  },
  "constraints": {
    "budget_limit": 1.50,
    "max_services": 5,
    "allowed_services": ["analysis_service", "summarizer_hub"]
  }
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "original_query": "analyze this document for quality issues and generate a comprehensive summary report",
    "interpretation": {
      "intent": "analyze_document",
      "confidence": 0.92,
      "entities": {
        "document_type": ["general"],
        "analysis_type": ["quality", "summary"],
        "output_format": ["report"]
      },
      "sentiment": "neutral",
      "complexity": "medium"
    },
    "ecosystem_context": {
      "detected_services": [
        {
          "service": "analysis_service",
          "capability": "analyze_quality",
          "confidence": 0.9,
          "estimated_cost": 0.80
        },
        {
          "service": "summarizer_hub",
          "capability": "generate_summary",
          "confidence": 0.85,
          "estimated_cost": 0.45
        }
      ],
      "available_workflows": [
        {
          "workflow_id": "workflow_abc123def456",
          "name": "Document Quality Analysis",
          "match_score": 0.92,
          "estimated_duration": 180,
          "estimated_cost": 1.25
        }
      ],
      "resource_requirements": {
        "memory_mb": 512,
        "processing_time_seconds": 180,
        "network_bandwidth_kbps": 1000
      }
    },
    "langgraph_workflows": {
      "best_match": {
        "workflow_name": "document-analysis-workflow",
        "match_score": 0.89,
        "parameters": {
          "document_url": "{{document_url}}",
          "analysis_type": "comprehensive",
          "include_summary": true
        }
      },
      "alternatives": [...]
    },
    "suggestions": [
      "Consider specifying the document type for more accurate analysis",
      "Security analysis can be included for comprehensive coverage",
      "Multiple output formats are available (JSON, Markdown, HTML)"
    ]
  },
  "message": "Natural language query processed successfully",
  "correlation_id": "req_abc123def456",
  "timestamp": "2024-01-15T10:30:05Z",
  "metadata": {
    "processing_time_ms": 245,
    "ai_confidence": 0.92,
    "tokens_used": 45,
    "model_used": "gpt-4"
  }
}
```

**Parameters**:
- **query** (string, required): The natural language query to process
- **user_id** (string, optional): User identifier for personalization
- **context** (object, optional): Processing context and constraints
  - **domain** (string): Domain context (documentation, code, analysis)
  - **priority** (string): Processing priority (low, normal, high, urgent)
  - **output_format** (string): Desired output format (json, markdown, html)
  - **include_metadata** (boolean): Include processing metadata in response
- **preferences** (object, optional): User preferences
  - **language** (string): Response language
  - **detail_level** (string): Detail level (brief, normal, comprehensive)
  - **include_suggestions** (boolean): Include improvement suggestions
- **constraints** (object, optional): Processing constraints
  - **budget_limit** (number): Maximum cost limit
  - **max_services** (integer): Maximum number of services to use
  - **allowed_services** (array): List of allowed services

#### **🚀 Execute Natural Workflow**
**Endpoint**: `POST /execute-natural-workflow`

**Purpose**: Execute natural language queries as complete workflows with full orchestration.

**Request Body**:
```json
{
  "query": "analyze this document and generate a quality report",
  "user_id": "user123",
  "execution_options": {
    "priority": "high",
    "timeout_minutes": 30,
    "continue_on_error": false,
    "callback_url": "https://example.com/webhook/completion",
    "metadata": {
      "source": "api",
      "project": "document_analysis"
    }
  },
  "workflow_preferences": {
    "auto_discover": true,
    "optimize_for_cost": true,
    "prefer_ai_workflows": true,
    "max_parallel_actions": 3
  }
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "execution_id": "exec_abc123def456",
    "workflow_id": "workflow_auto_generated_789",
    "status": "running",
    "original_query": "analyze this document and generate a quality report",
    "generated_workflow": {
      "name": "Auto-Generated Document Analysis",
      "description": "AI-generated workflow for document quality analysis",
      "actions": [...],
      "parameters": {...}
    },
    "progress": {
      "current_step": 1,
      "total_steps": 3,
      "current_action": "analyze_document",
      "completion_percentage": 33
    },
    "estimated_completion": "2024-01-15T10:32:00Z",
    "cost_estimate": 1.25
  },
  "message": "Natural language workflow execution started",
  "correlation_id": "req_abc123def456",
  "timestamp": "2024-01-15T10:30:05Z"
}
```

#### **🌐 Ecosystem Capabilities**
**Endpoint**: `GET /ecosystem/capabilities`

**Purpose**: Get comprehensive overview of available ecosystem services and capabilities.

**Query Parameters**:
- `include_details` (boolean, optional): Include detailed capability information
- `filter_by_domain` (string, optional): Filter by domain (documentation, code, analysis)
- `service_status` (string, optional): Filter by service status (healthy, degraded, offline)

**Response**:
```json
{
  "success": true,
  "data": {
    "ecosystem_overview": {
      "total_services": 12,
      "healthy_services": 11,
      "total_capabilities": 45,
      "available_workflows": 25
    },
    "services": [
      {
        "service_name": "analysis_service",
        "status": "healthy",
        "version": "2.1.0",
        "capabilities": [
          {
            "capability": "analyze_quality",
            "description": "Analyze document quality and consistency",
            "parameters": [...],
            "estimated_cost": 0.80,
            "average_response_time": 45.2
          },
          {
            "capability": "analyze_consistency",
            "description": "Check document consistency across sources",
            "parameters": [...],
            "estimated_cost": 0.60,
            "average_response_time": 30.1
          }
        ],
        "endpoints": ["/analyze", "/consistency-check", "/quality-report"]
      }
    ],
    "workflows": [...],
    "ai_models": [...],
    "integration_points": [...]
  },
  "correlation_id": "req_abc123def456",
  "timestamp": "2024-01-15T10:30:05Z"
}
```

## ⚙️ Configuration

### Environment Variables
| Name | Description | Default | Example |
|------|-------------|---------|---------|
| INTERPRETER_PORT | Service port | 5120 | 5120 |
| INTERPRETER_HOST | Service host | 0.0.0.0 | 0.0.0.0 |
| INTERPRETER_WORKERS | Number of worker processes | 4 | 8 |
| INTERPRETER_TIMEOUT | Request timeout in seconds | 300 | 600 |
| INTERPRETER_MAX_REQUEST_SIZE | Maximum request size in MB | 10 | 50 |
| INTERPRETER_LOG_LEVEL | Logging level | INFO | DEBUG |
| INTERPRETER_ENABLE_CORS | Enable CORS headers | false | true |
| INTERPRETER_CORS_ORIGINS | Allowed CORS origins | [] | ["https://example.com"] |
| INTERPRETER_ENABLE_TLS | Enable TLS/SSL | false | true |
| INTERPRETER_TLS_CERT_PATH | TLS certificate path | "" | "/certs/server.crt" |
| INTERPRETER_TLS_KEY_PATH | TLS private key path | "" | "/certs/server.key" |
| INTERPRETER_JWT_SECRET | JWT signing secret | "" | "your-secret-key" |
| INTERPRETER_API_KEY | API key for service access | "" | "your-api-key" |
| INTERPRETER_ENABLE_RATE_LIMITING | Enable rate limiting | true | true |
| INTERPRETER_RATE_LIMIT_REQUESTS | Requests per minute | 100 | 1000 |
| INTERPRETER_RATE_LIMIT_BURST | Burst limit | 20 | 50 |
| INTERPRETER_CACHE_ENABLED | Enable response caching | true | true |
| INTERPRETER_CACHE_TTL | Cache TTL in seconds | 300 | 1800 |
| INTERPRETER_CACHE_MAX_SIZE | Maximum cache size | 1000 | 5000 |

### Configuration File
```yaml
# config/interpreter.yaml
server:
  host: 0.0.0.0
  port: 5120
  workers: 4
  timeout: 300
  max_request_size: 10

security:
  enable_tls: false
  tls_cert_path: ""
  tls_key_path: ""
  jwt_secret: ""
  api_key: ""
  enable_cors: false
  cors_origins: []

rate_limiting:
  enabled: true
  requests_per_minute: 100
  burst_limit: 20

caching:
  enabled: true
  ttl_seconds: 300
  max_size: 1000

logging:
  level: INFO
  format: json
  enable_correlation: true

ai_processing:
  max_tokens: 4000
  temperature: 0.7
  model_preferences:
    - "gpt-4"
    - "claude-3"
    - "gemini-pro"

ecosystem_integration:
  service_discovery:
    enabled: true
    refresh_interval: 30
  health_checking:
    enabled: true
    interval: 60
  circuit_breaker:
    enabled: true
    failure_threshold: 5
    recovery_timeout: 60
```

## Quickstart
```bash
python services/interpreter/main.py
```

## Examples

### Legacy API Usage
```bash
# Basic interpretation
curl -X POST http://localhost:5120/interpret -H 'Content-Type: application/json' \
  -d '{"query":"analyze this document"}'

# Execute workflow
curl -X POST http://localhost:5120/execute -H 'Content-Type: application/json' \
  -d '{"query":"analyze this document"}'
```

### 🆕 Enhanced Natural Language API Usage

#### 1. Process Natural Language Query
```bash
curl -X POST http://localhost:5120/natural-query -H 'Content-Type: application/json' \
  -d '{
    "query": "analyze this document for quality issues and generate a summary",
    "user_id": "user123",
    "context": {"domain": "documentation", "priority": "high"}
  }'
```

**Response:**
```json
{
  "success": true,
  "data": {
    "original_query": "analyze this document for quality issues and generate a summary",
    "interpretation": {
      "intent": "analyze_document",
      "confidence": 0.9,
      "entities": {"document_type": ["general"]}
    },
    "ecosystem_context": {
      "detected_services": ["document_store", "analysis_service", "summarizer_hub"],
      "detected_capabilities": ["analyze_quality", "generate_summary"],
      "available_workflows": [...]
    },
    "langgraph_workflows": {
      "best_match": {
        "workflow_name": "document-analysis",
        "match_score": 0.9
      }
    }
  }
}
```

#### 2. Execute Natural Workflow
```bash
curl -X POST http://localhost:5120/execute-natural-workflow -H 'Content-Type: application/json' \
  -d '{
    "query": "analyze this document and generate a quality report",
    "user_id": "user123"
  }'
```

#### 3. Get Ecosystem Capabilities
```bash
curl http://localhost:5120/ecosystem/capabilities
```

#### 4. Discover Available Workflows
```bash
curl -X POST http://localhost:5120/workflows/discover
```

#### 5. Translate to Workflow Prompt
```bash
curl -X POST http://localhost:5120/prompt/translate -H 'Content-Type: application/json' \
  -d '{
    "query": "analyze code repository and generate documentation",
    "user_id": "developer123"
  }'
```

### Advanced Usage Examples

#### Document Analysis Workflow
```bash
curl -X POST http://localhost:5120/execute-natural-workflow -H 'Content-Type: application/json' \
  -d '{
    "query": "analyze the quality of this documentation, check for consistency, and generate a summary report",
    "context": {
      "document_type": "api_docs",
      "output_format": "json",
      "include_metrics": true
    }
  }'
```

#### Code Repository Processing
```bash
curl -X POST http://localhost:5120/execute-natural-workflow -H 'Content-Type: application/json' \
  -d '{
    "query": "analyze this GitHub repository, generate code documentation, and check for security vulnerabilities",
    "context": {
      "repo_url": "https://github.com/example/repo",
      "analysis_types": ["security", "quality", "documentation"]
    }
  }'
```

#### Multi-Service Orchestration
```bash
curl -X POST http://localhost:5120/execute-natural-workflow -H 'Content-Type: application/json' \
  -d '{
    "query": "ingest data from Jira, analyze it for patterns, generate a report, and send notifications to stakeholders",
    "context": {
      "source": "jira",
      "analysis_depth": "comprehensive",
      "notify_channels": ["email", "slack"]
    }
  }'
```

## Related
- Analysis Service: [../analysis-service/README.md](../analysis-service/README.md)
- Prompt Store: [../prompt-store/README.md](../prompt-store/README.md)
- Services index: [../README_SERVICES.md](../README_SERVICES.md)

## Testing

### Test Suites
- **Legacy Unit Tests**: [tests/unit/interpreter](../../tests/unit/interpreter)
- **🆕 Enhanced Integration Tests**: [test_enhanced_integration.py](./test_enhanced_integration.py)

### Test Coverage Areas
- **Ecosystem Context Awareness**: Service capability detection, workflow mapping, alias resolution
- **Orchestrator Integration**: Workflow execution, LangGraph orchestration, error handling
- **Prompt Engineering**: Query translation, optimization, fallback mechanisms
- **LangGraph Discovery**: Workflow discovery, parameter validation, execution
- **Enhanced API Endpoints**: Natural language processing, multi-service orchestration
- **Integration Scenarios**: End-to-end workflows, error handling, performance validation

### Running Tests
```bash
# Run legacy unit tests
pytest tests/unit/interpreter/ -v

# Run enhanced integration tests
pytest test_enhanced_integration.py -v

# Run specific test categories
pytest test_enhanced_integration.py::TestEcosystemContextIntegration -v
pytest test_enhanced_integration.py::TestOrchestratorIntegration -v
pytest test_enhanced_integration.py::TestLangGraphDiscovery -v
pytest test_enhanced_integration.py::TestEnhancedInterpreterAPI -v
```

### Test Architecture
- **Mock Testing**: External service dependencies fully mocked for isolation
- **Integration Testing**: End-to-end workflow execution with real service coordination
- **Performance Testing**: Response times, resource usage, and concurrent operation validation
- **Error Scenario Testing**: Comprehensive failure mode coverage and recovery mechanisms
- **Concurrent Testing**: Multi-user and multi-workflow scenario validation

### Test Strategies
- **Legacy Endpoints**: Ensure tests import real service app by adding project root to `sys.path`
- **Enhanced Endpoints**: Full ecosystem context testing with mocked external services
- **LangGraph Integration**: Workflow discovery and execution testing with mock orchestrator
- **Error Handling**: 404-tolerant fallbacks and graceful degradation testing
- **Performance**: Response time validation and resource usage monitoring
