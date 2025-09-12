# Infrastructure Setup

## Local (compose)
- Use docker-compose files if provided (`docker-compose.dev.yml`, `docker-compose.services.yml`).
- Example:
```bash
docker compose -f docker-compose.dev.yml up -d
```

## Secrets
- Use `.env.local` (never commit) or docker secrets.
- Example `.env.local`:
```bash
GITHUB_TOKEN=ghp_xxx
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_SESSION_TOKEN=...
BEDROCK_API_KEY=...
```

## Observability
- Health: `/health` endpoints on each service
- Logs: `services/log-collector` for dev/test

## Networking
- Default ports: Prompt Store 5110, Interpreter 5120, Log Collector 5080, Orchestrator 5099
