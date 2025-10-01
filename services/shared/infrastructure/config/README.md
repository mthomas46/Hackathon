# Centralized Configuration Management

This module provides a standardized configuration management system for all services in the LLM Documentation Ecosystem.

## Quick Start

```python
from services.shared.infrastructure.config import load_service_config

# Load configuration for your service
config = load_service_config("my-service")

# Access configuration values
port = config.server.port
redis_host = config.redis.host
log_level = config.logging.level
```

## Features

- **Multi-source configuration loading** (YAML files, environment variables, defaults)
- **Environment-specific overrides** (development, staging, production)
- **Type-safe configuration access** with dataclass-based schemas
- **Configuration validation** with customizable validators
- **Service dependency management** with standardized service URLs
- **Docker integration** with standardized compose files

## File Structure

```
services/shared/infrastructure/config/
├── __init__.py                 # Public API exports
├── configuration_manager.py    # Core configuration management
└── README.md                   # This file
```

## Configuration Files

Each service should have these configuration files:

- `config.yaml` - Base service configuration
- `config.development.yaml` - Development overrides
- `config.production.yaml` - Production overrides
- `config.staging.yaml` - Staging overrides (optional)

## Example Configuration

```yaml
# config.yaml
server:
  host: ${SERVER_API_HOST:-0.0.0.0}
  port: ${SERVER_API_PORT:-8080}
  debug: ${DEBUG:-false}

redis:
  host: ${REDIS_API_HOST:-redis}
  port: ${REDIS_API_PORT:-6379}

logging:
  level: ${LOG_LEVEL:-INFO}
  format: ${LOG_FORMAT:-json}

services:
  orchestrator_url: ${ORCHESTRATOR_URL:-http://orchestrator:5099}
  doc_store_url: ${DOC_STORE_URL:-http://doc_store:5087}
```

## Migration Tools

Use the provided scripts to migrate existing services:

```bash
# Analyze current configuration
python audit_configuration.py

# Standardize service configuration
python scripts/hardening/configuration_standardization.py --service my-service

# Migrate environment variables
python scripts/hardening/migrate_env_vars.py --service my-service --report
```

## API Reference

### load_service_config(service_name, config_class=None, environment=None)

Load configuration for a service.

**Parameters:**
- `service_name` (str): Name of the service
- `config_class` (Type[BaseServiceConfig], optional): Custom configuration class
- `environment` (Environment, optional): Target environment

**Returns:** Configuration object

### ConfigurationManager

Advanced configuration management with validation and custom loading.

**Methods:**
- `load_config(environment=None, validate=True)`: Load configuration
- `save_config(config, file_path=None)`: Save configuration to file
- `get_config_template()`: Generate configuration template

### BaseServiceConfig

Standard configuration schema that all services inherit from.

**Attributes:**
- `service_name`, `service_version`, `environment`
- `server` (ServerConfig)
- `redis` (RedisConfig)
- `logging` (LoggingConfig)
- `services` (ServiceDependencies)
- `limits`, `health`, `security` (Dict)
- `custom` (Dict) - Service-specific configuration

## Environment Variables

### Standard Variables

- `ENVIRONMENT` - Target environment (development/staging/production)
- `SERVER_API_HOST`, `SERVER_API_PORT` - Server configuration
- `REDIS_API_HOST`, `REDIS_API_PORT` - Redis configuration
- `LOG_LEVEL` - Logging level
- `DEBUG` - Debug mode flag

### Service URL Variables

All service URLs can be overridden with environment variables:
- `ORCHESTRATOR_URL`
- `DOC_STORE_URL`
- `ANALYSIS_SERVICE_URL`
- etc.

## Validation

Configuration is automatically validated on load. Custom validators can be added:

```python
from services.shared.infrastructure.config import ConfigurationValidator

class MyValidator(ConfigurationValidator):
    def validate(self, config):
        errors = []
        if config.server.port < 1000:
            errors.append("Port must be >= 1000")
        return errors

manager = ConfigurationManager(
    service_name="my-service",
    validators=[MyValidator()]
)
```

## Best Practices

1. **Use configuration files for defaults**, environment variables for overrides
2. **Validate configuration** in custom validators
3. **Document service-specific configuration** in the `custom` section
4. **Use standardized ports** from the port registry
5. **Test configuration loading** in unit tests

## Troubleshooting

### Configuration Not Loading

1. Check file permissions on `config.yaml`
2. Verify YAML syntax with `yamllint`
3. Ensure environment variables are properly formatted
4. Check service directory structure

### Validation Errors

1. Review error messages for specific validation failures
2. Check custom validators for service-specific requirements
3. Verify all required fields are present
4. Ensure data types match expected formats

### Environment-Specific Configs

1. Verify `ENVIRONMENT` variable is set correctly
2. Check that `config.{environment}.yaml` exists
3. Ensure environment name matches enum values

## Contributing

When adding new configuration options:

1. Add to the appropriate dataclass in `configuration_manager.py`
2. Update the base configuration files
3. Add environment variable mappings if needed
4. Update documentation and examples
5. Add validation rules if required
