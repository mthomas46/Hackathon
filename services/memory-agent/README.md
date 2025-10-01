# 🧠 Memory Agent - Context Memory Management

<!--
LLM Processing Metadata:
- document_type: "service_documentation"
- service_name: "memory-agent"
- port: 5090
- key_concepts: ["context_management", "ttl_memory", "operational_context", "ai_workflows"]
- architecture: "in_memory_context_store"
- processing_hints: "Lightweight context memory for AI workflows with TTL management and event processing"
- cross_references: ["../../ECOSYSTEM_MASTER_LIVING_DOCUMENT.md", "../orchestrator/README.md", "../../tests/unit/memory_agent/"]
- integration_points: ["orchestrator", "redis", "log_collector", "all_ai_workflows"]
-->

**Navigation**: [Home](../../README.md) · [Architecture](../../docs/architecture/) · [Testing](../../docs/guides/TESTING_GUIDE.md) · [Services](../README_SERVICES.md)  
**Tests**: [tests/unit/memory_agent](../../tests/unit/memory_agent)

**Status**: ✅ Production Ready  
**Port**: `5090` (External) → `5040` (Internal)  
**Version**: `1.8.0`  
**Last Updated**: September 18, 2025

## 🎯 **Overview & Purpose**

The **Memory Agent** is the **context memory management system** that provides short-term, intelligent memory storage for AI workflows and ecosystem operations. It serves as the central operational memory store, enabling context preservation and correlation across complex multi-service workflows.

**Core Mission**: Maintain operational context and summaries to enable intelligent decision-making and correlation across services, timelines, and AI-powered workflows.

## 🚀 **Key Features & Capabilities**

### **🧠 Intelligent Context Management**
- **Lightweight Memory Store**: High-performance in-memory storage for operational context and summaries
- **TTL Management**: Configurable time-to-live for automatic memory cleanup and optimization
- **Capacity Control**: Max-items configuration for memory management and resource optimization
- **Event Correlation**: Context preservation for correlating events across services and timelines

### **📊 Operational Intelligence**
- **LLM Summaries**: Storage and retrieval of AI-generated summaries and insights
- **Document Context**: Document and API summaries for enhanced operational awareness
- **Workflow Memory**: Context preservation for complex multi-step AI workflows
- **Event Breadcrumbs**: Operational breadcrumbs for debugging and analysis

### **⚡ Performance Optimization**
- **In-Memory Performance**: Sub-millisecond access times for context retrieval
- **Simple API Design**: Streamlined endpoints for efficient memory operations
- **Standard Middleware**: Request ID and metrics middleware for observability
- **Debug Support**: Simple list APIs for debugging and operational visibility

## 📡 **API Reference**

### **🔧 Core Memory Operations**

| Method | Path | Description | Purpose |
|--------|------|-------------|---------|
| **GET** | `/health` | Service health and memory count | System monitoring with memory statistics |
| **POST** | `/memory/put` | Store memory item | Context storage with TTL and categorization |
| **GET** | `/memory/list` | List recent memory items | Context retrieval with filtering (type, key, limit) |

### **🧠 Memory Item Storage**
```bash
POST /memory/put
Content-Type: application/json

{
  "key": "workflow-context-123",
  "type": "ai_workflow",
  "content": {
    "step": "document_analysis",
    "status": "completed",
    "summary": "Analysis completed successfully"
  },
  "ttl": 3600
}
```

### **📊 Memory Retrieval**
```bash
GET /memory/list?type=ai_workflow&limit=10
```

## 🔗 **Integration Points**

### **🎯 Ecosystem Integration**
- **Log Collector**: Emits structured logs when `LOG_COLLECTOR_URL` is configured for comprehensive observability
- **AI Workflows**: Provides context memory for all AI-powered operations and multi-step workflows
- **Event Processing**: Subscribes to key ecosystem events for intelligent context management
- **Service Coordination**: Enables correlation of events and findings across services and timelines

### **📊 Event Subscription**
The Memory Agent subscribes to critical ecosystem events:
- **`ingestion.requested`**: Track content ingestion workflows
- **`docs.ingested.*`**: Document processing and storage events
- **`apis.ingested.swagger`**: API discovery and documentation events
- **`findings.created`**: Analysis findings and insights

### **🧠 Memory Architecture**
- **Ring Buffer**: Configurable `_max_items` in-memory ring buffer for efficient memory management
- **Event Summaries**: Automatic summary generation and storage for subscribed events
- **Context Correlation**: Intelligent correlation of related events and operational context

## ⚙️ **Configuration**

### **🔧 Environment Variables**

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `LOG_COLLECTOR_URL` | Log collector endpoint for structured logging | - | Optional |
| `SERVICE_API_PORT` | Service port (internal) | `5040` | Optional |
| `TTL_DEFAULT` | Default TTL for memory items (seconds) | `3600` | Optional |
| `MAX_ITEMS` | Maximum items in memory ring buffer | `1000` | Optional |

## 🧪 **Testing**

### **🔧 Test Coverage**
- **Unit Tests**: [tests/unit/memory_agent](../../tests/unit/memory_agent) - Comprehensive unit test suite
- **TTL Validation**: Comprehensive testing of time-to-live functionality
- **Filter Testing**: Validation of list filtering by type, key, and limits
- **Integration Tests**: Event subscription and processing validation

### **📊 Testing Strategies**
- **Mock Item Validation**: TTL and list filter testing with mock memory items
- **Event Processing**: Validation of event subscription and summary generation
- **Performance Testing**: Memory access time and capacity management testing
- **Integration Testing**: Cross-service communication and event correlation

## 🚀 **Future Enhancements**

### **🔧 Planned Features**
- **Persistence Options**: Redis/SQLite persistence for enhanced durability
- **Semantic Search**: AI-powered semantic search capabilities for intelligent context retrieval
- **Query DSL**: Advanced query language for complex context filtering and analysis
- **Advanced TTL**: Dynamic TTL adjustment based on content importance and usage patterns

## 🔗 **Related Documentation**

### **📖 Primary References**
- **[Ecosystem Master Living Document](../../ECOSYSTEM_MASTER_LIVING_DOCUMENT.md#memory-agent-service-port-5090---context-memory-management)** - Complete technical reference
- **[Log Collector Service](../log-collector/README.md)** - Structured logging integration
- **[Orchestrator Service](../orchestrator/README.md)** - Workflow coordination

### **🎯 Integration Guides**
- **[Architecture Overview](../../docs/architecture/ECOSYSTEM_ARCHITECTURE.md)** - System design patterns
- **[Testing Guide](../../docs/guides/TESTING_GUIDE.md)** - Comprehensive testing strategies
- **[Shared Utilities](../shared/README.md)** - Common infrastructure components

### **⚡ Quick References**
- **[Quick Reference Guide](../../docs/guides/QUICK_REFERENCE_GUIDES.md)** - Common operations and commands
- **[Troubleshooting Index](../../docs/guides/TROUBLESHOOTING_INDEX.md)** - Issue resolution guide

---

**🎯 The Memory Agent provides essential context memory capabilities that enable intelligent correlation and decision-making across AI workflows, serving as the operational memory foundation for the entire ecosystem.**
