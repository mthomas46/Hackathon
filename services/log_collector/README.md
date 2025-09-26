# Log Collector Service

## Description

The **Log Collector Service** is a comprehensive logging and monitoring solution that provides centralized log aggregation, analysis, and alerting capabilities across the LLM Documentation Ecosystem. Built following **Domain-Driven Design (DDD)** principles, it serves as the **central nervous system** for operational visibility and system health monitoring.

### Key Features & Capabilities

#### Functionality

**🔍 Comprehensive Log Aggregation**
- Multi-source log collection from all ecosystem services
- Structured logging with correlation IDs and metadata
- Real-time log streaming and historical analysis
- Configurable log levels and filtering

**📊 Advanced Log Analysis**
- Pattern recognition and anomaly detection
- Performance metrics extraction and trending
- Error rate monitoring and alerting
- Log-based troubleshooting and diagnostics

**🚨 Intelligent Alerting System**
- Configurable alert rules and thresholds
- Multi-channel notifications (email, Slack, webhooks)
- Escalation policies and on-call rotation
- Automated incident response triggers

**🔄 Log Lifecycle Management**
- Configurable retention policies
- Automated log rotation and archiving
- Compression and storage optimization
- GDPR-compliant data handling

## Requirements

### Environment Variables

#### Core Configuration
```bash
# Service
LOG_COLLECTOR_PORT=5006
LOG_COLLECTOR_HOST=0.0.0.0

# Database
LOG_COLLECTOR_DB_URL=postgresql://user:pass@localhost:5432/log_collector

# External Services
LOG_COLLECTOR_REDIS_URL=redis://localhost:6379
LOG_COLLECTOR_SLACK_WEBHOOK=https://hooks.slack.com/services/...
```

#### Dependencies
- **PostgreSQL** 13+ for log storage and querying
- **Redis** 6+ for real-time log buffering
- **Elasticsearch** (optional) for advanced log search
- **Prometheus** for metrics collection

## Installation

### Local Development
```bash
cd services/log_collector
pip install -r requirements.txt
python main.py
```

### Docker Deployment
```yaml
# docker-compose.yml
services:
  log-collector:
    image: llm-docs-ecosystem/log-collector:latest
    ports:
      - "5006:5006"
    environment:
      - LOG_COLLECTOR_DB_URL=${DATABASE_URL}
      - LOG_COLLECTOR_REDIS_URL=${REDIS_URL}
```

## Config

### Service Configuration
```yaml
# config.yaml
service:
  name: log-collector
  version: "1.0.0"
  description: "Log Collector Service"

database:
  url: ${LOG_COLLECTOR_DB_URL}
  pool_size: 10
  max_overflow: 20

redis:
  url: ${LOG_COLLECTOR_REDIS_URL}
  key_prefix: "log_collector"

logging:
  level: INFO
  format: json
  file: logs/log_collector.log

alerting:
  slack_webhook: ${LOG_COLLECTOR_SLACK_WEBHOOK}
  email_recipients: ["ops@company.com"]
  error_threshold: 10
  warning_threshold: 5
```

## API Endpoints

### Core Endpoints

#### Log Ingestion
```
POST /api/v1/logs
- Ingest log entries with metadata
- Supports batch operations
- Automatic correlation ID assignment
```

#### Log Querying
```
GET /api/v1/logs
- Query logs with filtering and pagination
- Support for time ranges, log levels, services
- Full-text search capabilities
```

#### Alert Management
```
GET /api/v1/alerts
POST /api/v1/alerts/{alert_id}/acknowledge
- Alert listing and acknowledgment
- Alert rule configuration
```

#### Health Monitoring
```
GET /health
- Service health status
- Database connectivity checks
- Queue processing status
```

## Ecosystem Integration

### Service Dependencies

#### Required Services
- **shared**: Common utilities and base classes
- **Redis**: Real-time log buffering and caching
- **PostgreSQL**: Primary log storage

#### Optional Integrations
- **notification-service**: Alert delivery
- **monitoring**: Metrics and dashboards
- **Elasticsearch**: Advanced search capabilities

### Data Flow

```
Services → Log Collector → Redis Buffer → PostgreSQL Storage
                              ↓
                         Alert Engine → Notifications
                              ↓
                         Monitoring → Dashboards
```

## Architecture

### Domain Layer

#### Entities
- **LogEntry**: Core log data with metadata
- **Alert**: Alert definitions and instances
- **AlertRule**: Configurable alert conditions

#### Value Objects
- **LogLevel**: INFO, WARN, ERROR, DEBUG
- **CorrelationId**: Request tracing identifier
- **Timestamp**: ISO 8601 formatted timestamps

#### Domain Services
- **LogAnalysisService**: Pattern recognition and analysis
- **AlertEngine**: Alert evaluation and triggering
- **RetentionPolicy**: Log lifecycle management

### Application Layer

#### Commands
- **IngestLogCommand**: Log entry ingestion
- **CreateAlertCommand**: Alert rule creation
- **AcknowledgeAlertCommand**: Alert acknowledgment

#### Queries
- **GetLogsQuery**: Log retrieval with filtering
- **GetAlertsQuery**: Alert listing and status
- **GetMetricsQuery**: Log statistics and trends

#### CQRS Handlers
- **LogIngestionHandler**: Processes log ingestion commands
- **AlertQueryHandler**: Handles alert-related queries
- **MetricsQueryHandler**: Provides analytical insights

### Infrastructure Layer

#### Repositories
- **LogRepository**: PostgreSQL log storage
- **AlertRepository**: Alert rule and instance storage
- **MetricsRepository**: Aggregated statistics storage

#### External Services
- **RedisPublisher**: Real-time log publishing
- **SlackNotifier**: Alert notifications
- **EmailService**: Email alert delivery

## Monitoring & Observability

### Metrics
- **log_ingestion_rate**: Logs processed per second
- **alert_trigger_rate**: Alerts fired per hour
- **query_response_time**: API response times
- **storage_utilization**: Database storage usage

### Logging
- Structured JSON logging with correlation IDs
- Configurable log levels per component
- Automatic log rotation and retention

### Alerting
- Error rate thresholds
- Performance degradation alerts
- Storage capacity warnings
- Service availability monitoring

## Development

### Testing
```bash
# Run unit tests
pytest tests/unit/

# Run integration tests
pytest tests/integration/

# Run with coverage
pytest --cov=. --cov-report=html
```

### Code Quality
```bash
# Run linting
flake8 .

# Run type checking
mypy .

# Run security scanning
bandit -r .
```

## Deployment

### Production Checklist
- [ ] Database migrations applied
- [ ] Redis connectivity verified
- [ ] Alert webhook URLs configured
- [ ] Log retention policies set
- [ ] Monitoring dashboards configured
- [ ] SSL/TLS certificates installed

### Scaling Considerations
- **Horizontal Scaling**: Multiple log collector instances
- **Database Sharding**: Partition logs by time or service
- **Redis Clustering**: High availability log buffering
- **Load Balancing**: Distribute log ingestion requests

## Security

### Data Protection
- Log data encryption at rest and in transit
- PII detection and masking
- GDPR-compliant data retention policies
- Role-based access control

### Network Security
- Service-to-service authentication
- API rate limiting
- Input validation and sanitization
- Secure configuration management

## Troubleshooting

### Common Issues

#### High Log Volume
```
Symptoms: High CPU usage, slow queries
Solutions:
- Increase database connection pool
- Implement log sampling for high-volume services
- Add Redis buffering capacity
```

#### Alert Noise
```
Symptoms: Too many alerts, alert fatigue
Solutions:
- Tune alert thresholds
- Implement alert deduplication
- Use alert grouping and summarization
```

#### Storage Growth
```
Symptoms: Database storage filling up
Solutions:
- Configure log retention policies
- Implement log compression
- Archive old logs to cheaper storage
```

## Contributing

### Code Standards
- Follow DDD principles and CQRS patterns
- Write comprehensive unit tests
- Include docstrings for all public methods
- Use type hints throughout the codebase

### Commit Guidelines
- Use conventional commit format
- Include issue references when applicable
- Write clear, descriptive commit messages

## License

This service is part of the LLM Documentation Ecosystem and follows the same licensing terms as the main project.
