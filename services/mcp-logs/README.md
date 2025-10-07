---
llm_metadata:
  document_type: reference
  content_focus: operational
  platform:
    primary: mcp
  status: active
  created_date: '2025-10-07'
  last_modified: '2025-10-07'
  topics:
  - logging
  - observability
  - centralized_logging
  - log_aggregation
  - monitoring
  concepts: []
  technologies:
  - python
  - elasticsearch
  - kibana
  - fluentd
  - redis
  semantic_summary: Reference documentation for the MCP Logs service providing centralized logging, aggregation, and analysis for the Model Context Protocol ecosystem
  archive_reason: n/a
  historical_value: current
  reference_value: high
semantic_embedding:
  model: text-embedding-ada-002
  embedding_date: '2025-10-07'
  embedding_checksum: pending
rag_metadata:
  chunk_strategy: semantic
  optimal_chunk_size: 512
  retrieval_priority: high
---

# 📝 MCP Logs Service

**Port: 8016** | **Purpose: Centralized Logging & Observability Platform**

The MCP Logs Service provides comprehensive logging infrastructure for the Model Context Protocol ecosystem, enabling centralized log aggregation, analysis, and monitoring across all MCP-enabled services and applications.

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   MCP Services  │    │   MCP Logs      │    │  Log Storage    │
│                 │◄──►│   Service       │◄──►│   (Elastic)     │
│ • Applications  │    │   (Port 8016)   │    │                 │
│ • Gateways      │    │                 │    │ • Indexed       │
│ • Controllers   │    │ • Aggregation   │    │ • Searchable    │
│ • Extensions    │    │ • Processing    │    │ • Time-series   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         ▲                       ▲                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Log Collectors  │    │  Processing     │    │   Analytics     │
│   (Fluentd)     │    │   Pipeline      │    │   Engine        │
│                 │    │                 │    │                 │
│ • File Logs     │    │ • Parsing       │    │ • Correlations  │
│ • Syslog        │    │ • Enrichment    │    │ • Anomaly Det   │
│ • Journald      │    │ • Filtering     │    │ • Insights      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Core Features

### 📊 Log Aggregation
- **Multi-Source Collection**: Aggregate logs from files, syslog, journald, and APIs
- **Structured Logging**: Support for JSON, key-value, and custom log formats
- **Real-Time Streaming**: Live log ingestion and processing
- **Scalable Architecture**: Handle high-volume log streams efficiently

### 🔍 Log Processing & Analysis
- **Intelligent Parsing**: Automatic log format detection and parsing
- **Context Enrichment**: Add metadata, tags, and correlation IDs
- **Filtering & Routing**: Conditional log processing and routing rules
- **Data Transformation**: Log normalization and field extraction

### 📈 Search & Analytics
- **Full-Text Search**: Fast, indexed search across all log data
- **Advanced Queries**: Complex boolean queries with field filtering
- **Time-Based Analysis**: Historical log analysis and trend identification
- **Correlation Engine**: Link related log entries across services

### 🚨 Alerting & Monitoring
- **Log-Based Alerts**: Pattern matching and threshold-based alerting
- **Anomaly Detection**: Statistical analysis for unusual log patterns
- **Performance Monitoring**: Log volume and processing latency tracking
- **Health Dashboards**: Real-time log processing status visualization

## 📋 Log Categories

### Application Logs
- **Request/Response Logs**: API call logging with full context
- **Error Logs**: Exception tracking and error pattern analysis
- **Performance Logs**: Timing and resource usage metrics
- **Security Logs**: Authentication and authorization events

### System Logs
- **Service Lifecycle**: Startup, shutdown, and health check logs
- **Resource Monitoring**: CPU, memory, and I/O utilization logs
- **Network Activity**: Connection and data transfer logging
- **Configuration Changes**: Settings modification tracking

### MCP-Specific Logs
- **Context Operations**: Context creation, updates, and retrieval logs
- **Model Interactions**: LLM request/response logging (sanitized)
- **Protocol Events**: MCP protocol message and state change logging
- **Extension Activity**: Plugin and extension execution logs

### Infrastructure Logs
- **Container Logs**: Docker and Kubernetes orchestration logs
- **Network Logs**: Load balancer and proxy access logs
- **Database Logs**: Query performance and connection logs
- **Message Bus Logs**: Event streaming and queue processing logs

## 🛠️ API Endpoints

### Log Ingestion
```bash
# Ingest single log entry
POST /api/v1/logs
{
  "timestamp": "2025-10-07T15:30:00Z",
  "level": "INFO",
  "service": "mcp-gateway",
  "message": "Request processed successfully",
  "metadata": {
    "request_id": "req-12345",
    "user_id": "user-67890",
    "endpoint": "/api/v1/context"
  },
  "tags": ["api", "success"]
}

# Bulk log ingestion
POST /api/v1/logs/bulk

# Stream log ingestion
POST /api/v1/logs/stream
```

### Log Querying
```bash
# Search logs
GET /api/v1/logs/search?q=error&service=mcp-gateway&from=2025-10-07T00:00:00Z&size=100

# Get logs by correlation ID
GET /api/v1/logs/correlation/{correlation_id}

# Get service logs
GET /api/v1/logs/service/{service_name}?level=ERROR&since=1h

# Get logs with filtering
GET /api/v1/logs/filter?field=level&value=ERROR&time_range=24h
```

### Analytics & Monitoring
```bash
# Get log statistics
GET /api/v1/analytics/stats?time_range=24h

# Get error trends
GET /api/v1/analytics/errors/trends?service=mcp-gateway&days=7

# Get performance metrics
GET /api/v1/analytics/performance?metric=response_time&percentile=95

# Get anomaly detection results
GET /api/v1/analytics/anomalies?time_range=1h
```

## 🔧 Log Processing Pipeline

### 1. Collection Phase
- **Input Sources**: Files, syslog, HTTP APIs, message queues
- **Format Detection**: Automatic format identification
- **Initial Parsing**: Basic structure extraction
- **Timestamp Normalization**: Consistent timestamp formatting

### 2. Processing Phase
- **Field Extraction**: Structured field parsing and validation
- **Context Enrichment**: Add service metadata and correlation IDs
- **Filtering Rules**: Apply inclusion/exclusion filters
- **Data Transformation**: Normalize and standardize log formats

### 3. Storage Phase
- **Indexing**: Full-text and field-based indexing
- **Retention Policies**: Configurable data retention rules
- **Compression**: Automatic log compression for storage efficiency
- **Archival**: Long-term storage with different retention tiers

### 4. Analysis Phase
- **Real-Time Analysis**: Streaming analytics and alerting
- **Batch Processing**: Historical analysis and reporting
- **Correlation Engine**: Cross-service log correlation
- **Machine Learning**: Pattern recognition and anomaly detection

## ⚙️ Configuration

### Environment Variables
```bash
# Service Configuration
MCP_LOGS_PORT=8016
MCP_LOGS_HOST=0.0.0.0

# Storage Configuration
ELASTICSEARCH_HOSTS=http://localhost:9200
ELASTICSEARCH_INDEX_PREFIX=mcp-logs-
LOG_RETENTION_DAYS=30

# Processing Configuration
MAX_BATCH_SIZE=1000
PROCESSING_THREADS=4
ENABLE_REAL_TIME_ANALYTICS=true

# Security Configuration
API_KEY=your-secret-key
ENABLE_HTTPS=true
CERT_PATH=/path/to/cert.pem
```

### Log Collection Configuration
```yaml
# fluentd.conf
<source>
  @type tail
  path /var/log/mcp/*.log
  pos_file /var/log/td-agent/mcp.pos
  tag mcp.service.*
  <parse>
    @type json
  </parse>
</source>

<match mcp.service.**>
  @type http
  endpoint http://localhost:8016/api/v1/logs
  <format>
    @type json
  </format>
</match>
```

### Docker Deployment
```yaml
version: '3.8'
services:
  mcp-logs:
    image: mcp-logs:latest
    ports:
      - "8016:8016"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
      - LOG_RETENTION_DAYS=30
    volumes:
      - ./config:/app/config
      - ./logs:/app/logs
    depends_on:
      - elasticsearch
      - kibana

  elasticsearch:
    image: elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    ports:
      - "9200:9200"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data

  kibana:
    image: kibana:8.11.0
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch

  fluentd:
    image: fluent/fluentd:latest
    volumes:
      - ./fluentd.conf:/fluentd/etc/fluent.conf
      - /var/log/mcp:/var/log/mcp
    depends_on:
      - mcp-logs
```

## 📊 Monitoring & Metrics

### Service Health
```bash
# Service health check
GET /health

# Detailed health status
GET /health/detailed

# Metrics endpoint
GET /metrics
```

### Key Metrics
- **Ingestion Rate**: Logs per second ingestion rate
- **Processing Latency**: Time to process and index logs
- **Storage Usage**: Index size and retention metrics
- **Query Performance**: Search response times and throughput
- **Error Rate**: Failed log processing percentage

## 🔍 Search & Query Capabilities

### Query Syntax
```bash
# Simple text search
GET /api/v1/logs/search?q=error

# Field-based search
GET /api/v1/logs/search?q=service:mcp-gateway AND level:ERROR

# Time-based queries
GET /api/v1/logs/search?q=error&from=2025-10-07T00:00:00Z&to=2025-10-07T23:59:59Z

# Complex queries
GET /api/v1/logs/search?q=(service:mcp-gateway OR service:llm-gateway) AND level:ERROR AND message:*timeout*
```

### Advanced Features
- **Fuzzy Search**: Approximate string matching
- **Regular Expressions**: Pattern-based log matching
- **Aggregation Queries**: Statistical analysis and grouping
- **Geospatial Queries**: Location-based log filtering (if applicable)

## 🚨 Alerting System

### Alert Rules
```json
{
  "name": "High Error Rate Alert",
  "query": "level:ERROR",
  "condition": "count > 10",
  "time_window": "5m",
  "severity": "high",
  "channels": ["email", "slack"],
  "throttle": "10m"
}
```

### Alert Types
- **Threshold Alerts**: Count or rate-based thresholds
- **Pattern Alerts**: Specific log pattern matching
- **Anomaly Alerts**: Statistical deviation detection
- **Correlation Alerts**: Multi-service incident detection

### Notification Channels
- **Email**: SMTP-based notifications
- **Slack**: Real-time messaging integration
- **Webhook**: Custom HTTP webhook notifications
- **PagerDuty**: Incident management integration

## 🔧 Troubleshooting

### Common Issues

#### Logs Not Appearing
```bash
# Check service health
curl http://localhost:8016/health

# Verify Elasticsearch connection
curl http://localhost:9200/_cluster/health

# Check log ingestion
curl http://localhost:8016/api/v1/logs/search?q=*&size=1

# Review service logs
docker logs mcp-logs
```

#### Search Performance Issues
```bash
# Check index health
curl http://localhost:9200/_cat/indices/mcp-logs-*

# Monitor query performance
curl http://localhost:8016/metrics | grep query

# Optimize index settings
curl -X PUT http://localhost:9200/mcp-logs-*/_settings \
  -H 'Content-Type: application/json' \
  -d '{"index": {"refresh_interval": "30s"}}'
```

#### High Resource Usage
```bash
# Monitor system resources
docker stats

# Check log volume
curl http://localhost:8016/api/v1/analytics/stats

# Adjust retention policies
curl -X PUT http://localhost:8016/api/v1/config/retention \
  -H 'Content-Type: application/json' \
  -d '{"days": 7}'

# Scale the service
docker-compose up --scale mcp-logs=2
```

## 🔗 Integration Examples

### Application Logging
```python
import logging
import requests
import json
from datetime import datetime

class MCPLogHandler(logging.Handler):
    def __init__(self, service_name, logs_url="http://localhost:8016"):
        super().__init__()
        self.service_name = service_name
        self.logs_url = logs_url

    def emit(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "service": self.service_name,
            "message": self.format(record),
            "metadata": {
                "logger": record.name,
                "filename": record.filename,
                "lineno": record.lineno
            }
        }

        try:
            requests.post(f"{self.logs_url}/api/v1/logs", json=log_entry)
        except Exception:
            # Fallback to local logging if service unavailable
            pass

# Usage
logger = logging.getLogger(__name__)
handler = MCPLogHandler("my-mcp-service")
logger.addHandler(handler)
logger.info("Service started successfully")
```

### Log Analysis Integration
```python
import requests
from datetime import datetime, timedelta

class LogAnalyzer:
    def __init__(self, logs_url="http://localhost:8016"):
        self.logs_url = logs_url

    def get_error_summary(self, service, hours=24):
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)

        query = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"service": service}},
                        {"term": {"level": "ERROR"}},
                        {"range": {"timestamp": {"gte": start_time.isoformat(), "lte": end_time.isoformat()}}}
                    ]
                }
            },
            "size": 1000
        }

        response = requests.post(f"{self.logs_url}/api/v1/logs/search", json=query)
        return response.json()

    def detect_anomalies(self, service, metric="error_rate"):
        # Get recent metrics
        response = requests.get(f"{self.logs_url}/api/v1/analytics/anomalies?service={service}&metric={metric}")
        return response.json()

# Usage
analyzer = LogAnalyzer()
errors = analyzer.get_error_summary("mcp-gateway", hours=24)
anomalies = analyzer.detect_anomalies("mcp-gateway")
```

## 📚 Dependencies

- **Python 3.9+**
- **Elasticsearch**: Log storage and search
- **Kibana**: Log visualization (optional)
- **Fluentd**: Log collection and forwarding
- **Redis**: Caching and buffering (optional)
- **Kafka**: High-volume log streaming (optional)

## 🚀 Getting Started

1. **Start Elasticsearch**
   ```bash
   docker run -d -p 9200:9200 -p 9300:9300 elasticsearch:8.11.0
   ```

2. **Configure the service**
   ```bash
   export MCP_LOGS_PORT=8016
   export ELASTICSEARCH_HOSTS=http://localhost:9200
   ```

3. **Run the service**
   ```bash
   cd services/mcp-logs
   python -m uvicorn main:app --host 0.0.0.0 --port 8016
   ```

4. **Test log ingestion**
   ```bash
   curl -X POST http://localhost:8016/api/v1/logs \
     -H "Content-Type: application/json" \
     -d '{"timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'", "level": "INFO", "service": "test", "message": "Test log entry"}'
   ```

5. **Verify log search**
   ```bash
   curl "http://localhost:8016/api/v1/logs/search?q=test"
   ```

## 🎯 Use Cases

### Operational Monitoring
- **Incident Response**: Rapid log analysis during outages
- **Performance Debugging**: Identify bottlenecks and issues
- **Security Monitoring**: Detect suspicious activity patterns
- **Compliance Auditing**: Log retention for regulatory requirements

### Development & Testing
- **Debugging Support**: Detailed execution tracing
- **Integration Testing**: End-to-end log flow verification
- **Performance Analysis**: Load testing log analysis
- **Feature Validation**: New feature usage tracking

### Business Intelligence
- **User Behavior Analysis**: Application usage patterns
- **System Usage Metrics**: Service utilization tracking
- **Error Trend Analysis**: Long-term reliability monitoring
- **Capacity Planning**: Resource usage trend analysis

### MCP-Specific Applications
- **Context Tracking**: MCP context operation logging
- **Model Usage Analytics**: LLM interaction pattern analysis
- **Protocol Debugging**: MCP message flow tracing
- **Extension Monitoring**: Plugin and extension activity tracking

## 🤝 Contributing

### Development Setup
```bash
# Clone repository
git clone <repository>
cd services/mcp-logs

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/

# Start development server
uvicorn main:app --reload --host 0.0.0.0 --port 8016
```

### Adding New Log Sources
1. **Implement collector** for the new log source
2. **Add parser** for the log format
3. **Configure routing rules** for processing
4. **Update documentation** with new source details
5. **Add tests** for the new integration

## 📄 License

This service is part of the LLM Documentation Ecosystem. See project LICENSE for details.

---

**Status:** 🟢 Production Ready | **Port:** 8016 | **Storage:** Elasticsearch | **UI:** Kibana
