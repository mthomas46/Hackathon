# Configuration Management System

## Overview

The LLM Documentation Ecosystem now features a centralized, standardized configuration management system that provides consistent configuration handling across all services. This system eliminates configuration drift, reduces environment variable complexity, and provides type-safe configuration access.

## Architecture

### Core Components

1. **ConfigurationManager**: Central configuration loading and management
2. **BaseServiceConfig**: Standardized configuration schema
3. **ConfigurationValidator**: Validation and error checking
4. **Environment-specific overrides**: Development, staging, and production configurations

### Configuration Hierarchy

Configuration is loaded from multiple sources in the following precedence order (highest to lowest):

1. **Environment Variables** - Runtime overrides
2. **Environment-specific config** - `config.{environment}.yaml`
3. **Service config** - `config.yaml`
4. **Base config** - `services/shared/base_config.yaml`
5. **Defaults** - Built-in default values

## Configuration Schema

### Base Service Configuration

All services inherit from `BaseServiceConfig` which provides:

```python
@dataclass
class BaseServiceConfig:
    # Service metadata
    service_name: str
    service_version: str
    environment: Environment

    # Standard configurations
    server: ServerConfig
    redis: RedisConfig
    logging: LoggingConfig
    services: ServiceDependencies

    # Operational limits
    limits: Dict[str, Any]
    health: Dict[str, Any]
    security: Dict[str, Any]

    # Service-specific configuration
    custom: Dict[str, Any]
```

### Standard Sections

#### Server Configuration
```yaml
server:
  host: ${SERVER_API_HOST:-0.0.0.0}
  port: ${SERVER_API_PORT:-8080}
  debug: ${DEBUG:-false}
  workers: ${SERVER_WORKERS:-1}
  timeout: ${SERVER_TIMEOUT:-30}
```

#### Redis Configuration
```yaml
redis:
  host: ${REDIS_API_HOST:-redis}
  port: ${REDIS_API_PORT:-6379}
  db: ${REDIS_DB:-0}
  max_connections: ${REDIS_MAX_CONNECTIONS:-10}
```

#### Logging Configuration
```yaml
logging:
  level: ${LOG_LEVEL:-INFO}
  format: ${LOG_FORMAT:-json}
  structured: ${LOG_STRUCTURED:-true}
  console: ${LOG_CONSOLE:-true}
  file_path: ${LOG_FILE_PATH:-}
```

#### Service Dependencies
```yaml
services:
  orchestrator_url: ${ORCHESTRATOR_URL:-http://orchestrator:5099}
  doc_store_url: ${DOC_STORE_URL:-http://doc_store:5087}
  analysis_service_url: ${ANALYSIS_SERVICE_URL:-http://analysis-service:5020}
  # ... other service URLs
```

## Usage

### Basic Service Integration

```python
from services.shared.infrastructure.config import load_service_config

# Load configuration for current service
config = load_service_config("my-service")

# Access configuration values
port = config.server.port
redis_host = config.redis.host
log_level = config.logging.level
orchestrator_url = config.services.orchestrator_url
```

### Advanced Configuration Manager

```python
from services.shared.infrastructure.config import ConfigurationManager, Environment

# Create configuration manager with custom validator
manager = ConfigurationManager(
    service_name="my-service",
    config_class=MyServiceConfig,
    validators=[MyCustomValidator()]
)

# Load configuration for specific environment
config = manager.load_config(environment=Environment.PRODUCTION)

# Save configuration template
manager.save_config(config, "config.template.yaml")
```

## Environment-Specific Configuration

### Development Configuration (`config.development.yaml`)
```yaml
server:
  debug: true
logging:
  level: DEBUG
  console: true
```

### Production Configuration (`config.production.yaml`)
```yaml
server:
  debug: false
  workers: 4
logging:
  level: INFO
  console: false
  file_path: /var/log/my-service.log
redis:
  max_connections: 50
security:
  cors_origins: ["https://myapp.com"]
  rate_limiting:
    enabled: true
    requests_per_minute: 100
```

## Migration Guide

### From Environment Variables

**Before:**
```python
import os

port = int(os.environ.get("API_PORT", "8080"))
redis_host = os.environ.get("REDIS_API_HOST", "localhost")
debug = os.environ.get("DEBUG", "false").lower() == "true"
```

**After:**
```python
from services.shared.infrastructure.config import load_service_config

config = load_service_config("my-service")
port = config.server.port
redis_host = config.redis.host
debug = config.server.debug
```

### From YAML Loading

**Before:**
```python
import yaml

with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

port = config['server']['port']
```

**After:**
```python
from services.shared.infrastructure.config import load_service_config

config = load_service_config("my-service")
port = config.server.port
```

## Standardization Tools

### Configuration Audit Script
```bash
python audit_configuration.py
```
Analyzes all services and identifies configuration inconsistencies.

### Configuration Standardization Script
```bash
# Dry run
python scripts/hardening/configuration_standardization.py --dry-run

# Apply to specific service
python scripts/hardening/configuration_standardization.py --service my-service

# Apply to all services
python scripts/hardening/configuration_standardization.py
```

### Environment Variable Migration
```bash
# Analyze environment variable usage
python scripts/hardening/migrate_env_vars.py --service my-service --report

# Generate comprehensive migration report
python scripts/hardening/migrate_env_vars.py --report
```

## Best Practices

### 1. Environment Variables vs Configuration Files

- **Use environment variables for:**
  - Secrets and credentials
  - Environment-specific values (ports, hosts)
  - Runtime configuration that may change

- **Use configuration files for:**
  - Default values
  - Complex nested configurations
  - Service-specific settings
  - Feature flags and limits

### 2. Naming Conventions

- Environment variables: `SCREAMING_SNAKE_CASE`
- Configuration paths: `dot.separated.lowercase`
- Service names: `kebab-case`

### 3. Configuration Validation

Always implement custom validators for service-specific requirements:

```python
from services.shared.infrastructure.config import ConfigurationValidator

class MyServiceValidator(ConfigurationValidator):
    def validate(self, config):
        errors = []
        if config.custom.get('max_workers', 0) < 1:
            errors.append("max_workers must be positive")
        return errors
```

### 4. Service Port Assignments

Standardized ports for consistency across environments:

| Service | Port |
|---------|------|
| orchestrator | 5099 |
| doc_store | 5087 |
| analysis-service | 5020 |
| source-agent | 5085 |
| frontend | 3000 |
| log-collector | 5080 |

## Docker Integration

### Standardized Docker Compose

```yaml
version: "3.9"
services:
  my-service:
    image: python:3.12-slim
    working_dir: /app
    volumes:
      - ../../:/app:ro
      - ./:/app/services/my-service:rw
    environment:
      - ENVIRONMENT=development
    command: bash -lc "pip install --no-cache-dir -r requirements.txt && python services/my-service/main.py"
    ports:
      - "5080:5080"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## Monitoring and Observability

Configuration values are automatically included in health checks and metrics:

```json
{
  "status": "healthy",
  "service": "my-service",
  "version": "1.0.0",
  "config": {
    "environment": "production",
    "server": {"port": 5080, "debug": false},
    "redis": {"host": "redis", "port": 6379}
  }
}
```

## Troubleshooting

### Common Issues

1. **Configuration not loading**
   - Check file permissions on config.yaml
   - Verify YAML syntax
   - Ensure environment variables are set

2. **Validation errors**
   - Check custom validators
   - Verify required fields are present
   - Review error messages for specific issues

3. **Environment-specific configs not applied**
   - Check ENVIRONMENT variable is set
   - Verify config.{environment}.yaml exists
   - Ensure correct environment name (development/staging/production)

### Debug Mode

Enable debug logging to see configuration loading process:

```bash
export LOG_LEVEL=DEBUG
export DEBUG=true
```

## Future Enhancements

- **Hot reloading**: Configuration changes without service restart
- **Configuration server**: Centralized configuration distribution
- **Schema validation**: JSON Schema validation for configurations
- **Configuration encryption**: Secure handling of sensitive values
- **Configuration migration**: Automatic migration between versions
