# Notification Service

Navigation: [Home](../../README.md) · [Architecture](../../docs/architecture/) · [Testing](../../docs/guides/TESTING_GUIDE.md) · [Services](../README_SERVICES.md)
Owner resolution and notifications with DLQ and deduplication.

- **Port**: 5095
- **Endpoints**: `/owners/update`, `/owners/resolve`, `/notify`, `/dlq`, `/health`
- **Tests**: [tests/unit/notification_service](../../tests/unit/notification_service)

## Overview and role in the ecosystem
- Resolves owners to notification targets (email/webhook) and sends notifications from analysis workflows.
- Provides deduplication, DLQ, and simple caching to ensure reliable delivery.

## Features
- Owner resolution with heuristics and caching (TTL)
- Notification delivery (webhook stub; email/Slack placeholders)
- Deduplication and dead-letter queue
- Health endpoint and self-registration

## API
| Method | Path            | Description |
|--------|-----------------|-------------|
| GET    | /health         | Health check |
| POST   | /owners/update  | Update ownership registry (stub) |
| POST   | /owners/resolve | Resolve owners to targets |
| POST   | /notify         | Send notification |
| GET    | /dlq            | Read dead-letter queue |

## Examples
```bash
curl -X POST http://localhost:5095/owners/resolve -H 'Content-Type: application/json' \
  -d '{"owners":["devops","alerts@example.com"]}'
```

## Related
- Analysis Service (notify owners): [../analysis-service/README.md](../analysis-service/README.md)
- Services index: [../README_SERVICES.md](../README_SERVICES.md)

## Testing
- Unit tests: [tests/unit/notification_service](../../tests/unit/notification_service)
- Strategies:
  - Owner resolution heuristics and cache behavior
  - Webhook failures routed to DLQ; error envelopes

## Environment
| Name | Description | Default |
|------|-------------|---------|
| NOTIFY_OWNER_MAP_JSON | Inline JSON mapping for owners | - |
| NOTIFY_OWNER_MAP_FILE | Path to JSON mapping file | - |
| PORT | Service port | 5095 |
