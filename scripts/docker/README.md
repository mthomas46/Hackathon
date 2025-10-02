# Docker Management Scripts

This directory contains scripts for Docker container management, validation, and deployment operations in the LLM Documentation Ecosystem.

## Scripts

### Validation Scripts
- `validate-deployment.sh` - **Production Deployment Validator**
  - Comprehensive pre-deployment validation
  - Service health checking
  - Network connectivity testing
  - Resource usage monitoring
  - Generates detailed validation reports

- `validate-ports.sh` - **Port Conflict Validator**
  - Checks for port conflicts across services
  - Validates port availability
  - Docker network port mapping validation

### Health Check Scripts
- `accurate-health-check.sh` - **Enhanced Health Checking**
  - Advanced health check implementations
  - Service-specific health validation
  - Timeout and retry logic

- `health-check.sh` - **Basic Health Checking**
  - Standard Docker health check utilities
  - Container status monitoring
  - Basic service availability testing

### Management Scripts
- `bulletproof-startup.sh` - **Reliable Startup Script**
  - Dependency-aware service startup
  - Error recovery and retry logic
  - Comprehensive startup validation

- `pre-flight-check.sh` - **Pre-Flight Validation**
  - Pre-deployment environment validation
  - Docker daemon and network checks
  - Resource availability verification

### Utility Scripts
- `generate-compose.py` - **Compose File Generator**
  - Dynamic Docker Compose file generation
  - Service configuration templating
  - Environment-specific compose file creation

- `dockerfile-linter.sh` - **Dockerfile Linter**
  - Dockerfile best practices validation
  - Security scanning for Dockerfiles
  - Optimization recommendations

## Usage Examples

```bash
# Full deployment validation
./scripts/docker/validate-deployment.sh

# Port conflict checking
./scripts/docker/validate-ports.sh

# Bulletproof service startup
./scripts/docker/bulletproof-startup.sh

# Pre-flight environment check
./scripts/docker/pre-flight-check.sh
```

## Integration Points

- Referenced in `Makefile.docker`
- Used by deployment automation scripts
- Integrated with CI/CD validation pipelines
- Called by `docker_compose_validator.py` for comprehensive validation

## Purpose

These scripts ensure:
- ✅ Reliable Docker deployments
- ✅ Service health and connectivity validation
- ✅ Port conflict prevention
- ✅ Production-ready container management
- ✅ Automated deployment validation
