# Running Orchestrator Individually

The orchestrator service requires Redis for caching and coordination.

## Quick Start

```bash
cd services/orchestrator
docker-compose up
```

This will start:
- Orchestrator service (port 5099)
- Redis instance (port 6379)

## Dependencies

- Redis (automatically provided)

## Configuration

Configuration is loaded from:
- `../../config.yml` (project-wide settings)
- `../shared/config.yaml` (shared service settings)  
- `./config.yaml` (orchestrator-specific settings)

## Health Check

```bash
curl http://localhost:5099/health
```
