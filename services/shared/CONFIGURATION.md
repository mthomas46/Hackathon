# Shared Infrastructure Service Configuration

This document describes the environment variables and configuration options available for the Shared Infrastructure Service.

## Environment Variables

### Shared Service Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `SHARED_CONTACT_NAME` | `Shared Infrastructure Team` | Name of the contact person/team for the service |
| `SHARED_CONTACT_EMAIL` | `shared@company.com` | Contact email address |
| `SHARED_CONTACT_URL` | `https://shared.company.com/support` | Support/contact URL |
| `SHARED_LICENSE_NAME` | `Proprietary` | License name |
| `SHARED_LICENSE_URL` | `https://shared.company.com/license` | License URL |
| `SHARED_DOCS_HOST` | `localhost` | Host for documentation URLs in logs |
| `SHARED_DOCS_PORT` | `8000` | Port for documentation URLs in logs |

### Redis Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_HOST` | `localhost` | Redis server hostname |
| `REDIS_PORT` | `6379` | Redis server port |

### Existing Configuration (inherited from base config)

| Variable | Default | Description |
|----------|---------|-------------|
| `ENVIRONMENT` | `development` | Environment type (development/staging/production) |
| `DEBUG` | `false` | Enable debug mode |
| `DATABASE_URL` | `sqlite:///./shared.db` | Database connection URL |
| `REDIS_URL` | `redis://localhost:6379` | Alternative Redis URL |
| `SECRET_KEY` | - | Secret key for security (required) |
| `LOG_LEVEL` | `INFO` | Logging level |
| `HTTP_CLIENT_TIMEOUT` | `30` | HTTP client timeout in seconds |

## Configuration File Example

```bash
# Shared Service Specific
SHARED_CONTACT_NAME=DevOps Team
SHARED_CONTACT_EMAIL=devops@yourcompany.com
SHARED_CONTACT_URL=https://yourcompany.com/devops-support

# Redis Configuration
REDIS_HOST=redis.yourcompany.com
REDIS_PORT=6379

# Standard Configuration
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=your-very-secure-secret-key-here
LOG_LEVEL=WARNING
```

## Migration from Hardcoded Values

This service has been updated to eliminate hardcoded configuration values. Previously hardcoded values like:

- Contact URLs: `https://shared.company.com/support`
- Documentation URLs: `http://localhost:8000/docs`
- Redis defaults: `localhost:6379`

Are now configurable via environment variables with sensible defaults maintained for backward compatibility.
