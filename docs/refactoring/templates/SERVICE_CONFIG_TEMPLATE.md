<!-- AI_READ_PRIORITY: 3 -->
<!-- AI_TAGS: configuration, {{SERVICE_NAME}}, ports, credentials, profiles -->
<!-- AI_KEY_SECTIONS: Ports, Credentials, Profiles, Validation -->

---
ai_metadata:
  purpose: service_configuration
  read_priority: 3
  context_level: service
  service: {{SERVICE_NAME}}
  tags:
  - configuration
  - {{SERVICE_NAME}}
  - ports
  - credentials
  when_to_read: Before running service, during deployment
  key_sections:
  - Ports & Networking
  - Credentials & Secrets
  - Configuration Profiles
  - Validation
  execution_relevance: operational
---

# {{SERVICE_NAME}} Configuration

**Service**: {{SERVICE_NAME}}  
**Version**: {{VERSION}}  
**Last Updated**: {{DATE}}  
**Status**: {{STATUS}}

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Ports & Networking](#ports--networking)
3. [Credentials & Secrets](#credentials--secrets)
4. [Configuration Files](#configuration-files)
5. [Environment Variables](#environment-variables)
6. [Configuration Profiles](#configuration-profiles)
7. [Docker Configuration](#docker-configuration)
8. [Validation](#validation)
9. [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

{{SERVICE_DESCRIPTION}}

**Configuration managed by**: [MASTER_CONFIGURATION_REGISTRY.md](../../docs/refactoring/MASTER_CONFIGURATION_REGISTRY.md)

---

## 🌐 Ports & Networking

### Assigned Ports

| Port Type | Port Number | Purpose | External Access |
|-----------|-------------|---------|-----------------|
| HTTP | {{HTTP_PORT}} | REST API endpoints | {{HTTP_EXTERNAL}} |
| Internal | {{INTERNAL_PORT}} | Inter-service communication | No |
| gRPC | {{GRPC_PORT}} | gRPC API (if applicable) | No |
| Admin | {{ADMIN_PORT}} | Admin/debug endpoints | No |

### Network Configuration

**Docker Network**: `hackathon_{{NETWORK_TYPE}}`

**Service Discovery**:
- DNS Name: `{{SERVICE_NAME}}`
- Internal URL: `http://{{SERVICE_NAME}}:{{HTTP_PORT}}`

### Health Check

**Endpoint**: `GET /health`  
**Expected Response**: `200 OK`

```bash
# Check service health
curl http://localhost:{{HTTP_PORT}}/health
```

---

## 🔑 Credentials & Secrets

### Required Credentials

{{#if REQUIRES_CREDENTIALS}}
| Credential | Environment Variable | Required | Default | Notes |
|------------|---------------------|----------|---------|-------|
{{#each CREDENTIALS}}
| {{name}} | {{env_var}} | {{required}} | {{default}} | {{notes}} |
{{/each}}

### Setup

**Development**:
```bash
# Copy template
cp .env.template .env

# Edit with your credentials
vi .env
```

**Production**:
```bash
# Use secrets manager (Docker Secrets, K8s Secrets, etc.)
# Never commit credentials to git
```

{{else}}
**No credentials required** - This service is self-contained.
{{/if}}

---

## 📄 Configuration Files

### File Structure

```
{{SERVICE_NAME}}/
├── .env                    # Environment variables (gitignored)
├── .env.template           # Template for .env
├── config.yaml             # Application configuration
├── docker-compose.yml      # Docker Compose config
├── Dockerfile              # Production image
├── Dockerfile.dev          # Development image
└── Makefile                # Common commands
```

### config.yaml

**Location**: `./config.yaml`

```yaml
# Service configuration
service:
  name: {{SERVICE_NAME}}
  version: "{{VERSION}}"
  description: "{{SERVICE_DESCRIPTION}}"

server:
  host: "0.0.0.0"
  port: {{HTTP_PORT}}
  workers: ${WORKERS:-4}

logging:
  level: ${LOG_LEVEL:-info}
  format: json
  output: stdout

{{#if HAS_DEPENDENCIES}}
dependencies:
{{#each DEPENDENCIES}}
  {{name}}:
    url: {{url}}
{{/each}}
{{/if}}
```

### .env Template

**Location**: `./.env.template`

```bash
# Service: {{SERVICE_NAME}}
# Copy to .env and fill in values

# === Core Configuration ===
SERVICE_NAME={{SERVICE_NAME}}
SERVICE_PORT={{HTTP_PORT}}
LOG_LEVEL=info

{{#if REQUIRES_CREDENTIALS}}
# === Credentials ===
{{#each CREDENTIALS}}
{{env_var}}=your_{{name}}_here
{{/each}}
{{/if}}

# === Feature Flags ===
ENABLE_METRICS=true
ENABLE_TRACING=false

{{#if HAS_DEPENDENCIES}}
# === Dependencies ===
{{#each DEPENDENCIES}}
{{env_var}}={{default_url}}
{{/each}}
{{/if}}
```

---

## 🔧 Environment Variables

### Core Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SERVICE_NAME` | Service name | {{SERVICE_NAME}} | Yes |
| `SERVICE_PORT` | HTTP port | {{HTTP_PORT}} | Yes |
| `LOG_LEVEL` | Logging level | `info` | No |
| `WORKERS` | Worker processes | `4` | No |

### Feature Flags

| Variable | Description | Default | Type |
|----------|-------------|---------|------|
| `ENABLE_METRICS` | Enable Prometheus metrics | `true` | Boolean |
| `ENABLE_TRACING` | Enable distributed tracing | `false` | Boolean |
| `ENABLE_SWAGGER` | Enable Swagger UI | `true` | Boolean |

{{#if REQUIRES_CREDENTIALS}}
### Credentials

| Variable | Description | Required |
|----------|-------------|----------|
{{#each CREDENTIALS}}
| `{{env_var}}` | {{description}} | {{required}} |
{{/each}}
{{/if}}

---

## 🎛️ Configuration Profiles

### Available Profiles

#### Development Profile

**Purpose**: Local development with debug features

**Activation**:
```bash
export PROFILE=development
# or
docker-compose --profile dev up {{SERVICE_NAME}}
```

**Features**:
- Debug logging enabled
- Swagger UI accessible
- Hot reload enabled
- Sample/test data loaded
- Longer timeouts for debugging

**Configuration**:
```yaml
profile: development
log_level: debug
features:
  - swagger_ui
  - debug_endpoints
  - hot_reload
performance:
  workers: 2
  timeout: 300
```

#### Testing Profile

**Purpose**: Automated testing

**Activation**:
```bash
export PROFILE=testing
pytest tests/
```

**Features**:
- Minimal logging
- In-memory dependencies
- Test fixtures enabled
- Fast timeouts

**Configuration**:
```yaml
profile: testing
log_level: error
features:
  - test_mode
  - mock_dependencies
performance:
  workers: 1
  timeout: 10
```

#### Production Profile

**Purpose**: Production deployment

**Activation**:
```bash
export PROFILE=production
docker-compose --profile prod up {{SERVICE_NAME}}
```

**Features**:
- Optimized logging
- Metrics and tracing
- Rate limiting
- Security hardening

**Configuration**:
```yaml
profile: production
log_level: info
features:
  - metrics
  - tracing
  - rate_limiting
  - security_headers
performance:
  workers: 4
  timeout: 30
```

---

## 🐳 Docker Configuration

### Dockerfile

**Location**: `./Dockerfile`

**Build**:
```bash
docker build -t {{SERVICE_NAME}}:latest .
```

**Run**:
```bash
docker run -p {{HTTP_PORT}}:{{HTTP_PORT}} {{SERVICE_NAME}}:latest
```

### Docker Compose

**Location**: `./docker-compose.yml`

**Run standalone**:
```bash
docker-compose up {{SERVICE_NAME}}
```

**Run with ecosystem**:
```bash
# From root directory
docker-compose --profile dev up
```

### Docker Profiles

| Profile | Purpose | Command |
|---------|---------|---------|
| `dev` | Development | `docker-compose --profile dev up` |
| `prod` | Production | `docker-compose --profile prod up` |
| `testing` | Testing | `docker-compose --profile testing up` |

---

## ✅ Validation

### Preflight Checks

Run validation before starting service:

```bash
# Validate all configuration
make validate-config

# Check port availability
make check-ports

# Validate environment
make validate-env

# Validate YAML
make validate-yaml
```

### Manual Validation

```bash
# Check port conflicts
python ../../scripts/validation/check_port_conflicts.py {{SERVICE_NAME}} {{HTTP_PORT}}

# Validate config.yaml
yamllint config.yaml

# Test configuration loading
python -c "from config import load_config; load_config()"
```

### Health Checks

```bash
# Service health
curl http://localhost:{{HTTP_PORT}}/health

# Readiness check
curl http://localhost:{{HTTP_PORT}}/ready

# Service info
curl http://localhost:{{HTTP_PORT}}/about-me
```

---

## 🔧 Troubleshooting

### Common Issues

#### Port Already in Use

**Error**: `Address already in use`

**Solution**:
```bash
# Find process using port
lsof -i :{{HTTP_PORT}}

# Kill process or change port in config
```

#### Missing Credentials

**Error**: `Environment variable XYZ not set`

**Solution**:
```bash
# Check .env file exists
ls -la .env

# Verify variables are set
grep XYZ .env

# Copy from template if missing
cp .env.template .env
```

#### Service Won't Start

**Steps**:
1. Check logs: `docker logs {{SERVICE_NAME}}`
2. Validate config: `make validate-config`
3. Check dependencies: Ensure Redis, etc. are running
4. Check port conflicts: `make check-ports`

### Debug Mode

**Enable debug logging**:
```bash
export LOG_LEVEL=debug
python main.py
```

**Docker debug**:
```bash
docker-compose --profile dev up {{SERVICE_NAME}}
# Debug endpoints available at /debug/*
```

---

## 📚 Related Documentation

- [Master Configuration Registry](../../docs/refactoring/MASTER_CONFIGURATION_REGISTRY.md)
- [Service README](./README.md)
- [API Documentation](./docs/API.md)
- [Deployment Guide](../../docs/refactoring/DEPLOYMENT_GUIDE.md)

---

**Last Updated**: {{DATE}}  
**Maintained by**: Hackathon Team  
**Questions?**: See [Troubleshooting](#troubleshooting) or consult the team

