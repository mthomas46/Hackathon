# Monitoring Stack Setup

## Overview

The LLM Documentation Ecosystem includes a comprehensive monitoring stack built around the three pillars of observability:

- **Metrics**: Prometheus for collecting and storing time-series data
- **Visualization**: Grafana for dashboards and alerting
- **Tracing**: Jaeger for distributed request tracing

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Services      │───▶│   Prometheus    │───▶│     Grafana     │
│ (with metrics)  │    │  (scraping)     │    │ (dashboards)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Jaeger      │    │  Alertmanager   │    │   Alerting      │
│   (tracing)     │    │  (alerts)       │    │ (email/slack)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Quick Start

### 1. Start the Monitoring Stack

```bash
# Start monitoring stack only
docker-compose -f docker-compose.monitoring.yml up -d

# Or start with the full ecosystem
docker-compose --profile core up -d
docker-compose -f docker-compose.monitoring.yml up -d
```

### 2. Access Interfaces

- **Grafana**: http://localhost:3001 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Jaeger**: http://localhost:16686
- **Alertmanager**: http://localhost:9093

## Service Integration

### Adding Metrics to a Service

1. **Import metrics utilities** in your main.py:

```python
from services.shared.metrics import get_service_metrics, metrics_endpoint, instrument_http_request

# Initialize metrics
metrics = get_service_metrics("your-service-name")

# Add metrics endpoint
app.add_route("/metrics", metrics_endpoint("your-service-name"))

# Add middleware for HTTP metrics
app.middleware("http")(instrument_http_request(metrics))
```

2. **Record business metrics** in your handlers:

```python
from services.shared.metrics import record_document_processing, record_analysis_operation

# In your document processing handler
record_document_processing(metrics, source_type="github", status="success")

# In your analysis handler
record_analysis_operation(metrics, operation_type="consistency_check", status="completed")
```

3. **Track external requests**:

```python
import time
from services.shared.metrics import record_external_request

start_time = time.time()
try:
    # Make external request
    response = await client.get("http://external-service/api")
    duration = time.time() - start_time
    record_external_request(metrics, "external-service", "GET", str(response.status_code), duration)
except Exception as e:
    duration = time.time() - start_time
    record_external_request(metrics, "external-service", "GET", "error", duration)
```

## Key Metrics

### HTTP Metrics
- `http_requests_total{method, endpoint, status}` - Total requests
- `http_request_duration_seconds{method, endpoint}` - Response times

### Business Metrics
- `document_processing_total{source_type, status}` - Document operations
- `analysis_operations_total{operation_type, status}` - Analysis operations
- `external_requests_total{service_name, method, status}` - External API calls

### System Metrics
- `memory_usage_bytes` - Current memory usage
- `cpu_usage_percent` - Current CPU usage
- `queue_length{queue_name}` - Queue lengths

### Cache Metrics
- `cache_hits_total{cache_name}` - Cache hit count
- `cache_misses_total{cache_name}` - Cache miss count

## Alerting

### Alert Rules

The system includes comprehensive alerting for:

- **Service Health**: Services going down or flapping
- **Performance**: High CPU/memory usage, slow responses
- **Errors**: High error rates, timeouts
- **Resources**: Low disk space, high connection counts
- **Business Logic**: Queue backlogs, processing failures

### Alertmanager Configuration

Alerts are routed based on severity:
- **Critical**: Immediate notification to on-call
- **Warning**: Team notification
- **Info**: Dashboard indicators

### Notification Channels

- **Email**: SMTP configuration for team notifications
- **Slack**: Webhook integration for real-time alerts (optional)

## Grafana Dashboards

### Pre-configured Dashboards

1. **Service Overview** (`infrastructure/grafana/dashboards/services.json`)
   - Service health status
   - API response times (95th percentile)
   - Request rates per service
   - Error rates by service
   - CPU and memory usage
   - Redis/PostgreSQL metrics

### Creating Custom Dashboards

1. Access Grafana at http://localhost:3001
2. Create new dashboard
3. Add panels with Prometheus queries
4. Save and export JSON for version control

## Jaeger Tracing

### Instrumenting Services

1. **Add tracing to HTTP clients**:

```python
import requests
from jaeger_client import Config

# Configure Jaeger tracer
config = Config(
    config={
        'sampler': {'type': 'const', 'param': 1},
        'local_agent': {'reporting_host': 'jaeger', 'reporting_port': 6831},
        'logging': True,
    },
    service_name='your-service',
)
tracer = config.initialize_tracer()

# Instrument requests
def traced_request(method, url, **kwargs):
    with tracer.start_active_span(f'{method} {url}') as scope:
        return requests.request(method, url, **kwargs)
```

2. **Add spans to business logic**:

```python
with tracer.start_active_span('process_document') as scope:
    scope.set_tag('document_id', doc_id)
    scope.set_tag('source_type', source_type)
    # Your processing logic here
```

### Viewing Traces

- Access Jaeger UI at http://localhost:16686
- Search by service name, operation, or tags
- View flame graphs and span details
- Identify performance bottlenecks

## Scaling and Production

### High Availability

For production deployments:

1. **Prometheus Federation**: Multiple Prometheus instances
2. **Thanos**: Long-term storage and querying
3. **Cortex**: Horizontally scalable Prometheus
4. **Jaeger with Elasticsearch**: Scalable trace storage

### Security

```yaml
# Secure monitoring stack
prometheus:
  # Enable authentication
  web:
    config:
      basic_auth_users:
        admin: $2a$10$...

grafana:
  environment:
    GF_SECURITY_ADMIN_PASSWORD: ${SECURE_PASSWORD}
    GF_USERS_ALLOW_SIGN_UP: false
```

### Resource Requirements

Recommended minimum resources:

```yaml
prometheus:
  deploy:
    resources:
      limits:
        memory: 2G
        cpu: 1000m

grafana:
  deploy:
    resources:
      limits:
        memory: 1G
        cpu: 500m

jaeger:
  deploy:
    resources:
      limits:
        memory: 512M
        cpu: 500m
```

## Troubleshooting

### Common Issues

1. **Metrics not appearing in Prometheus**
   - Check service is running: `curl http://localhost:PORT/metrics`
   - Verify Prometheus scrape configuration
   - Check network connectivity between containers

2. **Grafana not showing data**
   - Verify Prometheus datasource configuration
   - Check query syntax in panels
   - Ensure time ranges include data points

3. **Jaeger not receiving traces**
   - Verify Jaeger agent configuration in services
   - Check network connectivity
   - Validate trace export format

4. **Alerts not firing**
   - Check Prometheus rule evaluation: `up == 0`
   - Verify alertmanager configuration
   - Test alert routing

### Debugging Commands

```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Query Prometheus metrics
curl "http://localhost:9090/api/v1/query?query=up"

# Check Grafana health
curl http://localhost:3001/api/health

# View Jaeger services
curl http://localhost:16686/api/services
```

## Integration with CI/CD

### Automated Testing

```bash
# Test metrics endpoint
curl -f http://localhost:5020/metrics

# Validate Prometheus configuration
docker run --rm -v $(pwd)/infrastructure/prometheus.yml:/etc/prometheus/prometheus.yml prom/prometheus --config.check
```

### Deployment Automation

```bash
# Deploy monitoring stack
docker-compose -f docker-compose.monitoring.yml up -d

# Health checks
docker-compose -f docker-compose.monitoring.yml ps
docker-compose -f docker-compose.monitoring.yml logs prometheus
```

## Performance Considerations

### Prometheus Optimization

- **Scrape intervals**: Balance between freshness and resource usage
- **Retention**: Configure appropriate data retention periods
- **Federation**: For multi-region deployments

### Grafana Optimization

- **Query caching**: Enable dashboard and query caching
- **Data source limits**: Configure query timeouts
- **Dashboard refresh**: Set appropriate refresh intervals

### Jaeger Optimization

- **Sampling**: Configure appropriate sampling rates
- **Storage**: Choose appropriate backend (memory/Cassandra/Elasticsearch)
- **Retention**: Configure trace retention policies

## Future Enhancements

- **Service Mesh Integration** (Istio, Linkerd)
- **Log Aggregation** (Loki, Elasticsearch)
- **Anomaly Detection** (Machine learning-based alerting)
- **Custom Metrics** (Business KPI tracking)
- **Multi-tenant Monitoring** (Team-based isolation)
