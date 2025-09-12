# Prompt Store

Navigation: [Home](../../README.md) · [Architecture](../../docs/architecture/) · [Testing](../../docs/guides/TESTING_GUIDE.md) · [Services](../README_SERVICES.md)

Prompt management with versioning, A/B testing, and analytics.

- **Port**: 5110
- **Tests**: [tests/unit/prompt_store](../../tests/unit/prompt_store)

## Overview and role in the ecosystem
- Central repository of prompts for all services, with version control and A/B testing.
- Provides analytics to guide prompt improvements and usage insights across the platform.

## API
| Method | Path                                   | Description |
|--------|----------------------------------------|-------------|
| POST   | /prompts                               | Create |
| GET    | /prompts                               | List |
| GET    | /prompts/search/{category}/{name}      | Fill variables |
| PUT    | /prompts/{id}                          | Update |
| DELETE | /prompts/{id}                          | Delete |
| POST   | /ab-tests                              | Create A/B test |
| GET    | /ab-tests/{id}/select                  | Choose prompt for test |
| GET    | /analytics                             | Usage analytics |
| POST   | /migrate                               | Import from YAML |

## Quickstart
```bash
python services/prompt-store/main.py
```

## Related
- Interpreter: [../interpreter/README.md](../interpreter/README.md)
- Services index: [../README_SERVICES.md](../README_SERVICES.md)

## Testing
- Unit tests: [tests/unit/prompt_store](../../tests/unit/prompt_store)
- Strategies:
  - Envelope-aware assertions: list/create/update/delete endpoints
  - Database-backed operations with in-memory or local SQLite
  - A/B test flows and analytics retrieval

## Environment
| Name | Description | Default |
|------|-------------|---------|
| PROMPT_STORE_DB | SQLite database path | services/prompt-store/prompt_store.db |
| PROMPT_STORE_PORT | Service port | 5110 |
