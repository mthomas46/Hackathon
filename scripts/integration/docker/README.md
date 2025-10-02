# Docker Integration Tests

This directory contains integration tests specifically for Docker containerized deployments and orchestration.

## Scripts

### `comprehensive_docker_test.py`
**Docker Ecosystem Integration Test Suite** - Comprehensive testing of the complete Docker ecosystem with all services.

**Features:**
- Full Docker Compose stack validation
- Multi-service container orchestration testing
- Network connectivity between containers
- Volume mounting and data persistence validation
- Resource usage monitoring across containers
- Container health check validation
- Docker network configuration testing

**Use Cases:**
- End-to-end Docker deployment validation
- Production Docker environment testing
- Container orchestration reliability testing
- Multi-service Docker communication validation
- Docker infrastructure regression testing

### `test_docker_services.py`
**Individual Docker Service Integration Tester** - Focused testing of individual services within Docker containers.

**Features:**
- Individual service container startup validation
- Service-specific Docker configuration testing
- Container networking and port mapping validation
- Docker volume mount testing per service
- Service health checks in containerized environment
- Resource limits and constraints validation

**Use Cases:**
- Individual service Docker deployment validation
- Service-specific container configuration testing
- Docker networking troubleshooting
- Container resource optimization
- Service isolation testing in Docker environment
