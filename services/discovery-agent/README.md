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

## 🎯 **Overview & Purpose**

The **Discovery Agent** is the **automated service discovery engine** that bridges the gap between individual services and ecosystem-wide coordination. It automatically discovers, analyzes, and registers services with the Orchestrator, enabling dynamic AI-powered workflows through intelligent tool generation.

**Core Mission**: Transform static service definitions into dynamic, AI-accessible tools that enable seamless workflow orchestration across the entire ecosystem.

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

### **Discovery Engine Architecture**
The Discovery Agent employs a sophisticated multi-phase discovery process:

1. **Service Detection**: Identifies available services through network scanning and configuration
2. **OpenAPI Harvesting**: Retrieves and parses OpenAPI specifications from discovered services  
3. **Capability Analysis**: Analyzes endpoints to determine service capabilities and categorization
4. **Tool Generation**: Creates LangGraph-compatible tool definitions for AI workflow integration
5. **Registry Update**: Registers discoveries with the Orchestrator for ecosystem-wide availability

### **Integration Patterns**
- **Pull-Based Discovery**: On-demand service discovery through REST API endpoints
- **Push-Based Registration**: Automatic registration of discovered services with the Orchestrator
- **Event Broadcasting**: Publishes discovery events for real-time ecosystem coordination
- **Health Monitoring**: Continuous monitoring of service availability and changes

## 📡 **API Reference**

### **🔧 Core Discovery Endpoints**

| Method | Path | Description | Purpose |
|--------|------|-------------|---------|
| **GET** | `/health` | Service health check | System monitoring and availability verification |
| **POST** | `/discover` | Service discovery | Fetch OpenAPI specs, extract endpoints, register with orchestrator |
| **POST** | `/discover/tools` | 🆕 **LangGraph tool discovery** | Convert OpenAPI specs to LangGraph tools and register with orchestrator |

### **🔍 Service Discovery API**

#### **Standard Service Discovery**
```bash
POST /discover
Content-Type: application/json

{
  "service_name": "analysis-service",
  "service_url": "http://analysis-service:5020",
  "openapi_url": "http://analysis-service:5020/openapi.json"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Service discovery completed",
  "data": {
    "service_name": "analysis-service",
    "endpoints_discovered": 15,
    "registration_status": "completed"
  }
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
