# Operational Runbook

## Health checks

### Service Health Endpoints

#### Core Services
- **Prompt Store**: `GET /health` - Database connectivity and basic functionality
- **Interpreter**: `GET /health` - Service availability and core functionality
- **Doc Store**: `GET /health` - Database connectivity and storage health
- **Source Agent**: `GET /health` - Multi-source connectivity and API health
- **Analysis Service**: `GET /integration/health` - Integration health with dependencies
- **Log Collector**: `GET /health` - In-memory storage health
- **Notification Service**: `GET /health` - Service availability and DLQ status
- **Secure Analyzer**: `GET /health` - AI provider connectivity
- **Summarizer Hub**: `GET /health` - AI provider health and model availability
- **GitHub MCP**: `GET /health` - GitHub API connectivity and tool health
- **Memory Agent**: `GET /health` - Redis connectivity and memory health
- **Code Analyzer**: `GET /health` - Analysis engine health
- **Frontend**: `GET /health` - Web service availability
- **Bedrock Proxy**: `GET /health` - Proxy service health
- **CLI**: Health check via orchestrator integration

#### Orchestrator Service (DDD Architecture)
- **Basic Health**: `GET /health` - Service availability
- **System Health**: `GET /api/v1/health/system` - Comprehensive system health
- **Service Health**: `GET /api/v1/health/services/{service_id}` - Individual service health
- **System Metrics**: `GET /api/v1/health/system/metrics` - Performance metrics
- **System Info**: `GET /api/v1/health/system/info` - System information
- **Readiness Check**: `GET /api/v1/health/system/readiness` - Startup readiness
- **Workflow Health**: `GET /api/v1/health/system/workflows` - Workflow system health

### Quick Health Check Script
```bash
# Check all services health
SERVICES=(prompt-store interpreter orchestrator doc_store source-agent analysis-service)

# Orchestrator-specific health checks (DDD architecture)
echo "Checking orchestrator basic health..."
curl -f http://localhost:5099/health || echo "Orchestrator basic health failed"

echo "Checking orchestrator system health..."
curl -f http://localhost:5099/api/v1/health/system || echo "Orchestrator system health failed"

# Standard service health checks
for service in "${SERVICES[@]}"; do
  echo "Checking $service..."
  curl -f http://localhost:$(get_port $service)/health || echo "$service health check failed"
done

# Orchestrator bounded context checks
echo "Checking orchestrator bounded contexts..."
curl -f http://localhost:5099/api/v1/service-registry/services || echo "Service registry check failed"
curl -f http://localhost:5099/api/v1/workflows || echo "Workflow management check failed"
```

## Common issues

### API and Integration Issues
- **422 Unprocessable Entity**: Malformed JSON payload or invalid schema
- **404 Not Found**: Incorrect endpoint path or missing route
- **500 Internal Server Error**: Service logic error or dependency failure
- **502 Bad Gateway**: Downstream service unavailable
- **503 Service Unavailable**: Service overloaded or in maintenance

### Data and State Issues
- **Envelope vs Direct Data**: Some endpoints return success envelopes, others direct JSON
- **In-memory State Accumulation**: Log Collector and Memory Agent may accumulate state between tests
- **Cache Invalidation**: Stale cached data causing inconsistent responses
- **Database Connection Issues**: SQLite or Redis connectivity problems

### Configuration Issues
- **Missing Environment Variables**: Service URLs or credentials not set
- **Port Conflicts**: Multiple services trying to use same port
- **Network Connectivity**: Inter-service communication blocked by firewall
- **Dependency Version Mismatch**: Incompatible package versions

## Per-service troubleshooting

### Interpreter
| Symptom | Checks | Fix |
|---------|--------|-----|
| 404 on /interpret in tests | sys.path includes project root | Add `sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))` |
| Envelope mismatch | Response contains success envelope | Adjust assertions: check `response.json().get("data")` |
| Module import errors | Dynamic import fails | Ensure `services/interpreter/main.py` loads correctly |
| Natural language processing fails | Model/token limits exceeded | Check input length and model constraints |

### Prompt Store
| Symptom | Checks | Fix |
|---------|--------|-----|
| Duplicate prompt creation | Existing prompt by name/category | Handle 409 error; rename or use PUT to update |
| Analytics empty | DB path and migration run | Verify `PROMPT_STORE_DB` env and call `/migrate` |
| Database locked | Concurrent access to SQLite | Implement connection pooling or file locking |
| Version conflicts | Multiple versions of same prompt | Use version parameter in API calls |

### Doc Store
| Symptom | Checks | Fix |
|---------|--------|-----|
| Search returns no results | Query syntax or index issues | Check search query format and reindex if needed |
| Document save fails | Storage permissions or disk space | Verify write permissions and available disk space |
| Quality signals not updating | Background job failures | Check job queue and restart worker processes |
| Database corruption | SQLite file integrity | Restore from backup or rebuild database |

### Source Agent
| Symptom | Checks | Fix |
|---------|--------|-----|
| Source API authentication fails | API tokens and credentials | Verify environment variables and token validity |
| Rate limit exceeded | API quota reached | Implement backoff strategy or increase limits |
| Normalization fails | Source data format changed | Update normalization logic for new data format |
| Cache performance degraded | Redis connectivity issues | Check Redis server and connection pooling |

### Analysis Service
| Symptom | Checks | Fix |
|---------|--------|-----|
| Integration health fails | Dependency services down | Start required services (Doc Store, Source Agent) |
| Analysis results empty | Input data quality issues | Validate input documents and preprocessing |
| Performance degradation | Large dataset processing | Implement pagination or batch processing |
| Model timeout errors | AI provider response delays | Increase timeout values or use fallback providers |

### Orchestrator (DDD Architecture)

The orchestrator service follows Domain-Driven Design with 7 bounded contexts. Issues are typically isolated to specific contexts.

#### General Issues
| Symptom | Checks | Fix |
|---------|--------|-----|
| Service fails to start | Import errors or missing dependencies | Check `python -c "from services.orchestrator.main import app"` |
| API returns 500 errors | Domain logic errors | Check orchestrator logs for DomainResult failures |
| High memory usage | In-memory repositories accumulating data | Restart service or implement data cleanup |
| Slow API responses | Complex cross-context operations | Profile with `/api/v1/health/system/metrics` |

#### Bounded Context Issues

**🎯 Workflow Management**
| Symptom | Checks | Fix |
|---------|--------|-----|
| Workflow creation fails | Validation errors | Check workflow schema and required fields |
| Execution stalls | Workflow executor issues | Verify LangGraph integration and dependencies |
| Parameter resolution fails | Missing context data | Ensure workflow parameters are properly defined |

**🔍 Service Registry**
| Symptom | Checks | Fix |
|---------|--------|-----|
| Service discovery fails | Registration incomplete | Check `/api/v1/service-registry/services` endpoint |
| Health checks failing | Service endpoints unreachable | Verify service URLs and network connectivity |
| Registration conflicts | Duplicate service IDs | Use unique service identifiers |

**🏥 Health Monitoring**
| Symptom | Checks | Fix |
|---------|--------|-----|
| Metrics collection fails | Service connectivity issues | Check individual service health endpoints |
| System health shows errors | Multiple service failures | Restart failing services or check dependencies |
| Readiness probes failing | Startup sequence issues | Verify service startup order and dependencies |

**⚙️ Infrastructure**
| Symptom | Checks | Fix |
|---------|--------|-----|
| Saga transactions hanging | Timeout configuration | Check saga timeout settings and retry logic |
| DLQ accumulation | Failed event processing | Process DLQ with `/api/v1/infrastructure/dlq/retry` |
| Event streaming fails | Message broker issues | Verify Redis connectivity and queue configuration |

**📥 Ingestion**
| Symptom | Checks | Fix |
|---------|--------|-----|
| Data ingestion fails | Source connectivity | Check source API credentials and endpoints |
| Ingestion status stuck | Processing errors | Monitor `/api/v1/ingestion/status/{id}` |
| Pipeline performance poor | Resource constraints | Scale ingestion workers or optimize processing |

**❓ Query Processing**
| Symptom | Checks | Fix |
|---------|--------|-----|
| Query interpretation fails | NLP model issues | Check model loading and input validation |
| Results inconsistent | Query parsing errors | Verify query syntax and context parameters |
| Performance degradation | Complex queries | Implement query optimization or caching |

**📊 Reporting**
| Symptom | Checks | Fix |
|---------|--------|-----|
| Report generation fails | Data source issues | Check data availability and access permissions |
| Report quality poor | Template or data issues | Update report templates and validate data sources |
| Scheduled reports missing | Scheduler configuration | Verify cron settings and execution permissions |

### Log Collector
| Symptom | Checks | Fix |
|---------|--------|-----|
| Stats not zero between tests | In-memory global not cleared | Add pytest fixture: `@pytest.fixture(autouse=True)` to clear `_logs` |
| Memory usage high | Log retention policy | Implement log rotation or size limits |
| Log ingestion fails | Payload format issues | Validate log format against expected schema |
| Performance degradation | High log volume | Implement batch processing or sampling |

### Secure Analyzer
| Symptom | Checks | Fix |
|---------|--------|-----|
| AI provider connection fails | API keys and endpoints | Verify credentials and network connectivity |
| Model selection errors | Unsupported model requested | Check available models and update configuration |
| Security policy violations | Content filtering triggered | Review content and adjust policy settings |
| Rate limiting issues | API quota exceeded | Implement request throttling or increase limits |

### Summarizer Hub
| Symptom | Checks | Fix |
|---------|--------|-----|
| Model loading fails | Model availability or disk space | Verify model files and storage capacity |
| Summarization quality poor | Prompt or model issues | Update prompts or switch to different model |
| Provider switching fails | Fallback configuration | Check provider priorities and availability |
| Token limit exceeded | Input text too long | Implement text chunking or summarization strategies |

### Notification Service
| Symptom | Checks | Fix |
|---------|--------|-----|
| Owner resolution fails | Owner mapping configuration | Update owner mappings in environment or file |
| Notification delivery fails | Webhook/SMTP configuration | Verify notification targets and credentials |
| DLQ accumulation | Failed notification backlog | Process DLQ items or update delivery configuration |
| Deduplication not working | Message fingerprinting issues | Check deduplication logic and time windows |

### Memory Agent
| Symptom | Checks | Fix |
|---------|--------|-----|
| Redis connection fails | Redis server availability | Start Redis server and verify connection string |
| Memory usage high | Cache eviction policy | Configure appropriate cache TTL and size limits |
| Data consistency issues | Concurrent access conflicts | Implement optimistic locking or serialization |
| Performance degradation | Cache miss rate high | Optimize cache keys and access patterns |

### GitHub MCP
| Symptom | Checks | Fix |
|---------|--------|-----|
| Tool invocation fails | GitHub API authentication | Verify GitHub token and API permissions |
| Tool filtering not working | Toolset configuration | Update `GITHUB_TOOLSETS` environment variable |
| Mock responses incorrect | Mock data format issues | Validate mock response schemas against real API |
| Rate limit handling fails | GitHub API quota management | Implement proper backoff and retry logic |

## Common errors and remediation

### HTTP Status Code Errors
| Error Code | Description | Likely Cause | Remediation |
|------------|-------------|--------------|-------------|
| 400 Bad Request | Client sent malformed request | Invalid request format or missing required fields | Validate request payload against API schema |
| 401 Unauthorized | Authentication failed | Missing or invalid credentials | Check API keys, tokens, or authentication headers |
| 403 Forbidden | Access denied | Insufficient permissions | Verify user roles and access controls |
| 404 Not Found | Resource not found | Incorrect URL or resource doesn't exist | Check endpoint paths and resource identifiers |
| 409 Conflict | Resource conflict | Duplicate resource or concurrent modification | Handle conflicts with retry logic or conflict resolution |
| 422 Unprocessable Entity | Validation failed | Malformed JSON or invalid data | Fix payload schema and data validation |
| 429 Too Many Requests | Rate limit exceeded | Too many requests in time window | Implement exponential backoff and rate limiting |
| 500 Internal Server Error | Server error | Unexpected server-side error | Check server logs and implement error handling |
| 502 Bad Gateway | Gateway error | Upstream service unavailable | Check dependent services and network connectivity |
| 503 Service Unavailable | Service overload | Service temporarily unavailable | Implement circuit breaker or retry with backoff |
| 504 Gateway Timeout | Request timeout | Slow upstream response | Increase timeout values or optimize slow operations |

### Application-Specific Errors
| Error Type | Likely Cause | Remediation |
|------------|--------------|-------------|
| Envelope mismatch | Service returns success envelope vs direct data | Check API documentation; unwrap data with `response.json().get("data")` |
| Missing env var | Required environment variable not set | Provide environment variable or use service defaults |
| Cross-service flakiness | Dependent service down or unresponsive | Use mocks/stubs in tests or ensure dependencies are running |
| Database connection failed | Database server unavailable | Check database connectivity and restart if needed |
| Cache miss/invalidation | Cached data stale or missing | Clear cache or implement cache warming strategies |
| Module import error | Python path issues in tests | Add project root to `sys.path` in test files |
| Authentication expired | API tokens or credentials expired | Refresh tokens or update credentials |
| Resource exhausted | Memory, CPU, or disk limits reached | Monitor resource usage and implement limits |
| Network timeout | Slow network or unresponsive service | Increase timeout values and implement retry logic |

### Testing-Specific Errors
| Error Type | Likely Cause | Remediation |
|------------|--------------|-------------|
| Test isolation failure | Global state not cleared between tests | Use pytest fixtures with `autouse=True` to reset state |
| Mock assertion failed | Unexpected call count or arguments | Verify mock setup and adjust expectations |
| Async test hanging | Coroutine not properly awaited | Ensure all async operations are properly awaited |
| Fixture dependency missing | Test requires unavailable fixture | Check fixture dependencies and mock unavailable services |
| Import path resolution | Module not found in test environment | Add project root to Python path in test files |

## Logs & Metrics

### Centralized Logging
- **Log Collector**: `GET /logs` and `GET /stats` for development/testing
- **Service Logs**: `docker compose logs <service>` for containerized deployments
- **Structured Logging**: All services use JSON-formatted logs with correlation IDs
- **Log Levels**: ERROR, WARNING, INFO, DEBUG (configurable via environment)

### Monitoring Endpoints
- **Health Checks**: `/health` endpoint on all services
- **Metrics**: `/metrics` endpoint (where available) for Prometheus integration
- **Service Info**: `/info` and `/config/effective` for service metadata
- **System Health**: `/health/system` on Orchestrator for overall system status

### Key Metrics to Monitor
- **Request Rate**: Requests per second by service and endpoint
- **Error Rate**: Percentage of failed requests (4xx/5xx status codes)
- **Response Time**: P95/P99 response times for critical endpoints
- **Resource Usage**: CPU, memory, and disk utilization
- **Queue Depth**: Redis queue lengths for async processing
- **Cache Hit Rate**: Redis/memory cache effectiveness
- **Database Connections**: Active connections and query performance

### Alerting Thresholds
- Error rate > 5% for 5 minutes
- Response time > 2 seconds for P95
- Service unavailable for > 30 seconds
- Queue depth > 1000 messages
- Memory usage > 85%
- Disk usage > 90%

## Escalation Procedures

### Level 1: Service Owner
1. Check service health endpoint (`/health`)
2. Review recent service logs
3. Verify environment configuration
4. Check dependent services status
5. Restart service if needed

### Level 2: Platform Team
1. Check infrastructure components (Redis, databases)
2. Review network connectivity
3. Analyze resource utilization
4. Check for configuration drift
5. Implement emergency fixes

### Level 3: Development Team
1. Analyze error patterns and stack traces
2. Review recent code changes
3. Implement permanent fixes
4. Update documentation and monitoring

## Incident Response Playbooks

### Service Down (Complete Failure)
**Symptoms**: Service returns 5xx errors or is unreachable
**Immediate Actions**:
1. Check service logs for error details
2. Verify dependent services are running
3. Check resource limits (memory, CPU)
4. Restart service container
5. If restart fails, check configuration and dependencies

### High Error Rate
**Symptoms**: Increased 4xx/5xx responses
**Investigation Steps**:
1. Analyze error patterns in logs
2. Check request payloads for validation issues
3. Verify external API dependencies
4. Review rate limiting and throttling
5. Implement circuit breaker if needed

### Performance Degradation
**Symptoms**: Slow response times or high resource usage
**Diagnostic Steps**:
1. Check system resources (CPU, memory, disk I/O)
2. Analyze slow query logs
3. Review cache hit rates
4. Check for memory leaks
5. Implement performance optimizations

### Data Consistency Issues
**Symptoms**: Inconsistent data across services
**Resolution Steps**:
1. Verify database connectivity and integrity
2. Check transaction boundaries
3. Review cache invalidation logic
4. Implement data reconciliation if needed
5. Update data validation rules

## Maintenance Procedures

### Regular Health Checks
```bash
# Daily health check script
#!/bin/bash
SERVICES=("prompt-store" "interpreter" "orchestrator" "doc_store" "source-agent")
for service in "${SERVICES[@]}"; do
  echo "=== $service ==="
  curl -s http://localhost:$(get_port $service)/health | jq .
  echo
done
```

### Log Rotation
- Configure log rotation for all services
- Archive logs older than 30 days
- Compress archived logs for storage efficiency
- Monitor log disk usage

### Backup Procedures
- Database backups: Daily full backups, hourly incremental
- Configuration backups: Version controlled in Git
- Log archives: Weekly compressed archives
- Test restore procedures monthly

### Security Updates
- Monitor for security vulnerabilities in dependencies
- Apply patches during maintenance windows
- Update base images and runtime environments
- Review and rotate API keys and credentials

## Communication Templates

### Incident Notification
```
Subject: [INCIDENT] Service Unavailable - {Service Name}

Description: {Brief description of the issue}
Impact: {Affected users/services}
Status: {Investigation/In Progress/Resolved}
ETA: {Estimated resolution time}
```

### Status Update
```
Subject: [UPDATE] Incident #{ID} - {Status}

Current Status: {Brief status description}
Actions Taken: {What has been done}
Next Steps: {Planned actions}
ETA: {Updated timeline}
```

### Post-Incident Review
```
Subject: [REVIEW] Incident #{ID} - Lessons Learned

Timeline: {Incident start/end times}
Impact: {Scope and severity}
Root Cause: {Technical cause analysis}
Resolution: {How the issue was fixed}
Prevention: {Steps to prevent recurrence}
```
