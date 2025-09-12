# Interpreter Service

Navigation: [Home](../../README.md) · [Architecture](../../docs/architecture/) · [Testing](../../docs/guides/TESTING_GUIDE.md) · [Services](../README_SERVICES.md)

Natural language interpretation and workflow generation.

- **Port**: 5120
- **Endpoints**: `/health`, `/interpret`, `/execute`, `/intents`
- **Tests**: [tests/unit/interpreter](../../tests/unit/interpreter)

## Features
- Intent recognition and entity extraction
- Workflow creation and execution helper
- Confidence scoring and metrics

## Overview and role in the ecosystem
- Entry point for natural language interactions. Converts free-form queries into structured intents and workflows.
- Integrates with Prompt Store, Analysis Service, Doc Store, and Source Agent to build executable plans.
- Enables CLI/Frontend to operate the platform via human-friendly commands.

## API
| Method | Path       | Description |
|--------|------------|-------------|
| GET    | /health    | Health check |
| POST   | /interpret | Interpret natural language query |
| POST   | /execute   | Interpret and execute workflow |
| GET    | /intents   | List supported intents |

## Environment
| Name | Description | Default |
|------|-------------|---------|
| INTERPRETER_PORT | Service port | 5120 |

## Quickstart
```bash
python services/interpreter/main.py
```

## Examples
```bash
curl -X POST http://localhost:5120/interpret -H 'Content-Type: application/json' \
  -d '{"query":"analyze this document"}'
```

## Related
- Analysis Service: [../analysis-service/README.md](../analysis-service/README.md)
- Prompt Store: [../prompt-store/README.md](../prompt-store/README.md)
- Services index: [../README_SERVICES.md](../README_SERVICES.md)

## Testing
- Unit tests: [tests/unit/interpreter](../../tests/unit/interpreter)
- Strategies:
  - Ensure tests import the real service app by adding project root to `sys.path`
  - For `/intents`, handle success envelopes and list structures
  - For `/interpret` and `/execute`, allow flexible result structures and 404-tolerant fallbacks
