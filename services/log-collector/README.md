# 📊 Log Collector - Centralized Logging & Observability

<!--
LLM Processing Metadata:
- document_type: "service_documentation"
- service_name: "log-collector"
- port: 5040
- key_concepts: ["logging", "observability", "aggregation", "debugging", "monitoring"]
- architecture: "centralized_logging_hub"
- processing_hints: "Central logging aggregation service for ecosystem observability, debugging, and operational insights"
- cross_references: ["../../ECOSYSTEM_MASTER_LIVING_DOCUMENT.md", "../orchestrator/README.md", "../../tests/unit/log_collector/"]
- integration_points: ["all_services", "orchestrator", "frontend", "monitoring_systems"]
-->

**Navigation**: [Home](../../README.md) · [Architecture](../../docs/architecture/) · [Testing](../../docs/guides/TESTING_GUIDE.md) · [Services](../README_SERVICES.md)  
**Tests**: [tests/unit/log_collector](../../tests/unit/log_collector)

**Status**: ✅ Production Ready  
**Port**: `5040` (External) → `5080` (Internal)  
**Version**: `2.1.0`  
**Last Updated**: September 18, 2025

## 🎯 **Overview & Purpose**

The **Log Collector** is the **centralized logging hub** that provides comprehensive log aggregation, real-time monitoring, and observability capabilities for the entire ecosystem. It serves as the primary logging infrastructure for debugging, operational insights, and system health monitoring.

**Core Mission**: Aggregate, store, and analyze logs from all ecosystem services to provide comprehensive observability, debugging capabilities, and operational intelligence for development and production environments.

## 🚀 **Key Features & Capabilities**

### **📊 Centralized Log Aggregation**
- **Multi-Service Ingestion**: Unified log collection from all ecosystem services
- **Structured Logging**: Support for structured log formats with metadata and categorization
- **Real-time Processing**: Immediate log ingestion and availability for analysis
- **In-Memory Storage**: High-performance ring buffer for rapid access and query processing

### **🔍 Advanced Log Analytics**
- **Smart Filtering**: Comprehensive filtering by service, log level, time ranges, and custom criteria
- **Statistical Analysis**: Real-time statistics and metrics for log patterns and service behavior
- **Batch Processing**: Efficient batch log ingestion for high-volume scenarios
- **Query Interface**: Flexible query capabilities for debugging and operational analysis

### **📈 Monitoring & Observability**
- **Dashboard Integration**: Integration with Frontend service for visual log monitoring
- **Health Monitoring**: Comprehensive health checks and service status reporting
- **Performance Metrics**: Detailed metrics on log volume, processing rates, and system performance
- **Alert Integration**: Integration with notification systems for critical log events

### **🏢 Enterprise Features**
- **Configurable Storage**: Adjustable storage limits and retention policies
- **Development/Production Modes**: Optimized configurations for different deployment environments
- **API Integration**: RESTful APIs for programmatic log access and integration
- **Standardized Middleware**: Consistent request tracking and performance monitoring

## 📡 **API Reference**

### **🔧 Core Log Management Endpoints**

| Method | Path | Description | Purpose |
|--------|------|-------------|---------|
| **GET** | `/health` | Service health check | System monitoring and availability verification |
| **POST** | `/logs` | Ingest single log entry | Individual log event ingestion and processing |
| **POST** | `/logs/batch` | Batch log ingestion | High-volume log processing and bulk operations |
| **GET** | `/logs` | Query and list logs | Log retrieval with filtering and pagination |
| **GET** | `/logs/time-range` | Time-range log queries | Get logs within specific time periods |
| **GET** | `/search` | Full-text log search | Advanced search across all log content |
| **GET** | `/stats` | Log statistics and metrics | Operational insights and performance monitoring |
| **GET** | `/metrics/{service}` | Service-specific metrics | Detailed health analysis for individual services |
| **POST** | `/export` | Export logs to file | Filtered log export in JSON/JSONL formats |

### **🔍 Log Query Parameters**

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `service` | string | Filter by service name | `?service=orchestrator` |
| `level` | string | Filter by log level | `?level=ERROR` |
| `limit` | integer | Limit result count | `?limit=100` |
| `since` | timestamp | Logs since timestamp | `?since=2025-09-18T10:00:00Z` |
| `q` | string | Full-text search query | `?q=error+timeout` |
| `start_time` | timestamp | Time range start | `?start_time=2025-09-18T09:00:00Z` |
| `end_time` | timestamp | Time range end | `?end_time=2025-09-18T11:00:00Z` |
| `time_window_minutes` | integer | Service metrics time window | `?time_window_minutes=60` |

### **📊 Usage Examples**

#### **Single Log Ingestion**
```bash
POST /logs
Content-Type: application/json

{
  "service": "orchestrator",
  "level": "INFO",
  "message": "Workflow completed successfully",
  "timestamp": "2025-09-18T10:30:00Z",
  "metadata": {
    "workflow_id": "wf-12345",
    "duration_ms": 1500
  }
}
```

#### **Batch Log Ingestion**
```bash
POST /logs/batch
Content-Type: application/json

{
  "logs": [
    {
      "service": "analysis-service",
      "level": "DEBUG",
      "message": "Analysis started",
      "timestamp": "2025-09-18T10:29:00Z"
    },
    {
      "service": "analysis-service", 
      "level": "INFO",
      "message": "Analysis completed",
      "timestamp": "2025-09-18T10:30:00Z"
    }
  ]
}
```

#### **Log Querying**
```bash
# Get recent error logs
GET /logs?level=ERROR&limit=50

# Get logs from specific service
GET /logs?service=orchestrator&limit=100

# Full-text search
GET /search?q=connection+timeout&limit=20

# Time-range queries
GET /logs/time-range?start_time=2025-09-18T09:00:00Z&end_time=2025-09-18T11:00:00Z

# Get statistics with time window
GET /stats?hours=24

# Get service-specific metrics
GET /metrics/orchestrator?time_window_minutes=120
```

#### **Log Export**
```bash
POST /export
Content-Type: application/json

{
  "filters": {
    "service": "orchestrator",
    "level": "ERROR"
  },
  "format": "jsonl",
  "filename": "orchestrator-errors.jsonl"
}
```

## 🏗️ **Architecture & Design**

### **🎯 Logging Architecture**
The Log Collector employs a sophisticated, multi-tier architecture with both in-memory and persistent storage capabilities:

#### **Core Components**
- **Dual Storage Engine**: In-memory ring buffer + optional disk persistence
- **Log Processor**: Real-time log parsing, validation, and metadata extraction
- **Advanced Query Engine**: Full-text search, time-range queries, and complex filtering
- **Statistics Calculator**: Real-time metrics, service health scoring, and analytics
- **Export Engine**: Flexible log export in multiple formats (JSON/JSONL)

#### **Storage Architecture**
- **Ring Buffer**: Configurable in-memory circular buffer (default: 5000 entries)
- **Persistent Storage**: Optional disk persistence with configurable retention (default: 7 days)
- **Automatic Cleanup**: Time-based cleanup with configurable retention policies
- **Thread-Safe Operations**: Concurrent access protection with threading locks

#### **Performance Optimization**
- **Lazy Cleanup**: Intelligent cleanup scheduling to minimize performance impact
- **Batch Processing**: Efficient bulk operations for high-volume scenarios
- **Memory Management**: Automatic cleanup and bounded memory usage
- **Search Optimization**: Indexed search capabilities for rapid query execution

## ⚙️ **Configuration**

### **🔧 Environment Variables**

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SERVICE_PORT` | Service port (internal) | `5080` | Optional |
| `MAX_LOGS` | Maximum logs in ring buffer | `5000` | Optional |
| `LOG_LEVEL` | Minimum log level to process | `DEBUG` | Optional |
| `ENABLE_STATS` | Enable statistics calculation | `true` | Optional |
| `PERSIST_LOGS` | Enable disk persistence | `false` | Optional |
| `LOG_STORAGE_PATH` | Path for persistent log storage | `./logs` | Optional |
| `LOG_RETENTION_DAYS` | Days to retain logs on disk | `7` | Optional |

### **🔧 Advanced Configuration Examples**

#### **High-Volume Production Setup**
```bash
export MAX_LOGS=10000
export PERSIST_LOGS=true
export LOG_STORAGE_PATH=/var/log/ecosystem
export LOG_RETENTION_DAYS=30
```

#### **Development Environment**
```bash
export MAX_LOGS=1000
export PERSIST_LOGS=false
export LOG_LEVEL=DEBUG
```

#### **Minimal Resource Setup**
```bash
export MAX_LOGS=500
export ENABLE_STATS=false
export LOG_RETENTION_DAYS=1
```

### **🎯 Service Dependencies**

| Service | Purpose | Integration | Required |
|---------|---------|-------------|----------|
| **All Services** | Log generation and ingestion | Universal logging client | ✅ |
| **Frontend** | Log visualization and monitoring | Dashboard integration | Integration |
| **Notification Service** | Critical log alerting | Error and warning notifications | Optional |

### **📊 Storage Configuration**
- **Ring Buffer**: In-memory circular buffer with configurable size limits
- **Retention Policy**: Automatic cleanup based on buffer size and age
- **Memory Management**: Efficient memory utilization with garbage collection
- **Performance Tuning**: Configurable parameters for different deployment scenarios

## 🔗 **Integration Points**

### **🎯 Ecosystem Integration**
- **Universal Logging**: All ecosystem services emit logs to the Log Collector
- **Frontend Dashboard**: Real-time log visualization and monitoring capabilities
- **Operational Intelligence**: Integration with monitoring and alerting systems
- **Development Support**: Comprehensive debugging capabilities for development teams

### **📊 Operational Workflows**
- **Real-time Monitoring**: Live log streaming for operational awareness
- **Debugging Support**: Comprehensive log analysis for issue resolution
- **Performance Analytics**: Service performance monitoring through log analysis
- **Alert Generation**: Critical event detection and notification integration

## 🧪 **Testing**

### **🔧 Test Coverage**
- **Unit Tests**: [tests/unit/log_collector](../../tests/unit/log_collector) - Comprehensive unit test suite
- **Storage Tests**: In-memory and persistent storage functionality validation
- **Search Tests**: Full-text search and time-range query testing
- **Statistics Tests**: Metrics calculation and service health scoring validation
- **Export Tests**: Log export functionality and format validation
- **Integration Tests**: Multi-service log ingestion and processing validation
- **Performance Tests**: High-volume log ingestion and query performance testing
- **Concurrency Tests**: Thread-safe operations and concurrent access validation

### **📊 Test Classes & Methods**

| Test Class | Methods | Coverage |
|------------|---------|----------|
| `TestLogStorage` | 8+ methods | Storage operations, persistence, cleanup |
| `TestLogSearch` | 6+ methods | Full-text search, filtering, time-range queries |
| `TestLogStatistics` | 5+ methods | Metrics calculation, health scoring, analytics |
| `TestLogExport` | 4+ methods | Export functionality, format validation |
| `TestLogIntegration` | 3+ methods | Multi-service scenarios, batch processing |

### **📊 Testing Strategies**
- **Storage Isolation**: Comprehensive test isolation with in-memory log state management
- **Flexible Assertions**: Adaptive test expectations for accumulated log scenarios
- **Volume Testing**: High-volume ingestion testing for performance validation
- **Query Validation**: Comprehensive filtering, search, and analytics functionality testing
- **Persistence Testing**: Disk storage, retention policies, and recovery validation
- **Concurrency Testing**: Thread-safe operations and race condition prevention

### **🔄 Performance Testing**
- **Batch Processing**: Large batch ingestion performance and memory management
- **Concurrent Access**: Multi-service concurrent log ingestion validation
- **Memory Management**: Ring buffer behavior and automatic cleanup validation
- **Query Performance**: Complex search and analytics performance under load
- **Persistence Performance**: Disk I/O performance and retention policy efficiency

## 🚀 **Future Enhancements**

### **🔧 Planned Features**
- **External Backend Integration**: Loki, ELK Stack, and other enterprise logging solutions
- **Advanced Analytics**: Machine learning-based log analysis and anomaly detection
- **Real-time Streaming**: WebSocket support for live log streaming and real-time dashboards
- **Log Correlation Engine**: Intelligent correlation of related log events across services
- **Alert Management**: Configurable alerting rules and notification channels
- **Log Archiving**: Long-term storage with compression and efficient retrieval
- **Multi-Region Support**: Distributed logging with cross-region replication
- **Custom Dashboards**: User-configurable log visualization and monitoring dashboards

### **🔬 Advanced Analytics Features**
- **Pattern Recognition**: Automatic detection of common error patterns and trends
- **Predictive Analytics**: Forecasting potential issues based on log patterns
- **Root Cause Analysis**: Intelligent analysis of error cascades and dependencies
- **Performance Trending**: Long-term performance analysis and capacity planning insights

## 🔗 **Related Documentation**

### **📖 Primary References**
- **[Ecosystem Master Living Document](../../ECOSYSTEM_MASTER_LIVING_DOCUMENT.md#log-collector-service-port-5040---centralized-logging)** - Complete technical reference
- **[Orchestrator Service](../orchestrator/README.md)** - Primary service coordination and logging
- **[Frontend Service](../frontend/README.md)** - Log visualization and monitoring dashboard

### **🎯 Integration Guides**
- **[Notification Service](../notification-service/README.md)** - Critical log alerting and notifications
- **[Architecture Overview](../../docs/architecture/ECOSYSTEM_ARCHITECTURE.md)** - System design patterns
- **[Testing Guide](../../docs/guides/TESTING_GUIDE.md)** - Comprehensive testing strategies

### **⚡ Quick References**
- **[Quick Reference Guide](../../docs/guides/QUICK_REFERENCE_GUIDES.md)** - Common operations and commands
- **[Troubleshooting Index](../../docs/guides/TROUBLESHOOTING_INDEX.md)** - Issue resolution guide
- **[Shared Utilities](../shared/README.md)** - Common infrastructure components

---

**🎯 The Log Collector provides essential centralized logging capabilities that enable comprehensive observability, debugging, and operational intelligence across the entire ecosystem.**
