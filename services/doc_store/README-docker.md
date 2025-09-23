# Running Doc Store Individually

The doc_store service requires both Redis (for caching) and SQLite (for persistence).

## Quick Start

```bash
cd services/doc_store
docker-compose up
```

This will start:
- Doc Store service (port 5087)
- Redis instance (port 6379)
- SQLite database (automatically mounted)

## Dependencies

- Redis (automatically provided)
- SQLite database (persistent volume provided)

## Configuration

Configuration is loaded from:
- `../../config.yml` (project-wide settings)
- `../shared/config.yaml` (shared service settings)
- `./config.yaml` (doc_store-specific settings)

## Health Check

```bash
curl http://localhost:5087/health
```

## Database Access

```bash
# Access SQLite database
docker exec -it <container_id> sqlite3 /app/services/doc_store/db.sqlite3
```
