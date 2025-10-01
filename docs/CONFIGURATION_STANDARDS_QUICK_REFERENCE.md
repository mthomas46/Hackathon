# Configuration Standards Quick Reference

## Environment Variable Naming Convention

### ✅ CORRECT Examples

```bash
# Service Identification
SERVICE_NAME=my-service
SERVICE_VERSION=1.0.0
SERVICE_PORT=8080

# Feature Flags
FEATURE_METRICS=true
FEATURE_HEALTH_CHECKS=true
FEATURE_CORS=false

# External Services
EXTERNAL_OPENAI_API_KEY=sk-...
EXTERNAL_GITHUB_TOKEN=ghp_...
EXTERNAL_AWS_ACCESS_KEY_ID=AKIA...

# Infrastructure
REDIS_HOST=redis
REDIS_PORT=6379
DATABASE_HOST=postgres
DATABASE_PORT=5432
DATABASE_NAME=myapp

# API Configuration
API_HOST=0.0.0.0
API_PORT=8080

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Monitoring
METRICS_ENABLED=true
METRICS_PORT=9090
HEALTH_CHECK_INTERVAL=30s
```

### ❌ INCORRECT Examples (Don't Use)

```bash
# Wrong: ENABLE_* instead of FEATURE_*
ENABLE_METRICS=true          # ❌
FEATURE_METRICS=true         # ✅

# Wrong: DB_* instead of DATABASE_*
DB_HOST=localhost            # ❌
DATABASE_HOST=localhost      # ✅

# Wrong: Generic names
HOST=0.0.0.0                 # ❌
API_HOST=0.0.0.0             # ✅

PORT=8080                     # ❌
API_PORT=8080                 # ✅

# Wrong: Inconsistent prefixes
ANTHROPIC_API_KEY=...         # ❌
EXTERNAL_ANTHROPIC_API_KEY=... # ✅
```

## Port Range Allocation

| Range | Purpose | Examples |
|-------|---------|----------|
| 8000-8999 | HTTP APIs | 8080, 8081, 8082 |
| 9000-9999 | Health Checks | 9000, 9001 |
| 10000-10999 | Metrics | 9090 (Prometheus) |
| 11000-11999 | Debug | 11434 (Ollama) |
| 12000-12999 | Databases | 5432 (PostgreSQL) |
| 13000-13999 | Message Queues | 5672 (RabbitMQ) |
| 14000-14999 | Monitoring | 16686 (Jaeger) |
| 15000-15999 | Load Balancers | 8080 (Nginx) |

### Reserved Ports (Never Use)

```
22 (SSH), 25 (SMTP), 53 (DNS), 80 (HTTP), 443 (HTTPS),
3306 (MySQL), 5432 (PostgreSQL), 6379 (Redis), 27017 (MongoDB)
```

## Docker Compose Standards

### Service Definition Template

```yaml
version: '3.8'
services:
  my-service:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "${SERVICE_PORT:-8080}:8080"
    environment:
      - SERVICE_NAME=my-service
      - SERVICE_VERSION=1.0.0
      - ENVIRONMENT=development
      - REDIS_HOST=redis
      - LOG_LEVEL=INFO
    volumes:
      - ./config.yaml:/app/config.yaml:ro
      - my-service_logs:/app/logs:rw
    depends_on:
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - hackathon_default

volumes:
  my-service_logs:
    driver: local

networks:
  hackathon_default:
    driver: bridge
```

## Network Standards

### Standard Network Names

```yaml
networks:
  hackathon_default:    # Default service communication
    driver: bridge

  hackathon_backend:    # Backend services
    driver: bridge

  hackathon_frontend:   # Frontend services
    driver: bridge

  hackathon_database:   # Database services
    driver: bridge

  hackathon_monitoring: # Monitoring services
    driver: bridge

  hackathon_external:   # External integrations
    driver: bridge
```

### Service Network Membership

| Service Type | Networks |
|--------------|----------|
| Frontend | `hackathon_default`, `hackathon_frontend` |
| Backend API | `hackathon_default`, `hackathon_backend` |
| Database | `hackathon_database` |
| Monitoring | `hackathon_monitoring`, `hackathon_default` |
| External | `hackathon_external` |

## Volume Standards

### Named Volume Convention

```yaml
volumes:
  # Data volumes
  my-service_data:
    driver: local

  # Log volumes
  my-service_logs:
    driver: local

  # Cache volumes
  my-service_cache:
    driver: local
```

### Volume Mount Patterns

```yaml
volumes:
  # Read-only configuration
  - ./config.yaml:/app/config.yaml:ro

  # Read-write logs
  - ./logs:/app/logs:rw

  # Named volume for data
  - my-service_data:/app/data:rw

  # Named volume for cache
  - my-service_cache:/app/cache:rw
```

### ❌ Prohibited Volume Patterns

```yaml
volumes:
  # Complex relative paths
  - ../../:/app:ro              # ❌ Too complex

  # Duplicate mounts
  - ./:/app:rw                  # ❌ Duplicate
  - ./:/app:rw                  # ❌ Duplicate

  # Bind mounts for code
  - ./:/app/services/my-service:rw  # ❌ Use named volumes
```

## Dependency Declaration Standards

### Preferred Format (with health checks)

```yaml
depends_on:
  redis:
    condition: service_healthy
  postgres:
    condition: service_started
  my-api:
    condition: service_healthy
```

### Simple Format (acceptable)

```yaml
depends_on:
  - redis
  - postgres
  - my-api
```

### Service Dependency Requirements

| Service Type | Required Dependencies |
|--------------|----------------------|
| API Services | `redis` |
| Backend Services | `redis`, `postgres` (if using DB) |
| Frontend Services | API service name |
| Workers/Queues | `redis`, `rabbitmq` |
| Data Services | `redis`, `postgres` |

## Configuration File Structure

### Service Config (config.yaml)

```yaml
# Service identification
service:
  name: "my-service"
  version: "1.0.0"
  port: 8080

# Server configuration
server:
  host: "0.0.0.0"
  port: 8080
  workers: 4

# Environment-specific overrides
environment:
  development:
    debug: true
    log_level: "DEBUG"
  production:
    debug: false
    log_level: "INFO"

# Service dependencies
dependencies:
  redis:
    required: true
  database:
    required: false

# Feature flags
features:
  metrics: true
  health_checks: true
  cors: false
```

## Validation Commands

### CI/CD Validation

```bash
# Comprehensive validation
make ci-validate

# Individual validations
make validate-config
make validate-docker-files
make validate-docker-compose
make validate-ports
make validate-env
```

### Manual Validation Tools

```bash
# Configuration audit
python3 scripts/hardening/unified_config_manager.py audit

# Environment variable analysis
python3 scripts/hardening/env_var_standardizer.py --mode analyze

# Port conflict check
python3 scripts/hardening/port_registry.py --action check

# Volume analysis
python3 scripts/hardening/volume_standardizer.py --mode analyze

# Network analysis
python3 scripts/hardening/network_standardizer.py --mode analyze

# Dependency analysis
python3 scripts/hardening/dependency_standardizer.py --mode analyze
```

## Common Issues & Fixes

### Environment Variables

**Issue:** `ENABLE_*` variables found
```bash
# Fix: Run migration
python3 scripts/hardening/env_var_migrator.py --action migrate
```

**Issue:** Inconsistent prefixes
```bash
# Check: Analyze patterns
python3 scripts/hardening/env_var_standardizer.py --mode analyze
```

### Ports

**Issue:** Port conflicts
```bash
# Check conflicts
python3 scripts/hardening/port_registry.py --action check

# Register new port
python3 scripts/hardening/port_registry.py --action register --service my-service --port 8080 --type http_api
```

### Docker Compose

**Issue:** Invalid syntax
```bash
# Validate
docker-compose -f docker-compose.yml config
```

**Issue:** Standardization issues
```bash
# Run standardizer
python3 scripts/hardening/unified_docker_standardizer.py --mode apply
```

### Volumes

**Issue:** Complex volume mounts
```bash
# Analyze issues
python3 scripts/hardening/volume_standardizer.py --mode analyze

# Auto-fix
python3 scripts/hardening/volume_simplifier.py
```

### Networks

**Issue:** Inconsistent network names
```bash
# Consolidate networks
python3 scripts/hardening/network_consolidator.py
```

### Dependencies

**Issue:** Missing dependencies
```bash
# Analyze dependencies
python3 scripts/hardening/dependency_standardizer.py --mode analyze

# Add missing ones
python3 scripts/hardening/dependency_adder.py
```

## Service Onboarding Checklist

### Pre-Onboarding
- [ ] Service directory created: `services/my-service/`
- [ ] Basic structure in place
- [ ] Service name follows conventions

### Configuration Setup
- [ ] `config.yaml` created with standard structure
- [ ] `docker-compose.yml` created with standard template
- [ ] Environment variables follow naming conventions
- [ ] Ports assigned from correct ranges
- [ ] Networks properly configured
- [ ] Dependencies declared
- [ ] Volumes standardized

### Validation
- [ ] `make ci-validate` passes
- [ ] `make validate-docker-compose` passes
- [ ] `make validate-ports` passes
- [ ] Service starts successfully
- [ ] Health checks working

### Documentation
- [ ] README.md created/updated
- [ ] Configuration options documented
- [ ] Environment variables documented
- [ ] Port assignments documented

## Emergency Contacts

| Issue Type | Contact | Response Time |
|------------|---------|---------------|
| Port conflicts | DevOps Team | < 4 hours |
| Configuration failures | Platform Team | < 2 hours |
| Security issues | Security Team | < 1 hour |
| Service downtime | On-call Engineer | < 30 minutes |

## Quick Links

- **Full Governance:** `docs/CONFIGURATION_GOVERNANCE.md`
- **Makefile Commands:** `make help`
- **CI/CD Pipeline:** `.github/workflows/`
- **Service Template:** `services/_template/`

---

## Need Help?

1. **Check this document first** - most common issues are covered
2. **Run validation commands** - automated tools catch most issues
3. **Check existing services** - use them as examples
4. **Ask in #platform-engineering** - for complex issues

Remember: **Validation is automatic** - CI/CD will catch issues before they reach production! 🚀
