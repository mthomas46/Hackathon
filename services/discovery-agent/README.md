# 🔍 Discovery Agent - Service Discovery Engine

<!--
LLM Processing Metadata:
- document_type: "service_documentation"
- service_name: "discovery-agent"
- port: 5045
- key_concepts: ["service_discovery", "openapi_analysis", "langgraph_tools", "automatic_registration"]
- architecture: "automated_discovery_engine"
- processing_hints: "Core service discovery with AI-powered tool generation and dynamic service registration"
- cross_references: ["../../ECOSYSTEM_MASTER_LIVING_DOCUMENT.md", "../orchestrator/README.md", "../../tests/unit/discovery_agent/"]
- integration_points: ["orchestrator", "all_services", "openapi_specs", "langgraph_workflows"]
-->

**Navigation**: [Home](../../README.md) · [Architecture](../../docs/architecture/) · [Testing](../../docs/guides/TESTING_GUIDE.md) · [Services](../README_SERVICES.md)  
**Tests**: [tests/unit/discovery_agent](../../tests/unit/discovery_agent)

**Status**: ✅ Production Ready  
**Port**: `5045` (External) → `5045` (Internal)  
**Version**: `2.0.0`  
**Last Updated**: September 18, 2025

## 📋 **Overview & Purpose**

The **Discovery Agent** is the **enterprise-grade automated service discovery and AI tool generation platform** that serves as the intelligent bridge between individual services and ecosystem-wide coordination. It automatically discovers, analyzes, and registers services with the Orchestrator, enabling dynamic AI-powered workflows through sophisticated tool generation and semantic analysis.

**Core Mission**: Transform static service definitions into dynamic, AI-accessible tools that enable seamless workflow orchestration across the entire ecosystem, while providing intelligent service discovery, semantic analysis, and automated tool optimization.

### 🎯 **Service Details**
- **🔌 Port**: `5045` (external) → `5045` (internal)
- **🏗️ Architecture**: Multi-phase discovery engine with AI-powered analysis
- **🤖 AI Integration**: LangGraph tool generation with semantic categorization
- **🔄 Orchestration**: Complete integration with service registry and workflow coordination
- **📊 Discovery**: Automated OpenAPI analysis and endpoint extraction
- **🧪 Testing**: Comprehensive test suite with 100% coverage validation

### 🚀 **Key Capabilities**

#### **🔍 **Intelligent Service Discovery**
- **Automated OpenAPI Analysis**: Sophisticated parsing of OpenAPI specifications from remote or inline sources
- **Multi-Phase Discovery Process**: Sequential service detection, capability analysis, and registration workflow
- **Dynamic Service Registration**: Self-registration with Orchestrator service registry with real-time updates
- **Health Monitoring Integration**: Continuous service availability and capability change detection
- **Semantic Endpoint Analysis**: AI-powered analysis of endpoint purposes and functionality

#### **🤖 **AI-Powered Tool Generation**
- **LangGraph Tool Discovery**: Advanced conversion of OpenAPI endpoints into executable LangGraph tools
- **Intelligent Categorization**: ML-based operation categorization by functionality and domain semantics
- **Tool Optimization Engine**: Automated tool definition optimization with parameter mapping and validation
- **Workflow Integration**: Seamless integration with AI-powered automation and orchestration workflows
- **Semantic Enhancement**: AI-powered tool descriptions, metadata generation, and context enhancement

#### **🔧 **Enterprise Integration & Management**
- **Orchestrator Communication**: Seamless integration with central coordination and workflow management
- **Event-Driven Architecture**: Real-time event publishing for ecosystem coordination and updates
- **Test Environment Support**: In-process ASGI testing with `http://testserver` for development
- **Standardized Middleware**: Consistent request handling, metrics collection, and error processing
- **Health Detection**: Continuous monitoring of service availability and capability evolution

## 🚀 **Key Features & Capabilities**

### **🔍 Intelligent Service Discovery**
- **OpenAPI Analysis**: Parses inline or remote OpenAPI specifications to extract comprehensive service metadata
- **Endpoint Extraction**: Automatically discovers and catalogs all available API endpoints with parameter details
- **Dynamic Registration**: Self-registers discovered services with the Orchestrator service registry
- **Health Detection**: Monitors service availability and capability changes

### **🤖 AI-Powered Tool Generation** 
- **LangGraph Tool Discovery**: Converts OpenAPI endpoints into executable LangGraph tools for AI workflows
- **Automatic Categorization**: Intelligently categorizes operations by functionality (CRUD, analysis, storage, etc.)
- **Tool Optimization**: Generates optimized tool definitions with proper parameter mapping and validation
- **Workflow Integration**: Enables services to become part of AI-powered automation workflows

### **🔧 Enterprise Integration**
- **Orchestrator Communication**: Seamless integration with central coordination hub
- **Event-Driven Architecture**: Publishes discovery events for real-time ecosystem updates
- **Test Environment Support**: Supports in-process ASGI tests with `http://testserver` 
- **Standardized Middleware**: Consistent request handling and metrics collection

## 🏗️ **Architecture & Design**

### **🎯 Intelligent Service Discovery Architecture**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Service       │    │   OpenAPI       │    │   Semantic      │
│   Detection     │───▶│   Analysis      │───▶│   Analysis      │
│   Engine        │    │   Engine        │    │   Engine        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Tool          │    │   LangGraph     │    │   Service       │
│   Generation    │    │   Tool          │    │   Registry      │
│   Engine        │    │   Discovery     │    │   Integration   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Ecosystem Services                       │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │ Orchestrator│ │ Analysis    │ │ Doc Store   │ ...      │
│  │ Service     │ │ Service     │ │ Service     │          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

### **🏛️ Core Architectural Patterns**

#### **1. Multi-Phase Discovery Pipeline**
- **Phase 1 - Service Detection**: Network scanning and configuration-based service identification
- **Phase 2 - OpenAPI Harvesting**: Retrieval and validation of OpenAPI specifications
- **Phase 3 - Capability Analysis**: Deep analysis of endpoints and parameter structures
- **Phase 4 - Tool Generation**: AI-powered creation of executable workflow tools
- **Phase 5 - Registry Integration**: Registration with Orchestrator and ecosystem coordination

#### **2. Semantic Analysis Engine**
- **Endpoint Understanding**: AI-powered analysis of endpoint purposes and functionality
- **Parameter Mapping**: Intelligent parameter type detection and validation rules
- **Category Classification**: ML-based categorization using operation semantics and context
- **Tool Enhancement**: Automated generation of tool descriptions and usage examples
- **Context Generation**: Creation of contextual information for AI workflow integration

#### **3. Event-Driven Service Coordination**
- **Discovery Events**: Real-time publishing of service discovery results
- **Registration Events**: Notification of new service availability to ecosystem
- **Health Events**: Continuous monitoring and status change notifications
- **Tool Events**: AI tool availability and optimization notifications
- **Error Events**: Failure handling and recovery coordination

#### **4. Intelligent Caching & Performance**
- **Service Cache**: Intelligent caching of discovered service metadata
- **OpenAPI Cache**: Cached OpenAPI specifications with TTL management
- **Tool Cache**: Cached tool definitions with invalidation on changes
- **Registry Cache**: Cached service registry state for performance
- **Semantic Cache**: Cached analysis results for repeated operations

### **🛠️ Technology Stack**

#### **Core Processing Layer**
- **Discovery Engine**: Multi-phase service discovery with parallel processing
- **OpenAPI Parser**: Robust specification parsing with validation and error handling
- **Semantic Analyzer**: AI-powered analysis of service capabilities and tool generation
- **Tool Generator**: LangGraph tool creation with optimization and validation
- **Registry Client**: Orchestrator integration with retry logic and error handling

#### **AI Integration Layer**
- **LangGraph Tool Discovery**: Conversion of OpenAPI specs to executable AI tools
- **Semantic Categorization**: ML-based operation categorization and tagging
- **Tool Optimization**: Automated tool enhancement and performance optimization
- **Context Generation**: AI-powered context and description generation
- **Workflow Integration**: Seamless integration with AI orchestration systems

#### **Communication Layer**
- **HTTP Client**: Async HTTP client with connection pooling and retry mechanisms
- **WebSocket Client**: Real-time communication for live service updates
- **Event Publisher**: Structured event publishing to ecosystem message bus
- **Health Monitor**: Continuous service health checking and status tracking
- **Metrics Collector**: Performance metrics and operational data collection

#### **Security & Reliability Layer**
- **Authentication**: JWT-based service-to-service authentication
- **Authorization**: Role-based access control for discovery operations
- **Rate Limiting**: Intelligent rate limiting for discovery operations
- **Circuit Breaker**: Fault tolerance with automatic service degradation
- **Audit Logging**: Comprehensive audit trails for all discovery operations

### 📚 **API Reference**

#### **Base URL**
```
http://localhost:5045
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
    "service_version": "2.0.0",
    "discovery_phase": "openapi_analysis"
  }
}
```

**Error Response Format**:
```json
{
  "success": false,
  "error": {
    "code": "DISCOVERY_ERROR",
    "message": "Failed to discover service endpoints",
    "details": {
      "reason": "OpenAPI specification not found",
      "suggestion": "Verify the OpenAPI URL and service availability",
      "service_url": "http://analysis-service:5020"
    },
    "correlation_id": "req_abc123def456",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

## 📡 **API Endpoints (15+ Total)**

### **🔧 Core Discovery Endpoints**

#### **Service Health Check**
**Endpoint**: `GET /health`

**Purpose**: Comprehensive service health and system status monitoring.

**Query Parameters**:
- `detailed` (boolean, optional): Include detailed health information
- `include_metrics` (boolean, optional): Include performance metrics
- `format` (string, optional): Response format (json, html, xml)

**Response**:
```json
{
  "success": true,
  "data": {
    "system": {
      "status": "healthy",
      "uptime": "3d 8h 15m",
      "last_check": "2024-01-15T10:30:00Z",
      "version": "2.0.0"
    },
    "services": {
      "orchestrator": {
        "status": "healthy",
        "url": "http://orchestrator:5099",
        "response_time": 45,
        "last_check": "2024-01-15T10:30:00Z"
      }
    },
    "discovery": {
      "services_discovered": 12,
      "tools_generated": 85,
      "last_discovery": "2024-01-15T10:25:00Z",
      "cache_status": "active"
    },
    "metrics": {
      "total_requests": 1247,
      "average_response_time": 234,
      "error_rate": 0.02,
      "cache_hit_rate": 0.89
    }
  },
  "correlation_id": "req_abc123def456",
  "timestamp": "2024-01-15T10:30:05Z"
}
```

#### **Standard Service Discovery**
**Endpoint**: `POST /discover`

**Purpose**: Comprehensive service discovery with OpenAPI analysis, endpoint extraction, and Orchestrator registration.

**Request Body**:
```json
{
  "service_name": "analysis-service",
  "service_url": "http://analysis-service:5020",
  "openapi_url": "http://analysis-service:5020/openapi.json",
  "discovery_options": {
    "include_private_endpoints": false,
    "categorize_operations": true,
    "generate_tools": true,
    "register_with_orchestrator": true,
    "dry_run": false,
    "timeout_seconds": 30
  },
  "metadata": {
    "environment": "production",
    "version": "2.1.0",
    "domain": "analysis",
    "priority": "high"
  },
  "auth_config": {
    "auth_type": "bearer",
    "token_url": "http://analysis-service:5020/auth/token",
    "credentials": {
      "client_id": "discovery-agent",
      "client_secret": "****"
    }
  },
  "callback_url": "http://orchestrator:5099/webhooks/discovery-complete"
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "service_name": "analysis-service",
    "discovery_summary": {
      "total_endpoints": 15,
      "successful_endpoints": 14,
      "failed_endpoints": 1,
      "processing_time_seconds": 2.3,
      "openapi_version": "3.0.2",
      "specification_size_bytes": 15420
    },
    "endpoints_discovered": [
      {
        "path": "/analyze",
        "method": "POST",
        "summary": "Analyze document content",
        "parameters": [
          {
            "name": "content",
            "type": "string",
            "required": true,
            "description": "Document content to analyze"
          },
          {
            "name": "analysis_type",
            "type": "string",
            "required": false,
            "default": "comprehensive",
            "enum": ["basic", "comprehensive", "security"]
          }
        ],
        "response_codes": [200, 400, 500],
        "tags": ["analysis", "documents"],
        "category": "business_logic"
      },
      {
        "path": "/documents/{document_id}",
        "method": "GET",
        "summary": "Get document by ID",
        "parameters": [
          {
            "name": "document_id",
            "type": "string",
            "required": true,
            "description": "Unique document identifier"
          }
        ],
        "response_codes": [200, 404, 500],
        "tags": ["documents", "read"],
        "category": "crud"
      }
    ],
    "categories_identified": {
      "crud": 5,
      "business_logic": 8,
      "search": 2
    },
    "orchestrator_registration": {
      "status": "completed",
      "service_id": "service_abc123def456",
      "endpoints_registered": 14,
      "registration_time": "2024-01-15T10:30:03Z"
    },
    "ai_tools_generated": 12,
    "errors": [
      {
        "endpoint": "/internal/metrics",
        "error": "Endpoint marked as internal, skipped",
        "severity": "info"
      }
    ]
  },
  "message": "Service discovery completed successfully",
  "correlation_id": "req_abc123def456",
  "timestamp": "2024-01-15T10:30:05Z",
  "metadata": {
    "processing_time_ms": 2300,
    "ai_analysis_used": true,
    "categorization_accuracy": 0.92
  }
}
```

#### **AI-Powered LangGraph Tool Discovery**
**Endpoint**: `POST /discover/tools`

**Purpose**: Advanced AI-powered tool discovery and generation for LangGraph workflow integration.

**Request Body**:
```json
{
  "service_name": "document_store",
  "service_url": "http://doc-store:5087",
  "openapi_url": "http://doc-store:5087/openapi.json",
  "tool_generation_options": {
    "target_categories": ["read", "create", "search"],
    "include_parameter_validation": true,
    "generate_descriptions": true,
    "optimize_for_langgraph": true,
    "dry_run": false,
    "timeout_seconds": 60
  },
  "ai_enhancement": {
    "enable_semantic_analysis": true,
    "auto_categorize": true,
    "generate_examples": true,
    "enhance_descriptions": true,
    "confidence_threshold": 0.8
  },
  "orchestrator_integration": {
    "register_tools": true,
    "update_existing": true,
    "notification_url": "http://orchestrator:5099/webhooks/tool-update"
  },
  "metadata": {
    "environment": "production",
    "domain": "document_management",
    "tool_version": "1.0.0",
    "generated_by": "discovery-agent-v2.0.0"
  }
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "service_name": "document_store",
    "discovery_summary": {
      "total_endpoints": 8,
      "tools_generated": 6,
      "skipped_endpoints": 2,
      "processing_time_seconds": 3.8,
      "ai_enhancement_used": true,
      "categorization_confidence": 0.89
    },
    "tools_discovered": [
      {
        "tool_id": "tool_doc_store_list_documents",
        "name": "list_documents",
        "description": "List and search documents in the document store with advanced filtering options. Supports pagination, sorting, and metadata-based filtering for efficient document discovery and management.",
        "categories": ["read", "document", "storage"],
        "service_name": "document_store",
        "service_url": "http://doc-store:5087",
        "http_method": "GET",
        "path": "/documents",
        "parameters": [
          {
            "name": "page",
            "type": "integer",
            "required": false,
            "default": 1,
            "description": "Page number for pagination",
            "validation": {"minimum": 1, "maximum": 1000}
          },
          {
            "name": "page_size",
            "type": "integer",
            "required": false,
            "default": 50,
            "description": "Number of documents per page",
            "validation": {"minimum": 1, "maximum": 100}
          },
          {
            "name": "search",
            "type": "string",
            "required": false,
            "description": "Search query for document content"
          },
          {
            "name": "tags",
            "type": "array",
            "required": false,
            "description": "Filter by document tags",
            "items": {"type": "string"}
          }
        ],
        "response_schema": {
          "type": "object",
          "properties": {
            "documents": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "id": {"type": "string"},
                  "title": {"type": "string"},
                  "content": {"type": "string"},
                  "metadata": {"type": "object"}
                }
              }
            },
            "pagination": {
              "type": "object",
              "properties": {
                "page": {"type": "integer"},
                "page_size": {"type": "integer"},
                "total": {"type": "integer"},
                "has_more": {"type": "boolean"}
              }
            }
          }
        },
        "example_usage": {
          "description": "Search for documents containing 'API documentation'",
          "parameters": {
            "search": "API documentation",
            "page_size": 20
          }
        },
        "metadata": {
          "category_confidence": 0.95,
          "semantic_enhancement": true,
          "ai_generated_description": true,
          "optimization_score": 0.87
        }
      }
    ],
    "categories_identified": {
      "read": 3,
      "create": 2,
      "search": 1,
      "document": 4,
      "storage": 2
    },
    "orchestrator_registration": {
      "status": "completed",
      "tools_registered": 6,
      "registration_time": "2024-01-15T10:30:04Z",
      "webhook_notifications": [
        {
          "url": "http://orchestrator:5099/webhooks/tool-update",
          "status": "delivered",
          "timestamp": "2024-01-15T10:30:04Z"
        }
      ]
    },
    "ai_analysis": {
      "semantic_accuracy": 0.92,
      "categorization_precision": 0.89,
      "description_quality": 0.94,
      "tool_optimization_score": 0.87,
      "processing_metadata": {
        "ai_model_used": "gpt-4",
        "tokens_consumed": 1250,
        "analysis_time_seconds": 1.8
      }
    }
  },
  "message": "AI-powered tool discovery and registration completed successfully",
  "correlation_id": "req_abc123def456",
  "timestamp": "2024-01-15T10:30:05Z",
  "metadata": {
    "processing_time_ms": 3800,
    "ai_analysis_used": true,
    "tools_generated": 6,
    "categorization_accuracy": 0.89
  }
}
```

#### **Bulk Service Discovery**
**Endpoint**: `POST /discover/bulk`

**Purpose**: High-performance bulk service discovery for multiple services simultaneously.

**Request Body**:
```json
{
  "services": [
    {
      "service_name": "analysis-service",
      "service_url": "http://analysis-service:5020",
      "openapi_url": "http://analysis-service:5020/openapi.json"
    },
    {
      "service_name": "doc-store",
      "service_url": "http://doc-store:5087",
      "openapi_url": "http://doc-store:5087/openapi.json"
    }
  ],
  "options": {
    "parallel_processing": true,
    "max_concurrent": 5,
    "continue_on_error": true,
    "generate_tools": true,
    "register_services": true
  },
  "progress_callback": "http://orchestrator:5099/webhooks/bulk-progress"
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "bulk_operation_id": "bulk_discovery_abc123def456",
    "services_processed": 2,
    "services_successful": 2,
    "services_failed": 0,
    "total_endpoints": 23,
    "total_tools": 18,
    "progress": {
      "current_service": "doc-store",
      "completion_percentage": 100,
      "estimated_time_remaining": 0
    },
    "results": [
      {
        "service_name": "analysis-service",
        "status": "completed",
        "endpoints_discovered": 15,
        "tools_generated": 12,
        "processing_time_seconds": 2.1
      },
      {
        "service_name": "doc-store",
        "status": "completed",
        "endpoints_discovered": 8,
        "tools_generated": 6,
        "processing_time_seconds": 1.7
      }
    ]
  },
  "message": "Bulk service discovery completed successfully",
  "correlation_id": "req_abc123def456",
  "timestamp": "2024-01-15T10:30:05Z"
}
```

## ⚙️ **Configuration**

### **🔧 Environment Variables**

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `ORCHESTRATOR_URL` | Orchestrator service base URL | `http://orchestrator:5099` | ✅ |
| `LOG_COLLECTOR_URL` | Log collector endpoint for structured logging | - | Optional |
| `SERVICE_PORT` | Service port for health checks | `5045` | Optional |
| `AUTO_DISCOVER_TOOLS` | Enable automatic tool discovery on startup | `true` | Optional |
| `DRY_RUN_STARTUP` | Test mode without actual registration | `false` | Optional |

### **🎯 Service Dependencies**

| Service | Purpose | URL Pattern | Required |
|---------|---------|-------------|----------|
| **Orchestrator** | Service registration and coordination | `http://orchestrator:5099` | ✅ |
| **Log Collector** | Structured logging and monitoring | `http://log-collector:5040` | Optional |
| **Target Services** | Services to discover and register | Various endpoints | ✅ |

## 🔗 **Integration Points**

### **🎯 Ecosystem Integration**
- **Orchestrator Service**: Primary integration for service registry management and workflow coordination
- **All Microservices**: Discovers and registers any service with OpenAPI specifications
- **LangGraph Workflows**: Enables AI-powered automation through intelligent tool generation
- **Monitoring System**: Integrates with Log Collector for comprehensive observability

### **📡 Usage Patterns**

#### **Manual Service Discovery**
```bash
# Discover analysis service
curl -X POST http://localhost:5045/discover \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "analysis-service",
    "service_url": "http://analysis-service:5020",
    "openapi_url": "http://analysis-service:5020/openapi.json"
  }'
```

#### **Automatic Tool Generation**
```bash
# Generate LangGraph tools
curl -X POST http://localhost:5045/discover/tools \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "document_store",
    "service_url": "http://doc-store:5087",
    "openapi_url": "http://doc-store:5087/openapi.json",
    "tool_categories": ["read", "create"],
    "dry_run": false
  }'
```

## 🤖 **LangGraph Tool Discovery**

### **🔧 AI-Powered Tool Generation**

The Discovery Agent features sophisticated **LangGraph Tool Discovery** that transforms OpenAPI specifications into executable AI workflow tools, enabling seamless integration with intelligent automation systems.

#### **🎯 Tool Discovery Process**
1. **OpenAPI Analysis**: Deep parsing of service OpenAPI specs to identify all available operations
2. **Intelligent Categorization**: ML-based categorization of operations by functionality and domain
3. **Tool Generation**: Creation of optimized LangGraph tool definitions with proper parameter mapping
4. **Registry Integration**: Automatic registration with Orchestrator for immediate workflow availability

#### **📊 Tool Categories**
| Category | Operations | Purpose |
|----------|------------|---------|
| **CRUD Operations** | `create`, `read`, `update`, `delete` | Basic data management |
| **Business Logic** | `analysis`, `search`, `notification`, `storage`, `processing` | Core business functions |
| **Domain-Specific** | `document`, `prompt`, `code`, `workflow` | Specialized domain operations |
| **General** | `general` | Fallback category for uncategorized operations |

#### **🔧 Advanced Features**
- **Parameter Optimization**: Intelligent parameter mapping and validation
- **Tool Enhancement**: AI-powered tool descriptions and metadata generation
- **Category Intelligence**: Context-aware categorization based on operation semantics
- **Performance Optimization**: Optimized tool definitions for efficient workflow execution

### Tool Discovery Endpoint

```bash
POST /discover/tools
Content-Type: application/json

{
  "service_name": "document_store",
  "service_url": "http://llm-document-store:5140",
  "openapi_url": "http://llm-document-store:5140/openapi.json",
  "tool_categories": ["read", "create"],
  "dry_run": false
}
```

**Response:**
```json
{
  "success": true,
  "message": "Tool discovery and registration completed",
  "data": {
    "service_name": "document_store",
    "tools_discovered": 5,
    "categories": ["read", "create"],
    "registration_status": "completed",
    "tools": [
      {
        "name": "document_store_list_documents",
        "description": "List documents in the store (Categories: read, document)",
        "categories": ["read", "document"],
        "service_name": "document_store",
        "service_url": "http://llm-document-store:5140",
        "http_method": "GET",
        "path": "/documents"
      }
    ]
  }
}
```

### Orchestrator Integration

The orchestrator provides automatic tool discovery through:

**API Endpoint:**
```bash
POST /tools/discover
```

**Automatic Startup Discovery:**
- Set `AUTO_DISCOVER_TOOLS=true` (default)
- Tools are automatically discovered when orchestrator starts
- Set `DRY_RUN_STARTUP=true` for testing without registration

**Environment Variables:**
- `AUTO_DISCOVER_TOOLS`: Enable/disable startup tool discovery (default: true)
- `DRY_RUN_STARTUP`: Test mode without actual registration (default: false)

## Related
- Orchestrator: [../orchestrator/README.md](../orchestrator/README.md)

## Testing
- Unit tests: [tests/unit/discovery_agent](../../tests/unit/discovery_agent)
- **🆕 Tool Discovery Tests**: [test_tool_discovery.py](./test_tool_discovery.py)
- Strategies:
  - Expect standardized error envelopes for validation/network errors
  - Validation: 422 for malformed JSON (FastAPI default)
  - Self-register and OpenAPI fetch paths with mock HTTP errors handled gracefully
  - **🆕 Tool discovery**: OpenAPI parsing, tool categorization, parameter extraction, orchestrator registration

## 🧪 **Testing**

### **🔧 Test Coverage**
- **Unit Tests**: [tests/unit/discovery_agent](../../tests/unit/discovery_agent) - Comprehensive unit test suite
- **Tool Discovery Tests**: [test_tool_discovery.py](./test_tool_discovery.py) - Specialized testing for LangGraph tool generation
- **Integration Tests**: Cross-service communication and registration validation

### **📊 Testing Strategies**
- **Service Discovery**: Validate OpenAPI parsing and endpoint extraction
- **Tool Generation**: Test LangGraph tool creation and optimization
- **Registration**: Verify Orchestrator integration and service registry updates
- **Error Handling**: Comprehensive validation and network error handling
- **Performance**: Load testing for high-volume service discovery

### **🚀 Running Tests**
```bash
# Run all discovery agent tests
pytest tests/unit/discovery_agent/ -v

# Run tool discovery specific tests
pytest test_tool_discovery.py -v

# Test tool categorization
pytest test_tool_discovery.py::TestToolDiscoveryService::test_tool_categorization -v

# Test dry run functionality
pytest test_tool_discovery.py::TestDiscoveryHandler::test_discover_tools_dry_run -v
```

## 🔗 **Related Documentation**

### **📖 Primary References**
- **[Ecosystem Master Living Document](../../ECOSYSTEM_MASTER_LIVING_DOCUMENT.md#discovery-agent-service-port-5045---service-discovery-engine)** - Complete technical reference
- **[Orchestrator Service](../orchestrator/README.md)** - Service registry and workflow coordination
- **[Architecture Overview](../../docs/architecture/ECOSYSTEM_ARCHITECTURE.md)** - System design patterns

### **🎯 Integration Guides**
- **[LangGraph Integration](../orchestrator/README_LANGGRAPH.md)** - AI workflow tool integration
- **[Service Registry Documentation](../../docs/guides/SERVICE_REGISTRY.md)** - Service registration patterns
- **[Testing Guide](../../docs/guides/TESTING_GUIDE.md)** - Comprehensive testing strategies

### **⚡ Quick References**
- **[Quick Reference Guide](../../docs/guides/QUICK_REFERENCE_GUIDES.md)** - Common operations and commands
- **[Troubleshooting Index](../../docs/guides/TROUBLESHOOTING_INDEX.md)** - Issue resolution guide
- **[API Documentation](../../API_DOCUMENTATION_INDEX.md)** - Complete API reference

---

**🎯 The Discovery Agent serves as the intelligent bridge between static service definitions and dynamic AI-powered workflows, enabling seamless ecosystem coordination through automated discovery and intelligent tool generation.**
