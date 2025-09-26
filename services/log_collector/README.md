# Log Collector Service

## Description

The **Log Collector Service** is a comprehensive logging and monitoring solution that provides centralized log aggregation, analysis, and alerting capabilities across the LLM Documentation Ecosystem. Built following **Domain-Driven Design (DDD)** principles, it serves as the **central nervous system** for operational visibility and system health monitoring.

## Features

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

## Infrastructure

### Docker Configuration
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
      - LOG_COLLECTOR_SLACK_WEBHOOK=${SLACK_WEBHOOK}
    depends_on:
      - postgres
      - redis
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: log_collector
      POSTGRES_USER: log_collector
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### Kubernetes Deployment
```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: log-collector
spec:
  replicas: 2
  selector:
    matchLabels:
      app: log-collector
  template:
    metadata:
      labels:
        app: log-collector
    spec:
      containers:
      - name: log-collector
        image: llm-docs-ecosystem/log-collector:latest
        ports:
        - containerPort: 5006
        env:
        - name: LOG_COLLECTOR_DB_URL
          valueFrom:
            secretKeyRef:
              name: log-collector-secrets
              key: database-url
        - name: LOG_COLLECTOR_REDIS_URL
          valueFrom:
            secretKeyRef:
              name: log-collector-secrets
              key: redis-url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

### Production Readiness
- **Health Checks**: Automatic service health monitoring
- **Logging**: Structured JSON logging with correlation IDs
- **Metrics**: Prometheus metrics endpoint for monitoring
- **Security**: TLS encryption and authentication
- **Backup**: Automated database backups and log archiving

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

## Ecosystem

### Service Dependencies

#### Required Services
- [**shared**](../../services/shared/): Common utilities and base classes
- **Redis**: Real-time log buffering and caching
- **PostgreSQL**: Primary log storage

#### Optional Integrations
- [**notification-service**](../notification-service/): Alert delivery and notifications
- [**monitoring**](../monitoring/): Metrics collection and dashboards
- **Elasticsearch**: Advanced search capabilities

### Data Flow

```
Services → [Log Collector](./) → Redis Buffer → PostgreSQL Storage
                              ↓
                         Alert Engine → [Notification Service](../notification-service/)
                              ↓
                         [Monitoring](../monitoring/) → Dashboards
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

## Related Documentation

- [Main Project README](../../README.md) - Project overview and setup instructions
- [Architecture Documentation](../../docs/architecture/) - System architecture and design patterns
- [Testing Guide](../../docs/guides/TESTING_GUIDE.md) - Comprehensive testing procedures
- [Services Overview](../README_SERVICES.md) - Complete ecosystem services catalog
- [Shared Infrastructure](../../services/shared/README.md) - Common utilities and shared patterns
- [API Documentation](./api/) - REST API endpoints and OpenAPI specifications

## License

This service is part of the LLM Documentation Ecosystem and follows the same licensing terms as the main project.
