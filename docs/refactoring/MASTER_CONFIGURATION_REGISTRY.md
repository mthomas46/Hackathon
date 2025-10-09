<!-- AI_READ_PRIORITY: 2 -->
<!-- AI_TAGS: configuration, ports, credentials, profiles, deployment, registry -->
<!-- AI_KEY_SECTIONS: Port Matrix, Credentials Registry, Config Standards, Profiles, Deployment -->

---
ai_metadata:
  purpose: configuration_registry
  read_priority: 2
  context_level: operational
  tags:
  - configuration
  - ports
  - credentials
  - profiles
  - deployment
  - registry
  when_to_read: Before and during Phase 2 (Design & Planning) and Phase 6 (Deployment)
  key_sections:
  - Master Port & Network Matrix
  - Credentials & API Keys Registry
  - Configuration File Standards
  - Service Config Profiles
  - Docker & Docker Compose Profiles
  - CI/CD & Deployment Strategies
  - Scripts & Makefiles Registry
  execution_relevance: critical
  update_frequency: Per service refactored
---

# 🔧 Master Configuration Registry

**Version**: 1.0.0  
**Created**: October 9, 2025  
**Last Updated**: October 9, 2025  
**Status**: Living Document - Updated Per Service  
**Owner**: Hackathon Team

---

## 📋 Table of Contents

1. [Purpose & Usage](#purpose--usage)
2. [Master Port & Network Matrix](#master-port--network-matrix)
3. [Credentials & API Keys Registry](#credentials--api-keys-registry)
4. [Configuration File Standards](#configuration-file-standards)
5. [Service Config Profiles](#service-config-profiles)
6. [Docker & Docker Compose Profiles](#docker--docker-compose-profiles)
7. [CI/CD & Deployment Strategies](#cicd--deployment-strategies)
8. [Scripts & Makefiles Registry](#scripts--makefiles-registry)
9. [AI Agent Integration](#ai-agent-integration)

---

## 🎯 Purpose & Usage

### What This Document Does

This is a **living registry** that tracks all configuration-related information across the entire microservices ecosystem. It serves as:

1. **Single Source of Truth** for ports, credentials, and config standards
2. **Conflict Prevention** tool (port conflicts, credential overlap)
3. **Configuration Guide** for AI agents refactoring services
4. **Documentation Template** source for per-service config docs
5. **Validation Reference** for preflight checks

### When AI Agents Use This

**REQUIRED Reading**:
- ✅ **Phase 1.1** (Service Audit): Check existing port/config
- ✅ **Phase 2.2** (API Design): Allocate ports, plan configs
- ✅ **Phase 6.1** (Deployment): Configure deployment
- ✅ **After ANY config change**: Update this registry

**Usage Pattern**:
```
1. READ this registry (check for conflicts)
2. UPDATE this registry (add/modify service entries)
3. GENERATE per-service config docs (based on this)
4. CREATE preflight checks (validate config)
5. RUN preflight checks (confirm working)
6. COMMIT changes (registry + service docs)
```

---

## 🌐 Master Port & Network Matrix

### Purpose
Track all port assignments across all services to prevent conflicts and enable proper networking configuration.

### Port Allocation Strategy

| Port Range | Purpose | Notes |
|------------|---------|-------|
| 3000-3999 | Frontend/UI Services | User-facing applications |
| 5000-5999 | Core Backend Services | Business logic services |
| 6000-6999 | Analysis Services | Code analysis, processing |
| 7000-7999 | Integration Services | External integrations |
| 8000-8999 | Infrastructure Services | Redis, databases, etc. |
| 9000-9999 | MCP Services | Model Context Protocol services |

### Service Port Registry

<!-- AI_SECTION: port_registry -->
<!-- AI_UPDATE: Add entry when refactoring a service -->

| Service Name | HTTP Port | Internal Port | gRPC Port | Admin Port | Status | Notes |
|--------------|-----------|---------------|-----------|------------|--------|-------|
| **Frontend Services** |
| frontend | 3000 | - | - | - | ✅ Active | React UI |
| cli | - | - | - | - | ✅ Active | Terminal only |
| unified-api-dashboard | 3001 | - | - | - | ✅ Active | API dashboard |
| simulation-dashboard | 3002 | - | - | - | ✅ Active | Simulation UI |
| data-services-dashboard | 3003 | - | - | - | ✅ Active | Data services UI |
| **Core Services** |
| orchestrator | 5000 | 5001 | - | 5099 | ✅ Active | Central coordinator |
| analysis-service | 5010 | 5011 | - | - | ✅ Active | Analysis orchestrator |
| llm-gateway | 5020 | 5021 | - | - | ✅ Active | LLM routing |
| prompt_store | 5030 | 5031 | - | - | 🔄 Refactor | Prompt management |
| source-agent | 5040 | 5041 | - | - | 🔄 Refactor | Source code agent |
| discovery-agent | 5050 | 5051 | - | - | 🔄 Refactor | Service discovery |
| memory-agent | 5060 | 5061 | - | - | 🔄 Refactor | Memory management |
| **Analysis Services** |
| code-analyzer | 6000 | 6001 | - | - | ✅ Refactored | Code analysis (v2 API) |
| secure-analyzer | 6010 | 6011 | - | - | 🔄 Refactor | Security analysis |
| architecture-digitizer | 6020 | 6021 | - | - | 🔄 Refactor | Architecture mapping |
| summarizer-hub | 6030 | 6031 | - | - | 🔄 Refactor | Content summarization |
| mock-data-generator | 6040 | 6041 | - | - | 🔄 Refactor | Mock data generation |
| **Integration Services** |
| github-mcp | 7000 | 7001 | - | - | 🔄 Refactor | GitHub integration |
| bedrock-proxy | 7010 | 7011 | - | - | 🔄 Refactor | AWS Bedrock proxy |
| interpreter | 7020 | 7021 | - | - | 🔄 Refactor | Code interpreter |
| log-collector | 7030 | 7031 | - | - | 🔄 Refactor | Log aggregation |
| notification-service | 7040 | 7041 | - | - | 🔄 Refactor | Notifications |
| **Infrastructure Services** |
| redis | 6379 | - | - | - | ✅ Active | Cache & messaging |
| doc_store | 8000 | 8001 | - | - | 🔄 Refactor | Document storage |
| user-store | 8010 | 8011 | - | - | 🔄 Refactor | User data |
| **MCP Services** |
| mcp-* | 9000-9999 | - | - | - | 🔄 Refactor | 13 MCP services |

<!-- /AI_SECTION -->

### Port Conflict Detection

**Automated Check**:
```bash
# Run this before assigning a new port
make check-port-conflicts
```

**Manual Check**:
```bash
# Check if port is in use
lsof -i :<port_number>

# Check port in registry
grep "<port_number>" docs/refactoring/MASTER_CONFIGURATION_REGISTRY.md
```

### Network Configuration

| Network Name | Purpose | Subnet | Services |
|--------------|---------|--------|----------|
| hackathon_default | Main service network | 172.20.0.0/16 | All services |
| hackathon_frontend | Frontend network | 172.21.0.0/16 | UI services |
| hackathon_backend | Backend network | 172.22.0.0/16 | Core services |
| hackathon_data | Data network | 172.23.0.0/16 | Storage services |

---

## 🔑 Credentials & API Keys Registry

### Purpose
Track which services require credentials, API keys, or secrets for operation.

<!-- AI_SECTION: credentials_registry -->
<!-- AI_UPDATE: Mark services requiring credentials -->

### Services Requiring Credentials

| Service | Credential Type | Environment Variable | Required | Notes |
|---------|----------------|---------------------|----------|-------|
| **LLM Services** |
| llm-gateway | API Key | `LLM_API_KEY` | ✅ Yes | OpenAI/Anthropic |
| bedrock-proxy | AWS Credentials | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | ✅ Yes | AWS Bedrock |
| **Integration Services** |
| github-mcp | GitHub Token | `GITHUB_TOKEN` | ✅ Yes | GitHub API access |
| notification-service | SMTP/API Keys | `SMTP_PASSWORD`, `SLACK_WEBHOOK` | ⚠️ Optional | Email/Slack |
| **Infrastructure Services** |
| redis | Password | `REDIS_PASSWORD` | ⚠️ Optional | If auth enabled |
| doc_store | DB Credentials | `DB_USER`, `DB_PASSWORD` | ✅ Yes | PostgreSQL |
| user-store | DB Credentials | `DB_USER`, `DB_PASSWORD` | ✅ Yes | PostgreSQL |
| **Analysis Services** |
| code-analyzer | - | - | ❌ No | Self-contained |
| secure-analyzer | - | - | ❌ No | Self-contained |

<!-- /AI_SECTION -->

### Credential Management Strategy

**Development**:
```bash
# Use .env files (gitignored)
cp .env.template .env
# Edit .env with actual credentials
```

**Production**:
```bash
# Use secrets management
# - Docker Secrets
# - Kubernetes Secrets
# - AWS Secrets Manager
# - HashiCorp Vault
```

### Secret Templates

**Location**: `config/.env.template`

```bash
# LLM Services
LLM_API_KEY=your_api_key_here
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret

# Integration Services
GITHUB_TOKEN=your_github_token

# Infrastructure
REDIS_PASSWORD=your_redis_password
DB_USER=your_db_user
DB_PASSWORD=your_db_password
```

---

## 📄 Configuration File Standards

### Purpose
Standardize configuration across different file formats to maintain consistency.

### File Types & Standards

<!-- AI_SECTION: config_standards -->

#### 1. YAML Files (.yaml, .yml)

**Used For**: Docker Compose, OpenAPI specs, CI/CD configs

**Standard Structure**:
```yaml
# Service: <service-name>
# Purpose: <what this configures>
# Last Updated: <date>
# AI_TAGS: <relevant-tags>

version: "3.8"  # For docker-compose

# Top-level keys (alphabetical)
services:
  <service-name>:
    # Required fields first
    image: <image>
    ports:
      - "<external>:<internal>"
    
    # Optional fields
    environment:
      - KEY=value
    
    # Dependencies last
    depends_on:
      - <service>
```

**Naming Conventions**:
- Keys: `snake_case`
- Service names: `kebab-case`
- Environment variables: `UPPER_SNAKE_CASE`

#### 2. Environment Files (.env)

**Used For**: Environment-specific configuration

**Standard Structure**:
```bash
# ============================================
# Service: <service-name>
# Environment: <dev/staging/prod>
# Last Updated: <date>
# ============================================

# === Core Configuration ===
SERVICE_NAME=<name>
SERVICE_PORT=<port>
LOG_LEVEL=info

# === Feature Flags ===
ENABLE_FEATURE_X=true

# === Credentials (use secrets in prod) ===
API_KEY=${API_KEY:-default_dev_key}

# === Dependencies ===
REDIS_URL=redis://redis:6379
```

**Naming Conventions**:
- Variables: `UPPER_SNAKE_CASE`
- Sections: Marked with `===`
- Defaults: Use `${VAR:-default}` syntax

#### 3. Dockerfile

**Standard Structure**:
```dockerfile
# Service: <service-name>
# Base Image: python:3.11-slim
# Last Updated: <date>

# === Build Stage ===
FROM python:3.11-slim AS builder

WORKDIR /app

# Dependencies first (cache layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# === Runtime Stage ===
FROM python:3.11-slim

WORKDIR /app

# Copy from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# Copy application
COPY . .

# Standard labels
LABEL service="<service-name>"
LABEL version="<version>"
LABEL maintainer="<team>"

# Standard health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:<port>/health || exit 1

# Run as non-root
USER nobody

# Standard entrypoint
ENTRYPOINT ["python", "main.py"]
```

#### 4. Docker Compose (docker-compose.yml)

**Standard Structure**:
```yaml
version: "3.8"

# === Services ===
services:
  <service-name>:
    # Build or image
    build:
      context: ./services/<service-name>
      dockerfile: Dockerfile
    
    # Container name
    container_name: <service-name>
    
    # Ports (external:internal)
    ports:
      - "<external>:<internal>"
    
    # Environment
    environment:
      - SERVICE_NAME=<name>
      - LOG_LEVEL=${LOG_LEVEL:-info}
    
    # Or env file
    env_file:
      - ./services/<service-name>/.env
    
    # Volumes
    volumes:
      - ./services/<service-name>:/app
      - /app/venv  # Exclude venv
    
    # Networks
    networks:
      - hackathon_default
    
    # Dependencies
    depends_on:
      - redis
    
    # Health check
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:<port>/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    
    # Restart policy
    restart: unless-stopped

# === Networks ===
networks:
  hackathon_default:
    driver: bridge

# === Volumes ===
volumes:
  redis_data:
```

#### 5. Config Files (config.yaml, app.yaml)

**Standard Structure**:
```yaml
# Service: <service-name>
# Purpose: Application configuration
# Last Updated: <date>

# === Service Identity ===
service:
  name: <service-name>
  version: "1.0.0"
  description: "<description>"

# === Server Configuration ===
server:
  host: "0.0.0.0"
  port: ${PORT:-5000}
  workers: ${WORKERS:-4}

# === Logging ===
logging:
  level: ${LOG_LEVEL:-info}
  format: json
  output: stdout
  
# === Features ===
features:
  enable_metrics: true
  enable_tracing: true
  
# === Dependencies ===
dependencies:
  redis:
    url: ${REDIS_URL:-redis://localhost:6379}
    pool_size: 10
```

<!-- /AI_SECTION -->

### Validation

**Automated Checks**:
```bash
# Validate all configs
make validate-configs

# Validate specific type
make validate-yaml
make validate-env
make validate-docker
```

---

## 🎛️ Service Config Profiles

### Purpose
Document different configuration profiles for each service (dev, test, staging, prod).

<!-- AI_SECTION: service_profiles -->
<!-- AI_UPDATE: Add profile info when refactoring a service -->

### Profile Structure

Each service should support multiple profiles:

| Profile | Purpose | Config Source | Features |
|---------|---------|---------------|----------|
| **development** | Local development | `.env.dev` | Debug logging, hot reload, mock services |
| **testing** | Automated tests | `.env.test` | In-memory DBs, test fixtures, minimal logging |
| **staging** | Pre-production | `.env.staging` | Production-like, test data, monitoring |
| **production** | Live system | Secrets manager | Full monitoring, backups, high availability |

### Per-Service Profiles

#### Template

```yaml
service: <service-name>
profiles:
  development:
    port: <dev-port>
    log_level: debug
    features:
      - hot_reload
      - debug_endpoints
    dependencies:
      - redis (local)
  
  testing:
    port: <test-port>
    log_level: warning
    features:
      - in_memory_cache
      - test_fixtures
    dependencies:
      - redis (mock)
  
  staging:
    port: <staging-port>
    log_level: info
    features:
      - monitoring
      - tracing
    dependencies:
      - redis (staging)
  
  production:
    port: <prod-port>
    log_level: warning
    features:
      - monitoring
      - tracing
      - alerts
      - backups
    dependencies:
      - redis (prod cluster)
```

#### Example: code-analyzer

```yaml
service: code-analyzer
profiles:
  development:
    port: 6000
    log_level: debug
    features:
      - swagger_ui
      - debug_endpoints
      - sample_data
    performance:
      workers: 2
      timeout: 300  # Longer for debugging
  
  testing:
    port: 0  # Random available port
    log_level: error
    features:
      - test_mode
    performance:
      workers: 1
      timeout: 10
  
  production:
    port: 6000
    log_level: info
    features:
      - metrics
      - tracing
      - rate_limiting
    performance:
      workers: 4
      timeout: 30
```

<!-- /AI_SECTION -->

---

## 🐳 Docker & Docker Compose Profiles

### Purpose
Manage different Docker deployment scenarios using profiles.

<!-- AI_SECTION: docker_profiles -->

### Docker Compose Profile Strategy

```yaml
# docker-compose.yml with profiles

services:
  # === Core Services (always run) ===
  redis:
    image: redis:7-alpine
    # No profile = always runs
  
  orchestrator:
    build: ./services/orchestrator
    # No profile = always runs
  
  # === Development Tools ===
  swagger-ui:
    image: swaggerapi/swagger-ui
    profiles: ["dev", "docs"]
  
  # === Analysis Services ===
  code-analyzer:
    build: ./services/code-analyzer
    profiles: ["analysis", "dev", "prod"]
  
  # === Monitoring (optional) ===
  prometheus:
    image: prom/prometheus
    profiles: ["monitoring", "prod"]
  
  grafana:
    image: grafana/grafana
    profiles: ["monitoring", "prod"]
```

### Standard Profiles

| Profile | Purpose | Services Included | Usage |
|---------|---------|-------------------|-------|
| **dev** | Development | Core + Dev tools + All services | `docker-compose --profile dev up` |
| **prod** | Production | Core + Production services + Monitoring | `docker-compose --profile prod up` |
| **analysis** | Analysis only | Core + Analysis services | `docker-compose --profile analysis up` |
| **monitoring** | With monitoring | All + Prometheus/Grafana | `docker-compose --profile monitoring up` |
| **minimal** | Minimal setup | Core services only | `docker-compose up` (no profile) |

### Usage Examples

```bash
# Development (all services + tools)
docker-compose --profile dev up

# Production (core + prod services + monitoring)
docker-compose --profile prod --profile monitoring up

# Analysis services only
docker-compose --profile analysis up

# Minimal (just core)
docker-compose up
```

<!-- /AI_SECTION -->

---

## 🚀 CI/CD & Deployment Strategies

### Purpose
Document standard deployment patterns and CI/CD configurations.

<!-- AI_SECTION: deployment_strategies -->

### Deployment Models

#### 1. Local Development

**Tools**: Docker Compose  
**Command**: `docker-compose --profile dev up`

**Features**:
- Hot reload
- Debug endpoints
- Local volumes
- Development credentials

#### 2. Testing (CI)

**Tools**: GitHub Actions, pytest, Docker  
**Trigger**: On PR, push to main

**Pipeline**:
```yaml
# .github/workflows/test.yml
name: Test Service

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
      - name: Install dependencies
        run: pip install -r requirements-test.txt
      - name: Run tests
        run: pytest --cov=. --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

#### 3. Staging Deployment

**Tools**: Docker, Docker Compose  
**Trigger**: Manual or on merge to `develop`

**Process**:
```bash
# Build with staging profile
docker-compose -f docker-compose.staging.yml build

# Deploy to staging
docker-compose -f docker-compose.staging.yml up -d

# Run smoke tests
make smoke-test-staging
```

#### 4. Production Deployment

**Tools**: Docker, Kubernetes (future), Blue-Green deployment  
**Trigger**: Manual approval on merge to `main`

**Process**:
```bash
# Build production image
docker build -t <service>:latest .

# Tag with version
docker tag <service>:latest <service>:v1.0.0

# Push to registry
docker push <service>:v1.0.0

# Deploy (blue-green)
# 1. Deploy new version (green)
# 2. Health check green
# 3. Switch traffic to green
# 4. Deprecate blue after validation
```

### Standard CI/CD Config per Service

**Required Files**:
```
service/
├── .github/
│   └── workflows/
│       ├── test.yml           # Run tests on PR
│       ├── build.yml          # Build Docker image
│       └── deploy.yml         # Deploy to staging/prod
├── Dockerfile                 # Production image
├── Dockerfile.dev             # Development image
├── docker-compose.yml         # Local development
├── docker-compose.test.yml    # Testing
├── docker-compose.staging.yml # Staging
└── Makefile                   # Common commands
```

<!-- /AI_SECTION -->

---

## 📜 Scripts & Makefiles Registry

### Purpose
Track all scripts and Makefiles, their purpose, and relationship to services.

<!-- AI_SECTION: scripts_registry -->

### Script Categories

#### 1. Refactoring Scripts

**Location**: `scripts/refactoring/`

| Script | Purpose | When to Use | Relationship |
|--------|---------|-------------|--------------|
| `init_ai_execution.py` | Initialize execution context | Start of Phase 1 | Ecosystem-wide |
| `update_execution_context.py` | Update progress | After each step | Current service |
| `audit_service.py` | Audit service structure | Phase 1.1 | Target service |
| `generate_dependency_map.py` | Map dependencies | Phase 1.2 | Target service |
| `validate_step_reality.py` | Validate completion | Any step completion | Current service |

#### 2. Service-Specific Makefiles

**Location**: `services/<service>/Makefile`

**Standard Targets**:
```makefile
# Service: <service-name>
# Generated during refactoring

.PHONY: help install test run clean

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install dependencies
	pip install -r requirements.txt

test:  ## Run tests
	pytest tests/ -v --cov=.

run:  ## Run service locally
	python main.py

run-docker:  ## Run in Docker
	docker-compose up <service-name>

validate-config:  ## Validate configuration
	@echo "Checking port conflicts..."
	@python ../../scripts/validation/check_port_conflicts.py
	@echo "Validating YAML..."
	@yamllint *.yaml
	@echo "Validating environment..."
	@python ../../scripts/validation/validate_env.py

lint:  ## Run linters
	pylint *.py
	black --check .

format:  ## Format code
	black .

clean:  ## Clean up
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
```

#### 3. Ecosystem Makefiles

**Location**: `Makefile` (root)

**Standard Targets**:
```makefile
# Ecosystem-wide Makefile

.PHONY: help

help:  ## Show help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# === Configuration Validation ===
check-port-conflicts:  ## Check for port conflicts
	@python scripts/validation/check_port_conflicts.py

validate-configs:  ## Validate all configs
	@python scripts/validation/validate_all_configs.py

validate-yaml:  ## Validate YAML files
	@find . -name "*.yaml" -o -name "*.yml" | xargs yamllint

validate-docker:  ## Validate Dockerfiles
	@find services -name "Dockerfile" | xargs hadolint

# === Service Management ===
start-all:  ## Start all services
	docker-compose --profile dev up -d

stop-all:  ## Stop all services
	docker-compose down

restart-service:  ## Restart specific service (usage: make restart-service SERVICE=<name>)
	docker-compose restart $(SERVICE)

# === Testing ===
test-all:  ## Run all tests
	@for dir in services/*/; do \
		if [ -f $$dir/Makefile ]; then \
			echo "Testing $$dir..."; \
			$(MAKE) -C $$dir test || exit 1; \
		fi \
	done

# === Refactoring ===
refactor-service:  ## Start refactoring a service (usage: make refactor-service SERVICE=<name>)
	@python scripts/refactoring/init_ai_execution.py --service $(SERVICE)
```

### Script Relationship Matrix

| Script/Makefile | Scope | Services Affected | Config Files Used |
|-----------------|-------|-------------------|-------------------|
| Root Makefile | Ecosystem | All | docker-compose.yml, all service configs |
| Service Makefile | Single service | One | Service .env, config.yaml |
| Refactoring scripts | Single service | One + dependencies | MASTER_CONFIGURATION_REGISTRY.md |
| Validation scripts | Ecosystem or service | All or one | All configs |

<!-- /AI_SECTION -->

---

## 🤖 AI Agent Integration

### How AI Agents Use This Registry

<!-- AI_SECTION: ai_integration -->

### 1. Read Pattern

**When**: Start of Phase 1.1 (Service Audit) and Phase 2.2 (API Design)

```python
# AI Agent reads this registry
registry = read_file("docs/refactoring/MASTER_CONFIGURATION_REGISTRY.md")

# Extract relevant sections
ports_in_use = extract_section(registry, "port_registry")
credentials_needed = extract_section(registry, "credentials_registry")
config_standards = extract_section(registry, "config_standards")
```

### 2. Update Pattern

**When**: After any configuration decision or change

```python
# AI Agent updates registry
def update_port_registry(service_name, http_port, internal_port):
    """Update port registry with new service."""
    registry = read_file("docs/refactoring/MASTER_CONFIGURATION_REGISTRY.md")
    
    # Check for conflicts
    if port_in_use(http_port, registry):
        raise PortConflictError(f"Port {http_port} already in use")
    
    # Add new entry
    new_entry = f"| {service_name} | {http_port} | {internal_port} | - | - | ✅ Refactored | <notes> |"
    registry = insert_into_section(registry, "port_registry", new_entry)
    
    # Save
    write_file("docs/refactoring/MASTER_CONFIGURATION_REGISTRY.md", registry)
    
    # Log update
    log(f"Updated port registry: {service_name} -> {http_port}")
```

### 3. Generate Per-Service Docs

**When**: Phase 2.2 (API Design) or Phase 5.1 (Documentation)

```python
# AI Agent generates service-specific config docs
def generate_service_config_docs(service_name):
    """Generate CONFIG.md for a service based on registry."""
    registry = read_file("docs/refactoring/MASTER_CONFIGURATION_REGISTRY.md")
    
    # Extract service-specific info
    service_ports = extract_service_ports(registry, service_name)
    service_credentials = extract_service_credentials(registry, service_name)
    config_standards = extract_section(registry, "config_standards")
    
    # Generate CONFIG.md
    config_doc = f"""
<!-- AI_READ_PRIORITY: 3 -->
<!-- AI_TAGS: configuration, {service_name}, ports, credentials -->

# {service_name} Configuration

## Ports

{service_ports}

## Credentials

{service_credentials}

## Configuration Files

{config_standards}

## Profiles

{extract_service_profiles(registry, service_name)}

## Validation

Run preflight checks:
```bash
make validate-config
```
"""
    
    write_file(f"services/{service_name}/CONFIG.md", config_doc)
    log(f"Generated CONFIG.md for {service_name}")
```

### 4. Create Preflight Checks

**When**: Phase 2.2 (API Design)

```python
# AI Agent creates service-specific Makefile
def create_preflight_makefile(service_name):
    """Create Makefile with validation targets."""
    registry = read_file("docs/refactoring/MASTER_CONFIGURATION_REGISTRY.md")
    
    makefile = f"""
# Makefile for {service_name}
# Generated from MASTER_CONFIGURATION_REGISTRY.md

.PHONY: validate-config

validate-config:  ## Validate configuration
\t@echo "Validating {service_name} configuration..."
\t@python ../../scripts/validation/check_port_conflicts.py {service_name}
\t@yamllint config.yaml
\t@python ../../scripts/validation/validate_env.py .env
\t@echo "✅ Configuration valid"
"""
    
    write_file(f"services/{service_name}/Makefile", makefile)
    log(f"Created Makefile for {service_name}")
```

### 5. Run Preflight Checks

**When**: After creating preflight checks, before marking step complete

```python
# AI Agent runs validation
def run_preflight_checks(service_name):
    """Run preflight checks to validate config."""
    result = subprocess.run(
        ["make", "-C", f"services/{service_name}", "validate-config"],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        raise ValidationError(f"Preflight checks failed:\n{result.stderr}")
    
    log(f"✅ Preflight checks passed for {service_name}")
    return True
```

### AI Agent Workflow

```
┌─────────────────────────────────────────┐
│ Phase 1.1: Service Audit                │
├─────────────────────────────────────────┤
│ 1. READ MASTER_CONFIGURATION_REGISTRY   │
│ 2. Extract existing config              │
│ 3. Document findings                    │
└─────────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────┐
│ Phase 2.2: API Design                   │
├─────────────────────────────────────────┤
│ 1. READ registry (check port conflicts) │
│ 2. Allocate port from available range   │
│ 3. UPDATE registry with new port        │
│ 4. GENERATE CONFIG.md for service       │
│ 5. CREATE Makefile with validation      │
│ 6. RUN preflight checks                 │
│ 7. If pass, mark step complete          │
│ 8. If fail, fix issues and retry        │
└─────────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────┐
│ Phase 5.1: Documentation                │
├─────────────────────────────────────────┤
│ 1. READ registry for service info       │
│ 2. UPDATE CONFIG.md with full details   │
│ 3. Add deployment instructions          │
│ 4. Add profile documentation            │
└─────────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────┐
│ Phase 6: Deployment                     │
├─────────────────────────────────────────┤
│ 1. READ registry for deployment config  │
│ 2. Use deployment strategies            │
│ 3. Validate with preflight checks       │
│ 4. Deploy to target environment         │
└─────────────────────────────────────────┘
```

<!-- /AI_SECTION -->

---

## 📊 Update Log

### October 9, 2025

**Initial Version**:
- Created Master Configuration Registry
- Defined port allocation strategy
- Established configuration file standards
- Documented profile system
- Created AI agent integration patterns

**Services Registered**:
- code-analyzer (first refactored service with v1.1.0)

---

## ✅ Validation Checklist

Before marking configuration complete for a service:

- [ ] Port assigned and added to Port Matrix
- [ ] Port conflict check passed
- [ ] Credentials documented (if required)
- [ ] Config files follow standards
- [ ] Profiles defined (dev, test, prod)
- [ ] Docker configuration created
- [ ] Makefile with validation targets created
- [ ] CONFIG.md generated for service
- [ ] Preflight checks run and passed
- [ ] Registry updated with service info

---

**This is a living document. Update it every time you refactor a service!**

---

**AI Agents**: See [AI_AGENT_EXECUTION_GUIDE.md](./AI_AGENT_EXECUTION_GUIDE.md) for detailed integration instructions.

