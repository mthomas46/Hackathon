# Running Frontend Individually

The frontend service is standalone and doesn't require external dependencies.

## Quick Start

```bash
cd services/frontend
docker-compose up
```

This will start:
- Frontend service (port 3000)

## Dependencies

- None (standalone service)

## Configuration

Configuration is loaded from:
- `../../config.yml` (project-wide settings)
- `../shared/config.yaml` (shared service settings)
- `./config.yaml` (frontend-specific settings)

## Health Check

```bash
curl http://localhost:3000/health
```

## Access

Open http://localhost:3000 in your browser
