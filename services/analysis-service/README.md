# Analysis Service

Navigation: [Home](../../README.md) · [Architecture](../../docs/architecture/) · [Testing](../../docs/guides/TESTING_GUIDE.md) · [Services](../README_SERVICES.md)

Comprehensive document analysis and consistency checking.

- **Port**: 5020
- **Depends on**: Doc Store, Source Agent, Prompt Store (optional), Redis (optional)
- **Tests**: [tests/unit/analysis_service](../../tests/unit/analysis_service)

## Features
- Consistency analysis and API mismatch detection
- Findings retrieval and reporting (summary, trends, ticket lifecycle, PR confidence)
- Integration helpers and prompt-driven analysis

## Overview and role in the ecosystem
- Core analysis engine for documentation consistency, API/document drift, and reporting.
- Consumes content from Doc Store and Source Agent; produces findings and reports used by UI and Orchestrator jobs.
- Integrates with Prompt Store and Interpreter for prompt-driven and natural language analyses.

## API
| Method | Path                                  | Description |
|--------|---------------------------------------|-------------|
| POST   | /analyze                               | Analyze targets |
| GET    | /findings                              | List findings (filters: limit, severity, finding_type_filter) |
| POST   | /reports/generate                      | Generate report: summary, trends, life_of_ticket, pr_confidence |
| GET    | /reports/confluence/consolidation      | Confluence consolidation report |
| GET    | /reports/jira/staleness                | Jira staleness report |
| POST   | /reports/findings/notify-owners        | Notify owners of findings |
| GET    | /integration/health                    | Integration health summary |
| POST   | /integration/analyze-with-prompt       | Analyze using prompt from Prompt Store |
| POST   | /integration/natural-language-analysis | Analyze via Interpreter query |
| POST   | /integration/log-analysis              | Log analysis usage |

## Quickstart
```bash
python services/analysis-service/main.py
# or via docker-compose if available
```

## Configuration
- `DOC_STORE_URL`, `SOURCE_AGENT_URL`, `ANALYSIS_SERVICE_URL`, `REDIS_HOST`

### Environment
| Name | Description | Default |
|------|-------------|---------|
| DOC_STORE_URL | Base URL for Doc Store | - |
| SOURCE_AGENT_URL | Base URL for Source Agent | - |
| ANALYSIS_SERVICE_URL | Self base URL (for internal calls) | - |
| REDIS_HOST | Redis host for events | redis |

## Related
- Prompt Store: [services/prompt-store/README.md](../prompt-store/README.md)
- Interpreter: [services/interpreter/README.md](../interpreter/README.md)
- Services index: [services/README_SERVICES.md](../README_SERVICES.md)

## Testing
- Unit tests: [tests/unit/analysis_service](../../tests/unit/analysis_service)
- Strategies:
  - Envelope-aware assertions for endpoints that return success envelopes
  - Mocked service clients (Doc Store, Source Agent) with URL-based branching
  - Validation of query param handling and error paths
  - Strict limits and filter behavior (e.g., `limit`, `severity`)
