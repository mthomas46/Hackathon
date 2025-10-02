# Docker Management Scripts

This directory contains scripts for Docker container management, validation, and deployment operations in the LLM Documentation Ecosystem.

## Scripts

### Validation Scripts

#### `validate-deployment.sh`
**Production Deployment Validator** - Comprehensive end-to-end deployment validation for production environments.

**Features:**
- Multi-service health verification across all 29 services
- Network connectivity testing between services
- Resource usage monitoring and threshold checking
- Database connectivity and performance validation
- Security configuration verification
- Automated rollback recommendations

**Use Cases:**
- Pre-production deployment validation
- Post-deployment health verification
- Automated deployment pipeline quality gates
- Production environment monitoring
- Disaster recovery validation

#### `validate-ports.sh`
**Port Conflict Validator** - Advanced port conflict detection and resolution for Docker deployments.

**Features:**
- Comprehensive port scanning across all services
- Host port availability checking
- Docker network port mapping validation
- Automatic conflict resolution suggestions
- Integration with Docker Compose port management

**Use Cases:**
- Development environment setup validation
- Production deployment preparation
- Troubleshooting port binding issues
- Network configuration optimization
- Multi-service deployment planning

### Health Check Scripts

#### `accurate-health-check.sh`
**Enterprise Health Checking** - Advanced, service-aware health validation with intelligent retry logic.

**Features:**
- Service-specific health check implementations
- Intelligent timeout and retry mechanisms
- Dependency-aware health validation
- Performance impact monitoring
- Automated health trend analysis
- Integration with monitoring systems

**Use Cases:**
- Production service health monitoring
- Load balancer health checks
- Automated recovery procedures
- Performance degradation detection
- Service mesh health validation

#### `health-check.sh`
**Basic Health Monitoring** - Lightweight health checking for development and testing environments.

**Features:**
- Standard HTTP health endpoint checking
- Basic service availability validation
- Simple timeout and retry logic
- Container status monitoring
- Basic resource usage alerts

**Use Cases:**
- Development environment validation
- Basic CI/CD health checking
- Quick service availability testing
- Development workflow integration
- Simple monitoring dashboards

### Management Scripts

#### `bulletproof-startup.sh`
**Reliable Service Orchestrator** - Production-grade service startup with comprehensive error handling and recovery.

**Features:**
- Dependency-aware service startup sequencing
- Automatic failure recovery and retry logic
- Resource availability validation
- Startup performance monitoring
- Comprehensive error logging and reporting
- Integration with service discovery systems

**Use Cases:**
- Production service deployment automation
- Zero-downtime service restarts
- Disaster recovery procedures
- Automated scaling operations
- Maintenance window management

#### `pre-flight-check.sh`
**Environment Readiness Validator** - Comprehensive pre-deployment environment validation and preparation.

**Features:**
- Docker daemon and API version validation
- Network connectivity and DNS resolution
- Resource availability checking (CPU, memory, disk)
- Security configuration validation
- Dependency verification (databases, external services)
- Configuration file validation

**Use Cases:**
- Pre-deployment environment preparation
- Automated deployment pipeline prerequisites
- Development environment setup validation
- Production environment audits
- Troubleshooting deployment failures

### Utility Scripts

#### `generate-compose.py`
**Dynamic Compose Generator** - Intelligent Docker Compose file generation based on service requirements and environment.

**Features:**
- Environment-aware compose file generation
- Service dependency analysis and ordering
- Network configuration optimization
- Volume mount configuration
- Environment variable templating
- Multi-environment support (dev/staging/prod)

**Use Cases:**
- Automated deployment configuration
- Multi-environment deployment management
- Service scaling configuration
- Development environment setup
- CI/CD pipeline compose file generation

#### `dockerfile-linter.sh`
**Dockerfile Security & Optimization Linter** - Comprehensive Dockerfile analysis and improvement recommendations.

**Features:**
- Security vulnerability scanning
- Best practices compliance checking
- Performance optimization suggestions
- Layer optimization analysis
- Base image security validation
- Build context optimization

**Use Cases:**
- CI/CD pipeline Dockerfile validation
- Security compliance auditing
- Performance optimization reviews
- Development workflow integration
- Automated code review processes

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
