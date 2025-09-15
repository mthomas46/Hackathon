# Configuration System

## Overview

The LLM Documentation Ecosystem uses a hierarchical configuration system that supports both unified project-wide settings and service-specific overrides. This system provides flexibility for different deployment environments while maintaining consistency.

## Configuration Hierarchy

Configuration values are resolved in the following order (highest to lowest precedence):

1. **Environment Variables** - Runtime overrides
2. **Service-specific config** (`services/{service}/config.yaml`)
3. **Unified project config** (`config.yml`)
4. **Shared base config** (`services/shared/base_config.yaml`)
5. **Defaults** - Built-in fallback values

## File Structure

```
project/
├── config.yml                    # Unified project configuration
├── docker-compose.dev.yml        # Development environment
├── docker-compose.prod.yml       # Production environment
├── services/
│   ├── shared/
│   │   ├── base_config.yaml      # Base configuration defaults
│   │   └── config.yaml           # Shared service settings
│   └── {service}/
│       └── config.yaml           # Service-specific overrides
```

## Unified Configuration (`config.yml`)

The `config.yml` file at the project root contains all project-wide settings and is the single source of truth for:

- Infrastructure settings (Redis, PostgreSQL)
- Service URLs and ports
- External API configurations
- AI provider settings
- Global limits and timeouts
- Environment-specific overrides

### Key Sections

#### Project Metadata
```yaml
project:
  name: "LLM Documentation Ecosystem"
  version: "1.0.0"
  environment: development
```

#### Infrastructure
```yaml
redis:
  host: redis
  port: 6379
  maxmemory: 512mb

postgresql:
  enabled: false  # Set to true for production
  host: postgres
  database: doc_consistency

sqlite:
  databases:
    doc_store:
      path: services/doc-store/db.sqlite3
    prompt_store:
      path: /app/data/prompt_store.db
```

#### Service Configuration
```yaml
services:
  orchestrator_url: http://orchestrator:5099
  doc_store_url: http://doc-store:5087
  # ... all service URLs

ports:
  orchestrator: 5099
  doc_store: 5087
  # ... all service ports
```

#### External APIs
```yaml
github:
  api_base: https://api.github.com
  token: ${GITHUB_TOKEN}

aws:
  region: us-east-1
  access_key_id: ${AWS_ACCESS_KEY_ID}
```

#### AI Providers
```yaml
ollama:
  host: http://host.docker.internal:11434
  model: llama3

openai:
  api_key: ${OPENAI_API_KEY}
  model: gpt-4o
```

## Service-Specific Configuration

Each service can override global settings in its `services/{service}/config.yaml`:

```yaml
# services/analysis-service/config.yaml
server:
  port: 5020

analysis:
  drift_overlap_threshold: 0.1
  critical_score: 90
```

## Environment Variables

All configuration values can be overridden using environment variables with the `${VAR_NAME:-default}` syntax.

### Common Environment Variables

```bash
# Infrastructure
REDIS_HOST=localhost
REDIS_PORT=6379
POSTGRES_HOST=localhost
POSTGRES_DB=doc_consistency

# External APIs
GITHUB_TOKEN=your_token_here
OPENAI_API_KEY=your_key_here
AWS_REGION=us-east-1

# Service Configuration
ENVIRONMENT=production
LOG_LEVEL=WARNING
DEBUG=false
```

## Docker Compose Integration

### Development Environment

```bash
# Start core services only
docker-compose --profile core up

# Start with AI services
docker-compose --profile ai_services up

# Start everything
docker-compose up
```

### Production Environment

```bash
# Production deployment
docker-compose -f docker-compose.prod.yml up -d
```

## Configuration Loading

Services load configuration through the shared `config.py` module:

```python
from services.shared.config import get_config_value

# Get a simple value
redis_host = get_config_value("REDIS_HOST", "redis")

# Get from a section
service_url = get_config_value("url", section="services", env_key="ORCHESTRATOR_URL")
```

## Environment-Specific Configuration

The unified config supports environment-specific overrides:

```yaml
environments:
  development:
    redis:
      host: redis
    ollama:
      host: http://host.docker.internal:11434
    debug: true

  production:
    redis:
      host: redis-cluster
    postgresql:
      enabled: true
    debug: false
```

## Validation

All YAML configuration files are validated for syntax correctness. Run validation:

```bash
# Validate all config files
find services -name "config.yaml" -exec python3 -c "import yaml; yaml.safe_load(open('{}'))" \;

# Validate unified config
python3 -c "import yaml; yaml.safe_load(open('config.yml'))"
```

## Migration Guide

### From Individual Configs to Unified Config

1. **Backup existing configs**
2. **Copy service-specific settings** to `services/{service}/config.yaml`
3. **Move global settings** to `config.yml`
4. **Update environment variables** to use unified naming
5. **Test configuration loading** in each service

### Legacy Support

The system maintains backward compatibility with:
- `config/app.yaml` (legacy global config)
- Individual service configs
- Environment variable overrides

## Best Practices

### Configuration Management

1. **Use environment variables** for secrets and environment-specific values
2. **Keep service configs minimal** - only override what's necessary
3. **Document configuration options** in service READMEs
4. **Validate configs** before deployment
5. **Version control** configuration files

### Security

1. **Never commit secrets** to version control
2. **Use environment variables** for sensitive data
3. **Restrict file permissions** on config files
4. **Audit configuration changes** regularly

### Performance

1. **Cache configuration values** after loading
2. **Use appropriate timeouts** for external services
3. **Configure connection pooling** for databases
4. **Monitor configuration impact** on startup time

## Troubleshooting

### Common Issues

1. **Configuration not loading**
   - Check file permissions
   - Verify YAML syntax
   - Check environment variables

2. **Service can't connect**
   - Verify service URLs in config
   - Check network configuration
   - Validate port mappings

3. **Environment overrides not working**
   - Check variable naming
   - Verify variable is set
   - Check for typos in variable names

### Debugging

Enable debug logging to troubleshoot configuration issues:

```bash
LOG_LEVEL=DEBUG docker-compose up
```

Check loaded configuration:

```python
from services.shared.config import _load_app_config
config = _load_app_config()
print(config)
```

## Monitoring Infrastructure

### Current State

The project includes basic health checks for all services, but advanced monitoring infrastructure (Jaeger, Prometheus, Grafana, Elasticsearch, Kibana) is **planned but not fully implemented**.

### What's Available

- **Service Health Checks**: All services have `/health` endpoints
- **Basic Redis Monitoring**: Via `redis-cli` commands
- **SQLite Maintenance**: Standard SQLite optimization commands

### What's Planned (Not Yet Functional)

The `docker-compose.infrastructure.yml` file defines advanced monitoring services, but they require additional configuration files:

- `infrastructure/prometheus.yml` - Prometheus configuration
- `infrastructure/grafana/dashboards/` - Grafana dashboard configs
- `infrastructure/grafana/datasources/` - Grafana data source configs
- `infrastructure/logstash.conf` - Logstash pipeline configuration

### To Enable Full Monitoring

1. Create the missing configuration files in `infrastructure/`
2. Uncomment monitoring services in `docker-compose.prod.yml`
3. Update `config.yml` monitoring section with full configurations

## Examples

### Development Setup

```bash
# Set environment variables
export ENVIRONMENT=development
export REDIS_HOST=localhost
export GITHUB_TOKEN=your_token

# Start services
docker-compose --profile core up
```

### Individual Service Development

Each service can run independently with its own dependencies. Every service has its own `docker-compose.yml` file:

```bash
# Run any service individually with its dependencies
cd services/{service-name} && docker-compose up

# Examples:
cd services/orchestrator && docker-compose up      # + Redis
cd services/doc-store && docker-compose up         # + Redis + SQLite
cd services/frontend && docker-compose up          # Standalone
cd services/prompt-store && docker-compose up      # + SQLite
```

**Service Categories by Dependencies:**

**Redis + SQLite services:**
- `doc-store` - Redis for caching, SQLite for document storage

**Redis-only services:**
- `orchestrator`, `analysis-service`, `source-agent`, `memory-agent`, `code-analyzer`

**SQLite-only services:**
- `prompt-store` - SQLite for prompt storage

**Standalone services (no external dependencies):**
- `frontend`, `bedrock-proxy`, `github-mcp`, `notification-service`, `log-collector`, `discovery-agent`, `interpreter`, `cli`, `secure-analyzer`, `summarizer-hub`

### Production Setup

```bash
# Use production config
export ENVIRONMENT=production
export REDIS_HOST=redis-cluster
export USE_POSTGRESQL=true

# Deploy
docker-compose -f docker-compose.prod.yml up -d
```

### Custom Configuration

```bash
# Use custom config file
export APP_CONFIG_PATH=/path/to/custom/config.yml
docker-compose up
```
