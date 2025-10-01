# Migration Guide: Standardized Configuration System

## Overview

This guide provides step-by-step instructions for migrating services from legacy `shared.core` imports to the new standardized configuration system.

## Benefits

- ✅ **Consistency**: All services use identical configuration patterns
- ✅ **Maintainability**: Centralized configuration management
- ✅ **Type Safety**: Pydantic-based validation
- ✅ **Environment Support**: Automatic environment variable loading
- ✅ **Documentation**: Self-documenting configuration classes

## Migration Pattern

### Before (Legacy)
```python
from services.shared.core.constants_new import ServiceNames, ErrorCodes
from services.shared.core.responses import create_success_response, create_error_response

# Hardcoded service configuration
SERVICE_NAME = "my-service"
SERVICE_TITLE = "My Service"
SERVICE_VERSION = "1.0.0"
DEFAULT_API_PORT = 8000

app = FastAPI(
    title=SERVICE_TITLE,
    description="Service description",
    version=SERVICE_VERSION,
)

setup_common_middleware(app, ServiceNames.MY_SERVICE)
```

### After (Standardized)
```python
from services.shared.infrastructure.config import load_service_config
from services.shared.presentation.responses import create_success_response, create_error_response

# Load standardized configuration
config = load_service_config(
    service_type="my-service",
    config_file="./config.yaml"  # Optional
)

# Service configuration from standardized config
SERVICE_TITLE = config.service_description or "My Service"
SERVICE_VERSION = config.service_version

app = FastAPI(
    title=SERVICE_TITLE,
    description="Service description",
    version=config.service_version,
    docs_url="/docs",
    redoc_url="/redoc",
)

setup_common_middleware(app, service_name=config.service_name)
```

## Step-by-Step Migration

### Step 1: Update Imports
```python
# Remove these legacy imports:
- from services.shared.core.constants_new import ServiceNames, ErrorCodes
- from services.shared.core.responses import create_success_response, create_error_response
- from services.shared.core.models import ...

# Add these standardized imports:
+ from services.shared.infrastructure.config import load_service_config
+ from services.shared.presentation.responses import create_success_response, create_error_response
```

### Step 2: Replace Service Configuration
```python
# Remove hardcoded constants:
- SERVICE_NAME = "my-service"
- SERVICE_TITLE = "My Service"
- SERVICE_VERSION = "1.0.0"
- DEFAULT_API_PORT = 8000

# Add standardized config loading:
+ config = load_service_config(
+     service_type="my-service",
+     config_file="./config.yaml"  # Optional
+ )
+
+ # Use config values:
+ SERVICE_TITLE = config.service_description or "My Service"
+ SERVICE_VERSION = config.service_version
+ DEFAULT_API_PORT = config.port
```

### Step 3: Update FastAPI App Creation
```python
# Update FastAPI instantiation:
app = FastAPI(
    title=SERVICE_TITLE,           # Now from config
    description="...",
    version=config.service_version,  # Now from config
    docs_url="/docs",              # Add standardized docs
    redoc_url="/redoc",            # Add standardized docs
)
```

### Step 4: Update Middleware Setup
```python
# Replace legacy middleware setup:
- setup_common_middleware(app, ServiceNames.MY_SERVICE)

# With standardized setup:
+ setup_common_middleware(app, service_name=config.service_name)
```

## Service-Specific Configuration

Each service can have specialized configuration by extending the base `ServiceConfig`:

```python
# In services/shared/infrastructure/config/service_config.py
class MyServiceConfig(ServiceConfig):
    """Specialized config for my-service."""

    # Add service-specific settings
    special_setting: str = Field(default="value")
    max_workers: int = Field(default=4, gt=0)
```

## Environment Variables

The standardized config automatically loads from environment variables with the `SERVICE_` prefix:

```bash
# Set service configuration via environment
export SERVICE_SECRET_KEY="your-secret-key"
export SERVICE_DEBUG="true"
export SERVICE_API_PORT="8080"
export SERVICE_DATABASE_URL="sqlite:///./app.db"
```

## Configuration File Support

Services can optionally load from YAML configuration files:

```yaml
# config.yaml
service:
  name: "my-service"
  version: "2.0.0"
  description: "Enhanced My Service"

database:
  url: "postgresql://localhost/mydb"

my_service:
  special_setting: "configured-value"
  max_workers: 8
```

## Remaining Services to Migrate

Based on current audit, these services still need migration:

1. **source-agent** - Large service with complex imports
2. **frontend** - User interface service
3. **project-simulation** - Massive service (4.2M lines) ⚠️ HIGH PRIORITY
4. **prompt_store** - Clean DDD service
5. **secure-analyzer** - Security-focused service
6. **cli** - Command-line interface
7. **architecture-digitizer** - Architecture analysis
8. **github-mcp** - GitHub integration

## Migration Priority

1. **HIGH**: `project-simulation` (largest impact due to size)
2. **HIGH**: `frontend`, `source-agent` (user-facing services)
3. **MEDIUM**: `prompt_store`, `secure-analyzer` (core business services)
4. **LOW**: `cli`, `architecture-digitizer`, `github-mcp` (specialized services)

## Testing Migration

After migration, verify:

1. **Config Loading**: `config.service_name` returns correct value
2. **App Creation**: FastAPI app initializes without errors
3. **Middleware**: Request logging and error handling works
4. **Health Endpoints**: `/health` endpoint responds correctly
5. **API Docs**: `/docs` and `/openapi.json` are accessible

## Rollback Plan

If issues occur, temporarily revert to legacy imports while debugging:

```python
# Temporary rollback imports
from services.shared.core.constants_new import ServiceNames
from services.shared.core.responses import create_success_response, create_error_response

# Keep standardized config but use legacy middleware
setup_common_middleware(app, ServiceNames.MY_SERVICE)  # Legacy
# setup_common_middleware(app, service_name=config.service_name)  # New
```

## Support

For migration issues, check:
1. Service-specific config class exists in `service_config.py`
2. Environment variables use correct `SERVICE_` prefix
3. Config file path is correct (if used)
4. All imports updated consistently
