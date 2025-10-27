# Configuration Registry Deployment Guide

**Version:** 1.0  
**Last Updated:** October 26, 2025  
**Target:** Production Deployment

---

## 📋 Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Deployment Steps](#deployment-steps)
3. [Verification](#verification)
4. [Rollback Procedure](#rollback-procedure)
5. [Monitoring Setup](#monitoring-setup)
6. [Troubleshooting](#troubleshooting)

---

## Pre-Deployment Checklist

### ✅ Prerequisites

- [ ] Configuration Registry implemented (Phases 0-3)
- [ ] Validation API implemented (Phase 4)
- [ ] Tests passing (Phase 5)
- [ ] Documentation reviewed (Phase 6)
- [ ] `service_registry.yaml` validated
- [ ] All services updated to use registry
- [ ] Tests run successfully

### ✅ Environment Preparation

- [ ] Docker and Docker Compose installed
- [ ] Required ports available (8002, 8501, 6379, 5432, etc.)
- [ ] Network connectivity verified
- [ ] Sufficient disk space
- [ ] Backup of existing configuration

### ✅ Configuration Review

- [ ] Review `config/service_registry.yaml`
- [ ] Verify all service names match
- [ ] Verify all Redis stream names match
- [ ] Verify all consumer group names match
- [ ] Verify database connection settings
- [ ] Verify port assignments

---

## Deployment Steps

### Step 1: Backup Current Configuration

```bash
# Backup existing configuration files
cd /Users/mykalthomas/Documents/work/Hackathon
mkdir -p backups/$(date +%Y%m%d_%H%M%S)
cp -r services/ecosystem-mcp/config backups/$(date +%Y%m%d_%H%M%S)/
cp docker-compose.yml backups/$(date +%Y%m%d_%H%M%S)/
```

### Step 2: Pull Latest Code

```bash
# Pull latest code with configuration registry
git pull origin main

# Or checkout specific commit
git checkout <commit-sha>
```

### Step 3: Validate Configuration

```bash
# Validate YAML syntax
cd services/ecosystem-mcp
python -c "
from src.config.registry import get_registry
registry = get_registry()
print('✅ Registry loaded successfully')
print(f'Environment: {registry.environment}')
print(f'Services: {len(registry.services)}')
"
```

**Expected Output:**
```
✅ Registry loaded successfully
Environment: production
Services: 6
```

### Step 4: Run Pre-Deployment Tests

```bash
# Unit tests
pytest tests/unit/test_config_validation_api.py -v

# Integration tests (critical drift detection tests)
pytest tests/integration/test_config_validation_integration.py -v -k "drift"

# Full test suite
pytest tests/ -v
```

**Expected:** All tests pass ✅

### Step 5: Stop Existing Services

```bash
# Stop services gracefully
docker-compose down

# Verify all containers stopped
docker ps | grep ecosystem
```

**Expected:** No running containers

### Step 6: Build New Images

```bash
# Force rebuild (no cache)
docker-compose build --no-cache ecosystem-mcp
docker-compose build --no-cache ecosystem-mcp-dashboard
docker-compose build --no-cache ecosystem-mcp-embedding
```

**Expected:** Successful builds for all services

### Step 7: Start Services with Validation

```bash
# Start services
docker-compose up -d

# Watch logs for preflight checks
docker-compose logs -f ecosystem-mcp | grep "Preflight"
```

**Expected Output:**
```
✅ Preflight checks passed
✅ Registry Validation: All 9 validations passed
✅ Redis Connection: Successful
✅ Database Connection: Successful
✅ ALL SERVICES INITIALIZED SUCCESSFULLY
```

**If Validation Fails:**
```
❌ Registry Validation: 1 critical validation(s) failed
   - Redis Consumer Groups: Mismatch detected
```

**Action:** Service will not start. Fix configuration and restart.

### Step 8: Verify Services Are Running

```bash
# Check container status
docker-compose ps

# Expected output:
#   ecosystem-mcp              running
#   ecosystem-mcp-dashboard    running
#   ecosystem-mcp-embedding    running
#   postgres                   running
#   redis                      running
#   ollama                     running
```

### Step 9: Run Post-Deployment Validation

```bash
# Health check
curl http://localhost:8002/health

# Configuration health
curl http://localhost:8002/api/v1/config/health

# Comprehensive validation
curl http://localhost:8002/api/v1/config/validate

# Drift detection
curl http://localhost:8002/api/v1/config/diff
```

**Expected:**
- Health: `{"status": "healthy"}`
- Config Health: `{"status": "healthy"}`
- Validation: `{"overall_status": "healthy"}`
- Drift: `{"total_differences": 0}`

---

## Verification

### 1. Service Health Checks

```bash
# Ecosystem MCP
curl http://localhost:8002/health
# Expected: {"status": "healthy", "service": "Ecosystem MCP"}

# Dashboard
curl http://localhost:8501
# Expected: 200 OK

# Check all endpoints
curl http://localhost:8002/docs
# Expected: OpenAPI/Swagger UI loads
```

### 2. Configuration Validation

```bash
# Run full validation
curl http://localhost:8002/api/v1/config/validate | jq

# Expected output:
# {
#   "total_checks": 9,
#   "passed": 9,
#   "failed": 0,
#   "overall_status": "healthy"
# }
```

### 3. Drift Detection

```bash
# Check for configuration drift
curl http://localhost:8002/api/v1/config/diff | jq

# Expected output:
# {
#   "total_differences": 0,
#   "recommendation": "No critical issues"
# }
```

### 4. Component-Specific Checks

```bash
# Redis
curl http://localhost:8002/api/v1/config/validate/redis | jq

# Database
curl http://localhost:8002/api/v1/config/validate/database | jq

# ChromaDB
curl http://localhost:8002/api/v1/config/validate/chromadb | jq

# Services
curl http://localhost:8002/api/v1/config/validate/services | jq
```

### 5. Functional Testing

```bash
# Test ingestion
curl -X POST http://localhost:8002/api/v1/admin/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "repo_path": "/test/path",
    "operation": "snapshot",
    "commit_depth": 10
  }'

# Test RAG query
curl -X POST http://localhost:8002/api/v1/query/basic \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is this project?",
    "n_results": 5
  }'
```

---

## Rollback Procedure

### If Deployment Fails

#### Option 1: Quick Rollback (Recommended)

```bash
# Stop new services
docker-compose down

# Restore backup configuration
cp backups/YYYYMMDD_HHMMSS/config/* services/ecosystem-mcp/config/
cp backups/YYYYMMDD_HHMMSS/docker-compose.yml .

# Checkout previous commit
git checkout <previous-commit-sha>

# Rebuild and restart
docker-compose build
docker-compose up -d

# Verify
curl http://localhost:8002/health
```

#### Option 2: Gradual Rollback

```bash
# Stop only the failing service
docker-compose stop ecosystem-mcp

# Restore its configuration
cp backups/YYYYMMDD_HHMMSS/config/service_registry.yaml services/ecosystem-mcp/config/

# Rebuild and restart
docker-compose build ecosystem-mcp
docker-compose up -d ecosystem-mcp

# Verify
curl http://localhost:8002/health
```

### Rollback Verification

```bash
# Check service status
docker-compose ps

# Check logs
docker-compose logs -f ecosystem-mcp

# Test functionality
curl http://localhost:8002/health
curl http://localhost:8002/docs
```

---

## Monitoring Setup

### 1. Configuration Health Monitoring

Add to your monitoring system (Prometheus, Datadog, etc.):

```yaml
# prometheus_alerts.yml
groups:
  - name: config_health
    interval: 5m
    rules:
      - alert: ConfigurationDriftDetected
        expr: config_drift_total > 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Configuration drift detected"
          description: "{{ $value }} configuration mismatches detected"
      
      - alert: ConfigValidationFailed
        expr: config_validation_failed_total > 0
        for: 5m
        labels:
          severity: high
        annotations:
          summary: "Configuration validation failed"
          description: "{{ $value }} validation checks failed"
```

### 2. Automated Health Checks

Add to cron:

```bash
# /etc/cron.d/config-health
# Check configuration health every 5 minutes
*/5 * * * * curl -s http://localhost:8002/api/v1/config/health | jq -e '.status == "healthy"' || /usr/local/bin/alert_ops.sh "Config health check failed"

# Check for drift every 15 minutes
*/15 * * * * curl -s http://localhost:8002/api/v1/config/diff | jq -e '.total_differences == 0' || /usr/local/bin/alert_ops.sh "Configuration drift detected: $(curl -s http://localhost:8002/api/v1/config/diff | jq -r '.differences[0].field')"
```

### 3. Log Monitoring

Monitor these log patterns:

```bash
# Watch for validation failures
docker-compose logs -f ecosystem-mcp | grep "Registry Validation"

# Watch for drift detection
docker-compose logs -f ecosystem-mcp | grep "Configuration drift"

# Watch for preflight failures
docker-compose logs -f ecosystem-mcp | grep "Preflight check failed"
```

### 4. Dashboard Integration (Optional)

If using Grafana:

1. Create dashboard "Configuration Health"
2. Add panels:
   - Configuration Health Status (gauge)
   - Validation Pass Rate (graph)
   - Drift Detection Events (table)
   - Failed Validations (counter)

Example query:
```promql
# Configuration health status
config_health_status{service="ecosystem-mcp"}

# Validation pass rate
rate(config_validation_passed_total[5m]) / rate(config_validation_total[5m])

# Drift events
increase(config_drift_detected_total[1h])
```

---

## Troubleshooting

### Issue 1: Service Won't Start - Validation Failure

**Symptom:**
```
❌ Registry Validation: 1 critical validation(s) failed
   - Redis Consumer Groups: Mismatch detected
```

**Solution:**
1. Check exact error:
```bash
docker-compose logs ecosystem-mcp | grep "Registry Validation" -A 10
```

2. Check configuration:
```bash
curl http://localhost:8002/api/v1/config/diff | jq
```

3. Fix configuration in `config/service_registry.yaml`

4. Restart:
```bash
docker-compose restart ecosystem-mcp
```

### Issue 2: Configuration Drift Detected Post-Deployment

**Symptom:**
```json
{
  "total_differences": 1,
  "differences": [
    {
      "category": "Redis",
      "field": "consumer_group",
      "registry_value": "ingestion-workers",
      "runtime_value": "ingestion-worker"
    }
  ]
}
```

**Solution:**
1. Identify the mismatch
2. Update code to use registry:
```python
# Before
CONSUMER_GROUP = "ingestion-worker"

# After
from src.config.registry import get_registry
registry = get_registry()
CONSUMER_GROUP = registry.redis.streams.ingestion.consumer_group
```

3. Rebuild and restart:
```bash
docker-compose build ecosystem-mcp
docker-compose restart ecosystem-mcp
```

4. Verify:
```bash
curl http://localhost:8002/api/v1/config/diff | jq
```

### Issue 3: Registry File Not Found

**Symptom:**
```
FileNotFoundError: config/service_registry.yaml not found
```

**Solution:**
1. Verify file exists:
```bash
ls -la services/ecosystem-mcp/config/service_registry.yaml
```

2. Check Docker volume mount:
```bash
docker-compose config | grep -A 5 "volumes:"
```

3. Ensure correct working directory:
```yaml
# docker-compose.yml
services:
  ecosystem-mcp:
    working_dir: /app
    volumes:
      - ./services/ecosystem-mcp:/app
```

### Issue 4: Performance Degradation

**Symptom:**
- Slow API responses
- High CPU usage
- Validation taking >10s

**Solution:**
1. Check validation frequency:
```bash
# Don't run validation on every request
# Use health check for frequent monitoring
curl http://localhost:8002/api/v1/config/health  # Fast
# Use full validation only periodically
curl http://localhost:8002/api/v1/config/validate  # Comprehensive
```

2. Optimize validation:
```python
# Cache validation results for 5 minutes
from cachetools import TTLCache
validation_cache = TTLCache(maxsize=1, ttl=300)
```

3. Monitor resource usage:
```bash
docker stats ecosystem-mcp
```

---

## Post-Deployment

### 1. Documentation Update

- [ ] Update README with new configuration instructions
- [ ] Update runbook with drift detection procedures
- [ ] Document any environment-specific overrides
- [ ] Update team wiki/confluence

### 2. Team Communication

- [ ] Notify team of successful deployment
- [ ] Share monitoring dashboard links
- [ ] Document new configuration registry usage
- [ ] Schedule knowledge sharing session

### 3. Continuous Improvement

- [ ] Monitor drift detection alerts for patterns
- [ ] Review validation failures in logs
- [ ] Collect feedback from team
- [ ] Plan Phase 7 enhancements (if needed)

---

## Environment-Specific Considerations

### Development

```yaml
# config/service_registry.yaml
environment: "development"
redis:
  connection:
    host: "localhost"
    port: 6379
database:
  connection:
    url: "postgresql://localhost/ecosystem_dev"
```

**Deployment:**
```bash
docker-compose -f docker-compose.dev.yml up -d
```

### Staging

```yaml
# config/service_registry.staging.yaml
environment: "staging"
redis:
  connection:
    host: "redis-staging"
    port: 6379
database:
  connection:
    url: "postgresql://staging-db/ecosystem_staging"
```

**Deployment:**
```bash
export CONFIG_FILE=config/service_registry.staging.yaml
docker-compose -f docker-compose.staging.yml up -d
```

### Production

```yaml
# config/service_registry.production.yaml
environment: "production"
redis:
  connection:
    host: "redis-cluster.production"
    port: 6379
database:
  connection:
    url: "postgresql://prod-db/ecosystem_prod"
```

**Deployment:**
```bash
export CONFIG_FILE=config/service_registry.production.yaml
docker-compose -f docker-compose.prod.yml up -d
```

---

## Deployment Timeline

### Estimated Deployment Time

| Phase | Duration | Description |
|-------|----------|-------------|
| Pre-deployment checks | 10 minutes | Validate configuration, run tests |
| Service shutdown | 2 minutes | Graceful shutdown |
| Build images | 5 minutes | Docker build (with cache) |
| Start services | 3 minutes | Docker compose up |
| Preflight checks | 1 minute | Automatic validation |
| Post-deployment verification | 5 minutes | Health checks, drift detection |
| **Total** | **~25 minutes** | **Full deployment** |

### Zero-Downtime Deployment (Advanced)

For production with zero downtime:

1. Deploy to staging first
2. Run full test suite
3. Use blue-green deployment:
```bash
# Start new version (green)
docker-compose -f docker-compose.green.yml up -d

# Verify green is healthy
curl http://localhost:8003/api/v1/config/health

# Switch load balancer to green
# Stop blue
docker-compose -f docker-compose.blue.yml down
```

---

## Success Criteria

### Deployment is successful when:

- [x] All services start without errors
- [x] Preflight checks pass
- [x] Configuration health is "healthy"
- [x] Full validation passes (9/9 checks)
- [x] Zero configuration drift detected
- [x] All functional tests pass
- [x] API endpoints respond correctly
- [x] Dashboard accessible
- [x] No errors in logs

### Monitoring confirms:

- [x] CPU usage normal (<20%)
- [x] Memory usage normal (<500MB)
- [x] Response times acceptable (<2s)
- [x] No alert triggers
- [x] Configuration health stable for 1 hour

---

## Support

### If Issues Arise:

1. **Check logs:**
```bash
docker-compose logs -f ecosystem-mcp
```

2. **Run diagnostics:**
```bash
curl http://localhost:8002/api/v1/config/validate | jq
curl http://localhost:8002/api/v1/config/diff | jq
```

3. **Contact:**
- On-call engineer: [contact info]
- Slack: #ecosystem-mcp-alerts
- Email: ops@example.com

---

**Deployment Guide v1.0 - Production Ready ✅**

**Last Validated:** October 26, 2025  
**Next Review:** January 26, 2026

