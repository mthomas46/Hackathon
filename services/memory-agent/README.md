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

### **🔧 Response Format Standards**

All API responses follow a consistent format:

```json
{
  "success": true,
  "data": { ... },
  "request_id": "req-12345678-1234-5678-abcd-123456789012",
  "timestamp": "2025-09-18T10:30:00Z",
  "version": "1.8.0"
}
```

Error responses follow the standard error format:

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": { ... }
  },
  "request_id": "req-12345678-1234-5678-abcd-123456789012",
  "timestamp": "2025-09-18T10:30:00Z"
}
```

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

### **🏗️ Modular Architecture**

The Memory Agent is built with a clean modular architecture:

#### **Core Modules**
- **`memory_ops.py`**: Core memory operations (put, list, cleanup, lazy cleanup)
- **`memory_state.py`**: Global memory state management with thread-safe operations
- **`event_processor.py`**: Redis pub/sub event processing and subscription management
- **`shared_utils.py`**: Common utilities, configuration, and standardized responses

#### **Architecture Benefits**
- **Separation of Concerns**: Each module has a single responsibility
- **Maintainability**: Easy to modify individual components without affecting others
- **Testability**: Modular design enables comprehensive unit testing
- **Performance**: Optimized lazy cleanup and efficient memory management

## ⚙️ **Configuration**

### **🔧 Environment Variables**

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `LOG_COLLECTOR_URL` | Log collector endpoint for structured logging | - | Optional |
| `SERVICE_PORT` | Service port (internal) | `5040` | Optional |
| `MEMORY_MAX_ITEMS` | Maximum items in memory ring buffer | `1000` | Optional |
| `MEMORY_TTL_SECONDS` | Default TTL for memory items (seconds) | `3600` | Optional |
| `REDIS_URL` | Redis connection URL for event processing | `redis://redis:6379` | Optional |

### **🔧 Advanced Configuration**

#### **Memory Management**
```bash
# High-throughput configuration
export MEMORY_MAX_ITEMS=5000
export MEMORY_TTL_SECONDS=7200

# Low-latency configuration
export MEMORY_MAX_ITEMS=500
export MEMORY_TTL_SECONDS=1800
```

#### **Event Processing**
```bash
# Enable Redis event processing
export REDIS_URL=redis://redis:6379

# Disable Redis (memory-only mode)
unset REDIS_URL
```

### **⚡ Capacity Planning Guide**

#### **Memory Sizing Guidelines**

| Use Case | Memory Items | TTL | Recommended Config |
|----------|-------------|-----|-------------------|
| **Development** | 500 | 30 min | `MEMORY_MAX_ITEMS=500` |
| **Small Production** | 1,000 | 1 hour | `MEMORY_MAX_ITEMS=1000` |
| **Medium Production** | 5,000 | 2 hours | `MEMORY_MAX_ITEMS=5000` |
| **Large Production** | 10,000+ | 4+ hours | `MEMORY_MAX_ITEMS=10000` |

#### **Performance Considerations**
- **Memory Usage**: ~1KB per memory item (varies with content size)
- **Cleanup Frequency**: Automatic lazy cleanup every 5 minutes
- **Concurrent Access**: Thread-safe operations with no locks
- **Event Processing**: Non-blocking Redis pub/sub processing

#### **Monitoring Alerts**
- Memory utilization > 80% of max capacity
- TTL cleanup removing > 50% of items in a cycle
- Redis connection failures affecting event processing
- Response times > 100ms for memory operations

## 🧪 **Testing**

### **🔧 Test Coverage**
- **Unit Tests**: [tests/unit/memory_agent](../../tests/unit/memory_agent) - Comprehensive unit test suite
- **Health Endpoint**: Service health monitoring and memory statistics validation
- **Memory Operations**: Complete CRUD testing for memory items (create, read, list)
- **TTL Management**: Time-to-live functionality with automatic expiration
- **Filtering & Pagination**: Advanced filtering by type, key, and pagination limits
- **Capacity Management**: Memory ring buffer limits and overflow handling
- **Event Processing**: Redis pub/sub event subscription and correlation
- **Error Handling**: Comprehensive error scenarios and edge cases
- **Concurrent Operations**: Multi-threaded memory operations testing
- **Integration Scenarios**: Complete workflow memory scenarios

### **📊 Test Classes & Methods**

| Test Class | Methods | Coverage |
|------------|---------|----------|
| `TestMemoryAgentHealth` | 2 methods | Health endpoint and memory statistics |
| `TestMemoryAgentStorage` | 4 methods | Memory item storage and validation |
| `TestMemoryAgentRetrieval` | 5 methods | Memory retrieval, filtering, pagination |
| `TestMemoryAgentIntegration` | 2 methods | Workflow scenarios and event processing |
| `TestMemoryAgentErrorHandling` | 2 methods | Error scenarios and concurrent operations |

### **📊 Testing Strategies**
- **Health Monitoring**: Service status and memory statistics validation
- **Storage Validation**: Memory item creation with various data types and TTL settings
- **Retrieval Testing**: List operations with filtering, pagination, and edge cases
- **TTL Verification**: Time-based expiration testing with cleanup validation
- **Capacity Testing**: Memory limits, overflow handling, and ring buffer behavior
- **Event Correlation**: Redis event processing and memory context generation
- **Concurrency Testing**: Multi-threaded operations and race condition prevention
- **Integration Testing**: End-to-end workflow memory management scenarios

## 📊 **Monitoring & Observability**

### **🔍 Structured Logging**
The Memory Agent integrates with the Log Collector service for comprehensive observability:

#### **Business Events**
- `memory_agent_startup`: Service initialization with configuration details
- `memory_item_storage_started`: Memory item storage operations begin
- `memory_item_stored`: Successful memory item storage completion
- `memory_items_retrieval_started`: Memory retrieval operations begin
- `memory_items_retrieved`: Successful memory retrieval completion

#### **Performance Metrics**
- `memory_storage`: Memory item storage operation timing
- `memory_retrieval`: Memory item retrieval operation timing

#### **Error Tracking**
- Comprehensive error logging with context and correlation IDs
- Request tracing across distributed operations
- Detailed stack traces for debugging and analysis

### **📈 Health Monitoring**
- **Memory Statistics**: Current memory count, capacity utilization
- **TTL Metrics**: Expired item cleanup frequency and effectiveness
- **Event Processing**: Redis connection status and event processing rates
- **Performance Metrics**: Response times and throughput statistics

## 🚀 **Future Enhancements**

### **🔧 Planned Features**
- **Persistence Options**: Redis/SQLite persistence for enhanced durability
- **Semantic Search**: AI-powered semantic search capabilities for intelligent context retrieval
- **Query DSL**: Advanced query language for complex context filtering and analysis
- **Advanced TTL**: Dynamic TTL adjustment based on content importance and usage patterns
- **Memory Analytics**: Usage patterns, access frequency, and content analysis
- **Distributed Caching**: Multi-node memory synchronization and replication
- **Memory Compression**: Intelligent compression for large memory items

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
