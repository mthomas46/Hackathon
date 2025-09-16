# Code Analyzer

Navigation: [Home](../../README.md) · [Architecture](../../docs/architecture/) · [Testing](../../docs/guides/TESTING_GUIDE.md) · [Services](../README_SERVICES.md)
Tests: [tests/unit/code_analyzer](../../tests/unit/code_analyzer)

## Overview and role in the ecosystem
- Extracts API endpoints and secure signals from code to enrich Doc Store and drive discovery/analysis.
- Provides a language-agnostic, lightweight path-based detection that can be swapped for AST/LLM later.

## Key Features
- Code endpoint extraction (FastAPI, Flask, Express) with golden tests.
- Style examples list/save and secure scanning for sensitive patterns.
- Posts analyzed `DocumentEnvelope` to doc_store `/documents/enveloped`.
- Standard middlewares, rate-limit toggle, and shared clients.

## Goal
- Provide a reusable service for code-aware analysis across sources (GitHub PRs, raw files, patches) and secure scanning (PII/secrets in code).

## Endpoints
| Method | Path             | Description |
|--------|------------------|-------------|
| GET    | /health          | Health check |
| POST   | /analyze/text    | Analyze text for endpoints |
| POST   | /analyze/files   | Analyze multiple files |
| POST   | /analyze/patch   | Analyze code patch |
| POST   | /scan/secure     | Secure scan for sensitive patterns |
| POST   | /style/examples  | Save style examples |
| GET    | /style/examples  | List style examples (by language) |

## Style Examples & Doc-store
- When `DOC_STORE_URL` is set, POST /style/examples persists examples as `type=style_example` via doc_store `/documents`.
- GET /style/examples will prefer doc_store’s `/style/examples` index if available.

All analyze endpoints return a DocumentEnvelope with a normalized `Document` containing an endpoint summary in `content`, `content_hash`, and `source_link` metadata. If style examples were used, `metadata.style_examples_used` lists them.

## Integration
- Emits `docs.ingested.code` with a `DocumentEnvelope`.
- `github-agent` and `consistency-engine` can call this service when `CODE_ANALYZER_URL` is set.
- Honors `REDIS_HOST` to publish envelopes (optional).

## Examples
```bash
curl -s -X POST "$CODE_ANALYZER_URL/style/examples" \
  -H 'content-type: application/json' \
  -d '{"items":[{"language":"python","snippet":"def add(a:int,b:int)->int:\n return a+b","title":"typed"}]}' | jq .
```

```bash
curl -s -X POST "$CODE_ANALYZER_URL/analyze/text" \
  -H 'content-type: application/json' \
  -d '{"content":"@app.get(\"/items\")","language":"python"}' | jq .
```

## Config
- `REDIS_HOST`: if set, envelopes are published to Redis.
- `DOC_STORE_URL`: if set, style examples are persisted and listed from doc_store.
- `RATE_LIMIT_ENABLED`: enable rate limiting on heavy endpoints when `true|1|yes`.

## Environment
| Name | Description | Default |
|------|-------------|---------|
| REDIS_HOST | Redis host for envelopes | - |
| DOC_STORE_URL | Doc Store base URL | - |
| RATE_LIMIT_ENABLED | Enable rate limiting | false |

## Shared utilities
- Request/metrics middleware: `services/shared/request_id.py`, `services/shared/metrics.py`.
- Config and constants: `services/shared/config.py`, `services/shared/constants.py`.
- JSON HTTP helpers: `services/shared/clients.py`.

## Notes
- Endpoint extraction is lightweight (decorators, route-like strings). Can be swapped for AST/LLM in future.

## Related
- Doc Store: [../doc_store/README.md](../doc_store/README.md)
- GitHub MCP: [../github-mcp/README.md](../github-mcp/README.md)

## Testing
- Unit tests: [tests/unit/code_analyzer](../../tests/unit/code_analyzer)
- Strategies:
  - Analyze endpoints accept text/files/patch; validate normalized envelope

