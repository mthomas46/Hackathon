# MCP Provisioner Service - Quick Start Guide

## Overview

The **MCP Provisioner Service** manages the lifecycle of Model Context Protocol (MCP) instances in the ecosystem. This guide will help you get started quickly.

---

## Prerequisites

- **Docker** and **Docker Compose** installed
- **Python 3.11+** (for local development)
- **Redis** (for state persistence)
- Access to the `hackathon_default` Docker network

---

## Quick Start Options

### Option 1: Run with Docker Compose (Recommended)

This is the easiest way to run the service with all dependencies.

```bash
# From project root
cd /Users/mykalthomas/Documents/work/Hackathon

# Start the service and dependencies
docker-compose up -d mcp-provisioner

# View logs
docker-compose logs -f mcp-provisioner

# Check health
curl http://localhost:8144/api/v1/health

# Open API documentation
open http://localhost:8144/docs
```

### Option 2: Run Locally (Development)

For active development with hot-reload.

```bash
# Navigate to service directory
cd services/mcp-provisioner

# Run the startup script
./scripts/start_local.sh

# Or manually:
# 1. Start Redis
docker-compose up -d redis

# 2. Create virtual environment and install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Set environment variables
export PYTHONPATH=$(pwd)/../..
export REDIS_HOST=localhost

# 4. Run service
python3 -m uvicorn services.mcp_provisioner.main:app --reload --port 5400
```

---

## API Endpoints

Once running, the service exposes the following endpoints:

### Health & Documentation

- **API Docs**: `http://localhost:8144/docs` (Swagger UI)
- **OpenAPI Spec**: `http://localhost:8144/openapi.json`
- **Health Check**: `GET /api/v1/health`
- **Readiness Check**: `GET /api/v1/ready`
- **Liveness Check**: `GET /api/v1/live`

### MCP Management

- **Provision MCP**: `POST /api/v1/mcps`
- **Start MCP**: `POST /api/v1/mcps/{mcp_id}/start`
- **Stop MCP**: `POST /api/v1/mcps/{mcp_id}/stop`
- **Get MCP Status**: `GET /api/v1/mcps/{mcp_id}`
- **List MCPs**: `GET /api/v1/mcps?state=<state>`
- **Delete MCP**: `DELETE /api/v1/mcps/{mcp_id}?force=<bool>`

---

## Example Usage

### 1. Provision a New MCP Instance

```bash
curl -X POST http://localhost:8144/api/v1/mcps \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "client-abc-123",
    "tier": 0,
    "memory_limit": "512m",
    "cpu_shares": 1024,
    "metadata": {
      "owner": "team-a",
      "project": "project-x"
    }
  }'
```

**Response:**
```json
{
  "status": "success",
  "message": "MCP instance provisioned successfully: <mcp_id>",
  "data": {
    "mcp_id": "550e8400-e29b-41d4-a716-446655440000",
    "client_id": "client-abc-123",
    "name": "mcp-client-abc-123-tier0",
    "state": "cold",
    "tier": 0,
    ...
  }
}
```

### 2. Start the MCP Instance

```bash
MCP_ID="550e8400-e29b-41d4-a716-446655440000"

curl -X POST http://localhost:8144/api/v1/mcps/${MCP_ID}/start
```

**State Transition:** `COLD → WARMING → HOT`

### 3. Get MCP Status

```bash
curl http://localhost:8144/api/v1/mcps/${MCP_ID}
```

### 4. List All MCPs

```bash
# All MCPs
curl http://localhost:8144/api/v1/mcps

# Filter by state
curl http://localhost:8144/api/v1/mcps?state=hot
```

### 5. Stop the MCP Instance

```bash
curl -X POST http://localhost:8144/api/v1/mcps/${MCP_ID}/stop
```

**State Transition:** `HOT → COOLING → COLD`

### 6. Delete the MCP Instance

```bash
# Normal delete (stops if running, then deletes)
curl -X DELETE http://localhost:8144/api/v1/mcps/${MCP_ID}

# Force delete (immediate stop and delete)
curl -X DELETE "http://localhost:8144/api/v1/mcps/${MCP_ID}?force=true"
```

---

## Testing

### Run Unit Tests

```bash
cd services/mcp-provisioner

# Install test dependencies
pip install -r requirements.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=services/mcp_provisioner --cov-report=html

# Run specific test categories
pytest -m unit           # Unit tests only
pytest -m integration    # Integration tests only
pytest tests/unit/domain/  # Domain layer tests only
```

### Run Integration Tests

```bash
# Ensure Redis and Docker are running
docker-compose up -d redis

# Run integration tests
pytest -m integration
```

---

## Configuration

### Environment Variables

Key configuration options (see `.env.example` for full list):

| Variable | Default | Description |
|----------|---------|-------------|
| `SERVICE_API_PORT` | `5400` | Internal API port |
| `REDIS_HOST` | `redis` | Redis hostname |
| `REDIS_PORT` | `6379` | Redis port |
| `DOCKER_NETWORK` | `hackathon_default` | Docker network name |
| `MCP_PORT_RANGE_START` | `9000` | Start of MCP port range |
| `MCP_PORT_RANGE_END` | `9100` | End of MCP port range |
| `LOG_LEVEL` | `INFO` | Logging level |

### Docker Network

The service uses the `hackathon_default` network (alias: `doc-ecosystem-dev`):
- **Subnet**: `172.20.0.0/16`
- **Bridge**: `hackathon_bridge`
- **MTU**: `1500`

---

## Architecture Overview

```
services/mcp-provisioner/
├── domain/              # Business logic
│   ├── entities/       # MCPInstance
│   ├── value_objects/  # MCPState, MCPConfig, ResourceLimits
│   └── repositories/   # MCPRepository interface
├── application/        # Use cases
│   ├── use_cases/     # Provision, Start, Stop, Get, List, Delete
│   └── dto/           # Data transfer objects
├── infrastructure/     # External integrations
│   ├── repositories/  # RedisMCPRepository
│   └── external_services/  # DockerServiceImpl, PortAllocator
├── presentation/       # API layer
│   └── api/
│       ├── routes/    # FastAPI routers
│       └── models/    # Pydantic models
└── tests/             # Comprehensive tests
```

---

## Troubleshooting

### Service Won't Start

1. **Check Redis**:
   ```bash
   redis-cli -h localhost ping
   # Should return: PONG
   ```

2. **Check Docker**:
   ```bash
   docker ps
   # Should list running containers
   ```

3. **Check Logs**:
   ```bash
   docker-compose logs mcp-provisioner
   ```

### Health Check Fails

```bash
# Check service status
curl http://localhost:8144/api/v1/health

# Expected response:
{
  "status": "healthy",
  "service": "mcp-provisioner",
  "version": "1.0.0",
  "dependencies": {
    "redis": "healthy",
    "docker": "healthy"
  }
}
```

### MCP Container Won't Start

1. **Check Docker Image Exists**:
   ```bash
   docker images | grep client-mcp
   ```

2. **Check Port Availability**:
   ```bash
   # Ports 9000-9100 should be available
   netstat -an | grep 900[0-9]
   ```

3. **Check Docker Network**:
   ```bash
   docker network ls | grep hackathon
   docker network inspect doc-ecosystem-dev
   ```

### Redis Connection Issues

```bash
# Test Redis connection
docker-compose exec mcp-provisioner redis-cli -h redis ping

# Check Redis keys
docker-compose exec redis redis-cli KEYS "mcp:provisioner:*"
```

---

## Development

### Code Quality

```bash
# Format code
black services/mcp_provisioner/

# Sort imports
isort services/mcp_provisioner/

# Type checking
mypy services/mcp_provisioner/

# Linting
pylint services/mcp_provisioner/

# Security scan
bandit -r services/mcp_provisioner/
```

### Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

---

## Next Steps

1. **Explore API Documentation**: Visit `http://localhost:8144/docs`
2. **Run Example Workflows**: Try the complete lifecycle (provision → start → stop → delete)
3. **Review Architecture**: Read `/services/mcp-provisioner/README.md`
4. **Integrate with Other Services**: Use MCP instances in your workflows
5. **Customize Configuration**: Adjust `.env` for your needs

---

## Support

- **Documentation**: `/docs/mcp-system-plan/`
- **Service README**: `/services/mcp-provisioner/README.md`
- **Architecture Guide**: `/docs/mcp-system-plan/MCP_SYSTEM_ARCHITECTURE.md`
- **Integration Guide**: `/docs/mcp-system-plan/ECOSYSTEM_INTEGRATION_GUIDE.md`

---

**Happy provisioning! 🚀**

