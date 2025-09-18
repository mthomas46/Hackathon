# Docker Standardization Guide

## Overview

This guide introduces a **centralized port management and Docker configuration system** that prevents the port mismatch issues we encountered and provides standardized, maintainable container configurations.

## 🎯 Problems This Solves

### Before (Issues We Faced):
- ❌ Services running on different internal ports than expected
- ❌ Manual port mapping maintenance in multiple files
- ❌ Inconsistent environment variable usage
- ❌ Port conflicts and configuration drift
- ❌ No single source of truth for service configurations

### After (With This System):
- ✅ **Centralized port registry** - Single source of truth
- ✅ **Automated validation** - Catch conflicts before deployment
- ✅ **Standardized templates** - Consistent service configurations
- ✅ **Environment protection** - Prevent configuration errors
- ✅ **Modular composition** - Reusable configuration patterns

---

## 📁 File Structure

```
config/
├── service-ports.yaml              # Central port registry
├── service-ports.env.template      # Environment variables template

scripts/docker/
├── generate-compose.py             # Configuration generator
├── validate-ports.sh               # Port validation script
├── service-targets.mk              # Makefile targets
└── docker-compose-template.yaml    # Standardized templates

docker-compose.dev.yml              # Your existing compose file
```

---

## 🚀 Quick Start

### 1. Validate Current Configuration
```bash
# Check for port conflicts and issues
make validate-ports

# Or run directly:
./scripts/docker/validate-ports.sh
```

### 2. Generate Standardized Configurations
```bash
# Generate all standardized config files
python3 scripts/docker/generate-compose.py
```

### 3. Use Standardized Service Management
```bash
# Start services by category
make start-core        # Core infrastructure
make start-ai          # AI/ML services  
make start-analysis    # Analysis services
make restart-agents    # Restart agent services
```

---

## 📋 Centralized Port Registry

The `config/service-ports.yaml` file is the **single source of truth** for all port assignments:

```yaml
# Example service configuration
ai_services:
  llm_gateway:
    internal_port: 5055    # Port inside container
    external_port: 5055    # Port exposed to host
    description: "LLM routing and management"
```

### Benefits:
- **Conflict Prevention**: Automatic detection of port collisions
- **Documentation**: Each port assignment is documented
- **Validation**: Automated checking of configuration consistency
- **Categorization**: Services grouped by function

---

## 🔧 How to Add a New Service

### 1. Add to Port Registry
```yaml
# In config/service-ports.yaml
ai_services:
  my_new_service:
    internal_port: 5200
    external_port: 5200
    description: "My new AI service"
```

### 2. Use Standardized Template
```yaml
# In docker-compose.dev.yml
my-new-service:
  <<: *ai-service-template
  build:
    context: .
    dockerfile: services/my-new-service/Dockerfile
  environment:
    - SERVICE_PORT=5200  # From port registry
  ports:
    - "5200:5200"        # External:Internal
```

### 3. Validate Configuration
```bash
make validate-ports
```

---

## 🛡️ Protection Mechanisms

### 1. **Port Conflict Detection**
```bash
# Automatically detects:
❌ ERROR: External port 5055 conflict between service1 and service2
⚠️  WARNING: Internal port 5055 conflict between service3 and service4
```

### 2. **Environment Variable Standardization**
```yaml
# Standard variables for all services
environment:
  - SERVICE_PORT=${SERVICE_PORT}    # From port registry
  - ENVIRONMENT=${ENVIRONMENT}      # development/staging/production
  - LOG_LEVEL=${LOG_LEVEL}         # DEBUG/INFO/WARN/ERROR
```

### 3. **Health Check Standardization**
```yaml
# Automatic health check generation
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:5055/health"]
  interval: 30s
  timeout: 10s
  retries: 3
```

---

## 📊 Service Categories

### Core Services (Infrastructure)
- `redis`, `doc_store`, `orchestrator`
- **Port Range**: 6000-6999, 5087, 5099

### AI/ML Services  
- `llm_gateway`, `ollama`, `mock_data_generator`, `summarizer_hub`
- **Port Range**: 5000-5199

### Analysis Services
- `analysis_service`, `code_analyzer`, `secure_analyzer`, `log_collector`
- **Port Range**: 5020-5099

### Agent Services
- `memory_agent`, `discovery_agent`, `source_agent`
- **Port Range**: 5040-5089

### Utility Services
- `prompt_store`, `interpreter`, `architecture_digitizer`
- **Port Range**: 5100-5149

---

## 🔄 Migration from Existing Setup

### Step 1: Audit Current Ports
```bash
# Check what ports services are actually using
docker ps --format "table {{.Names}}\t{{.Ports}}"
docker logs <service-name> | grep "running on"
```

### Step 2: Update Port Registry
```yaml
# Match actual service behavior in service-ports.yaml
analysis_service:
  internal_port: 5020    # What the service actually uses
  external_port: 5080    # What we want to expose
```

### Step 3: Apply Standardized Configuration
```yaml
# Update docker-compose.dev.yml
analysis-service:
  environment:
    - SERVICE_PORT=5080  # Tell service which port to use
  ports:
    - "5080:5020"        # Map external:internal correctly
```

---

## 🚀 Advanced Features

### 1. **Multi-Environment Support**
```bash
# Different configs per environment
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up
```

### 2. **Service Dependencies**
```python
# Automatically generate dependency chains
generator.generate_service_block(
    "my-service",
    dependencies=["redis", "llm-gateway"],
    profiles=["ai_services"]
)
```

### 3. **Configuration Validation**
```bash
# Pre-deployment validation
./scripts/docker/validate-ports.sh
docker-compose config --quiet  # Validate compose syntax
```

---

## 📈 Best Practices

### 1. **Port Assignment Strategy**
- Reserve port ranges by service category
- Use sequential numbering within categories
- Document port usage in the registry
- Avoid common ports (80, 443, 3000, 8080)

### 2. **Environment Variables**
- Use `SERVICE_PORT` for port configuration
- Standardize variable names across services
- Provide sensible defaults
- Document required vs optional variables

### 3. **Health Checks**
- Implement `/health` endpoint in all services
- Use consistent timeout and retry values
- Test health checks during development
- Monitor health check failures

### 4. **Service Organization**
- Group related services in profiles
- Use dependency management for startup order
- Implement graceful shutdown handling
- Plan for horizontal scaling

---

## 🎉 Results

### Immediate Benefits:
- ✅ **Zero port conflicts** - Automated detection prevents issues
- ✅ **Faster debugging** - Centralized configuration reduces confusion
- ✅ **Easier onboarding** - Clear documentation and standards
- ✅ **Reliable deployments** - Validation catches errors early

### Long-term Benefits:
- 🚀 **Scalable architecture** - Easy to add new services
- 🔧 **Maintainable codebase** - Standardized patterns reduce technical debt
- 🛡️ **Reduced errors** - Automated validation prevents misconfigurations
- 📊 **Better monitoring** - Consistent health checks and logging

---

## 🔗 Integration Examples

### With CI/CD:
```bash
# In your CI pipeline
- name: Validate Docker Configuration
  run: |
    python3 scripts/docker/generate-compose.py
    make validate-ports
    docker-compose config --quiet
```

### With Monitoring:
```yaml
# Prometheus-compatible health checks
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:5055/health"]
  # Metrics endpoint: http://localhost:5055/metrics
```

### With Development:
```bash
# Quick development commands
make start-ai          # Start AI services only
make restart-analysis  # Restart analysis services
make validate-ports    # Check configuration
```

---

**This standardization system transforms Docker configuration from error-prone manual work into a reliable, automated, and maintainable process.**

*Generated: September 18, 2025*
